import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List
from mistralai import Mistral
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class QuestionGenerator:
    def __init__(self, config: dict, num_questions: int = 5):
        """
        Initialise le générateur de questions avec l'API Mistral.
        
        Args:
            num_questions (int): Nombre de questions à générer (par défaut: 5)
        """
        self.config = config
        self.num_questions = num_questions
        print("Initialisation de l'API Mistral...")
        load_dotenv(override=True)
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("La clé API Mistral n'est pas définie. Veuillez définir la variable d'environnement MISTRAL_API_KEY")
        
        # Initialisation avec la nouvelle API
        self.client = Mistral(api_key=api_key)
        print("API Mistral initialisée avec succès!")
        
        # Chargement du prompt depuis le fichier si configuré
        self.prompt_template_unformated = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """
        Charge le template du prompt depuis le fichier.
        
        Returns:
            str: Le contenu du fichier de prompt
        """
        prompt_path = Path(self.config["prompt"]["path"])
        if not prompt_path.exists():
            raise FileNotFoundError(f"Le fichier de prompt n'existe pas: {prompt_path}")
            
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def _format_prompt(self, theme: str) -> str:
        """
        Formate le prompt avec les variables.
        
        Args:
            theme (str): Le thème du quiz
            difficulty (str): Le niveau de difficulté
            
        Returns:
            str: Le prompt formaté
        """
        
        # Utiliser le template chargé depuis le fichier
        prompt = self.prompt_template_unformated
        
        # Variables à remplacer
        replacements = {
            "theme": theme,
            "difficulty": self.config["prompt"]["difficulty"],
            "num_questions": str(self.config["prompt"]["num_questions"]),
            "num_choices": str(self.config["prompt"]["num_choices"])
        }
        # Remplacer les variables dans le prompt
        for var_name, var_value in replacements.items():
            prompt = prompt.replace(f"{{{var_name}}}", var_value)

        return prompt
        
    def _clean_json_string(self, text: str) -> str:
        """Nettoie une chaîne de caractères pour extraire un JSON valide."""
        print("\nTexte original:")
        print(text)
        
        # Supprime les espaces et sauts de ligne au début et à la fin
        text = text.strip()
        
        # Trouve le premier { et le premier } qui suit
        start_idx = text.find("{")
        if start_idx == -1:
            raise ValueError("Aucun JSON trouvé dans la réponse")
            
        # Compte les accolades pour trouver la fin du premier objet JSON
        count = 0
        end_idx = start_idx
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                count += 1
            elif text[i] == '}':
                count -= 1
                if count == 0:
                    end_idx = i
                    break
        
        if end_idx == start_idx:
            raise ValueError("Format JSON invalide")
            
        # Extrait le premier objet JSON
        json_str = text[start_idx:end_idx + 1]
        print("\nPremier JSON extrait:")
        print(json_str)
        
        # Supprime tout HTML et texte après le JSON
        json_str = re.sub(r'</?[^>]+>', '', json_str)
        json_str = re.sub(r'<style[^>]*>.*?</style>', '', json_str, flags=re.DOTALL)  # Supprime les balises style
        json_str = re.sub(r'<script[^>]*>.*?</script>', '', json_str, flags=re.DOTALL)  # Supprime les balises script
        
        # Supprime les sauts de ligne et espaces multiples
        json_str = re.sub(r'\s+', ' ', json_str)
        
        # Supprime les espaces après les { et avant les }
        json_str = re.sub(r'{\s+', '{', json_str)
        json_str = re.sub(r'\s+}', '}', json_str)
        
        # Supprime les espaces autour des :
        json_str = re.sub(r'\s*:\s*', ':', json_str)
        
        # Supprime les espaces autour des virgules
        json_str = re.sub(r'\s*,\s*', ',', json_str)
        
        # Supprime les espaces autour des guillemets
        json_str = re.sub(r'"\s+', '"', json_str)
        json_str = re.sub(r'\s+"', '"', json_str)
        
        print("\nJSON nettoyé:")
        print(json_str)
        
        return json_str
        
    def generate_question(self, theme: str) -> List[Dict[str, Any]]:
        # Utiliser le prompt formaté avec les variables
        prompt = self._format_prompt(theme)
        
        # Structure des messages pour la nouvelle API
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Appel à l'API Mistral avec la nouvelle API
        response = self.client.chat.complete(
            model=self.config["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=5000,
            top_p=0.95
        )
        
        # Récupération de la réponse (nouvelle structure)
        response_text = response.choices[0].message.content
        
        # Nettoyage et parsing du JSON
        json_str = self._clean_json_string(response_text)
        # Parse du JSON
        question_data = json.loads(json_str)
        # Validation de la structure
        if "questions" not in question_data or not isinstance(question_data["questions"], list):
            raise ValueError("Format de réponse invalide: 'questions' doit être une liste")
        
        # Validation de chaque question
        validated_questions = []
        for question in question_data["questions"]:
            if self.validate_question(question):
                validated_questions.append({
                    'question': question['question'].strip(),
                    'choices': question['choices'],
                    'answer': question['answer'].strip()
                })
        
        if not validated_questions:
            raise ValueError("Aucune question valide n'a été générée")
        
        # Limite le nombre de questions au nombre demandé
        validated_questions = validated_questions[:self.num_questions]
        
        # Si on n'a pas assez de questions valides, on génère à nouveau
        if len(validated_questions) < self.num_questions:
            print(f"Pas assez de questions valides ({len(validated_questions)}/{self.num_questions}), nouvelle tentative...")
            return self.generate_question(theme)
        
        return validated_questions 

    def validate_question(self, question_data: Dict) -> bool:
        """
        Valide le format et le contenu d'une question.
        
        Args:
            question_data (Dict): Les données de la question à valider
            
        Returns:
            bool: True si la question est valide, False sinon
        """
        num_choices = self.config["prompt"]["num_choices"]
        try:
            required_fields = ["question", "choices", "answer"]
            if not all(key in question_data for key in required_fields):
                return False

            # Vérification de la longueur de la question
            if len(question_data["question"]) > self.config["size_question"]:
                return False

            # Vérification des choix
            if not isinstance(question_data["choices"], dict) or len(question_data["choices"]) != num_choices:
                return False

            # Vérification que tous les choix sont présents
            for i in range(1, num_choices + 1):
                if str(i) not in question_data["choices"]:
                    return False

            # Vérification de la réponse
            if question_data["answer"] not in [str(i) for i in range(1, num_choices + 1)]:
                return False

            return True

        except Exception:
            return False 