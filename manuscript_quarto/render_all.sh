#!/bin/bash
# Render all Quarto output formats (HTML, PDF, DOCX)
#
# IMPORTANT: Quarto book projects overwrite _output on each render.
# This script renders all formats sequentially and preserves outputs.
#
# Usage: ./render_all.sh [--profile <name>] [--output-dir <path>]
# Examples:
#   ./render_all.sh                    # Default profile
#   ./render_all.sh --profile jeem     # JEEM submission format
#   ./render_all.sh --profile aer      # AER submission format
#
# Note: If a profile sets project.output-dir, this script will respect it.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
PROFILE_ARG=""
PROFILE_NAME=""
OUTPUT_DIR=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --profile) PROFILE_NAME="$2"; PROFILE_ARG="--profile $2"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

get_output_dir() {
    local file="$1"
    [ -f "$file" ] || return 0
    awk '
        $1 == "project:" {inproject=1; next}
        inproject && $1 == "output-dir:" {print $2; exit}
        inproject && $0 ~ /^[^[:space:]]/ {inproject=0}
    ' "$file"
}

if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="$(get_output_dir "_quarto.yml")"
    if [ -n "$PROFILE_NAME" ]; then
        PROFILE_OUTPUT_DIR="$(get_output_dir "_quarto-$PROFILE_NAME.yml")"
        if [ -n "$PROFILE_OUTPUT_DIR" ]; then
            OUTPUT_DIR="$PROFILE_OUTPUT_DIR"
        fi
    fi
fi

OUTPUT_DIR="${OUTPUT_DIR:-_output}"

# Ensure we have the quarto binary
QUARTO="../tools/bin/quarto"
if [ ! -f "$QUARTO" ]; then
    QUARTO="quarto"  # Fall back to system quarto
fi

echo "=== Rendering Quarto Manuscript (All Formats) ==="
[ -n "$PROFILE_ARG" ] && echo "    Using profile: $PROFILE_ARG"
echo "    Output dir: $OUTPUT_DIR"

# Create temp directory to preserve outputs
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Render HTML first
echo ""
echo ">>> Rendering HTML..."
$QUARTO render --to html $PROFILE_ARG
cp -r "$OUTPUT_DIR"/* "$TEMP_DIR/"
echo "    HTML saved."

# Render PDF
echo ""
echo ">>> Rendering PDF..."
$QUARTO render --to pdf $PROFILE_ARG
cp "$OUTPUT_DIR"/*.pdf "$TEMP_DIR/" 2>/dev/null || true
cp "$OUTPUT_DIR"/*.tex "$TEMP_DIR/" 2>/dev/null || true
echo "    PDF saved."

# Render DOCX
echo ""
echo ">>> Rendering DOCX..."
$QUARTO render --to docx $PROFILE_ARG
cp "$OUTPUT_DIR"/*.docx "$TEMP_DIR/" 2>/dev/null || true
echo "    DOCX saved."

# Restore all outputs to the active output directory
echo ""
echo ">>> Combining all outputs..."
rm -rf "$OUTPUT_DIR"/*
mkdir -p "$OUTPUT_DIR"
cp -r "$TEMP_DIR"/* "$OUTPUT_DIR"/

echo ""
echo "=== Done! All formats in $OUTPUT_DIR ==="
ls -la "$OUTPUT_DIR"/*.html "$OUTPUT_DIR"/*.pdf "$OUTPUT_DIR"/*.docx 2>/dev/null || ls -la "$OUTPUT_DIR"
