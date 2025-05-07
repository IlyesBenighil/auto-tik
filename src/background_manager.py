from pathlib import Path
from src.image_generator import ImageGenerator
from src.video_generator import VideoGenerator


class BackgroundManager:
    def __init__(self):
        """
        Initialise le gestionnaire de fonds vidéo.
        """
        self.videos_dir = Path("assets/backgrounds/videos")
        self.videos_dir.mkdir(parents=True, exist_ok=True)
    
    def get_background(self, theme: str) -> str:
        """
        Récupère un fond vidéo aléatoire pour un thème donné.
        
        Args:
            theme (str): Le thème du fond vidéo
        """
        formatted_theme = theme.lower().replace(" ", "_")
        video_path = self.videos_dir / f"{formatted_theme}.mp4"
        
        if video_path.exists():
            return str(video_path)
        video_generator = VideoGenerator(theme)
        img_generated_path = ImageGenerator().generete_and_save_image(theme)
        return video_generator.generate_video_from_image(img_generated_path)