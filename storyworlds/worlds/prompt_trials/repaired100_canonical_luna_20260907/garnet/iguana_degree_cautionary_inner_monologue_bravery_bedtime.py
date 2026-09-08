#!/usr/bin/env python3
"""
A gentle bedtime storyworld about an iguana, a degree of bravery, and learning
that courage can listen before it leaps.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    iguana: Item
    keeper: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    iguana_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Tessa", "Owen", "Ivy", "Pip", "Suri"]
IGUANA_NAMES = ["Jade", "Moss", "Pebble", "Clover", "Basil", "Fern"]
PLACES = [
    "the moonlit garden",
    "the quiet rooftop",
    "the sleepy greenhouse",
    "the warm courtyard",
    "the little house by the pond",
]


ASP_RULES = r"""
#show cautious/1.
#show brave/1.
#show safe/1.
#show learns/1.

cautious(H) :- notices_risk(H).
brave(H) :- chooses_care(H).
safe(I) :- uses_ramp(I).
learns(H) :- listens_to_keeper(H), chooses_care(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("notices_risk", "hero"),
            asp.fact("chooses_care", "hero"),
            asp.fact("uses_ramp", "iguana"),
            asp.fact("listens_to_keeper", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = """
#show cautious/1.
#show brave/1.
#show safe/1.
#show learns/1.
"""
    model = asp.one_model(asp_program(shown))
    found = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            if value.type == value.type.Number:
                args.append(value.number)
            elif value.type == value.type.String:
                args.append(value.string)
            else:
                args.append(value.name)
        found.add((atom.name, tuple(args)))
    expected = {
        ("cautious", ("hero",)),
        ("brave", ("hero",)),
        ("safe", ("iguana",)),
        ("learns", ("hero",)),
    }
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about an iguana and a degree of bravery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--iguana-name", choices=IGUANA_NAMES)
    parser.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        iguana_name=args.iguana_name or rng.choice(IGUANA_NAMES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"height": 1.25, "distance_to_iguana": 0.0},
        memes={"curiosity": 0.8, "worry": 0.45, "bravery": 0.55},
    )
    iguana = Item(
        id="iguana",
        label=params.iguana_name,
        phrase=f"the iguana {params.iguana_name}",
        kind="animal",
        owner="hero",
        meters={"height": 0.42, "gap_to_lantern": 2.0, "safe_ramp_length": 1.4},
        memes={"calm": 0.7, "trust": 0.65, "adventure": 0.75},
    )
    keeper = Item(
        id="keeper",
        label="Aunt Sol",
        phrase="Aunt Sol",
        kind="helper",
        meters={"distance_to_hero": 0.0},
        memes={"patience": 0.95, "care": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.iguana_name}|{params.place}")
    return World(
        hero=hero,
        iguana=iguana,
        keeper=keeper,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    discovery: str,
    risk: str,
    method: str,
    turn: str,
    resolution: str,
    ending: str,
    degree: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        cautious=True,
        brave=True,
        safe=True,
        learned=True,
    )
    return " ".join(lines)


def _moon_ladder_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    ig = world.iguana.label
    p = world.place
    glow = _choice(rng, ["a silver moth", "a pale beetle", "a tiny white flower"])
    discovery = f"{ig} had climbed onto the high moon gate to watch {glow}"
    risk = "the gate was narrow, smooth, and too high for a hurried rescue"
    method = "a low wooden ramp with a towel across its top"
    turn = f"{h} stopped reaching upward and noticed that {ig} kept looking toward the warm ramp"
    resolution = f"{h} placed {method} against the gate, then waited quietly while {ig} walked down"
    ending = "the iguana curled beside the lantern, and the moon made a small silver road across the floor"
    degree = "bravery grew by one careful degree when the child chose patience over a risky climb"
    lines = [
        f"At bedtime in {p}, {h} carried a lantern outside and found {ig} blinking at the moon.",
        f"The little iguana had climbed onto the high moon gate to watch {glow}, but the gate was narrow and smooth.",
        f"{h} reached for the gate. Inside, a worried thought whispered, \"Be brave. Leap up now.\"",
        f"Aunt Sol touched {h}'s sleeve. \"What would brave look like if it kept both of you safe?\" she asked.",
        f"{h} looked again. {ig} was not asking for a leap; the iguana was watching the warm doorway below.",
        f"The child made {method}. \"One slow step at a time,\" {h} said. \"Would you like to try?\"",
        f"{ig} lowered one claw, then another. {h} held the lantern still, and the iguana walked down without slipping.",
        f"{h} felt the worried thought grow quieter. The child learned that {degree}.",
        f"At last, {ending}.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        lines=lines,
    )


def _rain_barrel_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    ig = world.iguana.label
    p = world.place
    sound = _choice(rng, ["a soft drumbeat", "a silver patter", "a sleepy splash"])
    discovery = f"{ig} was stranded on a rain barrel after following {sound}"
    risk = "the barrel was slick, and jumping from it would have landed the iguana on hard stones"
    method = "a broad board tied to the barrel with a garden cloth"
    turn = f"{h} understood that a fast grab could frighten {ig} into a dangerous jump"
    resolution = f"{h} set {method} in place and spoke in a low, steady voice until {ig} crossed"
    ending = "the iguana rested beneath a dry fern while rain whispered itself to sleep"
    degree = "bravery was not a thunderclap but a small degree of steadiness repeated until help arrived"
    lines = [
        f"Rain tapped the roof at bedtime in {p}, making {sound}.",
        f"{h} looked through the window and saw {ig} stranded on a round rain barrel.",
        f"The barrel was slick, and the stones below were hard. Inside, {h}'s mind murmured, \"Run out and grab the iguana!\"",
        f"Aunt Sol opened the door only a little. \"If you rush, what might {ig} do?\" she asked.",
        f"\"Jump,\" said {h}. \"Then let us give those feet a safer choice,\" said Aunt Sol.",
        f"Together they laid {method}. {h} knelt several steps away and whispered, \"You can come when you are ready.\"",
        f"{ig} stretched one foot onto the board. \"Good and slow,\" said {h}. The iguana crossed while the rain kept its gentle rhythm.",
        f"{h} smiled as {ig} reached the dry fern. The child learned that {degree}.",
        f"Then {ending}.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        lines=lines,
    )


def _shadow_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    ig = world.iguana.label
    p = world.place
    shape = _choice(rng, ["a long dragon", "a sleepy giant", "a crooked bird"])
    discovery = f"the lantern cast {ig}'s shadow as {shape} across the wall"
    risk = "the moving shadow startled the iguana toward an open window"
    method = "a lowered lamp and a folded blanket beside the sill"
    turn = f"{h} noticed that the shadow grew whenever the lantern moved closer"
    resolution = f"{h} lowered the lamp, closed the window, and guided {ig} onto {method.split(' and ')[1]}"
    ending = "the wall held only a small, ordinary iguana shadow beside the quiet bed"
    degree = "courage became one thoughtful degree stronger when the child studied the frightening shape"
    lines = [
        f"Near bedtime in {p}, {h} placed a lantern beside {ig}'s glass house.",
        f"At once, the wall showed {shape}. The shadow stretched its neck whenever {ig} moved.",
        f"{h}'s inner monologue fluttered: \"A monster! Be brave and chase it away!\"",
        f"Aunt Sol whispered, \"Before bravery runs, let curiosity turn on a little light.\"",
        f"{h} moved the lantern back. The shadow shrank. The child moved it forward, and the shadow grew.",
        f"\"It is only light making a big picture,\" said {h}. But the iguana was still edging toward the open window.",
        f"{h} closed the window, lowered the lamp, and placed a folded blanket beside the sill. {ig} stepped onto it and settled.",
        f"The child learned that {degree}, and that understanding can guide brave hands.",
        f"By moonrise, {ending}.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        lines=lines,
    )


def _bell_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    ig = world.iguana.label
    p = world.place
    sound = _choice(rng, ["ding", "plink", "chime"])
    discovery = f"{ig} had nudged a hanging bell and made a bright {sound}"
    risk = "the startling bell sent the iguana toward a loose screen"
    method = "a soft cloth placed between the bell and its hook"
    turn = f"{h} learned that stopping the sound mattered more than chasing the frightened iguana"
    resolution = f"{h} covered the bell with {method.split(' placed between ')[0]} and secured the screen before calling softly"
    ending = "the bell slept under its cloth while the iguana breathed calmly beside a bowl of greens"
    degree = "bravery rose by a quiet degree when the child made the room safe before moving closer"
    lines = [
        f"In the warm courtyard at bedtime, {h} heard a bright {sound}.",
        f"{ig} had bumped a hanging bell, and the sudden ringing sent the iguana toward a loose screen.",
        f"{h}'s inner monologue cried, \"Go quickly! Hurry!\"",
        f"Aunt Sol said, \"Quick feet are useful after careful eyes. What is loose?\"",
        f"{h} saw the screen, the swinging bell, and the narrow path between them.",
        f"The child secured the screen first, then covered the bell with a soft cloth. The ringing stopped.",
        f"\"Now we can breathe,\" said {h}. \"Now we can come home,\" said Aunt Sol.",
        f"{ig} walked back to the greens. The child learned that {degree}.",
        f"Before sleep, {ending}.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        lines=lines,
    )


def _star_window_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    ig = world.iguana.label
    p = world.place
    star = _choice(rng, ["the evening star", "a bright planet", "a moonlit cloud"])
    discovery = f"{ig} climbed toward the window to follow {star}"
    risk = "the curtain cord was looped near the sill and could catch a small claw"
    method = "a folded towel ramp and a tied-back curtain"
    turn = f"{h} saw that reaching for {ig} might tighten the cord"
    resolution = f"{h} tied back the curtain, placed {method.split(' and ')[0]}, and invited {ig} down"
    ending = "the window showed stars, while the iguana slept safely under its broad leaf"
    degree = "the child found a brave degree between fear and foolishness"
    lines = [
        f"At the little house by the pond, bedtime moonlight shone through the window.",
        f"{ig} climbed toward {star}, and {h} followed with a sleepy lantern.",
        f"\"I must rescue you now,\" thought {h}. \"I must be brave.\"",
        f"Aunt Sol pointed gently. \"Look before you reach. What do you see near the sill?\"",
        f"{h} saw a curtain cord looped beside the iguana's claw. A quick grab might pull it tighter.",
        f"The child tied back the curtain and made a folded towel ramp. \"Come down when you are ready,\" said {h}.",
        f"{ig} tested the ramp, blinked at {star}, and walked safely to the floor.",
        f"{h} learned that {degree}. Courage had listened before it acted.",
        f"At last, {ending}.",
    ]
    return _record_story(
        world,
        discovery=discovery,
        risk=risk,
        method=method,
        turn=turn,
        resolution=resolution,
        ending=ending,
        degree=degree,
        lines=lines,
    )


ARC_BUILDERS = [
    _moon_ladder_arc,
    _rain_barrel_arc,
    _shadow_arc,
    _bell_arc,
    _star_window_arc,
]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7C)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about {world.iguana.label}?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What made the situation risky?",
            answer=f"The situation was risky because {facts['risk']}.",
        ),
        QAItem(
            question=f"How did {h} help the iguana?",
            answer=f"{h} helped by {facts['resolution'].lower()}.",
        ),
        QAItem(
            question="What did bravery mean in this story?",
            answer=f"Bravery meant {facts['degree']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an iguana?",
            answer="An iguana is a plant-eating lizard with strong legs, a long tail, and a row of spines along its back.",
        ),
        QAItem(
            question="What does a degree mean here?",
            answer="A degree is a small amount or step. In the story, bravery grows one careful step at a time.",
        ),
        QAItem(
            question="Why should someone be cautious near a high place?",
            answer="A high place may be slippery or unsafe, so a person should inspect the danger and use a steady, safe way to help.",
        ),
        QAItem(
            question="Can being cautious be brave?",
            answer="Yes. Being cautious can be brave when it means staying calm, noticing risks, and choosing a safe action instead of rushing.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story about an iguana and a child's growing bravery.",
        f"Tell a cautionary story set in {world.place}, where {world.iguana.label} needs careful help.",
        "Use a quiet inner monologue to show that bravery can mean listening before acting.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.iguana, world.keeper]:
        lines.append(
            f"  {ent.id:7} {ent.kind:9} label={ent.label!r} "
            f"owner={ent.owner!r} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        output.append(f"{i}. {prompt}")
    output.append("")
    output.append("== Story QA ==")
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.append("")
    output.append("== World QA ==")
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def _validate(world: World) -> None:
    if world.iguana.meters["safe_ramp_length"] <= 0:
        raise StoryError("The iguana needs a positive-length safe route.")
    if world.iguana.meters["gap_to_lantern"] < 0:
        raise StoryError("The iguana's distance from the lantern cannot be negative.")
    if world.hero.memes["bravery"] < 0 or world.hero.memes["bravery"] > 1:
        raise StoryError("The hero's bravery must be between zero and one.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _validate(world)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show cautious/1.\n"
                "#show brave/1.\n"
                "#show safe/1.\n"
                "#show learns/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show cautious/1.\n"
                "#show brave/1.\n"
                "#show safe/1.\n"
                "#show learns/1."
            )
        )
        print("ASP model:")
        for atom in sorted(str(atom) for atom in model):
            print(atom)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                iguana_name="Jade",
                place="the moonlit garden",
                seed=base_seed,
            ),
            StoryParams(
                name="Milo",
                iguana_name="Moss",
                place="the sleepy greenhouse",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Nia",
                iguana_name="Clover",
                place="the warm courtyard",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Tessa",
                iguana_name="Fern",
                place="the little house by the pond",
                seed=base_seed + 3,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} and {params.iguana_name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
