import os
import time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_with_retry(prompt, output_path, max_retries=3, aspect_ratio="16:9", resolution="2K"):
    """Generate image with retry logic for rate limits."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=resolution
                    ),
                ),
            )
            for part in response.parts:
                if part.text:
                    print(part.text)
                elif part.inline_data:
                    image = part.as_image()
                    image.save(output_path)
                    print(f"Saved: {output_path}")
                    return True
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                raise e
    return False

# Color scheme from IMAGE_GENERATION_GUIDE.md
# Primary accent: #ea580c (orange)
# Box backgrounds: #a8a29e
# Box borders: #57534e
# Text: #1c1917
# Background: #d6d3d1

WAIT_TIME = 45  # seconds between API calls

# ============================================================================
# Image 1: Hero Image - Claude Code Customization
# ============================================================================
hero_prompt = """Create a clean, minimal hero illustration representing Claude Code customization and developer workflow automation.

COMPOSITION:
- Center-focused design with visual elements flowing outward
- Center: A stylized terminal/CLI window with an AI brain icon inside
- Surrounding the center in a radial pattern: Six floating connected modules/boxes representing customization mechanisms
- Subtle connecting lines (orange) linking the modules to the center

VISUAL ELEMENTS:
- Central terminal window with rounded corners and a glowing orange accent
- Six smaller floating boxes arranged in a circle around the center, each with a distinct simple icon:
  - Book icon (Skills/Knowledge)
  - Parallel lines icon (Subagents)
  - Slash symbol (Slash Commands)
  - Connection/plug icon (MCP)
  - Package/box icon (Plugins)
  - Hook/anchor icon (Hooks)
- Subtle background pattern: faint grid or dot pattern
- Abstract code snippets or brackets floating faintly in background

KEY VISUAL STORY:
- The image should convey "extensibility and customization"
- Sense of modularity and power
- Professional, technical, but approachable

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - central glow, connecting lines, icon highlights
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Background elements: #78716c at 10-15% opacity
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design with subtle rounded corners
- 16:9 aspect ratio (standard blog header)
- Minimalist and clean
- Abstract enough to be a header, not overly technical
- Professional tech aesthetic
- No heavy shadows or 3D effects

AVOID:
- Photorealistic elements
- Cluttered composition
- Any text or labels
- Human figures
"""

print("=" * 60)
print("Generating Hero Image...")
print("=" * 60)
generate_with_retry(hero_prompt, "public/images/claude-code-customization-hero.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 2: Skills - Progressive Disclosure Diagram
# ============================================================================
skills_prompt = """Create a clean, minimal diagram showing Claude Code Skills progressive loading concept.

STRUCTURE:
- Left side: A vertical stack of 5 skill file icons (like documents) labeled faintly
- Center: A funnel or filter shape in orange
- Right side: A conversation/chat window showing only 1-2 skills loaded

VISUAL FLOW:
- Many skills on the left (showing "available but not loaded")
- Filter/funnel in the middle with text "Context-aware loading"
- Only relevant skills appear on the right (showing "loaded when needed")
- Orange arrows showing the filtering flow

VISUAL ELEMENTS:
- Document/file icons with rounded corners for skills
- Some skills shown grayed out (not loaded)
- One or two skills shown in full color (actively loaded)
- Funnel or gateway symbol in the center
- Chat/conversation icon on the right

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - funnel, arrows, active skill highlight
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Inactive/grayed elements: #78716c at 40% opacity
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design with subtle rounded corners
- Clean arrows in orange showing flow direction
- 16:9 aspect ratio
- Minimal text labels
- No heavy shadows or 3D effects
- Sans-serif font for any labels

AVOID:
- Photorealistic elements
- Cluttered composition
- Heavy gradients
"""

print("=" * 60)
print("Generating Skills Diagram...")
print("=" * 60)
generate_with_retry(skills_prompt, "public/images/claude-code-skills-progressive.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 3: Subagent Parallelization Diagram
# ============================================================================
subagent_prompt = """Create a clean, flat, modern technical diagram showing Claude Code subagent parallelization.

STRUCTURE:
- At the top: A single larger box labeled "Main Claude Agent" with a brain/AI icon
- Below it: Three arrows (in orange color #ea580c) fanning out downward simultaneously
- Three parallel worker boxes at the bottom arranged horizontally, each labeled:
  - "Code Review" with a magnifying glass icon
  - "Security Scan" with a shield icon
  - "Test Runner" with a checkmark icon
- Dashed arrows returning upward (in orange) showing results flowing back to main agent
- Small clock or timer icon suggesting parallel execution

VISUAL ELEMENTS:
- Main agent box is larger and more prominent
- Subagent boxes are uniform in size, smaller than main
- Arrows clearly show fork (solid) and join (dashed) pattern
- Optional: small "parallel" indicator showing simultaneous execution

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - arrows, icons, highlights
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600) with subtle rounded corners
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat design, no 3D effects or heavy shadows
- Clean sans-serif typography
- Minimalist, professional look suitable for a technical blog
- No gradients, keep it flat and modern
- 16:9 aspect ratio
"""

print("=" * 60)
print("Generating Subagent Parallelization Diagram...")
print("=" * 60)
generate_with_retry(subagent_prompt, "public/images/claude-code-subagents.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 4: Slash Commands Workflow Diagram
# ============================================================================
slash_prompt = """Create a clean, minimal diagram showing Claude Code Slash Commands concept.

STRUCTURE:
- Left side: A terminal prompt showing "/k8s-manifests" being typed
- Center: An expansion arrow or transformation symbol
- Right side: Multiple output files being generated (deployment.yaml, service.yaml, etc.)

VISUAL FLOW:
- Single command input on the left
- Expansion/transformation in the middle
- Multiple outputs on the right
- Shows the "one command, many actions" concept

VISUAL ELEMENTS:
- Terminal window with command prompt and slash command text
- Transformation/expansion arrow or burst symbol in orange
- Multiple file icons on the right (YAML files with Kubernetes wheel icon)
- Optional: small parameter indicator showing "$ARGUMENTS"

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - transformation symbol, arrows
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design with subtle rounded corners
- Clean arrows in orange showing flow direction
- 16:9 aspect ratio
- Minimal text labels
- No heavy shadows or 3D effects
- Sans-serif font for labels
"""

print("=" * 60)
print("Generating Slash Commands Diagram...")
print("=" * 60)
generate_with_retry(slash_prompt, "public/images/claude-code-slash-commands.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 5: MCP Integration Diagram
# ============================================================================
mcp_prompt = """Create a clean, flat, modern technical diagram showing MCP (Model Context Protocol) integration with Claude Code.

STRUCTURE:
- Center: A prominent box labeled "Claude Code" with an AI/terminal icon
- Surrounding it in a hub-and-spoke pattern: Four service boxes connected via bidirectional arrows
- Top-left: "GitHub" with an octocat/code icon
- Top-right: "Database" with a cylinder/database icon
- Bottom-left: "Kubernetes" with a ship wheel icon
- Bottom-right: "Slack" with a chat/message icon
- Label "MCP" on the connecting lines/protocol

VISUAL ELEMENTS:
- Central Claude Code box is larger and highlighted
- Four external service boxes arranged symmetrically
- Bidirectional arrows showing two-way communication
- "MCP" label on one or more connection lines
- Each service has a recognizable icon

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - connection lines, arrows, MCP label
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600) with subtle rounded corners
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat design, no 3D effects or heavy shadows
- Hub-and-spoke layout with Claude Code clearly in the center
- Clean sans-serif typography
- Minimalist, professional look suitable for a technical blog
- 16:9 aspect ratio
"""

print("=" * 60)
print("Generating MCP Integration Diagram...")
print("=" * 60)
generate_with_retry(mcp_prompt, "public/images/claude-code-mcp-integration.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 6: Six Mechanisms Overview / Architecture Diagram
# ============================================================================
architecture_prompt = """Create a clean, minimal architecture overview diagram showing all six Claude Code customization mechanisms working together.

STRUCTURE:
- Center: A hexagonal or circular hub representing "Claude Code" with AI icon
- Six spokes radiating outward to six mechanism boxes arranged in a circle:
  1. "Skills" (top) - book/knowledge icon
  2. "Subagents" (top-right) - parallel workers icon
  3. "Slash Commands" (bottom-right) - slash/command icon
  4. "MCP" (bottom) - connection/plug icon
  5. "Plugins" (bottom-left) - package/box icon
  6. "Hooks" (top-left) - hook/anchor icon

VISUAL ELEMENTS:
- Central hub is prominent with a subtle glow
- Six mechanism boxes are uniform in size
- Orange connecting lines from center to each mechanism
- Each mechanism has a distinct, simple icon
- Optional: subtle dotted lines between adjacent mechanisms showing they can work together

LAYERING CONCEPT:
- Show this as a modular, extensible system
- Each mechanism is independent but connected to the core

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - connecting lines, center glow, icon accents
- Box backgrounds: #a8a29e (stone-400)
- Box borders: #57534e (stone-600)
- Secondary connections: #78716c (dotted lines between mechanisms)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat, modern design with subtle rounded corners
- Radial/hub-and-spoke layout
- Clean sans-serif typography
- 16:9 aspect ratio
- Professional, technical aesthetic
- No heavy shadows or 3D effects
"""

print("=" * 60)
print("Generating Architecture Overview Diagram...")
print("=" * 60)
generate_with_retry(architecture_prompt, "public/images/claude-code-mechanisms-overview.jpg")
print(f"Waiting {WAIT_TIME}s before next generation...")
time.sleep(WAIT_TIME)

# ============================================================================
# Image 7: Decision Flowchart - Choosing the Right Mechanism
# ============================================================================
flowchart_prompt = """Create a clean, flat, modern decision flowchart diagram for choosing Claude Code mechanisms.

STRUCTURE:
- Vertical flowchart from top to bottom
- Start node at top: "What do you need?" in a rounded rectangle
- Series of diamond decision nodes with Yes/No branches:
  1. "External system access?" → Yes: "MCP" (exit to right)
  2. "Reusable workflow?" → Yes: "Slash Commands" (exit to right)
  3. "Parallel isolated tasks?" → Yes: "Subagents" (exit to right)
  4. "Context-aware knowledge?" → Yes: "Skills" (exit to right)
  5. "Automated enforcement?" → Yes: "Hooks" (exit to right)
  6. "Share with team?" → Yes: "Plugins" (exit to right)
- No branches continue downward to next decision

VISUAL FLOW:
- Main flow goes top to bottom (No path)
- Yes paths exit to the right to labeled mechanism boxes
- Clear decision tree structure

COLOR SCHEME (use these exact hex values):
- Primary accent: #ea580c (orange) - arrows, Yes paths, decision highlights
- Box backgrounds: #a8a29e (stone-400)
- Diamond backgrounds: slightly lighter or same as boxes
- Box borders: #57534e (stone-600)
- Text: #1c1917 (near black)
- Overall background: #d6d3d1 (stone-300)

STYLE:
- Flat design, no 3D effects or heavy shadows
- Clean flowchart with proper decision diamond shapes
- Sans-serif typography
- Minimalist, professional look
- 3:4 or 9:16 aspect ratio (vertical orientation)
"""

print("=" * 60)
print("Generating Decision Flowchart...")
print("=" * 60)
generate_with_retry(flowchart_prompt, "public/images/claude-code-decision-flowchart.jpg", aspect_ratio="3:4")

print("\n" + "=" * 60)
print("All images generated!")
print("=" * 60)
print("\nGenerated files:")
print("  - public/images/claude-code-customization-hero.jpg")
print("  - public/images/claude-code-skills-progressive.jpg")
print("  - public/images/claude-code-subagents.jpg")
print("  - public/images/claude-code-slash-commands.jpg")
print("  - public/images/claude-code-mcp-integration.jpg")
print("  - public/images/claude-code-mechanisms-overview.jpg")
print("  - public/images/claude-code-decision-flowchart.jpg")
