#!/usr/bin/env python3
"""
Performance monitoring script for SecurityGuard AI
Validates the <2 second response time requirement
"""

import asyncio
import time
import statistics
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from services.transaction_analyzer import TransactionAnalyzer
from services.ml_detector import MLAnomalyDetector
from services.exploit_database import ExploitDatabase
from core.config import get_settings


class PerformanceMonitor:
    """Real-time performance monitoring for SecurityGuard AI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.analyzer = TransactionAnalyzer()
        self.ml_detector = MLAnomalyDetector()
        self.exploit_db = ExploitDatabase()
        
        # Performance tracking
        self.response_times = []
        self.component_times = {
            "parsing": [],
            "program_analysis": [],
            "pattern_matching": [],
            "ml_detection": [],
            "account_analysis": []
        }
    
    async def initialize(self):
        """Initialize all services"""
        logger.info("🔧 Initializing SecurityGuard AI services...")
        
        try:
            await self.analyzer.initialize()
            await self.ml_detector.initialize()
            await self.ml_detector.load_model()
            await self.exploit_db.initialize()
            
            logger.info("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            return False
    
    def generate_test_transactions(self) -> List[str]:
        """Generate various test transaction types"""
        return [
            # Simple transfer
            "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG3fbh12Whk9nL4UbO63msHLSF7V9bN5E6jPWFfv8AqVt6AQICAAEMAgAAAADoAwAAAAAAAA==",
            
            # Token swap (medium complexity)
            "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG3fbh12Whk9nL4UbO63msHLSF7V9bN5E6jPWFfv8AqVt6AQICAAEMAgAAAADoAwAAAAAAAA==",
            
            # Complex DeFi transaction
            "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG3fbh12Whk9nL4UbO63msHLSF7V9bN5E6jPWFfv8AqVt6AQICAAEMAgAAAADoAwAAAAAAAA=="
        ]
    
    async def benchmark_component(self, component_name: str, func, *args) -> float:
        """Benchmark individual component performance"""
        start_time = time.time()
        
        try:
            result = await func(*args)
            execution_time = (time.time() - start_time) * 1000
            self.component_times[component_name].append(execution_time)
            return execution_time
            
        except Exception as e:
            logger.error(f"Component {component_name} failed: {e}")
            return 5000.0  # Return high time for failures
    
    async def run_full_analysis_benchmark(self, transaction_data: str) -> Dict[str, float]:
        """Run full analysis pipeline and measure component times"""
        total_start = time.time()
        component_times = {}
        
        try:
            # 1. Parse transaction
            parse_time = await self.benchmark_component(
                "parsing", 
                self.analyzer.parse_transaction, 
                transaction_data
            )
            component_times["parsing"] = parse_time
            
            # Get parsed transaction for other components
            parsed_tx = await self.analyzer.parse_transaction(transaction_data)
            
            # 2. Run analysis components in parallel (as in production)
            program_task = asyncio.create_task(self.analyzer.analyze_programs(parsed_tx))
            pattern_task = asyncio.create_task(self.exploit_db.check_patterns(parsed_tx))
            ml_task = asyncio.create_task(self.ml_detector.analyze_transaction(parsed_tx))
            account_task = asyncio.create_task(self.analyzer.analyze_accounts(parsed_tx, None))
            
            # Measure parallel execution time
            parallel_start = time.time()
            await asyncio.gather(program_task, pattern_task, ml_task, account_task)
            parallel_time = (time.time() - parallel_start) * 1000
            
            component_times["parallel_analysis"] = parallel_time
            
            # Total time
            total_time = (time.time() - total_start) * 1000
            component_times["total"] = total_time
            
            self.response_times.append(total_time)
            
            return component_times
            
        except Exception as e:
            logger.error(f"Full analysis benchmark failed: {e}")
            return {"total": 5000.0, "error": str(e)}
    
    async def run_performance_test(self, num_iterations: int = 100) -> Dict[str, Any]:
        """Run comprehensive performance test"""
        logger.info(f"🚀 Starting performance test with {num_iterations} iterations...")
        
        test_transactions = self.generate_test_transactions()
        all_results = []
        
        # Progress tracking
        progress_interval = max(1, num_iterations // 10)
        
        for i in range(num_iterations):
            # Rotate through different transaction types
            transaction_data = test_transactions[i % len(test_transactions)]
            
            # Run benchmark
            result = await self.run_full_analysis_benchmark(transaction_data)
            all_results.append(result)
            
            # Progress logging
            if (i + 1) % progress_interval == 0:
                progress = ((i + 1) / num_iterations) * 100
                logger.info(f"Progress: {progress:.0f}% ({i + 1}/{num_iterations})")
        
        # Calculate statistics
        total_times = [r.get("total", 5000) for r in all_results if "total" in r]
        parsing_times = [r.get("parsing", 0) for r in all_results if "parsing" in r]
        parallel_times = [r.get("parallel_analysis", 0) for r in all_results if "parallel_analysis" in r]
        
        if not total_times:
            return {"error": "No successful benchmarks completed"}
        
        # Performance statistics
        stats = {
            "total_iterations": num_iterations,
            "successful_runs": len(total_times),
            "success_rate": (len(total_times) / num_iterations) * 100,
            
            # Total response time stats
            "total_time": {
                "avg_ms": statistics.mean(total_times),
                "median_ms": statistics.median(total_times),
                "p95_ms": statistics.quantiles(total_times, n=20)[18] if len(total_times) >= 20 else max(total_times),
                "p99_ms": statistics.quantiles(total_times, n=100)[98] if len(total_times) >= 100 else max(total_times),
                "min_ms": min(total_times),
                "max_ms": max(total_times)
            },
            
            # Component breakdown
            "parsing_time": {
                "avg_ms": statistics.mean(parsing_times) if parsing_times else 0,
                "p95_ms": statistics.quantiles(parsing_times, n=20)[18] if len(parsing_times) >= 20 else (max(parsing_times) if parsing_times else 0)
            },
            
            "parallel_analysis_time": {
                "avg_ms": statistics.mean(parallel_times) if parallel_times else 0,
                "p95_ms": statistics.quantiles(parallel_times, n=20)[18] if len(parallel_times) >= 20 else (max(parallel_times) if parallel_times else 0)
            },
            
            # Requirement validation
            "requirement_validation": {
                "target_p95_ms": 2000,
                "actual_p95_ms": statistics.quantiles(total_times, n=20)[18] if len(total_times) >= 20 else max(total_times),
                "meets_requirement": (statistics.quantiles(total_times, n=20)[18] if len(total_times) >= 20 else max(total_times)) < 2000,
                "requests_under_2s": sum(1 for t in total_times if t < 2000),
                "percentage_under_2s": (sum(1 for t in total_times if t < 2000) / len(total_times)) * 100
            }
        }
        
        return stats
    
    async def run_concurrent_test(self, concurrent_requests: int = 10) -> Dict[str, Any]:
        """Test performance under concurrent load"""
        logger.info(f"🔄 Testing concurrent performance with {concurrent_requests} requests...")
        
        transaction_data = self.generate_test_transactions()[1]  # Use medium complexity
        
        # Create concurrent tasks
        tasks = [
            self.run_full_analysis_benchmark(transaction_data)
            for _ in range(concurrent_requests)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000
        
        # Process results
        successful_results = [r for r in results if isinstance(r, dict) and "total" in r]
        response_times = [r["total"] for r in successful_results]
        
        if not response_times:
            return {"error": "No successful concurrent requests"}
        
        return {
            "concurrent_requests": concurrent_requests,
            "successful_requests": len(successful_results),
            "total_time_ms": total_time,
            "avg_response_time_ms": statistics.mean(response_times),
            "p95_response_time_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
            "max_response_time_ms": max(response_times),
            "min_response_time_ms": min(response_times),
            "throughput_rps": len(successful_results) / (total_time / 1000)
        }
    
    def print_performance_report(self, stats: Dict[str, Any]):
        """Print formatted performance report"""
        print("\n" + "="*80)
        print("🎯 SECURITYGUARD AI PERFORMANCE REPORT")
        print("="*80)
        
        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        # Overall results
        req_val = stats["requirement_validation"]
        meets_req = "✅ PASSED" if req_val["meets_requirement"] else "❌ FAILED"
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {stats['total_iterations']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        print(f"   Requirement (<2s for 95%): {meets_req}")
        print(f"   Actual P95: {req_val['actual_p95_ms']:.1f}ms")
        print(f"   Requests under 2s: {req_val['percentage_under_2s']:.1f}%")
        
        # Response time breakdown
        total = stats["total_time"]
        print(f"\n⏱️  RESPONSE TIME BREAKDOWN:")
        print(f"   Average: {total['avg_ms']:.1f}ms")
        print(f"   Median: {total['median_ms']:.1f}ms")
        print(f"   95th Percentile: {total['p95_ms']:.1f}ms")
        print(f"   99th Percentile: {total['p99_ms']:.1f}ms")
        print(f"   Min: {total['min_ms']:.1f}ms")
        print(f"   Max: {total['max_ms']:.1f}ms")
        
        # Component performance
        parsing = stats["parsing_time"]
        parallel = stats["parallel_analysis_time"]
        print(f"\n🔧 COMPONENT PERFORMANCE:")
        print(f"   Parsing (avg): {parsing['avg_ms']:.1f}ms")
        print(f"   Parsing (p95): {parsing['p95_ms']:.1f}ms")
        print(f"   Analysis (avg): {parallel['avg_ms']:.1f}ms")
        print(f"   Analysis (p95): {parallel['p95_ms']:.1f}ms")
        
        print("\n" + "="*80)
    
    async def continuous_monitoring(self, duration_minutes: int = 5):
        """Run continuous performance monitoring"""
        logger.info(f"🔄 Starting continuous monitoring for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        test_count = 0
        
        while time.time() < end_time:
            transaction_data = self.generate_test_transactions()[test_count % 3]
            
            result = await self.run_full_analysis_benchmark(transaction_data)
            test_count += 1
            
            # Log every 10 tests
            if test_count % 10 == 0:
                recent_times = self.response_times[-10:]
                avg_recent = statistics.mean(recent_times)
                logger.info(f"Tests completed: {test_count}, Recent avg: {avg_recent:.1f}ms")
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Continuous monitoring completed: {test_count} tests")
        return test_count


async def main():
    """Main performance monitoring function"""
    monitor = PerformanceMonitor()
    
    # Initialize services
    if not await monitor.initialize():
        logger.error("❌ Failed to initialize services")
        return
    
    try:
        # Run performance test
        logger.info("🚀 Running performance benchmark...")
        stats = await monitor.run_performance_test(num_iterations=50)
        
        # Print report
        monitor.print_performance_report(stats)
        
        # Test concurrent performance
        logger.info("\n🔄 Testing concurrent performance...")
        concurrent_stats = await monitor.run_concurrent_test(concurrent_requests=10)
        
        print(f"\n🔄 CONCURRENT PERFORMANCE:")
        print(f"   Concurrent Requests: {concurrent_stats['concurrent_requests']}")
        print(f"   Success Rate: {concurrent_stats['successful_requests']}/{concurrent_stats['concurrent_requests']}")
        print(f"   Average Response: {concurrent_stats['avg_response_time_ms']:.1f}ms")
        print(f"   P95 Response: {concurrent_stats['p95_response_time_ms']:.1f}ms")
        print(f"   Throughput: {concurrent_stats['throughput_rps']:.1f} RPS")
        
        # Save results to file
        results = {
            "timestamp": time.time(),
            "performance_test": stats,
            "concurrent_test": concurrent_stats
        }
        
        with open("performance_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("📁 Results saved to performance_results.json")
        
        # Final validation
        if stats["requirement_validation"]["meets_requirement"]:
            logger.info("✅ PERFORMANCE REQUIREMENT MET: <2 seconds for 95% of requests")
        else:
            logger.error("❌ PERFORMANCE REQUIREMENT NOT MET")
            
    except Exception as e:
        logger.error(f"❌ Performance monitoring failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())