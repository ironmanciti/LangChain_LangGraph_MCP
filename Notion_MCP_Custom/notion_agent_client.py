# integrated_agent_client.py - 통합 클라이언트
# 여러 MCP 서버를 하나의 Agent에 통합하여 사용하는 예제

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv

load_dotenv()

model = init_chat_model("gpt-5-mini", model_provider="openai")
# model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

# =============================================================================
# 여러 MCP 서버의 도구들을 하나의 Agent에서 사용
# 🔹 Chinook 데이터베이스 MCP 서버 (SQL 분석)
# 🔹 Notion 자동화 MCP 서버 (결과 저장)
#   - 분석 결과를 Notion 페이지로 자동 저장
#   - 테이블 형태로 저장, 페이지 검색 등
# =============================================================================

# Chinook 데이터베이스 분석 기능을 제공하는 MCP 서버
chinook_server_params = StdioServerParameters(
    command="python",
    args=["../DB_MCP_Agent/agent_server.py"],  # Chinook DB 분석 서버 경로
)

# Notion API를 통한 페이지 생성 및 관리 기능 제공 서버
notion_server_params = StdioServerParameters(
    command="python",
    args=["./notion_mcp_server.py"],  # Notion 자동화 서버 경로
)

async def setup_servers():
    """    
    여러 MCP 서버의 도구들을 하나의 Agent에 통합하여
    LLM이 자동으로 적절한 도구를 선택하여 사용할 수 있게 합니다.
    """
    print("MCP 서버들 연결 중...")
    
    # MCP 서버와 stdio 통신 채널 열기
    async with stdio_client(chinook_server_params) as (chinook_read, chinook_write):
        # 클라이언트 세션 생성 및 초기화
        async with ClientSession(chinook_read, chinook_write) as chinook_session:
            # Chinook 서버 초기화
            await chinook_session.initialize()
            print("Chinook 데이터베이스 서버 연결 완료")
            
            # Notion 자동화 서버 연결
            async with stdio_client(notion_server_params) as (notion_read, notion_write):
                async with ClientSession(notion_read, notion_write) as notion_session:
                    # Notion 서버 초기화
                    await notion_session.initialize()
                    print("Notion 자동화 서버 연결 완료")
                    
                    # Chinook DB 관련 도구들 (SQL 쿼리, 테이블 조회 등)
                    chinook_tools = await load_mcp_tools(chinook_session)
                    
                    # Notion 관련 도구들 (페이지 생성, 테이블 생성 등)
                    notion_tools = await load_mcp_tools(notion_session)
                    
                    # 모든 도구를 하나의 리스트로 통합
                    all_tools = chinook_tools + notion_tools
                    
                    # 통합 결과 출력
                    print(f"Chinook DB 도구: {len(chinook_tools)}개")
                    print(f"Notion 도구: {len(notion_tools)}개")
                    print(f"총 통합 도구: {len(all_tools)}개")
                    
                    # 메모리 체크포인터 (대화 히스토리 저장)
                    memory = MemorySaver()
                    
                    # ReAct Agent 생성
                    agent = create_react_agent(model, all_tools, checkpointer=memory)
                    print("통합 Agent 생성 완료")
                    
                    # 대화형 챗봇 시작
                    await start_chatbot(agent)

async def start_chatbot(agent):
    """
    대화형 챗봇을 시작합니다.

    Args:
        agent: 통합된 ReAct Agent
    """
    print("\n" + "="*60)
    print("통합 MCP Agent 시작!")
    print("quit' 또는 'exit'로 종료")
    print("="*60 + "\n")
    
    # 대화 세션 ID (대화 히스토리 추적용)
    session_id = "integrated_session"
    
    while True:

        user_input = input("질문을 입력하세요: ")
        
        # 종료 명령어 확인
        if user_input.lower() in ['quit', 'exit', '종료']:
            print("\n통합 Agent를 종료합니다.")
            break
        
        print("처리 중...\n")
        
        # 사용자 메시지를 LangChain 형식으로 변환
        user_message = HumanMessage(content=user_input)
        
        # 메모리 설정 (대화 히스토리 유지)
        config = {"configurable": {"thread_id": session_id}}
        
        # 통합 Agent 실행
        response = await agent.ainvoke(
            {"messages": [user_message]}, 
            config=config
        )
        
        # Agent의 최종 응답 출력
        print("응답:")
        print(response["messages"][-1].content)
        print("\n" + "="*50 + "\n")

async def run():
    """
    메인 실행 함수
    두 MCP 서버를 설정하고 통합 Agent를 시작합니다.
    """
    await setup_servers()

if __name__ == "__main__":
    import asyncio
    
    # 이벤트 루프 실행
    asyncio.run(run())