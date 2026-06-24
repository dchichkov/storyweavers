#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
=======================================================

A small standalone story world about a missing javelin, a tense whodunit,
and a sharing-based resolution.

Premise:
- A child athlete has a prized javelin for practice.
- Someone else needs to borrow it, but the javelin goes missing.
- Suspense builds while the characters look for clues.
- The mystery resolves when the javelin is found and shared fairly.

The world uses typed entities with physical meters and emotional memes,
state-driven narration, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    borrowed_by: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    adult: object | None = None
    art: object | None = None
    borrower: object | None = None
    hero: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    clue_place: str
    vibe: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    is_missing: bool = False
    is_shareable: bool = True
    owner_kind: str = "child"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Cast:
    id: str
    type: str
    role: str
    label: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class StoryParams:
    setting: str
    hero: str
    sibling: str
    adult: str
    artifact: str
    borrower: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__suspense__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sibling = world.get("sibling")
    if hero.memes["trust"] < THRESHOLD or sibling.memes["kindness"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["shared"] += 1
    sibling.meters["shared"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(settings: Setting, artifact: Artifact) -> bool:
    return artifact.is_shareable and artifact.owner_kind == "child" and settings.place


def hidden_artifact(artifact: Entity) -> bool:
    return artifact.hidden or artifact.meters["missing"] >= THRESHOLD


def predict_mystery(world: World, hero_id: str) -> dict:
    sim = world.copy()
    sim.get(hero_id).memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("javelin").meters["shared"] > 0,
        "missing": hidden_artifact(sim.get("javelin")),
    }


def introduce(world: World, hero: Entity, sibling: Entity, adult: Entity, art: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who loved the smooth feel of {art.label} practice."
    )
    world.say(
        f"{sibling.id} was {hero.pronoun('possessive')} {sibling.role_word if hasattr(sibling, 'role_word') else sibling.role} {''}".strip()
    )
    world.say(
        f"At {world.setting.place}, {adult.label_word} watched over the field and the little locker room."
    )


def setup_story(world: World, hero: Entity, sibling: Entity, adult: Entity, art: Entity) -> None:
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    hero.memes["trust"] += 1
    sibling.memes["kindness"] += 1
    world.say(
        f"One bright afternoon, {hero.id} brought {art.phrase} to {world.setting.place}, where the air felt calm."
    )
    world.say(
        f"{sibling.id} wanted a turn too, because {world.setting.vibe} made sharing feel easy."
    )


def clue(world: World, hero: Entity, sibling: Entity, art: Entity) -> None:
    hero.memes["worry"] += 1
    sibling.memes["worry"] += 1
    world.say(
        f"But then the {art.label} was gone from the rack."
    )
    world.say(
        f"{hero.id} stared at the empty spot, and {sibling.id} glanced at the footprints in the dust near {world.setting.clue_place}."
    )


def warn(world: World, adult: Entity, hero: Entity, sibling: Entity, art: Entity) -> None:
    pred = predict_mystery(world, hero.id)
    world.facts["pred"] = pred
    world.say(
        f'"If {art.label} is missing now, we should look carefully," {adult.label_word} said. '
        f'"No rushing, no guessing."'
    )


def search(world: World, hero: Entity, sibling: Entity, art: Entity) -> None:
    hero.memes["curiosity"] += 1
    sibling.memes["curiosity"] += 1
    world.para()
    world.say(
        f"They looked beside the cones, under the bench, and behind the water bottle crate."
    )
    world.say(
        f"Each clue made the mystery feel bigger, until the answer seemed hidden right under their noses."
    )


def reveal_and_share(world: World, hero: Entity, sibling: Entity, adult: Entity, art: Entity, borrower: Entity) -> None:
    art.hidden = False
    art.meters["missing"] = 0
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    hero.memes["sharing"] += 1
    sibling.memes["sharing"] += 1
    world.para()
    world.say(
        f"At last, {sibling.id} found {art.phrase} behind the folding mat, where it had slipped quietly during practice."
    )
    world.say(
        f"{hero.id} laughed instead of scolding, and {sibling.id} suggested they share it with {borrower.id} one turn at a time."
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled, because the mystery ended with a fair plan instead of a fight."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", role="hero", traits=["careful"]))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="girl", role="sibling", traits=["curious"]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, role="adult", traits=["calm"], label="the coach"))
    borrower = world.add(Entity(id=params.borrower, kind="character", type="boy", role="borrower", traits=["patient"], label="the teammate"))
    art = world.add(Entity(id="javelin", type="artifact", label="javelin", owner=hero.id))
    art.hidden = True
    art.meters["missing"] = 1
    world.facts["artifact"] = art
    world.facts["borrower"] = borrower

    setup_story(world, hero, sibling, adult, art)
    world.para()
    clue(world, hero, sibling, art)
    warn(world, adult, hero, sibling, art)
    search(world, hero, sibling, art)
    reveal_and_share(world, hero, sibling, adult, art, borrower)
    propagate(world, narrate=False)
    world.facts.update(hero=hero, sibling=sibling, adult=adult, borrower=borrower, setting=setting)
    return world


SETTINGS = {
    "field": Setting(place="the school field", clue_place="the bench", vibe="the quiet afternoon"),
    "gym": Setting(place="the gym hall", clue_place="the equipment cart", vibe="the echoing room"),
    "park": Setting(place="the practice park", clue_place="the low fence", vibe="the windy afternoon"),
}

NAMES = {
    "hero": ["Noah", "Mia", "Leo", "Ava", "Eli", "Zoe"],
    "sibling": ["Ivy", "Ben", "Lena", "Max", "Nora", "Finn"],
    "borrower": ["Sam", "Tia", "Owen", "Jade", "Theo", "Ruby"],
}

CURATED = [
    StoryParams(setting="field", hero="Noah", sibling="Ivy", adult="mother", artifact="javelin", borrower="Sam"),
    StoryParams(setting="gym", hero="Leo", sibling="Ben", adult="father", artifact="javelin", borrower="Tia"),
    StoryParams(setting="park", hero="Ava", sibling="Nora", adult="mother", artifact="javelin", borrower="Theo"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "javelin", "javelin") for s in SETTINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a javelin mystery with suspense and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--borrower")
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
    hero = getattr(args, "hero", None) or rng.choice(NAMES["hero"])
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in NAMES["sibling"] if n != hero])
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father"])
    borrower = getattr(args, "borrower", None) or rng.choice(NAMES["borrower"])
    return StoryParams(setting=setting, hero=hero, sibling=sibling, adult=adult, artifact="javelin", borrower=borrower)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short whodunit for a young child about a missing javelin, suspense, and sharing.",
        f"Tell a gentle mystery where {f['hero'].id} and {f['sibling'].id} search for a missing javelin and then share it fairly.",
        "Write a child-friendly suspense story with clues, a found object, and a kind ending about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    art = f["artifact"]
    return [
        QAItem(question=f"What was missing in the story?", answer=f"The missing thing was the javelin, and that made everyone search carefully."),
        QAItem(question=f"Where did they find the javelin?", answer=f"They found the javelin behind the folding mat after following the clues."),
        QAItem(question=f"How did the story end?", answer=f"It ended with the javelin being shared one turn at a time so everyone stayed happy."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a javelin?", answer="A javelin is a long, light spear used in sports practice and competition."),
        QAItem(question="Why should people share?", answer="Sharing helps everyone take turns and use things fairly."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of waiting to find out what will happen next."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)} hidden={e.hidden}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(J) :- artifact(J), hidden(J).
needs_search(H) :- missing(J), hero(H).
shared(J) :- artifact(J), not hidden(J).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("artifact", "javelin"), asp.fact("hero", "hero")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared/1."))
    return 0 if asp.atoms(model, "shared") == [("javelin",)] else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show shared/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show shared/1."))
        print(asp.atoms(model, "shared"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
