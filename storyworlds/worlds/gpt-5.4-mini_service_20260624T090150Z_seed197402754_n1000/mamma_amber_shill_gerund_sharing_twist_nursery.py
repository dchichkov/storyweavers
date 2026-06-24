#!/usr/bin/env python3
"""
storyworlds/worlds/mamma_amber_shill_gerund_sharing_twist_nursery.py
=====================================================================

A tiny nursery-rhyme story world about mamma, amber, and a shill-gerund twist
around sharing.

Seed tale idea:
---
Mamma found an amber shill, bright as honey in the sun. A child loved it at once
and did not want to share. But the shill got twisty in small hands. Mamma showed
how to share it gently, untwist the ribbon, and make the day sweet again.

World model:
---
- The child loves a bright amber trinket.
- Sharing is a social action that can raise or soften feelings.
- A twist can tangle the trinket, making it harder to keep neat.
- Mamma guides the child toward a kinder choice.
- The ending image proves the change: the amber thing is shared, untwisted,
  and the child feels warm instead of tight-fisted.

This script follows the storyworld contract with:
- StoryParams and registries
- build_parser, resolve_params, generate, emit, main
- prose generation driven by a simulated world model
- inline ASP_RULES plus asp_facts() for parity checks
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mamma", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    twist: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    softening: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.twist_level: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.twist_level = self.twist_level
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["pulled"] < THRESHOLD:
            continue
        if ent.id == "amber":
            sig = ("twist", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["twisted"] += 1
            world.twist_level += 1
            out.append("The amber shill got a twist in it.")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    mamma = world.entities.get("mamma")
    amber = world.entities.get("amber")
    if not child or not mamma or not amber:
        return out
    if child.memes["stingy"] < THRESHOLD:
        return out
    if world.twist_level < THRESHOLD:
        return out
    sig = ("soften", "sharing")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["stingy"] = 0.0
    child.memes["warmth"] += 1
    mamma.memes["pride"] += 1
    amber.meters["twisted"] = max(0.0, amber.meters["twisted"] - 1)
    world.twist_level = max(0.0, world.twist_level - 1)
    out.append("The twist grew small when mamma showed a sharing way.")
    return out


CAUSAL_RULES = [Rule("twist", _r_twist), Rule("soften", _r_soften)]


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


def share_item(world: World, child: Entity, mamma: Entity, amber: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the nursery, {child.id} found the {amber.label} bright and warm, "
        f"like a drop of morning sun."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to keep {amber.it()} close and "
        f"would not share at first."
    )


def request_share(world: World, mamma: Entity, child: Entity, amber: Entity) -> None:
    child.memes["stingy"] += 1
    world.say(
        f"Then {mamma.id} sang, \"A sweet thing shines sweeter when little hands "
        f"can share.\""
    )
    world.say(
        f"{child.id} frowned, and the little {amber.label} began to feel tight in "
        f"{child.pronoun('possessive')} grip."
    )


def pull_twist(world: World, child: Entity, amber: Entity) -> None:
    child.meters["pulled"] += 1
    amber.meters["pulled"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{child.id} pulled the {amber.label} one way, then the other, "
        f"and it got all twisty."
    )


def offer_fix(world: World, mamma: Entity, child: Entity, amber: Entity, gear: Gear) -> None:
    world.say(
        f"{mamma.id} smiled and said, \"{gear.prep}, and we can share the bright "
        f"little {amber.label} together.\""
    )
    child.memes["stingy"] += 0  # keep explicit state link; softening comes by rule


def accept_share(world: World, child: Entity, mamma: Entity, amber: Entity, gear: Gear) -> None:
    child.memes["joy"] += 1
    child.memes["stingy"] = 0.0
    world.say(
        f"{child.id}'s face went round and glad. \"Yes, mamma,\" {child.pronoun()} "
        f"said, and {child.pronoun()} held the {amber.label} more gently."
    )
    world.say(
        f"They {gear.tail}. Soon the {amber.label} was shared in turns, the twist "
        f"was gone, and the nursery felt as soft as a song."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Nell", child_type: str = "girl",
         mamma_name: str = "Mamma") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, label=child_name,
    ))
    mamma = world.add(Entity(
        id="mamma", kind="character", type="mamma", label=mamma_name,
    ))
    amber = world.add(Entity(
        id="amber", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, caretaker=mamma.id,
        plural=prize_cfg.plural,
    ))

    share_item(world, child, mamma, amber)
    world.para()
    request_share(world, mamma, child, amber)
    pull_twist(world, child, amber)
    world.para()

    gear = GEAR[0]
    offer_fix(world, mamma, child, amber, gear)
    propagate(world, narrate=True)
    accept_share(world, child, mamma, amber, gear)

    world.facts.update(
        child=child,
        mamma=mamma,
        amber=amber,
        activity=activity,
        gear=gear,
        twist=world.twist_level >= THRESHOLD,
        resolved=True,
    )
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"sharing_twist"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"sharing_twist"}),
    "windowseat": Setting(place="the window seat", indoor=True, affords={"sharing_twist"}),
}

ACTIVITIES = {
    "sharing_twist": Activity(
        id="sharing_twist",
        verb="share the amber shill",
        gerund="sharing the amber shill",
        rush="grab the amber shill and tug it close",
        twist="twist it between small hands",
        keyword="amber",
        tags={"sharing", "twist", "amber", "nursery"},
    )
}

PRIZES = {
    "amber": Prize(
        label="amber shill",
        phrase="a bright amber shill",
        type="toy",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="ribbon",
        label="a soft ribbon",
        prep="let us tie a soft ribbon around it",
        tail="passed it back and forth by the ribbon",
        softening="sharing",
    )
]

NAMES = ["Nell", "Mina", "Pip", "Bess", "Lina", "Wren", "Ivy", "Rosie"]
TRAITS = ["gentle", "cheery", "curious", "busy", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    child_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [
        ("What does it mean to share?",
         "To share means to let someone else use or enjoy something too."),
    ],
    "twist": [
        ("What is a twist?",
         "A twist is a turn that makes something bend or tangle a little."),
    ],
    "amber": [
        ("What is amber?",
         "Amber is a golden-colored gem-like resin that can look warm and shiny."),
    ],
    "nursery": [
        ("What is a nursery?",
         "A nursery is a cozy room for little children to play, rest, or hear stories."),
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a nursery-rhyme story about a child, mamma, and an amber shill '
        'that begins with sharing and ends with a gentle twist being fixed.',
        f"Tell a sweet story where {child.id} tries to keep the amber shill, "
        f"then learns to share it with mamma's help.",
        "Make the story sing-song and child-friendly, with a bright amber thing, "
        "a small twist, and a kinder ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    amber = f["amber"]
    mamma = f["mamma"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} find in the nursery?",
            answer=f"{child.id} found the {amber.label}, a bright little thing like honey in the sun.",
        ),
        QAItem(
            question=f"Why did {mamma.id} ask {child.id} to share the {amber.label}?",
            answer=(
                f"{mamma.id} wanted the {amber.label} to be enjoyed kindly, not gripped so hard "
                f"that it got twisty in {child.id}'s hands."
            ),
        ),
        QAItem(
            question=f"What changed after {child.id} learned to share?",
            answer=(
                f"{child.id} grew happier and gentler, and the {amber.label} was passed back "
                f"and forth instead of being tugged tight."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for key in ["sharing", "twist", "amber", "nursery"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  twist_level={world.twist_level}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
twist(Amb) :- pulled(Amb), amber(Amb).
softened(Child, Amb) :- stingy(Child), twist(Amb), mamma(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_label", pid, p.label))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("gear_label", g.id, g.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme story world: mamma, amber, and a sharing twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, child_type=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.child_type)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show tag/2."))
    asp_tags = set(asp.atoms(model, "tag"))
    py_tags = {(a, t) for a, act in ACTIVITIES.items() for t in act.tags}
    if asp_tags == py_tags:
        print(f"OK: clingo gate matches registries ({len(asp_tags)} tags).")
        return 0
    print("MISMATCH between clingo and python registries.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show tag/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show tag/2."))
        tags = sorted(set(asp.atoms(model, "tag")))
        print(f"{len(tags)} ASP tags loaded.")
        for t in tags:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=pr, name="Nell", child_type="girl", trait="gentle"))
                   for p, a, pr in valid_combos()]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
