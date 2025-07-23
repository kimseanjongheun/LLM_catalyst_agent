"""
Langgraph 기반 노드 정의
각 노드는 LLM Catalyst Agent의 특정 기능을 수행합니다.
"""

import json
import pandas as pd
from typing import TypedDict, Dict, Any, List
from pathlib import Path

from agent.prompt_manager import PromptManager
from agent.llm_agent import LLMAgent
from agent.output_parsers import (
    create_composition_parser, 
    create_multiple_composition_parser,
    create_analysis_parser
)


class AgentState(TypedDict):
    """에이전트 상태 정의 - 노드 간 데이터 전달용"""
    context: Dict[str, Any]
    search_group: Dict[str, Any]
    prompt: str
    llm_output: str
    extracted_compositions: List[Dict[str, Any]]  # 여러 조성을 위해 복수형으로 변경
    extracted_analysis: Dict[str, Any]
    tool_summary: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: str
    error: str


def load_context_node(state: AgentState) -> AgentState:
    """Context 파일을 로딩하는 노드"""
    try:
        print("[노드 1] Context 로딩 시작...")
        
        with open("context/sample_context.json", "r", encoding="utf-8") as f:
            context = json.load(f)
        
        state["context"] = context
        print("[노드 1] Context 로딩 완료")
        
    except Exception as e:
        state["error"] = f"Context 로딩 실패: {str(e)}"
        print(f"[노드 1] 오류: {state['error']}")
    
    return state


def prepare_search_group_node(state: AgentState) -> AgentState:
    """Search group 데이터를 준비하는 노드"""
    try:
        print("[노드 2] Search group 준비 시작...")
        
        df = pd.read_csv("data/hydrogen/system_compositions_fraction.csv")
        search_group_data = df['composition_fraction'][:50].tolist()  # 50개만 사용
        
        search_group = {
            "count": len(search_group_data),
            "compositions": search_group_data,
            "description": f"총 {len(search_group_data)}개의 후보 조성"
        }
        
        state["search_group"] = search_group
        print(f"[노드 2] Search group 준비 완료: {search_group['count']}개 조성")
        
    except Exception as e:
        state["error"] = f"Search group 준비 실패: {str(e)}"
        print(f"[노드 2] 오류: {state['error']}")
    
    return state


def generate_prompt_node(state: AgentState) -> AgentState:
    """Prompt를 생성하는 노드"""
    try:
        print("[노드 3] Prompt 생성 시작...")
        
        prompt_manager = PromptManager()
        prompt = prompt_manager.build_prompt(state["context"], state["search_group"])
        
        state["prompt"] = prompt
        print("[노드 3] Prompt 생성 완료 (다중 조성 추천 모드)")
        
    except Exception as e:
        state["error"] = f"Prompt 생성 실패: {str(e)}"
        print(f"[노드 3] 오류: {state['error']}")
    
    return state


def llm_inference_node(state: AgentState) -> AgentState:
    """LLM 추론을 수행하는 노드 (MCP tools 사용)"""
    try:
        print("[노드 4] LLM 추론 시작... (다중 조성 추천)")
        
        llm_agent = LLMAgent(use_mcp_tools=True)
        llm_output = llm_agent.ask(state["prompt"])
        
        # Tool 사용 통계 수집
        tool_summary = llm_agent.get_tool_usage_summary()
        
        state["llm_output"] = llm_output
        state["tool_summary"] = tool_summary
        
        # Tool usage log 저장
        llm_agent.save_tool_usage_log()
        
        print("[노드 4] LLM 추론 완료 (MCP tools 사용)")
        print("LLM 응답:", llm_output)
        
    except Exception as e:
        state["error"] = f"LLM 추론 실패: {str(e)}"
        print(f"[노드 4] 오류: {state['error']}")
    
    return state


def extract_compositions_node(state: AgentState) -> AgentState:
    """여러 조성을 추출하는 노드 (MultipleCompositionOutputParser 사용)"""
    try:
        print("[노드 5] 다중 조성 추출 시작...")
        
        # MultipleCompositionOutputParser를 사용
        composition_parser = create_multiple_composition_parser(validation=True)
        compositions_list = composition_parser.parse(state["llm_output"])
        
        state["extracted_compositions"] = compositions_list
        
        print(f"[노드 5] 추출된 조성 개수: {len(compositions_list)}")
        for i, comp in enumerate(compositions_list, 1):
            print(f"  조성 {i}: {comp}")
        
        if not compositions_list:
            print("[노드 5] ⚠️ 조성 추출 실패 - 출력 형식을 확인하세요")
            # 백업: 단일 조성 파서로 시도
            print("[노드 5] 백업: 단일 조성 파서로 재시도...")
            single_parser = create_composition_parser(validation=True)
            single_comp = single_parser.parse(state["llm_output"])
            if single_comp:
                state["extracted_compositions"] = [single_comp]
                print(f"[노드 5] 백업 성공: {single_comp}")
        
    except Exception as e:
        state["error"] = f"조성 추출 실패: {str(e)}"
        print(f"[노드 5] 오류: {state['error']}")
    
    return state


def extract_analysis_node(state: AgentState) -> AgentState:
    """구조화된 분석 결과를 추출하는 노드 (EnhancedAnalysisOutputParser 사용)"""
    try:
        print("[노드 5.5] 다중 조성 분석 결과 추출 시작...")
        
        # EnhancedAnalysisOutputParser를 사용하여 전체 구조화된 출력 파싱
        analysis_parser = create_analysis_parser()
        analysis_result = analysis_parser.parse(state["llm_output"])
        
        state["extracted_analysis"] = analysis_result
        
        print(f"[노드 5.5] 추출된 분석:")
        print(f"  - Analysis: {'✓' if analysis_result.get('analysis') else '✗'}")
        print(f"  - Recommendations: {'✓' if analysis_result.get('recommendations') else '✗'}")
        print(f"  - Compositions: {len(analysis_result.get('compositions', []))}개")
        
        # 분석 파서에서 추출된 조성과 전용 파서 결과 비교
        analysis_compositions = analysis_result.get('compositions', [])
        state_compositions = state.get('extracted_compositions', [])
        
        if analysis_compositions and not state_compositions:
            print("[노드 5.5] 분석 파서에서 조성 발견 - 상태 업데이트")
            state["extracted_compositions"] = analysis_compositions
        
    except Exception as e:
        state["error"] = f"분석 결과 추출 실패: {str(e)}"
        print(f"[노드 5.5] 오류: {state['error']}")
    
    return state


def save_results_node(state: AgentState) -> AgentState:
    """결과를 저장하는 노드"""
    try:
        print("[노드 6] 결과 저장 시작...")
        
        state["timestamp"] = pd.Timestamp.now().isoformat()
        
        result = {
            "prompt": state["prompt"],
            "llm_output": state["llm_output"],
            "extracted_compositions": state["extracted_compositions"],  # 복수형
            "extracted_analysis": state.get("extracted_analysis", {}),
            "mcp_tool_usage": state["tool_summary"],
            "timestamp": state["timestamp"],
            "composition_count": len(state.get("extracted_compositions", []))  # 추가 정보
        }
        
        # results 디렉토리 생성
        Path("results").mkdir(exist_ok=True)
        
        with open("results/latest_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        state["result"] = result
        print("[노드 6] 결과 저장 완료: results/latest_result.json")
        print(f"[노드 6] 저장된 조성 개수: {result['composition_count']}")
        
    except Exception as e:
        state["error"] = f"결과 저장 실패: {str(e)}"
        print(f"[노드 6] 오류: {state['error']}")
    
    return state


def analyze_effectiveness_node(state: AgentState) -> AgentState:
    """MCP Tools 효과성을 분석하는 노드"""
    try:
        print("[노드 7] MCP Tools 효과성 분석 시작...")
        
        tool_summary = state["tool_summary"]
        
        print(f"\n[7] MCP Tool 사용 통계:")
        print(f"  - 총 tool 호출 수: {tool_summary['total_calls']}")
        
        if tool_summary['total_calls'] > 0:
            print(f"  - 성공한 호출: {tool_summary['successful_calls']}")
            print(f"  - 실패한 호출: {tool_summary['failed_calls']}")
            
            if tool_summary['functions_used']:
                print(f"  - 사용된 함수들:")
                for func, count in tool_summary['functions_used'].items():
                    print(f"    * {func}: {count}회")
            
            print("✅ MCP tools가 정상적으로 활용됨")
        else:
            print("  - 사용된 MCP tools 없음 ⚠️")
            print("⚠️  MCP tools가 사용되지 않음")
            print("   - LLM이 tools를 호출하지 않았거나")
            print("   - Tools 설정에 문제가 있을 수 있음")
        
        print("[노드 7] MCP Tools 효과성 분석 완료")
        
    except Exception as e:
        state["error"] = f"효과성 분석 실패: {str(e)}"
        print(f"[노드 7] 오류: {state['error']}")
    
    return state


def validate_results_node(state: AgentState) -> AgentState:
    """결과 검증 노드"""
    try:
        print("[노드 8] 결과 검증 시작...")
        
        compositions = state.get("extracted_compositions", [])
        analysis = state.get("extracted_analysis", {})
        
        validation_summary = {
            "compositions_extracted": len(compositions),
            "analysis_extracted": analysis.get("analysis") is not None,
            "recommendations_extracted": analysis.get("recommendations") is not None,
            "tools_used": state.get("tool_summary", {}).get("total_calls", 0) > 0,
            "multiple_compositions": len(compositions) > 1
        }
        
        print(f"[노드 8] 검증 결과:")
        print(f"  - 추출된 조성 개수: {validation_summary['compositions_extracted']}")
        print(f"  - 분석 섹션: {'✅' if validation_summary['analysis_extracted'] else '❌'}")
        print(f"  - 추천 섹션: {'✅' if validation_summary['recommendations_extracted'] else '❌'}")
        print(f"  - MCP Tools 사용: {'✅' if validation_summary['tools_used'] else '❌'}")
        print(f"  - 다중 조성 추천: {'✅' if validation_summary['multiple_compositions'] else '❌'}")
        
        # 검증 결과를 상태에 추가
        if "result" not in state:
            state["result"] = {}
        state["result"]["validation"] = validation_summary
        
        print("[노드 8] 결과 검증 완료")
        
    except Exception as e:
        state["error"] = f"결과 검증 실패: {str(e)}"
        print(f"[노드 8] 오류: {state['error']}")
    
    return state


def error_handler_node(state: AgentState) -> AgentState:
    """오류 처리 노드"""
    if "error" in state and state["error"]:
        print(f"❌ 오류 발생: {state['error']}")
        # 오류 로그 저장
        error_log = {
            "error": state["error"],
            "timestamp": pd.Timestamp.now().isoformat(),
            "state_summary": {
                "has_context": "context" in state,
                "has_search_group": "search_group" in state,
                "has_prompt": "prompt" in state,
                "has_llm_output": "llm_output" in state
            }
        }
        
        Path("results").mkdir(exist_ok=True)
        with open("results/error_log.json", "w", encoding="utf-8") as f:
            json.dump(error_log, f, ensure_ascii=False, indent=2)
        
        print("오류 로그가 results/error_log.json에 저장되었습니다.")
    
    return state


# 호환성을 위한 별칭
extract_composition_node = extract_compositions_node 