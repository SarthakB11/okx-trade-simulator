import time
import logging
from typing import Dict, List, Any, Optional
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance")

class PerformanceMonitor:
    """
    Utility class for monitoring and tracking performance metrics.
    Tracks latency, throughput, and other performance indicators.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize the performance monitor.
        
        Args:
            window_size: Number of measurements to keep for rolling statistics
        """
        self.window_size = window_size
        self.processing_times = deque(maxlen=window_size)
        self.tick_intervals = deque(maxlen=window_size)
        self.start_time = time.time()
        self.last_tick_time = None
        self.tick_count = 0
    
    def record_tick_received(self) -> float:
        """
        Record that a tick was received and calculate time since last tick.
        
        Returns:
            Time in milliseconds since the last tick, or None if this is the first tick
        """
        current_time = time.time()
        interval = None
        
        if self.last_tick_time is not None:
            interval = (current_time - self.last_tick_time) * 1000  # Convert to ms
            self.tick_intervals.append(interval)
        
        self.last_tick_time = current_time
        self.tick_count += 1
        
        return interval
    
    def start_processing_timer(self) -> float:
        """
        Start timing the processing of a tick.
        
        Returns:
            Start time in seconds
        """
        return time.perf_counter()
    
    def stop_processing_timer(self, start_time: float) -> float:
        """
        Stop timing the processing of a tick and record the duration.
        
        Args:
            start_time: Start time from start_processing_timer()
            
        Returns:
            Processing time in milliseconds
        """
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        self.processing_times.append(processing_time)
        return processing_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        # Calculate statistics for processing times
        if not self.processing_times:
            avg_processing_time = 0
            min_processing_time = 0
            max_processing_time = 0
            p95_processing_time = 0
            p99_processing_time = 0
        else:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
            min_processing_time = min(self.processing_times)
            max_processing_time = max(self.processing_times)
            
            # Calculate percentiles
            sorted_times = sorted(self.processing_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            p95_processing_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_processing_time
            p99_processing_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_processing_time
        
        # Calculate tick rate
        if not self.tick_intervals:
            avg_tick_interval = 0
            ticks_per_second = 0
        else:
            avg_tick_interval = sum(self.tick_intervals) / len(self.tick_intervals)
            ticks_per_second = 1000 / avg_tick_interval if avg_tick_interval > 0 else 0
        
        # Calculate overall tick rate
        elapsed_time = time.time() - self.start_time
        overall_ticks_per_second = self.tick_count / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'processingLatencyMs': avg_processing_time,
            'minLatencyMs': min_processing_time,
            'maxLatencyMs': max_processing_time,
            'p95LatencyMs': p95_processing_time,
            'p99LatencyMs': p99_processing_time,
            'avgTickIntervalMs': avg_tick_interval,
            'ticksPerSecond': ticks_per_second,
            'overallTicksPerSecond': overall_ticks_per_second,
            'tickCount': self.tick_count,
            'elapsedTimeSeconds': elapsed_time
        }
    
    def reset(self):
        """Reset all performance metrics."""
        self.processing_times.clear()
        self.tick_intervals.clear()
        self.start_time = time.time()
        self.last_tick_time = None
        self.tick_count = 0
        
        logger.info("Performance monitor reset")
