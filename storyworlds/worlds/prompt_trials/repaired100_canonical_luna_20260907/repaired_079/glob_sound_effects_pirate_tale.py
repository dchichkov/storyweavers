#!/usr/bin/env python3
"""
A small pirate tale about Glob, a noisy treasure map, and a crew that learns
to listen for the sound that matters.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Luna"
    mate: str = "Pip"
    ship: str = "the Jolly Button"


NAMES = ["Luna", "Pip", "Mara", "Finn", "Nell", "Toby", "Cora", "Beau"]
SHIPS = ["the Jolly Button", "the Sea Sprout", "the Copper Crab", "the Moon Kettle"]

ADVENTURES = [
    {
        "place": "a foggy cove",
        "noise": "BOOM! CLANG! SQUEAK!",
        "wrong": "followed every loud sound and sailed into a ring of empty barrels",
        "setback": "the tide nudged the ship onto a muddy sandbank before supper",
        "clue": "the map made a tiny pop whenever the safe path bent left",
        "fix": "covered the cannon, tapped the map gently, and followed the little pops instead of the big bangs",
        "rescue": "the ship slid free on the next rising tide",
        "ending": "a warm chest of cinnamon biscuits waited beneath the left-hand lantern",
        "lesson": "The loudest sound is not always the most helpful clue.",
    },
    {
        "place": "an island of singing shells",
        "noise": "WHOOSH! SPLASH! TOOT!",
        "wrong": "chased the biggest sound and tied the ship beside a grumpy sea lion",
        "setback": "the sea lion splashed their clean laundry into the water",
        "clue": "the map gave a soft glob-glob sound near the shell that marked the true route",
        "fix": "listened below the splashing, found the glob-glob, and steered toward the quiet shell",
        "rescue": "the sea lion swam away and revealed a calm blue channel",
        "ending": "the crew dried their laundry while the shells hummed a gentle welcome",
        "lesson": "Careful listening can turn a noisy puzzle into a clear path.",
    },
    {
        "place": "a reef shaped like a sleeping dragon",
        "noise": "CRACK! RATTLE! PLOP!",
        "wrong": "mistook a rattling anchor chain for a treasure signal and dropped anchor on a coral garden",
        "setback": "the anchor snagged, and the crew had to wait while the reef fish hid",
        "clue": "the treasure map made one round glob sound only when the anchor was safely lifted",
        "fix": "raised the anchor, waited for the glob, and guided the ship between the coral towers",
        "rescue": "the anchor came loose without harming the reef",
        "ending": "a pearl compass blinked beside the dragon's nose",
        "lesson": "A patient pause can protect a place while solving a problem.",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(params.captain, "character", "captain", params.captain))
    mate = world.add(Entity(params.mate, "character", "mate", params.mate))
    ship = world.add(Entity("ship", "thing", "ship", params.ship))
    map_ent = world.add(Entity("map", "thing", "map", "treasure map"))
    glob = world.add(Entity("glob", "thing", "sound", "glob"))

    captain.meters["courage"] = 1.0
    mate.meters["listening"] = 1.0
    ship.meters["safety"] = 1.0
    map_ent.memes["mystery"] = 1.0
    glob.memes["importance"] = 1.0
    world.facts.update(captain=captain, mate=mate, ship=ship, map=map_ent, glob=glob)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(params.captain + params.mate + params.ship))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    adventure = ADVENTURES[_token(params) % len(ADVENTURES)]
    captain = world.facts["captain"]
    mate = world.facts["mate"]
    ship = world.facts["ship"]
    world.facts["adventure"] = adventure

    world.say(f"Captain {captain.label} sailed {ship.label} toward {adventure['place']} with {mate.label} beside the wheel.")
    world.say("A rolled treasure map rested on the deck. It was supposed to point toward a friendly island picnic.")
    world.say(f"Then the sea began to shout: {adventure['noise']} The map fluttered, and the compass spun.")
    world.para()
    world.say(f"Captain {captain.label} cried, \"Turn toward the biggest sound!\"")
    world.say(f"{mate.label} answered, \"Wait! What if the map is making a smaller sound for a reason?\"")
    world.say(f"Before they could agree, the crew {adventure['wrong']}.")
    world.say(f"The result was a real setback: {adventure['setback']}.")
    world.say("For a moment, the voyage looked like it would end in a soggy, grumpy failure.")
    world.para()
    world.say(f"{mate.label} knelt beside the map and listened. Under the racket, {adventure['clue']}.")
    world.say(f"\"There is our clue,\" said {mate.label}. \"The sound of glob is small, but it is telling the truth.\"")
    world.say(f"Captain {captain.label} nodded. \"Then we will follow glob together.\"")
    world.say(f"The crew {adventure['fix']}.")
    world.para()
    world.say(f"The plan worked: {adventure['rescue']}.")
    world.say(f"Captain {captain.label} said, \"Next time, we listen before we leap.\"")
    world.say(f"{mate.label} grinned. \"And we never forget glob!\"")
    world.say(f"{adventure['lesson']}")
    world.say(f"The pirate tale ended happily: {adventure['ending']}.")

    world.facts.update(
        wrong=True,
        setback=True,
        clue_found=True,
        glob_followed=True,
        happy=True,
        adventure_index=_token(params) % len(ADVENTURES),
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    a = world.facts["adventure"]
    p = world.facts["params"]
    return [
        f"Write a child-friendly pirate tale about {p.captain}, {p.mate}, and the sound glob.",
        f"Tell how a pirate crew gets into trouble at {a['place']} by following loud sound effects.",
        "Show a bad turn becoming a happy ending when the crew listens carefully and follows the quiet clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    a = world.facts["adventure"]
    return [
        QAItem(
            f"Where did {p.captain} and {p.mate} sail?",
            f"They sailed {p.ship} toward {a['place']} with a treasure map on the deck.",
        ),
        QAItem(
            "What mistake did the crew make?",
            f"They {a['wrong']}.",
        ),
        QAItem(
            "What made the first part of the voyage go badly?",
            f"The crew suffered this setback: {a['setback']}.",
        ),
        QAItem(
            "What clue helped the pirates?",
            f"They discovered that {a['clue']}.",
        ),
        QAItem(
            "How did the crew fix the problem?",
            f"They {a['fix']}.",
        ),
        QAItem(
            "What did glob mean to the crew?",
            "Glob was the small, useful sound that showed the pirates which clue to trust beneath the louder noises.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily when {a['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pirate ship?", "A pirate ship is a sailing vessel used by pirates to travel across the sea."),
        QAItem("What is a sound effect?", "A sound effect is a made or recorded sound used to help show what is happening."),
        QAItem("Why can quiet sounds be useful?", "A quiet sound can be useful because it may carry an important clue without being buried in a noisy crowd."),
    ]


ASP_RULES = r"""
confused(S) :- loud_sounds(S), wrong_turn(S).
bad_ending(S) :- confused(S), setback(S).
good_clue(S) :- glob_heard(S), careful_listening(S).
happy_ending(S) :- bad_ending(S), good_clue(S), safe_route(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("loud_sounds", "story1"),
            asp.fact("wrong_turn", "story1"),
            asp.fact("setback", "story1"),
            asp.fact("glob_heard", "story1"),
            asp.fact("careful_listening", "story1"),
            asp.fact("safe_route", "story1"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate tale about Glob and useful sound effects.")
    parser.add_argument("--captain", choices=NAMES)
    parser.add_argument("--mate", choices=NAMES)
    parser.add_argument("--ship", choices=SHIPS)
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
    captain = args.captain or rng.choice(NAMES)
    mate = args.mate or rng.choice([n for n in NAMES if n != captain])
    ship = args.ship or rng.choice(SHIPS)
    return StoryParams(captain=captain, mate=mate, ship=ship)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:8} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  facts: {sorted(k for k in world.facts if k != 'params')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
    StoryParams(captain="Luna", mate="Pip", ship="the Jolly Button"),
    StoryParams(captain="Mara", mate="Finn", ship="the Sea Sprout"),
    StoryParams(captain="Cora", mate="Beau", ship="the Moon Kettle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
