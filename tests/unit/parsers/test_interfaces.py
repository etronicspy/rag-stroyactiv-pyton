"""
Unit Tests for Parser Interfaces

Tests for ABC interfaces and type definitions in core.parsers.interfaces
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass

from core.parsers.interfaces import (
    # Base types
    InputType,
    OutputType,
    ConfigType,
    ParseStatus,
    ParseResult,
    ParseRequest,
    BatchParseRequest,
    BatchParseResult,
    
    # Base interfaces
    IBaseParser,
    IParserHealthCheck,
    IParserConfig,
    IParserMetrics,
    
    # AI interfaces
    IAIParser,
    IMaterialParser,
    ITextParser,
    
    # AI types
    AIModelType,
    AIParseMode,
    AIParseRequest,
    AIParseResult,
    MaterialParseData,
    TextParseData,
    
    # Utility functions
    get_interface_info,
    list_available_interfaces,
    validate_interface_implementation
)


class TestParseStatus:
    """Tests for ParseStatus enum"""
    
    def test_parse_status_values(self):
        """Test that ParseStatus has expected values"""
        assert ParseStatus.SUCCESS.value == "success"
        assert ParseStatus.PARTIAL.value == "partial"
        assert ParseStatus.ERROR.value == "error"
        assert ParseStatus.TIMEOUT.value == "timeout"
    
    def test_parse_status_comparison(self):
        """Test ParseStatus comparison operations"""
        assert ParseStatus.SUCCESS == ParseStatus.SUCCESS
        assert ParseStatus.SUCCESS != ParseStatus.ERROR
        assert str(ParseStatus.SUCCESS) == "ParseStatus.SUCCESS"


class TestAIModelType:
    """Tests for AIModelType enum"""
    
    def test_ai_model_type_values(self):
        """Test that AIModelType has expected values"""
        assert AIModelType.GPT4O_MINI.value == "gpt-4o-mini"
        assert AIModelType.GPT4.value == "gpt-4"
        assert AIModelType.GPT3_5_TURBO.value == "gpt-3.5-turbo"
    
    def test_ai_model_type_default(self):
        """Test default AI model type"""
        assert AIModelType.get_default() == AIModelType.GPT4O_MINI


class TestAIParseMode:
    """Tests for AIParseMode enum"""
    
    def test_ai_parse_mode_values(self):
        """Test that AIParseMode has expected values"""
        assert AIParseMode.STANDARD.value == "standard"
        assert AIParseMode.STRICT.value == "strict"
        assert AIParseMode.CREATIVE.value == "creative"
    
    def test_ai_parse_mode_default(self):
        """Test default AI parse mode"""
        assert AIParseMode.get_default() == AIParseMode.STANDARD


class TestDataClasses:
    """Tests for data classes"""
    
    def test_material_parse_data_creation(self):
        """Test MaterialParseData creation"""
        data = MaterialParseData(
            name="Кирпич красный",
            original_unit="шт",
            original_price=25.0
        )
        
        assert data.name == "Кирпич красный"
        assert data.original_unit == "шт"
        assert data.original_price == 25.0
        assert data.unit_parsed is None
        assert data.price_coefficient is None
        assert data.color is None
    
    def test_material_parse_data_with_parsed_values(self):
        """Test MaterialParseData with parsed values"""
        data = MaterialParseData(
            name="Кирпич красный",
            original_unit="шт",
            original_price=25.0,
            unit_parsed="м3",
            price_coefficient=0.00195,
            color="красный",
            parsing_method="ai_gpt",
            confidence=0.9
        )
        
        assert data.unit_parsed == "м3"
        assert data.price_coefficient == 0.00195
        assert data.color == "красный"
        assert data.parsing_method == "ai_gpt"
        assert data.confidence == 0.9
    
    def test_text_parse_data_creation(self):
        """Test TextParseData creation"""
        data = TextParseData(
            original_text="Test text",
            language="russian"
        )
        
        assert data.original_text == "Test text"
        assert data.language == "russian"
        assert data.extracted_entities == []
        assert data.sentiment is None
    
    def test_parse_request_creation(self):
        """Test ParseRequest creation"""
        request = ParseRequest(
            input_data="Test input",
            request_id="test_123",
            options={"enable_debug": True}
        )
        
        assert request.input_data == "Test input"
        assert request.request_id == "test_123"
        assert request.options == {"enable_debug": True}
    
    def test_ai_parse_request_creation(self):
        """Test AIParseRequest creation"""
        request = AIParseRequest(
            input_data="Кирпич красный",
            request_id="ai_test_123",
            model_type=AIModelType.GPT4O_MINI,
            parse_mode=AIParseMode.STANDARD,
            options={"enable_embeddings": True}
        )
        
        assert request.input_data == "Кирпич красный"
        assert request.request_id == "ai_test_123"
        assert request.model_type == AIModelType.GPT4O_MINI
        assert request.parse_mode == AIParseMode.STANDARD
        assert request.options["enable_embeddings"] is True
    
    def test_parse_result_creation(self):
        """Test ParseResult creation"""
        data = MaterialParseData(
            name="Test material",
            original_unit="шт",
            original_price=100.0
        )
        
        result = ParseResult(
            status=ParseStatus.SUCCESS,
            data=data,
            confidence=0.8,
            processing_time=1.5,
            request_id="test_123"
        )
        
        assert result.status == ParseStatus.SUCCESS
        assert result.data == data
        assert result.confidence == 0.8
        assert result.processing_time == 1.5
        assert result.request_id == "test_123"
        assert result.error_message is None
    
    def test_ai_parse_result_creation(self):
        """Test AIParseResult creation"""
        data = MaterialParseData(
            name="Test material",
            original_unit="шт", 
            original_price=100.0
        )
        
        result = AIParseResult(
            status=ParseStatus.SUCCESS,
            data=data,
            confidence=0.85,
            processing_time=2.0,
            request_id="ai_test_123",
            model_used=AIModelType.GPT4O_MINI,
            tokens_used=150
        )
        
        assert result.status == ParseStatus.SUCCESS
        assert result.data == data
        assert result.confidence == 0.85
        assert result.processing_time == 2.0
        assert result.request_id == "ai_test_123"
        assert result.model_used == AIModelType.GPT4O_MINI
        assert result.tokens_used == 150
    
    def test_batch_parse_request_creation(self):
        """Test BatchParseRequest creation"""
        requests = [
            ParseRequest("Input 1", "req_1"),
            ParseRequest("Input 2", "req_2")
        ]
        
        batch_request = BatchParseRequest(
            requests=requests,
            parallel_processing=True,
            max_workers=2
        )
        
        assert len(batch_request.requests) == 2
        assert batch_request.parallel_processing is True
        assert batch_request.max_workers == 2
    
    def test_batch_parse_result_creation(self):
        """Test BatchParseResult creation"""
        data1 = MaterialParseData("Material 1", "шт", 100.0)
        data2 = MaterialParseData("Material 2", "кг", 50.0)
        
        results = [
            ParseResult(ParseStatus.SUCCESS, data1, 0.9, 1.0, "req_1"),
            ParseResult(ParseStatus.SUCCESS, data2, 0.8, 1.2, "req_2")
        ]
        
        batch_result = BatchParseResult(
            results=results,
            total_processed=2,
            successful_count=2,
            failed_count=0,
            success_rate=100.0,
            processing_time=2.5
        )
        
        assert len(batch_result.results) == 2
        assert batch_result.total_processed == 2
        assert batch_result.successful_count == 2
        assert batch_result.failed_count == 0
        assert batch_result.success_rate == 100.0
        assert batch_result.processing_time == 2.5


class TestConcreteParser(IBaseParser[str, MaterialParseData]):
    """Concrete implementation for testing IBaseParser"""
    
    async def parse_request(self, request: ParseRequest[str]) -> ParseResult[MaterialParseData]:
        """Test implementation of parse_request"""
        data = MaterialParseData(
            name=request.input_data,
            original_unit="шт",
            original_price=0.0
        )
        
        return ParseResult(
            status=ParseStatus.SUCCESS,
            data=data,
            confidence=1.0,
            processing_time=0.1,
            request_id=request.request_id
        )
    
    def is_healthy(self) -> bool:
        """Test implementation of is_healthy"""
        return True


class TestConcreteAIParser(IAIParser[str, MaterialParseData]):
    """Concrete implementation for testing IAIParser"""
    
    async def parse_request(self, request: AIParseRequest[str]) -> AIParseResult[MaterialParseData]:
        """Test implementation of parse_request"""
        data = MaterialParseData(
            name=request.input_data,
            original_unit="шт",
            original_price=0.0
        )
        
        return AIParseResult(
            status=ParseStatus.SUCCESS,
            data=data,
            confidence=0.9,
            processing_time=0.5,
            request_id=request.request_id,
            model_used=request.model_type,
            tokens_used=100
        )
    
    def is_healthy(self) -> bool:
        """Test implementation of is_healthy"""
        return True


class TestConcreteMaterialParser(IMaterialParser[str, MaterialParseData]):
    """Concrete implementation for testing IMaterialParser"""
    
    async def parse_material(self, material_text: str) -> AIParseResult[MaterialParseData]:
        """Test implementation of parse_material"""
        data = MaterialParseData(
            name=material_text,
            original_unit="шт",
            original_price=0.0
        )
        
        return AIParseResult(
            status=ParseStatus.SUCCESS,
            data=data,
            confidence=0.8,
            processing_time=0.3,
            request_id="material_test"
        )
    
    async def extract_unit(self, text: str) -> Optional[str]:
        """Test implementation of extract_unit"""
        if "кг" in text:
            return "кг"
        elif "м" in text:
            return "м"
        return "шт"
    
    async def extract_color(self, text: str) -> Optional[str]:
        """Test implementation of extract_color"""
        colors = ["красный", "белый", "синий", "зеленый"]
        for color in colors:
            if color in text.lower():
                return color
        return None
    
    def is_healthy(self) -> bool:
        """Test implementation of is_healthy"""
        return True


class TestInterfaceImplementations:
    """Tests for interface implementations"""
    
    def test_base_parser_implementation(self):
        """Test IBaseParser implementation"""
        parser = TestConcreteParser()
        assert parser.is_healthy() is True
        
        # Test that the parser implements the interface correctly
        assert hasattr(parser, 'parse_request')
        assert hasattr(parser, 'is_healthy')
    
    @pytest.mark.asyncio
    async def test_base_parser_parse_request(self):
        """Test IBaseParser parse_request method"""
        parser = TestConcreteParser()
        
        request = ParseRequest(
            input_data="Test material",
            request_id="test_123"
        )
        
        result = await parser.parse_request(request)
        
        assert result.status == ParseStatus.SUCCESS
        assert result.data.name == "Test material"
        assert result.confidence == 1.0
        assert result.request_id == "test_123"
    
    def test_ai_parser_implementation(self):
        """Test IAIParser implementation"""
        parser = TestConcreteAIParser()
        assert parser.is_healthy() is True
        
        # Test that the parser implements the interface correctly
        assert hasattr(parser, 'parse_request')
        assert hasattr(parser, 'is_healthy')
    
    @pytest.mark.asyncio
    async def test_ai_parser_parse_request(self):
        """Test IAIParser parse_request method"""
        parser = TestConcreteAIParser()
        
        request = AIParseRequest(
            input_data="Кирпич красный",
            request_id="ai_test_123",
            model_type=AIModelType.GPT4O_MINI
        )
        
        result = await parser.parse_request(request)
        
        assert result.status == ParseStatus.SUCCESS
        assert result.data.name == "Кирпич красный"
        assert result.confidence == 0.9
        assert result.model_used == AIModelType.GPT4O_MINI
        assert result.tokens_used == 100
    
    def test_material_parser_implementation(self):
        """Test IMaterialParser implementation"""
        parser = TestConcreteMaterialParser()
        assert parser.is_healthy() is True
        
        # Test that the parser implements the interface correctly
        assert hasattr(parser, 'parse_material')
        assert hasattr(parser, 'extract_unit')
        assert hasattr(parser, 'extract_color')
        assert hasattr(parser, 'is_healthy')
    
    @pytest.mark.asyncio
    async def test_material_parser_parse_material(self):
        """Test IMaterialParser parse_material method"""
        parser = TestConcreteMaterialParser()
        
        result = await parser.parse_material("Кирпич красный облицовочный")
        
        assert result.status == ParseStatus.SUCCESS
        assert result.data.name == "Кирпич красный облицовочный"
        assert result.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_material_parser_extract_unit(self):
        """Test IMaterialParser extract_unit method"""
        parser = TestConcreteMaterialParser()
        
        # Test different units
        assert await parser.extract_unit("цемент 50 кг") == "кг"
        assert await parser.extract_unit("доска 2 м") == "м"
        assert await parser.extract_unit("кирпич") == "шт"
    
    @pytest.mark.asyncio
    async def test_material_parser_extract_color(self):
        """Test IMaterialParser extract_color method"""
        parser = TestConcreteMaterialParser()
        
        # Test color extraction
        assert await parser.extract_color("кирпич красный") == "красный"
        assert await parser.extract_color("плитка белая") == "белый"
        assert await parser.extract_color("кирпич обычный") is None


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_get_interface_info(self):
        """Test get_interface_info function"""
        info = get_interface_info("IBaseParser")
        
        assert info is not None
        assert "description" in info
        assert "methods" in info
        assert "type_parameters" in info
    
    def test_list_available_interfaces(self):
        """Test list_available_interfaces function"""
        interfaces = list_available_interfaces()
        
        assert isinstance(interfaces, list)
        assert len(interfaces) > 0
        assert "IBaseParser" in interfaces
        assert "IAIParser" in interfaces
        assert "IMaterialParser" in interfaces
    
    def test_validate_interface_implementation_valid(self):
        """Test validate_interface_implementation with valid implementation"""
        is_valid = validate_interface_implementation(TestConcreteParser, "IBaseParser")
        assert is_valid is True
        
        is_valid = validate_interface_implementation(TestConcreteAIParser, "IAIParser")
        assert is_valid is True
        
        is_valid = validate_interface_implementation(TestConcreteMaterialParser, "IMaterialParser")
        assert is_valid is True
    
    def test_validate_interface_implementation_invalid(self):
        """Test validate_interface_implementation with invalid implementation"""
        # Test with a class that doesn't implement the interface
        class InvalidParser:
            pass
        
        is_valid = validate_interface_implementation(InvalidParser, "IBaseParser")
        assert is_valid is False
    
    def test_validate_interface_implementation_unknown_interface(self):
        """Test validate_interface_implementation with unknown interface"""
        is_valid = validate_interface_implementation(TestConcreteParser, "IUnknownParser")
        assert is_valid is False


class TestErrorHandling:
    """Tests for error handling in interfaces"""
    
    def test_parse_result_with_error(self):
        """Test ParseResult with error status"""
        result = ParseResult(
            status=ParseStatus.ERROR,
            data=None,
            confidence=0.0,
            processing_time=0.1,
            error_message="Test error message",
            request_id="error_test"
        )
        
        assert result.status == ParseStatus.ERROR
        assert result.data is None
        assert result.confidence == 0.0
        assert result.error_message == "Test error message"
    
    def test_ai_parse_result_with_timeout(self):
        """Test AIParseResult with timeout status"""
        result = AIParseResult(
            status=ParseStatus.TIMEOUT,
            data=None,
            confidence=0.0,
            processing_time=30.0,
            error_message="Request timed out",
            request_id="timeout_test"
        )
        
        assert result.status == ParseStatus.TIMEOUT
        assert result.error_message == "Request timed out"
        assert result.processing_time == 30.0


if __name__ == "__main__":
    pytest.main([__file__]) 