import time
import logging
import allure
from typing import Optional, Dict, List, Any

class Timer:
    """
    A context manager for measuring execution time of code blocks with Allure integration.

    Features:
    - Named timers for better identification
    - Optional logging instead of printing
    - Nested timer support
    - Statistics collection
    - Allure reporting integration
    """

    # Class-level storage for statistics if you want to track multiple timings
    _stats: Dict[str, List[float]] = {}

    def __init__(self, name: str = "", log_level: int = logging.INFO,
                 store_stats: bool = False, logger: Optional[logging.Logger] = None,
                 allure_attach: bool = True):
        """
        Initialize the Timer context manager.

        Args:
            name: A descriptive name for this timer
            log_level: The logging level to use when logging the time
            store_stats: Whether to store timing statistics for later analysis
            logger: Optional custom logger to use instead of the default
            allure_attach: Whether to attach timing information to the Allure report
        """
        self.name = name
        self.log_level = log_level
        self.store_stats = store_stats
        self.logger = logger or logging.getLogger(__name__)
        self.allure_attach = allure_attach
        self.start_time = 0
        self.end_time = 0
        self.elapsed = 0

    def __enter__(self):
        """Start the timer when entering the context."""
        # Add a step to Allure report indicating timer start
        if self.allure_attach and self.name:
            allure.step(f"Starting timer: {self.name}")
        
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the timer when exiting the context and log the elapsed time.

        Also stores statistics if configured to do so and attaches to Allure.
        """
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time

        # Format the message based on whether we have a named timer
        if self.name:
            message = f"{self.name} took {self.elapsed:.4f} seconds"
        else:
            message = f"Operation took {self.elapsed:.4f} seconds"

        # Log or print the result
        self.logger.log(self.log_level, message)

        # Attach timing information to Allure report
        if self.allure_attach:
            # Add an Allure step with timing information
            with allure.step(f"Timer results: {message}"):
                # Attach detailed timing data as a separate attachment
                allure.attach(
                    f"Start Time: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}\n"
                    f"End Time: {time.strftime('%H:%M:%S', time.localtime(self.end_time))}\n"
                    f"Elapsed Time: {self.elapsed:.4f} seconds",
                    name="Timing Details",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            # Add timing as a parameter to current test
            if self.name:
                allure.attach(
                    str(self.elapsed),
                    name=f"{self.name}_seconds",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            # You can also add the time as a test parameter for better filtering and visualization
            try:
                allure.dynamic.parameter(f"time_{self.name.replace(' ', '_')}", f"{self.elapsed:.4f}s")
            except Exception:
                # In case the test is not running in an Allure context
                pass

        # Store statistics if requested
        if self.store_stats:
            if self.name not in Timer._stats:
                Timer._stats[self.name] = []
            Timer._stats[self.name].append(self.elapsed)

    @classmethod
    def get_stats(cls, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get timing statistics.

        Args:
            name: Optional name to filter statistics for a specific timer

        Returns:
            Dictionary with timing statistics
        """
        import statistics

        if name is not None:
            if name not in cls._stats:
                return {}
            times = cls._stats[name]
            return {
                "count": len(times),
                "total": sum(times),
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0
            }

        # Return stats for all timers
        results = {}
        for timer_name, times in cls._stats.items():
            if len(times) > 0:
                results[timer_name] = {
                    "count": len(times),
                    "total": sum(times),
                    "min": min(times),
                    "max": max(times),
                    "mean": statistics.mean(times),
                    "median": statistics.median(times),
                    "stdev": statistics.stdev(times) if len(times) > 1 else 0
                }
        return results

    @classmethod
    def reset_stats(cls, name: Optional[str] = None):
        """Reset timing statistics."""
        if name is not None:
            if name in cls._stats:
                cls._stats[name] = []
        else:
            cls._stats = {}
            
    @classmethod
    def add_stats_to_allure(cls, name: Optional[str] = None):
        """
        Add collected statistics to Allure report.
        
        Args:
            name: Optional name to filter statistics for a specific timer
        """
        stats = cls.get_stats(name)
        
        if not stats:
            return
            
        if name is not None:
            # Add stats for specific timer
            timer_stats = stats
            with allure.step(f"Timing Statistics for {name}"):
                allure.attach(
                    "\n".join([f"{k}: {v}" for k, v in timer_stats.items()]),
                    name=f"Stats for {name}",
                    attachment_type=allure.attachment_type.TEXT
                )
        else:
            # Add stats for all timers
            for timer_name, timer_stats in stats.items():
                with allure.step(f"Timing Statistics for {timer_name}"):
                    allure.attach(
                        "\n".join([f"{k}: {v}" for k, v in timer_stats.items()]),
                        name=f"Stats for {timer_name}",
                        attachment_type=allure.attachment_type.TEXT
                    )
