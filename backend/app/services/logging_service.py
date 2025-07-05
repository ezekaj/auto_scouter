"""
Logging Management Service

This module provides comprehensive logging management functionality including:
- Log analysis and statistics
- Log searching and filtering
- Security event monitoring
- Performance monitoring
- Log retention management
"""

import os
import re
import json
import gzip
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict, Counter

from app.core.logging_config import get_logger


class LoggingService:
    """Service for managing and analyzing logs"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.log_dir = Path("logs")
        self.log_files = {
            'app': 'app.log',
            'error': 'error.log',
            'security': 'security.log',
            'performance': 'performance.log'
        }
    
    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive logging statistics"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            stats = {
                'period_hours': hours,
                'total_requests': 0,
                'error_count': 0,
                'security_events': 0,
                'performance_issues': 0,
                'top_endpoints': [],
                'error_types': {},
                'response_time_avg': 0.0,
                'status_codes': {},
                'user_activity': {},
                'ip_activity': {},
                'status': 'healthy'
            }
            
            # Analyze app logs
            app_stats = self._analyze_app_logs(cutoff_time)
            stats.update(app_stats)
            
            # Analyze error logs
            error_stats = self._analyze_error_logs(cutoff_time)
            stats['error_count'] = error_stats['count']
            stats['error_types'] = error_stats['types']
            
            # Analyze security logs
            security_stats = self._analyze_security_logs(cutoff_time)
            stats['security_events'] = security_stats['count']
            
            # Analyze performance logs
            performance_stats = self._analyze_performance_logs(cutoff_time)
            stats['performance_issues'] = performance_stats['count']
            
            # Determine overall health status
            if stats['error_count'] > 100 or stats['security_events'] > 50:
                stats['status'] = 'warning'
            if stats['error_count'] > 500 or stats['security_events'] > 200:
                stats['status'] = 'critical'
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get log stats: {str(e)}")
            return {
                'period_hours': hours,
                'error': str(e),
                'status': 'error'
            }
    
    def search_logs(self, query: str, log_type: str = 'app', 
                   level: str = None, hours: int = 24) -> Dict[str, Any]:
        """Search logs with filters"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            results = []
            total_matches = 0
            
            log_file = self.log_dir / self.log_files.get(log_type, 'app.log')
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            # Try to parse as JSON first
                            log_entry = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            
                            # Check time filter
                            if log_time < cutoff_time:
                                continue
                            
                            # Check level filter
                            if level and log_entry.get('level') != level.upper():
                                continue
                            
                            # Check query match
                            if query.lower() in log_entry.get('message', '').lower():
                                results.append({
                                    'line_number': line_num,
                                    'timestamp': log_entry['timestamp'],
                                    'level': log_entry.get('level'),
                                    'message': log_entry.get('message'),
                                    'logger': log_entry.get('logger'),
                                    'module': log_entry.get('module')
                                })
                                total_matches += 1
                                
                                # Limit results to prevent memory issues
                                if len(results) >= 1000:
                                    break
                                    
                        except (json.JSONDecodeError, KeyError):
                            # Handle non-JSON log lines
                            if query.lower() in line.lower():
                                results.append({
                                    'line_number': line_num,
                                    'raw_line': line.strip()
                                })
                                total_matches += 1
            
            return {
                'query': query,
                'log_type': log_type,
                'level': level,
                'hours': hours,
                'results': results,
                'total_matches': total_matches
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search logs: {str(e)}")
            return {
                'query': query,
                'error': str(e),
                'results': [],
                'total_matches': 0
            }
    
    def get_security_events(self, hours: int = 24) -> Dict[str, Any]:
        """Get security events from logs"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            events = []
            event_types = Counter()
            ip_counter = Counter()
            
            security_log = self.log_dir / self.log_files['security']
            
            if security_log.exists():
                with open(security_log, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            
                            if log_time >= cutoff_time:
                                event_type = log_entry.get('security_event_type', 'unknown')
                                ip_address = log_entry.get('ip_address', 'unknown')
                                
                                events.append({
                                    'timestamp': log_entry['timestamp'],
                                    'event_type': event_type,
                                    'message': log_entry.get('message'),
                                    'ip_address': ip_address,
                                    'user_id': log_entry.get('user_id')
                                })
                                
                                event_types[event_type] += 1
                                ip_counter[ip_address] += 1
                                
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            return {
                'period_hours': hours,
                'total_events': len(events),
                'event_types': dict(event_types.most_common(10)),
                'top_ips': dict(ip_counter.most_common(10)),
                'recent_events': events[-50:]  # Last 50 events
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get security events: {str(e)}")
            return {
                'period_hours': hours,
                'error': str(e),
                'total_events': 0
            }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics from logs"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            response_times = []
            slow_requests = []
            endpoint_performance = defaultdict(list)
            
            app_log = self.log_dir / self.log_files['app']
            
            if app_log.exists():
                with open(app_log, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                            
                            if (log_time >= cutoff_time and 
                                log_entry.get('event_type') == 'http_request'):
                                
                                response_time = log_entry.get('response_time', 0)
                                path = log_entry.get('path', 'unknown')
                                
                                response_times.append(response_time)
                                endpoint_performance[path].append(response_time)
                                
                                # Track slow requests (>1 second)
                                if response_time > 1.0:
                                    slow_requests.append({
                                        'timestamp': log_entry['timestamp'],
                                        'path': path,
                                        'method': log_entry.get('method'),
                                        'response_time': response_time,
                                        'status_code': log_entry.get('status_code')
                                    })
                                    
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            # Calculate statistics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate percentiles
            if response_times:
                sorted_times = sorted(response_times)
                p50 = sorted_times[int(len(sorted_times) * 0.5)]
                p95 = sorted_times[int(len(sorted_times) * 0.95)]
                p99 = sorted_times[int(len(sorted_times) * 0.99)]
            else:
                p50 = p95 = p99 = 0
            
            # Top slowest endpoints
            slowest_endpoints = []
            for endpoint, times in endpoint_performance.items():
                if times:
                    avg_time = sum(times) / len(times)
                    slowest_endpoints.append({
                        'endpoint': endpoint,
                        'avg_response_time': avg_time,
                        'request_count': len(times)
                    })
            
            slowest_endpoints.sort(key=lambda x: x['avg_response_time'], reverse=True)
            
            return {
                'period_hours': hours,
                'total_requests': len(response_times),
                'avg_response_time': avg_response_time,
                'p50_response_time': p50,
                'p95_response_time': p95,
                'p99_response_time': p99,
                'slow_requests_count': len(slow_requests),
                'slowest_endpoints': slowest_endpoints[:10],
                'recent_slow_requests': slow_requests[-20:]  # Last 20 slow requests
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            return {
                'period_hours': hours,
                'error': str(e),
                'total_requests': 0
            }
    
    def _analyze_app_logs(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze application logs"""
        stats = {
            'total_requests': 0,
            'top_endpoints': [],
            'status_codes': Counter(),
            'user_activity': Counter(),
            'ip_activity': Counter(),
            'response_times': []
        }
        
        app_log = self.log_dir / self.log_files['app']
        
        if app_log.exists():
            endpoint_counter = Counter()
            
            with open(app_log, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if (log_time >= cutoff_time and 
                            log_entry.get('event_type') == 'http_request'):
                            
                            stats['total_requests'] += 1
                            
                            path = log_entry.get('path', 'unknown')
                            status_code = log_entry.get('status_code', 0)
                            user_id = log_entry.get('user_id')
                            ip_address = log_entry.get('ip_address')
                            response_time = log_entry.get('response_time', 0)
                            
                            endpoint_counter[path] += 1
                            stats['status_codes'][status_code] += 1
                            stats['response_times'].append(response_time)
                            
                            if user_id:
                                stats['user_activity'][user_id] += 1
                            if ip_address:
                                stats['ip_activity'][ip_address] += 1
                                
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            stats['top_endpoints'] = [
                {'endpoint': endpoint, 'count': count}
                for endpoint, count in endpoint_counter.most_common(10)
            ]
            
            if stats['response_times']:
                stats['response_time_avg'] = sum(stats['response_times']) / len(stats['response_times'])
        
        return stats
    
    def _analyze_error_logs(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze error logs"""
        error_types = Counter()
        count = 0
        
        error_log = self.log_dir / self.log_files['error']
        
        if error_log.exists():
            with open(error_log, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if log_time >= cutoff_time:
                            count += 1
                            error_type = log_entry.get('logger', 'unknown')
                            error_types[error_type] += 1
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return {
            'count': count,
            'types': dict(error_types.most_common(10))
        }
    
    def _analyze_security_logs(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze security logs"""
        count = 0
        
        security_log = self.log_dir / self.log_files['security']
        
        if security_log.exists():
            with open(security_log, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if log_time >= cutoff_time:
                            count += 1
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return {'count': count}
    
    def _analyze_performance_logs(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze performance logs"""
        count = 0
        
        performance_log = self.log_dir / self.log_files['performance']
        
        if performance_log.exists():
            with open(performance_log, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        
                        if log_time >= cutoff_time:
                            count += 1
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return {'count': count}
