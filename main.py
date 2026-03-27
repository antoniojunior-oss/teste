import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Configuração da Página
st.set_page_config(page_title="IA Dealer - Editor de Scripts", layout="wide")

# Barra Lateral - Configurações
st.sidebar.title("Configurações")
api_key = st.sidebar.text_input("Insira sua Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🚗 IA Dealer: Análise e Edição de Sites")
st.write("Insira a URL da concessionária para capturar o código e sugerir alterações.")

# Input da URL
url = st.text_input("URL do Site da Concessionária:", placeholder="https://www.exemplo-concessionaria.com.br")

if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""

if st.button("Analisar Site"):
    if url:
        try:
            with st.spinner("Capturando código do site..."):
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Captura HTML básico e Scripts
                scripts = soup.find_all('script')
                texto_scripts = "\n".join([s.get_text() for s in scripts if s.get_text()])
                
                # Armazena no estado da sessão
                st.session_state.codigo_fonte = f"HTML ESTRUTURAL:\n{soup.prettify()[:5000]}\n\nSCRIPTS ATUAIS:\n{texto_scripts[:5000]}"
                st.success("Código capturado com sucesso (limite de 10k caracteres para o protótipo)!")
        except Exception as e:
            st.error(f"Erro ao acessar o site: {e}")
    else:
        st.warning("Por favor, insira uma URL válida.")

---

# Interface de Duas Colunas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Visualização / Código")
    if url:
        # Tenta mostrar o site original (pode ser bloqueado por alguns sites via iframe)
        st.components.v1.iframe(url, height=600, scrolling=True)
    else:
        st.info("Aguardando URL para visualização.")

with col2:
    st.subheader("Assistente de IA")
    
    if st.session_state.codigo_fonte:
        user_input = st.text_input("O que você deseja mudar no site?")
        
        if st.button("Gerar Script"):
            prompt = f"""
            Você é um desenvolvedor especialista em sites de concessionárias. 
            Abaixo está parte do código-fonte do site:
            {st.session_state.codigo_fonte}
            
            O usuário deseja a seguinte alteração: {user_input}
            
            Gere o script (JavaScript ou CSS) necessário para realizar essa mudança. 
            Explique de forma simples onde o usuário deve colar esse código no painel da concessionária.
            """
            
            with st.spinner("Pensando na solução..."):
                response = model.generate_content(prompt)
                st.markdown("### 💡 Sugestão da IA:")
                st.write(response.text)
    else:
        st.info("Analise um site primeiro para habilitar o assistente.")
