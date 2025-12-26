# Manuscript Variants

This project supports divergent manuscript drafts alongside the active version.

## Structure

- Active draft: `manuscript_quarto/index.qmd` and `manuscript_quarto/appendix-*.qmd`
- Variants: `manuscript_quarto/variants/<name>/`
- Variant profiles: `manuscript_quarto/_quarto-variant-<name>.yml`
- Outputs: `manuscript_quarto/_output/variants/<name>/`

## Create a Variant

```bash
cd manuscript_quarto
./variant_new.sh <name>
```

This copies the current draft into `manuscript_quarto/variants/<name>/` and creates a matching Quarto profile.

It also writes a provenance snapshot to:
- `manuscript_quarto/variants/<name>/variant.json` (machine-readable)
- `manuscript_quarto/variants/<name>/variant.md` (human-readable)

## Render a Variant

```bash
cd manuscript_quarto
./render_all.sh --profile variant-<name>
```

## Refresh Provenance

If you edit a variant or update figures/data, refresh the snapshot:

```bash
cd manuscript_quarto
python variant_tools.py snapshot --variant <name>
```

Activate `.venv` before running Python tools.

## Compare Variants

```bash
cd manuscript_quarto
python variant_tools.py compare --left <a> --right <b>
```

Add `--output` to save a report, e.g. `--output variants/compare/<a>-vs-<b>.md`.

## Index

`python variant_tools.py index` rebuilds:
- `manuscript_quarto/variants/INDEX.md`
- `manuscript_quarto/variants/index.json`

## Notes

- Variants are snapshots; they do not sync automatically with the active draft.
- If you add new chapters or appendices, update the variant profile to include them.
- For inline images in variant files, use paths relative to the manuscript root (for example, `../figures/...`) or rely on `FIG_DIR` in code chunks.
- Provenance captures the manuscript files, Quarto configs, support code, and the data/figure inputs used at snapshot time.
