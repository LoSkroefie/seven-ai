"""
SEVEN AI - PERFORMANCE MONITOR
Real-time performance tracking and optimization

Monitors:
- Response times
- Memory usage
- CPU efficiency
- Ollama performance
- Database operations
"""
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import statistics

class PerformanceMonitor:
    """
    Tracks Seven's performance metrics in real-time
    Helps identify bottlenecks and optimize operations
    """
    
    def __init__(self):
        self.metrics = {
            'response_times': deque(maxlen=100),
            'ollama_times': deque(maxlen=100),
            'db_times': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100),
        }
        
        self.session_stats = {
            'start_time': datetime.now(),
            'total_responses': 0,
            'total_ollama_calls': 0,
            'total_db_queries': 0,
            'errors_count': 0,
        }
        
        self.current_operation = None
        self.operation_start = None
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warn': 5.0,  # seconds
            'response_time_critical': 10.0,
            'memory_warn': 500,  # MB
            'memory_critical': 1000,
            'cpu_warn': 80,  # percent
            'cpu_critical': 95,
        }
        
        # Start background monitoring
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.current_operation = operation_name
        self.operation_start = time.time()
        
    def end_operation(self, operation_name: str = None):
        """End timing an operation"""
        if self.operation_start is None:
            return 0.0
            
        duration = time.time() - self.operation_start
        
        # Record based on operation type
        if 'ollama' in (operation_name or self.current_operation or '').lower():
            self.metrics['ollama_times'].append(duration)
            self.session_stats['total_ollama_calls'] += 1
        elif 'db' in (operation_name or self.current_operation or '').lower():
            self.metrics['db_times'].append(duration)
            self.session_stats['total_db_queries'] += 1
        else:
            self.metrics['response_times'].append(duration)
            self.session_stats['total_responses'] += 1
            
        self.current_operation = None
        self.operation_start = None
        
        return duration
        
    def record_error(self, error_type: str = "generic"):
        """Record an error"""
        self.session_stats['errors_count'] += 1
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # Get process info
                process = psutil.Process()
                
                # Memory usage (MB)
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.metrics['memory_usage'].append(memory_mb)
                
                # CPU usage (percent)
                cpu_percent = process.cpu_percent(interval=1)
                self.metrics['cpu_usage'].append(cpu_percent)
                
            except Exception:
                pass
                
            time.sleep(5)  # Monitor every 5 seconds
            
    def get_stats(self) -> Dict:
        """Get current performance statistics"""
        stats = {
            'uptime_seconds': (datetime.now() - self.session_stats['start_time']).total_seconds(),
            'total_responses': self.session_stats['total_responses'],
            'total_ollama_calls': self.session_stats['total_ollama_calls'],
            'total_db_queries': self.session_stats['total_db_queries'],
            'errors_count': self.session_stats['errors_count'],
        }
        
        # Response time stats
        if self.metrics['response_times']:
            stats['avg_response_time'] = statistics.mean(self.metrics['response_times'])
            stats['min_response_time'] = min(self.metrics['response_times'])
            stats['max_response_time'] = max(self.metrics['response_times'])
            stats['median_response_time'] = statistics.median(self.metrics['response_times'])
        
        # Ollama stats
        if self.metrics['ollama_times']:
            stats['avg_ollama_time'] = statistics.mean(self.metrics['ollama_times'])
            
        # Database stats
        if self.metrics['db_times']:
            stats['avg_db_time'] = statistics.mean(self.metrics['db_times'])
            
        # Resource stats
        if self.metrics['memory_usage']:
            stats['current_memory_mb'] = self.metrics['memory_usage'][-1]
            stats['avg_memory_mb'] = statistics.mean(self.metrics['memory_usage'])
            stats['peak_memory_mb'] = max(self.metrics['memory_usage'])
            
        if self.metrics['cpu_usage']:
            stats['current_cpu_percent'] = self.metrics['cpu_usage'][-1]
            stats['avg_cpu_percent'] = statistics.mean(self.metrics['cpu_usage'])
            stats['peak_cpu_percent'] = max(self.metrics['cpu_usage'])
            
        return stats
        
    def get_health_status(self) -> Dict:
        """Get health status with warnings"""
        stats = self.get_stats()
        health = {
            'status': 'healthy',
            'warnings': [],
            'critical': []
        }
        
        # Check response time
        if 'avg_response_time' in stats:
            if stats['avg_response_time'] > self.thresholds['response_time_critical']:
                health['critical'].append(f"Critical: Response time {stats['avg_response_time']:.1f}s (>{self.thresholds['response_time_critical']}s)")
                health['status'] = 'critical'
            elif stats['avg_response_time'] > self.thresholds['response_time_warn']:
                health['warnings'].append(f"Warning: Response time {stats['avg_response_time']:.1f}s (>{self.thresholds['response_time_warn']}s)")
                if health['status'] == 'healthy':
                    health['status'] = 'degraded'
                    
        # Check memory
        if 'current_memory_mb' in stats:
            if stats['current_memory_mb'] > self.thresholds['memory_critical']:
                health['critical'].append(f"Critical: Memory usage {stats['current_memory_mb']:.0f}MB (>{self.thresholds['memory_critical']}MB)")
                health['status'] = 'critical'
            elif stats['current_memory_mb'] > self.thresholds['memory_warn']:
                health['warnings'].append(f"Warning: Memory usage {stats['current_memory_mb']:.0f}MB (>{self.thresholds['memory_warn']}MB)")
                if health['status'] == 'healthy':
                    health['status'] = 'degraded'
                    
        # Check CPU
        if 'current_cpu_percent' in stats:
            if stats['current_cpu_percent'] > self.thresholds['cpu_critical']:
                health['critical'].append(f"Critical: CPU usage {stats['current_cpu_percent']:.1f}% (>{self.thresholds['cpu_critical']}%)")
                health['status'] = 'critical'
            elif stats['current_cpu_percent'] > self.thresholds['cpu_warn']:
                health['warnings'].append(f"Warning: CPU usage {stats['current_cpu_percent']:.1f}% (>{self.thresholds['cpu_warn']}%)")
                if health['status'] == 'healthy':
                    health['status'] = 'degraded'
                    
        # Check error rate
        if stats['total_responses'] > 0:
            error_rate = stats['errors_count'] / stats['total_responses']
            if error_rate > 0.1:  # More than 10% errors
                health['warnings'].append(f"Warning: High error rate {error_rate*100:.1f}%")
                if health['status'] == 'healthy':
                    health['status'] = 'degraded'
                    
        return health
        
    def get_recommendations(self) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        stats = self.get_stats()
        
        # Response time recommendations
        if 'avg_response_time' in stats and stats['avg_response_time'] > 3.0:
            recommendations.append("Consider enabling response streaming for faster perceived performance")
            
        if 'avg_ollama_time' in stats and stats['avg_ollama_time'] > 4.0:
            recommendations.append("Ollama responses are slow - check if model is fully loaded")
            
        # Memory recommendations
        if 'current_memory_mb' in stats and stats['current_memory_mb'] > 400:
            recommendations.append("High memory usage - consider clearing old conversation history")
            
        # Database recommendations
        if 'total_db_queries' in stats and 'uptime_seconds' in stats:
            queries_per_min = (stats['total_db_queries'] / stats['uptime_seconds']) * 60
            if queries_per_min > 10:
                recommendations.append("High database query rate - consider caching frequently accessed data")
                
        # Error recommendations
        if stats['errors_count'] > 5:
            recommendations.append("Multiple errors detected - check logs for recurring issues")
            
        if not recommendations:
            recommendations.append("Performance is optimal - no recommendations")
            
        return recommendations
        
    def format_report(self) -> str:
        """Format a readable performance report"""
        stats = self.get_stats()
        health = self.get_health_status()
        recommendations = self.get_recommendations()
        
        report = []
        report.append("=" * 70)
        report.append("SEVEN AI - PERFORMANCE REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Health Status
        status_icon = {
            'healthy': '[OK]',
            'degraded': '[WARNING]',
            'critical': '[ERROR]'
        }.get(health['status'], '[?]')
        
        report.append(f"Overall Health: {status_icon} {health['status'].upper()}")
        
        if health['critical']:
            report.append("\nCRITICAL ISSUES:")
            for issue in health['critical']:
                report.append(f"  {issue}")
                
        if health['warnings']:
            report.append("\nWARNINGS:")
            for warning in health['warnings']:
                report.append(f"  {warning}")
                
        report.append("")
        
        # Statistics
        report.append("Session Statistics:")
        report.append(f"  Uptime: {stats['uptime_seconds']/60:.1f} minutes")
        report.append(f"  Total Responses: {stats['total_responses']}")
        report.append(f"  Ollama Calls: {stats['total_ollama_calls']}")
        report.append(f"  Database Queries: {stats['total_db_queries']}")
        report.append(f"  Errors: {stats['errors_count']}")
        report.append("")
        
        # Performance Metrics
        if 'avg_response_time' in stats:
            report.append("Response Times:")
            report.append(f"  Average: {stats['avg_response_time']:.2f}s")
            report.append(f"  Median: {stats.get('median_response_time', 0):.2f}s")
            report.append(f"  Min/Max: {stats.get('min_response_time', 0):.2f}s / {stats.get('max_response_time', 0):.2f}s")
            report.append("")
            
        # Resource Usage
        if 'current_memory_mb' in stats:
            report.append("Resource Usage:")
            report.append(f"  Memory: {stats['current_memory_mb']:.0f}MB (avg: {stats.get('avg_memory_mb', 0):.0f}MB, peak: {stats.get('peak_memory_mb', 0):.0f}MB)")
            
        if 'current_cpu_percent' in stats:
            report.append(f"  CPU: {stats['current_cpu_percent']:.1f}% (avg: {stats.get('avg_cpu_percent', 0):.1f}%, peak: {stats.get('peak_cpu_percent', 0):.1f}%)")
            report.append("")
            
        # Recommendations
        report.append("Recommendations:")
        for rec in recommendations:
            report.append(f"  - {rec}")
            
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
        
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False

# Global instance
performance_monitor = PerformanceMonitor()
