import openai
import os
import re
import ast
import json
import logging
from dotenv import load_dotenv
import pandas as pd

# Set up logging for MCP tool tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_agent_mcp")

class LLMAgent:
    def __init__(self, use_mcp_tools=False):
        # key/.env 파일에서 API 키 로드
        load_dotenv("key/.env")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 key/.env 파일에 설정되지 않았습니다.")
        
        # OpenAI 클라이언트 초기화 (1.0.0+ 버전)
        self.client = openai.OpenAI(api_key=api_key)
        self.use_mcp_tools = use_mcp_tools
        
        # MCP tool usage tracking
        self.tool_usage_log = []
        
        logger.info(f"LLMAgent 초기화: MCP tools {'사용' if use_mcp_tools else '미사용'}")
        
        # MCP tools 정의 (DFT surrogate model)
        self.mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_adsorp_energy",
                    "description": "주어진 조성(composition)에 대한 흡착 에너지를 예측합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "composition": {
                                "type": "object",
                                "description": "촉매 조성을 나타내는 dictionary (예: {'Pt': 0.5, 'Ru': 0.5})",
                                "additionalProperties": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                }
                            }
                        },
                        "required": ["composition"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "check_composition_exists",
                    "description": "주어진 조성이 데이터베이스에 존재하는지 확인합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "composition": {
                                "type": "object",
                                "description": "확인할 조성 dictionary (예: {'Pt': 0.5, 'Ru': 0.5})",
                                "additionalProperties": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                }
                            }
                        },
                        "required": ["composition"]
                    }
                }
            }
        ]

    def ask(self, prompt):
        # LLM 호출 및 응답 반환 (새로운 API 사용)
        messages = [{"role": "user", "content": prompt}]
        
        if self.use_mcp_tools:
            logger.info("MCP tools를 사용하여 LLM 호출 시작")
            # MCP tools를 사용하는 경우
            response = self.client.chat.completions.create(
                model="gpt-4o", #"gpt-3.5-turbo"
                messages=messages,
                tools=self.mcp_tools,
                tool_choice="auto"
            )
            
            # Tool call이 있는지 확인
            if response.choices[0].message.tool_calls:
                tool_count = len(response.choices[0].message.tool_calls)
                logger.info(f"Tool calls {tool_count}개 감지됨")
                return self._handle_tool_calls(response, messages)
            else:
                logger.info("Tool calls 없음 - 일반 응답 반환")
                return response.choices[0].message.content
        else:
            logger.info("기본 모드로 LLM 호출")
            # 기본 모드
            response = self.client.chat.completions.create(
                model="gpt-4o", #"gpt-3.5-turbo"
                messages=messages
            )
            return response.choices[0].message.content
    
    def _handle_tool_calls(self, response, messages):
        """Handle tool calls from OpenAI response."""
        from dft.dft_surrogate_model import get_adsorp_energy_by_composition
        
        # Add assistant message with tool calls
        messages.append(response.choices[0].message)
        
        successful_calls = 0
        failed_calls = 0
        
        # Execute each tool call
        for i, tool_call in enumerate(response.choices[0].message.tool_calls):
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            tool_usage_entry = {
                "function_name": function_name,
                "arguments": arguments,
                "timestamp": json.dumps(pd.Timestamp.now(), default=str)
            }
            
            if function_name == "get_adsorp_energy":
                composition = arguments.get("composition")
                energy = get_adsorp_energy_by_composition(composition)
                
                result = {
                    "composition": composition,
                    "adsorp_energy": energy,
                    "status": "success" if energy is not None else "not_found"
                }
                
                tool_usage_entry["result"] = result
                if energy is not None:
                    successful_calls += 1
                else:
                    failed_calls += 1
                
            elif function_name == "check_composition_exists":
                composition = arguments.get("composition")
                energy = get_adsorp_energy_by_composition(composition)
                
                result = {
                    "composition": composition,
                    "exists": energy is not None,
                    "status": "success"
                }
                if energy is not None:
                    result["adsorp_energy"] = energy
                
                tool_usage_entry["result"] = result
                successful_calls += 1
            
            else:
                result = {"error": f"Unknown function: {function_name}"}
                tool_usage_entry["result"] = result
                failed_calls += 1
            
            self.tool_usage_log.append(tool_usage_entry)
            
            # Add tool result to messages
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result, ensure_ascii=False)
            })
        
        # 간략한 요약 로그만 출력
        total_calls = successful_calls + failed_calls
        logger.info(f"Tool calls 처리 완료: {total_calls}개 (성공: {successful_calls}, 실패: {failed_calls})")
        
        # Get final response from model
        final_response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    def get_tool_usage_summary(self):
        """MCP tool 사용 통계 반환"""
        if not self.tool_usage_log:
            return {"total_calls": 0, "functions_used": {}}
        
        summary = {
            "total_calls": len(self.tool_usage_log),
            "functions_used": {},
            "successful_calls": 0,
            "failed_calls": 0
        }
        
        for entry in self.tool_usage_log:
            func_name = entry["function_name"]
            if func_name not in summary["functions_used"]:
                summary["functions_used"][func_name] = 0
            summary["functions_used"][func_name] += 1
            
            if entry["result"].get("status") in ["success", "not_found"]:
                summary["successful_calls"] += 1
            else:
                summary["failed_calls"] += 1
        
        return summary
    
    def save_tool_usage_log(self, filepath="logs/mcp_tool_usage.json"):
        """MCP tool 사용 로그를 파일로 저장"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.tool_usage_log, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Tool usage log 저장: {filepath}")
    
    def parse_composition(self, llm_output):
        """
        LLM 출력에서 조성 정보(dictionary)만 추출합니다.
        다양한 형태의 답변을 처리할 수 있습니다.
        """
        if isinstance(llm_output, dict):
            return llm_output
        
        # 1. 직접 dictionary 형태인지 확인
        try:
            # 문자열을 dictionary로 파싱 시도
            composition = ast.literal_eval(llm_output.strip())
            if isinstance(composition, dict):
                return composition
        except:
            pass
        
        # 2. 코드 블록 내의 dictionary 찾기
        code_block_pattern = r'```(?:python)?\s*(\{.*?\})\s*```'
        matches = re.findall(code_block_pattern, llm_output, re.DOTALL)
        for match in matches:
            try:
                composition = ast.literal_eval(match)
                if isinstance(composition, dict):
                    return composition
            except:
                continue
        
        # 3. 조성: {dictionary} 형태 찾기
        composition_pattern = r'조성\s*[:：]\s*(\{.*?\})'
        matches = re.findall(composition_pattern, llm_output, re.DOTALL)
        for match in matches:
            try:
                composition = ast.literal_eval(match)
                if isinstance(composition, dict):
                    return composition
            except:
                continue
        
        # 4. {dictionary} 형태 직접 찾기
        dict_pattern = r'\{[^{}]*"[A-Za-z]+"[^{}]*:[^{}]*\d+\.?\d*[^{}]*\}'
        matches = re.findall(dict_pattern, llm_output)
        for match in matches:
            try:
                composition = ast.literal_eval(match)
                if isinstance(composition, dict):
                    return composition
            except:
                continue
        
        # 5. 실패 시 None 반환
        return None