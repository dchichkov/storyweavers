#!/usr/bin/env python3
"""
Historic Shutter Friendship Problem Solving Pirate Tale
=======================================================

A small self-contained pirate storyworld about friends solving a problem aboard
a historic harbor ship with a stubborn shutter in the way.

Seed words:
- historic
- shutter

Domain premise:
A friendly pirate crew finds a problem on an old ship at a harbor museum. A
stuck shutter blocks light or a needed view, and the crew must use teamwork,
careful thinking, and a brief spoken exchange to solve the problem.

The world model tracks physical meters and emotional memes:
- meters: distance, jam, light, fit, safety, repair
- memes: worry, trust, courage, relief, pride, friendship

The story should feel like a classic pirate tale, but child-facing and gentle:
a clear beginning, a problem, an attempt that fails, a better plan, and a final
image showing what changed.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

PLACE_NAMES = [
    "the old harbor museum ship",
    "the creaking dockside sloop",
    "the captain's historic lantern deck",
    "the weathered pirate gallery",
    "the tide-battered lookout cabin",
]

CHARACTERS = [
    ("Mara", "girl"),
    ("Jory", "boy"),
    ("Pip", "boy"),
    ("Lina", "girl"),
    ("Nell", "girl"),
    ("Tobin", "boy"),
]

HELPERS = [
    ("Captain Reef", "he"),
    ("Old Sable", "she"),
    ("Bosun Brine", "he"),
    ("Aunt Tide", "she"),
    ("Mate Finch", "he"),
]

PROBLEMS = [
    {
        "goal": "open the shutter so the captain can read the map in the museum cabin",
        "obstacle": "The wooden shutter had swollen shut with sea mist and would not budge.",
        "failed_attempt": "Jory pulled hard on the handle, but the shutter only groaned and stayed closed.",
        "clue": "Mara noticed a thin line of sand packed inside the hinge groove.",
        "solution": "The friends brushed the hinge clean, lifted the shutter together, and guided it open with a slow push.",
        "result": "Sunlight spilled across the map table, and the captain could read the route again.",
        "lesson": "small clues and steady hands can solve a stuck problem better than force",
        "ending": "the open shutter flashed bright as a gold coin and the old map shone on the table",
        "dialogue": '"Easy now," said Mara. "Let us clean the hinge before we pull again."',
    },
    {
        "goal": "fix a shutter that blocked the signal lantern from shining to the boat",
        "obstacle": "One shutter latch had slipped behind a bent nail and jammed tight.",
        "failed_attempt": "Pip tried to wiggle the latch with a spoon, but the spoon only skated away.",
        "clue": "Lina saw that the bent nail left just enough room for a ribbon loop.",
        "solution": "The friends threaded a ribbon through the gap, eased the latch free, and tied it back in place.",
        "result": "The lantern glowed straight out over the water, and the waiting boat saw the signal at once.",
        "lesson": "a careful tool can help where a hurried tug cannot",
        "ending": "the lantern beam cut a bright path through the mist like a friendly star",
        "dialogue": '"Try the ribbon," said Lina. "This jam needs a gentler trick."',
    },
    {
        "goal": "repair a shutter in the ship's gallery so the painted pirate flag would not fade",
        "obstacle": "The shutter hung crooked and caught on a loose board each time it moved.",
        "failed_attempt": "Nell pushed from the top, but that only made the board squeak louder.",
        "clue": "Tobin found a loose peg under the bench that fit the board's missing notch.",
        "solution": "The friends set the peg, squared the shutter, and slid it shut without another scrape.",
        "result": "The painted flag stayed in cool shade, safe from the noon sun.",
        "lesson": "repairing the right part can fix the whole trouble",
        "ending": "the shutter sat straight and neat, like a small ship ready for calm water",
        "dialogue": '"We do not need more force," said Tobin. "We need the right peg."',
    },
    {
        "goal": "free a shutter that covered the captain's historic compass room",
        "obstacle": "Salt crystals had crusted the track and pinned the shutter in place.",
        "failed_attempt": "Captain Reef tapped the frame twice, but the crust would not crack.",
        "clue": "Old Sable spotted a kettle of warm water near the stove.",
        "solution": "The friends dripped warm water along the track, waited, and then lifted the loosened shutter together.",
        "result": "The compass room opened, and the brass needle could turn without shadow.",
        "lesson": "waiting for the right helper can be part of the solution",
        "ending": "the compass needle gleamed inside a square of clean morning light",
        "dialogue": '"Warm water first," said Old Sable. "That salt has been bossing us long enough."',
    },
    {
        "goal": "make a shutter open so the crew could read the ship's logbook",
        "obstacle": "A toy crab had wedged its shell toy into the frame as a joke.",
        "failed_attempt": "Mate Finch laughed and tried to tug the shell free, but it only wedged tighter.",
        "clue": "Mara heard the shell rattle if it was tilted instead of pulled.",
        "solution": "The friends tipped the frame, slid the toy crab out, and opened the shutter without breaking it.",
        "result": "The logbook pages turned in the fresh light, and the captain found the missing date.",
        "lesson": "sometimes a problem wants a tilt, not a tug",
        "ending": "the little shell toy sat on the sill while the logbook lay open and clear",
        "dialogue": '"Tilt it," said Mara. "This crab wants to roll home, not be yanked."',
    },
]

ASP_RULES = r"""
goal(open_shutter).
problem(jam).
friendship(share_work).
problem_solving(find_clue).

solved :- goal(open_shutter), problem(jam), friendship(share_work), problem_solving(find_clue), clue(found), action(done).
bright_scene :- solved.
#show solved/0.
#show bright_scene/0.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "jam": 0.0, "light": 0.0, "fit": 0.0, "safety": 0.0, "repair": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "trust": 0.0, "courage": 0.0, "relief": 0.0, "pride": 0.0, "friendship": 0.0})


@dataclass
class StoryParams:
    setting: str = ""
    hero_name: str = ""
    hero_type: str = ""
    friend_name: str = ""
    friend_type: str = ""
    helper_name: str = ""
    helper_type: str = ""
    problem_index: int = 0
    voice_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about friendship and problem solving around a historic shutter.")
    ap.add_argument("--setting")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type")
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
    hero_name, hero_type = rng.choice(CHARACTERS)
    friend_name, friend_type = rng.choice(CHARACTERS)
    helper_name, helper_type = rng.choice(HELPERS)
    setting = args.setting or rng.choice(PLACE_NAMES)
    if args.hero_name:
        hero_name = args.hero_name
    if args.hero_type:
        hero_type = args.hero_type
    if args.friend_name:
        friend_name = args.friend_name
    if args.friend_type:
        friend_type = args.friend_type
    if args.helper_name:
        helper_name = args.helper_name
    if args.helper_type:
        helper_type = args.helper_type
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_name=helper_name,
        helper_type=helper_type,
        problem_index=rng.randrange(len(PROBLEMS)),
        voice_mode=rng.randrange(8),
    )


def tell(params: StoryParams) -> World:
    if params.problem_index < 0 or params.problem_index >= len(PROBLEMS):
        raise StoryError("problem_index out of range")
    problem = PROBLEMS[params.problem_index]
    place = params.setting or PLACE_NAMES[params.problem_index % len(PLACE_NAMES)]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="person", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="person", type=params.friend_type, label=params.friend_name))
    helper = world.add(Entity(id="helper", kind="person", type=params.helper_type, label=params.helper_name))
    shutter = world.add(Entity(id="shutter", kind="thing", type="shutter", label="historic shutter"))
    map_item = world.add(Entity(id="map", kind="thing", type="map", label="old map"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="signal lantern"))

    world.facts.update(problem=problem, hero=hero, friend=friend, helper=helper, shutter=shutter, map_item=map_item, lantern=lantern)

    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    helper.memes["trust"] += 1

    openers = [
        f"On a salty morning at {place}, {hero.label} and {friend.label} climbed aboard the historic ship.",
        f"At {place}, the pirate crew felt the deck sway under their boots as they stepped toward a stubborn shutter.",
        f"{helper.label} called the young crew to {place}, where an old shutter had become the day's trouble.",
        f"The wind was brisk at {place}, and {hero.label} and {friend.label} found a problem waiting by the cabin wall.",
    ]
    world.say(openers[params.voice_mode % len(openers)])
    world.say(f'Their task was to {problem["goal"]}.')
    world.say(f'{problem["obstacle"]} The crew knew they would need friendship and problem solving, not bluster.')
    world.para()

    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(f'"We can fix it fast," said {friend.label}. {problem["failed_attempt"]}')
    world.say(f'"Hold, matey," said {helper.label}. {problem["dialogue"]}')
    world.say(problem["clue"])
    world.say(problem["solution"])
    world.para()

    shutter.meters["repair"] = 1.0
    shutter.meters["fit"] = 1.0
    shutter.meters["jam"] = 0.0
    shutter.meters["light"] = 1.0
    hero.memes["courage"] += 1
    friend.memes["courage"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    helper.memes["pride"] += 1
    helper.memes["friendship"] += 1
    world.say(problem["result"])
    world.say(f'The captain smiled, and {helper.label} said, "That is fine work, crew."')
    world.say(f"{hero.label} answered, \"We solved it together, and that made the job easier.\"")
    world.para()

    world.say(f"By the end of the day, {problem['lesson']}.")
    world.say(f"The final sight was simple and bright: {problem['ending']}.")
    world.log(f"place={place}")
    world.log(f"problem={params.problem_index}")
    return world


def generation_prompts(world: World) -> list[str]:
    problem = world.facts["problem"]  # type: ignore[assignment]
    hero = world.facts["hero"]  # type: ignore[assignment]
    friend = world.facts["friend"]  # type: ignore[assignment]
    helper = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write a pirate tale about {hero.label} and {friend.label} solving a problem on a historic ship.",
        f"Tell a child-friendly story where {helper.label} helps open a shutter and the friends learn teamwork.",
        f"Use the words historic, shutter, friendship, and problem solving in a short pirate adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    problem = world.facts["problem"]  # type: ignore[assignment]
    hero = world.facts["hero"]  # type: ignore[assignment]
    friend = world.facts["friend"]  # type: ignore[assignment]
    helper = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did the crew need to solve?",
            answer=f"They needed to {problem['goal']}. The shutter was stuck, so the friends had to find a careful fix.",
        ),
        QAItem(
            question=f"Why did the first attempt fail?",
            answer=f"It failed because {problem['failed_attempt'][0].lower() + problem['failed_attempt'][1:]}. Force alone was not the answer.",
        ),
        QAItem(
            question=f"What clue helped the crew?",
            answer=f"{problem['clue']} That clue showed them what part of the shutter needed attention.",
        ),
        QAItem(
            question=f"How did the friends solve the shutter problem?",
            answer=f"{problem['solution']} {problem['result']}",
        ),
        QAItem(
            question=f"What did {hero.label} learn?",
            answer=f"{hero.label} learned that {problem['lesson']}. Friendship made the solution easier to find.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a historic place?",
            answer="A historic place is a place from the past that people keep or remember because it matters to history.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a board or cover that opens and closes over a window or opening to control light and protect what is inside.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and working together kindly.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking about a difficulty, trying ideas, and choosing the one that works best.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type}, meters={meters}, memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("clue", "found"),
            asp.fact("action", "done"),
            asp.fact("friendship", "share_work"),
            asp.fact("problem_solving", "find_clue"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/0. #show bright_scene/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"solved/0", "bright_scene/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="the old harbor museum ship", hero_name="Mara", hero_type="girl", friend_name="Jory", friend_type="boy", helper_name="Captain Reef", helper_type="he", problem_index=0),
    StoryParams(setting="the creaking dockside sloop", hero_name="Pip", hero_type="boy", friend_name="Lina", friend_type="girl", helper_name="Old Sable", helper_type="she", problem_index=1),
    StoryParams(setting="the captain's historic lantern deck", hero_name="Nell", hero_type="girl", friend_name="Tobin", friend_type="boy", helper_name="Bosun Brine", helper_type="he", problem_index=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0. #show bright_scene/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("ASP model:", " ".join(str(a) for a in asp.one_model(asp_program("#show solved/0. #show bright_scene/0."))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
