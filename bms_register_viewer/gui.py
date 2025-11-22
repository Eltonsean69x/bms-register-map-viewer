"""
Tkinter GUI entry point for the BMS / SCADA Register Map Viewer.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .model import RegisterMap, RegisterEntry, ValidationIssue
from .export import generate_markdown, generate_html, save_text


class RegisterMapViewerApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("BMS / SCADA Register Map Viewer")
        self.geometry("1000x600")  # reasonable default size

        # Data
        self._register_map: RegisterMap | None = None
        self._current_entries: list[RegisterEntry] = []

        # UI
        self._create_menu()
        self._create_main_widgets()
        self._create_status_bar()

    # --- UI setup methods ---

    def _create_menu(self) -> None:
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open...", command=self._on_file_open)
        file_menu.add_command(label="Export documentation...", command=self._on_export_docs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label="Validate register map", command=self._on_validate)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self._on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _create_main_widgets(self) -> None:
        root_container = ttk.Frame(self)
        root_container.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Filter bar at top ---
        filter_frame = ttk.Frame(root_container)
        filter_frame.pack(fill="x", side="top", pady=(0, 8))

        ttk.Label(filter_frame, text="Filter:").pack(side="left")

        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=40)
        filter_entry.pack(side="left", padx=(4, 4))
        filter_entry.bind("<Return>", self._on_filter_apply)

        filter_button = ttk.Button(filter_frame, text="Apply", command=self._on_filter_apply)
        filter_button.pack(side="left")

        clear_button = ttk.Button(filter_frame, text="Clear", command=self._on_filter_clear)
        clear_button.pack(side="left", padx=(4, 0))

        # --- Table area ---
        table_frame = ttk.Frame(root_container)
        table_frame.pack(fill="both", expand=True)

        columns = ("address", "function", "name", "unit", "scaling", "data_type", "notes")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        # Define headings and column widths
        self.tree.heading("address", text="Address")
        self.tree.heading("function", text="Function")
        self.tree.heading("name", text="Name / Description")
        self.tree.heading("unit", text="Unit")
        self.tree.heading("scaling", text="Scaling")
        self.tree.heading("data_type", text="Data Type")
        self.tree.heading("notes", text="Notes")

        self.tree.column("address", width=80, anchor="e")
        self.tree.column("function", width=70, anchor="center")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("unit", width=80, anchor="center")
        self.tree.column("scaling", width=80, anchor="center")
        self.tree.column("data_type", width=100, anchor="center")
        self.tree.column("notes", width=250, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Initially show a placeholder row
        self._set_placeholder_message("No register map loaded. Use File → Open... to load a CSV file.")

    def _create_status_bar(self) -> None:
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken",
        )
        status_label.pack(fill="x")

    # --- Command handlers ---

    def _on_file_open(self) -> None:
        """File → Open... menu handler."""
        file_path = filedialog.askopenfilename(
            title="Open register map CSV",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return  # user cancelled

        try:
            reg_map = RegisterMap.from_csv(file_path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                title="Error loading file",
                message=f"Failed to load file:\n{exc}",
            )
            self._set_status("Failed to load file.")
            return

        self._register_map = reg_map
        self._current_entries = reg_map.entries
        self._populate_table(self._current_entries)

        count = len(reg_map.entries)
        self._set_status(f"Loaded {count} registers from {reg_map.source_path.name}")
        self._update_title_with_filename(reg_map.source_path.name)

    def _on_export_docs(self) -> None:
        """File → Export documentation... handler."""
        if not self._register_map:
            messagebox.showinfo(
                title="Export documentation",
                message="No register map loaded. Please open a CSV file first.",
            )
            return

        # Suggest a default filename based on the CSV
        src_name = self._register_map.source_path.name if self._register_map.source_path else "register_map.csv"
        default_stem = Path(src_name).stem

        output_path = filedialog.asksaveasfilename(
            title="Export documentation",
            defaultextension=".md",
            initialfile=f"{default_stem}_doc.md",
            filetypes=[
                ("Markdown files", "*.md"),
                ("HTML files", "*.html;*.htm"),
                ("All files", "*.*"),
            ],
        )
        if not output_path:
            return  # user cancelled

        out_path = Path(output_path)
        ext = out_path.suffix.lower()

        device_name = default_stem  # simple heuristic; you can change later

        metadata = {
            "title": f"Register Map - {device_name}",
            "device_name": device_name,
            "summary": "Automatically generated documentation for the register map.",
            "source_file": src_name,
        }

        try:
            if ext in {".html", ".htm"}:
                text = generate_html(self._register_map, metadata)
            else:
                text = generate_markdown(self._register_map, metadata)

            save_text(out_path, text)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                title="Export documentation",
                message=f"Failed to export documentation:\n{exc}",
            )
            self._set_status("Failed to export documentation.")
            return

        messagebox.showinfo(
            title="Export documentation",
            message=f"Documentation exported to:\n{out_path}",
        )
        self._set_status(f"Exported documentation to {out_path.name}")

    def _on_validate(self) -> None:
        """Tools → Validate register map handler."""
        if not self._register_map:
            messagebox.showinfo(
                title="Validate register map",
                message="No register map loaded. Please open a CSV file first.",
            )
            return

        issues = self._register_map.validate(check_gaps=True)
        if not issues:
            messagebox.showinfo(
                title="Validate register map",
                message="Validation passed: no issues found.",
            )
            self._set_status("Validation: no issues found.")
            return

        num_errors = sum(1 for i in issues if i.severity == "error")
        num_warnings = sum(1 for i in issues if i.severity == "warning")

        lines = [
            f"Validation found {len(issues)} issues:",
            f"- {num_errors} errors",
            f"- {num_warnings} warnings",
            "",
        ]
        for issue in issues[:50]:
            loc = []
            if issue.address is not None:
                loc.append(f"addr={issue.address}")
            if issue.row_index is not None:
                loc.append(f"row={issue.row_index}")
            loc_str = (" [" + ", ".join(loc) + "]") if loc else ""
            lines.append(f"- [{issue.severity.upper()}]{loc_str} {issue.message}")

        if len(issues) > 50:
            lines.append("")
            lines.append(f"...and {len(issues) - 50} more.")

        text = "\n".join(lines)

        if num_errors > 0:
            messagebox.showwarning(title="Validate register map", message=text)
            self._set_status(f"Validation: {num_errors} errors, {num_warnings} warnings.")
        else:
            messagebox.showinfo(title="Validate register map", message=text)
            self._set_status(f"Validation: {num_errors} errors, {num_warnings} warnings.")

    def _on_about(self) -> None:
        """Help → About dialog."""
        message = (
            "BMS / SCADA Register Map Viewer\n"
            "\n"
            "A tool to view, validate, and document Modbus/BACnet register maps.\n"
            "\n"
            "Author: Your Name\n"
            "License: MIT"
        )
        messagebox.showinfo(title="About", message=message)

    def _on_filter_apply(self, event=None) -> None:  # type: ignore[override]
        """Apply text filter to the table."""
        if not self._register_map:
            return
        text = self.filter_var.get()
        filtered = self._register_map.filter_text(text)
        self._current_entries = filtered
        self._populate_table(filtered)
        self._set_status(f"Filter '{text}' → {len(filtered)} registers shown.")

    def _on_filter_clear(self) -> None:
        """Clear filter and show all entries."""
        if not self._register_map:
            self.filter_var.set("")
            return
        self.filter_var.set("")
        self._current_entries = list(self._register_map.entries)
        self._populate_table(self._current_entries)
        self._set_status(f"Filter cleared → {len(self._current_entries)} registers shown.")

    # --- Helper methods ---

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _update_title_with_filename(self, filename: str) -> None:
        self.title(f"BMS / SCADA Register Map Viewer - {filename}")

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _set_placeholder_message(self, text: str) -> None:
        """Show a single row that spans columns with a placeholder text."""
        self._clear_table()
        self.tree.insert("", "end", values=(text, "", "", "", "", "", ""))

    def _populate_table(self, entries: list[RegisterEntry]) -> None:
        """Populate the Treeview with register entries."""
        self._clear_table()
        if not entries:
            self._set_placeholder_message("No entries to display.")
            return

        for e in entries:
            self.tree.insert(
                "",
                "end",
                values=(
                    e.address,
                    e.function,
                    e.name,
                    e.unit,
                    e.scaling,
                    e.data_type,
                    e.notes,
                ),
            )


def main() -> None:
    app = RegisterMapViewerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
