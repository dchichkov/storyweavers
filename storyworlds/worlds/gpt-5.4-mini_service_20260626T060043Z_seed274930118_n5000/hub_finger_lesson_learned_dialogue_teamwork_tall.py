#!/usr/bin/env python3
"""
Storyworld: hub_finger_lesson_learned_dialogue_teamwork_tall

A small Tall Tale-style story world about a big wagon wheel hub, a curious
finger, a lesson learned, and a teamwork fix.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PRESENTS = {
    "hub": "the wagon wheel hub",
    "mill": "the mill wheel hub",
    "cart": "the cart hub",
    "cannon": "the cannon wheel hub",
}

CHARACTER_NAMES = ["Nell", "Buck", "Toby", "Mabel", "Finn", "Cora", "Jeb", "Annie"]
CHARACTER_ROLES = ["spark-eyed child", "wide-hatted helper", "plain-spoken fix-it friend"]
HUB_SIZES = ["big", "bigger-than-a-barn", "great as a supper table", "tall as a fence post"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Hub:
    label: str
    size: str
    jammed: bool = False
    crack: bool = False
    loosened: bool = False
    ready: bool = False


@dataclass
class StoryParams:
    place: str
    hub_kind: str
    name: str
    partner: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------


class World:
    def __init__(self, place: str, hub: Hub):
        self.place = place
        self.hub = hub
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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

        clone = World(self.place, copy.deepcopy(self.hub))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------


def _r_hub_wobbles(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.hub.jammed or world.hub.loosened:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.hub.jammed = True
    child.meters["finger"] = 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    out.append("The hub gave a great wobble, and the child's finger got pinched in the tight old rim.")
    return out


def _r_call_helpers(world: World) -> list[str]:
    out = []
    child = world.get("child")
    partner = world.get("partner")
    if not world.hub.jammed:
        return out
    sig = ("helpers",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    partner.memes["resolve"] = partner.memes.get("resolve", 0.0) + 1.0
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    out.append("That pinched finger made the child gasp, and the helper came running with steady hands.")
    return out


def _r_teamwork_fix(world: World) -> list[str]:
    out = []
    child = world.get("child")
    partner = world.get("partner")
    if not world.hub.jammed:
        return out
    if child.memes.get("trust", 0.0) < THRESHOLD or partner.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.hub.jammed = False
    world.hub.loosened = True
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1.0
    partner.memes["joy"] = partner.memes.get("joy", 0.0) + 1.0
    out.append("Together they rocked the wheel, lifted the hub, and freed the finger without breaking a thing.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_hub_wobbles, _r_call_helpers, _r_teamwork_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------


def build_hub(hub_kind: str) -> Hub:
    size = random.choice(HUB_SIZES)
    return Hub(label=PRESENTS[hub_kind], size=size)


def tell(place: str, hub_kind: str, name: str, partner_name: str) -> World:
    hub = build_hub(hub_kind)
    world = World(place=place, hub=hub)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=name,
        phrase=f"a {random.choice(CHARACTER_ROLES)} named {name}",
        meters={"finger": 0.0},
        memes={"curiosity": 1.0, "trust": 0.0},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type="adult",
        label=partner_name,
        phrase=f"a {random.choice(CHARACTER_ROLES)} named {partner_name}",
        memes={"resolve": 0.0},
    ))
    world.facts.update(child=child, partner=partner, hub=hub, place=place, hub_kind=hub_kind)

    # Act 1: setup.
    world.say(
        f"In {place}, there lived {child.phrase}, and {partner.phrase}, and before supper they stood beside {hub.label}."
    )
    world.say(
        f"{child.name_or_label()} had never seen a hub so {hub.size}, and {child.pronoun().capitalize()} wanted a closer look."
    )

    # Act 2: trouble.
    world.para()
    world.say(
        f"'Mind your finger,' {partner.name_or_label()} warned, but the child leaned in anyway and the old wheel shivered like a stump in a storm."
    )
    propagate(world, narrate=True)
    world.say(
        f"'Hold still,' {partner.name_or_label()} said. 'We can fix this together.'"
    )
    child.memes["trust"] += 1.0

    # Act 3: teamwork and lesson learned.
    world.para()
    propagate(world, narrate=True)
    world.say(
        f"After that, {child.name_or_label()} kept {child.pronoun('possessive')} fingers clear of tight places, and the whole crew worked as neat as a fiddler's tune."
    )
    world.hub.ready = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    partner = f["partner"]
    hub = f["hub"]
    return [
        f"Write a tall-tale story about {child.label}, a huge hub, and a mistake that gets fixed through teamwork.",
        f"Tell a child-friendly story where {child.label} learns a lesson after a finger gets pinched near {hub.label}.",
        f"Write a dialogue-heavy tale in which {partner.label} and {child.label} solve a hub problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    partner = f["partner"]
    hub = f["hub"]
    return [
        QAItem(
            question=f"What was {child.label} looking at near the start of the story?",
            answer=f"{child.label} was looking at {hub.label}, a {hub.size} old wheel hub in {world.place}.",
        ),
        QAItem(
            question=f"What went wrong when {child.label} leaned in too close?",
            answer=f"{child.label}'s finger got pinched in the tight rim of the hub, which scared the child and started the trouble.",
        ),
        QAItem(
            question=f"How did {child.label} and {partner.label} fix the problem?",
            answer=f"They worked together: they rocked the wheel, lifted the hub, and freed the finger without breaking anything.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned to keep {child.pronoun('possessive')} fingers clear of tight places and to ask for help right away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hub?",
            answer="A hub is the middle part of a wheel that holds the spokes together and lets the wheel turn.",
        ),
        QAItem(
            question="Why should you keep your fingers away from tight moving parts?",
            answer="You should keep your fingers away because tight moving parts can pinch or hurt them.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to get something done.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
place(hubtown).
activity(hub_lesson).
feature(dialogue).
feature(teamwork).
feature(lesson_learned).

valid(hubtown, hub_lesson) :- feature(dialogue), feature(teamwork), feature(lesson_learned).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("place", "hubtown"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "lesson_learned"),
        asp.fact("activity", "hub_lesson"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = sorted(set(asp.atoms(model, "valid")))
    py = [("hubtown", "hub_lesson")]
    if atoms == py:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH:")
    print("ASP:", atoms)
    print("PY :", py)
    return 1


# ---------------------------------------------------------------------------
# Parameters, parsing, generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a hub and a finger, with dialogue, teamwork, and a lesson learned.")
    ap.add_argument("--place", default="hubtown", choices=["hubtown"])
    ap.add_argument("--hub-kind", default="hub", choices=sorted(PRESENTS))
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--partner", choices=CHARACTER_NAMES)
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
    name = args.name or rng.choice(CHARACTER_NAMES)
    partner_choices = [n for n in CHARACTER_NAMES if n != name]
    partner = args.partner or rng.choice(partner_choices)
    return StoryParams(place=args.place, hub_kind=args.hub_kind, name=name, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hub_kind, params.name, params.partner)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place}")
    lines.append(f"hub: {world.hub}")
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: kind={ent.kind} type={ent.type} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"fired: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hubtown", hub_kind="hub", name="Nell", partner="Buck"),
    StoryParams(place="hubtown", hub_kind="mill", name="Toby", partner="Mabel"),
    StoryParams(place="hubtown", hub_kind="cart", name="Cora", partner="Jeb"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
