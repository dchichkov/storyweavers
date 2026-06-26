#!/usr/bin/env python3
"""
storyworlds/worlds/material_ize_aya_reconciliation_bravery_tall_tale.py
=======================================================================

A compact tall-tale story world about Aya, a swaggering wind, a missing prize,
and a brave reconciliation that makes the whole town feel wider.

Premise
-------
Aya lives in a little prairie town where big feelings travel fast on the wind.
One day, a sky-ribbon prize gets blown away during a public show. Aya wants to
prove bravery by chasing it alone, but the chase turns into a misunderstanding:
a friend thinks Aya is pushing them aside, and the pair quarrel under a huge
blue sky.

Turn
----
Aya finally says the plain brave thing: an apology. In this world, apology is
not weak; it is a bridge. Once Aya and the friend reconcile, they work together.
The missing prize is recovered, and the town gets its ending image: dust in the
sun, laughter in the breeze, and a little word -- "material-ize" -- that becomes
a reminder that courage can make help appear.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --seed, -n, --all
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    moved: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    sky: str
    signature: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    at_risk_from: str
    location: str


@dataclass
class Trouble:
    id: str
    verb: str
    rush: str
    consequence: str
    spark: str
    zone: str


@dataclass
class Bond:
    id: str
    label: str
    use: str
    result: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "plain": Place("plain", "the wide prairie", "blue", "dust and sun"),
    "fair": Place("fair", "the county fairgrounds", "bright", "music and popcorn"),
    "hill": Place("hill", "the hill above town", "windy", "grass and sky"),
}

TROUBLES = {
    "kite": Trouble(
        "kite",
        verb="chase the runaway kite",
        rush="run after the kite",
        consequence="the kite would sail farther and farther away",
        spark="a sudden wind snatched the ribbon",
        zone="sky",
    ),
    "banner": Trouble(
        "banner",
        verb="catch the flying banner",
        rush="dash after the banner",
        consequence="the banner would tangle in the fair pole",
        spark="a gust lifted the banner high",
        zone="sky",
    ),
    "pie": Trouble(
        "pie",
        verb="save the blueberry pie",
        rush="hurry after the pie",
        consequence="the pie would topple into the dust",
        spark="a wobble in the picnic table",
        zone="ground",
    ),
}

PRIZES = {
    "ribbon": Prize(
        "ribbon",
        label="sky ribbon",
        phrase="a bright sky ribbon for the tallest dance",
        at_risk_from="wind",
        location="sky",
    ),
    "cup": Prize(
        "cup",
        label="blue cup",
        phrase="a blue glass cup with a gold star",
        at_risk_from="wind",
        location="ground",
    ),
}

BONDS = {
    "rope": Bond("rope", "a long rope", "pull together", "a steady bridge formed"),
    "ladder": Bond("ladder", "a tall ladder", "reach together", "the climb became safe"),
    "apology": Bond("apology", "an honest apology", "bridge hurt feelings", "the quarrel melted away"),
}

NAMES = ["Aya", "Milo", "June", "Tessa", "Otis", "Pia"]
TRAIL_NAMES = ["Buck", "Dora", "Fern", "Gale", "Nell"]

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    trouble: str
    prize: str
    friend_name: str
    hero_name: str = "Aya"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def _narrate_setup(world: World, hero: Entity, friend: Entity, trouble: Trouble, prize: Prize) -> None:
    world.say(
        f"{hero.id} was a brave little {hero.type} who lived where the sky seemed to stretch clear to the edge of tomorrow."
    )
    world.say(
        f"{hero.id} and {friend.id} both loved the town's big shows, especially when the {prize.label} flashed high above the crowd."
    )
    world.say(
        f"That day, {trouble.spark}, and the {prize.label} slipped loose before the last cheer had even landed."
    )


def _narrate_chase(world: World, hero: Entity, friend: Entity, trouble: Trouble, prize: Prize) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} said {trouble.verb}, because {hero.id} had the kind of courage that makes a child stand a little taller than a fencepost."
    )
    world.say(
        f"{friend.id} called after {hero.id}, but {hero.id} was already {trouble.rush}, and the wind kept a blustering pace ahead."
    )
    world.say(
        f"Then {friend.id} thought {hero.id} was trying to do everything alone, and that thought pricked the air like a thorn."
    )
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    friend.memes["hurt"] = friend.memes.get("hurt", 0) + 1


def _narrate_reconciliation(world: World, hero: Entity, friend: Entity, bond: Bond, prize: Prize) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["sorry"] = hero.memes.get("sorry", 0) + 1
    friend.memes["forgive"] = friend.memes.get("forgive", 0) + 1
    world.say(
        f"At last, {hero.id} stopped, took a breath, and said the brave thing: 'I was wrong to race ahead. Will you help me?'"
    )
    world.say(
        f"That apology was like a bridge thrown over a creek, and {friend.id}'s hard face softened right away."
    )
    world.say(
        f"{friend.id} nodded, and together they used {bond.label} to {bond.use}, so {bond.result}."
    )
    prize_ent = world.get(prize.id)
    prize_ent.moved = True
    prize_ent.location = "safe in Aya's hands"
    world.say(
        f"Before the sun slipped down, they brought back the {prize.label}, and the town laughed as if the whole prairie had learned a new song."
    )
    world.say(
        f"From then on, whenever someone needed help, {hero.id} liked to whisper the old tall-tale word, 'material-ize' -- because brave hands and forgiving hearts can make good things appear."
    )


# ---------------------------------------------------------------------------
# Tell / generate
# ---------------------------------------------------------------------------
def tell(place: Place, trouble: Trouble, prize: Prize, hero_name: str, friend_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy"))
    prize_ent = world.add(Entity(id=prize.id, kind="thing", type="prize", label=prize.label, location=place.signature))
    world.facts.update(hero=hero, friend=friend, prize=prize, trouble=trouble, place=place, prize_ent=prize_ent)

    _narrate_setup(world, hero, friend, trouble, prize)
    world.para()
    _narrate_chase(world, hero, friend, trouble, prize)
    world.para()
    bond = BONDS["apology"] if trouble.id in {"kite", "banner"} else BONDS["rope"]
    _narrate_reconciliation(world, hero, friend, bond, prize)
    world.facts["bond"] = bond
    return world


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combo(place: str, trouble: str, prize: str) -> bool:
    # We only tell stories where the trouble and prize genuinely fit.
    if trouble in {"kite", "banner"} and prize == "ribbon":
        return True
    if trouble == "pie" and prize == "cup":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TROUBLES:
            for pr in PRIZES:
                if valid_combo(p, t, pr):
                    out.append((p, t, pr))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall-tale story for a child named {f["hero"].id} in {f["place"].label} about {f["trouble"].verb}, courage, and forgiveness.',
        f'Write a gentle prairie tale where {f["hero"].id} and {f["friend"].id} lose a {f["prize"].label} and then reconcile.',
        f'Create a child-friendly story that includes the word "material-ize" and ends with friends helping each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, trouble = f["hero"], f["friend"], f["prize"], f["trouble"]
    return [
        QAItem(
            question=f"Who was the brave child in the story?",
            answer=f"The brave child was {hero.id}, who chased the {prize.label} and later apologized with courage.",
        ),
        QAItem(
            question=f"Why did {friend.id} and {hero.id} quarrel?",
            answer=f"They quarreled because {hero.id} rushed ahead to {trouble.verb}, and {friend.id} thought that meant being left out.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"{hero.id} made a brave apology, {friend.id} accepted it, and together they used {f['bond'].label} to help bring the {prize.label} back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apology for?",
            answer="An apology is a way to say you are sorry and start repairing hurt feelings.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when your knees feel wobbly or your heart thumps fast.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to become friendly again after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
trouble(T) :- trouble_kind(T).
prize(P) :- prize_kind(P).

compatible(plain,kite,ribbon) :- setting(plain), trouble_kind(kite), prize_kind(ribbon).
compatible(fair,banner,ribbon) :- setting(fair), trouble_kind(banner), prize_kind(ribbon).
compatible(hill,kite,ribbon) :- setting(hill), trouble_kind(kite), prize_kind(ribbon).
compatible(plain,pie,cup) :- setting(plain), trouble_kind(pie), prize_kind(cup).
compatible(fair,pie,cup) :- setting(fair), trouble_kind(pie), prize_kind(cup).
compatible(hill,pie,cup) :- setting(hill), trouble_kind(pie), prize_kind(cup).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble_kind", tid))
    for prid in PRIZES:
        lines.append(asp.fact("prize_kind", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about Aya, bravery, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--hero-name", default="Aya")
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, prize = rng.choice(sorted(combos))
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != args.hero_name])
    return StoryParams(place=place, trouble=trouble, prize=prize, friend_name=friend_name, hero_name=args.hero_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TROUBLES[params.trouble], PRIZES[params.prize], params.hero_name, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:8}) location={e.location!r} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(place="plain", trouble="kite", prize="ribbon", friend_name="Milo"),
    StoryParams(place="fair", trouble="banner", prize="ribbon", friend_name="June"),
    StoryParams(place="hill", trouble="kite", prize="ribbon", friend_name="Pia"),
    StoryParams(place="plain", trouble="pie", prize="cup", friend_name="Otis"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
