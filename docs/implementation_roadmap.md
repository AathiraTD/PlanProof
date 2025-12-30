# PlanProof Implementation Roadmap

## Recommended Next Steps

### Phase 1: Minimal UI (Priority 1 - Start Here)

**Goal**: Enable validation officers to upload documents and see basic results

**Components to Build**:
1. **Upload Page** (Streamlit)
   - File upload widget (single or multiple PDFs)
   - Application reference input field
   - Applicant name (optional)
   - Submit button that calls existing `single_pdf()` or `batch-pdf` pipeline

2. **Processing Status Page**
   - Show run status (processing, completed, failed)
   - Progress indicator for multi-document batches
   - Link to results when complete

3. **Basic Results View**
   - Validation summary (pass/fail/needs_review counts)
   - List of validation findings with rule names
   - Click to expand evidence snippets
   - Simple pass/fail indicators

**Why Start Here**:
- Unblocks non-technical users immediately
- Validates the core pipeline with real users
- Provides foundation for Phase 2 features
- Low risk, high value

**Estimated Effort**: 2-3 weeks

---

### Phase 2: Enhanced Review UI (Priority 2)

**Goal**: Enable full HITL workflow with evidence navigation and overrides

**Components to Build**:
1. **Document Viewer**
   - PDF display with page navigation
   - Page thumbnails sidebar
   - Search within document
   - Highlight evidence bounding boxes

2. **Evidence Navigation**
   - Click validation failure → jump to evidence location
   - Show page number and bounding box highlight
   - Display evidence snippet in context

3. **Officer Override**
   - Override button on validation results
   - Notes text area (required)
   - Save override with audit trail
   - Update validation status

4. **Export Functionality**
   - Export validation report as JSON
   - Export validation report as PDF
   - Include officer notes and overrides

**Why Second**:
- Builds on Phase 1 foundation
- Completes core HITL requirements
- Enables full officer workflow

**Estimated Effort**: 2-3 weeks

---

### Phase 3: Backend Enhancements (Priority 3)

**Goal**: Complete missing validation rule categories and modification workflow

**Components to Build**:
1. **Delta Computation Engine**
   - Compare V0 vs V1+ submissions
   - Generate ChangeSets and ChangeItems
   - Calculate significance scores
   - Identify impacted rules

2. **Additional Rule Categories**
   - DOCUMENT_REQUIRED rules (check required docs by case type)
   - CONSISTENCY rules (field matches across documents)
   - MODIFICATION rules (parent case reference, delta completeness)
   - SPATIAL rules (when geometry/metrics exist)

3. **Modification Workflow UI**
   - Link V1+ to parent V0 submission
   - Delta view showing what changed
   - Revalidation targeting based on changes

**Why Third**:
- Backend logic can be tested via CLI first
   - UI can be added incrementally
   - Less critical for initial MVP validation

**Estimated Effort**: 4-6 weeks

---

### Phase 4: Advanced Features (Priority 4)

**Goal**: Spatial validation, advanced search, dashboards

**Components to Build**:
1. **Spatial Features**
   - Geometry feature input (manual/assisted)
   - Spatial metric computation
   - Spatial validation rules

2. **Search and Discovery**
   - Full-text search across documents
   - Case search by application reference
   - Filter by validation status

3. **Dashboards**
   - Team lead dashboard (consistency, throughput)
   - Policy coverage visibility
   - Audit log viewer

**Why Last**:
- Nice-to-have features
- Can be added based on user feedback
- Not blocking for MVP acceptance

**Estimated Effort**: 4-6 weeks

---

## Technical Recommendations

### UI Framework: Streamlit
**Pros**:
- Fast to build (matches requirements doc preference)
- Python-native (reuse existing code)
- Good for HITL workflows
- Easy deployment

**Cons**:
- Less polished than React
- Scaling limitations (but fine for MVP)

### Architecture Pattern
```
Streamlit UI → FastAPI Backend (optional) → Existing Pipeline Functions
```

**Option A: Direct Streamlit** (Recommended for MVP)
- Streamlit calls pipeline functions directly
- Simpler, faster to build
- Good for MVP scope

**Option B: Streamlit + FastAPI** (If needed later)
- Separate API layer
- Better for scaling
- More complex

### Database Access
- Streamlit can use existing `Database()` class
- No need for separate API initially
- Can add API layer later if needed

---

## Quick Start: Phase 1 UI

### File Structure
```
planproof/
  ui/
    __init__.py
    main.py              # Streamlit app entry point
    pages/
      upload.py         # Upload page
      results.py         # Results view
      status.py          # Processing status
```

### Minimal Upload Page (Example Structure)
```python
# planproof/ui/pages/upload.py
import streamlit as st
from planproof.main import single_pdf, batch_pdf

st.title("Upload Planning Documents")

app_ref = st.text_input("Application Reference", placeholder="APP/2024/001")
uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if st.button("Process Documents"):
    if uploaded_files and app_ref:
        # Save files temporarily
        # Call batch_pdf or single_pdf
        # Redirect to status/results page
        pass
```

---

## Decision: Should You Build Upload UI?

**YES - Build it now if**:
- ✅ You need validation officers to test the system
- ✅ You want to validate the pipeline with real users
- ✅ You need to demonstrate MVP completeness
- ✅ You have 2-3 weeks available

**NO - Delay if**:
- ❌ You're still iterating on core pipeline logic
- ❌ You need to complete backend features first
- ❌ You have limited development resources
- ❌ CLI is sufficient for current testing

**Recommendation**: **YES, build Phase 1 UI now**

The upload UI is the gateway to all other HITL features. Without it, officers can't use the system, which blocks:
- Real-world testing
- User feedback collection
- MVP acceptance
- Further feature development

You can build it incrementally:
1. Week 1: Upload + basic processing
2. Week 2: Results view + evidence snippets
3. Week 3: Polish + testing

This gives you a working system officers can use while you continue building Phase 2 and 3 features.

