#!/bin/bash
# Create a divergent manuscript variant with its own Quarto profile.
#
# Usage:
#   ./variant_new.sh <name>
#
# Example:
#   ./variant_new.sh alternative-model

set -euo pipefail

usage() {
    echo "Usage: ./variant_new.sh <name>"
    echo "Example: ./variant_new.sh alternative-model"
}

if [ "$#" -ne 1 ]; then
    usage
    exit 1
fi

VARIANT="$1"
if [[ ! "$VARIANT" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "Error: variant name must be alphanumeric with dashes/underscores." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TARGET_DIR="variants/$VARIANT"
PROFILE_NAME="variant-$VARIANT"
PROFILE_FILE="_quarto-$PROFILE_NAME.yml"

if [ -e "$TARGET_DIR" ]; then
    echo "Error: variant directory already exists: $TARGET_DIR" >&2
    exit 1
fi

if [ -e "$PROFILE_FILE" ]; then
    echo "Error: profile file already exists: $PROFILE_FILE" >&2
    exit 1
fi

mkdir -p "$TARGET_DIR"
cp index.qmd appendix-a-data.qmd appendix-b-methods.qmd appendix-c-robustness.qmd "$TARGET_DIR/"

cat > "$PROFILE_FILE" <<EOF
# Variant profile for $VARIANT
project:
  output-dir: _output/variants/$VARIANT

book:
  chapters:
    - variants/$VARIANT/index.qmd
  appendices:
    - variants/$VARIANT/appendix-a-data.qmd
    - variants/$VARIANT/appendix-b-methods.qmd
    - variants/$VARIANT/appendix-c-robustness.qmd
EOF

CREATED_BY="${CREATED_BY:-${USER:-}}"
python variant_tools.py snapshot --variant "$VARIANT" --created-by "$CREATED_BY"

echo "Created variant '$VARIANT' in $TARGET_DIR"
echo "Profile: $PROFILE_FILE"
echo "Render: ./render_all.sh --profile $PROFILE_NAME"
echo "Manifest: $TARGET_DIR/variant.json"
