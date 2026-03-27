texto = texto.replace('```', '').strip()
    return texto

@st.cache_resource
def configurar_modelo_ia(key):
    try:
        genai.configure(api_key=key)
        # Lista modelos para garantir compatibilidade
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ordem de preferência de modelos
        preferencia = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro']
        for p in preferencia:
            if p in modelos:
                return genai.GenerativeModel(p)
        return genai.GenerativeModel(modelos[0]) if modelos else None
    except Exception as e:
        st.sidebar.error(f"Erro na API Key: {e}")
        return None

model = None
if api_key:
    model = configurar_modelo_ia(api_key)
    if model:
        st.sidebar.success("✅ IA Conectada!")
    else:
        st.sidebar.warning("⚠️ Falha ao carregar modelo.")

# 3. ESTADO DA SESSÃO (MEMÓRIA)
if "codigo_fonte" not in st.session_state:
    st.session_state.codigo_fonte = ""
if "scripts_aplicados" not in st.session_state:
    st.session_state.scripts_aplicados = ""
if "url_atual" not in st.session_state:
    st.session_state.url_atual = ""
if "historico_scripts" not in st.session_state:
    st.session_state.historico_scripts = []

# 4. INTERFACE DE ENTRADA
st.title("🚗 IA Dealer: Editor & Sandbox")
st.write("Insira a URL, analise a estrutura e aplique scripts via IA para ver as mudanças no Sandbox.")

url_input = st.text_input("URL do Site da Concessionária:", placeholder="https://www.peugeot.com.br")

if st.button("🔍 1. Analisar Estrutura"):
    if url_input:
        try:
            with st.spinner("A extrair código e scripts do site..."):
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
                response = requests.get(url_input, headers=headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Salva os dados na sessão
                st.session_state.url_atual = url_input
                st.session_state.codigo_fonte = soup.prettify()
                st.session_state.scripts_aplicados = "" # Limpa scripts anteriores ao trocar de site
                st.session_state.historico_scripts = []
                st.success("✅ Estrutura capturada! O Sandbox foi gerado.")
        except Exception as e:
            st.error(f"Erro ao aceder ao site: {e}")
    else:
        st.warning("Insira uma URL válida.")

st.divider()

# 5. LAYOUT DE COLUNAS
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🧪 Visualização Sandbox (Editável)")
    if st.session_state.codigo_fonte:
        # CONSTRUÇÃO DO HTML PARA O SANDBOX
        # Usamos <base> para que os recursos originais (imagens/css) funcionem
        html_sandbox = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <base href="{st.session_state.url_atual}">
                <meta charset="UTF-8">
                <style>
                    /* Scripts CSS injetados pela IA */
                    {st.session_state.scripts_aplicados}
                </style>
            </head>
            <body>
                {st.session_state.codigo_fonte}
                <script>
                    /* Scripts JS injetados pela IA */
                    try {{
                        {st.session_state.scripts_aplicados}
                    }} catch(e) {{
                        console.error("Erro no script da IA:", e);
                    }}
                </script>
            </body>
        </html>
        """
        # Renderiza o Sandbox
        st.components.v1.html(html_sandbox, height=600, scrolling=True)
        
        if st.button("🗑️ Limpar Sandbox"):
            st.session_state.scripts_aplicados = ""
            st.session_state.historico_scripts = []
            st.rerun()
    else:
        st.info("Aguardando análise do site para ativar o Sandbox.")

with col2:
    st.subheader("🤖 Assistente de Script")
    if st.session_state.codigo_fonte:
        instrucao = st.text_area("O que deseja mudar?", 
                                 placeholder="Ex: Mude o fundo para preto e esconda o seletor de unidades.", 
                                 height=150)
        
        if st.button("✨ 2. Gerar e Aplicar Alteração"):
            if model:
                with st.spinner("A IA está a processar a alteração..."):
                    try:
                        prompt = f"""
                        CONTEXTO DO SITE: {st.session_state.url_atual}
                        HTML ESTRUTURAL (Resumo): {st.session_state.codigo_fonte[:3500]}
                        
                        PEDIDO: {instrucao}
                        
                        REGRAS:
                        1. Responda APENAS com código CSS ou JavaScript puro.
                        2. NÃO inclua explicações ou blocos de Markdown (```).
                        3. Se for esconder algo, use seletores reais do HTML fornecido.
                        """
                        response = model.generate_content(prompt)
                        codigo_gerado = limpar_codigo_ia(response.text)
                        
                        if codigo_gerado:
                            # Acumula o script para manter alterações anteriores vivas
                            st.session_state.scripts_aplicados += "\n" + codigo_gerado
                            st.session_state.historico_scripts.append(codigo_gerado)
                            st.rerun() # Atualiza o Sandbox imediatamente
                        else:
                            st.error("A IA devolveu um resultado vazio.")
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")
            else:
                st.error("Configure a API Key na barra lateral.")
        
        # Histórico para conferência
        if st.session_state.historico_scripts:
            with st.expander("📄 Ver Scripts Aplicados"):
                for s in st.session_state.historico_scripts:
                    st.code(s, language="javascript")
    else:
        st.info("Analise um site primeiro para habilitar a IA.")

# Rodapé de Referência
if st.session_state.url_atual:
    st.caption(f"Referência Original: [Abrir {st.session_state.url_atual}]({st.session_state.url_atual})")
