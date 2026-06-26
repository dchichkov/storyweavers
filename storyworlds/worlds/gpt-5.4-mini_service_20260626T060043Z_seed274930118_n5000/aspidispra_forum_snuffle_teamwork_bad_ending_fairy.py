#!/usr/bin/env python3
"""
storyworlds/worlds/aspidispra_forum_snuffle_teamwork_bad_ending_fairy.py
=======================================================================

A small fairy-tale storyworld about a forum, an aspidispra, and a snuffling
teamwork attempt that ends badly.

The story premise:
- In a moonlit fairy forum, the tiny aspidispra wants a silver bell to ring.
- The fairies try teamwork to help, but their plan goes wrong.
- Snuffling in the dark, they lose the bell and end with a bad ending image.

This world is intentionally compact and constraint-driven:
- one central problem
- one teamwork plan
- one failure mode
- one ending that proves the state changed

It supports the standard Storyweavers interface plus an inline ASP twin for the
reasonableness gate and parity checking.
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

# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"fairy", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "king", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Forum:
    place: str = "the moonlit forum"
    glow: str = "silver"
    hush: str = "quiet"
    affords: set[str] = field(default_factory=lambda: {"share", "sing", "carry"})


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    danger: str
    reward: str
    tag: str


@dataclass
class Plan:
    id: str
    helper1: str
    helper2: str
    method: str
    snuffle: str
    failure: str


class World:
    def __init__(self, forum: Forum) -> None:
        self.forum = forum
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        other = World(self.forum)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

FORUMS = {
    "moonforum": Forum(place="the moonlit forum", glow="silver", hush="soft"),
}

ASPIDISPRA = Thing(
    id="aspidispra",
    label="aspidispra",
    phrase="a tiny aspidispra with a bell-bright wish",
    type="sprite",
    danger="lost in the shadows",
    reward="heard by every friend",
    tag="aspidispra",
)

ITEMS = {
    "silver_bell": Thing(
        id="silver_bell",
        label="silver bell",
        phrase="a silver bell on a blue ribbon",
        type="bell",
        danger="dropped into the drain",
        reward="ringing for the forum",
        tag="bell",
    ),
    "lantern": Thing(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a warm wick",
        type="lantern",
        danger="going dark",
        reward="lighting the path",
        tag="light",
    ),
}

PLANS = {
    "snuffle_search": Plan(
        id="snuffle_search",
        helper1="Mira",
        helper2="Pip",
        method="searching together",
        snuffle="snuffling through the reeds",
        failure="they snuffled so hard that the bell slid away",
    ),
}

NAMES = ["Mira", "Pip", "Luna", "Tavi", "Nell", "Faye"]
TRAITS = ["kind", "brave", "gentle", "quick", "careful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    forum: str = "moonforum"
    item: str = "silver_bell"
    name: str = "Mira"
    helper: str = "Pip"
    trait: str = "kind"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reasonableness_gate(forum: Forum, item: Thing) -> bool:
    return forum.place == "the moonlit forum" and item.tag == "bell"


def choose_plan(world: World, hero: Entity, helper: Entity, item: Entity) -> Plan:
    return PLANS["snuffle_search"]


def _append(world: World, text: str) -> None:
    world.say(text)


def build_world(params: StoryParams) -> World:
    forum = FORUMS[params.forum]
    item_def = ITEMS[params.item]

    if not reasonableness_gate(forum, item_def):
        raise StoryError("This fairy tale needs the moonlit forum and a bell-shaped problem.")

    world = World(forum)
    hero = world.add(Entity(id=params.name, kind="character", type="fairy", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="fairy", label=params.helper))
    item = world.add(Entity(
        id=item_def.id,
        kind="thing",
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
    ))
    aspi = world.add(Entity(
        id="aspidispra",
        kind="character",
        type="sprite",
        label="aspidispra",
    ))

    # Act 1
    _append(world, f"Once upon a time, in {forum.place}, there lived {hero.id}, a {params.trait} fairy.")
    _append(world, f"{hero.id} loved the forum because every voice could be heard under the silver glow.")
    _append(world, f"There was also an {aspi.label}, a tiny aspidispra who longed to ring {item.label}.")
    _append(world, f"{aspi.label.capitalize()} kept the bell because it made the forum feel brave and bright.")

    world.para()

    # Act 2
    plan = choose_plan(world, hero, helper, item)
    world.facts["plan"] = plan
    world.facts["forum"] = forum
    world.facts["item"] = item
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["aspi"] = aspi

    _append(world, f"One night, {hero.id} and {helper.id} decided on teamwork.")
    _append(world, f"They tried {plan.method} so the {item.label} could reach the stone stage.")
    _append(world, f"But while they were {plan.snuffle}, {plan.failure}.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    aspi.memes["alarm"] = aspi.memes.get("alarm", 0) + 1
    item.meters["lost"] = item.meters.get("lost", 0) + 1

    world.para()

    # Act 3: bad ending
    _append(world, f"The little bell vanished into the dark cracks below the forum steps.")
    _append(world, f"{aspi.label} snuffled once, then twice, but the sound only echoed back sadly.")
    _append(world, f"In the end, their teamwork did not save the night; {item.label} stayed lost, and the forum grew quiet.")
    _append(world, f"Even so, the moon kept shining over the empty stage.")

    world.facts["bad_ending"] = True
    world.facts["resolved"] = False
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A forum tale is reasonable only if it is the moonlit forum and the problem is a bell.
reasonable_story(F, I) :- forum(F), item(I), moonlit(F), bell(I).

% Teamwork is present when two helpers act together.
teamwork(H1, H2) :- helper(H1), helper(H2), H1 != H2.

% Bad ending occurs when the bell is lost and the night is quiet.
bad_ending(I) :- lost(I), quiet_night.

#show reasonable_story/2.
#show teamwork/2.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("forum", "moonforum"), asp.fact("moonlit", "moonforum"), asp.fact("quiet_night")]
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    lines.append(asp.fact("bell", "silver_bell"))
    for name in NAMES:
        lines.append(asp.fact("helper", name))
    lines.append(asp.fact("lost", "silver_bell"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2.\n#show teamwork/2.\n#show bad_ending/1."))
    atoms = asp.atoms(model, "reasonable_story")
    tb = asp.atoms(model, "teamwork")
    be = asp.atoms(model, "bad_ending")
    return ("moonforum", "silver_bell") in atoms and ("Mira", "Pip") in tb and ("silver_bell",) in be


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fairy tale about aspidispra, a moonlit forum, teamwork, and a bad ending.',
        f"Tell a gentle story where {world.facts['hero'].id} and {world.facts['helper'].id} try to help the aspidispra with the {world.facts['item'].label}.",
        'Write a fairy tale that includes the words "aspidispra", "forum", and "snuffle".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    aspi: Entity = world.facts["aspi"]
    item: Entity = world.facts["item"]

    return [
        QAItem(
            question=f"Who tried teamwork in the moonlit forum?",
            answer=f"{hero.id} and {helper.id} tried teamwork in the moonlit forum to help the aspidispra.",
        ),
        QAItem(
            question=f"What did the aspidispra want to do with the {item.label}?",
            answer=f"The aspidispra wanted to ring the {item.label} so the whole forum could hear it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the {item.label} was lost, the night stayed quiet, and the forum grew still.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something they could not do as well alone.",
        ),
        QAItem(
            question="What does it mean to snuffle?",
            answer="To snuffle is to breathe or search in a noisy, sniffly way, often like a small animal or a child in the dark.",
        ),
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to talk, share ideas, or listen to one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    py = reasonableness_gate(FORUMS["moonforum"], ITEMS["silver_bell"])
    cl = asp_check()
    if py == cl:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld: aspidispra, forum, snuffle, teamwork, bad ending.")
    ap.add_argument("--forum", choices=sorted(FORUMS), default="moonforum")
    ap.add_argument("--item", choices=sorted(ITEMS), default="silver_bell")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
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
    forum = args.forum
    item = args.item
    if not reasonableness_gate(FORUMS[forum], ITEMS[item]):
        raise StoryError("No valid fairy story matches those choices.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(forum=forum, item=item, name=name, helper=helper, trait=trait, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show reasonable_story/2.\n#show teamwork/2.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/2.\n#show teamwork/2.\n#show bad_ending/1."))
        print("reasonable_story:", asp.atoms(model, "reasonable_story"))
        print("teamwork:", asp.atoms(model, "teamwork"))
        print("bad_ending:", asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(forum="moonforum", item="silver_bell", name="Mira", helper="Pip", trait="kind", seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
