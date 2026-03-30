# Performance Agent

Performance profiling and optimization for rebuilt Evergreen Python services. The performance agent provides specialized profiling and optimization capabilities — it complements the developer agent, it does not replace it.

## What This Is

A focused set of instructions for profiling Python code (CPU, memory, I/O), identifying bottlenecks, and applying optimization patterns. Covers cProfile, line_profiler, memory_profiler, py-spy, tracemalloc, NumPy vectorization, caching, parallelization, async I/O, database optimization, and benchmarking.

Based on [wshobson/agents — python-performance-optimization](https://github.com/wshobson/agents/tree/main/plugins/python-development/skills/python-performance-optimization), adapted to the rebuilder agent convention.

## How It's Activated

The performance agent is loaded **on demand** — it is not always-on like the developer and QA agents. Use it when:

- Investigating latency or throughput issues
- Optimizing hot paths identified by profiling
- Validating performance targets before release
- Debugging memory leaks or high memory consumption
- Running benchmark comparisons

Reference `performance-agent/skill.md` and `performance-agent/config.md` in your chat session when you need performance work.

## Files

| File | Purpose |
|---|---|
| `skill.md` | Performance profiling and optimization instructions — profiling tools, optimization patterns, best practices |
| `config.md` | Per-project performance config — profiling commands, performance targets, hot paths, infrastructure context |
| `references/advanced-patterns.md` | Extended examples — NumPy, caching, __slots__, multiprocessing, async I/O, database batching, benchmarking |
| `README.md` | This file |
