#!/usr/bin/env python3
"""
A tall tale about a trillion bright buttons, a bridge-wide conflict, and a
clever repair that turns a quarrel into a shared celebration.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


OPENERS = [
    "Once, when the clouds were still learning to count,",
    "Long ago, in a valley where shadows wore hats,",
    "In a town famous for its enormous ideas,",
    "Before clocks could keep up with breakfast,",
]

SCENES = [
    "the town bridge stretched from one blue hill to the next, with a river singing far below",
    "the market square glittered beneath a sky so wide that even the moon looked small",
    "the windmill hill turned its silver arms above a valley full of waving wheat",
    "the old parade road curled around the mountain like a ribbon tied by a giant",
]

CONFLICTS = {
    "ownership": {
        "warning": "two proud neighbors both claimed the same enormous treasure",
        "event": "At noon, the treasure cart rolled between them, and both neighbors grabbed its handle.",
        "clue": "the cart's wheels sinking on opposite sides",
        "cause": "They had counted the buttons by sight, and each count sounded bigger than the other.",
    },
    "noise": {
        "warning": "the treasure made such a thunderous rattle that nobody could hear a sensible word",
        "event": "A gust shook the treasure, and a trillion buttons clattered like rain on a thousand roofs.",
        "clue": "the quiet pause between two rattles",
        "cause": "Everyone shouted over the noise, so even friendly words arrived sounding cross.",
    },
    "shortcut": {
        "warning": "a quarrel can grow when everyone tries to pull the same thing in a different direction",
        "event": "The treasure cart reached a fork, and every helper tugged toward a different road.",
        "clue": "three sets of footprints pointing three ways",
        "cause": "Each helper believed the fastest road was the only wise road.",
    },
}

SOLUTIONS = {
    "share": {
        "tool": "a long measuring ribbon",
        "action": "measured the buttons into equal heaps",
        "result": "Each neighbor received a fair share, and the cart rolled lightly again.",
    },
    "song": {
        "tool": "a counting song with a very large chorus",
        "action": "made one team count while the other team listened and marked the tune",
        "result": "The shouting became singing, and the buttons marched in rhythm.",
    },
    "bridge": {
        "tool": "a broad plank painted with arrows",
        "action": "laid the plank down and gave each helper one clear direction",
        "result": "The cart crossed safely because every pull joined the next pull.",
    },
}

ENDINGS = [
    "That night, the town's trillion buttons shone like a second Milky Way beneath the stars.",
    "From then on, the neighbors greeted one another with a button-bright grin.",
    "The bridge hummed happily, and even the river seemed to know the new counting song.",
    "At sunset, the last button flashed gold, as if the sun itself approved the peace.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "person":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "bridge"
    conflict: str = "ownership"
    solution: str = "share"
    hero: str = "Luna"
    rival: str = "Bram"
    ending: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "bridge": Setting(
        id="bridge",
        place="the enormous blue-hill bridge",
        features={"bridge", "river", "market"},
    ),
}

HERO_NAMES = ["Luna", "Pip", "Mara", "Jo"]
RIVAL_NAMES = ["Bram", "Tavi", "Nell", "Gus"]


def build_world(params: StoryParams, rng: random.Random) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {params.conflict}")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {params.solution}")
    if params.hero == params.rival:
        raise StoryError("The hero and rival must have different names.")

    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(params.hero, "person", f"a bold child named {params.hero}"))
    rival = world.add(Entity(params.rival, "person", f"a proud neighbor named {params.rival}"))
    buttons = world.add(Entity("buttons", "treasure", "a trillion shining buttons"))
    cart = world.add(Entity("cart", "vehicle", "a cart wider than a cottage"))

    hero.memes["curiosity"] = 1
    rival.memes["pride"] = 1
    buttons.meters["count"] = 1_000_000_000_000
    buttons.meters["weight"] = 3
    cart.meters["strain"] = 1

    world.facts.update(
        hero=hero,
        rival=rival,
        buttons=buttons,
        cart=cart,
        conflict=CONFLICTS[params.conflict],
        solution=SOLUTIONS[params.solution],
        ending=ENDINGS[params.ending % len(ENDINGS)],
        scene=rng.choice(SCENES),
        opener=rng.choice(OPENERS),
    )
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    rival: Entity = world.facts["rival"]
    buttons: Entity = world.facts["buttons"]
    cart: Entity = world.facts["cart"]
    conflict = world.facts["conflict"]
    solution = world.facts["solution"]

    world.say(
        f"{world.facts['opener']} {world.facts['scene']}. "
        f"There lived {hero.label}, who could lift a thundercloud with one hand, "
        f"and {rival.label}, who could whistle a wagon uphill."
    )
    world.say(
        f"One morning, {hero.id} and {rival.id} discovered {buttons.label} piled in {cart.label}. "
        f"The buttons had come from a giant's coat, and there were exactly one trillion of them."
    )
    world.para()
    hero.memes["desire"] = 1
    rival.memes["desire"] = 1
    world.say(
        f"The trouble began because {conflict['warning']}. {conflict['cause']}"
    )
    world.say(conflict["event"])
    world.say(
        f'"That treasure is mine to lead!" {hero.id} cried. '
        f'"Not unless your side can pull harder than mine!" {rival.id} answered.'
    )
    world.say(
        f"The cart groaned. Its wheels rolled toward both directions at once, "
        f"and the bridge began to tremble like a spoon in a giant's teacup."
    )
    cart.meters["strain"] += 2
    hero.memes["worry"] = 1
    rival.memes["worry"] = 1
    world.para()
    world.say(
        f"{hero.id} noticed {conflict['clue']}. Instead of pulling harder, "
        f"{hero.id} lifted {solution['tool']} high enough to shade the river."
    )
    world.say(
        f'"Wait," {hero.id} said. "If we listen to one another, we can {solution["action"]}."'
    )
    world.say(
        f'{rival.id} rubbed {rival.pronoun("possessive")} chin. '
        f'"You mean the treasure can help both of us?"'
    )
    world.say(
        f'"That is what a treasure is for," {hero.id} replied. '
        f'"It should make the whole town richer in kindness."'
    )
    hero.memes["wisdom"] = 1
    rival.memes["trust"] = 1
    world.para()
    world.say(
        f"Together, they {solution['action']}. The first button went to the baker, "
        f"the next button went to the boat maker, and soon every person on the bridge had a job."
    )
    cart.meters["strain"] = 0
    buttons.owner = "town"
    world.say(solution["result"])
    world.say(
        f"{hero.id} and {rival.id} pulled side by side. The bridge stopped trembling, "
        f"the river stopped splashing, and the trillion buttons rolled safely into the town square."
    )
    world.para()
    world.say(world.facts["ending"])


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
    tell_story(world)
    hero: Entity = world.facts["hero"]
    rival: Entity = world.facts["rival"]
    solution = world.facts["solution"]
    conflict = world.facts["conflict"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a tall tale about {hero.id}, {rival.id}, and one trillion buttons.",
            f"Show how a conflict begins when {conflict['warning']}.",
            f"End with a giant problem repaired through {solution['tool']}.",
        ],
        story_qa=[
            QAItem(
                "What caused the conflict?",
                f"The conflict began because {conflict['cause']}",
            ),
            QAItem(
                "How did the children repair the problem?",
                f"They worked together and {solution['action']}, so the cart stopped straining and the town could share the buttons.",
            ),
            QAItem(
                "What changed at the end?",
                "The trillion buttons became a shared town treasure, and the two neighbors pulled the cart together instead of fighting.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a trillion?",
                "A trillion is the number 1,000,000,000,000, or one thousand billion.",
            ),
            QAItem(
                "What is conflict?",
                "Conflict is a disagreement or struggle between people, groups, or goals.",
            ),
            QAItem(
                "What is a tall tale?",
                "A tall tale is a playful story with exaggerated events, enormous numbers, and larger-than-life characters.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"  setting: {world.setting.place}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: meters={entity.meters} memes={entity.memes} owner={entity.owner}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A trillion-button tall tale about conflict and cooperation."
    )
    parser.add_argument("--setting", choices=SETTINGS, default="bridge")
    parser.add_argument("--conflict", choices=CONFLICTS, default=None)
    parser.add_argument("--solution", choices=SOLUTIONS, default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--rival", default=None)
    parser.add_argument("--ending", type=int, default=None)
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


ASP_RULES = r"""
setting(bridge).
feature(bridge, conflict).
treasure(buttons).
quantity(buttons, trillion).
character(hero).
character(rival).
shared_solution(share).
shared_solution(song).
shared_solution(bridge).

conflict_present :- feature(bridge, conflict), character(hero), character(rival).
repair_possible :- conflict_present, shared_solution(share).
repair_possible :- conflict_present, shared_solution(song).
repair_possible :- conflict_present, shared_solution(bridge).
valid_story :- conflict_present, repair_possible, treasure(buttons), quantity(buttons, trillion).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "bridge"),
            asp.fact("feature", "bridge", "conflict"),
            asp.fact("treasure", "buttons"),
            asp.fact("quantity", "buttons", "trillion"),
            asp.fact("character", "hero"),
            asp.fact("character", "rival"),
            asp.fact("shared_solution", "share"),
            asp.fact("shared_solution", "song"),
            asp.fact("shared_solution", "bridge"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if any(atom.name == "valid_story" for atom in model):
        print("OK: ASP confirms a trillion-button conflict has a cooperative repair.")
        return 0
    print("ASP verification failed.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    rival = args.rival or rng.choice([n for n in RIVAL_NAMES if n != hero])
    return StoryParams(
        setting=args.setting,
        conflict=args.conflict or rng.choice(list(CONFLICTS)),
        solution=args.solution or rng.choice(list(SOLUTIONS)),
        hero=hero,
        rival=rival,
        ending=args.ending if args.ending is not None else rng.randrange(len(ENDINGS)),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    count = max(1, args.n)
    if args.all:
        combinations = [
            (conflict, solution)
            for conflict in CONFLICTS
            for solution in SOLUTIONS
        ]
        for i, (conflict, solution) in enumerate(combinations):
            params = StoryParams(
                conflict=conflict,
                solution=solution,
                hero="Luna",
                rival="Bram",
                ending=i % len(ENDINGS),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(count):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
