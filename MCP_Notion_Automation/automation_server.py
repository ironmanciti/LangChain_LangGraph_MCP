from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

# 환경 변수 로드
load_dotenv()

# 전역 Notion API 설정
NOTION_API_KEY = None
NOTION_VERSION = "2022-06-28"

@asynccontextmanager
async def lifespan(app):
    """서버 시작/종료 시 Notion API 설정 관리"""
    global NOTION_API_KEY
    try:
        # 서버 시작 시 Notion API 키 설정
        NOTION_API_KEY = os.getenv("NOTION_API_KEY")
        if not NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        print("Notion API 설정 완료")
        yield
    finally:
        # 서버 종료 시 정리
        NOTION_API_KEY = None
        print("Notion API 연결 종료")

def _make_notion_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Notion API 요청을 보내는 헬퍼 함수"""
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    url = f"https://api.notion.com/v1/{endpoint}"
    
    try:
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
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Notion API 요청 실패: {str(e)}")

mcp = FastMCP("NotionAutomation", lifespan=lifespan)

@mcp.tool()
async def create_database_analysis_page(
    title: str,
    analysis_data: str,
    page_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    데이터베이스 분석 결과를 Notion 페이지에 자동으로 생성합니다.
    
    Args:
        title (str): 페이지 제목
        analysis_data (str): 분석 결과 데이터 (JSON 문자열 또는 텍스트)
        page_id (str, optional): 부모 페이지 ID. 없으면 루트에 생성
    
    Returns:
        Dict[str, Any]: 생성된 페이지 정보
    """
    print(f"[DEBUG] create_database_analysis_page 호출됨")
    print(f"[DEBUG] title: {title}")
    print(f"[DEBUG] analysis_data 타입: {type(analysis_data)}")
    print(f"[DEBUG] analysis_data 길이: {len(analysis_data) if analysis_data else 0}")
    print(f"[DEBUG] page_id: {page_id}")
    
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # 기본 페이지 ID 설정 (환경 변수에서 가져오거나 None)
        if not page_id:
            page_id = os.getenv("NOTION_PAGE_ID")
        
        # 분석 데이터를 Notion 블록으로 변환
        print(f"[DEBUG] 분석 데이터 길이: {len(analysis_data)}")
        blocks = _convert_analysis_to_blocks(analysis_data)
        print(f"[DEBUG] 생성된 블록 수: {len(blocks)}")
        
        # Notion API로 페이지 생성 (블록 포함)
        page_data = {
            "parent": {"page_id": page_id} if page_id else {"type": "workspace"},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": blocks  # 블록을 페이지 생성 시 직접 포함
        }
        
        # 페이지와 블록을 함께 생성
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
async def update_existing_page(
    page_id: str,
    analysis_data: str,
    append: bool = True
) -> Dict[str, Any]:
    """
    기존 Notion 페이지에 데이터베이스 분석 결과를 추가합니다.
    
    Args:
        page_id (str): 업데이트할 페이지 ID
        analysis_data (str): 분석 결과 데이터
        append (bool): True면 기존 내용에 추가, False면 덮어쓰기
    
    Returns:
        Dict[str, Any]: 업데이트 결과
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # 분석 데이터를 Notion 블록으로 변환
        blocks = _convert_analysis_to_blocks(analysis_data)
        
        if not append:
            # 기존 블록들 삭제
            existing_blocks = _make_notion_request("GET", f"blocks/{page_id}/children")
            for block in existing_blocks.get("results", []):
                _make_notion_request("DELETE", f"blocks/{block['id']}")
        
        # 새 블록들 추가
        for block in blocks:
            _make_notion_request("POST", f"blocks/{page_id}/children", {"children": [block]})
        
        return {
            "success": True,
            "page_id": page_id,
            "message": "페이지가 성공적으로 업데이트되었습니다."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"페이지 업데이트 중 오류 발생: {str(e)}"
        }

@mcp.tool()
async def create_database_table(
    page_id: str,
    table_data: List[Dict[str, Any]],
    table_title: str = "분석 결과 테이블"
) -> Dict[str, Any]:
    """
    데이터베이스 쿼리 결과를 Notion 테이블로 생성합니다.
    
    Args:
        page_id (str): 테이블을 추가할 페이지 ID
        table_data (List[Dict[str, Any]]): 테이블 데이터 (딕셔너리 리스트)
        table_title (str): 테이블 제목
    
    Returns:
        Dict[str, Any]: 테이블 생성 결과
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        if not table_data:
            return {
                "success": False,
                "error": "테이블 데이터가 비어있습니다."
            }
        
        # 테이블 헤더 추출
        headers = list(table_data[0].keys())
        
        # 테이블 블록 생성
        table_block = {
            "type": "table",
            "table": {
                "table_width": len(headers),
                "has_column_header": True,
                "has_row_header": False,
                "children": []
            }
        }
        
        # 헤더 행 추가
        header_row = {
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": header}}] for header in headers]
            }
        }
        table_block["table"]["children"].append(header_row)
        
        # 데이터 행들 추가
        for row_data in table_data:
            row = {
                "type": "table_row",
                "table_row": {
                    "cells": [[{"type": "text", "text": {"content": str(value)} if value is not None else {"content": ""}}] for value in row_data.values()]
                }
            }
            table_block["table"]["children"].append(row)
        
        # 페이지에 테이블 추가
        _make_notion_request("POST", f"blocks/{page_id}/children", {"children": [table_block]})
        
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
    Notion에서 페이지를 검색합니다.
    
    Args:
        query (str): 검색 쿼리
        page_size (int): 반환할 페이지 수
    
    Returns:
        Dict[str, Any]: 검색 결과
    """
    if NOTION_API_KEY is None:
        raise ValueError("Notion API 키가 설정되지 않았습니다.")
    
    try:
        # Notion API로 페이지 검색
        search_data = {
            "query": query,
            "page_size": page_size
        }
        
        result = _make_notion_request("POST", "search", search_data)
        
        pages = []
        for page in result.get("results", []):
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
    """분석 데이터를 Notion 블록으로 변환 (단순화된 버전)"""
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
        
        # 텍스트를 간단한 단락으로 분할
        text_chunks = [analysis_data[i:i+2000] for i in range(0, len(analysis_data), 2000)]
        
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

def _format_json_data(data: Any, level: int = 0) -> List[Dict[str, Any]]:
    """JSON 데이터를 Notion 블록으로 포맷팅"""
    blocks = []
    indent = "  " * level
    
    if isinstance(data, dict):
        for key, value in data.items():
            # 키를 헤딩으로 표시
            blocks.append({
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": f"🔹 {key}"}}]
                }
            })
            
            if isinstance(value, (dict, list)):
                blocks.extend(_format_json_data(value, level + 1))
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": str(value)}}]
                    }
                })
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": str(item)}}]
                }
            })
    
    else:
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": str(data)}}]
            }
        })
    
    return blocks

def _extract_page_title(page: Dict[str, Any]) -> str:
    """페이지에서 제목 추출"""
    properties = page.get("properties", {})
    for prop_name, prop_data in properties.items():
        if prop_data.get("type") == "title" and prop_data.get("title"):
            return prop_data["title"][0]["text"]["content"]
    return "제목 없음"

@mcp.resource("notion://pages")
async def get_notion_pages() -> Dict[str, Any]:
    """Notion 페이지 목록 조회"""
    if NOTION_API_KEY is None:
        return {"error": "Notion API 키가 설정되지 않았습니다."}
    
    try:
        # Notion API로 페이지 검색
        result = _make_notion_request("POST", "search", {"page_size": 20})
        
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
    return [
        base.AssistantMessage(
            "당신은 Notion 자동화 어시스턴트입니다.\n"
            "다음과 같은 기능을 제공합니다:\n"
            "- 데이터베이스 분석 결과를 Notion 페이지에 자동 생성\n"
            "- 기존 페이지에 분석 결과 추가/업데이트\n"
            "- 쿼리 결과를 Notion 테이블로 변환\n"
            "- Notion 페이지 검색 및 관리\n"
            "분석 결과를 구조화된 형태로 Notion에 저장하여 팀과 공유할 수 있습니다."
        ),
        base.UserMessage(message),
    ]

if __name__ == "__main__":
    try:
        print("Notion Automation MCP Server is running...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
