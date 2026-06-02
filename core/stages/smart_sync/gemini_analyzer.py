import os
import json
import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from core.utils.logger import log

class SyncSegment(BaseModel):
    script_sentence: str = Field(description="The exact sentence from the script")
    timestamp: float = Field(description="The best matching timestamp in seconds from the video")
    screen_description: str = Field(description="A brief description of what is on screen at this moment")

class SyncResult(BaseModel):
    segments: list[SyncSegment]

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.0-flash'

    def sync_script_to_video(self, video_path: str, script_text: str) -> List[Dict[str, Any]]:
        log.info(f"Uploading {video_path} to Gemini...")
        
        # Upload video to Gemini
        video_file = self.client.files.upload(file=video_path)
        
        # Wait for processing
        while video_file.state.name == 'PROCESSING':
            log.info("Waiting for video to process in Gemini...")
            time.sleep(2)
            video_file = self.client.files.get(name=video_file.name)
            
        if video_file.state.name == 'FAILED':
            log.error("Gemini video processing failed.")
            return []
            
        log.info("Video processed successfully. Analyzing with script...")
        
        prompt = f"""
Here is my tutorial script:
{script_text}

Watch this screen recording and for each sentence in the script,
tell me what timestamp in the video best matches that script line,
and what UI element is visible at that moment.
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[video_file, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SyncResult,
                        temperature=0.1
                    )
                )
                
                # Clean up the file to save quota
                self.client.files.delete(name=video_file.name)
                
                result_json = response.text
                parsed = json.loads(result_json)
                
                # If it's wrapped in a dict with 'segments' key
                if "segments" in parsed:
                    return parsed["segments"]
                return parsed
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < max_retries - 1:
                    log.warning(f"Rate limited by Gemini (429). Waiting 15 seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(15)
                else:
                    log.error(f"Gemini API Error: {e}")
                    try:
                        self.client.files.delete(name=video_file.name)
                    except:
                        pass
                    return []
