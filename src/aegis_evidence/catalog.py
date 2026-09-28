from __future__ import annotations

from pathlib import Path

import yaml

from .digest import digest_obj
from .models import Catalog


def load_catalog(path: Path) -> tuple[Catalog, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    catalog = Catalog.model_validate(raw)
    digest = digest_obj(catalog.model_dump())
    return catalog, digest


def load_system(path: Path):
    from .models import SystemRecord

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SystemRecord.model_validate(raw)
