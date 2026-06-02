import os
import glob
import base64
import ffmpeg
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI

from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable

class VideoAction(BaseModel):
    timestamp: float = Field(description="The timestamp in seconds where this action occurs")
    description: str = Field(description="A detailed description of the UI action happening at this timestamp")

class SyncSegment(BaseModel):
    script_sentence: str = Field(description="The exact sentence from the script")
    timestamp: float = Field(description="The best matching timestamp in seconds from the video")
    screen_description: str = Field(description="A brief description of what is on screen at this moment")

class SyncResult(BaseModel):
    video_analysis: list[VideoAction] = Field(description="A detailed chronological timeline of all actions seen in the video.")
    refined_script: str = Field(description="The user's original script rewritten or adjusted to perfectly narrate the actual actions occurring in the video analysis timeline.")
    segments: list[SyncSegment] = Field(description="The final mapping of the refined_script sentences to video timestamps.")

class OpenAIAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model_name = 'gpt-4o-mini'
        self.frames_dir = 'temp/frames'

    def _extract_frames(self, video_path: str) -> List[str]:
        os.makedirs(self.frames_dir, exist_ok=True)
        # Clear old frames
        for f in glob.glob(os.path.join(self.frames_dir, '*.jpg')):
            try:
                os.remove(f)
            except:
                pass
            
        log.info(f"Extracting frames at 0.5 FPS from {video_path}...")
        try:
            (
                ffmpeg
                .input(video_path)
                .filter('fps', fps=0.5)
                .output(os.path.join(self.frames_dir, 'frame_%04d.jpg'), q=5)
                .run(cmd=get_ffmpeg_executable() or 'ffmpeg', overwrite_output=True, quiet=True)
            )
        except ffmpeg.Error as e:
            err = e.stderr.decode('utf-8', 'ignore') if e.stderr else str(e)
            log.error(f"Frame extraction failed: {err}")
            return []
            
        frames = sorted(glob.glob(os.path.join(self.frames_dir, '*.jpg')))
        return frames

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def sync_script_to_video(self, video_path: str, script_text: str) -> tuple[List[Dict[str, Any]], str]:
        import json
        cache_path = f"temp/openai_cache_{os.path.basename(video_path)}.json"
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                log.info(f"Loaded cached OpenAI analysis for {os.path.basename(video_path)}")
                return cache_data['segments'], cache_data['refined_script']
            except:
                pass
                
        # Text-Only Recovery Fallback
        if os.path.exists("temp/openai.txt") and os.path.exists("temp/refined_script.txt"):
            log.info("Recovering missing timestamps from existing openai.txt timeline...")
            try:
                with open("temp/openai.txt", "r", encoding="utf-8") as f:
                    timeline = f.read()
                with open("temp/refined_script.txt", "r", encoding="utf-8") as f:
                    refined = f.read()
                    
                content = [
                    {
                        "type": "text",
                        "text": f"Here is an existing video timeline:\n{timeline}\n\nHere is the refined script:\n{refined}\n\nPlease output the mapping of the sentences to the timestamps exactly in JSON format."
                    }
                ]
                
                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=[{"role": "user", "content": content}],
                    response_format=SyncResult,
                    temperature=0.1,
                    max_tokens=2000
                )
                
                result = completion.choices[0].message.parsed
                if result:
                    segments_dump = [segment.model_dump() for segment in result.segments]
                    try:
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            json.dump({'segments': segments_dump, 'refined_script': result.refined_script}, f)
                    except Exception as e:
                        log.error(f"Failed to write OpenAI cache during recovery: {e}")
                    log.info("Successfully recovered and cached timestamps!")
                    return segments_dump, result.refined_script
            except Exception as e:
                log.error(f"Text recovery failed: {e}. Falling back to full image analysis.")
                
        frames = self._extract_frames(video_path)
        if not frames:
            return [], ""
            
        log.info(f"Extracted {len(frames)} frames. Sending to OpenAI ({self.model_name})...")
        
        # Build messages
        content = [
            {
                "type": "text", 
                "text": f"Here is my tutorial script:\n{script_text}\n\nI am providing you with a sequence of frames extracted from a screen recording at exactly 1 frame every 2 seconds (the first image is 0 seconds, the second is 2 seconds, the third is 4 seconds, etc.).\n\nTo ensure perfect accuracy, follow these steps:\n1. FIRST, carefully analyze the video frames in High Definition. Create a highly granular `video_analysis` timeline. You MUST read the text on the screen and write down exactly which parameters are being selected, the exact values entered, the specific UI button labels, and what is changing from frame to frame.\n2. SECOND, rewrite the user's tutorial script to create a `refined_script`. This script should perfectly match the visual actions in the video. Add missing narration for actions the user didn't mention, and remove narration for things that never happen on screen.\n3. THIRD, map the sentences from your `refined_script` to the most appropriate timestamp from your `video_analysis` timeline. Output exactly in JSON."
            }
        ]
        
        for frame in frames:
            b64 = self._encode_image(frame)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high"
                }
            })
            
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": content}
                ],
                response_format=SyncResult,
                temperature=0.1,
                max_tokens=2000
            )
            
            result = completion.choices[0].message.parsed
            if result:
                # Save the video analysis to a text file
                try:
                    os.makedirs('temp', exist_ok=True)
                    with open('temp/openai.txt', 'w', encoding='utf-8') as f:
                        f.write("=== OpenAI Video Timeline Analysis ===\n\n")
                        for action in result.video_analysis:
                            f.write(f"[{action.timestamp}s] {action.description}\n")
                    log.info("Saved video analysis timeline to temp/openai.txt")
                except Exception as e:
                    log.error(f"Failed to save openai.txt: {e}")
                    
                try:
                    with open('temp/refined_script.txt', 'w', encoding='utf-8') as f:
                        f.write(result.refined_script)
                    log.info("Saved refined narration script to temp/refined_script.txt")
                except Exception as e:
                    log.error(f"Failed to save refined script: {e}")
                    
                segments_dump = [segment.model_dump() for segment in result.segments]
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({'segments': segments_dump, 'refined_script': result.refined_script}, f)
                except Exception as e:
                    log.error(f"Failed to write OpenAI cache: {e}")
                    
                return segments_dump, result.refined_script
            return [], ""
            
        except Exception as e:
            log.error(f"OpenAI API Error: {e}")
            return [], ""
