"""
Output Parsers for LLM Catalyst Agent
LLM 출력을 구조화된 데이터로 파싱하는 파서들을 정의합니다.
"""

import re
import ast
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
import logging

logger = logging.getLogger(__name__)


class BaseOutputParser(ABC):
    """OutputParser의 기본 추상 클래스"""
    
    @abstractmethod
    def parse(self, text: str) -> Any:
        """LLM 출력 텍스트를 파싱하여 구조화된 데이터로 변환"""
        pass
    
    @abstractmethod
    def get_format_instructions(self) -> str:
        """파서가 예상하는 출력 형식에 대한 지침을 반환"""
        pass


class CompositionOutputParser(BaseOutputParser):
    """촉매 조성(composition) 파싱을 위한 전용 파서"""
    
    def __init__(self, validation: bool = True):
        """
        Args:
            validation: 파싱된 조성의 유효성을 검증할지 여부
        """
        self.validation = validation
    
    def parse(self, text: str) -> Optional[Dict[str, float]]:
        """
        LLM 출력에서 조성 정보(dictionary)를 추출합니다.
        
        Args:
            text: LLM의 출력 텍스트
            
        Returns:
            촉매 조성 딕셔너리 또는 None (파싱 실패시)
        """
        if isinstance(text, dict):
            return self._validate_composition(text) if self.validation else text
        
        # 파싱 전략들을 순서대로 시도
        parsing_strategies = [
            self._parse_direct_dict,
            self._parse_composition_section,
            self._parse_composition_line,
            self._parse_code_block,
            self._parse_code_block_with_assignment,
            self._parse_korean_format,
            self._parse_generic_dict
        ]
        
        for strategy in parsing_strategies:
            try:
                result = strategy(text)
                if result is not None:
                    logger.debug(f"Successfully parsed using {strategy.__name__}")
                    return self._validate_composition(result) if self.validation else result
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        logger.warning("All parsing strategies failed")
        return None
    
    def _parse_direct_dict(self, text: str) -> Optional[Dict[str, float]]:
        """직접 dictionary 형태인지 확인"""
        composition = ast.literal_eval(text.strip())
        return composition if isinstance(composition, dict) else None
    
    def _parse_composition_section(self, text: str) -> Optional[Dict[str, float]]:
        """**COMPOSITION:** 섹션 후의 composition = {...} 패턴"""
        pattern = r'\*\*COMPOSITION:\*\*\s*\n\s*composition\s*=\s*(\{[^}]*\})'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _parse_composition_line(self, text: str) -> Optional[Dict[str, float]]:
        """composition = {...} 라인 패턴"""
        pattern = r'composition\s*=\s*(\{[^}]*\})'
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _parse_code_block(self, text: str) -> Optional[Dict[str, float]]:
        """코드 블록 내의 dictionary"""
        pattern = r'```(?:python)?\s*(\{.*?\})\s*```'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _parse_code_block_with_assignment(self, text: str) -> Optional[Dict[str, float]]:
        """코드 블록 내의 composition = {...} 패턴"""
        pattern = r'```(?:python)?\s*composition\s*=\s*(\{[^}]*\})\s*```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _parse_korean_format(self, text: str) -> Optional[Dict[str, float]]:
        """조성: {dictionary} 형태 (한국어 호환성)"""
        pattern = r'조성\s*[:：]\s*(\{.*?\})'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _parse_generic_dict(self, text: str) -> Optional[Dict[str, float]]:
        """{dictionary} 형태 직접 찾기 (마지막 수단)"""
        pattern = r'\{[^{}]*"[A-Za-z]+"[^{}]*:[^{}]*\d+\.?\d*[^{}]*\}'
        matches = re.findall(pattern, text)
        for match in matches:
            composition = ast.literal_eval(match)
            if isinstance(composition, dict):
                return composition
        return None
    
    def _validate_composition(self, composition: Dict[str, float]) -> Optional[Dict[str, float]]:
        """조성의 유효성을 검증"""
        if not isinstance(composition, dict):
            return None
        
        # 모든 값이 숫자인지 확인
        for element, fraction in composition.items():
            if not isinstance(fraction, (int, float)):
                logger.warning(f"Non-numeric fraction for {element}: {fraction}")
                return None
            if fraction < 0 or fraction > 1:
                logger.warning(f"Invalid fraction for {element}: {fraction}")
                return None
        
        # 비율의 합이 1에 가까운지 확인 (허용 오차: 0.01)
        total = sum(composition.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Composition fractions sum to {total}, not 1.0")
            return None
        
        return composition
    
    def get_format_instructions(self) -> str:
        """파서가 예상하는 출력 형식 지침"""
        return """
Expected output format for composition:

**COMPOSITION:**
composition = {"Element1": fraction1, "Element2": fraction2, ...}

Requirements:
- Use exact Python dictionary syntax
- All fractions must be numbers between 0 and 1
- Fractions must sum to 1.0
- Element names should be valid chemical symbols
- This line must be the final line of your response

Example:
composition = {"Ni": 0.6, "Cu": 0.4}
"""


class MultipleCompositionOutputParser(BaseOutputParser):
    """여러 촉매 조성을 파싱하는 전용 파서"""
    
    def __init__(self, validation: bool = True):
        """
        Args:
            validation: 파싱된 조성의 유효성을 검증할지 여부
        """
        self.validation = validation
        self.single_parser = CompositionOutputParser(validation=validation)
    
    def parse(self, text: str) -> List[Dict[str, float]]:
        """
        LLM 출력에서 여러 조성 정보를 추출합니다.
        
        Args:
            text: LLM의 출력 텍스트
            
        Returns:
            촉매 조성 딕셔너리들의 리스트
        """
        compositions = []
        
        # **COMPOSITIONS:** 섹션에서 여러 조성 찾기
        compositions_section = self._extract_compositions_section(text)
        if compositions_section:
            compositions.extend(self._parse_multiple_compositions(compositions_section))
        
        # 개별 composition_N = {...} 패턴들 찾기
        individual_compositions = self._parse_individual_compositions(text)
        if individual_compositions:
            compositions.extend(individual_compositions)
        
        # 중복 제거 (같은 조성이 여러 번 파싱된 경우)
        unique_compositions = []
        for comp in compositions:
            if comp and comp not in unique_compositions:
                unique_compositions.append(comp)
        
        logger.info(f"Parsed {len(unique_compositions)} unique compositions")
        return unique_compositions
    
    def _extract_compositions_section(self, text: str) -> Optional[str]:
        """**COMPOSITIONS:** 섹션 전체를 추출"""
        pattern = r'\*\*COMPOSITIONS:\*\*\s*\n(.*?)(?=\n\n|\n\[|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _parse_multiple_compositions(self, section_text: str) -> List[Dict[str, float]]:
        """COMPOSITIONS 섹션에서 여러 조성 파싱"""
        compositions = []
        
        # composition_N = {...} 패턴들 찾기
        pattern = r'composition_\d+\s*=\s*(\{[^}]*\})'
        matches = re.findall(pattern, section_text, re.IGNORECASE)
        
        for match in matches:
            try:
                composition = ast.literal_eval(match)
                if isinstance(composition, dict):
                    if self.validation:
                        validated = self._validate_composition(composition)
                        if validated:
                            compositions.append(validated)
                    else:
                        compositions.append(composition)
            except Exception as e:
                logger.debug(f"Failed to parse composition {match}: {e}")
                continue
        
        return compositions
    
    def _parse_individual_compositions(self, text: str) -> List[Dict[str, float]]:
        """개별 composition_N = {...} 라인들을 찾기"""
        compositions = []
        
        # 전체 텍스트에서 composition_N = {...} 패턴 찾기
        pattern = r'composition_\d+\s*=\s*(\{[^}]*\})'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                composition = ast.literal_eval(match)
                if isinstance(composition, dict):
                    if self.validation:
                        validated = self._validate_composition(composition)
                        if validated:
                            compositions.append(validated)
                    else:
                        compositions.append(composition)
            except Exception as e:
                logger.debug(f"Failed to parse individual composition {match}: {e}")
                continue
        
        return compositions
    
    def _validate_composition(self, composition: Dict[str, float]) -> Optional[Dict[str, float]]:
        """조성의 유효성을 검증 (단일 조성용 파서 재사용)"""
        return self.single_parser._validate_composition(composition)
    
    def get_format_instructions(self) -> str:
        """파서가 예상하는 출력 형식 지침"""
        return """
Expected output format for multiple compositions:

**COMPOSITIONS:**
composition_1 = {"Element1": fraction1, "Element2": fraction2, ...}
composition_2 = {"Element1": fraction1, "Element2": fraction2, ...}
composition_3 = {"Element1": fraction1, "Element2": fraction2, ...}
[Add more compositions as needed, up to 5 total]

Requirements:
- Use exact Python dictionary syntax for each composition
- All fractions must be numbers between 0 and 1
- Fractions must sum to 1.0 for each composition
- Element names should be valid chemical symbols
- Compositions should be ordered by predicted performance (best first)
- Include 3-5 compositions unless fewer promising candidates exist

Example:
composition_1 = {"Ni": 0.6, "Cu": 0.4}
composition_2 = {"Ni": 0.7, "Cu": 0.3}
composition_3 = {"Pd": 0.5, "Ag": 0.5}
"""


class EnhancedAnalysisOutputParser(BaseOutputParser):
    """향상된 분석 결과 파서 (여러 조성 지원)"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """전체 구조화된 출력을 파싱 (여러 조성 포함)"""
        result = {
            "analysis": self._extract_analysis(text),
            "recommendations": self._extract_recommendations(text),
            "compositions": MultipleCompositionOutputParser(validation=True).parse(text)
        }
        return result
    
    def _extract_analysis(self, text: str) -> Optional[str]:
        """**ANALYSIS:** 섹션 추출"""
        pattern = r'\*\*ANALYSIS:\*\*\s*\n(.*?)(?=\*\*RECOMMENDATIONS?:\*\*|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_recommendations(self, text: str) -> Optional[str]:
        """**RECOMMENDATIONS:** 섹션 추출 (복수형도 지원)"""
        pattern = r'\*\*RECOMMENDATIONS?:\*\*\s*\n(.*?)(?=\*\*COMPOSITIONS?:\*\*|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def get_format_instructions(self) -> str:
        """전체 구조화된 출력 형식 지침 (여러 조성 지원)"""
        return """
Expected output format:

**ANALYSIS:**
[Detailed scientific reasoning for multiple candidates...]

**RECOMMENDATIONS:**
[Ranked recommendations with supporting evidence for each composition...]

**COMPOSITIONS:**
composition_1 = {"Element1": fraction1, "Element2": fraction2}
composition_2 = {"Element1": fraction1, "Element2": fraction2}
composition_3 = {"Element1": fraction1, "Element2": fraction2}
[Add more as needed, up to 5 total]
"""


class FlexibleOutputParser(BaseOutputParser):
    """여러 파서를 조합한 유연한 파서"""
    
    def __init__(self):
        self.composition_parser = CompositionOutputParser(validation=True)
        self.analysis_parser = EnhancedAnalysisOutputParser()
    
    def parse(self, text: str) -> Dict[str, Any]:
        """가능한 모든 정보를 추출"""
        return {
            "full_analysis": self.analysis_parser.parse(text),
            "composition_only": self.composition_parser.parse(text),
            "raw_text": text
        }
    
    def get_format_instructions(self) -> str:
        return self.analysis_parser.get_format_instructions()


def create_composition_parser(validation: bool = True) -> CompositionOutputParser:
    """CompositionOutputParser 팩토리 함수"""
    return CompositionOutputParser(validation=validation)


def create_multiple_composition_parser(validation: bool = True) -> MultipleCompositionOutputParser:
    """MultipleCompositionOutputParser 팩토리 함수"""
    return MultipleCompositionOutputParser(validation=validation)


def create_analysis_parser() -> EnhancedAnalysisOutputParser:
    """AnalysisOutputParser 팩토리 함수"""
    return EnhancedAnalysisOutputParser()


def create_flexible_parser() -> FlexibleOutputParser:
    """FlexibleOutputParser 팩토리 함수"""
    return FlexibleOutputParser() 