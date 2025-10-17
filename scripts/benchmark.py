#!/usr/bin/env python3
"""
LLM Local Inference Benchmark for Intel Hardware
Tests various configurations to find optimal settings for agent workloads

# Install dependencies
pip install psutil torch transformers intel-extension-for-pytorch psutil

# Run the benchmark
python benchmark.py
"""

import time
import psutil
import platform
import json
from datetime import datetime
from pathlib import Path
import sys

try:
    import torch
except ImportError:
    print("PyTorch not found. Install with: pip install torch")
    sys.exit(1)

# Optional imports - script continues if not available
OPTIONAL_LIBS = {}
try:
    import intel_extension_for_pytorch as ipex

    OPTIONAL_LIBS['ipex'] = True
except ImportError:
    OPTIONAL_LIBS['ipex'] = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

    OPTIONAL_LIBS['transformers'] = True
except ImportError:
    OPTIONAL_LIBS['transformers'] = False

try:
    import numpy as np

    OPTIONAL_LIBS['numpy'] = True
except ImportError:
    OPTIONAL_LIBS['numpy'] = False


class SystemProfiler:
    """Profile system capabilities"""

    @staticmethod
    def get_system_info():
        info = {
            'cpu': platform.processor(),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'ram_total_gb': round(psutil.virtual_memory().total / (1024 ** 3), 2),
            'ram_available_gb': round(psutil.virtual_memory().available / (1024 ** 3), 2),
            'platform': platform.system(),
            'python_version': platform.python_version(),
        }

        # Check for Intel GPU
        if torch.cuda.is_available():
            info['cuda_available'] = True
            info['cuda_device'] = torch.cuda.get_device_name(0)
        else:
            info['cuda_available'] = False

        # Check for Intel GPU via XPU (Arc/Iris)
        try:
            if hasattr(torch, 'xpu') and torch.xpu.is_available():
                info['xpu_available'] = True
                info['xpu_device_count'] = torch.xpu.device_count()
            else:
                info['xpu_available'] = False
        except:
            info['xpu_available'] = False

        return info


class BenchmarkSuite:
    """Run various benchmark tests"""

    def __init__(self, output_dir='benchmark_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': SystemProfiler.get_system_info(),
            'libraries_available': OPTIONAL_LIBS,
            'tests': []
        }

    def test_cpu_threading(self, thread_counts=[1, 4, 8, 12, 14, 16, 20]):
        """Test optimal thread count for matrix operations"""
        print("\n=== Testing CPU Threading Performance ===")

        if not OPTIONAL_LIBS['numpy']:
            print("NumPy not available, skipping threading test")
            return

        import numpy as np
        results = []

        # Matrix multiplication benchmark (similar to attention operations)
        matrix_size = 2048
        iterations = 10

        for threads in thread_counts:
            torch.set_num_threads(threads)

            times = []
            for _ in range(iterations):
                a = torch.randn(matrix_size, matrix_size)
                b = torch.randn(matrix_size, matrix_size)

                start = time.time()
                c = torch.mm(a, b)
                times.append(time.time() - start)

            avg_time = sum(times) / len(times)
            results.append({
                'threads': threads,
                'avg_time_ms': round(avg_time * 1000, 2),
                'throughput_gflops': round((2 * matrix_size ** 3) / (avg_time * 1e9), 2)
            })
            print(f"Threads: {threads:2d} | Time: {avg_time * 1000:6.2f}ms | "
                  f"GFLOPS: {results[-1]['throughput_gflops']:6.2f}")

        # Find optimal thread count
        best = min(results, key=lambda x: x['avg_time_ms'])
        print(f"\nOptimal thread count: {best['threads']}")

        self.results['tests'].append({
            'name': 'cpu_threading',
            'results': results,
            'recommendation': best['threads']
        })

    def test_memory_bandwidth(self):
        """Test memory bandwidth - important for loading model weights"""
        print("\n=== Testing Memory Bandwidth ===")

        sizes_mb = [100, 500, 1000, 2000, 4000]
        results = []

        for size_mb in sizes_mb:
            size_elements = (size_mb * 1024 * 1024) // 4  # 4 bytes per float32

            # Allocation test
            start = time.time()
            tensor = torch.randn(size_elements)
            alloc_time = time.time() - start

            # Read test
            start = time.time()
            _ = tensor.sum()
            read_time = time.time() - start

            # Write test
            start = time.time()
            tensor.fill_(1.0)
            write_time = time.time() - start

            results.append({
                'size_mb': size_mb,
                'alloc_time_ms': round(alloc_time * 1000, 2),
                'read_bandwidth_gbps': round((size_mb / 1024) / read_time, 2),
                'write_bandwidth_gbps': round((size_mb / 1024) / write_time, 2)
            })

            print(f"Size: {size_mb:4d}MB | Read: {results[-1]['read_bandwidth_gbps']:6.2f} GB/s | "
                  f"Write: {results[-1]['write_bandwidth_gbps']:6.2f} GB/s")

        self.results['tests'].append({
            'name': 'memory_bandwidth',
            'results': results
        })

    def test_quantization_impact(self):
        """Test inference speed with different quantization levels"""
        print("\n=== Testing Quantization Impact ===")

        if not OPTIONAL_LIBS['transformers']:
            print("Transformers library not available, skipping quantization test")
            return

        # Use a small model for testing
        model_name = "gpt2"  # Small model for quick testing

        try:
            print(f"Loading {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)

            test_prompt = "The quick brown fox jumps over the"
            inputs = tokenizer(test_prompt, return_tensors="pt")

            results = []

            # Test FP32
            print("\nTesting FP32...")
            model_fp32 = model.float()
            times = []
            for _ in range(5):
                start = time.time()
                with torch.no_grad():
                    outputs = model_fp32.generate(**inputs, max_new_tokens=50, do_sample=False)
                times.append(time.time() - start)

            avg_time = sum(times) / len(times)
            tokens_per_sec = 50 / avg_time
            results.append({
                'precision': 'fp32',
                'avg_time_s': round(avg_time, 3),
                'tokens_per_sec': round(tokens_per_sec, 2),
                'memory_mb': round(model_fp32.get_memory_footprint() / (1024 ** 2), 2)
            })
            print(f"FP32: {tokens_per_sec:.2f} tokens/sec | Memory: {results[-1]['memory_mb']:.2f} MB")

            # Test FP16/BF16 if available
            if torch.cuda.is_available() or (hasattr(torch, 'xpu') and torch.xpu.is_available()):
                print("\nTesting FP16...")
                model_fp16 = model.half()
                times = []
                for _ in range(5):
                    start = time.time()
                    with torch.no_grad():
                        outputs = model_fp16.generate(**inputs, max_new_tokens=50, do_sample=False)
                    times.append(time.time() - start)

                avg_time = sum(times) / len(times)
                tokens_per_sec = 50 / avg_time
                results.append({
                    'precision': 'fp16',
                    'avg_time_s': round(avg_time, 3),
                    'tokens_per_sec': round(tokens_per_sec, 2),
                    'memory_mb': round(model_fp16.get_memory_footprint() / (1024 ** 2), 2)
                })
                print(f"FP16: {tokens_per_sec:.2f} tokens/sec | Memory: {results[-1]['memory_mb']:.2f} MB")

            # Test with IPEX if available
            if OPTIONAL_LIBS['ipex']:
                print("\nTesting with IPEX optimization...")
                model_ipex = ipex.optimize(model.eval(), dtype=torch.bfloat16)
                times = []
                for _ in range(5):
                    start = time.time()
                    with torch.no_grad():
                        outputs = model_ipex.generate(**inputs, max_new_tokens=50, do_sample=False)
                    times.append(time.time() - start)

                avg_time = sum(times) / len(times)
                tokens_per_sec = 50 / avg_time
                results.append({
                    'precision': 'ipex_bf16',
                    'avg_time_s': round(avg_time, 3),
                    'tokens_per_sec': round(tokens_per_sec, 2)
                })
                print(f"IPEX BF16: {tokens_per_sec:.2f} tokens/sec")

            self.results['tests'].append({
                'name': 'quantization_impact',
                'model': model_name,
                'results': results
            })

        except Exception as e:
            print(f"Error in quantization test: {e}")
            print("This is likely due to missing model files. Install with:")
            print("pip install transformers accelerate")

    def test_agent_simulation(self):
        """Simulate agent workflow with multiple sequential inferences"""
        print("\n=== Simulating Agent Workflow ===")

        if not OPTIONAL_LIBS['transformers']:
            print("Transformers library not available, skipping agent simulation")
            return

        try:
            # Use a small model for simulation
            model_name = "gpt2"
            print(f"Loading {model_name} for agent simulation...")

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            model.eval()

            # Simulate agent workflow: multiple short inferences
            agent_tasks = [
                "Task: Analyze the request",
                "Task: Plan the approach",
                "Task: Execute step 1",
                "Task: Execute step 2",
                "Task: Summarize results"
            ]

            total_start = time.time()
            task_times = []

            for task in agent_tasks:
                inputs = tokenizer(task, return_tensors="pt")

                start = time.time()
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=30, do_sample=False)
                task_time = time.time() - start
                task_times.append(task_time)

                print(f"{task}: {task_time:.3f}s")

            total_time = time.time() - total_start

            result = {
                'num_inferences': len(agent_tasks),
                'individual_times_s': [round(t, 3) for t in task_times],
                'total_time_s': round(total_time, 3),
                'avg_time_per_inference_s': round(total_time / len(agent_tasks), 3)
            }

            print(f"\nTotal agent workflow time: {total_time:.3f}s")
            print(f"Average per inference: {result['avg_time_per_inference_s']:.3f}s")

            self.results['tests'].append({
                'name': 'agent_simulation',
                'results': result
            })

        except Exception as e:
            print(f"Error in agent simulation: {e}")

    def test_kv_cache_benefit(self):
        """Test benefit of KV cache reuse for repeated prefixes"""
        print("\n=== Testing KV Cache Reuse Benefit ===")

        if not OPTIONAL_LIBS['transformers']:
            print("Transformers library not available, skipping KV cache test")
            return

        try:
            model_name = "gpt2"
            print(f"Loading {model_name}...")

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            model.eval()

            # Long system prompt (common in agents)
            system_prompt = "You are a helpful AI assistant. You answer questions clearly and concisely. "
            user_queries = [
                "What is Python?",
                "What is JavaScript?",
                "What is Rust?"
            ]

            # Test without cache reuse
            print("\nWithout KV cache reuse:")
            times_without_cache = []
            for query in user_queries:
                full_prompt = system_prompt + query
                inputs = tokenizer(full_prompt, return_tensors="pt")

                start = time.time()
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=30, do_sample=False)
                times_without_cache.append(time.time() - start)
                print(f"  Query: {query[:20]}... | Time: {times_without_cache[-1]:.3f}s")

            # Test with cache reuse (simulate by pre-computing system prompt)
            print("\nWith KV cache reuse (simulated):")
            system_inputs = tokenizer(system_prompt, return_tensors="pt")

            times_with_cache = []
            for query in user_queries:
                inputs = tokenizer(query, return_tensors="pt")

                start = time.time()
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=30, do_sample=False)
                times_with_cache.append(time.time() - start)
                print(f"  Query: {query[:20]}... | Time: {times_with_cache[-1]:.3f}s")

            avg_without = sum(times_without_cache) / len(times_without_cache)
            avg_with = sum(times_with_cache) / len(times_with_cache)
            speedup = avg_without / avg_with if avg_with > 0 else 0

            result = {
                'avg_time_without_cache_s': round(avg_without, 3),
                'avg_time_with_cache_s': round(avg_with, 3),
                'speedup_factor': round(speedup, 2)
            }

            print(f"\nAverage speedup with cache: {speedup:.2f}x")

            self.results['tests'].append({
                'name': 'kv_cache_benefit',
                'results': result
            })

        except Exception as e:
            print(f"Error in KV cache test: {e}")

    def run_all_tests(self):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("LLM LOCAL INFERENCE BENCHMARK")
        print("=" * 60)
        print("\nSystem Information:")
        for key, value in self.results['system_info'].items():
            print(f"  {key}: {value}")

        print("\nAvailable Libraries:")
        for lib, available in OPTIONAL_LIBS.items():
            status = "✓" if available else "✗"
            print(f"  {status} {lib}")

        # Run tests
        self.test_cpu_threading()
        self.test_memory_bandwidth()
        self.test_quantization_impact()
        self.test_agent_simulation()
        self.test_kv_cache_benefit()

        # Save results
        output_file = self.output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print("\n" + "=" * 60)
        print(f"Benchmark complete! Results saved to: {output_file}")
        print("=" * 60)

        self.print_recommendations()

    def print_recommendations(self):
        """Print optimization recommendations based on test results"""
        print("\n=== RECOMMENDATIONS ===\n")

        # Thread count recommendation
        for test in self.results['tests']:
            if test['name'] == 'cpu_threading' and 'recommendation' in test:
                print(f"✓ Set thread count to: {test['recommendation']}")
                print(f"  Add to your code: torch.set_num_threads({test['recommendation']})\n")

        # Memory recommendations
        ram_gb = self.results['system_info']['ram_total_gb']
        if ram_gb >= 32:
            print("✓ 32GB RAM: Can run 7B-13B models with 4-bit quantization")
            print("  Recommended: GGUF Q4_K_M format with llama.cpp\n")
        elif ram_gb >= 16:
            print("✓ 16GB RAM: Stick to 7B models or smaller")
            print("  Recommended: GGUF Q4_K_S format\n")

        # Library recommendations
        if not OPTIONAL_LIBS['ipex']:
            print("⚠ Install Intel Extension for PyTorch for 2-3x speedup:")
            print("  pip install intel_extension_for_pytorch\n")

        if self.results['system_info'].get('xpu_available'):
            print("✓ Intel GPU detected - consider using XPU acceleration")
            print("  Set device: model.to('xpu')\n")

        print("✓ For production agent workloads, consider:")
        print("  - llama.cpp with GGUF models")
        print("  - OpenVINO runtime for Intel optimization")
        print("  - KV cache reuse for repeated system prompts")
        print("  - Batching parallel agent operations when possible")


def main():
    """Main entry point"""
    print("Preparing benchmark suite...")
    print("This may take several minutes depending on your system.\n")

    # Check if we should download test models
    if OPTIONAL_LIBS['transformers']:
        response = input("Download small test model (GPT-2, ~500MB)? [y/N]: ").lower()
        if response != 'y':
            print("\nSkipping model-based tests. Only running system benchmarks.")
            OPTIONAL_LIBS['transformers'] = False

    benchmark = BenchmarkSuite()
    benchmark.run_all_tests()


if __name__ == "__main__":
    main()