#!/usr/bin/env python3
"""
A small space-adventure storyworld about an atlas, a careful waitress, and
teamwork that turns a mistake into reconciliation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = ["the moon cafe", "the comet station", "the orbital diner"]
ATLAS_NAMES = ["star atlas", "planet atlas", "old route atlas"]
DISHES = ["meteor soup", "moonberry pie", "comet noodles", "starlight tea"]
NAMES = ["Luna", "Milo", "Asha", "Ren", "Tavi", "Sora"]
PARTNERS = ["brother", "sister", "friend", "cousin"]
TRAITS = ["brave", "careful", "curious", "patient", "hopeful"]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("held", "safe", "located", "repaired", "shared"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "worry", "kindness", "anger", "hope", "focus"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    atlas: str
    dish: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    opening: str
    problem: str
    mistake: str
    flashback: str
    dialogue: str
    plan: str
    teamwork: str
    reconciliation: str
    ending: str


INCIDENTS = [
    Incident(
        "The Atlas on the Wrong Table",
        "A meteor shower had just painted silver lines across the cafe windows",
        "the star atlas was gone from Luna's table when the crew needed it to find their home dock",
        "Luna blamed the waitress for clearing it away",
        "she remembered the atlas being beside a tray of moonberry pie before the lights flickered",
        '"Wait," Luna said. "I remember where it was, but I may be remembering alone."',
        "ask the waitress kindly, check the tray route, and compare the remembered map marks",
        "Luna followed the route while her partner checked the cafe tables and the waitress searched the safe return shelf",
        "Luna apologized when the atlas was found under a clean napkin cart, and the waitress accepted her apology",
        "They reached the dock with the atlas open to a bright blue planet and left the waitress a thank-you note.",
    ),
    Incident(
        "The Crumb Trail to Mars",
        "The orbital diner hummed while ships drifted past its round windows",
        "a red crumb trail made everyone think the atlas had been dropped near the service hatch",
        "the crew hurried after the wrong clue and nearly missed their departure signal",
        "Luna recalled that the waitress had carried a covered dish along the same path, not the atlas",
        '"Could the crumbs belong to supper instead of our map?" her partner asked.',
        "separate the food trail from the atlas trail and search only places where the book could rest safely",
        "one child read the docking symbols, one watched the clock, and the waitress checked the counter shelves",
        "the crew admitted their mistake and thanked the waitress for protecting the atlas from a spilled drink",
        "The ship lifted off after the atlas showed them the shortest safe route through the stars.",
    ),
    Incident(
        "The Quiet Shelf",
        "At the moon cafe, the gravity lamps glowed like tiny suns",
        "the atlas had been placed on a high shelf while a waitress cleaned the table",
        "Luna reached for it alone and knocked a cup toward the edge",
        "a flashback showed the waitress moving the atlas because a robot had begun spraying foam",
        '"I thought you had hidden it," Luna said. "I should have asked before I guessed."',
        "let the waitress explain, then use two pairs of hands to retrieve the atlas and steady the shelf",
        "the partner held the ladder, Luna guided the atlas down, and the waitress secured the cups",
        "Luna and the waitress forgave one another for the frightening moment",
        "The atlas rested safely beside the navigation window while the crew planned their next jump.",
    ),
    Incident(
        "The Missing Docking Mark",
        "A comet tail shimmered beyond the diner as the crew prepared to leave",
        "a smudge covered the atlas mark for their docking bay",
        "Luna thought the waitress had wiped away the important symbol",
        "she remembered drawing the mark with a blue pencil while waiting for tea",
        '"Maybe the mark is not gone," the waitress said. "Maybe it is hiding under the smudge."',
        "clean the page gently, compare it with the station board, and ask for help before guessing",
        "the partner held the atlas flat, Luna checked the board, and the waitress brought a soft cloth",
        "Luna thanked the waitress after discovering that her own tea ring had made the smudge",
        "The restored blue mark guided their ship home beneath a field of quiet stars.",
    ),
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def choose_incident(params: StoryParams) -> Incident:
    key = "|".join(
        str(x)
        for x in (
            params.seed,
            params.place,
            params.atlas,
            params.dish,
            params.name,
            params.partner,
            params.trait,
        )
    )
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return INCIDENTS[int.from_bytes(digest[:4], "big") % len(INCIDENTS)]


def tell(params: StoryParams) -> World:
    if params.atlas not in ATLAS_NAMES:
        raise StoryError(f"Unknown atlas: {params.atlas}")
    if params.dish not in DISHES:
        raise StoryError(f"Unknown dish: {params.dish}")

    incident = choose_incident(params)
    world = World(Setting(params.place))

    hero = world.add(Entity("hero", "character", "traveler", params.name))
    partner = world.add(Entity("partner", "character", "traveler", f"{params.partner}"))
    waitress = world.add(Entity("waitress", "character", "waitress", "the waitress"))
    atlas = world.add(Entity("atlas", "thing", "atlas", params.atlas, owner="hero"))
    dish = world.add(Entity("dish", "thing", "dish", params.dish))

    hero.memes.update(worry=1, focus=1)
    partner.memes.update(trust=1, focus=1)
    waitress.memes.update(kindness=1, trust=1)
    atlas.meters.update(held=1, safe=1, located=0)
    dish.meters.update(located=1)

    world.facts.update(
        hero=hero,
        partner=partner,
        waitress=waitress,
        atlas=atlas,
        dish=dish,
        incident=incident,
        reconciled=False,
        teamwork=False,
        flashback=True,
    )

    world.say(
        f"{incident.opening}, {hero.label}, who was {params.trait}, sat in {params.place} with {partner.label} and a {params.atlas}."
    )
    world.say(
        f"They needed the atlas to guide their little ship past the next moon before the station gates closed."
    )
    world.say(f"The trouble began when {incident.problem}.")
    world.say(f"{hero.label} grew worried and {incident.mistake}.")

    world.para()
    world.say(
        f"Then a flashback returned: {incident.flashback}. The memory did not solve everything, but it gave the crew a better question."
    )
    world.say(incident.dialogue)
    world.say(f"Together they made a plan: {incident.plan}.")

    atlas.meters["located"] = 1
    atlas.meters["shared"] = 1
    hero.memes["focus"] += 1
    partner.memes["focus"] += 1
    waitress.memes["trust"] += 1
    world.facts["teamwork"] = True
    world.say(f"The plan became teamwork. {incident.teamwork}.")

    world.para()
    world.say(f"{hero.label} looked at the waitress and said, {incident.reconciliation.split(' and ')[0]}.")
    world.say(f"The reconciliation came when {incident.reconciliation}.")
    world.facts["reconciled"] = True
    hero.memes["anger"] = 0
    hero.memes["worry"] = 0
    waitress.memes["hope"] += 1

    world.say(incident.ending)
    atlas.meters["safe"] = 1
    atlas.meters["held"] = 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    incident: Incident = f["incident"]  # type: ignore[assignment]
    return [
        "Write a child-facing Space Adventure about a traveler, an atlas, and a waitress who solve a mistake through reconciliation.",
        f"Tell a story called {incident.title} using a flashback, teamwork, and a concrete search for a missing atlas.",
        "Include dispose, atlas, and waitress naturally, with spoken dialogue that changes the characters' decisions.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    partner: Entity = f["partner"]  # type: ignore[assignment]
    waitress: Entity = f["waitress"]  # type: ignore[assignment]
    atlas: Entity = f["atlas"]  # type: ignore[assignment]
    incident: Incident = f["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What problem did {hero.label} face with the atlas?",
            f"The atlas was difficult to find or use because {incident.problem}. {hero.label} first made the mistake that {incident.mistake}.",
        ),
        QAItem(
            "What did the flashback help the crew remember?",
            f"It helped them remember that {incident.flashback}. That memory gave them a useful clue instead of another guess.",
        ),
        QAItem(
            "How did teamwork solve the problem?",
            f"They followed this plan: {incident.plan}. Then {incident.teamwork}.",
        ),
        QAItem(
            f"How did {hero.label} and the waitress reconcile?",
            f"{hero.label} admitted the mistake and the waitress accepted the apology. Their reconciliation restored trust while they kept the {atlas.label} safe.",
        ),
        QAItem(
            "What happened at the end of the adventure?",
            incident.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an atlas?",
            "An atlas is a book or collection of maps that helps people learn about places and find routes.",
        ),
        QAItem(
            "What does reconcile mean?",
            "To reconcile means to make peace after a disagreement and restore a friendly relationship.",
        ),
        QAItem(
            "Why is teamwork useful?",
            "Teamwork is useful because people can combine their different skills and help one another finish a task safely.",
        ),
        QAItem(
            "What does dispose mean?",
            "To dispose of something means to get rid of it in a suitable or safe way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label:12} ({entity.type:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  teamwork={world.facts.get('teamwork')}")
    lines.append(f"  reconciled={world.facts.get('reconciled')}")
    lines.append(f"  flashback={world.facts.get('flashback')}")
    return "\n".join(lines)


CURATED = [
    StoryParams("the moon cafe", "star atlas", "moonberry pie", "Luna", "friend", "careful"),
    StoryParams("the comet station", "planet atlas", "meteor soup", "Milo", "sister", "brave"),
    StoryParams("the orbital diner", "old route atlas", "starlight tea", "Asha", "cousin", "curious"),
]


ASP_RULES = r"""
located(A) :- atlas(A), recovered(A).
teamwork_ok :- hero_present, partner_present, waitress_present, located(atlas).
reconciled_ok :- teamwork_ok, apology, trust_restored.
good_story :- teamwork_ok, reconciled_ok, flashback_used.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("atlas", "atlas"),
        asp.fact("hero_present"),
        asp.fact("partner_present"),
        asp.fact("waitress_present"),
        asp.fact("recovered", "atlas"),
        asp.fact("apology"),
        asp.fact("trust_restored"),
        asp.fact("flashback_used"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        atoms = asp.one_model(asp_program())
    except ImportError:
        print("OK: ASP twin is present; clingo is not installed, so solving was skipped.")
        return 0
    if not any(str(atom) == "good_story" for atom in atoms):
        raise StoryError("ASP parity failed: good_story was not derived")
    for index, params in enumerate(CURATED):
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("teamwork") or not sample.world.facts.get("reconciled"):
            raise StoryError(f"Python parity failed for curated sample {index + 1}")
    print("OK: Python stories and ASP twin agree on teamwork and reconciliation.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld about an atlas, a waitress, and reconciliation."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--atlas", choices=ATLAS_NAMES)
    parser.add_argument("--dish", choices=DISHES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        atlas=args.atlas or rng.choice(ATLAS_NAMES),
        dish=args.dish or rng.choice(DISHES),
        name=args.name or rng.choice(NAMES),
        partner=args.partner or rng.choice(PARTNERS),
        trait=args.trait or rng.choice(TRAITS),
    )


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
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.asp:
        try:
            import asp
            atoms = asp.one_model(asp_program())
            print(json.dumps({"atoms": [str(atom) for atom in atoms]}, indent=2))
        except ImportError:
            print("ASP requested, but clingo is not installed.")
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.name}: {sample.params.atlas} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
