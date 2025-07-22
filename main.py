"""
LLM Catalyst Agent Main Pipeline - Simplified
핵심 기능:
1. Context 로딩
2. Prompt 생성  
3. LLM 추론 (MCP DFT tools 사용)
4. 결과 저장
5. MCP tool 사용 추적
"""

import json
import pandas as pd

def main():
    print("=== LLM Catalyst Agent 시작 ===")
    
    # 1. Context 로딩
    with open("context/sample_context.json", "r", encoding="utf-8") as f:
        context = json.load(f)
    print("[1] Context 로딩 완료")
    
    # 2. Search group 준비 (후보 조성들)
    df = pd.read_csv("data/hydrogen/system_compositions_fraction.csv")
    search_group_data = df['composition_fraction'][:50].tolist()  # 50개만 사용
    search_group = {
        "count": len(search_group_data),
        "compositions": search_group_data,
        "description": f"총 {len(search_group_data)}개의 후보 조성"
    }
    print(f"[2] Search group 준비 완료: {search_group['count']}개 조성")
    
    # 3. Prompt 생성
    from agent.prompt_manager import PromptManager
    prompt_manager = PromptManager()
    prompt = prompt_manager.build_prompt(context, search_group)
    print("[3] Prompt 생성 완료")
    
    # 4. LLM 추론 (MCP tools 사용)
    from agent.llm_agent import LLMAgent
    llm_agent = LLMAgent(use_mcp_tools=True)
    llm_output = llm_agent.ask(prompt)
    print("[4] LLM 추론 완료 (MCP tools 사용)")
    print("LLM 응답:", llm_output)
    
    # 5. MCP Tool 사용 추적 및 보고
    tool_summary = llm_agent.get_tool_usage_summary()
    print(f"\n[5] MCP Tool 사용 통계:")
    print(f"  - 총 tool 호출 수: {tool_summary['total_calls']}")
    if tool_summary['total_calls'] > 0:
        print(f"  - 성공한 호출: {tool_summary['successful_calls']}")
        print(f"  - 실패한 호출: {tool_summary['failed_calls']}")
    if tool_summary['functions_used']:
        print(f"  - 사용된 함수들:")
        for func, count in tool_summary['functions_used'].items():
            print(f"    * {func}: {count}회")
    else:
        print("  - 사용된 MCP tools 없음 ⚠️")
    
    # Tool usage log 저장
    llm_agent.save_tool_usage_log()
    
    # 6. 조성 추출 (backup method)
    composition_dict = llm_agent.parse_composition(llm_output)
    print(f"[6] 추출된 조성: {composition_dict}")
    
    # 7. 결과 저장
    result = {
        "prompt": prompt,
        "llm_output": llm_output,
        "extracted_composition": composition_dict,
        "mcp_tool_usage": tool_summary,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open("results/latest_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("[7] 결과 저장 완료: results/latest_result.json")
    
    # 8. MCP Tools 효과성 분석
    print(f"\n[8] MCP Tools 효과성 분석:")
    if tool_summary['total_calls'] > 0:
        print("✅ MCP tools가 정상적으로 활용됨")
    else:
        print("⚠️  MCP tools가 사용되지 않음")
        print("   - LLM이 tools를 호출하지 않았거나")
        print("   - Tools 설정에 문제가 있을 수 있음")
    
    print("=== 완료 ===")

if __name__ == "__main__":
    main() 
