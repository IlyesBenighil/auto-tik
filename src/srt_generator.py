#!/usr/bin/env python3
import argparse
import os
import logging
import whisperx
import torch
import sys
import re
from pathlib import Path
from moviepy import AudioFileClip, concatenate_audioclips

logger = logging.getLogger(__name__)

class SRTGenerator:
    def __init__(self, config: dict):
        """
        Initialise le générateur de sous-titres SRT.
        """
        self.config = config
        self.temp_dir = Path(config["path_assets"]["temp"])
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_srt(self, audio_infos: list) -> str:
        """
        Génère un fichier SRT à partir des informations audio, avec un sous-titre par mot.
        Prend en compte la pause de 3 secondes entre la question et la réponse.
        
        Args:
            audio_infos (list): Liste des informations audio [{
                'path': str,  # Chemin du fichier audio
                'text': str,  # Texte correspondant
                'duration': float,  # Durée en secondes
                'start_time': float,  # Temps de début
                'end_time': float  # Temps de fin
                'is_question': bool,  # Optional, indique si c'est une question
                'is_answer': bool,  # Optional, indique si c'est une réponse
            }]
            
        Returns:
            str: Chemin du fichier SRT généré
        """
        try:
            # Générer le nom du fichier SRT
            srt_path = str(self.temp_dir / "subtitles.srt")
            
            # Générer le fichier SRT
            logger.info("Génération du fichier SRT mot par mot...")
            
            # Créer une liste pour stocker tous les mots avec leurs timings
            all_words = []
            
            # Vérifier si word_by_word est activé
            word_by_word = self.config["subtitles"].get("word_by_word", True)
            
            # Durée du timer entre question et réponse
            timer_duration = 3.0
            
            # Parcourir tous les segments audio
            for i, info in enumerate(audio_infos):
                # Vérifier si ce segment doit être ajusté en fonction du segment précédent
                if i > 0:
                    prev_info = audio_infos[i-1]
                    
                    # Si le segment précédent était une question, vérifier si nous devons ajouter un timer
                    if prev_info.get('is_question', False) and not info.get('is_answer', False):
                        # Si ce n'est pas explicitement marqué comme une réponse,
                        # aucun timer n'est nécessaire
                        pass
                    elif prev_info.get('is_question', False) and info.get('is_answer', False):
                        # Si segment précédent = question et segment actuel = réponse,
                        # vérifier si le timer est déjà inclus dans le timing
                        expected_start = prev_info['end_time'] + timer_duration
                        if info['start_time'] < expected_start:
                            # Ajuster le timing pour inclure le timer
                            logger.info(f"Ajout du timer entre question et réponse pour le segment {i}")
                            offset = expected_start - info['start_time']
                            info['start_time'] = expected_start
                            info['end_time'] += offset
                
                # Diviser le texte en mots
                if word_by_word:
                    words = self._split_text_into_words(info['text'])
                else:
                    # Si word_by_word est désactivé, traiter le texte entier comme un seul segment
                    words = [info['text']]
                
                # S'il n'y a pas de mots, passer à l'info suivante
                if not words:
                    continue
                
                # Calculer la durée par mot (répartition uniforme)
                segment_duration = info['end_time'] - info['start_time']
                word_duration = segment_duration / len(words)
                
                # Attribuer les timings à chaque mot
                current_time = info['start_time']
                for word in words:
                    word_info = {
                        'text': word,
                        'start_time': current_time,
                        'end_time': current_time + word_duration,
                        'is_question': info.get('is_question', False),
                        'is_answer': info.get('is_answer', False)
                    }
                    all_words.append(word_info)
                    current_time += word_duration
            
            # Écrire le fichier SRT
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                for i, word_info in enumerate(all_words, 1):
                    # Écrire le numéro du sous-titre
                    srt_file.write(f"{i}\n")
                    
                    # Écrire les timings
                    start_formatted = self._format_time(word_info['start_time'])
                    end_formatted = self._format_time(word_info['end_time'])
                    srt_file.write(f"{start_formatted} --> {end_formatted}\n")
                    
                    # Écrire le texte du mot
                    srt_file.write(f"{word_info['text']}\n\n")
            
            logger.info(f"Fichier SRT créé avec {len(all_words)} mots: {srt_path}")
            return srt_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du SRT: {str(e)}")
            raise
    
    def transcribe_with_timestamps(self, audio_infos: list) -> str:
        """
        Utilise la fonction transcribe_with_timestamps pour générer un fichier SRT à partir des fichiers audio,
        en tenant compte de la pause de 3 secondes entre chaque question et sa réponse correspondante.
        
        Args:
            audio_infos (list): Liste des informations audio avec les flags is_question et is_answer
            
        Returns:
            str: Chemin du fichier SRT généré
        """
        try:
            # Vérifier qu'il y a au moins un fichier audio
            if not audio_infos or len(audio_infos) == 0:
                raise ValueError("Aucune information audio fournie")
            
            # Générer le nom du fichier SRT
            srt_path = str(self.temp_dir / "subtitles.srt")
            
            # Si on utilise la transcription WhisperX mot par mot
            if self.config["subtitles"].get("use_whisperx", False):
                logger.info("Utilisation de WhisperX pour la transcription mot par mot...")
                
                # Transcrire chaque fichier audio séparément
                all_segments = []
                total_offset = 0
                
                # Durée du timer entre question et réponse
                timer_duration = 3.0
                
                for i, info in enumerate(audio_infos):
                    audio_path = info['path']
                    # Vérifier que le fichier existe
                    if not os.path.exists(audio_path):
                        logger.warning(f"Fichier audio {audio_path} non trouvé, ignoré")
                        continue
                    
                    # Paramètres de configuration
                    model_size = self.config["subtitles"].get("model_size", "medium")
                    language = self.config["subtitles"].get("language", "fr")
                    device = "cpu"  # Utiliser CPU par défaut pour plus de compatibilité
                    
                    # Générer un fichier SRT temporaire pour ce segment
                    temp_srt = str(self.temp_dir / f"temp_subtitles_{i}.srt")
                    
                    # Transcription du segment
                    logger.info(f"Transcription du segment {i+1}/{len(audio_infos)}...")
                    transcribe_with_timestamps(
                        audio_file=audio_path,
                        output_file=temp_srt,
                        model_size=model_size,
                        language=language,
                        device=device
                    )
                    
                    # Charger les sous-titres générés
                    with open(temp_srt, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extraire les segments et ajuster les timings
                    segments = self._parse_srt_file(content)
                    
                    # Ajouter les métadonnées du segment
                    for segment in segments:
                        segment['start'] += total_offset
                        segment['end'] += total_offset
                        segment['is_question'] = info.get('is_question', False)
                        segment['is_answer'] = info.get('is_answer', False)
                        all_segments.append(segment)
                    
                    # Mettre à jour l'offset total
                    total_offset += info['duration']
                    
                    # Si c'est une question, ajouter le timer pour la réponse
                    # mais seulement si le segment suivant est une réponse
                    if info.get('is_question', False) and i+1 < len(audio_infos) and audio_infos[i+1].get('is_answer', False):
                        logger.info(f"Ajout d'un timer de {timer_duration}s après la question {i+1}")
                        total_offset += timer_duration
                
                # Écrire tous les segments dans le fichier SRT final
                with open(srt_path, "w", encoding="utf-8") as srt_file:
                    for i, segment in enumerate(all_segments, 1):
                        # Écrire le numéro du sous-titre
                        srt_file.write(f"{i}\n")
                        
                        # Écrire les timings
                        start_formatted = self._format_time(segment['start'])
                        end_formatted = self._format_time(segment['end'])
                        srt_file.write(f"{start_formatted} --> {end_formatted}\n")
                        
                        # Écrire le texte
                        srt_file.write(f"{segment['text']}\n\n")
                
                logger.info(f"Fichier SRT créé avec {len(all_segments)} segments: {srt_path}")
            
            # Sinon, utiliser l'approche par défaut (répartition uniforme)
            else:
                logger.info("Génération du fichier SRT mot par mot par répartition uniforme...")
                srt_path = self.generate_srt(audio_infos)
            
            return srt_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {str(e)}")
            raise
    
    def _combine_audio_files(self, audio_infos: list) -> str:
        """
        Combine plusieurs fichiers audio en un seul fichier temporaire.
        
        Args:
            audio_infos (list): Liste des informations audio
            
        Returns:
            str: Chemin du fichier audio combiné
        """
        try:
            # Créer le fichier audio combiné
            combined_path = str(self.temp_dir / "combined_audio.wav")
            
            # Charger tous les fichiers audio
            audio_clips = []
            for info in audio_infos:
                audio_path = info['path']
                # Vérifier que le fichier existe
                if not os.path.exists(audio_path):
                    logger.warning(f"Fichier audio {audio_path} non trouvé, ignoré")
                    continue
                    
                try:
                    # Charger l'audio
                    audio_clip = AudioFileClip(audio_path)
                    audio_clips.append(audio_clip)
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement du fichier audio {audio_path}: {str(e)}")
            
            if not audio_clips:
                raise ValueError("Aucun fichier audio valide trouvé")
                
            # Concaténer les clips audio
            combined_audio = concatenate_audioclips(audio_clips)
            
            # Sauvegarder le fichier combiné
            combined_audio.write_audiofile(combined_path, 
                                          fps=44100, 
                                          nbytes=2, 
                                          codec='pcm_s16le',
                                          verbose=False,
                                          logger='bar')
            
            # Fermer les clips pour libérer les ressources
            for clip in audio_clips:
                clip.close()
                
            logger.info(f"Fichier audio combiné créé: {combined_path}")
            return combined_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la combinaison des fichiers audio: {str(e)}")
            raise
    
    def _split_text_into_words(self, text: str) -> list:
        """
        Divise un texte en mots individuels.
        
        Args:
            text (str): Texte à diviser
            
        Returns:
            list: Liste des mots
        """
        # Nettoyer le texte et le diviser en mots
        # On conserve la ponctuation avec le mot précédent
        words = re.findall(r'\w+(?:[.,!?;])?|\S', text)
        return [word for word in words if word.strip()]
            
    def _format_time(self, seconds: float) -> str:
        """
        Convertit les secondes en format SRT: HH:MM:SS,mmm
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{int((seconds - int(seconds)) * 1000):03d}"

    def _parse_srt_file(self, content: str) -> list:
        """
        Parse un fichier SRT et extrait les segments.
        
        Args:
            content (str): Contenu du fichier SRT
            
        Returns:
            list: Liste des segments [{start, end, text}]
        """
        segments = []
        lines = content.strip().split('\n')
        i = 0
        
        while i < len(lines):
            # Ignorer les numéros de segment
            if lines[i].strip().isdigit():
                i += 1
                
                # Extraire les timings
                if i < len(lines):
                    timings = lines[i].strip()
                    start_str, end_str = timings.split(' --> ')
                    start = self._parse_srt_time(start_str)
                    end = self._parse_srt_time(end_str)
                    i += 1
                    
                    # Extraire le texte
                    text = ""
                    while i < len(lines) and lines[i].strip():
                        text += lines[i].strip() + " "
                        i += 1
                    
                    segments.append({
                        'start': start,
                        'end': end,
                        'text': text.strip()
                    })
            i += 1
        
        return segments
    
    def _parse_srt_time(self, time_str: str) -> float:
        """
        Convertit un temps au format SRT (HH:MM:SS,mmm) en secondes.
        
        Args:
            time_str (str): Temps au format SRT
            
        Returns:
            float: Temps en secondes
        """
        # Format: HH:MM:SS,mmm
        hours, minutes, seconds = time_str.replace(',', '.').split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

def transcribe_with_timestamps(audio_file, output_file, model_size="medium", language="fr", device="cpu"):
    """
    Transcrit un fichier audio et génère un fichier SRT avec un timing pour chaque mot
    en utilisant WhisperX.
    """
    # Vérifier que le fichier existe
    if not os.path.exists(audio_file):
        print(f"Le fichier {audio_file} n'existe pas.")
        return
    
    # Vérification du device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Déterminer le compute_type en fonction du device
    compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"Chargement du modèle (device: {device}, compute_type: {compute_type})...")
    try:
        # Charger le modèle Whisper et transcrire l'audio
        model = whisperx.load_model(model_size, device=device, compute_type=compute_type)
        print(f"Transcription en cours avec le modèle {model_size} sur {device}...")
        
        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, language=language)
        
        # Alignement au niveau des mots
        print("Alignement des mots...")
        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        aligned = whisperx.align(result["segments"], model_a, metadata, audio, device=device)
        
        # Générer le fichier SRT
        print("Génération du fichier SRT...")
        generate_srt_from_words(aligned["word_segments"], output_file)
        
        print(f"Transcription terminée! Fichier SRT créé: {output_file}")
        print(f"Nombre total de mots: {len(aligned['word_segments'])}")
        return output_file
        
    except ValueError as e:
        if "float16 compute type" in str(e):
            print("Erreur de type de calcul détectée: le CPU ne supporte pas float16.")
            print("Réessai avec compute_type=int8...")
            model = whisperx.load_model(model_size, device=device, compute_type="int8")
            audio = whisperx.load_audio(audio_file)
            result = model.transcribe(audio, language=language)
            
            print("Alignement des mots...")
            model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
            aligned = whisperx.align(result["segments"], model_a, metadata, audio, device=device)
            
            print("Génération du fichier SRT...")
            generate_srt_from_words(aligned["word_segments"], output_file)
            
            print(f"Transcription terminée! Fichier SRT créé: {output_file}")
            print(f"Nombre total de mots: {len(aligned['word_segments'])}")
            return output_file
        else:
            raise e
    except RuntimeError as e:
        if "CUDA" in str(e) or "cuDNN" in str(e):
            print("Erreur CUDA détectée.")
            print("Message d'erreur original:", str(e))
            print("\nSolutions possibles:")
            print("1. Utilisez l'option --device cpu pour utiliser le CPU au lieu du GPU")
            print("2. Installez la bonne version de cuDNN (voir README)")
            print("3. Installez une version compatible de PyTorch: pip install torch==1.10.0 torchaudio==0.10.0")
            sys.exit(1)
        else:
            raise e

def generate_srt_from_words(word_segments, output_file):
    """
    Génère un fichier SRT à partir des segments de mots de WhisperX.
    Chaque mot sera un segment SRT distinct.
    """
    with open(output_file, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(word_segments, 1):
            word = segment["word"]
            start_time = segment["start"]
            end_time = segment["end"]
            
            # Écrire le segment SRT
            srt_file.write(f"{i}\n")
            start_formatted = format_time(start_time)
            end_formatted = format_time(end_time)
            srt_file.write(f"{start_formatted} --> {end_formatted}\n")
            srt_file.write(f"{word}\n\n")

def format_time(seconds):
    """
    Convertit les secondes en format SRT: HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{int((seconds - int(seconds)) * 1000):03d}"

def main():
    parser = argparse.ArgumentParser(description='Transcrit un fichier audio en fichier SRT avec timing par mot en utilisant WhisperX')
    parser.add_argument('audio_file', help='Chemin vers le fichier audio à transcrire')
    parser.add_argument('--output', '-o', help='Chemin du fichier SRT de sortie', default=None)
    parser.add_argument('--model', '-m', help='Taille du modèle Whisper à utiliser', default="medium", 
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument('--language', '-l', help='Code de langue à utiliser', default="fr")
    parser.add_argument('--device', '-d', help='Périphérique à utiliser (cuda ou cpu)', choices=["cuda", "cpu"], default=None)
    parser.add_argument('--compute_type', help='Type de calcul à utiliser', choices=["float16", "int8", "float32"], default=None)
    
    args = parser.parse_args()
    
    # Si le fichier de sortie n'est pas spécifié, utiliser le même nom que le fichier d'entrée
    if args.output is None:
        base_name = os.path.splitext(args.audio_file)[0]
        args.output = f"{base_name}.srt"
    
    transcribe_with_timestamps(args.audio_file, args.output, args.model, args.language, args.device)

if __name__ == "__main__":
    main()  