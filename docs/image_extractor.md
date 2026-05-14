# Node 3: Image Extractor

This node extracts visual information (diagrams, charts, figures) from the source document to preserve context that text alone cannot capture.

## Extraction Logic

1. **Section Mapping**: For each section, the node identifies the corresponding page range.
2. **PyMuPDF Extraction**: Uses the PDF's internal image objects to extract high-quality assets.
3. **Filtering**: To avoid "noise" (icons, logos, decorative lines), images are filtered by size:
   - `min_image_width`: 100px
   - `min_image_height`: 100px
4. **Storage**: Images are saved to:
   `./output/images/{document_slug}/{section_index}_{image_count}.png`

## Config Options

```yaml
image_extractor:
  enabled: true
  output_dir: "./output/images"
  min_image_width: 100
  min_image_height: 100
```

## Integration with Output
The file paths to these images are added to the `Section` metadata, allowing the **Writer** node to insert Markdown image references (`![]()`) at the end of the corresponding section.
