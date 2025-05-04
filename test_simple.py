#!/usr/bin/env python3
import logging
from pathlib import Path
from moviepy.editor import ColorClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer le dossier de sortie s'il n'existe pas
output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

try:
    # Créer un clip de couleur rouge foncé
    width, height = 1080, 1920
    duration = 5  # 5 secondes
    
    # Créer un simple clip de couleur
    clip = ColorClip(size=(width, height), color=(128, 0, 0))
    clip = clip.with_duration(duration)
    
    # Définir explicitement le fps
    clip.fps = 30
    
    # Sauvegarder la vidéo
    output_path = output_dir / "test_simple.mp4"
    logger.info(f"Création de la vidéo simple: {output_path}")
    
    clip.write_videofile(
        str(output_path),
        fps=30,
        codec='libx264',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    logger.info(f"Vidéo créée avec succès: {output_path}")
    
except Exception as e:
    logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
finally:
    # Nettoyage
    if 'clip' in locals():
        clip.close() 