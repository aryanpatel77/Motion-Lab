# Site Privacy v2: light motion-graphics film (70 s, 1920x1080)

The structure mirrors the client reference (the Shapes HR launch film) technique for technique. The content is FlytBase's
Blur outside Geofence feature, taken from the customer guide and the "Introducing Site Privacy" video.

| Time | Reference technique | Here |
|---|---|---|
| 0-2.4 | Paper-collage opener, re-shuffling every 0.8 s | "Your drone / sees / everything." with blobs and drone stills |
| 2.4-4.6 | Sentence with inline photos opening between words | "Even [house] next [trucks] door?" |
| 4.6-6.7 | Typed beat, small lockup | "Not anymore." then the mascot and "Site Privacy" |
| 6.7-10.3 | Words split for a 3D card carousel | "Keep [homes, roads, vehicles, yards…] out of view" |
| 10.3-12.2 | Shape swirl collapsing into the mascot | Six shapes swirl, then the privacy-lens mascot |
| 12.2-18.2 | Mascot as cursor over rebuilt glass UI, camera pushes in | Live feed, then Video overlays, then Zone overlays on, then the geofence |
| 18.2-22.4 | Rolodex text with one focus line | "Your dock… The neighbour's backyard": "Not yours to see." |
| 22.4-25.4 | Clutter toggle, zoom through the knob | "Blur outside Geofence" toggle; the photos fly off |
| 25.4-31.4 | Card reveal | The blur falls on everything outside the boundary (before/after stills) |
| 31.4-34.4 | "Thinking" steps | Drone moves / gimbal turns / camera zooms, so the blur re-projects |
| 34.4-42.4 | Footage cards with chips and bubbles | Tracking, then fully outside (private), then swing back (focus) |
| 42.4-45.4 | Inline-photo sentence | "Same [before] flight. Same [after] camera." |
| 45.4-50.8 | Word split and carousel | "All you [geofence synced · Fast link · Chrome/Edge+WebGPU · in flight] need" |
| 50.8-56.2 | Mascot hopping a path | Four steps to turn it on |
| 56.2-60.6 | Glass notification that expands | Good to know: live view only, capture unchanged, a visual aid, safety first |
| 60.6-63.4 | Words split around a photo collage | "Privacy [stills] built in" |
| 63.4-67.0 | Words on rolling shape tokens | "It only / shows / what's / yours." |
| 67.0-70.0 | Shapes morph into the logo | Mascot and "Site Privacy", in FlytBase Cockpit |

Footage `<video>` tags are authored statically in `#root` and placed and moved by `vplace()` / `camTo()`, so they ride the
scene cameras. Render at 180 fps and blend 6 sub-frames per output frame for real motion blur:

```bash
npx hyperframes@0.8.59 render --fps 180 --quality delivery --workers 4 -o /tmp/sp2_180.mp4
ffmpeg -i /tmp/sp2_180.mp4 -i sfx.wav -filter_complex "[0:v]tmix=frames=6,select='eq(mod(n\,6)\,5)',setpts=N/30/TB[v]" \
  -map "[v]" -map 1:a -r 30 -c:v libx264 -crf 15 -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac out.mp4
```
