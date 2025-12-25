from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os
import random

class VideoMaker:
    def __init__(self, output_file: str = "history_video.mp4"):
        self.output_file = output_file

    def create_video(self, segments: list, enable_ken_burns: bool = False, bgm_file: str = None, bgm_volume: float = 0.1, padding_config: dict = None):
        """
        Combines segments into a final video.
        Each segment is a dict: {'image': path, 'audio': path, 'text': str}
        padding_config: Dict mapping index (int) or 'default' to padding seconds. 
                       Supports negative indices (e.g., -1 for last).
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
            image_clip = image_clip.resized(new_size=(1920, 1080))
            
            if enable_ken_burns:
                # Ken Burns Effect: Small Random Zoom
                scale_amount = random.uniform(0.02, 0.06)  # 2% to 6% zoom
                if random.choice([True, False]):
                    # Zoom In: 1.0 -> 1.0 + scale_amount
                    image_clip = image_clip.resized(lambda t: 1 + scale_amount * (t / duration))
                else:
                    # Zoom Out: 1.0 + scale_amount -> 1.0
                    image_clip = image_clip.resized(lambda t: 1 + scale_amount * (1 - t / duration))
                
                image_clip = image_clip.with_position('center')
            
            # Create Subtitle (Optional, simple version)
            # Note: TextClip requires ImageMagick. If not installed, this might fail.
            # We will try/except or just skip subtitles if complex.
            # For this implementation, we'll try a simple TextClip.
            
            clips_to_compose = [image_clip]
            
            try:
                txt_clip = TextClip(segment['text'], font_size=40, color='white', size=(1800, None), method='caption')
                txt_clip = txt_clip.with_position(('center', 'bottom')).with_duration(duration)
                clips_to_compose.append(txt_clip)
            except Exception as e:
                print(f"Warning: Could not create TextClip (ImageMagick might be missing). using image only. Error: {e}")
            
            # Composite with fixed size to handle the zooming image
            video_clip = CompositeVideoClip(clips_to_compose, size=(1920, 1080))
            
            video_clip = video_clip.with_audio(audio_clip)
            clips.append(video_clip)
            
        final_clip = concatenate_videoclips(clips)
        
        # Add Background Music
        if bgm_file and os.path.exists(bgm_file):
            try:
                from moviepy import CompositeAudioClip
                from moviepy.audio.fx import AudioLoop
                
                bgm_clip = AudioFileClip(bgm_file)
                
                # Loop BGM if it's shorter than the video
                if bgm_clip.duration < final_clip.duration:
                    bgm_clip = bgm_clip.with_effects([AudioLoop(duration=final_clip.duration)])
                else:
                    bgm_clip = bgm_clip.subclipped(0, final_clip.duration)
                
                # Set volume
                bgm_clip = bgm_clip.with_volume_scaled(bgm_volume)
                
                # Composite audio
                final_audio = CompositeAudioClip([final_clip.audio, bgm_clip])
                final_clip = final_clip.with_audio(final_audio)
                print(f"Added background music: {bgm_file} (Volume: {bgm_volume})")
            except Exception as e:
                print(f"Error adding background music: {e}")

        final_clip.write_videofile(self.output_file, fps=24)
