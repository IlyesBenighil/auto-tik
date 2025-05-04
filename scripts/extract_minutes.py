#!/usr/bin/env python3
"""
Script pour extraire les premières minutes d'une vidéo et appliquer un flou.
Usage: python extract_minutes.py input_video.mp4 output_video.mp4 3
Le dernier paramètre est le nombre de minutes à extraire (par défaut: 3).
"""

import sys
import os
from moviepy import VideoFileClip
import numpy as np
from scipy.ndimage import gaussian_filter

def blur_frame(frame, sigma=3):
    """
    Applique un flou gaussien à une image
    
    Args:
        frame: Image à flouter (array numpy)
        sigma: Intensité du flou (par défaut: 3)
    
    Returns:
        Array numpy avec l'image floutée
    """
    # Appliquer le flou gaussien à chaque canal de couleur
    frame_blurred = np.zeros_like(frame)
    for i in range(3):  # RGB
        frame_blurred[:, :, i] = gaussian_filter(frame[:, :, i], sigma=sigma)
    return frame_blurred

def extract_minutes(input_file, output_file, minutes=3, blur_intensity=5):
    """
    Extrait les premières minutes d'une vidéo et applique un flou
    
    Args:
        input_file: Chemin du fichier vidéo d'entrée
        output_file: Chemin du fichier vidéo de sortie
        minutes: Nombre de minutes à extraire (par défaut: 3)
        blur_intensity: Intensité du flou (par défaut: 5)
    """
    try:
        # Charger la vidéo
        video = VideoFileClip(input_file)
        
        # Calculer le temps de fin
        end_time = minutes * 60  # Fin en secondes
        
        # Vérifier si la vidéo est assez longue
        if video.duration < 60:
            print(f"Attention: La vidéo ne dure que {video.duration:.2f} secondes, ce qui est moins d'une minute.")
            
        # Ajuster end_time si nécessaire
        end_time = min(end_time, video.duration)
        
        # Extraire la partie voulue
        extracted_clip = video.subclipped(0, end_time)
        
        # Appliquer le flou
        print(f"Application du flou avec intensité {blur_intensity}...")
        
        # Créer une fonction pour lire et appliquer le flou à chaque image
        def make_frame_blurred(t):
            # Obtenir l'image à l'instant t
            frame = extracted_clip.get_frame(t)
            # Appliquer le flou
            return blur_frame(frame, sigma=blur_intensity)
        
        # Créer un nouveau clip avec les images floutées
        from moviepy import VideoClip
        blurred_clip = VideoClip(make_frame_blurred, duration=extracted_clip.duration)
        
        # Conserver l'audio du clip original
        if extracted_clip.audio is not None:
            blurred_clip = blurred_clip.with_audio(extracted_clip.audio)
        
        # Définir le fps du clip flouté
        blurred_clip.fps = extracted_clip.fps
        
        # Enregistrer le résultat
        blurred_clip.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='ultrafast',
            threads=4
        )
        
        # Nettoyage
        video.close()
        extracted_clip.close()
        blurred_clip.close()
        
        minutes_extraites = end_time / 60
        print(f"Les {minutes_extraites:.1f} premières minutes ont été extraites et floutées avec succès: {output_file}")
        print(f"Extrait de 0 à {end_time} secondes")
        
    except Exception as e:
        print(f"Erreur lors de l'extraction: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input_video.mp4 output_video.mp4 [minutes] [blur_intensity]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Nombre de minutes optionnel
    minutes = 3  # Par défaut
    if len(sys.argv) > 3:
        try:
            minutes = int(sys.argv[3])
            if minutes <= 0:
                print("Le nombre de minutes doit être positif.")
                sys.exit(1)
        except ValueError:
            print("Le nombre de minutes doit être un entier.")
            sys.exit(1)
    
    # Intensité du flou optionnelle
    blur_intensity = 5  # Par défaut
    if len(sys.argv) > 4:
        try:
            blur_intensity = int(sys.argv[4])
            if blur_intensity <= 0:
                print("L'intensité du flou doit être positive.")
                sys.exit(1)
        except ValueError:
            print("L'intensité du flou doit être un entier.")
            sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"Le fichier {input_file} n'existe pas.")
        sys.exit(1)
        
    extract_minutes(input_file, output_file, minutes, blur_intensity) 