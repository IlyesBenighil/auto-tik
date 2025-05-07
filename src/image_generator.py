from io import BytesIO
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

class ImageGenerator:
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv(override=True)
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.output_dir = "assets/backgrounds/images"
        
    def generete_and_save_image(self, theme: str):
        prompt = f"""
        'Generate an image of an '{theme}' scene with a calm, dimly-lit yet colorful and mystical atmosphere. The environment should feel serene and enchanting, with soft glows, magical lights, and vibrant but harmonious colors. Think misty air with colorful highlights, glowing symbols, and dreamy lighting. The style should be fantasy-cinematic or surreal-realistic, combining mystery and vivid beauty.',
        """

        response = self.client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images= 1,
                aspectRatio="9:16"
            )
        )

        # Créer un nom de fichier
        clean_theme = theme.lower().replace(" ", "_")
        filename = f"{clean_theme}.png"
        output_path = f"{self.output_dir}/{filename}"

        # Sauvegarder l'image
        image = Image.open(BytesIO(response.generated_images[0].image.image_bytes))
        image.save(output_path)
        print(f"Image sauvegardée dans: {output_path}")
        return output_path