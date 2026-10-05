# Site Privacy (Blur outside Geofence): motion product video

86 s, 1920x1080, 30 fps. FlytBase brand: charcoal base, Signal Orange accent, Lora / Geist / Geist Mono, sharp corners.
Footage: FlytBase "Introducing Site Privacy" (YouTube, 720p max), cropped clean into `assets/clips/`.
Copy follows releases.flytbase.com/september-2026/blur-outside-geofence-customer-guide.

| Time | Scene |
|---|---|
| 0-5 | Hook: "Your drone sees [clip] hundreds of metres out. Including what isn't yours." |
| 5-9 | Title: Site Privacy / Blur outside Geofence, over the real blurred feed |
| 9-18 | The reach: rebuilt Cockpit panel, zoom 1x -> 14x, callouts on neighbouring property |
| 18-26.5 | Video overlays menu (rebuilt) -> Zone overlays on -> geofence on live video + map |
| 26.5-32.5 | "The drone stays inside the line. The camera doesn't." |
| 32.5-37.5 | One switch: Blur outside Geofence (BETA) |
| 37.5-45.5 | Before/after wipe on the identical frame |
| 45.5-56.5 | Moves with drone / gimbal / zoom; fully outside -> private; swing back -> focus |
| 56.5-62 | Zone labels stay on top · remembered · off in one click |
| 62-68.5 | How to turn it on (4 steps) |
| 68.5-75 | What you need: synced geofence, Fast link, Chrome/Edge + WebGPU, drone in flight |
| 75-80.5 | Live view only; a visual aid, not a guarantee (falls back to the clear view) |
| 80.5-86 | "It only shows what's yours." + FlytBase logo |

Footage `<video>` tags are authored statically at the top of `#root` (HyperFrames pre-extracts frames from markup;
never create them in JS or nest them inside a timed `.clip`). The script only positions and shows them.

Render: `npx hyperframes@0.8.59 render --fps 30 --quality delivery -o out.mp4`, then mux the synthesized
pulse/effects track with `-af loudnorm=I=-16:TP=-1.5:LRA=11`.
