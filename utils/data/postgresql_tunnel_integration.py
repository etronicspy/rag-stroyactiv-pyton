#!/usr/bin/env python3
"""
PostgreSQL Integration with SSH Tunnel Service Utility.

Этот utility тестирует интеграцию PostgreSQL с существующим SSH tunnel service,
включая автоматическое переключение между tunneled и direct connections.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import get_settings
from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from services.ssh_tunnel_service import (
    get_tunnel_service, 
    initialize_tunnel_service,
    shutdown_tunnel_service
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLTunnelTester:
    """PostgreSQL integration tester with SSH tunnel service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.adapter: Optional[PostgreSQLAdapter] = None
        self.tunnel_service = None
        
    async def test_tunnel_service_status(self) -> Dict[str, Any]:
        """Test SSH tunnel service status."""
        logger.info("🔍 Testing SSH tunnel service status...")
        
        try:
            # Get tunnel service
            self.tunnel_service = get_tunnel_service()
            
            if not self.tunnel_service:
                return {
                    "status": "not_available",
                    "message": "SSH tunnel service not initialized",
                    "recommendations": [
                        "Check if SSH tunnel is enabled in configuration",
                        "Verify SSH credentials and connection settings",
                        "Try initializing tunnel service manually"
                    ]
                }
            
            # Get service status
            service_status = self.tunnel_service.get_status()
            is_active = self.tunnel_service.is_tunnel_active()
            
            return {
                "status": "available",
                "service_running": service_status.get("service_running", False),
                "config_enabled": service_status.get("config_enabled", False),
                "tunnel_active": is_active,
                "tunnel_manager": service_status.get("tunnel_manager"),
                "message": f"Tunnel active: {is_active}"
            }
            
        except Exception as e:
            logger.error(f"Error checking tunnel service: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to check tunnel service status"
            }
    
    async def test_postgresql_connection_scenarios(self) -> Dict[str, Any]:
        """Test different PostgreSQL connection scenarios."""
        logger.info("🔍 Testing PostgreSQL connection scenarios...")
        
        scenarios = {}
        
        # Scenario 1: With tunnel service
        logger.info("📡 Testing connection with tunnel service...")
        scenarios["with_tunnel"] = await self._test_connection_scenario("with_tunnel")
        
        # Scenario 2: Force direct connection (mock no tunnel)
        logger.info("🔗 Testing direct connection...")
        scenarios["direct"] = await self._test_connection_scenario("direct")
        
        return scenarios
    
    async def _test_connection_scenario(self, scenario: str) -> Dict[str, Any]:
        """Test specific connection scenario."""
        try:
            self.adapter = PostgreSQLAdapter(self.settings)
            
            # For direct scenario, temporarily disable tunnel
            original_tunnel = None
            if scenario == "direct":
                original_tunnel = self.adapter._tunnel_service
                self.adapter._tunnel_service = None
            
            start_time = time.time()
            connection_result = await self.adapter.connect()
            connection_time = time.time() - start_time
            
            if not connection_result:
                return {
                    "status": "failed",
                    "message": "Connection failed",
                    "connection_time": connection_time
                }
            
            # Test health check
            health_result = await self.adapter.health_check()
            
            # Get connection info
            connection_info = {
                "connection_string": self.adapter._connection_string,
                "tunnel_status": health_result.get("tunnel_status", "unknown"),
                "connection_type": health_result.get("connection_type", "unknown"),
                "database": health_result.get("database"),
                "user": health_result.get("user")
            }
            
            # Restore original tunnel for cleanup
            if scenario == "direct" and original_tunnel:
                self.adapter._tunnel_service = original_tunnel
            
            await self.adapter.disconnect()
            
            return {
                "status": "success",
                "connection_time": round(connection_time, 3),
                "health_check": health_result,
                "connection_info": connection_info,
                "message": f"Connection successful via {connection_info['connection_type']}"
            }
            
        except Exception as e:
            if self.adapter:
                await self.adapter.disconnect()
            
            return {
                "status": "error",
                "error": str(e),
                "message": f"Connection failed: {e}"
            }
    
    async def test_database_operations(self) -> Dict[str, Any]:
        """Test basic database operations."""
        logger.info("🔍 Testing database operations...")
        
        try:
            self.adapter = PostgreSQLAdapter(self.settings)
            
            if not await self.adapter.connect():
                return {
                    "status": "failed",
                    "message": "Cannot connect to database"
                }
            
            operations = {}
            
            # Test basic query
            operations["basic_query"] = await self._test_basic_query()
            
            # Test database info
            operations["database_info"] = await self._test_database_info()
            
            # Test extensions
            operations["extensions"] = await self._test_extensions()
            
            await self.adapter.disconnect()
            
            return {
                "status": "success",
                "operations": operations,
                "message": "Database operations completed"
            }
            
        except Exception as e:
            if self.adapter:
                await self.adapter.disconnect()
            
            return {
                "status": "error",
                "error": str(e),
                "message": f"Database operations failed: {e}"
            }
    
    async def _test_basic_query(self) -> Dict[str, Any]:
        """Test basic SQL query."""
        try:
            async with self.adapter.session_factory() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                
                return {
                    "status": "success",
                    "result": row[0] if row else None,
                    "message": "Basic query successful"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Basic query failed: {e}"
            }
    
    async def _test_database_info(self) -> Dict[str, Any]:
        """Test database information queries."""
        try:
            async with self.adapter.session_factory() as session:
                from sqlalchemy import text
                
                # Get database info
                result = await session.execute(text("""
                    SELECT 
                        current_database() as database_name,
                        current_user as current_user,
                        version() as version,
                        pg_database_size(current_database()) as size_bytes
                """))
                
                row = result.fetchone()
                
                if row:
                    return {
                        "status": "success",
                        "database": row[0],
                        "user": row[1],
                        "version": row[2],
                        "size_mb": round(row[3] / 1024 / 1024, 2),
                        "message": "Database info retrieved"
                    }
                else:
                    return {
                        "status": "failed",
                        "message": "No database info returned"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Database info query failed: {e}"
            }
    
    async def _test_extensions(self) -> Dict[str, Any]:
        """Test database extensions."""
        try:
            async with self.adapter.session_factory() as session:
                from sqlalchemy import text
                
                # Check for ICU and vector extensions
                result = await session.execute(text("""
                    SELECT 
                        extname,
                        extversion
                    FROM pg_extension
                    WHERE extname IN ('vector', 'pg_trgm', 'btree_gin')
                    ORDER BY extname
                """))
                
                extensions = {}
                for row in result:
                    extensions[row[0]] = row[1]
                
                # Check ICU locale support
                locale_result = await session.execute(text("""
                    SELECT 
                        datname,
                        datlocprovider,
                        daticulocale
                    FROM pg_database
                    WHERE datname = current_database()
                """))
                
                locale_row = locale_result.fetchone()
                locale_info = None
                if locale_row:
                    locale_info = {
                        "database": locale_row[0],
                        "locale_provider": locale_row[1],
                        "icu_locale": locale_row[2]
                    }
                
                return {
                    "status": "success",
                    "extensions": extensions,
                    "locale_info": locale_info,
                    "message": f"Found {len(extensions)} extensions"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Extensions check failed: {e}"
            }
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report."""
        logger.info("📊 Generating PostgreSQL-SSH Tunnel integration report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": {
                "postgresql_host": self.settings.POSTGRESQL_HOST,
                "postgresql_port": self.settings.POSTGRESQL_PORT,
                "postgresql_database": self.settings.POSTGRESQL_DATABASE,
                "ssh_tunnel_enabled": self.settings.SSH_TUNNEL_ENABLED
            }
        }
        
        # Test tunnel service
        report["tunnel_service"] = await self.test_tunnel_service_status()
        
        # Test connection scenarios
        report["connection_scenarios"] = await self.test_postgresql_connection_scenarios()
        
        # Test database operations (if any connection works)
        if any(scenario.get("status") == "success" 
               for scenario in report["connection_scenarios"].values()):
            report["database_operations"] = await self.test_database_operations()
        else:
            report["database_operations"] = {
                "status": "skipped",
                "message": "No successful connections available"
            }
        
        return report


async def main():
    """Main test runner."""
    print("🚀 PostgreSQL-SSH Tunnel Integration Test")
    print("=" * 50)
    
    tester = PostgreSQLTunnelTester()
    
    try:
        # Initialize tunnel service if needed
        logger.info("🔧 Initializing tunnel service...")
        tunnel_service = await initialize_tunnel_service()
        
        if tunnel_service:
            logger.info("✅ Tunnel service initialized")
        else:
            logger.warning("⚠️ Tunnel service not available")
        
        # Generate report
        report = await tester.generate_report()
        
        # Print results
        print("\n📊 TEST RESULTS:")
        print("-" * 30)
        
        # Tunnel Service Status
        tunnel_status = report["tunnel_service"]
        print(f"🔌 Tunnel Service: {tunnel_status['status']}")
        if tunnel_status["status"] == "available":
            print(f"   - Active: {tunnel_status.get('tunnel_active', False)}")
            print(f"   - Config: {tunnel_status.get('config_enabled', False)}")
        
        # Connection Scenarios
        print("\n🔗 Connection Tests:")
        for scenario, result in report["connection_scenarios"].items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"   {status_emoji} {scenario}: {result['status']}")
            if result["status"] == "success":
                conn_info = result["connection_info"]
                print(f"      Type: {conn_info['connection_type']}")
                print(f"      Database: {conn_info['database']}")
                print(f"      Time: {result['connection_time']}s")
        
        # Database Operations
        if "database_operations" in report:
            db_ops = report["database_operations"]
            print(f"\n💾 Database Operations: {db_ops['status']}")
            if db_ops["status"] == "success":
                for op, result in db_ops["operations"].items():
                    status_emoji = "✅" if result["status"] == "success" else "❌"
                    print(f"   {status_emoji} {op}: {result['status']}")
        
        # Summary
        print("\n📋 SUMMARY:")
        tunnel_ok = report["tunnel_service"]["status"] == "available"
        connection_ok = any(s["status"] == "success" for s in report["connection_scenarios"].values())
        operations_ok = report.get("database_operations", {}).get("status") == "success"
        
        print(f"   Tunnel Service: {'✅' if tunnel_ok else '❌'}")
        print(f"   PostgreSQL Connection: {'✅' if connection_ok else '❌'}")
        print(f"   Database Operations: {'✅' if operations_ok else '❌'}")
        
        if tunnel_ok and connection_ok and operations_ok:
            print("\n🎉 All tests passed! PostgreSQL-SSH Tunnel integration is working correctly.")
            return True
        else:
            print("\n⚠️ Some tests failed. Check configuration and connectivity.")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            await shutdown_tunnel_service()
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 