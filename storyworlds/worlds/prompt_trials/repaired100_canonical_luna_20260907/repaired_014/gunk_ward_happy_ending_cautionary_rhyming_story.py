#!/usr/bin/env python3
"""
A small rhyming storyworld about gunk, a careful ward, and a happy ending.
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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=lambda: {"inspect", "protect", "clean"})


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    place: int = 0
    gunk: int = 0
    ward: int = 0
    rhyme: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trouble:
    place: str
    object_name: str
    gunk_desc: str
    danger: str
    safe_method: str
    repair: str
    ending: str
    rhyme_pair: tuple[str, str]


TROUBLES = [
    Trouble(
        "the moonlit garden gate",
        "a brass birdbath",
        "a thick green blob beneath its rim",
        "the birdbath might wobble and splash the nesting birds",
        "wear gloves, use a wooden spoon, and ask an adult to help",
        "scrape the gunk into a covered pail and rinse the basin",
        "clean birds came dipping while the garden glimmered bright",
        ("gate", "wait"),
    ),
    Trouble(
        "the little school shed",
        "a red wagon",
        "sticky black gunk across one wheel",
        "the wheel could seize while someone pulled the wagon",
        "keep fingers away, block the wagon, and call the caretaker",
        "lift the wheel safely and brush it clean",
        "the wagon rolled smoothly beneath the afternoon sun",
        ("shed", "said"),
    ),
    Trouble(
        "the riverside park",
        "a wooden bench",
        "a shiny purple smear along one slat",
        "someone might sit on it and carry the mess home",
        "place a bright warning card nearby and fetch the park keeper",
        "cover the smear and replace the slat",
        "friends sat safely where the river sparkled blue",
        ("park", "mark"),
    ),
    Trouble(
        "the baker's back yard",
        "a small rain barrel",
        "a lumpy gray patch around its tap",
        "the water could become dirty for the thirsty plants",
        "close the tap, keep away from the patch, and tell the baker",
        "wash the barrel and fit a fresh clean tap",
        "the flowers drank clear drops and nodded in the breeze",
        ("yard", "guard"),
    ),
]

RHYME_LINES = [
    ("When gunk looks slick, do not touch it quick;", "step back, stay wise, and ask for advice."),
    ("If goo is near, be calm, not queer;", "a careful ward can keep trouble clear."),
    ("A sticky sight may seem small and light;", "but safe hands make the ending right."),
    ("Do not poke muck just for luck;", "call for a helper, and do not get stuck."),
]

CHILD_NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip"]
HELPER_NAMES = ["Ari", "Bea", "Tess", "Jun", "Mara"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def build_story(params: StoryParams) -> World:
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("Names must not be empty.")
    trouble = TROUBLES[params.place % len(TROUBLES)]
    rhyme = RHYME_LINES[params.rhyme % len(RHYME_LINES)]
    setting = Setting(trouble.place)
    world = World(setting)

    child = world.add(Entity("Child", "character", "child", params.child_name))
    helper = world.add(Entity("Helper", "character", "helper", params.helper_name))
    gunk = world.add(Entity("Gunk", "thing", "gunk", trouble.gunk_desc))
    ward = world.add(Entity("Ward", "thing", "warning", "the careful ward"))
    object_ent = world.add(Entity("Object", "thing", "object", trouble.object_name))

    world.facts.update(
        child=child,
        helper=helper,
        gunk=gunk,
        ward=ward,
        object=object_ent,
        trouble=trouble,
        rhyme=rhyme,
    )

    gunk.meters["thickness"] = 1.0
    gunk.memes["unsafe"] = 1.0
    child.memes["curiosity"] = 1.0

    world.say(
        f"In {setting.place}, {child.label} saw {trouble.gunk_desc} on {trouble.object_name}. "
        f"It looked small, but {trouble.danger}."
    )
    world.say(f"{child.label} leaned close and sang, \"{rhyme[0]}\"")
    world.say(f'"Should I poke it?" {child.label} asked. "{rhyme[1]}"')
    world.para()

    helper.memes["caution"] = 1.0
    world.say(
        f"{helper.label} stepped beside {child.label}. \"No poking, no yanking, and no licking. "
        f"We will make a ward first.\""
    )
    world.say(
        f"Together they placed {ward.label} near {trouble.object_name}, then moved back behind a safe line."
    )
    ward.meters["distance"] = 1.0
    ward.memes["protective"] = 1.0
    world.say(f'"The ward tells everyone to wait," said {helper.label}. "{trouble.safe_method.capitalize()}."')
    world.para()

    world.say(
        f"The warning worked. Nobody touched the gunk, and {child.label} noticed a useful clue: "
        f"{trouble.gunk_desc} was not part of {trouble.object_name} at all."
    )
    child.memes["patience"] = 1.0
    world.say(f'"Caution helped us learn first," {child.label} said. "{rhyme[0]}"')
    world.say(f'"Exactly," said {helper.label}. "{rhyme[1]}"')
    world.para()

    world.say(
        f"They called the proper helper, who {trouble.safe_method}. Then the helper could {trouble.repair}."
    )
    gunk.meters["thickness"] = 0.0
    gunk.memes["unsafe"] = 0.0
    object_ent.memes["safe"] = 1.0
    world.say(
        f"After the last sticky bit was gone, {child.label} and {helper.label} folded up the ward. "
        f"{trouble.ending.capitalize()}."
    )
    world.say(
        "The children learned a cautionary truth: a strange mess is a signal to pause, protect, and ask—not a puzzle to poke."
    )
    world.facts["lesson"] = (
        "When something strange may be unsafe, pause, make a clear warning, and ask a capable helper."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trouble = world.facts["trouble"]
    return [
        f"Write a rhyming cautionary story about gunk found on {trouble.object_name}.",
        "Include a careful ward, helpful dialogue, and a happy ending.",
        "Show why children should pause and ask before touching a strange mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trouble: Trouble = f["trouble"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What did {child.label} find?",
            f"{child.label} found {trouble.gunk_desc} on {trouble.object_name}.",
        ),
        QAItem(
            f"Why did {helper.label} make a ward?",
            f"{helper.label} made a ward so people would keep away while they found a safe way to handle the gunk. {trouble.danger.capitalize()}.",
        ),
        QAItem(
            "How did the children solve the problem?",
            f"They did not touch the strange mess. They placed a warning, stepped back, called the proper helper, and then the helper could {trouble.repair}.",
        ),
        QAItem(
            "What cautionary lesson did the story teach?",
            "A strange mess may be unsafe, so it is wiser to pause, protect the area, and ask a capable helper than to poke it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is gunk?", "Gunk is a thick, sticky, or dirty substance that may be hard to clean."),
        QAItem("What is a ward in this story?", "A ward is a warning or protective barrier that helps keep people away from danger."),
        QAItem("What does caution mean?", "Caution means slowing down and acting carefully when something might be unsafe."),
        QAItem("What makes an ending happy?", "A happy ending shows that the problem is safely resolved and people or places are better afterward."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "gunk"),
            asp.fact("topic", "ward"),
            asp.fact("feature", "happy_ending"),
            asp.fact("feature", "cautionary"),
            asp.fact("style", "rhyming_story"),
            asp.fact("action", "pause"),
            asp.fact("action", "ask_helper"),
        ]
    )


ASP_RULES = r"""
topic(gunk).
topic(ward).
feature(happy_ending).
feature(cautionary).
style(rhyming_story).
action(pause).
action(ask_helper).

safe_plan :- action(pause), action(ask_helper).
story_ok :- topic(gunk), topic(ward), feature(cautionary),
            feature(happy_ending), style(rhyming_story), safe_plan.
#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if any(symbol.name == "story_ok" for symbol in model):
        print("OK: ASP twin recognizes the gunk-and-ward story world.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming cautionary story about gunk and a ward.")
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
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
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        place=rng.randrange(len(TROUBLES)),
        gunk=rng.randrange(4),
        ward=rng.randrange(4),
        rhyme=rng.randrange(len(RHYME_LINES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, trouble in enumerate(TROUBLES):
            params = StoryParams(
                child_name="Luna",
                helper_name="Ari",
                place=i,
                gunk=i,
                ward=i,
                rhyme=i % len(RHYME_LINES),
                seed=seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(max(0, args.n)):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
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
