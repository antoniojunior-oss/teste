import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. Funções de Suporte
def carregar_modelo_seguro(key):
    try:
        if not key: return None
        genai.configure(api_key=key)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if opcao in modelos: return genai.GenerativeModel(opcao)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except Exception as e:
        st.sidebar.error(f"Erro na API: {e}")
        return None

def capturar_site(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza agressiva para performance do sandbox
        for s in soup(['iframe', 'noscript']): s.decompose()
        for s in soup.find_all('script', src=True):
            src = s.get('src', '').lower()
            if any(x in src for x in ['google-analytics', 'facebook', 'hotjar', 'gtm', 'pixel']):
                s.decompose()
        
        return soup.prettify()
    except Exception as e:
        st.error(f"Erro ao capturar site: {e}")
        return None

# 3. Inicialização do Estado
for key in ["codigo_fonte", "scripts_aplicados", "url_atual", "refresh_count"]:
    if key not in st.session_state: st.session_state[key] = "" if key != "refresh_count" else 0

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel de Controle")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Otimizador")
url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Novo Site"):
    if url_input:
        with st.spinner("Capturando estrutura..."):
            html_clonado = capturar_site(url_input)
            if html_clonado:
                st.session_state.url_atual, st.session_state.codigo_fonte = url_input, html_clonado
                st.session_state.scripts_aplicados = ""
                st.rerun()

st.divider()
col_sandbox, col_ia = st.columns([1.1, 0.9])

with col_ia:
    st.subheader("🤖 Assistente de Edição Inteligente")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("Descreva a alteração:", placeholder="Ex: Mudar cor do botão de conversão para verde e disparar alert ao clicar", height=120)
        
        if st.button("✨ Gerar e Otimizar para PageSpeed", use_container_width=True):
            if model:
                with st.spinner("Passo 1: Criando lógica..."):
                    contexto_html = st.session_state.codigo_fonte[:7000]
                    
                    # PROMPT 1: GERAÇÃO DE LÓGICA
                    p1 = f"""Atue como Dev Sênior. Crie apenas o código de alteração (CSS/JS) para: {prompt_usuario}.
                    HTML Contexto: {contexto_html}
                    REGRAS: 
                    1. NÃO repita o HTML base. 
                    2. Retorne APENAS as tags <style> e <script>.
                    3. Se for JS, use seletores específicos."""
                    
                    res1 = model.generate_content(p1).text
                    
                with st.spinner("Passo 2: Otimizando Performance..."):
                    # PROMPT 2: OTIMIZAÇÃO E LIMPEZA (PAGESPEED)
                    p2 = f"""Atue como Especialista em Web Performance. 
                    Otimize o código abaixo para ter impacto ZERO no PageSpeed:
                    CÓDIGO: {res1}
                    
                    REGRAS DE OTIMIZAÇÃO:
                    1. Minifique o CSS e JS.
                    2. Use 'DOMContentLoaded' para não bloquear a renderização.
                    3. Remova qualquer comentário ou espaço desnecessário.
                    4. Retorne EXCLUSIVAMENTE o código final dentro das tags <style> e <script>.
                    5. NUNCA inclua markdown como ```html."""
                    
                    res2 = model.generate_content(p2).text
                    
                    # Limpeza final via Regex/String
                    limpo = res2.replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "").strip()
                    
                    st.session_state.scripts_aplicados = limpo
                    st.toast("Código otimizado aplicado!", icon="⚡")
                    st.rerun()

        if st.session_state.scripts_aplicados:
            with st.expander("📄 Código Otimizado (Pronto para GTM/Site)", expanded=False):
                st.code(st.session_state.scripts_aplicados, language="html")

with col_sandbox:
    st.subheader("🧪 Sandbox")
    if st.session_state.codigo_fonte:
        template = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <base href="{st.session_state.url_atual}/">
                <meta charset="UTF-8">
            </head>
            <body>
                {st.session_state.codigo_fonte}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        st.components.v1.html(template, height=800, scrolling=True)
