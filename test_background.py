#!/usr/bin/env python3
import logging
import os
from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip, concatenate_videoclips
import numpy as np
from pathlib import Path
from scipy.io import wavfile


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer le dossier de sortie s'il n'existe pas
output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

try:
    # Dimensions TikTok (9:16)
    width, height = 1080, 1920
    part_duration = 2.5  # 2.5 secondes par partie
    total_duration = 5  # 5 secondes au total
    
    # Créer un son simple pour les clips
    def make_beep_sound(duration):
        # Chercher des fichiers MP3 existants
        for mp3_path in [
            "assets/music/beep.mp3",
            "assets/music/notification.mp3",
        ]:
            if os.path.exists(mp3_path):
                return mp3_path
                
        # Si pas de fichier trouvé, générer un son simple
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        beep = np.sin(2 * np.pi * 440 * t) * np.where((t % 1) < 0.2, 0.5, 0)
        beep = np.int16(beep * 32767)
        temp_beep_path = output_dir / "beep.wav"
        wavfile.write(str(temp_beep_path), sample_rate, beep)
        return str(temp_beep_path)
    
    # Obtenir de la musique de fond
    def get_background_music(duration):
        # Chercher des fichiers MP3 existants
        mp3_files = list(Path("assets/music").glob("*.mp3"))
        if mp3_files:
            return str(mp3_files[0])
            
        # Sinon générer un son simple
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        sound = np.sin(2 * np.pi * 100 * t) * 0.2
        sound = np.int16(sound * 32767)
        temp_sound_path = output_dir / "background_sound.wav"
        wavfile.write(str(temp_sound_path), sample_rate, sound)
        return str(temp_sound_path)
    
    # Charger ou générer les fichiers audio
    audio_path1 = get_background_music(part_duration)
    audio_path2 = get_background_music(part_duration)
    
    # Fonds de couleur pour les deux parties
    color1 = ColorClip(size=(width, height), color=(50, 50, 100))  # Bleu foncé
    color1 = color1.with_duration(part_duration)
    
    color2 = ColorClip(size=(width, height), color=(100, 50, 50))  # Rouge foncé
    color2 = color2.with_duration(part_duration)
    
    # Textes pour les deux parties
    text1 = TextClip(
        text="Partie 1",
        font_size=100,
        color="white",
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    )
    text1 = text1.with_position(('center', 'center')).with_duration(part_duration)
    
    text2 = TextClip(
        text="Partie 2",
        font_size=100,
        color="yellow",
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    )
    text2 = text2.with_position(('center', 'center')).with_duration(part_duration)
    
    # Créer les deux clips composites
    audio1 = AudioFileClip(audio_path1)
    clip1 = CompositeVideoClip([color1, text1], size=(width, height))
    clip1 = clip1.with_audio(audio1)
    clip1.fps = 30  # Important!
    
    # audio2 = AudioFileClip(audio_path2)
    # clip2 = CompositeVideoClip([color2, text2], size=(width, height))
    # clip2 = clip2.with_audio(audio2)
    # clip2.fps = 30  # Important!
    
    # CONCATÉNATION des clips - c'est ici que les clips sont mis bout à bout
    logger.info("Concaténation des clips vidéo...")
    final_clip = concatenate_videoclips([clip1])
    final_clip.fps = 30  # Important!
    
    # Écrire la vidéo finale
    output_path = output_dir / "test_concatenate.mp4"
    logger.info(f"Création de la vidéo concaténée: {output_path}")
    
    final_clip.write_videofile(
        str(output_path),
        fps=30,
        codec='libx264',
        audio_codec='aac',
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
    for var in ['clip1', 'clip2', 'final_clip', 'audio1', 'audio2']:
        if var in locals():
            try:
                locals()[var].close()
            except:
                pass 