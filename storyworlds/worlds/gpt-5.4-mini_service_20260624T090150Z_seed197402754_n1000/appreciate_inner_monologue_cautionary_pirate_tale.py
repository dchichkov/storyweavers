#!/usr/bin/env python3
"""
storyworlds/worlds/appreciate_inner_monologue_cautionary_pirate_tale.py
======================================================================

A small pirate-tale storyworld about a young deckhand who wants treasure, but
learns to appreciate a cautious inner monologue and a safer choice at sea.

Premise:
- A child pirate loves adventure and treasure.
- A tempting risky choice threatens the ship, the map, or a prize.
- The captain's careful inner monologue notices the danger.
- A cautionary turn leads to a safer pirate-style resolution.

This world is intentionally compact and classical: one domain, a clear tension,
and a resolution driven by state changes in the ship, the route, and the crew's
feelings.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "appreciation": 0.0, "caution": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_person(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str = "the little pirate ship"
    sea: str = "the bright sea"


@dataclass
class Choice:
    id: str
    risky_verb: str
    cautious_verb: str
    risk_reason: str
    consequence: str
    safer_choice: str
    tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

CHOICES = {
    "reef": Choice(
        id="reef",
        risky_verb="sail near the reef",
        cautious_verb="turn away from the reef",
        risk_reason="the rocks could tear the hull",
        consequence="the ship could spring a leak",
        safer_choice="follow the open water",
        tag="reef",
    ),
    "storm": Choice(
        id="storm",
        risky_verb="cross the dark storm clouds",
        cautious_verb="wait for the storm to pass",
        risk_reason="the wind could snap the sail",
        consequence="the mast could shake and groan",
        safer_choice="stay in calmer water",
        tag="storm",
    ),
    "cave": Choice(
        id="cave",
        risky_verb="row into the sea cave",
        cautious_verb="row past the sea cave",
        risk_reason="the cave could hide sharp stones",
        consequence="the little boat could scrape and wobble",
        safer_choice="keep close to the sunlight",
        tag="cave",
    ),
    "chest": Choice(
        id="chest",
        risky_verb="rush for the shining chest",
        cautious_verb="check the chest for traps first",
        risk_reason="the chest might be tied to a net or a trick",
        consequence="someone could get tangled or splashed",
        safer_choice="open it carefully",
        tag="treasure",
    ),
}

TREASURES = {
    "map": ("a creased treasure map", "map"),
    "spyglass": ("a brass spyglass", "spyglass"),
    "lamp": ("a small lantern", "lantern"),
}

CHAR_NAMES = ["Mina", "Ned", "Pip", "Tia", "Bo", "Rae", "Sailor Sam"]
ADJECTIVES = ["brave", "bright-eyed", "merry", "quick", "curious", "spry"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A choice is reasonable if the risky action has a real danger and the
% cautious action avoids it.
danger(C) :- choice(C), risk(C, R), reason(C, R).
safer(C) :- choice(C), safe(C, S), avoids(C, S).
valid(C) :- danger(C), safer(C).

#show valid/1.
#show danger/1.
#show safer/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("risk", cid, c.risky_verb))
        lines.append(asp.fact("reason", cid, c.risk_reason))
        lines.append(asp.fact("safe", cid, c.safer_choice))
        lines.append(asp.fact("avoids", cid, c.consequence))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_choices() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    out = [args[0] for args in asp.atoms(model, "valid")]
    return sorted(set(out))


def asp_verify() -> int:
    python_set = set(valid_choices())
    asp_set = set(asp_valid_choices())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_choices() ({len(python_set)} choices).")
        return 0
    print("MISMATCH between clingo and valid_choices():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    choice: str
    treasure: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


def valid_choices() -> list[str]:
    return list(CHOICES.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small pirate tale about caution, inner monologue, and appreciation."
    )
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["captain", "mate", "deckhand"])
    ap.add_argument("--trait", choices=ADJECTIVES)
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
    choice = args.choice or rng.choice(sorted(valid_choices()))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    name = args.name or rng.choice(CHAR_NAMES)
    role = args.role or rng.choice(["captain", "mate", "deckhand"])
    trait = args.trait or rng.choice(ADJECTIVES)
    return StoryParams(choice=choice, treasure=treasure, name=name, role=role, trait=trait)


# ---------------------------------------------------------------------------
# Simulation and prose
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.choice in CHOICES and params.treasure in TREASURES


def make_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("Invalid pirate story parameters.")

    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    treasure_phrase, treasure_tag = TREASURES[params.treasure]
    treasure = world.add(
        Entity(
            id="Treasure",
            kind="thing",
            type=treasure_tag,
            label=params.treasure,
            phrase=treasure_phrase,
            owner=hero.id,
            caretaker=captain.id,
            location="deck",
        )
    )
    choice = CHOICES[params.choice]
    world.facts.update(
        hero=hero,
        captain=captain,
        treasure=treasure,
        choice=choice,
        params=params,
    )

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} little deckhand aboard {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved adventure and wanted to appreciate every new thing at sea."
    )
    world.say(
        f"One day, {hero.id}'s captain showed {hero.pronoun('object')} {treasure.phrase}."
    )
    treasure.worn_by = hero.id
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} held the {params.treasure} close and smiled at how fine it looked in the sun."
    )

    # Act 2: tension and inner monologue
    world.para()
    world.say(
        f"When {world.setting.sea} turned rough, {hero.id} wanted to {choice.risky_verb}."
    )
    hero.memes["worry"] += 1
    captain.memes["caution"] += 1
    world.say(
        f"Inside, {hero.id} had a careful little inner monologue: "
        f'"What if {choice.risk_reason}? I should think first."'
    )
    world.say(
        f"The captain's own cautionary thought was even quieter: "
        f'"Stay wise, stay slow, and keep the crew safe."'
    )
    world.say(
        f"That warning mattered, because {choice.consequence}."
    )

    # Act 3: safer turn
    world.para()
    hero.memes["appreciation"] += 1
    world.say(
        f"{hero.id} paused and appreciated the caution instead of rushing ahead."
    )
    world.say(
        f"So {hero.id} chose to {choice.cautious_verb} and {choice.safer_choice}."
    )
    world.say(
        f"That kept the {params.treasure} safe, and the ship sailed on with calm water under its belly."
    )
    world.say(
        f"{hero.id} grinned, because a brave pirate could be careful too."
    )

    return world


def story_prompt_text(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    choice: Choice = f["choice"]
    return [
        f'Write a short pirate tale for a child named {p.name} that includes the word "appreciate".',
        f"Tell a cautionary pirate story where {p.name} wants to {choice.risky_verb} but learns to listen to an inner monologue.",
        f"Write a gentle sea adventure where a {p.trait} {p.role} chooses a safer way after noticing danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    choice: Choice = f["choice"]
    hero: Entity = f["hero"]
    treasure: Entity = f["treasure"]
    captain: Entity = f["captain"]
    return [
        QAItem(
            question=f"What did {p.name} want to do when the sea got rough?",
            answer=f"{p.name} wanted to {choice.risky_verb}.",
        ),
        QAItem(
            question=f"What did {p.name}'s inner monologue warn about?",
            answer=f"It warned that {choice.risk_reason}.",
        ),
        QAItem(
            question=f"How did {p.name} show appreciation for the captain's caution?",
            answer=(
                f"{p.name} paused, appreciated the warning, and chose to {choice.cautious_verb} "
                f"so the {p.treasure} would stay safe."
            ),
        ),
        QAItem(
            question=f"What happened to the {p.treasure} at the end?",
            answer=f"The {p.treasure} stayed safe while the ship sailed on calmly.",
        ),
        QAItem(
            question=f"Who helped keep {p.name} safe?",
            answer=f"The captain helped keep {hero.id} safe by offering a cautious warning.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cautionary story?",
            answer=(
                "A cautionary story is a story that shows a risk and helps the listener "
                "understand why a careful choice is better."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is the quiet talking a character does in their own mind, "
                "like thinking through a problem before acting."
            ),
        ),
        QAItem(
            question="Why do pirates use maps and careful plans?",
            answer=(
                "Pirates use maps and careful plans so they can avoid rocks, storms, and tricks "
                "while searching for treasure."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt_text(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def show_asp_program() -> str:
    return asp_program("#show valid/1.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(choice="reef", treasure="map", name="Mina", role="captain", trait="brave"),
    StoryParams(choice="storm", treasure="spyglass", name="Pip", role="deckhand", trait="curious"),
    StoryParams(choice="cave", treasure="lamp", name="Tia", role="mate", trait="merry"),
    StoryParams(choice="chest", treasure="map", name="Ned", role="captain", trait="spry"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_choices() -> list[str]:
    return sorted(CHOICES)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} valid choices:")
        for choice in asp_valid_stories():
            print(" ", choice[0])
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.choice} with {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
