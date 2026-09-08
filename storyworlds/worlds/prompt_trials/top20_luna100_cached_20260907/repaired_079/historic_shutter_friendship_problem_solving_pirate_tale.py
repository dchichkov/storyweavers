#!/usr/bin/env python3
"""
A child-facing pirate tale about a historic shutter, a friendship, and a clever repair.
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
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

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
    captain_name: str = "Luna"
    friend_name: str = "Pip"
    ship_name: str = "the Moonlit Gull"
    island: str = "Harbor Bell Island"


CAPTAINS = ["Luna", "Mara", "Nell", "Rosa", "Tessa", "Zara"]
FRIENDS = ["Pip", "Finn", "Jo", "Kit", "Ollie", "Sam"]
SHIPS = ["the Moonlit Gull", "the Coral Comet", "the Friendly Fox", "the Blue Parrot"]
ISLANDS = ["Harbor Bell Island", "Old Lantern Isle", "Cannonball Cove", "Sailor's Rest"]


INCIDENTS = [
    {
        "landmark": "the historic lighthouse",
        "shutter": "a heavy wooden shutter over the lighthouse lantern",
        "problem": "the shutter had swollen in the sea damp and would not lift",
        "risk": "the evening fog would soon hide the reef from every passing boat",
        "clue": "three tiny shells were wedged along its bottom edge",
        "plan": "use the shells as wedges and pull together when the tide tugged the rope",
        "repair": "slid the shells beneath the shutter, rubbed its hinges with fish oil, and counted three strong pulls",
        "result": "the old shutter rose with a friendly wooden groan",
        "ending": "the lighthouse beam swept across the waves and guided a fishing boat safely home",
        "lesson": "A small clue and a friend's steady help can open a very big door.",
    },
    {
        "landmark": "the historic map room",
        "shutter": "a painted shutter guarding the map room window",
        "problem": "a broken latch trapped the shutter closed",
        "risk": "the crew could not see the tide marks needed to find the hidden channel",
        "clue": "a brass button from an old sailor's coat lay beside the latch",
        "plan": "use the button as a pin while a friend held the latch straight",
        "repair": "threaded the brass button through the latch, tied it with sail thread, and tested it gently",
        "result": "the painted shutter clicked open",
        "ending": "sunlight fell on the tide map, and the crew sailed through the safe blue channel",
        "lesson": "Good problem solving begins when friends notice what others might overlook.",
    },
    {
        "landmark": "the historic fort gate",
        "shutter": "a broad iron shutter in the fort's old lookout",
        "problem": "sand had jammed its runners",
        "risk": "a storm was coming, and the harbor boats needed the lookout's warning flag",
        "clue": "a line of dry seaweed showed where the wind had pushed the sand",
        "plan": "clear the runners from the sheltered side before pushing the shutter",
        "repair": "swept away the sand with a palm brush, poured water along the runners, and pushed side by side",
        "result": "the iron shutter rolled free",
        "ending": "the warning flag flew before the storm, and every boat found shelter",
        "lesson": "A careful plan is stronger than a hurried shove.",
    },
]


MODES = [
    ("The sea shone like a silver coin beneath the morning sun.", "The first idea failed, but it also showed the friends where to look next."),
    ("A warm wind filled the pirate ship's bright red sail.", "Luna and her friend stopped blaming the stubborn thing and started studying it."),
    ("The island looked peaceful until a wooden clang rang from the shore.", "They treated the trouble as a puzzle they could solve together."),
]


def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(params.captain_name, "character", "captain", params.captain_name))
    friend = world.add(Entity(params.friend_name, "character", "friend", params.friend_name))
    ship = world.add(Entity("ship", "thing", "ship", params.ship_name))
    shutter = world.add(Entity("shutter", "thing", "historic_shutter", "historic shutter"))
    rope = world.add(Entity("rope", "thing", "rope", "hemp rope"))
    captain.meters.update(courage=1.0, patience=0.8)
    captain.memes["worry"] = 0.2
    friend.meters.update(observation=1.0, loyalty=1.0)
    friend.memes["trust"] = 1.0
    ship.meters["safety"] = 0.7
    shutter.meters.update(resistance=1.0, historic_value=1.0)
    rope.meters["strength"] = 1.0
    world.facts.update(captain=captain, friend=friend, ship=ship, shutter=shutter, rope=rope)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.captain_name}|{params.friend_name}|{params.ship_name}|{params.island}"
    ))


def tell_story(params: StoryParams) -> World:
    if params.captain_name == params.friend_name:
        raise StoryError("The captain and friend must have different names.")
    world = World()
    _setup(world, params)
    incident = INCIDENTS[_token(params) % len(INCIDENTS)]
    mode = MODES[(_token(params) // len(INCIDENTS)) % len(MODES)]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    ship = world.facts["ship"]
    shutter = world.facts["shutter"]

    world.say(mode[0])
    world.say(
        f"Captain {captain.label} and {friend.label} sailed {ship.label} to {params.island}, "
        f"where {incident['landmark']} stood above the harbor."
    )
    world.say(
        f"They had come to open {incident['shutter']} before the island boats needed its signal."
    )

    world.para()
    world.say(f"But {incident['problem']}.")
    world.say(f"The trouble mattered because {incident['risk']}.")
    world.say(
        f'“I can pull harder!” cried Captain {captain.label}. '
        f'“Wait,” said {friend.label}. “Let us see what is holding it.”'
    )
    world.say(mode[1])
    world.say(f"Captain {captain.label} pulled once. The shutter did not move, and the rope slipped into a puddle.")

    world.para()
    world.say(
        f"That first try was a bad ending for the morning: {incident['problem'].capitalize()} "
        "and the fog was drawing closer."
    )
    world.say(f"Then {friend.label} noticed that {incident['clue']}.")
    world.say(
        f'“The old shutter is not refusing us,” {friend.label} explained. '
        f'“It is asking for the right way.”'
    )
    world.say(f"Together they made a plan: {incident['plan']}.")

    world.para()
    world.say(f"Captain {captain.label} held the rope while {friend.label} prepared the repair.")
    world.say(f"They {incident['repair']}.")
    world.say(f"On the final pull, {incident['result']}.")

    shutter.meters["resistance"] = 0.0
    ship.meters["safety"] = 1.0
    captain.memes["worry"] = 0.0
    friend.memes["trust"] = 1.2
    world.fired.update({("notice_clue",), ("plan_together",), ("repair_shutter",)})

    world.say(
        f'“We did it because we listened to each other,” said Captain {captain.label}. '
        f'{friend.label} grinned. “That is what shipmates are for.”'
    )
    world.say(f"{incident['result'].capitalize()}, and {incident['ending']}.")
    world.say(incident["lesson"])
    world.say(
        f"That night, the friends shared warm cocoa on the deck while the historic shutter "
        "rested open beneath the stars."
    )
    world.facts.update(incident=incident, params=params, captain=captain, friend=friend)
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly pirate tale about {p.captain_name} and {p.friend_name} repairing {incident['shutter']}.",
        f"Show how friendship and problem solving help the crew overcome this problem: {incident['problem']}.",
        f"Tell a complete adventure with a failed first try, a useful clue, a shared plan, and a happy harbor ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            f"Where did Captain {p.captain_name} and {p.friend_name} sail?",
            f"They sailed {p.ship_name} to {p.island}, where {incident['landmark']} stood above the harbor.",
        ),
        QAItem(
            "What problem did the friends face?",
            f"{incident['problem'].capitalize()}.",
        ),
        QAItem(
            "Why was the problem important?",
            f"It mattered because {incident['risk']}.",
        ),
        QAItem(
            "What clue helped them?",
            f"{p.friend_name} noticed that {incident['clue']}.",
        ),
        QAItem(
            "How did friendship help solve the problem?",
            f"They listened to each other, made a shared plan, and then {incident['repair']}.",
        ),
        QAItem(
            "What happened after the repair?",
            f"{incident['result'].capitalize()}, and {incident['ending']}.",
        ),
        QAItem(
            "What lesson did the pirate friends learn?",
            incident["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a panel that can cover a window or opening to protect it from light, wind, or weather.",
        ),
        QAItem(
            "What does historic mean?",
            "Historic means important in history or connected with an earlier time.",
        ),
        QAItem(
            "Why do friends solve problems together?",
            "Friends can share ideas, notice different clues, and encourage one another when a problem is difficult.",
        ),
    ]


ASP_RULES = r"""
confused_crew(S) :- historic_shutter(S), shutter_stuck(S).
bad_turn(S) :- confused_crew(S), first_try_failed(S).
friendship(S) :- clue_noticed(S), plan_shared(S).
problem_solved(S) :- friendship(S), shutter_repaired(S).
happy_ending(S) :- bad_turn(S), problem_solved(S), harbor_safe(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("historic_shutter", "story1"),
        asp.fact("shutter_stuck", "story1"),
        asp.fact("first_try_failed", "story1"),
        asp.fact("clue_noticed", "story1"),
        asp.fact("plan_shared", "story1"),
        asp.fact("shutter_repaired", "story1"),
        asp.fact("harbor_safe", "story1"),
    ])


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
    parser = argparse.ArgumentParser(
        description="Pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain-name", choices=CAPTAINS)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--ship-name", choices=SHIPS)
    parser.add_argument("--island", choices=ISLANDS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain_name or rng.choice(CAPTAINS)
    friend = args.friend_name or rng.choice(FRIENDS)
    return StoryParams(
        captain_name=captain,
        friend_name=friend,
        ship_name=args.ship_name or rng.choice(SHIPS),
        island=args.island or rng.choice(ISLANDS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
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
    StoryParams(captain_name="Luna", friend_name="Pip", ship_name="the Moonlit Gull", island="Harbor Bell Island"),
    StoryParams(captain_name="Mara", friend_name="Finn", ship_name="the Coral Comet", island="Old Lantern Isle"),
    StoryParams(captain_name="Nell", friend_name="Jo", ship_name="the Friendly Fox", island="Cannonball Cove"),
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
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
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
