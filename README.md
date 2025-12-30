# PlanProof

A hybrid AI-rules validation system for planning applications that combines deterministic field extraction with gated LLM resolution for missing or ambiguous data.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Technical Choices](#technical-choices)
- [Functional Use Cases](#functional-use-cases)
- [Development](#development)
- [Pending Features](#pending-features)
- [Documentation](#documentation)
- [Contributing](#contributing)

## Overview

PlanProof processes planning application documents through a multi-stage pipeline:

1. **Ingest**: Upload PDFs to Azure Blob Storage with content hash deduplication
2. **Extract**: Use Azure Document Intelligence to extract text, tables, and layout
3. **Map Fields**: Deterministic extraction of structured fields (address, proposal, etc.)
4. **Validate**: Apply rule-based validation against extracted fields
5. **LLM Gate**: Conditionally use Azure OpenAI to resolve missing fields only when necessary

### Key Features

- **Deterministic-first design**: Fields extracted using regex and heuristics before AI
- **Evidence-linked validation**: Every field includes page numbers and text snippets
- **Document-type awareness**: Different extraction rules for application forms vs. plan sheets
- **Field ownership**: LLM only triggered for fields extractable from specific document types
- **Cost-efficient**: LLM calls reduced by 80%+ through smart gating
- **Auditable**: Complete traceability with run tracking and evidence pointers
- **Web UI**: Streamlit-based interface for document upload and results review

## Architecture

```
┌─────────────┐
│   PDFs      │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Ingest    │────▶│   Extract    │────▶│ Field Mapper│
│ (Blob + DB) │     │ (DocIntel)  │     │ (Determin.) │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Validate  │◀────│  Evidence    │     │  LLM Gate   │
│  (Rules)    │     │   Index      │     │ (Conditional)│
└──────┬──────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  Results    │
│ (JSON + DB) │
└─────────────┘
```

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick Start

### Prerequisites

- **Python 3.11+** (3.11 or 3.12 recommended)
- **Azure Account** with the following services:
  - Azure Blob Storage
  - Azure PostgreSQL Flexible Server (with PostGIS extension)
  - Azure OpenAI (gpt-4o-mini or similar)
  - Azure Document Intelligence
- **System Dependencies**:
  - Poppler (for PDF processing)
  - PostgreSQL client tools (optional, for direct DB access)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd PlanProof
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Set up database**:
   ```bash
   # Enable PostGIS extension
   python scripts/db/enable_postgis.py
   
   # Add content hash column (if needed)
   python scripts/db/add_content_hash_column.py
   
   # Or create all tables
   python scripts/db/create_tables.py
   ```

5. **Build rule catalog**:
   ```bash
   python scripts/build_rule_catalog.py
   ```

For detailed Azure setup instructions, see [docs/setup_guide.md](docs/setup_guide.md).

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_INBOX=inbox
AZURE_STORAGE_CONTAINER_ARTEFACTS=artefacts
AZURE_STORAGE_CONTAINER_LOGS=logs

# PostgreSQL Database
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname?sslmode=require

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

# Azure Document Intelligence
AZURE_DOCINTEL_ENDPOINT=https://your-service.cognitiveservices.azure.com/
AZURE_DOCINTEL_KEY=your-api-key

# Optional: Logging
LOG_LEVEL=INFO
```

**Security Note**: Never commit the `.env` file. It's already included in `.gitignore`.

## Usage

### Command Line Interface

#### Process a single PDF:
```bash
python main.py single-pdf --pdf "path/to/document.pdf" --application-ref "APP/2024/001"
```

#### Process a folder of PDFs:
```bash
python main.py batch-pdf --folder "path/to/folder" --application-ref "APP/2024/001" --applicant-name "John Doe"
```

#### Check results:
```bash
# List recent runs
python scripts/utilities/list_runs.py

# Check a specific run
python scripts/utilities/check_run.py <run_id>

# Analyze batch results
python scripts/utilities/analyze_batch.py data/batch_results.json
```

### Web UI (Streamlit)

Start the Streamlit UI:

```bash
# Windows
streamlit run planproof/ui/main.py

# Or use the convenience script
.\start_ui.bat

# Linux/Mac
streamlit run planproof/ui/main.py

# Or use the convenience script
./start_ui.sh
```

The UI will be available at `http://localhost:8501`.

**Features**:
- Upload PDF documents
- Enter application reference
- View processing status
- Review validation results with evidence
- Export results

For detailed UI usage, see [docs/guides/START_UI.md](docs/guides/START_UI.md).

### Verify Setup

Run smoke tests to verify all services are configured correctly:

```bash
python scripts/smoke_test.py
```

## Project Structure

```
PlanProof/
├── planproof/                 # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── db.py                  # Database models and helpers
│   ├── storage.py             # Azure Blob Storage client
│   ├── docintel.py            # Document Intelligence wrapper
│   ├── aoai.py                # Azure OpenAI client
│   ├── pipeline/              # Processing pipeline
│   │   ├── ingest.py          # PDF ingestion
│   │   ├── extract.py         # Document extraction
│   │   ├── field_mapper.py    # Deterministic field extraction
│   │   ├── validate.py        # Rule-based validation
│   │   └── llm_gate.py        # LLM resolution gating
│   ├── rules/                 # Rule catalog
│   │   └── catalog.py         # Rule parser
│   └── ui/                    # Streamlit web UI
│       ├── main.py            # UI entry point
│       ├── run_orchestrator.py
│       └── pages/
│           ├── upload.py      # Upload page
│           ├── status.py      # Status page
│           └── results.py     # Results page
├── scripts/                   # Utility scripts
│   ├── build_rule_catalog.py  # Build rule catalog from markdown
│   ├── smoke_test.py          # Test Azure connections
│   ├── db/                    # Database scripts
│   │   ├── create_tables.py
│   │   ├── enable_postgis.py
│   │   └── migrate_*.py
│   ├── utilities/             # Utility scripts
│   │   ├── check_*.py         # Various check scripts
│   │   ├── list_*.py          # Listing scripts
│   │   └── query_*.py         # Query scripts
│   └── analysis/              # Analysis scripts
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── API.md                 # API documentation
│   ├── DATA_STORAGE_STRATEGY.md
│   ├── TROUBLESHOOTING.md     # Troubleshooting guide
│   ├── setup_guide.md         # Detailed setup instructions
│   └── guides/                # Additional guides
│       └── ...
├── tests/                     # Test files
│   └── test_*.py
├── data/                      # Sample/test data
│   └── *.json
├── artefacts/                 # Generated artefacts
│   └── rule_catalog.json      # Parsed validation rules
├── runs/                      # Runtime outputs (gitignored)
│   └── <run_id>/
│       ├── inputs/
│       └── outputs/
├── main.py                    # CLI entry point
├── run_ui.py                  # UI entry point (alternative)
├── validation_requirements.md # Source of truth for validation rules
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Dependencies

### Core Libraries

- **FastAPI** (0.109.0): Web API framework
- **Streamlit** (1.30.0): Web UI framework
- **SQLAlchemy** (2.0.25): ORM for database operations
- **psycopg[binary]** (3.3.2): PostgreSQL adapter (Psycopg 3)
- **GeoAlchemy2** (0.14.3): PostGIS support
- **Pydantic** (2.5.3): Data validation and settings management

### Azure Services

- **azure-storage-blob** (12.19.0): Blob Storage client
- **azure-ai-documentintelligence** (1.0.2): Document Intelligence client
- **openai** (1.10.0): Azure OpenAI client
- **azure-identity** (1.15.0): Azure authentication

### Document Processing

- **pdfplumber** (0.10.3): PDF text extraction
- **pdf2image** (1.17.0): PDF to image conversion (requires Poppler)
- **pytesseract** (0.3.10): OCR fallback (optional, requires Tesseract)

### NLP & Utilities

- **spacy** (3.7.2): NLP processing (requires `en_core_web_sm` model)
- **python-dotenv** (1.0.0): Environment variable management
- **httpx** (0.26.0): HTTP client

### Testing & Quality

- **pytest** (7.4.4): Testing framework
- **black** (24.1.1): Code formatting
- **flake8** (7.0.0): Linting
- **mypy** (1.8.0): Type checking

See [requirements.txt](requirements.txt) for the complete list with versions.

## Technical Choices

### Architecture Decisions

1. **Hybrid Storage Strategy**
   - JSON artefacts in Blob Storage for complete audit trail
   - Relational tables in PostgreSQL for queryable, structured data
   - Benefits: Auditability + Queryability

2. **Deterministic-First Approach**
   - Regex and heuristics extract 70-90% of fields
   - LLM only used as fallback for missing/ambiguous fields
   - Reduces costs by 80%+ while maintaining accuracy

3. **Evidence-Linked Extraction**
   - Every field includes page numbers and text snippets
   - Enables traceability, explainability, and defensibility
   - Supports human-in-the-loop workflows

4. **Field Ownership Model**
   - Different document types can extract different fields
   - Prevents false negatives (e.g., not expecting application_ref on plan sheets)
   - LLM gating respects field ownership

5. **PostGIS for Spatial Data**
   - Database schema includes geometry columns
   - Ready for spatial validation rules (not yet implemented)
   - Supports future spatial metric calculations

6. **Azure-First Infrastructure**
   - All core services are Azure-managed
   - Local development connects to cloud services
   - Enables cost control (stop/start database)
   - Build once, deploy anywhere parity

### Technology Stack Rationale

- **Python 3.11+**: Modern type hints, performance improvements
- **Psycopg 3**: Modern PostgreSQL adapter with async support (prepared for future)
- **SQLAlchemy 2.0**: Modern ORM with better type support
- **Streamlit**: Rapid UI development for MVP, can migrate to React later
- **FastAPI**: Modern async API framework (prepared for future API needs)
- **Pydantic Settings**: Type-safe configuration management

### Database Design

- **Hybrid storage**: JSON + Relational
- **Content hash deduplication**: SHA256-based document deduplication
- **Run tracking**: Complete audit trail for all processing operations
- **Submission versioning**: Support for V0 and V1+ submissions with parent-child relationships
- **PostGIS extension**: Ready for spatial operations

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Functional Use Cases

### 1. Process New Planning Application

**Scenario**: Validation officer receives a new planning application with multiple PDF documents.

**Workflow**:
1. Upload PDFs via Web UI or CLI
2. System ingests documents to Blob Storage
3. Documents are extracted using Document Intelligence
4. Fields are extracted deterministically (address, proposal, etc.)
5. Validation rules are applied
6. Missing fields trigger LLM resolution (if needed)
7. Results are displayed with evidence pointers
8. Officer reviews and can export results

**Commands**:
```bash
# CLI
python main.py batch-pdf --folder "documents" --application-ref "APP/2024/001"

# Or use Web UI
streamlit run planproof/ui/main.py
```

### 2. Validate Single Document

**Scenario**: Quick validation of a single document to check field extraction.

**Workflow**:
1. Process single PDF
2. Review extracted fields and validation results
3. Check evidence pointers

**Command**:
```bash
python main.py single-pdf --pdf "document.pdf" --application-ref "APP/2024/001"
```

### 3. Check Processing Status

**Scenario**: Monitor batch processing status.

**Workflow**:
1. List recent runs
2. Check run status
3. View results for completed runs

**Commands**:
```bash
python scripts/utilities/list_runs.py
python scripts/utilities/check_run.py <run_id>
```

### 4. Analyze Batch Results

**Scenario**: Analyze validation results across multiple documents.

**Workflow**:
1. Process batch and save results JSON
2. Run analysis script
3. Review summary statistics

**Command**:
```bash
python main.py batch-pdf --folder "documents" --application-ref "APP/2024/001" --out batch_results.json
python scripts/utilities/analyze_batch.py batch_results.json
```

### 5. Add New Validation Rule

**Scenario**: Add a new validation rule to the system.

**Workflow**:
1. Edit `validation_requirements.md`
2. Rebuild rule catalog
3. Rule is automatically loaded in next validation run

**Command**:
```bash
# Edit validation_requirements.md, then:
python scripts/build_rule_catalog.py
```

## Development

### Running Tests

```bash
# Smoke test Azure connections
python scripts/smoke_test.py

# Verify blob storage
python scripts/utilities/check_blobs.py

# Check database
python scripts/utilities/check_db.py
```

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to all public functions
- Format code with `black`
- Check types with `mypy`

### Adding New Fields

1. Add extraction logic to `planproof/pipeline/field_mapper.py`
2. Update validation rules in `validation_requirements.md`
3. Rebuild catalog: `python scripts/build_rule_catalog.py`

### Adding New Rules

1. Edit `validation_requirements.md` following the existing format
2. Rebuild catalog: `python scripts/build_rule_catalog.py`
3. Rules are automatically loaded during validation

### Adding New Document Types

1. Add classification hints to `DOC_TYPE_HINTS` in `field_mapper.py`
2. Update `DOC_FIELD_OWNERSHIP` with extractable fields
3. Test with sample documents

For detailed development guidelines, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Pending Features

The following features are planned but not yet implemented:

### High Priority

1. **Enhanced UI Features**
   - Document viewer with page thumbnails, zoom, and search
   - Evidence navigation UI (jump to evidence bounding boxes)
   - Officer override functionality with notes and audit trail
   - Export validation reports as PDF

2. **Modification Workflow**
   - Delta computation engine (V0 vs V1+ submissions)
   - ChangeSet and ChangeItem generation
   - Significance scoring for changes
   - Revalidation targeting based on deltas

3. **Spatial Features**
   - Geometry feature creation (manual/assisted outline input)
   - Spatial metric computation (distance, area, projections)
   - Spatial validation rules

### Medium Priority

4. **Advanced Validation**
   - Document type-specific required document validation
   - Consistency validation rules (field matches across documents)
   - Modification validation rules
   - Conflict detection and reconciliation

5. **Search & Analytics**
   - Full-text search (PostgreSQL or Azure AI Search)
   - Dashboard for team leads (metrics and throughput)
   - Monitoring and observability (Application Insights)

6. **Workflow Features**
   - Request-info workflow for incomplete submissions
   - Case and submission overview screens
   - RBAC (Role-Based Access Control)

### Lower Priority

7. **Additional OCR Support**
   - Tier 3 OCR fallback (Tesseract) - currently only Tier 1 and Tier 2 implemented

8. **Testing & Quality**
   - Golden-case test set for verification
   - Evidence integrity checks
   - Usability walkthrough testing

For detailed requirements status, see [docs/guides/requirements_status.md](docs/guides/requirements_status.md).

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System architecture and design decisions
- **[API Documentation](docs/API.md)**: API endpoints and usage
- **[Data Storage Strategy](docs/DATA_STORAGE_STRATEGY.md)**: Hybrid storage approach
- **[Setup Guide](docs/setup_guide.md)**: Detailed Azure setup instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Query Guide](docs/QUERY_GUIDE.md)**: Database querying examples
- **[Contributing](docs/CONTRIBUTING.md)**: Development guidelines

Additional guides are available in the [docs/guides/](docs/guides/) directory.

## Contributing

Contributions are welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license here]

## Contact

[Add contact information]
