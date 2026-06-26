#!/usr/bin/env python3
"""
storyworlds/worlds/lotto_nurse_bazaar_surprise_superhero_story.py
===================================================================

A small superhero-style story world about a nurse at a bazaar who gets a
surprising lotto ticket result and uses the prize to help people.

Premise:
- A kind nurse works a busy bazaar booth.
- The nurse hopes a surprise lotto ticket might change the day.
- A small emergency and a sudden prize create tension.
- The story ends with a heroic, helpful turn: the prize is used to fix the
  problem in a way that fits the world.

This world models both physical state ("meters") and emotional state ("memes")
for a few typed entities. The prose is driven by the simulated state, not a
fixed paragraph template.

Seed inspiration:
- lotto
- nurse
- bazaar
- surprise
- superhero style
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"broken": 0.0, "lost": 0.0, "delivered": 0.0}
        if not self.memes:
            self.memes = {
                "hope": 0.0,
                "surprise": 0.0,
                "worry": 0.0,
                "pride": 0.0,
                "kindness": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"nurse", "woman", "girl", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    kind: str
    label: str
    effect: str
    requires: set[str] = field(default_factory=set)
    reward: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bazaar": Setting(place="the bazaar", affords={"sell", "search", "help"}),
    "clinic": Setting(place="the clinic corner", affords={"help"}),
}

EVENTS = {
    "lotto": Event(
        id="lotto",
        kind="chance",
        label="lotto ticket",
        effect="wins",
        requires={"ticket"},
        reward="money",
    ),
    "surprise": Event(
        id="surprise",
        kind="chance",
        label="surprise announcement",
        effect="reveals",
        requires={"news"},
        reward="hope",
    ),
    "crowd": Event(
        id="crowd",
        kind="problem",
        label="crowd trouble",
        effect="blocks",
        requires={"people"},
        reward="worry",
    ),
}

TRADES = {
    "bandages": "bandages",
    "supplies": "medical supplies",
    "fruit": "fruit for the stall",
    "toy": "a bright toy",
}

HERO_NAMES = ["Mina", "Iris", "Nora", "Tia", "Lena", "Zara"]
SIDEKICK_NAMES = ["Pip", "Dot", "Jules", "Rae"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    ticket_kind: str
    surprise_kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, ticket_kind: str, surprise_kind: str) -> bool:
    if place != "bazaar":
        return False
    if ticket_kind != "lotto":
        return False
    if surprise_kind != "surprise":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bazaar", "lotto", "surprise")]


def explain_rejection(place: str, ticket_kind: str, surprise_kind: str) -> str:
    return (
        f"(No story: this world is built for a bazaar scene with a lotto surprise; "
        f"got place={place!r}, ticket={ticket_kind!r}, surprise={surprise_kind!r}.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def hero_intro(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a nurse at the bazaar who moved fast when people needed help, "
        f"and {sidekick.id} liked to help carry things beside {hero.pronoun('object')}."
    )


def bazaar_life(world: World, hero: Entity) -> None:
    world.say(
        f"At {world.setting.place}, baskets of fruit, ribbons, and warm bread filled the air "
        f"with busy sounds."
    )
    hero.memes["hope"] += 1


def surprise_ticket(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"One afternoon, {hero.id} found a surprise lotto ticket tucked into a box of supplies."
    )


def predict_win(world: World, hero: Entity) -> bool:
    return True


def trouble_arrives(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then a little child nearby began to cry, because a jar of medicine had tipped and split."
    )
    world.facts["need"] = "medical supplies"


def win_lotto(world: World, hero: Entity) -> None:
    if not predict_win(world, hero):
        return
    hero.meters["money"] = hero.meters.get("money", 0.0) + 1
    hero.memes["surprise"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"When {hero.id} checked the ticket, it was a winner. The prize was enough to buy more "
        f"medical supplies right away."
    )


def act_heroically(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} hurried to the clinic corner, bought bandages and clean water, and asked "
        f"{sidekick.id} to help carry them."
    )
    world.say(
        f"Together, they fixed the spill, comforted the child, and kept the bazaar calm."
    )


def ending_image(world: World, hero: Entity) -> None:
    world.say(
        f"By sunset, {hero.id} was back under the bazaar awning, smiling like a true superhero "
        f"nurse while the new supplies sat safely beside {hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# Build and generate
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.ticket_kind, params.surprise_kind):
        raise StoryError(explain_rejection(params.place, params.ticket_kind, params.surprise_kind))

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="nurse"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="hero"))
    world.add(Entity(id="ticket", type="ticket", label="lotto ticket", owner=hero.id))
    world.add(Entity(id="supplies", type="supplies", label="medical supplies", caretaker=hero.id))

    world.facts.update(hero=hero, sidekick=sidekick, place=params.place)
    hero_intro(world, hero, sidekick)
    bazaar_life(world, hero)
    world.para()
    surprise_ticket(world, hero)
    trouble_arrives(world, hero)
    win_lotto(world, hero)
    world.para()
    act_heroically(world, hero, sidekick)
    ending_image(world, hero)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a superhero-style story about a nurse named {hero.id} at the bazaar who gets a lotto surprise.",
        f"Tell a short, child-friendly story where {hero.id} finds a winning ticket and uses it to help people.",
        f"Write a gentle story with the words lotto, nurse, bazaar, and surprise, ending in a heroic helpful act.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a nurse who works at the bazaar and acts like a superhero when people need help.",
        ),
        QAItem(
            question=f"What surprising thing did {hero.id} find?",
            answer=f"{hero.id} found a surprise lotto ticket, and it turned out to be a winner.",
        ),
        QAItem(
            question=f"How did {hero.id} use the prize?",
            answer=f"{hero.id} used the lotto prize to buy medical supplies and help fix the problem at the bazaar.",
        ),
        QAItem(
            question=f"Who helped {hero.id} carry the supplies?",
            answer=f"{sidekick.id} helped carry the supplies beside {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nurse?",
            answer="A nurse is a helper who cares for sick or hurt people and can bring comfort, medicine, and care.",
        ),
        QAItem(
            question="What is a bazaar?",
            answer="A bazaar is a busy market where people sell and buy things from little stalls.",
        ),
        QAItem(
            question="What is a lotto ticket?",
            answer="A lotto ticket is a ticket for a game of chance. If it wins, the person who bought it may get a prize.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes someone suddenly feel amazed or excited.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(Place, Ticket, Surprise) :- place(Place), ticket(Ticket), surprise(Surprise),
                                  place_is_bazaar(Place), ticket_is_lotto(Ticket),
                                  surprise_is_surprise(Surprise).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in SETTINGS:
        lines.append(asp.fact("place", name))
        if name == "bazaar":
            lines.append(asp.fact("place_is_bazaar", name))
    lines.append(asp.fact("ticket", "lotto"))
    lines.append(asp.fact("ticket_is_lotto", "lotto"))
    lines.append(asp.fact("surprise", "surprise"))
    lines.append(asp.fact("surprise_is_surprise", "surprise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style bazaar nurse lotto surprise story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--ticket-kind", choices=["lotto"])
    ap.add_argument("--surprise-kind", choices=["surprise"])
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
    place = args.place or "bazaar"
    ticket_kind = args.ticket_kind or "lotto"
    surprise_kind = args.surprise_kind or "surprise"
    if not valid_combo(place, ticket_kind, surprise_kind):
        raise StoryError(explain_rejection(place, ticket_kind, surprise_kind))
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        ticket_kind=ticket_kind,
        surprise_kind=surprise_kind,
    )


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="bazaar", hero_name="Mina", sidekick_name="Pip", ticket_kind="lotto", surprise_kind="surprise"),
    StoryParams(place="bazaar", hero_name="Iris", sidekick_name="Dot", ticket_kind="lotto", surprise_kind="surprise"),
    StoryParams(place="bazaar", hero_name="Nora", sidekick_name="Jules", ticket_kind="lotto", surprise_kind="surprise"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero_name}: bazaar lotto surprise"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
