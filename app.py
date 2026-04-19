import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from flask import Flask, jsonify, request
import threading
import time

app = Flask(__name__)

ARQUIVO_NOTICIAS = 'noticias_vistas.json'

# Palavras-chave relacionadas a editais
PALAVRAS_EDITAL = [
    'edital', 'editais', 'convocação', 'seleção', 'processo seletivo',
    'inscrição', 'inscrições', 'candidatura', 'candidaturas',
    'chamada pública', 'chamadas públicas', 'licitação', 'licitações',
    'concurso', 'concursos', 'bolsa', 'bolsas', 'auxílio', 'auxílios',
    'financiamento', 'financiamentos', 'subsídio', 'subsídios',
    'fomento', 'apoio', 'investimento', 'investimentos',
    'resultado', 'resultados', 'classificação', 'classificações',
    'homologação', 'homologações', 'recurso', 'recursos',
    'aviso', 'avisos', 'comunicado', 'comunicados'
]

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
    try:
        resposta = requests.get('https://www.fapema.br/category/noticias/', timeout=10)
        sopa = BeautifulSoup(resposta.content, 'html.parser')
        
        noticias_atuais = []
        itens = sopa.find_all('div', class_='search-result-item')
        
        for item in itens:
            elem_titulo = item.find('a')
            elem_autor = item.find('span', class_='search-result-author')
            elem_resumo = item.find('div', class_='search-result-excerpt')
            
            if elem_titulo:
                titulo = elem_titulo.text.strip()
                resumo = elem_resumo.text.strip() if elem_resumo else 'Sem resumo'
                
                noticia = {
                    'titulo': titulo,
                    'link': elem_titulo.get('href'),
                    'autor': elem_autor.text.strip() if elem_autor else 'Sem autor',
                    'resumo': resumo,
                    'data_captura': datetime.now().isoformat(),
                    'eh_edital': detectar_edital(titulo, resumo)
                }
                noticias_atuais.append(noticia)
        
        return noticias_atuais
    except Exception as e:
        print(f"Erro no scraping: {e}")
        return []

def detectar_edital(titulo, resumo):
    texto_completo = (titulo + ' ' + resumo).lower()
    return any(palavra in texto_completo for palavra in PALAVRAS_EDITAL)

def detectar_novas_noticias(noticias_atuais, noticias_vistas):
    links_vistas = [n['link'] for n in noticias_vistas]
    novas = [n for n in noticias_atuais if n['link'] not in links_vistas]
    return novas

def executar_scraping_periodico():
    while True:
        try:
            print(f"[{datetime.now()}] Executando scraping...")
            noticias_vistas = carregar_noticias_vistas()
            noticias_atuais = fazer_scraping()
            noticias_novas = detectar_novas_noticias(noticias_atuais, noticias_vistas)
            
            if noticias_novas:
                todas_noticias = noticias_atuais + noticias_vistas
                salvar_noticias_vistas(todas_noticias)
                print(f"[{datetime.now()}] {len(noticias_novas)} notícia(s) nova(s) encontrada(s)")
            else:
                print(f"[{datetime.now()}] Nenhuma notícia nova")
        except Exception as e:
            print(f"Erro no scraping periódico: {e}")
        
        time.sleep(3600)  # 1 hora

@app.route('/noticias-novas', methods=['GET'])
def obter_noticias_novas():
    filtro = request.args.get('filtro', 'editais').lower()
    
    noticias_vistas = carregar_noticias_vistas()
    noticias_atuais = fazer_scraping()
    noticias_novas = detectar_novas_noticias(noticias_atuais, noticias_vistas)
    
    salvar_noticias_vistas(noticias_atuais)
    
    if filtro == 'editais':
        noticias_novas = [n for n in noticias_novas if n['eh_edital']]
    elif filtro == 'todas':
        pass
    
    return jsonify({
        'noticias_novas': noticias_novas,
        'total_novas': len(noticias_novas),
        'filtro': filtro,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/todas-noticias', methods=['GET'])
def obter_todas_noticias():
    filtro = request.args.get('filtro', 'editais').lower()
    
    noticias = carregar_noticias_vistas()
    
    if filtro == 'editais':
        noticias = [n for n in noticias if n['eh_edital']]
    elif filtro == 'todas':
        pass
    
    return jsonify({
        'noticias': noticias,
        'total': len(noticias),
        'filtro': filtro,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'API funcionando',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    thread_scraping = threading.Thread(target=executar_scraping_periodico, daemon=True)
    thread_scraping.start()
    
    porta = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=porta)
