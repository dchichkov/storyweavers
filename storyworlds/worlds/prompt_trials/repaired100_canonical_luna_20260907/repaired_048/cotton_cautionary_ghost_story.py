#!/usr/bin/env python3
"""
A gentle cautionary ghost story about cotton, a promise, and a little care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
class Setting:
    place: str
    floor: str
    weather: str


@dataclass
class StoryParams:
    place: str
    child: str
    ghost: str
    cotton_object: str
    warning: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    object_detail: str
    rule: str
    temptation: str
    warning_sign: str
    ghost_request: str
    danger: str
    careful_action: str
    lesson: str
    ending: str


TALES = [
    Tale(
        "a soft cotton quilt stitched with blue moons",
        "never leave a cotton candle cover near an open flame",
        "to drape the quilt over a chilly lantern",
        "the quilt's moons trembled although the windows were shut",
        "Please lift the cotton away before the little flame grows hungry",
        "a bright tongue of fire began licking the quilt's loose edge",
        "folded the quilt on a wooden chair and snuffed the lantern",
        "Soft things still need careful places.",
        "the blue moons rested safely while the ghost's glow faded into the dawn",
    ),
    Tale(
        "a cotton curtain that brushed the old stove",
        "keep cotton cloth well away from hot iron",
        "to hang the curtain closer so the moonlight would look silver",
        "a pale handprint appeared beside a darkening thread",
        "Please move the cotton before the heat turns a thread into a spark",
        "the curtain's hem began to smoke above the stove",
        "pulled the curtain onto its cool hook and called for help",
        "A pretty idea is not worth ignoring a warning.",
        "the curtain waved in the morning breeze, far from the quiet stove",
    ),
    Tale(
        "a basket packed with clean cotton balls",
        "do not scatter cotton near a breathing child",
        "to make a floating white path across the nursery floor",
        "the ghost's small cough echoed from beneath the basket",
        "Please keep the cotton together and let the air stay clear",
        "loose cotton began drifting toward the baby's open cradle",
        "swept the cotton into its basket and closed the nursery door",
        "Care can be gentle and still be firm.",
        "the cotton balls slept in their basket beneath a bright paper star",
    ),
    Tale(
        "a cotton bandage beside a dusty bottle",
        "use clean cotton only for a clean wound",
        "to wrap a scraped knee with an old bandage from the attic",
        "the ghost pointed toward a fresh roll on the shelf",
        "Please choose the clean cotton; kindness must also be careful",
        "dust shook from the old bandage onto the child's hands",
        "washed carefully and used a fresh cotton bandage",
        "Helping well means choosing safe materials.",
        "the unused old bandage rested in a sealed box while the fresh one stayed bright",
    ),
    Tale(
        "a cotton kite folded beside a candle",
        "store cotton toys away from candles",
        "to hold the kite close so its tail would glow",
        "the kite string pulled itself toward the dark window",
        "Please carry the cotton kite to the table before lighting anything",
        "the candle flame leaned toward the kite's thin tail",
        "blew out the candle and moved the kite to the windowsill",
        "A warning heard early can prevent a frightening accident.",
        "the cotton kite rose safely in the cool morning wind",
    ),
]

OPENINGS = [
    "On a moonlit evening,",
    "Near the end of a rainy day,",
    "When the old house had grown quiet,",
    "Just after the clock whispered midnight,",
    "On the first night of autumn,",
]

GHOST_LINES = [
    '"Do not be afraid," said the ghost. "Be careful instead."',
    '"I am not here to frighten you," whispered the ghost. "I am here to warn you."',
    '"Listen to the cotton," murmured the ghost. "It tells you when it is too near danger."',
    '"Will you help me keep this place safe?" asked the ghost.',
]

CONSEQUENCES = [
    "The child stopped, though the tempting plan seemed harmless.",
    "The child took one step back and looked at the cotton with new eyes.",
    "For a moment the room felt colder, but the child chose patience over hurry.",
    "The child remembered that a soft object could still cause a hard problem.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


PLACES = {
    "attic": Setting("the attic", "wooden", "rainy"),
    "cottage": Setting("the cottage", "stone", "windy"),
    "schoolhouse": Setting("the old schoolhouse", "dusty", "misty"),
    "lighthouse": Setting("the lighthouse", "spiral", "foggy"),
}

CHILDREN = ["Luna", "Mara", "Nell", "Toby", "Ivo", "Pia"]
GHOSTS = ["the Lantern Ghost", "the Cotton Ghost", "the Quiet Ghost", "the Window Ghost"]
COTTON_OBJECTS = [
    "cotton quilt",
    "cotton curtain",
    "cotton basket",
    "cotton bandage",
    "cotton kite",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values() if False else [
        params.place, params.child, params.ghost, params.cotton_object, params.warning
    ])))


def tell(world: World, params: StoryParams) -> None:
    rng = random.Random(stable_seed(params) ^ 0xC0770)
    tale = rng.choice(TALES)
    opening = rng.choice(OPENINGS)
    ghost_line = rng.choice(GHOST_LINES)
    consequence = rng.choice(CONSEQUENCES)

    child = world.add(Entity("child", "character", "child", params.child))
    ghost = world.add(Entity("ghost", "character", "ghost", params.ghost))
    cotton = world.add(Entity("cotton", "thing", "cotton", params.cotton_object))
    danger = world.add(Entity("danger", "thing", "hazard", "danger"))

    child.memes.update(curiosity=1, caution=0, relief=0)
    ghost.memes.update(worry=1, hope=1)
    cotton.meters.update(softness=1, distance_from_danger=0)
    danger.meters.update(heat=1, risk=1)

    world.say(f"{opening} {params.child} entered {world.setting.place}.")
    world.say(
        f"On a shelf lay {tale.object_detail}, and beside it was a note that said, "
        f'"{params.warning}."'
    )
    world.say(
        f"{params.child} knew the cotton felt soft and harmless, but the old house had rules for a reason."
    )

    world.para()
    world.say(
        f"Then {params.child} thought it would be lovely {tale.temptation}."
    )
    world.say(consequence)
    world.say(
        f"The room grew still, and {params.ghost} appeared beside the doorway."
    )
    world.say(ghost_line)
    world.say(
        f'"What could go wrong?" asked {params.child}. '
        f'"{tale.rule.capitalize()}," answered the ghost.'
    )

    child.memes["curiosity"] = 0
    child.memes["caution"] = 1
    ghost.memes["worry"] = 0
    world.fired.add("warning_given")

    world.para()
    world.say(
        f"At once, {tale.warning_sign}. That small clue showed that the warning was about more than old-fashioned fear."
    )
    world.say(
        f"The danger became clear: {tale.danger}."
    )
    world.say(
        f"{params.child} chose the safe action and {tale.careful_action}."
    )
    cotton.meters["distance_from_danger"] = 1
    danger.meters["risk"] = 0
    child.memes["relief"] = 1
    ghost.memes["hope"] = 0
    world.fired.add("danger_avoided")

    world.para()
    world.say(
        f"The ghost nodded. {tale.lesson}"
    )
    world.say(
        f"Before sunrise, {tale.ending}."
    )

    world.facts.update(
        child=child,
        ghost=ghost,
        cotton=cotton,
        danger=danger,
        tale=tale,
        place=world.setting.place,
        warning=params.warning,
    )


ASP_RULES = r"""
dangerous(C) :- cotton(C), near_danger(C), hazard_hot(H).
safe(C) :- cotton(C), moved_away(C), not dangerous(C).
warned(C) :- cotton(C), ghost_warns(C).
resolved(C) :- warned(C), safe(C).

#show dangerous/1.
#show safe/1.
#show warned/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("cotton", "cotton"),
        asp.fact("near_danger", "cotton"),
        asp.fact("hazard_hot", "flame"),
        asp.fact("ghost_warns", "cotton"),
        asp.fact("moved_away", "cotton"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary cotton ghost story.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--child")
    parser.add_argument("--ghost")
    parser.add_argument("--cotton-object", choices=COTTON_OBJECTS)
    parser.add_argument("--warning")
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
    place = args.place or rng.choice(list(PLACES))
    child = args.child or rng.choice(CHILDREN)
    ghost = args.ghost or rng.choice(GHOSTS)
    cotton_object = args.cotton_object or rng.choice(COTTON_OBJECTS)
    warning = args.warning or rng.choice([
        "Keep cotton away from flame",
        "Soft does not always mean safe",
        "Cotton belongs in a clean, cool place",
        "Listen before you lift",
    ])
    return StoryParams(place, child, ghost, cotton_object, warning)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle cautionary ghost story for a child that includes cotton.',
        f"Tell how {f['child'].label} learned to treat cotton carefully in {f['place']}.",
        f"Write a ghost story in which a warning about {f['tale'].rule} prevents danger.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    tale: Tale = f["tale"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {f['child'].label} find the cotton?",
            f"{f['child'].label} found {tale.object_detail} in {f['place']}.",
        ),
        QAItem(
            "Why did the ghost appear?",
            f"The ghost appeared to warn the child that {tale.rule}.",
        ),
        QAItem(
            "What danger did the child notice?",
            f"The child noticed that {tale.danger}.",
        ),
        QAItem(
            "What did the child do to solve the problem?",
            f"The child {tale.careful_action}.",
        ),
        QAItem(
            "What lesson did the ghost teach?",
            tale.lesson,
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is cotton?",
            "Cotton is a soft plant fiber used to make cloth, bandages, and other useful things.",
        ),
        QAItem(
            "Why should cotton be kept away from flames?",
            "Cotton can catch fire, so it should be kept in a cool place away from candles and stoves.",
        ),
        QAItem(
            "What is a cautionary story?",
            "A cautionary story gives a warning and shows how a careful choice can prevent trouble.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.child.strip():
        raise StoryError("The child name cannot be empty.")
    if not params.ghost.strip():
        raise StoryError("The ghost name cannot be empty.")
    world = World(PLACES[params.place])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show safe/1.\n#show warned/1.\n#show resolved/1.\n"
    ))
    safe = set(asp.atoms(model, "safe"))
    warned = set(asp.atoms(model, "warned"))
    resolved = set(asp.atoms(model, "resolved"))
    if safe == {("cotton",)} and warned == {("cotton",)} and resolved == {("cotton",)}:
        sample = generate(StoryParams(
            place="attic",
            child="Luna",
            ghost="the Cotton Ghost",
            cotton_object="cotton quilt",
            warning="Keep cotton away from flame",
            seed=7,
        ))
        if "cotton" in sample.story.lower() and sample.world and "danger_avoided" in sample.world.fired:
            print("OK: ASP/Python parity and generated story checks passed.")
            return 0
    print("MISMATCH: ASP/Python cautionary resolution differs.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dangerous/1.\n#show safe/1.\n#show warned/1.\n#show resolved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show dangerous/1.\n#show safe/1.\n#show warned/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("attic", "Luna", "the Cotton Ghost", "cotton quilt", "Keep cotton away from flame", base_seed),
            StoryParams("cottage", "Mara", "the Quiet Ghost", "cotton curtain", "Soft does not always mean safe", base_seed + 1),
            StoryParams("lighthouse", "Toby", "the Lantern Ghost", "cotton kite", "Listen before you lift", base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(0, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
