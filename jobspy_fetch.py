"""Daily JobSpy fetch for Ankit's pipeline. Writes jobs.json (Bengaluru/remote, last 7 days)."""
import json, datetime, re
import pandas as pd
from jobspy import scrape_jobs

# (track, search term, sites)
QUERIES = [
    ("Cloud/DevOps", "devops cloud engineer fresher", ["linkedin", "indeed", "naukri"]),
    ("Cloud/DevOps", "AWS cloud engineer terraform docker junior", ["linkedin", "indeed"]),
    ("Cloud/DevOps", "cloud support engineer entry level", ["linkedin", "naukri"]),
    ("Internship", "devops cloud intern internship", ["linkedin", "indeed", "naukri"]),
    ("Dev", "software developer fresher", ["linkedin", "indeed", "naukri"]),
    ("Dev", "python backend developer FastAPI fresher", ["linkedin"]),
    ("IT", "IT support engineer fresher", ["linkedin", "indeed", "naukri"]),
    ("AI", "AI ML engineer fresher", ["linkedin", "indeed", "naukri"]),
    ("AI", "generative AI LLM RAG engineer fresher", ["linkedin", "indeed", "naukri"]),
    ("AI", "AI ML data science intern", ["linkedin", "naukri"]),
]
LOCS = [("Bengaluru, Karnataka, India", False), ("India", True)]  # (location, remote_only)
OK = re.compile(r"bengaluru|bangalore|remote|work from home|wfh", re.I)

rows = []
for track, term, sites in QUERIES:
    for loc, remote in LOCS:
        if remote and track not in ("Cloud/DevOps", "AI", "Dev"):
            continue
        try:
            df = scrape_jobs(site_name=sites, search_term=term, location=loc,
                             results_wanted=20, hours_old=168, country_indeed="India",
                             is_remote=remote, linkedin_fetch_description=False)
        except Exception as e:
            print("ERR", term, loc, str(e)[:120]); continue
        for r in df.to_dict("records"):
            where = f"{r.get('location') or ''} {'remote' if r.get('is_remote') else ''}"
            if not OK.search(where):
                continue
            d = r.get("date_posted")
            rows.append({
                "track_hint": track, "title": r.get("title"), "company": r.get("company"),
                "location": r.get("location"), "remote": bool(r.get("is_remote")),
                "source": r.get("site"), "url": r.get("job_url"),
                "posted": str(d) if pd.notna(d) else None,
                "job_type": r.get("job_type"), "experience": r.get("experience_range"),
                "description": (r.get("description") or "")[:1500],
            })

seen, out = set(), []
for r in rows:  # dedupe by url
    if r["url"] and r["url"] not in seen:
        seen.add(r["url"]); out.append(r)
json.dump({"generated": datetime.datetime.utcnow().isoformat() + "Z", "count": len(out), "jobs": out},
          open("jobs.json", "w"), indent=1, default=str)
print("wrote", len(out))
