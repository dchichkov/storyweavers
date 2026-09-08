#!/usr/bin/env python3
"""
A child-friendly whodunit about a missing pecan, a wise admonition, and the
choice not to forsake a friend when clues point the wrong way.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Case:
    title: str
    opening: str
    false_clue: str
    flashback: str
    true_clue: str
    careful_action: str
    culprit: str
    resolution: str
    ending: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)

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


SETTING = Setting(
    place="the old pecan orchard beside the village school",
    affords={"shade", "picnic", "clues", "honest_questions"},
)

CASES = [
    Case(
        "the_blue_ribbon",
        "At the orchard picnic, the mayor's prize pecan vanished from a red cloth.",
        "A blue ribbon lay beneath the picnic bench, and blue ribbon was tied to Tessa's basket.",
        "Luna remembered seeing the ribbon blow from the school noticeboard before Tessa ever reached the orchard.",
        "A tiny crescent of red cloth was caught on a low branch beside the squirrel path.",
        "asked every witness to point out where they had stood, then followed the red thread instead of the blue ribbon",
        "a young squirrel that had dragged the pecan toward its nest",
        "The prize pecan was found under leaves near the oak fence, and Tessa was cleared.",
        "The children placed a spare basket near the trees, while the squirrel nibbled safely beyond the picnic cloth.",
        "A bright clue is not always the first true clue.",
    ),
    Case(
        "the_silver_shell",
        "The school baker set one perfect pecan beside the cooling pies, but it disappeared before judging.",
        "A silver shell fleck glittered on Milo's sleeve after he carried a tray outside.",
        "Luna recalled that Milo had brushed against the old shell wreath while fetching water, long before the pie was baked.",
        "Fresh flour dust led from the window to a loose board beneath the worktable.",
        "checked the time of each footprint and lifted the loose board with the baker's help",
        "the kitchen mouse, which had rolled the pecan through the flour",
        "The pecan was returned, and Milo apologized for being suspected.",
        "The baker left a small crumb dish by the wall for the mouse and a covered tray for every future contest.",
        "A clue matters only when it fits the whole story.",
    ),
    Case(
        "the_missing_crack",
        "During a nature lesson, the class's largest pecan vanished from a labeled tray.",
        "The tray's label was torn, and everyone knew Arlo had been mending labels with glue.",
        "Luna remembered Arlo had repaired the label at his desk before the tray was carried outdoors.",
        "The tray had been placed beneath a branch with a fresh squirrel scratch.",
        "measured the shadows to learn when the tray had been moved and asked the gardener to inspect the branch",
        "a squirrel hiding nuts for a rainy afternoon",
        "The class found the pecan in a hollow stump and restored Arlo's good name.",
        "The children made a seed shelf for birds and squirrels beside the lesson table.",
        "Do not forsake a friend because a clue looks convenient.",
    ),
    Case(
        "the_green_glove",
        "A green gardening glove covered the spot where the orchard's special pecan had rested.",
        "Nia owned green gloves and had been the last child near the tree.",
        "Luna remembered Nia lending one glove to the groundskeeper while she carried water with both hands.",
        "A pair of muddy paw prints curved from the tree toward the compost heap.",
        "compared the glove's clean palm with the muddy trail and searched the compost heap slowly",
        "the orchard cat, which had batted the pecan into a pile of leaves",
        "The pecan was found beside the compost screen, and Nia was thanked for her help.",
        "The class hung gloves on a peg so no one would mistake a tool for proof.",
        "Kind questions protect people while careful evidence finds the truth.",
    ),
]

NAMES = ["Luna", "Mara", "Tavi", "Niko", "Pia", "Jori"]
PARTNERS = ["Tessa", "Milo", "Arlo", "Nia"]
TRAITS = ["patient", "curious", "careful", "bright", "thoughtful"]
DIALOGUES = [
    "What did the clue touch, and when did it get there?",
    "May we ask what happened before we decide who is blamed?",
    "Could the clue belong to a story older than this morning?",
    "What would we see if we followed the trail instead of the rumor?",
]
REFLECTIONS = [
    "Luna's admonition was gentle: never forsake a friend for the sake of a quick answer.",
    "The old teacher's admonition returned to them: evidence should open a question, not close a heart.",
    "They remembered the orchard's quiet admonition: look twice before naming a culprit.",
]


@dataclass
class StoryParams:
    place: str
    name: str
    partner: str
    trait: str
    case: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a pecan whodunit with a Flashback clue."
    )
    parser.add_argument("--place", default="orchard", choices=["orchard"])
    parser.add_argument("--name")
    parser.add_argument("--partner")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--case", choices=[c.title for c in CASES])
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
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice([p for p in PARTNERS if p != name])
    trait = args.trait or rng.choice(TRAITS)
    case = args.case or rng.choice([c.title for c in CASES])
    return StoryParams(args.place, name, partner, trait, case, args.seed)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "orchard":
        raise StoryError("This case belongs in the pecan orchard.")
    if params.name == params.partner:
        raise StoryError("The detective and the witness must be different characters.")
    if params.case not in {c.title for c in CASES}:
        raise StoryError("That mystery is not in the casebook.")


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def change_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = meter(entity, key) + amount


def change_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = meme(entity, key) + amount


def tell(world: World, params: StoryParams) -> World:
    case = next(c for c in CASES if c.title == params.case)
    detective = world.add(Entity(params.name, "character", params.name))
    partner = world.add(Entity(params.partner, "character", params.partner))
    pecan = world.add(Entity("prize_pecan", "object", "the prize pecan", owner="school"))
    tree = world.add(Entity("pecan_tree", "place", "the old pecan tree"))

    change_meme(detective, "curiosity", 1)
    change_meme(detective, "worry", 1)
    change_meter(detective, "attention", 1)

    world.say(
        f"At the old pecan orchard beside the school, {params.name}, a {params.trait} young detective, "
        f"kept a notebook for small mysteries."
    )
    world.say(case.opening)
    world.say(
        f"{params.partner} looked worried. “Everyone will think I took it,” {params.partner} said. "
        f"{params.name} answered, “I will not forsake you for a rumor. We will follow the facts.”"
    )
    world.para()

    change_meme(partner, "worry", 1)
    world.say(f"The first clue was easy to notice: {case.false_clue}")
    world.say(
        f"{params.name} almost pointed at {params.partner}, but an old admonition came back from yesterday's lesson."
    )
    world.say(f"“{DIALOGUES[(len(params.name) + len(case.title)) % len(DIALOGUES)]}” {params.name} asked.")
    world.say(f"{params.partner} replied, “I remember something that may help.”")
    world.say(f"That answer changed the search from blame to memory: {case.flashback}")
    world.para()

    change_meter(detective, "questions", 1)
    change_meme(detective, "patience", 1)
    world.say(f"Together, the children examined the orchard. {case.true_clue}")
    world.say(f"{params.name} {case.careful_action}.")
    change_meter(detective, "evidence", 1)
    change_meme(partner, "trust", 1)
    world.say(f"The hidden truth was {case.culprit}. {case.resolution}")
    world.para()

    world.say(
        f"The teacher praised {params.name} for solving a whodunit without turning a friend into a suspect."
    )
    world.say(f"{case.lesson} {random.Random(len(case.title)).choice(REFLECTIONS)}")
    world.say(case.ending)

    world.facts.update(
        case=case,
        detective=detective,
        partner=partner,
        pecan=pecan,
        tree=tree,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(World(SETTING), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    return [
        f"Write a child-friendly whodunit about {detective.label} investigating a missing pecan.",
        f"Include a Flashback showing why the first clue is misleading: {case.flashback}",
        "Use the words pecan, admonition, and forsake in a gentle mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    partner: Entity = world.facts["partner"]
    return [
        QAItem(
            f"Who investigated the missing pecan?",
            f"{detective.label}, a {world.facts['detective'].memes and 'curious' or 'careful'} young detective, investigated the missing pecan.",
        ),
        QAItem(
            "Why did the first clue seem to blame the friend?",
            f"It seemed to blame {partner.label} because {case.false_clue}",
        ),
        QAItem(
            "What did the Flashback reveal?",
            f"The Flashback revealed that {case.flashback}",
        ),
        QAItem(
            "What evidence solved the mystery?",
            f"The true evidence was {case.true_clue} {detective.label} then {case.careful_action}.",
        ),
        QAItem(
            "Who took the pecan?",
            f"{case.culprit.capitalize()} took the pecan, not {partner.label}.",
        ),
        QAItem(
            "What did the children learn?",
            f"They learned that {case.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pecan?", "A pecan is an edible nut that grows inside the shell of a pecan tree's fruit."),
        QAItem("What is an admonition?", "An admonition is a gentle warning or piece of advice about what someone should do."),
        QAItem("What does forsake mean?", "To forsake someone means to abandon or turn away from that person."),
        QAItem("What is a Flashback?", "A Flashback is a storytelling moment that returns to an earlier event to reveal useful information."),
        QAItem("What is a whodunit?", "A whodunit is a mystery story in which someone investigates who caused a puzzling event."),
    ]


ASP_RULES = r"""
valid(orchard).
has_word(pecan).
has_word(admonition).
has_word(forsake).
feature(flashback).
style(whodunit).
reasonable :- valid(orchard), has_word(pecan), has_word(admonition),
               has_word(forsake), feature(flashback), style(whodunit).
#show reasonable/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("valid", "orchard"),
            asp.fact("has_word", "pecan"),
            asp.fact("has_word", "admonition"),
            asp.fact("has_word", "forsake"),
            asp.fact("feature", "flashback"),
            asp.fact("style", "whodunit"),
        ]
    )


def asp_program(show: str = "#show reasonable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    if models and asp.atoms(models[0], "reasonable"):
        print("OK: ASP reasonableness gate passed.")
        return 0
    print("MISMATCH: ASP reasonableness gate failed.")
    return 1


def format_qa(sample: StorySample) -> str:
    chunks = ["== Prompts =="]
    chunks.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    chunks.append("\n== Story QA ==")
    for item in sample.story_qa:
        chunks.extend([f"Q: {item.question}", f"A: {item.answer}"])
    chunks.append("\n== World QA ==")
    for item in sample.world_qa:
        chunks.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(chunks)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"setting: {world.setting.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: kind={entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("orchard", "Luna", "Tessa", "curious", "the_blue_ribbon"),
    StoryParams("orchard", "Mara", "Milo", "patient", "the_silver_shell"),
    StoryParams("orchard", "Niko", "Arlo", "careful", "the_missing_crack"),
    StoryParams("orchard", "Pia", "Nia", "thoughtful", "the_green_glove"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            raise SystemExit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                raise SystemExit("Generated-story verification failed.")
        print("OK: generated stories passed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
            header = f"### {sample.params.name}: {sample.params.case}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
