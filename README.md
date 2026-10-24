# BioGraph AI — V1

A tiny first version of a biomedical knowledge-graph app.

## What it does
- Enter a disease
- Shows a disease → gene/protein → drug graph
- Click a node to inspect details
- Uses sample Alzheimer's data for now

## Run it

### 1. Open this folder in VS Code

### 2. Create a virtual environment
Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install packages
```bash
pip install -r requirements.txt
```

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

### 5. Open
http://127.0.0.1:8000

## Next milestones
1. Replace sample graph data with Open Targets / ChEMBL data
2. Add PubMed/OpenAlex paper retrieval
3. Add evidence scoring
4. Add AI-generated explanations
5. Add supporting-vs-contradicting evidence
