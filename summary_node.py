from node_models import GraphState, TokenUsage, SubAgentQuery, CatalystCandidate, SimulationResult, DEFAULT_SAVE_PATH
import asyncio
import json
from validation_node import OPTIMAL_ENERGY
import os


async def summary_node(state: GraphState):
    print("=====summary_node=====")
    final_hypothesis_path = os.path.join(DEFAULT_SAVE_PATH, "final_hypothesis.txt")
    final_candidates_path = os.path.join(DEFAULT_SAVE_PATH, "final_candidates.txt")

    with open(final_hypothesis_path, "w", encoding="utf-8") as f:
        f.write(f"반복 수: {state.step_of_hypothesis}\n")
        f.write("==========================================\n")
        f.write(f"최종 가설: {state.hypothesis}\n")
        f.write("==========================================\n")
        f.write(f"최종 선정 후보군: {state.result_from_simulation}\n")

    import json
    # CatalystCandidate와 SimulationResult 객체를 JSON 직렬화할 수 있도록 변환 함수 정의
    def simulation_result_to_dict(result):
        return {
            "candidate": {
                "metal_1": result.candidate.metal_1,
                "metal_2": result.candidate.metal_2,
                "metal_1_composition": result.candidate.metal_1_composition,
                "metal_2_composition": result.candidate.metal_2_composition,
                "site": result.candidate.site,
            },
            "adsorption_energy_eV": result.adsorption_energy_eV,
            "is_success": result.is_success,
            "error_message": result.error_message,
        }

    results_json = [simulation_result_to_dict(r) for r in state.result_from_simulation]
    with open(final_candidates_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)

    print(f"[결과 정리]")
    print(f"최종 반복 수: {state.step_of_hypothesis}")

    exist_candidates = 0
    non_exist_candidates = 0
    for i, result in enumerate(state.result_from_simulation):
        if result.is_success:
            print(f"[후보 {i+1}] {result.candidate.metal_1}-{result.candidate.metal_2} ({result.candidate.metal_1_composition:.2f}:{result.candidate.metal_2_composition:.2f}) - {result.candidate.site}: {result.adsorption_energy_eV:.4f} eV")
            exist_candidates += 1
        else:
            non_exist_candidates += 1

    print(f"존재한 후보 개수: {exist_candidates}개")
    print(f"존재하지 않은 후보 개수: {non_exist_candidates}개")
    successful_results = [result for result in state.result_from_simulation if result.is_success]
    # 최적 촉매 후보 선정
    best_catalysts = successful_results[0]
    for result in successful_results:
        if abs(result.adsorption_energy_eV - OPTIMAL_ENERGY) < abs(best_catalysts.adsorption_energy_eV - OPTIMAL_ENERGY):
            best_catalysts = result
    print(f"최고의 촉매: {best_catalysts.candidate.metal_1}-{best_catalysts.candidate.metal_2}-{best_catalysts.candidate.metal_1_composition:.2f}-{best_catalysts.candidate.metal_2_composition:.2f}-{best_catalysts.candidate.site}: {best_catalysts.adsorption_energy_eV:.4f} eV")

    print(f"가설 결과 파일 경로: {final_hypothesis_path}")
    print(f"후보군 결과 파일 경로: {final_candidates_path}")

    return state


if __name__ == "__main__":
    async def test_summary_node():
        state = GraphState()
        result = await summary_node(state)
    
    asyncio.run(test_summary_node())
