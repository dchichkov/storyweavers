#!/usr/bin/env python3
"""A gentle mountain ghost story about an avalanche, a certificate, and teamwork."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
for _parent in _HERE.parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Kit"
    curator: str = "Mara"
    ghost: str = "Ada"
    place: str = "the Ridge Museum"
    plan: str = "padded_tray"
    opening: int = 0
    ending: int = 0


CHILDREN = ["Kit", "Nell", "Robin", "June", "Theo"]
CURATORS = ["Mara", "Tomas", "Ivy", "Bea", "Oren"]
GHOSTS = ["Ada", "Elsie", "Ruth", "Mina", "Willa"]
PLACES = ["the Ridge Museum", "the Pass Museum", "the old Mountain Museum"]

PLANS = {
    "padded_tray": {
        "gear": "felt_padding",
        "shared_role": "steady_and_carry",
        "action": (
            "{curator} laid a felt-padded tray beside the frame. "
            "{child} steadied it while {curator} eased the certificate onto the soft cloth."
        ),
        "sound": "The frame made a soft shuff as it settled onto the felt.",
    },
    "two_person_carry": {
        "gear": "steady_hands",
        "shared_role": "carry_together",
        "action": (
            "{curator} took one side of the frame and {child} carefully held the other. "
            "Together they carried it along the dry inner wall."
        ),
        "sound": "Their careful steps went tap, tap, tap across the wooden floor.",
    },
    "rolling_cart": {
        "gear": "museum_cart",
        "shared_role": "guide_and_push",
        "action": (
            "{curator} set the frame on the museum's padded cart. "
            "{child} guided its wheels around the damp patch as {curator} pushed."
        ),
        "sound": "The cart wheels hummed softly over the boards.",
    },
}

OPENINGS = [
    "On a snowy evening, {child} was helping {curator} close {place}.",
    "At dusk, the last visitors left {place}, and {child} stayed to help {curator}.",
    "A blue winter twilight settled over {place} as {child} and {curator} tidied the gallery.",
    "The mountain wind hummed around {place}, where {child} was listening to {curator}'s stories.",
]

ENDINGS = [
    "By morning, the certificate hung safely in the map room, where its gold letters caught the first sun.",
    "When the storm quieted, the old certificate gleamed beside the map, dry and whole.",
    "The next morning, a pale blue glow rested on the certificate's glass, then faded as the room filled with sunlight.",
    "In the quiet map room, the framed certificate stood beside the trail map, ready to tell its story again.",
]


ASP_RULES = r"""
safe_plan(P) :-
    plan(P),
    gear(P),
    indoors,
    adult_leads,
    dry_room,
    ghost_warns,
    shared_role(P).

teamwork(P) :- safe_plan(P), ghost_guides.
#show safe_plan/1.
#show teamwork/1.
"""


def asp_facts() -> str:
    """Emit the small registry and safety facts used by the ASP twin."""
    import asp

    facts = [
        asp.fact("indoors"),
        asp.fact("adult_leads"),
        asp.fact("dry_room"),
        asp.fact("ghost_warns"),
        asp.fact("ghost_guides"),
    ]
    for plan, data in PLANS.items():
        facts.extend(
            [
                asp.fact("plan", plan),
                asp.fact("gear", data["gear"]),
                asp.fact("shared_role", plan),
            ]
        )
    return "\n".join(facts)


def asp_program(show: str = "#show safe_plan/1.\n#show teamwork/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_plans() -> set[tuple[str]]:
    """Python reasonableness gate: every plan must keep the team indoors and share the work."""
    indoors = True
    adult_leads = True
    dry_room = True
    ghost_warns = True
    ghost_guides = True
    if not all((indoors, adult_leads, dry_room, ghost_warns, ghost_guides)):
        return set()
    return {(plan,) for plan in PLANS if PLANS[plan]["shared_role"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about a mountain avalanche and a saved certificate."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--curator", choices=CURATORS)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--plan")
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
    plan = args.plan if args.plan is not None else rng.choice(list(PLANS))
    if plan not in PLANS:
        choices = ", ".join(PLANS)
        raise StoryError(f"Unknown moving plan {plan!r}; choose one of: {choices}.")
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(CHILDREN),
        curator=args.curator or rng.choice(CURATORS),
        ghost=args.ghost or rng.choice(GHOSTS),
        place=args.place or rng.choice(PLACES),
        plan=plan,
        opening=rng.randrange(len(OPENINGS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.plan not in PLANS:
        raise StoryError(
            f"Unknown moving plan {params.plan!r}; choose one of: {', '.join(PLANS)}."
        )
    if params.child == params.curator or params.child == params.ghost:
        raise StoryError("The child, curator, and ghost must have different names.")
    if params.curator == params.ghost:
        raise StoryError("The curator and ghost must have different names.")

    world = World()
    child = world.add(
        Entity(
            id=params.child,
            kind="character",
            type="child",
            label=params.child,
            meters={"distance_from_display": 2.0},
            memes={"curiosity": 0.8, "worry": 0.2, "confidence": 0.5},
        )
    )
    curator = world.add(
        Entity(
            id=params.curator,
            kind="character",
            type="curator",
            label=params.curator,
            meters={"distance_from_display": 2.0},
            memes={"care": 0.9, "worry": 0.3},
        )
    )
    ghost = world.add(
        Entity(
            id=params.ghost,
            kind="character",
            type="ghost",
            label=params.ghost,
            meters={"glow": 0.6},
            memes={"fondness": 0.9, "hope": 0.5},
        )
    )
    certificate = world.add(
        Entity(
            id="teamwork_certificate",
            kind="artifact",
            type="certificate",
            label="the old teamwork certificate",
            meters={"dampness": 0.0, "intact": 1.0, "distance_from_display": 0.0},
            memes={"importance": 1.0},
        )
    )
    avalanche = world.add(
        Entity(
            id="ridge_avalanche",
            kind="natural_event",
            type="avalanche",
            label="the avalanche on the ridge",
            meters={"distance_from_museum": 80.0, "noise": 0.8},
            memes={"danger": 0.8},
        )
    )

    world.say(
        OPENINGS[params.opening % len(OPENINGS)].format(
            child=child.label, curator=curator.label, place=params.place
        )
    )
    world.say(
        f"On the wall hung a certificate honoring {ghost.label} and the old ridge-watch team "
        "for helping travelers together."
    )
    world.say(
        f"Then a distant avalanche rumbled down the mountain. The museum shivered, and a thin "
        f"trickle began to bead on the certificate's glass."
    )
    certificate.meters["dampness"] = 0.35
    avalanche.meters["noise"] = 1.0
    child.memes["worry"] = 0.7
    curator.memes["worry"] = 0.7
    world.say(
        f"{ghost.label} appeared in a pale blue glow. Three quiet taps sounded from the inner map room."
    )
    world.say(
        f"'{ghost.label}, are you telling us to move the certificate away from this wall?' "
        f"{child.label} asked."
    )
    world.say(
        f"'Yes,' whispered {ghost.label}. 'The map room is dry, and the old north wall always drips after a slide.'"
    )
    world.say(
        f"'{child.label} can help me carry it safely,' said {curator.label}. "
        "'We will stay inside and work together.'"
    )
    world.say(
        PLANS[params.plan]["action"].format(child=child.label, curator=curator.label)
    )
    world.say(PLANS[params.plan]["sound"])
    certificate.meters["dampness"] = 0.05
    certificate.meters["distance_from_display"] = 6.0
    child.memes["worry"] = 0.2
    child.memes["confidence"] = 0.9
    curator.memes["worry"] = 0.2
    ghost.memes["hope"] = 1.0
    ghost.meters["glow"] = 0.3
    world.say(
        f"Just then, another drop darkened the empty spot where the frame had hung. "
        f"{child.label} and {curator.label} had moved it in time."
    )
    world.say(
        f"{ghost.label} smiled. 'That certificate was given for teamwork. You have honored it again.'"
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        child=child,
        curator=curator,
        ghost=ghost,
        certificate=certificate,
        avalanche=avalanche,
        plan=params.plan,
        plan_data=PLANS[params.plan],
        place=params.place,
        stayed_indoors=True,
        certificate_saved=True,
        ghost_warning=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a gentle ghost story about {facts['child'].label}, {facts['ghost'].label}, and a certificate saved after an avalanche.",
        f"Tell a child-friendly story where {facts['curator'].label} and a young helper listen to a ghost and protect an old teamwork certificate.",
        f"Write a complete mountain ghost story with a spoken exchange, a safe indoor rescue, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"].label
    curator = facts["curator"].label
    ghost = facts["ghost"].label
    plan = facts["plan_data"]
    return [
        QAItem(
            question="What caused the museum to shiver?",
            answer="A distant avalanche rumbled down the mountain, and its shaking made the museum shiver.",
        ),
        QAItem(
            question=f"How did {ghost} help save the certificate?",
            answer=(
                f"{ghost} appeared and tapped to point out that the inner map room was dry. "
                "The warning helped the others move the certificate before another drip fell."
            ),
        ),
        QAItem(
            question=f"How did {child} and {curator} work together?",
            answer=plan["action"].format(child=child, curator=curator),
        ),
        QAItem(
            question="Why was the certificate special to the ghost?",
            answer=(
                f"It honored {ghost} and the old ridge-watch team for helping travelers together, "
                "so saving it carried forward the teamwork it celebrated."
            ),
        ),
        QAItem(
            question="Where was the certificate safe at the end?",
            answer="The team moved it into the dry inner map room, where it could hang safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer=(
                "An avalanche is a large mass of snow that rushes down a mountain slope. "
                "People should stay away from avalanche paths and follow trained adults' safety advice."
            ),
        ),
        QAItem(
            question="What is a certificate?",
            answer="A certificate is a document that records an award, achievement, or other important recognition.",
        ),
        QAItem(
            question="Why can teamwork help during a difficult task?",
            answer=(
                "Teamwork lets people share jobs, listen to useful ideas, and help one another "
                "finish a task more safely."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions -- answerable from the story text =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions -- child level, no story needed =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> tuple[set[tuple], set[tuple]]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "safe_plan")), set(asp.atoms(model, "teamwork"))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_plans = set(asp.atoms(model, "safe_plan"))
    asp_teamwork = set(asp.atoms(model, "teamwork"))
    python_plans = python_valid_plans()
    python_teamwork = python_plans
    if asp_plans != python_plans or asp_teamwork != python_teamwork:
        print("MISMATCH between the ASP twin and the Python reasonableness gate.")
        print("  ASP safe plans:", sorted(asp_plans))
        print("  Python safe plans:", sorted(python_plans))
        print("  ASP teamwork plans:", sorted(asp_teamwork))
        return 1

    exercised = 0
    for plan in PLANS:
        for opening in range(len(OPENINGS)):
            params = StoryParams(
                child="Kit",
                curator="Mara",
                ghost="Ada",
                plan=plan,
                opening=opening,
                ending=opening % len(ENDINGS),
            )
            sample = generate(params)
            if not all(word in sample.story.lower() for word in ("avalanche", "certificate")):
                print(f"Generated story for {plan} omitted a required seed word.")
                return 1
            if sample.story.count("'") < 4 or not sample.world.facts["certificate_saved"]:
                print(f"Generated story for {plan} lacks dialogue or a resolved rescue.")
                return 1
            if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
                print(f"Generated story for {plan} lacks grounded questions.")
                return 1
            exercised += 1
    print(f"OK: ASP/Python parity matches; exercised {exercised} generated stories.")
    return 0


CURATED = [
    StoryParams(
        seed=101,
        child="Kit",
        curator="Mara",
        ghost="Ada",
        place="the Ridge Museum",
        plan="padded_tray",
        opening=0,
        ending=0,
    ),
    StoryParams(
        seed=202,
        child="Nell",
        curator="Tomas",
        ghost="Elsie",
        place="the Pass Museum",
        plan="two_person_carry",
        opening=2,
        ending=1,
    ),
    StoryParams(
        seed=303,
        child="Robin",
        curator="Ivy",
        ghost="Ruth",
        place="the old Mountain Museum",
        plan="rolling_cart",
        opening=3,
        ending=2,
    ),
]


def emit(
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
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
        safe_plans, teamwork_plans = asp_valid()
        print(f"{len(safe_plans)} ASP-approved certificate-moving plans")
        for plan in sorted(safe_plans):
            print(f"{plan[0]}: teamwork={plan in teamwork_plans}")
        return
    if args.n < 1 and not args.all:
        raise SystemExit("The number of stories (-n) must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child}: a certificate at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
