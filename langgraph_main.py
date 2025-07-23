"""
Langgraph 기반 LLM Catalyst Agent Main Pipeline
기존 main.py를 Langgraph 프레임워크로 재구성
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agent.langgraph_nodes import (
    AgentState,
    load_context_node,
    prepare_search_group_node,
    generate_prompt_node,
    llm_inference_node,
    extract_compositions_node,  # 복수형으로 변경
    extract_analysis_node,
    save_results_node,
    analyze_effectiveness_node,
    validate_results_node,
    error_handler_node
)


def should_continue_after_context(state: AgentState) -> str:
    """Context 로딩 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_search_group(state: AgentState) -> str:
    """Search group 준비 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_prompt(state: AgentState) -> str:
    """Prompt 생성 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_llm(state: AgentState) -> str:
    """LLM 추론 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_extraction(state: AgentState) -> str:
    """다중 조성 추출 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_analysis_extraction(state: AgentState) -> str:
    """분석 추출 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_analysis(state: AgentState) -> str:
    """효과성 분석 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def should_continue_after_validation(state: AgentState) -> str:
    """결과 검증 후 다음 단계 결정"""
    if "error" in state and state["error"]:
        return "error_handler"
    return "continue"


def create_agent_graph():
    """LLM Catalyst Agent 그래프 생성"""
    
    # StateGraph 초기화
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("prepare_search_group", prepare_search_group_node)
    workflow.add_node("generate_prompt", generate_prompt_node)
    workflow.add_node("llm_inference", llm_inference_node)
    workflow.add_node("extract_compositions", extract_compositions_node)  # 복수형
    workflow.add_node("extract_analysis", extract_analysis_node)
    workflow.add_node("analyze_effectiveness", analyze_effectiveness_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("save_results", save_results_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # 시작점 설정
    workflow.set_entry_point("load_context")
    
    # 순차적 실행 경로 정의
    workflow.add_conditional_edges(
        "load_context",
        should_continue_after_context,
        {
            "continue": "prepare_search_group",
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "prepare_search_group", 
        should_continue_after_search_group,
        {
            "continue": "generate_prompt",
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_prompt",
        should_continue_after_prompt,
        {
            "continue": "llm_inference", 
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "llm_inference",
        should_continue_after_llm,
        {
            "continue": "extract_compositions",  # 복수형
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "extract_compositions",  # 복수형
        should_continue_after_extraction,
        {
            "continue": "extract_analysis",
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "extract_analysis",
        should_continue_after_analysis_extraction,
        {
            "continue": "analyze_effectiveness",
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_effectiveness",
        should_continue_after_analysis,
        {
            "continue": "validate_results",
            "error_handler": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "validate_results",
        should_continue_after_validation,
        {
            "continue": "save_results",
            "error_handler": "error_handler"
        }
    )
    
    # 결과 저장 후 종료
    workflow.add_edge("save_results", END)
    
    # 오류 처리 경로
    workflow.add_edge("error_handler", END)
    
    # 메모리 저장기 설정 (선택사항)
    memory = MemorySaver()
    
    # 그래프 컴파일
    app = workflow.compile(checkpointer=memory)
    
    return app


def main():
    """Langgraph 기반 메인 실행 함수"""
    print("=== Langgraph 기반 LLM Catalyst Agent 시작 ===")
    print("🔧 OutputParser 시스템 적용됨")
    print("🚀 다중 조성 추천 모드 활성화")
    
    try:
        # 그래프 생성
        app = create_agent_graph()
        
        # 초기 상태 설정
        initial_state = {
            "context": {},
            "search_group": {},
            "prompt": "",
            "llm_output": "",
            "extracted_compositions": [],  # 복수형 리스트
            "extracted_analysis": {},
            "tool_summary": {},
            "result": {},
            "timestamp": "",
            "error": ""
        }
        
        # 그래프 실행
        config = {"configurable": {"thread_id": "catalyst_agent_1"}}
        
        print("\n🚀 그래프 실행 시작...")
        final_state = app.invoke(initial_state, config=config)
        
        print("\n=== 최종 실행 결과 ===")
        if "error" in final_state and final_state["error"]:
            print(f"❌ 실행 중 오류 발생: {final_state['error']}")
        else:
            print("✅ 모든 노드가 성공적으로 실행되었습니다!")
            print(f"📁 결과 파일: results/latest_result.json")
            
            # OutputParser 결과 요약
            compositions = final_state.get("extracted_compositions", [])
            analysis = final_state.get("extracted_analysis", {})
            
            print(f"\n📊 다중 조성 OutputParser 결과:")
            print(f"  🧪 추출된 조성 개수: {len(compositions)}")
            print(f"  📝 분석 추출: {'✅' if analysis.get('analysis') else '❌'}")
            print(f"  💡 추천 추출: {'✅' if analysis.get('recommendations') else '❌'}")
            
            if compositions:
                print(f"\n  🔬 추출된 조성들:")
                for i, comp in enumerate(compositions, 1):
                    print(f"    {i}. {comp}")
            
            if "tool_summary" in final_state:
                print(f"  🔧 MCP Tools 사용 횟수: {final_state['tool_summary'].get('total_calls', 0)}")
        
        print("\n=== Langgraph 기반 다중 조성 추천 완료 ===")
        
        return final_state
        
    except Exception as e:
        print(f"❌ Langgraph 실행 중 오류: {str(e)}")
        return None


def visualize_graph():
    """그래프 구조를 시각화 (선택사항)"""
    try:
        app = create_agent_graph()
        
        # 그래프 구조를 mermaid 형식으로 출력
        print("\n=== 그래프 구조 (Mermaid) ===")
        print("```mermaid")
        print("graph TD")
        print("    START --> load_context[Context 로딩]")
        print("    load_context --> prepare_search_group[Search Group 준비]")
        print("    prepare_search_group --> generate_prompt[Prompt 생성]")
        print("    generate_prompt --> llm_inference[LLM 추론]")
        print("    llm_inference --> extract_compositions[다중 조성 추출]")
        print("    extract_compositions --> extract_analysis[분석 추출]")
        print("    extract_analysis --> analyze_effectiveness[효과성 분석]")
        print("    analyze_effectiveness --> validate_results[결과 검증]")
        print("    validate_results --> save_results[결과 저장]")
        print("    save_results --> END")
        print("    load_context -.-> error_handler[오류 처리]")
        print("    prepare_search_group -.-> error_handler")
        print("    generate_prompt -.-> error_handler")
        print("    llm_inference -.-> error_handler")
        print("    extract_compositions -.-> error_handler")
        print("    extract_analysis -.-> error_handler")
        print("    analyze_effectiveness -.-> error_handler")
        print("    validate_results -.-> error_handler")
        print("    error_handler --> END")
        print("```")
        
    except Exception as e:
        print(f"그래프 시각화 오류: {str(e)}")


if __name__ == "__main__":
    # 그래프 구조 시각화 (선택사항)
    # visualize_graph()
    
    # 메인 실행
    main()