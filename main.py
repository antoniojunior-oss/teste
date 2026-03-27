import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer - Editor de Scripts", layout="wide")

# 2. Barra Lateral - Configurações de API
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Insira sua Gemini API Key", type="password", help="Pegue sua chave em aistudio.google.com")

# Inicialização do Modelo de IA
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Usando gemini-1.5-pro que é mais estável para codificação
        model = genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        st.sidebar.error(f"Erro na API Key: {e}")

# 3. Cabeçalho Principal
st.title("🚗 IA Dealer: Dashboard de Edição")
st.write("Analise qualquer site de concessionária e gere scripts customizados com IA.")

# Inicializa o estado da sessão para manter os dados ao interagir
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""

# 4. Campo de Entrada de URL
url = st.text_input("URL da Concessionária:", placeholder="https://www.fiat.itavema.com.br")

if st.button("🔍 Analisar Site"):
    if url:
        try:
            with st.spinner("Extraindo código e scripts..."):
                # Headers para simular um navegador real e evitar bloqueios
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extração de Scripts e estrutura básica
                scripts = soup.find_all('script')
                texto_scripts = "\n".join([s.get_text() for s in scripts if s.get_text()])
                html_base = soup.prettify()[:5000] # Limite para não estourar o contexto da IA
                
                st.session_state.codigo_fonte = f"HTML ESTRUTURAL:\n{html_base}\n\nSCRIPTS ATUAIS:\n{texto_scripts[:5000]}"
                st.success("Análise concluída! A IA agora conhece a estrutura deste site.")
        except Exception as e:
            st.error(f"Não foi possível acessar o site: {e}")
    else:
        st.warning("Insira uma URL antes de analisar.")

st.divider()

# 5. Interface de Duas Colunas (Visualização vs IA)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🖼️ Visualização do Site")
    if url:
        # Tentativa de carregar via Proxy para contornar bloqueios de Iframe
        proxy_url = f"https://api.allorigins.win/raw?url={url}"
        st.components.v1.iframe(proxy_url, height=650, scrolling=True)
        st.caption("Se a tela acima estiver branca, o site possui bloqueios rígidos de visualização, mas a IA ainda pode editá-lo à direita.")
    else:
        st.info("Insira uma URL acima para visualizar o site aqui.")

with col2:
    st.subheader("🤖 Assistente de Edição")
    
    if st.session_state.codigo_fonte:
        instrucao = st.text_area("O que você deseja alterar?", placeholder="Ex: Crie um script para mudar a cor do botão de 'Tenho Interesse' para laranja e aumentar a fonte.")
        
        if st.button("✨ Gerar Script Customizado"):
            if not api_key:
                st.error("Você precisa inserir a API Key na barra lateral primeiro.")
            else:
                prompt_final = f"""
                Você é um desenvolvedor Web Senior especializado em portais de concessionárias.
                CONTEXTO DO SITE ATUAL:
                {st.session_state.codigo_fonte}

                PEDIDO DO USUÁRIO:
                {instrucao}

                TAREFA:
                1. Analise as classes CSS e IDs de botões no código acima.
                2. Gere um código (CSS ou JavaScript) pronto para ser inserido na área de 'Scripts Personalizados' do site.
                3. Explique de forma muito simples (para leigos) o que esse código faz.
                """
                
                with st.spinner("A IA está escrevendo o código..."):
                    try:
                        response = model.generate_content(prompt_final)
                        st.markdown("### ✅ Script Sugerido:")
                        st.code(response.text, language="javascript")
                        st.success("Pronto! Copie o código acima e teste no seu ambiente de staging.")
                    except Exception as e:
                        st.error(f"Erro ao gerar script: {e}")
    else:
        st.info("Aguardando análise de um site para habilitar a IA.")
