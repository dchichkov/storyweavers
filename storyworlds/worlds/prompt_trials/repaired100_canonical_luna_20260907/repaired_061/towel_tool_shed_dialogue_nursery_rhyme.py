#!/usr/bin/env python3
"""
A gentle nursery-rhyme storyworld about a towel, a tool shed, and a helpful
conversation that turns a small muddle into a tidy song.
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

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    shed: str = "tool shed"
    child: str = "Luna"
    helper: str = "Milo"
    towel: str = "blue towel"
    tool: str = "watering can"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SHEDS = ["tool shed", "garden shed", "little shed"]
CHILDREN = ["Luna", "Nina", "Pip", "Tess"]
HELPERS = ["Milo", "Finn", "Bess", "Otis"]
TOWELS = ["blue towel", "striped towel", "yellow towel", "soft red towel"]
TOOLS = ["watering can", "small rake", "wooden hammer", "green shovel"]

INCIDENTS = [
    {
        "opening": "By the door lay a towel, damp from the morning rain.",
        "problem": "A little puddle crept beneath the shelves, and the wooden hammer began to wobble.",
        "clue": "three bright drops leading from the window to the towel",
        "turn": "The friends lifted the towel together and found a loose shutter tapping in the breeze.",
        "fix": "They used the wooden hammer to tap the shutter closed, then spread the towel flat to dry.",
        "ending": "The towel dried in a sunny square, and the tools stood straight as a rhyme.",
    },
    {
        "opening": "A towel hung from a peg beside the rows of tools.",
        "problem": "A silver drip went tip-tap, tip-tap, into the corner where the small rake rested.",
        "clue": "a dark wet line beneath the roof beam",
        "turn": "The friends followed the line and found a tiny hole above the peg.",
        "fix": "They moved the tools away, placed the towel beneath the drip, and called for a grown-up to mend the roof.",
        "ending": "The last drop sang plink, then stopped, while the towel waved like a little flag.",
    },
    {
        "opening": "A towel was curled inside the tool shed like a sleeping cat.",
        "problem": "When the door swung wide, the towel slid toward the green shovel and tangled around its handle.",
        "clue": "a trail of dry leaves caught in the towel's fringe",
        "turn": "The friends saw that the wind had carried leaves through a crack and wrapped them in the cloth.",
        "fix": "They closed the crack with a board, freed the shovel gently, and shook the leaves into a neat pile.",
        "ending": "The towel rested on its peg, and the shovel gleamed beside the tidy leaves.",
    },
    {
        "opening": "A striped towel sat on a crate beside the watering can.",
        "problem": "The can was full, but its handle pointed toward the wall and no one could lift it safely.",
        "clue": "a bent cord looped around the handle",
        "turn": "The friends spoke softly, loosened the cord, and discovered that it had caught on a nail.",
        "fix": "They pulled the cord free, dried the handle with the towel, and carried the can outside together.",
        "ending": "The garden drank a silver sprinkle, and the towel danced on the shed line.",
    },
]


def build_world(params: StoryParams) -> World:
    if params.child == params.helper:
        raise StoryError("the child and helper must have different names")
    w = World(params)
    child = w.add(Entity("child", "character", "child", params.child))
    helper = w.add(Entity("helper", "character", "friend", params.helper))
    towel = w.add(Entity("towel", "thing", "towel", params.towel))
    tool = w.add(Entity("tool", "thing", "tool", params.tool))
    incident = INCIDENTS[(params.seed or 0) % len(INCIDENTS)]
    w.facts.update(child=child, helper=helper, towel=towel, tool=tool, incident=incident)
    return w


def narrate(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    towel: Entity = world.facts["towel"]  # type: ignore[assignment]
    tool: Entity = world.facts["tool"]  # type: ignore[assignment]
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]

    child.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0
    world.trace.append("The children entered the tool shed and noticed the towel and a problem.")
    world.say(f"In the little {p.shed}, where the bright tools lay, {child.label} and {helper.label} came to work and play.")
    world.say(incident["opening"])
    world.say(f'"What is happening?" asked {child.label}. "{tool.label.capitalize()} needs care," said {helper.label}.')

    world.para()
    world.trace.append("The friends paused and searched for a clue instead of pulling at the tool.")
    world.say(incident["problem"])
    world.say(f'"Should we tug?" asked {child.label}. "Not so fast," said {helper.label}. "Let us look and ask."')
    world.say(f"They found {incident['clue']}.")

    world.para()
    child.memes["understanding"] = 1.0
    helper.memes["teamwork"] = 1.0
    world.trace.append("The clue explained the trouble, and the friends chose a safe repair.")
    world.say(incident["turn"])
    world.say(f'"Now we know," said {helper.label}. "{towel.label.capitalize()} can help us, too."')
    world.say(incident["fix"])

    world.para()
    towel.meters["dryness"] = 1.0
    tool.meters["safe"] = 1.0
    world.trace.append("The towel dried and the tool became safe to use.")
    world.say(f"Then {child.label} sang, \"Tap-tap, drip-drop, tidy the shop!\"")
    world.say(f"{helper.label} clapped the beat: \"Dry the {towel.label}, mind every tool, careful hands make a happy rule!\"")
    world.say(incident["ending"])


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a nursery-rhyme story with dialogue about a {p.towel} in a {p.shed}.",
        f"Tell a gentle rhyming story where {p.child} and {p.helper} solve a tool-shed problem using a towel.",
        "Make the characters speak, notice a clue, and end with a tidy rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who visited the {p.shed}?",
            answer=f"{p.child} and {p.helper} visited the {p.shed} together.",
        ),
        QAItem(
            question="What problem did they notice?",
            answer=incident["problem"],
        ),
        QAItem(
            question="What clue helped them understand the problem?",
            answer=f"They noticed {incident['clue']}.",
        ),
        QAItem(
            question="How did the towel help?",
            answer=f"They used the {p.towel} as part of the safe solution: {incident['fix']}",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The tool was safe, the {p.towel} was cared for, and {incident['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is a towel used for?",
            answer="A towel is used for drying water or keeping a surface from getting wet.",
        ),
        QAItem(
            question="Why should children ask before repairing a tool?",
            answer="Children should ask before repairing a tool so a grown-up can help them stay safe.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the spoken exchange of words between characters.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, playful poem or song with a memorable rhythm.",
        ),
        QAItem(
            question=f"What is a {p.shed}?",
            answer=f"A {p.shed} is a small place where garden tools and useful objects can be stored.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
character(child).
character(helper).
thing(towel).
thing(tool).
has_dialogue :- said(child).
has_dialogue :- said(helper).
has_clue :- clue(found).
has_solution :- repair(safe).
good_story :- has_dialogue, has_clue, has_solution.
#show good_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("character", "child"),
        asp.fact("character", "helper"),
        asp.fact("thing", "towel"),
        asp.fact("thing", "tool"),
        asp.fact("said", "child"),
        asp.fact("said", "helper"),
        asp.fact("clue", "found"),
        asp.fact("repair", "safe"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    asp_good = any(symbol.name == "good_story" for symbol in model)
    sample = generate(StoryParams(seed=0))
    python_good = (
        '"What is happening?"' in sample.story
        and '"Now we know,"' in sample.story
        and sample.world is not None
        and sample.world.entities["towel"].meters.get("dryness") == 1.0
    )
    if asp_good == python_good == True:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme tool-shed storyworld about a helpful towel."
    )
    parser.add_argument("--shed", choices=SHEDS)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--towel", choices=TOWELS)
    parser.add_argument("--tool", choices=TOOLS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([name for name in HELPERS if name != child])
    return StoryParams(
        shed=args.shed or rng.choice(SHEDS),
        child=child,
        helper=helper,
        towel=args.towel or rng.choice(TOWELS),
        tool=args.tool or rng.choice(TOOLS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            StoryParams("tool shed", "Luna", "Milo", "blue towel", "watering can", base_seed),
            StoryParams("garden shed", "Nina", "Finn", "striped towel", "small rake", base_seed + 1),
            StoryParams("little shed", "Pip", "Bess", "yellow towel", "wooden hammer", base_seed + 2),
            StoryParams("tool shed", "Tess", "Otis", "soft red towel", "green shovel", base_seed + 3),
        ]
        samples = [generate(params) for params in combinations]
    else:
        for index in range(args.n):
            sample_seed = base_seed + index
            rng = random.Random(sample_seed)
            params = resolve_params(args, rng, sample_seed)
            if params.child == params.helper:
                raise StoryError("the child and helper must have different names")
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
