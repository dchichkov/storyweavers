#!/usr/bin/env python3
"""
A small mythic storyworld about a plumber, a blocked spring, and the virtues of
problem solving, bravery, and kindness.
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
    plumber_name: str = "Luna"
    helper_name: str = "Milo"
    village: str = "Willowmere"
    tool: str = "a brass wrench"


NAMES = ["Luna", "Milo", "Nia", "Tavi", "Orin", "Pia", "Suri", "Theo"]
VILLAGES = ["Willowmere", "Brightbrook", "Mossbell", "Sunstone"]
TOOLS = ["a brass wrench", "a silver pipe key", "a wooden plunger", "a moon-shaped spanner"]

INCIDENTS = [
    {
        "spring": "the ancient spring beneath the hill",
        "problem": "a black root had curled through the water pipe",
        "clue": "the water made a hollow knocking sound whenever the root moved",
        "solution": "listen for the knock, loosen the root with a warm stone, and guide it out instead of cutting it",
        "danger": "the hill trembled and a crack opened beside the spring",
        "gift": "the freed root curled into a living bridge over the stream",
        "lesson": "A patient mind can find a kinder path through a hard problem.",
    },
    {
        "spring": "the fountain of the village square",
        "problem": "three pebbles from a sleeping giant's crown blocked its narrow pipe",
        "clue": "the pebbles chimed in a different order whenever the moonlight touched them",
        "solution": "copy the moonlit order and lift each pebble with a loop of river grass",
        "danger": "the fountain rose like a silver tower and threatened to flood the square",
        "gift": "the giant awoke only long enough to bless the village with clear water",
        "lesson": "Courage is strongest when it makes room for another creature's rest.",
    },
    {
        "spring": "the golden bathhouse of the hill spirits",
        "problem": "a proud little dragon had stuffed treasure coins into the drain",
        "clue": "the dragon sobbed whenever anyone called the coins useless",
        "solution": "ask the dragon why the coins mattered, then trade a safe basket for the blocked treasure",
        "danger": "steam filled the bathhouse while the dragon's tail struck the old pipes",
        "gift": "the dragon used its warm breath to mend every cracked pipe",
        "lesson": "Kind words can open a door that force would only close.",
    },
    {
        "spring": "the cloud well above the village",
        "problem": "a silver feather had wedged itself inside the rain pipe",
        "clue": "the feather hummed whenever someone spoke an honest promise",
        "solution": "climb the windy tower, promise to return the feather, and pull it free with a soft cloth",
        "danger": "the ladder shook above the clouds and thunder rolled around the tower",
        "gift": "the sky bird returned and filled the well with gentle rain",
        "lesson": "Bravery means doing the careful thing even while your knees tremble.",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    plumber = world.add(Entity(params.plumber_name, "character", "plumber", params.plumber_name))
    helper = world.add(Entity(params.helper_name, "character", "helper", params.helper_name))
    spring = world.add(Entity("spring", "place", "water_source", "the village water source"))
    tool = world.add(Entity("tool", "thing", "plumbing_tool", params.tool))
    plumber.meters.update(skill=1.0, courage=0.5)
    plumber.memes.update(kindness=0.5, worry=0.2)
    helper.meters.update(observation=1.0)
    helper.memes.update(trust=0.7)
    spring.meters.update(flow=0.0, danger=0.4)
    tool.meters.update(strength=1.0)
    world.facts.update(plumber=plumber, helper=helper, spring=spring, tool=tool)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.plumber_name}|{params.helper_name}|{params.village}|{params.tool}"
    ))


def tell_story(params: StoryParams) -> World:
    if params.plumber_name == params.helper_name:
        raise StoryError("The plumber and helper must have different names.")
    if params.tool not in TOOLS:
        raise StoryError("That tool is not registered for this mythic plumbing story.")

    world = World()
    _setup(world, params)
    plumber = world.facts["plumber"]
    helper = world.facts["helper"]
    spring = world.facts["spring"]
    tool = world.facts["tool"]
    incident = INCIDENTS[_token(params) % len(INCIDENTS)]

    world.say(
        f"In the old days, when rivers still whispered names, {plumber.label} was the plumber of "
        f"{params.village}, and {helper.label} was the sharp-eyed child who carried {tool.label}."
    )
    world.say(
        f"One dawn, {incident['spring']} fell silent. The people of {params.village} searched the dry stones, "
        f"but only {plumber.label} dared to descend beneath the hill."
    )
    world.say(f"Inside the dark passage, {plumber.label} discovered that {incident['problem']}.")

    world.para()
    world.say(f'"Should I pull hard?" {plumber.label} asked.')
    world.say(f'"First listen," {helper.label} replied. "The pipe is telling us what it needs."')
    world.say(f"That was good advice, for {incident['clue']}.")

    world.para()
    world.say(
        f"{plumber.label} studied the pipe instead of striking it. The stone floor shivered, and "
        f"{incident['danger']}. Fear fluttered in the plumber's chest, but bravery was not the absence of fear."
    )
    world.say(f'"Stay behind me," {plumber.label} said. "If the tunnel shifts, run toward the sunlight."')
    world.say(f'"I will stay beside you," {helper.label} answered. "We can solve it together."')

    world.para()
    world.say(
        f"Then {plumber.label} remembered the old rule of the water folk: {incident['solution']}."
    )
    world.say(
        f"The plumber worked slowly while {helper.label} held the lamp and watched the stones. "
        "Neither of them mocked the thing that had caused the trouble."
    )
    world.say(
        f"When the last obstruction slipped free, the pipe roared, the spring awoke, and "
        f"{incident['gift']}."
    )

    world.para()
    world.say(
        f"Clear water flowed through {params.village}, filling cups, gardens, and the little stone basin "
        "where travelers rested."
    )
    world.say(
        f'"You saved us with your hands," {helper.label} said. '
        f'"And you saved us with your questions," {plumber.label} replied.'
    )
    world.say(f"{incident['lesson']} The people remembered that day whenever a pipe began to groan.")

    plumber.meters["courage"] = 1.0
    plumber.memes["kindness"] = 1.0
    spring.meters["flow"] = 1.0
    spring.meters["danger"] = 0.0
    world.facts.update(
        params=params,
        incident=incident,
        incident_index=_token(params) % len(INCIDENTS),
        solved=True,
        bravery=True,
        kindness=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Tell a mythic story about plumber {p.plumber_name} repairing {incident['spring']} in {p.village}.",
        f"Show how {p.plumber_name} uses problem solving, bravery, and kindness instead of force.",
        f"Include a helpful exchange between {p.plumber_name} and {p.helper_name}, a dangerous turn, and a restored water source.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"What problem did plumber {p.plumber_name} find?",
            answer=f"{incident['problem'].capitalize()} The blockage stopped {incident['spring']} from giving water.",
        ),
        QAItem(
            question="What clue helped the plumber solve the problem?",
            answer=f"The clue was that {incident['clue']}. Listening to that clue helped the plumber choose a careful method.",
        ),
        QAItem(
            question="How did the plumber show bravery?",
            answer=f"{incident['danger'].capitalize()} Even while afraid, the plumber entered the danger and kept working carefully.",
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"The plumber chose to understand the cause and {incident['solution']}. That gentle choice kept the problem from becoming worse.",
        ),
        QAItem(
            question="What did the helper contribute?",
            answer=f"{p.helper_name} noticed the important clue, held the lamp, and stayed beside the plumber so they could solve the problem together.",
        ),
        QAItem(
            question="How did the village know the repair worked?",
            answer=f"The spring returned to life, and {incident['gift']}. Clear water then flowed through {p.village}.",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=incident["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a plumber do?",
            answer="A plumber repairs and connects pipes that carry water or other liquids.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means observing a difficulty, thinking of possible choices, and testing a careful way to improve it.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing what is right or necessary even when something feels frightening.",
        ),
        QAItem(
            question="Why is kindness useful during a difficult repair?",
            answer="Kindness helps people and creatures feel safe enough to share clues, accept help, and find a solution without needless harm.",
        ),
    ]


ASP_RULES = r"""
confused_story(S) :- blocked_source(S), needs_repair(S).
problem_solved(S) :- listens_for_clue(S), careful_method(S).
brave_choice(S) :- danger_present(S), enters_danger(S).
kind_choice(S) :- understands_cause(S), avoids_harm(S).
happy_ending(S) :- problem_solved(S), brave_choice(S), kind_choice(S), water_flows(S).
valid_story(S) :- confused_story(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("blocked_source", "story1"),
        asp.fact("needs_repair", "story1"),
        asp.fact("listens_for_clue", "story1"),
        asp.fact("careful_method", "story1"),
        asp.fact("danger_present", "story1"),
        asp.fact("enters_danger", "story1"),
        asp.fact("understands_cause", "story1"),
        asp.fact("avoids_harm", "story1"),
        asp.fact("water_flows", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic plumbing storyworld about problem solving, bravery, and kindness."
    )
    parser.add_argument("--plumber-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=NAMES)
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--tool", choices=TOOLS)
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
    plumber = args.plumber_name or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != plumber]
    return StoryParams(
        seed=None,
        plumber_name=plumber,
        helper_name=args.helper_name or rng.choice(helper_choices),
        village=args.village or rng.choice(VILLAGES),
        tool=args.tool or rng.choice(TOOLS),
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
    lines.append(f"  solved={world.facts.get('solved')}")
    lines.append(f"  bravery={world.facts.get('bravery')}")
    lines.append(f"  kindness={world.facts.get('kindness')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(plumber_name="Luna", helper_name="Milo", village="Willowmere", tool="a brass wrench"),
    StoryParams(plumber_name="Nia", helper_name="Theo", village="Brightbrook", tool="a silver pipe key"),
    StoryParams(plumber_name="Suri", helper_name="Orin", village="Mossbell", tool="a wooden plunger"),
    StoryParams(plumber_name="Pia", helper_name="Tavi", village="Sunstone", tool="a moon-shaped spanner"),
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
        samples = [generate(params) for params in CURATED]
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
