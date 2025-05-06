#!/usr/bin/env python3
import logging
import os
import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip, VideoClip, concatenate_videoclips, concatenate_audioclips

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer le dossier de sortie s'il n'existe pas
output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

class TimerAnimationDemo:
    def __init__(self):
        # Dimensions TikTok (9:16)
        self.width = 1080
        self.height = 1920
        self.fps = 30
        self.timer_duration = 3.0  # Durée du timer en secondes
        self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        # Trouver un fichier audio de tick adapté
        self.tick_sound = self.find_tick_sound()
        
    def find_tick_sound(self):
        """Recherche un fichier audio de tick dans le projet"""
        paths_to_check = [
            "assets/sound_effects/beep_10.wav",
            "assets/sound_effects/tick.wav",
            "assets/sound_effects/beep.wav"
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                return path
                
        # Si aucun fichier trouvé, retourne None
        logger.warning("Aucun fichier audio de tick trouvé")
        return None
    
    def create_sliding_bar_timer(self):
        """Timer avec une barre qui se remplit horizontalement"""
        logger.info("Création du timer avec barre de progression...")
        
        # Paramètres de la barre
        bar_width = int(self.width * 0.8)  # 80% de la largeur de l'écran
        bar_height = 80
        
        # Couleurs modernes et attrayantes
        bar_bg_color = (40, 44, 52, 180)  # Fond gris foncé semi-transparent
        bar_color = (86, 182, 194, 255)  # Bleu turquoise
        border_color = (248, 248, 242, 200)  # Bordure blanche légère
        text_color = (248, 248, 242, 255)  # Texte blanc
        
        # Effet de lueur
        glow_color = (86, 182, 194, 100)  # Lueur turquoise
        
        # Position de la barre
        bar_x = (self.width - bar_width) // 2
        bar_y = int(self.height * 0.45)
        
        # On va créer une séquence d'images
        bar_frames = []
        frames_per_second = self.fps
        total_frames = int(self.timer_duration * frames_per_second)
        
        for frame in range(total_frames):
            # Pourcentage de progression
            progress = frame / total_frames
            
            # Créer une image PIL transparente
            img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Ajouter un flou de fond (effet vignette)
            # Dessiner un rectangle arrondi noir semi-transparent plus grand
            vignette_width = bar_width + 80
            vignette_height = bar_height + 200
            vignette_x = (self.width - vignette_width) // 2
            vignette_y = bar_y - 100
            
            # Créer un rectangle avec coins arrondis pour la vignette
            for offset in range(20, 0, -1):
                opacity = 5 + offset
                draw.rounded_rectangle(
                    [(vignette_x - offset, vignette_y - offset),
                     (vignette_x + vignette_width + offset, vignette_y + vignette_height + offset)],
                    radius=30,
                    fill=(0, 0, 0, opacity)
                )
            
            # Dessiner l'arrière-plan de la barre avec des coins arrondis
            draw.rounded_rectangle(
                [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
                radius=bar_height // 2,  # Coins parfaitement arrondis
                fill=bar_bg_color,
                outline=border_color,
                width=3
            )
            
            # Effet de lueur derrière la barre de progression
            for offset in range(10, 0, -1):
                opacity = 10 + offset * 3
                filled_width = int(bar_width * (1 - progress))
                if filled_width > 0:
                    draw.rounded_rectangle(
                        [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
                        radius=bar_height // 2,
                        fill=(glow_color[0], glow_color[1], glow_color[2], opacity)
                    )
            
            # Dessiner la barre de progression qui se vide de gauche à droite
            filled_width = int(bar_width * (1 - progress))
            if filled_width > 0:
                draw.rounded_rectangle(
                [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
                    radius=bar_height // 2,
                fill=bar_color
            )
            
            # Ajouter le texte du compte à rebours
            time_left = int(self.timer_duration - (frame/frames_per_second))
            font_size = 70
            font = ImageFont.truetype(self.font_path, font_size)
            
            # Effet de texte avec ombre
            shadow_offset = 3
            draw.text(
                (self.width // 2 + shadow_offset, bar_y + bar_height // 2 + shadow_offset),
                str(time_left + 1),
                fill=(0, 0, 0, 150),  # Ombre noire semi-transparente
                font=font,
                anchor="mm"
            )
            
            # Texte principal
            draw.text(
                (self.width // 2, bar_y + bar_height // 2),
                str(time_left + 1),
                fill=text_color,
                font=font,
                anchor="mm",
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255)
            )
            
            # Ajouter une étiquette "secondes"
            label_font_size = 30
            label_font = ImageFont.truetype(self.font_path, label_font_size)
            draw.text(
                (self.width // 2, bar_y + bar_height + 40),
                "secondes",
                fill=(text_color[0], text_color[1], text_color[2], 180),
                font=label_font,
                anchor="mm"
            )
            
            # Convertir l'image PIL en array NumPy avec le mode correct
            img = img.convert("RGB")
            bar_img = np.array(img)
            bar_frames.append(bar_img)
        
        # Créer une fonction pour retourner l'image correspondant à chaque frame
        def make_frame(t):
            frame_idx = min(int(t * frames_per_second), len(bar_frames) - 1)
            return bar_frames[frame_idx]
        
        # Créer un clip à partir des images
        bar_clip = VideoClip(make_frame, duration=self.timer_duration)
        bar_clip.fps = self.fps
        
        # Ajout du son de tick
        if self.tick_sound:
            tick_audio = AudioFileClip(self.tick_sound)
            # S'assurer que l'audio est de la bonne durée
            if tick_audio.duration < self.timer_duration:
                # Créer une boucle audio manuelle
                repeats = int(np.ceil(self.timer_duration / tick_audio.duration))
                tick_audio = concatenate_audioclips([tick_audio] * repeats).subclipped(0, self.timer_duration)
            else:
                # Couper l'audio si trop long
                tick_audio = tick_audio.subclipped(0, self.timer_duration)
            bar_clip = bar_clip.with_audio(tick_audio)
        
        return bar_clip
    
    def create_demo_video(self):
        """Créer une vidéo de démonstration avec le timer personnalisé"""
        logger.info("Création de la vidéo de démonstration...")
        
        # Créer le timer
        timer_clip = self.create_sliding_bar_timer()
            
            # Fond noir pour le timer
            timer_bg = ColorClip(
                size=(self.width, self.height),
                color=(0, 0, 0)
            ).with_duration(timer_clip.duration)
            
            # Combiner le fond et le timer
            complete_timer_clip = CompositeVideoClip([timer_bg, timer_clip], size=(self.width, self.height))
            complete_timer_clip.fps = self.fps
        
        # Chemin du fichier de sortie
        output_path = str(output_dir / "timer_animation_demo.mp4")
        
        # Exporter la vidéo
        logger.info(f"Export de la vidéo vers {output_path}...")
        complete_timer_clip.write_videofile(output_path, fps=self.fps, codec="libx264", audio_codec="aac")
        
        logger.info("Vidéo de démonstration créée avec succès!")
        return output_path

if __name__ == "__main__":
    demo = TimerAnimationDemo()
    output_path = demo.create_demo_video()
    logger.info(f"Vidéo créée: {output_path}")
