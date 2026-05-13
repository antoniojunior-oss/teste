import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Full Modular", layout="wide", page_icon="🚗")

# 2. Funções de Suporte
def carregar_modelo_seguro(key):
    try:
        if not key: return None
        genai.configure(api_key=key)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if opcao in modelos: return genai.GenerativeModel(opcao)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except Exception as e:
        st.sidebar.error(f"Erro na API: {e}")
        return None

def capturar_site(url):
    """Clona e segmenta o site em Head, Body e Footer, limpando trackers."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for s in soup(['script', 'iframe']):
            src = s.get('src', '')
            if any(x in src for x in ['google-analytics', 'facebook', 'hotjar', 'gtm']):
                s.decompose()
        
        head_content = "".join([str(item) for item in soup.head.contents]) if soup.head else ""
        
        footer_tag = soup.find('footer')
        footer_content = str(footer_tag) if footer_tag else ""
        
        if footer_tag:
            footer_tag.decompose()
        body_content = "".join([str(item) for item in soup.body.contents]) if soup.body else ""
        
        return {
            "head": head_content,
            "body": body_content,
            "footer": footer_content
        }
    except Exception as e:
        st.error(f"Erro ao capturar site: {e}")
        return None

# 3. Inicialização do Estado da Sessão
if "site_partes" not in st.session_state:
    st.session_state.site_partes = {"head": "", "body": "", "footer": ""}
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""

# 4. Barra Lateral
st.sidebar.title("⚙️ Configurações")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor Full Modular")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Estrutura Completa"):
    if url_input:
        with st.spinner("Mapeando Head, Body e Footer..."):
            partes = capturar_site(url_input)
            if partes:
                st.session_state.url_atual = url_input
                st.session_state.site_partes = partes
                st.session_state.scripts_aplicados = "" 
                st.rerun()

st.divider()

# 6. Layout de Colunas
col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Analista de Performance")
    if st.session_state.site_partes["body"]:
        prompt_usuario = st.text_area("O que deseja alterar?", height=120)
        
        if st.button("✨ Gerar Código Otimizado", use_container_width=True):
            if model:
                with st.spinner("Analisando melhor solução..."):
                    contexto_html = st.session_state.site_partes["body"][:5000]
                    
                    prompt_final = f"""
                    Atue como Arquiteto Front-end Sênior.
                    Analise: Use CSS (<style>) para visual e JS (<script>) apenas para lógica dinâmica.
                    Retorne APENAS o código puro dentro das tags necessárias. Sem markdown.
                    
                    CONTEÚDO BODY: {contexto_html}
                    CÓDIGO ATUAL: {st.session_state.scripts_aplicados}
                    PEDIDO: {prompt_usuario}
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        texto_ia = resposta.text.strip()
                        
                        # Limpeza robusta para evitar o erro de SyntaxError mostrado na imagem image_2b5137.png
                        # Remove blocos de código markdown se a IA os incluir por engano
                        if texto_ia.startswith("```"):
                            linhas = texto_ia.splitlines()
                            # Remove a primeira linha (
```html) e a última (```)
                            codigo_limpo = "\n".join(linhas[1:-1]) if len(linhas) > 2 else texto_ia
                        else:
                            codigo_limpo = texto_ia
                        
                        st.session_state.scripts_aplicados = codigo_limpo
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.error("Insira a API Key!")

        if st.button("🗑️ Resetar Tudo", use_container_width=True):
            st.session_state.site_partes = {"head": "", "body": "", "footer": ""}
            st.session_state.scripts_aplicados = ""
            st.session_state.url_atual = ""
            st.rerun()

        st.divider()
        with st.expander("📄 Implementação no CMS", expanded=True):
            tab_script, tab_body, tab_footer = st.tabs(["Custom Scripts (IA)", "Body Base", "Footer Base"])
            with tab_script:
                st.code(st.session_state.scripts_aplicados, language="html")
            with tab_body:
                st.code(st.session_state.site_partes["body"], language="html")
            with tab_footer:
                st.code(st.session_state.site_partes["footer"], language="html")

with col_sandbox:
    st.subheader("🧪 Sandbox")
    if st.session_state.site_partes["body"]:
        html_final = f"""
<!DOCTYPE html>
<html>
    <head>
        <base href="{st.session_state.url_atual}/">
        <meta charset="UTF-8">
        {st.session_state.site_partes["head"]}
        <style> body {{ margin: 0; padding: 0; }} </style>
    </head>
    <body>
        {st.session_state.site_partes["body"]}
        {st.session_state.site_partes["footer"]}
        {st.session_state.scripts_aplicados}
    </body>
</html>
"""
        st.components.v1.html(html_final, height=800, scrolling=True)
