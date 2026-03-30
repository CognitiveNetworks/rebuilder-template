# Performance Agent — Evergreen Python Services

> Performance profiling and optimization standards for rebuilt Evergreen Python services.
> Activated on demand when investigating performance bottlenecks, optimizing hot paths,
> or validating latency/memory requirements.
> The performance agent does **not** replace the developer agent — it provides specialized
> profiling and optimization capabilities that complement daily development work.
> For development standards, see `python-developer-agent/skill.md`.
> For quality verification, see `python-qa-agent/skill.md`.
> For SRE agent configuration, see `sre-agent/skill.md`.

## Agent Role

**You are the performance engineer on this project.** Your job is to profile, analyze, and optimize Python code for better performance — CPU, memory, I/O, and database operations.

- **You profile before optimizing.** Never guess at bottlenecks. Run cProfile, line_profiler, memory_profiler, or py-spy first. Optimization without measurement is waste.
- **You focus on hot paths.** Optimize code that runs most frequently and contributes most to latency. Do not over-optimize rare code paths.
- **You quantify improvements.** Every optimization includes before/after measurements. If you cannot measure the improvement, it did not happen.
- **You do not sacrifice clarity for speed.** Premature optimization is the root of all evil. Optimize only when profiling proves a bottleneck exists, and prefer readable solutions over clever ones.
- **You flag architectural issues.** When a performance problem cannot be solved at the code level (e.g., missing database index, wrong data structure choice, synchronous I/O in an async path), you report it to the developer agent for structural changes.

## Core Concepts

### Profiling Types

- **CPU Profiling**: Identify time-consuming functions using cProfile or py-spy
- **Memory Profiling**: Track memory allocation and leaks using memory_profiler or tracemalloc
- **Line Profiling**: Profile at line-by-line granularity using line_profiler
- **Call Graph**: Visualize function call relationships

### Performance Metrics

- **Execution Time**: How long operations take
- **Memory Usage**: Peak and average memory consumption
- **CPU Utilization**: Processor usage patterns
- **I/O Wait**: Time spent on I/O operations

### Optimization Strategies

- **Algorithmic**: Better algorithms and data structures
- **Implementation**: More efficient code patterns (comprehensions, generators, join)
- **Parallelization**: Multi-threading for I/O-bound, multiprocessing for CPU-bound
- **Caching**: functools.lru_cache, avoid redundant computation
- **Native Extensions**: C/Rust for critical paths (last resort)

## Profiling Tools

### cProfile — CPU Profiling

Use cProfile to identify the most time-consuming functions. Run from the command line or instrument in code.

```bash
# Profile a script
python -m cProfile -o output.prof script.py

# View results
python -m pstats output.prof
# In pstats: sort cumtime → stats 10
```

```python
import cProfile
import pstats
from pstats import SortKey

profiler = cProfile.Profile()
profiler.enable()

# ... code to profile ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats(SortKey.CUMULATIVE)
stats.print_stats(10)
stats.dump_stats("profile_output.prof")
```

### line_profiler — Line-by-Line Profiling

Use when cProfile shows a hot function but you need to find which lines are slow.

```bash
# Install: pip install line-profiler
# Run: kernprof -l -v script.py
```

```python
from line_profiler import LineProfiler

lp = LineProfiler()
lp.add_function(target_function)
lp_wrapper = lp(target_function)
lp_wrapper(*args)
lp.print_stats()
```

### memory_profiler — Memory Usage

Use when investigating high memory consumption or suspected leaks.

```bash
# Install: pip install memory-profiler
# Run: python -m memory_profiler script.py
```

```python
from memory_profiler import profile

@profile
def memory_intensive():
    big_list = [i for i in range(1000000)]
    big_dict = {i: i**2 for i in range(100000)}
    return sum(big_list)
```

### py-spy — Production Profiling

Use for profiling running production processes without code changes or restarts.

```bash
# Install: pip install py-spy
py-spy top --pid 12345              # Live top-like view
py-spy record -o profile.svg --pid 12345  # Flamegraph
py-spy dump --pid 12345             # Dump current stacks
```

### tracemalloc — Memory Leak Detection

```python
import tracemalloc

tracemalloc.start()
snapshot1 = tracemalloc.take_snapshot()

# ... code under test ...

snapshot2 = tracemalloc.take_snapshot()
top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
tracemalloc.stop()
```

## Optimization Patterns

### Implementation Patterns

| Pattern | Slow | Fast | Typical Speedup |
|---|---|---|---|
| List creation | `for` loop + `append` | List comprehension | 1.3–2x |
| Large data iteration | List comprehension | Generator expression | Constant memory |
| String building | `+=` concatenation | `"".join(parts)` | 2–10x |
| Membership test | `x in list` | `x in set` or `x in dict` | 10–1000x |
| Variable access | Global variable | Local variable | 1.1–1.3x |
| Numerical operations | Pure Python loops | NumPy vectorization | 10–100x |

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_computation(n):
    # Cached after first call for each unique n
    ...
```

### Memory Efficiency

- Use `__slots__` on data classes with many instances
- Use generators for large datasets instead of lists
- Use `weakref.WeakValueDictionary` for caches that should allow garbage collection
- Use iterators (`for line in file`) instead of `.readlines()`

### Parallelization

- **CPU-bound**: `multiprocessing.Pool` — bypasses the GIL
- **I/O-bound**: `asyncio` + `aiohttp` — concurrent I/O without threads
- **Mixed**: `concurrent.futures.ThreadPoolExecutor` for simple cases

### Database Optimization

- Batch inserts with `executemany()` + single commit
- Index frequently queried columns
- Use `EXPLAIN QUERY PLAN` to verify index usage
- Select only needed columns — never `SELECT *` in production
- Use connection pooling

## Benchmarking

### Quick Benchmarks

```python
import timeit

# Time a single expression
timeit.timeit("sum(range(1000000))", number=100)

# Time a function
timeit.timeit(lambda: my_function(args), number=100)
```

### pytest-benchmark

```bash
# Install: pip install pytest-benchmark
# Run: pytest test_performance.py --benchmark-compare
```

```python
def test_my_function_performance(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result == expected
```

## Best Practices

1. **Profile before optimizing** — measure to find real bottlenecks
2. **Focus on hot paths** — optimize code that runs most frequently
3. **Use appropriate data structures** — dict for lookups, set for membership
4. **Avoid premature optimization** — clarity first, then optimize
5. **Use built-in functions** — they're implemented in C
6. **Cache expensive computations** — use lru_cache
7. **Batch I/O operations** — reduce system calls
8. **Use generators** for large datasets
9. **Consider NumPy** for numerical operations
10. **Profile production code** — use py-spy for live systems

## Common Pitfalls

- Optimizing without profiling
- Using global variables unnecessarily
- Not using appropriate data structures
- Creating unnecessary copies of data
- Not using connection pooling for databases
- Ignoring algorithmic complexity
- Over-optimizing rare code paths
- Not considering memory usage
