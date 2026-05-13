import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Full Modular", layout="wide", page_icon="🚗")

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
    """Clona e segmenta o site em Head, Body e Footer."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza de trackers
        for s in soup(['script', 'iframe']):
            src = s.get('src', '')
            if any(x in src for x in ['google-analytics', 'facebook', 'gtm']): s.decompose()
        
        # Segmentação Modular
        head_content = "".join([str(item) for item in soup.head.contents]) if soup.head else ""
        
        footer_tag = soup.find('footer')
        footer_content = str(footer_tag) if footer_tag else ""
        
        if footer_tag:
            footer_tag.decompose()
        body_content = "".join([str(item) for item in soup.body.contents]) if soup.body else ""
        
        return {
            "head": head_content,
            "body": body_content,
            "footer": footer_content
        }
    except Exception as e:
        st.error(f"Erro ao capturar site: {e}")
        return None

# 3. Estado da Sessão
if "site_partes" not in st.session_state:
    st.session_state.site_partes = {"head": "", "body": "", "footer": ""}
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""

# 4. Interface e Lógica
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

st.title("🚗 IA Dealer: Editor Full Modular")
url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Estrutura Completa"):
    if url_input:
        with st.spinner("Mapeando Head, Body e Footer..."):
            partes = capturar_site(url_input)
            if partes:
                st.session_state.url_atual = url_input
                st.session_state.site_partes = partes
                st.session_state.scripts_aplicados = "" 
                st.rerun()

st.divider()
col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Analista de Performance")
    if st.session_state.site_partes["body"]:
        prompt_usuario = st.text_area("Descreva a melhoria:", height=100)
        
        if st.button("✨ Gerar Código Otimizado", use_container_width=True):
            if model:
                with st.spinner("Analisando necessidade técnica..."):
                    contexto = st.session_state.site_partes["body"][:5000]
                    prompt_final = f"""
                    Atue como Arquiteto Front-end. 
                    Analise: Use CSS (<style>) para visual e JS (<script>) apenas para lógica.
                    Retorne apenas as tags de código, sem markdown.
                    
                    HTML BASE: {contexto}
                    PEDIDO: {prompt_usuario}
                    """
                    try:
                        resposta = model.generate_content(prompt_final)
                        texto_ia = resposta.text.strip()
                        
                        # Limpeza segura de blocos de código
                        if "```" in texto_ia:
                            partes_texto = texto_ia.split("```")
                            # Pega o conteúdo de dentro do bloco se houver
                            codigo_limpo = partes_texto[1] if len(partes_texto) > 1 else texto_ia
                            # Remove possíveis tags de linguagem como 'html' ou 'css' na primeira linha
                            if "\n" in codigo_limpo:
                                codigo_limpo = "\n".join(codigo_limpo.split("\n")[1:])
                        else:
                            codigo_limpo = texto_ia
                            
                        st.session_state.scripts_aplicados = codigo_limpo
                        st.rerun()
                    except Exception as e: st.error(f"Erro IA: {e}")

        with st.expander("📄 Códigos para Implementação Real", expanded=True):
            tab1, tab2, tab3 = st.tabs(["Custom Scripts (IA)", "Body Base", "Footer Base"])
            with tab1: st.code(st.session_state.scripts_aplicados, language="html")
            with tab2: st.code(st.session_state.site_partes["body"], language="html")
            with tab3: st.code(st.session_state.site_partes["footer"], language="html")

with col_sandbox:
    st.subheader("🧪 Sandbox")
    if st.session_state.site_partes["body"]:
        html_render = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <base href="{st.session_state.url_atual}/">
                {st.session_state.site_partes["head"]}
            </head>
            <body>
                {st.session_state.site_partes["body"]}
                {st.session_state.site_partes["footer"]}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        st.components.v1.html(html_render, height=800, scrolling=True)
