#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/revise_tough_property_canal_path_conflict_humor.py
===================================================================================

A standalone storyworld for a tiny whodunit on a canal path.

Premise
-------
A child detective and a grown-up walk the canal path, trying to figure out who
kept moving a small property marker near the towpath gate. The case starts with
conflict, gets a little silly, and ends with a clear answer that changes the
world: the marker is revised, the confusion is solved, and everyone can use the
path again.

The story is built from simulated state, not from a frozen paragraph. It uses:
- typed entities with meters and memes,
- a simple forward-chaining causal engine,
- a reasonableness gate,
- a Python/ASP twin,
- three Q&A sets grounded in the simulated world.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/revise_tough_property_canal_path_conflict_humor.py
    python storyworlds/worlds/gpt-5.4-mini/revise_tough_property_canal_path_conflict_humor.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/revise_tough_property_canal_path_conflict_humor.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"moved": 0.0, "messy": 0.0, "found": 0.0, "fixed": 0.0}
        if not self.memes:
            self.memes = {"conflict": 0.0, "humor": 0.0, "curiosity": 0.0, "relief": 0.0}

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    setting: str = "canal path"
    culprit: str = "duck"
    witness: str = "Mina"
    witness_gender: str = "girl"
    parent: str = "mother"
    marker: str = "property sign"
    clue: str = "muddy track"
    tool: str = "notebook"
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
    path_sound: str
    water_sound: str
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


@dataclass
class Culprit:
    id: str
    label: str
    sound: str
    mischief: str
    clue: str
    harmless: bool = True
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


@dataclass
class Marker:
    id: str
    label: str
    phrase: str
    tough: str
    movable: bool = True
    property_word: str = "property"
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
class Fix:
    id: str
    label: str
    verb: str
    effect: str
    revise_word: str = "revise"
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("conflict", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["humor"] += 1
        out.append("__conflict__")
    return out


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    marker = world.entities.get("marker")
    if not culprit or not marker:
        return out
    if culprit.meters.get("moved", 0.0) < THRESHOLD:
        return out
    sig = ("mud",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    marker.meters["messy"] += 1
    out.append("A muddy track curled beside the marker.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("mud", _r_mud)]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, c in CULPRITS.items():
        for mid, m in MARKERS.items():
            if c.harmless and m.movable:
                combos.append((cid, mid))
    return combos


def reasonableness_gate(culprit: Culprit, marker: Marker) -> bool:
    return culprit.harmless and marker.movable


def predict(world: World, culprit: Culprit, marker: Marker) -> dict:
    sim = world.copy()
    sim.get("culprit").meters["moved"] += 1
    sim.get("witness").memes["conflict"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("witness").memes["conflict"],
        "messy": sim.get("marker").meters["messy"],
    }


def setup(world: World, setting: Setting, witness: Entity, parent: Entity, culprit: Culprit, marker: Marker) -> None:
    world.say(
        f"On the {setting.place}, {witness.id} and {parent.label_word} followed the {setting.path_sound} of the towpath."
    )
    world.say(
        f"Near the water, the little {marker.label} stood by the fence like it was guarding a secret."
    )
    witness.memes["curiosity"] += 1
    witness.memes["conflict"] += 1
    parent.memes["conflict"] += 1


def clue_scene(world: World, setting: Setting, culprit: Culprit, marker: Marker, clue: str) -> None:
    world.say(
        f"Then came a tiny {culprit.sound}, a soft {setting.water_sound}, and a {clue} by the {marker.label}."
    )
    world.say(
        f'"Someone moved it," {world.get("witness").id} whispered. "This is a tough case."'
    )


def accuse(world: World, witness: Entity, culprit: Culprit) -> None:
    witness.memes["conflict"] += 1
    world.say(
        f'"Was it {culprit.label}?" {witness.id} asked, squinting at the trail.'
    )
    world.say(
        f'The answer looked funny at first, because the clue had {culprit.clue} written all over it.'
    )


def revise_case(world: World, witness: Entity, fixer: Fix, marker: Marker, culprit: Culprit) -> None:
    witness.memes["relief"] += 1
    witness.memes["humor"] += 1
    world.say(
        f'{witness.id} opened {world.get("tool").label_word if "tool" in world.entities else "the notebook"} and decided to {fixer.revise_word} the note.'
    )
    world.say(
        f'Instead of blaming the wrong suspect, {witness.id} wrote the new answer: {culprit.label} only made a harmless mess.'
    )
    world.say(
        f'{fixer.label.capitalize()} {fixer.verb} the {marker.label} so the property line made sense again.'
    )
    marker.meters["fixed"] += 1


def reveal(world: World, culprit: Culprit, marker: Marker) -> None:
    world.say(
        f"It turned out the culprit was not sneaky after all; {culprit.label} had only left a silly trail."
    )
    world.say(
        f'{culprit.sound}! {marker.label} was still standing, just a little muddy and much less mysterious.'
    )


def end_image(world: World, setting: Setting, witness: Entity, parent: Entity, marker: Marker) -> None:
    witness.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"By the end, the {setting.place} was calm again, the clue was cleared up, and the property marker pointed the right way."
    )
    world.say(
        f"{witness.id} and {parent.label_word} walked on, laughing at the case that had seemed so tough an hour before."
    )


SETTINGS = {
    "canal_path": Setting(
        id="canal_path",
        place="canal path",
        detail="a narrow path beside the water",
        path_sound="clop-clop",
        water_sound="plip",
        tags={"canal", "path"},
    )
}

CULPRITS = {
    "duck": Culprit(
        id="duck",
        label="duck",
        sound="quack",
        mischief="left tracks",
        clue="muddy tracks",
        harmless=True,
        tags={"duck", "humor", "sound"},
    ),
    "goose": Culprit(
        id="goose",
        label="goose",
        sound="honk",
        mischief="stomped around",
        clue="squishy prints",
        harmless=True,
        tags={"goose", "humor", "sound"},
    ),
    "cat": Culprit(
        id="cat",
        label="cat",
        sound="mrrp",
        mischief="slipped by quietly",
        clue="tiny paw marks",
        harmless=True,
        tags={"cat", "humor", "sound"},
    ),
}

MARKERS = {
    "sign": Marker(
        id="sign",
        label="property sign",
        phrase="the property sign",
        tough="tough",
        movable=True,
        property_word="property",
        tags={"property"},
    ),
    "post": Marker(
        id="post",
        label="property post",
        phrase="the property post",
        tough="tough",
        movable=True,
        property_word="property",
        tags={"property"},
    ),
}

FIXES = {
    "revise": Fix(
        id="revise",
        label="the detective",
        verb="revise",
        effect="rewrote the note",
        revise_word="revise",
        tags={"revise"},
    )
}

KNOWLEDGE = {
    "canal": [("What is a canal?", "A canal is a man-made waterway where boats can travel."),],
    "path": [("What is a path?", "A path is a narrow strip of ground people can walk on.")],
    "property": [("What does property mean?", "Property is something that belongs to someone, like a sign, a house, or a yard.")],
    "tough": [("What does tough mean?", "Tough can mean strong and hard to break or move.")],
    "revise": [("What does revise mean?", "Revise means to change something and make it better or more correct.")],
    "humor": [("What is humor?", "Humor is something funny that makes people smile or laugh.")],
    "sound": [("What are sound effects?", "Sound effects are little words like plip or quack that help you hear the scene in your head.")],
}
KNOWLEDGE_ORDER = ["canal", "path", "property", "tough", "revise", "humor", "sound"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld on a canal path.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--tool", choices=["notebook"])
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
    if args.culprit and args.marker:
        if not reasonableness_gate(CULPRITS[args.culprit], MARKERS[args.marker]):
            raise StoryError("No story: that suspect and marker do not make a sensible canal-path mystery.")
    choices = [c for c in valid_combos()
               if (args.culprit is None or c[0] == args.culprit)
               and (args.marker is None or c[1] == args.marker)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    culprit, marker = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Pia", "Owen", "Tess", "June"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=args.setting or "canal_path",
        culprit=culprit,
        witness=name,
        witness_gender=gender,
        parent=parent,
        marker=marker,
        clue=CULPRITS[culprit].clue,
        tool=args.tool or "notebook",
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.culprit not in CULPRITS or params.marker not in MARKERS:
        raise StoryError("Unknown culprit or marker.")
    world = World()
    setting = SETTINGS[params.setting]
    culprit = CULPRITS[params.culprit]
    marker = MARKERS[params.marker]
    witness = world.add(Entity(id=params.witness, kind="character", type=params.witness_gender, role="witness"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}", role="helper"))
    world.add(Entity(id="culprit", kind="thing", type=culprit.id, label=culprit.label, tags=culprit.tags))
    world.add(Entity(id="marker", kind="thing", type=marker.id, label=marker.label, tags=marker.tags))
    world.add(Entity(id="tool", kind="thing", type="tool", label=params.tool))
    setup(world, setting, witness, parent, culprit, marker)
    world.para()
    clue_scene(world, setting, culprit, marker, params.clue)
    accuse(world, witness, culprit)
    world.get("witness").memes["conflict"] += 1
    world.get("witness").meters["found"] += 1
    world.para()
    fixer = FIXES["revise"]
    reveal(world, culprit, marker)
    revise_case(world, witness, fixer, marker, culprit)
    end_image(world, setting, witness, parent, marker)
    world.facts.update(setting=setting, culprit=culprit, marker=marker, witness=witness, parent=parent, fixer=fixer)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a 3-to-5-year-old set on a canal path that includes the words "revise", "tough", and "property".',
        f"Tell a funny little mystery where {f['witness'].id} thinks someone moved the {f['marker'].label}, but the answer turns out to be harmless and silly.",
        f"Write a story with sound effects like quack or plip, a small conflict, and an ending that revises the clue and solves the property mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    witness = f["witness"]
    parent = f["parent"]
    culprit = f["culprit"]
    marker = f["marker"]
    return [
        QAItem(
            question="Who was trying to solve the mystery?",
            answer=f"{witness.id} was trying to solve it, with {parent.label_word} walking beside {witness.pronoun('object')}."),
        QAItem(
            question="What seemed to be the problem at first?",
            answer=f"It looked like someone had moved the {marker.label}, and that made the case feel tough. The clue was muddy, so the answer was not obvious right away."),
        QAItem(
            question=f"What did {witness.id} do to fix the mistake?",
            answer=f"{witness.id} decided to revise the note and write the correct answer. That way the property marker made sense again, and the confusion could stop."),
        QAItem(
            question="How did the story end?",
            answer=f"The mystery turned out to be harmless and a little funny. In the end, {culprit.label} only left silly tracks, and everyone could laugh and keep walking."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for e in list(world.entities.values()):
        tags |= set(e.tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    parts.append(f"fired={sorted(world.fired)}")
    return "\n".join(parts)


ASP_RULES = r"""
conflict(E) :- actor(E), wants_answer(E).
mystery(C,M) :- culprit(C), marker(M), harmless(C), movable(M).
solution(M) :- mystery(_,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if c.harmless:
            lines.append(asp.fact("harmless", cid))
    for mid, m in MARKERS.items():
        lines.append(asp.fact("marker", mid))
        if m.movable:
            lines.append(asp.fact("movable", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, culprit=None, marker=None, name=None, gender=None, parent=None, tool=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    print("OK" if rc == 0 else "FAIL")
    return rc


CURATED = [
    StoryParams(setting="canal_path", culprit="duck", witness="Mina", witness_gender="girl", parent="mother", marker="sign", clue="muddy tracks", tool="notebook"),
    StoryParams(setting="canal_path", culprit="goose", witness="Owen", witness_gender="boy", parent="father", marker="post", clue="squishy prints", tool="notebook"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if args.show_asp:
        print(asp_program("#show mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
