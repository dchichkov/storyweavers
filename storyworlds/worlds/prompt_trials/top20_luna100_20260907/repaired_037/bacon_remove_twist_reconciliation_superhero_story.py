#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, a stuck signal, a surprising twist,
and reconciliation.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    place: str
    affords: set[str] = field(default_factory=set)


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
    friend_name: str
    incident: int = 0
    opening: int = 0
    twist: int = 0
    reconciliation: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting("the rooftop rescue station", {"bacon", "signal"}),
    "kitchen": Setting("the neighborhood kitchen", {"bacon", "signal"}),
    "skybridge": Setting("the skybridge above Bright City", {"signal"}),
}

HERO_NAMES = ["Nova", "Bolt", "Comet", "Flash"]
FRIEND_NAMES = ["Mira", "Pax", "Sunny", "Jules"]

INCIDENTS = [
    {
        "glimmer": "a red warning light blinking beside a tray of bacon",
        "problem": "the breakfast signal had been trapped under the sizzling tray",
        "urge": "grab the tray and dash it across the rooftop",
        "clue": "the signal wire curled around the tray handle",
        "twist": "the bacon was not blocking the alarm by accident; the hungry rescue robot had pulled the tray close while following its wonderful smell",
        "fix": "They switched off the burner, used a cool metal mitt to remove the tray, and freed the wire.",
        "ending": "The alarm shone green while the rescued bacon cooled on a safe plate.",
    },
    {
        "glimmer": "a smoky cloud rising over the kitchen's bacon pan",
        "problem": "the smoke beacon was calling every hero in Bright City",
        "urge": "wave a cape through the smoke and fan it toward the open window",
        "clue": "the pan sat beneath a forgotten warming lamp",
        "twist": "the smoke was not a villain's attack at all; the warming lamp had been left on after a busy breakfast",
        "fix": "They turned off the lamp, moved the pan away from the heat, and opened the window.",
        "ending": "Fresh air filled the kitchen, and the bacon crackled gently without frightening anyone.",
    },
    {
        "glimmer": "a golden bacon-shaped badge stuck to the skybridge rail",
        "problem": "the city map beacon could not point rescuers toward a lost kite",
        "urge": "pull the badge loose with superhero strength",
        "clue": "a strip of sticky syrup held the badge over the map's tiny compass",
        "twist": "the badge had been placed there by a child who wanted to mark the best breakfast view",
        "fix": "They softened the syrup with warm water, removed the badge carefully, and restored the compass.",
        "ending": "The map pointed true again, and the child received a clean badge for the breakfast club.",
    },
]

OPENINGS = [
    "At sunrise, {hero} flew over {place}, where the city was waking to the smell of bacon.",
    "Before school bells rang, {hero} checked {place} while carrying a bright superhero cape.",
    "The morning sky glittered above {place} as {hero} promised to keep every neighbor safe.",
]

TWISTS = [
    '"Wait," said {friend}. "The clue may be telling us this is a mistake, not an attack."',
    '"Do not rush," {hero} replied. "A real hero checks what caused the trouble."',
    '{hero} lowered the cape. "Let us solve the mystery before we blame anyone."',
]

RECONCILIATIONS = [
    '"I thought you caused the trouble," {hero} admitted. "I am sorry I blamed you."',
    '"I should have told you before moving things," said {friend}. "Can we fix it together?"',
    '"Heroes can be wrong," {hero} said. "What matters is listening and making things right."',
]


ASP_RULES = r"""
#show valid/2.
setting(rooftop). setting(kitchen). setting(skybridge).
affords(rooftop,bacon). affords(rooftop,signal).
affords(kitchen,bacon). affords(kitchen,signal).
affords(skybridge,signal).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", name, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in python:", sorted(py - clingo))
    print("  only in clingo:", sorted(clingo - py))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(SETTINGS[params.place])

    hero = world.add(Entity(
        params.hero_name, "character", "superhero",
        traits=["brave", "curious"],
        memes={"courage": 1.0, "certainty": 0.3},
    ))
    friend = world.add(Entity(
        params.friend_name, "character", "helper",
        traits=["observant", "honest"],
        memes={"trust": 0.6},
    ))
    bacon = world.add(Entity(
        "bacon", "thing", "food", "bacon",
        owner="neighborhood_kitchen",
        meters={"warmth": 0.8, "distance_to_plate": 4.0},
    ))
    signal = world.add(Entity(
        "signal", "thing", "beacon", "rescue signal",
        meters={"clarity": 0.2},
    ))

    place = world.setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, place=place))
    world.say(f"Then {hero.id} saw {incident['glimmer']}.")
    world.say(
        f'"A villain must be hiding nearby," {hero.id} said. '
        f'"Or breakfast needs help," {friend.id} answered.'
    )
    world.para()
    world.say(f"The trouble was clear: {incident['problem']}.")
    world.say(f"{hero.id} wanted to {incident['urge']}, but {friend.id} pointed toward the clue: {incident['clue']}.")
    world.say(TWISTS[params.twist % len(TWISTS)].format(hero=hero.id, friend=friend.id))
    world.say(f"Together they discovered the twist: {incident['twist']}.")
    hero.memes["certainty"] = 0.9
    friend.memes["trust"] = 0.9
    world.facts["tension"] = True
    world.facts["twist_revealed"] = True
    world.para()
    world.say(f"{hero.id} took a breath and said {RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)].format(hero=hero.id, friend=friend.id)}")
    world.say(f"They worked side by side. {incident['fix']}")
    world.say(
        f'"Next time, we will ask before we act," {friend.id} said. '
        f'"And we will protect breakfast while we protect the city," {hero.id} replied.'
    )
    world.say(incident["ending"])
    world.say(f"{hero.id} and {friend.id} shared the first slice, reconciled and ready for the next call.")

    world.facts.update(hero=hero, friend=friend, bacon=bacon, signal=signal, incident=incident)
    return world


def generation_prompts(world: StoryState) -> list[str]:
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write a superhero story about {hero.id} protecting bacon while investigating {incident['problem']}.",
        f"Tell a child-friendly story where {hero.id} and {friend.id} discover a twist and reconcile.",
        "Write a complete superhero adventure with dialogue, bacon, a careful removal, and a peaceful ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    hero = f["hero"].id
    friend = f["friend"].id
    return [
        QAItem("Who was the superhero?", f"The superhero was {hero}, who investigated the bacon trouble instead of rushing into danger."),
        QAItem(f"What did {hero} first think was happening?", f"{hero} first suspected a villain, but {friend} noticed clues that suggested an ordinary problem."),
        QAItem("What was the twist?", f"The twist was that {incident['twist']}."),
        QAItem("How was the problem fixed?", incident["fix"]),
        QAItem("How did the characters reconcile?", f"{hero} apologized for blaming too quickly, and {friend} worked with {hero} to repair the signal and keep everyone safe."),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem("What is bacon?", "Bacon is a food made from cured meat that is usually cooked before it is eaten."),
        QAItem("Why should a person remove a hot pan carefully?", "A hot pan can burn someone, so it should be turned off and moved with a suitable mitt or tool."),
        QAItem("What does reconciliation mean?", "Reconciliation means repairing trust and peace after people have disagreed or hurt one another."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(k for k in world.facts if k not in {'hero', 'friend', 'bacon', 'signal'})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        raise StoryError("Hero and friend must have different names.")
    return StoryParams(
        place=place,
        hero_name=hero,
        friend_name=friend,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero bacon, twist, and reconciliation storyworld.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
        raise SystemExit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:")
        for place, item in asp_valid():
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            samples.append(generate(StoryParams(place, f"{place.title()}Hero", f"{place.title()}Helper")))
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
