import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide")

# 2. Funções de Suporte
def carregar_modelo(key):
    try:
        genai.configure(api_key=key)
        # Tenta pegar o Flash que é mais rápido para scripts simples
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        return None

# 3. Estado da Sessão (Persistência de Dados)
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""

# 4. Barra Lateral
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Insira sua Gemini API Key", type="password")
model = carregar_modelo(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url = st.text_input("URL da Concessionária:", value=st.session_state.url_atual, placeholder="https://www.exemplo.com.br")

if st.button("🔍 Analisar e Clonar Site"):
    if url:
        try:
            with st.spinner("Capturando estrutura..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                st.session_state.url_atual = url
                st.session_state.codigo_fonte = soup.prettify()
                st.session_state.scripts_aplicados = "" # Limpa scripts antigos ao carregar novo site
                st.success("Site capturado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao acessar: {e}")

st.divider()

# 6. Colunas: Visualização vs Controles
col1, col2 = st.columns([1.2, 0.8])

with col2:
    st.subheader("🤖 Assistente IA")
    if st.session_state.codigo_fonte:
        instrucao = st.text_area("O que deseja mudar no Sandbox?", 
                                 placeholder="Ex: Altere a cor dos botões para vermelho e mude o texto do banner principal.")
        
        btn_gerar = st.button("✨ Gerar e Aplicar Alterações")
        
        if btn_gerar:
            if model:
                with st.spinner("IA criando o script..."):
                    # Prompt mais robusto para garantir retorno limpo
                    prompt = f"""
                    Você é um especialista em web design. Analise o HTML abaixo e crie um código (CSS ou JS) para atender ao pedido.
                    HTML (trecho): {st.session_state.codigo_fonte[:5000]}
                    
                    PEDIDO: {instrucao}
                    
                    REGRAS:
                    1. Se for alteração visual, gere CSS dentro de <style>.
                    2. Se for alteração de texto ou funcional, gere JS dentro de <script>.
                    3. Retorne APENAS o código puro, sem explicações e sem blocos de markdown (```).
                    """
                    try:
                        res = model.generate_content(prompt)
                        novo_script = res.text.strip()
                        
                        # Limpeza extra de Markdown se a IA teimar em colocar
                        for tag in ["```javascript", "```css", "```html", "```"]:
                            novo_script = novo_script.replace(tag, "")
                        
                        st.session_state.scripts_aplicados += "\n" + novo_script
                        st.toast("Script aplicado ao Sandbox!", icon="✅")
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.warning("⚠️ Configure a API Key na barra lateral.")
        
        if st.button("🗑️ Limpar Sandbox"):
            st.session_state.scripts_aplicados = ""
            st.rerun()

with col1:
    st.subheader("🧪 Sandbox em Tempo Real")
    if st.session_state.codigo_fonte:
        # Montagem do HTML com base na URL original para carregar imagens/estilos originais
        # Injetamos o código da IA logo antes do fechamento do Body
        html_completo = f"""
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
        st.components.v1.html(html_completo, height=700, scrolling=True)
    else:
        st.info("Insira uma URL acima para começar a editar.")
