# Performance Benchmark Report

### Pages Version — Step by Step

| Step | JS Heap (MB) | DOM Nodes | Articles | Stories | Time (ms) |
|------|-------------|-----------|----------|---------|-----------|
| DOM loaded (shell only) | 3.6 | 69 | 0 | 0 | 0 |
| Data loaded + first batch | 5 | 2201 | 50 | 0 | 118 |
| After load-more #1 | 6.2 | 3154 | 100 | 0 | 528 |
| After load-more #2 | 5.1 | 4106 | 150 | 0 | 876 |
| After load-more #3 | 5.6 | 5057 | 200 | 0 | 1206 |
| After load-more #4 | 6 | 6007 | 250 | 0 | 1540 |
| After load-more #5 | 5.1 | 6958 | 300 | 0 | 1874 |
| Switched to grouped view | 5.4 | 6376 | 208 | 50 | 2000 |
| Switched back to newest | 6.4 | 2201 | 50 | 0 | 2084 |
| After filter toggle | 7.3 | 2207 | 50 | 0 | 2443 |
| After raw text open | 52.3 | 2207 | 50 | 0 | 4535 |

**Delta (first → last):** Heap 3.6 → 52.3 MB, DOM 69 → 2207 nodes