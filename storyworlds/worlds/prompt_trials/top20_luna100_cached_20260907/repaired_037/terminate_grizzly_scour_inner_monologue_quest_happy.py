#!/usr/bin/env python3
"""
A child-friendly superhero quest about Luna, a grizzly bear, and a search
that ends with a happy helping hand.

The story uses an inner monologue as Luna thinks through a problem, but all
important choices are shown through action and dialogue.
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

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    key: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    grizzly_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    thought: int = 0
    turn: int = 0
    ending: int = 0


SETTINGS = {
    "mountain_trail": Setting(
        "mountain_trail",
        "the moonlit mountain trail",
        {"trail", "cave", "stream"},
    ),
    "forest_camp": Setting(
        "forest_camp",
        "the quiet forest camp",
        {"trail", "campfire", "stream"},
    ),
    "pine_valley": Setting(
        "pine_valley",
        "the bright pine valley",
        {"trail", "meadow", "stream"},
    ),
}

HERO_NAMES = ["Luna", "Mira", "Nova", "Skye", "Zara", "Piper"]
GRIZZLY_NAMES = ["Bruno", "Bramble", "Honey", "Moss", "Gus", "Bear"]

OPENINGS = [
    "At sunset, {hero}, the superhero of the northern hills, followed a silver trail through {place}.",
    "When the evening clouds turned pink, superhero {hero} checked the paths around {place}.",
    "A cool wind swept across {place}, and {hero} tightened her bright blue cape before beginning a rescue quest.",
    "The small alarm on {hero}'s hero belt blinked beside {place}. Something needed careful help.",
    "{hero} loved ordinary rescues best, so she flew low over {place} and listened to the sounds below.",
]

THOUGHTS = [
    '"I could rush in," {hero} thought, "but a true hero first learns what is wrong."',
    '"Bravery is not being loud," {hero} told herself. "It is choosing the safest helpful step."',
    '"If I follow the clues instead of my fear, I may find the answer," {hero} thought.',
    '"The quest is not to defeat someone," {hero} reminded herself. "It is to protect a friend."',
    '"Slow eyes, kind hands, clear words," {hero} thought as she studied the trail.',
]

TURNS = [
    "The mark was not a monster's footprint at all. It was a torn blue ribbon caught on a thorn, and the trail led toward the stream.",
    "The loud growl was not an attack. It was a hungry, frightened grizzly calling from behind a fallen pine.",
    "The dark shape was only a broken camp sign leaning in the wind, but something large had brushed against it.",
    "The shining scratches belonged to a rescue sled that had slipped downhill and stopped beside a muddy bank.",
    "The mystery became clear when a tiny bell rang from the brambles. A lost pack had tangled there, and its owner was nearby.",
]

INCIDENTS = [
    {
        "clue": "three deep paw prints beside a row of silver stones",
        "risk": "charge toward the sound",
        "cause": "a young grizzly had slipped behind a fallen log while searching for berries",
        "repair": "Luna used her cape as a bright flag, guided the grizzly around the log, and led him to a safe berry patch",
        "lesson": "a frightening clue can become a helping quest when you gather facts first",
        "ending": "The grizzly carried a basket of berries to his family, and Luna's cape glowed warmly beneath the stars.",
    },
    {
        "clue": "a deep growl echoing from the mouth of a rocky cave",
        "risk": "enter the cave alone",
        "cause": "a grizzly cub was calling because a fallen branch blocked the cave entrance",
        "repair": "Luna called to the cub, then lifted the branch only after the mother grizzly moved to a safe distance",
        "lesson": "even a superhero needs patience, distance, and a plan",
        "ending": "The cub waddled back to its mother, while Luna watched the cave become quiet and safe.",
    },
    {
        "clue": "muddy claw marks crossing the path toward the camp",
        "risk": "scour the woods without telling anyone",
        "cause": "a grizzly had followed the smell of a forgotten lunch bag",
        "repair": "Luna asked the campers to stand together, helped them pack the food away, and guided the grizzly back toward the forest",
        "lesson": "good choices can protect both people and wild animals",
        "ending": "The campers shared a grateful wave, and the grizzly disappeared among the pines without finding another snack.",
    },
    {
        "clue": "a red scarf snagged high in a pine tree",
        "risk": "climb the slippery trunk immediately",
        "cause": "a grizzly had tugged the scarf loose while passing beneath the tree",
        "repair": "Luna lowered the scarf with her rescue line and checked that nobody had left food near the roots",
        "lesson": "a careful tool is better than a dangerous shortcut",
        "ending": "The scarf flew home like a tiny flag, and the bear wandered peacefully toward the valley.",
    },
    {
        "clue": "a stream of paw prints ending beside a quiet waterfall",
        "risk": "cross the wet rocks by herself",
        "cause": "a grizzly had stopped there because a shiny can was stuck between two stones",
        "repair": "Luna anchored her safety rope, removed the can, and carried it to the camp's recycling box",
        "lesson": "protecting a wild place means noticing small trouble before it grows",
        "ending": "The waterfall ran clear again, and the grizzly drank while Luna smiled from the dry bank.",
    },
    {
        "clue": "a row of bushes shaking under the evening sky",
        "risk": "shout and throw a stone into the leaves",
        "cause": "a tired grizzly was resting beneath the bushes after a long walk",
        "repair": "Luna stepped back, spoke softly, and helped hikers take a wide path around the resting animal",
        "lesson": "kindness sometimes means giving a wild neighbor plenty of room",
        "ending": "The grizzly rose when it was ready and lumbered away, leaving the trail peaceful for everyone.",
    },
]

ASP_RULES = r"""
#show valid/2.
setting(mountain_trail). setting(forest_camp). setting(pine_valley).
feature(mountain_trail,trail). feature(mountain_trail,cave). feature(mountain_trail,stream).
feature(forest_camp,trail). feature(forest_camp,campfire). feature(forest_camp,stream).
feature(pine_valley,trail). feature(pine_valley,meadow). feature(pine_valley,stream).
valid(P, F) :- setting(P), feature(P, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        for feature in sorted(setting.features):
            lines.append(asp.fact("feature", key, feature))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((key, feature) for key, value in SETTINGS.items() for feature in value.features)


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(python_valid())
    asp_set = set(asp_valid())
    if python_set == asp_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.hero_name.strip() or not params.grizzly_name.strip():
        raise StoryError("Hero and grizzly names must not be empty.")
    if params.hero_name == params.grizzly_name:
        raise StoryError("The hero and grizzly need different names.")

    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting=setting)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type="superhero",
            label=params.hero_name,
            traits=["brave", "thoughtful", "helpful"],
            meters={"courage": 8.0, "energy": 7.0},
            memes={"care": 8.0, "confidence": 6.0},
        )
    )
    grizzly = world.add(
        Entity(
            id=params.grizzly_name,
            kind="character",
            type="grizzly",
            label=f"grizzly {params.grizzly_name}",
            traits=["large", "wild", "frightened"],
            meters={"strength": 9.0, "distance": 1.0},
            memes={"fear": 7.0, "trust": 2.0},
        )
    )
    world.add(
        Entity(
            id="rescue_line",
            type="tool",
            label="a golden rescue line",
            traits=["strong", "bright"],
            owner=hero.id,
        )
    )

    place = setting.label
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, place=place))
    world.say(f"Near the trail, {hero.id} discovered {incident['clue']}.")
    world.say(
        f'"That sounds like a grizzly," {hero.id} said. '
        f'"Please stay where I can see you," called a hiker from the camp.'
    )

    world.para()
    world.say(
        f"The grizzly moved behind the trees, and {hero.id} wanted to {incident['risk']}."
    )
    world.say(THOUGHTS[params.thought % len(THOUGHTS)].format(hero=hero.id))
    world.say(
        f'"I am scared, but I can help safely," {hero.id} called. '
        f'"Can you hear me, friend?"'
    )
    world.say(
        f"The grizzly answered with a low rumble. {hero.id} did not chase. "
        "Instead, she kept a wide space, used her golden rescue line, and began to scour the area with her eyes."
    )
    world.say(TURNS[params.turn % len(TURNS)])
    world.say(
        f'"I see you now," {hero.id} said. "I will not hurt you. We can solve this together."'
    )
    world.say(
        f"The grizzly blinked and stepped back. That small pause changed the quest from a chase into a rescue."
    )

    world.para()
    world.say(
        f"{hero.id} explained the clues to the nearby helpers, and they followed her careful plan."
    )
    world.say(incident["repair"] + ".")
    world.say(
        f'"You were brave because you thought first," the hiker told {hero.id}. '
        f'"And you were kind to the grizzly."'
    )
    world.say(
        f'"Everyone can be a hero when they protect a neighbor," {hero.id} replied.'
    )
    world.say(incident["ending"])
    world.say(
        f"With the danger gone, {hero.id} folded her cape, and the happy valley settled into a peaceful night."
    )

    hero.memes["confidence"] = 9.0
    grizzly.memes["trust"] = 7.0
    grizzly.meters["distance"] = 5.0
    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        incident=incident,
        place=place,
        resolution=incident["repair"],
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    facts = world.facts
    incident = facts["incident"]
    return [
        f"Write a superhero quest in {facts['place']} where {facts['hero'].id} must scour the area after noticing {incident['clue']}.",
        f"Tell a child-friendly story about {facts['hero'].id} helping grizzly {facts['grizzly'].id} without rushing or causing harm.",
        "Use inner monologue, a brief dialogue exchange, a clear turning point, and a happy ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    grizzly = facts["grizzly"]
    incident = facts["incident"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"{hero.id} was the superhero. {hero.id} used courage and careful thinking to help {grizzly.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice first?",
            answer=f"{hero.id} noticed {incident['clue']}. That clue began the rescue quest.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of rushing toward the grizzly?",
            answer=f"{hero.id} kept a wide space, spoke calmly, and scoured the area with careful eyes before choosing a safe plan.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=incident["repair"] + ".",
        ),
        QAItem(
            question="Why did the story have a happy ending?",
            answer=f"The ending was happy because {hero.id} protected people and the grizzly, and {grizzly.id} became calm enough to return safely to the wild.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large wild bear with strong legs, sharp claws, and a powerful sense of smell.",
        ),
        QAItem(
            question="Why should people give wild bears plenty of space?",
            answer="People should give wild bears plenty of space because bears are powerful wild animals that may feel threatened when approached.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully and thoroughly.",
        ),
        QAItem(
            question="What makes a superhero helpful?",
            answer="A helpful superhero protects others, thinks before acting, and uses strength with kindness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.label}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")

    hero_name = args.name or rng.choice(HERO_NAMES)
    grizzly_name = args.grizzly or rng.choice(GRIZZLY_NAMES)
    if hero_name == grizzly_name:
        choices = [name for name in GRIZZLY_NAMES if name != hero_name]
        grizzly_name = rng.choice(choices)

    return StoryParams(
        place=place,
        hero_name=hero_name,
        grizzly_name=grizzly_name,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        thought=rng.randrange(len(THOUGHTS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(3),
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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld: a careful quest involving a grizzly."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--name", help="superhero name")
    parser.add_argument("--grizzly", help="grizzly name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(f"{len(asp_valid())} valid setting-feature combinations:\n")
        for place, feature in asp_valid():
            print(f"  {place:16} {feature}")
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name="Luna",
                grizzly_name="Bruno",
                incident=list(SETTINGS).index(place) % len(INCIDENTS),
                opening=0,
                thought=0,
                turn=0,
                ending=0,
            )
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not generate enough distinct stories.")

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
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)
