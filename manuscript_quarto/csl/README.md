# Citation Styles

This directory contains CSL (Citation Style Language) files for formatting references.

## Available Styles

| File | Style | Common Usage |
|------|-------|--------------|
| `apa.csl` | APA 7th Edition | Psychology, social sciences |
| `chicago-author-date.csl` | Chicago Author-Date | Economics, history, political science |
| `harvard.csl` | Harvard | UK universities, general |
| `nature.csl` | Nature (numeric) | Natural sciences |

## How It Works

1. **Default style**: Set in `_quarto.yml` with `csl: csl/apa.csl`
2. **Per-journal override**: Each profile (e.g., `_quarto-jeem.yml`) can specify its own CSL:
   ```yaml
   csl: csl/chicago-author-date.csl
   ```

## Adding a New Style

1. Download the CSL file from the [Zotero Style Repository](https://www.zotero.org/styles)
2. Save it to this directory: `manuscript_quarto/csl/`
3. Reference it in your journal profile:
   ```yaml
   # In _quarto-{journal}.yml
   csl: csl/your-style.csl
   ```

## Finding CSL Files

- **Official repository**: https://github.com/citation-style-language/styles
- **Zotero search**: https://www.zotero.org/styles
- **Direct download**:
  ```bash
  curl -sL "https://raw.githubusercontent.com/citation-style-language/styles/master/{style-name}.csl" -o csl/{style-name}.csl
  ```

## Common Economics Styles

| Journal | Recommended CSL |
|---------|-----------------|
| AER, QJE, JPE | `chicago-author-date.csl` |
| JEEM | `chicago-author-date.csl` |
| Econometrica | `chicago-author-date.csl` |
| Review of Economics and Statistics | `chicago-author-date.csl` |

## Verifying Style

After changing CSL, render and check:
1. In-text citation format (Author Year) vs [1]
2. Bibliography entry format
3. Sorting (alphabetical vs appearance order)
