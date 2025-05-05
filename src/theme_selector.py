import random
from typing import List

class ThemeSelector:
    def __init__(self, config: dict):
        self.config = config
        self.themes: List[str] = self.config["themes"]


    def get_next_theme(self) -> str:
        """
        Sélectionne le prochain thème selon la stratégie spécifiée.
        Returns:
            str: Le thème sélectionné
        """
        return random.choice(self.themes)
