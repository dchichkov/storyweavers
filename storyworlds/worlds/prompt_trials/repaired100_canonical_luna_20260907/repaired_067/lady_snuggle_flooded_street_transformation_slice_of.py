#!/usr/bin/env python3
"""
A small slice-of-life story world about Lady Snuggle and a flooded street.

A familiar errand changes when a puddled street becomes a place for noticing,
helping, and making a careful new plan.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
flooded_street(S) :- street(S), has_water(S).
careful(L) :- lady(L), notices(L, blocked_drain).
helper(L) :- lady(L), carries(L, umbrella).
transformation(S) :- flooded_street(S), drain_clear(S), people_cross(S).
kind_story(L,S) :- lady(L), transformation(S), helps(L,S).
safe_story(L,S) :- kind_story(L,S), speaks_up(L), no_child_falls(S).
"""


LADY_NAMES = ["Lady Snuggle", "Lady June", "Lady May", "Lady Rosa"]
FRIEND_NAMES = ["Mina", "Theo", "Pip", "Nora"]
STREET_NAMES = ["Maple Street", "Willow Street", "Cedar Street", "Sunny Street"]
OBJECTS = ["a basket of warm rolls", "a library book", "a yellow raincoat", "a paper bag of apples"]


@dataclass(frozen=True)
class Incident:
    title: str
    premise: str
    danger: str
    clue: str
    first_plan: str
    action: str
    result: str
    transformation: str
    joke: str
    ending: str


INCIDENTS = [
    Incident(
        title="the deep middle puddle",
        premise="Rain had filled Maple Street until the road looked like a long gray mirror.",
        danger="the deepest water hid a loose paving stone near the crossing",
        clue="small bubbles rose beside the storm drain",
        first_plan="step straight through and finish the errand quickly",
        action="put on her boots, found a long broom, and guided the floating leaves toward the drain",
        result="the water slipped away from the crossing and the loose stone became visible",
        transformation="the street changed from a risky shortcut into a clear path for neighbors",
        joke="That puddle was trying very hard to become a swimming pool",
        ending="By evening, the wet street reflected windows and careful footsteps instead of hiding stones.",
    ),
    Incident(
        title="the stranded stroller",
        premise="A family stood at the corner while rainwater curled around the wheels of a stroller.",
        danger="the stroller could tip if its front wheels dropped into a covered gutter",
        clue="a red ribbon on the gutter grate trembled under the water",
        first_plan="pull the stroller across the nearest part of the street",
        action="asked the family to wait, placed bright cones around the gutter, and found a dry route beside the bakery",
        result="the stroller rolled safely along the higher pavement",
        transformation="the flooded corner became a place where people shared directions and waited for one another",
        joke="The stroller wanted a walk, not a surprise boat ride",
        ending="The baby waved from the dry pavement while the cones stood like tiny orange guards.",
    ),
    Incident(
        title="the floating grocery bag",
        premise="A paper bag of apples drifted down the flooded street like a little red boat.",
        danger="a child might chase it into water deeper than it looked",
        clue="the bag spun toward a dark patch beside a parked van",
        first_plan="wade after the apples before they floated away",
        action="called to the child, used a broom to draw the bag toward the curb, and asked an adult to lift it",
        result="the apples were saved without anyone stepping into the hidden dip",
        transformation="a lost grocery bag became a small lesson in stopping, calling, and choosing safe tools",
        joke="The apples had planned a very soggy shopping trip",
        ending="The rescued apples sat in a dry basket while the street carried only rainwater.",
    ),
    Incident(
        title="the quiet storm drain",
        premise="Lady Snuggle noticed that one corner of the flooded street stayed higher than the rest.",
        danger="leaves and twigs had packed tightly over the drain",
        clue="water circled the grate but did not make its usual rushing sound",
        first_plan="ignore the corner and take the long way home",
        action="told the shopkeeper, wore thick gloves, and cleared only the leaves that were safe to lift",
        result="the drain began to gulp water again and the street slowly lowered",
        transformation="a gloomy puddle became a visible sign that neighbors could solve a small problem together",
        joke="The drain had been holding its breath all afternoon",
        ending="The last leaves floated away as neighbors watched a clean silver channel open beside the curb.",
    ),
    Incident(
        title="the borrowed umbrella",
        premise="Rain tapped on every umbrella while Lady Snuggle carried a borrowed blue one toward the bus stop.",
        danger="a gust could turn the umbrella inside out near the fast-moving water",
        clue="a loose handle strap slapped against the umbrella pole",
        first_plan="hold the umbrella tightly and hurry",
        action="stepped beneath the shop awning, tied the strap, and waited for the strongest gust to pass",
        result="the umbrella stayed whole and the borrowed item returned safely",
        transformation="the waiting place became a calm little shelter where strangers shared weather news",
        joke="The umbrella had almost become a flying blue pancake",
        ending="At the bus stop, the repaired umbrella dripped neatly into a row of patient puddles.",
    ),
]


OPENINGS = [
    "On an ordinary rainy afternoon, {title} began.",
    "Lady Snuggle expected a short walk, but {title} changed the afternoon.",
    "The rain had been falling since breakfast when {title} appeared.",
    "Nothing seemed unusual until Lady Snuggle reached {street} and saw {title}.",
    "The flooded street made a quiet mirror, and then {title} gave Lady Snuggle a reason to stop.",
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    street: str
    condition: str = "flooded street"


@dataclass
class World:
    setting: Setting
    lady: Character
    friend: Character
    object: str
    incident: Incident
    route: int
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    lady: str
    friend: str
    street: str
    object: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice-of-life transformation story on a flooded street.")
    parser.add_argument("--lady", choices=LADY_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--street", choices=STREET_NAMES)
    parser.add_argument("--object", choices=OBJECTS)
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
    lady = args.lady or rng.choice(LADY_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    street = args.street or rng.choice(STREET_NAMES)
    obj = args.object or rng.choice(OBJECTS)
    if lady == friend:
        raise StoryError("The lady and friend must have different names.")
    return StoryParams(lady=lady, friend=friend, street=street, object=obj)


def make_world(params: StoryParams) -> World:
    lady = Character(
        id=params.lady,
        role="lady",
        meters={"care": 0.8, "caution": 0.7, "helpfulness": 0.6},
        memes={"calm": 0.6, "kindness": 0.8},
    )
    friend = Character(
        id=params.friend,
        role="neighbor",
        meters={"attention": 0.5, "helpfulness": 0.5},
        memes={"trust": 0.5},
    )
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values() if False else [
        params.lady, params.friend, params.street, params.object
    ]))
    return World(
        setting=Setting(street=params.street),
        lady=lady,
        friend=friend,
        object=params.object,
        incident=INCIDENTS[key % len(INCIDENTS)],
        route=(key // len(INCIDENTS)) % len(OPENINGS),
    )


def tell(world: World) -> None:
    lady = world.lady
    friend = world.friend
    incident = world.incident
    street = world.setting.street

    opening = OPENINGS[world.route].format(title=incident.title, street=street)
    world.say(f"{opening} {incident.premise}")
    world.say(
        f"At {street}, {lady.id} held her coat close and noticed that {incident.danger}. "
        f"She did not want the ordinary errand to become a risky adventure."
    )
    world.para()

    world.say(
        f"For a moment, {lady.id} thought she might {incident.first_plan}. "
        f'"Wait," said {friend.id}. "What do you see near the water?"'
    )
    world.say(
        f'"I see this: {incident.clue}," {lady.id} replied. '
        f'"Then let us make a safer plan." Her words changed what they decided to do.'
    )
    world.para()

    world.say(f"Together, they {incident.action}. Soon, {incident.result}.")
    world.say(
        f"They kept the flooded street open for others and checked that no one followed the hidden water. "
        f"{friend.id} carried {world.object} while {lady.id} showed neighbors the safer way."
    )
    world.para()

    world.say(
        f'"{incident.joke}," said {lady.id}. {friend.id} laughed, but they still watched the water carefully.'
    )
    world.say(
        f"The afternoon had transformed: {incident.transformation}. "
        f"{incident.ending}"
    )

    world.facts.update(
        lady=lady,
        friend=friend,
        setting=world.setting,
        incident=incident,
        danger=incident.danger,
        clue=incident.clue,
        action=incident.action,
        result=incident.result,
        transformation=incident.transformation,
        ending=incident.ending,
    )


def generation_prompts(world: World) -> list[str]:
    incident = world.incident
    return [
        f"Write a child-friendly slice-of-life story about {world.lady.id} on a flooded street, where {incident.title} leads to a careful transformation.",
        f"Tell a story in which {world.lady.id} notices that {incident.danger}, listens to {world.friend.id}, and uses a safe plan.",
        f"Write a gentle transformation tale ending with this image: {incident.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.incident
    lady = world.lady
    friend = world.friend
    return [
        QAItem(
            question=f"What did {lady.id} notice on {world.setting.street}?",
            answer=f"{lady.id} noticed that {incident.danger}. The clue was that {incident.clue}.",
        ),
        QAItem(
            question=f"How did {friend.id}'s words change the plan?",
            answer=f"{friend.id} asked what {lady.id} could see, so they stopped rushing and made a safer plan together.",
        ),
        QAItem(
            question="What did the characters do to solve the problem?",
            answer=f"Together, they {incident.action}. As a result, {incident.result}.",
        ),
        QAItem(
            question="How did the flooded street transform?",
            answer=f"{incident.transformation}. The ending shows the change because {incident.ending}",
        ),
        QAItem(
            question="Why did Lady Snuggle avoid hurrying?",
            answer=f"She avoided hurrying because {incident.danger}. Looking at the clue first helped everyone choose a safer route.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flooded street?",
            answer="A flooded street is a road covered by more water than it can safely carry away, so people should watch for hidden holes, drains, and moving water.",
        ),
        QAItem(
            question="What does transformation mean in this story?",
            answer="Transformation means that something changes. Here, a worrying flooded street becomes a safer, more helpful place because people notice the problem and work together.",
        ),
        QAItem(
            question="Why is it useful to speak up when something looks unsafe?",
            answer="Speaking up lets other people know what you noticed, so everyone can pause and choose a safer action.",
        ),
    ]


def dump_trace(world: World) -> str:
    incident = world.incident
    return "\n".join(
        [
            "--- world model state ---",
            f"lady={world.lady.id} role={world.lady.role} meters={world.lady.meters} memes={world.lady.memes}",
            f"friend={world.friend.id} role={world.friend.role} meters={world.friend.meters} memes={world.friend.memes}",
            f"street={world.setting.street} condition={world.setting.condition}",
            f"object={world.object}",
            f"incident={incident.title}",
            f"danger={incident.danger}",
            f"clue={incident.clue}",
            f"action={incident.action}",
            f"result={incident.result}",
            f"transformation={incident.transformation}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("lady", "lady_snuggle"),
            asp.fact("street", "flooded_street"),
            asp.fact("has_water", "flooded_street"),
            asp.fact("notices", "lady_snuggle", "blocked_drain"),
            asp.fact("carries", "lady_snuggle", "umbrella"),
            asp.fact("drain_clear", "flooded_street"),
            asp.fact("people_cross", "flooded_street"),
            asp.fact("speaks_up", "lady_snuggle"),
            asp.fact("no_child_falls", "flooded_street"),
        ]
    )


def asp_program(show: str = "#show safe_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    expected = {("lady_snuggle", "flooded_street")}
    actual = set(asp.atoms(model, "safe_story"))
    if actual != expected:
        print(f"MISMATCH: ASP safe_story={actual}, expected={expected}")
        return 1

    for params in curated():
        sample = generate(params)
        if "transformed" not in sample.story and "transform" not in sample.story:
            print("MISMATCH: generated story lacks transformation.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story lacks QA.")
            return 1

    print("OK: ASP parity and generated-story checks verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams("Lady Snuggle", "Mina", "Maple Street", "a basket of warm rolls"),
        StoryParams("Lady June", "Theo", "Willow Street", "a library book"),
        StoryParams("Lady May", "Pip", "Cedar Street", "a yellow raincoat"),
        StoryParams("Lady Rosa", "Nora", "Sunny Street", "a paper bag of apples"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show careful/1.\n"
                "#show helper/1.\n"
                "#show transformation/1.\n"
                "#show kind_story/2.\n"
                "#show safe_story/2."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index if args.seed is not None else None
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
