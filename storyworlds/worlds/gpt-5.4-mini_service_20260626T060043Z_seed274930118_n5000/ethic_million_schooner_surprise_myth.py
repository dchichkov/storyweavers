#!/usr/bin/env python3
"""
A tiny mythic storyworld about an ethic, a million, and a schooner.

Premise:
- A seaside village keeps one living ethic: never take more from the tide than
  you can carry back with both hands.
- A schooner named Surprise is used to move offerings, lanterns, and people.
- One day, a silver million appears in the harbor chest, and everyone must
  decide whether to keep, count, share, or return it.

This world models:
- physical state in meters: distance, load, fullness, brightness
- emotional state in memes: wonder, greed, trust, duty, shame, relief

The story turns on a mythic test: Surprise can safely carry a small honest load,
but a million coins would drag her low and break the village ethic.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Story configuration
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Iris"
    gender: str = "girl"
    guardian: str = "elder"
    place: str = "harbor"
    surprise: str = "Surprise"
    item: str = "silver coins"
    count: int = 1000000
    virtue: str = "ethic"


@dataclass
class HarborSetting:
    place: str = "the harbor"
    weather: str = "windy"


@dataclass
class Vessel:
    id: str
    label: str
    length: float
    load_limit: float
    carries: str
    brave: bool = True


SETTINGS = {
    "harbor": HarborSetting(place="the harbor", weather="windy"),
    "cove": HarborSetting(place="the cove", weather="misty"),
    "island": HarborSetting(place="the island pier", weather="salt-bright"),
}

VESSELS = {
    "Surprise": Vessel(id="surprise", label="Surprise", length=18.0, load_limit=40.0, carries="passengers"),
}

GUARDIANS = {
    "elder": {"type": "elder", "label": "the elder"},
    "captain": {"type": "captain", "label": "the captain"},
    "mother": {"type": "mother", "label": "the mother"},
    "father": {"type": "father", "label": "the father"},
}

NAMES = {
    "girl": ["Iris", "Mara", "Sera", "Lena", "Nia"],
    "boy": ["Orin", "Tomas", "Jory", "Evan", "Perrin"],
}

TRAITS = ["quiet", "brave", "thoughtful", "curious", "gentle"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _new_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(place=setting.place, weather=setting.weather)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"distance": 0.0},
        memes={"wonder": 0.0, "duty": 0.0, "trust": 0.0, "greed": 0.0, "relief": 0.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=GUARDIANS[params.guardian]["type"],
        label=GUARDIANS[params.guardian]["label"],
        meters={"distance": 0.0},
        memes={"duty": 0.0, "fear": 0.0, "trust": 0.0},
    ))
    schooner = world.add(Entity(
        id="surprise",
        kind="thing",
        type="schooner",
        label="Surprise",
        phrase="the schooner Surprise",
        meters={"load": 0.0, "draft": 0.0, "brightness": 1.0},
        memes={"memory": 0.0, "hope": 0.0},
    ))
    chest = world.add(Entity(
        id="chest",
        kind="thing",
        type="chest",
        label="harbor chest",
        phrase="a harbor chest",
        meters={"coins": float(params.count), "shine": 1.0},
        memes={"temptation": 1.0, "wonder": 1.0},
    ))
    ethic = world.add(Entity(
        id="ethic",
        kind="thing",
        type="rule",
        label=params.virtue,
        phrase="the old ethic",
        meters={"weight": 1.0},
        memes={"authority": 1.0, "mercy": 1.0},
    ))

    world.facts.update(
        child=child,
        guardian=guardian,
        schooner=schooner,
        chest=chest,
        ethic=ethic,
        params=params,
        setting=setting,
        vessel=VESSELS[params.surprise],
        count=params.count,
    )
    return world


def _count_to_story(count: int) -> str:
    if count == 1:
        return "one coin"
    if count == 2:
        return "two coins"
    if count < 10:
        return f"{count} coins"
    if count < 1000:
        return f"{count} shining coins"
    if count < 1000000:
        return f"{count:,} coins"
    return "a million silver coins"


def _weight_of(count: int) -> float:
    return count / 25000.0


def _is_overloaded(world: World) -> bool:
    vessel = world.facts["vessel"]
    return world.get("surprise").meters["load"] > vessel.load_limit


def _narrate_setup(world: World) -> None:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    schooner = world.get("surprise")

    trait = random.choice(TRAITS)
    world.say(
        f"In the old harbor, {child.label} was a {trait} child who listened to the sea as if it told stories."
    )
    world.say(
        f"People there kept one sacred {world.get('ethic').label}: never let hunger for more outrun a fair hand."
    )
    world.say(
        f"Every dawn, the schooner Surprise rocked at the pier, her ropes singing softly in the wind."
    )


def _narrate_discovery(world: World) -> None:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    chest = world.get("chest")

    world.para()
    world.say(
        f"One gray morning, {child.label} found the harbor chest open and bright with {_count_to_story(p.count)}."
    )
    world.say(
        f"{guardian.label.capitalize()} came close and went still, because such a sight could wake wonder or greed."
    )
    child.memes["wonder"] += 1.0
    guardian.memes["duty"] += 1.0
    chest.memes["temptation"] += 0.5


def _narrate_warning(world: World) -> None:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    schooner = world.get("surprise")
    ethic = world.get("ethic")

    world.say(
        f'"That is not a treasure to pile high," {guardian.label} said. "If we load Surprise with all of it, she will sink low."'
    )
    child.memes["trust"] += 1.0
    child.memes["duty"] += 0.5
    world.say(
        f'The old {ethic.label} answered in {child.label}\'s chest like a bell: take only what you can return.'
    )


def _apply_load(world: World, amount: int) -> None:
    schooner = world.get("surprise")
    schooner.meters["load"] = _weight_of(amount)
    schooner.meters["draft"] = schooner.meters["load"] / 2.0
    if amount > 0:
        schooner.memes["memory"] += 1.0


def _narrate_turn(world: World) -> None:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    schooner = world.get("surprise")

    half = p.count // 2
    small_share = 12
    _apply_load(world, p.count)
    if _is_overloaded(world):
        world.say(
            f"When they tried to lift the whole prize aboard Surprise, the deck dipped and the rope groaned."
        )
        child.memes["fear"] += 1.0
        guardian.memes["fear"] += 1.0
    else:
        world.say("The load sat lightly, and the deck did not complain.")
    _apply_load(world, small_share)
    world.say(
        f"Then {child.label} held up a smaller purse—only {small_share} coins—and asked if a fair offering could be made instead."
    )
    child.memes["wonder"] += 0.5
    child.memes["duty"] += 1.0
    guardian.memes["trust"] += 1.0


def _narrate_resolution(world: World) -> None:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    schooner = world.get("surprise")
    ethic = world.get("ethic")

    world.say(
        f"{guardian.label} nodded. " +
        f'"The ethic is wiser than a crowd," {guardian.label} said. "We return the million, and we keep the promise."'
    )
    child.memes["greed"] = 0.0
    child.memes["relief"] += 1.0
    guardian.memes["relief"] = 1.0
    schooner.meters["load"] = 0.48
    schooner.meters["brightness"] = 1.2
    world.say(
        f"So they sailed out on Surprise with only the fair share, and the sea accepted it without a splash of shame."
    )
    world.say(
        f"By sunset, the chest was sealed again, the harbor was quiet, and the old {ethic.label} stood true as a lighthouse."
    )


def tell(params: StoryParams) -> World:
    world = _new_world(params)
    _narrate_setup(world)
    _narrate_discovery(world)
    _narrate_warning(world)
    _narrate_turn(world)
    _narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a mythic story for a child about an ethic, a million silver coins, and a schooner named Surprise.',
        f"Tell a small seaside myth where {p.name} learns that a million is too heavy for Surprise, and a fair share is wiser.",
        f'Write a gentle legend about the word "{p.virtue}" and a harbor chest full of "{_count_to_story(p.count)}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.get(p.name)
    guardian = world.get("guardian")
    schooner = world.get("surprise")
    ethic = world.get("ethic")

    return [
        QAItem(
            question=f"Who found the open chest in the harbor?",
            answer=f"{child.label} found the open chest in the harbor and saw {_count_to_story(p.count)} shining inside.",
        ),
        QAItem(
            question=f"Why did {guardian.label} warn against loading all the coins onto Surprise?",
            answer=f"{guardian.label} warned because the schooner Surprise would have sunk low if they loaded the whole million aboard.",
        ),
        QAItem(
            question=f"What did the village choose to do instead of keeping the million?",
            answer=f"They chose to return the million and sail with only a fair share, because the old {ethic.label} mattered more than greed.",
        ),
        QAItem(
            question=f"How did Surprise end the story?",
            answer=f"Surprise ended bright on the water with only a small honest load, while the chest was sealed and the harbor was peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a schooner?",
            answer="A schooner is a sailing ship with tall masts and sails that catch the wind.",
        ),
        QAItem(
            question="What is an ethic?",
            answer="An ethic is a strong rule about what is fair, right, and kind.",
        ),
        QAItem(
            question="What does a million mean?",
            answer="A million is a very large number: 1,000,000.",
        ),
        QAItem(
            question="What is surprise in a story?",
            answer="A surprise is something unexpected that makes the story feel sudden or exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A million coins are too heavy for the schooner Surprise.
overloaded(C) :- cargo(C), million(C), too_heavy_for_surprise(C).

% The mythic ethic says the honest share is allowed, but the million is not.
allowed(C) :- cargo(C), fair_share(C).
rejected(C) :- cargo(C), million(C).

% A valid story exists only when there is both temptation and a safe resolution.
valid_story(P, C, S) :- place(P), cargo(C), schooner(S), fair_share(C), named_surprise(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid, vessel in VESSELS.items():
        lines.append(asp.fact("schooner", sid))
        if vessel.label == "Surprise":
            lines.append(asp.fact("named_surprise", sid))
    lines.append(asp.fact("cargo", "million"))
    lines.append(asp.fact("million", "million"))
    lines.append(asp.fact("too_heavy_for_surprise", "million"))
    lines.append(asp.fact("cargo", "fair_share"))
    lines.append(asp.fact("fair_share", "fair_share"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python reasonableness gate: only fair share is valid, million is rejected.
    python_valid = {("harbor", "fair_share", "surprise"),
                    ("cove", "fair_share", "surprise"),
                    ("island", "fair_share", "surprise")}
    clingo_valid = set(asp_valid_stories())
    if clingo_valid == python_valid:
        print(f"OK: clingo gate matches Python gate ({len(clingo_valid)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_valid - python_valid:
        print("  only in clingo:", sorted(clingo_valid - python_valid))
    if python_valid - clingo_valid:
        print("  only in python:", sorted(python_valid - clingo_valid))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic harbor storyworld: ethic, million, schooner, surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guardian", choices=GUARDIANS.keys())
    ap.add_argument("--surprise", choices=VESSELS.keys(), default="Surprise")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    guardian = args.guardian or rng.choice(list(GUARDIANS.keys()))
    return StoryParams(
        seed=args.seed,
        name=name,
        gender=gender,
        guardian=guardian,
        place=place,
        surprise="Surprise",
        item="silver coins",
        count=1000000,
        virtue="ethic",
    )


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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Iris", gender="girl", guardian="elder", place="harbor"),
            StoryParams(name="Orin", gender="boy", guardian="captain", place="cove"),
            StoryParams(name="Mara", gender="girl", guardian="mother", place="island"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
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
