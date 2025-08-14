from langgraph.graph import StateGraph, START, END
import asyncio
import os
import time
import shutil

# 직접 선언한 라이브러리    
import hypothesis_node
import sub_agent_node
import simulation_node
import validation_node
import summary_node
import node_models


async def generate_workflow():
    print("LangGraph Workflow 생성 시작...")
    workflow = StateGraph(node_models.GraphState)

    # 그래프 노드 추가
    workflow.add_node("hypothesis agent", hypothesis_node.hypothesis_node)
    workflow.add_node("excutor agent", sub_agent_node.sub_agent_node)
    workflow.add_node("simulation", simulation_node.simulation_node)
    workflow.add_node("validation", validation_node.validation_node_v3) # 검증 노드 버전 3번 
    workflow.add_node("summary", summary_node.summary_node)
    
    # 그래프 연결
    workflow.add_edge(START, "hypothesis agent")
    workflow.add_edge("hypothesis agent", "excutor agent")
    workflow.add_edge("excutor agent", "simulation")
    workflow.add_edge("simulation", "validation")
    
    workflow.add_conditional_edges(
        "validation",
        node_models.should_summary_condition,
        {
            "continue": "hypothesis agent",
            "summary": "summary"
        }
    )

    workflow.add_edge("summary", END)

    return workflow

async def run_workflow():
    workflow = await generate_workflow()
    app = workflow.compile()
    
    # 초기 상태 설정
    initial_state = node_models.GraphState()
    
    # 워크플로우 실행
    print("LangGraph Agent 가동 시작...")
    start_time = time.time()
    result = await app.ainvoke(initial_state, {"recursion_limit": 75})
    end_time = time.time()
    
    # 실행 시간 계산 및 출력
    execution_time = end_time - start_time
    print(f"총 실행 시간: {execution_time:.2f}초 ({execution_time/60:.2f}분)")
    time_usage_save_path = os.path.join(node_models.DEFAULT_SAVE_PATH, "time_usage.txt")
    with open(time_usage_save_path, "w", encoding="utf-8") as f:
        f.write(f"{execution_time:.2f} s")
    print(f"시간 사용량 저장 파일 경로: {time_usage_save_path}")
    
    return result


async def visualize_graph():
    workflow = await generate_workflow()
    app = workflow.compile()

    print("LangGraph Workflow 시각화 시작...")
    png_bytes = app.get_graph().draw_mermaid_png()
    png_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\validation_results\graph_ver3_1.png"
    with open(png_path, "wb") as f:
        f.write(png_bytes)
    print(f"{png_path} 저장 완료")

    print("=====Mermaid 코드 출력=====")
    mermaid_code = app.get_graph().draw_mermaid()
    print(mermaid_code)
    


if __name__ == "__main__":
    # 워크플로우 실행
    # 결과 폴더 초기화
    print("결과 폴더 초기화 시작...")
    result_folder_path = node_models.DEFAULT_SAVE_PATH
    # 폴더가 있으면 삭제
    if os.path.exists(result_folder_path):
        shutil.rmtree(result_folder_path)
    os.makedirs(result_folder_path, exist_ok=True)

    asyncio.run(run_workflow()) # 사용 시 활성화
    
    # 그래프 시각화 (동기 방식 사용)
    # asyncio.run(visualize_graph()) # 사용 시 활성화


