#!/usr/bin/env python3
"""Convert markdown file(s) into a self-contained reveal.js presentation.

Usage:
    python3 md_to_slides.py input.md [-o output.html] [--theme moon] [--title "My Talk"]
    python3 md_to_slides.py file1.md file2.md file3.md -o combined.html

Slide separators:
    ---        horizontal slide break (new section)
    --         vertical slide break (sub-slide within section)

Speaker notes: lines after "Note:" within a slide become speaker notes.

Themes: black (default), white, league, beige, night, moon, serif, simple, sky, solarized
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

REVEAL_CDN = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0"

THEMES = [
    "black", "white", "league", "beige", "night",
    "moon", "serif", "simple", "sky", "solarized",
]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-like frontmatter (key: value) from markdown. Returns (metadata, remaining text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 3:].strip()
    meta = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta, body


def split_slides(markdown: str) -> list[list[str]]:
    """Split markdown into sections (horizontal) and sub-slides (vertical).

    Returns a list of sections, where each section is a list of slide contents.
    """
    # Normalize line endings
    markdown = markdown.replace("\r\n", "\n")

    # Split on horizontal separator: a line that is exactly "---"
    # (but not frontmatter, which is already stripped)
    h_sections = re.split(r"\n---\n", markdown)

    result = []
    for section in h_sections:
        # Split on vertical separator: a line that is exactly "--"
        v_slides = re.split(r"\n--\n", section)
        result.append([s.strip() for s in v_slides if s.strip()])

    return [s for s in result if s]


def build_html(
    slides_md: str,
    title: str = "Presentation",
    theme: str = "black",
    custom_css: str = "",
) -> str:
    """Build a self-contained reveal.js HTML presentation."""
    escaped_md = html.escape(slides_md)
    theme = theme if theme in THEMES else "black"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{REVEAL_CDN}/dist/reset.css">
<link rel="stylesheet" href="{REVEAL_CDN}/dist/reveal.css">
<link rel="stylesheet" href="{REVEAL_CDN}/dist/theme/{theme}.css">
<link rel="stylesheet" href="{REVEAL_CDN}/plugin/highlight/monokai.css">
<style>
  .reveal h1, .reveal h2, .reveal h3 {{ text-wrap: balance; }}
  .reveal pre {{ width: 100%; }}
  .reveal pre code {{ max-height: 500px; }}
  .reveal img {{ max-height: 65vh; object-fit: contain; }}
  .reveal blockquote {{ font-style: italic; border-left: 4px solid rgba(255,255,255,0.3); padding-left: 1em; }}
  .reveal table {{ margin: 0 auto; border-collapse: collapse; }}
  .reveal th, .reveal td {{ border: 1px solid rgba(255,255,255,0.3); padding: 0.4em 0.8em; }}
  .reveal ul, .reveal ol {{ display: block; text-align: left; }}
  {custom_css}
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">
    <section data-markdown data-separator="^---$" data-separator-vertical="^--$" data-separator-notes="^Note:">
      <textarea data-template>
{escaped_md}
      </textarea>
    </section>
  </div>
</div>
<script src="{REVEAL_CDN}/dist/reveal.js"></script>
<script src="{REVEAL_CDN}/plugin/markdown/markdown.js"></script>
<script src="{REVEAL_CDN}/plugin/highlight/highlight.js"></script>
<script src="{REVEAL_CDN}/plugin/notes/notes.js"></script>
<script src="{REVEAL_CDN}/plugin/math/math.js"></script>
<script>
Reveal.initialize({{
  hash: true,
  slideNumber: true,
  transition: 'slide',
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes, RevealMath.KaTeX]
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to reveal.js slides")
    parser.add_argument("inputs", nargs="+", help="Markdown file(s)")
    parser.add_argument("-o", "--output", help="Output HTML file (default: <input>.html)")
    parser.add_argument("--theme", default=None, help=f"Theme: {', '.join(THEMES)}")
    parser.add_argument("--title", default=None, help="Presentation title")
    parser.add_argument("--css", default="", help="Extra CSS to inject")
    args = parser.parse_args()

    # Read and concatenate inputs
    parts = []
    first_meta = {}
    for i, path in enumerate(args.inputs):
        p = Path(path)
        if not p.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)
        text = p.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        if i == 0:
            first_meta = meta
        parts.append(body)

    combined = "\n---\n".join(parts)

    title = args.title or first_meta.get("title", Path(args.inputs[0]).stem)
    theme = args.theme or first_meta.get("theme", "black")

    html_out = build_html(combined, title=title, theme=theme, custom_css=args.css)

    out_path = args.output or Path(args.inputs[0]).with_suffix(".html")
    Path(out_path).write_text(html_out, encoding="utf-8")
    print(f"Created: {out_path}")


if __name__ == "__main__":
    main()
