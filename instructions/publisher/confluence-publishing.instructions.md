---
description: Confluence page creation and publishing workflow for the Publisher agent.
---

# Confluence Publishing

## Workflow
1. Convert all Mermaid diagrams to PNG (see [diagram-conversion](diagram-conversion.instructions.md))
2. Prepare Confluence content (in-memory conversion only):
   - Replace each ```mermaid block with `[ATTACHMENT: mermaid-fig-N.png]`
   - Format figure captions in italic: `*Fig N: description*`
3. Create Confluence page using MCP confluence_create_page:
   - space_key: from user request
   - parent_id: from user request (page ID from URL)
   - title: from document H1 header
   - content: converted markdown with attachment placeholders
4. Record page ID and URL
5. Report completion with manual upload instructions

## Known Limitations
- MCP Confluence tools CANNOT upload file attachments
- CANNOT embed images programmatically
- Manual image insertion ALWAYS required after page creation

## Manual Upload Instructions (include in report)
```
To add diagrams to Confluence:
1. Open page: [URL]
2. Click "..." → "Attachments"
3. Upload all PNG files from: [images folder path]
4. Edit page
5. For each [ATTACHMENT: filename.png] placeholder:
   - Delete the placeholder text
   - Click "+" → "Image"
   - Select the uploaded file
6. Save page
```

## Publishing Report Format
```
# Publishing Complete: [Page Title]

Confluence Details:
- URL: [Full page URL]
- Page ID: [ID]
- Space: [Space key]
- Version: [N]

Diagrams Converted:
| # | File | Size | Caption |
|---|------|------|---------|
| 1 | mermaid-fig-1.png | 65 KB | Fig 1: [desc] |

Images Location: [path to images/ folder]
Status: Page created, awaiting manual image upload
```
