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

model = init_chat_model("gpt-5-nano", model_provider="openai")
# model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

server_params = StdioServerParameters(
    command="python",
    args=["./agent_server.py"],
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            ##### RESOURCES TEST #####
            print("=====TESTING CHINOOK DB RESOURCES=====")
            
            # 1. Database Info Resource 호출
            try:
                db_info_result = await session.read_resource("database://info")
                db_info_text = db_info_result.contents[0].text
                print(f"Database Info Resource: {db_info_text}")
            except Exception as e:
                print(f"Database Info Resource Error: {e}")
            
            # 2. Table Info Resource 호출
            try:
                table_info_result = await session.read_resource("table://Employee")
                table_info_text = table_info_result.contents[0].text
                print(f"Table Info Resource (first 30 chars): {table_info_text[:30]}...")
            except Exception as e:
                print(f"Table Info Resource Error: {e}")
            
            
            print("=====RESOURCES TEST COMPLETE=====\n")

            ##### AGENT WITH MEMORY #####
            # MCP 서버에서 가져온 도구들을 langchain의 도구로 변환
            tools = await load_mcp_tools(session)  
            
            # 메모리 체크포인트 추가 (대화 히스토리 기억)
            memory = MemorySaver()
            agent = create_react_agent(model, tools, checkpointer=memory)

            ##### CHATBOT LOOP WITH MEMORY #####
            print("=====대화형 Chinook 데이터베이스 분석 챗봇 시작 (메모리 포함)=====")
            print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
            print("대화 히스토리가 기억됩니다!\n")
            
            # 대화 세션 ID (사용자별로 구분 가능)
            session_id = "user_session_1"
            
            while True:
                user_input = input("질문을 입력하세요: ")
                
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("챗봇을 종료합니다.")
                    break
                
                print("=====PROCESSING WITH MEMORY=====")
                
                # 사용자 메시지를 LangChain 메시지 형식으로 변환
                user_message = HumanMessage(content=user_input)
                
                # 메모리를 포함한 에이전트 실행
                # config에 thread_id를 포함하여 대화 히스토리 유지
                config = {"configurable": {"thread_id": session_id}}
                
                response = await agent.ainvoke(
                    {"messages": [user_message]}, 
                    config=config
                )

                print("=====RESPONSE=====")
                print(response["messages"][-1].content)
                print("\n" + "="*50 + "\n")


import asyncio

asyncio.run(run())