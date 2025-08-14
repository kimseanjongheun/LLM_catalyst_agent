
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import asyncio
import pandas as pd
import instructor
from langgraph.graph import START, END

# 반복 실험을 위한 전역변수
EXPERIMENT_REPEAT = 6
SUB_AGENT_MODEL_NAME = "gpt-4o-mini"
MAIN_AGENT_MODEL_NAME = "gpt-4o-mini"

DEFAULT_SAVE_PATH = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\results\main_{MAIN_AGENT_MODEL_NAME}_sub_{SUB_AGENT_MODEL_NAME}\repeat_{EXPERIMENT_REPEAT}"



class CatalystCandidate(BaseModel):
    """
    이원금속 촉매 후보 정보를 담는 데이터 모델
    
    Attributes:
        metal_1 (str): 이원금속 촉매의 첫 번째 금속 (예: 'Pt', 'Ru', 'Ni' 등)
        metal_2 (str): 이원금속 촉매의 두 번째 금속 (예: 'Cu', 'Fe', 'Co' 등)
        metal_1_composition (float): metal_1의 조성 분율 (0.0 ~ 1.0, 주로 0.5 또는 0.75)
        metal_2_composition (float): metal_2의 조성 분율 (0.0 ~ 1.0, 주로 0.5 또는 0.25)
        site (str): 흡착 사이트 ('top', 'bridge', 'hollow' 중 하나)
    
    Note:
        - metal_1_composition + metal_2_composition = 1.0이어야 함
        - 조성은 데이터베이스 제약으로 인해 0.5:0.5 또는 0.75:0.25만 허용됨
    """
    metal_1: str = Field(description="The first metal of the bimetallic catalyst")
    metal_2: str = Field(description="The second metal of the bimetallic catalyst")
    metal_1_composition: float = Field(description="The composition fraction of metal_1 (0.0 to 1.0)")
    metal_2_composition: float = Field(description="The composition fraction of metal_2 (0.0 to 1.0)")
    site: str = Field(description="The adsorption site: top, bridge, or hollow")



class SubAgentQuery(BaseModel):
    """
    서브 에이전트가 시뮬레이션 시스템에 전달하는 쿼리 모델
    
    Attributes:
        candidates (list[CatalystCandidate]): 시뮬레이션할 촉매 후보들의 리스트
    
    Note:
        메인 에이전트가 생성한 가설을 바탕으로 서브 에이전트가 선택한 후보들을
        DFT 시뮬레이션 시스템에 전달하기 위한 중간 데이터 구조
    """
    candidates: list[CatalystCandidate] = Field(description="List of catalyst candidates to test")



class SimulationResult(BaseModel):
    """
    DFT 시뮬레이션 결과를 담는 데이터 모델
    
    Attributes:
        candidate (CatalystCandidate): 시뮬레이션된 촉매 후보 정보
        adsorption_energy_eV (float): 흡착 에너지 (전자볼트 단위)
        is_success (bool): 시뮬레이션 성공 여부
        error_message (str): 시뮬레이션 실패 시 에러 메시지 (기본값: 빈 문자열)
    
    Note:
        - adsorption_energy_eV는 시뮬레이션 성공 시에만 유효한 값
        - is_success가 False인 경우 error_message에 실패 원인이 기록됨
        - 최적 HER 성능은 흡착 에너지가 0에 가까울 때 달성됨
    """
    candidate: CatalystCandidate = Field(description="The catalyst candidate")
    adsorption_energy_eV: float = Field(description="The adsorption energy in eV")
    is_success: bool = Field(description="Whether the simulation was successful")
    error_message: str = Field(default="", description="Error message if simulation failed")



class TokenUsage(BaseModel):
    """
    LLM 모델의 토큰 사용량을 추적하는 데이터 모델
    
    Attributes:
        input_tokens (int): 입력 토큰 수 (프롬프트에 사용된 토큰)
        output_tokens (int): 출력 토큰 수 (응답에 사용된 토큰)
        total_tokens (int): 총 토큰 수 (input_tokens + output_tokens)
    
    Note:
        - OpenAI API 비용 계산에 사용됨
        - 메인 에이전트와 서브 에이전트의 토큰 사용량을 각각 추적
        - 각 스텝별로 토큰 사용량이 기록되어 비용 분석에 활용됨
    """
    input_tokens: int = Field(description="The number of input tokens")
    output_tokens: int = Field(description="The number of output tokens")
    total_tokens: int = Field(description="The total number of tokens")


class GraphState(BaseModel):
    """
    LangGraph 워크플로우의 전체 상태를 관리하는 데이터 모델
    
    이 클래스는 촉매 발견 워크플로우의 모든 단계에서 필요한 정보를 담고 있으며,
    각 노드 간에 데이터를 전달하는 중앙 집중식 상태 관리 역할을 합니다.
    
    Attributes:
        user_prompt (str): 메인 에이전트를 위한 사용자 프롬프트
        main_system_prompt (str): 메인 에이전트의 시스템 프롬프트
        sub_system_prompt (str): 서브 에이전트의 시스템 프롬프트
        db_info (str): 촉매 데이터베이스 정보
        hypothesis (str): 메인 에이전트가 생성한 가설
        step_of_hypothesis (int): 현재 가설 검증 단계 (1부터 시작)
        query_to_simulation (SubAgentQuery): 시뮬레이션에 전달할 쿼리
        result_from_simulation (list): 시뮬레이션 결과 리스트 (SimulationResult 객체들)
        should_stop (bool): 워크플로우 종료 여부 결정 플래그
        main_agent_token_usage (list): 메인 에이전트의 토큰 사용량 기록 (TokenUsage 객체들)
        sub_agent_token_usage (list): 서브 에이전트의 토큰 사용량 기록 (TokenUsage 객체들)
    
    Note:
        - 각 스텝마다 새로운 GraphState 인스턴스가 생성되거나 업데이트됨
        - result_from_simulation은 누적되어 전체 시뮬레이션 히스토리를 유지
        - should_stop이 True가 되면 워크플로우가 종료됨
        - 토큰 사용량은 각 스텝별로 기록되어 비용 분석에 활용됨
    """
    user_prompt: str = Field(default="", description="The user prompt for the main agent")
    main_system_prompt: str = Field(default="", description="The system prompt for the main agent")
    sub_system_prompt: str = Field(default="", description="The system prompt for the sub agent")
    db_info: str = Field(default="", description="The information about the database")
    hypothesis: str = Field(default="", description="The hypothesis for the main agent")
    step_of_hypothesis: int = Field(default=0, description="The step of the hypothesis")
    query_to_simulation: SubAgentQuery = Field(default=SubAgentQuery(candidates=[]), description="The query to the simulation")
    result_from_simulation: list = Field(default=[], description="The result of the simulation")
    should_stop: bool = Field(default=False, description="Whether to stop the graph")
    main_agent_token_usage: list = Field(default=[], description="The token usage of the main agent")
    sub_agent_token_usage: list = Field(default=[], description="The token usage of the sub agent")



# 환경 변수에서 OpenAI API 키 로드
load_dotenv("key/.env")
api_key = os.getenv("OPENAI_API_KEY")

# GPT-4o-mini 모델 인스턴스 생성
# 이 모델은 메인 에이전트와 서브 에이전트 모두에서 사용됨
model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)



def should_summary_condition(state: GraphState):
    """
    LangGraph 워크플로우의 조건부 엣지 함수
    
    Args:
        state (GraphState): 현재 워크플로우 상태
    
    Returns:
        str: 다음 노드 결정
            - "summary": 워크플로우 종료 (should_stop이 True인 경우)
            - "continue": 다음 반복 진행 (should_stop이 False인 경우)
    
    Note:
        이 함수는 validation_node에서 설정된 should_stop 플래그에 따라
        워크플로우를 계속 진행할지 종료할지를 결정합니다.
    """
    if state.should_stop:
        return "summary"
    else:
        return "continue"


if __name__ == "__main__":
    """
    모듈 테스트를 위한 메인 함수
    
    GraphState 인스턴스 생성 및 should_summary_condition 함수 테스트
    """
    state = GraphState()
    result = should_summary_condition(state)
    print(f"Initial state should_stop: {state.should_stop}")
    print(f"Edge condition result: {result}")