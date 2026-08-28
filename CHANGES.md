# CHANGES

**Every image made for the animation, why it exists, and whether it went into the film.**

Newest at the bottom. Nothing is deleted from this log, including things that were rejected, because
knowing what was tried is worth as much as knowing what was kept.

Format:

```
## <date>  scene <n>

- `<file>` — what it is, and why. **accepted into the film** / **proposal** / **rejected, reason**
```

---

## 19.8.2026  folder opened

Marko met Kristijan. Scene 1 first: variations of existing frames, and extra frames where a cut needs
a step in between once it moves. Nothing made yet.

## 27.08.2026  inbox

- `1-3_v2_watchtest.jpg` — no frame number in the name, so it went to inbox, 2752x1536 cropped to 2731x1536. **proposal**
- `2-5_watchtest_FG.png` — no frame number in the name, so it went to inbox, transparent, left alone. **proposal**
- `WATCHTEST_notes.txt` — no frame number in the name, so it went to inbox. **proposal**

## 27.08.2026  inbox

- `WATCHTEST_notes.txt` — no frame number in the name, so it went to inbox. **proposal**

## 27.08.2026  scene 1

- `1-3_v2_watchtest.jpg` — frame 1-3, 2752x1536 cropped to 2731x1536. **proposal**

## 27.08.2026  scene 2

- `2-5_watchtest_FG.png` — frame 2-5, transparent, left alone. **proposal**

## 28.08.2026  scene 1

- `1-1-v2.png` — frame 1-1, 2752x1536 cropped to 2731x1536. **proposal**

## 28.08.2026  inbox

- `4-BRAIN_BRAKE_READ_THROUGH_v4.pdf` — no frame number in the name, so it went to inbox. **proposal**

## 28.08.2026  moved to its own repository

Everything above happened in `BRAIN_BRAKE/animator/`. On 28.8.2026 the whole folder moved here, to
`ANIMATOR_COLLABORATION`, because `BRAIN_BRAKE` had reached about 1.4 GB and pushes were failing on
size. The scene folders are now `BB_C_1` to `BB_C_8` instead of `scene_01` to `scene_08`. Nothing was
renamed and nothing was lost, only moved. This log continues.

## 28.08.2026  scene 3

- `3-2_v2_step51test.jpg` — frame 3-2, 2752x1536 cropped to 2731x1536. **proposal**

## 28.08.2026  inbox

- `STEP51_no_frame_number.png` — no frame number in the name, so it went to inbox, 800x600 cropped to 2731x1536. **proposal**

## 28.08.2026  the two lines above were a test

`3-2_v2_step51test.jpg` and `STEP51_no_frame_number.png` were dropped into the watch folder to prove
it pushes here now instead of into `BRAIN_BRAKE`. Both files are **removed from the repository**. The
lines stay, because nothing is deleted from this log.

## 28.08.2026  scene 1

- `1-1-v3.png` — frame 1-1, 2752x1536 cropped to 2731x1536. **proposal**

## 28.08.2026  scene 1

- `1-1-v4.png` — frame 1-1, arrived 2752x1536 and was **not** cropped to 2731x1536. **proposal**
- `1-1-v5.png` — frame 1-1, arrived 2752x1536 and was **not** cropped to 2731x1536. **proposal**
- `1-1-v6.png` — frame 1-1, arrived 2752x1536 and was **not** cropped to 2731x1536. **proposal**

These three lines were written by hand on 28.8.2026, after the fact. The watch folder logged
`1-1-v2.png` and `1-1-v3.png` and cropped both, then logged nothing for v4, v5 and v6 and cropped
none of them. The files were left exactly as they arrived rather than being cropped in place,
because all three had already been pushed and a published file is never overwritten. They will be
reissued at the correct width under new numbers.

## 28.08.2026  scene 1 cleared to a clean slate

Scene 1 is being rebuilt from scratch, so every version of frame 1.1 came **off the site**:
`1-1-v2.png`, `1-1-v3.png`, `1-1-v4.png`, `1-1-v5.png`, `1-1-v6.png`. They are removed from
`catalog.json` only. **The files are still in the repository and every link to them still works**,
because a file that has left the machine is never deleted and never overwritten. The lines above stay
too. What changed is only what the animator is asked to look at.

- `CHARACTER_SHEET_RUNNER-v1.jpg` — the marathon runner, four views, front / three quarter / profile /
  rear. Added as the first thing on the scene 1 page, above the frames. **reference**

The scene page now carries a **Character sheet** section above a **Frames** section, and the two tick
boxes, need a breakdown and need a modification, are on every picture on the site including sheets.

## 28.08.2026  the frame becomes its own layer

- `FRAME_BORDER-v1.png` — the panel border alone, transparent middle, 2731x1536 RGBA. **reference**

It was **not generated and cost nothing.** It was cut out of `V7_7_1_apart.jpg`, which was chosen by
measurement as the donor with a complete border on all four sides and the least ink inside it, 2.2%.
The alpha comes from ink depth and is then kept only in a band along the rectangle, which is what
guarantees the middle is empty rather than merely looking empty. Verified: zero non transparent
pixels anywhere inside the rectangle, and all four sides between 27% and 30% coverage.

Because it is cut from the film's own artwork it carries the same hand, the same wobble and the same
graphite as everything it goes over, which a redrawn rectangle never would.

It sits on the landing page under **The frame**, on a checkerboard so the transparency is visible,
with a download link and the same two tick boxes as everything else.

## 28.08.2026  the frame, corrected

- `FRAME_BORDER-v2.png` — the frame as a **matte**: solid paper margin and solid line, transparent
  window in the middle. 2731x1536 RGBA. **reference**

v1 was the wrong shape for the job. It was the line alone with everything around it transparent, so
laid over a frame it drew a line and did nothing else. What is actually wanted is a matte that cuts
its own window: the artwork shows through the middle and the margin and the border come from the
overlay. Marko sent a picture of what it should look like and that settled it in one look.

The window edge follows the hand drawn wobble exactly, because it was found by walking outward from
the centre of a real drawing until it hit the line, rather than by drawing a rectangle. The two
figures standing inside the donor frame were swallowed by filling the holes in that region.

v1 is kept and its link still works.

## 28.08.2026  scene, shot, key frame

The site now has three levels instead of two, matching how the film is actually being made.

    scene -> shot -> key frame

A **scene page** shows one representative picture per shot. Clicking it opens a **shot page** holding
every key frame in that shot, including the representative one, and that is where the breakdown and
modification tick boxes now live. Asking for a change is a thing you do to a key frame, so it belongs
next to the key frame and not next to a shot.

`shot-1-1.html` and so on are generated from `catalog.json` like everything else. A key frame is an
entry with `"kind": "keyframe"` and a `"shot"`, and one of them per shot carries
`"representative": true`. If none does, the newest one that is not retired stands for the shot, so a
shot always has a face.

**The rule at the top.** `"working_scene"` in the catalog names the scene being worked on. That scene
page and its shot pages carry the rule strip saying so, and no other page does. Move the number and
the rule moves with it.

There are no shots catalogued yet. The structure is live and empty and waiting.

## 28.08.2026  plate, layer, composite

Anything that moves on its own now arrives as **three files, never one picture**:

    PLATE      the drawing with the moving thing taken out of it
    LAYER      the moving thing alone, transparent everywhere else
    COMPOSITE  the two stacked, so there is never a question about where it sits

The pattern is shown on the scene 1 page under **How a layer arrives**, worked through with the frame
because the frame is the one that is already finished. The layer sits on a checkerboard so the
transparency is visible, and all three can be downloaded.

The sweat droplets on shot 1.1 arrive in exactly this shape: a plate with dry skin, the droplets on
their own transparency, and a composite.

Driven by `catalog.json` like everything else: an entry with `"kind": "example"` and `plate`, `layer`
and `composite` files. A `"scene"` key pins it to a scene page, no key leaves it on the landing page.

**One bug fixed on the way.** The What changed log assumed every catalogue entry has exactly one
`file`. An example has three, so the landing page stopped building the moment the first one was
added. It no longer assumes the shape of an entry.

## 28.08.2026  shot 1.1 locked, and the attempts that did not make it

**Shot 1.1 is `1-1-v11` → `1-1-v15` → `1-1-v18`.** Down and dying, lifting, sees it. One continuous
move with no cut, and the camera does not move: all three measure the same ink bounds, x 15% to 64%,
y 9% to 99%.

**Five attempts were rejected on the way. The files are all still in the repository and every link
still works.** They are off the shot page so nobody builds on a dead version, and they are listed
here because a version that failed is worth as much as one that did not.

- `1-1-v12.png` — framing drifted wider and more frontal than v11, and it grew sweat the others do
  not have. Sweat is its own layer, so it has to be absent or consistent.
- `1-1-v13.png` — wider and more frontal than the rest of the shot. Across a cutless rise that reads
  as the camera pulling back rather than the man lifting.
- `1-1-v14.png` — came back 2048 square. The aspect ratio had reset to 1:1 and cropped his shoulder
  off. The performance was right, so v15 is the same prompt run again at 16:9.
- `1-1-v16.png` — turned fully frontal and stared at camera. He has to be looking at something far
  ahead and out of frame, because the next shot cuts to what he sees. Looking at us breaks the cut.
- `1-1-v17.png` — angle and framing right, expression wrong. Wide eyes over an open mouth reads as
  shock, not recognition. v18 relaxed the whole face and lifted the corners of the mouth instead.

**The lesson in three of those five: the prompt caused it.** "Eyes wide open and fixed", "head fully
up", "shoulders squared" all pull toward a frontal stare. What was wanted was relief arriving.
