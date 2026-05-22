"""Process-level diagnostics. /proc/self/status parser used by both
the /api/admin/debug/memory endpoint and the job runner instrumentation.

No external deps (psutil deliberately avoided — would add a build-time
dep for what /proc gives us free on Linux).
"""

from __future__ import annotations


def proc_status() -> dict[str, int]:
    """Parse /proc/self/status. Returns Vm* values in bytes.

    Best-effort: returns {} on any failure (non-Linux, permission issues,
    /proc unmounted). Never raises.
    """
    out: dict[str, int] = {}
    try:
        with open("/proc/self/status", "r", encoding="ascii") as fh:
            for line in fh:
                if not line.startswith("Vm"):
                    continue
                key, _, rest = line.partition(":")
                rest = rest.strip()
                if not rest:
                    continue
                parts = rest.split()
                if not parts:
                    continue
                try:
                    val = int(parts[0])
                except ValueError:
                    continue
                unit = parts[1].lower() if len(parts) > 1 else "kb"
                multiplier = {"kb": 1024, "mb": 1024 * 1024, "gb": 1024 ** 3}.get(unit, 1)
                out[key.strip()] = val * multiplier
    except OSError:
        pass
    return out


def rss_mib() -> float:
    """Return VmRSS in MiB (rounded to 2 decimals), 0.0 on failure.

    Cheap call (~1 KB read of /proc/self/status). Safe to use in hot
    paths if logging memory growth — e.g. before/after each source_run
    in the durable update job runner.
    """
    bytes_val = proc_status().get("VmRSS", 0)
    return round(bytes_val / 1024 / 1024, 2)
