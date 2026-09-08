#!/usr/bin/env python3
"""
A small mystery storyworld about Graham, an arc of colored stones, and curiosity.
Graham discovers that a missing arc-piece has been moved, asks careful questions,
and follows clues until the whole arc is restored.
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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affordances: frozenset[str]


@dataclass(frozen=True)
class Mystery:
    id: str
    clue: str
    hiding_place: str
    cause: str
    method: str
    result: str
    answer: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


SETTINGS = {
    "courtyard": Setting(
        "courtyard",
        "the old school courtyard",
        frozenset({"observe", "search", "ask"}),
    ),
    "greenhouse": Setting(
        "greenhouse",
        "the glass greenhouse",
        frozenset({"observe", "search", "ask"}),
    ),
    "museum": Setting(
        "museum",
        "the little town museum",
        frozenset({"observe", "search", "ask"}),
    ),
}

MYSTERIES = {
    "blue_stone": Mystery(
        "blue_stone",
        "one blue stone was missing from the painted arc",
        "beneath a fern beside the rain barrel",
        "a gust of wind had pushed the loose stone away",
        "Graham followed a thin blue scrape across the dusty path",
        "the missing stone clicked back into its empty place",
        "The blue stone had blown beneath a fern beside the rain barrel.",
    ),
    "silver_mark": Mystery(
        "silver_mark",
        "a silver mark appeared where the arc should have ended",
        "behind a wooden sign near the gate",
        "a visitor had moved the final stone to steady the sign",
        "Graham compared the dust under the sign with the clean patch in the arc",
        "the stone returned and the sign stood firmly on its post",
        "A visitor had moved the final stone to steady the gate sign.",
    ),
    "green_leaf": Mystery(
        "green_leaf",
        "a green stone had vanished before the morning tour",
        "inside a basket of fallen leaves",
        "a gardener had swept it up without noticing its painted color",
        "Graham noticed a bright green edge among the leaves",
        "the stone was washed and placed safely in the arc",
        "The gardener had swept the green stone into a leaf basket.",
    ),
    "red_shadow": Mystery(
        "red_shadow",
        "the red stone seemed to disappear at sunset",
        "under a long bench",
        "the low sun made the stone's shadow look like an empty space",
        "Graham moved the lantern and watched the shadow change",
        "the red stone shone beneath the bench",
        "The red stone was still under the bench, hidden by a long shadow.",
    ),
}

NAMES = ["Graham", "Luna", "Mira", "Theo", "Nell"]
HELPERS = ["Luna", "Mara", "Mr. Bell", "Aunt Jo"]
TRAITS = ["patient", "bright", "careful", "cheerful", "quiet"]
OPENINGS = [
    "{name} liked mysteries, especially small ones that other people hurried past.",
    "At {place}, {name} studied an arc of painted stones whenever the morning light arrived.",
    "{name} carried a little notebook, not because every mystery was huge, but because every clue mattered.",
    "The arc at {place} curved like a rainbow resting on the ground, and {name} visited it after breakfast.",
]
TURNS = [
    "{name} did not guess. He knelt down and looked closely at the dust.",
    '"Let us ask what changed," {name} said. "A clue is more useful than a guess."',
    "Curiosity made {name} slow down, compare the marks, and listen before choosing a path.",
    "{helper} pointed one way, but {name} noticed that the tiny trail went another way.",
]
ENDINGS = [
    "When the arc was whole again, {helper} smiled. The mystery had become a lesson: curiosity grows stronger when it is patient.",
    "The stones gleamed in a complete curve. {name} closed his notebook, happy that careful questions had solved what rushing could not.",
    "By afternoon, visitors admired the restored arc. {name} kept one dusty clue in his notebook and left the rest of the mystery at peace.",
    "The last stone settled with a soft click. {name} and {helper} stood back as the arc caught the light like a quiet answer.",
]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    graham: str = "Graham"
    helper: str = "Luna"
    trait: str = "curious"
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


ASP_RULES = r"""
valid_setting(S) :- setting(S), affords(S, observe), affords(S, search), affords(S, ask).
valid_mystery(M) :- mystery(M), has_clue(M), has_method(M).
valid_story(S, M) :- valid_setting(S), valid_mystery(M), setting_mystery(S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, affordance))
        for mid in MYSTERIES:
            lines.append(asp.fact("setting_mystery", sid, mid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_clue", mid))
        lines.append(asp.fact("has_method", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, mid) for sid in SETTINGS for mid in MYSTERIES]


def asp_valid() -> set[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return set(asp.atoms(model, "valid_story"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about Graham, an arc, and curiosity."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--graham", default=None)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [pair for pair in combos if pair[0] == args.setting]
    if args.mystery:
        combos = [pair for pair in combos if pair[1] == args.mystery]
    if not combos:
        raise StoryError("No setting and mystery combination is available.")

    setting, mystery = rng.choice(combos)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        graham=args.graham or "Graham",
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(len(OPENINGS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if not params.graham.strip():
        raise StoryError("Graham's name cannot be empty.")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    graham = world.add(
        Entity(
            "graham",
            "child",
            params.graham,
            meters={"distance": 0.0, "clues": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "helper",
            params.helper,
            meters={"distance": 0.0},
            memes={"trust": 1.0, "relief": 0.0},
        )
    )
    arc = world.add(
        Entity(
            "arc",
            "object",
            "the painted arc",
            meters={"missing_pieces": 1.0},
            memes={"mystery": 1.0},
        )
    )

    values = {
        "name": graham.label,
        "helper": helper.label,
        "place": setting.place,
        "trait": params.trait,
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(f"That morning, {mystery.clue}.")
    world.para()

    world.say(
        f'{helper.label} looked at the empty place. "{graham.label}, perhaps someone simply forgot it," '
        "the helper said."
    )
    world.say(
        f'"Perhaps," said {graham.label}. "But I am curious. What can the marks on the ground tell us?"'
    )
    graham.memes["curiosity"] += 1.0
    graham.meters["clues"] += 1.0
    world.say(mystery.cause.capitalize() + ".")
    world.para()

    world.say(TURNS[params.turn % len(TURNS)].format(**values))
    world.say(
        f'{helper.label} asked, "What did you find?" '
        f'{graham.label} answered, "{mystery.method}."'
    )
    graham.meters["distance"] += 1.0
    graham.meters["clues"] += 2.0
    graham.memes["worry"] = 0.0
    graham.memes["pride"] += 1.0
    arc.meters["missing_pieces"] = 0.0
    arc.memes["mystery"] = 0.0
    helper.memes["relief"] += 1.0

    world.say(f"Together, they solved the mystery: {mystery.result}.")
    world.para()

    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))
    world.facts.update(graham=graham, helper=helper, arc=arc, mystery=mystery)
    return world


def prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        f"Write a child-friendly mystery about Graham investigating {mystery.clue}.",
        f"Tell a curious story in which Graham follows clues and discovers that {mystery.answer.lower()}",
        "Write a gentle mystery about an arc, careful questions, and a surprising but safe answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    graham = world.facts["graham"]
    helper = world.facts["helper"]
    arc = world.facts["arc"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            "What was unusual about the arc?",
            f"The arc was missing one piece: {mystery.clue}.",
        ),
        QAItem(
            f"Why did {graham.label} keep investigating?",
            f"{graham.label} kept investigating because curiosity made him look for clues instead of guessing.",
        ),
        QAItem(
            f"How did {graham.label} and {helper.label} solve the mystery?",
            f"They solved it when {graham.label} followed the physical clue and discovered that {mystery.answer.lower()}",
        ),
        QAItem(
            "What changed at the end?",
            "The missing stone was returned, so the painted arc became complete again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an arc?",
            "An arc is a curved part of a line or shape.",
        ),
        QAItem(
            "What is curiosity?",
            "Curiosity is a wish to learn or find out more about something.",
        ),
        QAItem(
            "Why are clues useful in a mystery?",
            "Clues are useful because they give information that helps people explain what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = asp_valid()
    if python_pairs != asp_pairs:
        print("Mismatch between ASP and Python.")
        print("Only Python:", sorted(python_pairs - asp_pairs))
        print("Only ASP:", sorted(asp_pairs - python_pairs))
        return 1

    for params in [
        StoryParams("courtyard", "blue_stone"),
        StoryParams("greenhouse", "green_leaf", helper="Mara"),
        StoryParams("museum", "red_shadow", opening=2, turn=1, ending=3),
    ]:
        sample = generate(params)
        if not sample.story or "Graham" not in sample.story:
            print("Generated story verification failed.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("QA verification failed.")
            return 1

    print(f"OK: ASP and Python agree on {len(python_pairs)} valid combinations.")
    print("OK: generated stories and QA passed.")
    return 0


CURATED = [
    StoryParams("courtyard", "blue_stone", opening=0, turn=1, ending=0),
    StoryParams("greenhouse", "green_leaf", helper="Mara", opening=1, turn=2, ending=1),
    StoryParams("museum", "silver_mark", helper="Mr. Bell", opening=2, turn=0, ending=2),
    StoryParams("courtyard", "red_shadow", helper="Aunt Jo", opening=3, turn=1, ending=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show valid_story/2."))
        return

    if args.verify:
        raise SystemExit(verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
