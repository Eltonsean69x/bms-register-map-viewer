"""
Data model and CSV loading for the BMS / SCADA Register Map Viewer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import csv
import pathlib


@dataclass
class ValidationIssue:
    """Represents a validation problem found in the register map."""
    severity: str  # "error" or "warning"
    message: str
    address: Optional[str] = None
    row_index: Optional[int] = None


@dataclass
class RegisterEntry:
    """Represents a single register row from the register map."""

    address: str
    function: str
    name: str
    unit: str
    scaling: str
    data_type: str
    notes: str

    @property
    def address_int(self) -> Optional[int]:
        """Return the address as int if possible, otherwise None."""
        try:
            return int(self.address)
        except (TypeError, ValueError):
            return None


class RegisterMap:
    """Holds a list of register entries and provides helper methods."""

    def __init__(self, entries: List[RegisterEntry], source_path: Optional[pathlib.Path] = None) -> None:
        self.entries = entries
        self.source_path = source_path

    @classmethod
    def from_csv(cls, path: str) -> "RegisterMap":
        """
        Load a register map from a CSV file.

        Expected columns (case-insensitive):
        - Address
        - Function
        - Name or Description
        - Unit
        - Scaling
        - DataType or Data type
        - Notes (optional)
        """
        p = pathlib.Path(path)
        entries: List[RegisterEntry] = []

        with p.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Normalize fieldnames (case-insensitive)
            fieldnames = [fn.lower() for fn in (reader.fieldnames or [])]

            def get_value(row, *possible_names: str) -> str:
                for name in possible_names:
                    name_lower = name.lower()
                    if name_lower in fieldnames:
                        return (row.get(name) or row.get(name_lower) or "").strip()
                return ""

            for row in reader:
                entry = RegisterEntry(
                    address=get_value(row, "Address"),
                    function=get_value(row, "Function", "Func"),
                    name=get_value(row, "Name", "Description"),
                    unit=get_value(row, "Unit"),
                    scaling=get_value(row, "Scaling", "Scale"),
                    data_type=get_value(row, "DataType", "Data Type", "Type"),
                    notes=get_value(row, "Notes", "Comment"),
                )
                entries.append(entry)

        return cls(entries=entries, source_path=p)

    def filter_text(self, text: str) -> List[RegisterEntry]:
        """Return entries whose fields contain the given text (case-insensitive)."""
        text = text.strip().lower()
        if not text:
            return list(self.entries)

        filtered: List[RegisterEntry] = []
        for e in self.entries:
            haystack = " ".join(
                [
                    e.address,
                    e.function,
                    e.name,
                    e.unit,
                    e.scaling,
                    e.data_type,
                    e.notes,
                ]
            ).lower()
            if text in haystack:
                filtered.append(e)
        return filtered

    def validate(self, check_gaps: bool = False) -> List[ValidationIssue]:
        """Validate the register map and return a list of issues."""
        issues: List[ValidationIssue] = []

        # Basic per-row checks
        address_to_indices: dict[int, List[int]] = {}
        for idx, entry in enumerate(self.entries):
            # +2 to account for CSV header row (1) and 0-based index
            row_index = idx + 2

            # Required fields
            if not entry.address.strip():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message="Missing address.",
                        address=None,
                        row_index=row_index,
                    )
                )

            if not entry.function.strip():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message="Missing function code.",
                        address=entry.address or None,
                        row_index=row_index,
                    )
                )

            if not entry.name.strip():
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        message="Missing name/description.",
                        address=entry.address or None,
                        row_index=row_index,
                    )
                )

            if not entry.data_type.strip():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message="Missing data type.",
                        address=entry.address or None,
                        row_index=row_index,
                    )
                )

            # Address validity
            addr_int = entry.address_int
            if addr_int is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message="Invalid address (not an integer).",
                        address=entry.address or None,
                        row_index=row_index,
                    )
                )
            else:
                address_to_indices.setdefault(addr_int, []).append(row_index)

        # Duplicate addresses
        for addr_int, rows in address_to_indices.items():
            if len(rows) > 1:
                for r in rows:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            message=f"Duplicate address {addr_int}.",
                            address=str(addr_int),
                            row_index=r,
                        )
                    )

        # Optional: gaps in addresses (only uses valid addresses)
        if check_gaps and address_to_indices:
            sorted_addrs = sorted(address_to_indices.keys())
            for i in range(len(sorted_addrs) - 1):
                cur_addr = sorted_addrs[i]
                next_addr = sorted_addrs[i + 1]
                if next_addr - cur_addr > 1:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            message=f"Gap in addresses between {cur_addr} and {next_addr}.",
                            address=str(cur_addr),
                            row_index=None,
                        )
                    )

        return issues
