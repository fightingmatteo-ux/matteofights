import json
import os
import tempfile
import pytest
from catalog import Catalog, AssetEntry


def make_catalog(entries=None):
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(entries or [], tmp)
    tmp.close()
    return tmp.name


def test_load_empty_catalog():
    path = make_catalog([])
    cat = Catalog(path)
    assert cat.all() == []


def test_add_entry():
    path = make_catalog([])
    cat = Catalog(path)
    entry = AssetEntry(
        id="clip_001",
        file="ai-assets/arrivals/test.mp4",
        source="ai",
        shot_type="arrival",
        style_preset="gym",
        mood="cinematic",
        likeness=True,
        tags=["gym", "entrance"],
        duration_sec=5.0,
        prompt="dark moody gym entrance",
        generated_at="2026-06-07",
    )
    cat.add(entry)
    assert len(cat.all()) == 1
    assert cat.all()[0]["id"] == "clip_001"


def test_query_by_shot_type():
    path = make_catalog([
        {"id": "a", "shot_type": "arrival", "tags": [], "source": "ai",
         "file": "x.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
        {"id": "b", "shot_type": "outdoor", "tags": [], "source": "ai",
         "file": "y.mp4", "style_preset": "outdoor", "mood": "sunny",
         "likeness": False, "duration_sec": 4.0, "prompt": "", "generated_at": ""},
    ])
    cat = Catalog(path)
    arrivals = cat.query(shot_type="arrival")
    assert len(arrivals) == 1
    assert arrivals[0]["id"] == "a"


def test_query_by_tags():
    path = make_catalog([
        {"id": "a", "shot_type": "arrival", "tags": ["gym", "red-wraps"], "source": "ai",
         "file": "x.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
        {"id": "b", "shot_type": "arrival", "tags": ["gym"], "source": "ai",
         "file": "y.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
    ])
    cat = Catalog(path)
    results = cat.query(tags=["red-wraps"])
    assert len(results) == 1
    assert results[0]["id"] == "a"


def test_persist_to_disk():
    path = make_catalog([])
    cat = Catalog(path)
    entry = AssetEntry(
        id="clip_002", file="ai-assets/training/test.mp4", source="ai",
        shot_type="training", style_preset="gym", mood="intense",
        likeness=True, tags=["training"], duration_sec=6.0,
        prompt="boxing training", generated_at="2026-06-07",
    )
    cat.add(entry)
    cat2 = Catalog(path)
    assert len(cat2.all()) == 1
