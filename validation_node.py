import asyncio
import pandas as pd
import os
from node_models import GraphState, TokenUsage, SubAgentQuery, CatalystCandidate, SimulationResult, DEFAULT_SAVE_PATH


# 검증 기준; validation metric 설정(다른 파일에서 사용하기 위해 전역 변수로 선언)
OPTIMAL_ENERGY_THRESHOLD = 0.1  # eV
OPTIMAL_ENERGY = -0.27  # eV
# 2번 검증 기준
RECENT_CANDIDATES_COUNT = 10  # 가장 최근에 예측할 후보 개수
MIN_SUCCESS_COUNT = 6  # 최소 성공해야 할 후보 개수
# 1번 검증 기준
REQUIRED_CANDIDATES_COUNT = 10 # 찾을 후보 개수
# 3번 검증 기준
REQUIRED_ITERATION_COUNT = 10 # 최소 반복 횟수


# GraphState의 result_from_simulation list에 중복 SimulationResult가 있는 지 확인하는 함수
def remove_duplicate_simulation_results(state: GraphState):
    # 중복 후보를 제거한 list 생성하기
    unique_results = []
    for result in state.result_from_simulation:
        if result not in unique_results:
            unique_results.append(result)
        else:
            print(f"중복 후보: {result.candidate.metal_1}-{result.candidate.metal_2}-{result.candidate.metal_1_composition:.2f}-{result.candidate.metal_2_composition:.2f}-{result.candidate.site}")
    
    state.result_from_simulation = unique_results
    return state


async def validation_node(state: GraphState):
    """
    시뮬레이션 결과를 검증하여 반복 여부를 결정합니다.
    딕셔너리 대신 구조화된 객체를 사용하여 더 깔끔한 알고리즘을 구현합니다.
    """
    print("=====validation_node=====")

    # 토큰 정보 저장
    token_usage_save_path = os.path.join(DEFAULT_SAVE_PATH, f"token_usage_step_{state.step_of_hypothesis}.csv")
    df_token_usage = pd.DataFrame([{
        "main_agent_input_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "main_agent_output_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "main_agent_total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "sub_agent_input_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "sub_agent_output_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "sub_agent_total_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens + state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens
    }])
    df_token_usage.to_csv(token_usage_save_path, index=False)
    print(f"토큰 수 저장 파일 경로: {token_usage_save_path}")

    # 중복 제거 
    num_of_candidates_before_duplication = len(state.result_from_simulation)
    state = remove_duplicate_simulation_results(state)
    num_of_candidates_after_duplication = len(state.result_from_simulation)
    print(f"중복 제거 (전) -> (후): {num_of_candidates_before_duplication} -> {num_of_candidates_after_duplication}")
    
    # 성공한 시뮬레이션 결과만 필터링
    successful_results = [result for result in state.result_from_simulation if result.is_success]
    if not successful_results:
        print("검증할 성공적인 결과가 없습니다. 반복을 계속합니다.")
        state.should_stop = False
        return state
    else:
        optimal_catalysts_count = sum(
            1 for result in successful_results
            if abs(result.adsorption_energy_eV - OPTIMAL_ENERGY) <= OPTIMAL_ENERGY_THRESHOLD
        ) 
    
    validation_description = f"""
    지금까지 조사한 전체 후보 개수: {len(state.result_from_simulation)}
    지금까지 시뮬레이션에 성공한 후보 개수: {len(successful_results)}
    누적된 최적 촉매 개수 (|ΔE| ≤ {OPTIMAL_ENERGY_THRESHOLD} eV): {optimal_catalysts_count}
    """

    # 반복 여부 결정
    if optimal_catalysts_count >= REQUIRED_CANDIDATES_COUNT:
        state.should_stop = True
        print(f"✅ validation metric 통과 --> 반복 중단")
    else:
        state.should_stop = False
        print(f"❌ validation metric 통과 실패 --> 반복 진행")


    print(f"[검증 결과(Step {state.step_of_hypothesis})]")
    print(validation_description)

    # 결과 저장 코드
    print("검증 결과 저장 시작...")
    validation_result_path = os.path.join(DEFAULT_SAVE_PATH, f"validation_result_step_{state.step_of_hypothesis}.txt")
    with open(validation_result_path, "w", encoding="utf-8") as f:
        f.write(f"검증 결과: {validation_description}")
    print(f"결과 파일 경로: {validation_result_path}")
    
    return state



async def validation_node_v2(state: GraphState):
    """
    시뮬레이션 결과를 검증하여 반복 여부를 결정합니다.
    딕셔너리 대신 구조화된 객체를 사용하여 더 깔끔한 알고리즘을 구현합니다.
    """
    print("=====validation_node=====")

    # 토큰 정보 저장
    token_usage_save_path = os.path.join(DEFAULT_SAVE_PATH, f"token_usage_step_{state.step_of_hypothesis}.csv")
    df_token_usage = pd.DataFrame([{
        "main_agent_input_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "main_agent_output_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "main_agent_total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "sub_agent_input_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "sub_agent_output_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "sub_agent_total_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens + state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens
    }])
    df_token_usage.to_csv(token_usage_save_path, index=False)
    print(f"토큰 수 저장 파일 경로: {token_usage_save_path}")
    
    # 성공한 시뮬레이션 결과만 필터링
    successful_results = [result for result in state.result_from_simulation if result.is_success]    


    # 성공한 시뮬레이션 결과가 없는 경우
    if not successful_results:
        print("검증할 성공적인 결과가 없습니다. 반복을 계속합니다.")
        state.should_stop = False
        return state

    # ========================(2번 조건)=======================
    # 가장 최근 후보들만 선택 (최대 RECENT_CANDIDATES_COUNT개)
    recent_candidates = successful_results[-RECENT_CANDIDATES_COUNT:]
    # 최근 후보 개수가 RECENT_CANDIDATES_COUNT개 미만인 경우
    if len(recent_candidates) < RECENT_CANDIDATES_COUNT:
        print(f"최근 후보 개수가 {RECENT_CANDIDATES_COUNT}개 미만입니다(현재 {len(recent_candidates)}개). 반복을 계속합니다.")
        state.should_stop = False
        return state
    

    # 최근 후보들 중 최적 촉매 개수 계산 (절댓값이 임계값 이하인 경우)
    optimal_catalysts = sum(
        1 for result in recent_candidates 
        if abs(result.adsorption_energy_eV - OPTIMAL_ENERGY) <= OPTIMAL_ENERGY_THRESHOLD
    )
    
    total_recent_candidates = len(recent_candidates)
    optimal_ratio = (optimal_catalysts / total_recent_candidates) * 100 if total_recent_candidates > 0 else 0
    validation_description = f"""
    지금까지 시도한 전체 후보 개수: {len(state.result_from_simulation)}
    지금까지 시뮬레이션 가동에 성공한 후보 개수: {len(successful_results)}
    시험용 후보 개수: {RECENT_CANDIDATES_COUNT}
    시험용 후보 중 최적 촉매 개수 (|ΔE| ≤ {OPTIMAL_ENERGY_THRESHOLD} eV): {optimal_catalysts}
    시험용 후보 중 최적 촉매 비율: {optimal_ratio:.1f}%
    """
    # 반복 여부 결정
    if optimal_catalysts >= MIN_SUCCESS_COUNT:
        state.should_stop = True
        print(f"✅ validation metric 통과 --> 반복 중단")
    else:
        state.should_stop = False
        print(f"❌ validation metric 통과 실패 --> 반복 진행")
    
    # ========================(공통 출력 코드)=======================
    print(f"[검증 결과(Step {state.step_of_hypothesis})]")
    print(validation_description)

    # 결과 저장 코드
    print("검증 결과 저장 시작...")
    validation_result_path = os.path.join(DEFAULT_SAVE_PATH, f"validation_result_step_{state.step_of_hypothesis}.txt")
    with open(validation_result_path, "w", encoding="utf-8") as f:
        f.write(f"검증 결과: {validation_description}")
    print(f"결과 파일 경로: {validation_result_path}")
    
    return state


async def validation_node_v3(state: GraphState):
    """
    Step 10에서 자동으로 종료시키는 metric 적용
    최종 목표는 10번의 반복 동안 가장 좋은 촉매를 찾는 것
    """
    print("=====validation_node_v3=====")

    # 토큰 정보 저장
    token_usage_save_path = os.path.join(DEFAULT_SAVE_PATH, f"token_usage_step_{state.step_of_hypothesis}.csv")
    df_token_usage = pd.DataFrame([{
        "main_agent_input_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "main_agent_output_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "main_agent_total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "sub_agent_input_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].input_tokens,
        "sub_agent_output_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].output_tokens,
        "sub_agent_total_tokens": state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens,
        "total_tokens": state.main_agent_token_usage[state.step_of_hypothesis-1].total_tokens + state.sub_agent_token_usage[state.step_of_hypothesis-1].total_tokens
    }])
    df_token_usage.to_csv(token_usage_save_path, index=False)
    print(f"토큰 수 저장 파일 경로: {token_usage_save_path}")

    # 중복 제거 
    num_of_candidates_before_duplication = len(state.result_from_simulation)
    state = remove_duplicate_simulation_results(state)
    num_of_candidates_after_duplication = len(state.result_from_simulation)
    print(f"중복 제거 (전) -> (후): {num_of_candidates_before_duplication} -> {num_of_candidates_after_duplication}")
    
    # 성공한 시뮬레이션 결과만 필터링
    successful_results = [result for result in state.result_from_simulation if result.is_success]
    if not successful_results:
        print("검증할 성공적인 결과가 없습니다. 반복을 계속합니다.")
        state.should_stop = False
        return state
    else:
        optimal_catalysts_count = sum(
            1 for result in successful_results
            if abs(result.adsorption_energy_eV - OPTIMAL_ENERGY) <= OPTIMAL_ENERGY_THRESHOLD
        ) 
    


    # 최적 촉매 후보 선정
    best_catalysts = successful_results[0]
    for result in successful_results:
        if abs(result.adsorption_energy_eV - OPTIMAL_ENERGY) < abs(best_catalysts.adsorption_energy_eV - OPTIMAL_ENERGY):
            best_catalysts = result


    validation_description = f"""
    지금까지 조사한 전체 후보 개수: {len(state.result_from_simulation)}
    지금까지 시뮬레이션에 성공한 후보 개수: {len(successful_results)}
    최고의 촉매: {best_catalysts.candidate.metal_1}-{best_catalysts.candidate.metal_2}-{best_catalysts.candidate.metal_1_composition:.2f}-{best_catalysts.candidate.metal_2_composition:.2f}-{best_catalysts.candidate.site}
    {best_catalysts.adsorption_energy_eV:.4f} eV (|ΔE| = {abs(best_catalysts.adsorption_energy_eV - OPTIMAL_ENERGY):.4f} eV)
    """
    
    print(f"[검증 결과(Step {state.step_of_hypothesis})]")
    print(validation_description)

    # 반복 여부 결정
    if state.step_of_hypothesis >= REQUIRED_ITERATION_COUNT:
        state.should_stop = True
        print(f"✅ {REQUIRED_ITERATION_COUNT}번의 반복 횟수 도달 --> 반복 중단")
    else:
        state.should_stop = False
        print(f"{REQUIRED_ITERATION_COUNT}번의 반복 횟수 미만 --> 반복 진행")


    # 결과 저장 코드
    print("검증 결과 저장 시작...")
    validation_result_path = os.path.join(DEFAULT_SAVE_PATH, f"validation_result_step_{state.step_of_hypothesis}.txt")
    with open(validation_result_path, "w", encoding="utf-8") as f:
        f.write(f"검증 결과: {validation_description}")
    print(f"결과 파일 경로: {validation_result_path}")
    
    return state



if __name__ == "__main__":
    async def test_validation_node():
        state = GraphState()
        
        # 테스트용 시뮬레이션 결과 생성
        test_candidate1 = CatalystCandidate(
            metal_1='Pt', 
            metal_2='Ru', 
            metal_1_composition=0.75, 
            metal_2_composition=0.25, 
            site='top'
        )
        test_candidate2 = CatalystCandidate(
            metal_1='Hg', 
            metal_2='Pt', 
            metal_1_composition=0.5, 
            metal_2_composition=0.5, 
            site='top'
        )
        
        test_result1 = SimulationResult(
            candidate=test_candidate1,
            adsorption_energy_eV=-0.249490838358696,
            is_success=True
        )
        test_result2 = SimulationResult(
            candidate=test_candidate2,
            adsorption_energy_eV=-0.1537735711562788,
            is_success=True
        )
        test_result3 = SimulationResult(
            candidate=test_candidate1,
            adsorption_energy_eV=-0.249490838358696,
            is_success=True
        )
        
        state.result_from_simulation = [test_result1, test_result2, test_result3]
        state.main_agent_token_usage = [TokenUsage(input_tokens=1321, output_tokens=535, total_tokens=1856)]
        state.sub_agent_token_usage = [TokenUsage(input_tokens=2746, output_tokens=154, total_tokens=2900)]
        state.step_of_hypothesis = 1
        result = await validation_node_v3(state)
    
    asyncio.run(test_validation_node())