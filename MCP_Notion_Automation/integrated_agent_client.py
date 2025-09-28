# integrated_agent_client.py - 통합 클라이언트
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv

load_dotenv()

model = init_chat_model("gpt-5-nano", model_provider="openai")
# model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

# =============================================================================
# 통합 MCP 클라이언트
# 🔹 Part 1: Chinook 데이터베이스 MCP 서버 (SQL 분석)
# 🔹 Part 2: Notion 자동화 MCP 서버 (결과 저장)
# =============================================================================
# Part 1: Chinook 데이터베이스 MCP 서버 설정
chinook_server_params = StdioServerParameters(
    command="python",
    args=["../LangGraph_MCP_Agent/agent_server.py"],  # Chinook DB 분석 서버
)

# Part 2: Notion 자동화 MCP 서버 설정  
notion_server_params = StdioServerParameters(
    command="python",
    args=["./automation_server.py"],  # Notion 자동화 서버
)

async def setup_servers():
    """두 MCP 서버를 설정하고 도구들을 로드합니다."""
    print("MCP 서버들 연결 중...")
    
    # Chinook 서버 연결
    async with stdio_client(chinook_server_params) as (chinook_read, chinook_write):
        async with ClientSession(chinook_read, chinook_write) as chinook_session:
            await chinook_session.initialize()
            print("Chinook 데이터베이스 서버 연결 완료")
            
            # Notion 서버 연결
            async with stdio_client(notion_server_params) as (notion_read, notion_write):
                async with ClientSession(notion_read, notion_write) as notion_session:
                    await notion_session.initialize()
                    print("Notion 자동화 서버 연결 완료")
                    
                    # 도구들 로드
                    print("MCP 도구들 통합 중...")
                    chinook_tools = await load_mcp_tools(chinook_session)
                    notion_tools = await load_mcp_tools(notion_session)
                    all_tools = chinook_tools + notion_tools
                    
                    print(f"   Chinook DB 도구: {len(chinook_tools)}개")
                    print(f"   Notion 도구: {len(notion_tools)}개")
                    print(f"   총 도구: {len(all_tools)}개")
                    
                    # Agent 생성
                    print("통합 Agent 생성 중...")
                    memory = MemorySaver()
                    agent = create_react_agent(model, all_tools, checkpointer=memory)
                    print("통합 Agent 생성 완료")
                    
                    # 대화형 챗봇 시작
                    await start_chatbot(agent)

async def start_chatbot(agent):
    """대화형 챗봇을 시작합니다."""
    print("\n" + "="*60)
    print("통합 MCP Agent 시작!")
    print("   Chinook 데이터베이스 분석 + Notion 자동 저장")
    print("   자연어로 '노션에 저장해줘', 'Notion에 올려줘' 등으로 요청 가능")
    print("   'quit' 또는 'exit'로 종료")
    print("="*60 + "\n")
    
    session_id = "integrated_session"
    
    while True:
        user_input = input("질문을 입력하세요: ")
        
        if user_input.lower() in ['quit', 'exit', '종료']:
            print("통합 Agent를 종료합니다.")
            break
        
        print("처리 중...")
        
        # 사용자 메시지 처리 - LLM이 자동으로 도구 선택
        user_message = HumanMessage(content=user_input)
        config = {"configurable": {"thread_id": session_id}}
        
        # 통합 Agent 실행 (LLM이 자동으로 적절한 도구 선택)
        response = await agent.ainvoke(
            {"messages": [user_message]}, 
            config=config
        )
        
        print("응답:")
        print(response["messages"][-1].content)
        print("\n" + "="*50 + "\n")

async def run():
    """메인 실행 함수"""
    await setup_servers()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())