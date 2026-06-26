#!/usr/bin/env python3
"""
A tiny storyworld: a child meets a ghost, imagines the worst case, and finds a
reconciliation by learning the basics of being kind and brave.

The world is intentionally small and constraint-checked. The core premise is a
ghost story with a gentle turn: the scary-looking ghost is only lonely, and the
child's hypothetical fear gets resolved by a simple act of listening.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    indoors: bool = True
    spooky: bool = False
    echoes: bool = False


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    warm: bool = False
    lights: bool = False
    comfort: bool = False


@dataclass
class StoryParams:
    place: str
    prop: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


LOCATIONS = {
    "attic": Location("attic", "the attic", indoors=True, spooky=True, echoes=True),
    "hall": Location("hall", "the old hallway", indoors=True, spooky=True, echoes=True),
    "garden": Location("garden", "the moonlit garden", indoors=False, spooky=True, echoes=False),
}

PROPS = {
    "lantern": Prop("lantern", "lantern", "a small lantern", "light", lights=True, comfort=True),
    "blanket": Prop("blanket", "blanket", "a soft blanket", "comfort", comfort=True),
    "tea": Prop("tea", "tea", "a warm cup of tea", "warmth", warm=True, comfort=True),
    "chalk": Prop("chalk", "chalk", "a piece of white chalk", "marking", comfort=False),
}

GIRL_NAMES = ["Maya", "Nora", "Lina", "Zoe", "Ivy", "Rose"]
BOY_NAMES = ["Eli", "Finn", "Theo", "Ben", "Noah", "Owen"]
TRAITS = ["curious", "careful", "brave", "gentle", "thoughtful"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.echoes:
        return out
    for c in world.characters():
        if c.memes.get("speaks", 0) < THRESHOLD:
            continue
        sig = ("echo", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["unease"] = c.memes.get("unease", 0.0) + 1
        out.append("The old place echoed the words back softly.")
    return out


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.memes.get("seen", 0) < THRESHOLD:
        return out
    sig = ("lonely",)
    if sig in world.fired:
        return out
    if ghost.memes.get("lonely", 0) < THRESHOLD:
        world.fired.add(sig)
        ghost.memes["lonely"] = 1.0
        out.append("The ghost looked less scary and more lonely.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.memes.get("lonely", 0) < THRESHOLD:
        return out
    if child.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["comfort"] = ghost.memes.get("comfort", 0.0) + 1
    ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1
    out.append("They found a quiet reconciliation.")
    return out


CAUSAL_RULES = [
    Rule("echo", _r_echo),
    Rule("lonely", _r_lonely),
    Rule("reconcile", _r_reconcile),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Location, prop: Prop, name: str, gender: str, companion: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity("child", kind="character", type=gender, label=name))
    ghost = world.add(Entity("ghost", kind="character", type="ghost", label="the ghost"))
    helper = world.add(Entity("helper", kind="character", type=companion, label="the grown-up"))
    item = world.add(Entity("prop", kind="thing", type=prop.kind, label=prop.label, phrase=prop.phrase, owner=name, carried_by=name))
    ghost.meters["pale"] = 1.0
    ghost.memes["alone"] = 1.0
    child.memes["curious"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["speaks"] = 1.0

    world.say(f"{name} was a {trait} child who knew the basics of staying quiet in {place.label}.")
    world.say(f"One night, {name} carried {item.phrase} because {item.label} made the dark feel less empty.")
    world.para()
    world.say(f"In {place.label}, {name} saw {ghost.label}, pale as mist, and {name}'s heart jumped.")
    world.say(f"{name} wondered a hypothetical thing: what if the ghost wanted to frighten everyone away?")
    child.memes["worry"] = 1.0
    child.memes["speaks"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{name} remembered the basics: look, listen, and ask before deciding.")
    if prop.comfort:
        world.say(f"So {name} offered {prop.phrase} and a kind hello.")
        child.memes["kindness"] = 1.0
        ghost.memes["seen"] = 1.0
        if prop.warm:
            ghost.meters["warmth"] = 1.0
        if prop.lights:
            ghost.meters["light"] = 1.0
    else:
        world.say(f"So {name} simply asked what the ghost needed.")
        child.memes["kindness"] = 1.0
        ghost.memes["seen"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"The ghost told the truth: it was not a menace at all, only lonely in the old place.")
    world.say(f"{name} smiled, and the fear turned into a small, steady courage.")
    world.say(f"By the end, {name}, {ghost.label}, and {helper.label} stood together in the quiet dark, no longer apart.")

    world.facts.update(
        child=child,
        ghost=ghost,
        helper=helper,
        prop=item,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prop = f["prop"]
    return [
        f'Write a short ghost story for a child named {child.label} that uses the word "basics".',
        f'Write a gentle, hypothetical ghost story where {child.label} worries about a ghost but then makes peace with it using {prop.label}.',
        f'Create a child-facing ghost story about a scary-looking presence in {world.place.label} that ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, prop = f["child"], f["ghost"], f["prop"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.label}, who met {ghost.label} in {world.place.label}.",
        ),
        QAItem(
            question=f"What hypothetical worry did {child.label} have about the ghost?",
            answer=f"{child.label} wondered if the ghost wanted to frighten everyone away, but that turned out not to be true.",
        ),
        QAItem(
            question=f"What did {child.label} offer to help make peace?",
            answer=f"{child.label} offered {prop.phrase}, along with a gentle hello.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with reconciliation, because the ghost was lonely and the child answered with kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story like this?",
            answer="A ghost is a spooky-looking character that can seem scary at first, even when it is really lonely or sad.",
        ),
        QAItem(
            question="What do the basics mean?",
            answer="The basics are the simple first things you do, like looking, listening, and asking kindly.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when two sides stop being upset and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", prop="lantern", name="Maya", gender="girl", companion="mother", trait="curious"),
    StoryParams(place="hall", prop="blanket", name="Eli", gender="boy", companion="father", trait="thoughtful"),
    StoryParams(place="garden", prop="tea", name="Nora", gender="girl", companion="mother", trait="gentle"),
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

at_risk(P) :- prop(P), prop_kind(P,K), ghost_story_kind(K).
safe_fix(P,R) :- prop(P), fix(P,R), not block(R).
valid(L,P,G) :- location(L), prop(P), gender(G), at_risk(P), safe_fix(P,_), fits_gender(P,G).
valid_story(L,P,G) :- valid(L,P,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.spooky:
            lines.append(asp.fact("spooky", lid))
        if loc.echoes:
            lines.append(asp.fact("echoes", lid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("prop_kind", pid, prop.kind))
        if prop.warm:
            lines.append(asp.fact("fix", pid, "warmth"))
        if prop.lights:
            lines.append(asp.fact("fix", pid, "light"))
        if prop.comfort:
            lines.append(asp.fact("fix", pid, "comfort"))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for g in ["attic", "hall", "garden"]:
        lines.append(asp.fact("ghost_story_kind", "comfort"))
    for pid in PROPS:
        for g in ["girl", "boy"]:
            lines.append(asp.fact("fits_gender", pid, g))
    lines.append(asp.fact("block", "none"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid, loc in LOCATIONS.items():
        for pid, prop in PROPS.items():
            if prop.comfort:
                for g in ["girl", "boy"]:
                    combos.append((lid, pid, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny ghost storyworld with reconciliation and hypothetical fear.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(LOCATIONS))
    prop = args.prop or rng.choice(list(PROPS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, prop=prop, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.place], PROPS[params.prop], params.name, params.gender, params.companion, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.prop}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
