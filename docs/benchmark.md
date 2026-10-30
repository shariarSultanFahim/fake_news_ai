# Performance Benchmark Report (M3)

## Environment
- **Platform**: Windows 11 (64bit)
- **Processor**: Intel64 Family 6 Model 165 Stepping 2, GenuineIntel
- **RAM**: 15.8 GB
- **Python**: 3.12.10
- **PyTorch**: 2.15.0+cpu (Device: CPU)
- **Model**: Fine-tuned BanglaBERT (Electra sequence classification, 256 tokens)

## Results (50 Requests of Realistic Article Length)

| Configuration | Threads | Caching | Mean Latency | p50 Latency | p95 Latency | Peak Memory (RSS) |
|---|---|---|---|---|---|---|
| **Target VPS (2 vCPU)** | 2 | Disabled | 150.5 ms | 130.8 ms | 250.2 ms | 856.3 MB |
| **Development Default** | 2 | Disabled | 120.9 ms | 118.7 ms | 140.4 ms | 856.5 MB |
| **VPS with Cache** | 2 | Enabled (SHA-256) | 26.1 ms | 0.0 ms | 133.8 ms | 863.6 MB |

## Memory Limit Evaluation
- **Requirement**: Peak memory must stay well under 8 GB (Hostinger KVM 2 target).
- **Observed Peak Memory**: ~856.5 MB.
- **Evaluation**: PASS. Fits comfortably within the 8 GB budget (< 1 GB total footprint).

## Dynamic INT8 Quantization Note
Dynamic INT8 quantization was evaluated. Due to PyTorch 2.15+ CPU Electra embeddings and fp32 parity accuracy on CPU, INT8 quantization is not enabled by default to strictly protect the 0.05 parity tolerance established in M1.
