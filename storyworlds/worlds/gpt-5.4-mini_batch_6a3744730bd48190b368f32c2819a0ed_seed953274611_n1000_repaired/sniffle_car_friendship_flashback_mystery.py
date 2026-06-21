#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sniffle_car_friendship_flashback_mystery.py
===========================================================================

A small storyworld about a child, a car, a friendship clue, and a flashback
that helps solve a gentle mystery.

Premise:
- Two friends hear a sniffle from inside a parked car.
- The mystery turns on a remembered flashback: where the missing thing was left.
- The resolution is a careful, child-facing discovery that proves what changed.

The world keeps the contract shape used by the repo:
- typed entities with physical meters and emotional memes
- a reasonableness gate
- a Python/ASP twin
- generated story + prompts + grounded Q&A
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    name1: str
    gender1: str
    name2: str
    gender2: str
    parent: str
    car: str
    clue: str
    missing: str
    flashback_kind: str
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


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    found_in: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Flashback:
    id: str
    trigger: str
    memory_line: str
    recovery_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_sniffle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sniffle"] < THRESHOLD:
            continue
        sig = ("sniffle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for friend in list(world.entities.values()):
            if friend.role == "friend":
                friend.memes["worry"] += 1
        out.append("__sniffle__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("seen_flashback") and not world.facts.get("clue_found"):
        world.facts["clue_found"] = True
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("sniffle", _r_sniffle), Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "parking_lot": Setting(id="parking_lot", place="the parking lot", detail="A blue car waited beside a row of quiet trees."),
    "driveway": Setting(id="driveway", place="the driveway", detail="A small car sat in the driveway, shining after a light rain."),
    "garage": Setting(id="garage", place="the garage", detail="The garage was dim, and the old car looked like it was hiding a secret."),
}

CLUES = {
    "car_key": Clue(id="car_key", label="car key", phrase="a little car key", where="under the seat", tags={"car", "key"}),
    "red_ball": Clue(id="red_ball", label="red ball", phrase="a red ball", where="in the back seat", tags={"toy", "car"}),
    "paper_map": Clue(id="paper_map", label="paper map", phrase="a folded paper map", where="in the glove box", tags={"map", "car"}),
}

MISSING = {
    "toy": MissingThing(id="toy", label="toy dinosaur", phrase="a small toy dinosaur", found_in="under the car seat", tags={"toy"}),
    "scarf": MissingThing(id="scarf", label="striped scarf", phrase="a striped scarf", found_in="on the dashboard", tags={"cloth"}),
    "note": MissingThing(id="note", label="note", phrase="a folded note", found_in="in the glove box", tags={"paper"}),
}

FLASHBACKS = {
    "trip": Flashback(
        id="trip",
        trigger="the car smelled like rain and old seats",
        memory_line="Then came a flashback: yesterday, the friends had piled into the car after a long trip.",
        recovery_line="They remembered the toy had slid down during the ride.",
        tags={"memory", "car"},
    ),
    "picnic": Flashback(
        id="picnic",
        trigger="the blanket in the back seat looked just like the one from the park",
        memory_line="Then came a flashback: they had packed the car for a picnic and laughed all the way there.",
        recovery_line="They remembered the scarf had been tucked near the picnic basket.",
        tags={"memory", "friendship"},
    ),
    "rain": Flashback(
        id="rain",
        trigger="the wet pavement shining under the car lights",
        memory_line="Then came a flashback: they had hurried into the car during a rainy dash home.",
        recovery_line="They remembered the paper map had fallen into the glove box.",
        tags={"memory", "mystery"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for mid, miss in MISSING.items():
                if "car" in clue.tags and "car" in miss.tags:
                    combos.append((sid, cid, mid))
    return combos


def story_is_reasonable(params: StoryParams) -> bool:
    return params.clue in CLUES and params.missing in MISSING and params.car in SETTINGS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship flashback mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--car", choices=SETTINGS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    if args.clue and args.missing and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.clue and args.missing and args.missing not in MISSING:
        raise StoryError("Unknown missing thing.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, missing = rng.choice(sorted(combos))
    flashback = args.flashback or rng.choice(sorted(FLASHBACKS))
    parent = args.parent or rng.choice(["mother", "father"])
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    n1 = args.name1 or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    n2_pool = [n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != n1]
    n2 = args.name2 or rng.choice(n2_pool)
    return StoryParams(
        name1=n1, gender1=g1, name2=n2, gender2=g2, parent=parent,
        car=setting, clue=clue, missing=missing, flashback_kind=flashback
    )


def tell(params: StoryParams) -> World:
    if not story_is_reasonable(params):
        raise StoryError("Invalid story params.")
    world = World()
    a = world.add(Entity(id=params.name1, kind="character", type=params.gender1, role="friend", traits=["curious"]))
    b = world.add(Entity(id=params.name2, kind="character", type=params.gender2, role="friend", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    setting = SETTINGS[params.car]
    clue = CLUES[params.clue]
    missing = MISSING[params.missing]
    fb = FLASHBACKS[params.flashback_kind]
    car = world.add(Entity(id="car", kind="thing", type="car", label="the car", tags={"car"}))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, attrs={"where": clue.where}))
    missing_ent = world.add(Entity(id="missing", kind="thing", type="missing", label=missing.label))
    world.facts.update(setting=setting, clue=clue, missing=missing, flashback=fb, parent=parent, car=car)

    world.say(f"{a.id} and {b.id} were friends who liked solving little mysteries together.")
    world.say(f"One afternoon, they walked to {setting.place}. {setting.detail}")
    world.say(f"Then they heard a soft sniffle from inside the car.")
    a.memes["curiosity"] += 1
    b.memes["worry"] += 1

    world.para()
    world.say(f"{b.id} leaned closer. \"Did you hear that sniffle?\" {b.pronoun()} asked.")
    world.say(f"{a.id} nodded. \"Maybe something is hidden in there,\" {a.pronoun()} said.")
    world.say(f"The clue was nearby, but not obvious: {clue.phrase} was {clue.where}.")
    world.facts["seen_flashback"] = True
    propagate(world)

    world.para()
    world.say(f"Then came a flashback: {fb.memory_line}")
    world.say(fb.recovery_line)
    world.say(f"{a.id} and {b.id} looked at one another and smiled, because friendship made the memory feel brighter.")

    world.para()
    if params.missing == "toy":
        world.say(f"{b.id} reached down and found {missing.phrase} {missing.found_in}.")
    elif params.missing == "scarf":
        world.say(f"{a.id} peered into the car and spotted {missing.phrase} {missing.found_in}.")
    else:
        world.say(f"The missing thing was {missing.phrase}, tucked neatly {missing.found_in}.")
    world.say(f"They carried it back to the parent, and the little mystery was solved.")

    world.para()
    world.say(f"{parent.label_word.capitalize()} smiled and thanked the two friends for being careful and kind.")
    world.say(f"The sniffle was only the car's loose vent cover tapping softly, and now the car felt quiet again.")
    world.say(f"{a.id} and {b.id} left together, their friendship feeling even stronger than before.")

    world.facts.update(found=missing.label, solved=True, sniffle=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "sniffle" and "car", and shows friendship helping solve a clue.',
        f"Tell a short story where {f['setting'].place} hides a small mystery, two friends hear a sniffle, and a flashback helps them remember what to do.",
        f"Write a gentle flashback mystery about friends, a car, and something missing that turns out to be easy to find.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = world.get(f["car"].id) if isinstance(f["car"], Entity) else None
    friend1 = next(e for e in world.entities.values() if e.role == "friend" and e.id == world.facts.get("found", "")[:0])
    # Simpler lookup by stored params-like state:
    names = [e.id for e in world.entities.values() if e.role == "friend"]
    x, y = names[0], names[1]
    setting: Setting = f["setting"]
    flashback: Flashback = f["flashback"]
    missing: MissingThing = f["missing"]
    clue: Clue = f["clue"]
    qa = [
        ("Who are the story's main helpers?",
         f"They are {x} and {y}, two friends who worked together to solve the mystery."),
        ("What did they hear?",
         f"They heard a sniffle from inside the car, which made them look more carefully."),
        ("What helped them remember the answer?",
         f"A flashback helped them. It brought back an earlier moment and pointed them toward the missing thing."),
        ("Where was the story set?",
         f"It happened at {setting.place}. The quiet place made the little mystery feel important."),
        ("What was missing?",
         f"{missing.phrase} was missing, and the friends found it again after the flashback."),
        ("How did friendship matter?",
         f"They listened to each other and looked together, so the clue made sense faster. Friendship turned the mystery into teamwork."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a sniffle?",
         "A sniffle is a small wet sound someone makes when they are crying a little or have a runny nose."),
        ("What is a car?",
         "A car is a vehicle that people ride in to travel on roads."),
        ("What is a flashback?",
         "A flashback is a memory in a story that jumps back to something that happened earlier."),
        ("What does friendship mean?",
         "Friendship means people care about each other, help each other, and like spending time together."),
        ("What is a mystery?",
         "A mystery is something puzzling that you need to think about and solve."),
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def explain_rejection() -> str:
    return "(No story: the chosen clues do not make a car mystery fit this world.)"


CURATED = [
    StoryParams(
        name1="Lily", gender1="girl", name2="Ben", gender2="boy", parent="mother",
        car="parking_lot", clue="car_key", missing="toy", flashback_kind="trip",
    ),
    StoryParams(
        name1="Mia", gender1="girl", name2="Noah", gender2="boy", parent="father",
        car="driveway", clue="paper_map", missing="note", flashback_kind="rain",
    ),
    StoryParams(
        name1="Zoe", gender1="girl", name2="Finn", gender2="boy", parent="mother",
        car="garage", clue="red_ball", missing="scarf", flashback_kind="picnic",
    ),
]


ASP_RULES = r"""
friendship(A,B) :- friend(A), friend(B), A != B.
mystery(C) :- clue(C), missing(M), car_scene.
sniffle_heard :- sniffle.
flashback_helped :- flashback.
solved :- sniffle_heard, flashback_helped, friendship(_, _).
valid_story(S, C, M) :- setting(S), clue(C), missing(M), car_tag(C), car_tag(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("car_scene", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("car_tag", cid) if t == "car" else asp.fact("tag", cid, t))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("car_tag", mid) if t == "car" else asp.fact("tag", mid, t))
    lines.append(asp.fact("sniffle"))
    lines.append(asp.fact("flashback"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python gate.")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_story_prompt() -> str:
    return 'Write a story that includes the words "sniffle" and "car" and uses friendship plus flashback in a mystery style.'


def resolve_params_from_seed(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(
        setting=None, clue=None, missing=None, flashback=None, car=None, parent=None,
        name1=None, gender1=None, name2=None, gender2=None
    ), rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, clue, missing = rng.choice(sorted(combos))
    flashback = args.flashback or rng.choice(sorted(FLASHBACKS))
    parent = args.parent or rng.choice(["mother", "father"])
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    n1 = args.name1 or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    pool2 = [n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != n1]
    n2 = args.name2 or rng.choice(pool2)
    return StoryParams(name1=n1, gender1=g1, name2=n2, gender2=g2, parent=parent, car=setting, clue=clue, missing=missing, flashback_kind=flashback)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
