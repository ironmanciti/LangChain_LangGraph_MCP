# Notion MCP Smithery Agent

## 프로그램 개요

### notion_agent_smithery_client.py
- **단일 Notion MCP 클라이언트**: 공식 @notionhq/notion-mcp-server만 사용하는 전용 클라이언트
- **Notion 전용 Agent**: 데이터베이스 분석 없이 순수 Notion 작업에 특화된 대화형 챗봇
- **공식 MCP 서버**: npx로 실행되는 Notion 공식 MCP 서버와 직접 연동
- **환경변수 기반**: NOTION_PAGE_ID를 기본 작업 페이지로 설정하여 편의성 제공
- **도구 목록 표시**: 사용 가능한 Notion MCP 도구들을 시작 시 자동 출력
- **ReAct Agent**: LangGraph 기반으로 Notion 작업을 자동화

## 주요 특징
- **Notion 전용**: SQL 분석 없이 순수 Notion 페이지/데이터베이스 관리에 집중
- **공식 서버 활용**: Notion에서 공식 제공하는 MCP 서버의 모든 기능 활용


