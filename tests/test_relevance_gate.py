from app.services.retrieval import LocalRetriever

def test_unrelated_emergency_assembly_point_question_returns_no_evidence():
    chunks = [
        {
            "document_number": "SAF-SOP-003",
            "revision": "05",
            "revision_status": "current",
            "text": (
                "Lockout Tagout procedure. Isolate electrical, compressed air "
                "and hydraulic energy before maintenance."
            ),
        },
        {
            "document_number": "QC-SOP-014",
            "revision": "04",
            "revision_status": "current",
            "text": "Incoming material inspection and sampling plan.",
        },
    ]
    results = LocalRetriever(chunks).search(
        "Where is the emergency evacuation assembly point at the Hosur plant?"
    )
    assert results == []

def test_hydraulic_pressure_question_still_retrieves_relevant_evidence():
    chunks = [
        {
            "document_number": "MNT-MAN-CNC-02",
            "revision": "02",
            "revision_status": "current",
            "text": (
                "TX-200 CNC normal hydraulic system pressure is "
                "3.5 - 4.0 MPa (35 - 40 bar)."
            ),
        },
        {
            "document_number": "SAF-SOP-003",
            "revision": "05",
            "revision_status": "current",
            "text": "Lockout tagout and isolate hydraulic energy.",
        },
    ]
    results = LocalRetriever(chunks).search(
        "What is the normal hydraulic pressure range for the TX-200 CNC machine?"
    )
    assert results
    assert results[0]["document_number"] == "MNT-MAN-CNC-02"
    assert "hydraulic" in results[0]["matched_terms"]

def test_sampling_question_still_retrieves_current_sampling_table():
    chunks = [
        {
            "document_number": "QC-SOP-014",
            "revision": "04",
            "revision_status": "current",
            "text": (
                "Sampling Plan. Lot size 91 - 500 pieces: inspect 13 samples."
            ),
        },
        {
            "document_number": "QC-SOP-014",
            "revision": "03",
            "revision_status": "historical",
            "text": "Draw five samples at random from every lot.",
        },
    ]
    results = LocalRetriever(chunks).search(
        "How many samples for a lot size of 100 in the current QC sampling plan?"
    )
    assert results
    assert all(item["revision"] == "04" for item in results)
    assert "sampling" in results[0]["matched_terms"]
