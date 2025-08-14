from node_models import GraphState, TokenUsage, SubAgentQuery, CatalystCandidate, SimulationResult, DEFAULT_SAVE_PATH
import pandas as pd
import asyncio
import pickle
import os


async def simulation_node(state: GraphState):
    print("=====simulation_node=====")
    # 후보군 선정 함수
    def get_simulation_result(df: pd.DataFrame,
                             candidate: CatalystCandidate,
                             random_state: int = None) -> pd.DataFrame:
        """
        DB에서 주어진 촉매 후보 조건을 만족하는 후보군을 무작위로 추출합니다.

        Args:
            df (pd.DataFrame): 읽어올 DB.
            candidate (CatalystCandidate): 촉매 후보 정보.
            random_state (int, optional): 재현 가능한 랜덤 시드를 주려면 지정.

        Returns:
            pd.DataFrame: 조건을 만족하는 행 중 무작위 추출된 DataFrame.
        """

        # 필터 조건 설정
        filters = {
            'Metal1': candidate.metal_1,
            'Metal2': candidate.metal_2,
            'Metal1_Composition': candidate.metal_1_composition,
            'Metal2_Composition': candidate.metal_2_composition,
            'Site': candidate.site
        }

        # 각 필터 조건 적용
        mask = pd.Series(True, index=df.index)
        for col, cond in filters.items():
            if col not in df.columns:
                raise KeyError(f"'{col}' 열이 DB에 존재하지 않습니다.")
            mask &= (df[col] == cond)

        # 필터링된 후보군
        candidates = df[mask]
        if candidates.empty:
            # 딕셔너리 대신 읽기 쉬운 형태로 에러 메시지 생성
            error_details = f"Metal1={candidate.metal_1}, Metal2={candidate.metal_2}, Composition=({candidate.metal_1_composition:.2f}:{candidate.metal_2_composition:.2f}), Site={candidate.site}"
            raise ValueError(f"조건을 만족하는 후보가 없습니다: {error_details}")

        # 무작위 샘플링 (1개 추출)
        return candidates.sample(n=1, random_state=random_state)

    
    # DB 경로 설정
    db_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_MamunHighT2019.csv"
    df = pd.read_csv(db_path)
    
    # 각 후보에 대해 시뮬레이션 수행
    results = []
    random_state = 42
    
    for i, candidate in enumerate(state.query_to_simulation.candidates):
        try:
            result = get_simulation_result(df, candidate, random_state)
            adsorption_energy = float(result['adsorption_energy'].values[0])
            
            simulation_result = SimulationResult(
                candidate=candidate,
                adsorption_energy_eV=adsorption_energy,
                is_success=True
            )
            results.append(simulation_result)
            
            print(f"후보 {i+1}: {candidate.metal_1}-{candidate.metal_2} ({candidate.metal_1_composition:.2f}:{candidate.metal_2_composition:.2f}) - {candidate.site}: {adsorption_energy} eV")
            
        except ValueError as e:
            # 조건을 만족하는 후보가 없는 경우
            print(f"후보 {i+1} 처리 중 오류: {e}")
            simulation_result = SimulationResult(
                candidate=candidate,
                adsorption_energy_eV=10000.0,
                is_success=False,
                error_message=str(e)
            )
            results.append(simulation_result)
            
        except KeyError as e:
            # DB 컬럼이 존재하지 않는 경우
            print(f"후보 {i+1} 처리 중 오류: {e}")
            simulation_result = SimulationResult(
                candidate=candidate,
                adsorption_energy_eV=10000.0,
                is_success=False,
                error_message=f"DB 컬럼 오류: {str(e)}"
            )
            results.append(simulation_result)
            
        except Exception as e:
            # 기타 예외 처리
            print(f"후보 {i+1} 처리 중 예상치 못한 오류: {e}")
            simulation_result = SimulationResult(
                candidate=candidate,
                adsorption_energy_eV=10000.0,
                is_success=False,
                error_message=f"예상치 못한 오류: {str(e)}"
            )
            results.append(simulation_result)
    
    # 결과 저장 코드(중복 제거 버전) pickle 사용
    unique_results_in_this_step = []
    for result in results:
        if result not in state.result_from_simulation:
            unique_results_in_this_step.append(result)
        else:
            print(f"중복 후보: {result.candidate.metal_1}-{result.candidate.metal_2}-{result.candidate.metal_1_composition:.2f}-{result.candidate.metal_2_composition:.2f}-{result.candidate.site}")

    simulation_result_path = os.path.join(DEFAULT_SAVE_PATH, f"simulation_result_step_{state.step_of_hypothesis}_unique.pkl")
    with open(simulation_result_path, "wb") as f:
        pickle.dump(unique_results_in_this_step, f)
    print(f"중복 제거 결과 파일 경로: {simulation_result_path}")
    print(f"-> 시뮬레이션 결과{len(unique_results_in_this_step)}개(중복 제거) 저장 완료(Step {state.step_of_hypothesis})")
    
    # 결과 저장 코드(중복 포함 버전) pickle 사용
    simulation_result_path = os.path.join(DEFAULT_SAVE_PATH, f"simulation_result_step_{state.step_of_hypothesis}.pkl")
    with open(simulation_result_path, "wb") as f:
        pickle.dump(results, f)
    print(f"중복 포함 결과 파일 경로: {simulation_result_path}")
    print(f"-> 시뮬레이션 결과{len(results)}개(중복 포함) 저장 완료(Step {state.step_of_hypothesis})")


    # 결과를 state에 저장(결과는 중복으로 저장하기)
    state.result_from_simulation.extend(results)
    return state



if __name__ == "__main__":
    async def test_simulation_node():
        state = GraphState()        
        candidate = SubAgentQuery(
            candidates=[CatalystCandidate(metal_1="Pt", 
            metal_2="Ru", 
            metal_1_composition=0.75, 
            metal_2_composition=0.25,
            site="top"),
            CatalystCandidate(metal_1="Hg", 
            metal_2="Pt", 
            metal_1_composition=0.5, 
            metal_2_composition=0.5,
            site="top")
            ],
        )

        state.query_to_simulation = candidate
        
        result = await simulation_node(state)
        print("결과 DataFrame:")
        print(result.result_from_simulation)
    
    asyncio.run(test_simulation_node())