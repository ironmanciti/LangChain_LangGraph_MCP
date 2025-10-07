from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

load_dotenv()

# 전역 Notion API 설정
NOTION_API_KEY = None
# Notion API 버전 (최신 버전으로 업데이트)
NOTION_VERSION = "2022-06-28"

@asynccontextmanager
async def lifespan(app):
    """
    서버 시작/종료 시 Notion API 설정 관리
    
    FastMCP 서버의 lifespan 이벤트를 처리합니다.
    - 서버 시작 시: Notion API 키 로드 및 검증
    - 서버 종료 시: 리소스 정리
    """
    global NOTION_API_KEY
    try:
        # 서버 시작 시 환경 변수에서 Notion API 키 가져오기
        NOTION_API_KEY = os.getenv("NOTION_API_KEY")
        if not NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        print("Notion API 설정 완료")
        
        # yield로 서버가 실행되는 동안 대기
        yield
    finally:
        # 서버 종료 시 API 키 정리
        NOTION_API_KEY = None
        print("Notion API 연결 종료")

def _make_notion_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """
    Notion API 요청을 보내는 헬퍼 함수
    
    Args:
        method (str): HTTP 메서드 (GET, POST, PATCH, DELETE)
        endpoint (str): API 엔드포인트 (예: "pages", "blocks/{id}/children")
        data (Dict, optional): 요청 본문 데이터
    
    Returns:
        Dict: API 응답 JSON
        
    Raises:
        ValueError: 지원하지 않는 HTTP 메서드
        Exception: API 요청 실패
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    # Notion API 요청 헤더 설정
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",  # 인증 토큰
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION  # API 버전 명시
    }
    
    # 전체 URL 구성
    url = f"https://api.notion.com/v1/{endpoint}"
    
    try:
        # HTTP 메서드에 따라 적절한 요청 실행
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
        
        # HTTP 오류 발생 시 예외 발생 (4xx, 5xx)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Notion API 요청 실패: {str(e)}")

# FastMCP 서버 인스턴스 생성
mcp = FastMCP("NotionAutomation", lifespan=lifespan)

@mcp.tool()
async def create_database_analysis_page(
    title: str,
    analysis_data: str,
    page_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    데이터베이스 분석 결과를 Notion 페이지에 자동으로 생성합니다.
    
    분석 결과를 구조화된 Notion 페이지로 변환하여 저장합니다.
    팀원들과 분석 결과를 쉽게 공유할 수 있습니다.
    
    Args:
        title (str): 생성할 페이지의 제목
        analysis_data (str): 분석 결과 데이터 (JSON 문자열 또는 일반 텍스트)
        page_id (str, optional): 부모 페이지 ID. 없으면 워크스페이스 루트에 생성
    
    Returns:
        Dict[str, Any]: 페이지 생성 결과
            - success (bool): 성공 여부
            - page_id (str): 생성된 페이지 ID
            - url (str): 페이지 URL
            - title (str): 페이지 제목
            - message (str): 결과 메시지
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # page_id가 없으면 환경 변수에서 기본값 가져오기
        if not page_id:
            page_id = os.getenv("NOTION_PAGE_ID")
        
        # 분석 데이터를 Notion 블록 형식으로 변환
        print(f"[DEBUG] 분석 데이터 길이: {len(analysis_data)}")
        blocks = _convert_analysis_to_blocks(analysis_data)
        print(f"[DEBUG] 생성된 블록 수: {len(blocks)}")
        
        # Notion 페이지 생성 요청 데이터 구성
        page_data = {
            # 부모 페이지 설정 (없으면 워크스페이스 루트)
            "parent": {"page_id": page_id} if page_id else {"type": "workspace"},
            # 페이지 속성 (제목)
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            # 페이지 내용 (블록들)
            "children": blocks  # 블록을 페이지 생성 시 직접 포함
        }
        
        # Notion API로 페이지와 블록을 함께 생성
        result = _make_notion_request("POST", "pages", page_data)
        
        return {
            "success": True,
            "page_id": result["id"],
            "url": result["url"],
            "title": title,
            "message": "데이터베이스 분석 결과가 Notion 페이지에 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        print(f"[ERROR] 페이지 생성 중 오류: {str(e)}")
        return {
            "success": False,
            "error": f"페이지 생성 중 오류 발생: {str(e)}"
        }

@mcp.tool()
async def create_database_table(
    page_id: str,
    table_data: List[Dict[str, Any]],
    table_title: str = "분석 결과 테이블"
) -> Dict[str, Any]:
    """    
    SQL 쿼리 결과나 데이터 분석 결과를 시각적인 테이블 형태로
    Notion 페이지에 추가합니다.
    
    Args:
        page_id (str): 테이블을 추가할 페이지의 ID
        table_data (List[Dict[str, Any]]): 테이블 데이터 (딕셔너리 리스트)
            예: [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        table_title (str): 테이블 제목
    
    Returns:
        Dict[str, Any]: 테이블 생성 결과
            - success (bool): 성공 여부
            - page_id (str): 페이지 ID
            - rows (int): 생성된 행 수
            - columns (int): 컬럼 수
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # 테이블 데이터가 비어있는지 확인
        if not table_data:
            return {
                "success": False,
                "error": "테이블 데이터가 비어있습니다."
            }
        
        # 첫 번째 행에서 테이블 헤더(컬럼명) 추출
        headers = list(table_data[0].keys())
        
        # Notion에서는 테이블 대신 구조화된 텍스트 블록 사용
        # 제목 블록 추가
        title_block = {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": table_title}}]
            }
        }
        
        # 헤더를 구분자로 연결한 문자열 생성
        header_text = " | ".join(headers)
        header_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": header_text, "annotations": {"bold": True}}}]
            }
        }
        
        # 구분선 추가
        divider_block = {
            "type": "divider",
            "divider": {}
        }
        
        # 데이터 행들을 텍스트 블록으로 추가
        data_blocks = []
        for row_data in table_data:
            row_text = " | ".join([str(row_data.get(header, "")) for header in headers])
            data_block = {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": row_text}}]
                }
            }
            data_blocks.append(data_block)
        
        # 모든 블록을 하나의 리스트로 결합
        all_blocks = [title_block, header_block, divider_block] + data_blocks
        
        # 페이지에 모든 블록 추가
        _make_notion_request("POST", f"blocks/{page_id}/children", {"children": all_blocks})
        
        return {
            "success": True,
            "page_id": page_id,
            "table_title": table_title,
            "rows": len(table_data),
            "columns": len(headers),
            "message": "테이블이 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"테이블 생성 중 오류 발생: {str(e)}"
        }

@mcp.tool()
async def search_notion_pages(query: str = "", page_size: int = 10) -> Dict[str, Any]:
    """
    Notion에서 키워드로 페이지를 검색하여 ID, 제목, URL 등의 정보를 가져옵니다.

    Args:
        query (str): 검색할 키워드 (빈 문자열이면 최근 페이지 반환)
        page_size (int): 반환할 최대 페이지 수
    
    Returns:
        Dict[str, Any]: 검색 결과
            - success (bool): 성공 여부
            - pages (List): 페이지 정보 리스트
            - total (int): 찾은 페이지 수
            - query (str): 검색한 쿼리
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # Notion API 검색 요청 데이터
        search_data = {
            "query": query,
            "page_size": page_size
        }
        
        # 검색 API 호출
        result = _make_notion_request("POST", "search", search_data)
        
        # 페이지 정보만 추출하여 정리
        pages = []
        for page in result.get("results", []):
            # 페이지 객체만 처리 (데이터베이스 제외)
            if page["object"] == "page":
                page_info = {
                    "id": page["id"],
                    "title": _extract_page_title(page),
                    "url": page["url"],
                    "created_time": page["created_time"],
                    "last_edited_time": page["last_edited_time"]
                }
                pages.append(page_info)
        
        return {
            "success": True,
            "pages": pages,
            "total": len(pages),
            "query": query
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"페이지 검색 중 오류 발생: {str(e)}"
        }

def _convert_analysis_to_blocks(analysis_data: str) -> List[Dict[str, Any]]:
    """
    분석 데이터를 Notion 블록으로 변환
    
    긴 텍스트를 Notion 블록으로 분할합니다.
    (Notion API 블록당 최대 2000자 제한)
    
    Args:
        analysis_data (str): 변환할 분석 데이터
    
    Returns:
        List[Dict[str, Any]]: Notion 블록 리스트
    """
    blocks = []
    
    try:
        # 현재 시간 헤더 추가
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        blocks.append({
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": f"데이터베이스 분석 결과 - {current_time}"}}]
            }
        })
        
        # 텍스트를 2000자 단위로 분할
        text_chunks = [analysis_data[i:i+2000] for i in range(0, len(analysis_data), 2000)]
        
        # 각 청크를 단락 블록으로 변환
        for chunk in text_chunks:
            blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
        
        return blocks
        
    except Exception as e:
        # 오류 발생 시 기본 텍스트 블록 반환
        return [{
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": analysis_data[:2000]}}]
            }
        }]

def _extract_page_title(page: Dict[str, Any]) -> str:
    """
    Notion API 응답에서 페이지 제목을 추출합니다.
    
    Args:
        page (Dict[str, Any]): Notion 페이지 객체
    
    Returns:
        str: 페이지 제목 (없으면 "제목 없음")
    """
    properties = page.get("properties", {})
    # properties에서 title 타입의 속성 찾기
    for prop_name, prop_data in properties.items():
        if prop_data.get("type") == "title" and prop_data.get("title"):
            return prop_data["title"][0]["text"]["content"]
    return "제목 없음"

@mcp.resource("notion://pages")
async def get_notion_pages() -> Dict[str, Any]:
    """
    Notion 페이지 목록 조회 (MCP 리소스)
    
    클라이언트가 "notion://pages" URI로 접근 시 
    최근 페이지 목록을 반환합니다.
    
    Returns:
        Dict[str, Any]: 페이지 목록
            - pages (List): 페이지 정보 리스트
            - total (int): 총 페이지 수
    """
    if NOTION_API_KEY is None:
        return {"error": "Notion API 키가 설정되지 않았습니다."}
    
    try:
        # 최근 20개 페이지 검색
        result = _make_notion_request("POST", "search", {"page_size": 20})
        
        # 페이지 정보 추출
        pages = []
        for page in result.get("results", []):
            if page["object"] == "page":
                pages.append({
                    "id": page["id"],
                    "title": _extract_page_title(page),
                    "url": page["url"]
                })
        
        return {
            "pages": pages,
            "total": len(pages)
        }
    except Exception as e:
        return {"error": f"페이지 조회 중 오류: {str(e)}"}

@mcp.prompt()
def default_prompt(message: str) -> List[base.Message]:
    """
    기본 프롬프트 생성 (MCP 프롬프트)
    
    Args:
        message (str): 사용자 메시지
    
    Returns:
        List[base.Message]: 어시스턴트와 사용자 메시지 리스트
    """
    return [
        base.AssistantMessage(
            "당신은 Notion 자동화 어시스턴트입니다.\n"
            "다음과 같은 기능을 제공합니다:\n"
            "- 데이터베이스 분석 결과를 Notion 페이지에 자동 생성\n"
            "- 쿼리 결과를 Notion 테이블로 변환\n"
            "- Notion 페이지 검색 및 관리\n"
            "분석 결과를 구조화된 형태로 Notion에 저장하여 팀과 공유할 수 있습니다."
        ),
        base.UserMessage(message),
    ]

# 메인 실행 블록
if __name__ == "__main__":
    try:
        print("Notion Automation MCP Server is running...")
        # stdio 방식으로 MCP 서버 실행
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        # Ctrl+C로 종료 시 정상 종료 메시지
        print("\n서버가 정상적으로 종료되었습니다.")
    except Exception as e:
        # 예상치 못한 오류 발생 시
        print(f"서버 오류: {e}")
