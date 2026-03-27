


import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide")

# 2. Barra Lateral - Configurações
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Insira sua Gemini API Key", type="password")

def carregar_modelo(key):
    try:
        genai.configure(api_key=key)
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for p in ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro']:
            if p in modelos_disponiveis:
                return genai.GenerativeModel(p)
        return genai.GenerativeModel(modelos_disponiveis[0])
    except:
        return None

model = carregar_modelo(api_key) if api_key else None

# 3. Estado da Sessão (Memória do App)
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""

# 4. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url = st.text_input("URL da Concessionária:", placeholder="https://www.exemplo.com.br")

if st.button("🔍 Analisar Site"):
    if url:
        try:
            with st.spinner("Capturando estrutura..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Armazena os dados
                st.session_state.url_atual = url
                scripts = soup.find_all('script')
                texto_scripts = "\n".join([s.get_text() for s in scripts if s.get_text()])
                st.session_state.codigo_fonte = soup.prettify()
                st.success("Site capturado! O Sandbox está pronto.")
        except Exception as e:
            st.error(f"Erro ao acessar: {e}")

st.divider()

# 5. Colunas: Visualização vs Controles
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🖼️ 1. Site Original (Referência)")
    if st.session_state.url_atual:
        # Iframe simples do site real
        proxy_url = f"https://api.allorigins.win/raw?url={st.session_state.url_atual}"
        st.components.v1.iframe(proxy_url, height=350, scrolling=True)
    
    st.subheader("🧪 2. Sandbox (Editável)")
    if st.session_state.codigo_fonte:
        # Montagem do HTML modificado
        html_editado = f"""
        <html>
            <head>
                <base href="{st.session_state.url_atual}">
                <style>
                    /* Injeção de CSS da IA */
                    {st.session_state.scripts_aplicados if 'body' in st.session_state.scripts_aplicados or '{' in st.session_state.scripts_aplicados else ''}
                </style>
            </head>
            <body>
                {st.session_state.codigo_fonte}
                <script>
                    // Injeção de JS da IA
                    {st.session_state.scripts_aplicados}
                </script>
            </body>
        </html>
        """
        st.components.v1.html(html_editado, height=500, scrolling=True)
        
        if st.button("Limpar Alterações"):
            st.session_state.scripts_aplicados = ""
            st.rerun()

with col2:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        instrucao = st.text_area("O que deseja mudar no Sandbox?", placeholder="Ex: Deixe o fundo preto e esconda o seletor de unidades.")
        
        if st.button("✨ Gerar e Aplicar"):
            if model:
                with st.spinner("IA trabalhando..."):
                    prompt = f"""
                    Abaixo está o HTML de um site.
                    HTML: {st.session_state.codigo_fonte[:4000]}
                    
                    Pedido: {instrucao}
                    
                    Gere APENAS o código CSS ou JavaScript necessário para isso. 
                    Não use blocos de Markdown (como ```css). Mande apenas o código puro.
                    """
                    res = model.generate_content(prompt)
                    # Limpeza simples de segurança
                    limpo = res.text.replace("```javascript", "").replace("```css", "").replace("```", "").strip()
                    
                    # Acumula o script na sessão
                    st.session_state.scripts_aplicados += "\n" + limpo
                    st.rerun()
            else:
                st.warning("Insira a API Key na lateral.")
    else:
        st.info("Analise um site para começar.")
