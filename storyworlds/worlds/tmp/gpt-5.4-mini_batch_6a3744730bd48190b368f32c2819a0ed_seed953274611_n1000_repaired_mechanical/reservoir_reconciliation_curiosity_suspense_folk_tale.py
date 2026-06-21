#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reservoir_reconciliation_curiosity_suspense_folk_tale.py
=========================================================================================

A standalone storyworld for a small folk-tale domain: two children are warned
away from an old reservoir, curiosity leads one of them toward a suspenseful
moment, and a reconciliation with a cautious helper turns the danger into a
shared lesson and a safer ending.

The world is built from typed entities with physical meters and emotional memes.
State changes drive the prose; this is not a frozen paragraph with swapped names.
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    name: str
    waterside: bool
    has_bridge: bool = False
    has_gate: bool = False
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
class Interest:
    id: str
    label: str
    verb: str
    lure: str
    risk: str
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
class Helper:
    id: str
    label: str
    title: str
    comfort: str
    method: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["edge"] < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reconciled"):
        return out
    for e in world.characters():
        if e.memes["softened"] >= THRESHOLD:
            sig = ("reconcile", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["peace"] += 1
            out.append("__")
            world.facts["reconciled"] = True
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("reconciliation", _r_reconciliation)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def valid_combo(place: Place, interest: Interest) -> bool:
    return place.waterside and interest.id in {"pebble", "frog", "lost_scarf"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, interest in INTERESTS.items():
            if valid_combo(place, interest):
                combos.append((pid, iid))
    return combos


def smell_reservoir(world: World, child: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At the edge of the village stood the reservoir, dark and still, with reeds whispering around its bank."
    )
    world.say(
        f"{child.id} leaned closer because {child.pronoun('possessive')} heart wanted to know what hid beneath the water."
    )


def warning(world: World, helper: Entity, child: Entity, interest: Interest, place: Place) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} said, \"Do not wander to the {place.name}; the water keeps its own secrets.\""
    )
    world.say(
        f"But {child.id} had noticed {interest.lure}, and curiosity tugged harder than caution."
    )


def suspense_scene(world: World, child: Entity, interest: Interest) -> None:
    child.meters["edge"] += 1
    propagate(world)
    world.say(
        f"{child.id} reached for {interest.label}, and for one breath the world held its own breath too."
    )
    world.say(
        f"The ripples shivered, the reeds bent, and even the crows went quiet above the reservoir."
    )


def rescue_and_reconcile(world: World, helper: Entity, child: Entity, interest: Interest) -> None:
    child.memes["softened"] += 1
    helper.memes["softened"] += 1
    child.meters["edge"] = 0.0
    world.say(
        f"Then {helper.id} stepped close, used {helper.method}, and guided {child.id} back from the bank."
    )
    world.say(
        f"{helper.label_word.capitalize()} was not angry. {helper.label_word.capitalize()} only said that a child can be brave and still listen."
    )
    world.say(
        f"{child.id} looked at {interest.label}, then at {helper.id}, and the two of them made peace over the scared little moment."
    )


def ending(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["peace"] += 1
    helper.memes["peace"] += 1
    if place.has_bridge:
        bridge = "the little bridge"
        extra = "They crossed back by the little bridge, hand in hand."
    else:
        bridge = "the path"
        extra = "They walked back along the path, side by side."
    world.say(
        f"Afterward, {child.id} and {helper.id} stood together at {bridge} and watched the reservoir glow like a silver bowl under the evening sky."
    )
    world.say(extra)


def tell(place: Place, interest: Interest, helper_cfg: Helper, child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="curious", traits=["curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["wise"]))
    world.facts.update(place=place, interest=interest, helper=helper_cfg, child=child, reconciled=False)

    smell_reservoir(world, child, place)
    world.para()
    warning(world, helper, child, interest, place)
    world.para()
    suspense_scene(world, child, interest)
    world.para()
    rescue_and_reconcile(world, helper, child, interest)
    world.para()
    ending(world, child, helper, place)
    return world


PLACES = {
    "reservoir": Place(id="reservoir", name="reservoir", waterside=True, has_bridge=True, tags={"water", "folk"}),
    "pond": Place(id="pond", name="pond", waterside=True, has_gate=False, tags={"water", "folk"}),
    "mill_pool": Place(id="mill_pool", name="mill pool", waterside=True, has_bridge=False, has_gate=True, tags={"water", "folk"}),
}

INTERESTS = {
    "pebble": Interest(id="pebble", label="a bright pebble", verb="reach for a bright pebble", lure="the bright pebble glinting near the water", risk="slip", tags={"curiosity"}),
    "frog": Interest(id="frog", label="a green frog", verb="follow a green frog", lure="the green frog hopping by the reeds", risk="slip", tags={"curiosity"}),
    "lost_scarf": Interest(id="lost_scarf", label="a red scarf", verb="reach for a red scarf", lure="the red scarf caught on a branch by the bank", risk="fall", tags={"curiosity"}),
}

HELPERS = {
    "grandmother": Helper(id="grandmother", label="grandmother", title="Grandmother", comfort="a soft shawl", method="a steady hand on the shoulder", tags={"reconciliation"}),
    "uncle": Helper(id="uncle", label="uncle", title="Uncle", comfort="a calm voice", method="a long walking stick", tags={"reconciliation"}),
    "old_heron": Helper(id="old_heron", label="old heron", title="Old Heron", comfort="a patient look", method="a white wing pointed toward the path", tags={"folk", "reconciliation"}),
}

CHILD_NAMES = ["Mina", "Tobin", "Lena", "Oren", "Pia", "Ravi", "Tessa", "Nico"]
HELPER_NAMES = ["Grandmother", "Uncle Bram", "Old Heron"]

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    place: str
    interest: str
    helper: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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


CURATED = [
    StoryParams(place="reservoir", interest="pebble", helper="grandmother", child_name="Mina", child_type="girl", helper_name="Grandmother", helper_type="mother"),
    StoryParams(place="pond", interest="frog", helper="uncle", child_name="Tobin", child_type="boy", helper_name="Uncle Bram", helper_type="uncle"),
    StoryParams(place="mill_pool", interest="lost_scarf", helper="old_heron", child_name="Lena", child_type="girl", helper_name="Old Heron", helper_type="thing"),
]


KNOWLEDGE = {
    "reservoir": [("What is a reservoir?", "A reservoir is a place where a lot of water is kept. People and animals must stay careful around it.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to know more. It can help you learn, but it can also lead you into trouble if you are not careful.")],
    "suspense": [("What does suspense mean?", "Suspense is the feeling of waiting and wondering what will happen next. It can make a story feel very tense.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people make peace after a worried or angry moment. They speak kindly again and the upset feeling goes away.")],
}
KNOWLEDGE_ORDER = ["reservoir", "curiosity", "suspense", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, place, interest = f["child"], f["helper"], f["place"], f["interest"]
    return [
        f"Write a folk-tale style story about {child.id}, the {place.name}, and {interest.label}, with curiosity and suspense.",
        f"Tell a gentle suspense story where {child.id} nearly gets too close to the {place.name}, but {helper.id} helps {child.id} reconcile and return safely.",
        f"Write a child-friendly story that includes the word reservoir and ends with peace after a tense moment by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, place, interest = f["child"], f["helper"], f["place"], f["interest"]
    return [
        QAItem(question="What was the story about?", answer=f"It was about {child.id} by the {place.name}, where curiosity led to a tense moment and then reconciliation. The reservoir was the quiet place that made the whole scene feel old and full of secrets."),
        QAItem(question=f"What did {child.id} want?", answer=f"{child.id} wanted to {interest.verb}. That wish made the story suspenseful because the water was nearby and the moment felt dangerous."),
        QAItem(question=f"How did {helper.id} help?", answer=f"{helper.id} used {f['helper'].method} and brought {child.id} back from the bank. That careful help turned fear into reconciliation."),
        QAItem(question="How did the story end?", answer=f"It ended with {child.id} and {helper.id} together again, calm and safe. They stood near the reservoir and watched the water shine without any more trouble."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["place"].tags) | set(world.facts["interest"].tags) | set(world.facts["helper"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_for_params(params: StoryParams) -> bool:
    return params.place in PLACES and params.interest in INTERESTS and params.helper in HELPERS


def explain_rejection(params: StoryParams) -> str:
    if params.place not in PLACES:
        return "(No story: unknown place.)"
    if params.interest not in INTERESTS:
        return "(No story: unknown interest.)"
    return "(No story: this combination does not create a believable waterside suspense tale.)"


ASP_RULES = r"""
place(reservoir). place(pond). place(mill_pool).
waterside(reservoir). waterside(pond). waterside(mill_pool).
has_bridge(reservoir). has_gate(mill_pool).

interest(pebble). interest(frog). interest(lost_scarf).

valid(P, I) :- waterside(P), interest(I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].waterside:
            lines.append(asp.fact("waterside", pid))
        if PLACES[pid].has_bridge:
            lines.append(asp.fact("has_bridge", pid))
        if PLACES[pid].has_gate:
            lines.append(asp.fact("has_gate", pid))
    for iid in INTERESTS:
        lines.append(asp.fact("interest", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, interest=None, helper=None, child_name=None, child_type=None, helper_name=None, helper_type=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: normal generation crashed: {exc}")
        rc = 1
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"MISMATCH: emit crashed: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about reservoir curiosity and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--interest", choices=INTERESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle", "thing"])
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
    place = args.place or rng.choice(list(PLACES))
    interest = args.interest or rng.choice(list(INTERESTS))
    helper = args.helper or rng.choice(list(HELPERS))
    if not valid_combo(PLACES[place], INTERESTS[interest]):
        raise StoryError(explain_rejection(StoryParams(place=place, interest=interest, helper=helper, child_name="", child_type="", helper_name="", helper_type="")))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Tobin", "Lena", "Oren", "Pia", "Ravi", "Tessa", "Nico"])
    helper_type = args.helper_type or ("thing" if helper == "old_heron" else rng.choice(["mother", "father", "aunt", "uncle"]))
    helper_name = args.helper_name or {"grandmother": "Grandmother", "uncle": "Uncle Bram", "old_heron": "Old Heron"}[helper]
    return StoryParams(place=place, interest=interest, helper=helper, child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if not valid_for_params(params):
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], INTERESTS[params.interest], HELPERS[params.helper], params.child_name, params.child_type, params.helper_name, params.helper_type)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible place/interest combos:")
        for p, i in asp_valid_combos():
            print(f"  {p:10} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
