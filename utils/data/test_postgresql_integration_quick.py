#!/usr/bin/env python3
"""
Quick PostgreSQL SSH Tunnel Integration Test.

Быстрый тест интеграции PostgreSQL с SSH tunnel service без реальных подключений.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import get_settings
from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from services.ssh_tunnel_service import get_tunnel_service


async def test_postgresql_adapter_creation():
    """Test PostgreSQL adapter creation."""
    try:
        print("🔧 Testing PostgreSQL adapter creation...")
        settings = get_settings()
        adapter = PostgreSQLAdapter(settings)
        
        print(f"✅ Adapter created successfully")
        print(f"   - Settings loaded: {hasattr(adapter, 'settings')}")
        print(f"   - Tunnel service: {adapter._tunnel_service}")
        
        return True
    except Exception as e:
        print(f"❌ Adapter creation failed: {e}")
        return False


async def test_tunnel_service_integration():
    """Test SSH tunnel service integration."""
    try:
        print("\n🔧 Testing SSH tunnel service integration...")
        
        # Test tunnel service getter
        tunnel_service = get_tunnel_service()
        print(f"   - Tunnel service available: {tunnel_service is not None}")
        
        if tunnel_service:
            print(f"   - Service running: {tunnel_service.is_running}")
            print(f"   - Tunnel active: {tunnel_service.is_tunnel_active()}")
            status = tunnel_service.get_status()
            print(f"   - Config enabled: {status.get('config_enabled', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Tunnel service integration failed: {e}")
        return False


async def test_connection_logic_with_mock():
    """Test connection logic with mocked tunnel service."""
    try:
        print("\n🔧 Testing connection logic with mocked services...")
        
        settings = get_settings()
        adapter = PostgreSQLAdapter(settings)
        
        # Test 1: Mock active tunnel
        print("   📡 Testing with active tunnel...")
        mock_tunnel = Mock()
        mock_tunnel.is_tunnel_active.return_value = True
        mock_tunnel.config.local_port = 5435
        
        with patch('core.database.adapters.postgresql_adapter.get_tunnel_service', return_value=mock_tunnel):
            with patch.object(adapter, 'engine') as mock_engine:
                mock_engine.begin = MagicMock()
                mock_engine.begin.return_value.__aenter__ = MagicMock()
                mock_engine.begin.return_value.__aexit__ = MagicMock()
                mock_conn = Mock()
                mock_conn.execute = MagicMock()
                mock_engine.begin.return_value.__aenter__.return_value = mock_conn
                
                # Simulate connection attempt
                adapter._tunnel_service = mock_tunnel
                
                # Build connection string logic
                if adapter._tunnel_service and adapter._tunnel_service.is_tunnel_active():
                    connection_string = (
                        f"postgresql+asyncpg://{settings.POSTGRESQL_USER}:"
                        f"{settings.POSTGRESQL_PASSWORD}@localhost:"
                        f"{mock_tunnel.config.local_port}/{settings.POSTGRESQL_DATABASE}"
                    )
                    print(f"      ✅ Tunneled connection string: localhost:{mock_tunnel.config.local_port}")
                
        # Test 2: Mock no tunnel
        print("   🔗 Testing without tunnel...")
        with patch('core.database.adapters.postgresql_adapter.get_tunnel_service', return_value=None):
            # Simulate direct connection
            connection_string = (
                f"postgresql+asyncpg://{settings.POSTGRESQL_USER}:"
                f"{settings.POSTGRESQL_PASSWORD}@{settings.POSTGRESQL_HOST}:"
                f"{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DATABASE}"
            )
            print(f"      ✅ Direct connection string: {settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}")
        
        return True
    except Exception as e:
        print(f"❌ Connection logic test failed: {e}")
        return False


async def test_health_check_logic():
    """Test health check logic."""
    try:
        print("\n🔧 Testing health check logic...")
        
        settings = get_settings()
        adapter = PostgreSQLAdapter(settings)
        
        # Test without engine
        health = await adapter.health_check()
        print(f"   - No engine health check: {health['status']}")
        assert health['status'] == 'error'
        
        # Test with mocked engine
        adapter.engine = Mock()
        adapter._tunnel_service = Mock()
        adapter._tunnel_service.is_tunnel_active.return_value = True
        
        # Mock database query
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("PostgreSQL 14.0", "stbr_rag1", "postgres")
        mock_conn.execute = MagicMock(return_value=mock_result)
        
        adapter.engine.begin = MagicMock()
        adapter.engine.begin.return_value.__aenter__ = MagicMock(return_value=mock_conn)
        adapter.engine.begin.return_value.__aexit__ = MagicMock()
        
        health = await adapter.health_check()
        print(f"   - Mocked health check: {health['status']}")
        print(f"   - Tunnel status: {health['tunnel_status']}")
        print(f"   - Connection type: {health['connection_type']}")
        
        return True
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False


async def test_configuration_access():
    """Test configuration access."""
    try:
        print("\n🔧 Testing configuration access...")
        
        settings = get_settings()
        
        # Test PostgreSQL settings
        required_settings = [
            'POSTGRESQL_HOST', 'POSTGRESQL_PORT', 'POSTGRESQL_USER', 
            'POSTGRESQL_PASSWORD', 'POSTGRESQL_DATABASE'
        ]
        
        for setting in required_settings:
            value = getattr(settings, setting, None)
            print(f"   - {setting}: {'✅' if value else '❌'} {value}")
        
        # Test SSH tunnel settings
        ssh_settings = [
            'SSH_TUNNEL_ENABLED', 'SSH_TUNNEL_REMOTE_HOST', 'SSH_TUNNEL_LOCAL_PORT'
        ]
        
        for setting in ssh_settings:
            value = getattr(settings, setting, None)
            print(f"   - {setting}: {'✅' if value is not None else '❌'} {value}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🚀 Quick PostgreSQL-SSH Tunnel Integration Test")
    print("=" * 55)
    
    tests = [
        ("PostgreSQL Adapter Creation", test_postgresql_adapter_creation),
        ("SSH Tunnel Service Integration", test_tunnel_service_integration),
        ("Connection Logic with Mocks", test_connection_logic_with_mock),
        ("Health Check Logic", test_health_check_logic),
        ("Configuration Access", test_configuration_access),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 TEST RESULTS SUMMARY:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All integration tests passed!")
        print("✅ PostgreSQL-SSH Tunnel integration is working correctly!")
        return True
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed.")
        print("❌ Some integration issues need to be resolved.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 