# LangGraph MCP Agent - Chinook 데이터베이스 분석

이 프로젝트는 Model Context Protocol (MCP)을 사용하여 Chinook 데이터베이스를 분석하는 대화형 AI 에이전트입니다.

## 🚀 주요 기능

### 1. Chinook 데이터베이스 분석
- **SQL 쿼리 실행**: 복잡한 SQL 쿼리 실행 및 결과 반환
- **테이블 스키마 조회**: 특정 테이블의 구조 및 메타데이터 제공
- **테이블 목록**: 데이터베이스의 모든 테이블 정보 제공
- **쿼리 검증**: SQL 문법 검증 및 최적화 제안

### 2. 대화형 메모리
- **대화 히스토리**: 이전 대화 내용을 기억하고 컨텍스트 유지
- **연속 질문**: 이전 질문을 참조한 후속 질문 처리
- **세션 관리**: 사용자별 독립적인 대화 세션

### 3. LangChain 통합
- **ReAct 에이전트**: 추론과 행동을 결합한 에이전트 패턴
- **MCP 어댑터**: MCP 서버의 도구를 LangChain 도구로 변환
- **메모리 체크포인트**: 대화 상태 저장 및 복원

## 🛠️ 설정 방법

### 1. 환경 변수 설정

`.env` 파일에 다음 변수를 설정하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `mcp` - Model Context Protocol
- `langchain` - LangChain 프레임워크
- `langchain-mcp-adapters` - MCP-LangChain 어댑터
- `langgraph` - LangGraph 프레임워크
- `python-dotenv` - 환경 변수 관리

### 3. 데이터베이스 파일 확인

`Chinook.db` 파일이 프로젝트 루트에 있는지 확인하세요.

## 🎯 사용 방법

### 1. MCP 서버 실행

```bash
python agent_server.py
```

### 2. 클라이언트 실행

```bash
python agent_client.py
```

### 3. 사용 예시

```
=====대화형 Chinook 데이터베이스 분석 챗봇 시작 (메모리 포함)=====
종료하려면 'quit' 또는 'exit'를 입력하세요.
대화 히스토리가 기억됩니다!

질문을 입력하세요: 고객별 총 구매액을 조회해줘

=====PROCESSING WITH MEMORY=====
=====RESPONSE=====
[분석 결과 출력]

질문을 입력하세요: 가장 많이 구매한 고객 5명을 보여줘

=====PROCESSING WITH MEMORY=====
=====RESPONSE=====
[이전 결과를 참조한 분석 결과]
```

## 🔧 기술적 특징

### 1. MCP 아키텍처
- **agent_server.py**: Chinook DB 분석 MCP 서버
- **agent_client.py**: LangChain 기반 대화형 클라이언트
- **stdio 통신**: 표준 입출력을 통한 MCP 통신

### 2. LangChain 통합
- **MCP 어댑터**: MCP 도구를 LangChain 도구로 자동 변환
- **ReAct 에이전트**: 추론(Reasoning)과 행동(Action) 결합
- **메모리 관리**: MemorySaver를 통한 대화 상태 저장

### 3. 데이터베이스 연결
- **SQLite 연결**: Chinook.db 파일 직접 연결
- **LangChain SQLDatabase**: SQL 쿼리 실행 및 결과 처리
- **스키마 정보**: 테이블 구조 및 메타데이터 제공

## 📊 지원되는 분석 유형

### 1. SQL 쿼리 실행
```sql
SELECT CustomerId, SUM(Total) as TotalSpent 
FROM Invoice 
GROUP BY CustomerId 
ORDER BY TotalSpent DESC
```

### 2. 테이블 스키마 조회
- 컬럼 정보 및 데이터 타입
- 제약 조건 및 인덱스
- 외래키 관계

### 3. 데이터베이스 메타데이터
- 사용 가능한 테이블 목록
- 데이터베이스 정보
- 테이블별 상세 정보

### 4. 쿼리 검증
- SQL 문법 검증
- 실행 계획 분석
- 성능 최적화 제안

## 🎨 Chinook 데이터베이스 구조

Chinook은 디지털 미디어 스토어를 나타내는 샘플 데이터베이스입니다:

### 주요 테이블
- **Customer**: 고객 정보
- **Invoice**: 주문 정보
- **Track**: 음악 트랙 정보
- **Album**: 앨범 정보
- **Artist**: 아티스트 정보
- **Genre**: 장르 정보
- **Employee**: 직원 정보

### 관계 구조
```
Artist 1 ── N Album ── N Track
Customer 1 ── N Invoice ── N InvoiceLine ── N Track
Employee (자체 참조) - 각 Customer의 담당 직원
```

## 🔍 사용 가능한 도구

### 1. execute_sql_query(query: str)
- SQL 쿼리 실행 및 결과 반환
- SELECT, INSERT, UPDATE, DELETE 지원
- 오류 처리 및 결과 포맷팅

### 2. get_table_schema(table_name: str)
- 특정 테이블의 스키마 정보 제공
- 컬럼 정보, 데이터 타입, 제약 조건
- 외래키 관계 정보

### 3. list_tables()
- 데이터베이스의 모든 테이블 목록
- 사용 가능한 테이블 이름 반환

### 4. validate_sql_query(query: str)
- SQL 쿼리 문법 검증
- 실행 계획 분석
- 오류 메시지 제공

## 📁 리소스

### 1. database://info
- 데이터베이스 기본 정보
- 사용 가능한 테이블 목록
- 데이터베이스 설명

### 2. table://{table_name}
- 특정 테이블의 상세 정보
- 스키마 및 메타데이터
- 관계 정보

## 🚨 주의사항

1. **데이터베이스 파일**: `Chinook.db` 파일이 프로젝트 루트에 있어야 함
2. **API 키**: OpenAI API 키가 올바르게 설정되어야 함
3. **메모리 사용**: 대화 히스토리가 메모리에 저장됨
4. **SQL 보안**: 사용자 입력에 대한 SQL 인젝션 주의

## 🔍 문제 해결

### 데이터베이스 연결 실패
- `Chinook.db` 파일이 존재하는지 확인
- 파일 경로가 올바른지 확인
- 파일 권한 확인

### MCP 서버 연결 실패
- `agent_server.py`가 실행 중인지 확인
- 환경 변수가 올바르게 설정되었는지 확인
- 포트 충돌 확인

### 쿼리 실행 오류
- SQL 문법이 올바른지 확인
- 테이블 이름이 정확한지 확인
- 컬럼 이름이 존재하는지 확인

## 📈 확장 가능성

1. **추가 데이터베이스 지원**: PostgreSQL, MySQL 등
2. **웹 인터페이스**: Streamlit, FastAPI 등
3. **시각화**: 차트 및 그래프 생성
4. **스케줄링**: 정기적인 분석 자동화
5. **다중 사용자**: 사용자별 세션 관리

## 📁 파일 구조

```
LangGraph_MCP_Agent/
├── agent_client.py      # LangChain 기반 대화형 클라이언트
├── agent_server.py      # Chinook DB MCP 서버
├── Chinook.db          # 샘플 데이터베이스
├── README.md           # 이 문서
└── requirements.txt    # 의존성 패키지
```

## 🎯 사용 예시

### 기본 질문
```
질문을 입력하세요: 고객 수는 몇 명인가요?
질문을 입력하세요: 가장 인기 있는 장르는 무엇인가요?
질문을 입력하세요: 직원들의 매출 기여도를 분석해줘
```

### 복잡한 분석
```
질문을 입력하세요: 고객별 구매 패턴을 분석해줘
질문을 입력하세요: 월별 매출 트렌드를 보여줘
질문을 입력하세요: 아티스트별 인기도를 계산해줘
```

### 연속 질문
```
질문을 입력하세요: 고객별 총 구매액을 조회해줘
질문을 입력하세요: 그 중에서 상위 10명만 보여줘
질문을 입력하세요: 이 고객들의 구매 내역을 자세히 분석해줘
```

## 라이선스

MIT License
