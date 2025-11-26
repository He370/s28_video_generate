# Gemini API Models
# Text Models Selection
# GEMINI_TEXT_MODEL = "gemini-2.5-pro-preview-03-25"
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
# GEMINI_TEXT_MODEL = "gemini-2.5-pro-preview-05-06"
# GEMINI_TEXT_MODEL = "gemini-2.5-pro-preview-06-05"
# GEMINI_TEXT_MODEL = "gemini-2.5-pro"
# GEMINI_TEXT_MODEL = "gemini-exp-1206"
# GEMINI_TEXT_MODEL = "gemini-2.0-flash-thinking-exp-01-21"
# GEMINI_TEXT_MODEL = "gemini-2.0-flash-thinking-exp"
# GEMINI_TEXT_MODEL = "gemini-2.0-flash-thinking-exp-1219"
# GEMINI_TEXT_MODEL = "learnlm-2.0-flash-experimental"
# GEMINI_TEXT_MODEL = "gemini-flash-latest"
# GEMINI_TEXT_MODEL = "gemini-flash-lite-latest"
# GEMINI_TEXT_MODEL = "gemini-pro-latest"
# GEMINI_TEXT_MODEL = "gemini-2.5-flash-lite"
# GEMINI_TEXT_MODEL = "gemini-2.5-flash-preview-09-2025"
# GEMINI_TEXT_MODEL = "gemini-2.5-flash-lite-preview-09-2025"
GEMINI_TEXT_ADVANCED_MODEL = "gemini-3-pro-preview"

# Image Models Selection
# GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"
# GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image-preview"
#GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
# GEMINI_IMAGE_MODEL = "gemini-3-pro-image-preview"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"  # nano banana
#GEMINI_IMAGE_MODEL = "imagen-4.0-fast-generate-001"
# GEMINI_IMAGE_MODEL = "imagen-3.0-generate-002"
GEMINI_IMAGE_ADVANCED_MODEL = "gemini-3-pro-image-preview"

IMAGE_STYLE_PROMPT = (
    "The style should be realistic high quality historical illustration, painting, "
    "should be detailed and suitable for a history museum display, do not include text in the image. "
    "The image should be in 16:9 aspect ratio."
)

API_DELAY_SECONDS = 1 # Fudge factor to avoid rate limits
