import json
from typing import Dict, List, Optional
from .gemini_client import GeminiClient

class MetadataGenerator:
    def __init__(self, client: GeminiClient):
        self.client = client

    def generate_metadata(self, script: str, topic: str, date: Optional[str] = None, style: Optional[str] = None, extra_requirements: Optional[str] = None, default_tags: List[str] = None, default_description: str = "Generated video.") -> Dict[str, str]:
        """
        Generates YouTube title, description, and tags based on the video script.
        
        Args:
            script: The full text of the video script.
            topic: The main topic of the video.
            date: Optional date context (e.g., "November 25").
            style: Optional style context.
            extra_requirements: Optional specific requirements for the metadata.
            
        Returns:
            Dict containing 'title', 'description', and 'tags'.
        """
        print("Generating YouTube metadata...")
        
        context_info = f"Topic: {topic}"
        if date:
            context_info += f"\nDate: {date}"
            
        requirements_text = ""
        if extra_requirements:
            requirements_text = f"\n        Specific Requirement: {extra_requirements}"

        prompt = f"""
        Based on the following video script about "{topic}", generate optimized YouTube metadata.
        
        Context:
        {context_info}
        
        Script:
        {script[:2000]}... (truncated)
        
        Requirements:
        1. Title: Catchy, click-worthy, under 100 characters.{requirements_text}
        2. Description: Engaging summary, 2-3 sentences max.
        3. Tags: 5-8 relevant, high-traffic keywords, comma-separated tags for YouTube.
        
        Output strictly in JSON format:
        {{
            "title": "Your Title Here",
            "description": "Your Description Here",
            "tags": "tag1,tag2,tag3"
        }}
        """
        
        try:
            response = self.client.generate_text(prompt, response_mime_type="application/json")
            metadata = json.loads(response)
            
            # Ensure tags is a list if it came back as a string
            tags_raw = metadata.get("tags", "")
            if isinstance(tags_raw, str):
                tags_list = [t.strip() for t in tags_raw.split(',')]
            elif isinstance(tags_raw, list):
                tags_list = tags_raw
            else:
                tags_list = []
                
            # Clean up tags (remove empty strings)
            tags_list = [t for t in tags_list if t]
            
            return {
                "title": metadata.get("title", f"Video about {topic}"),
                "description": metadata.get("description", "Generated video."),
                "tags": tags_list
            }
            
        except Exception as e:
            print(f"Error generating metadata: {e}")
            return {
                "title": f"Video about {topic}",
                "description": default_description,
                "tags": default_tags if default_tags else ["generated", "ai"]
            }
