from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
from langchain_community.utilities import SQLDatabase
import os

# 전역 데이터베이스 연결 변수
db = None

@asynccontextmanager
async def lifespan(app):
    """서버 시작/종료 시 데이터베이스 연결 관리"""
    global db
    try:
        # 서버 시작 시 데이터베이스 연결
        db_path = "Chinook.db"
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Chinook.db 파일을 찾을 수 없습니다: {db_path}")
        
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        print("Chinook 데이터베이스 연결 성공")
        yield
    finally:
        # 서버 종료 시 연결 정리
        if db:
            db = None
            print("Chinook 데이터베이스 연결 종료")

mcp = FastMCP("ChinookDBAnalysis", lifespan=lifespan)

@mcp.tool()
def execute_sql_query(query: str) -> str:
    """
    SQL 쿼리를 실행하고 결과를 반환합니다.
    Args:
        query (str): 실행할 SQL 쿼리입니다.
    Returns:
        str: 쿼리 실행 결과를 문자열로 반환합니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        result = db.run(query)
        return str(result)
    except Exception as e:
        return f"쿼리 실행 중 오류 발생: {str(e)}"

@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    특정 테이블의 스키마 정보를 반환합니다.
    Args:
        table_name (str): 스키마를 조회할 테이블 이름입니다.
    Returns:
        str: 테이블 스키마 정보를 문자열로 반환합니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        schema_info = db.get_table_info([table_name])
        return schema_info
    except Exception as e:
        return f"스키마 조회 중 오류 발생: {str(e)}"

@mcp.tool()
def list_tables() -> list:
    """
    데이터베이스의 모든 테이블 목록을 반환합니다.
    Returns:
        list: 테이블 이름들의 리스트입니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        tables = db.get_usable_table_names()
        return tables
    except Exception as e:
        return [f"테이블 목록 조회 중 오류 발생: {str(e)}"]

@mcp.tool()
def validate_sql_query(query: str) -> dict:
    """
    SQL 쿼리의 문법을 검증합니다.
    Args:
        query (str): 검증할 SQL 쿼리입니다.
    Returns:
        dict: 검증 결과와 오류 메시지를 포함하는 딕셔너리입니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        # 쿼리 문법 검증을 위해 실제 실행하지 않고 파싱만 시도
        validation_query = f"EXPLAIN QUERY PLAN {query}"
        db.run(validation_query)
        return {"valid": True, "message": "쿼리 문법이 올바릅니다."}
    except Exception as e:
        return {"valid": False, "message": f"쿼리 문법 오류: {str(e)}"}

@mcp.resource("database://info")
def get_database_info() -> dict:
    """Get Chinook database information"""
    if db is None:
        return {"error": "데이터베이스가 연결되지 않았습니다."}
    
    try:
        tables = db.get_usable_table_names()
        return {
            "database": "Chinook",
            "tables_count": len(tables),
            "tables": tables[:3] + (["..."] if len(tables) > 3 else []),  # 처음 3개만 표시
            "description": "디지털 미디어 스토어 샘플 데이터베이스"
        }
    except Exception as e:
        return {"error": f"데이터베이스 정보 조회 중 오류: {str(e)}"}

@mcp.resource("table://{table_name}")
def get_table_info(table_name: str) -> str:
    """Get specific table information"""
    if db is None:
        return "데이터베이스가 연결되지 않았습니다."
    
    try:
        schema_info = db.get_table_info([table_name])
        # 스키마 정보를 100자로 제한
        if len(schema_info) > 100:
            return schema_info[:100] + "..."
        return schema_info
    except Exception as e:
        return f"테이블 정보 조회 중 오류: {str(e)}"


@mcp.prompt()
def default_prompt(message: str) -> list[base.Message]:
    return [
        base.AssistantMessage(
            "당신은 유용한 Chinook 데이터베이스 분석 어시스턴트입니다.\n"
            "다음과 같은 방법으로 Chinook 음악 스토어 데이터베이스를 분석할 수 있습니다:\n"
            "- 데이터를 검색하기 위한 SQL 쿼리 실행\n"
            "- 테이블 스키마 정보 제공\n"
            "- SQL 쿼리 문법 검증\n"
            "- 사용 가능한 테이블 목록 제공\n"
            "분석 결과를 명확하게 정리하여 반환해주세요."
        ),
        base.UserMessage(message),
    ]

if __name__ == "__main__":
    try:
        print("MCP Server is running...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")