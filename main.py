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

# Inicializa o estado da sessão
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""

# Input da URL
url = st.text_input("URL do Site da Concessionária:", placeholder="https://www.exemplo.com.br")

if st.button("Analisar Site"):
    if url:
        try:
            with st.spinner("Capturando código do site..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Captura Scripts e HTML
                scripts = soup.find_all('script')
                texto_scripts = "\n".join([s.get_text() for s in scripts if s.get_text()])
                
                st.session_state.codigo_fonte = f"HTML ESTRUTURAL:\n{soup.prettify()[:5000]}\n\nSCRIPTS ATUAIS:\n{texto_scripts[:5000]}"
                st.success("Site analisado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao acessar o site: {e}")
    else:
        st.warning("Por favor, insira uma URL válida.")

st.divider()

# Interface de Duas Colunas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Visualização do Site")
    if url:
        # Usando o Proxy para tentar burlar o bloqueio de visualização
        proxy_url = f"https://api.allorigins.win/raw?url={url}"
        st.components.v1.iframe(proxy_url, height=600, scrolling=True)
        st.caption("Nota: Se o site não aparecer, ele possui proteções avançadas contra frames.")
    else:
        st.info("Aguardando URL para visualização.")

with col2:
    st.subheader("Assistente de IA")
    
    if st.session_state.codigo_fonte:
        pergunta = st.text_input("O que você deseja mudar no site?")
        
        if st.button("Gerar Script") and api_key:
            prompt = f"""
            Você é um desenvolvedor especialista em sites de concessionárias. 
            Abaixo está parte do código-fonte do site analisado:
            {st.session_state.codigo_fonte}
            
            O usuário deseja a seguinte alteração: {pergunta}
            
            Gere o código (JavaScript ou CSS) necessário para realizar essa mudança. 
            Seja didático e explique onde colar esse código no painel da concessionária.
            """
            
            with st.spinner("A IA está gerando a solução..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### 💡 Sugestão da IA:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
        elif not api_key:
            st.warning("Por favor, insira sua API Key na barra lateral.")
    else:
        st.info("Analise um site primeiro para habilitar o assistente.")
