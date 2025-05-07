import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

load_dotenv(override=True)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='Generate an image of an ecole au japon scene with a calm, dimly-lit yet colorful and mystical atmosphere. The environment should feel serene and enchanting, with soft glows, magical lights, and vibrant but harmonious colors. Think misty air with colorful highlights, glowing symbols, and dreamy lighting. The style should be fantasy-cinematic or surreal-realistic, combining mystery and vivid beauty.',
    config=types.GenerateImagesConfig(
        number_of_images= 1,
    )
)
for generated_image in response.generated_images:
  image = Image.open(BytesIO(generated_image.image.image_bytes))
  image.show()