# guptavis.com

Source for [guptavis.com](https://guptavis.com). Hand-authored HTML (Jinja templates sharing one header and footer) plus a small generator for the publications list. Pushing to `main` builds and deploys via GitHub Actions to GitHub Pages.

- `data/papers.yml`: publications, the single source of truth (schema in its header comment).
- `data/site.yml`: name, links, nav and the yearly `recruiting` line.
- `templates/`: pages. `base.html` holds the shared header and footer.
- `static/`: `site.css` (the design system), images, icons (self-hosted SVG), hosted paper PDFs, and `cv.pdf`.
- `build.py`: renders everything into `_site/`. It **fails** if a `local_pdf` is missing or differs in case, or if `cv.pdf` is missing.

Preview locally:

```
pip install -r requirements.txt
python build.py && python -m http.server -d _site 8000
```

`static/cv.pdf` is a copy of `GuptaCV.pdf` from `~/Documents/Resumes and CVS/LaTexConversion/`. **Never** the `-internal` PDF.
The old Jekyll site is archived in the `faculty_website` repo.
