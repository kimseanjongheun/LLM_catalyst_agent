from langchain_core.prompts import ChatPromptTemplate
import asyncio
import os
from node_models import GraphState, TokenUsage, SubAgentQuery, CatalystCandidate, SimulationResult
from dotenv import load_dotenv
import instructor
from node_models import SUB_AGENT_MODEL_NAME


# key 선언
load_dotenv("key/.env")
api_key = os.getenv("OPENAI_API_KEY")


async def sub_agent_node(state: GraphState):
    print("=====sub_agent_node=====")
    # prompt 선언
    system_prompt_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\prompts\sub_system_prompt.txt"
    db_info_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\prompts\DB_info.txt"
    
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        state.sub_system_prompt = f.read()
    
    with open(db_info_path, "r", encoding="utf-8") as f:
        state.db_info = f.read()
    
    # 서브 에이전트 쿼리 생성
    sub_agent_query_prompt = ChatPromptTemplate.from_messages([
        ("system", state.sub_system_prompt),
        ("user", """
    Based on the following information, please formulate a query for the sub‐agent:

    Main Agent Query:
    {main_agent_query}

    Database Information:
    {db_info}

    Previous Result:
    {previous_result}

    Instructions:
    Synthesize the above into a clear, focused query for the sub‐agent.  
    The query **must** specify a bimetallic combination (Metal1, Metal2) and composition fractions that exist in the provided database.  
    Include the adsorption site (top, bridge, or hollow) as defined in the DB.  
    Do not invent any new metal combinations—only use entries available in DB.
    Do not repeat the same metal combination that has been tested before.
    """)
    ])

    
    # CatalystCandidate와 SimulationResult 객체를 string 직렬화할 수 있도록 변환 함수 정의
    def simulation_result_to_str(result):
        if result.is_success:
            return f"{result.candidate.metal_1}-{result.candidate.metal_2}-{result.candidate.metal_1_composition:.2f}-{result.candidate.metal_2_composition:.2f}-{result.candidate.site}: {result.adsorption_energy_eV:.4f} eV"
        else:
            return f"{result.error_message}"

    results_str = [simulation_result_to_str(r) + "\n" for r in state.result_from_simulation]
    
    
    # 프롬프트에 변수 전달
    formatted_prompt = await sub_agent_query_prompt.ainvoke({
        "main_agent_query": state.hypothesis,
        "db_info": state.db_info,
        "previous_result": results_str
    })

    client = instructor.from_provider(
    f"openai/{SUB_AGENT_MODEL_NAME}",
     api_key=api_key,
     mode=instructor.Mode.TOOLS
     )

    print("sub agent 답변 생성중...")
    state.query_to_simulation, completion = client.chat.completions.create_with_completion(
    response_model=SubAgentQuery,
    messages=[{"role": "user", "content": formatted_prompt.to_string()}],
    )

    # 토큰 수 집계
    token_usage = TokenUsage(
        input_tokens=completion.usage.prompt_tokens,
        output_tokens=completion.usage.completion_tokens,
        total_tokens=completion.usage.total_tokens
    )
    state.sub_agent_token_usage.append(token_usage)
    print(f"Sub agent token 사용량: {state.sub_agent_token_usage[state.step_of_hypothesis-1]}")


    print(f"[서브 에이전트 쿼리 생성 완료(Step {state.step_of_hypothesis})]")
    # print(state.query_to_simulation)
    
    return state


if __name__ == "__main__":
    async def test_sub_agent_node():
        state = GraphState()
        result = await sub_agent_node(state)
    
    asyncio.run(test_sub_agent_node())
