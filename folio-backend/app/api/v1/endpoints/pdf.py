"""
app/services/pdf_service.py
────────────────────────────
Generate pixel-perfect PDF resumes via WeasyPrint + Jinja2 templates.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

# WeasyPrint for HTML → PDF
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "resume"

_jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render_html(resume_data: Dict[str, Any], template_id: str = "modern") -> str:
    """Render resume data into HTML using a Jinja2 template."""
    template_file = f"{template_id}.html"

    # Fallback to modern if template not found
    try:
        template = _jinja.get_template(template_file)
    except Exception:
        template = _jinja.get_template("modern.html")

    return template.render(resume=resume_data)


def generate_pdf(
    resume_data: Dict[str, Any],
    template_id: str = "modern",
    output_path: Optional[str] = None,
) -> bytes:
    """
    Generate a PDF from resume data.
    Returns raw PDF bytes.
    If output_path is given, also writes to disk.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not installed. Run: pip install weasyprint")

    html_content = _render_html(resume_data, template_id)

    # Base URL for resolving relative CSS/font paths
    base_url = str(TEMPLATES_DIR)

    pdf_bytes = HTML(string=html_content, base_url=base_url).write_pdf()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Inline HTML template (used when no file template exists)
# This is the "Modern Clean" style.
# ─────────────────────────────────────────────────────────────────────────────
MODERN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;600&family=DM+Mono:wght@400&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; color: #0d0d0d; font-size: 10pt; line-height: 1.5; padding: 2.5cm; }
  h1 { font-family: 'Playfair Display', serif; font-size: 28pt; font-weight: 900; letter-spacing: -0.03em; }
  h2 { font-family: 'DM Mono', monospace; font-size: 7pt; text-transform: uppercase; letter-spacing: 0.12em; color: #7a7265; margin: 16pt 0 6pt; padding-bottom: 4pt; border-bottom: 1px solid #d8d2c5; }
  .role { color: #c8503a; font-size: 11pt; font-weight: 600; margin-top: 2pt; }
  .contact { display: flex; gap: 20pt; margin-top: 8pt; font-size: 8.5pt; color: #7a7265; flex-wrap: wrap; }
  .divider { border: none; border-top: 1.5px solid #0d0d0d; margin: 10pt 0; }
  .summary { font-size: 9.5pt; line-height: 1.7; color: #444; }
  .job { margin-bottom: 10pt; }
  .job-header { display: flex; justify-content: space-between; align-items: baseline; }
  .job-title { font-weight: 700; font-size: 10pt; }
  .job-company { color: #7a7265; font-size: 9pt; }
  .job-date { font-family: 'DM Mono', monospace; font-size: 8pt; color: #7a7265; }
  ul { padding-left: 14pt; margin-top: 4pt; }
  li { font-size: 9pt; color: #444; margin-bottom: 2pt; }
  .skills { display: flex; flex-wrap: wrap; gap: 4pt; margin-top: 4pt; }
  .skill { background: #ede8dd; padding: 2pt 7pt; border-radius: 3pt; font-size: 8.5pt; font-weight: 500; }
  .edu-row { display: flex; justify-content: space-between; }
  .edu-school { font-weight: 700; font-size: 10pt; }
  .edu-degree { color: #7a7265; font-size: 9pt; margin-top: 2pt; }
  .proj-name { font-weight: 700; font-size: 9.5pt; }
  .proj-stack { color: #c8503a; font-size: 8.5pt; font-weight: 600; margin: 1pt 0; }
  .proj-desc { font-size: 8.5pt; color: #444; }
</style>
</head>
<body>
  <h1>{{ resume.first_name }} {{ resume.last_name }}</h1>
  <div class="role">{{ resume.professional_title }}</div>
  <div class="contact">
    {% if resume.email %}<span>{{ resume.email }}</span>{% endif %}
    {% if resume.contact.phone %}<span>{{ resume.contact.phone }}</span>{% endif %}
    {% if resume.contact.location %}<span>{{ resume.contact.location }}</span>{% endif %}
    {% if resume.contact.linkedin %}<span>{{ resume.contact.linkedin }}</span>{% endif %}
    {% if resume.contact.github %}<span>{{ resume.contact.github }}</span>{% endif %}
  </div>
  <hr class="divider"/>

  {% if resume.summary %}
  <h2>Professional Summary</h2>
  <p class="summary">{{ resume.summary }}</p>
  {% endif %}

  {% if resume.experience %}
  <h2>Work Experience</h2>
  {% for job in resume.experience %}
  <div class="job">
    <div class="job-header">
      <div>
        <div class="job-title">{{ job.job_title }}</div>
        <div class="job-company">{{ job.company }}{% if job.location %} · {{ job.location }}{% endif %}</div>
      </div>
      <div class="job-date">{{ job.start_date or '' }}{% if job.end_date %} — {{ job.end_date }}{% endif %}</div>
    </div>
    {% if job.description %}
    <ul>
      {% for bullet in job.description.split('\\n') %}
        {% if bullet.strip() %}
        <li>{{ bullet.strip().lstrip('•-').strip() }}</li>
        {% endif %}
      {% endfor %}
    </ul>
    {% endif %}
  </div>
  {% endfor %}
  {% endif %}

  {% if resume.projects %}
  <h2>Projects</h2>
  {% for proj in resume.projects %}
  <div class="job">
    <div class="proj-name">{{ proj.name }}</div>
    {% if proj.tech_stack %}<div class="proj-stack">{{ proj.tech_stack }}</div>{% endif %}
    {% if proj.description %}<div class="proj-desc">{{ proj.description }}</div>{% endif %}
  </div>
  {% endfor %}
  {% endif %}

  {% if resume.skills %}
  <h2>Skills</h2>
  <div class="skills">
    {% for skill in resume.skills %}
    <span class="skill">{{ skill }}</span>
    {% endfor %}
  </div>
  {% endif %}

  {% if resume.education %}
  <h2>Education</h2>
  {% for edu in resume.education %}
  <div class="job">
    <div class="edu-row">
      <div>
        <div class="edu-school">{{ edu.institution }}</div>
        <div class="edu-degree">{{ edu.degree }}{% if edu.gpa %} · GPA: {{ edu.gpa }}{% endif %}</div>
      </div>
      <div class="job-date">{% if edu.start_year %}{{ edu.start_year }}{% endif %}{% if edu.end_year %} — {{ edu.end_year }}{% endif %}</div>
    </div>
  </div>
  {% endfor %}
  {% endif %}
</body>
</html>"""


def get_inline_template() -> str:
    return MODERN_TEMPLATE