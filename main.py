import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Configuração da Página
st.set_page_config(page_title="IA Dealer Pro - Sandbox", layout="wide", page_icon="🚗")

# 2. Funções de Suporte
def carregar_modelo_seguro(key):
    try:
        genai.configure(api_key=key)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if opcao in modelos:
                return genai.GenerativeModel(opcao)
        return None
    except Exception:
        return None

def capturar_site(url):
    """Função para clonar o HTML original da URL fornecida."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza de scripts de rastreamento pesados
        for s in soup(['script', 'iframe']):
            if s.get('src') and any(x in s['src'] for x in ['google-analytics', 'facebook', 'hotjar']):
                s.decompose()
        
        return soup.prettify()
    except Exception as e:
        st.error(f"Erro ao capturar site: {e}")
        return None

# 3. Inicialização do Estado da Sessão
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel de Controle")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar Novo Site"):
    if url_input:
        with st.spinner("Clonando estrutura..."):
            html_clonado = capturar_site(url_input)
            if html_clonado:
                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = html_clonado
                st.session_state.scripts_aplicados = "" # Limpa scripts ao trocar de site
                st.success("Site clonado com sucesso!")
                st.rerun()

st.divider()

# 6. Layout de Colunas
col_sandbox, col_ia = st.columns([1.3, 0.7])

with col_ia:
    st.subheader("🤖 Assistente de Edição")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que você quer mudar?", height=120)
        
        if st.button("✨ Aplicar/Otimizar Mudanças", use_container_width=True):
            if model:
                with st.spinner("IA otimizando código..."):
                    contexto_html = st.session_state.codigo_fonte[:5000]
                    script_atual = st.session_state.scripts_aplicados
                    
                    prompt_final = f"""
                    Você é um desenvolvedor Front-end Senior. 
                    CONTEXTO: Você já aplicou scripts neste site.
                    HTML BASE (RESUMIDO): {contexto_html}
                    SCRIPTS EXISTENTES: {script_atual if script_atual else "Nenhum."}
                    PEDIDO: {prompt_usuario}
                    REGRAS: Retorne APENAS o código consolidado dentro de <style> e <script>. Sem markdown.
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_ia = resposta.text.strip().replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        st.session_state.scripts_aplicados = codigo_ia
                        st.toast("Scripts otimizados!", icon="🛠️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
            else:
                st.warning("Insira a API Key.")

        if st.button("🗑️ Resetar Tudo", use_container_width=True):
            st.session_state.scripts_aplicados = ""
            st.session_state.codigo_fonte = ""
            st.session_state.url_atual = ""
            st.rerun()

        st.divider()
        with st.expander("📄 Ver Scripts Inseridos", expanded=True):
            if st.session_state.scripts_aplicados:
                st.code(st.session_state.scripts_aplicados, language="html")
            else:
                st.write("Nenhum script ativo.")

with col_sandbox:
    c1, c2 = st.columns([0.8, 0.2])
    c1.subheader("🧪 Sandbox (Visualização)")
    
    # FUNCIONALIDADE REFEITA: O Refresh agora re-scrappa o site original
    if c2.button("🔄 Refresh", help="Recarregar do link inicial mantendo scripts da IA"):
        if st.session_state.url_atual:
            with st.spinner("Atualizando fonte..."):
                novo_html = capturar_site(st.session_state.url_atual)
                if novo_html:
                    st.session_state.codigo_fonte = novo_html
                    st.session_state.refresh_count += 1
                    st.toast("Site recarregado da fonte original!")
                    st.rerun()

    if st.session_state.codigo_fonte:
        try:
            # Montagem segura do HTML
            template = """
<!DOCTYPE html>
<html>
    <head>
        <base href="[URL]/">
        <meta charset="UTF-8">
        <style> body { margin: 0; padding: 0; } </style>
        </head>
    <body>
        [HTML_BASE]
        [SCRIPTS]
    </body>
</html>
"""
            html_render = template.replace("[URL]", str(st.session_state.url_atual))
            html_render = html_render.replace("[HTML_BASE]", str(st.session_state.codigo_fonte))
            html_render = html_render.replace("[SCRIPTS]", str(st.session_state.scripts_aplicados))
            html_render = html_render.replace("[REF]", str(st.session_state.refresh_count))

            st.components.v1.html(html_render, height=800, scrolling=True)
        except Exception as e:
            st.error(f"Erro visual: {e}")
    else:
        st.info("Aguardando URL.")
