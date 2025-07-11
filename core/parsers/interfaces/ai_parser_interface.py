"""
AI Parser Interface

Specialized interface for AI-powered parsing operations with support for
embeddings, confidence scoring, and advanced AI features.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum

from .parser_interface import (
    IBaseParser,
    ParseRequest,
    ParseResult,
    BatchParseRequest,
    BatchParseResult,
    InputType,
    OutputType,
    ConfigType
)

# AI-specific types
EmbeddingType = TypeVar('EmbeddingType', bound=List[float])
PromptType = TypeVar('PromptType', bound=str)


class AIModelType(Enum):
    """Types of AI models supported."""
    OPENAI_GPT = "openai_gpt"
    OPENAI_EMBEDDING = "openai_embedding"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class AIParseMode(Enum):
    """AI parsing modes."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    STREAMING = "streaming"
    BATCH_OPTIMIZED = "batch_optimized"


class AIParseRequest(ParseRequest[InputType]):
    """
    AI-specific parsing request with additional AI parameters.
    
    Args:
        InputType: Type of input data to parse
    """
    
    model_type: AIModelType = Field(
        default=AIModelType.OPENAI_GPT,
        description="AI model type to use for parsing"
    )
    
    parse_mode: AIParseMode = Field(
        default=AIParseMode.STANDARD,
        description="AI parsing mode"
    )
    
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperature for AI model responses"
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=8000,
        description="Maximum tokens for AI responses"
    )
    
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for AI model"
    )
    
    user_prompt: Optional[str] = Field(
        default=None,
        description="User prompt for AI model"
    )
    
    enable_embeddings: bool = Field(
        default=False,
        description="Whether to generate embeddings"
    )
    
    embedding_model: Optional[str] = Field(
        default=None,
        description="Embedding model to use"
    )
    
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for accepting results"
    )
    
    retry_on_low_confidence: bool = Field(
        default=False,
        description="Whether to retry on low confidence results"
    )
    
    context_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context data for AI model"
    )


class AIParseResult(ParseResult[OutputType]):
    """
    AI-specific parsing result with additional AI metadata.
    
    Args:
        OutputType: Type of parsed output data
    """
    
    model_used: Optional[str] = Field(
        default=None,
        description="AI model used for parsing"
    )
    
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used in AI request"
    )
    
    embeddings: Optional[List[float]] = Field(
        default=None,
        description="Generated embeddings if requested"
    )
    
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI confidence score for the result"
    )
    
    reasoning: Optional[str] = Field(
        default=None,
        description="AI reasoning behind the result"
    )
    
    alternative_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Alternative parsing results with lower confidence"
    )
    
    prompt_used: Optional[str] = Field(
        default=None,
        description="Final prompt used for AI model"
    )
    
    ai_response_raw: Optional[str] = Field(
        default=None,
        description="Raw AI response before processing"
    )
    
    retry_count: int = Field(
        default=0,
        description="Number of retries performed"
    )
    
    cost_estimate: Optional[float] = Field(
        default=None,
        description="Estimated cost of AI operation"
    )


class MaterialParseData(BaseModel):
    """Specific data structure for parsed materials."""
    
    name: str = Field(description="Material name")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    price: Optional[float] = Field(default=None, description="Price per unit")
    color: Optional[str] = Field(default=None, description="Material color")
    coefficient: Optional[float] = Field(default=None, description="Conversion coefficient")
    category: Optional[str] = Field(default=None, description="Material category")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Additional specifications")


class TextParseData(BaseModel):
    """Specific data structure for parsed text."""
    
    extracted_text: str = Field(description="Extracted text content")
    language: Optional[str] = Field(default=None, description="Detected language")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Named entities")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    sentiment: Optional[str] = Field(default=None, description="Sentiment analysis")
    summary: Optional[str] = Field(default=None, description="Text summary")


class IAIParser(IBaseParser[InputType, OutputType, ConfigType]):
    """
    Interface for AI-powered parsers with enhanced capabilities.
    
    This interface extends the base parser interface with AI-specific methods
    for embeddings, confidence scoring, and advanced AI features.
    """
    
    @abstractmethod
    async def parse_with_ai(
        self,
        request: AIParseRequest[InputType]
    ) -> AIParseResult[OutputType]:
        """
        Parse input using AI with enhanced features.
        
        Args:
            request: AI parsing request with AI-specific parameters
            
        Returns:
            AIParseResult: Result with AI-specific metadata
        """
        raise NotImplementedError("Subclasses must implement parse_with_ai method")
    
    @abstractmethod
    async def generate_embeddings(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embeddings for given text.
        
        Args:
            text: Input text to generate embeddings for
            model: Optional specific model to use
            
        Returns:
            List[float]: Generated embedding vector
        """
        raise NotImplementedError("Subclasses must implement generate_embeddings method")
    
    @abstractmethod
    async def validate_confidence(
        self,
        result: AIParseResult[OutputType],
        threshold: float
    ) -> bool:
        """
        Validate if result meets confidence threshold.
        
        Args:
            result: AI parsing result to validate
            threshold: Minimum confidence threshold
            
        Returns:
            bool: True if result meets threshold, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate_confidence method")
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported AI models.
        
        Returns:
            List[str]: List of supported model names
        """
        raise NotImplementedError("Subclasses must implement get_supported_models method")
    
    @abstractmethod
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific AI model.
        
        Args:
            model_name: Name of the AI model
            
        Returns:
            Dict[str, Any]: Model information including capabilities and limits
        """
        raise NotImplementedError("Subclasses must implement get_model_info method")
    
    @abstractmethod
    async def estimate_cost(
        self,
        request: AIParseRequest[InputType]
    ) -> float:
        """
        Estimate the cost of AI parsing operation.
        
        Args:
            request: AI parsing request
            
        Returns:
            float: Estimated cost in USD
        """
        raise NotImplementedError("Subclasses must implement estimate_cost method")
    
    # Optional methods with default implementations
    
    async def optimize_prompt(
        self,
        base_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Optimize prompt for better AI performance.
        
        Args:
            base_prompt: Base prompt to optimize
            context: Additional context for optimization
            
        Returns:
            str: Optimized prompt
        """
        return base_prompt
    
    async def post_process_ai_result(
        self,
        result: AIParseResult[OutputType]
    ) -> AIParseResult[OutputType]:
        """
        Post-process AI parsing result.
        
        Args:
            result: Original AI parsing result
            
        Returns:
            AIParseResult: Post-processed result
        """
        return result
    
    def supports_streaming(self) -> bool:
        """
        Check if parser supports streaming responses.
        
        Returns:
            bool: True if streaming is supported, False otherwise
        """
        return False
    
    def supports_batch_optimization(self) -> bool:
        """
        Check if parser supports batch optimization.
        
        Returns:
            bool: True if batch optimization is supported, False otherwise
        """
        return False
    
    def get_default_temperature(self) -> float:
        """
        Get default temperature for AI model.
        
        Returns:
            float: Default temperature value
        """
        return 0.1
    
    def get_default_max_tokens(self) -> int:
        """
        Get default maximum tokens for AI model.
        
        Returns:
            int: Default maximum tokens
        """
        return 1000


class IMaterialParser(IAIParser[str, MaterialParseData, Dict[str, Any]]):
    """
    Interface for material-specific parsing operations.
    
    Specialized interface for parsing construction materials with
    support for units, prices, colors, and specifications.
    """
    
    @abstractmethod
    async def parse_material(
        self,
        material_text: str,
        unit: Optional[str] = None,
        price: Optional[float] = None
    ) -> AIParseResult[MaterialParseData]:
        """
        Parse material information from text.
        
        Args:
            material_text: Text containing material information
            unit: Optional unit hint
            price: Optional price hint
            
        Returns:
            AIParseResult: Parsed material data
        """
        raise NotImplementedError("Subclasses must implement parse_material method")
    
    @abstractmethod
    async def extract_unit(self, text: str) -> Optional[str]:
        """
        Extract unit of measurement from text.
        
        Args:
            text: Text to extract unit from
            
        Returns:
            Optional[str]: Extracted unit or None if not found
        """
        raise NotImplementedError("Subclasses must implement extract_unit method")
    
    @abstractmethod
    async def extract_color(self, text: str) -> Optional[str]:
        """
        Extract color information from text.
        
        Args:
            text: Text to extract color from
            
        Returns:
            Optional[str]: Extracted color or None if not found
        """
        raise NotImplementedError("Subclasses must implement extract_color method")
    
    @abstractmethod
    async def calculate_coefficient(
        self,
        from_unit: str,
        to_unit: str
    ) -> Optional[float]:
        """
        Calculate conversion coefficient between units.
        
        Args:
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Optional[float]: Conversion coefficient or None if not possible
        """
        raise NotImplementedError("Subclasses must implement calculate_coefficient method")


class ITextParser(IAIParser[str, TextParseData, Dict[str, Any]]):
    """
    Interface for text parsing operations.
    
    Specialized interface for parsing and analyzing text content with
    support for entity extraction, sentiment analysis, and summarization.
    """
    
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List[Dict[str, Any]]: List of extracted entities
        """
        raise NotImplementedError("Subclasses must implement extract_entities method")
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Sentiment classification (positive, negative, neutral)
        """
        raise NotImplementedError("Subclasses must implement analyze_sentiment method")
    
    @abstractmethod
    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """
        Generate summary of text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            str: Generated summary
        """
        raise NotImplementedError("Subclasses must implement summarize_text method")
    
    @abstractmethod
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List[str]: List of extracted keywords
        """
        raise NotImplementedError("Subclasses must implement extract_keywords method")


# Export all AI interface types
__all__ = [
    'EmbeddingType',
    'PromptType',
    'AIModelType',
    'AIParseMode',
    'AIParseRequest',
    'AIParseResult',
    'MaterialParseData',
    'TextParseData',
    'IAIParser',
    'IMaterialParser',
    'ITextParser'
] 