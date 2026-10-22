"""Build guptavis.com into _site/.  Usage: python build.py

Hand-authored pages live in templates/ and share base.html. The only generated content is the
publications list, rendered from data/papers.yml. The build FAILS if a referenced local PDF or the
CV is missing, or if a filename differs in case (this is what would have caught debiasing.pdf).
"""
import datetime, json, os, re, shutil, sys
import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "_site")
LINK_ORDER = [("doi", "DOI"), ("proceedings", "Proceedings"), ("chapter", "Chapter"), ("pdf", "PDF"),
              ("optimization_online", "Optimization Online"), ("ssrn", "SSRN"), ("arxiv", "arXiv"),
              ("openreview", "OpenReview"), ("code", "Code")]
TOPICS = ["Decision-focused learning", "Small-data optimization", "Policy evaluation", "Optimization proxies",
          "Robust optimization", "Inverse optimization", "Deployed systems", "Education"]
APPS = ["Healthcare & public health", "Supply chain", "Pricing", "Public sector", "Finance"]
VENUE_ORDER = ["Management Science", "Operations Research", "Mathematical Programming", "Nature", "NeurIPS",
               "AISTATS", "INFORMS Journal on Applied Analytics", "European Journal of Operational Research",
               "INFORMS Transactions on Education", "Book chapters", "Technical notes", "Under review"]
SIDE_LIST = {"workshop", "working"}
errors = []


def exists_exact(path):
    """True only if every path component exists with exactly this spelling (macOS is case-insensitive)."""
    d = ROOT
    for part in os.path.relpath(path, ROOT).split(os.sep):
        if part not in os.listdir(d):
            return False
        d = os.path.join(d, part)
    return True


def initials(name):
    *given, last = name.split()
    return "".join(g if g.endswith(".") else ".".join(x[0] for x in g.split("-")) + "." for g in given) + " " + last


def italics(s):
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", str(escape(s)))


def author_html(name, students):
    star = "*" if name.rstrip("†") in students else ""
    dag = "<sup>†</sup>" if name.endswith("†") else ""
    n = name.rstrip("†")
    if n == "Vishal Gupta":
        return f"<b>V. Gupta{dag}</b>"
    return f"{escape(initials(n))}{star}{dag}"


def join(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def prepare(p):
    students = set(p.get("student_coauthors") or [])
    venue = italics(p["venue_short"])
    if p["status"] == "accepted":
        venue += ", forthcoming"
    elif p["status"] in SIDE_LIST and p.get("year"):
        venue += f" {p['year']}"
    elif p.get("year") and p["status"] != "under_review":
        venue += f", {p['year']}"
    if p.get("author_order"):
        who = join([author_html(a, students) for a in p["author_order"]]) + " · "
    elif p["authors"]:
        who = "with " + join([author_html(a, students) for a in p["authors"]]) + " · "
    else:
        who = "" if "chapter" in p["venue_short"].lower() else "Single-authored · "
    p["byline"] = Markup(who + venue)
    p["author_note_html"] = Markup(str(escape(p.get("author_note") or "")).replace("†", "<sup>†</sup>"))
    links = p.get("links") or {}
    p["link_list"] = [(label, links[k]) for k, label in LINK_ORDER if links.get(k)]
    if p.get("local_pdf"):
        local = os.path.join(ROOT, "static", "papers", p["local_pdf"])
        if not exists_exact(local):
            errors.append(f"{p['key']}: local_pdf static/papers/{p['local_pdf']} is missing (or its case differs)")
        p["link_list"].append(("PDF", "/papers/" + p["local_pdf"]))
    p["href"] = p.get("primary") or (p.get("local_pdf") and "/papers/" + p["local_pdf"])
    p["filter_json"] = json.dumps({"t": p.get("themes") or [], "a": p.get("applications") or [],
                                   "v": p.get("venue_group")})
    for t in p.get("themes") or []:
        if t not in TOPICS: errors.append(f"{p['key']}: unknown topic {t!r}")
    for a in p.get("applications") or []:
        if a not in APPS: errors.append(f"{p['key']}: unknown application {a!r}")
    return p


def sort_key(p):
    if p.get("year") is None:
        return (0, 0 if p["status"] == "under_review" else 1)
    return (1, -p["year"])


def main():
    site = yaml.safe_load(open(os.path.join(ROOT, "data", "site.yml")))
    papers = [prepare(p) for p in yaml.safe_load(open(os.path.join(ROOT, "data", "papers.yml")))]
    pubs = sorted([p for p in papers if p["status"] not in SIDE_LIST], key=sort_key)
    others = sorted([p for p in papers if p["status"] in SIDE_LIST], key=sort_key)
    if not exists_exact(os.path.join(ROOT, "static", "cv.pdf")):
        errors.append("static/cv.pdf is missing (copy GuptaCV.pdf there, NEVER the -internal PDF)")
    if errors:
        sys.exit("BUILD FAILED:\n  " + "\n  ".join(errors))

    icons = {f[:-4]: Markup(open(os.path.join(ROOT, "static", "icons", f)).read().strip())
             for f in os.listdir(os.path.join(ROOT, "static", "icons")) if f.endswith(".svg")}
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=True)
    common = dict(site=site, icon=icons, year=datetime.date.today().year)
    person = {"@context": "https://schema.org", "@type": "Person", "name": site["name"], "url": site["url"] + "/",
              "image": site["url"] + "/img/headshot-large.jpg", "email": "mailto:" + site["email"],
              "jobTitle": site["job_title"],
              "affiliation": {"@type": "CollegeOrUniversity", "name": "University of Southern California"},
              "alumniOf": ["Massachusetts Institute of Technology", "Yale University", "University of Cambridge"],
              "sameAs": [site["scholar"], site["orcid"], site["github"]]}
    desc = ("Vishal Gupta is an operations research and machine learning researcher at USC Marshall, "
            "working on how optimization structure should shape learning when data are scarce or noisy.")
    pages = [
        ("home.html", "/", "Vishal Gupta · USC Marshall", desc,
         dict(selected=[p for p in pubs if p.get("selected")], person_jsonld=Markup(json.dumps(person)))),
        ("publications.html", "/publications/", "Publications · Vishal Gupta",
         "Publications by Vishal Gupta on decision-focused learning, small-data optimization, policy evaluation and robust optimization.",
         dict(pubs=pubs, others=others, topics=TOPICS, apps=APPS,
              venues=[v for v in VENUE_ORDER if any(p["venue_group"] == v for p in pubs)]
              + sorted({p["venue_group"] for p in pubs} - set(VENUE_ORDER)))),
        ("phd.html", "/phd/", "Students · Vishal Gupta",
         f"Prospective PhD students: Vishal Gupta is admitting students for {site['recruiting']['term']} at USC.", {}),
        ("about.html", "/about/", "About · Vishal Gupta", "About Vishal Gupta, with a bio and photo for organizers.", {}),
    ]
    # Overwrite in place (no rmtree): CI always starts clean, and locally this avoids deleting files.
    shutil.copytree(os.path.join(ROOT, "static"), OUT, ignore=shutil.ignore_patterns("icons", ".DS_Store"),
                    dirs_exist_ok=True)
    for tpl, path, title, description, extra in pages:
        html = env.get_template(tpl).render(path=path, title=title, description=description, **common, **extra)
        dest = os.path.join(OUT, path.strip("/"), "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w").write(html)
    urls = "".join(f"<url><loc>{site['url']}{p[1]}</loc></url>" for p in pages)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n")
    print(f"Built {len(pages)} pages, {len(pubs)} publications + {len(others)} working/workshop papers -> _site/")


if __name__ == "__main__":
    main()
