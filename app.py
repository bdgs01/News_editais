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

def scrape_noticias():
    response = requests.get('https://www.fapema.br/category/noticias/')
    soup = BeautifulSoup(response.content, 'html.parser')
    
    noticias_atuais = []
    items = soup.find_all('div', class_='search-result-item')
    
    for item in items:
        titulo_elem = item.find('a')
        autor_elem = item.find('span', class_='search-result-author')
        resumo_elem = item.find('div', class_='search-result-excerpt')
        
        if titulo_elem:
            noticia = {
                'titulo': titulo_elem.text.strip(),
                'link': titulo_elem.get('href'),
                'autor': autor_elem.text.strip() if autor_elem else 'Sem autor',
                'resumo': resumo_elem.text.strip() if resumo_elem else 'Sem resumo',
                'data_captura': datetime.now().isoformat()
            }
            noticias_atuais.append(noticia)
    
    return noticias_atuais

def detectar_novas_noticias(noticias_atuais, noticias_vistas):
    links_vistas = [n['link'] for n in noticias_vistas]
    novas = [n for n in noticias_atuais if n['link'] not in links_vistas]
    return novas

@app.route('/noticias', methods=['GET'])
def get_noticias():
    noticias_vistas = carregar_noticias_vistas()
    noticias_atuais = scrape_noticias()
    novas_noticias = detectar_novas_noticias(noticias_atuais, noticias_vistas)
    
    salvar_noticias_vistas(noticias_atuais)
    
    return jsonify({
        'novas_noticias': novas_noticias,
        'total_novas': len(novas_noticias),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/todas-noticias', methods=['GET'])
def get_todas_noticias():
    noticias = carregar_noticias_vistas()
    return jsonify({
        'noticias': noticias,
        'total': len(noticias)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
