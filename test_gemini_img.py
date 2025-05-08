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
    prompt='A detailed hand-drawn illustration in a cozy, cottagecore illustrated style, featuring a vibrant spread of rustic food items arranged on a wooden table with a simple patterned tablecloth. The perspective is flat and slightly overhead, emphasizing the variety and texture of the food. Imagine freshly baked sourdough bread with a rich, golden crust, nestled beside a selection of ripe, jewel-toned berries – plump strawberries, blueberries, and raspberries spilling from a small woven basket. There are also jars filled with homemade preserves, their labels handwritten and charmingly imperfect, reflecting the bounty of a cottage garden. A ceramic bowl holds creamy, artisanal cheese, perhaps garnished with a sprig of rosemary or thyme. Scattered around the main items are smaller details that enhance the scene: a few fallen leaves, a single, half-eaten apple showing its crisp white flesh, and perhaps a small, slightly chipped teacup filled with steaming herbal tea. The color palette should be warm and earthy, with soft greens, muted browns, and pops of natural red, blue, and gold from the fruits and baked goods. The linework should be visible, suggesting a loving, unpretentious artistic touch, with a gentle texture that evokes the feel of paper and ink. The overall mood is one of simple abundance, tranquility, and the comforting pleasure of home-prepared food in a serene, natural setting. Sunlight streams gently from an unseen window, casting soft, diffused light across the scene, highlighting the textures of the food and the hand-drawn lines. The composition is balanced but feels natural and unposed, as if capturing a quiet moment of rural life centered around nourishment.',
    config=types.GenerateImagesConfig(
        number_of_images= 1,
    )
)
for generated_image in response.generated_images:
  image = Image.open(BytesIO(generated_image.image.image_bytes))
  image.show()