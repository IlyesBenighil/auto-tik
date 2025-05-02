import os
import logging
from typing import List, Dict
from pathlib import Path
import random
import time
from moviepy.editor import (
    ImageClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, VideoFileClip, CompositeAudioClip,
    ColorClip, concatenate_audioclips
)
from PIL import Image

logger = logging.getLogger(__name__)

class VideoCreator:
    def __init__(self):
        """
        Initialise le créateur de vidéos.
        """
        self.temp_dir = Path("assets/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Chargement des ressources
        self.backgrounds_dir = Path("assets/backgrounds")
        self.music_dir = Path("assets/music")
        
        # Vérification des ressources
        if not self.backgrounds_dir.exists():
            raise ValueError("Le répertoire des arrière-plans n'existe pas")
        if not self.music_dir.exists():
            raise ValueError("Le répertoire de la musique n'existe pas")
            
        # Dimensions TikTok (9:16)
        self.width = 1080
        self.height = 1920
        
        # Sélection de la musique qui sera utilisée pour toutes les vidéos
        self.music_path = random.choice(list(self.music_dir.glob("*.mp3")))
        self.music = AudioFileClip(str(self.music_path))
        self.music = self.music.volumex(0.1)  # Réduction du volume à 10%
        
        # Couleurs et styles
        self.colors = {
            'background': (0, 0, 0, 0.7),  # Noir semi-transparent
            'text': 'white',
            'highlight': '#FF2D55',  # Rose TikTok
            'correct': '#00FF00'  # Vert pour la bonne réponse
        }
            
    def _get_unique_filename(self, prefix: str = "video") -> str:
        """
        Génère un nom de fichier unique basé sur le timestamp.
        
        Args:
            prefix (str): Préfixe du nom de fichier
            
        Returns:
            str: Nom de fichier unique
        """
        timestamp = int(time.time() * 1000)
        return f"{prefix}_{timestamp}.mp4"
            
    def _calculate_text_positions(self, question_clip: TextClip, choices_clips: List[TextClip], total_duration: float) -> List[tuple]:
        """
        Calcule les positions optimales pour éviter le chevauchement des textes.
        
        Args:
            question_clip (TextClip): Clip de la question
            choices_clips (List[TextClip]): Liste des clips des choix
            total_duration (float): Durée totale de la vidéo
            
        Returns:
            List[tuple]: Liste des positions (x, y) pour chaque clip
        """
        # Position initiale de la question
        question_height = question_clip.size[1]
        question_y = self.height * 0.1
        positions = [('center', question_y)]
        
        # Calcul de l'espace disponible pour les choix
        available_height = self.height - (question_y + question_height)
        
        # Calcul de la hauteur totale des choix
        total_choices_height = sum(choice.size[1] for choice in choices_clips)
        
        # Calcul de l'espacement entre les choix
        spacing = 100
        
        # Position initiale pour les choix
        current_y = question_y + question_height + spacing
        
        # Calcul des positions pour chaque choix
        for choice_clip in choices_clips:
            positions.append(('center', current_y))
            current_y += choice_clip.size[1] + spacing
            
        return positions

    def _get_answer_timestamp(self, audio_file: str, answer: str) -> float:
        """
        Estime le moment où la bonne réponse est donnée dans l'audio.
        Pour l'instant, on utilise une estimation simple basée sur la durée totale.
        
        Args:
            audio_file (str): Chemin du fichier audio
            answer (str): La bonne réponse
            
        Returns:
            float: Timestamp estimé de la bonne réponse
        """
        # On estime que la bonne réponse est donnée à 80% de la durée totale
        audio = AudioFileClip(audio_file)
        return audio.duration * 0.8

    def _detect_answer_timestamp(self, audio_file: str, answer: str, choices: Dict[str, str]) -> float:
        """
        Détecte automatiquement le moment où la bonne réponse est donnée dans l'audio.
        
        Args:
            audio_file (str): Chemin du fichier audio
            answer (str): La bonne réponse (numéro)
            choices (Dict[str, str]): Dictionnaire des choix
            
        Returns:
            float: Timestamp où la bonne réponse est donnée
        """
        try:
            # On cherche le texte de la bonne réponse
            correct_choice_text = choices[answer].lower()
            
            # On utilise whisper pour transcrire l'audio
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_file)
            
            # On cherche le segment qui contient la bonne réponse
            for segment in result["segments"]:
                if correct_choice_text in segment["text"].lower():
                    return segment["start"]
            
            # Si on ne trouve pas, on retourne 80% de la durée
            audio = AudioFileClip(audio_file)
            return audio.duration * 0.8
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection du timestamp de la réponse: {str(e)}")
            # En cas d'erreur, on retourne 80% de la durée
            audio = AudioFileClip(audio_file)
            return audio.duration * 0.8

    def _generate_tts_audio(self, question_data: Dict) -> List[str]:
        """
        Génère les fichiers audio TTS pour la question et la réponse en utilisant Google Cloud TTS.
        
        Args:
            question_data (Dict): Les données de la question
            
        Returns:
            List[str]: Liste des chemins des fichiers audio [question_audio, answer_audio]
        """
        try:
            from google.cloud import texttospeech
            
            # Initialisation du client Google Cloud TTS
            client = texttospeech.TextToSpeechClient()
            
            # Configuration de la voix
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name="fr-FR-Standard-A",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Configuration de l'audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Création du texte pour la question et les choix
            question_text = f"{question_data['question']}\n"
            for i in range(1, 5):
                question_text += f"{i}. {question_data['choices'][str(i)]}\n"
            
            # Création du texte pour la réponse
            answer_text = f"La bonne réponse est : {question_data['choices'][question_data['answer']]}"
            
            # Génération des fichiers audio
            def generate_audio(text: str, output_path: str):
                synthesis_input = texttospeech.SynthesisInput(text=text)
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                with open(output_path, "wb") as out:
                    out.write(response.audio_content)
            
            # Audio pour la question et les choix
            qc_audio_path = self.temp_dir / f"tts_qc_{int(time.time() * 1000)}.mp3"
            generate_audio(question_text, str(qc_audio_path))
            
            # Audio pour la réponse
            ans_audio_path = self.temp_dir / f"tts_ans_{int(time.time() * 1000)}.mp3"
            generate_audio(answer_text, str(ans_audio_path))
            
            return [str(qc_audio_path), str(ans_audio_path)]
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des fichiers audio TTS: {str(e)}")
            raise

    def create_video(self, question_data: Dict, audio_files: List[str] = None, timer_sound_path: str = None) -> str:
        """
        Crée une vidéo pour une question avec :
        - lecture question+choix (tts1)
        - timer 3s (avec effet sonore et affichage)
        - révélation de la bonne réponse (tts2 et mise en valeur)
        
        Args:
            question_data (Dict): {
                'question': str,
                'choices': Dict[str, str],
                'answer': str
            }
            audio_files (List[str]): [tts_question_choix, tts_reponse] (optionnel)
            timer_sound_path (str): chemin du son du timer (optionnel)
            
        Returns:
            str: Chemin de la vidéo générée
        """
        try:
            # Génération des fichiers audio si non fournis ou si la liste est vide
            if audio_files is None or len(audio_files) < 2:
                logger.info("Génération des fichiers audio TTS...")
                audio_files = self._generate_tts_audio(question_data)
                logger.info(f"Fichiers audio générés : {audio_files}")
            
            # Vérification que les fichiers audio existent
            for audio_file in audio_files:
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Le fichier audio {audio_file} n'existe pas")
            
            # --- Préparation des ressources visuelles ---
            background_path = random.choice(list(self.backgrounds_dir.glob("*.jpg")))
            with Image.open(background_path) as img:
                resized_img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                temp_img_path = self.temp_dir / f"temp_bg_{int(time.time() * 1000)}.jpg"
                resized_img.save(temp_img_path)
            background = ImageClip(str(temp_img_path))
            overlay = ColorClip(size=(self.width, self.height), color=self.colors['background'])

            # --- Partie 1 : question + choix ---
            tts_qc = AudioFileClip(audio_files[0])
            part1_duration = tts_qc.duration
            question_clip = TextClip(
                question_data['question'],
                fontsize=90,
                color=self.colors['text'],
                font='Arial-Bold',
                size=(self.width * 0.9, None),
                method='caption',
                align='center',
                stroke_color=self.colors['highlight'],
                stroke_width=2
            ).set_position(('center', self.height * 0.1)).set_duration(part1_duration)
            choices_clips = []
            correct_answer = question_data['answer']
            for i in range(1, 5):
                choice_text = f"{i}. {question_data['choices'][str(i)]}"
                choice_clip = TextClip(
                    choice_text,
                    fontsize=70,
                    color=self.colors['text'],
                    font='Arial',
                    size=(self.width * 0.8, None),
                    method='caption',
                    align='center',
                    stroke_color=self.colors['highlight'],
                    stroke_width=1
                ).set_duration(part1_duration)
                choices_clips.append(choice_clip)
            positions = self._calculate_text_positions(question_clip, choices_clips, part1_duration)
            question_clip = question_clip.set_position(positions[0])
            for i, (choice_clip, position) in enumerate(zip(choices_clips, positions[1:]), 1):
                choices_clips[i-1] = choice_clip.set_position(position)
            part1 = CompositeVideoClip([
                background.set_duration(part1_duration),
                overlay.set_duration(part1_duration),
                question_clip,
                *choices_clips
            ], size=(self.width, self.height)).set_audio(tts_qc)

            # --- Partie 2 : timer 3s ---
            timer_duration = 3.0
            
            # Création d'un fond semi-transparent pour le timer
            timer_bg = ColorClip(
                size=(200, 200),
                color=(0, 0, 0, 0.7)
            ).set_position(('center', self.height*0.45))
            
            # Création des clips de texte pour le timer avec un style plus visible
            timer_texts = []
            for t in range(3):
                timer_text = TextClip(
                    str(3-t),
                    fontsize=150,
                    color='#FFD700',  # Or
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=3
                ).set_position(('center', self.height*0.45))
                # Chaque chiffre commence à un moment différent
                timer_texts.append(timer_text.set_start(t).set_duration(1))
            
            # Création du clip du timer avec tous les éléments
            timer_clip = CompositeVideoClip([
                background.set_duration(timer_duration),
                overlay.set_duration(timer_duration),
                question_clip.set_duration(timer_duration),  # Garde la question visible
                *[choice.set_duration(timer_duration) for choice in choices_clips],  # Garde les choix visibles
                timer_bg.set_duration(timer_duration),
                *timer_texts
            ], size=(self.width, self.height))
            
            # Ajout de l'effet sonore du timer
            if timer_sound_path:
                timer_audio = AudioFileClip(timer_sound_path).subclip(0, timer_duration)
                timer_clip = timer_clip.set_audio(timer_audio)
            else:
                # Création d'un son de "tick" simple si aucun son n'est fourni
                from scipy.io import wavfile
                import numpy as np
                
                # Génération d'un son de "tick" simple
                sample_rate = 44100
                duration = 0.1
                t = np.linspace(0, duration, int(sample_rate * duration))
                tick_sound = np.sin(2 * np.pi * 880 * t) * np.exp(-5 * t)
                tick_sound = np.int16(tick_sound * 32767)
                
                # Sauvegarde du son
                temp_tick_path = self.temp_dir / f"tick_{int(time.time() * 1000)}.wav"
                wavfile.write(str(temp_tick_path), sample_rate, tick_sound)
                
                # Création d'un clip audio avec 3 ticks, un à chaque seconde
                tick_audio = AudioFileClip(str(temp_tick_path))
                tick_clips = []
                for i in range(3):
                    # Réduction du volume de 90%
                    tick_clips.append(tick_audio.set_start(i).volumex(0.1))
                timer_audio = CompositeAudioClip(tick_clips)
                timer_clip = timer_clip.set_audio(timer_audio)

            # --- Partie 3 : révélation de la bonne réponse ---
            tts_ans = AudioFileClip(audio_files[1])
            part3_duration = tts_ans.duration + 1
            question_clip3 = question_clip.set_duration(part3_duration)
            choices_clips3 = []
            for i in range(1, 5):
                choice_text = f"{i}. {question_data['choices'][str(i)]}"
                is_correct = str(i) == correct_answer
                if is_correct:
                    choice_clip = TextClip(
                        choice_text,
                        fontsize=70,
                        color=self.colors['correct'],
                        font='Arial-Bold',
                        size=(self.width * 0.8, None),
                        method='caption',
                        align='center',
                        stroke_color=self.colors['correct'],
                        stroke_width=3
                    ).set_duration(part3_duration)
                else:
                    choice_clip = TextClip(
                        choice_text,
                        fontsize=70,
                        color=self.colors['text'],
                        font='Arial',
                        size=(self.width * 0.8, None),
                        method='caption',
                        align='center',
                        stroke_color=self.colors['highlight'],
                        stroke_width=1
                    ).set_duration(part3_duration)
                choices_clips3.append(choice_clip)
            positions3 = self._calculate_text_positions(question_clip3, choices_clips3, part3_duration)
            question_clip3 = question_clip3.set_position(positions3[0])
            for i, (choice_clip, position) in enumerate(zip(choices_clips3, positions3[1:]), 1):
                choices_clips3[i-1] = choice_clip.set_position(position)
            part3 = CompositeVideoClip([
                background.set_duration(part3_duration),
                overlay.set_duration(part3_duration),
                question_clip3,
                *choices_clips3
            ], size=(self.width, self.height)).set_audio(tts_ans)

            # --- Assemblage final ---
            final_video = concatenate_videoclips([part1, timer_clip, part3])
            output_path = self.temp_dir / self._get_unique_filename(prefix="question")
            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast'
            )
            # Nettoyage
            final_video.close()
            background.close()
            overlay.close()
            tts_qc.close()
            tts_ans.close()
            if temp_img_path.exists():
                temp_img_path.unlink()
            return str(output_path)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
            raise
            
    def concatenate_videos(self, video_paths: List[str]) -> str:
        """
        Concatène plusieurs vidéos en une seule.
        
        Args:
            video_paths (List[str]): Liste des chemins des vidéos à concaténer
            
        Returns:
            str: Chemin de la vidéo finale
        """
        try:
            # Chargement des clips
            clips = [VideoFileClip(path) for path in video_paths]
            
            # Concaténation
            final_clip = concatenate_videoclips(clips)
            
            # Calcul de la durée totale
            total_duration = final_clip.duration
            
            # Vérification de la durée de la musique
            music_duration = self.music.duration
            if total_duration > music_duration:
                # Si la vidéo est plus longue que la musique, on répète la musique
                n_repeats = int(total_duration / music_duration) + 1
                music_clips = [self.music] * n_repeats
                music_clip = concatenate_audioclips(music_clips).subclip(0, total_duration)
            else:
                # Sinon on prend juste la partie nécessaire
                music_clip = self.music.subclip(0, total_duration)
            
            # Mixage de l'audio des vidéos avec la musique
            final_audio = CompositeAudioClip([final_clip.audio, music_clip])
            final_clip = final_clip.set_audio(final_audio)
            
            # Sauvegarde avec un nom unique
            output_path = self.temp_dir / self._get_unique_filename(prefix="final")
            final_clip.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast'
            )
            
            # Nettoyage
            final_clip.close()
            for clip in clips:
                clip.close()
                
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la concaténation des vidéos: {str(e)}")
            raise
            
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
            if hasattr(self, 'music'):
                self.music.close()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temporaires: {str(e)}") 