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
        # Prioridade para o Flash 1.5 (mais rápido e eficiente para código)
        for opcao in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if opcao in modelos:
                return genai.GenerativeModel(opcao)
        return None
    except Exception:
        return None

def capturar_site(url):
    """Clona o HTML da URL e limpa scripts de rastreamento."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza de scripts que podem travar o sandbox ou monitorar cliques reais
        for s in soup(['script', 'iframe']):
            src = s.get('src', '')
            if any(x in src for x in ['google-analytics', 'facebook', 'hotjar', 'gtm']):
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
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Obtenha em aistudio.google.com")
model = carregar_modelo_seguro(api_key) if api_key else None

if model:
    st.sidebar.success(f"Modelo Ativo: {model.model_name}")
else:
    st.sidebar.warning("Aguardando API Key válida...")

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual, placeholder="https://www.site.com.br")

if st.button("🔍 Clonar Novo Site"):
    if url_input:
        with st.spinner("Capturando estrutura..."):
            html_clonado = capturar_site(url_input)
            if html_clonado:
                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = html_clonado
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado!")
                st.rerun()

st.divider()

# 6. Layout de Colunas
col_sandbox, col_ia = st.columns([1.2, 0.8])

with col_ia:
    st.subheader("🤖 Assistente de Edição")
    if st.session_state.codigo_fonte:
        prompt_usuario = st.text_area("O que você quer mudar?", 
                                     placeholder="Ex: Se o cliente escolher a opção X, redirecione para o link Y...",
                                     height=150)
        
        if st.button("✨ Aplicar/Otimizar Mudanças", use_container_width=True):
            if model:
                with st.spinner("IA processando e otimizando código..."):
                    # Enviamos um resumo do HTML para a IA entender o contexto
                    contexto_html = st.session_state.codigo_fonte[:6000]
                    script_atual = st.session_state.scripts_aplicados
                    
                    prompt_final = f"""
                    Atue como Desenvolvedor Front-end Sênior.
                    OBJETIVO: Modificar o comportamento/visual de um site de concessionária.
                    
                    HTML BASE (trecho): {contexto_html}
                    
                    CÓDIGO JÁ EXISTENTE (Otimize-o se necessário): 
                    {script_atual if script_atual else "Nenhum código aplicado ainda."}
                    
                    NOVO PEDIDO DO USUÁRIO: {prompt_usuario}
                    
                    REGRAS:
                    1. Consolide o novo pedido com o código antigo em um bloco único e limpo.
                    2. Use <style> para CSS e <script> para JavaScript.
                    3. Retorne APENAS o código puro. Sem explicações, sem markdown (```).
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_ia = resposta.text.strip().replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        
                        # Sobrescreve com a versão otimizada
                        st.session_state.scripts_aplicados = codigo_ia
                        st.toast("Alterações aplicadas com sucesso!", icon="🚀")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.error("ERRO: Você precisa inserir a API Key na barra lateral!")

        if st.button("🗑️ Resetar Tudo", use_container_width=True):
            st.session_state.scripts_aplicados = ""
            st.session_state.codigo_fonte = ""
            st.session_state.url_atual = ""
            st.rerun()

        st.divider()
        with st.expander("📄 Scripts Inseridos (Copiar Código)", expanded=True):
            if st.session_state.scripts_aplicados:
                st.code(st.session_state.scripts_aplicados, language="html")
            else:
                st.info("Nenhum script gerado ainda.")

with col_sandbox:
    header_col, refresh_col = st.columns([0.7, 0.3])
    header_col.subheader("🧪 Sandbox")
    
    # Refresh funcional: Recarrega o HTML original mantendo o JS da IA
    if refresh_col.button("🔄 Refresh", use_container_width=True):
        if st.session_state.url_atual:
            with st.spinner("Recarregando fonte..."):
                novo_html = capturar_site(st.session_state.url_atual)
                if novo_html:
                    st.session_state.codigo_fonte = novo_html
                    st.session_state.refresh_count += 1
                    st.rerun()

    if st.session_state.codigo_fonte:
        try:
            # Template seguro usando replace para evitar erro de chaves {}
            template_sandbox = """
<!DOCTYPE html>
<html>
    <head>
        <base href="[URL_BASE]/">
        <meta charset="UTF-8">
        <style> body { margin: 0; padding: 0; } </style>
        </head>
    <body>
        [CONTEUDO_HTML]
        [SCRIPTS_IA]
    </body>
</html>
"""
            html_final = template_sandbox.replace("[URL_BASE]", str(st.session_state.url_atual))
            html_final = html_final.replace("[CONTEUDO_HTML]", str(st.session_state.codigo_fonte))
            html_final = html_final.replace("[SCRIPTS_IA]", str(st.session_state.scripts_aplicados))
            html_final = html_final.replace("[REF_ID]", str(st.session_state.refresh_count))

            st.components.v1.html(html_final, height=800, scrolling=True)
        except Exception as e:
            st.error(f"Erro na renderização: {e}")
    else:
        st.info("Insira uma URL para começar.")
