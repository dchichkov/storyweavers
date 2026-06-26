#!/usr/bin/env python3
"""
A small mythic story world: a child cannot read, a strange advantage seems terrible,
and a shared mystery leads to reconciliation.

The premise is built from a seed tale in which a village notices a quiet person
who cannot read the old signs. The person is mocked for being illiterate, then
appears to have a terrible advantage: they can feel a hidden path by touch and
memory, while others cannot. A mystery to solve pulls the village toward a
choice between pride and repair, and the ending turns on reconciliation.
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
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    feature: str
    mood: str = "old"


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_truth: str
    danger: str
    solved_by: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mystery_solved: bool = False

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


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    setting: str
    seed: Optional[int] = None


GIRL_NAMES = ["Asha", "Mira", "Nila", "Suri", "Tala", "Iva"]
BOY_NAMES = ["Orin", "Ravi", "Kian", "Bela", "Taro", "Malo"]
COMPANIONS = ["mother", "father", "grandmother", "brother", "sister"]

SETTINGS = {
    "grove": Setting(place="the moonlit grove", feature="an old stone arch", mood="ancient"),
    "river": Setting(place="the river bend", feature="a bridge of roots", mood="wild"),
    "hill": Setting(place="the wind hill", feature="a ring of standing stones", mood="high"),
}

MYSTERIES = {
    "arch": Mystery(
        id="arch",
        clue="the runes on the stone arch were worn smooth where small hands had touched them",
        hidden_truth="a hidden door opened only when someone traced the marks by memory, not by reading",
        danger="the village feared the arch because no one could read the warning carved above it",
        solved_by="tracing the worn rune with a finger and speaking the old names aloud",
    ),
    "bridge": Mystery(
        id="bridge",
        clue="the root-bridge sang only when the water was low and the wind was kind",
        hidden_truth="the song was a map, guiding travelers across the river safely",
        danger="the village thought the bridge was a trap because the signs were written in forgotten script",
        solved_by="listening to the bridge and following its rhythm step by step",
    ),
    "stones": Mystery(
        id="stones",
        clue="the standing stones cast one shadow that looked like a sleeping gate",
        hidden_truth="the gate opened when two feuding kin stood together and named the same star",
        danger="the village called the hill cursed because the directions were too old to read",
        solved_by="reconciliation between rivals and the shared naming of the star",
    ),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
mystery_site(grove, arch).
mystery_site(river, bridge).
mystery_site(hill, stones).

place_feature(grove, ancient).
place_feature(river, wild).
place_feature(hill, high).

needs_reconciliation(stones).
needs_touch_reading(arch).
needs_listening(bridge).

valid_story(Place, Mystery) :- mystery_site(Place, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("place_feature", key, setting.feature))
    for key, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_site", mystery.id, key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, m) for s, m in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative world
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["illiterate", "courageous", "quiet"],
        memes={"hurt": 0.0, "hope": 0.0, "reconciliation": 0.0},
    ))
    kin = world.add(Entity(
        id="Kin",
        kind="character",
        type=params.companion,
        label=f"the {params.companion}",
        memes={"pride": 0.0, "regret": 0.0, "love": 0.0},
    ))
    mystery = MYSTERIES[params.setting if params.setting in MYSTERIES else "arch"]
    if params.setting == "grove":
        mystery = MYSTERIES["arch"]
    elif params.setting == "river":
        mystery = MYSTERIES["bridge"]
    else:
        mystery = MYSTERIES["stones"]

    world.facts.update(hero=hero, kin=kin, mystery=mystery, params=params)
    return world


def intro(world: World) -> None:
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    setting = world.setting
    world.say(
        f"Long ago, in {setting.place}, there lived {hero.id}, a little one who was "
        f"illiterate and ashamed of it."
    )
    world.say(
        f"{hero.id} traveled with {kin.label}, and the old people whispered that "
        f"the {setting.feature} kept a terrible advantage for whoever could understand it."
    )


def build_tension(world: World) -> None:
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    mystery = world.facts["mystery"]
    world.para()
    world.say(f"The village feared the place, for {mystery.danger}.")
    world.say(
        f"Yet {hero.id} noticed {mystery.clue}, and that seemed like a terrible advantage: "
        f"{hero.pronoun('subject').capitalize()} could not read the signs, but {hero.pronoun('subject')} could feel their truth."
    )
    kin.memes["pride"] += 1
    hero.memes["hurt"] += 1
    world.say(
        f"The {world.facts['params'].companion} laughed at first, calling {hero.id} foolish, "
        f"which made {hero.pronoun('object')} go quiet."
    )


def solve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    mystery = world.facts["mystery"]
    params = world.facts["params"]
    world.para()
    if mystery.id == "stones":
        world.say(
            f"At the end of the wind, {hero.id} asked {kin.label} to stand beside "
            f"{hero.pronoun('object')} and speak the shared star-name."
        )
        world.say(
            f"They did so, and the standing stones answered with a deep hum. "
            f"The old gate opened because reconciliation was the true key."
        )
    elif mystery.id == "bridge":
        world.say(
            f"{hero.id} listened to the root-bridge until the rhythm became a map. "
            f"{kin.label} followed the beat, step by careful step."
        )
        world.say(
            f"When they reached the far bank, the hidden way made sense at last, "
            f"and the village saw that the bridge had been trying to help, not harm."
        )
    else:
        world.say(
            f"{hero.id} traced the worn arch with one small finger, though {hero.pronoun('subject')} could not read a single rune."
        )
        world.say(
            f"The stone door opened, for the mystery had always listened to touch and memory."
        )
    hero.memes["hope"] += 1
    kin.memes["regret"] += 1
    kin.memes["love"] += 1
    world.mystery_solved = True
    world.say(
        f"The {params.companion} bowed their head and begged pardon for the cruel words."
    )
    hero.memes["reconciliation"] += 1
    kin.memes["reconciliation"] = kin.memes.get("reconciliation", 0.0) + 1


def resolution(world: World) -> None:
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    world.para()
    world.say(
        f"{hero.id} forgave the {world.facts['params'].companion}, and the two walked home together."
    )
    world.say(
        f"By dawn, the village spoke of {hero.id} not as illiterate, but as wise in a different way: "
        f"{hero.pronoun('subject').capitalize()} could not read the old marks, yet {hero.pronoun('subject')} had solved the mystery to solve."
    )
    world.say(
        f"The terrible advantage had become a gift shared by all, and reconciliation sat over {world.setting.place} like a warm star."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    build_tension(world)
    solve_mystery(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Generation / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    return [
        f"Write a mythic story about {p.name}, an illiterate child, whose strange gift seems like a terrible advantage.",
        f"Tell a short legend set at {world.setting.place} where a mystery to solve leads to reconciliation.",
        f"Write a child-friendly myth about a forgotten sign, a family quarrel, and the old truth hidden in {m.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    kin = world.facts["kin"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {p.name}, a little {p.gender} who was illiterate but brave enough to face the old mystery.",
        ),
        QAItem(
            question=f"Why did the village call the advantage terrible?",
            answer=f"They called it terrible because the old signs looked frightening and no one trusted the hidden path at first, even though {p.name}'s way of noticing things could help.",
        ),
        QAItem(
            question=f"What was the mystery to solve in the story?",
            answer=f"The mystery was about {mystery.clue}. Its hidden truth was that {mystery.hidden_truth}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation: {p.name} forgave the {p.companion}, the truth was revealed, and the village learned to honor a different kind of wisdom.",
        ),
        QAItem(
            question=f"How did {kin.label} change?",
            answer=f"{kin.label} stopped laughing, grew sorry, and came to love and respect {hero.id}'s quiet gift.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does illiterate mean?",
            answer="Illiterate means a person cannot read or write yet. That does not mean the person cannot notice, remember, or understand many other things.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were hurt or angry make peace again and come back together with kindness.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something hidden or puzzling that people try to understand by looking, listening, and thinking carefully.",
        ),
        QAItem(
            question="What is an advantage?",
            answer="An advantage is a helpful strength or edge that makes something easier or better for someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind}/{e.type} memes={e.memes} meters={e.meters}")
    lines.append(f"mystery_solved={world.mystery_solved}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with a mystery and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(name=name, gender=gender, companion=companion, setting=setting)


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
    StoryParams(name="Asha", gender="girl", companion="mother", setting="grove"),
    StoryParams(name="Orin", gender="boy", companion="father", setting="river"),
    StoryParams(name="Mira", gender="girl", companion="grandmother", setting="hill"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, mystery in combos:
            print(f"  {place} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
