import asyncio
import edge_tts
import os
import wave
from google import genai
from google.genai import types

class AudioGenerator:
    VOICE_MAPPING = {
        "Chinese": {"gemini": "Puck", "edge": "zh-CN-XiaoxiaoNeural", "code": "zh"},
        "Spanish": {"gemini": "Kore", "edge": "es-ES-ElviraNeural", "code": "es"},
        "Japanese": {"gemini": "Fenrir", "edge": "ja-JP-NanamiNeural", "code": "ja"},
        "French": {"gemini": "Puck", "edge": "fr-FR-DeniseNeural", "code": "fr"},
        "Hindi": {"gemini": "Kore", "edge": "hi-IN-SwaraNeural", "code": "hi"},
        "English": {"gemini": "Fenrir", "edge": "en-US-ChristopherNeural", "code": "en"}
    }

    def __init__(self, language: str = "English", mode: str = "dev", voice_name: str = None, prompt_prefix: str = None):
        self.language = language
        self.mode = mode
        
        # Select voice based on language and mode
        voice_config = self.VOICE_MAPPING.get(language, self.VOICE_MAPPING["English"])
        self.edge_voice = voice_config["edge"]
        # Use provided voice_name if available, otherwise default to language mapping
        self.gemini_voice = voice_name if voice_name else voice_config["gemini"]
        
        # Set prompt prefix
        self.prompt_prefix = prompt_prefix if prompt_prefix else "Please read the following text at a regular and moderate speaking pace suitable for a documentary narration: "
        
        # Initialize Gemini client for prod mode
        if self.mode == "prod":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            self.client = genai.Client(api_key=api_key)

    async def generate_audio(self, text: str, output_file: str):
        """
        Generates audio from text using edge-tts.
        """
        communicate = edge_tts.Communicate(text, self.edge_voice)
        await communicate.save(output_file)

    def generate_audio_gemini(self, text: str, output_file: str):
        """
        Generates audio from text using Gemini API TTS.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=f"{self.prompt_prefix}{text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.gemini_voice
                            )
                        )
                    )
                )
            )
            
            # Extract audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Save as WAV file
            self._save_wave_file(output_file, audio_data)
            print(f"Gemini TTS audio saved to {output_file}")
            
        except Exception as e:
            print(f"Error generating audio with Gemini API: {e}")
            raise e

    def _save_wave_file(self, filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """
        Save PCM data as a WAV file.
        """
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)

    def generate_audio_sync(self, text: str, output_file: str):
        """
        Synchronous wrapper for audio generation.
        Routes to edge-tts (dev) or Gemini API (prod) based on mode.
        """
        if self.mode == "prod":
            self.generate_audio_gemini(text, output_file)
        else:
            asyncio.run(self.generate_audio(text, output_file))

