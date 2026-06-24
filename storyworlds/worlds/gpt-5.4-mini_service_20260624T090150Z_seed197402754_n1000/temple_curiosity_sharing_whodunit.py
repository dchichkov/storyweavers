#!/usr/bin/env python3
"""
A small story world: a temple whodunit about curiosity and sharing.

Premise:
A child at a temple wants to look closely at a special object, but the object
must be shared carefully among visitors. The mystery is whether a missing thing
was stolen, misplaced, or simply handed around for a ritual.

World model:
- Characters have meters (physical presence, carried objects) and memes
  (curiosity, suspicion, relief, trust).
- Objects can be held, hidden, or shared.
- The story advances through clues, misdirection, discovery, and resolution.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: Optional[str] = None
    shared: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Temple:
    name: str = "the temple"
    room: str = "the candle hall"
    display: str = "the stone altar"
    affords: set[str] = field(default_factory=lambda: {"look", "share", "search"})


@dataclass
class StoryParams:
    temple_name: str
    hero_name: str
    helper_name: str
    item: str
    seed: Optional[int] = None


@dataclass
class World:
    temple: Temple
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
TEMPLES = {
    "sun_temple": Temple(name="the Sun Temple", room="the candle hall", display="the altar"),
    "river_temple": Temple(name="the River Temple", room="the quiet passage", display="the offering shelf"),
    "hill_temple": Temple(name="the Hill Temple", room="the inner court", display="the low stone table"),
}

ITEMS = {
    "lantern": {
        "label": "lantern",
        "phrase": "a small brass lantern",
        "risk": "missing",
        "clue": "warm wax on the base",
    },
    "scroll": {
        "label": "scroll",
        "phrase": "a wrapped prayer scroll",
        "risk": "lost",
        "clue": "a ribbon tied in a double knot",
    },
    "key": {
        "label": "key",
        "phrase": "an old bronze key",
        "risk": "taken",
        "clue": "fine dust on the teeth",
    },
    "coin": {
        "label": "coin",
        "phrase": "a silver temple coin",
        "risk": "gone",
        "clue": "fingerprints on the bowl",
    },
}

NAMES = ["Mina", "Taro", "Lina", "Jai", "Rumi", "Sora", "Kimi", "Noa"]
HELPER_NAMES = ["Bela", "Niko", "Ari", "Mara", "Oren", "Suri"]


# ---------------------------------------------------------------------------
# Reasonable gate
# ---------------------------------------------------------------------------
def item_needs_sharing(item_id: str) -> bool:
    return item_id in ITEMS


def valid_combo(temple_key: str, item_id: str) -> bool:
    return temple_key in TEMPLES and item_id in ITEMS


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
needs_sharing(I) :- item(I).
valid_story(T, I) :- temple(T), item(I), needs_sharing(I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for tid in TEMPLES:
        lines.append(asp.fact("temple", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("needs_sharing", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(t, i) for t in TEMPLES for i in ITEMS if valid_combo(t, i)}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    temple = TEMPLES[params.temple_name]
    world = World(temple=temple)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="child",
        label=params.hero_name,
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "suspicion": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="caretaker",
        label=params.helper_name,
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "suspicion": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    item_cfg = ITEMS[params.item]
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type=params.item,
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=helper.id,
        held_by=helper.id,
        shared=True,
        meters={"shine": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, relic=relic, item_cfg=item_cfg)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get(params.hero_name)
    helper = world.get(params.helper_name)
    relic = world.get("relic")
    item_cfg = world.facts["item_cfg"]
    temple = world.temple

    world.say(
        f"{hero.id} came to {temple.name} with {helper.id}, and the air smelled like cool stone and candle smoke."
    )
    world.say(
        f"On the {temple.display}, there was {relic.phrase}, a temple object meant to be shared with care."
    )
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} kept looking at {relic.label} because {hero.pronoun('possessive')} curiosity would not sit still."
    )

    world.para()
    world.say(
        f"Then the {relic.label} was gone from the {temple.display}."
    )
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} wondered if someone had taken {relic.it()}, while {helper.id} frowned and checked the floor."
    )

    world.para()
    clue = item_cfg["clue"]
    world.say(
        f"Near the {temple.room}, {hero.id} found {clue}."
    )
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} said the clue did not look like theft; it looked like someone had handled {relic.it()} during the sharing."
    )

    world.para()
    world.say(
        f"They searched the side shelf together, and behind a folded cloth they found the {relic.label}, waiting where it had been set down."
    )
    world.say(
        f"{helper.id} smiled and said the temple visitors had passed {relic.it()} along for blessings, then tucked it away for safety."
    )
    world.say(
        f"{hero.id} felt {hero.pronoun('possessive')} suspicion fade as {hero.pronoun('possessive')} curiosity turned into relief."
    )
    hero.memes["suspicion"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child set at {world.temple.name} about a missing {f["relic"].label} and a gentle act of sharing.',
        f"Tell a temple mystery where {f['hero'].id} gets curious about {f['relic'].phrase} and learns who moved it.",
        f"Write a simple detective story in which the answer is not a thief, but careful sharing and a misplaced object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    relic = world.facts["relic"]
    item_cfg = world.facts["item_cfg"]

    return [
        QAItem(
            question=f"Why did {hero.id} start looking so closely at the {relic.label}?",
            answer=f"{hero.id} was curious, so {hero.pronoun('possessive')} curiosity made {hero.id} keep looking at the {relic.label}.",
        ),
        QAItem(
            question=f"What made {hero.id} think something bad might have happened to the {relic.label}?",
            answer=f"When the {relic.label} was gone from the altar, {hero.id} worried that someone had taken {relic.it()}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {helper.id} solve the mystery?",
            answer=f"The clue was {item_cfg['clue']}, which suggested someone had handled {relic.it()} during the sharing instead of stealing it.",
        ),
        QAItem(
            question=f"Where did they find the {relic.label} in the end?",
            answer=f"They found the {relic.label} behind a folded cloth on the side shelf, where it had been set down safely.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} felt relief and trust at the end, because the mystery was solved and the {relic.label} was back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a temple?",
            answer="A temple is a special place where people may pray, reflect, or keep meaningful objects with care.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too, often by taking turns or passing it carefully.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} held_by={e.held_by} hidden_in={e.hidden_in} "
            f"meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Temple whodunit story world about curiosity and sharing.")
    ap.add_argument("--temple", choices=TEMPLES.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    temple = args.temple or rng.choice(list(TEMPLES.keys()))
    item = args.item or rng.choice(list(ITEMS.keys()))
    if not valid_combo(temple, item):
        raise StoryError("Invalid temple/item choice.")
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(temple_name=temple, hero_name=hero, helper_name=helper, item=item)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("sun_temple", "Mina", "Bela", "lantern"),
    StoryParams("river_temple", "Taro", "Ari", "scroll"),
    StoryParams("hill_temple", "Lina", "Mara", "key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t, i in stories:
            print(f"  {t:12} {i}")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            sample = generate(params)
            if sample.story not in seen:
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
