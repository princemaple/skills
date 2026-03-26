---
name: md-to-slides
description: Convert markdown file(s) into beautiful reveal.js HTML presentations. Use when the user wants to create slides, presentations, decks, or talks from markdown content — or when asked to turn notes, outlines, or documents into a presentation format. Triggers on requests like "make a presentation", "create slides", "convert to slides", "build a deck", or any task involving .md to slideshow conversion.
---

# Markdown to Slides

Convert markdown into self-contained reveal.js HTML presentations using `scripts/md_to_slides.py`.

## Workflow

1. **Write markdown** following the slide format below (or convert existing content)
2. **Run the script** to generate an HTML presentation
3. **Open the HTML file** in any browser — no server needed

## Markdown Slide Format

- `---` on its own line separates horizontal slides (new sections)
- `--` on its own line separates vertical slides (sub-slides within a section)
- `Note:` on its own line starts speaker notes (visible with `S` key)
- Optional YAML frontmatter for `title` and `theme`

Example structure:

```markdown
---
title: My Talk
theme: moon
---

# Title Slide

Subtitle

---

## Section 2

Content with **formatting**, lists, images, tables

--

### Sub-slide

Vertical slide within the same section

Note: Only the presenter sees this

---

## Final Slide

Thanks!
```

A full example template is at `assets/example-presentation.md`.

## Running the Script

```bash
# Single file
python3 scripts/md_to_slides.py input.md -o output.html

# Multiple files (concatenated as separate sections)
python3 scripts/md_to_slides.py part1.md part2.md part3.md -o combined.html

# With options
python3 scripts/md_to_slides.py input.md -o output.html --theme moon --title "My Talk"
```

**Options:**
- `-o, --output` — output path (default: `<input>.html`)
- `--theme` — reveal.js theme (default: `black`)
- `--title` — presentation title (default: from frontmatter or filename)
- `--css` — extra CSS string to inject

## Available Themes

`black` (default), `white`, `league`, `beige`, `night`, `moon`, `serif`, `simple`, `sky`, `solarized`

## Supported Markdown Features

All standard markdown works inside slides: headings, bold/italic, lists, links, images, tables, blockquotes, and fenced code blocks with syntax highlighting. LaTeX math is supported via KaTeX (`$inline$` and `$$block$$`).

## Writing Effective Slides

- One idea per slide — avoid walls of text
- Use headings (`##`) as slide titles
- Prefer bullet points over paragraphs
- Use vertical slides (`--`) for drill-down detail
- Put supplementary context in `Note:` speaker notes
- Use code blocks for technical content — they get syntax highlighting automatically

## When Converting Existing Documents

When turning an existing markdown document, outline, or notes into a presentation:

1. Read the source document
2. Identify logical sections → these become horizontal slides (`---`)
3. Break dense sections into sub-slides (`--`)
4. Distill paragraphs into bullet points
5. Add a title slide and closing slide
6. Write the markdown to a `.md` file, then run the script
