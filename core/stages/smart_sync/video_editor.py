import os
import re
import ffmpeg
import subprocess
from typing import List, Dict, Any
from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable

def parse_srt(srt_path: str) -> List[Dict[str, Any]]:
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple SRT parser
    blocks = content.strip().split('\n\n')
    segments = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            text = ' '.join(lines[2:])
            
            # 00:00:01,234 --> 00:00:05,678
            m = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
            if m:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
                start = int(h1)*3600 + int(m1)*60 + int(s1) + int(ms1)/1000.0
                end = int(h2)*3600 + int(m2)*60 + int(s2) + int(ms2)/1000.0
                segments.append({
                    'start': start,
                    'end': end,
                    'text': text
                })
    return segments

def get_duration(file_path: str) -> float:
    cmd = [get_ffmpeg_executable() or 'ffmpeg', '-i', file_path]
    try:
        # ffmpeg outputs to stderr
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        m = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
        if m:
            h, m, s = m.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        log.error(f"Error getting duration for {file_path}: {e}")
    return 0.0

class VideoEditor:
    def sync_video_to_audio(self, video_path: str, srt_path: str, audio_path: str, gemini_data: List[Dict[str, Any]], output_path: str) -> bool:
        log.info(f"Syncing video {video_path} to audio {audio_path} using Gemini timestamps...")
        
        audio_segments = parse_srt(srt_path)
        if not audio_segments:
            log.warning("No audio segments found in SRT.")
            return False

        if not gemini_data:
            log.warning("No Gemini mapping data provided.")
            return False

        # Create mapping points (audio_time, video_time)
        mapping_points = []
        mapping_points.append((0.0, 0.0))  # Start of video
        
        # We assume the gemini_data corresponds roughly to the audio segments.
        # But we might have fewer Gemini segments than audio segments if sentences were grouped.
        # So we just match by finding the closest text or just sequentially mapping the ones we have.
        
        for g_seg in gemini_data:
            g_text = g_seg.get('script_sentence', '').strip().lower()
            g_time = float(g_seg.get('timestamp', 0.0))
            
            # Find matching audio segment
            best_match = None
            for a_seg in audio_segments:
                a_text = a_seg['text'].strip().lower()
                if g_text in a_text or a_text in g_text:
                    best_match = a_seg
                    break
            
            if best_match:
                # Map audio start time to video timestamp
                mapping_points.append((best_match['start'], g_time))
                
        # Get total durations
        audio_duration = get_duration(audio_path)
        if audio_duration <= 0.0:
            audio_duration = audio_segments[-1]['end'] if audio_segments else 0.0
            
        video_duration = get_duration(video_path)

        # Sort mapping points
        mapping_points.sort(key=lambda x: x[0])
        
        # Add end point
        mapping_points.append((audio_duration, video_duration))

        # Generate clips
        clips = []
        
        for i in range(len(mapping_points) - 1):
            a_start, v_start = mapping_points[i]
            a_end, v_end = mapping_points[i+1]
            
            a_dur = a_end - a_start
            v_dur = v_end - v_start
            
            if a_dur <= 0.1:
                continue
                
            if v_dur <= 0.1:
                # If video duration is very short or negative, just freeze the frame
                v_dur = 0.1
                v_end = v_start + 0.1
                
            base_clip = ffmpeg.input(video_path).trim(start=v_start, end=v_end).setpts('PTS-STARTPTS')
            
            if v_dur < a_dur:
                # Video action is short: Play at normal speed, then FREEZE last frame
                pad_duration = a_dur - v_dur
                clip = base_clip.filter('tpad', stop=-1, stop_mode='clone', stop_duration=pad_duration)
            else:
                # Video action is long: Gently speed it up so it finishes during the sentence
                pts_factor = v_dur / a_dur
                clip = base_clip.setpts(f'{pts_factor}*PTS')
                
            clips.append(clip)

        if not clips:
            log.error("No clips generated.")
            return False

        try:
            log.info(f"Rendering {len(clips)} individual clips to prevent graph errors...")
            os.makedirs("temp/clips", exist_ok=True)
            clip_files = []
            
            for i, clip in enumerate(clips):
                clip_path = f"temp/clips/clip_{i:04d}.mp4"
                out = ffmpeg.output(clip, clip_path, vcodec='libx264', preset='ultrafast')
                out.run(cmd=get_ffmpeg_executable() or 'ffmpeg', overwrite_output=True, quiet=True)
                clip_files.append(clip_path)
                
            log.info("Concatenating synced video clips...")
            concat_file = "temp/clips/concat.txt"
            with open(concat_file, "w") as f:
                for p in clip_files:
                    f.write(f"file '{os.path.basename(p)}'\n")
                    
            cmd = [
                get_ffmpeg_executable() or 'ffmpeg',
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-c:a', 'aac',
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            log.info(f"Synced video saved to {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode('utf8', 'ignore') if e.stderr else str(e)
            log.error(f"ffmpeg error: {err}")
            return False
        except ffmpeg.Error as e:
            err = e.stderr.decode('utf8', 'ignore') if e.stderr else str(e)
            log.error(f"ffmpeg error: {err}")
            return False
