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
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
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
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# 4. Barra Lateral
st.sidebar.title("⚙️ Painel de Controle")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
model = carregar_modelo_seguro(api_key) if api_key else None

if model:
    st.sidebar.success(f"Modelo Ativo: {model.model_name}")

# 5. Interface Principal
st.title("🚗 IA Dealer: Editor & Sandbox")

url_input = st.text_input("URL da Concessionária:", value=st.session_state.url_atual)

if st.button("🔍 Clonar e Analisar Site"):
    if url_input:
        try:
            with st.spinner("Capturando estrutura do site..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url_input, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Limpeza de scripts de terceiros
                for s in soup(['script', 'iframe']):
                    if s.get('src') and any(x in s['src'] for x in ['google-analytics', 'facebook', 'hotjar']):
                        s.decompose()

                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = soup.prettify()
                st.session_state.scripts_aplicados = "" 
                st.success("Site clonado!")
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
                                     placeholder="Ex: Deixe os botões arredondados e azuis...",
                                     height=150)
        
        if st.button("✨ Aplicar/Otimizar Mudanças", use_container_width=True):
            if model:
                with st.spinner("IA otimizando código..."):
                    # ... (Lógica de geração do Gemini que já definimos antes)
                    contexto_html = st.session_state.codigo_fonte[:5000]
                    script_atual = st.session_state.scripts_aplicados
                    
                    prompt_final = f"""
                    Você é um desenvolvedor Front-end Senior. 
                    CONTEXTO: Você já aplicou alguns scripts neste site.
                    HTML BASE (RESUMIDO): {contexto_html}
                    
                    SCRIPTS JÁ EXISTENTES:
                    {script_atual if script_atual else "Nenhum script aplicado ainda."}
                    
                    NOVA SOLICITAÇÃO: {prompt_usuario}
                    
                    TAREFA:
                    1. Integre a nova solicitação ao código existente.
                    2. Otimize o código: remova redundâncias e combine seletores.
                    3. Retorne APENAS o código final consolidado dentro de <style> e <script>.
                    4. Não use explicações nem markdown.
                    """
                    
                    try:
                        resposta = model.generate_content(prompt_final)
                        codigo_ia = resposta.text.strip().replace("```html", "").replace("```javascript", "").replace("```css", "").replace("```", "")
                        st.session_state.scripts_aplicados = codigo_ia
                        st.toast("Scripts otimizados!", icon="🛠️")
                        st.rerun() # Rerun para atualizar o visualizador e a lista de scripts
                    except Exception as e:
                        st.error(f"Erro na geração: {e}")
            else:
                st.warning("Insira a API Key.")

        if st.button("🗑️ Resetar Tudo", use_container_width=True):
            st.session_state.scripts_aplicados = ""
            st.session_state.url_atual = ""
            st.session_state.codigo_fonte = ""
            st.rerun()

        # --- NOVA SEÇÃO: SCRIPTS GERADOS ---
        st.divider()
        with st.expander("📄 Ver Scripts Gerados (Pronto para copiar)", expanded=True):
            if st.session_state.scripts_aplicados:
                st.info("Este é o código consolidado e otimizado pela IA:")
                st.code(st.session_state.scripts_aplicados, language="html")
            else:
                st.write("Nenhum script gerado ainda.")

with col_sandbox:
    # Cabeçalho do Sandbox com botão de Refresh
    c1, c2 = st.columns([0.8, 0.2])
    c1.subheader("🧪 Sandbox (Visualização)")
    
    # Ao clicar em refresh, aumentamos o contador
    if c2.button("🔄 Refresh", help="Recarregar o sandbox"):
        st.session_state.refresh_key += 1

    if st.session_state.codigo_fonte:
        try:
            # 1. Garantimos que tudo seja STRING pura
            url_str = str(st.session_state.url_atual)
            html_original = str(st.session_state.codigo_fonte)
            scripts_ia = str(st.session_state.scripts_aplicados)
            refresh_id = str(st.session_state.refresh_key)
            
            # 2. Criamos o template
            # Injetamos o [ID_REFRESH] como um comentário para forçar a atualização da string
            template_html = """
<!DOCTYPE html>
<html>
    <head>
        <base href="[URL_BASE]/">
        <meta charset="UTF-8">
        <style> 
            body { margin: 0; padding: 0; overflow-x: hidden; } 
        </style>
    </head>
    <body>
        [CONTEUDO_ORIGINAL]
        [SCRIPTS_CUSTOM]
    </body>
</html>
"""
            # 3. Substituições manuais seguras
            html_final = template_html.replace("[URL_BASE]", url_str)
            html_final = html_final.replace("[CONTEUDO_ORIGINAL]", html_original)
            html_final = html_final.replace("[SCRIPTS_CUSTOM]", scripts_ia)
            html_final = html_final.replace("[ID_REFRESH]", refresh_id)

            # 4. Renderizamos SEM o argumento 'key'
            st.components.v1.html(
                html_final, 
                height=800, 
                scrolling=True
            )
        except Exception as e:
            st.error(f"Erro ao renderizar sandbox: {e}")
    else:
        st.info("Aguardando URL para gerar o ambiente de teste.")

