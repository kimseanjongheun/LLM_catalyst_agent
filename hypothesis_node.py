from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import asyncio
import os
from node_models import GraphState, TokenUsage, SubAgentQuery, CatalystCandidate, SimulationResult
from dotenv import load_dotenv
from node_models import MAIN_AGENT_MODEL_NAME, DEFAULT_SAVE_PATH


load_dotenv("key/.env")
api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model=MAIN_AGENT_MODEL_NAME, api_key=api_key)


async def hypothesis_node(state: GraphState):
    print("=====hypothesis_node=====")
    if state.step_of_hypothesis == 0:
        
        # 가설 step 증가
        state.step_of_hypothesis += 1
        print(f"[가설 생성 시작(Step {state.step_of_hypothesis})]")

        # prompt 선언
        system_prompt_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\prompts\main_system_prompt.txt"
        db_info_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\prompts\DB_info.txt"
        user_prompt_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\prompts\user_prompt.txt"
        
        with open(user_prompt_path, "r", encoding="utf-8") as f:
            state.user_prompt = f.read()

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            state.main_system_prompt = f.read()

        with open(db_info_path, "r", encoding="utf-8") as f:
            state.db_info = f.read()
        
        # 가설 생성을 위한 프롬프트 템플릿 생성
        hypothesis_prompt = ChatPromptTemplate.from_messages([
            ("system", state.main_system_prompt),
            ("user", f"""
        Based on the following information, please formulate a hypothesis:

        User Request:
        {state.user_prompt}

        Database Information:
        {state.db_info}

        Please synthesize the above information and present a scientific and specific hypothesis.
        """)
        ])
        
        # 가설 생성
        hypothesis_chain = hypothesis_prompt | model
        response = await hypothesis_chain.ainvoke({})

        # 토큰 수 집계 및 저장장
        token_usage = TokenUsage(
            input_tokens=response.usage_metadata['input_tokens'],
            output_tokens=response.usage_metadata['output_tokens'],
            total_tokens=response.usage_metadata['total_tokens']
        )
        state.main_agent_token_usage.append(token_usage)
        print(f"Main agent token 사용량량: {state.main_agent_token_usage[state.step_of_hypothesis-1]}")

        # 생성된 가설을 state에 저장
        state.hypothesis = response.content

        # state.hypothesis에 들어있을 중괄호 제거하기
        state.hypothesis = state.hypothesis.replace("{", "[").replace("}", "]")
        
        print(f"가설 생성 완료(Step {state.step_of_hypothesis})")
        # print(state.hypothesis)

        # 결과 저장 코드
        print("가설 저장 시작...")
        hypothesis_result_path = os.path.join(DEFAULT_SAVE_PATH, f"hypothesis_result_step_{state.step_of_hypothesis}.txt")
        with open(hypothesis_result_path, "w", encoding="utf-8") as f:
            f.write(state.hypothesis)
        print(f"결과 파일 경로: {hypothesis_result_path}")

        return state

    else:

        # 가설 step 증가
        state.step_of_hypothesis += 1
        print(f"[가설 수정 시작(Step {state.step_of_hypothesis})]")
        # prompt 선언
        # CatalystCandidate와 SimulationResult 객체를 string 직렬화할 수 있도록 변환 함수 정의
        def simulation_result_to_str(result):
            if result.is_success:
                return f"{result.candidate.metal_1}-{result.candidate.metal_2}-{result.candidate.metal_1_composition:.2f}-{result.candidate.metal_2_composition:.2f}-{result.candidate.site}: {result.adsorption_energy_eV:.4f} eV"
            else:
                return f"{result.error_message}"

        results_str = [simulation_result_to_str(r) + "\n" for r in state.result_from_simulation]

        # 가설 수정을 위한 프롬프트 템플릿 생성        
        hypothesis_prompt = ChatPromptTemplate.from_messages([
            ("system", state.main_system_prompt),
            ("user", f"""
        Based on the result of the simulation, please modify the hypothesis:

        Hypothesis:
        {state.hypothesis}

        Simulation Result:
        {results_str}

        """)
        ])
        
        # 가설 생성
        hypothesis_chain = hypothesis_prompt | model
        response = await hypothesis_chain.ainvoke({})

        # 토큰 수 집계 및 저장
        token_usage = TokenUsage(
            input_tokens=response.usage_metadata['input_tokens'],
            output_tokens=response.usage_metadata['output_tokens'],
            total_tokens=response.usage_metadata['total_tokens']
        )
        state.main_agent_token_usage.append(token_usage)
        print(f"Main agent token 사용량: {state.main_agent_token_usage[state.step_of_hypothesis-1]}")

        
        # 생성된 가설을 state에 저장
        state.hypothesis = response.content
        
        # state.hypothesis에 들어있을 중괄호 제거하기
        state.hypothesis = state.hypothesis.replace("{", "[").replace("}", "]")

        print(f"가설 수정 완료(Step {state.step_of_hypothesis})")
        # print(state.hypothesis)

        # 결과 저장 코드
        print("가설 수정 결과 저장 시작...")
        hypothesis_result_path = os.path.join(DEFAULT_SAVE_PATH, f"hypothesis_result_step_{state.step_of_hypothesis}.txt")
        with open(hypothesis_result_path, "w", encoding="utf-8") as f:
            f.write(f"가설 수정 결과: {state.hypothesis}")
        print(f"결과 파일 경로: {hypothesis_result_path}")

        return state

if __name__ == "__main__":
    async def test_hypothesis_node():
        state = GraphState()
        # state.step_of_hypothesis = 0 # 원하는 분기점 활성화
        state.step_of_hypothesis = 1 # 원하는 분기점 활성화
        result = await hypothesis_node(state)
        print(result)
    
    asyncio.run(test_hypothesis_node())
    
