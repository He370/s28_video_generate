import json
from typing import List, Dict, Callable
from .gemini_client import GeminiClient

class ScriptGenerator:
    def __init__(self, client: GeminiClient):
        self.client = client

    def generate_script(self, context: str, language: str, category: str, word_limit: int) -> str:
        """
        Generates a video script based on the provided parameters.
        
        Args:
            context: The project context or topic.
            language: The language of the script.
            category: The story category (e.g., 'Fairy Tale', 'Horror', 'History').
            word_limit: The approximate word limit for the script.
            
        Returns:
            A string containing the generated script.
        """
        prompt = f"""
        You are a creative scriptwriter. Write a video script for the following request:
        
        Context/Topic: {context}
        Language: {language}
        Category: {category}
        Word Limit: Approximately {word_limit} words.
        
        The script should be engaging and suitable for a video narration (TTS). 
        IMPORTANT: 
        - START WITH A SHORT, EXTREMELY ENGAGING HOOK. Avoid flowery introductions or long preambles. Get straight to the point.
        - END abruptly WITH A STRONG, CONCISE CALL-TO-ACTION URGING THE AUDIENCE TO SUBSCRIBE.
        - Do not include scene directions, camera angles, or stage directions.
        - Do not include music cues like "(Intro music fades in and out)" or "(Background music)".
        - Do not include sound effects or any non-spoken text.
        - Only include the actual narration text that will be read aloud.
        - Write in a natural, conversational tone suitable for voice narration.
        """
        
        print(f"Generating script for context: {context}, category: {category}...")
        return self.client.generate_text(prompt)

    def process_script(self, script_text: str, split_prompt: str, image_prompt_generator_func: Callable[[str, int, Dict], str], debug_scene_limit: int = None) -> List[Dict[str, str]]:
        """
        Splits the generated script into paragraphs and generates image prompts for each using the provided callback.
        
        Args:
            script_text: The full text of the video script.
            split_prompt: The prompt used to split the script into scenes.
            image_prompt_generator_func: A callback function that takes (scene_text, index, scene_metadata) and returns an image prompt.
            debug_scene_limit: Optional limit on the number of scenes to generate.
            
        Returns:
            A list of dictionaries, where each dictionary contains:
            - "text": The paragraph text.
            - "image_prompt": The corresponding image generation prompt.
            - ... any other metadata returned by the split prompt
        """
        
        # Step 1: Split script into logical paragraphs/scenes
        print("Splitting script into scenes...")
        response_text = self.client.generate_text(split_prompt, response_mime_type="application/json")
        
        try:
            scenes = json.loads(response_text)
        except json.JSONDecodeError:
            print(f"Error decoding JSON response: {response_text}")
            # Fallback: treat entire script as one scene
            scenes = [{"text": script_text}]
        
        # Step 2: Generate image prompts for each scene using the callback
        print(f"Generating image prompts for {len(scenes)} scenes...")
        result = []
        for i, scene in enumerate(scenes):
            if debug_scene_limit and i >= debug_scene_limit:
                print(f"DEBUG: Limiting scenes from {len(scenes)} to {debug_scene_limit}")
                break
            scene_text = scene.get("text", "")
            if not scene_text:
                continue
            
            print(f"  Scene {i+1}/{len(scenes)}...")
            
            # Generate image prompt using the provided callback
            try:
                image_prompt = image_prompt_generator_func(scene_text, i, scene)
            except Exception as e:
                print(f"Error generating image prompt for scene {i}: {e}")
                image_prompt = "A generic image representing the scene."

            # Create result item with all scene metadata + image_prompt
            item = scene.copy()
            item["image_prompt"] = image_prompt
            result.append(item)
        
        return result if result else [{"text": script_text, "image_prompt": "A generic image representing the script."}]

