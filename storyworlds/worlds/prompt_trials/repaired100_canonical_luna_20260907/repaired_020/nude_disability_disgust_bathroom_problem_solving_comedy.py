#!/usr/bin/env python3
"""
A gentle bathroom problem-solving comedy about dignity, access, and a stubborn
soap bubble. Nudity is treated as ordinary privacy, disability as a practical
access need, and disgust as a temporary obstacle rather than a joke about a
person.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str = "the accessible bathroom"
    privacy: float = 1.0
    floor_dry: bool = False
    drain_clear: bool = False


@dataclass
class StoryParams:
    bathroom: str = "accessible"
    hero: str = "Luna"
    helper: str = "Pip"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


ARCS = [
    {
        "mess": "a heroic wobble of shampoo foam",
        "problem": "the drain was clogged with a whisker of hair and a shiny bath bead",
        "tool": "a rubber suction cup",
        "fix": "Luna pressed the suction cup down, lifted slowly, and caught the clog in a small tray",
        "line1": '"The foam is staging a takeover," Luna said.',
        "line2": '"Then we negotiate with the drain," Pip replied.',
        "ending": "the last bubble popped beside the clean drain",
    },
    {
        "mess": "a suspicious puddle shaped like a moustache",
        "problem": "the floor was slick because a loose bottle cap had let soap drip beneath the sink",
        "tool": "a long-handled sponge",
        "fix": "Luna used the sponge from her seated position while Pip tightened the cap and placed the bottle in a basket",
        "line1": '"That puddle has excellent comic timing," Luna said.',
        "line2": '"Good. We will give it a dry ending," Pip said.',
        "ending": "the moustache puddle vanished under three careful sponge swipes",
    },
    {
        "mess": "a mountain of bath bubbles leaning toward the door",
        "problem": "the bath mat had folded over the wheelchair's turning space",
        "tool": "two bright floor markers",
        "fix": "Luna asked Pip to move the mat, then marked a clear turning path with the bright markers",
        "line1": '"The mat has become a tiny mountain range," Luna said.',
        "line2": '"And every mountain needs a safe route around it," Pip answered.',
        "ending": "the turning path stayed wide while the bubbles settled into harmless hills",
    },
    {
        "mess": "a greenish blob trembling under the toilet brush",
        "problem": "a forgotten cleaning tablet had dissolved into a startlingly smelly puddle",
        "tool": "gloves, a scoop, and a sealed waste bag",
        "fix": "Pip put on gloves, Luna held the bag open, and together they scooped the puddle without touching it",
        "line1": '"That smell has entered the room before us," Luna said.',
        "line2": '"We can still be the ones who leave first," Pip said.',
        "ending": "the sealed bag waited outside while fresh air returned",
    },
    {
        "mess": "a towel turban sliding down the mirror",
        "problem": "the grab bar had been hidden behind a hanging robe",
        "tool": "a low wall hook",
        "fix": "Luna moved the robe to the low hook and checked that the grab bar was easy to reach",
        "line1": '"The robe is pretending to be architecture," Luna said.',
        "line2": '"Architecture should not surprise people who need a handhold," Pip replied.',
        "ending": "the grab bar shone clearly beside the neatly hung robe",
    },
]

DETAILS = [
    "a rubber duck wearing a paper crown",
    "a purple towel with yellow stars",
    "a tiny basket of lavender soap",
    "a clock shaped like a smiling fish",
    "a blue cup full of toothbrushes",
]


def validate(params: StoryParams) -> None:
    if params.bathroom != "accessible":
        raise StoryError("This story requires the accessible bathroom setting.")
    if params.hero == params.helper:
        raise StoryError("Luna and Pip must be different characters.")


def tell_story(params: StoryParams) -> World:
    validate(params)
    seed = params.seed or 0
    arc = ARCS[seed % len(ARCS)]
    detail = DETAILS[(seed // len(ARCS)) % len(DETAILS)]
    world = World(Place())
    luna = world.add(Entity("luna", "character", "wheelchair_user", params.hero))
    pip = world.add(Entity("pip", "character", "helper", params.helper))
    luna.meters.update({"mobility": 0.7, "reach": 0.5})
    luna.memes.update({"confidence": 1.0, "disgust": 0.0})
    pip.meters.update({"reach": 1.0, "lifting": 1.0})
    pip.memes.update({"patience": 1.0})

    world.say(
        f"{luna.label} rolled into {world.place.name} after a private bath, comfortably nude and wrapped in a towel "
        f"until the room was ready. Beside the sink sat {detail}."
    )
    world.say(
        f"Then {arc['mess']} blocked the easy route to the grab bar. Luna's nose wrinkled with disgust, "
        f"but she did not panic."
    )
    world.facts["problem_seen"] = True
    world.facts["cause"] = arc["problem"]
    world.place.floor_dry = False
    world.para()
    world.say(
        f'"I can reach the controls, but not that mess from this angle," {luna.label} said. '
        f'"Let us solve the bathroom instead of blaming the bathroom."'
    )
    world.say(f'"I will bring the right tool and listen to your directions," {pip.label} answered.')
    world.facts["dialogue_changed_plan"] = True
    world.say(f"They discovered that {arc['problem']}. {arc['line1']} {arc['line2']}")
    world.facts["tool"] = arc["tool"]
    world.say(f"Pip brought {arc['tool']}. {arc['fix']}.")
    world.facts["problem_solved"] = True
    world.place.drain_clear = True
    world.place.floor_dry = True
    luna.memes["disgust"] = 0.0
    luna.memes["relief"] = 1.0
    pip.memes["pride"] = 1.0
    world.para()
    world.say(
        f"Together they added one simple rule: keep the turning space clear, put tools where Luna could reach them, "
        f"and ask before moving anything near her chair. Being nude had never been the problem; being unable to move "
        f"safely through the room had been."
    )
    world.say(
        f"At last, {arc['ending']}. Luna gave the rubber duck a solemn nod, and Pip bowed to the clean floor."
    )
    world.facts.update(
        hero=luna,
        helper=pip,
        mess=arc["mess"],
        cause=arc["problem"],
        tool=arc["tool"],
        ending=arc["ending"],
        arc=seed % len(ARCS),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly bathroom comedy about a nude adult handling privacy with dignity.",
        f"Tell a problem-solving story where {f['hero'].label}'s disability leads the characters to improve access.",
        f"Use gentle comedy to resolve a disgusting bathroom problem caused by {f['cause']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Why was {hero.label} in the bathroom?",
            answer=f"{hero.label} had finished a private bath and was getting ready safely in the accessible bathroom.",
        ),
        QAItem(
            question=f"What made the bathroom unpleasant?",
            answer=f"The unpleasant problem was {f['mess']}; specifically, {f['cause']}.",
        ),
        QAItem(
            question=f"How did {hero.label}'s disability affect the solution?",
            answer=f"{hero.label} explained which parts were reachable from the wheelchair and helped choose a safe method instead of being moved without permission.",
        ),
        QAItem(
            question=f"What did {helper.label} do?",
            answer=f"{helper.label} brought {f['tool']} and followed {hero.label}'s directions while they solved the problem together.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The problem was solved, the floor and route were safer, and the ending image was that {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can an accessible bathroom help a wheelchair user?",
            answer="It can provide turning space, reachable fixtures, grab bars, and a safer path across the room.",
        ),
        QAItem(
            question="What is a respectful way to help someone with a disability?",
            answer="Ask what help they want, listen to their instructions, and do not move their body or equipment without permission.",
        ),
        QAItem(
            question="Why should a bathroom floor be kept dry?",
            answer="A dry floor reduces slipping and makes movement safer for everyone.",
        ),
    ]


ASP_RULES = r"""
problem_seen.
accessible_space.
asked_before_help.
tool_available.
problem_solved :- problem_seen, accessible_space, asked_before_help, tool_available.
safe_bathroom :- problem_solved.
#show safe_bathroom/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("problem_seen"),
            asp.fact("accessible_space"),
            asp.fact("asked_before_help"),
            asp.fact("tool_available"),
        ]
    )


def asp_program(show: str = "#show safe_bathroom/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "safe_bathroom"))


def asp_verify() -> int:
    if asp_outcome() != [()]:
        print("MISMATCH: ASP did not derive safe_bathroom.")
        return 1
    sample = generate(StoryParams(seed=7))
    required = ["nude", "disability", "disgust"]
    missing = [word for word in required if word not in sample.story.lower()]
    if missing:
        print(f"MISMATCH: story is missing {missing}")
        return 1
    if "bathroom" not in sample.story.lower() or not sample.world.facts["problem_solved"]:
        print("MISMATCH: generated story did not complete the bathroom problem.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


HEROES = ["Luna", "Mina", "Nora", "Tess"]
HELPERS = ["Pip", "Jo", "Remy", "Ari"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accessible bathroom problem-solving comedy.")
    parser.add_argument("--bathroom", choices=["accessible"])
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    choices = [name for name in HELPERS if name != hero]
    helper = args.helper or rng.choice(choices)
    return StoryParams(
        bathroom=args.bathroom or "accessible",
        hero=hero,
        helper=helper,
        seed=args.seed,
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
    lines.append(f"  place: {world.place.name}")
    lines.append(
        f"  floor_dry={world.place.floor_dry} drain_clear={world.place.drain_clear} "
        f"privacy={world.place.privacy}"
    )
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(ARCS)):
            samples.append(
                generate(
                    StoryParams(
                        bathroom="accessible",
                        hero="Luna",
                        helper="Pip",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
