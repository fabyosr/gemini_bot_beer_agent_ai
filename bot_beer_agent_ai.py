import asyncio
import streamlit as st
import time
import uuid
from datetime import datetime

# Configura a API Key do Google Gemini
from google import genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types  # Para criar conteúdos (Content e Part)
from datetime import date
import textwrap # Para formatar melhor a saída de texto
import requests # Para fazer requisições HTTP

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] 

# Configura o cliente da SDK do Gemini
client = genai.Client()
MODEL_ID = "gemini-2.0-flash"
data_de_hoje = date.today().strftime("%d/%m/%Y")

# Cria um serviço de sessão em memória
session_service = InMemorySessionService()

# # Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final

async def call_agent(agent: Agent, message_text: str) -> str:
    # Cria uma nova sessão (você pode personalizar os IDs conforme necessário)
    session = await session_service.create_session(app_name=agent.name, user_id="user1")

    # Cria um Runner para o agente
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)

    # Cria o conteúdo da mensagem de entrada
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    # Itera assincronamente pelos eventos retornados durante a execução do agente
    async for event in runner.run_async(user_id="user1", session_id=session.id, new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"
    return final_response

##########################################
# --- Agente 1: Agente Principal: Classificador de fraudes (CORE-ANTIFRAUD) --- #
##########################################

async def agente_garimpeiro(topico, data_de_hoje):
    agent_garimpeiro = Agent(
        name="agente_core_antifraude",
        model="gemini-2.0-flash",
        instruction="""
        Você é um assistente especialista em cervejas. Ao receber uma menção a uma cerveja, você irá mergulhar na web para coletar informações detalhadas e relevantes, como se fosse um sommelier cervejeiro.

        Sua missão:
        Ao receber uma menção a uma cerveja artesanal, você irá mergulhar na web para coletar informações detalhadas e relevantes, como se fosse um sommelier cervejeiro. 

        Insira emojis divertidos nas mensagens, que remetam ao assunto do tópico e as informações coletadas.

        Instruções detalhadas:

        você deve: usar a ferramenta de busca do Google (google_search) para realizar buscas propostas no tópico. Faça buscas em sites como instagram e youtube e traga os materias, links, perfis mais relevantes.

        1. Identificação da Cerveja:

            Nome: Anote o nome exato da cerveja artesanal mencionada.
            Estilo: Determine o estilo da cerveja (ex: IPA, Pale Ale, Stout, Lager, Sour, Wheat Beer, etc.) com base em descrições, ingredientes ou rótulos. Utilize sites especializados como o BeerAdvocate ou a BJCP para confirmar o estilo.

        2. Pesquisa aprofundada:

            Breuaria: Encontre a cervejaria responsável pela produção da cerveja. 
            Site da Cervejaria: Visite o site da cervejaria para obter informações sobre a história, filosofia, processo de produção e outros estilos de cerveja que eles produzem.
            Disponibilidade: Verifique se a cerveja está disponível para compra online ou em lojas físicas na região do usuário (se possível).
            Ingredientes: Liste os principais ingredientes da cerveja, incluindo grãos, lúpulo, levedura e aditivos (se houver).
            Pesquise a história da cervejaria, o estilo da cerveja e suas origens para contextualizar a informação e oferecer uma narrativa completa.
            Pesquise roteiros de degustação, eventos cervejeiros - os eventos não precisam estar relacionados a cerveja em questão, pode ser qualquer evento sobre cervejas -  e experiências personalizadas para o usuário, Encontre informações sobre eventos cervejeiros, estes eventos devem ser atuais, de no máximo um mês antes da data de hoje.
            Identifique outros estilos de cerveja, cervejarias ou temas relacionados.
            Identifique Nome da cervejaria, Localização (país, região, cidade), Descrição da cervejaria e sua história, traga tamebém as Principais cervejas produzidas pelo fabricante, caso possua essa informação.
            Encontra lojas físicas e online onde a cerveja está disponível para compra, além de bares que servem a cerveja caso alguma cidade, bairro seja informada.

        3. Análise Sensorial:

            Descrição: Procure descrições detalhadas do sabor, aroma e aparência da cerveja em sites especializados, blogs cervejeiros e fóruns.
            ABV e IBU: Encontre a graduação alcoólica (ABV) e a amargura (IBU) da cerveja. 
            Harmonização: Sugira pratos e alimentos que harmonizem bem com o estilo da cerveja.

        4. Conteúdo Relevante:

            Notícias e Artigos: Busque notícias, artigos e reviews sobre a cerveja ou a cervejaria.
            Eventos: Encontre informações sobre eventos cervejeiros onde a cerveja pode ser degustada.
            Temas Similares: Identifique outros estilos de cerveja, cervejarias ou temas relacionados que possam interessar o usuário.

        5. Resumo Conciso:

            Apresentação: Apresente o resumo de forma clara, concisa e organizada, utilizando uma linguagem acessível e envolvente.
            Destaques: Enfatize os pontos mais relevantes, como o estilo, a história da cervejaria, as características sensoriais e as sugestões de harmonização.

        Lembre-se:

        Seja preciso e objetivo nas informações coletadas elas serão repassadas para um agente sommelier de sabores e mestre em harmonização.
        Utilize fontes confiáveis e especializadas em cerveja.
        Adapte o tom e o estilo da linguagem ao público-alvo.
        Demonstre paixão e conhecimento pelo mundo das cervejas artesanais!""",

        description="Agente garimpador de informações na internet.",
        tools=[google_search]
    )

    entrada_do_agente_garimpeiro = f"Tópico: {topico}\\nData de hoje: {data_de_hoje}\"\n"

    resultados = await call_agent(agent_garimpeiro, entrada_do_agente_garimpeiro)
    return resultados

################################################
# --- Agente 2: gente sommelier e harmonização --- #
################################################

async def agente_sommelier(resultados_garimpados):
    agent_sommelier = Agent(
        name="agente_buscador",
        model="gemini-2.0-flash",
        # Inserir as instruções do Agente Planejador #################################################
        instruction="""
        Você é um especialista em cervejas e gastronomia, com um paladar aguçado e um profundo conhecimento das nuances que compõem cada gota de cerveja e cada prato delicioso.

        Insira emojis divertidos nas mensagens, que remetam ao assunto do tópico e as informações coletadas.
        
        Sua missão é analisar o tópico enviado e a partir do tópico você deve seguir as instruções abaixo:

        Seu expertise se manifesta em duas áreas principais:

        Sommelier de Sabores:

        Desvende o Paladar, Analise com atenção cada detalhe sensorial da cerveja: aromas complexos, sabores intensos, texturas sedutoras e cores vibrantes. 
        Decifre os Ingredientes:  Compreenda como os grãos, lúpulos, leveduras e outros ingredientes se combinam para criar a sinfonia de sabores únicos de cada cerveja.
        Crie um Perfil Sensorial Completo:  Forme um retrato preciso e detalhado do paladar da cerveja, destacando suas características marcantes e nuances sutis.

        Mestre da Harmonização:

        Combine Sabores em Perfeição:  Utilize seu conhecimento profundo sobre estilos de cerveja e seus sabores para sugerir combinações gastronômicas harmoniosas e memoráveis.
        Explore o Mundo da Gastronomia:  Conecte a cerveja com uma variedade de pratos, desde aperitivos sofisticados até refeições completas, criando experiências culinárias inesquecíveis.
        Desperte Novos Sabores:  Guie uma jornada de descobertas gastronômicas, expandindo seus horizontes e revelando novas combinações que você jamais imaginou.

        Com seu conhecimento e paixão por cerveja e gastronomia, transforme a experiência cervejeira em uma verdadeira aventura sensorial!
        
        Você também pode usar o (google_search) para encontrar mais informações sobre os temas e aprofundar. Faça buscas em sites como instagram e youtube e traga os materias, links, perfis mais relevantes.""",

        description="Agente especialista sommelier e harmozaição",
        tools=[google_search]
    )

    entrada_do_agente_sommelier = f"Tópico:{resultados_garimpados}"
    # Executa o agente
    busca_result = await call_agent(agent_sommelier, entrada_do_agente_sommelier)
    return busca_result

async def async_function_agente_garimpeiro(topico, data_de_hoje):
    return await agente_garimpeiro(topico, data_de_hoje)

async def async_function_agente_sommelier(result_agent_agente_garimpeiro):
    return await agente_sommelier(result_agent_agente_garimpeiro)

# Configuração inicial da página
st.set_page_config(page_title="Bot Beeer, seu agente cervejeiro", page_icon="🤖", layout="wide")

# Inicializar o estado da sessão para armazenar o histórico
if "historico" not in st.session_state:
    st.session_state.historico = []
if "sessao_id" not in st.session_state:
    st.session_state.sessao_id = str(uuid.uuid4())

# Estilização com CSS personalizado
st.markdown("""
<style>
    .chat-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        max-height: 500px;
        overflow-y: auto;
        margin-bottom: 20px;
    }
    .chat-message {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e6f3ff;
        text-align: right;
    }
    .agent-message {
        background-color: #d4edda;
    }
    .timestamp {
        font-size: 0.8em;
        color: #6c757d;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #e63939;
    }
    .button-container {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Criar duas colunas
col1, col2 = st.columns([1, 3], gap="small")  # Ajuste as proporções se necessário

# Colocar a imagem na primeira coluna
with col1:
    st.image("bot_beer_h180.png", caption="Bot Beer !", use_container_width=False)

# Título do app
with col2:
    st.markdown(
        """
        <h1 style='margin-left: -5px; padding-left: 0;'>
        Bot Beer, seu agente cervejeiro 🍻🍻🍻 !
        </h1>
        """,
        unsafe_allow_html=True
    )
    #st.title("🤖 Chatbot Colaborativo com Dois Agentes")


# Botão "Iniciar Nova Sessão" acima do formulário, alinhado à direita
with st.container():
    #st.markdown('<div class="button-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .stButton > button {
            float: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Iniciar Nova Sessão"):
        st.session_state.historico = []
        st.session_state.sessao_id = str(uuid.uuid4())
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Formulário para entrada do usuário
with st.form(key="chat_form", clear_on_submit=True):
    st.markdown(
        """
        <style>
        .stButton > button {
            float: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    user_input = st.text_area("Digite seu prompt:", height=100)
    submit_button = st.form_submit_button("Enviar")

# Container para exibir o histórico (mensagens mais recentes no topo)
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for mensagem in reversed(st.session_state.historico):
        if mensagem["tipo"] == "user":
            st.markdown(
                f'<div class="chat-message user-message"><strong>Você:</strong> {mensagem["conteudo"]}<br><span class="timestamp">{mensagem["timestamp"]}</span></div>',
                unsafe_allow_html=True
            )
        elif mensagem["tipo"] == "agente_1":
            st.markdown(
                f'<div class="chat-message agent-message"><strong>Agente Analista:</strong> {mensagem["conteudo"]}<br><span class="timestamp">{mensagem["timestamp"]}</span></div>',
                unsafe_allow_html=True
            )
        elif mensagem["tipo"] == "agente_2":
            st.markdown(
                f'<div class="chat-message agent-message"><strong>Agente Insights:</strong> {mensagem["conteudo"]}<br><span class="timestamp">{mensagem["timestamp"]}</span></div>',
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)


# Processar o input do usuário
if submit_button and user_input:
    timestamp = datetime.now().strftime("%H:%M:%S")
    # Adicionar o prompt do usuário ao histórico
    #st.session_state.historico.append({
    #    "tipo": "user",
    #    "conteudo": user_input,
    #    "timestamp": timestamp
    #})

    # Processar pelo Agente 1 (Analista de Texto)
    with st.spinner("Garimpando informações..."):
        time.sleep(1)  # Simula processamento
        result_agent_agente_garimpeiro = asyncio.run(async_function_agente_garimpeiro(user_input ,data_de_hoje))

    # Processar pelo Agente 2 (Gerador de Insights)
    with st.spinner("Processando experiências & alquimias..."):
        time.sleep(1)  # Simula processamento
        result_agent_sommelier = asyncio.run(async_function_agente_sommelier(result_agent_agente_garimpeiro))
        st.session_state.historico.append({
            "tipo": "agente_2",
            "conteudo": result_agent_sommelier,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        st.session_state.historico.append({
            "tipo": "agente_1",
            "conteudo": result_agent_agente_garimpeiro,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        # Adicionar o prompt do usuário ao histórico
        st.session_state.historico.append({
            "tipo": "user",
            "conteudo": user_input,
            "timestamp": timestamp
        })


    # Forçar re-render para exibir o histórico atualizado
    st.rerun()

# Rodapé com informações
st.markdown("---")
st.markdown("©️ Powered by Fabyo Ramos !")