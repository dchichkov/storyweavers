#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glop_instant_walk_happy_ending_inner_monologue.py
=================================================================================

A small bedtime storyworld about a child, an accidental glop spill, a careful
walk through the hallway, and a happy ending with inner monologue.

Premise:
- A child is getting ready for bed.
- An instant bowl of glop gets spilled near the hallway.
- The child wants to walk through and worries about making the mess worse.
- A grown-up helps clean it up in a sensible way.
- The child ends the night safe, calm, and tucked in.

This is a standalone storyworld script. It models typed entities with physical
meters and emotional memes, includes a Python reasonableness gate and an inline
ASP twin, and supports the shared Storyweavers CLI contract.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    instant: bool = True
    sweet: bool = False
    spill_word: str = "glop"
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
class Place:
    id: str
    label: str
    scene: str
    dark: bool = False
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
class Cleanup:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["mess"] >= THRESHOLD and e.memes["worry"] >= THRESHOLD:
            sig = ("worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["frown"] += 1
            out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["relief"] >= THRESHOLD:
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["calm"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(source: Source, place: Place) -> bool:
    return source.instant and place.dark


def sensible_cleanups() -> list[Cleanup]:
    return [c for c in CLEANUPS.values() if c.sense >= SENSE_MIN]


def story_tension(source: Source, delay: int) -> int:
    return 1 + delay


def can_fix(cleanup: Cleanup, delay: int) -> bool:
    return cleanup.power >= story_tension(SOURCES["instant_glop"], delay)


def predict_glop(world: World, source_id: str) -> dict:
    sim = world.copy()
    _spill(sim, sim.get(source_id), narrate=False)
    child = next(iter(sim.characters()))
    return {"mess": child.meters["mess"], "worry": child.memes["worry"]}


def _spill(world: World, source_ent: Entity, narrate: bool = True) -> None:
    child = world.get("child")
    hall = world.get("hall")
    child.meters["mess"] += 1
    hall.meters["mess"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, child: Entity, parent: Entity, place: Place, source: Source) -> None:
    child.memes["hope"] += 1
    world.say(
        f"At bedtime, {child.id} padded down the hall, thinking sleep would come "
        f"as soon as {child.pronoun('possessive')} room was ready. But the hallway "
        f"looked sleepy and dim, and a little bowl of {source.phrase} had already "
        f"turned into {source.spill_word} on the floor."
    )
    world.say(
        f'{child.id} thought, "If I walk too fast, I might smush it. If I walk too '
        f"slow, I might never get to bed.""
    )


def notice(world: World, child: Entity, parent: Entity, place: Place, source: Source) -> None:
    pred = predict_glop(world, "instant_glop")
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{child.id} took a careful breath. "I want to walk to bed," '
        f"{child.pronoun()} whispered to {child.pronoun('possessive')}self, "
        f'"but I do not want {source.spill_word} on my feet."'
    )
    world.say(
        f"{parent.label_word.capitalize()} heard the tiny worry and knelt beside "
        f"{child.id}. {parent.pronoun().capitalize()} said the glop would be fixed "
        f"before anyone tried the long walk again."
    )


def spill(world: World, child: Entity, source: Source) -> None:
    child.meters["mess"] += 1
    child.memes["worry"] += 1
    _spill(world, world.get("instant_glop"))
    world.say(
        f"The bowl tipped just a little, and glop splashed into a shiny smear. "
        f"{child.id}'s heart thumped. " f'"Oh no," {child.id} thought, "now the hall '
        f"feels sticky."'
    )


def fix(world: World, parent: Entity, cleanup: Cleanup, source: Source) -> None:
    parent.memes["care"] += 1
    if cleanup.id == "towel":
        world.get("hall").meters["mess"] = 0
        world.get("child").meters["mess"] = 0
        world.get("child").memes["relief"] += 1
        world.get("parent").memes["relief"] += 1
        world.say(
            f"{parent.label_word.capitalize()} came with a soft towel and wiped the "
            f"glop up in one patient sweep. {cleanup.qa_text}."
        )
    else:
        world.get("hall").meters["mess"] = 0
        world.get("child").meters["mess"] = 0
        world.get("child").memes["relief"] += 1
        world.get("parent").memes["relief"] += 1
        world.say(
            f"{parent.label_word.capitalize()} used {cleanup.text} and made the "
            f"floor safe again. {cleanup.qa_text}."
        )


def end_walk(world: World, child: Entity, parent: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    world.say(
        f'Then {child.id} and {parent.label_word} did the walk to bed together, '
        f"slow and sure, past the clean hallway and into the warm room."
    )
    world.say(
        f'{child.id} curled under the blanket and thought, "The night feels small '
        f'now. I am safe, and I can sleep."'
    )


def tell(place: Place, source: Source, cleanup: Cleanup, delay: int = 0,
         child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="hall", type="hall", label="the hallway"))
    world.add(Entity(id="instant_glop", type="spill", label=source.label))
    child.memes["worry"] = 1
    begin(world, child, parent, place, source)
    world.para()
    notice(world, child, parent, place, source)
    spill(world, child, source)
    world.para()
    if can_fix(cleanup, delay):
        fix(world, parent, cleanup, source)
        end_walk(world, child, parent, place)
        outcome = "happy"
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried to help, but the spill had "
            f"already spread too far for that simple fix."
        )
        outcome = "sad"
    world.facts.update(
        child=child,
        parent=parent,
        place=place,
        source=source,
        cleanup=cleanup,
        outcome=outcome,
        delay=delay,
        glop_seen=True,
        cleaned=outcome == "happy",
    )
    return world


PLACES = {
    "hallway": Place(id="hallway", label="the hallway", scene="a quiet hallway", dark=True, tags={"hall", "dark"}),
    "kitchen": Place(id="kitchen", label="the kitchen", scene="a cozy kitchen", dark=False, tags={"kitchen"}),
    "stairs": Place(id="stairs", label="the stairs", scene="the stairs by the door", dark=True, tags={"stairs", "dark"}),
}

SOURCES = {
    "instant_glop": Source(id="instant_glop", label="instant glop", phrase="instant glop", instant=True, sweet=True, spill_word="glop", tags={"glop", "instant"}),
    "berry_glop": Source(id="berry_glop", label="berry glop", phrase="berry glop", instant=True, sweet=False, spill_word="glop", tags={"glop"}),
}

CLEANUPS = {
    "towel": Cleanup(id="towel", sense=3, power=3, text="a soft towel", fail="pressed too hard and smeared it around", qa_text="The towel made the floor dry and easy to walk on", tags={"towel"}),
    "napkin": Cleanup(id="napkin", sense=2, power=2, text="a stack of napkins", fail="used napkins, but the glop was too sticky", qa_text="The napkins helped for a little bit", tags={"napkin"}),
    "mop": Cleanup(id="mop", sense=3, power=4, text="a small mop", fail="tried to mop it, but it had already spread", qa_text="The mop left the hallway clean and shiny", tags={"mop"}),
}

SENSE_MIN = 2

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    place: str
    source: str
    cleanup: str
    child_name: str
    child_type: str
    parent_type: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, source in SOURCES.items():
            for cid, cleanup in CLEANUPS.items():
                if hazard_at_risk(source, place) and cleanup.sense >= SENSE_MIN:
                    combos.append((pid, sid, cid))
    return combos


GIRL_NAMES = ["Mina", "Luna", "Nora", "Tessa", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Owen", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a glop spill and a happy walk back to bed.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.place and args.source and not hazard_at_risk(SOURCES[args.source], PLACES[args.place]):
        raise StoryError("That source and place don't make a real bedtime worry.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.source is None or c[1] == args.source)
              and (args.cleanup is None or c[2] == args.cleanup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, source, cleanup = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place=place, source=source, cleanup=cleanup, child_name=name, child_type=gender, parent_type=parent, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "glop", "instant", and "walk".',
        f"Tell a cozy story where {f['child'].id} wants to walk through the hallway, sees {f['source'].label}, and a parent helps with a calm happy ending.",
        "Write a gentle story with a little worry inside the child's thoughts and a warm ending in bed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source = f["source"]
    cleanup = f["cleanup"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to walk to bed through the hallway, but the glop made the path feel tricky. The child had to slow down and think before stepping.",
        ),
        QAItem(
            question="Why did the child worry?",
            answer=f"{child.id} worried because the instant glop had spilled on the floor and could get smeared if the child walked too fast. The worry was small, but it was enough to ask for help.",
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"The grown-up cleaned the glop with {cleanup.text}, which made the hallway safe again. That let the bedtime walk happen without making the mess worse.",
        ),
    ]
    if f["outcome"] == "happy":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {child.id} walking back to bed beside the grown-up after the glop was cleaned. The child felt calm enough to sleep at last.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["source"].tags) | set(world.facts["cleanup"].tags)
    out = []
    if "glop" in tags:
        out.append(QAItem(
            question="What is glop?",
            answer="Glop is a gooey, sloppy mess. It can splash and smear, so it is best to clean it up carefully.",
        ))
    if "instant" in tags:
        out.append(QAItem(
            question="What does instant mean?",
            answer="Instant means very fast or right away. If something is instant, it happens almost at once.",
        ))
    out.append(QAItem(
        question="What does a towel do on a spill?",
        answer="A towel soaks up wet messes and helps make the floor safe again. It is a simple, calm way to clean up.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world QA ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, S) :- place(P), source(S), instant(S), dark(P).
valid(P, S, C) :- hazard(P, S), cleanup(C), sense(C, N), N >= sense_min.
happy :- chosen_cleanup(C), power(C, P), severity(V), P >= V.
severity(1 + D) :- delay(D).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for sid, s in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if s.instant:
            lines.append(asp.fact("instant", sid))
    for cid, c in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) == set(valid_combos()):
            print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
        else:
            print("MISMATCH in gate.")
            rc = 1
    except Exception:
        traceback.print_exc()
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.source not in SOURCES or params.cleanup not in CLEANUPS:
        raise StoryError("Unknown story parameters.")
    place = PLACES[params.place]
    source = SOURCES[params.source]
    cleanup = CLEANUPS[params.cleanup]
    if not hazard_at_risk(source, place):
        raise StoryError("That combination does not make a bedtime problem.")
    world = tell(place, source, cleanup, delay=params.delay, child_name=params.child_name, child_type=params.child_type, parent_type=params.parent_type)
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


def resolve_single(args: argparse.Namespace, seed: int) -> StoryParams:
    return resolve_params(args, random.Random(seed))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hallway", source="instant_glop", cleanup="towel", child_name="Mina", child_type="girl", parent_type="mother", delay=0),
            StoryParams(place="stairs", source="berry_glop", cleanup="mop", child_name="Noah", child_type="boy", parent_type="father", delay=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_single(args, base_seed + i)
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
