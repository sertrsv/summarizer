# summarizer
Transcribing and summarizing meetings on a local device

## Installation

1. Create virtual environment

```bash
python3 -m venv .env
```

2. Activate virtual environment

```bash
source .env/bin/activate  # для Linux/macOS
```

или

```bash
.env\Scripts\activate     # для Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Install summarizer

```bash
python3 scripts/install.py
```

## Using

```bash
python3 scripts/summarize.py <path-to-audiofile>
```