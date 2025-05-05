import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.theme_selector import ThemeSelector
from src.question_generator import QuestionGenerator
from src.tts_engine import TTSEngine
from src.video_creator import VideoCreator
from src.storage import StorageManager

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
        self.theme = self.theme_selector.get_next_theme()
        self.tts_engine = TTSEngine(config=self.config)
        self.video_creator = VideoCreator(theme=self.theme, config=self.config)
        self.storage_manager = StorageManager(config=self.config)

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
            "assets/temp",
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
            small_video_objects = []
            for i, question in enumerate(questions, 1):
                logger.info(f"Traitement de la question {i}/{len(questions)}")
                
                # Génération de la voix
                audio_files = self.tts_engine.generate_question_audio(question)
                logger.info(f"Audio généré pour la question {i}")
                
                # Création de la vidéo
                small_video_objects.append(self.video_creator.create_video(question, audio_files))

            # 4. Concaténation des vidéos
            final_video_path = self.video_creator.concatenate_videos(video_clips=small_video_objects)

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