import os
import argparse
from pathlib import Path
from moviepy import VideoFileClip, CompositeVideoClip, ColorClip
import numpy as np
from PIL import Image, ImageFilter

def blur_frame(frame, blur_radius=10):
    """Applique un flou à une image (frame)"""
    img = Image.fromarray(frame)
    img_blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return np.array(img_blurred)

def process_video(input_path, output_path, start_time=0, end_time=None, blur_background=False, blur_radius=10):
    """
    Traite une vidéo pour TikTok:
    - Redimensionne au format 9:16
    - Ajoute un flou en arrière-plan si nécessaire
    - Coupe la vidéo aux temps spécifiés
    
    Args:
        input_path: Chemin de la vidéo d'entrée
        output_path: Chemin de la vidéo de sortie
        start_time: Temps de début en secondes
        end_time: Temps de fin en secondes (None pour utiliser toute la vidéo)
        blur_background: Ajouter un flou en arrière-plan
        blur_radius: Rayon du flou (plus élevé = plus flou)
    """
    # Charger la vidéo
    clip = VideoFileClip(input_path)
    
    # Couper la vidéo si nécessaire
    if end_time is None:
        end_time = clip.duration
    
    clip = clip.subclipped(start_time, end_time)
    
    # Dimensions TikTok (9:16)
    tiktok_width = 1080
    tiktok_height = 1920
    
    # Obtenir les dimensions originales
    orig_width, orig_height = clip.size
    
    # Calculer les ratios
    width_ratio = tiktok_width / orig_width
    height_ratio = tiktok_height / orig_height
    
    # Choisir le ratio qui préserve l'aspect tout en remplissant l'écran
    if width_ratio > height_ratio:
        # La vidéo sera plus large que haute
        new_width = tiktok_width
        new_height = int(orig_height * width_ratio)
        resize_ratio = width_ratio
    else:
        # La vidéo sera plus haute que large
        new_width = int(orig_width * height_ratio)
        new_height = tiktok_height
        resize_ratio = height_ratio
    
    # Redimensionner la vidéo
    resized_clip = clip.resized(resize_ratio)
    
    # Calculer les positions pour centrer
    pos_x = (tiktok_width - new_width) // 2
    pos_y = (tiktok_height - new_height) // 2
    
    final_clip = None
    
    if blur_background and (new_width < tiktok_width or new_height < tiktok_height):
        # Créer une version floutée de la vidéo pour l'arrière-plan
        blurred_clip = clip.resized((tiktok_width, tiktok_height)).fl_image(
            lambda frame: blur_frame(frame, blur_radius)
        )
        
        # Combiner la vidéo floutée et la vidéo redimensionnée
        final_clip = CompositeVideoClip(
            [blurred_clip, resized_clip.with_position((pos_x, pos_y))],
            size=(tiktok_width, tiktok_height)
        )
    else:
        # Créer un fond noir
        bg_clip = ColorClip(
            size=(tiktok_width, tiktok_height),
            color=(0, 0, 0),
            duration=clip.duration
        )
        
        # Combiner le fond et la vidéo redimensionnée
        final_clip = CompositeVideoClip(
            [bg_clip, resized_clip.with_position((pos_x, pos_y))],
            size=(tiktok_width, tiktok_height)
        )
    
    # Définir la fréquence d'images
    final_clip.fps = clip.fps if clip.fps else 30
    
    # Exporter la vidéo
    final_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4
    )
    
    # Fermer les clips pour libérer les ressources
    clip.close()
    final_clip.close()
    if 'blurred_clip' in locals():
        blurred_clip.close()
    if 'resized_clip' in locals():
        resized_clip.close()

def main():
    parser = argparse.ArgumentParser(description="Traitement de vidéo pour TikTok")
    parser.add_argument("input", help="Chemin de la vidéo d'entrée")
    parser.add_argument("-o", "--output", help="Chemin de la vidéo de sortie (par défaut: input_tiktok.mp4)")
    parser.add_argument("-s", "--start", type=float, default=0, help="Temps de début en secondes")
    parser.add_argument("-e", "--end", type=float, help="Temps de fin en secondes")
    parser.add_argument("-b", "--blur", action="store_true", help="Ajouter un flou en arrière-plan")
    parser.add_argument("-r", "--radius", type=int, default=10, help="Rayon du flou (défaut: 10)")
    
    args = parser.parse_args()
    
    # Définir le chemin de sortie s'il n'est pas spécifié
    if not args.output:
        input_path = Path(args.input)
        output_path = str(input_path.parent / f"{input_path.stem}_tiktok{input_path.suffix}")
    else:
        output_path = args.output
    
    print(f"Traitement de la vidéo: {args.input}")
    print(f"Sortie: {output_path}")
    print(f"Temps de début: {args.start} secondes")
    print(f"Temps de fin: {args.end if args.end else 'fin de la vidéo'} secondes")
    print(f"Flou en arrière-plan: {'Oui' if args.blur else 'Non'}")
    if args.blur:
        print(f"Rayon du flou: {args.radius}")
    
    process_video(
        args.input,
        output_path,
        args.start,
        args.end,
        args.blur,
        args.radius
    )
    
    print(f"Traitement terminé. Vidéo sauvegardée: {output_path}")

if __name__ == "__main__":
    main() 