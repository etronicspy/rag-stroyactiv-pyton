"""
Unit Tests for Enhanced Parser Integration

Tests for the enhanced parser integration service that bridges
legacy and new parser architectures.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any, Optional
import asyncio

from services.enhanced_parser_integration import (
    EnhancedParserIntegrationService,
    get_parser_service,
    test_enhanced_parser
)
from core.schemas.enhanced_parsing import (
    EnhancedParseRequest,
    EnhancedParseResult,
    BatchParseRequest,
    BatchParseResponse,
    ParserIntegrationConfig,
    ParsingMethod
)


class TestEnhancedParserIntegrationService:
    """Tests for EnhancedParserIntegrationService"""
    
    def test_initialization_with_new_parsers(self):
        """Test initialization when new parsers are available"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.is_migration_complete', return_value=True), \
             patch('services.enhanced_parser_integration.get_material_parser_service'), \
             patch('services.enhanced_parser_integration.get_batch_parser_service'), \
             patch('services.enhanced_parser_integration.get_parser_config_manager'), \
             patch('services.enhanced_parser_integration.check_parser_availability', return_value={}):
            
            service = EnhancedParserIntegrationService()
            
            assert service.use_new_parsers is True
            assert service.stats["parser_type"] == "new"
            assert service.material_parser is not None
            assert service.batch_parser is not None
            assert service.config_manager is not None
    
    def test_initialization_with_legacy_parsers(self):
        """Test initialization when only legacy parsers are available"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser') as mock_parser:
            
            service = EnhancedParserIntegrationService()
            
            assert service.use_new_parsers is False
            assert service.stats["parser_type"] == "legacy"
            assert service.parser is not None
            mock_parser.assert_called_once()
    
    def test_initialization_no_parsers_available(self):
        """Test initialization when no parsers are available"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', False):
            
            with pytest.raises(RuntimeError, match="No parser system available"):
                EnhancedParserIntegrationService()
    
    def test_initialization_with_config(self):
        """Test initialization with custom configuration"""
        config = ParserIntegrationConfig(
            openai_model="gpt-4",
            confidence_threshold=0.9,
            max_concurrent_requests=5
        )
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService(config)
            
            assert service.config.openai_model == "gpt-4"
            assert service.config.confidence_threshold == 0.9
            assert service.config.max_concurrent_requests == 5
    
    @pytest.mark.asyncio
    async def test_parse_single_material_with_new_parsers(self):
        """Test parsing single material with new parsers"""
        # Mock parse result
        mock_parse_result = Mock()
        mock_parse_result.status = Mock()
        mock_parse_result.status.name = "SUCCESS"
        mock_parse_result.data = Mock()
        mock_parse_result.data.unit_parsed = "м3"
        mock_parse_result.data.price_coefficient = 0.5
        mock_parse_result.data.price_parsed = 50.0
        mock_parse_result.data.color = "красный"
        mock_parse_result.data.embeddings = [0.1, 0.2, 0.3]
        mock_parse_result.data.color_embedding = [0.4, 0.5, 0.6]
        mock_parse_result.data.unit_embedding = [0.7, 0.8, 0.9]
        mock_parse_result.confidence = 0.85
        mock_parse_result.processing_time = 1.5
        
        mock_material_parser = AsyncMock()
        mock_material_parser.parse_material.return_value = mock_parse_result
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.is_migration_complete', return_value=True), \
             patch('services.enhanced_parser_integration.get_material_parser_service', return_value=mock_material_parser), \
             patch('services.enhanced_parser_integration.get_batch_parser_service'), \
             patch('services.enhanced_parser_integration.get_parser_config_manager'), \
             patch('services.enhanced_parser_integration.check_parser_availability', return_value={}), \
             patch('services.enhanced_parser_integration.ParseStatus.SUCCESS', mock_parse_result.status):
            
            service = EnhancedParserIntegrationService()
            
            request = EnhancedParseRequest(
                name="Кирпич красный",
                unit="шт",
                price=25.0,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            result = await service.parse_single_material(request)
            
            assert result.success is True
            assert result.unit_parsed == "м3"
            assert result.color == "красный"
            assert result.confidence == 0.85
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_parse_single_material_with_legacy_parsers(self):
        """Test parsing single material with legacy parsers"""
        # Mock legacy parser result
        mock_legacy_result = {
            "name": "Кирпич красный",
            "original_unit": "шт",
            "original_price": 25.0,
            "unit_parsed": "м3",
            "price_coefficient": 0.5,
            "price_parsed": 50.0,
            "color": "красный",
            "embeddings": [0.1, 0.2, 0.3],
            "parsing_method": "ai_gpt",
            "confidence": 0.8,
            "success": True,
            "processing_time": 1.2
        }
        
        mock_parser = Mock()
        mock_parser.parse_single.return_value = mock_legacy_result
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser', return_value=mock_parser):
            
            service = EnhancedParserIntegrationService()
            
            request = EnhancedParseRequest(
                name="Кирпич красный",
                unit="шт",
                price=25.0,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            result = await service.parse_single_material(request)
            
            assert result.success is True
            assert result.unit_parsed == "м3"
            assert result.color == "красный"
            assert result.confidence == 0.8
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_parse_single_material_error_handling(self):
        """Test error handling in single material parsing"""
        mock_parser = Mock()
        mock_parser.parse_single.side_effect = Exception("Test error")
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser', return_value=mock_parser):
            
            service = EnhancedParserIntegrationService()
            
            request = EnhancedParseRequest(
                name="Кирпич красный",
                unit="шт",
                price=25.0,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            result = await service.parse_single_material(request)
            
            assert result.success is False
            assert result.error_message == "Test error"
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_parse_batch_materials_with_new_parsers(self):
        """Test batch parsing with new parsers"""
        # Mock batch result
        mock_batch_result = Mock()
        mock_batch_result.results = [
            Mock(status=Mock(name="SUCCESS"), data=Mock(unit_parsed="м3", color="красный"), 
                 confidence=0.8, processing_time=1.0),
            Mock(status=Mock(name="SUCCESS"), data=Mock(unit_parsed="кг", color="белый"), 
                 confidence=0.9, processing_time=1.2)
        ]
        
        mock_batch_parser = AsyncMock()
        mock_batch_parser.parse_batch.return_value = mock_batch_result
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.is_migration_complete', return_value=True), \
             patch('services.enhanced_parser_integration.get_material_parser_service'), \
             patch('services.enhanced_parser_integration.get_batch_parser_service', return_value=mock_batch_parser), \
             patch('services.enhanced_parser_integration.get_parser_config_manager'), \
             patch('services.enhanced_parser_integration.check_parser_availability', return_value={}), \
             patch('services.enhanced_parser_integration.ParseStatus.SUCCESS', mock_batch_result.results[0].status):
            
            service = EnhancedParserIntegrationService()
            
            materials = [
                EnhancedParseRequest(name="Кирпич красный", unit="шт", price=25.0),
                EnhancedParseRequest(name="Цемент белый", unit="кг", price=15.0)
            ]
            
            request = BatchParseRequest(
                materials=materials,
                parallel_processing=True,
                max_workers=2
            )
            
            response = await service.parse_batch_materials(request)
            
            assert response.total_processed == 2
            assert response.successful_parses == 2
            assert response.failed_parses == 0
            assert response.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_parse_batch_materials_with_legacy_parsers_parallel(self):
        """Test batch parsing with legacy parsers in parallel mode"""
        # Mock successful parse results
        mock_results = [
            EnhancedParseResult(
                name="Кирпич красный",
                original_unit="шт",
                original_price=25.0,
                unit_parsed="м3",
                color="красный",
                success=True,
                processing_time=1.0
            ),
            EnhancedParseResult(
                name="Цемент белый",
                original_unit="кг",
                original_price=15.0,
                unit_parsed="кг",
                color="белый",
                success=True,
                processing_time=1.2
            )
        ]
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Mock the parse_single_material method to return our mock results
            async def mock_parse_single(request):
                if request.name == "Кирпич красный":
                    return mock_results[0]
                else:
                    return mock_results[1]
            
            service.parse_single_material = mock_parse_single
            
            materials = [
                EnhancedParseRequest(name="Кирпич красный", unit="шт", price=25.0),
                EnhancedParseRequest(name="Цемент белый", unit="кг", price=15.0)
            ]
            
            request = BatchParseRequest(
                materials=materials,
                parallel_processing=True,
                max_workers=2
            )
            
            response = await service.parse_batch_materials(request)
            
            assert response.total_processed == 2
            assert response.successful_parses == 2
            assert response.failed_parses == 0
            assert response.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_parse_batch_materials_with_legacy_parsers_sequential(self):
        """Test batch parsing with legacy parsers in sequential mode"""
        mock_results = [
            EnhancedParseResult(
                name="Кирпич красный",
                original_unit="шт",
                original_price=25.0,
                success=True,
                processing_time=1.0
            ),
            EnhancedParseResult(
                name="Цемент белый",
                original_unit="кг",
                original_price=15.0,
                success=True,
                processing_time=1.2
            )
        ]
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Mock the parse_single_material method
            async def mock_parse_single(request):
                if request.name == "Кирпич красный":
                    return mock_results[0]
                else:
                    return mock_results[1]
            
            service.parse_single_material = mock_parse_single
            
            materials = [
                EnhancedParseRequest(name="Кирпич красный", unit="шт", price=25.0),
                EnhancedParseRequest(name="Цемент белый", unit="кг", price=15.0)
            ]
            
            request = BatchParseRequest(
                materials=materials,
                parallel_processing=False,
                max_workers=1
            )
            
            response = await service.parse_batch_materials(request)
            
            assert response.total_processed == 2
            assert response.successful_parses == 2
            assert response.failed_parses == 0
            assert response.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_parse_batch_materials_with_errors(self):
        """Test batch parsing with some errors"""
        mock_results = [
            EnhancedParseResult(
                name="Кирпич красный",
                original_unit="шт",
                original_price=25.0,
                success=True,
                processing_time=1.0
            ),
            EnhancedParseResult(
                name="Цемент белый",
                original_unit="кг",
                original_price=15.0,
                success=False,
                error_message="Parse error",
                processing_time=0.5
            )
        ]
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Mock the parse_single_material method
            async def mock_parse_single(request):
                if request.name == "Кирпич красный":
                    return mock_results[0]
                else:
                    return mock_results[1]
            
            service.parse_single_material = mock_parse_single
            
            materials = [
                EnhancedParseRequest(name="Кирпич красный", unit="шт", price=25.0),
                EnhancedParseRequest(name="Цемент белый", unit="кг", price=15.0)
            ]
            
            request = BatchParseRequest(
                materials=materials,
                parallel_processing=False,
                max_workers=1
            )
            
            response = await service.parse_batch_materials(request)
            
            assert response.total_processed == 2
            assert response.successful_parses == 1
            assert response.failed_parses == 1
            assert response.success_rate == 50.0
    
    def test_get_statistics_with_new_parsers(self):
        """Test getting statistics with new parsers"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.is_migration_complete', return_value=True), \
             patch('services.enhanced_parser_integration.get_material_parser_service') as mock_material, \
             patch('services.enhanced_parser_integration.get_batch_parser_service') as mock_batch, \
             patch('services.enhanced_parser_integration.get_parser_config_manager') as mock_config, \
             patch('services.enhanced_parser_integration.check_parser_availability', return_value={}):
            
            # Mock statistics methods
            mock_material.return_value.get_statistics.return_value = {"material_stats": "data"}
            mock_batch.return_value.get_statistics.return_value = {"batch_stats": "data"}
            mock_config.return_value.get_statistics.return_value = {"config_stats": "data"}
            
            service = EnhancedParserIntegrationService()
            
            stats = service.get_statistics()
            
            assert stats["service_type"] == "enhanced_parser_integration"
            assert stats["parser_architecture"] == "new"
            assert "integration_stats" in stats
            assert "material_parser_stats" in stats
            assert "batch_parser_stats" in stats
            assert "config_manager_stats" in stats
    
    def test_get_statistics_with_legacy_parsers(self):
        """Test getting statistics with legacy parsers"""
        mock_parser = Mock()
        mock_parser.get_statistics.return_value = {"legacy_stats": "data"}
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser', return_value=mock_parser):
            
            service = EnhancedParserIntegrationService()
            
            stats = service.get_statistics()
            
            assert stats["service_type"] == "enhanced_parser_integration"
            assert stats["parser_architecture"] == "legacy"
            assert "integration_stats" in stats
            assert "legacy_parser_stats" in stats
    
    def test_clear_statistics(self):
        """Test clearing statistics"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Add some stats
            service.stats["total_requests"] = 10
            service.stats["successful_parses"] = 8
            service.stats["failed_parses"] = 2
            
            # Clear stats
            service.clear_statistics()
            
            # Verify stats were cleared
            assert service.stats["total_requests"] == 0
            assert service.stats["successful_parses"] == 0
            assert service.stats["failed_parses"] == 0
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Mock successful parsing
            async def mock_parse_single(request):
                return EnhancedParseResult(
                    name=request.name,
                    original_unit=request.unit,
                    original_price=request.price,
                    success=True,
                    processing_time=0.1
                )
            
            service.parse_single_material = mock_parse_single
            
            result = await service.test_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test failed connection test"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            # Mock failed parsing
            async def mock_parse_single(request):
                raise Exception("Connection failed")
            
            service.parse_single_material = mock_parse_single
            
            result = await service.test_connection()
            assert result is False
    
    def test_get_parser_info_with_new_parsers(self):
        """Test getting parser info with new parsers"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.is_migration_complete', return_value=True), \
             patch('services.enhanced_parser_integration.get_material_parser_service'), \
             patch('services.enhanced_parser_integration.get_batch_parser_service'), \
             patch('services.enhanced_parser_integration.get_parser_config_manager') as mock_config, \
             patch('services.enhanced_parser_integration.check_parser_availability', return_value={"ai_parser": True}):
            
            mock_config.return_value.current_profile = "development"
            
            service = EnhancedParserIntegrationService()
            
            info = service.get_parser_info()
            
            assert info["architecture"] == "new"
            assert info["migration_complete"] is True
            assert "config" in info
            assert "parser_availability" in info
            assert "current_profile" in info
            assert info["current_profile"] == "development"
    
    def test_get_parser_info_with_legacy_parsers(self):
        """Test getting parser info with legacy parsers"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = EnhancedParserIntegrationService()
            
            info = service.get_parser_info()
            
            assert info["architecture"] == "legacy"
            assert info["migration_complete"] is False
            assert "config" in info
            assert "parser_availability" not in info
            assert "current_profile" not in info


class TestServiceFactory:
    """Tests for service factory function"""
    
    def test_get_parser_service_default_config(self):
        """Test getting parser service with default config"""
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = get_parser_service()
            
            assert isinstance(service, EnhancedParserIntegrationService)
            assert service.config is not None
    
    def test_get_parser_service_custom_config(self):
        """Test getting parser service with custom config"""
        config = ParserIntegrationConfig(
            openai_model="gpt-4",
            confidence_threshold=0.9
        )
        
        with patch('services.enhanced_parser_integration.NEW_PARSERS_AVAILABLE', False), \
             patch('services.enhanced_parser_integration.LEGACY_PARSERS_AVAILABLE', True), \
             patch('services.enhanced_parser_integration.MaterialParser'):
            
            service = get_parser_service(config)
            
            assert isinstance(service, EnhancedParserIntegrationService)
            assert service.config.openai_model == "gpt-4"
            assert service.config.confidence_threshold == 0.9


class TestIntegrationFunction:
    """Tests for integration testing function"""
    
    @pytest.mark.asyncio
    async def test_test_enhanced_parser_success(self):
        """Test successful enhanced parser test"""
        with patch('services.enhanced_parser_integration.get_parser_service') as mock_get_service:
            mock_service = Mock()
            mock_service.test_connection = AsyncMock(return_value=True)
            mock_service.parse_batch_materials = AsyncMock(return_value=BatchParseResponse(
                results=[],
                total_processed=2,
                successful_parses=2,
                failed_parses=0,
                success_rate=100.0,
                total_processing_time=1.0
            ))
            
            mock_get_service.return_value = mock_service
            
            result = await test_enhanced_parser()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_enhanced_parser_connection_failure(self):
        """Test enhanced parser test with connection failure"""
        with patch('services.enhanced_parser_integration.get_parser_service') as mock_get_service:
            mock_service = Mock()
            mock_service.test_connection = AsyncMock(return_value=False)
            
            mock_get_service.return_value = mock_service
            
            result = await test_enhanced_parser()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_test_enhanced_parser_batch_failure(self):
        """Test enhanced parser test with batch processing failure"""
        with patch('services.enhanced_parser_integration.get_parser_service') as mock_get_service:
            mock_service = Mock()
            mock_service.test_connection = AsyncMock(return_value=True)
            mock_service.parse_batch_materials = AsyncMock(return_value=BatchParseResponse(
                results=[],
                total_processed=2,
                successful_parses=0,
                failed_parses=2,
                success_rate=0.0,
                total_processing_time=1.0
            ))
            
            mock_get_service.return_value = mock_service
            
            result = await test_enhanced_parser()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_test_enhanced_parser_exception(self):
        """Test enhanced parser test with exception"""
        with patch('services.enhanced_parser_integration.get_parser_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Test exception")
            
            result = await test_enhanced_parser()
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__]) 