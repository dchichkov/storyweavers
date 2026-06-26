#!/usr/bin/env python3
"""
A small mystery-style storyworld about a child, a curious clue, a suspicious
snack, and a moral choice.

Seed image:
A child notices a strange smell of pastrami near a pair of overalls, worries
something is off, listens to an inner monologue, and chooses a kinder, truer
path.

The world is built to generate short complete stories with:
- a concrete setting
- a clue and a mild mystery
- an inner monologue that affects the choice
- a moral value that changes the ending

The language stays child-facing and simple, but the structure is driven by
simulated state: clues, suspicion, trust, and a resolution that proves what
changed.
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
    worn_by: Optional[str] = None
    trait: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Clue:
    id: str
    label: str
    smell: str
    oddness: str
    truth: str


@dataclass
class MoralValue:
    id: str
    label: str
    lesson: str
    action: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    value: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", detail="Warm light sat on the table and the floor was very still."),
    "hall": Setting(place="the hall", detail="The hallway was narrow, with old shoes by the wall and a quiet front door."),
    "market": Setting(place="the market", detail="The market had bright signs, busy baskets, and many people passing by."),
    "shed": Setting(place="the shed", detail="The shed smelled like wood and dust, and its shelves held forgotten things."),
}

CLUES = {
    "pastrami": Clue(
        id="pastrami",
        label="pastrami",
        smell="smelled like pastrami",
        oddness="the smell did not match the quiet room",
        truth="a sandwich had been left nearby",
    ),
    "button": Clue(
        id="button",
        label="a loose button",
        smell="had no smell at all",
        oddness="it looked like it had fallen off something important",
        truth="someone had brushed past in a hurry",
    ),
    "overalls": Clue(
        id="overalls",
        label="overalls",
        smell="smelled faintly of fabric and grass",
        oddness="one pocket was turned inside out",
        truth="someone had been searching that pocket",
    ),
    "ink": Clue(
        id="ink",
        label="ink",
        smell="smelled like old paper",
        oddness="a blue mark pointed to the wrong shelf",
        truth="a note had been written in secret",
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        label="honesty",
        lesson="telling the truth helps the mystery become clear",
        action="tell the truth",
    ),
    "kindness": MoralValue(
        id="kindness",
        label="kindness",
        lesson="being kind matters even when you are worried",
        action="speak gently",
    ),
    "courage": MoralValue(
        id="courage",
        label="courage",
        lesson="being brave means looking carefully instead of guessing too fast",
        action="look again",
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Ruby", "Nora", "Ivy"],
    "boy": ["Tobin", "Milo", "Eli", "Finn", "Otis"],
}

TRAITS = ["curious", "careful", "brave", "thoughtful", "quiet"]


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def inner_monologue(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} stared at the clue and thought, "
        f'"That is strange. I should beware before I guess too fast."'
    )
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1


def observe_clue(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} noticed {clue.label} near a pair of overalls, and {clue.oddness}."
    )
    world.facts["clue_seen"] = clue.id
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1


def suspect(world: World, hero: Entity, clue: Clue, overalls: Entity) -> None:
    world.say(
        f"{hero.id} wondered if the overalls hid something important, because {clue.smell}."
    )
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    overalls.meters["mystery"] = overalls.meters.get("mystery", 0.0) + 1


def reveal(world: World, hero: Entity, clue: Clue, overalls: Entity) -> None:
    world.say(
        f"At last, {hero.id} checked the pocket and found the truth: {clue.truth}."
    )
    world.facts["truth"] = clue.truth
    world.facts["resolved"] = True


def moral_choice(world: World, hero: Entity, value: MoralValue, companion: Entity) -> None:
    if value.id == "honesty":
        hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
        world.say(
            f"{hero.id} chose {value.action} and explained everything to {companion.label}."
        )
    elif value.id == "kindness":
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
        world.say(
            f"{hero.id} chose to {value.action} and did not make anyone feel small."
        )
    else:
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
        world.say(
            f"{hero.id} chose to {value.action}, even though the hallway felt a little spooky."
        )
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1


def tell(setting: Setting, clue: Clue, value: MoralValue, hero_name: str, gender: str, companion_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        trait=random.choice(TRAITS),
        meters={"attention": 0.0},
        memes={"doubt": 0.0, "suspicion": 0.0, "trust": 0.0, "peace": 0.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=companion_type,
        label=f"the {companion_type}",
        meters={},
        memes={},
    ))
    overalls = world.add(Entity(
        id="Overalls",
        kind="thing",
        type="overalls",
        label="overalls",
        phrase="a faded pair of overalls",
        owner=companion.id,
        worn_by=companion.id,
        meters={"mystery": 0.0},
        memes={},
    ))

    world.say(
        f"{hero.id} was a {hero.trait} {gender} who liked quiet places and tiny clues."
    )
    world.say(
        f"One day at {setting.place}, {hero.id} saw {clue.label} and felt a prickly little mystery in {hero.pronoun('possessive')} chest."
    )
    world.para()
    observe_clue(world, hero, clue)
    inner_monologue(world, hero, clue)
    suspect(world, hero, clue, overalls)
    world.say(
        f"{setting.detail}"
    )
    world.para()
    reveal(world, hero, clue, overalls)
    moral_choice(world, hero, value, companion)
    world.say(
        f"In the end, {hero.id} felt calm, because the clue made sense and {value.lesson}."
    )

    world.facts.update(hero=hero, companion=companion, clue=clue, value=value, overalls=overalls)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    value: MoralValue = f["value"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a young child that includes "{clue.label}", "beware", and "overalls".',
        f"Tell a gentle mystery about {hero.id} who notices {clue.label}, thinks carefully, and learns a moral lesson about {value.label}.",
        f"Write a tiny story with an inner monologue, a suspicious clue, and a kind ending near some overalls.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    value: MoralValue = f["value"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    overalls: Entity = f["overalls"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What strange thing did {hero.id} notice near the overalls?",
            answer=f"{hero.id} noticed {clue.label} near the overalls, and it made the room feel mysterious.",
        ),
        QAItem(
            question=f"What did {hero.id} think in {hero.pronoun('possessive')} inner monologue?",
            answer=f"{hero.id} thought that the clue was strange and that {hero.pronoun('subject')} should beware before guessing too fast.",
        ),
        QAItem(
            question=f"What truth did {hero.id} find after checking the overalls?",
            answer=f"{hero.id} found that {clue.truth}, so the mystery was solved.",
        ),
        QAItem(
            question=f"What moral value guided {hero.id}'s choice at the end?",
            answer=f"The story was guided by {value.label}, which meant {value.lesson}.",
        ),
        QAItem(
            question=f"Who did {hero.id} explain everything to at the end?",
            answer=f"{hero.id} explained everything to {companion.label}, so nobody had to stay confused.",
        ),
        QAItem(
            question=f"Were the overalls important to the mystery?",
            answer=f"Yes. The overalls were the place where the clue led {hero.id}, so they were part of the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story where something strange happens and the characters have to figure out what is true.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking voice inside their head.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of choosing, like honesty, kindness, or courage.",
        ),
        QAItem(
            question="What are overalls?",
            answer="Overalls are clothes with straps and a front piece, often worn over a shirt.",
        ),
        QAItem(
            question="What is pastrami?",
            answer="Pastrami is a seasoned meat often used in sandwiches, and it has a strong smell.",
        ),
        QAItem(
            question="What does beware mean?",
            answer="Beware means to be careful and watch out for possible trouble.",
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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id} ({ent.kind}/{ent.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.

valid(S, C, V, G) :- setting(S), clue(C), value(V), gender(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    for g in NAMES:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, c, v, g) for s in SETTINGS for c in CLUES for v in VALUES for g in NAMES}
    asps = set(asp_valid())
    if py == asps:
        print(f"OK: ASP and Python agree on {len(py)} combinations.")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - asps:
        print("Only in Python:", sorted(py - asps)[:20])
    if asps - py:
        print("Only in ASP:", sorted(asps - py)[:20])
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with clues, inner monologue, and moral values.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father", "teacher", "neighbor"])
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    value = args.value or rng.choice(list(VALUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(["mother", "father", "teacher", "neighbor"])
    return StoryParams(setting=setting, clue=clue, value=value, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        VALUES[params.value],
        params.name,
        params.gender,
        params.companion,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible (setting, clue, value, gender) combinations:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for clue in CLUES:
                for value in VALUES:
                    params = StoryParams(
                        setting=setting,
                        clue=clue,
                        value=value,
                        name="Mina",
                        gender="girl",
                        companion="mother",
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
