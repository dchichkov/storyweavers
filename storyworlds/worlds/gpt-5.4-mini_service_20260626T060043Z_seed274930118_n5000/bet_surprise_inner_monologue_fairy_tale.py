#!/usr/bin/env python3
"""
storyworlds/worlds/bet_surprise_inner_monologue_fairy_tale.py
==============================================================

A small fairy-tale storyworld about a child, a bet, a surprise,
and an inner monologue that helps turn boast into kindness.

Source seed image:
---
A little village girl is dared into a bet by a proud little lord. She must
bring back a moon-cup from the old willow before supper. On the path, she
thinks to herself that she is scared, but she notices a hidden fairy who
needs help. The fairy surprises her by revealing the cup was never on the
branch at all; it was nested in the willow root. The girl wins the bet by
being gentle, not greedy.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("distance", "risk", "help", "bright", "lost"):
            self.meters.setdefault(k, 0.0)
        for k in ("hope", "fear", "pride", "kindness", "surprise", "resolve", "worry", "relief", "shame"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "queen", "fairy"}
        male = {"boy", "prince", "father", "king", "lord", "troll", "boyish"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    quest: str
    verb: str
    place: str
    prize: str
    challenge: str
    hidden_help: str
    surprise_reveal: str
    keyword: str = "bet"


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "willow": Place(id="willow", label="the old willow", kind="tree", affords={"fetch"}),
    "bridge": Place(id="bridge", label="the mossy bridge", kind="bridge", affords={"fetch"}),
    "meadow": Place(id="meadow", label="the moonlit meadow", kind="field", affords={"fetch"}),
}

TASKS = {
    "mooncup": Task(
        id="mooncup",
        quest="fetch the moon-cup",
        verb="bring back the moon-cup",
        place="willow",
        prize="mooncup",
        challenge="the branch looks too high",
        hidden_help="a tiny fairy hiding in the roots",
        surprise_reveal="the cup was never on the branch; it was in the roots all along",
    ),
    "starbell": Task(
        id="starbell",
        quest="fetch the star-bell",
        verb="find the star-bell",
        place="meadow",
        prize="starbell",
        challenge="the grass hides every shining thing",
        hidden_help="a sleepy moth with silver wings",
        surprise_reveal="the bell was tucked inside a hollow stone",
    ),
}

PRIZES = {
    "mooncup": Prize(id="mooncup", label="moon-cup", phrase="a little silver moon-cup", type="cup", region="hand"),
    "starbell": Prize(id="starbell", label="star-bell", phrase="a bright little star-bell", type="bell", region="hand"),
}

HERO_NAMES = ["Mira", "Elin", "Sana", "Lina", "Tessa"]
RIVAL_NAMES = ["Lord Bram", "Prince Rowan", "Lord Ivo", "Prince Alder"]
TRAITS = ["brave", "small", "quick-witted", "gentle", "curious"]


@dataclass
class StoryParams:
    place: str
    task: str
    hero_name: str
    rival_name: str
    hero_trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bet storyworld with surprise and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--rival", choices=RIVAL_NAMES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TASKS if p == TASKS[t].place]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or args.place == c[0])
              if (args.task is None or args.task == c[1])]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, task = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    rival_name = args.rival or rng.choice(RIVAL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, hero_name=hero_name, rival_name=rival_name, hero_trait=trait)


def _inner_thought(world: World, hero: Entity, text: str) -> None:
    world.say(f"Inside, {hero.pronoun('subject')} thought, “{text}”")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    prize = PRIZES[task.prize]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    rival = world.add(Entity(id=params.rival_name, kind="character", type="lord", label=params.rival_name))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label="a tiny fairy"))

    hero.memes["hope"] += 1
    rival.memes["pride"] += 1
    world.say(f"Once in a little village, {hero.id} was a {params.hero_trait} girl who loved fair riddles and winding paths.")
    world.say(f"One bright evening, {rival.label} made a {task.keyword} with {hero.id}: if she could {task.verb} from {place.label}, she would win a ribbon of blue silk.")
    _inner_thought(world, hero, "I am not afraid, but I do not like a boastful smile.")
    world.say(f"{hero.id} walked to {place.label}, where the air was cool and the leaves whispered like bedtime songs.")
    world.say(f"The task seemed hard because {task.challenge}.")
    hero.memes["fear"] += 1
    hero.memes["resolve"] += 1
    _inner_thought(world, hero, "If I hurry, I may fail. If I look carefully, I may learn.")
    world.say(f"Then {hero.id} noticed {task.hidden_help}.")
    fairy.memes["surprise"] += 1
    hero.memes["surprise"] += 1
    hero.memes["kindness"] += 1
    world.say(f"With a sudden smile, the fairy surprised her and whispered that {task.surprise_reveal}.")
    world.say(f"{hero.id} did not snatch or shake the branches. Instead, she knelt by the roots and looked in the shadowed curl of wood.")
    world.say(f"There lay the {prize.label}, shining softly as a sleeping moon.")
    world.say(f"{hero.id} lifted it with careful hands and carried it back as the evening bells began to ring.")
    hero.memes["relief"] += 1
    rival.memes["shame"] += 1
    world.say(f"{rival.label} blinked in surprise, for the bet was won by patience, not boasting.")
    world.say(f"{hero.id} smiled and gave the ribbon back to the village child who needed it more, and that made the little world feel kinder than before.")

    world.facts.update(hero=hero, rival=rival, fairy=fairy, prize=prize, task=task, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story about a child named {f["hero"].id} who accepts a {f["task"].keyword} and learns something surprising.',
        f"Tell a gentle story where {f['hero'].id} uses an inner monologue to stay brave during a test at {f['place'].label}.",
        f"Write a short fairy tale about a bet, a hidden helper, and a surprise ending with a moonlit treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, prize, task = f["hero"], f["rival"], f["prize"], f["task"]
    return [
        QAItem(
            question=f"What was the bet between {hero.id} and {rival.label}?",
            answer=f"{rival.label} made a bet with {hero.id}: if {hero.id} could {task.verb}, she would win a ribbon of blue silk.",
        ),
        QAItem(
            question=f"What did {hero.id} think to herself when the task looked hard?",
            answer="She thought that she was not afraid, but she did not like a boastful smile, and that looking carefully might help her learn.",
        ),
        QAItem(
            question=f"Where did {hero.id} finally find the {prize.label}?",
            answer=f"She found the {prize.label} in the shadowed roots of {f['place'].label}, not up on the branch.",
        ),
        QAItem(
            question=f"How did the surprise help {hero.id} win?",
            answer="The surprise showed her where to look, so she used patience and careful hands instead of rushing or grabbing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bet?",
            answer="A bet is a promise that one person will win if they can do a challenge better or first.",
        ),
        QAItem(
            question="What does an inner monologue mean?",
            answer="An inner monologue is the little voice a character thinks in their own head.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
place(willow). place(bridge). place(meadow).
task(mooncup). task(starbell).

task_place(mooncup, willow).
task_place(starbell, meadow).

valid(P, T) :- place(P), task(T), task_place(T, P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
        lines.append(asp.fact("task_place", t, TASKS[t].place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        mem = {k: v for k, v in e.memes.items() if v}
        met = {k: v for k, v in e.meters.items() if v}
        bits = []
        if mem:
            bits.append(f"memes={mem}")
        if met:
            bits.append(f"meters={met}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


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
    StoryParams(place="willow", task="mooncup", hero_name="Mira", rival_name="Lord Bram", hero_trait="quick-witted"),
    StoryParams(place="meadow", task="starbell", hero_name="Lina", rival_name="Prince Rowan", hero_trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
