# notion_agent_client.py - Notion 자동화 클라이언트 (npx 로 Notion 공식 MCP 실행)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv, find_dotenv
import os

# 현재 경로에서 .env 파일 찾기, 없으면 상위 폴더에서 찾기
load_dotenv(find_dotenv())

model = init_chat_model("gpt-5-mini", model_provider="openai")
# model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

# ─────────────────────────────────────────────────────────────
# Notion 공식 MCP 서버 (@notionhq/notion-mcp-server) - npx 실행
#   • 기본 transport: stdio (별도 옵션 불필요)
#   • 인증: NOTION_API_KEY (Notion 내부 Integration 토큰)
#   • 페이지 ID: NOTION_PAGE_ID (기본 작업 페이지)
#     - .env 파일에 NOTION_API_KEY=ntn_... 로 저장
#     - .env 파일에 NOTION_PAGE_ID=페이지ID 로 저장
# 참고: https://github.com/makenotion/notion-mcp-server
# ─────────────────────────────────────────────────────────────
notion_server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@notionhq/notion-mcp-server"],
    env={"NOTION_TOKEN": os.getenv("NOTION_API_KEY", "")}
)

async def setup_servers():
    print("Notion MCP 서버 연결 중...")
    async with stdio_client(notion_server_params) as (notion_read, notion_write):
        async with ClientSession(notion_read, notion_write) as notion_session:
            await notion_session.initialize()
            print("Notion 자동화 서버 연결 완료")

            notion_tools = await load_mcp_tools(notion_session)
            print(f"Notion 도구: {len(notion_tools)}개")
            
            # 사용 가능한 도구 목록 출력
            print("\n사용 가능한 Notion 도구들:")
            for i, tool in enumerate(notion_tools, 1):
                print(f"  {i}. {tool.name}: {tool.description}")
            print()

            memory = MemorySaver()
            agent = create_react_agent(model, notion_tools, checkpointer=memory)
            print("Notion Agent 생성 완료")

            await start_chatbot(agent)

async def start_chatbot(agent):
    # .env에서 기본 페이지 ID 읽기
    default_page_id = os.getenv("NOTION_PAGE_ID", "")
    
    print("\n" + "="*60)
    print("Notion 자동화 Agent 시작!")
    if default_page_id:
        print(f"기본 작업 페이지 ID: {default_page_id}")
        print("페이지 ID를 별도로 입력할 필요 없이 바로 작업할 수 있습니다.")
    else:
        print("⚠️  .env 파일에 NOTION_PAGE_ID가 설정되지 않았습니다.")
        print("페이지 작업 시 페이지 ID를 직접 입력해야 합니다.")
    print("'quit' 또는 'exit'로 종료")
    print("="*60 + "\n")

    session_id = "notion_session"

    while True:
        user_input = input("질문을 입력하세요: ")
        if user_input.lower() in ['quit', 'exit', '종료']:
            print("\nNotion Agent를 종료합니다.")
            break

        # 기본 페이지 ID가 설정되어 있으면 사용자 입력에 추가 정보 제공
        if default_page_id:
            enhanced_input = f"{user_input}\n\n[참고: 기본 작업 페이지 ID는 {default_page_id}입니다. 페이지 작업 시 이 ID를 사용하세요.]"
        else:
            enhanced_input = user_input

        print("처리 중...\n")
        user_message = HumanMessage(content=enhanced_input)
        config = {"configurable": {"thread_id": session_id}}

        response = await agent.ainvoke({"messages": [user_message]}, config=config)
        print("응답:")
        print(response["messages"][-1].content)
        print("\n" + "="*50 + "\n")

async def run():
    try:
        await setup_servers()
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
