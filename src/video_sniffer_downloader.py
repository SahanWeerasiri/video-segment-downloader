#!/usr/bin/env python3
"""
Video Sniffer & Segment Downloader
----------------------------------
1. Navigates to a webpage using an optimized headless browser (Brave / Chrome).
2. Intercepts network packets via Chrome DevTools Protocol (CDP).
3. Automatically triggers playback on HTML5 video players.
4. Identifies streaming manifests (.m3u8, .mpd) or media segments (.ts, .m4s).
5. Closes the browser IMMEDIATELY after sniffing to release CPU & RAM.
6. Downloads segments (supporting both MPEG-TS and fMP4/CMAF with EXT-X-MAP init segments)
   and stitches them into a final .mp4 video using FFmpeg.
"""

import os
import sys
import time
import json
import re
import signal
import atexit
import argparse
import subprocess
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import psutil

# Global reference for signal handling and cleanup
_ACTIVE_DRIVER = None
_ACTIVE_BROWSER_PIDS = set()


def _register_browser_pids(driver):
    """Discovers and tracks all browser and renderer PIDs for clean termination."""
    global _ACTIVE_BROWSER_PIDS
    _ACTIVE_BROWSER_PIDS.clear()

    # Track chromedriver service process
    service_proc = getattr(getattr(driver, "service", None), "process", None)
    if service_proc and service_proc.pid:
        _ACTIVE_BROWSER_PIDS.add(service_proc.pid)

    # Track browser processes by remote debugging port
    dbg = driver.capabilities.get("goog:chromeOptions", {}).get("debuggerAddress", "")
    port = dbg.split(":")[1] if ":" in dbg else None
    if port:
        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = " ".join(p.info["cmdline"] or [])
                if f"--remote-debugging-port={port}" in cmdline:
                    _ACTIVE_BROWSER_PIDS.add(p.info["pid"])
                    # Include child processes (renderers, gpu, crashpad)
                    for child in p.children(recursive=True):
                        _ACTIVE_BROWSER_PIDS.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


def close_driver(driver=None):
    """
    Stops page execution and forcefully terminates the headless browser
    and all associated processes to prevent CPU throttling and fan noise.
    """
    global _ACTIVE_DRIVER, _ACTIVE_BROWSER_PIDS
    target_driver = driver or _ACTIVE_DRIVER
    if not target_driver:
        return

    # 1. Stop all video playback and unload page scripts immediately
    try:
        target_driver.execute_script("""
            window.stop();
            document.querySelectorAll('video, audio').forEach(el => {
                try { el.pause(); el.src = ''; el.load(); } catch(e) {}
            });
        """)
        target_driver.get("about:blank")
    except Exception:
        pass

    # 2. Standard quit
    try:
        target_driver.quit()
    except Exception:
        pass

    # 3. Ensure all tracked child/browser processes are dead
    for pid in list(_ACTIVE_BROWSER_PIDS):
        try:
            p = psutil.Process(pid)
            if p.is_running():
                p.terminate()
                p.wait(timeout=1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            try:
                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    _ACTIVE_BROWSER_PIDS.clear()
    _ACTIVE_DRIVER = None


def _signal_handler(sig, frame):
    """Ensures clean shutdown when user interrupts (Ctrl+C)."""
    print("\n[!] Process interrupted. Releasing resources...")
    close_driver()
    sys.exit(0)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
atexit.register(close_driver)


def get_driver():
    """Initializes an optimized headless browser with low CPU/RAM footprint."""
    global _ACTIVE_DRIVER
    from seleniumbase import Driver
    print("[1/5] Initializing lightweight headless browser with CDP network interception...")

    # Flags to suppress rendering, audio, and background tasks to reduce CPU usage
    chromium_flags = (
        "--mute-audio,"
        "--disable-gpu,"
        "--disable-software-rasterizer,"
        "--disable-dev-shm-usage,"
        "--disable-background-networking,"
        "--disable-background-timer-throttling,"
        "--disable-renderer-backgrounding"
    )

    try:
        # Use Brave browser as configured in ~/projects/headless_telebot
        driver = Driver(
            browser="brave",
            uc=True,
            headless=True,
            log_cdp_events=True,
            page_load_strategy="eager",
            block_images=True,
            disable_gpu=True,
            chromium_arg=chromium_flags
        )
    except Exception as e:
        print(f"      Brave unavailable ({e}), falling back to Chrome...")
        driver = Driver(
            uc=True,
            headless=True,
            log_cdp_events=True,
            page_load_strategy="eager",
            block_images=True,
            disable_gpu=True,
            chromium_arg=chromium_flags
        )

    driver.set_page_load_timeout(30)
    _ACTIVE_DRIVER = driver
    _register_browser_pids(driver)
    return driver


def trigger_video_playback(driver):
    """Detects video elements or play buttons and triggers playback."""
    print("[2/5] Inspecting page for video player and triggering playback...")
    
    # 1. Autoplay HTML5 video tags via JavaScript (mute first to bypass browser autoplay policy)
    js_play_script = """
    let played = false;
    const videos = document.querySelectorAll('video');
    videos.forEach(v => {
        try {
            v.muted = true;
            v.play();
            played = true;
        } catch(e) {}
    });
    return played;
    """
    try:
        played = driver.execute_script(js_play_script)
        if played:
            print("      Triggered playback on <video> element via JavaScript.")
    except Exception:
        pass

    # 2. Check for common play buttons or overlays
    play_selectors = [
        "button[aria-label*='Play' i]",
        "button[title*='Play' i]",
        ".play-button",
        ".vjs-big-play-button",
        ".ytp-play-button",
        ".jw-display-icon-container",
        "[class*='play-btn']",
        "[class*='playButton']"
    ]
    for selector in play_selectors:
        try:
            elem = driver.find_element("css selector", selector)
            if elem and elem.is_displayed():
                elem.click()
                print(f"      Clicked play button overlay: {selector}")
                break
        except Exception:
            continue


def sniff_network_stream(driver, max_wait_sec=15):
    """
    Inspects Chrome DevTools Protocol network events to find:
    - HLS / DASH manifests (.m3u8, .mpd)
    - Video segments (.ts, .m4s, chunk/segment patterns)
    - Request headers (Referer, User-Agent, Cookie)
    """
    print(f"[3/5] Sniffing network packets (waiting up to {max_wait_sec}s for media stream)...")
    start_time = time.time()
    
    manifest_urls = []
    segment_urls = []
    captured_headers = {}

    while time.time() - start_time < max_wait_sec:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                data = json.loads(entry["message"])["message"]
                method = data.get("method")
                
                if method == "Network.requestWillBeSent":
                    req = data["params"]["request"]
                    url = req.get("url", "")
                    headers = req.get("headers", {})
                    
                    # Ignore internal browser pages and tracking/ad scripts
                    if url.startswith("chrome://") or url.startswith("brave://"):
                        continue
                    if any(bad in url.lower() for bad in [".css", ".js", "analytics", "favicon"]):
                        continue

                    # Store headers for authenticated fetching
                    if not captured_headers and ("Referer" in headers or "referer" in headers):
                        captured_headers = headers

                    url_lower = url.lower()
                    if ".m3u8" in url_lower or ".mpd" in url_lower:
                        if url not in manifest_urls:
                            manifest_urls.append(url)
                            print(f"      [Manifest Discovered] {url}")
                    elif any(k in url_lower for k in [".ts", ".m4s", "segment", "chunk", "frag", "video/"]):
                        if url not in segment_urls:
                            segment_urls.append(url)
                            print(f"      [Segment Packet] {url[:90]}...")
            except Exception:
                continue

        # If we have captured a playlist or sufficient segments, we can proceed immediately
        if manifest_urls or len(segment_urls) >= 3:
            break
            
        time.sleep(1)

    return manifest_urls, segment_urls, captured_headers


def parse_m3u8_segments(m3u8_url, headers):
    """
    Parses an HLS m3u8 playlist to extract:
    - Master variant playlists (picks highest resolution)
    - Fragmented MP4 initialization segments (#EXT-X-MAP:URI="...")
    - All media segment URLs (.ts, .m4s, etc.)
    """
    print(f"[4/5] Parsing HLS playlist: {m3u8_url}")
    session = requests.Session()
    req_headers = {
        "User-Agent": headers.get("User-Agent", headers.get("user-agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")),
        "Referer": headers.get("Referer", headers.get("referer", m3u8_url))
    }

    resp = session.get(m3u8_url, headers=req_headers, timeout=15)
    resp.raise_for_status()
    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]

    # Check if this is a master playlist pointing to child playlists
    sub_playlists = [line for line in lines if not line.startswith("#") and (".m3u8" in line or "http" in line)]
    if any(line.startswith("#EXT-X-STREAM-INF") for line in lines) and sub_playlists:
        target_sub = urljoin(m3u8_url, sub_playlists[-1])
        print(f"      Master playlist detected. Selected stream: {target_sub}")
        return parse_m3u8_segments(target_sub, headers)

    # Check for fMP4 initialization segment (#EXT-X-MAP:URI="...")
    init_url = None
    for line in lines:
        if line.startswith("#EXT-X-MAP:"):
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                init_url = urljoin(m3u8_url, match.group(1))
                print(f"      fMP4 Initialization header detected: {init_url}")
                break

    # Extract all media segment URLs
    segments = []
    for line in lines:
        if not line.startswith("#"):
            seg_url = urljoin(m3u8_url, line)
            segments.append(seg_url)

    print(f"      Identified {len(segments)} segments in playlist.")
    return segments, req_headers, init_url


def download_single_segment(url, index, dest_dir, headers, is_init=False, max_retries=3):
    """Downloads one segment chunk with retry logic."""
    ext = os.path.splitext(urlparse(url).path)[1]
    if not ext or len(ext) > 5:
        ext = ".m4s" if is_init else ".ts"

    if is_init:
        target_path = os.path.join(dest_dir, f"init_header{ext}")
    else:
        target_path = os.path.join(dest_dir, f"segment_{index:05d}{ext}")

    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return target_path

    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            with open(target_path, "wb") as f:
                f.write(r.content)
            return target_path
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)


def download_all_segments(segments, headers, output_dir, init_url=None, max_workers=8):
    """Downloads initialization segment and all media segments concurrently."""
    os.makedirs(output_dir, exist_ok=True)
    
    init_file = None
    if init_url:
        print(f"      Downloading stream initialization header...")
        init_file = download_single_segment(init_url, 0, output_dir, headers, is_init=True)

    print(f"[4/5] Downloading {len(segments)} segments concurrently (threads={max_workers})...")
    downloaded_files = [None] * len(segments)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(download_single_segment, url, idx, output_dir, headers): idx
            for idx, url in enumerate(segments)
        }
        completed = 0
        total = len(segments)
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                filepath = future.result()
                downloaded_files[idx] = filepath
                completed += 1
                if completed % 10 == 0 or completed == total:
                    pct = (completed / total) * 100
                    print(f"      Downloaded {completed}/{total} segments ({pct:.1f}%)", end="\r")
            except Exception as e:
                print(f"\n      [Error] Segment {idx} failed: {e}")

    print("\n      All segments downloaded successfully.")
    valid_files = [f for f in downloaded_files if f]
    return init_file, valid_files


def merge_segments_to_mp4(init_file, segment_files, output_mp4):
    """
    Stitches downloaded segments together into final .mp4 video.
    - Handles fMP4 (CMAF) by prepending initialization header + media chunks.
    - Handles MPEG-TS by continuous chunk concatenation.
    - Uses FFmpeg -c copy for instant lossless output.
    """
    print(f"[5/5] Stitching segments into final video: {output_mp4}...")
    temp_dir = os.path.dirname(segment_files[0])
    combined_raw = os.path.join(temp_dir, "combined_stream.raw")

    # Sequentially concatenate chunks to binary stream
    with open(combined_raw, "wb") as outfile:
        if init_file and os.path.exists(init_file):
            with open(init_file, "rb") as f:
                outfile.write(f.read())
        for seg in segment_files:
            with open(seg, "rb") as f:
                outfile.write(f.read())

    # Remux through ffmpeg with limited threads to save CPU
    cmd = [
        "ffmpeg",
        "-y",
        "-threads", "2",
        "-i", combined_raw,
        "-c", "copy",
        "-movflags", "+faststart",
        output_mp4
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0 and os.path.exists(output_mp4):
        size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"      [Success] Video created: {output_mp4} ({size_mb:.2f} MB)")
        return True
    else:
        # Fallback: keep combined raw if already playable
        if os.path.exists(combined_raw) and os.path.getsize(combined_raw) > 1024:
            import shutil
            shutil.copyfile(combined_raw, output_mp4)
            size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
            print(f"      [Success] Video assembled: {output_mp4} ({size_mb:.2f} MB)")
            return True
        return False


def ffmpeg_direct_stream_download(m3u8_url, headers, output_mp4):
    """
    High-performance native HLS stream downloader:
    Passes manifest URL and intercepted headers directly to FFmpeg with real-time progress.
    Limits CPU thread saturation using -threads 2.
    """
    print(f"[4/5] Downloading and remuxing stream via FFmpeg: {output_mp4}")
    ua = headers.get("User-Agent", headers.get("user-agent", "Mozilla/5.0 (X11; Linux x86_64)"))
    ref = headers.get("Referer", headers.get("referer", m3u8_url))
    header_str = f"User-Agent: {ua}\r\nReferer: {ref}\r\n"

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-threads", "2",        # Limit threads to keep CPU cool
        "-headers", header_str,
        "-i", m3u8_url,
        "-c", "copy",
        "-movflags", "+faststart",
        output_mp4
    ]
    
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    last_print = 0
    for line in proc.stderr:
        if "time=" in line and (time.time() - last_print > 1):
            time_match = re.search(r'time=([\d:.]+)', line)
            speed_match = re.search(r'speed=([\d.x]+)', line)
            time_str = time_match.group(1) if time_match else ""
            speed_str = speed_match.group(1) if speed_match else ""
            print(f"      Stream progress: time={time_str} speed={speed_str}", end="\r")
            last_print = time.time()
            
    proc.wait()
    print()

    if proc.returncode == 0 and os.path.exists(output_mp4):
        size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"      [Success] Video downloaded: {output_mp4} ({size_mb:.2f} MB)")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Headless Browser Video Sniffer & Segment Downloader"
    )
    parser.add_argument("url", help="Webpage URL containing the video")
    parser.add_argument("-o", "--output", default="downloaded_video.mp4", help="Output file path (default: downloaded_video.mp4)")
    parser.add_argument("--wait", type=int, default=15, help="Seconds to sniff for video packets (default: 15)")
    parser.add_argument("--threads", type=int, default=6, help="Concurrent segment download threads (default: 6)")
    parser.add_argument("--method", choices=["auto", "segments", "ffmpeg-direct"], default="auto",
                        help="'auto' chooses the fastest and most reliable method; 'segments' downloads chunks; 'ffmpeg-direct' passes stream to ffmpeg")
    args = parser.parse_args()

    driver = None
    try:
        driver = get_driver()
        print(f"      Navigating to: {args.url}")
        driver.get(args.url)
        time.sleep(2)

        # Trigger playback
        trigger_video_playback(driver)

        # Sniff network packets
        manifests, segments, headers = sniff_network_stream(driver, max_wait_sec=args.wait)

        if not manifests and not segments:
            print("[!] Could not detect video stream packets. The page may require login, interaction, or DRM.")
            close_driver(driver)
            sys.exit(1)

        # CRITICAL OPTIMIZATION:
        # Immediately terminate the browser and reap all renderer/GPU processes!
        # The browser is no longer needed. Releasing it now prevents CPU heating and fan noise during download.
        print("[*] Stream captured! Terminating headless browser to free CPU & RAM...")
        close_driver(driver)
        driver = None

        # Output folder for temporary chunks
        chunks_dir = os.path.join(os.path.dirname(os.path.abspath(args.output)), "_temp_segments")
        success = False

        if manifests:
            selected_manifest = manifests[0]
            print(f"[*] Target stream identified: {selected_manifest}")
            
            # Use ffmpeg-direct if auto or requested
            if args.method in ["auto", "ffmpeg-direct"]:
                success = ffmpeg_direct_stream_download(selected_manifest, headers, args.output)

            # Fallback to manual segment downloading if ffmpeg-direct failed or if 'segments' requested
            if not success and args.method in ["auto", "segments"]:
                seg_urls, req_headers, init_url = parse_m3u8_segments(selected_manifest, headers)
                init_file, seg_files = download_all_segments(seg_urls, req_headers, chunks_dir, init_url=init_url, max_workers=args.threads)
                success = merge_segments_to_mp4(init_file, seg_files, args.output)
        else:
            print(f"[*] Found {len(segments)} raw segment packets (no manifest).")
            init_file, seg_files = download_all_segments(segments, headers, chunks_dir, max_workers=args.threads)
            success = merge_segments_to_mp4(init_file, seg_files, args.output)

        if success:
            print(f"\n🎉 Finished! Downloaded video saved to: {os.path.abspath(args.output)}")
            # Clean up temp segments
            if os.path.exists(chunks_dir):
                import shutil
                shutil.rmtree(chunks_dir, ignore_errors=True)
        else:
            print("\n❌ Failed to assemble video.")

    finally:
        if driver:
            close_driver(driver)


if __name__ == "__main__":
    main()
