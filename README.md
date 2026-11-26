# LLM File System & Resume Assistant

A set of file system tools for an LLM agent. The tools read, list, search and write documents in `.pdf`, `.docx` and `.txt` formats. Each tool comes with an OpenAI-compatible function-calling schema, so a model can call it.

## Features

| Tool | Description |
|------|-------------|
| `read_file(filepath)` | Extracts text from `.pdf`, `.docx` and `.txt` files and returns it with metadata (name, absolute path, size, extension). |
| `list_files(directory, extension=None)` | Lists the files in a directory, with an optional extension filter (`"pdf"` or `".pdf"`). Returns name, path, size and modified date. |
| `search_in_file(filepath, keyword)` | Case-insensitive keyword search that returns each match's line number and the lines on either side of it. |
| `write_file(filepath, content)` | Writes UTF-8 text and creates any missing parent directories. |

Every tool returns a JSON-serializable `dict` with a `status` of `"success"` or `"error"`. The one exception is `list_files`, which returns a list and gives an empty list when the directory is missing.

`TOOLS_SCHEMA` holds the function-calling definitions for all four tools.

## Project Structure

```
.
├── fs_tools.py        # Tool implementations + TOOLS_SCHEMA
├── requirements.txt   # Python dependencies
├── resumes/           # Sample resumes (.pdf, .docx, .txt)
└── summaries/         # Generated resume summaries
```

## Installation

Requires Python 3.8+.

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Usage

### Calling the tools directly

```python
from fs_tools import read_file, list_files, search_in_file, write_file

for f in list_files("resumes", extension="pdf"):
    print(f["name"], f["size_bytes"])

print(read_file("resumes/resume_john_doe.txt")["content"])

result = search_in_file("resumes/resume_jane_smith.pdf", "python")
print(result["match_count"], "matches")

write_file("summaries/example.txt", "Summary text here")
```

### Using the tools with an LLM (function calling)

`fs_tools.py` has no agent loop of its own. The example below shows one way to connect the tools to the OpenAI API. Set `OPENAI_API_KEY` in your environment before running it.

```python
import json
from openai import OpenAI
from fs_tools import TOOLS_SCHEMA, read_file, list_files, search_in_file, write_file

TOOLS = {
    "read_file": read_file,
    "list_files": list_files,
    "search_in_file": search_in_file,
    "write_file": write_file,
}

client = OpenAI()
messages = [{"role": "user", "content": "Which resumes in ./resumes mention Python? Summarize them into ./summaries."}]

while True:
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=TOOLS_SCHEMA)
    msg = response.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        print(msg.content)
        break
    for call in msg.tool_calls:
        result = TOOLS[call.function.name](**json.loads(call.function.arguments))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
```

## Notes

- `.doc`, `.rtf` and other formats return an `Unsupported extension` error.
- Text extraction from scanned or image-only PDFs may return empty content (no OCR).
- `write_file` overwrites existing files.
- `reportlab` is listed in `requirements.txt` for generating sample PDF resumes. The tools themselves don't use it.
