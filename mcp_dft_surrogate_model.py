#!/usr/bin/env python3
"""
MCP DFT Surrogate Model Server

LLM agent가 DFT surrogate model을 도구로 사용할 수 있도록 하는 MCP 서버입니다.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

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

from dft.dft_surrogate_model import get_adsorp_energy_by_composition

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-dft-surrogate")

# Create server instance
server = Server("mcp-dft-surrogate")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools for DFT surrogate model."""
    return [
        Tool(
            name="get_adsorp_energy",
            description="주어진 조성(composition)에 대한 흡착 에너지를 예측합니다. 조성은 dictionary 형태로 제공해야 합니다.",
            inputSchema={
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
        ),
        Tool(
            name="check_composition_exists", 
            description="주어진 조성이 system_compositions_fraction.csv에 존재하는지 확인합니다.",
            inputSchema={
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
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for DFT surrogate model."""
    
    if name == "get_adsorp_energy":
        try:
            composition = arguments.get("composition")
            if not composition:
                return [TextContent(type="text", text="Error: composition parameter is required")]
            
            # Validate composition is dict
            if not isinstance(composition, dict):
                return [TextContent(type="text", text="Error: composition must be a dictionary")]
            
            # Get adsorption energy
            energy = get_adsorp_energy_by_composition(composition)
            
            if energy is not None:
                result = {
                    "composition": composition,
                    "adsorp_energy": energy,
                    "status": "success"
                }
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            else:
                result = {
                    "composition": composition,
                    "adsorp_energy": None,
                    "status": "not_found",
                    "message": "해당 조성에 대한 데이터를 찾을 수 없습니다."
                }
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
                
        except Exception as e:
            error_result = {
                "composition": arguments.get("composition"),
                "status": "error",
                "error": str(e)
            }
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
    
    elif name == "check_composition_exists":
        try:
            composition = arguments.get("composition")
            if not composition:
                return [TextContent(type="text", text="Error: composition parameter is required")]
            
            # Check if composition exists by trying to get energy
            energy = get_adsorp_energy_by_composition(composition)
            exists = energy is not None
            
            result = {
                "composition": composition,
                "exists": exists,
                "status": "success"
            }
            if exists:
                result["adsorp_energy"] = energy
                
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        except Exception as e:
            error_result = {
                "composition": arguments.get("composition"),
                "status": "error", 
                "error": str(e)
            }
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
    
    else:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP DFT Surrogate Model Server")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-dft-surrogate",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 