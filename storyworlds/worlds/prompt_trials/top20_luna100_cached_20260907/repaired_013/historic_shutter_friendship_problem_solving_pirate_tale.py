#!/usr/bin/env python3
"""
A child-facing pirate tale about a historic shutter, friendship, and clever
problem solving.
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
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the historic harbor"
    hero: str = "Luna"
    friend: str = "Pip"
    captain: str = "Captain Brine"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the historic harbor": {"tags": {"historic", "sea", "pirate"}, "mood": "windy and bright"},
    "the old lighthouse island": {"tags": {"historic", "island", "pirate"}, "mood": "rocky and misty"},
    "the mapmaker's quay": {"tags": {"historic", "maps", "pirate"}, "mood": "busy and salty"},
}


@dataclass(frozen=True)
class PirateArc:
    title: str
    premise: str
    problem: str
    dialogue: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


ARCS = [
    PirateArc(
        "The Shutter at Storm Bell Tower",
        "The historic harbor kept an old wooden shutter that had once protected the storm bell.",
        "A squall pushed the shutter shut before the bell could warn boats away from the reef.",
        "\"We cannot pull harder,\" said Pip. \"Then we will think wider,\" Luna replied.",
        "They tied a spare sailcloth to the shutter, used a barrel as a rolling lever, and pulled together when the wind eased.",
        "The shutter swung open, and the storm bell rang across the water.",
        "The storm shutter closed before the warning bell could sound, leaving boats near a reef.",
        "Luna and Pip stopped pulling blindly and combined sailcloth, a barrel, and careful timing.",
        "Their plan opened the shutter so the bell could warn every boat.",
        "wet footprints led from the pier to the bell tower, where the historic shutter stood open beneath a rainbow",
    ),
    PirateArc(
        "The Captain's Crooked Window",
        "In the old captain's house, a historic shutter hid a window carved with the harbor's safest sailing route.",
        "Salt had swollen the wood, and the crew could not see the route before nightfall.",
        "\"A strong arm is not enough,\" said Luna. \"Perhaps a patient trick is,\" said Pip.",
        "They brushed oil along the hinges, slipped a spoon beneath the latch, and worked the shutter a little at a time.",
        "The window opened without a crack, revealing a safe channel marked by three silver stars.",
        "The swollen shutter hid a vital sailing route, and forcing it might have broken the historic window.",
        "The friends used oil, a spoon, and patient teamwork instead of brute force.",
        "They opened the window safely and found the route that guided the crew through the dark.",
        "three silver stars shone through the open shutter while the crew sailed safely home",
    ),
    PirateArc(
        "The Gull That Guarded the Shutter",
        "A clever gull nested behind a historic shutter at the edge of the pirate museum.",
        "Visitors could not open the shutter to rescue a trapped kitten inside the storehouse.",
        "\"The gull is guarding something,\" Pip whispered. \"Let us ask before we act,\" Luna said.",
        "They placed fish beside the hinge, waited for the gull to move, and lifted the shutter slowly while the kitten crept out.",
        "The gull returned to its nest, the kitten returned to its owner, and the shutter remained whole.",
        "A nesting gull blocked the shutter while a kitten was trapped inside the storehouse.",
        "The friends solved the problem gently by understanding the gull's need and making room for it.",
        "Their careful plan rescued the kitten without harming the bird or the historic shutter.",
        "the gull slept above the shutter while the rescued kitten watched the harbor from the windowsill",
    ),
    PirateArc(
        "The Moonlit Shutter Code",
        "Every historic shutter on the moonlit quay bore a tiny mark left by sailors long ago.",
        "The marks formed a code, but one jammed shutter hid the final sign needed to find a lost medicine chest.",
        "\"Read the clues we have,\" said Luna. \"And test one idea at a time,\" Pip answered.",
        "They matched the visible marks to the tide chart, then used a warm lantern to loosen the frozen latch.",
        "The shutter opened, the last sign completed the code, and the medicine chest was found beneath the dock.",
        "A jammed shutter hid the final clue to a medicine chest needed by the harbor families.",
        "The friends combined observation, a tide chart, and a warm lantern instead of guessing.",
        "Opening the shutter completed the code and led them to the medicine chest.",
        "the historic shutters glimmered like a row of moonlit shields above the medicine chest",
    ),
    PirateArc(
        "The Shutter and the Sunken Bell",
        "A historic shutter above the harbor steps showed the tide level for an old sunken bell.",
        "Muddy water covered its marks, so the crew could not tell when the bell would rise.",
        "\"The water is hiding the answer,\" said Pip. \"Then we will let it speak,\" said Luna.",
        "They cleared a narrow drain, watched the water fall, and compared the revealed marks with the bell rope.",
        "At the right tide they pulled once, and the sunken bell rang beneath the waves.",
        "Muddy water hid the tide marks needed to raise a sunken warning bell.",
        "The friends cleared the drain and observed the changing water instead of guessing the tide.",
        "Their measurements showed the right moment, and one pull rang the bell.",
        "ripples carried the bell's deep song beneath the open historic shutter",
    ),
]


OPENINGS = [
    "Ahoy, young sailors! In {setting}, Luna and Pip sailed beneath a striped flag.",
    "Long ago, when wooden ships crowded {setting}, two friends named Luna and Pip kept watch together.",
    "The sea was bright around {setting}, but the old buildings creaked whenever the wind blew.",
    "Luna and Pip were small pirates with a large promise: they would solve trouble together.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(
        (params.setting, params.hero, params.friend, params.captain)
    )))


def fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")
    if params.hero == params.captain or params.friend == params.captain:
        raise StoryError("The captain must be different from both young friends.")
    if params.setting not in SETTING_REGISTRY:
        raise StoryError("That setting is not in the historic harbor registry.")

    seed = stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    facts = {
        "hero": params.hero,
        "friend": params.friend,
        "captain": params.captain,
        "setting": params.setting,
    }

    world = World(params.setting)
    hero = world.add(Entity(params.hero, "pirate", meters={"energy": 1.0}, memes={"friendship": 1.0}))
    friend = world.add(Entity(params.friend, "pirate", meters={"energy": 1.0}, memes={"problem_solving": 1.0}))
    captain = world.add(Entity(params.captain, "captain", meters={"trust": 0.5}, memes={"patience": 1.0}))
    shutter = world.add(Entity("the historic shutter", "artifact", meters={"open": 0.0, "sturdiness": 1.0}, memes={"memory": 1.0}))
    world.add(Entity("the pirate boat", "boat", meters={"afloat": 1.0}, memes={"home": 1.0}))
    world.facts.update(
        arc=arc,
        title=arc.title,
        hero=hero.name,
        friend=friend.name,
        captain=captain.name,
        setting=params.setting,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        problem=fill(arc.problem, facts),
        action=fill(arc.action, facts),
        result=fill(arc.result, facts),
        ending=fill(arc.ending, facts),
        friendship=1.0,
        problem_solving=1.0,
    )

    opening = fill(OPENINGS[world.facts["opening_variant"]], facts)
    lines = [
        f"{opening} This is the tale called \"{arc.title}.\"",
        f"{fill(arc.premise, facts)} {fill(arc.problem, facts)}",
        f"{params.captain} called, \"Can you help the harbor?\" {fill(arc.dialogue, facts)}",
        fill(arc.action, facts),
        f"{params.captain} raised a brass spyglass. \"That was clever seamanship!\" he cheered. {fill(arc.result, facts)}",
        f"At sunset, {fill(arc.ending, facts)}. From that day on, the crew remembered that friendship and problem solving could steer a ship through trouble.",
    ]
    story = "\n\n".join(lines)

    prompts = [
        f"Write a pirate tale about {params.hero} and {params.friend} solving a problem with a historic shutter.",
        "Tell a child-friendly sea adventure where friendship and careful thinking save the day.",
        f"Create a warm pirate story set in {params.setting}.",
    ]
    story_qa = [
        QAItem(f"What problem did the friends face in \"{arc.title}\"?", arc.problem_answer),
        QAItem("How did Luna and Pip use problem solving?", arc.choice_answer),
        QAItem("What changed after their plan worked?", arc.result_answer),
        QAItem(f"What final image closes \"{arc.title}\"?", f"The tale ends with {fill(arc.ending, facts)}."),
    ]
    world_qa = [
        QAItem("What is a historic object?", "A historic object is something from the past that helps people remember earlier times."),
        QAItem("What is a shutter?", "A shutter is a hinged cover that can close over a window or opening."),
        QAItem("What is friendship?", "Friendship is a caring bond in which people help, trust, and listen to one another."),
        QAItem("What is problem solving?", "Problem solving means understanding a difficulty, trying a thoughtful plan, and changing the plan when needed."),
        QAItem("What does a pirate captain do?", "A pirate captain leads a crew, makes careful choices, and helps keep the ship and its people safe."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
setting(historic_harbor).
setting(old_lighthouse_island).
setting(mapmakers_quay).
feature(friendship).
feature(problem_solving).
historic_shutter.
safe_story(S) :- setting(S), feature(friendship), feature(problem_solving), historic_shutter.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace("'", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend([
        asp.fact("feature", "friendship"),
        asp.fact("feature", "problem_solving"),
        asp.fact("historic_shutter"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale of a historic shutter, friendship, and problem solving.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--captain")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Mara", "Nell", "Cora"])
    friend = args.friend or rng.choice(["Pip", "Toby", "Finn", "Jo"])
    captain = args.captain or rng.choice(["Captain Brine", "Captain Coral", "Captain Wren"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if hero == captain or friend == captain:
        raise StoryError("The captain must be different from both young friends.")
    return StoryParams(setting=setting, hero=hero, friend=friend, captain=captain)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={dict(entity.meters)}, memes={dict(entity.memes)}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import asp
    python_settings = {
        (setting.replace("the ", "").replace("'", "").replace(" ", "_"),)
        for setting in SETTING_REGISTRY
    }
    model = asp.one_model(asp_program("#show safe_story/1."))
    clingo_settings = set(asp.atoms(model, "safe_story"))
    if python_settings == clingo_settings:
        print(f"OK: clingo gate matches python ({len(python_settings)} settings).")
        for seed in range(5):
            params = StoryParams(seed=seed)
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("Generated-story check failed.")
                return 1
        print("OK: generated-story checks passed.")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_settings - clingo_settings))
    print("clingo only:", sorted(clingo_settings - python_settings))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/1."))
        for item in asp.atoms(model, "safe_story"):
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(generate(StoryParams(
                setting=setting,
                hero="Luna",
                friend="Pip",
                captain="Captain Brine",
            )))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
