"""
Documentation export (Markdown / HTML) for the BMS / SCADA Register Map Viewer.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional

from .model import RegisterMap, RegisterEntry


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_markdown(
    register_map: RegisterMap,
    metadata: Optional[Mapping[str, str]] = None,
) -> str:
    """Generate a Markdown document for the given register map."""
    metadata = dict(metadata or {})

    title = metadata.get("title", "Register Map")
    device_name = metadata.get("device_name", "")
    summary = metadata.get("summary", "")
    source_file = metadata.get("source_file", register_map.source_path.name if register_map.source_path else "")
    generated_at = metadata.get("generated_at", _now_iso())

    lines: list[str] = []

    # Title
    lines.append(f"# {title}")
    lines.append("")

    # Metadata block
    if device_name or source_file or generated_at:
        lines.append("**Metadata**")
        lines.append("")
        if device_name:
            lines.append(f"- Device: `{device_name}`")
        if source_file:
            lines.append(f"- Source file: `{source_file}`")
        lines.append(f"- Generated: `{generated_at}`")
        lines.append("")

    if summary:
        lines.append("**Summary**")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Table header
    lines.append("## Register Map")
    lines.append("")
    lines.append(
        "| Address | Function | Name / Description | Unit | Scaling | Data Type | Notes |"
    )
    lines.append(
        "|--------:|:--------:|--------------------|:----:|:-------:|:---------:|:------|"
    )

    # Table rows
    for e in register_map.entries:
        lines.append(_markdown_row_for_entry(e))

    lines.append("")  # trailing newline

    return "\n".join(lines)


def _markdown_row_for_entry(e: RegisterEntry) -> str:
    def esc(text: str) -> str:
        # Basic escaping to avoid breaking tables
        return text.replace("|", "\\|")

    return (
        f"| {esc(e.address)}"
        f" | {esc(e.function)}"
        f" | {esc(e.name)}"
        f" | {esc(e.unit)}"
        f" | {esc(e.scaling)}"
        f" | {esc(e.data_type)}"
        f" | {esc(e.notes)} |"
    )


def generate_html(
    register_map: RegisterMap,
    metadata: Optional[Mapping[str, str]] = None,
) -> str:
    """Generate a simple standalone HTML document for the register map."""
    metadata = dict(metadata or {})

    title = metadata.get("title", "Register Map")
    device_name = metadata.get("device_name", "")
    summary = metadata.get("summary", "")
    source_file = metadata.get("source_file", register_map.source_path.name if register_map.source_path else "")
    generated_at = metadata.get("generated_at", _now_iso())

    def esc(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    lines: list[str] = []

    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append('<meta charset="utf-8">')
    lines.append(f"<title>{esc(title)}</title>")
    lines.append(
        "<style>"
        "body { font-family: Arial, sans-serif; font-size: 14px; }"
        "table { border-collapse: collapse; width: 100%; }"
        "th, td { border: 1px solid #ccc; padding: 4px 6px; }"
        "th { background: #f0f0f0; text-align: left; }"
        "td.numeric { text-align: right; }"
        "</style>"
    )
    lines.append("</head>")
    lines.append("<body>")

    lines.append(f"<h1>{esc(title)}</h1>")

    # Metadata
    if device_name or source_file or generated_at:
        lines.append("<h2>Metadata</h2>")
        lines.append("<ul>")
        if device_name:
            lines.append(f"<li><strong>Device:</strong> <code>{esc(device_name)}</code></li>")
        if source_file:
            lines.append(f"<li><strong>Source file:</strong> <code>{esc(source_file)}</code></li>")
        lines.append(f"<li><strong>Generated:</strong> <code>{esc(generated_at)}</code></li>")
        lines.append("</ul>")

    if summary:
        lines.append("<h2>Summary</h2>")
        lines.append(f"<p>{esc(summary)}</p>")

    # Table
    lines.append("<h2>Register Map</h2>")
    lines.append("<table>")
    lines.append("<thead>")
    lines.append(
        "<tr>"
        "<th>Address</th>"
        "<th>Function</th>"
        "<th>Name / Description</th>"
        "<th>Unit</th>"
        "<th>Scaling</th>"
        "<th>Data Type</th>"
        "<th>Notes</th>"
        "</tr>"
    )
    lines.append("</thead>")
    lines.append("<tbody>")

    for e in register_map.entries:
        lines.append(
            "<tr>"
            f"<td class='numeric'>{esc(e.address)}</td>"
            f"<td class='numeric'>{esc(e.function)}</td>"
            f"<td>{esc(e.name)}</td>"
            f"<td>{esc(e.unit)}</td>"
            f"<td>{esc(e.scaling)}</td>"
            f"<td>{esc(e.data_type)}</td>"
            f"<td>{esc(e.notes)}</td>"
            "</tr>"
        )

    lines.append("</tbody>")
    lines.append("</table>")

    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines)


def save_text(path: str | Path, text: str) -> None:
    """Save text to a file with UTF-8 encoding."""
    p = Path(path)
    p.write_text(text, encoding="utf-8")
