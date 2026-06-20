#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/herald_guide_surgery_lesson_learned_foreshadowing_mystery.py
=============================================================================================

A standalone story world for a small mystery tale about a herald, a guide, and a
needed surgery.

Core premise:
- A child notices a worrying clue.
- A herald brings an important message.
- A guide helps the family find the right place and the right grown-up.
- Surgery fixes the problem.
- The story includes foreshadowing and a lesson learned, in a child-facing,
  mystery-leaning style.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven rendering
- prompts, story QA, and world knowledge QA
- Python reasonableness gate plus inline ASP twin
- --verify smoke test and parity check
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

# Make the shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    mood: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Herald:
    id: str
    title: str
    message: str
    reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Guide:
    id: str
    title: str
    path: str
    help_line: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Surgery:
    id: str
    name: str
    problem: str
    fix: str
    recovery: str
    urgency: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["symptom"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["symptom"] >= THRESHOLD and ("foreshadow", "clue") not in world.fired:
        world.fired.add(("foreshadow", "clue"))
        world.get("clue").meters["hint"] += 1
        out.append("__hint__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("foreshadow", "mystery", _r_foreshadow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def could_need_surgery(ache: Surgery, severity: int) -> bool:
    return severity >= ache.urgency


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HERALDS:
            for g in GUIDES:
                for s in SURGERIES:
                    if p.id in {"clinic", "hospital"} and could_need_surgery(s, 2):
                        combos.append((p.id, h.id, g.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    herald: str
    guide: str
    surgery: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: a herald, a guide, a surgery, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--herald", choices=HERALDS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--surgery", choices=SURGERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    herald = args.herald or rng.choice(list(HERALDS))
    guide = args.guide or rng.choice(list(GUIDES))
    surgery = args.surgery or rng.choice(list(SURGERIES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent or (rng.choice(["Mom", "Dad"]) if parent_gender == "mother" else rng.choice(["Mom", "Dad"]))
    if args.place and args.place not in {"clinic", "hospital"}:
        raise StoryError("This mystery needs a clinic or hospital setting so surgery can happen.")
    return StoryParams(place, herald, guide, surgery, child_name, child_gender, parent_name, parent_gender)


def tell(world: World, child: Entity, parent: Entity, herald: Herald, guide: Guide, surgery: Surgery) -> None:
    child.memes["curiosity"] += 1
    child.meters["symptom"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} noticed a strange ache and a tiny sign that did not make sense. "
        f"It was not loud, but it kept coming back."
    )
    world.say(
        f"Near the doorway, a herald arrived with a clear message: {herald.message}. "
        f"{herald.reveal}."
    )
    world.say(
        f"{child.id} looked at {parent.id} and then at the clue by the hall. "
        f"It had been there all morning, like a secret waiting to be understood."
    )
    world.para()
    child.memes["fear"] += 1
    world.say(
        f"A guide stepped forward and said, {guide.help_line} "
        f"{guide.path}. The guide helped them find the right place without getting lost."
    )
    world.say(
        f"At the clinic, the grown-ups explained that the problem was called {surgery.problem}. "
        f"{surgery.fix}."
    )
    child.meters["needs_surgery"] += 1
    child.meters["repaired"] += 1
    child.memes["relief"] += 1
    world.para()
    world.say(
        f"The surgery {surgery.name} went carefully and gently. Afterward, {surgery.recovery}, and "
        f"{child.id} felt the ache fade away."
    )
    world.say(
        f"{parent.id} smiled and held {child.id}'s hand. The little clue had been a foreshadowing of the real problem, "
        f"and now the mystery made sense."
    )
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} learned that when a small sign keeps returning, it is smart to tell a grown-up early. "
        f"That way, help can arrive before the trouble grows bigger."
    )
    world.say(
        f"By evening, {child.id} walked home feeling lighter, while {parent.id} kept the medicine card safe in a pocket."
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    herald = HERALDS[params.herald]
    guide = GUIDES[params.guide]
    surgery = SURGERIES[params.surgery]
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue"))
    world.add(Entity(id="herald", kind="character", type="messenger", role="herald"))
    world.add(Entity(id="guide", kind="character", type="helper", role="guide"))

    tell(world, child, parent, herald, guide, surgery)
    world.facts.update(
        child=child,
        parent=parent,
        place=place,
        herald=herald,
        guide=guide,
        surgery=surgery,
        clue=clue,
        lesson=True,
        foreshadow=True,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "herald", "guide", and "surgery".',
        f"Tell a gentle mystery where {f['child'].id} notices a clue, a herald brings news, a guide helps, and surgery solves the problem.",
        "Write a child-facing mystery with foreshadowing and a lesson learned, ending in a calm hospital scene.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    surgery = f["surgery"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {parent.id}, who work through a small mystery together."),
        ("What clue helped foreshadow the problem?", "A tiny repeated sign kept showing up early, which hinted that something inside needed attention."),
        ("What fixed the problem?", f"The surgery called {surgery.name} fixed it. After that, the ache faded and the mystery was solved."),
        ("What lesson did the child learn?", "The child learned to tell a grown-up early when a small sign keeps coming back. That helps the right people find the problem sooner."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a herald?", "A herald is a messenger who brings an important announcement."),
        ("What is a guide?", "A guide is someone who helps other people find their way."),
        ("What is surgery?", "Surgery is a medical operation that doctors do to fix a problem in the body."),
        ("What is foreshadowing?", "Foreshadowing is when a story gives a small clue early that hints at what will matter later."),
        ("What is a mystery story?", "A mystery story asks a question, shows clues, and then reveals what was really going on."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_combo(place: str, herald: str, guide: str, surgery: str) -> bool:
    return place in {"clinic", "hospital"} and herald in HERALDS and guide in GUIDES and surgery in SURGERIES


def explain_rejection(place: str) -> str:
    return "This story needs a clinic or hospital so surgery can happen and the mystery can be solved."


@dataclass
class CatalogItem:
    id: str
    label: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "clinic": Place("clinic", "the clinic", "bright", "a small clue in the waiting room", {"medical"}),
    "hospital": Place("hospital", "the hospital", "quiet", "a small clue in the hallway", {"medical"}),
    "house": Place("house", "the house", "cozy", "a small clue near the stairs", {"medical"}),
}

HERALDS = {
    "bell": Herald("bell", "a little bell", "a herald rang a little bell", "The message said help was needed soon", {"message"}),
    "letter": Herald("letter", "a sealed letter", "the herald carried a sealed letter", "It named the right doctor", {"message"}),
    "knock": Herald("knock", "a knock at the door", "the herald gave three polite knocks", "The sound came before the grown-ups spoke", {"message"}),
}

GUIDES = {
    "nurse": Guide("nurse", "a nurse", "through the bright hallway", "The guide said to follow the green arrow", {"helper"}),
    "doctor": Guide("doctor", "a doctor", "to the calm side door", "The guide said the safest room was nearby", {"helper"}),
    "friend": Guide("friend", "a kind friend", "down the quiet path", "The guide held a flashlight and kept everyone steady", {"helper"}),
}

SURGERIES = {
    "tonsils": Surgery("tonsils", "tonsil surgery", "swollen tonsils", "The doctor fixed the sore part so breathing would be easier", "the child rested with a soft cup of water", 2, {"medical"}),
    "arm": Surgery("arm", "arm surgery", "a bent arm problem", "The doctor straightened and protected the arm", "the arm stayed in a cozy sling", 2, {"medical"}),
    "tummy": Surgery("tummy", "tummy surgery", "a hidden tummy problem", "The doctor repaired the spot that hurt", "the child slept and woke up feeling better", 3, {"medical"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Sam", "Noah"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HERALDS:
        lines.append(asp.fact("herald", hid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    for sid in SURGERIES:
        lines.append(asp.fact("surgery", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H,G,S) :- place(P), herald(H), guide(G), surgery(S), (P = clinic; P = hospital).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    rc = 0
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
    try:
        sample = generate(resolve_params(argparse.Namespace(place="clinic", herald=None, guide=None, surgery=None, name=None, gender=None, parent=None, parent_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in {"clinic", "hospital"}:
        raise StoryError(explain_rejection(args.place))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.herald is None or c[1] == args.herald)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, herald, guide = rng.choice(combos)
    surgery = args.surgery or rng.choice(list(SURGERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent = args.parent or rng.choice(["Mom", "Dad"])
    return StoryParams(place, herald, guide, surgery, name, gender, parent, parent_gender)


def generate_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue"))
    herald = HERALDS[params.herald]
    guide = GUIDES[params.guide]
    surgery = SURGERIES[params.surgery]
    tell(world, child, parent, herald, guide, surgery)
    world.facts.update(child=child, parent=parent, clue=clue, herald=herald, guide=guide, surgery=surgery)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams("clinic", "bell", "nurse", "tonsils", "Mia", "girl", "Mom", "mother"),
    StoryParams("hospital", "letter", "doctor", "arm", "Leo", "boy", "Dad", "father"),
    StoryParams("clinic", "knock", "friend", "tummy", "Nora", "girl", "Mom", "mother"),
]


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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
