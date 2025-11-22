\# BMS / SCADA Register Map Viewer



A small desktop tool for data center / BMS / SCADA / PME engineers to:



\- Load Modbus (and later BACnet) register maps from CSV (Excel export).

\- View and filter registers in a simple GUI.

\- Validate the register map (duplicates, gaps, missing fields, invalid addresses).

\- Auto-generate documentation in Markdown or HTML.



\## Features (v0.1)



\- 🚪 \*\*CSV import\*\*

&nbsp; - Supports typical columns like: `Address`, `Function`, `Name/Description`, `Unit`, `Scaling`, `DataType`, `Notes`.

&nbsp; - Case-insensitive column name matching (handles small variations).



\- 👓 \*\*GUI viewer (Tkinter)\*\*

&nbsp; - Table view using `ttk.Treeview`.

&nbsp; - Filter box to quickly search by any text (address, name, unit, etc.).

&nbsp; - Status bar with context messages.



\- ✅ \*\*Validation\*\*

&nbsp; - Invalid / non-numeric addresses.

&nbsp; - Duplicate addresses.

&nbsp; - Missing required fields (address, function, data type).

&nbsp; - Optional warnings for gaps between addresses.



\- 📄 \*\*Auto-documentation\*\*

&nbsp; - Export to \*\*Markdown\*\* (`.md`) or \*\*HTML\*\* (`.html`).

&nbsp; - Includes:

&nbsp;   - Title

&nbsp;   - Device name (based on file name)

&nbsp;   - Source CSV file name

&nbsp;   - Generation timestamp

&nbsp; - Register map rendered as a table.



\## Requirements



\- Python 3.10+ (tested with Python 3.13).

\- Standard library only (no external dependencies).



\## Installation



Clone the repository:



```bash

git clone git@github.com:your-user/bms-register-map-viewer.git

cd bms-register-map-viewer



