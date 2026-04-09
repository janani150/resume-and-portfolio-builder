"""PDF generation service using Jinja2 templates and WeasyPrint."""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def render_template_to_pdf(template_name: str, context: dict) -> bytes:
    """Render a Jinja2 template to PDF bytes using WeasyPrint.

    Note: WeasyPrint has system dependencies (libpango, libcairo). In environments
    where those are not available, this function will raise; in production ensure
    the runtime includes them (or run PDF generation in a worker with proper libs).
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    html = template.render(**context)
    pdf = HTML(string=html).write_pdf()
    return pdf
