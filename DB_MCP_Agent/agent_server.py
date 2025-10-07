from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
from langchain_community.utilities import SQLDatabase
import os
import sys
import asyncio

# 전역 데이터베이스 연결 변수
# 서버 수명 주기 동안 유지되는 데이터베이스 연결 객체
db = None

@asynccontextmanager
async def lifespan(app):
    """
    서버 시작/종료 시 데이터베이스 연결 관리
    """
    global db
    try:
        # 서버 시작 시 데이터베이스 연결 (절대경로로 계산)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "Chinook.db")
        
        # 데이터베이스 파일 존재 여부 확인
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Chinook.db 파일을 찾을 수 없습니다: {db_path}")
        
        # SQLite 데이터베이스 연결 생성
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        print("Chinook 데이터베이스 연결 성공", file=sys.stderr)
        
        # yield로 서버가 실행되는 동안 대기
        yield
    finally:
        # 서버 종료 시 연결 정리
        if db:
            db = None
            print("Chinook 데이터베이스 연결 종료", file=sys.stderr)

# FastMCP 서버 인스턴스 생성
# - "ChinookDBAnalysis": MCP 서버의 이름
# - lifespan: 서버 시작/종료 시 실행될 함수
mcp = FastMCP("ChinookDBAnalysis", lifespan=lifespan)

@mcp.tool()
def execute_sql_query(query: str) -> str:
    """
    SQL 쿼리를 실행하고 결과를 반환합니다.
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
    특정 테이블의 컬럼명, 데이터 타입, 제약조건 등의
    스키마 정보를 조회합니다.
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
    현재 연결된 데이터베이스에서 사용 가능한
    모든 테이블의 이름을 리스트로 반환합니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        # 사용 가능한 모든 테이블 이름 조회
        tables = db.get_usable_table_names()
        return tables
    except Exception as e:
        return [f"테이블 목록 조회 중 오류 발생: {str(e)}"]

@mcp.tool()
def validate_sql_query(query: str) -> dict:
    """
    실제로 쿼리를 실행하지 않고 문법만 검증하여
    SQL 쿼리가 올바른지 확인합니다.
    """
    if db is None:
        raise ValueError("데이터베이스가 연결되지 않았습니다.")
    
    try:
        # 쿼리가 유효하면 실행 계획만 반환되고 데이터는 변경되지 않음
        validation_query = f"EXPLAIN QUERY PLAN {query}"
        db.run(validation_query)
        return {"valid": True, "message": "쿼리 문법이 올바릅니다."}
    except Exception as e:
        return {"valid": False, "message": f"쿼리 문법 오류: {str(e)}"}

@mcp.resource("database://info")
def get_database_info() -> dict:
    """
    Chinook 데이터베이스의 전반적인 정보를 반환합니다.
    MCP 리소스로 등록되어 클라이언트가 데이터베이스의
    기본 정보를 조회할 수 있습니다.
    
    Returns:
        dict: 데이터베이스 정보
              - database: 데이터베이스 이름
              - tables_count: 테이블 개수
              - tables: 테이블 목록 
              - description: 데이터베이스 설명
    """
    if db is None:
        return {"error": "데이터베이스가 연결되지 않았습니다."}
    
    try:
        # 모든 테이블 목록 조회
        tables = db.get_usable_table_names()
        return {
            "database": "Chinook",
            "tables_count": len(tables),
            "tables": tables,
            "description": "디지털 미디어 스토어 샘플 데이터베이스"
        }
    except Exception as e:
        return {"error": f"데이터베이스 정보 조회 중 오류: {str(e)}"}

@mcp.resource("table://{table_name}")
def get_table_info(table_name: str) -> str:
    """  
    MCP 리소스로 등록되어 동적 URI 패턴으로
    특정 테이블의 상세 정보를 반환합니다.    
    """
    if db is None:
        return "데이터베이스가 연결되지 않았습니다."
    
    try:
        # 테이블 스키마 정보 조회
        schema_info = db.get_table_info([table_name])
        
        # 스키마 정보가 너무 길 경우 100자로 제한하고 "..." 추가
        if len(schema_info) > 100:
            return schema_info[:100] + "..."
        return schema_info
    except Exception as e:
        return f"테이블 정보 조회 중 오류: {str(e)}"


@mcp.prompt()
def default_prompt(message: str) -> list[base.Message]:
    """ 
    MCP 프롬프트로 등록되어 클라이언트가 대화를 시작할 때
    사용할 수 있는 시스템 메시지와 사용자 메시지를 반환합니다.
    """
    return [
        # 어시스턴트의 역할과 기능을 설명하는 시스템 메시지
        base.AssistantMessage(
            "당신은 유용한 Chinook 데이터베이스 분석 어시스턴트입니다.\n"
            "다음과 같은 방법으로 Chinook 음악 스토어 데이터베이스를 분석할 수 있습니다:\n"
            "- 데이터를 검색하기 위한 SQL 쿼리 실행\n"
            "- 테이블 스키마 정보 제공\n"
            "- SQL 쿼리 문법 검증\n"
            "- 사용 가능한 테이블 목록 제공\n"
            "분석 결과를 명확하게 정리하여 반환해주세요."
        ),
        # 사용자의 실제 메시지
        base.UserMessage(message),
    ]

if __name__ == "__main__":
    try:
        print("MCP Server is running...", file=sys.stderr)
        # stdio: 표준 입출력을 통해 클라이언트와 통신
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        # Ctrl+C로 서버 종료 시 정상 종료 메시지 출력
        print("\n✅ 서버가 정상적으로 종료되었습니다.", file=sys.stderr)
    except Exception as e:
        # 클라이언트가 정상적으로 연결을 끊을 때 anyio/asyncio 취소가 전파되며
        # BaseExceptionGroup("unhandled errors in a TaskGroup ...") 또는
        # asyncio.CancelledError/GeneratorExit 등이 발생할 수 있음. 이를 정상 종료로 간주.
        def _is_normal_disconnect(exc: BaseException) -> bool:
            # BaseExceptionGroup일 경우 내부 예외들을 검사
            if hasattr(exc, 'exceptions') and isinstance(exc.exceptions, (list, tuple)):
                return all(_is_normal_disconnect(sub) for sub in exc.exceptions) or False
            # anyio 취소 스코프 RuntimeError도 정상 종료로 간주
            if isinstance(exc, RuntimeError) and 'cancel scope' in str(exc):
                return True
            # Python 3.11+의 BaseExceptionGroup 중 TaskGroup 종료 메시지 포함 시 정상 종료 간주
            if "TaskGroup" in str(type(exc)) or "TaskGroup" in str(exc):
                return True
            return isinstance(exc, (asyncio.CancelledError, GeneratorExit, BrokenPipeError))

        if _is_normal_disconnect(e):
            print("\n✅ 클라이언트 연결 종료로 서버가 정상 종료되었습니다.", file=sys.stderr)
        else:
            # 예상치 못한 오류만 에러로 출력
            print(f"❌ 서버 오류: {e}", file=sys.stderr)