# Image Generation Guide for Blog Diagrams

Instructions for generating consistent, on-brand diagram images using LLMs (Claude, ChatGPT, Midjourney, etc.).

## Color Scheme

Use these exact hex values for consistency across all diagrams:

| Purpose | Color | Hex |
|---------|-------|-----|
| Primary accent | Orange | `#ea580c` |
| Text | Near black | `#1c1917` |
| Box backgrounds | Stone 400 | `#a8a29e` |
| Box borders | Stone 600 | `#57534e` |
| Background elements | Warm gray | `#78716c` |
| Overall background | Stone 300 | `#d6d3d1` |
| Success/completion | Green | `#16a34a` |
| Info/secondary | Blue | `#3b82f6` |

### Section Backgrounds (for swim lane diagrams)

Use semi-transparent overlays:

- Top section: `#78716c` at 20% opacity
- Middle section: `#ea580c` at 15% opacity
- Bottom section: `#57534e` at 20% opacity

## Style Guidelines

Always include these style directives:

```
STYLE:
- Flat, modern design with subtle rounded corners
- Clean arrows in orange (#ea580c) showing flow direction
- No heavy shadows or 3D effects
- Monospace or sans-serif font for labels
- Minimal text labels, let shapes and flow communicate
- Balanced whitespace - don't fill every corner
```

## Common Aspect Ratios

- **16:9** - Standard horizontal diagrams, hero images
- **9:16 or 3:4** - Vertical flow diagrams
- **1:1** - Icons, simple diagrams

## Prompt Template

```
Create a clean, minimal [TYPE] diagram illustration showing [SUBJECT].

STRUCTURE:
[Describe the layout - sections, flow direction, key elements]

VISUAL ELEMENTS:
[List specific boxes, arrows, icons needed]

ICONS TO INCLUDE:
[List recognizable icons: GitHub logo, Docker whale, Kubernetes wheel, etc.]

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - use for arrows, icons, and key highlights
- Box backgrounds: #a8a29e (stone-400)
- Box borders/outlines: #57534e (stone-600)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)
[Add section backgrounds if using swim lanes]

STYLE:
- Flat, modern design with subtle rounded corners
- Clean arrows in orange (#ea580c) showing flow direction
- [Aspect ratio] aspect ratio
- Minimal text labels, let shapes and flow communicate
- No heavy shadows or 3D effects
- Monospace or sans-serif font for labels

AVOID:
- Photorealistic elements
- Too many small details that won't scale well
- Heavy gradients or glossy effects
- Cluttered composition
- Text or labels (image only) [if applicable]
```

## Diagram Type Examples

### Workflow/Pipeline Diagram

```
Create a clean, minimal workflow diagram illustration showing [PIPELINE NAME].

STRUCTURE:
- [X] horizontal sections/swim lanes stacked vertically
- Flow direction: left to right (or top to bottom)
- Each section represents: [DESCRIPTION]

[SECTION NAME]:
- Box: "[Step 1]" on the left
- Arrow flowing right to "[Step 2]"
- Arrow flowing to "[Step 3]"
[Repeat for each section]

ICONS TO INCLUDE:
- [Relevant technology logos]

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange)
- Section backgrounds:
  - Top: #78716c at 20% opacity
  - Middle: #ea580c at 15% opacity
  - Bottom: #57534e at 20% opacity
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design with subtle rounded corners
- Clean arrows in orange (#ea580c)
- 16:9 aspect ratio
- Minimal text labels
- No heavy shadows or 3D effects
- Sans-serif font for labels
```

### Architecture Diagram

```
Create a clean, minimal architecture diagram showing [SYSTEM NAME].

COMPOSITION:
- [Describe spatial layout: left-right, center-focused, hierarchical]
- [Describe connections between components]

COMPONENTS:
- [Component 1]: [Description, position]
- [Component 2]: [Description, position]
- [Connections]: [How they link]

ICONS TO INCLUDE:
- [Technology-specific logos]

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - connections, highlights
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design
- 16:9 aspect ratio
- Professional tech aesthetic
- Balanced whitespace
```

### Timeline Diagram

```
Create a clean, minimal horizontal timeline diagram showing [PROCESS NAME].

STRUCTURE:
- Horizontal timeline arrow spanning the width, pointing right
- [X] milestone markers evenly spaced along the timeline

MILESTONES (left to right):
1. "[Stage 1]"
   - Icon: [description]
   - Below: "[Detail]"
2. "[Stage 2]"
   - Icon: [description]
   - Below: "[Detail]"
[Continue for all stages]

VISUAL ELEMENTS:
- Circular nodes on the timeline for each milestone
- Vertical lines connecting nodes to labels
- Progression from left to right suggesting forward motion

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - timeline arrow, nodes
- Connecting lines: #78716c (warm gray)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)
- Completion indicators: #16a34a (green)

STYLE:
- Flat, modern design
- 16:9 or wider aspect ratio
- Clean and minimal
- Sans-serif font
```

### Hero/Header Image

```
Create a clean, minimal hero illustration representing [TOPIC].

COMPOSITION:
- Center-focused design with visual elements flowing [direction]
- [Left element]: [Description]
- [Center element]: [Description]
- [Right element]: [Description]

VISUAL ELEMENTS:
- [Primary visual]
- [Secondary visuals]
- Subtle background elements: [grid, dots, patterns]

KEY VISUAL STORY:
- The image should convey "[message]"
- Sense of [emotion/action]
- Professional, technical, but approachable

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange)
- Secondary elements: #a8a29e (stone-400)
- Background elements: #78716c at 10-15% opacity
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design
- 16:9 aspect ratio (standard blog header)
- Minimalist and clean
- Abstract enough to be a header, not a technical diagram
- Professional tech aesthetic

AVOID:
- Photorealistic elements
- Cluttered composition
- Text or labels
```

## Post-Generation Optimization

After generating images, optimize them before adding to the blog:

```bash
# Check dimensions and size
identify image.png

# Resize and initial optimization (max 1600px)
magick image.png -resize '1600x1600>' -strip -quality 90 image-temp.png

# Reduce colors for smaller file size
magick image-temp.png -colors 256 -depth 8 PNG8:image-final.png

# Clean up
mv image-final.png image.png
rm image-temp.png
```

Target file sizes:
- Hero images: < 500KB
- Diagrams: < 400KB
- Icons: < 100KB

## Common Icons Reference

Technology logos to request:
- **GitHub**: Octocat silhouette or GitHub mark
- **Docker**: Whale with containers
- **Kubernetes**: Ship's wheel (helm)
- **ArgoCD**: Orange squid/octopus
- **Git**: Branch/merge icon
- **Cloud**: Generic cloud shape
- **Database**: Cylinder
- **API**: Connected nodes or puzzle pieces
