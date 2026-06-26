#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chagrined_minor_barracuda_magic_bravery_surprise_rhyming.py
======================================================================================================

A standalone story world for a small rhyming ocean tale.

Premise:
- A minor barracuda loves sparkle, song, and small magic tricks.
- He wants to use a magic pearl to impress the reef.
- A surprise current scatters the pearls, leaving him chagrined.
- Brave help and a clever rhyme turn the mishap into a happy show.

This world is intentionally tiny and constraint-checked:
- only a few plausible story variants
- explicit invalid choices raise StoryError
- the world model tracks physical meters and emotional memes
- prose is generated from the simulated state, not from a frozen template
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"barracuda", "fish", "boy"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in {"girl", "mermaid"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Reef:
    name: str = "the reef"
    place: str = "the reef"
    sparkle: bool = True
    current: str = "gentle"


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    kind: str
    glow: str
    guards: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    act: str
    tail: str
    kind: str = "helper"


@dataclass
class World:
    reef: Reef
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    name: str
    gender: str
    charm: str
    helper: str
    current: str
    seed: Optional[int] = None


HERO_NAMES = ["Nico", "Marin", "Toby", "Mina", "Luna", "Cleo"]
HELPER_NAMES = ["Coral", "Pippa", "Dory", "Bram", "Sage"]
CURRENT_CHOICES = ["gentle", "sudden", "swirly"]


CHARMS = {
    "pearl": Charm(
        id="pearl",
        label="magic pearl",
        phrase="a tiny magic pearl",
        kind="magic",
        glow="glimmered like a moonlit bead",
        guards={"surprise"},
    ),
    "shell": Charm(
        id="shell",
        label="magic shell",
        phrase="a shiny magic shell",
        kind="magic",
        glow="sparkled with a silver hum",
        guards={"surprise"},
    ),
    "star": Charm(
        id="star",
        label="magic star",
        phrase="a little magic star",
        kind="magic",
        glow="twinkled with a warm bright gleam",
        guards={"surprise"},
    ),
}

HELPERS = {
    "breeze": Helper(
        id="breeze",
        label="the brave breeze",
        act="helped the tiny pearls spin in a tidy ring",
        tail="fanned the glitter back into a neat bright line",
    ),
    "crab": Helper(
        id="crab",
        label="a brave crab",
        act="held the shell steady with two careful claws",
        tail="clacked the beat while the sparkle stayed neat",
    ),
    "ray": Helper(
        id="ray",
        label="a brave ray",
        act="guided the shine with a smooth blue sway",
        tail="swept the swirl into a merry display",
    ),
}


def rhymed_pair(a: str, b: str) -> str:
    return f"{a} {b}"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_surprise(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    charm = world.get("charm")
    if hero.meters.get("magic", 0) >= THRESHOLD and world.reef.current != "gentle":
        if hero.meters.get("surprised", 0) >= THRESHOLD:
            return out
        hero.meters["surprised"] = 1
        hero.memes["chagrin"] = hero.memes.get("chagrin", 0) + 1
        charm.meters["scattered"] = 1
        out.append("The current surprised the show and scattered the glow.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes.get("chagrin", 0) >= THRESHOLD and helper.meters.get("helped", 0) >= THRESHOLD:
        if hero.memes.get("bravery", 0) >= THRESHOLD:
            return out
        hero.memes["bravery"] = 1
        hero.memes["chagrin"] = 0
        out.append("With brave breath, the hero chose the bright next step.")
    return out


CAUSAL_RULES = [Rule("surprise", _r_surprise), Rule("bravery", _r_bravery)]


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


def can_story(params: StoryParams) -> bool:
    return params.charm in CHARMS and params.helper in HELPERS and params.current in CURRENT_CHOICES


def build_world(params: StoryParams) -> World:
    if not can_story(params):
        raise StoryError("The requested story parts do not fit this tiny reef tale.")

    world = World(Reef(current=params.current))
    hero = world.add(Entity(id="hero", kind="character", type="barracuda", label=params.name))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=CHARMS[params.charm].label, phrase=CHARMS[params.charm].phrase))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=HELPERS[params.helper].label))

    world.facts.update(hero=hero, charm=charm, helper=helper, params=params)

    hero.meters["magic"] = 1
    hero.memes["pride"] = 1
    charm.meters["glow"] = 1

    world.say(f"Near the reef, {hero.label} was a minor barracuda with a grin so bold.")
    world.say(f"He loved {charm.phrase}, because it {CHARMS[params.charm].glow}.")
    world.say(f"Each day he would practice a soft little trick, bright as gold.")

    world.para()
    world.say(f"One day he swam to {world.reef.place}, where the water hummed and the bubbles blew.")
    world.say(f"He wanted to show his {charm.label} trick, neat and sweet, in a silver-blue view.")
    if params.current == "sudden":
        world.say("But a sudden current swished the sea and gave the plan a spin.")
    elif params.current == "swirly":
        world.say("But a swirly current whisked the waves and made the bubbles twirl within.")
    else:
        world.say("Even a gentle current can nudge a trick the wrong way, as he would soon know.")

    hero.meters["magic"] += 1
    world.say(f"He flicked his fins and let the {charm.label} shine, singing, 'Gleam, beam, dream!'")
    propagate(world)

    world.para()
    if charm.meters.get("scattered"):
        world.say(f"The glow flew wide and the little barracuda felt chagrined, not keen.")
        world.say(f"But then {HELPERS[params.helper].label} came brave and calm, with a helpful routine.")
        helper.meters["helped"] = 1
        helper.memes["bravery"] = 1
        world.say(f"{HELPERS[params.helper].act.capitalize()}, and that made the shining scene.")
        world.say("The hero took a steady breath and tried one more tune.")
        hero.memes["bravery"] = 1
        hero.meters["magic"] += 1
        propagate(world)
        world.say(f"Together they made the sparkle dance, a merry moonbeam moon.")
        world.say(f"The reef cheered for the little barracuda, who bowed with a grin and no gloom.")
    else:
        world.say("The glow stayed tidy, so he smiled and gave the reef a joyful swoon.")
        world.say(f"{HELPERS[params.helper].label.capitalize()} still clapped along, because brave friends are always in tune.")
        hero.memes["bravery"] = 1

    world.facts["resolved"] = True
    return world


def story_text(world: World) -> str:
    return world.render()


def story_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short rhyming story for a child about a minor barracuda named {p.name} who uses magic and bravery after a surprise in the sea.',
        f'Create a gentle rhyming tale where {p.name} the barracuda is chagrined by an ocean surprise, then finds courage with help.',
        f'Write a tiny ocean story with magic, bravery, and surprise that ends happily near the reef.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    charm = world.facts["charm"]
    helper = world.facts["helper"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.name}, a minor barracuda who loves {charm.label} magic near the reef.",
        ),
        QAItem(
            question=f"What made {p.name} feel chagrined?",
            answer=f"A sudden surprise in the water scattered the glow and made {p.name} feel chagrined.",
        ),
        QAItem(
            question=f"Who helped the barracuda?",
            answer=f"{helper.label.capitalize()} helped {p.name} turn the mishap into a happy show.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.name} feeling brave, using magic again, and making the reef shine bright.",
        ),
    ]
    if hero.memes.get("chagrin", 0) == 0:
        qa.append(
            QAItem(
                question="What changed after the surprise?",
                answer="The chagrin faded, and bravery took its place so the show could go on.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barracuda?",
            answer="A barracuda is a sleek ocean fish with a long body and a fast swimming style.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is something unusual and wondrous that can make surprising things happen.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous or unsure.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you were not ready for it.",
        ),
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% The hero is chagrined when a surprise current disrupts a magic show.
chagrined(hero) :- magic(hero), surprise(current), scattered(charm).

% Bravery can resolve chagrin when a helper lends support.
brave(hero) :- chagrined(hero), helped(helper).
resolved(hero) :- brave(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("magic", "hero"))
    lines.append(asp.fact("surprise", "current"))
    lines.append(asp.fact("helped", "helper"))
    lines.append(asp.fact("scattered", "charm"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show brave/1.\n#show chagrined/1."))
    atoms = set(asp.atoms(model, "resolved"))
    if ("hero",) in atoms:
        print("OK: ASP model supports the story resolution.")
        return 0
    print("MISMATCH: ASP model did not resolve as expected.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming reef story about a minor barracuda, magic, bravery, and surprise.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--current", choices=CURRENT_CHOICES)
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
    charm = args.charm or rng.choice(list(CHARMS))
    helper = args.helper or rng.choice(list(HELPERS))
    current = args.current or rng.choice(CURRENT_CHOICES)
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(HERO_NAMES if gender == "boy" else HERO_NAMES)
    return StoryParams(name=name, gender=gender, charm=charm, helper=helper, current=current)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=story_prompts(world),
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


CURATED = [
    StoryParams(name="Nico", gender="boy", charm="pearl", helper="crab", current="sudden"),
    StoryParams(name="Mina", gender="girl", charm="shell", helper="ray", current="swirly"),
    StoryParams(name="Toby", gender="boy", charm="star", helper="breeze", current="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1.\n#show brave/1.\n#show chagrined/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1.\n#show brave/1.\n#show chagrined/1."))
        print("ASP atoms:", asp.atoms(model, "resolved"), asp.atoms(model, "brave"), asp.atoms(model, "chagrined"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
