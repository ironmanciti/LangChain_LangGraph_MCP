from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv
import os

load_dotenv()

model = init_chat_model("gpt-5-mini", model_provider="openai")
# model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

# MCP 서버 연결을 위한 파라미터 설정
server_params = StdioServerParameters(
    command="python",                    # 실행할 명령어
    args=["./agent_server.py"],         # MCP 서버 스크립트 경로
)

async def run():
    """
    MCP 클라이언트의 메인 실행 함수
    
    MCP 서버와 연결하여 다음 작업을 수행합니다:
    1. 리소스 테스트 (데이터베이스 정보 조회)
    2. 메모리 기반 대화형 에이전트 실행
    """
    # MCP 서버와 stdio 통신 채널 열기
    async with stdio_client(server_params) as (read, write):
        # 클라이언트 세션 생성 및 초기화
        async with ClientSession(read, write) as session:
            # MCP 서버와 핸드셰이크 및 초기화
            await session.initialize()

            ##### MCP 리소스 기능 테스트 #####
            print("=====TESTING CHINOOK DB RESOURCES=====")
            
            # 1. Database Info Resource 호출
            # URI 패턴: database://info
            try:
                # 데이터베이스 전체 정보 리소스 읽기
                db_info_result = await session.read_resource("database://info")
                # 리소스 결과의 첫 번째 컨텐츠 텍스트 추출
                db_info_text = db_info_result.contents[0].text
                print(f"Database Info Resource: {db_info_text}")
            except Exception as e:
                print(f"Database Info Resource Error: {e}")
            
            # 2. Table Info Resource 호출
            # URI 패턴: table://{table_name}
            try:
                # Employee 테이블의 스키마 정보 리소스 읽기
                table_info_result = await session.read_resource("table://Employee")
                table_info_text = table_info_result.contents[0].text
                # 긴 텍스트는 처음 30자만 출력
                print(f"Table Info Resource (first 30 chars): {table_info_text[:30]}...")
            except Exception as e:
                print(f"Table Info Resource Error: {e}")
            
            print("=====RESOURCES TEST COMPLETE=====\n")

            # MCP 서버의 도구들을 LangChain 형식으로 변환
            # session.list_tools()로 가져온 도구들을 LangChain Tool 객체로 래핑
            tools = await load_mcp_tools(session)  
            
            # 메모리 체크포인터 생성 
            memory = MemorySaver()
            
            # ReAct 에이전트 생성
            agent = create_react_agent(model, tools, checkpointer=memory)

            print("=====대화형 Chinook 데이터베이스 분석 챗봇 시작 (메모리 포함)=====")
            print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
            print("대화 히스토리가 기억됩니다!\n")
            
            # 대화 세션 ID 설정
            session_id = "user_session_1"
            
            while True:
                # 사용자 입력 받기
                user_input = input("질문을 입력하세요: ")
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("챗봇을 종료합니다.")
                    break
                
                user_message = HumanMessage(content=user_input)
                
                # 메모리 설정을 포함한 config 생성
                config = {"configurable": {"thread_id": session_id}}
                
                # 비동기 방식으로 에이전트 호출
                response = await agent.ainvoke(
                    {"messages": [user_message]}, 
                    config=config
                )

                # 에이전트 응답 출력
                print("=====RESPONSE=====")
                # response["messages"]의 마지막 메시지가 에이전트의 최종 답변
                print(response["messages"][-1].content)
                print("\n" + "="*50 + "\n")


# asyncio를 사용하여 비동기 함수 실행
import asyncio

# 이벤트 루프를 생성하고 run() 함수 실행
asyncio.run(run())