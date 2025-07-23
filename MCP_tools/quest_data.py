#!/usr/bin/env python3
"""
Quest Data MCP Server

LLM이 실제 연구 공간(search space)에 접근할 수 있도록 하는 MCP 서버입니다.
system_compositions_fraction.csv 기반으로 가능한 조성들을 제공합니다.
"""

import asyncio
import json
import logging
import pandas as pd
import ast
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quest-data-server")

# Create server instance
server = Server("quest-data-server")

# Global data storage
compositions_db = None

def load_compositions_database():
    """system_compositions_fraction.csv를 로드하여 전역 변수에 저장"""
    global compositions_db
    try:
        df = pd.read_csv(r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_compositions_fraction.csv")
        compositions_db = []
        
        for _, row in df.iterrows():
            try:
                comp_str = row["composition_fraction"]
                if isinstance(comp_str, str) and comp_str != "Error or Not Available":
                    comp_dict = ast.literal_eval(comp_str)
                    if isinstance(comp_dict, dict):
                        compositions_db.append({
                            "system_id": row["system_id"],
                            "composition": comp_dict,
                            "elements": list(comp_dict.keys()),
                            "n_elements": len(comp_dict.keys())
                        })
            except:
                continue
        
        logger.info(f"조성 데이터베이스 로드 완료: {len(compositions_db)}개 조성")
        return True
    except Exception as e:
        logger.error(f"조성 데이터베이스 로드 실패: {e}")
        return False

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """연구 공간 탐색을 위한 도구들을 나열합니다."""
    return [
        Tool(
            name="get_available_elements",
            description="사용 가능한 모든 원소들의 목록을 반환합니다.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_compositions_by_elements",
            description="지정된 원소들을 포함하는 조성들을 검색합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "검색할 원소들의 배열 (예: ['Pt', 'Ru'])"
                    },
                    "exact_match": {
                        "type": "boolean",
                        "description": "정확히 이 원소들만 포함하는지 여부 (기본값: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "반환할 최대 결과 수 (기본값: 10)",
                        "default": 10
                    }
                },
                "required": ["elements"]
            }
        ),
        Tool(
            name="get_random_compositions",
            description="무작위로 조성들을 샘플링합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "반환할 조성 수 (기본값: 5)",
                        "default": 5
                    },
                    "n_elements": {
                        "type": "integer",
                        "description": "원소 개수 필터 (1=단원계, 2=이원계, 3=삼원계 등)",
                        "minimum": 1
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_search_space_summary",
            description="전체 연구 공간의 요약 통계를 반환합니다.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="validate_composition",
            description="주어진 조성이 연구 공간에 존재하는지 확인합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "composition": {
                        "type": "object",
                        "description": "확인할 조성 dictionary",
                        "additionalProperties": {
                            "type": "number"
                        }
                    }
                },
                "required": ["composition"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """연구 공간 탐색 도구 호출을 처리합니다."""
    
    if compositions_db is None:
        if not load_compositions_database():
            return [TextContent(type="text", text=json.dumps({
                "error": "조성 데이터베이스를 로드할 수 없습니다."
            }, ensure_ascii=False))]
    
    if name == "get_available_elements":
        try:
            all_elements = set()
            for comp_data in compositions_db:
                all_elements.update(comp_data["elements"])
            
            result = {
                "available_elements": sorted(list(all_elements)),
                "total_elements": len(all_elements),
                "status": "success"
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e), "status": "error"
            }, ensure_ascii=False))]
    
    elif name == "search_compositions_by_elements":
        try:
            elements = arguments.get("elements", [])
            exact_match = arguments.get("exact_match", False)
            limit = arguments.get("limit", 10)
            
            matches = []
            for comp_data in compositions_db:
                comp_elements = set(comp_data["elements"])
                search_elements = set(elements)
                
                if exact_match:
                    if comp_elements == search_elements:
                        matches.append(comp_data)
                else:
                    if search_elements.issubset(comp_elements):
                        matches.append(comp_data)
                
                if len(matches) >= limit:
                    break
            
            result = {
                "matches": matches,
                "total_found": len(matches),
                "search_elements": elements,
                "exact_match": exact_match,
                "status": "success"
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e), "status": "error"
            }, ensure_ascii=False))]
    
    elif name == "get_random_compositions":
        try:
            count = arguments.get("count", 5)
            n_elements = arguments.get("n_elements")
            
            filtered_db = compositions_db
            if n_elements:
                filtered_db = [c for c in compositions_db if c["n_elements"] == n_elements]
            
            if not filtered_db:
                result = {
                    "compositions": [],
                    "message": f"원소 개수 {n_elements}인 조성을 찾을 수 없습니다." if n_elements else "조성 데이터가 없습니다.",
                    "status": "not_found"
                }
            else:
                import random
                sample_count = min(count, len(filtered_db))
                sampled = random.sample(filtered_db, sample_count)
                
                result = {
                    "compositions": sampled,
                    "requested_count": count,
                    "returned_count": sample_count,
                    "total_available": len(filtered_db),
                    "filter_n_elements": n_elements,
                    "status": "success"
                }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e), "status": "error"
            }, ensure_ascii=False))]
    
    elif name == "get_search_space_summary":
        try:
            # 원소별 통계
            element_counts = {}
            n_element_counts = {}
            
            for comp_data in compositions_db:
                # 원소별 카운트
                for element in comp_data["elements"]:
                    element_counts[element] = element_counts.get(element, 0) + 1
                
                # n원계별 카운트
                n_elem = comp_data["n_elements"]
                n_element_counts[n_elem] = n_element_counts.get(n_elem, 0) + 1
            
            result = {
                "total_compositions": len(compositions_db),
                "unique_elements": len(element_counts),
                "element_frequency": dict(sorted(element_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
                "n_element_distribution": n_element_counts,
                "available_elements": sorted(list(element_counts.keys())),
                "status": "success"
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e), "status": "error"
            }, ensure_ascii=False))]
    
    elif name == "validate_composition":
        try:
            composition = arguments.get("composition")
            if not composition:
                return [TextContent(type="text", text=json.dumps({
                    "error": "composition 파라미터가 필요합니다."
                }, ensure_ascii=False))]
            
            tolerance = 1e-6
            for comp_data in compositions_db:
                stored_comp = comp_data["composition"]
                
                # 키가 같은지 확인
                if set(stored_comp.keys()) == set(composition.keys()):
                    # 값이 tolerance 내에서 같은지 확인
                    if all(abs(stored_comp[k] - composition[k]) < tolerance for k in stored_comp):
                        result = {
                            "valid": True,
                            "system_id": comp_data["system_id"],
                            "exact_match": comp_data,
                            "status": "success"
                        }
                        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
            result = {
                "valid": False,
                "composition": composition,
                "message": "연구 공간에 해당 조성이 존재하지 않습니다.",
                "status": "not_found"
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e), "status": "error"
            }, ensure_ascii=False))]
    
    else:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Unknown tool '{name}'"
        }, ensure_ascii=False))]

async def main():
    """Main entry point for the Quest Data MCP server."""
    logger.info("Starting Quest Data MCP Server")
    
    # 서버 시작 전에 데이터베이스 로드
    if not load_compositions_database():
        logger.error("조성 데이터베이스 로드 실패 - 서버를 종료합니다.")
        return
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="quest-data-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

이제 LLM Agent에 Quest Data MCP 도구들을 추가해야 합니다:

```python
# agent/llm_agent.py에 추가할 도구들
quest_data_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_available_elements",
            "description": "연구 가능한 모든 원소들의 목록을 확인합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_compositions_by_elements", 
            "description": "특정 원소들을 포함하는 실제 존재하는 조성들을 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "검색할 원소들"
                    },
                    "exact_match": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["elements"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_composition",
            "description": "제안하려는 조성이 실제 연구 공간에 존재하는지 검증합니다.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "composition": {"type": "object", "description": "검증할 조성"}
                },
                "required": ["composition"]
            }
        }
    }
]
```

### 주요 기능:

1. **get_available_elements**: 연구 가능한 모든 원소 목록 제공
2. **search_compositions_by_elements**: 특정 원소 조합으로 실제 존재하는 조성 검색
3. **get_random_compositions**: 무작위 샘플링으로 다양한 조성 제안
4. **validate_composition**: 제안 조성이 실제 존재하는지 검증
5. **get_search_space_summary**: 전체 연구 공간 통계

이렇게 하면 GPT-4o가 존재하지 않는 조성을 제안하는 문제를 해결하고, 실제 연구 가능한 범위 내에서만 조성을 제안하도록 할 수 있습니다!
