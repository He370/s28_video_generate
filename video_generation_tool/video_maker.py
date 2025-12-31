from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import os
import random
import math
import numpy as np
from PIL import Image

class VideoMaker:
    def __init__(self, output_file: str = "history_video.mp4"):
        self.output_file = output_file

    def apply_ken_burns(self, clip, duration: float):
        """
        Applies a random Ken Burns effect (Pan & Zoom) to the clip.
        Uses manual transform with PIL for high quality resize, as MoviePy 2.x
        Crop/Resize effects may not support animation/lambdas easily yet.
        """
        w, h = clip.size
        target_ratio = 16 / 9
        current_ratio = w / h
        
        # 1. Determine maximum 16:9 crop that fits in the original image
        if current_ratio > target_ratio:
            max_h = h
            max_w = int(h * target_ratio)
        else:
            max_w = w
            max_h = int(w / target_ratio)
            
        # 2. Random Start/End Zoom (1.0 = max fit, >1.0 = zoomed in)
        zoom_min = 1.15
        zoom_max = 1.40 
        
        z1 = random.uniform(zoom_min, zoom_max)
        z2 = random.uniform(zoom_min, zoom_max)
        
        # 3. Calculate Crop Dimensions
        w1, h1 = max_w / z1, max_h / z1
        w2, h2 = max_w / z2, max_h / z2
        
        # 4. Calculate Valid Top-Left Positions
        x1_max = w - w1
        y1_max = h - h1
        x2_max = w - w2
        y2_max = h - h2
        
        # Random positions
        # Ensure we don't go negative if zoomed out too much (logic protects this mostly)
        x1 = random.uniform(0, max(0, x1_max))
        y1 = random.uniform(0, max(0, y1_max))
        x2 = random.uniform(0, max(0, x2_max))
        y2 = random.uniform(0, max(0, y2_max))
        
        def filter_frame(get_frame, t):
            # Safe interpolation
            p = t / duration if duration > 0 else 0
            p = max(0, min(1, p)) # clamp
            
            current_x = x1 + (x2 - x1) * p
            current_y = y1 + (y2 - y1) * p
            current_w = w1 + (w2 - w1) * p
            current_h = h1 + (h2 - h1) * p
            
            # Get frame
            img_np = get_frame(t)
            
            # Crop
            ix = int(current_x)
            iy = int(current_y)
            iw = int(current_w)
            ih = int(current_h)
            
            # PIL Image for Resize (high quality)
            # MoviePy frames are HxWx3 (RGB)
            try:
                img_pil = Image.fromarray(img_np)
                
                # Crop
                # box = (left, upper, right, lower)
                box = (ix, iy, ix + iw, iy + ih)
                img_crop = img_pil.crop(box)
                
                # Resize
                # BICUBIC is high quality
                img_resized = img_crop.resize((1920, 1080), resample=Image.BILINEAR)
                
                return np.array(img_resized)
            except Exception as e:
                # Fallback to avoid crash during render
                print(f"Error in Ken Burns frame: {e}")
                return img_np

        # Create new clip
        # Note: transform allows changing size? 
        # Usually transform keeps size unless we cheat or use another generic wrapper.
        # But 'transform' doc says "Modifies the clip by applying...". 
        # If the returned frame has different size, the clip size property might be wrong 
        # unless updated. 
        # Actually, VideoClip with make_frame is better if size changes.
        # But here use `transform` and assume MoviePy handles frame size change dynamically 
        # OR we force-set metadata.
        
        # Actually, simpler to just wrap in a new VideoClip if using arbitrary frame gen.
        # But `clip.transform` is meant for this.
        
        new_clip = clip.transform(filter_frame)
        
        # IMPORTANT: Manually set the size of the new clip to 1920x1080
        # because the internal metadata won't update automatically just by the function.
        # But MoviePy 2 might be strict.
        # Let's use `resized` for final safety metadata update?
        # Or just trust that we return 1920x1080
        
        # In simple Manual:
        # new_clip.size = (1920, 1080)
        # return new_clip
        
        # However, `transform` returns a copy.
        # We should monkeypatch size or use `with_effects([vfx.Resize((1920, 1080))])` 
        # but that would resize AGAIN.
        
        # Let's try creating a generic VideoClip with make_frame
        
        from moviepy import VideoClip as ValidVideoClip
        def make_frame(t):
           return filter_frame(clip.get_frame, t)
           
        final_clip = ValidVideoClip(make_frame, duration=duration)
        final_clip.fps = 24
        final_clip.size = (1920, 1080)
        
        return final_clip



    def create_video(self, segments: list, enable_ken_burns: bool = False, bgm_file: str = None, bgm_files: list = None, bgm_volume: float = 0.1, padding_config: dict = None):
        """
        Combines segments into a final video.
        Each segment is a dict: {'image': path, 'audio': path, 'text': str}
        padding_config: Dict mapping index (int) or 'default' to padding seconds. 
                       Supports negative indices (e.g., -1 for last).
        bgm_file: Path to a single BGM file (legacy support).
        bgm_files: List of paths to BGM files to play sequentially.
        """
        clips = []
        
        # Check explicit padding for start/end if passed, or use defaults
        # Example usage: {0: 2.0, -1: 3.0, 'default': 0.5}
        pad_conf = padding_config if padding_config else {}
        default_padding = pad_conf.get('default', 0.5)
        
        for i, segment in enumerate(segments):
            # Load Audio
            audio_clip = AudioFileClip(segment['audio'])
            
            # Determine padding
            # Check explicit index
            if i in pad_conf:
                padding = pad_conf[i]
            # Check negative index logic (last element)
            elif (i - len(segments)) in pad_conf:
                 padding = pad_conf[i - len(segments)]
            else:
                 padding = default_padding
                
            duration = audio_clip.duration + padding
            
            # Load Image
            image_clip = ImageClip(segment['image']).with_duration(duration)
            
            # Check Ken Burns flag: Segment specific or Global override
            use_ken_burns = segment.get('ken_burns', enable_ken_burns)

            if use_ken_burns:
                try:
                    # Apply Advanced Ken Burns
                    image_clip = self.apply_ken_burns(image_clip, duration)
                except Exception as e:
                    print(f"Error applying Ken Burns, falling back to static: {e}")
                    image_clip = image_clip.resized(new_size=(1920, 1080))
            else:
                # Standard fit
                image_clip = image_clip.resized(new_size=(1920, 1080))
                
            image_clip = image_clip.with_position('center')
            
            # Create Subtitle (Optional, simple version)
            # Note: TextClip requires ImageMagick. If not installed, this might fail.
            # We will try/except or just skip subtitles if complex.
            # For this implementation, we'll try a simple TextClip.
            
            clips_to_compose = [image_clip]
            
            # Composite with fixed size to handle the zooming image
            video_clip = CompositeVideoClip(clips_to_compose, size=(1920, 1080))
            
            video_clip = video_clip.with_audio(audio_clip)
            clips.append(video_clip)
            
        final_clip = concatenate_videoclips(clips)
        
        # Add Background Music
        # Prioritize bgm_files if provided, else use bgm_file
        effective_bgm_files = []
        if bgm_files:
            effective_bgm_files = bgm_files
        elif bgm_file:
            effective_bgm_files = [bgm_file]
            
        if effective_bgm_files:
            try:
                from moviepy import CompositeAudioClip
                from moviepy.audio.fx import AudioLoop
                
                bgm_clips = []
                current_duration = 0
                target_duration = final_clip.duration
                
                # Load and sequence BGM clips until we cover the duration
                # If we run out of files, loop the list or just stop adding? 
                # Request said "don't loop a single song", but if list is exhausted, we might need to repeat the list.
                # However, usually BGM lists are long enough. Let's loop the list index.
                
                idx = 0
                while current_duration < target_duration and effective_bgm_files:
                    # Pick file (cycling through list)
                    file_path = effective_bgm_files[idx % len(effective_bgm_files)]
                    idx += 1
                    
                    if os.path.exists(file_path):
                        clip = AudioFileClip(file_path)
                        bgm_clips.append(clip)
                        current_duration += clip.duration
                    else:
                        print(f"BGM file not found: {file_path}")
                        # Avoid infinite loop if all files are missing
                        if idx >= len(effective_bgm_files) * 2: 
                             break

                if bgm_clips:
                    # Concatenate them
                    full_bgm = concatenate_audioclips(bgm_clips)
                    
                    # Trim to exact video duration
                    if full_bgm.duration > target_duration:
                        full_bgm = full_bgm.subclipped(0, target_duration)
                    else:
                        # If still too short (rare case if list loop logic works), loop it
                         full_bgm = full_bgm.with_effects([AudioLoop(duration=target_duration)])
                    
                    # Set volume
                    full_bgm = full_bgm.with_volume_scaled(bgm_volume)
                    
                    # Composite audio
                    final_audio = CompositeAudioClip([final_clip.audio, full_bgm])
                    final_clip = final_clip.with_audio(final_audio)
                    print(f"Added background music using {len(bgm_clips)} tracks (Volume: {bgm_volume})")
                    
            except Exception as e:
                print(f"Error adding background music: {e}")

        final_clip.write_videofile(self.output_file, fps=24)
