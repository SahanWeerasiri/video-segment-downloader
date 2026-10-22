# ADR-0003: Fragmented MP4 (fMP4/CMAF) Initialization & Hybrid Assembly

**Date**: 2026-10-21
**Status**: accepted
**Deciders**: Project Team

## Context

Streaming platforms have significantly shifted from legacy MPEG-TS (`.ts`) containers toward Fragmented MP4 (fMP4 / CMAF, using `.m4s` or `.mp4` chunks) for modern codecs like AV1, VP9, and HEVC.

In fragmented MP4 HLS streams, the initialization data (containing `ftyp`, `moov`, `tfhd`, and track metadata) is separated into a designated header chunk declared via `#EXT-X-MAP:URI="init.mp4"`.

Attempting to concatenate raw `.m4s` chunks without the initialization segment causes FFmpeg to fail with:
`trun track id unknown, no tfhd was found`.
Furthermore, standard FFmpeg concat demuxers (`-f concat -i concat_list.txt`) fail because individual `.m4s` media chunks do not contain standalone file headers.

## Decision

We implement a two-tier hybrid stream processing architecture:

1. **Primary Streaming Mode (`auto` / `ffmpeg-direct`):**
   When an `.m3u8` or `.mpd` manifest is intercepted, the script passes the manifest URL along with the sniffed `Referer` and `User-Agent` headers directly to FFmpeg. FFmpeg natively downloads and decodes fMP4 initialization maps, handles variant selection, adjusts timestamps, and remuxes with lossless stream copy (`-c copy -movflags +faststart`). Real-time progress is streamed to stdout.

2. **Fallback / Manual Chunk Mode (`segments`):**
   If direct streaming fails or manual segment assembly is selected, the manifest parser explicitly extracts `#EXT-X-MAP:URI="..."` to download the initialization segment. All chunks are downloaded concurrently via a thread pool, concatenated in binary sequence (`init + seg_1 + seg_2 ...`), and finalized via FFmpeg.

## Alternatives Considered

### Alternative 1: MPEG-TS Concat Demuxer Only
- **Pros**: Simple text-file-based playlist for FFmpeg concat.
- **Cons**: Completely breaks on fMP4 / CMAF streams (`trun track id unknown, no tfhd was found`).
- **Why not**: Modern streaming sites overwhelmingly use fMP4 for high-efficiency codecs.

### Alternative 2: Full Transcoding / Re-encoding
- **Pros**: Universal compatibility across malformed chunks.
- **Cons**: Extremely CPU/GPU intensive, slow, and causes video/audio generation loss.
- **Why not**: Lossless remuxing (`-c copy`) preserves 100% original stream quality and completes in seconds.

## Consequences

### Positive
- Robust compatibility across both legacy MPEG-TS (`.ts`) and modern Fragmented MP4 (`.m4s`, AV1, H.264, AAC).
- Native FFmpeg streaming provides fast, resilient throughput with real-time ETA and speed telemetry.
- Fallback chunk mode guarantees reliability even when direct streaming is network-throttled.

### Negative
- Direct FFmpeg streaming relies on a locally available `ffmpeg` binary.

### Risks
- **Risk**: CDN token expiry during multi-gigabyte video downloads.
- **Mitigation**: FFmpeg maintains active persistent HTTP keep-alive connections with the original signed manifest parameters.
