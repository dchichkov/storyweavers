#!/usr/bin/env python3
"""
A small Pirate Tale story world about a captain, a servant, a strange mixture,
a mistake in what someone perceives, and a friendship that ends badly.

The premise is simple: a pirate captain keeps a secret mixture aboard ship.
A loyal servant notices it, thinks it is a treasure drink, and tries to help.
But the mixture is actually meant to clean tar from the deck, and the wrong
choice causes a poor ending to the friendship.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "servant", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pirate ship"
    sea: str = "calm"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mixture:
    id: str
    label: str
    phrase: str
    color: str
    use: str
    mess: str
    smell: str
    can_perceive_as: str


@dataclass
class StoryParams:
    place: str
    mixture: str
    servant_name: str
    captain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the pirate ship", sea="calm", affords={"mix", "clean", "watch"}),
    "harbor": Setting(place="the harbor dock", sea="windy", affords={"mix", "clean", "watch"}),
}

MIXTURES = {
    "deckwash": Mixture(
        id="deckwash",
        label="deckwash mixture",
        phrase="a pale green mixture",
        color="green",
        use="clean tar from the deck",
        mess="slippery foam",
        smell="sharp and salty",
        can_perceive_as="treasure drink",
    ),
    "lampoil": Mixture(
        id="lampoil",
        label="lamp-oil mixture",
        phrase="a dark shiny mixture",
        color="dark",
        use="feed the ship's lamps",
        mess="sticky spill",
        smell="strong and smoky",
        can_perceive_as="treasure drink",
    ),
}

SERVANT_NAMES = ["Ned", "Mira", "Pip", "June", "Toby", "Lia"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Brine", "Captain Sal", "Captain Wren"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "mix" not in setting.affords:
            continue
        for mid in MIXTURES:
            combos.append((place, mid))
    return combos


def explain_rejection(place: str, mixture: str) -> str:
    return f"(No story: {place} cannot host the mixture {mixture} in a useful pirate scene.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def perceive_mixture(observer: Entity, mixture: Mixture) -> str:
    return f"{observer.pronoun().capitalize()} thought the {mixture.label} looked like {mixture.can_perceive_as}."


def can_clean(world: World, mixture: Mixture) -> bool:
    return world.setting.affords and "clean" in world.setting.affords


def simulate_spill(world: World, mixture: Mixture) -> None:
    deck = world.get("deck")
    deck.meters["mess"] = deck.meters.get("mess", 0.0) + 1.0
    deck.meters["slippery"] = deck.meters.get("slippery", 0.0) + 1.0
    world.facts["spilled"] = True
    world.say(f"The mixture slipped across the deck and left {mixture.mess}.")


def tell(setting: Setting, mixture: Mixture, servant_name: str, captain_name: str) -> World:
    world = World(setting)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label=captain_name,
        meters={"trust": 1.0},
        memes={"pride": 1.0, "friendship": 1.0},
    ))
    servant = world.add(Entity(
        id="servant",
        kind="character",
        type="servant",
        label=servant_name,
        meters={"help": 1.0},
        memes={"loyalty": 1.0, "friendship": 1.0, "hope": 1.0},
    ))
    deck = world.add(Entity(id="deck", kind="thing", type="deck", label="the deck"))
    bottle = world.add(Entity(
        id="mixture",
        kind="thing",
        type="mixture",
        label=mixture.label,
        phrase=mixture.phrase,
        owner="captain",
        caretaker="captain",
    ))

    world.say(
        f"On the {setting.place}, {captain.label} kept a {mixture.phrase} in a little bottle."
    )
    world.say(
        f"{servant.label} was a loyal servant, and {servant.pronoun()} liked to help the captain."
    )
    world.say(
        f"One morning, {servant.label} saw the bottle and {perceive_mixture(servant, mixture).lower()}"
    )

    world.para()
    world.say(
        f"{servant.label} wanted to make {captain.label} smile, so {servant.pronoun()} carried the bottle to the deck."
    )
    world.say(
        f"But the bottle was only for work, not for drinking, and its smell was {mixture.smell}."
    )

    # Conflict: the servant misperceives the mixture and spills it.
    world.para()
    world.say(
        f"{servant.label} shook the bottle to taste the splash, and the cap popped loose."
    )
    simulate_spill(world, mixture)
    captain.meters["trust"] = 0.0
    captain.memes["friendship"] = 0.0
    servant.memes["friendship"] = 0.0
    world.facts["bad_ending"] = True

    world.say(
        f"{captain.label} was not pleased. The deck became hard to walk on, and the good mood drifted away."
    )
    world.say(
        f"{captain.label} said, 'That bottle was meant to {mixture.use}, not to be fooled with!'"
    )

    # Bad ending: no reconciliation.
    world.para()
    world.say(
        f"{servant.label} looked down at the shiny mess and felt the friendship break apart like a snapped rope."
    )
    world.say(
        f"In the end, the ship stayed afloat, but {servant.label} and {captain.label} no longer smiled together."
    )

    world.facts.update(
        captain=captain,
        servant=servant,
        mixture=mixture,
        setting=setting,
        deck=deck,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    servant = f["servant"]
    captain = f["captain"]
    mixture = f["mixture"]
    return [
        f'Write a short pirate tale for young children about a servant named {servant.label} who notices a {mixture.label}.',
        f'Tell a story where {servant.label} tries to help {captain.label} but misunderstands a {mixture.label} on a ship.',
        f'Write a small pirate story that includes a mixture, a mistaken perception, and a friendship that ends badly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    servant = f["servant"]
    captain = f["captain"]
    mixture = f["mixture"]
    return [
        QAItem(
            question=f"What did {servant.label} think the {mixture.label} was?",
            answer=f"{servant.label} thought it was a treasure drink, but it was really a working mixture for the ship.",
        ),
        QAItem(
            question=f"Why did the friendship end badly on the pirate ship?",
            answer=f"The friendship ended badly because {servant.label} shook the bottle, spilled the mixture, and ruined the captain's trust.",
        ),
        QAItem(
            question=f"What was the {mixture.label} supposed to do?",
            answer=f"It was supposed to {mixture.use}.",
        ),
        QAItem(
            question=f"How did the deck change after the mistake?",
            answer=f"The deck got slippery and messy with {mixture.mess}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a servant?",
            answer="A servant is a helper who works for another person and does useful tasks for them.",
        ),
        QAItem(
            question="What is a mixture?",
            answer="A mixture is made when two or more things are stirred or combined together.",
        ),
        QAItem(
            question="What does it mean to perceive something?",
            answer="To perceive something means to notice it with your senses, like seeing, hearing, or smelling it.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates for sailing, carrying goods, and traveling across the sea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(P, M) :- place(P), mixture(M), affordable(P).

bad_ending(P, M) :- valid_combo(P, M), spills(M).
friendship_lost(P) :- bad_ending(P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if "clean" in setting.affords:
            lines.append(asp.fact("affordable", pid))
    for mid, mix in MIXTURES.items():
        lines.append(asp.fact("mixture", mid))
        lines.append(asp.fact("spills", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(asp_set - python_set))
    print(" only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a mistaken mixture and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mixture", choices=MIXTURES.keys())
    ap.add_argument("--name")
    ap.add_argument("--captain")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.mixture and args.mixture not in MIXTURES:
        raise StoryError("Unknown mixture.")
    combos = valid_combos()
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    combos = [c for c in combos if args.mixture is None or c[1] == args.mixture]
    if not combos:
        raise StoryError("No valid pirate mixture story matches those options.")
    place, mixture = rng.choice(sorted(combos))
    servant_name = args.name or rng.choice(SERVANT_NAMES)
    captain_name = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(place=place, mixture=mixture, servant_name=servant_name, captain_name=captain_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MIXTURES[params.mixture], params.servant_name, params.captain_name)
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(parts)}")
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
    StoryParams(place="ship", mixture="deckwash", servant_name="Ned", captain_name="Captain Reed"),
    StoryParams(place="harbor", mixture="lampoil", servant_name="Mira", captain_name="Captain Brine"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_combo/2."))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.servant_name} and {p.captain_name} at {p.place} ({p.mixture})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
