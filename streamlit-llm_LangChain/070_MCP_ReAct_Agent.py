# ---------------------------------------------------------
# Streamlit 통합 MCP ReAct Agent 챗봇 (060 UI 스타일)
#  - Chinook DB MCP 서버 + Notion MCP 서버 통합
#  - 제출 시마다 MCP 서버 연결 후 에이전트 단회 호출
# ---------------------------------------------------------
from dotenv import load_dotenv
_ = load_dotenv()

import os
import asyncio

import streamlit as st
from streamlit_chat import message

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


# ---------------------------------------------------------
# LLM 초기화 (LangChain 표준 init_chat_model)
# ---------------------------------------------------------
llm = init_chat_model("gpt-5-mini", model_provider="openai")

# ---------------------------------------------------------
# Streamlit 페이지 및 헤더
# ---------------------------------------------------------
st.set_page_config(page_title="통합 MCP Agent Chatbot", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>통합 MCP Agent 챗봇</h1>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 사이드바 버튼
# ---------------------------------------------------------
st.sidebar.title("😎")
refresh_button = st.sidebar.button("대화 내용 초기화")
summaries_button = st.sidebar.button("대화 내용 요약")

# ---------------------------------------------------------
# Session State 초기화
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [SystemMessage(content="당신은 유용한 도우미입니다.")]

# ---------------------------------------------------------
# 환경 변수 점검 (Notion 관련)
# ---------------------------------------------------------
notion_api_key = os.getenv("NOTION_API_KEY", "")
default_page_id = os.getenv("NOTION_PAGE_ID", "")

if not notion_api_key:
    st.sidebar.warning(".env에 NOTION_API_KEY가 설정되어 있지 않습니다.")
if not default_page_id:
    st.sidebar.info(".env에 NOTION_PAGE_ID가 없으면 페이지 작업 시 ID를 직접 입력해야 합니다.")

# ---------------------------------------------------------
# MCP Agent 실행 (제출 시 일회 호출)
# ---------------------------------------------------------
async def run_agent_with_mcp(messages: list[object]) -> str:
    """
    주어진 메시지 히스토리(messages)를 입력으로 받아
    MCP 서버(Chinook DB + Notion)와 통합된 ReAct Agent를 실행하여
    최종 AI 응답 텍스트(content)를 반환합니다.
    """

    # ───────────────────────────────────────────────
    # ① 서버 스크립트 경로 설정
    #   현재 파일 경로: <project_root>/streamlit-llm_LangChain/070_Chatbot.py
    #   Chinook DB MCP 서버: <project_root>/DB_MCP_Agent/agent_server.py
    # ───────────────────────────────────────────────
    streamlit_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(streamlit_dir)
    chinook_agent_path = os.path.abspath(
        os.path.join(project_root, "DB_MCP_Agent", "agent_server.py")
    )

    # ───────────────────────────────────────────────
    # ② MCP 서버 실행 파라미터 정의
    #   • Chinook DB 서버: Python 스크립트 직접 실행
    #   • Notion MCP 서버: Node.js 기반 npx 실행
    # ───────────────────────────────────────────────
    chinook_server_params = StdioServerParameters(
        command="python",
        args=[chinook_agent_path],
    )

    notion_server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={"NOTION_TOKEN": notion_api_key},  # 환경변수로 인증키 전달
    )

    # ───────────────────────────────────────────────
    # ③ 사용자 입력 메시지에 "기본 Notion 페이지 ID" 안내문 추가
    #   • 마지막 HumanMessage만 찾아서 안내문을 덧붙임
    #   • Notion 페이지 자동화 시 기본 parent ID로 활용됨
    # ───────────────────────────────────────────────
    enhanced_messages: list[object] = []
    last_human_index = -1

    # 마지막 HumanMessage 인덱스 찾기
    for idx, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            last_human_index = idx

    # 해당 메시지에 기본 페이지 ID 주입
    for idx, msg in enumerate(messages):
        if idx == last_human_index and isinstance(msg, HumanMessage) and default_page_id:
            enhanced_input = (
                f"{msg.content}\n\n[참고: 기본 작업 페이지 ID는 {default_page_id}입니다. "
                f"페이지 생성/업데이트 시 이 ID를 기본 부모로 사용하세요.]"
            )
            enhanced_messages.append(HumanMessage(content=enhanced_input))
        else:
            enhanced_messages.append(msg)

    # ───────────────────────────────────────────────
    # ④ MCP 서버들과 비동기 통신 채널(표준입출력 기반) 생성
    #   • Chinook DB → SQL 분석용 도구 로드
    #   • Notion → 페이지 생성/갱신용 도구 로드
    #   • 두 MCP 서버에서 제공하는 도구들을 통합
    #   • LangGraph ReAct Agent 생성 후 일회 실행
    # ───────────────────────────────────────────────
    async with stdio_client(chinook_server_params) as (chinook_read, chinook_write):
        async with ClientSession(chinook_read, chinook_write) as chinook_session:
            await chinook_session.initialize()  # Chinook MCP 서버 초기화

            async with stdio_client(notion_server_params) as (notion_read, notion_write):
                async with ClientSession(notion_read, notion_write) as notion_session:
                    await notion_session.initialize()  # Notion MCP 서버 초기화

                    # 각 MCP 서버에서 제공하는 LangChain 도구 목록 로드
                    chinook_tools = await load_mcp_tools(chinook_session)
                    notion_tools = await load_mcp_tools(notion_session)
                    all_tools = chinook_tools + notion_tools  # 전체 도구 통합

                    # LangGraph의 ReAct Agent 생성 (LLM + 도구 결합)
                    agent = create_react_agent(llm, all_tools)

                    # 에이전트를 비동기 실행 (메시지 히스토리 기반)
                    response = await agent.ainvoke({"messages": enhanced_messages})

                    # 마지막 AI 응답 메시지를 추출하여 텍스트만 반환
                    ai_msg = response["messages"][-1]
                    return ai_msg.content


# ---------------------------------------------------------
# 사이드바 버튼 동작
# ---------------------------------------------------------
if refresh_button:
    st.session_state.messages = [SystemMessage(content="당신은 유용한 도우미입니다.")]

if summaries_button:
    # ─────────────────────────────────────────────
    # 세션에 저장된 전체 대화(message)들을 문자열로 합치기
    # 각 메시지의 타입(System / User / AI)에 따라 역할(Role)을 구분함
    # ─────────────────────────────────────────────
    conversation_text = []
    for msg in st.session_state.messages:
        if isinstance(msg, SystemMessage):
            role = "System"   # 시스템 프롬프트 (초기 안내 등)
        elif isinstance(msg, HumanMessage):
            role = "User"     # 사용자가 입력한 메시지
        elif isinstance(msg, AIMessage):
            role = "AI"       # 모델(AI)이 생성한 응답
        else:
            role = "Unknown"  # 기타 타입(안전장치)

        # role 과 content(본문)를 합쳐 문자열 리스트에 저장
        conversation_text.append(f"{role}: {msg.content}")

    # 대화 목록을 줄바꿈(\n)으로 하나의 긴 문자열로 결합
    joined_conversation = "\n".join(conversation_text)

    # LLM에게 전달할 요약 요청 프롬프트 구성
    prompt_content = f"""다음 대화를 요약해주세요:\n{joined_conversation}\n--- \n요약:\n"""
    summary_response = llm.invoke([HumanMessage(content=prompt_content)])
    summary_text = summary_response.content

    # Streamlit 사이드바에 요약 결과 출력
    st.sidebar.write("**대화 요약:**")
    st.sidebar.write(summary_text)

# ---------------------------------------------------------
# 메인 입력 폼 및 Agent 호출
# ---------------------------------------------------------
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_area("질문을 입력하세요:", key='input', height=100)
    submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        # 사용자 메시지 추가
        st.session_state.messages.append(HumanMessage(content=user_input))

        try:
            ai_text = asyncio.run(run_agent_with_mcp(st.session_state.messages))
            st.session_state.messages.append(AIMessage(content=ai_text))
        except Exception as e:
            error_msg = f"에러가 발생했습니다: {str(e)}"
            st.session_state.messages.append(AIMessage(content=error_msg))

# ---------------------------------------------------------
# 마지막 AIMessage를 입력 폼 바로 아래에 표시
# ---------------------------------------------------------
if st.session_state.messages:
    last_msg = st.session_state.messages[-1]
    if isinstance(last_msg, AIMessage):
        st.text(last_msg.content)

# ---------------------------------------------------------
# 이전 대화 이력 표시 (060 스타일)
# ---------------------------------------------------------
st.subheader("이전 대화 이력")
for idx, msg in enumerate(st.session_state.messages):
    if isinstance(msg, HumanMessage):
        message(msg.content, is_user=True, key=str(idx) + "_user")
    elif isinstance(msg, AIMessage):
        message(msg.content, is_user=False, key=str(idx) + "_ai")


