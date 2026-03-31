import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. Funções de Suporte
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

# 5. Interface
st.title("🚗 IA Dealer: Editor & Sandbox")
url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Site"):
    if url_input:
        try:
            with st.spinner("Capturando e otimizando estrutura..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_input, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # OTIMIZAÇÃO: Remove elementos que pesam e não ajudam na edição visual
                for tag in soup(["script", "style", "svg"]): 
                    # Mantemos apenas o que não for externo ou muito grande
                    if tag.name == "script" and tag.get("src"): tag.decompose()
                
                st.session_state.url_atual = url_input
                # Limitamos o tamanho para evitar erro de buffer do Streamlit
                st.session_state.codigo_fonte = soup.prettify()[:100000] 
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao clonar: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja mudar?", height=100)
        if st.button("✨ Otimizar e Aplicar"):
            if model:
                with st.spinner("IA trabalhando..."):
                    prompt = f"Melhore este código JS/CSS: {st.session_state.scripts_aplicados}\nNova mudança: {prompt_usuario}\nRetorne apenas o código puro, sem markdown."
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
        # Montagem ultra-simplificada
        html_final = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
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
        try:
            st.components.v1.html(html_final, height=700, scrolling=True, key=f"sb_{st.session_state.sandbox_key}")
        except:
            st.error("O site original é muito complexo para o Sandbox. Tente uma URL mais simples ou resete os scripts.")
