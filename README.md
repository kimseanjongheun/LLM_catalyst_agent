# LLM Catalyst Agent

LLM 기반 촉매 설계 자동화 시스템으로, 대화형 AI 에이전트를 통해 최적의 촉매 조성을 탐색하고 발견하는 프로젝트입니다.

## 📋 프로젝트 개요

이 프로젝트는 LangGraph를 기반으로 한 멀티 에이전트 시스템으로, 사용자가 원하는 촉매 특성을 입력하면 AI가 자동으로 가설을 생성하고, 데이터베이스에서 후보군을 스크리닝하여 최적의 촉매를 찾아내는 과정을 자동화합니다.

## 🏗️ 시스템 아키텍처

### 핵심 컴포넌트

1. **Hypothesis Agent**: 사용자 요구사항을 분석하여 과학적 가설을 생성
2. **Executor Agent**: 가설을 바탕으로 조사할 촉매 후보군을 선정
3. **Simulation Node**: 선정된 후보군의 흡착 에너지를 계산
4. **Validation Node**: 결과를 분석하여 루프 계속 여부를 결정
5. **Summary Node**: 최종 결과를 요약하고 정리

### 워크플로우

```
START → Hypothesis Agent → Executor Agent → Simulation → Validation
  ↑                                                           ↓
  └─────────────────── Continue ←─────────────────────────────┘
                                                              ↓
                                                           Summary → END
```

## 🔄 상세 워크플로우

### 1. 초기 가설 생성 (Hypothesis Node)
- **입력**: 사용자 프롬프트, DB 정보, 시스템 프롬프트
- **처리**: 사용자가 찾고자 하는 촉매의 특징을 분석
- **출력**: 과학적이고 구체적인 가설 생성

### 2. 후보군 선정 (Executor Node)
- **입력**: 가설, 시뮬레이션 규칙, DB 정보
- **처리**: 가설에 부합하는 '조성-site' 조합을 포함한 쿼리 생성
- **출력**: 조사할 촉매 후보군 리스트

### 3. 시뮬레이션 수행 (Simulation Node)
- **입력**: 선정된 후보군
- **처리**: 각 후보에 대한 흡착 에너지 계산
- **출력**: 시뮬레이션 결과 (성공/실패, 에너지 값)

### 4. 결과 검증 (Validation Node)
- **입력**: 시뮬레이션 결과
- **처리**: 기준치 만족 여부 확인
- **출력**: 루프 계속 또는 종료 결정

### 5. 반복 및 최적화
- 기준치 미달 시: 이전 결과와 가설을 바탕으로 가설 수정 후 재실행
- 기준치 달성 시: 최종 결과 요약 및 종료

## 📁 프로젝트 구조

```
LLM_Catalyst_Agent/
├── main.py                          # 메인 실행 파일
├── node_models.py                   # 데이터 모델 및 상태 정의
├── hypothesis_node.py               # 가설 생성 노드
├── sub_agent_node.py                # 실행자 에이전트 노드
├── simulation_node.py               # 시뮬레이션 노드
├── validation_node.py               # 검증 노드
├── summary_node.py                  # 요약 노드
├── prompts/                         # 프롬프트 템플릿
│   ├── main_system_prompt.txt       # Hypothesis Agent 시스템 프롬프트
│   ├── sub_system_prompt.txt        # Executor Agent 시스템 프롬프트
│   ├── DB_info.txt                  # 데이터베이스 정보
│   ├── user_prompt.txt              # 사용자 프롬프트
│   ├── user 프롬프트 후보.txt        # 사용자 프롬프트 후보들
│   └── main_프롬프트_1.txt           # 메인 프롬프트 템플릿
├── data/                           # 데이터 파일들
│   └── MamunHighT2019/             # 촉매 데이터베이스
├── data_processing/                # 데이터 처리 스크립트들
├── results/                        # 실행 결과 저장
│   ├── main_gpt-4o_sub_gpt-4o/     # GPT-4o 모델 결과
│   ├── main_gpt-4o-mini_sub_gpt-4o-mini/  # GPT-4o-mini 모델 결과
│   ├── main_gpt-5_sub_gpt-5/       # GPT-5 모델 결과
│   ├── main_gpt-5-mini_sub_gpt-5-mini/    # GPT-5-mini 모델 결과
│   └── main_gpt-5-nano_sub_gpt-5-nano/    # GPT-5-nano 모델 결과
├── validation_results/             # 검증 결과 및 시각화
├── paper_writing/                  # 논문 작성 관련 파일들
├── requirements.txt                # 의존성 패키지
└── README.md                      # 프로젝트 문서
```

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 저장소 클론
git clone [repository-url]
cd LLM_Catalyst_Agent

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정
```bash
# key/.env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 실행
```bash
python main.py
```

## 🔧 주요 설정

### 모델 설정 (`node_models.py`)
```python
SUB_AGENT_MODEL_NAME = "gpt-4o-mini"
MAIN_AGENT_MODEL_NAME = "gpt-4o-mini"
EXPERIMENT_REPEAT = 6
```

### 데이터 모델
- **CatalystCandidate**: 이원금속 촉매 후보 정보
- **SubAgentQuery**: 서브 에이전트 쿼리 모델
- **SimulationResult**: DFT 시뮬레이션 결과
- **TokenUsage**: LLM 토큰 사용량 추적

### 제약 조건
- **조성 제약**: Metal1_Composition은 0.75 또는 0.5만 허용
- **사이트 제약**: top, bridge, hollow 중 하나만 허용
- **중복 방지**: 이전에 테스트된 후보는 재선택 금지

## 📊 성능 분석 및 시각화

`validation_results/` 폴더에서 다음과 같은 분석을 수행할 수 있습니다:

### 분석 기능
- **Step별 성공률 분석**: 각 단계별 성공한 후보 수 추적
- **흡착 에너지 분포**: 성공한 후보들의 에너지 분포 시각화
- **토큰 사용량 분석**: Main Agent와 Sub Agent의 토큰 사용량 추적
- **비용 분석**: 다양한 GPT 모델 사용 비용 계산
- **중복 후보 검증**: 동일한 후보가 여러 번 나타나는지 확인

### 생성되는 그래프
1. **Adsorption Energy Distribution**: Step별 박스플롯
2. **Candidate Count by Step**: Step별 후보 수 꺾은선 그래프
3. **Token Usage by Step**: Main/Sub Agent 토큰 사용량 히스토그램
4. **Cost by Step**: Step별 비용 분석 그래프

## 🔬 실험 구성

### 모델별 실험
- **GPT-4o**: 고성능 모델 (3회 반복)
- **GPT-4o-mini**: 표준 모델 (6회 반복)
- **GPT-5**: 최신 모델 (3회 반복)
- **GPT-5-mini**: 중간 성능 모델 (5회 반복)
- **GPT-5-nano**: 경량 모델 (4회 반복)

### 결과 저장 구조
```
results/
├── main_{MAIN_MODEL}_sub_{SUB_MODEL}/
│   ├── repeat_1/
│   ├── repeat_2/
│   └── ...
└── validation_results/
    ├── main_{MAIN_MODEL}_sub_{SUB_MODEL}/
    │   ├── avg_repeat/
    │   ├── repeat_1/
    │   └── ...
```

## 📈 결과 해석

### 성공률 분석
- **전체 성공률**: 모든 시뮬레이션 중 성공한 비율
- **Step별 성공률**: 각 단계별 성공률 변화 추적
- **중복 후보 성공률**: 중복된 후보들의 성공률 분석

### 비용 효율성
- **Step별 비용**: 각 단계별 AI 모델 사용 비용
- **총 비용**: 전체 프로젝트 비용
- **성공당 비용**: 성공한 후보 1개당 평균 비용

## 🧪 데이터 처리

### 데이터베이스 정보
- **MamunHighT2019**: 이원금속 촉매 데이터베이스
- **조성 제약**: 0.75:0.25 또는 0.5:0.5만 허용
- **사이트**: top, bridge, hollow

### 데이터 처리 스크립트
- `data_processing/`: 데이터 검사, 통합, 시각화 스크립트
- `data_processing_for_validation_result/`: 검증 결과 데이터 처리

## 📝 논문 작성

`paper_writing/` 폴더에는 논문 작성 관련 파일들이 포함되어 있습니다:
- `main_paper.tex`: 메인 논문 텍스트
- `figures/`: 논문용 그림들
- `llm_catalyst_workflow.docx`: 워크플로우 설명서

## 🤝 기여 방법

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성해 주세요.

---

**참고**: 이 프로젝트는 연구 목적으로 개발되었으며, 실제 촉매 설계에 적용하기 전에 추가적인 검증이 필요할 수 있습니다.
