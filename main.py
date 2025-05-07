import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import argparse

from src.theme_selector import ThemeSelector
from src.question_generator import QuestionGenerator
from src.tts_engine import TTSEngine
from src.video_creator import VideoCreator
from src.storage import StorageManager
from src.srt_generator import SRTGenerator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

class VideoGenerator:
    def __init__(self):
        """
        Initialise le générateur de vidéos.
        """
        self.config = self._load_config()
        self._setup_directories()
        
        # Initialisation des composants
        self.theme_selector = ThemeSelector(config=self.config)
        self.question_generator = QuestionGenerator(num_questions=self.config["num_questions"], config=self.config)
        parser = argparse.ArgumentParser(description="Génération de vidéo")
        parser.add_argument("theme", nargs="?", help="Thème de la vidéo", default="None")
        args = parser.parse_args()
        theme = args.theme
        if theme == "None":
            theme = self.theme_selector.get_next_theme()
        self.theme = theme
        self.tts_engine = TTSEngine(config=self.config)
        self.video_creator = VideoCreator(theme=self.theme, config=self.config)
        self.storage_manager = StorageManager(config=self.config)
        self.srt_generator = SRTGenerator(config=self.config)

    def _load_config(self):
        """Charge la configuration depuis le fichier settings.json"""
        config_path = Path("config/settings.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _setup_directories(self):
        """Crée les répertoires nécessaires s'ils n'existent pas"""
        directories = [
            "assets/backgrounds",
            "assets/music",
            "temp",
            "assets/generated"
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def generate_video(self):
        """Génère une vidéo complète"""
        try:
            # 1. Sélection du thème
            theme = self.theme
            logger.info(f"Thème sélectionné : {theme}")

            # 2. Génération des questions
            questions = self.question_generator.generate_question(theme)
            logger.info(f"{len(questions)} questions générées")

            # 3. Génération des vidéos pour chaque question
            video_clips = []
            all_audio_info = []
            current_time = 0  # Pour suivre le timing des sous-titres
            
            for i, question in enumerate(questions, 1):
                logger.info(f"Traitement de la question {i}/{len(questions)}")
                
                # Génération de la voix avec les informations détaillées
                audio_info = self.tts_engine.generate_question_audio(question)
                logger.info(f"Audio généré pour la question {i}")
                
                # Ajuster les timings pour les sous-titres
                for j, info in enumerate(audio_info):
                    info['start_time'] = current_time
                    current_time += info['duration']
                    info['end_time'] = current_time
                    # Si c'est la première partie (question), ajouter la durée du timer
                    if info.get('is_question', False) and j+1 < len(audio_info) and audio_info[j+1].get('is_answer', False):
                        # Ajouter le timer à l'offset total uniquement si suivi d'une réponse
                        timer_duration = 3.0
                        current_time += timer_duration
                
                all_audio_info.extend(audio_info)
                
                # Création de la vidéo
                video_clip = self.video_creator.create_video(question, audio_info)
                video_clips.append(video_clip)
                logger.info(f"Vidéo générée pour la question {i}")

            # Génération du fichier SRT avec les bons timings
            if self.config["subtitles"]["enabled"]:
                logger.info("Génération des sous-titres...")
                
                # Utiliser WhisperX si configuré
                if self.config["subtitles"].get("use_whisperx", False):
                    srt_file = self.srt_generator.transcribe_with_timestamps(all_audio_info)
                    logger.info(f"Fichier SRT généré avec WhisperX : {srt_file}")
                else:
                    # Sinon utiliser la répartition uniforme
                    srt_file = self.srt_generator.generate_srt(all_audio_info)
                    logger.info(f"Fichier SRT généré par répartition uniforme : {srt_file}")

                # 4. Concaténation des vidéos avec les sous-titres
                final_video_path = self.video_creator.concatenate_videos(
                    video_clips=video_clips,
                    srt_file=srt_file,
                    audio_info=all_audio_info
                )
            else:
                final_video_path = self.video_creator.concatenate_videos(video_clips=video_clips)

            # 5. Sauvegarde de la vidéo
            saved_path = self.storage_manager.save_video(final_video_path)
            logger.info(f"Vidéo sauvegardée : {saved_path}")

            # Nettoyage des fichiers temporaires
            self.tts_engine.cleanup()
            self.video_creator.cleanup()

            return saved_path

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la vidéo: {str(e)}")
            raise

def main():
    try:
        generator = VideoGenerator()
        video_path = generator.generate_video()
        logger.info(f"Vidéo générée avec succès : {video_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {str(e)}")
        raise

if __name__ == "__main__":
    main()