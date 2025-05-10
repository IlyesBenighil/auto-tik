#!/usr/bin/env python3
import argparse
import os
import numpy as np
from PIL import Image, ImageFilter
import cv2
import math

class ZoomEffect:
    def __init__(self):
        print("ZoomEffect init")
    def create_zoom_video(self,image_path, output_path, duration=5.0, zoom_factor=1.5, fps=30, 
                          blur=0, width=1080, height=1920, movement=0.1, movement_type="circle",
                          zoom_time=0.5):
        """
        Crée une vidéo avec un effet de zoom progressif sur une image et un mouvement léger.

        Args:
            image_path (str): Chemin de l'image source
            output_path (str): Chemin de sortie pour la vidéo
            duration (float): Durée de la vidéo en secondes
            zoom_factor (float): Facteur de zoom final (1.0 = pas de zoom, 2.0 = zoom x2)
            fps (int): Images par seconde
            blur (int): Intensité du flou (constant) à appliquer (0 = pas de flou)
            width (int): Largeur de la vidéo
            height (int): Hauteur de la vidéo
            movement (float): Intensité du mouvement (0 = pas de mouvement, 1 = mouvement maximal)
            movement_type (str): Type de mouvement ("circle", "horizontal", "vertical", "diagonal", "random")
            zoom_time (float): Temps de zoom en secondes (durée d'un cycle zoom/dézoom)
        """

        # Vérifier que le fichier image existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"L'image {image_path} n'existe pas")

        # Charger l'image
        original_image = Image.open(image_path)

        # Redimensionner l'image pour correspondre aux dimensions de la vidéo
        # tout en préservant les proportions
        img_ratio = original_image.width / original_image.height
        video_ratio = width / height

        if img_ratio > video_ratio:  # Image plus large que la vidéo
            new_height = original_image.height
            new_width = int(new_height * video_ratio)
            offset_x = (original_image.width - new_width) // 2
            offset_y = 0
            original_image = original_image.crop((offset_x, offset_y, offset_x + new_width, offset_y + new_height))
        else:  # Image plus haute que la vidéo
            new_width = original_image.width
            new_height = int(new_width / video_ratio)
            offset_x = 0
            offset_y = (original_image.height - new_height) // 2
            original_image = original_image.crop((offset_x, offset_y, offset_x + new_width, offset_y + new_height))

        # Redimensionner à la taille de la vidéo avec une marge pour le mouvement
        # Ajouter une marge plus grande pour que le mouvement ne révèle pas les bords
        movement_margin = int(max(width, height) * movement * 0.5)
        enlarged_width = width + movement_margin * 2
        enlarged_height = height + movement_margin * 2

        # Redimensionner l'image avec la marge supplémentaire
        original_image = original_image.resize((enlarged_width, enlarged_height), Image.LANCZOS)

        # Appliquer le flou constant si nécessaire
        if blur > 0:
            original_image = original_image.filter(ImageFilter.GaussianBlur(radius=blur))

        # Convertir l'image PIL en tableau NumPy pour OpenCV
        original_array = np.array(original_image)

        # Convertir RGB à BGR pour OpenCV si l'image a 3 canaux (RGB)
        if len(original_array.shape) == 3 and original_array.shape[2] == 3:
            original_array = original_array[:, :, ::-1]  # Inverser les canaux RGB -> BGR

        # Calculer le nombre total de frames
        num_frames = int(duration * fps)

        # Créer l'objet VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Fonction pour calculer le zoom avec effet de rebond
        def calculate_zoom(progress, frame_index):
            # Calculer le nombre de cycles de zoom complets
            cycles = duration / zoom_time
            # Calculer la position dans le cycle actuel
            cycle_progress = (progress * cycles) % 1.0
            # Utiliser une fonction sinusoïdale pour créer l'effet de rebond
            zoom_progress = abs(math.sin(cycle_progress * math.pi))
            # Appliquer le facteur de zoom
            return 1.0 + zoom_progress * (zoom_factor - 1.0)

        # Fonction pour calculer le déplacement selon le type de mouvement
        def calculate_movement(progress, frame_index):
            # Intensité du mouvement ajustée pour la marge disponible
            max_offset_x = movement_margin
            max_offset_y = movement_margin

            if movement_type == "circle":
                # Mouvement circulaire
                angle = progress * 2 * math.pi  # Compléter un cercle sur la durée
                offset_x = max_offset_x * math.cos(angle)
                offset_y = max_offset_y * math.sin(angle)
            elif movement_type == "horizontal":
                # Mouvement horizontal (aller-retour)
                offset_x = max_offset_x * math.sin(progress * math.pi * 2)
                offset_y = 0
            elif movement_type == "vertical":
                # Mouvement vertical (aller-retour)
                offset_x = 0
                offset_y = max_offset_y * math.sin(progress * math.pi * 2)
            elif movement_type == "diagonal":
                # Mouvement diagonal (coin à coin)
                offset_x = max_offset_x * math.sin(progress * math.pi * 2)
                offset_y = max_offset_y * math.sin(progress * math.pi * 2)
            elif movement_type == "random":
                # Mouvement semi-aléatoire doux (utiliser une fonction de bruit ou une interpolation pourrait être mieux)
                # On utilise des fréquences différentes pour X et Y pour éviter un mouvement trop régulier
                offset_x = max_offset_x * math.sin(progress * math.pi * 2.5 + 0.4)
                offset_y = max_offset_y * math.sin(progress * math.pi * 1.7 + 0.9)
            else:
                # Par défaut, pas de mouvement
                offset_x = 0
                offset_y = 0

            return offset_x, offset_y

        # Génération des frames et écriture directe dans le fichier vidéo
        for i in range(num_frames):
            # Afficher la progression tous les 10% ou toutes les 100 frames
            if i % max(1, num_frames // 10) == 0 or i % 100 == 0:
                print(f"Progression: {i}/{num_frames} frames ({i/num_frames*100:.1f}%)")

            # Calculer le zoom pour cette frame avec effet de rebond
            progress = i / num_frames
            current_zoom = calculate_zoom(progress, i)

            # Calculer le mouvement pour cette frame
            offset_x, offset_y = calculate_movement(progress, i)

            # Calculer les nouvelles dimensions pour le zoom
            new_w = int(enlarged_width * current_zoom)
            new_h = int(enlarged_height * current_zoom)

            # Redimensionner l'image avec OpenCV
            resized = cv2.resize(original_array, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

            # Calculer les offsets pour centrer le zoom (en tenant compte du mouvement)
            # Les offsets sont calculés pour centrer la frame dans la dimension agrandie
            center_x = (new_w - width) // 2
            center_y = (new_h - height) // 2

            # Ajouter le décalage de mouvement
            adjusted_x = int(center_x + offset_x * current_zoom)
            adjusted_y = int(center_y + offset_y * current_zoom)

            # S'assurer que les offsets restent dans les limites de l'image redimensionnée
            adjusted_x = max(0, min(adjusted_x, new_w - width))
            adjusted_y = max(0, min(adjusted_y, new_h - height))

            # Extraire la région avec le zoom et le mouvement appliqués
            cropped = resized[adjusted_y:adjusted_y + height, adjusted_x:adjusted_x + width]

            # Écrire la frame dans la vidéo
            video_writer.write(cropped)

        # Libérer les ressources
        video_writer.release()

        print(f"Vidéo créée avec succès: {output_path}")

        # Conversion du format de la vidéo si nécessaire (OpenCV utilise MPEG-4 qui peut ne pas être compatible avec tous les lecteurs)
        try:
            import subprocess
            temp_output = output_path + ".temp.mp4"
            os.rename(output_path, temp_output)

            # Utiliser FFmpeg pour convertir en format plus compatible
            cmd = [
                "ffmpeg", "-y", "-i", temp_output, 
                "-c:v", "libx264", "-preset", "ultrafast", 
                "-pix_fmt", "yuv420p", output_path
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Supprimer le fichier temporaire
            os.remove(temp_output)
            print(f"Conversion terminée: {output_path}")
        except Exception as e:
            # En cas d'échec, restaurer la vidéo originale
            if os.path.exists(temp_output):
                os.rename(temp_output, output_path)

        return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crée une vidéo avec effet de zoom et mouvement à partir d'une image")
    parser.add_argument("image", help="Chemin vers l'image source")
    parser.add_argument("--output", "-o", help="Chemin de sortie pour la vidéo (défaut: zoom_output.mp4)", default="zoom_output.mp4")
    parser.add_argument("--duration", "-d", type=float, help="Durée de la vidéo en secondes (défaut: 5.0)", default=5.0)
    parser.add_argument("--zoom", "-z", type=float, help="Facteur de zoom final (défaut: 1.5)", default=1.5)
    parser.add_argument("--fps", "-f", type=int, help="Images par seconde (défaut: 30)", default=30)
    parser.add_argument("--blur", "-b", type=int, help="Intensité du flou constant (défaut: 0, pas de flou)", default=0)
    parser.add_argument("--width", "-W", type=int, help="Largeur de la vidéo (défaut: 1080)", default=1080)
    parser.add_argument("--height", "-H", type=int, help="Hauteur de la vidéo (défaut: 1920)", default=1920)
    parser.add_argument("--movement", "-m", type=float, help="Intensité du mouvement (défaut: 0.1, 0=aucun, 1=max)", default=0.1)
    parser.add_argument("--movement-type", "-mt", help="Type de mouvement (défaut: circle)", 
                       choices=["circle", "horizontal", "vertical", "diagonal", "random", "none"], default="circle")
    parser.add_argument("--zoom-time", "-zt", type=float, help="Temps de zoom en secondes (défaut: 0.5)", default=0.5)

    args = parser.parse_args()

    zoom_effect = ZoomEffect()
    zoom_effect.create_zoom_video(
        args.image, 
        args.output, 
        duration=args.duration, 
        zoom_factor=args.zoom, 
        fps=args.fps,
        blur=args.blur,
        width=args.width,
        height=args.height,
        movement=args.movement,
        movement_type=args.movement_type,
        zoom_time=args.zoom_time
    )
