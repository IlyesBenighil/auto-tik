#!/usr/bin/env python3
"""
Script pour extraire la 3ème minute d'une vidéo.
Usage: python extract_minute.py input_video.mp4 output_video.mp4
"""

import sys
import os
from moviepy import VideoFileClip

def extract_minute(input_file, output_file, minute=3):
    """
    Extrait une minute spécifique d'une vidéo
    
    Args:
        input_file: Chemin du fichier vidéo d'entrée
        output_file: Chemin du fichier vidéo de sortie
        minute: Numéro de la minute à extraire (par défaut: 3)
    """
    try:
        # Charger la vidéo
        video = VideoFileClip(input_file)
        
        # Calculer les temps de début et de fin
        start_time = (minute - 1) * 60  # Début de la minute spécifiée
        end_time = minute * 60          # Fin de la minute spécifiée
        
        # Vérifier si la vidéo est assez longue
        if video.duration < start_time:
            print(f"La vidéo ne dure que {video.duration:.2f} secondes, ce qui est moins que {start_time} secondes.")
            sys.exit(1)
            
        # Ajuster end_time si nécessaire
        end_time = min(end_time, video.duration)
        
        # Extraire la partie voulue
        extracted_clip = video.subclipped(start_time, end_time)
        
        # Enregistrer le résultat
        extracted_clip.write_videofile(
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
        
        print(f"La {minute}ème minute a été extraite avec succès: {output_file}")
        print(f"Extrait de {start_time} à {end_time} secondes")
        
    except Exception as e:
        print(f"Erreur lors de l'extraction: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input_video.mp4 output_video.mp4")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Le fichier {input_file} n'existe pas.")
        sys.exit(1)
        
    extract_minute(input_file, output_file) 