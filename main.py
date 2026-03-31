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

# 3. Inicialização do Estado da Sessão
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""
if "sandbox_key" not in st.session_state:
    st.session_state.sandbox_key = 0 # Para o botão de refresh

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
                st.session_state.codigo_fonte = soup.prettify()
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

st.divider()

col_sandbox, col_ia = st.columns([1.3, 0.7])

with col_ia:
    st.subheader("🤖 Assistente de Edição")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que deseja mudar ou adicionar?", height=100)
        
        if st.button("✨ Otimizar e Aplicar"):
            if model:
                with st.spinner("IA Otimizando Scripts..."):
                    # Aqui passamos os scripts antigos para a IA consolidar
                    scripts_atuais = st.session_state.scripts_aplicados
                    
                    prompt_final = f"""
                    Você é um especialista em performance web. 
                    Tarefa: Criar um novo script ou atualizar os existentes.
                    
                    SCRIPTS JÁ EXISTENTES NO SANDBOX:
                    {scripts_atuais if scripts_atuais else "Nenhum script aplicado ainda."}
                    
                    NOVA SOLICITAÇÃO:
                    {prompt_usuario}
                    
                    REGRAS DE OTIMIZAÇÃO:
                    1. Reuna tudo em um único bloco <style> e um único bloco <script> (se necessário).
                    2. Remova seletores CSS duplicados ou redundantes.
                    3. Se a nova solicitação alterar algo que já existe nos scripts anteriores, substitua a lógica antiga pela nova.
                    4. Retorne APENAS o código puro otimizado. Sem markdown (```).
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_limpo = resposta.text.strip().replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        
                        # Atualiza a sessão com o código CONSOLIDADO (não apenas somado)
                        st.session_state.scripts_aplicados = codigo_limpo
                        st.toast("Scripts otimizados e aplicados!", icon="🛠️")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.warning("Insira a API Key.")

        if st.button("🗑️ Resetar Tudo"):
            st.session_state.scripts_aplicados = ""
            st.rerun()
            
        with st.expander("Ver Código Consolidado"):
            st.code(st.session_state.scripts_aplicados, language="html")

with col_sandbox:
    header_sandbox = st.columns([1, 1])
    header_sandbox[0].subheader("🧪 Sandbox")
    
    # BOTÃO DE REFRESH: Aumenta a key do componente para forçar o reload do iframe
    if header_sandbox[1].button("🔄 Recarregar Sandbox"):
        st.session_state.sandbox_key += 1
        st.toast("Recarregando ambiente...")

    if st.session_state.codigo_fonte:
        html_sandbox = f"""
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
        # A 'key' dinâmica faz o Streamlit entender que é um novo componente e recarrega
        st.components.v1.html(
            html_sandbox, 
            height=800, 
            scrolling=True, 
            key=f"sandbox_v_{st.session_state.sandbox_key}"
        )
