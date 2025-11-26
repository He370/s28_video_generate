import os
import sys
from moviepy import AudioFileClip, CompositeAudioClip
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def make_seamless_loop(audio_path: str, output_path: str, crossfade_duration: float = 3.0):
    """
    Converts an audio file into a seamless loop using the 'swap and crossfade' technique.
    1. Cut audio in half.
    2. Swap the two halves (End becomes Start, Start becomes End).
    3. Crossfade the center join (which was the original start/end boundary).
    
    This ensures the new start and end match perfectly (they were originally continuous).
    """
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        if duration < crossfade_duration * 2:
            print(f"Skipping {os.path.basename(audio_path)}: Duration {duration:.2f}s too short for {crossfade_duration}s crossfade.")
            # Just copy it or maybe apply simple fade in/out? 
            # Let's just apply simple fades for short clips to avoid clicks
            audio = audio.with_effects([AudioFadeIn(duration=0.1), AudioFadeOut(duration=0.1)])
            audio.write_audiofile(output_path, logger=None)
            return

        # Midpoint
        mid = duration / 2
        
        # Split
        part1 = audio.subclipped(0, mid)
        part2 = audio.subclipped(mid, duration)
        
        # Swap: Part2 then Part1
        # We need to overlap them at the join.
        # Structure: [Part2 (minus overlap)] [Crossfade Zone] [Part1 (minus overlap)]
        # Actually, simpler:
        # Overlap Part2's end with Part1's start.
        # But Part2 was originally at the end, Part1 at start.
        # The discontinuity is between Part2_End and Part1_Start.
        # So we place Part2 first, then Part1.
        # We overlap them by crossfade_duration.
        
        # To do this with CompositeAudioClip:
        # Clip A: Part2. Start at 0.
        # Clip B: Part1. Start at Part2.duration - crossfade_duration.
        # We fade out Clip A end, fade in Clip B start.
        
        # Apply fades to the join point
        part2 = part2.with_effects([AudioFadeOut(duration=crossfade_duration)])
        part1 = part1.with_effects([AudioFadeIn(duration=crossfade_duration)])
        
        # Shift Part1
        part1 = part1.with_start(part2.duration - crossfade_duration)
        
        # Composite
        final = CompositeAudioClip([part2, part1])
        
        # The total duration will be duration - crossfade_duration
        # The new start (Part2 start) and new end (Part1 end) correspond to the original 'mid' point.
        # Since the original audio was continuous at 'mid', the new loop point is perfect.
        
        final.write_audiofile(output_path, logger=None, bitrate="320k")
        print(f"Processed: {os.path.basename(audio_path)} -> {os.path.basename(output_path)}")
        
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")

def main():
    # Paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.abspath(os.path.join(project_dir, "../../audio_generater/extracted_sounds"))
    target_dir = os.path.join(project_dir, "resources")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")
        
    print(f"Scanning {source_dir}...")
    
    files_processed = 0
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav')):
                source_path = os.path.join(root, file)
                
                # Maintain relative structure if needed, or just flat?
                # User said "store... under white_noise/resources path".
                # Let's keep it flat for simplicity unless there are name collisions.
                # Or maybe subfolders? extracted_sounds usually has subfolders?
                # Let's check if extracted_sounds has subfolders.
                
                rel_path = os.path.relpath(source_path, source_dir)
                target_path = os.path.join(target_dir, rel_path)
                
                # Ensure target subdir exists
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                make_seamless_loop(source_path, target_path)
                files_processed += 1
                
    print(f"Done. Processed {files_processed} files.")

if __name__ == "__main__":
    main()
