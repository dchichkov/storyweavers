#!/usr/bin/env python3
"""
Storyworld: mathematics_cautionary_dialogue_pirate_tale
=======================================================

A small standalone storyworld about a pirate tale with cautionary dialogue
and a math lesson: counting, splitting, and not guessing at sea.
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
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "captain"}
        male = {"boy", "man", "father", "dad", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    affords: set[str] = field(default_factory=lambda: {"counting", "sorting", "sharing"})


@dataclass
class Treasure:
    label: str
    phrase: str
    count: int
    kind: str = "coins"
    plural: bool = True


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]
    kind: str = "tool"


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.harbor)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HARBORS = {
    "harbor": Harbor(place="the harbor", affords={"counting", "sorting", "sharing"}),
    "deck": Harbor(place="the deck", affords={"counting", "sorting", "sharing"}),
    "cove": Harbor(place="the quiet cove", affords={"counting", "sorting"}),
}

TREASURES = {
    "coins": Treasure(label="coins", phrase="a heavy pouch of gold coins", count=12),
    "pearls": Treasure(label="pearls", phrase="a little chest of pearls", count=8),
    "shells": Treasure(label="shells", phrase="a bucket of bright shells", count=10),
}

TOOLS = [
    Tool(id="abacus", label="an abacus", use="count the treasure bead by bead", helps={"counting"}),
    Tool(id="chalk", label="a piece of chalk", use="mark the piles clearly", helps={"sorting"}),
    Tool(id="rope_ring", label="a rope ring", use="keep each share in a neat circle", helps={"sharing"}),
]

CREW_NAMES = ["Mira", "Jory", "Nell", "Pip", "Tess", "Finn"]
PIRATE_TITLES = ["captain", "mate", "pirate", "first mate"]
TRAITS = ["brave", "curious", "careful", "stubborn", "gentle"]


@dataclass
class StoryParams:
    harbor: str
    treasure: str
    hero: str
    title: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is risky when the crew must share it but cannot count or sort it first.
risky(T) :- treasure(T), needs_sharing(T), not has_tool(T).

has_tool(T) :- tool(X), helps(X, counting), used_for(X, T).
has_tool(T) :- tool(X), helps(X, sorting), used_for(X, T).
has_tool(T) :- tool(X), helps(X, sharing), used_for(X, T).

valid_story(H, T) :- harbor(H), treasure(T), risky(T), has_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, h in HARBORS.items():
        lines.append(asp.fact("harbor", hid))
        for a in sorted(h.affords):
            lines.append(asp.fact("affords", hid, a))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("needs_sharing", tid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
    # seed compatible usage facts
    for tid in TREASURES:
        lines.append(asp.fact("used_for", "abacus", tid))
        lines.append(asp.fact("used_for", "chalk", tid))
        lines.append(asp.fact("used_for", "rope_ring", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def treasure_needs_math(treasure: Treasure) -> bool:
    return treasure.count >= 2


def select_tool(treasure: Treasure) -> Optional[Tool]:
    # For this world, a valid fix must help with counting or sorting before sharing.
    for t in TOOLS:
        if "counting" in t.helps:
            return t
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for hid, h in HARBORS.items():
        for tid, tr in TREASURES.items():
            if h.affords and treasure_needs_math(tr) and select_tool(tr):
                combos.append((hid, tid))
    return combos


def explain_rejection(harbor: Harbor, treasure: Treasure) -> str:
    return (
        f"(No story: at {harbor.place}, the crew could not make a careful math problem "
        f"from {treasure.phrase}. The tale needs a treasure worth counting and a tool "
        f"that can help the pirates share it fairly.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def count_story_value(treasure: Treasure) -> tuple[int, int]:
    total = treasure.count
    first_share = total // 2
    second_share = total - first_share
    return first_share, second_share


def tell(harbor: Harbor, treasure: Treasure, hero_name: str, title: str, trait: str) -> World:
    world = World(harbor)
    hero = world.add(Entity(id=hero_name, kind="character", type=title, label=title))
    mate = world.add(Entity(id="mate", kind="character", type="pirate", label="the mate"))
    chest = world.add(Entity(id="treasure", type=treasure.kind, label=treasure.label, phrase=treasure.phrase))

    tool = world.add(Entity(id="abacus", type="tool", label="an abacus"))
    chest.owner = hero.id
    chest.caretaker = mate.id

    first, second = count_story_value(treasure)
    world.facts.update(hero=hero, mate=mate, chest=chest, treasure=treasure, harbor=harbor, tool=tool, split=(first, second))

    # Act 1
    world.say(f"{hero_name} was a {trait} {title} aboard a little pirate ship near {harbor.place}.")
    world.say(f"{hero_name} loved the shiny treasure, especially {treasure.phrase}.")
    world.say(f"One afternoon, {hero_name} said, \"Let's count it now and split it fair!\"")

    # Act 2
    world.para()
    world.say(f"The mate peered at the chest and frowned. \"Don't guess,\" {mate.pronoun('subject')} said.")
    world.say(f"\"If we hurry, we may leave someone with less than {first} coins,\" {hero_name} answered.")
    world.say(f"So {hero_name} took up {tool.label} to {tool.pronoun('object') if False else 'count each piece one by one'}.")
    world.say(f"The crew lined the treasure into two piles and checked the numbers twice.")

    # Act 3
    world.para()
    world.say(f"\"See?\" {hero_name} said. \"{first} for one side and {second} for the other. No one gets cheated.\"")
    world.say(f"The mate nodded. \"Aye, careful counting keeps a ship from quarrels.\"")
    world.say(f"By sunset, the pirates sailed on with fair shares, and the little abacus stayed as tidy as the deck.")

    world.facts.update(tool=tool, split=(first, second), fair=True)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    harbor = f["harbor"]
    return [
        f'Write a short pirate tale for a child where {hero.id} uses mathematics to share {treasure.phrase} fairly at {harbor.place}.',
        f'Tell a cautionary dialogue story about pirates who learn not to guess when counting treasure.',
        f'Write a gentle story with talking pirates, a careful count, and a fair split of treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    treasure = f["treasure"]
    first, second = f["split"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with {treasure.phrase}?",
            answer=f"{hero.id} wanted to count {treasure.label} and split them fair with the crew.",
        ),
        QAItem(
            question=f"Why did the mate warn {hero.id} not to guess?",
            answer=f"The mate warned that guessing could leave someone with less than another pirate, so they needed careful counting.",
        ),
        QAItem(
            question=f"What tool helped the pirates with the numbers?",
            answer=f"{f['tool'].label.capitalize()} helped them count each piece one by one.",
        ),
        QAItem(
            question=f"How many pieces were in the two fair piles?",
            answer=f"The treasure was split into {first} on one side and {second} on the other.",
        ),
    ]
    if f.get("fair"):
        qa.append(
            QAItem(
                question=f"What happened after the pirates checked the math twice?",
                answer=f"They found a fair split, the mate agreed, and the ship sailed on without a quarrel.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an abacus help people do?",
            answer="An abacus helps people count by moving beads or markers so the numbers are easier to see.",
        ),
        QAItem(
            question="Why is it risky to guess when sharing treasure?",
            answer="Guessing can make the shares uneven, and then one person might get less than another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world Q&A ==")
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
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    harbor: str
    treasure: str
    hero: str
    title: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with cautionary dialogue and mathematics.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero", choices=CREW_NAMES)
    ap.add_argument("--title", choices=PIRATE_TITLES)
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
    hid = args.harbor or rng.choice(list(HARBORS))
    tid = args.treasure or rng.choice(list(TREASURES))
    if args.harbor and args.treasure:
        if (hid, tid) not in valid_combos():
            raise StoryError(explain_rejection(HARBORS[hid], TREASURES[tid]))
    return StoryParams(
        harbor=hid,
        treasure=tid,
        hero=args.hero or rng.choice(CREW_NAMES),
        title=args.title or rng.choice(PIRATE_TITLES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(HARBORS[params.harbor], TREASURES[params.treasure], params.hero, params.title, params.trait)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


CURATED = [
    StoryParams(harbor="harbor", treasure="coins", hero="Mira", title="captain", trait="careful"),
    StoryParams(harbor="deck", treasure="pearls", hero="Jory", title="first mate", trait="curious"),
    StoryParams(harbor="cove", treasure="shells", hero="Nell", title="pirate", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid story combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
