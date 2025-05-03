import os
import logging
from typing import List, Dict
from pathlib import Path
import random
import time
from PIL import Image, ImageDraw
from moviepy import AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip, ImageClip, TextClip, VideoFileClip, concatenate_audioclips, concatenate_videoclips
import numpy as np

logger = logging.getLogger(__name__)

class VideoCreator:
    def __init__(self, theme: str = 'geographie'):
        """
        Initialise le créateur de vidéos.
        
        Args:
            theme (str): Le thème du quiz (par défaut: 'geographie')
        """
        self.theme = theme
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
        # Gestionnaire de fonds vidéo
        try:
            from src.background_manager import BackgroundManager
            self.background_manager = BackgroundManager()
            logger.info("BackgroundManager initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du BackgroundManager: {str(e)}")
            self.background_manager = None
        
        # Couleurs et styles
        self.colors = {
            'background': (0, 0, 0, 0.5),  # Noir semi-transparent (réduit à 50%)
            'text': 'white',
            'highlight': '#000000',
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
            
            # Création du texte pour la réponse (sans répéter la question)
            answer_text = f"La réponse est : {question_data['choices'][question_data['answer']]}"
            
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

    def _create_text_box(self, text: str, fontsize: int, color: str, is_correct: bool = False) -> CompositeVideoClip:
        """
        Crée une boîte design contenant du texte.
        
        Args:
            text (str): Le texte à afficher
            fontsize (int): Taille de la police
            color (str): Couleur du texte
            is_correct (bool): Si c'est la bonne réponse
            
        Returns:
            CompositeVideoClip: La boîte avec le texte
        """
        try:
            # Création du texte avec une police système standard
            text_clip = TextClip(
                text=text,
                font_size=fontsize,
                color=color,
                size=(int(self.width * 0.8), None),
                method='caption',
                stroke_color=self.colors['highlight'],
                stroke_width=2,
                font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            )
            
            # Dimensions de la boîte avec padding
            padding = 30
            box_width = text_clip.size[0] + padding * 2
            box_height = text_clip.size[1] + padding * 2
            
            # Création d'une image PIL pour la boîte
            box_image = Image.new('RGBA', (box_width, box_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(box_image)
            
            # Couleurs de la boîte
            if is_correct:
                fill_color = (0, 255, 0, 102)  # Vert semi-transparent
                border_color = (0, 255, 0, 255)  # Vert plein
            else:
                fill_color = (0, 0, 0, 153)  # Noir semi-transparent
                border_color = (255, 255, 255, 204)  # Blanc semi-transparent
            
            # Dessin du fond
            draw.rectangle(
                [(0, 0), (box_width, box_height)],
                fill=fill_color
            )
            
            # Dessin de la bordure
            border_width = 4
            draw.rectangle(
                [(0, 0), (box_width, box_height)],
                outline=border_color,
                width=border_width
            )
            
            # Création du clip à partir de l'image PIL
            box_clip = ImageClip(np.array(box_image))
            
            # Positionnement du texte au centre de la boîte
            text_clip = text_clip.with_position(('center', 'center'))
            
            # Assemblage de la boîte
            final_clip = CompositeVideoClip([
                box_clip,
                text_clip
            ], size=(box_width, box_height))
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la boîte: {str(e)}")
            raise

    def create_video(self, question_data: Dict, audio_files: List[str]) -> CompositeVideoClip:
        """
        Crée une vidéo à partir des données de la question et des fichiers audio.
        
        Args:
            question_data (Dict): Données de la question
            audio_files (List[str]): Liste des chemins des fichiers audio [question_audio, answer_audio]
            
        Returns:
            CompositeVideoClip: Le clip vidéo créé
        """
        try:
            # Vérification et génération des fichiers audio si nécessaire
            if len(audio_files) < 2:
                logger.info("Génération des fichiers audio TTS...")
                audio_files = self._generate_tts_audio(question_data)
                logger.info(f"Fichiers audio générés : {audio_files}")
            
            # Vérification que les fichiers audio existent
            for audio_file in audio_files:
                if not os.path.exists(audio_file):
                    raise FileNotFoundError(f"Le fichier audio {audio_file} n'existe pas")
            
            # --- Création des clips audio ---
            question_audio = AudioFileClip(audio_files[0])
            answer_audio = AudioFileClip(audio_files[1])
            
            # Calcul des durées
            part1_duration = question_audio.duration
            timer_duration = 3.0  # Durée du timer
            part2_duration = answer_audio.duration
            total_duration = part1_duration + timer_duration + part2_duration
            
            # --- Création des clips vidéo ---
            # Partie 1 : Question et choix
            # Création de la boîte pour la question
            question_box = self._create_text_box(
                question_data['question'],
                fontsize=90,
                color=self.colors['text']
            )
            
            # Création des boîtes pour les choix (tous en style normal)
            choices_boxes = []
            correct_answer = question_data['answer']
            
            for i in range(1, 5):
                choice_text = f"{i}. {question_data['choices'][str(i)]}"
                choice_box = self._create_text_box(
                    choice_text,
                    fontsize=70,
                    color=self.colors['text'],
                    is_correct=False  # Tous les choix sont en style normal
                )
                choices_boxes.append(choice_box)
            
            # Calcul des positions optimales
            positions = self._calculate_text_positions(question_box, choices_boxes, part1_duration)
            
            # Application des positions
            question_box = question_box.with_position(positions[0]).with_duration(part1_duration)
            for i, (choice_box, position) in enumerate(zip(choices_boxes, positions[1:]), 1):
                choices_boxes[i-1] = choice_box.with_position(position).with_duration(part1_duration)
            
            # Création de la première partie
            part1 = CompositeVideoClip([
                question_box,
                *choices_boxes
            ], size=(self.width, self.height)).with_audio(question_audio)
            
            # --- Partie Timer ---
            # Création d'un fond semi-transparent pour le timer
            timer_bg = ColorClip(
                size=(200, 200),
                color=(0, 0, 0, 0.7)
            ).with_position(('center', self.height*0.45))
            
            # Création des clips de texte pour le timer
            timer_texts = []
            for t in range(3):
                timer_text = TextClip(
                    text=str(3-t),
                    font_size=150,
                    color='#FFD700',
                    font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                    stroke_color='black',
                    stroke_width=3
                ).with_position(('center', self.height*0.45))
                timer_texts.append(timer_text.with_start(t).with_duration(1))
            
            # Création du clip du timer
            timer_clip = CompositeVideoClip([
                question_box.with_duration(timer_duration),
                *[choice.with_duration(timer_duration) for choice in choices_boxes],
                timer_bg.with_duration(timer_duration),
                *timer_texts
            ], size=(self.width, self.height))
            
            # Création d'un son de "tick" simple
            from scipy.io import wavfile
            import numpy as np
            
            sample_rate = 44100
            duration = 0.1
            t = np.linspace(0, duration, int(sample_rate * duration))
            tick_sound = np.sin(2 * np.pi * 880 * t) * np.exp(-5 * t)
            tick_sound = np.int16(tick_sound * 32767)
            
            temp_tick_path = self.temp_dir / f"tick_{int(time.time() * 1000)}.wav"
            wavfile.write(str(temp_tick_path), sample_rate, tick_sound)
            
            tick_audio = AudioFileClip(str(temp_tick_path))
            tick_clips = []
            for i in range(3):
                tick_clips.append(tick_audio.with_start(i))
            timer_audio = CompositeAudioClip(tick_clips)
            timer_clip = timer_clip.with_audio(timer_audio)
            
            # Partie 2 : Réponse
            # Création des boîtes pour la partie 2 (avec la bonne réponse en vert)
            choices_boxes2 = []
            for i in range(1, 5):
                choice_text = f"{i}. {question_data['choices'][str(i)]}"
                is_correct = str(i) == correct_answer
                choice_box = self._create_text_box(
                    choice_text,
                    fontsize=70,
                    color=self.colors['text'],
                    is_correct=is_correct  # La bonne réponse sera en vert
                )
                choices_boxes2.append(choice_box)
            
            # Application des positions
            question_box2 = question_box.with_duration(part2_duration)
            for i, (choice_box, position) in enumerate(zip(choices_boxes2, positions[1:]), 1):
                choices_boxes2[i-1] = choice_box.with_position(position).with_duration(part2_duration)
            
            # Création de la deuxième partie
            part2 = CompositeVideoClip([
                question_box2,
                *choices_boxes2
            ], size=(self.width, self.height)).with_audio(answer_audio)
            
            # --- Assemblage final ---
            #final_clip = concatenate_videoclips([part1, timer_clip, part2])
            final_clip = part1

            
            # Nettoyage
            question_audio.close()
            answer_audio.close()
            tick_audio.close()
            
            # Vérification de la durée de la musique
            music_duration = self.music.duration
            if total_duration > music_duration:
                # Si la vidéo est plus longue que la musique, on répète la musique
                n_repeats = int(total_duration / music_duration) + 1
                music_clips = [self.music] * n_repeats
                music_clip = concatenate_audioclips(music_clips).subclipped(0, total_duration)
            else:
                # Sinon on prend juste la partie nécessaire
                music_clip = self.music.subclipped(0, total_duration)
            
            # # On s'assure que l'audio de la vidéo est valide
            # if hasattr(final_clip, 'audio') and final_clip.audio is not None:
            #     # Mixage de l'audio des vidéos avec la musique
            #     final_audio = CompositeAudioClip([final_clip.audio, music_clip])
            #     final_clip = final_clip.with_audio(final_audio)
            # else:
            #     # Si pas d'audio, on utilise juste la musique
            #     final_clip = final_clip.with_audio(music_clip)
            
            # Ajout de la vidéo de fond
            video_path = self.background_manager.get_background_video(self.theme)
            logger.info(f"Chemin de la vidéo de fond: {video_path}")
            
            if video_path:
                try:
                    logger.info("Chargement de la vidéo de fond...")
                    background = VideoFileClip(video_path)
                    logger.info(f"Dimensions originales du background: {background.size}")
                    
                    # Ajustement de la taille
                    logger.info(f"Redimensionnement à {self.width}x{self.height}")
                    background = background.resized((self.width, self.height))
                    logger.info(f"Nouvelles dimensions du background: {background.size}")
                    
                    # Boucle si nécessaire
                    logger.info(f"Durée du background: {background.duration}s, durée totale: {total_duration}s")
                    if background.duration < total_duration:
                        n_loops = int(total_duration / background.duration) + 1
                        logger.info(f"Création de {n_loops} boucles du background")
                        background = background.loop(n=n_loops)
                    
                    background = background.subclipped(0, total_duration)
                    logger.info("Background préparé avec succès")
                    
                    # On crée d'abord le clip avec le background
                    background_clip = background.with_position('center')
                    
                    # # On crée le clip final avec l'audio
                    # final_clip = final_clip.with_position('center')
                    
                    # # On crée le composite avec les deux clips
                    # final_clip = CompositeVideoClip([
                    #     background_clip,
                    #     final_clip
                    # ], size=(self.width, self.height))
                    
                    # On s'assure que l'audio est préservé
                    # if hasattr(final_clip, 'audio') and final_clip.audio is not None:
                    #     final_clip = final_clip.with_audio(final_clip.audio)
                    
                    logger.info("Superposition terminée avec succès")
                    
                    # Sauvegarde avec un nom unique
                    output_path = self.temp_dir / self._get_unique_filename(prefix="final")
                    final_clip.write_videofile(
                        filename=str(output_path),

                    )
                    
                    # Nettoyage
                    background.close()
                    final_clip.close()
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la préparation du background: {str(e)}")
                    logger.error("Utilisation de la vidéo sans background")
                    # En cas d'erreur, on sauvegarde la vidéo sans background
                    output_path = self.temp_dir / self._get_unique_filename(prefix="final")
                    final_clip.write_videofile(
                        str(output_path),
                        fps=30,
                        codec='libx264',
                        audio_codec='aac',
                        preset='ultrafast',
                        threads=None,
                        logger="bar"
                    )
                    final_clip.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
            raise
            
    def concatenate_videos(self, video_clips: List[CompositeVideoClip]) -> str:
        """
        Concatène plusieurs clips vidéo en une seule vidéo.
        
        Args:
            video_clips (List[CompositeVideoClip]): Liste des clips vidéo à concaténer
            
        Returns:
            str: Chemin de la vidéo finale
        """
        try:
            # Concaténation
            final_clip = concatenate_videoclips(video_clips)
            
            # Calcul de la durée totale
            total_duration = final_clip.duration
            
            # Vérification de la durée de la musique
            music_duration = self.music.duration
            if total_duration > music_duration:
                # Si la vidéo est plus longue que la musique, on répète la musique
                n_repeats = int(total_duration / music_duration) + 1
                music_clips = [self.music] * n_repeats
                music_clip = concatenate_audioclips(music_clips).subclipped(0, total_duration)
            else:
                # Sinon on prend juste la partie nécessaire
                music_clip = self.music.subclipped(0, total_duration)
            
            # On s'assure que l'audio de la vidéo est valide
            if hasattr(final_clip, 'audio') and final_clip.audio is not None:
                # Mixage de l'audio des vidéos avec la musique
                final_audio = CompositeAudioClip([final_clip.audio, music_clip])
                final_clip = final_clip.with_audio(final_audio)
            else:
                # Si pas d'audio, on utilise juste la musique
                final_clip = final_clip.with_audio(music_clip)
            
            # Ajout de la vidéo de fond
            video_path = self.background_manager.get_background_video(self.theme)
            logger.info(f"Chemin de la vidéo de fond: {video_path}")
            
            if video_path:
                try:
                    logger.info("Chargement de la vidéo de fond...")
                    background = VideoFileClip(video_path)
                    logger.info(f"Dimensions originales du background: {background.size}")
                    
                    # Ajustement de la taille
                    logger.info(f"Redimensionnement à {self.width}x{self.height}")
                    background = background.resize((self.width, self.height))
                    logger.info(f"Nouvelles dimensions du background: {background.size}")
                    
                    # Boucle si nécessaire
                    logger.info(f"Durée du background: {background.duration}s, durée totale: {total_duration}s")
                    if background.duration < total_duration:
                        n_loops = int(total_duration / background.duration) + 1
                        logger.info(f"Création de {n_loops} boucles du background")
                        background = background.loop(n=n_loops)
                    
                    background = background.subclipped(0, total_duration)
                    logger.info("Background préparé avec succès")
                    
                    # On sauvegarde l'audio avant la superposition
                    audio = final_clip.audio
                    
                    # Création du clip composite
                    logger.info("Création du clip composite...")
                    
                    # On crée d'abord le clip avec le background
                    background_clip = background.with_position('center')
                    
                    # On crée le clip final avec l'audio
                    final_clip = final_clip.with_position('center')
                    
                    # On crée le composite avec les deux clips
                    final_clip = CompositeVideoClip([
                        background_clip,
                        final_clip
                    ], size=(self.width, self.height))
                    
                    # On s'assure que l'audio est préservé
                    if hasattr(final_clip, 'audio') and final_clip.audio is not None:
                        final_clip = final_clip.with_audio(final_clip.audio)
                    
                    logger.info("Superposition terminée avec succès")
                    
                    # Sauvegarde avec un nom unique
                    output_path = self.temp_dir / self._get_unique_filename(prefix="final")
                    final_clip.write_videofile(
                        str(output_path),
                        fps=30,
                        codec='libx264',
                        audio_codec='aac',
                        preset='ultrafast',
                        threads=4,  # Utilisation de plusieurs threads pour l'encodage
                        logger=None  # Désactive les logs de moviepy pour éviter les conflits
                    )
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la préparation du background: {str(e)}")
                    logger.error("Utilisation de la vidéo sans background")
                    # En cas d'erreur, on continue sans le background
                    pass
            
            # Nettoyage
            final_clip.close()
            if 'background' in locals():
                background.close()
                
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la concaténation des vidéos: {str(e)}")
            raise
            
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():  # On ne supprime que les fichiers
                    file.unlink()
            if hasattr(self, 'music'):
                self.music.close()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temporaires: {str(e)}") 