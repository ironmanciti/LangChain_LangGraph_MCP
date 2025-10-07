# MCP Notion 자동화 시스템

이 시스템은 Model Context Protocol (MCP)을 사용하여 Chinook 데이터베이스 분석과 Notion 자동 업데이트를 결합한 대화형 AI 에이전트입니다.

## 🚀 주요 기능

### 1. Chinook 데이터베이스 분석 (MCP 서버)
- SQL 쿼리 실행 및 결과 반환
- 테이블 스키마 조회 및 정보 제공
- 데이터베이스 메타데이터 검색
- 쿼리 문법 검증 및 최적화

### 2. Notion 자동 업데이트 (MCP 서버)
- 사용자 요청 키워드 자동 감지
- 분석 결과를 Notion 페이지로 자동 변환
- 실시간 페이지 생성 및 업데이트
- 구조화된 데이터 포맷팅

### 3. 통합 클라이언트 (automation_client.py)
- 이중 MCP 서버 연결 관리
- 대화형 메모리 및 컨텍스트 유지
- 자동 키워드 감지 및 Notion 업데이트 트리거
- LangChain 기반 대화형 AI 에이전트

## 🛠️ 설정 방법

### 1. 환경 변수 설정

`.env` 파일에 다음 변수들을 설정하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# Notion API 설정 (자동 업데이트용)
NOTION_API_KEY=ntn_your_notion_api_key_here
NOTION_PAGE_ID=your_notion_page_id_here
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `mcp` - Model Context Protocol
- `langchain` - LangChain 프레임워크
- `langchain-mcp-adapters` - MCP-LangChain 어댑터
- `requests` - HTTP 요청
- `python-dotenv` - 환경 변수 관리

### 3. Notion API 키 발급

1. [Notion Developers](https://www.notion.so/my-integrations)에 접속
2. "New integration" 클릭
3. 통합 이름 입력 (예: "MCP Notion Automation")
4. 워크스페이스 선택
5. "Submit" 클릭하여 API 키 생성
6. 생성된 API 키를 `NOTION_API_KEY`에 설정 (형식: `ntn_...`)

### 4. 페이지 ID 확인

1. Notion에서 분석 결과를 저장할 페이지 열기
2. URL에서 페이지 ID 추출
   - URL: `https://www.notion.so/your-workspace/Page-Title-{page_id}`
   - `{page_id}` 부분을 `NOTION_PAGE_ID`에 설정

### 5. 권한 설정

Notion 통합에 페이지 접근 권한을 부여:
1. 대상 페이지 열기
2. 우상단 "Share" 클릭
3. 생성한 통합 추가
4. "Can edit" 권한 부여

## 🎯 사용 방법

### 1. MCP 서버 실행

```bash
# Chinook 데이터베이스 분석 서버
python ../LangGraph_MCP_Agent/agent_server.py

# Notion 자동화 서버 (별도 터미널)
python automation_server.py
```

### 2. 통합 클라이언트 실행

```bash
python automation_client.py
```

### 3. 사용 예시

```
=====대화형 Chinook 데이터베이스 분석 챗봇 시작 (메모리 + Notion 자동 업데이트)=====
종료하려면 'quit' 또는 'exit'를 입력하세요.
대화 히스토리가 기억되고, Notion 업데이트 요청 시 자동으로 전송됩니다!

Notion 업데이트를 원할 때는 'notion에 저장해줘', '노션에 올려줘' 등의 키워드를 포함하세요.

질문을 입력하세요: 고객별 총 구매액을 조회해줘

=====PROCESSING WITH MEMORY=====
=====RESPONSE=====
[분석 결과 출력]

질문을 입력하세요: 이 결과를 notion에 저장해줘

=====NOTION AUTO-UPDATE DETECTED=====
분석 결과를 Notion에 자동 업데이트 중...
전송할 데이터 타입: <class 'str'>
전송할 데이터 길이: 1234
Notion에 성공적으로 업데이트되었습니다!
페이지 URL: https://www.notion.so/...
```

### Notion 업데이트 키워드

다음 키워드가 포함된 요청 시 자동으로 Notion에 업데이트됩니다:

- "notion", "노션"
- "업데이트", "저장", "전송", "보내", "올려", "추가"

예시:
- "이 결과를 notion에 저장해줘"
- "노션에 올려줘"
- "분석 결과를 업데이트해줘"

## 🔧 기술적 특징

### 1. MCP 아키텍처
- **automation_server.py**: Notion API 직접 호출 MCP 서버
- **agent_server.py**: Chinook DB 분석 MCP 서버
- **automation_client.py**: 이중 MCP 서버 연결 클라이언트

### 2. LangChain 통합
- LangChain MCP 어댑터 사용
- 대화형 메모리 (MemorySaver)
- ReAct 에이전트 패턴

### 3. 스마트 데이터 처리
- 키워드 기반 Notion 업데이트 감지
- 텍스트 데이터 자동 추출 및 구조화
- Notion 블록 형식 자동 변환

### 4. 견고한 오류 처리
- MCP 서버 연결 실패 처리
- Notion API 오류 복구
- 단계별 디버깅 정보 제공

## 📊 지원되는 분석 유형

### 1. SQL 쿼리 결과
```sql
SELECT CustomerId, SUM(Total) as TotalSpent 
FROM Invoice 
GROUP BY CustomerId 
ORDER BY TotalSpent DESC
```

### 2. 테이블 스키마 정보
- 컬럼 정보
- 데이터 타입
- 제약 조건

### 3. 데이터베이스 통계
- 테이블 개수
- 레코드 수
- 관계 정보

## 🎨 Notion 페이지 구조

생성되는 Notion 페이지는 다음과 같은 구조를 가집니다:

```
데이터베이스 분석 결과 - 2024-01-15 14:30:00

[분석 결과 텍스트 내용이 여기에 표시됩니다]
- 테이블 구조 정보
- SQL 쿼리 결과
- 데이터베이스 통계
- 기타 분석 내용
```

### 페이지 생성 과정
1. **페이지 생성**: 제목과 기본 구조 생성
2. **블록 추가**: 분석 결과를 Notion 블록으로 변환
3. **텍스트 분할**: 긴 텍스트를 2000자 단위로 분할
4. **오류 처리**: 블록 추가 실패 시 개별 처리

## 🚨 주의사항

1. **API 키 보안**: `.env` 파일을 `.gitignore`에 추가하여 API 키가 노출되지 않도록 주의
2. **Notion 권한**: 통합에 적절한 권한이 부여되었는지 확인
3. **MCP 서버 실행**: 두 개의 MCP 서버가 모두 실행되어야 함
4. **네트워크 연결**: Notion API 호출을 위해 인터넷 연결 필요
5. **데이터 크기**: 대용량 데이터의 경우 Notion 페이지 생성 시간이 오래 걸릴 수 있음

## 🔍 문제 해결

### Notion 업데이트 실패
- API 키가 올바른지 확인 (형식: `ntn_...`)
- 페이지 ID가 정확한지 확인
- 통합 권한이 부여되었는지 확인
- Notion API 응답 오류 메시지 확인

### MCP 서버 연결 실패
- `agent_server.py`가 실행 중인지 확인
- `automation_server.py`가 실행 중인지 확인
- 환경 변수가 올바르게 설정되었는지 확인

### 데이터 추출 실패
- 분석 결과에 텍스트 데이터가 포함되어 있는지 확인
- 키워드 감지가 정상적으로 작동하는지 확인

### 디버깅
- `automation_server.py`에 상세한 디버깅 로그 포함
- Notion API 요청/응답 로그 확인
- MCP 서버 연결 상태 확인

## 📈 확장 가능성

이 MCP 시스템은 다음과 같은 방식으로 확장할 수 있습니다:

1. **추가 MCP 서버**: 다른 데이터베이스나 서비스용 MCP 서버 추가
2. **다양한 출력 형식**: PDF, Excel, CSV 등 다양한 형식으로 내보내기
3. **스케줄링**: 정기적인 분석 및 업데이트 자동화
4. **알림 기능**: Slack, Teams, Discord 등으로 결과 알림
5. **웹 인터페이스**: Streamlit, FastAPI 등을 통한 웹 인터페이스
6. **다중 사용자 지원**: 사용자별 세션 관리 및 권한 제어

## 📁 파일 구조

```
MCP_Notion_Automation/
├── automation_client.py      # 통합 클라이언트 (LangChain + MCP)
├── automation_server.py      # Notion MCP 서버
├── README.md                 # 이 문서
├── requirements.txt          # 의존성 패키지
└── .env                      # 환경 변수 (생성 필요)

../LangGraph_MCP_Agent/
└── agent_server.py           # Chinook DB MCP 서버
```

## 라이선스

MIT License