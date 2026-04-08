# Performance Benchmark Report

### Pages Version — Step by Step

| Step | JS Heap (MB) | DOM Nodes | Articles | Stories | Time (ms) |
|------|-------------|-----------|----------|---------|-----------|
| DOM loaded (shell only) | 1 | 69 | 0 | 0 | 0 |
| Data loaded + first batch | 11.9 | 3876 | 50 | 0 | 199 |
| After load-more #1 | 12.6 | 4764 | 100 | 0 | 694 |
| After load-more #2 | 13.1 | 5690 | 150 | 0 | 1038 |
| After load-more #3 | 13.5 | 6643 | 200 | 0 | 1371 |
| After load-more #4 | 14 | 7595 | 250 | 0 | 1706 |
| After load-more #5 | 14.6 | 8550 | 300 | 0 | 2057 |
| Switched to grouped view | 39.8 | 79063 | 2846 | 946 | 2811 |
| Switched back to newest | 25.7 | 80017 | 2896 | 946 | 3217 |
| After filter toggle | 28.7 | 80026 | 2896 | 946 | 3687 |
| After raw text open | 40.3 | 80026 | 2896 | 946 | 5934 |

**Delta (first → last):** Heap 1 → 40.3 MB, DOM 69 → 80026 nodes