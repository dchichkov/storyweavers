#!/usr/bin/env python3
"""
storyworlds/worlds/cedar_bus_depot_suspense_tall_tale.py
========================================================

A standalone story world for a tiny Tall Tale at a bus depot: cedar crates,
a suspenseful wait, and a safe resolution that changes the world state.

Premise:
- A child and a grown-up are waiting at a bus depot.
- A cedar crate or cedar sign seems to hide something important.
- Suspense rises as the bus is late or a needed ticket/bundle goes missing.
- The turn reveals a harmless cause.
- The ending proves what changed in the world: the missing thing is found,
  the wait ends, and the depot feels bright again.

The prose is state-driven: meters and memes shape the narration, and the
story should read as a complete, authored miniature tale.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    bundle: object | None = None
    child: object | None = None
    clock: object | None = None
    crate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str = "the bus depot"
    afford: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    label: str
    phrase: str
    hide: str
    cause: str
    reveal: str
    suspense: str
    keyword: str = "cedar"
    tags: set[str] = field(default_factory=set)
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
class Resolution:
    id: str
    method: str
    clue: str
    text: str
    qa_text: str
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _rule_wait(world: World) -> list[str]:
    out = []
    if world.get("clock").meters.get("lateness", 0) >= THRESHOLD and ("tension",) not in world.fired:
        world.fired.add(("tension",))
        world.get("child").memes["worry"] = world.get("child").memes.get("worry", 0) + 1
        world.get("adult").memes["worry"] = world.get("adult").memes.get("worry", 0) + 1
        out.append("__tension__")
    return out


def _rule_reveal(world: World) -> list[str]:
    out = []
    if world.get("crate").meters.get("shaken", 0) >= THRESHOLD and ("reveal",) not in world.fired:
        world.fired.add(("reveal",))
        world.get("crate").meters["opened"] = 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [
    _rule_wait,
    _rule_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_delay(world: World) -> bool:
    sim = world.copy()
    sim.get("clock").meters["lateness"] += 1
    propagate(sim, narrate=False)
    return sim.get("clock").meters.get("lateness", 0) >= THRESHOLD


def nudge_crate(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.get("crate").meters["shaken"] = world.get("crate").meters.get("shaken", 0) + 1
    world.say(f"{child.id} tapped the cedar crate, and it answered with a hollow little thump.")


def worry(world: World, adult: Entity, child: Entity, mystery: Mystery) -> None:
    if predict_delay(world):
        adult.memes["worry"] = adult.memes.get("worry", 0) + 1
        world.say(f'"{child.id}, that cedar box sounds odd," {adult.pronoun()} said. "Let’s not rush it."')
    else:
        world.say(f"{adult.id} glanced at the depot clock, but the minute hand still seemed harmless.")


def listen(world: World, child: Entity) -> None:
    child.memes["listening"] = child.memes.get("listening", 0) + 1
    world.say(f"{child.id} held still, listening for the next clue in the depot hush.")


def reveal(world: World, mystery: Mystery, resolution: Resolution) -> None:
    world.say(f"The mystery was no monster at all. The cedar crate only hid {mystery.reveal}.")
    world.say(resolution.text)


def ending(world: World, child: Entity, adult: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    adult.memes["relief"] = adult.memes.get("relief", 0) + 1
    world.say(f"In the end, {child.id} and {adult.id} stood by the depot window, smiling at the bright road beyond.")


def tell(setting: Setting, mystery: Mystery, resolution: Resolution,
         child_name: str = "Milo", child_type: str = "boy",
         adult_type: str = "mother", adult_name: str = "Mama") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_name, role="adult"))
    crate = world.add(Entity(id="crate", type="thing", label="cedar crate", phrase="a cedar crate"))
    clock = world.add(Entity(id="clock", type="thing", label="depot clock"))
    bundle = world.add(Entity(id="bundle", type="thing", label=mystery.label, phrase=mystery.phrase, owner=child.id))
    world.add(Entity(id="bench", type="thing", label="wooden bench"))

    clock.meters["lateness"] = 1
    child.memes["hope"] = 1
    adult.memes["patience"] = 1

    world.say(f"At the bus depot, {child.label} and {adult.label} waited where the cedar smell hung in the air.")
    world.say(f"Near the bench sat {mystery.phrase}, and nobody could tell what it was hiding.")
    world.say(f"{child.label} loved a good mystery, but the depot felt extra still, the way a room does before a storm.")

    world.para()
    nudge_crate(world, child)
    worry(world, adult, child, mystery)
    listen(world, child)

    world.para()
    clock.meters["lateness"] += 1
    propagate(world, narrate=False)
    if world.get("clock").meters["lateness"] >= THRESHOLD:
        world.say(f"The bus was late, and that made the silence stretch long and thin.")
    reveal(world, mystery, resolution)

    world.para()
    bundle.meters["found"] = 1
    child.memes["relief"] = 1
    world.say(f"Under the cedar crate, {child.label} found the missing {bundle.label}.")
    world.say(f"It had slipped behind the bench, where no one had looked because everyone was listening too hard.")

    world.para()
    ending(world, child, adult)

    world.facts.update(
        child=child, adult=adult, mystery=mystery, resolution=resolution,
        crate=crate, clock=clock, bundle=bundle
    )
    return world


SETTINGS = {
    "bus_depot": Setting(place="the bus depot", afford={"wait", "search"}),
}

MYSTERIES = {
    "lost_bundle": Mystery(
        id="lost_bundle",
        label="paper bundle",
        phrase="a paper bundle tied with blue string",
        hide="behind the bench",
        cause="slipped while the child was waiting",
        reveal="the route slip and a stamped ticket",
        suspense="the bundle seemed to rustle on its own",
        tags={"cedar", "bus", "depot", "ticket"},
    ),
    "shiny_box": Mystery(
        id="shiny_box",
        label="tin box",
        phrase="a tin box with a bright latch",
        hide="under the schedule board",
        cause="a gust of wind nudged it there",
        reveal="a stack of bus tokens",
        suspense="the latch clicked softly in the hush",
        tags={"cedar", "bus", "depot", "tokens"},
    ),
}

RESOLUTIONS = {
    "find_ticket": Resolution(
        id="find_ticket",
        method="look behind the bench",
        clue="a tiny edge of paper",
        text="The grown-up pointed, and together they peeked behind the bench, where the missing ticket had been hiding all along.",
        qa_text="looked behind the bench and found the missing ticket",
        tags={"find", "ticket"},
    ),
    "open_box": Resolution(
        id="open_box",
        method="open the little latch",
        clue="a soft click",
        text="They eased the latch open, and the tin box gave up its secret: bus tokens gleaming like small moons.",
        qa_text="opened the box and found bus tokens",
        tags={"open", "tokens"},
    ),
}

CHILD_NAMES = ["Milo", "June", "Nia", "Theo", "Ada", "Ben", "Pia", "Ollie"]
ADULT_NAMES = ["Mama", "Papa", "Aunt Jo", "Uncle Ray"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    resolution: str
    child_name: str
    child_type: str
    adult_type: str
    adult_name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for r in RESOLUTIONS:
                combos.append((s, m, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale-style suspense story for a 3-to-5-year-old set at a bus depot, and include the word "cedar".',
        f"Tell a story where {f['child'].label} waits at the bus depot, a cedar crate seems mysterious, and a grown-up helps solve the puzzle.",
        f"Write a short, child-facing tale with suspense, a cedar object, and a safe ending at a bus depot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, mystery, res = f["child"], f["adult"], f["mystery"], f["resolution"]
    return [
        QAItem(
            question=f"Who is the story about at the bus depot?",
            answer=f"It is about {child.label} and {adult.label}, who are waiting at the bus depot and looking at the cedar mystery together.",
        ),
        QAItem(
            question="What made the depot feel suspenseful?",
            answer=f"The cedar crate and the late bus made the wait feel suspenseful, because everything was quiet and the clue seemed hard to read.",
        ),
        QAItem(
            question="What did the child find in the end?",
            answer=f"{child.label} found {world.facts['bundle'].label}, and the hidden thing turned out to be harmless.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=res.qa_text.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cedar?",
            answer="Cedar is a kind of tree wood that smells warm and sharp, and people use it for boxes, boards, and closets.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, wait, and get ready to travel again.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next when something seems mysterious or important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,M,R) :- setting(S), mystery(M), resolution(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for r in RESOLUTIONS:
        lines.append(asp.fact("resolution", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale suspense at a bus depot.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--adult-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "resolution", None) is None or c[2] == getattr(args, "resolution", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery, resolution = (list(rng.choice(combos)) + [None, None, None])[:3]
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    child_type = getattr(args, "child_type", None) or rng.choice(["boy", "girl"])
    adult_type = getattr(args, "adult_type", None) or rng.choice(["mother", "father"])
    adult_name = getattr(args, "adult", None) or rng.choice(ADULT_NAMES)
    return StoryParams(setting, mystery, resolution, child_name, child_type, adult_type, adult_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(RESOLUTIONS, params.resolution),
        params.child_name,
        params.child_type,
        params.adult_type,
        params.adult_name,
    )
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, m, r in asp_valid_combos():
            print(f"  {s:10} {m:12} {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(s, m, r, "Milo", "boy", "mother", "Mama")) for s, m, r in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
