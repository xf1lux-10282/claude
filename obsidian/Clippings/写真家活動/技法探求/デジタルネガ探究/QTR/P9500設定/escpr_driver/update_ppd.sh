#!/bin/bash
# Update PPD file to fix GUI printing issue
# This adds the missing filter chain for PostScript → CUPS Raster conversion

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== PPD File Update Script ===${NC}"
echo ""
echo "This script will:"
echo "  1. Install the updated PPD file with PostScript → CUPS Raster filter"
echo "  2. Fix the issue where Photoshop/Preview.app print jobs get stuck"
echo ""

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PPD_SOURCE="$SCRIPT_DIR/P9550_ESCPR_QTR.ppd"
PPD_DEST="/Library/Printers/PPDs/Contents/Resources/P9550_ESCPR_QTR.ppd"

if [ ! -f "$PPD_SOURCE" ]; then
    echo -e "${RED}ERROR: PPD file not found: $PPD_SOURCE${NC}"
    exit 1
fi

echo -e "${BLUE}[1/3] Copying updated PPD file...${NC}"
sudo cp "$PPD_SOURCE" "$PPD_DEST"
echo -e "${GREEN}✓ Copied to $PPD_DEST${NC}"

echo -e "${BLUE}[2/3] Compressing PPD file...${NC}"
sudo gzip -f "$PPD_DEST"
echo -e "${GREEN}✓ Compressed to $PPD_DEST.gz${NC}"

echo -e "${BLUE}[3/3] Restarting CUPS...${NC}"
sudo launchctl stop org.cups.cupsd
sleep 1
sudo launchctl start org.cups.cupsd
sleep 2
echo -e "${GREEN}✓ CUPS restarted${NC}"

echo ""
echo -e "${GREEN}=== Update Complete ===${NC}"
echo ""
echo "The PPD file has been updated with the proper filter chain:"
echo "  PostScript/PDF → cgpdftoraster → CUPS Raster → rastertop9550 → Printer"
echo ""
echo "You can now test printing from Photoshop or Preview.app."
echo ""
