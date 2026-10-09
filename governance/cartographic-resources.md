# Cartographic resources must resolve locally

A project may not rely on an author's style-library cache or silent substitution.
The saved project is the authoritative style configuration.

| Resource | Packaging rule | Validation |
| --- | --- | --- |
| Native simple marker, line or fill | Save its QGIS definition in the project. No separate download is needed. | Supported native symbol type, valid colors, no unsupported dynamic properties or effects; native rendering. |
| Color | Store the color values in the symbol/text definition. A palette plugin is unnecessary after values are saved. | Validate colors in admitted native styles and inspect the exported result. |
| SVG marker | Include the standalone SVG in the repository and declare its path, checksum, provenance and license in `assets`. | File exists, remains inside project root, is declared, checksum matches, XML and SVG renderer accept it. External references/rich SVG content are blocked. |
| Label/layout font | Install the licensed font in the runtime or package a redistributable font with an explicit installation recipe. Merely copying a font into the repository does not install it. | Requested family exists in Qt's font database, QGIS reports it found, and the resolved family matches. Record requested/resolved families in the report. |
| Raster/image fill, font marker, custom symbol or plugin renderer | Record assets and runtime dependencies. | Currently blocked until dedicated dependency/render tests support the type. |

Do not automatically download assets while validating. Acquisition and font
installation are separate reproducible preparation steps. System fonts may be
runtime prerequisites without being copied into the repository; do not redistribute
proprietary fonts without a license. A missing dependency must fail or block, never
become a generic replacement symbol and pass because some pixels were rendered.

Relocation uses only declared assets and the saved project, with original project
reads and network access denied. Installed fonts are host runtime dependencies,
not isolated by project relocation. A cross-platform release therefore needs a
validation run on each target runtime. The validator also shapes actual supported layer-label and plain layout-label
text through Qt and rejects missing glyphs or Last Resort placeholder fonts.
Installed fallback fonts may supply individual characters. This is generic: no
particular label wording or number sequence is required. Font-file versions and
exact typography still need pinned fonts and visual review.

Current scope is intentionally bounded. The validator permits simple symbols,
standalone SVG markers, basic native labels and supported print-layout items.
Unknown resource-bearing style features remain blocked. Save label numbers and
print layouts inside the QGZ when they are part of the delivered map; a PDF-only
style must not be mistaken for the editable project's appearance.
