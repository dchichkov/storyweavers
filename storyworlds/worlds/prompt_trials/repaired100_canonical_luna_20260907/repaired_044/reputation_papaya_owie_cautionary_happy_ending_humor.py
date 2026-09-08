#!/usr/bin/env python3
"""
A small Animal Story world about reputation, a papaya, and an owie.

A proud animal hurries to prove a grand reputation, slips while carrying a
papaya, and learns that careful help matters more than looking brave. The
ending is happy, gentle, and a little funny.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("balance", "softness", "distance", "pain"):
            self.meters.setdefault(key, 0.0)
        for key in ("reputation", "pride", "worry", "kindness", "joy", "humor"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    surface: str


@dataclass(frozen=True)
class Trial:
    id: str
    task: str
    warning: str
    mistake: str
    clue: str
    helper_action: str
    twist: str
    repair: str
    ending: str
    snack: str
    lesson: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


PLACES = {
    "orchard": Place("orchard", "the papaya orchard", "a springy path"),
    "riverbank": Place("riverbank", "the sunny riverbank", "a pebbly path"),
    "garden": Place("garden", "the village garden", "a leafy path"),
}

ANIMALS = {
    "monkey": {"label": "monkey", "trait": "quick"},
    "parrot": {"label": "parrot", "trait": "chatty"},
    "tortoise": {"label": "tortoise", "trait": "steady"},
    "lemur": {"label": "lemur", "trait": "curious"},
    "rabbit": {"label": "rabbit", "trait": "springy"},
}

NAMES = ["Luna", "Owie", "Mimi", "Pip", "Coco", "Nori", "Tala", "Bobo"]

TRIALS = [
    Trial(
        "rolling_papaya",
        "carry a ripe papaya to the picnic stump",
        "The papaya was round, heavy, and much slipperier than it looked.",
        "tried to balance it on one paw while bowing to the crowd",
        "a bent leaf showed that the papaya had already started rolling downhill",
        "placed a vine around the fruit and asked everyone to walk slowly",
        "the papaya was not attacking anyone; it was simply practicing its own downhill idea",
        "washed the fruit, wrapped it in leaves, and shared it in careful slices",
        "The animals cheered as the papaya sat safely in a bowl, wearing a tiny leaf hat.",
        "papaya slices",
        "A good reputation grows when brave-looking creatures also make careful choices.",
    ),
    Trial(
        "papaya_bridge",
        "carry a papaya across a little branch bridge",
        "The branch bridge wobbled whenever a heavy foot hurried over it.",
        "rushed with the papaya and stepped on a loose twig",
        "the bridge dipped before the fruit slipped",
        "held the bridge steady while another animal fetched a basket",
        "the bridge, not the carrier, had made the frightening wobble",
        "crossed one at a time and carried the papaya in the basket",
        "The papaya reached the picnic while the repaired bridge wore two bright ribbons.",
        "papaya-and-banana cups",
        "Reputation is safer when a friend can help before a small danger becomes a big one.",
    ),
    Trial(
        "papaya_sneeze",
        "present a papaya at the animal welcome feast",
        "A cloud of papaya pollen tickled every nose near the table.",
        "held the fruit high and sneezed it toward a sleeping hedgehog",
        "the sneeze came just before the fruit tipped",
        "caught the papaya with a broad leaf and moved the feast downwind",
        "the great dramatic roar was only a sneeze wearing a very silly hat",
        "apologized, checked the hedgehog, and served the fruit outdoors",
        "The hedgehog woke to a plate of papaya and gave the sneeze a sleepy thumbs-up.",
        "cool papaya cubes",
        "When a mistake happens, a quick apology can protect trust.",
    ),
]


ASP_RULES = r"""
place(orchard). place(riverbank). place(garden).
trial(rolling_papaya). trial(papaya_bridge). trial(papaya_sneeze).
caution(trial) :- trial(_).
happy_ending(trial) :- trial(_).
humor(trial) :- trial(_).
valid_story(P,T) :- place(P), trial(T), caution(trial), happy_ending(trial), humor(trial).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for place in PLACES:
        facts.append(asp.fact("place", place))
    for trial in TRIALS:
        facts.append(asp.fact("trial", trial.id))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: "StoryParams") -> None:
    if params.place not in PLACES:
        raise StoryError("That place is not part of the papaya story world.")
    if params.trial not in {trial.id for trial in TRIALS}:
        raise StoryError("That trial is not part of the papaya story world.")
    if params.hero_kind not in ANIMALS:
        raise StoryError("That hero animal is not in the animal registry.")
    if params.helper_kind not in ANIMALS:
        raise StoryError("That helper animal is not in the animal registry.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper need different names.")
    if params.hero_kind == params.helper_kind and params.hero == params.helper:
        raise StoryError("The hero and helper cannot be the same character.")


@dataclass
class StoryParams:
    place: str
    trial: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    trial = next(item for item in TRIALS if item.id == params.trial)
    hero_info = ANIMALS[params.hero_kind]
    helper_info = ANIMALS[params.helper_kind]

    world = World(place)
    hero = world.add(Entity(params.hero, "character", params.hero_kind, params.hero))
    helper = world.add(Entity(params.helper, "character", params.helper_kind, params.helper))
    papaya = world.add(Entity("papaya", "thing", "fruit", "papaya", owner=hero.id))

    openings = [
        f"At {place.name}, {params.hero} the {hero_info['label']} polished a reputation for being wonderfully {hero_info['trait']}.",
        f"Everyone in {place.name} knew {params.hero} the {hero_info['label']} had a very important reputation: always brave, always ready, and sometimes too ready.",
        f"One bright morning at {place.name}, {params.hero} the {hero_info['label']} announced that a new adventure would improve an already famous reputation.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.helper} the {helper_info['label']} came along because {params.hero} had promised to {trial.task}. "
        f"{params.helper} carried a basket, while {params.hero} carried a large papaya."
    )
    world.say("The animals smiled, and one small bird began keeping score with a crumb of toast.")
    world.para()

    hero.memes["reputation"] = 2
    hero.memes["pride"] = 2
    papaya.meters["softness"] = 2
    papaya.meters["distance"] = 1
    world.say(f"But {trial.warning} {trial.clue.capitalize()}.")
    world.say(f'"I can do this without slowing down," said {params.hero}. "My reputation is counting on me."')
    world.say(f'"Your reputation can wait one little minute," said {params.helper}. "Your toes should not have to."')
    world.para()

    hero.meters["balance"] -= 2
    hero.meters["pain"] += 1
    hero.memes["pride"] += 1
    helper.memes["worry"] += 2
    world.say(f"{params.hero} {trial.mistake}, and the papaya made a soft plop.")
    world.say(f"That plop was followed by an owie: {params.hero} bumped a paw and sat down with a surprised squeak.")
    world.say(f"The animals gasped, but {params.helper} stayed calm. {trial.clue.capitalize()}.")
    world.say(f'"Tell me where it hurts," said {params.helper}. "We can fix the fruit and the frown together."')
    world.say(f'"My paw is sore, and my reputation is wobbling," admitted {params.hero}.')
    world.say(f'"Then let us steady both," said {params.helper}.')
    world.para()

    helper.memes["kindness"] = 3
    hero.memes["pride"] = 0
    hero.memes["reputation"] = 3
    hero.memes["joy"] = 2
    papaya.meters["distance"] = 0
    papaya.meters["softness"] = 1
    world.say(f"{params.helper} {trial.helper_action}.")
    world.say(f"The funny twist was that {trial.twist}.")
    world.say(f"{params.hero} apologized, accepted the careful plan, and {trial.repair}.")
    world.say(f"Then the animals shared {trial.snack}. {trial.lesson}")
    world.say(f"At the end, {trial.ending}")
    world.say("The bird erased its scorecard and replaced it with one word: careful.")

    world.facts.update(
        place=params.place,
        trial=trial.id,
        hero=params.hero,
        helper=params.helper,
        hero_kind=params.hero_kind,
        helper_kind=params.helper_kind,
        task=trial.task,
        warning=trial.warning,
        mistake=trial.mistake,
        clue=trial.clue,
        helper_action=trial.helper_action,
        twist=trial.twist,
        repair=trial.repair,
        ending=trial.ending,
        snack=trial.snack,
        lesson=trial.lesson,
        owie=True,
        reputation_changed=True,
        papaya=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write an Animal Story about {facts['hero']} and a papaya at {PLACES[facts['place']].name}.",
        f"Tell a cautionary but funny story where {facts['hero']} gets an owie after ignoring a warning.",
        f"Write a happy ending in which {facts['helper']} helps repair {facts['hero']}'s reputation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Where did {f['hero']} carry the papaya?",
            f"{f['hero']} carried it through {PLACES[f['place']].name}.",
        ),
        QAItem(
            "Why did the owie happen?",
            f"The owie happened because {f['hero']} {f['mistake']}.",
        ),
        QAItem(
            "What clue warned the animals?",
            f"The warning clue was that {f['clue']}.",
        ),
        QAItem(
            f"How did {f['helper']} help?",
            f"{f['helper']} {f['helper_action']}.",
        ),
        QAItem(
            "What changed about the hero's reputation?",
            f"The hero learned that a good reputation grows from careful choices, accepting help, and repairing mistakes.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a reputation?", "A reputation is what others come to expect about someone from that person's actions."),
        QAItem("What is a papaya?", "A papaya is a soft tropical fruit with sweet orange flesh."),
        QAItem("What is an owie?", "An owie is a small hurt or sore spot that needs gentle care."),
        QAItem("What is a cautionary story?", "A cautionary story shows a danger so characters can learn to make safer choices."),
        QAItem("What makes an ending happy?", "A happy ending shows that the problem has been repaired and the characters are safe or joyful."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place.name}"]
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{ {meters} }} memes={{ {memes} }}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal Story world about reputation, papaya, and an owie.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--trial", choices=[trial.id for trial in TRIALS])
    parser.add_argument("--hero")
    parser.add_argument("--hero-kind", choices=sorted(ANIMALS))
    parser.add_argument("--helper")
    parser.add_argument("--helper-kind", choices=sorted(ANIMALS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_kind = args.hero_kind or rng.choice(sorted(ANIMALS))
    helper_kind = args.helper_kind or rng.choice([kind for kind in ANIMALS if kind != hero_kind])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        trial=args.trial or rng.choice([trial.id for trial in TRIALS]),
        hero=hero,
        hero_kind=hero_kind,
        helper=helper,
        helper_kind=helper_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("orchard", "rolling_papaya", "Luna", "monkey", "Owie", "tortoise"),
    StoryParams("riverbank", "papaya_bridge", "Pip", "rabbit", "Mimi", "parrot"),
    StoryParams("garden", "papaya_sneeze", "Coco", "lemur", "Nori", "tortoise"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {(place, trial.id) for place in PLACES for trial in TRIALS}
    if actual != expected:
        print("MISMATCH between ASP and Python registries.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "papaya" not in sample.story.lower() or "owie" not in sample.story.lower():
            print("MISMATCH: generated story is missing required narrative facts.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(actual)} shapes).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid story shapes:")
        for place, trial in values:
            print(f"  {place} / {trial}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} / {sample.params.helper} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
