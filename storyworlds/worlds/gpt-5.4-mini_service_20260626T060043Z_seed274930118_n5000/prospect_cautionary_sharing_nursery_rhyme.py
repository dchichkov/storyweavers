#!/usr/bin/env python3
"""
storyworlds/worlds/prospect_cautionary_sharing_nursery_rhyme.py
===============================================================

A small story world about a child facing a hopeful prospect, learning caution,
and practicing sharing in a nursery-rhyme style.

The premise: a little child is excited about a fresh prospect, but a friendly
warning helps them slow down and share with care.
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
# Core world model
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("safe", 0.0)
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("bright", 0.0)
        self.meters.setdefault("supply", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("caution", 0.0)
        self.memes.setdefault("care", 0.0)
        self.memes.setdefault("sharing", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Prospect:
    noun: str
    phrase: str
    risk: str
    caution: str
    sharing_act: str
    sharing_step: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affordances={"sharing", "caution"}),
    "playroom": Setting(place="the playroom", indoor=True, affordances={"sharing", "caution"}),
    "garden_gate": Setting(place="the garden gate", indoor=False, affordances={"sharing", "caution"}),
}

PROSPECTS = {
    "cookies": Prospect(
        noun="cookies",
        phrase="a plate of warm cookies",
        risk="they might be snatched or spilled",
        caution="a careful pause keeps crumbs from tumbling",
        sharing_act="share the cookies",
        sharing_step="split the plate with a small smile",
        outcome="each friend got a sweet, tidy treat",
        tags={"food", "sweet", "sharing"},
    ),
    "blocks": Prospect(
        noun="blocks",
        phrase="a bright stack of blocks",
        risk="they might tip and clatter",
        caution="a steady hand keeps the tower from wobbling",
        sharing_act="share the blocks",
        sharing_step="pass the blocks one by one",
        outcome="the tower grew tall with many helping hands",
        tags={"toy", "building", "sharing"},
    ),
    "berries": Prospect(
        noun="berries",
        phrase="a little bowl of berries",
        risk="they might bruise if grabbed too fast",
        caution="gentle fingers keep the fruit neat",
        sharing_act="share the berries",
        sharing_step="offer the bowl around the circle",
        outcome="the bowl stayed bright and everyone had a taste",
        tags={"food", "fruit", "sharing"},
    ),
    "crayons": Prospect(
        noun="crayons",
        phrase="a small tin of crayons",
        risk="they might break if tossed in a hurry",
        caution="slow hands keep colors from snapping",
        sharing_act="share the crayons",
        sharing_step="sort the colors into tiny piles",
        outcome="the colors stayed ready for many pictures",
        tags={"toy", "art", "sharing"},
    ),
}

NAMES = ["Mina", "Toby", "Lily", "Nico", "Penny", "Finn", "Ruby", "Theo"]
PARENT_NAMES = ["Mama", "Papa", "Nana", "Dada"]
TRAITS = ["gentle", "curious", "bright", "small", "cheery"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    prospect: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prospect_is_reasonable(setting: Setting, prospect: Prospect) -> bool:
    return bool(setting.affordances & {"sharing", "caution"}) and bool(prospect.tags & {"sharing"})


def explain_invalid(setting: Setting, prospect: Prospect) -> str:
    return f"(No story: {setting.place} cannot plausibly host a cautionary sharing lesson about {prospect.noun}.)"


# ---------------------------------------------------------------------------
# World narration
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, prospect: Prospect) -> None:
    world.say(
        f"Once in {world.setting.place}, little {child.name_word()} had a bright little prospect: "
        f"{prospect.phrase}."
    )
    world.say(
        f"{child.name_word()} loved the look of it, and {child.pronoun('possessive')} heart went "
        f"drip-drip-dance with joy."
    )


def caution(world: World, parent: Entity, child: Entity, prospect: Prospect) -> None:
    child.memes["caution"] += 1
    child.meters["risk"] += 1
    world.say(
        f"But {parent.name_word()} said, “Easy now, easy now; {prospect.caution}.”"
    )
    world.say(
        f"{child.name_word()} slowed down, for the little rhyme in the warning felt wise and true."
    )


def share(world: World, child: Entity, other: Entity, prospect: Prospect) -> None:
    child.memes["sharing"] += 1
    child.memes["care"] += 1
    child.memes["joy"] += 1
    other.memes["joy"] += 1
    world.say(
        f"So {child.name_word()} chose to {prospect.sharing_act}, and {other.name_word()} smiled so wide."
    )
    world.say(
        f"Together they {prospect.sharing_step}, and the worry-frown went skipping far away."
    )


def ending(world: World, child: Entity, prospect: Prospect) -> None:
    child.meters["safe"] += 1
    world.say(
        f"In the end, {prospect.outcome}, and {child.name_word()} learned that careful sharing is a merry sort of magic."
    )
    world.say(
        f"{child.name_word()} tucked the lesson close: when a prospect looks sweet, a gentle pause can make it last."
    )


def tell(setting: Setting, prospect: Prospect, name: str = "Mina", parent_name: str = "Mama", trait: str = "gentle") -> World:
    world = World(setting=setting)
    child = world.add(Entity(id=name, kind="character", type="girl", label=name))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", label=parent_name))
    friend = world.add(Entity(id="Friend", kind="character", type="boy", label="a friend"))

    child.memes["joy"] += 1
    child.meters["bright"] += 1

    introduce(world, child, prospect)
    world.para()
    caution(world, parent, child, prospect)
    share(world, child, friend, prospect)
    world.para()
    ending(world, child, prospect)

    world.facts.update(
        child=child,
        parent=parent,
        friend=friend,
        prospect=prospect,
        trait=trait,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prospect = f["prospect"]
    return [
        f'Write a nursery-rhyme style story about {child.name_word()} and a hopeful prospect involving {prospect.noun}.',
        f"Tell a cautionary sharing story where {child.name_word()} learns to slow down before sharing {prospect.noun}.",
        f"Write a gentle rhyme in which a child with a bright prospect chooses careful sharing over hurry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prospect = f["prospect"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"What was {child.name_word()}'s bright prospect in the story?",
            answer=f"{child.name_word()}'s bright prospect was {prospect.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.name_word()} speak in a careful way?",
            answer=f"{parent.name_word()} wanted {child.name_word()} to be cautious, because {prospect.risk}.",
        ),
        QAItem(
            question=f"How did {child.name_word()} solve the problem with {prospect.noun}?",
            answer=f"{child.name_word()} chose to share {prospect.noun} with {friend.name_word()} instead of rushing.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the worry turned into sharing, and the whole little group enjoyed {prospect.outcome}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prospect = f["prospect"]
    out = [
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before you act, so you can avoid a hurt or a mess.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you, so everyone can take part.",
        ),
        QAItem(
            question=f"Why is {prospect.noun} something a child can share?",
            answer=f"{prospect.noun.capitalize()} are the kind of thing children can pass around, divide up, or enjoy together.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_ok(S) :- setting(S).
prospect_ok(P) :- prospect(P).
cautionary_story(S,P) :- setting_ok(S), prospect_ok(P), affords(S,sharing), affords(S,caution), shares(P).

#show cautionary_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for pid, prospect in PROSPECTS.items():
        lines.append(asp.fact("prospect", pid))
        lines.append(asp.fact("shares", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models() -> list[list]:
    import storyworlds.asp as asp
    return asp.solve(asp_program("#show cautionary_story/2."), models=1)


def asp_verify() -> int:
    python_set = {(s, p) for s, setting in SETTINGS.items() for p, pros in PROSPECTS.items() if prospect_is_reasonable(setting, pros)}
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show cautionary_story/2."))
    clingo_set = set(asp.atoms(model, "cautionary_story"))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python reasonableness gate ({len(clingo_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation and output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary sharing nursery-rhyme story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prospect", choices=PROSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    setting_id = args.setting or rng.choice(list(SETTINGS))
    prospect_id = args.prospect or rng.choice(list(PROSPECTS))
    setting = SETTINGS[setting_id]
    prospect = PROSPECTS[prospect_id]
    if not prospect_is_reasonable(setting, prospect):
        raise StoryError(explain_invalid(setting, prospect))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, prospect=prospect_id, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROSPECTS[params.prospect], params.name, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
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


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, prospect in PROSPECTS.items():
            if prospect_is_reasonable(setting, prospect):
                out.append((sid, pid))
    return out


CURATED = [
    StoryParams(setting="nursery", prospect="cookies", name="Mina", parent="Mama", trait="gentle"),
    StoryParams(setting="playroom", prospect="blocks", name="Toby", parent="Papa", trait="curious"),
    StoryParams(setting="garden_gate", prospect="berries", name="Ruby", parent="Nana", trait="cheery"),
    StoryParams(setting="nursery", prospect="crayons", name="Theo", parent="Dada", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show cautionary_story/2."))
        pairs = sorted(set(asp.atoms(model, "cautionary_story")))
        print(f"{len(pairs)} compatible setting/prospect pairs:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
