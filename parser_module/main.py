"""
Main Entry Point for AI Material Parser

This module provides command-line interface and testing capabilities 
for the AI-powered material parser.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
try:
    # Try relative imports (when imported as module)
    from .material_parser import MaterialParser, create_parser
    from .parser_config import get_config
except ImportError:
    # Fall back to absolute imports (when run as script)
    from material_parser import MaterialParser, create_parser
    from parser_config import get_config


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("parser.log")
        ]
    )


def parse_single_material(name: str, unit: str, price: float, env: str = "default", 
                          enable_embeddings: bool = True, embeddings_model: str = "text-embedding-3-small") -> Dict[str, Any]:
    """Parse a single material"""
    print(f"\n🔍 Parsing material: {name}")
    print(f"   Original unit: {unit}")
    print(f"   Original price: {price}")
    
    try:
        config = get_config(env)
        # Apply embeddings settings
        config.embeddings_enabled = enable_embeddings
        config.embeddings_model = embeddings_model
        
        parser = MaterialParser(config, env)
        result = parser.parse_single(name, unit, price)
        
        print(f"\n✅ Parsing Result:")
        print(f"   Unit parsed: {result.get('unit_parsed', 'N/A')}")
        print(f"   Price coefficient: {result.get('price_coefficient', 'N/A')}")
        print(f"   Price parsed: {result.get('price_parsed', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Processing time: {result.get('processing_time', 0.0):.3f}s")
        
        if result.get('error_message'):
            print(f"   Error: {result.get('error_message')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error parsing material: {e}")
        return {}


def parse_file(file_path: str, output_path: str = None, env: str = "default",
               enable_embeddings: bool = True, embeddings_model: str = "text-embedding-3-small"):
    """Parse materials from file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"\n📁 Parsing materials from file: {file_path}")
    
    try:
        config = get_config(env)
        # Apply embeddings settings
        config.embeddings_enabled = enable_embeddings
        config.embeddings_model = embeddings_model
        
        parser = MaterialParser(config, env)
        results = parser.parse_from_file(file_path)
        
        # Print summary
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"\n📊 Parsing Summary:")
        print(f"   Total materials: {total}")
        print(f"   Successful parses: {successful}")
        print(f"   Failed parses: {total - successful}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        # Show sample results
        print(f"\n🔍 Sample Results:")
        for i, result in enumerate(results[:5]):  # Show first 5 results
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {i+1}. {status} {result.get('name', 'Unknown')}")
            print(f"      {result.get('unit_parsed', 'N/A')} (coeff: {result.get('price_coefficient', 'N/A')})")
        
        if total > 5:
            print(f"   ... and {total - 5} more materials")
        
        # Save results if output path provided
        if output_path:
            output_path = Path(output_path)
            parser.save_results(results, output_path)
            print(f"\n💾 Results saved to: {output_path}")
        
        # Show statistics
        stats = parser.get_statistics()
        print(f"\n📈 Parser Statistics:")
        print(f"   Cache size: {stats.get('cache_size', 0)}")
        print(f"   AI success rate: {stats.get('ai_success_rate', 0):.3f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return []


def run_demo():
    """Run demonstration with sample materials"""
    print("🚀 AI Material Parser Demo")
    print("=" * 50)
    
    # Sample materials from test file
    sample_materials = [
        {"name": "Цемент 50кг", "unit": "меш", "price": 300.0},
        {"name": "Кирпич шамотный огнеупорный ШБ-8 (250x120x65)", "unit": "шт", "price": 47.0},
        {"name": "Газобетон 600x300x200 1шт D500", "unit": "шт", "price": 95.0},
        {"name": "Базальтовый утеплитель (насыпной) 1 упак. 0,5 м³", "unit": "шт", "price": 460.0},
        {"name": "Проволока вязальная ст. низкоуглерод. т/о 5кг", "unit": "кг", "price": 60.0}
    ]
    
    print("🔍 Parsing sample materials...")
    
    try:
        parser = create_parser("development")
        results = parser.parse_batch(sample_materials)
        
        print(f"\n📊 Demo Results:")
        for i, result in enumerate(results):
            status = "✅" if result.get('success', False) else "❌"
            print(f"\n{i+1}. {status} {result.get('name', 'Unknown')}")
            print(f"   Original: {result.get('original_unit', 'N/A')} @ {result.get('original_price', 0.0)}")
            print(f"   Parsed: {result.get('unit_parsed', 'N/A')} (coeff: {result.get('price_coefficient', 'N/A')})")
            print(f"   Price per unit: {result.get('price_parsed', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            
            if result.get('error_message'):
                print(f"   Error: {result.get('error_message')}")
        
        # Show statistics
        stats = parser.get_statistics()
        print(f"\n📈 Final Statistics:")
        print(f"   Total processed: {stats.get('total_processed', 0)}")
        print(f"   Success rate: {stats.get('success_rate', 0):.3f}")
        print(f"   Cache size: {stats.get('cache_size', 0)}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


def test_configuration():
    """Test different configurations"""
    print("\n🔧 Testing Configurations")
    print("=" * 30)
    
    environments = ["default", "development", "production"]
    
    for env in environments:
        print(f"\n🔍 Testing {env} configuration...")
        try:
            config = get_config(env)
            print(f"   Model: {config.openai_model}")
            print(f"   Temperature: {config.openai_temperature}")
            print(f"   Max tokens: {config.openai_max_tokens}")
            print(f"   Timeout: {config.openai_timeout}")
            print(f"   ✅ Configuration valid")
        except Exception as e:
            print(f"   ❌ Configuration error: {e}")


def create_example_file():
    """Create example data file"""
    example_path = Path("example_materials.json")
    
    print(f"\n📝 Creating example file: {example_path}")
    
    try:
        parser = create_parser()
        parser.create_example_data(example_path)
        print(f"✅ Example file created successfully")
        return str(example_path)
    except Exception as e:
        print(f"❌ Error creating example file: {e}")
        return None


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description="AI-powered material parser for construction materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse single material
  python main.py single "Цемент 50кг" "меш" 300.0
  
  # Parse from file with embeddings
  python main.py file test_materials_image.json -o results.json
  
  # Parse without embeddings (faster)
  python main.py file test_materials_image.json --no-embeddings
  
  # Parse with custom embeddings model
  python main.py file test_materials_image.json --embeddings-model text-embedding-3-large
  
  # Run demo
  python main.py demo
  
  # Test configurations
  python main.py test-config
  
  # Create example file
  python main.py create-example
"""
    )
    
    parser.add_argument(
        "command",
        choices=["single", "file", "demo", "test-config", "create-example"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the command"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path for results"
    )
    
    parser.add_argument(
        "-e", "--env",
        default="default",
        choices=["default", "development", "production", "integration"],
        help="Environment configuration"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Disable embeddings generation"
    )
    
    parser.add_argument(
        "--embeddings-model",
        default="text-embedding-3-small",
        help="OpenAI embeddings model to use"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # Execute command
    if args.command == "single":
        if len(args.args) < 3:
            print("❌ Single command requires: name unit price")
            return
        
        name, unit, price = args.args[0], args.args[1], float(args.args[2])
        result = parse_single_material(
            name, unit, price, args.env,
            enable_embeddings=not args.no_embeddings,
            embeddings_model=args.embeddings_model
        )
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Result saved to: {output_path}")
    
    elif args.command == "file":
        if len(args.args) < 1:
            print("❌ File command requires: file_path")
            return
        
        file_path = args.args[0]
        parse_file(
            file_path, args.output, args.env,
            enable_embeddings=not args.no_embeddings,
            embeddings_model=args.embeddings_model
        )
    
    elif args.command == "demo":
        run_demo()
    
    elif args.command == "test-config":
        test_configuration()
    
    elif args.command == "create-example":
        create_example_file()
    
    print("\n🎉 Parser execution completed!")


if __name__ == "__main__":
    main() 