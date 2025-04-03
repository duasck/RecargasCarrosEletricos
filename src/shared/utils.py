import random
import json
import os

def gera_coordenadas():
    return {
        "lat": random.uniform(-23.56, -23.54),
        "lon": random.uniform(-46.66, -46.62)
    }

def carregar_dados():
    try:
        with open('shared/dados_clientes.json', 'r') as f:
            clientes = json.load(f)
        with open('shared/dados_pontos.json', 'r') as f:
            pontos = json.load(f)
        return clientes, pontos
    except FileNotFoundError:
        return [], []