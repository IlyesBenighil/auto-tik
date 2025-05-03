import os
import logging
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        """
        Initialise le moteur TTS avec Google Cloud Text-to-Speech.
        """
        load_dotenv(override=True)
        
        # Vérification des credentials Google Cloud
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError("Les credentials Google Cloud ne sont pas définis. Veuillez définir la variable d'environnement GOOGLE_APPLICATION_CREDENTIALS")
        
        self.client = texttospeech.TextToSpeechClient()
        self.temp_dir = Path("assets/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration de la voix française
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="fr-FR",
            name="fr-FR-Chirp3-HD-Orus",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        # Configuration de l'audio
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
    def generate_question_audio(self, question_data: Dict) -> List[str]:
        """
        Génère les fichiers audio pour une question.
        
        Args:
            question_data (Dict): Les données de la question
            
        Returns:
            List[str]: Liste des chemins des fichiers audio générés
        """
        try:
            # Construction du texte complet
            text = f"{question_data['question']}\n\n"
            for i in range(1, 5):
                text += f"Choix {i} : {question_data['choices'][str(i)]}\n"
            text += f"\nLa réponse est : {question_data['choices'][question_data['answer']]}"
            
            # Génération de l'audio
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            # Sauvegarde de l'audio
            audio_path = self.temp_dir / "question.mp3"
            with open(audio_path, "wb") as out:
                out.write(response.audio_content)
            
            return [str(audio_path)]
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'audio: {str(e)}")
            raise
            
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        try:
            for file in self.temp_dir.glob("*.mp3"):
                file.unlink()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temporaires: {str(e)}") 