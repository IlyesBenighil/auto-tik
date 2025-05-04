#!/usr/bin/env python3
"""
Script pour réduire le volume d'un fichier MP3 de 90%.
Usage: python reduce_volume.py input.mp3 output.mp3
"""

import sys
import os
from pydub import AudioSegment

def reduce_volume(input_file, output_file, volume_reduction=0.9):
    """
    Réduit le volume d'un fichier audio
    
    Args:
        input_file: Chemin du fichier MP3 d'entrée
        output_file: Chemin du fichier MP3 de sortie
        volume_reduction: Pourcentage de réduction (0.9 = 90% de réduction)
    """
    try:
        # Charger le fichier audio
        audio = AudioSegment.from_file(input_file)
        
        # Calculer la réduction en dB (logarithmique)
        # Une réduction de 90% équivaut environ à -20dB
        db_reduction = -20 if volume_reduction >= 0.9 else 20 * (1 - volume_reduction - 1)
        
        # Appliquer la réduction de volume
        reduced_audio = audio + db_reduction
        
        # Exporter le résultat
        reduced_audio.export(output_file, format="mp3")
        
        print(f"Le fichier a été traité avec succès: {output_file}")
        
    except Exception as e:
        print(f"Erreur lors du traitement: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input.mp3 output.mp3")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Le fichier {input_file} n'existe pas.")
        sys.exit(1)
        
    reduce_volume(input_file, output_file) 