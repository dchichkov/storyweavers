#!/usr/bin/env python3
"""
A small superhero quest about Duplo, courage, and the moral value of helping.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = (
    "a bright playroom beneath the city library",
    "a cozy apartment where rain tapped the windows",
    "a little clubhouse beside the community garden",
    "a sunny classroom after the other children had gone home",
)

HEROES = (
    ("Luna", "girl"),
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Theo", "boy"),
    ("Sam", "child"),
)

HELPERS = (
    ("Pip", "small robot"),
    ("Bramble", "friendly dog"),
    ("Zee", "inventor"),
    ("Tara", "neighbor"),
)

QUESTS = (
    {
        "object": "a Duplo bridge",
        "danger": "the toy dragon could not cross the stream of blue blocks",
        "clue": "a red Duplo brick beside the pretend river",
        "act": "shared the strongest pieces instead of saving them for a private tower",
        "place": "the Duplo city by the window",
        "ending": "the dragon rolled safely across the bright bridge",
    },
    {
        "object": "a Duplo rescue cart",
        "danger": "the tiny toy villagers were stranded beyond a wall of cushions",
        "clue": "yellow Duplo wheels near the fallen cushion wall",
        "act": "asked each builder for one brick and listened to every idea",
        "place": "the blanket mountain",
        "ending": "the rescue cart carried every villager home",
    },
    {
        "object": "a Duplo lighthouse",
        "danger": "the toy boats were lost in a dark sea made of blue bricks",
        "clue": "a white Duplo window glowing under the table",
        "act": "let the smallest builder place the final bright brick",
        "place": "the blue-block harbor",
        "ending": "the boats followed the lighthouse beam into the harbor",
    },
    {
        "object": "a Duplo space station",
        "danger": "the toy astronauts had no safe place to land",
        "clue": "a green Duplo plate beside the cushion rocket",
        "act": "gave up the tallest tower pieces so everyone could build a landing pad",
        "place": "the rug's pretend moon",
        "ending": "the astronauts landed and waved from the new station",
    },
)

MORALS = (
    "A real hero makes room for others.",
    "Sharing your strength can make everyone stronger.",
    "Courage listens before it acts.",
    "Kindness is a superpower that grows when it is shared.",
)

ENDING_IMAGES = (
    "Luna's cape rested beside the Duplo bricks while the whole team planned tomorrow's adventure.",
    "The finished Duplo build gleamed in the window, and every helper had a place inside it.",
    "As the room grew quiet, the rescued toys stood together beneath a little block-built star.",
)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    hero_type: str = "girl"
    helper_name: str = "Pip"
    helper_type: str = "small robot"
    setting: str = SETTINGS[0]
    quest: dict = field(default_factory=lambda: dict(QUESTS[0]))
    moral: str = MORALS[0]
    ending_image: str = ENDING_IMAGES[0]


def _pronoun(entity: Entity, case: str = "subject") -> str:
    if entity.kind == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if entity.kind == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")
    if not params.quest or "object" not in params.quest:
        raise StoryError("The quest needs a concrete Duplo object.")

    world = World()
    hero = world.add(Entity(
        "hero",
        params.hero_type,
        params.hero_name,
        meters={"energy": 1.0},
        memes={"curiosity": 1.0, "kindness": 0.0, "courage": 0.0},
    ))
    helper = world.add(Entity(
        "helper",
        params.helper_type,
        params.helper_name,
        meters={"energy": 1.0},
        memes={"trust": 1.0},
    ))
    duplo = world.add(Entity(
        "duplo",
        "toy",
        params.quest["object"],
        meters={"stability": 0.3},
        memes={"shared": 0.0, "hope": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, duplo=duplo, quest=params.quest)

    world.say(
        f"In {params.setting}, {hero.label} wore a blue cape and watched over a wonderful "
        f"Duplo world."
    )
    world.say(
        f"One afternoon, {params.quest['danger'].capitalize()}. The pieces of {params.quest['object']} "
        f"were scattered across the floor."
    )

    world.para()
    world.say(
        f"{hero.label} spotted {params.quest['clue']} and hurried to {params.quest['place']}."
    )
    world.say(
        f'"I can fix everything alone," {hero.label} said. '
        f'"A hero does not leave anyone behind," {helper.label} replied.'
    )
    hero.memes["courage"] += 1.0
    hero.memes["kindness"] += 1.0
    world.fired.add("dialogue")

    world.say(
        f"{hero.label} listened, then {params.quest['act']}. "
        f"Together, the builders clicked the Duplo pieces into place."
    )
    duplo.meters["stability"] = 1.0
    duplo.memes["shared"] = 1.0
    hero.memes["kindness"] += 1.0
    world.fired.add("sharing")

    world.para()
    world.say(
        f"The quest was complete: {params.quest['ending'].capitalize()}. "
        f"{hero.label} smiled as every toy found a safe place."
    )
    world.say(f'"We did it together," {hero.label} said. {helper.label} gave a happy beep.')
    world.say(f"{params.moral} {params.ending_image}")
    world.fired.add("resolved")
    return world


ASP_RULES = r"""
duplo_quest.
needs_help.
hero_has_courage.
hero_shares.
quest_complete :- duplo_quest, needs_help, hero_has_courage, hero_shares.
moral_learned :- quest_complete.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("duplo_quest"),
        asp.fact("needs_help"),
        asp.fact("hero_has_courage"),
        asp.fact("hero_shares"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_complete/0.\n#show moral_learned/0."))
    complete = bool(asp.atoms(model, "quest_complete"))
    moral = bool(asp.atoms(model, "moral_learned"))
    if complete and moral:
        print("OK: ASP and Python agree that the shared Duplo quest is complete.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = args.seed if args.seed is not None else 0
    hero_name, hero_type = HEROES[seed % len(HEROES)]
    helper_name, helper_type = HELPERS[(seed // len(HEROES)) % len(HELPERS)]
    return StoryParams(
        seed=seed,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        setting=rng.choice(SETTINGS),
        quest=dict(rng.choice(QUESTS)),
        moral=rng.choice(MORALS),
        ending_image=rng.choice(ENDING_IMAGES),
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    return [
        "Write a superhero story about a child, Duplo, and the moral value of helping.",
        f"Tell a quest in which {hero.label} must solve this problem: {quest['danger']}.",
        "Show how sharing changes the ending of a heroic Duplo adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What quest did {hero.label} face?",
            answer=f"{hero.label} had to build {quest['object']} because {quest['danger']}.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the quest?",
            answer=f"{hero.label} solved it by {quest['act']}, then working with {helper.label} to connect the Duplo pieces.",
        ),
        QAItem(
            question=f"What did {hero.label} learn?",
            answer=f"{hero.label} learned that {world.facts.get('moral', 'sharing helps everyone')}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Duplo?",
            answer="Duplo is a set of large, colorful building bricks made for young children to connect and use in creative play.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle that helps someone choose how to treat other people, such as kindness, honesty, or fairness.",
        ),
        QAItem(
            question="Why can teamwork help on a quest?",
            answer="Teamwork combines different ideas and abilities, so people can solve a difficult problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["moral"] = params.moral
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
    parser = argparse.ArgumentParser(description="A Duplo superhero moral-value quest.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/0.\n#show moral_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_complete/0.\n#show moral_learned/0."))
        print(sorted(set(asp.atoms(model, "quest_complete"))))
        print(sorted(set(asp.atoms(model, "moral_learned"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else max(1, args.n)
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(argparse.Namespace(seed=seed), random.Random(seed))
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
