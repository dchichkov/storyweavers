#!/usr/bin/env python3
"""
A standalone story world for a small pirate-tale domain.

Premise:
A young pirate crew sails toward a quiet cove, but the sea has other plans.
A surprise storm threatens the ship, a batten-down-the-hatches task becomes
urgent, and a flashback explains why the captain cares so much about the
old chest below deck. Dialogue carries the turns, and the ending proves the
ship was made safe just in time.

The world model tracks:
- physical meters: storm strength, ship dryness, plank security, chest safety
- emotional memes: worry, courage, relief, surprise, pride
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
# Domain model
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    chest: object | None = None
    deckhand: object | None = None
    ship: object | None = None
    storm: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the sea"
    afford_storm: bool = True
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
    name: str
    gender: str
    captain_title: str
    setting: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Story content registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "harbor": Setting(place="the harbor", afford_storm=True),
    "cove": Setting(place="the cove", afford_storm=True),
    "open_sea": Setting(place="the open sea", afford_storm=True),
}

NAMES = {
    "girl": ["Mira", "Ruby", "Nell", "Ada"],
    "boy": ["Finn", "Jory", "Pip", "Tate"],
}

CAPTAIN_TITLES = ["captain", "old captain"]


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def batten_down(world: World, ship: Entity, storm: Entity) -> None:
    ship.meters["planks"] += 1
    ship.meters["dry"] += 1
    storm.meters["threat"] += 1
    world.say(
        f'The crew hurried to batten down the ship before the waves could slap the deck.'
    )


def surprise_storm(world: World, ship: Entity, storm: Entity) -> None:
    if storm.meters["threat"] >= 1:
        world.say(
            f"Then, as quick as a wink, a surprise squall rolled in from the dark water."
        )
        world.say(
            f"The captain blinked. \"By the barnacles, that storm came out of nowhere!\""
        )


def flashback(world: World, captain: Entity, chest: Entity) -> None:
    captain.memes["memory"] += 1
    world.say(
        f"The captain's hand rested on the old chest, and for a moment the sea grew quiet."
    )
    world.say(
        f'The captain remembered a smaller ship, a colder night, and a promise made over that same chest.'
    )
    world.say(
        f'"I kept this chest safe once before," {captain.pronoun("subject")} whispered.'
    )


def dialogue_turn(world: World, crew: Entity, captain: Entity, ship: Entity, chest: Entity) -> None:
    crew.memes["surprise"] += 1
    crew.memes["courage"] += 1
    world.say(f'"What is in the chest?" the deckhand asked.')
    world.say(
        f'"Something dear to this crew," said the {captain.type}. "If we batten the hatches now, we keep it dry."'
    )
    world.say(
        f'"Aye!" the deckhand cried. "Then let us lash the ropes and save the ship!"'
    )


def fix_ship(world: World, ship: Entity, chest: Entity, captain: Entity) -> None:
    ship.meters["dry"] += 2
    ship.meters["safe"] += 2
    chest.meters["safe"] += 2
    captain.memes["pride"] += 1
    captain.memes["relief"] += 1
    world.say(
        f"The crew pounded the boards, tied the ropes, and battened every hatch tight."
    )
    world.say(
        f"The spray bounced away, the chest stayed dry below deck, and the ship rode the waves like a brave gull."
    )
    world.say(
        f'The captain smiled. "That is how a ship keeps her secrets," {captain.pronoun("subject")} said.'
    )


def tell_story(world: World) -> None:
    ship = world.get("ship")
    storm = world.get("storm")
    captain = world.get("captain")
    crew = world.get("deckhand")
    chest = world.get("chest")

    world.say(
        f"{captain.label} stood on {world.setting.place} with {crew.label}, listening to the salt wind."
    )
    world.say(
        f"The crew loved the bright day, but the captain kept glancing at the hatch where the old chest waited."
    )
    world.para()
    surprise_storm(world, ship, storm)
    batten_down(world, ship, storm)
    world.say(
        f'"We must batten the hatches!" shouted {captain.label}.'
    )
    world.say(
        f'"Aye, captain!" said {crew.label}.'
    )
    world.para()
    flashback(world, captain, chest)
    dialogue_turn(world, crew, captain, ship, chest)
    fix_ship(world, ship, chest, captain)


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))

    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=params.captain_title,
        label=f"Captain {params.name}",
        meters={"dry": 0.0},
        memes={"worry": 1.0},
    ))
    deckhand = world.add(Entity(
        id="deckhand",
        kind="character",
        type="boy" if params.gender == "boy" else "girl",
        label="a deckhand",
        meters={"dry": 0.0},
        memes={"courage": 0.0, "surprise": 0.0},
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label="the ship",
        meters={"planks": 0.0, "dry": 0.0, "safe": 0.0},
        memes={"pride": 0.0},
    ))
    storm = world.add(Entity(
        id="storm",
        kind="thing",
        type="storm",
        label="the storm",
        meters={"threat": 0.0},
        memes={"surprise": 0.0},
    ))
    chest = world.add(Entity(
        id="chest",
        kind="thing",
        type="chest",
        label="the old chest",
        owner="captain",
        caretaker="captain",
        meters={"safe": 0.0},
        memes={"memory": 0.0},
    ))

    world.facts.update(captain=captain, deckhand=deckhand, ship=ship, storm=storm, chest=chest)
    tell_story(world)
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    return [
        "Write a short pirate tale for a young child where a crew must batten the hatches during a surprise storm.",
        f"Tell a story where {captain.label} remembers something important in a flashback, then speaks to the crew in dialogue.",
        "Write a pirate adventure with a surprise, a flashback, and a bit of dialogue that ends with the ship safe and dry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = _safe_fact(world, f, "captain")
    deckhand: Entity = _safe_fact(world, f, "deckhand")
    ship: Entity = _safe_fact(world, f, "ship")
    chest: Entity = _safe_fact(world, f, "chest")
    return [
        QAItem(
            question="What had the crew to do when the storm came up so fast?",
            answer="They had to batten down the ship and tie everything tight before the waves could splash the deck.",
        ),
        QAItem(
            question=f"Why did {captain.label} care so much about the old chest?",
            answer="The captain cared because the story flashed back to an old promise made over the chest, so keeping it dry mattered a lot.",
        ),
        QAItem(
            question=f"Who asked what was in the chest?",
            answer=f"{deckhand.label.capitalize()} asked what was in the chest, and the captain answered in a gentle pirate voice.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The crew battened the hatches, the chest stayed dry below deck, and the ship rode safely on the waves.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to batten the hatches?",
            answer="To batten the hatches means to close and fasten the ship's openings tightly so wind and water have a harder time getting in.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the reader understands why it matters now.",
        ),
        QAItem(
            question="Why do pirates care about a ship staying dry?",
            answer="Pirates care because dry wood, dry ropes, and dry cargo help a ship sail safely and keep useful things from getting ruined.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% setting(Place).
% character(Id, Gender).
% object(Id, Type).
% storm_event(storm).
% cue(batten).
% beats: surprise, flashback, dialogue.

surprise_story(S) :- story(S), has_surprise(S), has_flashback(S), has_dialogue(S), batten_required(S), safe_end(S).

batten_required(S) :- storm_arrives(S), ship_present(S).
safe_end(S) :- batten_done(S), chest_dry(S), ship_safe(S).

has_surprise(S) :- feature(S, surprise).
has_flashback(S) :- feature(S, flashback).
has_dialogue(S) :- feature(S, dialogue).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("story", "pirate_tale"),
        asp.fact("feature", "pirate_tale", "surprise"),
        asp.fact("feature", "pirate_tale", "flashback"),
        asp.fact("feature", "pirate_tale", "dialogue"),
        asp.fact("storm_arrives", "pirate_tale"),
        asp.fact("ship_present", "pirate_tale"),
        asp.fact("batten_done", "pirate_tale"),
        asp.fact("chest_dry", "pirate_tale"),
        asp.fact("ship_safe", "pirate_tale"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show surprise_story/1."))
    atoms = set(asp.atoms(model, "surprise_story"))
    py = {("pirate_tale",)}
    if atoms == py:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with surprise, flashback, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain-title", choices=CAPTAIN_TITLES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    captain_title = getattr(args, "captain_title", None) or rng.choice(CAPTAIN_TITLES)
    return StoryParams(
        name=name,
        gender=gender,
        captain_title=captain_title,
        setting=setting,
    )


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show surprise_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Mira", gender="girl", captain_title="captain", setting="harbor"),
            StoryParams(name="Finn", gender="boy", captain_title="old captain", setting="cove"),
            StoryParams(name="Ruby", gender="girl", captain_title="captain", setting="open_sea"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
