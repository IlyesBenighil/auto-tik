import os
import logging
import time
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self, config: dict):
        """
        Initialise le moteur TTS avec Google Cloud Text-to-Speech.
        """
        self.config = config
        load_dotenv(override=True)
        
        # Vérification des credentials Google Cloud
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError("Les credentials Google Cloud ne sont pas définis. Veuillez définir la variable d'environnement GOOGLE_APPLICATION_CREDENTIALS")
        
        self.client = texttospeech.TextToSpeechClient()
        self.temp_dir = Path("assets/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration de la voix française
        ssml_gender = (config["tts"]["gender"] == "female") if texttospeech.SsmlVoiceGender.FEMALE else texttospeech.SsmlVoiceGender.MALE 
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=config["tts"]["language"],
            name=config["tts"]["voice"],
            ssml_gender=ssml_gender
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
            text_question_and_choices = f"{question_data['question']}\n\n"
            for i in range(1, self.config["num_choices"] + 1):
                text_question_and_choices += f"{i} : {question_data['choices'][str(i)]}\n"
                
            text_answer = f"\nLa réponse est : {question_data['choices'] [question_data['answer']]}"
            
            # Génération de l'audio
            synthesis_input_question_and_choices = texttospeech.SynthesisInput(text=text_question_and_choices)
            synthesis_input_answer = texttospeech.SynthesisInput(text=text_answer)
            synthesis_inputs = [synthesis_input_question_and_choices, synthesis_input_answer]
            output_paths = []
            for synthesis_input in synthesis_inputs:
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=self.voice,
                    audio_config=self.audio_config
                )
                # Sauvegarde de l'audio
                audio_path = self.temp_dir / f"tts_{str(time.time()*1000).replace('.', '')}.mp3"
                with open(audio_path, "wb") as out:
                    out.write(response.audio_content)
                output_paths.append(str(audio_path))
            
            return output_paths
            
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
            
        