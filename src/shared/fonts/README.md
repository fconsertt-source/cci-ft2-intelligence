# Shared Fonts

The PDF generator will look here (or in the path defined by
`paths.fonts_dir` in `config.yaml`) for fonts it can register.
Drop any TrueType/OpenType font files you want to use, especially for
Arabic support. Example:

- `Tajawal-Regular.ttf`
- `Tajawal-Bold.ttf`

If the directory is empty the generator falls back to Helvetica.
