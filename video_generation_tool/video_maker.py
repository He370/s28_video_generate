from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
import os
import random
import math
import numpy as np
from PIL import Image

class VideoMaker:
    def __init__(self, output_file: str = "history_video.mp4"):
        self.output_file = output_file

    def apply_ken_burns_ffmpeg(self, image_path: str, duration: float, output_path: str, effect_mode: str = None):
        """
        Applies a smooth Ken Burns effect using FFmpeg's zoompan filter.
        Supports random zoom in/out and panning directions.
        
        Args:
            image_path: Path to the input image
            duration: Duration of the effect in seconds
            output_path: Path for the output video file
            effect_mode: Optional specific mode to use
            
        Returns:
            True if successful, False otherwise
        """
        import subprocess
        
        # Use 60fps for smoother motion
        fps = 60
        total_frames = int(duration * fps)
        
        # Randomly select an effect mode if not provided
        modes = [
            'zoom_in_center', 'zoom_out_center', 
            'pan_right', 'pan_left', 
            'pan_up', 'pan_down',
            'zoom_in_top_left', 'zoom_in_bottom_right',
            'zoom_out_top_right', 'zoom_out_bottom_left'
        ]
        
        if effect_mode and effect_mode in modes:
            mode = effect_mode
        else:
            mode = random.choice(modes)
        
        # Zoom parameters
        z_min = 1.0
        z_max = 1.25  # 25% zoom
        z_step = (z_max - z_min) / total_frames
        
        # Default expressions
        z_expr = f"{z_max}"  # distinct from zoom logic
        x_expr = "0"
        y_expr = "0"
        
        if mode == 'zoom_in_center':
            z_expr = f"min({z_min}+{z_step}*on,{z_max})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
            
        elif mode == 'zoom_out_center':
            z_expr = f"max({z_max}-{z_step}*on,{z_min})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
            
        elif mode == 'pan_right':
            # Zoom fixed at z_max, pan x from 0 to max_x
            z_expr = f"{z_max}"
            max_x = f"iw-iw/{z_max}"
            x_expr = f"({max_x})*(on/{total_frames})"
            y_expr = f"ih/2-(ih/zoom/2)"
            
        elif mode == 'pan_left':
            # Zoom fixed at z_max, pan x from max_x to 0
            z_expr = f"{z_max}"
            max_x = f"iw-iw/{z_max}"
            x_expr = f"({max_x})*(1-on/{total_frames})"
            y_expr = f"ih/2-(ih/zoom/2)"
            
        elif mode == 'pan_down':
            # Zoom fixed at z_max, pan y from 0 to max_y
            z_expr = f"{z_max}"
            max_y = f"ih-ih/{z_max}"
            x_expr = f"iw/2-(iw/zoom/2)"
            y_expr = f"({max_y})*(on/{total_frames})"
            
        elif mode == 'pan_up':
            # Zoom fixed at z_max, pan y from max_y to 0
            z_expr = f"{z_max}"
            max_y = f"ih-ih/{z_max}"
            x_expr = f"iw/2-(iw/zoom/2)"
            y_expr = f"({max_y})*(1-on/{total_frames})"

        elif mode == 'zoom_in_top_left':
            # Zoom in towards top-left (0,0)
            z_expr = f"min({z_min}+{z_step}*on,{z_max})"
            # x, y stay at 0 (top-left aligned) relative to the frame?
            # Actually zoompan centers on x,y. 
            # If x=0, y=0, it's top left.
            x_expr = "0"
            y_expr = "0"
            
        elif mode == 'zoom_in_bottom_right':
            # Zoom in towards bottom-right
            z_expr = f"min({z_min}+{z_step}*on,{z_max})"
            x_expr = "iw-iw/zoom"
            y_expr = "ih-ih/zoom"
        
        elif mode == 'zoom_out_top_right':
            # Start zoomed in at top-right, zoom out
            z_expr = f"max({z_max}-{z_step}*on,{z_min})"
            x_expr = "iw-iw/zoom"
            y_expr = "0"

        elif mode == 'zoom_out_bottom_left':
            # Start zoomed in at bottom-left, zoom out
            z_expr = f"max({z_max}-{z_step}*on,{z_min})"
            x_expr = "0"
            y_expr = "ih-ih/zoom"
            
        # Build video filter chain:
        # 1. Scale up to 4K (3840x2160) for quality, but not 8K to save performance
        # 2. Apply zoompan
        # 3. Scale output to 1080p for consistency? Or keep 4K? 
        # The project seems to output 1080p final. 
        # Let's keep the filter chain simple: Scale -> Zoompan -> Format
        # Zoompan 's' parameter sets the OUTPUT size of the filter.
        
        vf_chain = (
            f"scale=3840x2160,"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1920x1080:fps={fps},"
            f"format=yuv420p"
        )
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-loop', '1',  # Required for still image input
            '-i', image_path,
            '-vf', vf_chain,
            '-c:v', 'libx264',
            '-crf', '18',  # High quality
            '-preset', 'slow',
            '-t', str(duration),
            '-y',  # Overwrite output file
            output_path
        ]
        
        print(f"Applying Ken Burns: Mode={mode}")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error applying Ken Burns: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"Error applying Ken Burns with FFmpeg: {e}")
            return False



    def create_video(self, segments: list, enable_ken_burns: bool = False, bgm_file: str = None, bgm_files: list = None, bgm_volume: float = 0.1, padding_config: dict = None):
        """
        Combines segments into a final video.
        Each segment is a dict: {'image': path, 'audio': path, 'text': str}
        padding_config: Dict mapping index (int) or 'default' to padding seconds. 
                       Supports negative indices (e.g., -1 for last).
        bgm_file: Path to a single BGM file (legacy support).
        bgm_files: List of paths to BGM files to play sequentially.
        """
        from moviepy import VideoFileClip
        import tempfile
        
        clips = []
        temp_files = []  # Track temporary files for cleanup
        
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
            
            # Check Ken Burns flag: Segment specific or Global override
            use_ken_burns = segment.get('ken_burns', enable_ken_burns)

            if use_ken_burns:
                # Use FFmpeg to pre-process the image with Ken Burns effect
                temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_video_path = temp_video.name
                temp_video.close()
                temp_files.append(temp_video_path)
                
                success = self.apply_ken_burns_ffmpeg(
                    segment['image'], 
                    duration, 
                    temp_video_path
                )
                
                if success:
                    # Load the pre-processed video clip
                    video_clip = VideoFileClip(temp_video_path)
                    video_clip = video_clip.with_audio(audio_clip)
                else:
                    print(f"Failed to apply Ken Burns with FFmpeg, using static image")
                    # Fallback to static image
                    image_clip = ImageClip(segment['image']).with_duration(duration)
                    image_clip = image_clip.resized(new_size=(1920, 1080))
                    image_clip = image_clip.with_position('center')
                    video_clip = CompositeVideoClip([image_clip], size=(1920, 1080))
                    video_clip = video_clip.with_audio(audio_clip)
            else:
                # Standard static image
                image_clip = ImageClip(segment['image']).with_duration(duration)
                image_clip = image_clip.resized(new_size=(1920, 1080))
                image_clip = image_clip.with_position('center')
                video_clip = CompositeVideoClip([image_clip], size=(1920, 1080))
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
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                print(f"Error cleaning up temporary file {temp_file}: {e}")
