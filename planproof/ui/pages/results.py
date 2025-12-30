"""
Results page - Display validation results and findings.
"""

import streamlit as st
import json
import zipfile
from pathlib import Path
from planproof.ui.run_orchestrator import get_run_results


def render():
    """Render the results page."""
    st.title("📋 Validation Results")
    
    # Get run_id from session state or allow manual input
    run_id_input = st.text_input(
        "Run ID",
        value=str(st.session_state.run_id) if st.session_state.run_id else "",
        help="Enter the run ID to view results"
    )
    
    if not run_id_input:
        st.info("Enter a run ID to view results, or go to Upload page to start a new run.")
        return
    
    try:
        run_id = int(run_id_input)
    except ValueError:
        st.error("Run ID must be a number")
        return
    
    # Fetch results
    results = get_run_results(run_id)
    
    if "error" in results:
        st.error(results["error"])
        return
    
    # Summary cards
    st.markdown("### Summary")
    summary = results.get("summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", summary.get("total_documents", 0))
    
    with col2:
        st.metric("Processed", summary.get("processed", 0))
    
    with col3:
        st.metric("Errors", summary.get("errors", 0))
    
    with col4:
        st.metric("LLM Calls", results.get("llm_calls_per_run", 0))
    
    # Validation summary by status
    findings = results.get("validation_findings", [])
    
    if findings:
        # Count by status
        pass_count = sum(1 for f in findings if f.get("status") == "pass")
        needs_review_count = sum(1 for f in findings if f.get("status") == "needs_review")
        fail_count = sum(1 for f in findings if f.get("status") == "fail")
        
        st.markdown("### Validation Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success(f"✅ PASS: {pass_count}")
        
        with col2:
            st.warning(f"⚠️ NEEDS REVIEW: {needs_review_count}")
        
        with col3:
            st.error(f"❌ FAIL: {fail_count}")
    
    # Findings table
    st.markdown("### Validation Findings")
    
    if not findings:
        st.info("No validation findings available.")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pass", "needs_review", "fail"],
                index=0
            )
        
        with col2:
            severity_filter = st.selectbox(
                "Filter by Severity",
                ["All", "error", "warning"],
                index=0
            )
        
        # Apply filters
        filtered_findings = findings
        if status_filter != "All":
            filtered_findings = [f for f in filtered_findings if f.get("status") == status_filter]
        if severity_filter != "All":
            filtered_findings = [f for f in filtered_findings if f.get("severity") == severity_filter]
        
        # Display findings
        for idx, finding in enumerate(filtered_findings):
            with st.expander(
                f"{finding.get('rule_id', 'Unknown')} - {finding.get('status', 'unknown').upper()} "
                f"({finding.get('document_name', 'unknown')})"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Rule ID:** {finding.get('rule_id', 'N/A')}")
                    st.markdown(f"**Status:** {finding.get('status', 'N/A')}")
                    st.markdown(f"**Severity:** {finding.get('severity', 'N/A')}")
                    st.markdown(f"**Document:** {finding.get('document_name', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Message:** {finding.get('message', 'N/A')}")
                    if finding.get('missing_fields'):
                        st.markdown(f"**Missing Fields:** {', '.join(finding['missing_fields'])}")
                
                # Evidence section
                evidence = finding.get("evidence", {})
                if evidence:
                    st.markdown("**Evidence:**")
                    
                    evidence_snippets = evidence.get("evidence_snippets", [])
                    if evidence_snippets:
                        for ev in evidence_snippets[:3]:  # Show top 3
                            page = ev.get("page", "?")
                            snippet = ev.get("snippet", "")
                            st.code(f"Page {page}: {snippet}", language="text")
                    else:
                        st.info("No evidence snippets available")
    
    # Errors section
    errors = results.get("errors", [])
    if errors:
        st.markdown("### Processing Errors")
        for error in errors:
            with st.expander(f"❌ {error.get('filename', 'Unknown file')}"):
                st.error(error.get("error", "Unknown error"))
                if error.get("traceback"):
                    st.code(error.get("traceback"), language="text")
    
    # Export buttons
    st.markdown("---")
    st.markdown("### Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download JSON
        json_data = json.dumps(results, indent=2, ensure_ascii=False)
        st.download_button(
            "📥 Download JSON",
            data=json_data,
            file_name=f"results_run_{run_id}.json",
            mime="application/json"
        )
    
    with col2:
        # Download run bundle (zip)
        def create_run_bundle():
            """Create a zip file with all run artifacts."""
            run_dir = Path(f"./runs/{run_id}")
            if not run_dir.exists():
                return None
            
            import io
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add inputs
                inputs_dir = run_dir / "inputs"
                if inputs_dir.exists():
                    for file_path in inputs_dir.glob("*"):
                        zip_file.write(file_path, f"inputs/{file_path.name}")
                
                # Add outputs
                outputs_dir = run_dir / "outputs"
                if outputs_dir.exists():
                    for file_path in outputs_dir.glob("*"):
                        zip_file.write(file_path, f"outputs/{file_path.name}")
                
                # Add results JSON
                zip_file.writestr("results.json", json_data)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
        
        bundle_data = create_run_bundle()
        if bundle_data:
            st.download_button(
                "📦 Download Run Bundle (ZIP)",
                data=bundle_data,
                file_name=f"run_{run_id}_bundle.zip",
                mime="application/zip"
            )
        else:
            st.info("Run bundle not available")

