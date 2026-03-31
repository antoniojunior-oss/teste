import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. Funções de Suporte e IA
def carregar_modelo_seguro(key):
    try:
        genai.configure(api_key=key)
        # Lista os modelos para evitar o erro 404 de 'model not found'
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Prioridade: 1.5 Flash (mais rápido) -> 1.5 Pro -> Qualquer um disponível
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if opcao in modelos:
                return genai.GenerativeModel(opcao)
        
        if modelos:
            return genai.GenerativeModel(modelos[0])
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")
        return None

# 3. Inicialização do Estado da Sessão
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel de Controle")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Pegue sua chave em aistudio.google.com")
model = carregar_modelo_seguro(api_key) if api_key else None

if model:
    st.sidebar.success(f"Modelo Ativo: {model.model_name}")

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")
st.markdown("Clone qualquer site de concessionária e faça edições em tempo real usando IA.")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual, placeholder="https://www.minhaconcessionaria.com.br")

if st.button("🔍 Clonar e Analisar Site"):
    if url_input:
        try:
            with st.spinner("Capturando estrutura do site..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url_input, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Limpeza básica para evitar scripts de rastreamento pesados no sandbox
                for s in soup(['script', 'iframe']):
                    if s.get('src') and ('google-analytics' in s['src'] or 'facebook' in s['src']):
                        s.decompose()

                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = soup.prettify()
                st.session_state.scripts_aplicados = "" # Reseta edições ao trocar de site
                st.success("Site clonado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao acessar a URL: {e}")

st.divider()

# 6. Layout de Colunas
col_sandbox, col_ia = st.columns([1.3, 0.7])

with col_ia:
    st.subheader("🤖 Assistente de Edição")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que você quer mudar?", 
                                     placeholder="Ex: Deixe todos os botões arredondados e com cor azul marinho. Mude o texto do cabeçalho para 'Ofertas Exclusivas'.",
                                     height=150)
        
        if st.button("✨ Aplicar Mudanças"):
            if model:
                with st.spinner("IA processando alterações..."):
                    contexto_html = st.session_state.codigo_fonte[:6000] # Limite para não estourar a API
                    
                    prompt_final = f"""
                    Você é um desenvolvedor Front-end Senior. 
                    Alvo: Modificar um site de concessionária.
                    HTML Base: {contexto_html}
                    
                    PEDIDO DO USUÁRIO: {prompt_usuario}
                    
                    REGRAS:
                    1. Para mudanças visuais, use CSS dentro de <style>.
                    2. Para mudanças de texto ou comportamento, use JavaScript dentro de <script>.
                    3. Retorne APENAS o código puro (tags <style> ou <script>). 
                    4. Não use explicações nem blocos de markdown (```).
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_ia = resposta.text.strip()
                        
                        # Limpeza de segurança caso a IA envie markdown
                        codigo_ia = codigo_ia.replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        
                        st.session_state.scripts_aplicados += "\n" + codigo_ia
                        st.toast("Alteração aplicada!", icon="🚀")
                    except Exception as e:
                        st.error(f"Erro na geração: {e}")
            else:
                st.warning("Insira sua API Key na lateral para habilitar a IA.")

        if st.button("🗑️ Resetar Sandbox"):
            st.session_state.scripts_aplicados = ""
            st.rerun()
            
        with st.expander("Ver Scripts Injetados"):
            st.code(st.session_state.scripts_aplicados, language="html")

with col_sandbox:
    st.subheader("🧪 Sandbox (Visualização)")
    if st.session_state.codigo_fonte:
        # Montagem do ambiente isolado
        # A tag <base> é crucial para que imagens e fontes originais funcionem
        html_sandbox = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <base href="{st.session_state.url_atual}/">
                <meta charset="UTF-8">
                <style>
                    /* Reset de scrollbar para o iframe */
                    body {{ margin: 0; padding: 0; }}
                </style>
            </head>
            <body>
                {st.session_state.codigo_fonte}
                {st.session_state.scripts_aplicados}
            </body>
        </html>
        """
        st.components.v1.html(html_sandbox, height=800, scrolling=True)
    else:
        st.info("Aguardando URL para gerar o ambiente de teste.")
