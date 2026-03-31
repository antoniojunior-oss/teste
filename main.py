import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import base64
import re

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. IA - Carregamento Seguro
def carregar_modelo_seguro(key):
    try:
        genai.configure(api_key=key)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if opcao in modelos: return genai.GenerativeModel(opcao)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except: return None

# 3. Estado da Sessão
if "codigo_fonte" not in st.session_state: st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state: st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state: st.session_state.url_atual = ""
if "sandbox_key" not in st.session_state: st.session_state.sandbox_key = 0

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")
url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Site"):
    if url_input:
        try:
            with st.spinner("Extraindo estrutura..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_input, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Limpeza para evitar bugs de renderização
                for tag in soup(["script", "style", "link", "img", "svg", "iframe"]):
                    tag.decompose()
                
                # Pegar o texto/estrutura essencial
                corpo = soup.find('body')
                texto_base = corpo.get_text(separator="\n", strip=True) if corpo else "Erro ao ler conteúdo."
                
                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = f"<div>{texto_base[:20000]}</div>" 
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja criar?", height=150)
        
        if st.button("✨ Gerar e Otimizar"):
            if model:
                with st.spinner("IA processando..."):
                    prompt = f"""
                    HTML BASE: {st.session_state.codigo_fonte[:2000]}
                    SCRIPTS EXISTENTES: {st.session_state.scripts_aplicados}
                    PEDIDO: {prompt_usuario}
                    REGRA: Retorne APENAS blocos <style> e <script> consolidados. Sem markdown.
                    """
                    res = model.generate_content(prompt)
                    codigo = res.text.replace("```html", "").replace("```", "").strip()
                    st.session_state.scripts_aplicados = codigo
                    st.rerun()
            else: st.warning("Insira a API Key.")
        
        if st.button("🗑️ Resetar"):
            st.session_state.scripts_aplicados = ""
            st.rerun()

with col_sandbox:
    st.subheader("🧪 Sandbox")
    if st.button("🔄 Refresh"):
        st.session_state.sandbox_key += 1
        st.rerun()

    if st.session_state.codigo_fonte:
        # MONTAGEM BLINDADA COM BASE64
        html_completo = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
                </style>
            </head>
            <body>
                {st.session_state.codigo_fonte}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        
        try:
            # Converte para Base64 para o Streamlit não "ler" os caracteres e dar TypeError
            b64_html = base64.b64encode(html_completo.encode('utf-8')).decode('utf-8')
            src_data = f"data:text/html;base64,{b64_html}"
            
            # Usamos um iframe nativo via markdown para máxima compatibilidade
            st.write(
                f'<iframe src="{src_data}" width="100%" height="600" style="border:1px solid #ddd; border-radius:10px;"></iframe>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Erro de renderização: {e}")
