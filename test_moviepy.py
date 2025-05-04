#!/usr/bin/env python3
import logging
from pathlib import Path

from moviepy import ColorClip, CompositeVideoClip, TextClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer le dossier de sortie s'il n'existe pas
output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

try:
    # 1. Créer un clip de base (fond noir)
    width, height = 1080, 1920
    background = ColorClip(size=(width, height), color=(0, 0, 0))
    background = background.with_duration(5)  # 5 secondes
    
    # 2. Créer un texte simple
    text = TextClip(
        text="Test MoviePy",
        font_size=70,
        color="white",
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    )
    text = text.with_position(('center', 'center')).with_duration(5)
    
    # 3. Combiner les clips
    final_clip = CompositeVideoClip([background, text], size=(width, height))
    
    # 4. Définir le fps explicitement
    final_clip.fps = 30
    
    # 5. Écrire la vidéo
    output_path = output_dir / "test_video.mp4"
    logger.info(f"Création de la vidéo de test: {output_path}")
    
    final_clip.write_videofile(
        str(output_path),
        fps=30,  # Spécifié explicitement ici aussi
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    logger.info(f"Vidéo créée avec succès: {output_path}")
    
except Exception as e:
    logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
finally:
    # Nettoyage
    if 'final_clip' in locals():
        final_clip.close() 