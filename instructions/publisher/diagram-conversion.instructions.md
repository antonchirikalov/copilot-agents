---
description: Mermaid diagram to PNG conversion procedures for the Publisher agent.
---

# Diagram Conversion

## Process
1. Read markdown file to extract all ```mermaid code blocks
2. Create images/ subfolder next to the document
3. Convert each diagram to PNG
4. Keep original markdown UNCHANGED (Mermaid code stays intact)

## Conversion Commands

### Check mmdc installed
```bash
which mmdc || npm install -g @mermaid-js/mermaid-cli
```

### Create images folder
```bash
mkdir -p generated_docs_[TIMESTAMP]/images
```

### Convert each diagram
```bash
cat > /tmp/diagram-N.mmd << 'EOF'
[mermaid code from document]
EOF
mmdc -i /tmp/diagram-N.mmd -o generated_docs_[TIMESTAMP]/images/mermaid-fig-N.png -b transparent -w 1200
rm /tmp/diagram-N.mmd
```

### Batch conversion
```bash
for i in 1 2 3 4; do
  mmdc -i /tmp/diagram-$i.mmd -o images/mermaid-fig-$i.png -b transparent -w 1200
done
```

### Verify
```bash
ls -la generated_docs_[TIMESTAMP]/images/
```

## mmdc Options
- `-b transparent`: Transparent background
- `-w 1200`: Width in pixels
- `-H 800`: Height (optional)
- `-t dark`: Dark theme (optional)

## Important
- Original markdown file remains UNCHANGED with Mermaid code
- Diagram to PNG conversion is for Confluence publishing only
- Track figure numbers and captions for Confluence placeholders
