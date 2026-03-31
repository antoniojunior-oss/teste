import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
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
            with st.spinner("Limpando e clonando estrutura..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_input, headers=headers, timeout=10)
                # Forçamos a codificação para evitar caracteres quebrados
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # REMOÇÃO DE TAGS CONFLITANTES
                for tag in soup(["script", "style", "iframe", "noscript", "svg", "link", "img"]):
                    tag.decompose()
                
                # Pega apenas o conteúdo visível (Body) e converte para string limpa
                body = soup.find('body')
                html_raw = str(body.get_text(separator="\n", strip=True)) if not body else "Erro ao ler body"
                
                # Criamos um HTML minimalista baseado no conteúdo
                html_limpo = f"<div>{html_raw[:30000]}</div>" 
                
                # Removemos qualquer caractere que não seja texto comum para evitar o TypeError
                html_limpo = re.sub(r'[^\x00-\x7f]',r' ', html_limpo)

                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = html_limpo
                st.session_state.scripts_aplicados = "" 
                st.success("Estrutura capturada!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao acessar site: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja criar?", placeholder="Ex: Crie um título azul e um botão de contato.")
        
        if st.button("✨ Gerar e Otimizar"):
            if model:
                with st.spinner("IA processando..."):
                    prompt = f"""
                    Contexto: {st.session_state.codigo_fonte[:2000]}
                    Scripts Atuais: {st.session_state.scripts_aplicados}
                    Pedido: {prompt_usuario}
                    Regra: Retorne APENAS o código CSS/JS consolidado dentro de <style> e <script>. Sem markdown.
                    """
                    res = model.generate_content(prompt)
                    # Limpeza extra para garantir que a IA não mande lixo
                    novo_codigo = res.text.replace("```html", "").replace("```", "").strip()
                    st.session_state.scripts_aplicados = novo_codigo
                    st.rerun()
            else: st.warning("Insira a API Key.")
        
        st.button("🗑️ Resetar", on_click=lambda: st.session_state.update({"scripts_aplicados": ""}))

with col_sandbox:
    c1, c2 = st.columns([2, 1])
    c1.subheader("🧪 Sandbox")
    if c2.button("🔄 Refresh"):
        st.session_state.sandbox_key += 1
        st.rerun()

    if st.session_state.codigo_fonte:
        # A montagem da string final agora é protegida
        html_render = f"<html><body>{st.session_state.codigo_fonte}{st.session_state.scripts_aplicados}</body></html>"
        
        st.components.v1.html(
            html_render, 
            height=600, 
            scrolling=True, 
            key=f"sandbox_{st.session_state.sandbox_key}"
        )
