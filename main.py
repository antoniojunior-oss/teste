import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json

# ── Configuração da Página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="IA Dealer Pro",
    layout="wide",
    page_icon="🚗",
    initial_sidebar_state="collapsed"
)

# Remove padding e header padrão do Streamlit
st.markdown("""
<style>
    #MainMenu, header, footer { display: none !important; }
    .stApp { overflow: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── Funções de suporte ──────────────────────────────────────────────────────
def capturar_site(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for s in soup(["script", "iframe"]):
            src = s.get("src", "")
            if any(x in src for x in ["google-analytics", "facebook", "hotjar", "gtm"]):
                s.decompose()
        return {"ok": True, "html": soup.prettify()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def gerar_script_ia(api_key, html_contexto, script_atual, prompt_usuario):
    try:
        genai.configure(api_key=api_key)
        modelos = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        modelo = None
        for opcao in ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]:
            if opcao in modelos:
                modelo = genai.GenerativeModel(opcao)
                break
        if not modelo and modelos:
            modelo = genai.GenerativeModel(modelos[0])
        if not modelo:
            return {"ok": False, "error": "Nenhum modelo disponível"}

        prompt = f"""
Atue como Desenvolvedor Front-end Sênior focado em Web Performance (Core Web Vitals).
OBJETIVO: Implementar a mudança solicitada de forma extremamente leve.
CONTEXTO HTML: {html_contexto[:8000]}
CÓDIGO ATUAL PARA MELHORAR: {script_atual if script_atual else "Nenhum."}
PEDIDO DO USUÁRIO: {prompt_usuario}
PROCESSO DE PENSAMENTO OBRIGATÓRIO:
1. Analise o pedido e gere a solução funcional.
2. REVISÃO CRÍTICA: Posso diminuir seletores? Posso usar Vanilla JS? O CSS está duplicado?
3. OTIMIZAÇÃO: Remova comentários, espaços excessivos, consolide funções.
REGRAS DE SAÍDA:
- Consolide TUDO (antigo + novo) em um único bloco.
- CSS em <style>, JS em <script>.
- Não use bibliotecas externas a menos que seja estritamente necessário.
- Retorne APENAS o código. Sem explicações, sem crases de markdown.
"""
        resposta = modelo.generate_content(prompt)
        codigo = resposta.text.strip()
        for tag in ["```html", "```javascript", "```css", "```"]:
            codigo = codigo.replace(tag, "")
        return {"ok": True, "code": codigo.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Session state ───────────────────────────────────────────────────────────
for key, val in {
    "html_clonado": "",
    "scripts_aplicados": "",
    "url_atual": "",
    "acao": None,
    "resultado": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Recebe mensagens do front via query params ──────────────────────────────
params = st.query_params

if "acao" in params:
    acao = params["acao"]

    if acao == "clonar" and "url" in params:
        resultado = capturar_site(params["url"])
        if resultado["ok"]:
            st.session_state.html_clonado = resultado["html"]
            st.session_state.url_atual = params["url"]
            st.session_state.scripts_aplicados = ""
        st.session_state.resultado = json.dumps(resultado)
        st.session_state.acao = "clonar"

    elif acao == "ia" and "prompt" in params and "apikey" in params:
        resultado = gerar_script_ia(
            api_key=params["apikey"],
            html_contexto=st.session_state.html_clonado,
            script_atual=st.session_state.scripts_aplicados,
            prompt_usuario=params["prompt"]
        )
        if resultado["ok"]:
            st.session_state.scripts_aplicados = resultado["code"]
        st.session_state.resultado = json.dumps(resultado)
        st.session_state.acao = "ia"

    elif acao == "resetar":
        st.session_state.html_clonado = ""
        st.session_state.scripts_aplicados = ""
        st.session_state.url_atual = ""
        st.session_state.resultado = json.dumps({"ok": True})
        st.session_state.acao = "resetar"

    st.query_params.clear()

# ── Lê o HTML do front e injeta os dados do estado ─────────────────────────
with open("index.html", "r", encoding="utf-8") as f:
    html_front = f.read()

# Injeta os dados do session_state diretamente no HTML como variáveis JS
dados_injetados = f"""
<script>
  window.__ST_STATE__ = {{
    htmlClonado: {json.dumps(st.session_state.html_clonado)},
    scriptsAplicados: {json.dumps(st.session_state.scripts_aplicados)},
    urlAtual: {json.dumps(st.session_state.url_atual)},
    acao: {json.dumps(st.session_state.acao)},
    resultado: {json.dumps(st.session_state.resultado)},
  }};
</script>
"""

html_final = html_front.replace("</head>", dados_injetados + "</head>")

st.components.v1.html(html_final, height=900, scrolling=False)
