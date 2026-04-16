# Input Files

Place your source files here before running the pipeline.

## Directory Layout

```
input/
├── thesis/          ← Your thesis PDF (any filename, e.g. Dissertation_YourName.pdf)
├── presentation/    ← Your defence presentation PPTX
└── notes/           ← Professor question notes / PM slide deck PPTX
```

## What Goes Where

| Subfolder | File type | Used by agent |
|-----------|-----------|---------------|
| `thesis/` | `*.pdf` | `thesis_analyst` (Agent 01) |
| `presentation/` | `*.pptx` | `automl_analyst` (Agent 02) |
| `notes/` | `*.pptx` | `automl_analyst` (Agent 02) — known examiner questions |

## Notes

- Each subfolder is scanned for the **first matching file** of the expected type.
- All files in `input/` are excluded from git via `.gitignore` (except this README).
- If a required file is missing, the relevant agent will print a clear error and exit.

## Quick Setup

```powershell
# Copy your files in (adjust source paths)
Copy-Item "path\to\your\thesis.pdf"         input\thesis\
Copy-Item "path\to\your\presentation.pptx"  input\presentation\
Copy-Item "path\to\your\notes.pptx"         input\notes\

# Verify
Get-ChildItem input -Recurse
```
