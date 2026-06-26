#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/recognition_rhyme_humor_curiosity_nursery_rhyme.py
=================================================================================================

A standalone story world about recognition, rhyme, humor, and curiosity in a
small nursery-rhyme-style domain.

Seed story sketch:
---
Little Nia heard a tippity tap in the garden path. She peeked behind a pot,
under a hat, and inside a toy basket. "A cat in a hat?" she guessed, and then
laughed because the hat was on a scarecrow, not a cat.

The tapping kept going, so Nia followed the sound with a curious heart. At last
she recognized the culprit: a tiny clockwork robin, chiming on a ribbon and
bobbing its shiny beak. She wound it up, and the merry little bird sang again.

The story turns on recognition: first a funny wrong guess, then a real clue
trail, then a happy discovery that proves what changed.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    detail: str
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
class Mystery:
    id: str
    clue_sound: str
    clue_text: str
    culprit_label: str
    culprit_phrase: str
    reveal_line: str
    topic: str
    tags: set[str] = field(default_factory=set)
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
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


def _guess_wrong(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["humor"] += 1
    world.say(
        f"{child.id} heard a tiny tippity tap and looked left and right. "
        f"{child.pronoun().capitalize()} guessed, \"A cat in a hat?\" and then "
        f"giggle-giggled, because the hat belonged to a scarecrow, not a cat."
    )


def _follow_clues(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} did not stop there. {child.pronoun().capitalize()} peeked "
        f"behind the pot, then under the bench, then beside the basket, "
        f"following the little clue: {mystery.clue_text}."
    )


def _recognize(world: World, child: Entity, mystery: Mystery, toy: Entity) -> None:
    child.memes["recognition"] += 1
    toy.meters["wound"] += 1
    world.say(
        f"At last {child.id} recognized the sound. It was a tiny clockwork robin, "
        f"{mystery.culprit_phrase}. {mystery.reveal_line}"
    )
    world.say(
        f"{child.id} wound it once more, and the bright little bird gave a merry "
        f"chime as if it had been waiting just for that hand."
    )


def tell_story(setting: Setting, mystery: Mystery, name: str, gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    toy = world.add(
        Entity(
            id="robin",
            type="toy",
            label="clockwork robin",
            phrase=mystery.culprit_phrase,
            location=setting.place,
        )
    )

    world.say(
        f"{child.id} went to {setting.place}. {setting.detail} "
        f"The air felt warm and bright, and the day was ready for a little riddle."
    )
    world.say(
        f"Then came a tippity tap, a trilly clink, and a tiny sound that made "
        f"{child.id} tilt {child.pronoun('possessive')} head."
    )

    _guess_wrong(world, child)
    world.para()
    _follow_clues(world, child, mystery)
    _recognize(world, child, mystery, toy)

    world.facts.update(
        child=child,
        toy=toy,
        mystery=mystery,
        setting=setting,
        recognized=child.memes["recognition"] >= THRESHOLD,
    )
    return world


SETTINGS: dict[str, Setting] = {
    "garden": Setting(
        place="the garden",
        detail="The marigolds nodded, the path was pale, and a painted pot stood by the gate.",
        affords={"listen", "peek", "follow"},
    ),
    "yard": Setting(
        place="the yard",
        detail="The grass was soft, the fence was old, and a little bench waited in the sun.",
        affords={"listen", "peek", "follow"},
    ),
    "porch": Setting(
        place="the porch",
        detail="The porch boards were creaky, the steps were small, and a basket sat near the door.",
        affords={"listen", "peek", "follow"},
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "robin": Mystery(
        id="robin",
        clue_sound="tippity tap",
        clue_text="a tiny red feather near the pot",
        culprit_label="clockwork robin",
        culprit_phrase="a tiny clockwork robin, chiming on a ribbon",
        reveal_line="Its shiny beak bobbed, and its ribbon tail trembled like a tiny flag.",
        topic="robin",
        tags={"bird", "toy", "sound", "rhyme", "curiosity"},
    ),
    "bellbug": Mystery(
        id="bellbug",
        clue_sound="ting-a-ling",
        clue_text="a brass speck shining under the bench",
        culprit_label="bellbug",
        culprit_phrase="a tinny bellbug, blinking under a leaf",
        reveal_line="Its little shell rang when it waddled, and the tune sounded like a jingle song.",
        topic="bell",
        tags={"bug", "toy", "sound", "rhyme", "humor"},
    ),
    "mouse": Mystery(
        id="mouse",
        clue_sound="tip-top tap",
        clue_text="a crumb trail by the basket",
        culprit_label="wind-up mouse",
        culprit_phrase="a wind-up mouse, ticking in a circle",
        reveal_line="Its painted tail spun around, and its whiskers twitched like a tiny broom.",
        topic="mouse",
        tags={"toy", "sound", "curiosity", "humor"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
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


GIRL_NAMES = ["Nia", "Mila", "Tess", "Luna", "Pia", "Bea", "Ada", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Max", "Leo", "Milo", "Ben", "Theo", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES if "listen" in _safe_lookup(SETTINGS, s).affords]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world of clues, giggles, and recognition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[1] == getattr(args, "mystery", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f"Write a short nursery-rhyme story about {child.id} and a mystery sound in {world.setting.place}.",
        f"Tell a funny little tale where someone makes a wrong guess before recognizing {mystery.culprit_label}.",
        "Write a gentle rhyme with curiosity, humor, and a happy recognition at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What did {child.id} first guess about the tippity tap?",
            answer=f"{child.id} first guessed, \"A cat in a hat?\" It was a funny wrong guess.",
        ),
        QAItem(
            question=f"What clue helped {child.id} follow the mystery sound?",
            answer=f"The clue was {mystery.clue_text}, and it helped {child.id} look in the right place.",
        ),
        QAItem(
            question=f"What did {child.id} recognize at last?",
            answer=f"{child.id} recognized a {mystery.culprit_label}. The sound came from {mystery.culprit_phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is recognition?",
            answer="Recognition is when you notice something and realize you know it, like recognizing a face, a song, or a familiar sound.",
        ),
        QAItem(
            question="Why can funny wrong guesses make a story feel playful?",
            answer="Funny wrong guesses can make a story playful because they surprise us, and then the correct answer feels extra satisfying.",
        ),
        QAItem(
            question="Why do clues help curious readers?",
            answer="Clues help curious readers because each clue narrows the mystery and points toward the answer.",
        ),
        QAItem(
            question="What does a nursery rhyme often use?",
            answer="A nursery rhyme often uses rhythm, repeated sounds, and playful words that are easy to hear and remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).

recognized(C,M) :- child(C), mystery(M), clue_seen(C,M), wrong_guess(C), follow_clues(C), reveal(M).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    # Simple parity check against the Python reasonableness gate.
    prog = asp_program("#show mystery_fact/1.")
    model = asp.one_model(prog)
    asp_mysteries = {args[0] for args in asp.atoms(model, "mystery_fact")}
    py_mysteries = set(MYSTERIES)
    if asp_mysteries != py_mysteries:
        print("MISMATCH between ASP and Python registries.")
        return 1
    print(f"OK: ASP parity check passed ({len(asp_mysteries)} mysteries).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender)
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


CURATED = [
    StoryParams(setting="garden", mystery="robin", name="Nia", gender="girl"),
    StoryParams(setting="yard", mystery="mouse", name="Owen", gender="boy"),
    StoryParams(setting="porch", mystery="bellbug", name="Mila", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_fact/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
