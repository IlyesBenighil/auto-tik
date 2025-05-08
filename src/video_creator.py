import os
import logging
from typing import List, Dict
from pathlib import Path
import random
import time
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioClip, AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip, ImageClip, TextClip, VideoFileClip, VideoClip, concatenate_audioclips, concatenate_videoclips
from moviepy.video.tools.subtitles import SubtitlesClip
import numpy as np
import ast

logger = logging.getLogger(__name__)

class VideoCreator:
    def __init__(self, config: dict, theme: str):
        """
        Initialise le créateur de vidéos.
        
        Args:
            theme (str): Le thème du quiz (par défaut: 'geographie')
        """
        self.config = config
        self.theme = theme
        self.temp_dir = Path(config["path_assets"]["temp"])
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Nouvelle variable pour stocker la position Y du bas du dernier choix
        self.last_choice_bottom_y = None
        
        # Chargement des ressources
        
        # Fond video background
        self.backgrounds_dir = Path(config["path_assets"]["backgrounds"])
        # Fond musique background
        self.music_dir = Path(config["path_assets"]["music"])
        
        # Vérification des ressources
        if not self.backgrounds_dir.exists():
            raise ValueError("Le répertoire des arrière-plans n'existe pas")
        if not self.music_dir.exists():
            raise ValueError("Le répertoire de la musique n'existe pas")
            
        # Dimensions TikTok (9:16)
        self.width = self.config["video"]["width"]
        self.height = self.config["video"]["height"]
        
        # Sélection de la musique qui sera utilisée pour toutes les vidéos
        self.music = AudioFileClip(str(self.music_dir) + '/' + self.config["music"]["background"])
        
        # Position Y du bas du dernier choix
        self.lowest_choices_y = 0
        
        # Gestionnaire de fonds vidéo
        try:
            from src.background_manager import BackgroundManager
            self.background_manager = BackgroundManager(config=self.config)
            logger.info("BackgroundManager initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du BackgroundManager: {str(e)}")
            self.background_manager = None
        
    
        # Couleurs et styles
        self.colors = {
            'text': self.config["video"]["text_color"],
            'highlight': self.config["video"]["highlight_color"],
            'choice_correct_background': ast.literal_eval(self.config["video"]["choice_correct_background"]),
            'choice_correct_highlight': ast.literal_eval(self.config["video"]["choice_correct_highlight"]),
            'choice_background': ast.literal_eval(self.config["video"]["choice_background"]),
            'choice_highlight': ast.literal_eval(self.config["video"]["choice_highlight"])
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
            
    def _calculate_text_positions(self, question_clip: TextClip, choices_clips: List[TextClip]):
        """
        Calcule les positions optimales pour éviter le chevauchement des textes.
        
        Args:
            question_clip (TextClip): Clip de la question
            choices_clips (List[TextClip]): Liste des clips des choix
        """
        # Position de la question en haut
        question_y = self.height * 0.15
        question_clip_with_position = question_clip.with_position(('center', question_y))
        
        # Espacement entre les options
        spacing = self.config["video"]["spacing"]
        question_clip_height = question_clip.size[1]
        
        current_y = question_clip_height + question_y + spacing 
        
        choices_clips_with_position = []
        # Calculer les positions pour chaque choix
        for i, choice_clip in enumerate(choices_clips):
            choices_clips_with_position.append(choice_clip.with_position(('center', current_y)))
            current_y += choice_clip.size[1] + spacing
        if current_y > self.lowest_choices_y:
            self.lowest_choices_y = current_y
        # Stocker la position Y du bas du dernier choix pour les sous-titres
        if choices_clips:
            last_choice = choices_clips[-1]
            self.last_choice_bottom_y = current_y - spacing  # Position après le dernier choix
        else:
            self.last_choice_bottom_y = question_clip_height + question_y + spacing
            
        return question_clip_with_position, choices_clips_with_position

    def _wrap_japanese_text(self, text, max_chars=9):
        from fugashi import Tagger
        tagger = Tagger()
        tokens = [word.surface for word in tagger(text)]
       
        lines = []
        current_line = ''
       
        for token in tokens:
            if len(current_line) + len(token) > max_chars:
               lines.append(current_line)
               current_line = token
            else:
               current_line += token
       
        if current_line:
            lines.append(current_line)
       
        return '\n'.join(lines)
    
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
        method = 'caption'
        if self.config["subtitles"]["language"] == "ja":
            text = self._wrap_japanese_text(text)
            method = 'label'
        # Création du texte avec une police système standard
        text_clip = TextClip(
            text=text,
            font_size=fontsize,
            color=color,
            size=(int(self.width * 0.8), None),
            method=method,
            stroke_color=self.colors['highlight'],
            stroke_width=2,
            font=self.config["video"]["font"]
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
            fill_color = self.colors['choice_correct_background']
            border_color = self.colors['choice_correct_highlight']
        else:
            fill_color = self.colors['choice_background']
            border_color = self.colors['choice_highlight']
        
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

    def create_video(self, question_data: Dict, audio_info: List[Dict]) -> CompositeVideoClip:
        """
        Crée une vidéo à partir des données de la question et des informations audio.
        
        Args:
            question_data (Dict): Données de la question
            audio_info (List[Dict]): Liste des informations audio [
                {
                    'path': str,  # Chemin du fichier audio
                    'text': str,  # Texte correspondant
                    'duration': float  # Durée en secondes
                }
            ]
            
        Returns:
            CompositeVideoClip: Le clip vidéo créé
        """
        try:
            # Vérification que les fichiers audio existent
            for info in audio_info:
                audio_path = info['path']
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"Le fichier audio {audio_path} n'existe pas")
            
            # --- Création des clips audio ---
            question_audio = AudioFileClip(audio_info[0]['path'])
            answer_audio = AudioFileClip(audio_info[1]['path'])
            
            # Calcul des durées
            part1_duration = audio_info[0]['duration']
            timer_duration = 3.0  # Durée du timer
            part2_duration = audio_info[1]['duration']
            
            # --- Création des clips vidéo ---
            # Partie 1 : Question et choix
            # Création de la boîte pour la question
            question_box = self._create_text_box(
                question_data['question'],
                fontsize=self.config["video"]["question_font_size"],
                color=self.colors['text']
            )
        
            # Création des boîtes pour les choix (tous en style normal)
            choices_boxes = []
            
            for i in range(1, self.config["prompt"]["num_choices"] + 1):
                choice_text = f"{i}. {question_data['choices'][str(i)]}"
                choice_box = self._create_text_box(
                    choice_text,
                    fontsize=self.config["video"]["choices_font_size"],
                    color=self.colors['text'],
                    is_correct=False  # Tous les choix sont en style normal
                )
                choices_boxes.append(choice_box)
            
            # Calcul des positions optimales
            question_box, choices_boxes = self._calculate_text_positions(question_box, choices_boxes)
            
            # Création de la première partie
            part1 = CompositeVideoClip(
                [question_box] + choices_boxes,
                size=(self.width, self.height)
            )
            part1.fps = self.config["video"]["fps"]
            part1 = part1.with_audio(question_audio)
            part1 = part1.with_duration(part1_duration)
            
            # --- Partie Timer ---
            timer_clip = self._create_progress_bar_timer(timer_duration, question_box, choices_boxes)
            
            # --- Partie 2 : Réponse ---
            # Création des boîtes pour la partie 2 (avec la bonne réponse en vert)
            choices_boxes_part2 = []
            correct_answer_index = int(question_data['answer'])
            for i in range(1, len(question_data['choices']) + 1):
                if i == correct_answer_index:
                    choice_box = self._create_text_box(
                        question_data['choices'][str(i)],
                        fontsize=self.config["video"]["choices_font_size"],
                        color=self.colors['text'],
                        is_correct=True
                    )
                    choices_boxes_part2.append(choice_box)
                else:
                    choices_boxes_part2.append(choices_boxes[i-1])
            
            question_box2 = question_box.with_duration(part2_duration)
            # Calcul des positions optimales
            question_box2, choices_boxes_part2 = self._calculate_text_positions(question_box2, choices_boxes_part2)
            
            # Création de la deuxième partie
            part2 = CompositeVideoClip(
                [question_box2] + choices_boxes_part2,
                size=(self.width, self.height)
            )
            part2.fps = self.config["video"]["fps"]
            part2 = part2.with_audio(answer_audio)
            part2 = part2.with_duration(part2_duration)
            
            # --- Assemblage final ---
            final_clips = []
            if part1.duration is not None:
                final_clips.append(part1)
            if timer_clip.duration is not None:
                final_clips.append(timer_clip)
            if part2.duration is not None:
                final_clips.append(part2)
                
            if not final_clips:
                raise ValueError("Aucun clip vidéo valide à concaténer")
                
            final_clip = concatenate_videoclips(final_clips)
            final_clip.fps = self.config["video"]["fps"]
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
            raise
    
    
    def create_video_v2(self, workflow: Dict, audio_info: List[Dict]) -> CompositeVideoClip:
        phases = workflow["phases"]
        question_data = workflow["question_data"]
        return None
      
    def _create_progress_bar_timer(self, timer_duration: float, question_box: CompositeVideoClip, choices_boxes: List[CompositeVideoClip]) -> CompositeVideoClip:
        # Paramètres du timer circulaire
        circle_radius = 100  # Deux fois plus grand
        circle_thickness = 20  # Épaisseur proportionnelle
        circle_color = (255, 165, 0, 255)  # Orange
        circle_bg_color = (40, 44, 52, 180)  # Fond gris foncé semi-transparent
        text_color = (248, 248, 242, 255)    # Texte blanc
        
        frames_per_second = self.config["video"]["fps"]
        total_frames = int(timer_duration * frames_per_second)
        
        # Calcul de la position du timer
        spacing = self.config["video"]["spacing"]
        question_height = question_box.size[1]
        question_y = self.height * 0.1
        choices_total_height = sum(choice.size[1] for choice in choices_boxes)
        total_spacing = spacing * len(choices_boxes)
        
        # Position au centre de l'écran sous les choix
        timer_y = question_y + question_height + choices_total_height + total_spacing + 80  # Plus d'espace pour un timer plus grand
        timer_y = min(timer_y, self.height * 0.8)
        
        # Créer les images pour chaque frame
        frames = []
        for frame in range(total_frames):
            # Calculer le temps restant
            progress = frame / total_frames
            time_left = int(timer_duration - (frame / frames_per_second)) + 1
            
            # Créer une image pour le timer - plus grande
            img = Image.new("RGBA", (2*circle_radius + 40, 2*circle_radius + 40), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Dessiner le cercle de fond
            draw.ellipse(
                [(20, 20), (20 + 2*circle_radius, 20 + 2*circle_radius)], 
                outline=circle_bg_color, 
                width=circle_thickness
            )
            
            # Calculer l'angle pour l'arc de progression (360 degrés = cercle complet)
            angle = int(360 * (1 - progress))
            
            # Dessiner l'arc de progression
            # L'angle 0 est à droite (Est) et tourne dans le sens anti-horaire
            draw.arc(
                [(20, 20), (20 + 2*circle_radius, 20 + 2*circle_radius)],
                start=270, 
                end=(270 + angle) % 360,
                fill=circle_color, 
                width=circle_thickness
            )
            
            # Ajouter le texte du temps restant
            try:
                font = ImageFont.truetype(self.config["video"]["font"], 80)  # Police plus grande
            except:
                font = ImageFont.load_default()
                
            # Position texte au centre du cercle
            text_x = circle_radius + 20
            text_y = circle_radius + 20
            draw.text(
                (text_x, text_y), 
                str(time_left), 
                fill=text_color, 
                font=font, 
                anchor="mm"
            )
            
            # Convertir en array pour moviepy
            frame_array = np.array(img)
            frames.append(frame_array)
        
        # Créer les clips pour chaque image
        timer_clips = []
        for i, frame in enumerate(frames):
            clip = ImageClip(frame)
            clip = clip.with_duration(1/frames_per_second)
            timer_clips.append(clip)
        
        # Créer un clip combinant toutes les images du timer
        if timer_clips:
            timer_sequence = concatenate_videoclips(timer_clips, method="compose")
            timer_sequence = timer_sequence.with_duration(timer_duration)
            
            # Préparer la question et les choix
            question_clip = question_box.with_duration(timer_duration)
            choices_clips = [choice.with_duration(timer_duration) for choice in choices_boxes]
            
            # Positionner le timer au centre
            timer_pos = ("center", timer_y)
            
            # Ajouter le son beep_10
            beep_path = os.path.join(self.config["path_assets"]["sound_effects"] + '/' + self.config["sound_effects"]["tick"])
            
            # Vérifier si le fichier audio existe
            audio_clip = None
            if os.path.exists(beep_path):
                try:
                    beep_audio = AudioFileClip(beep_path)
                    
                    # Si l'audio est plus court que le timer, créer une boucle
                    if beep_audio.duration < timer_duration:
                        # Calculer combien de fois il faut répéter l'audio
                        repeats = int(timer_duration / beep_audio.duration) + 1
                        # Créer une liste d'audio clips à concaténer
                        beep_clips = [beep_audio] * repeats
                        # Concaténer et couper à la durée exacte
                        audio_clip = concatenate_audioclips(beep_clips).subclipped(0, timer_duration)
                    else:
                        # Sinon, couper l'audio à la durée du timer
                        audio_clip = beep_audio.subclipped(0, timer_duration)
                        
                    logger.info(f"Son beep_10 ajouté au timer")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement du son beep_10: {str(e)}")
            else:
                logger.warning(f"Fichier son beep_10 introuvable: {beep_path}")
            
            # Créer le clip final avec question, choix et timer
            timer_clip = CompositeVideoClip(
                [question_clip] + choices_clips + [timer_sequence.with_position(timer_pos)],
                size=(self.width, self.height)
            )
            timer_clip.fps = self.config["video"]["fps"]
            
            # Ajouter l'audio si disponible
            if audio_clip:
                timer_clip = timer_clip.with_audio(audio_clip)
            
            return timer_clip
        else:
            # Fallback si pas de frames
            logger.error("Aucune frame générée pour le timer")
            blank = ColorClip(size=(self.width, self.height), color=(0, 0, 0, 0))
            return blank.with_duration(timer_duration)

    def concatenate_videos(self, video_clips: List[CompositeVideoClip], srt_file: str = None, audio_info: List[Dict] = None) -> str:
        """
        Concatène plusieurs clips vidéo en une seule vidéo.
        
        Args:
            video_clips (List[CompositeVideoClip]): Liste des clips vidéo à concaténer
            srt_file (str, optional): Chemin vers le fichier SRT des sous-titres
            audio_info (List[Dict], optional): Informations sur les fichiers audio pour le calcul des offsets
            
        Returns:
            str: Chemin de la vidéo finale
        """
        try:
            # Vérification et préparation des clips
            valid_clips = []
            for clip in video_clips:
                if clip is not None:
                    # Assurer que les dimensions sont correctes
                    if hasattr(clip, 'size') and clip.size != (self.width, self.height):
                        clip = clip.resize((self.width, self.height))
                    
                    # Assurer que le fps est défini
                    if not hasattr(clip, 'fps') or clip.fps is None:
                        clip.fps = self.config["video"]["fps"]
                    
                    # Si pas d'audio, ajouter un clip silencieux
                    if not hasattr(clip, 'audio') or clip.audio is None:
                        clip = clip.with_audio(None)
                        
                    valid_clips.append(clip)
            
            # Vérifier qu'il y a des clips valides
            if not valid_clips:
                raise ValueError("Aucun clip vidéo valide à concaténer")
                
            # Concaténation
            final_clip = concatenate_videoclips(valid_clips)
            final_clip.fps = self.config["video"]["fps"]
            
            # Calcul de la durée totale
            total_duration = final_clip.duration
            
            # Gestion des sous-titres si fournis et activés dans la configuration
            if self.config["subtitles"]["enabled"] and srt_file and os.path.exists(srt_file):
                try:
                    logger.info(f"Ajout des sous-titres depuis {srt_file}")
                    
                    # Définir la position des sous-titres en fonction de la position du dernier choix
                    subtitle_position = ('center', 'bottom')  # Position par défaut
                    
                    extra_spacing = self.config["subtitles"].get("extra_spacing", 30)
                    
                    # Position en pixels absolus
                    subtitle_position = ('center', self.lowest_choices_y + extra_spacing)
                    
                    # Créer le générateur de sous-titres
                    make_textclip = lambda txt: self._create_subtitle_clip(txt, self.height)
                    
                    # Charger les sous-titres avec la position calculée
                    subtitles = SubtitlesClip(srt_file, make_textclip=make_textclip).with_position(subtitle_position)
                    
                    # Ajouter les sous-titres à la vidéo
                    final_clip = CompositeVideoClip([final_clip, subtitles])
                    logger.info("Sous-titres ajoutés avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout des sous-titres: {str(e)}")
            
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
            
            # Récupération du fond vidéo, si aucun fond vidéo n'est défini, on génère un fond vidéo depuis une image génré par ia.
            background_video_file = self.config["video"]["background"];
            background_video_path = self.config["path_assets"]["backgrounds"] + '/' + background_video_file
            if background_video_file == "":
                background_video_path = self.background_manager.get_background(self.theme)
            
            logger.info(f"Chemin de la vidéo de fond: {background_video_path}")
            output_path = str(self.temp_dir) + '/' + self._get_unique_filename(prefix="final")

            if background_video_path:
                try:
                    logger.info("Chargement de la vidéo de fond...")
                    background_video_path = VideoFileClip(background_video_path)
                    background_video_path = background_video_path.resized((self.width, self.height))
                    
                    if background_video_path.duration < total_duration:
                        n_loops = int(total_duration / background_video_path.duration) + 1
                        background_video_path = background_video_path.loop(n=n_loops)
                    
                    background_video_path = background_video_path.subclipped(0, total_duration)
                    
                    # Création du clip composite final
                    final_clip = CompositeVideoClip(
                        [background_video_path.with_position(('center', 'center')), final_clip.with_position(('center', 'center'))],
                        size=(self.width, self.height)
                    )
                    final_clip.fps = self.config["video"]["fps"]
                    
                    if hasattr(final_clip, 'audio') and final_clip.audio is not None:
                        final_clip = final_clip.with_audio(final_clip.audio)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la préparation du background: {str(e)}")
                    logger.error("Utilisation de la vidéo sans background")
                    
            final_clip.write_videofile(
                str(output_path),
                fps=self.config["video"]["fps"],
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                threads=16,
                logger="bar"
            )
            final_clip.close()
            if 'background' in locals():
                background_video_path.close()
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

    def _make_background(self, size, bg_color, corner_radius):
        """
        Crée un fond avec coins arrondis pour les sous-titres.
        
        Args:
            size (tuple): Dimensions (largeur, hauteur)
            bg_color (list): Couleur de fond [R, G, B]
            corner_radius (int): Rayon des coins arrondis
            
        Returns:
            tuple: (fond, masque)
        """
        w, h = size
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Créer les coins arrondis
        r = corner_radius
        for i in range(h):
            for j in range(w):
                # Vérifier les quatre coins
                if (j < r and i < r and (j-r)**2 + (i-r)**2 >= r**2) or \
                    (j < r and i >= h-r and (j-r)**2 + (i-(h-r))**2 >= r**2) or \
                    (j >= w-r and i < r and (j-(w-r))**2 + (i-r)**2 >= r**2) or \
                    (j >= w-r and i >= h-r and (j-(w-r))**2 + (i-(h-r))**2 >= r**2):
                    mask[i, j] = 0
                else:
                    mask[i, j] = 255
                        
        # Créer l'image de fond
        color_array = np.array(bg_color).astype('uint8')
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(3):  # RGB channels
            bg[:, :, i] = color_array[i]
        
        return bg, mask/255.0  # Normaliser le masque 

    def _create_subtitle_clip(self, txt, video_height):
        """
        Crée un clip de sous-titre stylisé avec fond arrondi, optimisé pour les mots individuels.
        Le positionnement est géré séparément dans concatenate_videos.
        
        Args:
            txt (str): Texte du sous-titre (un mot individuel)
            video_height (int): Hauteur de la vidéo (non utilisé pour le positionnement)
            
        Returns:
            CompositeVideoClip: Clip du sous-titre
        """
        # Paramètres des sous-titres tirés de la configuration
        font_size = self.config["subtitles"].get("font_size", 70)
        bg_color = self.config["subtitles"].get("background_color", [220, 20, 20])
        text_color = self.config["subtitles"].get("text_color", "#ffffff")
        stroke_color = self.config["subtitles"].get("stroke_color", "#000000")
        stroke_width = self.config["subtitles"].get("stroke_width", 1)
        corner_radius = self.config["subtitles"].get("corner_radius", 15)
        padding_x = self.config["subtitles"].get("padding_x", 20)
        padding_y = self.config["subtitles"].get("padding_y", 10)
        
        # Adaptations pour les mots individuels
        # Augmentation de la taille du texte pour les mots courts
        adjusted_font_size = font_size
        if len(txt.strip()) <= 3:
            adjusted_font_size = int(font_size * 1.3)  # 30% plus grand pour les petits mots
        
        # Création du texte avec options optimisées
        text_clip = TextClip(
            text=txt.strip(),
            font_size=adjusted_font_size,
            color=text_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            font=self.config["video"]["font"]
        )
        
        # Obtenir la taille du texte et ajouter une marge
        text_w, text_h = text_clip.size
        bg_w, bg_h = text_w + 2*padding_x, text_h + 2*padding_y
        
        # Création du fond avec coins arrondis
        bg_img, mask_img = self._make_background((bg_w, bg_h), bg_color, corner_radius)
        
        # Création d'un clip de couleur pour le fond
        bg_clip = ColorClip(size=(bg_w, bg_h), color=bg_color)
        
        # Création d'un clip image pour le masque
        mask_clip = ImageClip(mask_img, is_mask=True)
        
        # Application du masque au fond
        bg_clip = bg_clip.with_mask(mask_clip)
        
        # Positionnement du texte au centre du fond
        text_clip = text_clip.with_position('center')
        
        # Composition du texte et du fond
        final_clip = CompositeVideoClip([bg_clip, text_clip], size=(bg_w, bg_h))
        
        return final_clip

    def _format_time(self, seconds: float) -> str:
        """
        Convertit un nombre de secondes en format SRT (HH:MM:SS,mmm).
        
        Args:
            seconds (float): Nombre de secondes
            
        Returns:
            str: Temps formaté pour SRT
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remaining = seconds % 60
        milliseconds = int((seconds_remaining % 1) * 1000)
        seconds = int(seconds_remaining)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}" 