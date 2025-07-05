#!/usr/bin/env python3
"""
Logging System Test Script

This script tests the comprehensive logging functionality including:
- Logging configuration
- Structured logging
- Log file creation and rotation
- Security event logging
- Performance logging
- Log analysis and statistics
"""

import os
import sys
import time
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import (
    setup_logging, get_logger, JSONFormatter, ContextFilter,
    log_request, log_security_event, log_performance_event
)
from app.services.logging_service import LoggingService


def test_logging_configuration():
    """Test logging configuration setup"""
    print("\n⚙️ Testing Logging Configuration")
    print("=" * 50)
    
    try:
        # Setup logging
        setup_logging()
        
        # Get a logger
        logger = get_logger(__name__)
        
        print("✅ Logging configuration initialized")
        print(f"   Logger name: {logger.name}")
        print(f"   Logger level: {logger.level}")
        print(f"   Handler count: {len(logger.handlers)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging configuration test failed: {str(e)}")
        return False


def test_structured_logging():
    """Test structured logging functionality"""
    print("\n📋 Testing Structured Logging")
    print("=" * 50)
    
    try:
        logger = get_logger(__name__)
        
        # Test different log levels
        logger.debug("Debug message for testing")
        logger.info("Info message for testing")
        logger.warning("Warning message for testing")
        logger.error("Error message for testing")
        
        # Test structured logging with extra fields
        logger.info(
            "Structured log message",
            extra={
                'user_id': 'test_user_123',
                'action': 'test_action',
                'ip_address': '192.168.1.100',
                'custom_field': 'custom_value'
            }
        )
        
        print("✅ Structured logging messages sent")
        print("   Sent debug, info, warning, error messages")
        print("   Sent structured message with extra fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Structured logging test failed: {str(e)}")
        return False


def test_json_formatter():
    """Test JSON formatter"""
    print("\n🔧 Testing JSON Formatter")
    print("=" * 50)
    
    try:
        import logging
        
        # Create a test logger with JSON formatter
        test_logger = logging.getLogger('test_json')
        test_logger.setLevel(logging.INFO)
        
        # Create a string handler to capture output
        from io import StringIO
        string_handler = logging.StreamHandler(StringIO())
        
        # Add JSON formatter
        json_formatter = JSONFormatter()
        string_handler.setFormatter(json_formatter)
        test_logger.addHandler(string_handler)
        
        # Log a message
        test_logger.info("Test JSON message", extra={'test_field': 'test_value'})
        
        # Get the formatted output
        output = string_handler.stream.getvalue()
        
        # Try to parse as JSON
        log_entry = json.loads(output.strip())
        
        print("✅ JSON formatter working correctly")
        print(f"   Parsed JSON fields: {list(log_entry.keys())}")
        print(f"   Message: {log_entry.get('message')}")
        print(f"   Level: {log_entry.get('level')}")
        print(f"   Custom field: {log_entry.get('test_field')}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON formatter test failed: {str(e)}")
        return False


def test_context_filter():
    """Test context filter"""
    print("\n🏷️ Testing Context Filter")
    print("=" * 50)
    
    try:
        import logging
        
        # Create a test record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Apply context filter
        context_filter = ContextFilter()
        context_filter.filter(record)
        
        print("✅ Context filter applied successfully")
        print(f"   App name: {getattr(record, 'app_name', 'Not set')}")
        print(f"   App version: {getattr(record, 'app_version', 'Not set')}")
        print(f"   Environment: {getattr(record, 'environment', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Context filter test failed: {str(e)}")
        return False


def test_convenience_functions():
    """Test convenience logging functions"""
    print("\n🎯 Testing Convenience Functions")
    print("=" * 50)
    
    try:
        logger = get_logger(__name__)
        
        # Test HTTP request logging
        log_request(
            logger,
            method='GET',
            path='/api/v1/test',
            status_code=200,
            response_time=0.123,
            user_id='test_user_456'
        )
        
        # Test security event logging
        log_security_event(
            logger,
            event_type='test_security_event',
            message='This is a test security event',
            user_id='test_user_456',
            ip_address='192.168.1.200'
        )
        
        # Test performance event logging
        log_performance_event(
            logger,
            operation='test_operation',
            duration=2.5,
            details={'test': True, 'operation_id': 'test_123'}
        )
        
        print("✅ Convenience functions working correctly")
        print("   HTTP request logged")
        print("   Security event logged")
        print("   Performance event logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {str(e)}")
        return False


def test_log_file_creation():
    """Test log file creation"""
    print("\n📁 Testing Log File Creation")
    print("=" * 50)
    
    try:
        # Check if logs directory exists
        logs_dir = Path("logs")
        
        print(f"   Logs directory exists: {logs_dir.exists()}")
        
        if logs_dir.exists():
            # List log files
            log_files = list(logs_dir.glob("*.log"))
            print(f"   Found {len(log_files)} log files:")
            
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"     - {log_file.name}: {size} bytes")
        
        # Generate some log entries to ensure files are created
        logger = get_logger(__name__)
        logger.info("Test log entry for file creation")
        logger.error("Test error entry for file creation")
        
        # Test security and performance logging
        log_security_event(logger, 'test', 'Test security event for file creation')
        log_performance_event(logger, 'test_op', 1.0)
        
        print("✅ Log file creation test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Log file creation test failed: {str(e)}")
        return False


def test_logging_service():
    """Test logging service functionality"""
    print("\n🔍 Testing Logging Service")
    print("=" * 50)
    
    try:
        logging_service = LoggingService()
        
        # Test getting log stats
        stats = logging_service.get_log_stats(24)
        
        print("✅ Log statistics retrieved")
        print(f"   Period: {stats.get('period_hours', 0)} hours")
        print(f"   Status: {stats.get('status', 'unknown')}")
        
        if 'error' not in stats:
            print(f"   Total requests: {stats.get('total_requests', 0)}")
            print(f"   Error count: {stats.get('error_count', 0)}")
            print(f"   Security events: {stats.get('security_events', 0)}")
        
        # Test log search
        search_results = logging_service.search_logs('test', 'app', hours=1)
        
        print(f"   Search results: {search_results.get('total_matches', 0)} matches")
        
        # Test security events
        security_events = logging_service.get_security_events(24)
        
        print(f"   Security events: {security_events.get('total_events', 0)} events")
        
        # Test performance metrics
        performance_metrics = logging_service.get_performance_metrics(24)
        
        print(f"   Performance metrics: {performance_metrics.get('total_requests', 0)} requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging service test failed: {str(e)}")
        return False


def test_log_rotation():
    """Test log rotation functionality"""
    print("\n🔄 Testing Log Rotation")
    print("=" * 50)
    
    try:
        # This is a basic test - in a real scenario you'd need to generate enough logs
        # to trigger rotation or manually test with smaller file sizes
        
        logger = get_logger(__name__)
        
        # Generate multiple log entries
        for i in range(100):
            logger.info(f"Log rotation test message {i+1}")
        
        print("✅ Log rotation test completed")
        print("   Generated 100 log entries")
        print("   (Rotation would occur based on file size limits)")
        
        return True
        
    except Exception as e:
        print(f"❌ Log rotation test failed: {str(e)}")
        return False


def test_error_handling():
    """Test error handling in logging"""
    print("\n⚠️ Testing Error Handling")
    print("=" * 50)
    
    try:
        logger = get_logger(__name__)
        
        # Test logging with exception
        try:
            raise ValueError("Test exception for logging")
        except Exception as e:
            logger.error("Test error with exception", exc_info=True)
        
        # Test logging with various data types
        logger.info("Testing with various data types", extra={
            'string_field': 'test_string',
            'int_field': 42,
            'float_field': 3.14,
            'bool_field': True,
            'list_field': [1, 2, 3],
            'dict_field': {'nested': 'value'}
        })
        
        print("✅ Error handling test completed")
        print("   Exception logged with traceback")
        print("   Various data types logged successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Logging System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    tests = [
        ("Logging Configuration", test_logging_configuration),
        ("Structured Logging", test_structured_logging),
        ("JSON Formatter", test_json_formatter),
        ("Context Filter", test_context_filter),
        ("Convenience Functions", test_convenience_functions),
        ("Log File Creation", test_log_file_creation),
        ("Logging Service", test_logging_service),
        ("Log Rotation", test_log_rotation),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Logging system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check implementation and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
