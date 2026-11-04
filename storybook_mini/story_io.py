"""A declarative JSON interface to the content author / prose-generator boundary."""
from dataclasses import asdict, fields
import json
from pathlib import Path
from .model import Entity, Fact, Proposition, Story


def construct(cls, data):
    if not isinstance(data, dict):
        raise ValueError(f"{cls.__name__} must be an object")
    unknown = set(data) - {f.name for f in fields(cls)}
    if unknown:
        raise ValueError(f"Unknown {cls.__name__} fields: {sorted(unknown)}")
    try:
        return cls(**data)
    except TypeError as error:
        raise ValueError(f"Invalid {cls.__name__}: {error}") from error


def story_from_dict(data):
    if not isinstance(data, dict) or set(data) != {"id", "title", "entities", "facts"}:
        raise ValueError("Story JSON needs id, title, entities and facts")
    entities = tuple(construct(Entity, e) for e in data["entities"])
    facts = []
    for item in data["facts"]:
        item = dict(item)
        for key in ("goal", "speech"):
            if item.get(key) is not None:
                item[key] = construct(Proposition, item[key])
        for key in ("requires", "effects", "meme_deltas"):
            if key in item:
                item[key] = tuple(tuple(row) for row in item[key])
        facts.append(construct(Fact, item))
    return Story(data["id"], data["title"], entities, tuple(facts))


def load_story(path):
    return story_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def save_story(path, story):
    Path(path).write_text(json.dumps(asdict(story), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
