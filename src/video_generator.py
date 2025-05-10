from scripts.zoom_effect import ZoomEffect

class VideoGenerator:
    def __init__(self, theme: str):
        # Chargement des variables d'environnement
        self.output_dir = "assets/backgrounds/videos"
        self.clean_theme = theme.lower().replace(" ", "_")
    def generate_video_from_image(self, img_path: str):
        zoom_effect = ZoomEffect()
        return zoom_effect.create_zoom_video(
            image_path=img_path,
            output_path=self.output_dir + '/' + self.clean_theme + '.mp4',
            duration=120,
            zoom_factor=1.1,
            fps=30,
            blur=0,
            width=1080,
            height=1920,
            movement=0.1,
            movement_type="none",
            zoom_time=10
            )