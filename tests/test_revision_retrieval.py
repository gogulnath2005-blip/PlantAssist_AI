from app.services.revision_registry import mark_revision_status, asks_for_history
from app.services.retrieval import LocalRetriever

def sample_chunks():
    docs = [
        {"document_number":"QC-SOP-014","revision":"03","text":"Always take five random samples. Use paper QF-07.","page":1,"title":"Inspection","effective_date":"15-Mar-2023"},
        {"document_number":"QC-SOP-014","revision":"04","text":"For lot size 501 to 3200 inspect 32 samples. Use QF-07A in QMS.","page":1,"title":"Inspection","effective_date":"01-Jul-2026"},
    ]
    marked = mark_revision_status(docs)
    return marked

def test_latest_revision_marked_current():
    docs = sample_chunks()
    assert {d["revision"]: d["revision_status"] for d in docs} == {"03":"historical","04":"current"}

def test_default_retrieval_excludes_historical_revision():
    results = LocalRetriever(sample_chunks()).search("inspection samples QF-07", 10)
    assert results
    assert all(r["revision"] == "04" for r in results)

def test_explicit_history_retrieves_historical_revision():
    assert asks_for_history("What did revision 03 say?")
    results = LocalRetriever(sample_chunks()).search("historical revision 03 five random samples", 10)
    assert results
    assert all(r["revision_status"] == "historical" for r in results)
