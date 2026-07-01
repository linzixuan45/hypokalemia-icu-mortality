#!/usr/bin/env python3
"""Fill Zenodo DOI placeholders across repository docs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: apply_zenodo_doi.py <version_doi> [concept_doi]", file=sys.stderr)
        return 1

    version_doi = sys.argv[1].removeprefix("https://doi.org/")
    if len(sys.argv) > 2:
        concept_doi = sys.argv[2].removeprefix("https://doi.org/")
    else:
        recid = version_doi.rsplit(".", 1)[-1]
        concept_doi = version_doi.replace(recid, str(int(recid) - 1)) if recid.isdigit() else version_doi
    version_url = f"https://doi.org/{version_doi}"

    code_availability = ROOT / "CODE_AVAILABILITY.md"
    text = code_availability.read_text()
    text = text.replace("[Zenodo concept DOI — fill after linking GitHub]", concept_doi)
    text = text.replace("[Zenodo version DOI — fill after release]", version_doi)
    text = text.replace("[Zenodo version DOI]", version_url)
    code_availability.write_text(text)

    readme = ROOT / "README.md"
    text = readme.read_text()
    text = text.replace("[fill after release]", version_url)
    readme.write_text(text)

    snippets = ROOT / "JOURNAL_COMPLIANCE_SNIPPETS.md"
    text = snippets.read_text()
    text = text.replace("[Zenodo version DOI]", version_url)
    text = text.replace("| Zenodo concept DOI | Pending | |", f"| Zenodo concept DOI | Done | {concept_doi} |")
    text = text.replace("| Zenodo version DOI | Pending | |", f"| Zenodo version DOI | Done | {version_doi} |")
    text = text.replace("| Release tag | Recommended | `v1.0.0` |", "| Release tag | Done | `v1.0.0` |")
    snippets.write_text(text)

    checklist = ROOT / "RELEASE_CHECKLIST.md"
    text = checklist.read_text()
    text = text.replace("- [ ] Repository public at https://github.com/linzixuan45/hypokalemia-icu-mortality", "- [x] Repository public at https://github.com/linzixuan45/hypokalemia-icu-mortality")
    text = text.replace("- [ ] Create release tag `v1.0.0` from the commit used for the manuscript", "- [x] Create release tag `v1.0.0` from the commit used for the manuscript")
    text = text.replace("- [ ] Enable GitHub integration in Zenodo", "- [x] Enable GitHub integration in Zenodo")
    text = text.replace("- [ ] Trigger archive from GitHub release `v1.0.0`", "- [x] Trigger archive from GitHub release `v1.0.0`")
    text = text.replace("- [ ] Record concept DOI and version DOI", "- [x] Record concept DOI and version DOI")
    checklist.write_text(text)

    print(f"Version DOI: {version_doi}")
    print(f"Concept DOI: {concept_doi}")
    print(f"Version URL: {version_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
