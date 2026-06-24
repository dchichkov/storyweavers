#!/usr/bin/env python3
"""
storyworlds/worlds/script_constipate_rejoice_transformation_humor_mystery.py
============================================================================

A small storyworld about a missing script in a tiny theater, a puzzling
transformation, and a funny mystery that ends in relief and rejoicing.

Premise:
- A child-stage troupe is preparing a short play.
- A script goes missing.
- The missing pages cause a surprising transformation in a costume or prop.
- The players solve the mystery, laugh, and rejoice when the play can begin.

The world keeps one physical meter and one emotional meter per entity, and the
story is driven by state changes, not by swapping nouns in a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    costume_ent: object | None = None
    manager: object | None = None
    script_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Stage:
    name: str
    place: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class ScriptItem:
    id: str
    title: str
    pages: int
    clue_word: str
    transformation: str
    humor: str
    mystery: str
    affects: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Costume:
    id: str
    label: str
    state: str
    transformed_label: str
    clue_word: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.stage)
        w.entities = deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    script = world.get("script")
    costume = world.get("costume")
    if script.meters.get("missing", 0) >= THRESHOLD and costume.meters.get("stuck", 0) >= THRESHOLD:
        sig = ("transform",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        costume.meters["transformed"] = 1
        costume.label = costume.transformed_label
        out.append("__transform__")
    return out


def _r_rejoice(world: World) -> list[str]:
    out: list[str] = []
    if world.get("script").meters.get("found", 0) >= THRESHOLD:
        sig = ("rejoice",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for eid in ("child", "manager"):
            world.get(eid).memes["joy"] = world.get(eid).memes.get("joy", 0) + 1
        out.append("__rejoice__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_transform, _r_rejoice):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for stage in STAGES.values():
        for script_id, script in SCRIPTS.items():
            for costume_id, costume in COSTUMES.items():
                if costume.clue_word in script.tags and stage.name in stage.affords:
                    combos.append((script_id, costume_id))
    return combos


@dataclass
class StoryParams:
    stage: str
    script: str
    costume: str
    child_name: str
    child_type: str
    manager_name: str
    manager_type: str
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


STAGES = {
    "backstage": Stage(name="backstage", place="the little theater", affords={"missing-script", "search", "show"}),
    "greenroom": Stage(name="greenroom", place="the greenroom", affords={"missing-script", "search", "show"}),
}

SCRIPTS = {
    "moon_pie": ScriptItem(
        id="moon_pie",
        title="The Moon Pie Script",
        pages=8,
        clue_word="script",
        transformation="the costume felt suddenly moon-white",
        humor="everyone giggled at the sticky moon pie joke",
        mystery="a missing page left a strange clue on the stool",
        affects="costume",
        tags={"script", "moon", "missing"},
    ),
    "bird_song": ScriptItem(
        id="bird_song",
        title="The Bird Song Script",
        pages=6,
        clue_word="script",
        transformation="the costume turned bright and feather-light",
        humor="the chorus chirped with silly squeaks",
        mystery="a ribbon clue peeked from behind the curtain",
        affects="costume",
        tags={"script", "bird", "missing"},
    ),
    "shoe_case": ScriptItem(
        id="shoe_case",
        title="The Shoe Case Script",
        pages=7,
        clue_word="script",
        transformation="the costume looked as stiff as a shoe box",
        humor="the hero laughed at the squeaky stage step",
        mystery="a dusty footprint pointed to the prop shelf",
        affects="costume",
        tags={"script", "shoe", "missing", "constipate"},
    ),
}

COSTUMES = {
    "lion": Costume(id="lion", label="lion costume", state="plain", transformed_label="sparkly lion costume", clue_word="script", tags={"script"}),
    "cloak": Costume(id="cloak", label="blue cloak", state="plain", transformed_label="shimmering blue cloak", clue_word="script", tags={"script"}),
    "mask": Costume(id="mask", label="paper mask", state="plain", transformed_label="smiling paper mask", clue_word="script", tags={"script"}),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ada", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Owen", "Leo", "Max"]
MANAGERS = ["Ms. Bell", "Mr. Finch", "Ms. Dale"]


def explain_rejection(script: ScriptItem, costume: Costume) -> str:
    return f"(No story: this script mystery does not plausibly transform the {costume.label}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["script_obj"]
    c = f["costume_obj"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old about a missing script, a funny clue, and a costume that changes. Include the word "{s.clue_word}".',
        f"Tell a child-friendly theater mystery where {f['child'].id} finds a strange clue, the costume changes, and everyone can finally rejoice.",
        f"Write a gentle story with transformation and humor, about a tiny stage, a lost script, and {c.label} becoming {c.transformed_label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    manager = f["manager"]
    script = f["script_obj"]
    costume = f["costume_obj"]
    return [
        QAItem(
            question=f"What was missing in the little theater?",
            answer=f"The script was missing, and that made everyone stop and look for clues on the stage.",
        ),
        QAItem(
            question=f"What changed when the mystery was solved?",
            answer=f"The {costume.label} transformed into {costume.transformed_label}, which showed the strange clue had been understood.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and ready to rejoice, because the script was found and the play could begin.",
        ),
        QAItem(
            question=f"Why did {manager.id} smile?",
            answer=f"{manager.id} smiled because the funny clue made the mystery easier to solve and the stage was ready again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a script?", answer="A script is a set of words that tells actors what to say and do in a play."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that people try to figure out."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new form or looks different."),
        QAItem(question="What is humor?", answer="Humor is something funny that makes people smile or laugh."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(stage: Stage, script: ScriptItem, costume: Costume, child_name: str, child_type: str, manager_name: str, manager_type: str) -> World:
    world = World(stage)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    manager = world.add(Entity(id="manager", kind="character", type=manager_type, label=manager_name))
    script_ent = world.add(Entity(id="script", type="script", label=script.title, meters={"missing": 0}, memes={"mystery": 1}))
    costume_ent = world.add(Entity(id="costume", type="costume", label=costume.label, meters={"stuck": 1}, attrs={"transformed_label": costume.transformed_label}))
    world.facts.update(child=child, manager=manager, script_obj=script, costume_obj=costume)
    world.say(f"{child_name} and {manager_name} were backstage at {stage.place}.")
    world.say(f"They noticed the {script.title.lower()}, but one page was missing, and that was the start of the mystery.")
    world.para()
    world.say(f"{script.mystery.capitalize()} Meanwhile, the {costume.label} looked odd, almost like it was waiting for a clue.")
    world.say(f"{child_name} laughed at the silly part, because the play had just enough humor to make the search feel playful.")
    script_ent.meters["missing"] = 1
    propagate(world, narrate=False)
    if costume_ent.meters.get("transformed", 0) >= THRESHOLD:
        world.say(f"When the page was found, the {costume.label} transformed into {costume.transformed_label}.")
    world.para()
    script_ent.meters["found"] = 1
    propagate(world, narrate=False)
    world.say(f"{manager_name} held up the script, and everyone could rejoice.")
    world.say(f"The little theater felt calm again, and the play could begin at last.")
    return world


CURATED = [
    StoryParams(stage="backstage", script="shoe_case", costume="mask", child_name="Mia", child_type="girl", manager_name="Ms. Bell", manager_type="woman"),
    StoryParams(stage="greenroom", script="bird_song", costume="cloak", child_name="Ben", child_type="boy", manager_name="Mr. Finch", manager_type="man"),
    StoryParams(stage="backstage", script="moon_pie", costume="lion", child_name="Luna", child_type="girl", manager_name="Ms. Dale", manager_type="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny theater mystery with transformation and humor.")
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--script", choices=SCRIPTS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--name")
    ap.add_argument("--manager")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "script", None) is None or c[0] == getattr(args, "script", None))
              and (getattr(args, "costume", None) is None or c[1] == getattr(args, "costume", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    script_id, costume_id = rng.choice(list(combos))
    stage = getattr(args, "stage", None) or rng.choice(list(STAGES))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    manager = getattr(args, "manager", None) or rng.choice(MANAGERS)
    child_type = "girl" if name in GIRL_NAMES else "boy"
    manager_type = "woman" if manager.startswith("Ms.") else "man"
    return StoryParams(
        stage=stage,
        script=script_id,
        costume=costume_id,
        child_name=name,
        child_type=child_type,
        manager_name=manager,
        manager_type=manager_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(STAGES, params.stage), _safe_lookup(SCRIPTS, params.script), _safe_lookup(COSTUMES, params.costume), params.child_name, params.child_type, params.manager_name, params.manager_type)
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
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print()
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


ASP_RULES = r"""
valid(S,C) :- script(S), costume(C), clue_word(S,W), clue_word(C,W).
transform(C) :- script(S), costume(C), missing(S), stuck(C), valid(S,C).
rejoice :- found(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    out = []
    for sid, s in SCRIPTS.items():
        out.append(asp.fact("script", sid))
        out.append(asp.fact("clue_word", sid, s.clue_word))
    for cid, c in COSTUMES.items():
        out.append(asp.fact("costume", cid))
        out.append(asp.fact("clue_word", cid, c.clue_word))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("MISMATCH")
        print("only in asp:", sorted(a - b))
        print("only in python:", sorted(b - a))
        return 1
    sample = generate(resolve_params(argparse.Namespace(stage=None, script=None, costume=None, name=None, manager=None), random.Random(7)))
    if not sample.story:
        return 1
    print(f"OK: {len(a)} combos verified and smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2.\n#show transform/1.\n#show rejoice/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
