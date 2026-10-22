# ADR-0006: Lifecycle Process Cleanup & CPU Resource Optimization

**Date**: 2026-10-22
**Status**: accepted
**Deciders**: Project Team

## Context

During previous runs, users reported aggressive CPU heating and high fan speeds:
- A single download caused noticeable CPU spikes.
- Consecutive or multiple runs escalated CPU consumption exponentially, throttling system performance.

Investigation revealed three root causes:
1. **Prolonged Browser Lifecycle:** The headless browser remained open throughout the entire download process (which often lasts 10–30 minutes for large videos). During this window, dynamic video decoding, JavaScript timers, ads, and background animations continued running live inside the headless browser.
2. **Software Rasterization & Audio Decoding:** Chromium was running software WebGL/GPU rasterization and audio rendering on the CPU in headless mode.
3. **Orphaned Processes:** Undetected-chromedriver instances and child renderer/crashpad processes were not guaranteed to terminate if interrupted by signals (`SIGINT` / `Ctrl+C`).

## Decision

We enforce a strict early-termination and resource suppression policy:

1. **Immediate Browser Teardown:** The browser is strictly treated as a short-lived sniffer (3–10 seconds). As soon as the streaming manifest or segment URLs are intercepted, the script executes `window.stop()`, pauses all media tags, navigates to `about:blank`, and immediately terminates the browser (`close_driver()`) **before** downloading starts.
2. **Process Tree Tracking & Force Reaping:** We record the browser remote debugging port and chromedriver PID using `psutil`. Upon shutdown or interruption (`SIGINT`, `SIGTERM`, `atexit`), all tracked parent and child processes are verified dead, with fallback `SIGKILL` cleanup to prevent zombie processes.
3. **Chromium Flag Hardening:** The browser is launched with `--disable-gpu`, `--disable-software-rasterizer`, `--mute-audio`, `--disable-background-networking`, and `block_images=True` to minimize CPU cycles during page evaluation.
4. **Thread-Capped FFmpeg:** Direct FFmpeg streaming is capped with `-threads 2` to prevent saturation of multi-core laptop CPUs.

## Alternatives Considered

### Alternative 1: Keep Browser Alive for Session Cookies
- **Pros**: Browser maintains active session throughout download.
- **Cons**: Severe thermal penalty and battery drain; browser decodes video in parallel with FFmpeg downloading it.
- **Why not**: Intercepted HTTP headers (`Referer`, `User-Agent`, signed manifest query tokens) are already sufficient for FFmpeg to download streams without the browser running.

### Alternative 2: OS-level Nice / CPU Affinity Limiting
- **Pros**: Throttles CPU consumption at the kernel scheduler level.
- **Cons**: Does not stop orphaned processes from lingering or wasting memory; slower downloads.
- **Why not**: Terminating the browser directly solves the root cause completely rather than masking it.

## Consequences

### Positive
- CPU usage during downloading drops from ~100%+ to ~2–5%.
- Laptop stays cool and fans remain quiet.
- Running consecutive or multiple downloads no longer degrades system responsiveness.
- Clean exit guaranteed on `Ctrl+C` with zero orphaned Chromium processes.

### Negative
- Sites that require continuous WebSocket heartbeats to keep stream tokens alive may expire after 10–15 minutes (extremely rare on standard VOD platforms; if encountered, token refresh logic can be added).

### Risks
- **Risk**: Process discovery by remote debugging port fails if debugging port format changes.
- **Mitigation**: Dual tracking combining `driver.service.process` and remote debugging port discovery with graceful exception handling.
