#!/usr/bin/env python3
"""
A tiny storyworld for a comedic jewelry-sharing mystery with evidence and reconciliation.

Seed premise:
- A child wants to wear shiny jewelry.
- Someone else borrows it, leaving clues.
- The evidence leads to a funny misunderstanding.
- The characters share the jewelry and make up.

The story should feel concrete and state-driven: possession changes, clues appear,
feelings shift, and the ending proves the reconciliation happened.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    jewelry: str
    hero: str
    hero_type: str
    other: str
    other_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


def note_state(world: World, msg: str) -> None:
    world.trace.append(msg)


def _share_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    other = world.get("other")
    jewel = world.get("jewel")
    if hero.memes.get("share", 0) < 1:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jewel.shared_with.update({hero.id, other.id})
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    other.memes["joy"] = other.memes.get("joy", 0) + 1
    hero.memes["grudge"] = 0
    other.memes["grudge"] = 0
    out.append("They agreed to share the jewelry and laughed at the silly fuss.")
    note_state(world, "sharing resolved the argument")
    return out


def _reconcile_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    other = world.get("other")
    clue = world.facts.get("evidence_found", False)
    if not clue:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    if hero.memes.get("surprise", 0) < 1 or other.memes.get("embarrass", 0) < 1:
        return out
    world.fired.add(sig)
    hero.memes["grudge"] = 0
    other.memes["grudge"] = 0
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    other.memes["love"] = other.memes.get("love", 0) + 1
    out.append("They made up, because the clue turned the whole mystery into a joke.")
    note_state(world, "reconciliation completed")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_share_rule, _reconcile_rule):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


SETTING = Setting(place="the bedroom", affords={"getting-ready", "pretend-detective"})
JEWELRY = {
    "bracelet": {"label": "sparkly bracelet", "kind": "bracelet"},
    "necklace": {"label": "tiny silver necklace", "kind": "necklace"},
    "earrings": {"label": "flower earrings", "kind": "earrings"},
}
NAMES_GIRL = ["Mina", "Lily", "Ruby", "Nora", "Zoe"]
NAMES_BOY = ["Finn", "Theo", "Ben", "Max", "Owen"]
OTHER_NAMES = ["Ava", "Milo", "Iris", "Jasper", "Penny"]


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    other = world.add(Entity(id="other", kind="character", type=params.other_type, label=params.other))
    jewel = world.add(Entity(id="jewel", type=params.jewelry, label=JEWELRY[params.jewelry]["label"], owner=hero.id))

    hero.memes["want"] = 1
    hero.memes["grudge"] = 0
    other.memes["curious"] = 1
    other.memes["grudge"] = 0
    world.facts.update(hero=hero, other=other, jewel=jewel, setting=SETTING)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    other = world.get("other")
    jewel = world.get("jewel")

    world.say(f"{hero.label} loved {jewel.label}, because it glittered like a tiny moon.")
    world.say(f"One afternoon, {hero.label} put it on and twirled in {world.setting.place}.")
    world.para()
    world.say(f"Then {other.label} spotted it and said, \"Can I try it for one minute?\"")
    world.say(f"{hero.label} frowned and said no, so the room got as quiet as a held breath.")
    hero.memes["grudge"] = 1
    other.memes["embarrass"] = 1
    world.para()

    world.say("A funny clue appeared next: a ribbon of glitter on the pillow and a sticky note that said QRS.")
    world.facts["evidence_found"] = True
    hero.memes["surprise"] = 1
    other.memes["embarrass"] = 1
    world.say(f"{hero.label} and {other.label} followed the evidence like two very serious detectives.")
    world.say(f"It led them to the toy cat, which was wearing the jewelry and looking far too pleased with itself.")
    world.say(f"{other.label} burst out laughing and admitted, \"I only borrowed it to show the cat how shiny it was.\"")
    hero.memes["share"] = 1
    propagate(world)
    world.para()
    world.say(f"In the end, {hero.label} and {other.label} took turns wearing {jewel.label}, and the cat got a ribbon instead.")
    world.say("They were still giggling when bedtime came, and the little clue note stayed on the dresser like a trophy.")


def select_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    jewelry = args.jewelry or rng.choice(list(JEWELRY))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    other_type = args.other_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    other = args.other or rng.choice([n for n in OTHER_NAMES if n != hero])
    place = args.place or SETTING.place
    return StoryParams(place=place, jewelry=jewelry, hero=hero, hero_type=hero_type, other=other, other_type=other_type)


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    other = world.get("other")
    jewel = world.get("jewel")
    return [
        QAItem(
            question=f"What shiny thing did {hero.label} love at the start?",
            answer=f"{hero.label} loved the {jewel.label}, because it glittered like a tiny moon.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} and {other.label} solve the problem?",
            answer="They found a glittery ribbon and a note that said QRS, which pointed them toward the toy cat.",
        ),
        QAItem(
            question=f"How did {hero.label} and {other.label} fix the problem at the end?",
            answer=f"They shared the {jewel.label}, took turns wearing it, and laughed together after the misunderstanding.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is evidence in a mystery?",
            answer="Evidence is a clue or fact that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why can jewelry be shared?",
            answer="Jewelry can be shared when people take turns and handle it carefully so everyone gets a chance to enjoy it.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after an argument and becoming friendly again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    jewel = world.get("jewel")
    return [
        f"Write a short comedy story about {hero.label}, a {hero.type}, and a {jewel.label} that ends with sharing.",
        "Tell a playful story where evidence helps two kids solve a jewelry mix-up and make up.",
        "Write a child-friendly mystery about a lost piece of jewelry, a funny clue, and a happy reconciliation.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired={sorted(world.fired)}")
    lines.extend(world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about jewelry, evidence, sharing, and reconciliation.")
    ap.add_argument("--place", choices=[SETTING.place])
    ap.add_argument("--jewelry", choices=sorted(JEWELRY))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-type", choices=["girl", "boy"])
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
    return select_params(args, rng)


ASP_RULES = r"""
chosen_jewelry(J) :- jewelry(J).
shared(J) :- evidence_found, chosen_jewelry(J).
reconciled :- shared(J).
valid_story(P, J) :- setting(P), jewelry(J), reconciled.
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", SETTING.place)]
    for jid in JEWELRY:
        lines.append(asp.fact("jewelry", jid))
    lines.append(asp.fact("evidence_found"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(SETTING.place, j) for j in JEWELRY}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story seeds.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, jid in enumerate(sorted(JEWELRY)):
            params = StoryParams(
                place=SETTING.place,
                jewelry=jid,
                hero=NAMES_GIRL[i % len(NAMES_GIRL)],
                hero_type="girl",
                other=OTHER_NAMES[i % len(OTHER_NAMES)],
                other_type="boy",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
