import os
import json
from pathlib import Path
from typing import Optional
import boto3
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

class StorageManager:
    def __init__(self, config: dict):
        self.config = config
        self.local_path = Path(self.config["storage"]["local_path"])


    def save_video(self, video_path: str, filename: Optional[str] = None) -> str:
        """
        Sauvegarde la vidéo localement et dans le cloud si configuré.
        
        Args:
            video_path (str): Chemin de la vidéo à sauvegarder
            filename (Optional[str]): Nom du fichier de sortie
            
        Returns:
            str: Chemin final de la vidéo sauvegardée
        """

        # Génération du nom de fichier
        if not filename:
            filename = Path(video_path).name
        
        # Sauvegarde locale
        local_path = self.local_path / filename
        Path(video_path).rename(local_path)
            
        return str(local_path)