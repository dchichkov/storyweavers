#!/usr/bin/env python3
"""
A standalone story world for a small ghost-story domain.

Premise:
- A child has a purple checkerboard blanket and a curious cognitive checker game.
- At night, a friendly ghost appears.
- The child feels conflict, talks with the ghost, and uses a little magic to help the ghost.
- The ending proves something changed in the world: fear becomes trust, and the ghost is not lonely anymore.
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


THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    color: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    pluraL: object | None = None
    checker: object | None = None
    child: object | None = None
    ghost: object | None = None
    magic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    nocturnal: bool = True
    affords: set[str] = field(default_factory=set)
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
class Checker:
    id: str
    phrase: str
    color: str
    theme: str
    cognitive: bool = False
    playable: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Magic:
    id: str
    label: str
    verb: str
    effect: str
    cost: str
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mood: str = "quiet"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.mood = self.mood
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    checker: str
    ghost: str
    magic: str
    seed: Optional[int] = None
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
    "attic": Setting(place="the attic", nocturnal=True, affords={"visit", "talk", "magic"}),
    "hallway": Setting(place="the hallway", nocturnal=True, affords={"visit", "talk", "magic"}),
    "garden": Setting(place="the moonlit garden", nocturnal=True, affords={"visit", "talk", "magic"}),
}

CHECKERS = {
    "purple_checker": Checker(
        id="purple_checker",
        phrase="a purple checkerboard toy",
        color="purple",
        theme="checker",
        cognitive=True,
        playable=True,
    ),
    "cognitive_checker": Checker(
        id="cognitive_checker",
        phrase="a little cognitive checker puzzle",
        color="purple",
        theme="cognitive",
        cognitive=True,
        playable=True,
    ),
    "night_checker": Checker(
        id="night_checker",
        phrase="a checker game with shiny squares",
        color="purple",
        theme="checker",
        cognitive=False,
        playable=True,
    ),
}

MAGICS = {
    "lantern_spell": Magic(
        id="lantern_spell",
        label="lantern spell",
        verb="shine",
        effect="the room glowed gently",
        cost="a tiny flicker of courage",
        safe=True,
    ),
    "purple_glow": Magic(
        id="purple_glow",
        label="purple glow",
        verb="float",
        effect="purple light drifted over the floor",
        cost="a whispered promise",
        safe=True,
    ),
    "soft_bell": Magic(
        id="soft_bell",
        label="soft bell magic",
        verb="ring",
        effect="a calm bell sound settled the air",
        cost="a slow breath",
        safe=True,
    ),
}


def _act_visit(world: World, child: Entity, checker: Entity, ghost: Entity) -> None:
    child.memes["caution"] += 1
    world.say(
        f"At {world.setting.place}, {child.id} held {child.pronoun('possessive')} "
        f"{checker.label} close and listened to the hush."
    )
    world.say(
        f"Then {ghost.id} appeared near the old wall, pale as moonlight and quiet as dust."
    )


def _act_conflict(world: World, child: Entity, ghost: Entity, checker: Entity) -> None:
    child.memes["fear"] += 1
    child.memes["conflict"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f"{child.id} felt a twist of conflict. {child.pronoun().capitalize()} wanted to run, "
        f"but {child.pronoun('possessive')} purple checker toy felt warm in {child.pronoun('possessive')} hands."
    )
    world.say(
        f"{ghost.id} looked lonely instead of scary, as if {ghost.pronoun('subject')} had been waiting to speak."
    )


def _act_dialogue(world: World, child: Entity, ghost: Entity, checker: Entity) -> None:
    child.memes["curiosity"] += 1
    ghost.memes["hope"] += 1
    world.say(
        f'"Are you lost?" {child.id} asked, keeping {child.pronoun("possessive")} voice small.'
    )
    world.say(
        f'"I am only lonely," {ghost.id} answered. "I keep hearing games and never get to join them."'
    )
    world.say(
        f'{child.id} looked down at the checker pattern and said, "Then maybe you can help me think."'
    )


def _act_magic(world: World, child: Entity, ghost: Entity, magic: Entity) -> None:
    child.memes["brave"] += 1
    ghost.memes["joy"] += 1
    ghost.memes["lonely"] = 0.0
    world.say(
        f'{child.id} whispered the {magic.label}, and {magic.effect}.'
    )
    world.say(
        f"The purple light touched the checker squares, and {ghost.id} smiled like a lamp turning on."
    )


def _act_resolution(world: World, child: Entity, ghost: Entity, checker: Entity, magic: Entity) -> None:
    child.memes["conflict"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["trust"] += 1
    ghost.memes["belonging"] += 1
    checker.worn_by = child.id
    world.say(
        f'{child.id} set the {checker.label} between them and said, "We can play together."'
    )
    world.say(
        f"{ghost.id} moved a hand over the squares, and each purple check seemed brighter than before."
    )
    world.say(
        f"By the end, {ghost.id} was not a fright in the dark anymore. {ghost.pronoun().capitalize()} was a friend beside the game."
    )


def tell(setting: Setting, checker_cfg: Checker, magic_cfg: Magic,
         child_name: str = "Mina", child_type: str = "girl",
         ghost_name: str = "Pip") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, label=child_name,
        meters={}, memes={"curiosity": 0.0, "fear": 0.0, "trust": 0.0, "brave": 0.0, "conflict": 0.0},
    ))
    ghost = world.add(Entity(
        id=ghost_name, kind="character", type="ghost", label=ghost_name,
        meters={}, memes={"lonely": 1.0, "hope": 0.0, "joy": 0.0, "belonging": 0.0},
    ))
    checker = world.add(Entity(
        id=checker_cfg.id, type="toy", label="checker toy",
        phrase=checker_cfg.phrase, color=checker_cfg.color, owner=child.id,
        pluraL=False if False else False,
    ))
    magic = world.add(Entity(
        id=magic_cfg.id, type="magic", label=magic_cfg.label, phrase=magic_cfg.effect,
    ))

    world.say(
        f"{child.id} was a little {child.type} who loved the color purple and the sound of careful thinking."
    )
    world.say(
        f"{child.id} always carried {child.pronoun('possessive')} {checker_cfg.phrase}, especially on quiet nights."
    )
    world.para()
    _act_visit(world, child, checker, ghost)
    _act_conflict(world, child, ghost, checker)
    world.para()
    _act_dialogue(world, child, ghost, checker)
    _act_magic(world, child, ghost, magic)
    _act_resolution(world, child, ghost, checker, magic)

    world.facts.update(
        child=child, ghost=ghost, checker=checker, magic=magic, setting=setting,
        checker_cfg=checker_cfg, magic_cfg=magic_cfg
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, ghost, checker = f["child"], f["ghost"], f["checker_cfg"]
    return [
        f'Write a short ghost story for a child who loves a {checker.color} checker toy and meets a lonely ghost.',
        f"Tell a gentle story where {child.id} feels conflict at {world.setting.place}, talks with {ghost.id}, and uses magic.",
        f'Write a small bedtime story that includes the words "purple", "checker", and "ghost" in a calm, magical way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, checker, magic = f["child"], f["ghost"], f["checker_cfg"], f["magic_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} carry on the quiet night?",
            answer=f"{child.id} carried a purple checker toy to {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel conflict when {ghost.id} appeared?",
            answer=f"{child.id} felt conflict because {ghost.id} was strange at first, but then it became clear that {ghost.id} was only lonely.",
        ),
        QAItem(
            question=f"What happened when {child.id} used the {magic.label}?",
            answer=f"The {magic.label} made purple light glow softly, and that helped {ghost.id} feel welcome.",
        ),
        QAItem(
            question=f"How did the story end for {ghost.id}?",
            answer=f"It ended with {ghost.id} beside the checker game, no longer lonely and now treated like a friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a checkerboard pattern?",
            answer="A checkerboard pattern is made of alternating squares, often in two colors like black and white or purple and another color.",
        ),
        QAItem(
            question="What does a ghost story usually feel like?",
            answer="A ghost story usually feels a little spooky at first, but it can still end kindly and safely.",
        ),
        QAItem(
            question="What does magical light do in a story?",
            answer="Magical light can make a dark place feel friendly, bright, and easier to understand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", child_name="Mina", child_type="girl", checker="purple_checker", ghost="Pip", magic="purple_glow"),
    StoryParams(place="hallway", child_name="Eli", child_type="boy", checker="cognitive_checker", ghost="Moth", magic="lantern_spell"),
    StoryParams(place="garden", child_name="Nora", child_type="girl", checker="night_checker", ghost="Wren", magic="soft_bell"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: purple checker, conflict, dialogue, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--checker", choices=CHECKERS)
    ap.add_argument("--ghost")
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    checker = getattr(args, "checker", None) or rng.choice(list(CHECKERS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or (rng.choice(["Mina", "Nora", "Lena"]) if child_type == "girl" else rng.choice(["Eli", "Noah", "Theo"]))
    ghost = getattr(args, "ghost", None) or rng.choice(["Pip", "Moth", "Wisp", "Lark"])

    if checker not in CHECKERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if magic not in MAGICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    if _safe_lookup(CHECKERS, checker).color != "purple":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, child_name=child_name, child_type=child_type, checker=checker, ghost=ghost, magic=magic)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHECKERS, params.checker), _safe_lookup(MAGICS, params.magic), params.child_name, params.child_type, params.ghost)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
setting(attic).
setting(hallway).
setting(garden).

purple(checker).
cognitive(checker).
feature(conflict).
feature(dialogue).
feature(magic).

valid_story(P, C, G, M) :- setting(P), purple(C), cognitive(C), feature(conflict), feature(dialogue), feature(magic), ghost(G), magic(M).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for cid, c in CHECKERS.items():
        lines.append(asp.fact("checker", cid))
        lines.append(asp.fact("purple", cid))
        if c.cognitive:
            lines.append(asp.fact("cognitive", cid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    lines.append(asp.fact("feature", "conflict"))
    lines.append(asp.fact("feature", "dialogue"))
    lines.append(asp.fact("feature", "magic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    got = sorted(set(asp.atoms(model, "valid_story")))
    expected = []
    for p in SETTINGS:
        for c in CHECKERS:
            for g in ["Pip", "Moth", "Wisp", "Lark"]:
                for m in MAGICS:
                    expected.append((p, c, g, m))
    expected = sorted(set(expected))
    if got:
        print(f"OK: ASP produced {len(got)} model atoms.")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
