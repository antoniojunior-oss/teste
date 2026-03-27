import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Configuração da Página
st.set_page_config(page_title="IA Dealer - Editor de Scripts", layout="wide")

# Barra Lateral
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Insira sua Gemini API Key", type="password")

# --- FUNÇÃO PARA INICIALIZAR O MELHOR MODELO DISPONÍVEL ---
def carregar_modelo(key):
    try:
        genai.configure(api_key=key)
        # Lista os modelos para ver o que sua chave permite
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ordem de preferência
        preferencia = [
            'models/gemini-1.5-pro',
            'models/gemini-1.5-flash',
            'models/gemini-pro'
        ]
        
        for p in preferencia:
            if p in modelos_disponiveis:
                return genai.GenerativeModel(p)
        
        # Se não achar nenhum dos preferidos, pega o primeiro que funcionar
        return genai.GenerativeModel(modelos_disponiveis[0])
    except Exception as e:
        st.error(f"Erro ao conectar com Google AI: {e}")
        return None

model = None
if api_key:
    model = carregar_modelo(api_key)

# Cabeçalho
st.title("🚗 IA Dealer: Dashboard de Edição")
st.write("Analise o site e gere scripts customizados.")

if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""

url = st.text_input("URL da Concessionária:", placeholder="https://www.fiat.itavema.com.br")

if st.button("🔍 Analisar Site"):
    if url:
        try:
            with st.spinner("Extraindo código..."):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                scripts = soup.find_all('script')
                texto_scripts = "\n".join([s.get_text() for s in scripts if s.get_text()])
                html_base = soup.prettify()[:5000]
                
                st.session_state.codigo_fonte = f"HTML:\n{html_base}\n\nSCRIPTS:\n{texto_scripts[:5000]}"
                st.success("Análise concluída!")
        except Exception as e:
            st.error(f"Erro ao acessar site: {e}")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🖼️ Visualização")
    if url:
        proxy_url = f"https://api.allorigins.win/raw?url={url}"
        st.components.v1.iframe(proxy_url, height=600, scrolling=True)
    else:
        st.info("Insira uma URL.")

with col2:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        instrucao = st.text_area("O que deseja mudar?")
        if st.button("✨ Gerar Script"):
            if model:
                with st.spinner("Gerando código..."):
                    try:
                        prompt = f"Contexto: {st.session_state.codigo_fonte}\n\nPedido: {instrucao}\n\nGere o script CSS ou JS e explique como usar."
                        response = model.generate_content(prompt)
                        st.code(response.text, language="javascript")
                    except Exception as e:
                        st.error(f"Erro na geração: {e}")
            else:
                st.warning("Verifique sua API Key.")
    else:
        st.info("Analise um site primeiro.")
