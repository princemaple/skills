#!/usr/bin/env python3
"""Convert markdown file(s) into a reveal.js presentation.

Usage:
    python3 md_to_slides.py input.md [-o output.html] [--theme moon] [--title "My Talk"]
    python3 md_to_slides.py input.md -o deck/ --theme white --custom-theme songri.css --logo logo.png

When --logo or --custom-theme is used, output is a directory with index.html and assets.
Otherwise output is a single HTML file.

Slide separators:
    ---        horizontal slide break (new section)
    --         vertical slide break (sub-slide within section)

Speaker notes: lines after "Note:" within a slide become speaker notes.

Themes: black (default), white, league, beige, night, moon, serif, simple, sky, solarized
"""

import argparse
import html
import re
import shutil
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


def build_html(
    slides_md: str,
    title: str = "Presentation",
    theme: str = "black",
    custom_css: str = "",
    custom_theme_href: str = "",
    logo_src: str = "",
) -> str:
    """Build a reveal.js HTML presentation."""
    escaped_md = html.escape(slides_md)
    theme = theme if theme in THEMES else "black"

    theme_link = f'<link rel="stylesheet" href="{custom_theme_href}">' if custom_theme_href else ""
    logo_block = f'<img class="slide-logo" src="{logo_src}" alt="logo">' if logo_src else ""

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
  .slide-logo {{ position: fixed; top: 20px; left: 30px; height: 32px; z-index: 100; pointer-events: none; }}
  #slide-page-counter {{
    position: fixed;
    bottom: 18px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.45);
    color: rgba(255, 255, 255, 0.9);
    padding: 3px 14px;
    border-radius: 12px;
    font-size: 0.72em;
    font-family: sans-serif;
    letter-spacing: 0.05em;
    z-index: 200;
    opacity: 0;
    transition: opacity 0.25s ease;
    pointer-events: none;
    white-space: nowrap;
  }}
  #slide-page-counter.visible {{ opacity: 1; }}
  {custom_css}
</style>
{theme_link}
</head>
<body>
{logo_block}
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
<div id="slide-page-counter"></div>
<script>
Reveal.initialize({{
  hash: true,
  slideNumber: false,
  transition: 'slide',
  plugins: [RevealMarkdown, RevealHighlight, RevealNotes, RevealMath.KaTeX]
}});

(function() {{
  var counter = document.getElementById('slide-page-counter');
  var hideTimer = null;

  function showCounter() {{
    var current = Reveal.getSlidePastCount() + 1;
    var total = Reveal.getTotalSlides();
    counter.textContent = current + ' / ' + total;
    counter.classList.add('visible');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() {{
      counter.classList.remove('visible');
    }}, 1800);
  }}

  Reveal.on('slidechanged', showCounter);
}})();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to reveal.js slides")
    parser.add_argument("inputs", nargs="+", help="Markdown file(s)")
    parser.add_argument("-o", "--output", help="Output HTML file or directory")
    parser.add_argument("--theme", default=None, help=f"Theme: {', '.join(THEMES)}")
    parser.add_argument("--title", default=None, help="Presentation title")
    parser.add_argument("--css", default="", help="Extra CSS to inject")
    parser.add_argument("--custom-theme", default=None, help="Path to a custom CSS theme file")
    parser.add_argument("--logo", default=None, help="Path to a logo image file")
    args = parser.parse_args()

    has_assets = args.custom_theme or args.logo

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

    if has_assets:
        # Directory mode: create dir with index.html + assets
        out_dir = Path(args.output) if args.output else Path(args.inputs[0]).with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)

        custom_theme_href = ""
        if args.custom_theme:
            ct = Path(args.custom_theme)
            if not ct.exists():
                print(f"Error: {args.custom_theme} not found", file=sys.stderr)
                sys.exit(1)
            dest = out_dir / ct.name
            if ct.resolve() != dest.resolve():
                shutil.copy2(ct, dest)
            custom_theme_href = ct.name

        logo_src = ""
        if args.logo:
            lp = Path(args.logo)
            if not lp.exists():
                print(f"Error: {args.logo} not found", file=sys.stderr)
                sys.exit(1)
            dest = out_dir / lp.name
            if lp.resolve() != dest.resolve():
                shutil.copy2(lp, dest)
            logo_src = lp.name

        html_out = build_html(combined, title=title, theme=theme, custom_css=args.css,
                              custom_theme_href=custom_theme_href, logo_src=logo_src)

        (out_dir / "index.html").write_text(html_out, encoding="utf-8")
        print(f"Created: {out_dir}/index.html")
    else:
        # Single file mode
        html_out = build_html(combined, title=title, theme=theme, custom_css=args.css)
        out_path = Path(args.output) if args.output else Path(args.inputs[0]).with_suffix(".html")
        out_path.write_text(html_out, encoding="utf-8")
        print(f"Created: {out_path}")


if __name__ == "__main__":
    main()
