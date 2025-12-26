# Manuscript Variants

Each variant is a divergent manuscript draft stored in its own folder.

- Create a variant: `cd manuscript_quarto && ./variant_new.sh <name>`
- Render a variant: `cd manuscript_quarto && ./render_all.sh --profile variant-<name>`
- Outputs go to: `manuscript_quarto/_output/variants/<name>/`
- Snapshot provenance: `cd manuscript_quarto && python variant_tools.py snapshot --variant <name>`
- Compare variants: `cd manuscript_quarto && python variant_tools.py compare --left <a> --right <b>`
- Index: `manuscript_quarto/variants/INDEX.md` and `manuscript_quarto/variants/index.json`
- Variant metadata: `manuscript_quarto/variants/<name>/variant.json` and `manuscript_quarto/variants/<name>/variant.md`

Variants are snapshots of the main draft. Edits do not sync automatically.
