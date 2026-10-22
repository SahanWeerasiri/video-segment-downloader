# ADR-0002: Headless Browser Automation with CDP Network Sniffing

**Date**: 2026-10-21
**Status**: accepted
**Deciders**: Project Team

## Context

Many modern streaming and video hosting sites do not provide plain, static `<video src="...">` tags in their initial HTML response. Instead, they employ JavaScript-driven video players (Video.js, JWPlayer, custom players), dynamic iframe embeds, bot mitigation challenges, and client-side manifest hydration.

Static scrapers like `curl`, `requests`, or `BeautifulSoup` only fetch the unrendered HTML, failing to trigger the video player or observe the actual network packets and media stream URLs negotiated by the browser runtime.

## Decision

We use headless browser automation (`SeleniumBase` with undetected-chromedriver and Brave/Chrome browser fallback) coupled with Chrome DevTools Protocol (`CDP`) network interception (`log_cdp_events=True`, listening to `Network.requestWillBeSent`).

The pipeline navigates to the target page, triggers HTML5 video playback via JavaScript/simulated clicks, and captures network stream manifests (`.m3u8`, `.mpd`) and segment packets (`.ts`, `.m4s`) along with critical authentication headers (`Referer`, `User-Agent`).

## Alternatives Considered

### Alternative 1: Static HTTP Scraping (curl / requests)
- **Pros**: Extremely fast, lightweight, and requires no browser binary dependencies.
- **Cons**: Cannot execute client-side JavaScript, cannot interact with DOM overlays, and cannot solve client-side token handshakes.
- **Why not**: Ineffective for the vast majority of modern video platforms.

### Alternative 2: Dedicated Third-Party Downloaders Only (e.g. yt-dlp standalone)
- **Pros**: Extensive pre-built extractors for established platforms.
- **Cons**: Brittle against custom, unindexed, or rapidly changing video player platforms; fails when no dedicated site extractor exists.
- **Why not**: We need a generic network-level sniffer capable of capturing stream packets from arbitrary players.

### Alternative 3: MITM Proxy Interception (selenium-wire / mitmproxy)
- **Pros**: Deep inspection of request/response bodies.
- **Cons**: Requires local TLS/SSL root certificate installation, introduces proxy latency, and can trigger anti-bot certificate pinning alarms.
- **Why not**: Native CDP performance logging provides the necessary URL and header telemetry with zero proxy overhead.

## Consequences

### Positive
- Works on dynamic, obfuscated, and single-page application (SPA) players.
- Automatically captures essential request headers (`Referer`, `User-Agent`) needed to prevent CDN `403 Forbidden` responses.
- Reuses existing local browser binary (`Brave` / `Chrome`) and undetected driver setup.

### Negative
- Requires a local Chromium-based browser installation and headless driver overhead.
- Browser startup incurs a small latency penalty compared to raw socket requests.

### Risks
- **Risk**: Autoplay blocking policies in headless mode prevent media streaming.
- **Mitigation**: Injected JavaScript explicitly mutes video tags prior to calling `.play()`, adhering to browser autoplay policies.
