import random
import json
from pathlib import Path
from typing import List, Optional

class ThemeSelector:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = self._load_config(config_path)
        self.themes: List[str] = self.config["themes"]
        self.last_theme: Optional[str] = None
        self._load_history()

    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier settings.json"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_history(self):
        """Charge l'historique des thèmes utilisés"""
        history_path = Path("assets/temp/theme_history.json")
        if history_path.exists():
            with open(history_path, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def _save_history(self):
        """Sauvegarde l'historique des thèmes utilisés"""
        history_path = Path("assets/temp/theme_history.json")
        with open(history_path, 'w') as f:
            json.dump(self.history, f)

    def get_next_theme(self, strategy: str = "random") -> str:
        """
        Sélectionne le prochain thème selon la stratégie spécifiée.
        
        Args:
            strategy (str): 'random' pour une sélection aléatoire,
                          'cycle' pour une sélection cyclique
        
        Returns:
            str: Le thème sélectionné
        """
        if strategy == "random":
            # Évite de répéter le dernier thème utilisé
            available_themes = [t for t in self.themes if t != self.last_theme]
            theme = random.choice(available_themes)
        else:  # cycle
            if not self.history:
                theme = self.themes[0]
            else:
                current_index = self.themes.index(self.history[-1])
                next_index = (current_index + 1) % len(self.themes)
                theme = self.themes[next_index]

        self.last_theme = theme
        self.history.append(theme)
        self._save_history()
        
        return theme 