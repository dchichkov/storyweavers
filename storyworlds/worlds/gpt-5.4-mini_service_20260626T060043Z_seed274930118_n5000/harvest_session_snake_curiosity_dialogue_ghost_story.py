#!/usr/bin/env python3
"""
A small storyworld about a harvest session, curiosity, and a snake in a ghostly
old field. The tale follows a child who wants to peek, hears a warning, and
learns a safe way to look at a spooky shape without making a bigger fright.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    basket: object | None = None
    child: object | None = None
    parent: object | None = None
    snake: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the old orchard"
    session: str = "the harvest session"
    has_corn: bool = True
    has_barn: bool = True
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard": Setting(place="the old orchard", session="the harvest session"),
    "barn": Setting(place="the candlelit barn", session="the harvest session"),
    "field": Setting(place="the quiet field", session="the harvest session"),
    "garden": Setting(place="the lantern garden", session="the harvest session"),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Iris", "Ada"],
    "boy": ["Owen", "Toby", "Eli", "Finn", "Asher"],
}
TRAITS = ["curious", "bright-eyed", "gentle", "bold", "quiet"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def ghostly_phrase(place: str) -> str:
    return {
        "the old orchard": "The wind moved through the apple trees like a soft whisper.",
        "the candlelit barn": "The barn glowed gold, but the corners stayed dark and watchful.",
        "the quiet field": "The corn bent and sighed as if someone were walking just out of sight.",
        "the lantern garden": "The lanterns trembled, and their light made the shadows look long.",
    }[place]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
    ))
    basket = world.add(Entity(
        id="basket",
        type="basket",
        label="a wicker basket",
        phrase="a wicker basket of harvested pears",
        owner=child.id,
    ))
    snake = world.add(Entity(
        id="snake",
        type="snake",
        label="snake",
        phrase="a pale snake that looked like a ribbon in moonlight",
        meters={"hiding": 1.0, "seen": 0.0},
        memes={"spook": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who loved quiet evenings at "
        f"{setting.session}."
    )
    world.say(
        f"{child.id} helped carry {basket.phrase} and kept asking what would happen next."
    )
    world.say(ghostly_phrase(setting.place))

    # Act 2: curiosity and fear
    world.para()
    child.memes["curiosity"] = 1.0
    world.say(
        f"When the helpers went on with the {setting.session}, {child.id} spotted a small trail near the fence."
    )
    world.say(
        f'"What made that mark?" {child.pronoun()} asked, because {child.pronoun("subject")} was too curious to stay still.'
    )
    child.memes["unease"] = 1.0
    if setting.has_barn:
        world.say(
            f"Then a thin shape slid through the grass, and the shape looked like a snake."
        )
    world.say(
        f"{parent.pronoun().capitalize()} stepped closer and whispered, "
        f'"Stay by me. We will look carefully."'
    )
    child.memes["fear"] = 1.0

    # Act 3: resolution
    world.para()
    snake.meters["seen"] = 1.0
    snake.memes["spook"] = 0.0
    world.say(
        f"{parent.pronoun().capitalize()} lifted a lantern, and the mystery became clear."
    )
    world.say(
        f"It was only {snake.phrase}, curled beside a warm stone and not trying to hurt anyone."
    )
    child.memes["curiosity"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["wonder"] = 1.0
    world.say(
        f"{child.id} smiled, listened to the crickets, and stayed near {parent.pronoun('object')} while the harvest session went on."
    )
    world.say(
        f"By the time the lantern light faded, the field felt less like a ghost story and more like a safe place to learn."
    )

    world.facts.update(
        child=child,
        parent=parent,
        basket=basket,
        snake=snake,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a gentle ghost-story for children that includes the words "harvest", "session", and "snake".',
        f"Tell a short story where {child.id} feels curious during a harvest session and learns what the snake really is.",
        f"Write a spooky-but-safe story set at {world.setting.place} with a child, a parent, and a lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, snake, setting = f["child"], f["parent"], f["snake"], f["setting"]
    return [
        QAItem(
            question=f"Where did {child.id} go during the harvest session?",
            answer=f"{child.id} went to {setting.place} during the harvest session with {parent.label}.",
        ),
        QAItem(
            question=f"Why did {child.id} ask about the track near the fence?",
            answer=f"{child.id} asked because {child.pronoun()} was curious and wanted to know what made the mark.",
        ),
        QAItem(
            question="Was the snake a monster?",
            answer=f"No. The snake was only a small snake in the grass, and it was not trying to hurt anyone.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} ended the story feeling calm, because the lantern showed the truth and the scary shape was not a ghost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harvest session?",
            answer="A harvest session is a time when people gather and work together to bring in crops or celebrate the harvest.",
        ),
        QAItem(
            question="Why do lanterns help in the dark?",
            answer="Lanterns help because they give out light, so people can see where they are going.",
        ),
        QAItem(
            question="What should you do if you see a snake?",
            answer="You should stay calm, keep a safe distance, and tell a grown-up.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(orchar d).
place(barn).
place(field).
place(garden).

setting_session(orchar d, harvest_session).
setting_session(barn, harvest_session).
setting_session(field, harvest_session).
setting_session(garden, harvest_session).

valid_story(P) :- place(P), setting_session(P, harvest_session).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting_session", pid, "harvest_session"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted((p,) for p in SETTINGS)
    if found == expected:
        print(f"OK: ASP matches Python registry ({len(found)} places).")
        return 0
    print("MISMATCH")
    print("ASP:", found)
    print("PY :", expected)
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghostly harvest storyworld with curiosity and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="orchard", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="barn", name="Owen", gender="boy", parent="father", trait="quiet"),
    StoryParams(place="field", name="Iris", gender="girl", parent="mother", trait="bright-eyed"),
    StoryParams(place="garden", name="Finn", gender="boy", parent="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        for item in items:
            print(item[0])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
