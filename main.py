import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. IA - Carregamento
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
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # REMOÇÃO AGRESSIVA DE PESO:
                # Removemos scripts, iframes e estilos inline gigantes que travam o buffer
                for tag in soup(["script", "style", "iframe", "noscript", "svg", "link"]):
                    # Mantemos apenas o CSS essencial se quiser, mas aqui vamos remover tudo para dar controle total à IA
                    tag.decompose()
                
                # Pegamos apenas o conteúdo do Body para ser mais leve
                body_content = soup.find('body')
                html_limpo = str(body_content.prettify()) if body_content else str(soup.prettify())
                
                st.session_state.url_atual = url_input
                # Limite de 50k caracteres para garantir que o Streamlit não quebre
                st.session_state.codigo_fonte = html_limpo[:50000] 
                st.session_state.scripts_aplicados = "" 
                st.success("Estrutura capturada! O Sandbox está leve e pronto.")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao acessar site: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja mudar visualmente?", height=120)
        
        if st.button("✨ Otimizar e Aplicar"):
            if model:
                with st.spinner("IA processando..."):
                    contexto = st.session_state.codigo_fonte[:5000] # Trecho para IA entender a estrutura
                    prompt = f"""
                    Baseado no HTML abaixo, crie um código CSS/JS para atender o pedido.
                    HTML: {contexto}
                    SCRIPTS JÁ EXISTENTES: {st.session_state.scripts_aplicados}
                    PEDIDO: {prompt_usuario}
                    REGRAS: 
                    1. Reuna e otimize tudo em um único bloco <style> e <script>.
                    2. Retorne APENAS o código puro, sem explicações e sem blocos de código markdown (```).
                    """
                    res = model.generate_content(prompt)
                    st.session_state.scripts_aplicados = res.text.replace("```html", "").replace("```", "").strip()
                    st.rerun()
            else: st.warning("Insira a API Key.")
        
        if st.button("🗑️ Resetar"):
            st.session_state.scripts_aplicados = ""
            st.rerun()

with col_sandbox:
    c1, c2 = st.columns([2, 1])
    c1.subheader("🧪 Sandbox")
    if c2.button("🔄 Refresh"):
        st.session_state.sandbox_key += 1
        st.rerun()

    if st.session_state.codigo_fonte:
        # Montagem do HTML Final (Leve)
        html_final = f"""
        <html>
            <head>
                <base href="{st.session_state.url_atual}/">
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: sans-serif; background: #f4f4f4; padding: 20px; }}
                </style>
            </head>
            <body>
                {st.session_state.codigo_fonte}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        # Renderização sem o Try/Except para vermos se há erro de sistema
        st.components.v1.html(html_final, height=700, scrolling=True, key=f"sb_{st.session_state.sandbox_key}")
