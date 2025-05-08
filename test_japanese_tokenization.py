#!/usr/bin/env python3
"""
Script de test pour le découpage des mots japonais avec Fugashi
"""

from fugashi import Tagger
import unicodedata
import re

def tokenize_japanese_fugashi(text):
    """
    Découpe un texte japonais en mots en utilisant Fugashi.
    """
    tagger = Tagger()
    tokens = []
    for word in tagger(text):
        token = {
            'surface': word.surface,  # Forme de surface (texte)
            'feature': word.feature.pos,  # Partie du discours (nom, verbe, etc.)
            'lemma': word.feature.lemma if word.feature.lemma else word.surface  # Forme de base
        }
        tokens.append(token)
    return tokens

def tokenize_japanese_simple(text):
    """
    Découpe un texte japonais en utilisant une expression régulière simple.
    """
    pattern = r'[\p{Han}\p{Hiragana}\p{Katakana}]+|[a-zA-Z0-9]+|[.,!?;]'
    words = re.findall(pattern, text, re.UNICODE)
    return words

def get_unicode_info(char):
    """
    Retourne les informations Unicode pour un caractère.
    """
    try:
        return {
            'char': char,
            'name': unicodedata.name(char),
            'category': unicodedata.category(char)
        }
    except ValueError:
        return {
            'char': char,
            'name': 'Unknown',
            'category': 'Unknown'
        }

def analyze_text(text):
    """
    Analyse un texte japonais et montre différentes informations.
    """
    print(f"\nTexte d'entrée: {text}")
    
    # Analyse Unicode
    print("\nAnalyse Unicode par caractère:")
    for char in text:
        if char.strip():  # Ignorer les espaces
            info = get_unicode_info(char)
            print(f"{info['char']} - {info['name']} ({info['category']})")
    
    # Découpage avec Fugashi
    print("\nDécoupage avec Fugashi:")
    tokens = tokenize_japanese_fugashi(text)
    for i, token in enumerate(tokens):
        print(f"{i+1}. {token['surface']} - {token['feature']} (Forme de base: {token['lemma']})")
    
    # Découpage simple
    print("\nDécoupage avec regex simple:")
    words = tokenize_japanese_simple(text)
    for i, word in enumerate(words):
        print(f"{i+1}. {word}")

def main():
    examples = [
        "こんにちは、私の名前はマリーです。", # Bonjour, je m'appelle Marie.
        "東京駅で新幹線に乗りました。",  # J'ai pris le Shinkansen à la gare de Tokyo.
        "アニメとマンガが大好きです。",  # J'aime beaucoup les anime et les manga.
        "すしとラーメンは日本の有名な料理です。"  # Les sushis et les ramen sont des plats japonais célèbres.
    ]
    
    for example in examples:
        analyze_text(example)
        print("\n" + "="*50)
    
    # Permettre à l'utilisateur d'entrer son propre texte
    custom_text = input("\nEntrez un texte japonais à analyser (ou appuyez sur Entrée pour quitter): ")
    if custom_text:
        analyze_text(custom_text)

if __name__ == "__main__":
    main() 