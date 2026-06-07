import json
import os
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Optional


@dataclass
class AssetEntry:
    file: str
    source: str          # "ai" or "real"
    shot_type: str       # "arrival" | "training" | "atmosphere" | "outdoor" | "lifestyle" | "hero"
    style_preset: str    # "gym" | "outdoor" | "lifestyle"
    mood: str
    likeness: bool
    tags: List[str]
    duration_sec: float
    prompt: Optional[str] = None
    generated_at: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]


class Catalog:
    def __init__(self, path: str):
        self.path = path
        self._entries: List[dict] = self._load()

    def _load(self) -> List[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return json.load(f)

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._entries, f, indent=2)

    def all(self) -> List[dict]:
        return list(self._entries)

    def add(self, entry: AssetEntry):
        self._entries.append(asdict(entry))
        self._save()

    def query(
        self,
        shot_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        likeness: Optional[bool] = None,
        source: Optional[str] = None,
    ) -> List[dict]:
        results = self._entries
        if shot_type:
            results = [e for e in results if e["shot_type"] == shot_type]
        if tags:
            results = [e for e in results if all(t in e["tags"] for t in tags)]
        if likeness is not None:
            results = [e for e in results if e["likeness"] == likeness]
        if source:
            results = [e for e in results if e["source"] == source]
        return results
