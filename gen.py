# gen.py
"""
gen.py — Minecraft schematic generation for Dungeon Designer.

This module reads the floor/wall layer data structure produced by main.py and
exports a stacked .schem compatible with Minecraft 1.20.1 (Java).

Assumptions (as requested):
- Each editor pixel maps to EXACTLY 1×1 block in XZ (no scaling).
- "Blocks per floor" (wall height) is fixed at 4.
- For each floor pair we place:
    floor (y = baseY)
    walls extruded up for 4 blocks (y = baseY+1 .. baseY+4)
    ceiling (copy of the floor) at y = baseY+5
    then the next floor starts at baseY = baseY + 6
- Different blocks is ON: each floor pair uses the next wool color in a cycle.
  (Both the floor and the walls for that pair use the same color.)

Public entrypoint:
    createSchematic(floors)

Where `floors` is a list like:
    [
      { 'name': 'Floor 1', 'cells': { (x, y, 'floor'): True, (x, y, 'walls'): True, ... } },
      { 'name': 'Floor 2', 'cells': { ... } },
      ...
    ]

We use tkinter's "Save As" dialog to choose the output file. The file is saved
using mcschematic with Version.JE_1_20_1 when available (fallbacks included).
"""

import os
from typing import Dict, List, Tuple

# Import save dialog locally to avoid forcing tkinter init when not exporting
try:
    from tkinter.filedialog import asksaveasfile
except Exception:
    asksaveasfile = None  # If tkinter isn't available, we'll fallback to a default path

# mcschematic import (the package exposes MCSchematic and a Version enum)
from mcschematic import MCSchematic, Version


# ----------------------------- CONFIG CONSTANTS -----------------------------

wallHeight = 4  # fixed number of blocks between floor and ceiling (a.k.a. "blocks per floor")

# 16 wool colors for floors
woolCycle = [
    "minecraft:white_wool",
    "minecraft:light_gray_wool",
    "minecraft:gray_wool",
    "minecraft:black_wool",
    "minecraft:brown_wool",
    "minecraft:red_wool",
    "minecraft:orange_wool",
    "minecraft:yellow_wool",
    "minecraft:lime_wool",
    "minecraft:green_wool",
    "minecraft:cyan_wool",
    "minecraft:light_blue_wool",
    "minecraft:blue_wool",
    "minecraft:purple_wool",
    "minecraft:magenta_wool",
    "minecraft:pink_wool",
]

# Matching concrete colors for walls
concreteCycle = [c.replace("_wool", "_concrete") for c in woolCycle]

# ----------------------------- HELPER FUNCTIONS -----------------------------

def _pickVersion():
    """
    Choose the best available Minecraft Java version constant for saving.
    Prefers 1.20.1, falls back to sensible older enums if needed.
    """
    for name in ("JE_1_20_1", "JE_1_20", "JE_1_19_4", "JE_1_19", "JE_1_18"):
        if hasattr(Version, name):
            return getattr(Version, name)
    # Absolute last resort: grab any attribute that isn't a dunder
    for k, v in vars(Version).items():
        if not k.startswith("_"):
            return v
    raise RuntimeError("No compatible Version enum found in mcschematic.Version")


def _setBlock(schematic: MCSchematic, x: int, y: int, z: int, blockName: str):
    """
    Place a single block into the schematic at integer coordinates.
    This wrapper exists for readability and potential future safety checks.
    """
    schematic.setBlock((x, y, z), blockName)


def _exportSingleLayerPair(
    schematic: MCSchematic,
    layerIndex: int,
    layerCells: Dict[Tuple[int, int, str], bool],
    baseY: int,
):
    """
    Export one floor+walls pair into the schematic at the given baseY.
    Floors use wool, walls use concrete of the same color.
    """
    floorBlock = woolCycle[layerIndex % len(woolCycle)]
    wallBlock  = concreteCycle[layerIndex % len(concreteCycle)]

    # 1) Place the floor at baseY
    for (x, z, cellType), filled in layerCells.items():
        if not filled:
            continue
        if cellType == "floor":
            _setBlock(schematic, x, baseY, z, floorBlock)

    # 2) Extrude walls for wallHeight above the floor
    for (x, z, cellType), filled in layerCells.items():
        if not filled:
            continue
        if cellType == "walls":
            for dy in range(1, wallHeight + 1):
                _setBlock(schematic, x, baseY + dy, z, wallBlock)

    # 3) Ceiling (same as floor) at y = baseY + wallHeight + 1
    ceilingY = baseY + wallHeight + 1
    for (x, z, cellType), filled in layerCells.items():
        if not filled:
            continue
        if cellType == "floor":
            _setBlock(schematic, x, ceilingY, z, floorBlock)

    return ceilingY + 1



def _splitPath(path: str):
    """
    Split a full path into (directory, filename_without_ext).
    If no directory is present, returns ('.', filename_without_ext).
    """
    directory, filename = os.path.split(path)
    name, _ext = os.path.splitext(filename)
    if directory == "":
        directory = "."
    return directory, name


# ------------------------------- PUBLIC API --------------------------------

def createSchematic(floors: List[dict]):
    """
    Build and save a .schem file from the provided floors list.

    Parameters
    ----------
    floors : List[dict]
        Each item must be a dict with:
          - 'name': str
          - 'cells': dict with keys of (x: int, y: int, type: 'floor'|'walls') and truthy values.

    Behavior
    --------
    Floors are exported in list order (index 0 = bottommost).
    For each pair we place floor, walls (up to wallHeight), and ceiling.
    Each pair uses a distinct wool color cycling through 16 variants.
    """
    # Create schematic container
    schematic = MCSchematic()

    # Stack layers along +Y starting at y = 0
    baseY = 0
    for idx, layer in enumerate(floors):
        layerCells = layer.get("cells", {})
        baseY = _exportSingleLayerPair(schematic, idx, layerCells, baseY)

    # Choose output path
    saveDir = "exports"
    os.makedirs(saveDir, exist_ok=True)
    saveName = "dungeon"  # default name if no dialog is available or user cancels

    # Try Save As dialog if available
    chosenPath = None
    if asksaveasfile is not None:
        try:
            fobj = asksaveasfile(
                defaultextension=".schem",
                filetypes=[("Minecraft Schematic", "*.schem")],
                initialdir=saveDir,
                initialfile=saveName + ".schem",
                title="Save Schematic As"
            )
            if fobj is not None:
                chosenPath = fobj.name
                try:
                    # Some tk backends keep the file handle open; we only need the path
                    fobj.close()
                except Exception:
                    pass
        except Exception:
            # If tkinter fails for any reason, we silently fall back to defaults
            chosenPath = None

    if chosenPath is None:
        # Fallback to a timestamped filename in ./exports
        import time as _time
        saveName = f"{saveName}_{int(_time.time())}"
        directory, nameOnly = saveDir, saveName
    else:
        directory, nameOnly = _splitPath(chosenPath)

    # Save schematic with a 1.20.1-compatible version (with fallbacks)
    versionEnum = _pickVersion()
    schematic.save(directory, nameOnly, versionEnum)
    # Optionally return the actual path for UI feedback
    return os.path.join(directory, f"{nameOnly}.schem")
