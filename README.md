# Video Sniffer & Segment Downloader

An autonomous video sniffing and segment downloading utility designed for web video streams.

It launches a headless browser (Brave / Chrome via SeleniumBase), bypasses autoplay restrictions, inspects low-level network packets via Chrome DevTools Protocol (`CDP`), identifies streaming manifests (`.m3u8`, `.mpd`) and segment chunks (`.m4s`, `.ts`), and losslessly merges them into a single playable `.mp4` video.

---

## 🚀 Key Features

* **CDP Network Packet Sniffing:** Captures media manifests and transport packets at the browser layer (`Network.requestWillBeSent`), uncovering stream URLs even behind obfuscated or single-page application (SPA) players.
* **Autoplay & Player Detection:** Automatically unmutes and starts `<video>` elements via JavaScript and clicks standard player overlay buttons.
* **Modern Streaming Format Support:**
  * **Fragmented MP4 (fMP4 / CMAF):** Automatically detects and downloads `#EXT-X-MAP:URI="init.mp4"` initialization headers to prevent track header errors.
  * **Legacy MPEG-TS:** Supports classic `.ts` chunk streaming and sequential concatenation.
  * **Wide Codec Compatibility:** Supports AV1, H.264, H.265/HEVC, VP9, and AAC/MP3 audio.
* **Lossless Fast Remuxing:** Uses FFmpeg stream copy (`-c copy -movflags +faststart`) to assemble multi-gigabyte videos in seconds without re-encoding or quality degradation.
* **Zero Configuration:** Operates completely credential-free without `.env` files or third-party API dependencies.

---

## 📁 Project Structure

```text
video/
├── docs/                         # Documentation & Architecture records
│   └── adr/                      # Architecture Decision Records (ADRs)
│       ├── README.md             # ADR index table
│       ├── 0001-record-architecture-decisions.md
│       ├── 0002-headless-browser-cdp-network-sniffing.md
│       ├── 0003-fmp4-initialization-and-hybrid-assembly.md
│       ├── 0004-zero-secret-configuration-no-env.md
│       ├── 0005-modular-directory-structure.md
│       └── template.md           # Template for new ADRs
├── scripts/                      # Execution wrappers and shell automation
│   └── run.sh                    # Runner pre-configured with Python venv
├── src/                          # Core Python application logic
│   └── video_sniffer_downloader.py # Sniffer, parser, downloader, and merger
├── downloaded_files/             # Default destination directory for downloaded media
├── .agents/                      # Engineering standards, playbooks, and AI skills
├── AGENTS.md                     # Engineering pairing guidelines
└── README.md                     # Project documentation
```

---

## ⚡ Quick Start

### Basic Usage

Run the runner script from anywhere, passing the video page URL:

```bash
./scripts/run.sh "https://example.com/watch-video" -o my_video.mp4
```

Or save directly to `downloaded_files/`:

```bash
./scripts/run.sh "https://example.com/watch-video" -o downloaded_files/my_video.mp4
```

### Command Line Options

```bash
./scripts/run.sh --help

positional arguments:
  url                   Webpage URL containing the video

options:
  -h, --help            Show this help message and exit
  -o, --output OUTPUT   Output file path (default: downloaded_video.mp4)
  --wait WAIT           Seconds to sniff for video packets (default: 15)
  --threads THREADS     Concurrent segment download threads (default: 8)
  --method {auto,segments,ffmpeg-direct}
                        'auto' (default) selects the best stream pipeline;
                        'ffmpeg-direct' passes stream directly to ffmpeg;
                        'segments' manually downloads all chunks with EXT-X-MAP init support.
```

---

## 🛠️ How It Works

```
Target URL ──► Headless Browser (Brave/Chrome via SeleniumBase)
                     │
                     ├─► Find & Autoplay Video Player (HTML5 / Play Button)
                     │
                     ▼
           CDP Network Sniffer (Chrome DevTools Protocol)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  Stream Manifest (.m3u8/.mpd)   Segment Packets (.ts/.m4s)
         │                       │
         └───────────┬───────────┘
                     ▼
           Segment Pattern Resolver & Headers Extractor
                     ▼
       Concurrent Segment Downloader (ThreadPool)
                     ▼
       Lossless Remux & Merge via FFmpeg ──► output.mp4
```

1. **Browser Initialization:** Starts an undetected headless browser (`SeleniumBase`) with `log_cdp_events=True` to observe all transport layer network traffic.
2. **Playback Trigger:** Executes DOM scripts to unmute and trigger `.play()` on `<video>` elements, bypassing strict browser autoplay restrictions.
3. **CDP Sniffing:** Analyzes performance logs for manifest URLs (`.m3u8`, `.mpd`) and media chunks (`.ts`, `.m4s`), extracting essential CDN headers (`Referer`, `User-Agent`).
4. **Stream Processing:**
   - **Auto Mode (Default):** Directly streams the intercepted manifest via FFmpeg with real-time ETA and speed telemetry.
   - **Segment Mode:** Downloads the `#EXT-X-MAP` initialization header (if fMP4) plus all numbered media segments in parallel via a thread pool, sequentially chains the binary stream, and finalizes with `-movflags +faststart`.

---

## 🔒 Configuration & Environment

* **No `.env` Required:** This tool operates entirely client-side using browser automation and direct media streams. It does not require API keys, credentials, or third-party service tokens (see [ADR-0004](docs/adr/0004-zero-secret-configuration-no-env.md)).
* **Dependencies:**
  - Python 3 with `seleniumbase` and `requests`.
  - System binaries: `ffmpeg` and `brave-browser` (or `google-chrome`).

---

## 📜 Architecture Decisions

All significant architectural choices are documented in [`docs/adr/`](docs/adr/README.md):

| ADR | Title | Status | Date |
|:---:|:------|:------:|:----:|
| [0001](docs/adr/0001-record-architecture-decisions.md) | Record Architecture Decisions | accepted | 2026-10-20 |
| [0002](docs/adr/0002-headless-browser-cdp-network-sniffing.md) | Headless Browser Automation with CDP Network Sniffing | accepted | 2026-10-21 |
| [0003](docs/adr/0003-fmp4-initialization-and-hybrid-assembly.md) | Fragmented MP4 (fMP4/CMAF) Initialization & Hybrid Assembly | accepted | 2026-10-21 |
| [0004](docs/adr/0004-zero-secret-configuration-no-env.md) | Zero Secret Configuration (No .env Dependency) | accepted | 2026-10-22 |
| [0005](docs/adr/0005-modular-directory-structure.md) | Modular Directory Structure (src, scripts, docs) | accepted | 2026-10-22 |
| [0006](docs/adr/0006-lifecycle-cleanup-and-resource-optimization.md) | Lifecycle Process Cleanup & CPU Resource Optimization | accepted | 2026-10-22 |
