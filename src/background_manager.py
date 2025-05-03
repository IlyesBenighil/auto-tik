import os
import logging
import requests
from pathlib import Path
import cv2
import numpy as np
from typing import Dict, Optional
from dotenv import load_dotenv
import re
import random

# Chargement des variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class BackgroundManager:
    def __init__(self):
        """
        Initialise le gestionnaire de fonds vidéo.
        """
        self.api_key = os.getenv('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError("La clé API Pexels n'est pas définie dans le fichier .env")
            
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {
            "Authorization": self.api_key
        }
        self.videos_dir = Path("assets/backgrounds/videos")
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
    def _apply_blur(self, video_path: str, output_path: str, blur_strength: int = 31):
        """
        Applique un flou sur la vidéo en utilisant FFmpeg.
        
        Args:
            video_path (str): Chemin de la vidéo source
            output_path (str): Chemin de sortie
            blur_strength (int): Force du flou (doit être un nombre impair positif)
        """
        try:
            # S'assurer que blur_strength est un nombre impair positif
            if blur_strength % 2 == 0:
                blur_strength += 1
            if blur_strength < 1:
                blur_strength = 1
                
            # Utilisation de FFmpeg pour appliquer le flou
            import subprocess
            
            # D'abord, obtenir la durée de la vidéo source
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            duration = subprocess.check_output(probe_cmd).decode().strip()
            if not duration:
                raise Exception("Impossible de déterminer la durée de la vidéo source")
            
            # Construction de la commande FFmpeg avec des métadonnées explicites
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'gblur=sigma={blur_strength//2}',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-movflags', '+faststart',  # Optimisation pour le streaming
                '-metadata', f'duration={duration}',  # Métadonnée explicite de durée
                '-y',  # Écraser le fichier de sortie s'il existe
                output_path
            ]
            
            # Exécution de la commande
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur FFmpeg: {stderr.decode()}")
            
            # Vérification que la vidéo a été correctement créée
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception("La vidéo floutée n'a pas été correctement créée")
            
            # Vérification finale de la durée
            verify_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                output_path
            ]
            
            final_duration = subprocess.check_output(verify_cmd).decode().strip()
            if not final_duration:
                raise Exception("La vidéo de sortie n'a pas de durée valide")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application du flou: {str(e)}")
            raise
            
    def _download_video(self, video_url: str, output_path: str):
        """
        Télécharge une vidéo depuis une URL.
        
        Args:
            video_url (str): URL de la vidéo
            output_path (str): Chemin de sortie
        """
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de la vidéo: {str(e)}")
            raise
            
    def _to_snake_case(self, text: str) -> str:
        """
        Convertit un texte en snake_case.
        
        Args:
            text (str): Le texte à convertir
            
        Returns:
            str: Le texte en snake_case
        """
        # Remplacer les espaces et caractères spéciaux par des underscores
        text = re.sub(r'[^a-zA-Z0-9]+', '_', text)
        # Convertir en minuscules
        text = text.lower()
        # Supprimer les underscores multiples
        text = re.sub(r'_+', '_', text)
        # Supprimer les underscores au début et à la fin
        text = text.strip('_')
        return text

    def get_background_video(self, theme: str) -> Optional[str]:
        """
        Récupère une vidéo de fond pour un thème donné.
        Si une vidéo existe déjà pour ce thème, elle est réutilisée.
        Sinon, une nouvelle vidéo est téléchargée.
        
        Args:
            theme (str): Thème de la vidéo (utilisé directement comme mot-clé de recherche)
            
        Returns:
            Optional[str]: Chemin de la vidéo floutée, ou None si erreur
        """
        try:
            # Conversion du thème en snake_case
            theme_snake = self._to_snake_case(theme)
            
            # Recherche de vidéos sur Pexels avec le thème comme mot-clé
            search_url = f"{self.base_url}/search?query={theme}&per_page=1"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('videos'):
                logger.warning(f"Aucune vidéo trouvée pour le thème: {theme}")
                # On prend une vidéo au hasard parmi tous les thèmes
                all_videos = []
                for root, _, files in os.walk(self.videos_dir):
                    for file in files:
                        if file.endswith('.mp4'):
                            all_videos.append(os.path.join(root, file))
                if all_videos:
                    random_video = random.choice(all_videos)
                    logger.info(f"Utilisation d'une vidéo aléatoire: {random_video}")
                    return str(random_video)
                return None
                
            # Récupération de la meilleure qualité disponible
            video = data['videos'][0]
            video_files = video['video_files']
            best_quality = max(video_files, key=lambda x: x['width'])
            
            # Création du chemin final avec le thème en snake_case
            final_path = self.videos_dir / f"{theme_snake}_{video['id']}_blurred.mp4"
            
            # Si la vidéo n'existe pas déjà, on la télécharge et on applique le flou
            if not final_path.exists():
                temp_path = self.videos_dir / f"temp_{theme_snake}_{video['id']}.mp4"
                self._download_video(best_quality['link'], str(temp_path))
                self._apply_blur(str(temp_path), str(final_path))
                
                # Nettoyage
                if temp_path.exists():
                    temp_path.unlink()
            
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vidéo de fond: {str(e)}")
            return None 