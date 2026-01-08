# reMarkable Style Contract

## 1. Purpose

This document defines the **authoritative style and formatting contract** for all documents, templates, and artefacts intended for use on **reMarkable tablets** and other monochrome e‑ink devices.

It is designed to be:

* Referenced explicitly from prompts (Codex / LLM / tooling)
* Stable over time
* Optimised for **handwritten annotation, thinking, and review**

If any generated document conflicts with this contract, **this contract takes precedence**.

---

## 2. Target Medium Assumptions (Normative)

All documents MUST assume:

* Monochrome e‑ink display
* High-latency refresh
* No colour fidelity
* Pen‑first interaction (not typing)

The document is expected to be:

* Annotated heavily by hand
* Used for extended reading or thinking sessions
* Viewed primarily in portrait orientation

---

## 3. Colour & Contrast Rules

### 3.1 Allowed

* Black (#000000)
* Dark grey
* Light grey
* White background

### 3.2 Forbidden

* Colour of any kind
* Gradients
* Shadows
* Transparency
* Background textures or patterns

### 3.3 Contrast

* All text and lines MUST be clearly legible at low contrast sensitivity
* Avoid thin strokes or light fonts

---

## 4. Typography Contract

### 4.1 Intent (Font-Agnostic)

Exact font names are not mandated, but **visual intent is normative**.

* Headings: clean, neutral, sans‑serif feel
* Body text: readable, print‑like serif or humanist
* Monospaced fonts: allowed only for code or identifiers

### 4.2 Rules

* No decorative or stylised fonts
* No condensed fonts
* No script or handwriting‑style fonts
* Avoid excessive hierarchy (maximum 3 heading levels)

### 4.3 Sizing

* Text MUST remain readable when zoomed out
* Prefer fewer, larger text elements over dense text

---

## 5. Page Layout

### 5.1 Page Format

* Default: A4 portrait
* Single-column layout only
* Generous margins on all sides

### 5.2 Spacing

* Whitespace is mandatory and intentional
* Avoid dense blocks of text
* Sections should feel visually separated without heavy rules

### 5.3 Navigation

* Page numbers may be included subtly
* Headers/footers must be minimal and non-distracting

---

## 6. Handwriting Optimisation Rules (Critical)

Documents MUST:

* Leave sufficient empty space for handwriting
* Avoid filling pages edge-to-edge with printed text
* Support annotations, arrows, highlights, and margin notes

Strong preference for:

* Short paragraphs
* Bullet points
* Open-ended sections
* Writing zones

---

## 7. Structural Elements

### 7.1 Allowed

* Light horizontal rules
* Simple boxes
* Checklists
* Tables with minimal borders (only if necessary)

### 7.2 Forbidden

* Dense tables
* Multi-column grids
* UI-like components
* Decorative icons

Icons, if used, must:

* Be monochrome
* Remain legible at small sizes
* Not rely on colour or shading

---

## 8. Markdown & Conversion Contract

When authoring in Markdown:

* Structure must survive Markdown → PDF conversion
* Do not rely on colour-based emphasis
* Avoid constructs that collapse whitespace
* Use headings and spacing deliberately

The rendered PDF must preserve:

* Spacing
* Section separation
* Visual calm

---

## 9. Cognitive Design Principles

Documents should:

* Reduce cognitive load
* Encourage reflection and thinking
* Avoid visual noise
* Feel calm, intentional, and understated

The printed structure should **disappear** once handwriting begins.

---

## 10. Compliance Checklist (For Humans & Codex)

Before accepting a document as compliant:

* [ ] No colours or gradients present
* [ ] High contrast throughout
* [ ] Adequate whitespace for handwriting
* [ ] Single-column layout
* [ ] No decorative elements
* [ ] Readable when zoomed out
* [ ] Comfortable for long pen-based sessions

---

## 11. Prompt Reference Snippet

When used from a prompt, reference this contract explicitly:

> "All output MUST comply with the reMarkable Style Contract defined in this repository. If any ambiguity exists, prioritise handwriting ergonomics, monochrome e‑ink constraints, and visual simplicity over aesthetics."

---

## 12. Scope & Evolution

This contract is expected to evolve as:

* reMarkable firmware changes
* Conversion pipelines improve
* Usage patterns mature

Any change must preserve:

* Handwriting-first design
* Monochrome robustness
* Cognitive clarity
