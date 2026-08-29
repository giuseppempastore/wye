"""Bounded, dependency-free XLSX container and worksheet reading."""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile

from app.scientific_ingestion.errors import ScientificParserError


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class BoundedXlsxReader:
    """Read selected worksheets after validating the whole archive envelope."""

    def __init__(self, body: bytes, *, provider: str, max_decompressed_bytes: int,
                 max_archive_entries: int = 200):
        self.provider = provider
        try:
            self.archive = zipfile.ZipFile(io.BytesIO(body))
        except (zipfile.BadZipFile, OSError) as exc:
            raise ScientificParserError(
                f"{provider} artifact is not a valid XLSX container"
            ) from exc
        infos = self.archive.infolist()
        if (len(infos) > max_archive_entries
                or sum(item.file_size for item in infos) > max_decompressed_bytes):
            raise ScientificParserError(f"{provider} XLSX exceeds decompression limits")
        if any(".." in item.filename.split("/")
               or item.filename.startswith(("/", "\\")) for item in infos):
            raise ScientificParserError(f"unsafe {provider} XLSX archive path")
        if "xl/workbook.xml" not in self.archive.namelist():
            raise ScientificParserError(f"{provider} artifact is not an XLSX workbook")
        try:
            self.shared_strings = self._shared_strings()
            self.sheet_paths = self._sheet_paths()
        except (KeyError, ET.ParseError, IndexError, ValueError) as exc:
            raise ScientificParserError(f"invalid {provider} XLSX workbook structure") from exc

    def close(self):
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def rows(self, sheet_name: str) -> list[list[str]]:
        try:
            content = self.archive.read(self.sheet_paths[sheet_name])
            return self._sheet_rows(content)
        except (KeyError, ET.ParseError, IndexError, ValueError) as exc:
            raise ScientificParserError(
                f"invalid or missing {self.provider} worksheet: {sheet_name}"
            ) from exc

    def records(self, sheet_name: str) -> list[dict[str, str]]:
        matrix = self.rows(sheet_name)
        if not matrix:
            raise ScientificParserError(f"{self.provider} worksheet has no header: {sheet_name}")
        headers = matrix[0]
        if not headers or len(headers) != len(set(headers)):
            raise ScientificParserError(
                f"{self.provider} worksheet has blank or duplicate headers: {sheet_name}"
            )
        return [
            {header: row[index] if index < len(row) else ""
             for index, header in enumerate(headers)}
            for row in matrix[1:]
            if any(value.strip() for value in row)
        ]

    def _shared_strings(self):
        try:
            root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        except KeyError:
            return []
        return [
            "".join(node.text or "" for node in item.iter(MAIN_NS + "t"))
            for item in root
        ]

    def _sheet_paths(self):
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(
            self.archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        paths = {}
        for sheet in workbook.iter(MAIN_NS + "sheet"):
            target = targets[sheet.attrib[REL_NS + "id"]]
            paths[sheet.attrib["name"]] = "xl/" + target.lstrip("/").removeprefix("xl/")
        return paths

    def _sheet_rows(self, content):
        root, rows = ET.fromstring(content), []
        for row in root.iter(MAIN_NS + "row"):
            values = {}
            for cell in row.findall(MAIN_NS + "c"):
                match = re.match(r"[A-Z]+", cell.attrib["r"])
                if match is None:
                    raise ValueError("invalid XLSX cell reference")
                column = 0
                for char in match.group():
                    column = column * 26 + ord(char) - 64
                node = cell.find(MAIN_NS + "v")
                value = "" if node is None else node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = self.shared_strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(
                        item.text or "" for item in cell.iter(MAIN_NS + "t")
                    )
                values[column - 1] = value
            rows.append([values.get(index, "")
                         for index in range(max(values, default=-1) + 1)])
        return rows
