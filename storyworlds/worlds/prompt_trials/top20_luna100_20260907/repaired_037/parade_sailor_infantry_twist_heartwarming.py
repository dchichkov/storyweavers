#!/usr/bin/env python3
"""
A heartwarming storyworld about a sailor, an infantry band, and a parade
whose missing drumbeat is solved by listening to an unexpected helper.
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
    sailor_name: str
    captain_name: str
    child_name: str
    twist: int = 0
    opening: int = 0
    kindness: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "harbor_square": Setting(
        "the harbor square",
        {"parade", "sailor", "infantry", "band", "flags"},
    ),
    "town_green": Setting(
        "the town green",
        {"parade", "sailor", "infantry", "band", "flags"},
    ),
    "seaside_avenue": Setting(
        "the seaside avenue",
        {"parade", "sailor", "infantry", "band", "flags"},
    ),
}

SAILOR_NAMES = ["Luna", "Mara", "Finn", "Nora", "Sami", "Wren"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Vale", "Captain Ellis", "Captain June"]
CHILD_NAMES = ["Pip", "Mina", "Theo", "Bea", "Ollie", "Rosa"]

OPENINGS = [
    "Bright flags fluttered above {place} as sailor {sailor} polished the little brass whistle that would lead the parade.",
    "The morning sun warmed {place}. Sailor {sailor} stood with the infantry while children gathered to watch their town parade.",
    "At {place}, boots tapped and flags lifted in the breeze. Sailor {sailor} checked every marching row before the music began.",
    "A cheerful parade was about to cross {place}, and sailor {sailor} felt proud to march beside the friendly infantry.",
]

KINDNESS_LINES = [
    '"A parade is not only a sound," said {captain}. "It is a promise that nobody has to walk alone."',
    '"Let us make room for every helper," {captain} told them. "The best march has many kinds of footsteps."',
    '"We can slow down without losing heart," said {captain}. "People remember kindness longer than perfect timing."',
    '"Listen first," {captain} advised. "Sometimes the quietest neighbor knows how to save the day."',
]

TWISTS = [
    {
        "problem": "the parade drum split with a soft pop just before the first turn",
        "want": "borrow another drum and hurry the parade onward",
        "clue": "a row of tin cups on a baker's stall trembled whenever the harbor bell rang",
        "helper": "a shy baker's daughter named Elsie",
        "method": "tap the cups in the same steady pattern as marching boots",
        "reveal": "Elsie had been practicing that rhythm while waiting for her father to finish baking",
        "repair": "The infantry followed her bright cup rhythm, and the broken drum became a small treasure tucked safely under the band's cart.",
        "ending": "Elsie marched beside the sailors, tapping two tin cups while the whole parade smiled.",
        "lesson": "a useful rhythm can come from an unexpected place",
    },
    {
        "problem": "a thick fog swallowed the parade route's painted arrows",
        "want": "push ahead and hope the flags pointed the right way",
        "clue": "a lighthouse keeper's bell answered from beyond the fog at regular intervals",
        "helper": "an old lighthouse keeper named Bram",
        "method": "follow the bell's patient pattern while the sailors called back",
        "reveal": "Bram had kept the harbor path safe by listening to that same bell for forty years",
        "repair": "The infantry formed a bright line behind the flags, and Bram guided everyone safely to the town green.",
        "ending": "When the fog lifted, Bram received the first parade flag and carried it proudly.",
        "lesson": "patience and careful listening can guide a crowd",
    },
    {
        "problem": "the wind tore the parade's biggest banner from its pole",
        "want": "chase the banner into the busy street",
        "clue": "a group of children were holding a long blue fishing net beside the pier",
        "helper": "three young dock workers",
        "method": "ask them to spread the net across the safe side of the square",
        "reveal": "the dock workers knew how to catch drifting sails without stepping into danger",
        "repair": "Together they caught the banner, mended its corner, and tied it to two shorter poles.",
        "ending": "The repaired banner flew lower than before, where every child could read its golden words: WELCOME HOME.",
        "lesson": "asking for help is braver than rushing into danger",
    },
    {
        "problem": "the youngest infantry marcher froze when the crowd grew loud",
        "want": "leave the line and hide behind the supply wagon",
        "clue": "sailor {sailor} noticed that the child could keep marching when someone hummed softly",
        "helper": "the child’s grandmother, who stood near the curb",
        "method": "let the grandmother hum while the sailor matched a slow walking pace",
        "reveal": "the grandmother had taught the child the parade song during quiet evenings at home",
        "repair": "The captain shortened the next block and invited the grandmother to walk beside the infantry.",
        "ending": "The nervous marcher finished the route with one hand in the grandmother's and one flag in the other.",
        "lesson": "care can turn a frightening crowd into a friendly one",
    },
    {
        "problem": "rain blurred the music sheets before the parade reached the bridge",
        "want": "guess the next song from memory",
        "clue": "a sailor's knot card showed colored threads for each part of the tune",
        "helper": "the ship's cook, who remembered songs by their colors",
        "method": "read the colored knots while the infantry kept a gentle beat",
        "reveal": "the cook had tied the cards for homesick sailors who could not read music",
        "repair": "The band played from the knot card until they reached a dry awning, where the sheets were copied again.",
        "ending": "Under the awning, the cook taught everyone a new verse about returning safely home.",
        "lesson": "knowledge shared kindly can outlast a sudden storm",
    },
]

def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown parade setting: {params.place}")
    setting = SETTINGS[params.place]
    twist = TWISTS[params.twist % len(TWISTS)]
    world = StoryState(setting)

    sailor = world.add(Entity(
        params.sailor_name,
        "character",
        "sailor",
        traits=["brave", "observant"],
        meters={"steadiness": 0.8, "distance": 0.0},
        memes={"belonging": 0.6, "responsibility": 0.8},
    ))
    captain = world.add(Entity(
        params.captain_name,
        "character",
        "captain",
        traits=["kind", "wise"],
        meters={"steadiness": 0.9},
        memes={"care": 0.9},
    ))
    child = world.add(Entity(
        params.child_name,
        "character",
        "child",
        traits=["curious", "hopeful"],
        meters={"distance": 0.0},
        memes={"courage": 0.4},
    ))
    infantry = world.add(Entity(
        "infantry",
        "group",
        "infantry",
        label="the infantry",
        traits=["disciplined", "friendly"],
        memes={"togetherness": 0.8},
    ))
    parade = world.add(Entity(
        "parade",
        "event",
        "parade",
        label="the parade",
        traits=["colorful", "welcoming"],
        memes={"joy": 0.7},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        place=setting.place,
        sailor=sailor.id,
    ))
    world.say(
        f'"Ready to lead us, {sailor.id}?" asked {captain.id}. '
        f'"Ready to help everyone keep step," replied {sailor.id}.'
    )

    world.para()
    world.say(f"Then {twist['problem']}. The bright parade slowed, and the infantry looked toward {sailor.id}.")
    world.say(
        f'"We should {twist["want"]}," one marcher suggested. '
        f'"Wait. Let us look and listen first," said {sailor.id}.'
    )
    world.say(KINDNESS_LINES[params.kindness % len(KINDNESS_LINES)].format(
        captain=captain.id
    ))
    world.say(f"From the edge of {setting.place}, {twist['clue']}.")
    world.say(
        f'{sailor.id} asked for help instead of giving an order. '
        f'Together, they decided to {twist["method"]}.'
    )
    world.say(
        f'The unexpected helper was {twist["helper"]}. '
        f'"I know this beat," the helper said. "I can try."'
    )
    world.say(
        f'"And we will listen," {sailor.id} promised. '
        f'"You do not have to do it alone."'
    )
    world.say(f"That was the twist: {twist['reveal']}.")
    world.say(twist["repair"])

    world.para()
    world.say(
        f'The captain smiled. "You changed our plan, {sailor.id}, and made the parade stronger." '
        f'"The helper changed it too," {sailor.id} answered.'
    )
    world.say(
        f'The infantry marched again, not faster, but together. '
        f'Children copied the new rhythm, and the sailor watched every face brighten.'
    )
    world.say(
        f'At the end of the route, {child.id} asked, '
        f'"What made the parade succeed?" '
        f'{sailor.id} replied, "We noticed a need, invited a helper, and made room for a new way."'
    )
    world.say(twist["ending"])

    sailor.memes["belonging"] = 1.0
    child.memes["courage"] = 0.9
    infantry.memes["togetherness"] = 1.0
    world.facts.update(
        sailor=sailor,
        captain=captain,
        child=child,
        infantry=infantry,
        parade=parade,
        twist=twist,
        place=setting.place,
        resolved=True,
    )
    return world


ASP_RULES = r"""
#show valid/2.
setting(harbor_square). setting(town_green). setting(seaside_avenue).
affords(harbor_square,parade). affords(harbor_square,sailor).
affords(harbor_square,infantry). affords(harbor_square,band).
affords(harbor_square,flags).
affords(town_green,parade). affords(town_green,sailor).
affords(town_green,infantry). affords(town_green,band).
affords(town_green,flags).
affords(seaside_avenue,parade). affords(seaside_avenue,sailor).
affords(seaside_avenue,infantry). affords(seaside_avenue,band).
affords(seaside_avenue,flags).
valid(P, F) :- affords(P, F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", name, feature))
    return "\n".join(lines)

def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def python_valid() -> list[tuple[str, str]]:
    return sorted(
        (place, feature)
        for place, setting in SETTINGS.items()
        for feature in setting.affords
    )

def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))

def asp_verify() -> int:
    expected = set(python_valid())
    actual = set(asp_valid())
    if expected != actual:
        print("MISMATCH between Python and ASP gates.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1
    for place in SETTINGS:
        params = StoryParams(place, "Luna", "Captain Reed", "Pip")
        sample = generate(params)
        if not sample.story.strip() or "parade" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and story generation verified ({len(actual)} combinations).")
    return 0


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming parade story about sailor {f['sailor'].id} and the infantry.",
        f"Tell a story in {f['place']} where an unexpected twist helps save the parade.",
        f"Write a child-friendly story about listening, teamwork, and welcoming a surprising helper.",
    ]

def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    twist = f["twist"]
    sailor = f["sailor"].id
    child = f["child"].id
    return [
        QAItem(
            "Who helped lead the parade?",
            f"Sailor {sailor} helped lead the parade and listened carefully when the plan changed.",
        ),
        QAItem(
            "What problem interrupted the parade?",
            f"The parade was interrupted because {twist['problem']}. The group paused instead of rushing.",
        ),
        QAItem(
            "Who became an unexpected helper?",
            f"The unexpected helper was {twist['helper']}. The sailor invited the helper to contribute safely.",
        ),
        QAItem(
            f"What did {child} learn from the parade?",
            f"{child} learned that people can solve a problem by listening, asking for help, and making room for a new way to belong.",
        ),
        QAItem(
            "How did the parade end?",
            twist["ending"],
        ),
    ]

def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a parade?",
            "A parade is an organized procession in which people move together, often with music, flags, or decorations.",
        ),
        QAItem(
            "What is a sailor?",
            "A sailor is a person who works or travels on a ship or boat.",
        ),
        QAItem(
            "What does infantry mean?",
            "Infantry are soldiers who serve and move on foot.",
        ),
        QAItem(
            "Why can listening help a team?",
            "Listening helps a team notice useful ideas, understand people's needs, and choose a safer or kinder plan together.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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

def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.traits:
            details.append(f"traits={entity.traits}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:14} ({entity.type:10}) {' '.join(details)}")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    child = args.child or rng.choice(CHILD_NAMES)
    if len({sailor, captain, child}) < 3:
        alternatives = [name for name in CHILD_NAMES if name not in {sailor, captain}]
        if not alternatives:
            raise StoryError("Sailor, captain, and child must have distinct names.")
        child = rng.choice(alternatives)
    return StoryParams(
        place=place,
        sailor_name=sailor,
        captain_name=captain,
        child_name=child,
        twist=rng.randrange(len(TWISTS)),
        opening=rng.randrange(len(OPENINGS)),
        kindness=rng.randrange(len(KINDNESS_LINES)),
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
        description="Heartwarming parade storyworld with a sailor, infantry, and a twist."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--sailor")
    parser.add_argument("--captain")
    parser.add_argument("--child")
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

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:\n")
        for place, feature in asp_valid():
            print(f"  {place:18} {feature}")
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                sailor_name="Luna",
                captain_name="Captain Reed",
                child_name="Pip",
                twist=list(SETTINGS).index(place) % len(TWISTS),
                opening=list(SETTINGS).index(place) % len(OPENINGS),
                kindness=list(SETTINGS).index(place) % len(KINDNESS_LINES),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce the requested number of distinct stories.")

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
