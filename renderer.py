from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import math
import shutil
import subprocess
import tempfile


# TODO: try and figure out how to use ffmpeg svg_pipe, maybe I can get rid of
#    rasterizing the frames entirely.
# TODO: Try and figure out the parallizing code. It doesn't work the way I
#    think it does.
# TODO: Still need to test scroll y, and fade
# TODO: Are there any other behaviors I need?
#    - teleport might be cool

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def get_number(node, key, default=0.0):
  v = node.attrib.get(f"data-{key}")
  return float(v) if v is not None else default


def get_bool(node, key, default=False):
  v = node.attrib.get(f"data-{key}")
  return v.lower() == "true" if v is not None else default


def clamp(v, a, b):
  return max(a, min(b, v))


def format_time(seconds):
  seconds = max(0, int(seconds))
  return f"{seconds // 60}:{seconds % 60:02d}"


def get_timeline(node, t):
  delay = get_number(node, "delay", 0)
  duration = get_number(node, "duration", math.inf)
  loop = get_bool(node, "loop", False)

  local = t - delay

  if local < 0:
    return {"active": False, "t": 0, "progress": 0}

  if loop and math.isfinite(duration) and duration > 0:
    local %= duration

  progress = (
    clamp(local / duration, 0, 1)
    if math.isfinite(duration)
    else 0
  )

  return {
    "active": True,
    "t": local,
    "progress": progress,
  }


def behavior_scroll_x(node, tl):
  fx = get_number(node, "from-x", 0)
  tx = get_number(node, "to-x", 0)
  x = fx + (tx - fx) * tl["progress"]
  node.set("transform", f"translate({x}, 0)")


def behavior_scroll_y(node, tl):
  fy = get_number(node, "from-y", 0)
  ty = get_number(node, "to-y", 0)
  y = fy + (ty - fy) * tl["progress"]
  node.set("transform", f"translate({y}, 0)")


def behavior_flash(node, tl):
  freq = get_number(node, "frequency", 1)
  phase = (tl["t"] % freq) / freq
  opacity = "1" if phase < 0.5 else "0"
  node.set("opacity", opacity)


def behavior_countdown(node, tl):
  start = get_number(node, "start", 60)
  remaining = max(0, start - tl["t"])
  node.text = format_time(remaining)


def behavior_countup(node, tl):
  max_t = get_number(node, "max", math.inf)
  elapsed = min(max_t, tl["t"])
  node.text = format_time(elapsed)


def behavior_fade(node, tl):
  f = get_number(node, "from-opacity", 0)
  t = get_number(node, "to-opacity", 1)
  op = f + (t - f) * tl["progress"]
  style = node.attrib.get("style", "")
  node.set("style", style + f";opacity:{op}")


BEHAVIORS = {
  "scroll-x": behavior_scroll_x,
  "scroll-y": behavior_scroll_y,
  "flash": behavior_flash,
  "countdown": behavior_countdown,
  "countup": behavior_countup,
  "fade": behavior_fade,
}


def apply_animations(root, t):
  nodes = [n for n in root.iter() if "data-anim" in n.attrib]

  for node in nodes:
    tl = get_timeline(node, t)

    if not tl["active"]:
      continue

    for name in node.attrib["data-anim"].split():
      fn = BEHAVIORS.get(name)
      if fn:
        fn(node, tl)


def write_svg_frame(args):
  root, t, out_path = args

  frame = deepcopy(root)
  apply_animations(frame, t)

  ET.ElementTree(frame).write(
    out_path,
    encoding="utf-8",
    xml_declaration=True,
  )


def generate_svg_frames(scene_svg, svg_dir, fps, duration):
  tree = ET.parse(scene_svg)
  root = tree.getroot()

  total = fps * duration
  svg_dir.mkdir(parents=True, exist_ok=True)
  tasks = []

  for i in range(total):
    t = i / fps
    path = svg_dir / f"frame_{i:06d}.svg"
    tasks.append((root, t, path))

  for i, _ in enumerate(tasks):
    write_svg_frame(tasks[i])
    if i % fps == 0:
      print(f"SVG second {i // fps}")


def rasterize_one(svg_path, png_path):
  subprocess.run(
    ["resvg", str(svg_path), str(png_path)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=True,
  )


# I don't think this is actually working the way I think it does, I don't get it
def rasterize_parallel(svg_dir, png_dir, workers):
  svg_files = sorted(svg_dir.glob("frame_*.svg"))
  png_dir.mkdir(parents=True, exist_ok=True)

  with ProcessPoolExecutor(max_workers=workers) as pool:
    futures = []

    for svg in svg_files:
      png = png_dir / (svg.stem + ".png")
      futures.append(pool.submit(rasterize_one, svg, png))

    for i, f in enumerate(as_completed(futures)):
      f.result()
      if i % 30 == 0:
        print(f"Raster second {i // 30}")


def encode(png_dir, out, fps):
  subprocess.run(
    [
      "ffmpeg",
      "-y",
      "-framerate",
      str(fps),
      "-i",
      str(png_dir / "frame_%06d.png"),
      "-c:v",
      "libx264",
      "-pix_fmt",
      "yuv420p",
      "-crf",
      "18",
      "-preset",
      "medium",
      "-movflags",
      "+faststart",
      str(out),
    ],
    check=True,
  )


def render(scene_svg, output, fps, duration, workers):
  tmp = Path(tempfile.mkdtemp(prefix="svg_anim_"))
  svg_dir = tmp / "svg"
  png_dir = tmp / "png"

  try:
    print("Generating SVG...")
    generate_svg_frames(scene_svg, svg_dir, fps, duration)

    print("Rasterizing PNG...")
    rasterize_parallel(svg_dir, png_dir, workers)

    print("Encoding video...")
    encode(png_dir, output, fps)

    print(f"Done: {output}")

  finally:
    shutil.rmtree(tmp, ignore_errors=True)


def main():
  p = argparse.ArgumentParser()
  p.add_argument("--scene", required=True)
  p.add_argument("--output", default="out.mp4")
  p.add_argument("--fps", type=int, default=30)
  p.add_argument("--duration", type=int, required=True)
  p.add_argument("--workers", type=int, default=8)
  args = p.parse_args()

  render(
    Path(args.scene),
    Path(args.output),
    args.fps,
    args.duration,
    args.workers,
  )


if __name__ == "__main__":
  main()
