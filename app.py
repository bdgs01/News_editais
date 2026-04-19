import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

ARQUIVO_NOTICIAS = 'noticias_vistas.json'

def carregar_noticias_vistas():
    try:
        with open(ARQUIVO_NOTICIAS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_noticias_vistas(noticias):
    with open(ARQUIVO_NOTICIAS, 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

def fazer_scraping():
    resposta = requests.get('https://www.fapema.br/category/noticias/')
    sopa = BeautifulSoup(resposta.content, 'html.parser')
    
    noticias_atuais = []
    itens = sopa.find_all('div', class_='search-result-item')
    
    for item in itens:
        elem_titulo = item.find('a')
        elem_autor = item.find('span', class_='search-result-author')
        elem_resumo = item.find('div', class_='search-result-excerpt')
        
        if elem_titulo:
            noticia = {
                'titulo': elem_titulo.text.strip(),
                'link': elem_titulo.get('href'),
                'autor': elem_autor.text.strip() if elem_autor else 'Sem autor',
                'resumo': elem_resumo.text.strip() if elem_resumo else 'Sem resumo',
                'data_captura': datetime.now().isoformat()
            }
            noticias_atuais.append(noticia)
    
    return noticias_atuais

def detectar_novas_noticias(noticias_atuais, noticias_vistas):
    links_vistas = [n['link'] for n in noticias_vistas]
    novas = [n for n in noticias_atuais if n['link'] not in links_vistas]
    return novas

@app.route('/noticias-novas', methods=['GET'])
def obter_noticias_novas():
    noticias_vistas = carregar_noticias_vistas()
    noticias_atuais = fazer_scraping()
    noticias_novas = detectar_novas_noticias(noticias_atuais, noticias_vistas)
    
    salvar_noticias_vistas(noticias_atuais)
    
    return jsonify({
        'noticias_novas': noticias_novas,
        'total_novas': len(noticias_novas),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/todas-noticias', methods=['GET'])
def obter_todas_noticias():
    noticias = carregar_noticias_vistas()
    return jsonify({
        'noticias': noticias,
        'total': len(noticias)
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'API funcionando',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=porta)
