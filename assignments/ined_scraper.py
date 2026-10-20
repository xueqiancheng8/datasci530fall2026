# %% Setup
import re, time
from datetime import date
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE = "https://www.ined.fr"
LIST_URL = BASE + "/en/research/research-activites"
DELAY = 1.5   # seconds between requests (document as a collection restriction)
HEADERS = {"User-Agent": "DATASCI530 student project (your.email@emory.edu)"}

def get_soup(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(DELAY)
    return BeautifulSoup(r.text, "html.parser")

# %% Step 1: loop over listing pages (12 projects per page)
def parse_listing(soup):
    rows = {}
    for a in soup.select('a[href*="/research-activites/ct-projectsearch-id-"]'):
        url = BASE + a["href"] if a["href"].startswith("/") else a["href"]
        card = a.find_parent(["li", "article", "div"])          # VERIFY with Inspect
        status = re.search(r"\b(Ongoing|Closed)\b", card.get_text(" ")) if card else None
        rows[url] = {"url": url,
                     "project_id": int(re.search(r"id-(\d+)", url).group(1)),
                     "status": status.group(1) if status else None}
    return list(rows.values())   # dict removes duplicate links to the same project

listing, page = [], 0
while True:
    rows = parse_listing(get_soup(LIST_URL, {"page": page}))
    if not rows:
        break
    listing += rows
    page += 1
projects = pd.DataFrame(listing).drop_duplicates("url")

# %% Step 2: automated navigation into each project page
HEADINGS = {"Members List", "Head of Units", "Research unit", "Research activities",
            "Research axes", "Programme structurant", "Funding", "Funding program :",
            "Mini-site", "Follow us!"}

def section(lines, heading):
    """Lines after `heading` up to the next known heading."""
    if heading not in lines:
        return []
    out = []
    for line in lines[lines.index(heading) + 1:]:
        if line in HEADINGS:
            break
        out.append(line)
    return out

def parse_project(url):
    s = get_soup(url)
    h1 = s.find("h1")
    lines = [l.strip() for l in s.get_text("\n").split("\n") if l.strip()]
    lines = lines[lines.index(h1.get_text(strip=True)) + 1:]    # skip header/nav menus

    leads = section(lines, "Head of Units")                      # name, role, name, role...
    names, roles = leads[0::2], leads[1::2]
    axes = [l for l in section(lines, "Research axes") if l not in {"Ongoing", "Closed", "Axe"}]
    funding = section(lines, "Funding program :")
    funding = funding[0] if funding else None
    updated = next((l for l in lines if l.startswith("Updated on")), None)

    return {"url": url,
            "acronym": h1.get_text(strip=True).split(" - CT")[0] or None,
            "lead_names": "; ".join(names), "lead_roles": "; ".join(roles),
            "n_leads": len(names),
            "units": "; ".join(section(lines, "Research unit")),
            "n_units": len(section(lines, "Research unit")),
            "axes": "; ".join(dict.fromkeys(axes)),               # names appear twice
            "funding_program": funding,
            "ined_role": (re.search(r"INED (coordinateur|partenaire)", funding or "") or [None, None])[1],
            "updated_on": updated.replace("Updated on ", "") if updated else None}

details = pd.DataFrame([parse_project(u) for u in projects["url"]])

# %% Step 3: merge and save
out = projects.merge(details, on="url", how="left")
out["collected_on"] = date.today().isoformat()
out.to_csv("ined_projects.csv", index=False)

# Long table: one row per project lead (useful for "who works on what")
leads = (out.assign(name=out["lead_names"].str.split("; "), role=out["lead_roles"].str.split("; "))
            .explode(["name", "role"])[["project_id", "acronym", "name", "role", "units"]]
            .query("name != ''"))
leads.to_csv("ined_project_leads.csv", index=False)

print(len(out), "projects;", len(leads), "project-lead rows")
print(out.isna().sum())
