# Fonts Directory

This folder is scanned by the PDF generator when selecting a font for reports.

To enable Arabic support, drop an Arabic-capable TrueType font here, for example:

- `Tajawal-Regular.ttf` (open source from Google Fonts)
- `arabic.ttf` (any suitably licensed font)

The PDF engine will register the first font it finds and name it `ArabicFont` or
`MainFont`. If no font is available the generator will fall back to Helvetica
and Arabic text may not render correctly.

You can also configure a custom path by setting `paths.fonts_dir` in
`config.yaml`.
