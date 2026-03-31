import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. Funções de Suporte
def carregar_modelo_seguro(key):
    try:
        genai.configure(api_key=key)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if opcao in modelos:
                return genai.GenerativeModel(opcao)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except:
        return None

# 3. Inicialização do Estado da Sessão (Essencial para evitar o TypeError)
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""
if "sandbox_key" not in st.session_state:
    st.session_state.sandbox_key = 0

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel de Controle")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Site"):
    if url_input:
        try:
            with st.spinner("Capturando..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_input, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = str(soup.prettify()) # Força ser string
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente de Edição")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja mudar ou adicionar?", height=100)
        
        if st.button("✨ Otimizar e Aplicar"):
            if model:
                with st.spinner("IA Otimizando Scripts..."):
                    scripts_atuais = st.session_state.scripts_aplicados
                    
                    prompt_final = f"""
                    Tarefa: Criar um novo script ou atualizar os existentes.
                    SCRIPTS JÁ EXISTENTES: {scripts_atuais if scripts_atuais else "Nenhum."}
                    NOVA SOLICITAÇÃO: {prompt_usuario}
                    REGRAS: 
                    - Reuna tudo em um único bloco <style> e um único bloco <script>.
                    - Substitua lógicas antigas se a nova solicitação conflitar.
                    - Retorne APENAS o código puro, sem markdown (```).
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_limpo = resposta.text.strip().replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        st.session_state.scripts_aplicados = codigo_limpo
                        st.toast("Scripts otimizados!", icon="🛠️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.warning("Insira a API Key.")

        if st.button("🗑️ Resetar Tudo"):
            st.session_state.scripts_aplicados = ""
            st.rerun()

with col_sandbox:
    # Cabeçalho do Sandbox com botão de refresh
    c1, c2 = st.columns([2, 1])
    c1.subheader("🧪 Sandbox")
    if c2.button("🔄 Refresh"):
        st.session_state.sandbox_key += 1
        st.rerun()

    if st.session_state.codigo_fonte:
        # Criamos a string HTML fora da chamada da função para garantir que ela exista
        html_sandbox = f"""
        <html>
            <head>
                <base href="{st.session_state.url_atual}/">
                <meta charset="UTF-8">
            </head>
            <body style="margin:0; padding:0;">
                {st.session_state.codigo_fonte}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        
        # Chamada segura do componente
        try:
            st.components.v1.html(
                html_sandbox, 
                height=700, 
                scrolling=True, 
                key=f"sb_{st.session_state.sandbox_key}" # Nome da chave mais curto
            )
        except Exception as e:
            st.error("Erro ao renderizar o Sandbox. Tente resetar os scripts.")
    else:
        st.info("Aguardando clonagem do site...")
