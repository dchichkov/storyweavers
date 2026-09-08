#!/usr/bin/env python3
"""
A tiny Storyweavers world about an anxious tummy, a magical rhyme, and a
flashback that helps a child derive courage from an earlier brave moment.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id.replace("_", " ")


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass(frozen=True)
class Arc:
    key: str
    object_name: str
    challenge: str
    action: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    flashback: tuple[str, str]
    magic: tuple[str, str]
    ending: tuple[str, str]


ARCS = (
    Arc(
        "moon_kite",
        "moon-bright kite",
        "the kite was tangled in the tallest cloud tower",
        "Luna remembered a small knot she had untied before and followed the rhyme step by step",
        "the kite sailed free and painted a silver loop across the sky",
        (
            "In the hilltop meadow, Luna carried a moon-bright kite so tall it brushed the clouds.",
            "She meant to fly it past the birds, past the windmills, and nearly past the moon.",
        ),
        (
            "But the string twisted into a cloud tower. Luna's gut gave a nervous flip.",
            '"I feel anxious," she said. "What if I cannot bring it down?"',
        ),
        (
            "Then came a flashback: last spring, a tiny red bow had tangled in her wagon wheel.",
            "She had breathed slowly, found the crossing loop, and freed it with careful fingers.",
        ),
        (
            'Luna whispered, "Loop by loop, slow and true; brave old me knows what to do."',
            "The rhyme shimmered like magic. It turned her remembered courage into a bright blue thread.",
        ),
        (
            "Luna followed the thread, loosened the cloud knot, and derived a plan from her old success.",
            "The kite swooped free, and even the tallest cloud bowed as Luna laughed beneath it.",
        ),
    ),
    Arc(
        "giant_teacup",
        "giant teacup",
        "the teacup's handle had wedged beneath a stone arch",
        "Luna remembered how she had shifted a stuck garden gate and used the same gentle rocking motion",
        "the teacup rolled into the village picnic without spilling a drop",
        (
            "At the valley picnic, Luna found a giant teacup big enough for a baker to nap inside.",
            "She pushed it toward the tables, where a hundred sandwiches waited in neat rows.",
        ),
        (
            "The cup met a stone arch and stopped. Her gut rumbled like a distant drum.",
            '"I am anxious," Luna told Pip. "This cup is wider than our house!"',
        ),
        (
            "A flashback filled her mind: she had once freed a stuck garden gate by rocking it softly.",
            "She had not shoved wildly. She had watched, listened, and tried one small movement at a time.",
        ),
        (
            'She sang, "Rock it light, rock it right; little steps can move a might."',
            "Magic sparks skipped from the rhyme, and the stone arch seemed to point toward the best angle.",
        ),
        (
            "Luna derived a plan from the old gate trick, rocked the cup, and guided it around the arch.",
            "The picnic cheered as the enormous teacup arrived, still full enough for everyone to share.",
        ),
    ),
    Arc(
        "thunder_boot",
        "thunder-sized boot",
        "the boot had trapped the village bell rope",
        "Luna remembered how she had untangled a ribbon from a tree and copied its patient turns",
        "the bell rang so loudly that birds flew in a perfect circle above the town",
        (
            "By the village tower lay a thunder-sized boot, large enough to house a family of goats.",
            "Luna planned to carry it to the parade so the marching giant could wear it proudly.",
        ),
        (
            "Its lace had caught the bell rope. Luna's gut clenched, and the tower gave a nervous clang.",
            '"I am anxious," she said. "If I pull, the bell may shout forever."',
        ),
        (
            "A flashback showed Luna freeing a ribbon that had twisted high in an apple tree.",
            "She had remembered to hold the ribbon's loose end before she unwound the high loops.",
        ),
        (
            'Luna chanted, "Hold the end, unwind the bend; patient hands can help a friend."',
            "Magic warmed the rhyme, and golden arrows appeared wherever the lace should turn.",
        ),
        (
            "Luna derived the old lesson, held the rope, and unwound the boot lace without a yank.",
            "The bell rang once, the giant got his boot, and the whole town danced around the tower.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "girl"
    helper_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "cloud_meadow": Place("cloud_meadow", "the hilltop meadow", {"outdoors", "high"}),
    "giant_valley": Place("giant_valley", "the giant valley", {"outdoors", "picnic"}),
    "bell_town": Place("bell_town", "the village tower square", {"town", "tower"}),
}

NAMES = {
    "girl": ["Luna", "Mara", "Nell", "Pia"],
    "boy": ["Pip", "Theo", "Ollie", "Finn"],
}

CURATED = [
    StoryParams("cloud_meadow", "Luna", "Pip"),
    StoryParams("giant_valley", "Mara", "Theo"),
    StoryParams("bell_town", "Nell", "Finn"),
]


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name, "hero"))
    helper = world.add(Entity(params.helper_name, "character", params.helper_gender, params.helper_name, "helper"))
    arc = ARCS[random.Random(params.seed if params.seed is not None else 0).randrange(len(ARCS))]
    object_entity = world.add(Entity("challenge_object", "thing", "object", arc.object_name))
    tummy = world.add(Entity("gut", "body", "gut", "Luna's gut"))

    values = {"place": place.label, "hero": hero.phrase, "helper": helper.phrase}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    hero.memes["anxious"] += 1
    tummy.meters["tightness"] = 1
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["remembering"] += 1
    hero.meters["flashback"] = 1
    for line in arc.flashback:
        world.say(line.format(**values))
    world.para()

    hero.memes["magic"] += 1
    helper.memes["encouraging"] += 1
    for line in arc.magic:
        world.say(line.format(**values))
    world.para()

    hero.memes["anxious"] = 0
    hero.memes["brave"] += 1
    tummy.meters["tightness"] = 0
    object_entity.meters["free"] = 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        helper=helper,
        gut=tummy,
        object=object_entity,
        arc=arc,
        challenge=arc.challenge,
        action=arc.action,
        result=arc.result,
        place=place,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall tale of gut feelings, magic, rhyme, and remembered courage.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-gender", choices=["girl", "boy"], default="girl")
    parser.add_argument("--helper-gender", choices=["girl", "boy"], default="boy")
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
    hero_gender = args.hero_gender or "girl"
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES[hero_gender])
    choices = [name for name in NAMES[helper_gender] if name != hero]
    helper = args.helper or rng.choice(choices)
    return StoryParams(place, hero, helper, hero_gender, helper_gender, args.seed)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Hero and helper names must not be empty.")
    if params.hero_name == params.helper_name:
        raise StoryError("Hero and helper must have different names.")
    world = tell(params)
    f = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly tall tale using the words gut, anxious, and derive.",
            f"Tell how {f['hero'].phrase} used a flashback and a magic rhyme to solve a problem.",
            "Show an anxious feeling changing into courage through a remembered action.",
        ],
        story_qa=[
            QAItem(
                "Why did the hero feel anxious?",
                f"{f['hero'].phrase} felt anxious because {f['challenge']}. The tight feeling in the gut warned that a careless move could make the problem worse.",
            ),
            QAItem(
                "How did the flashback help?",
                f"The flashback reminded {f['hero'].phrase} of an earlier success. From that memory, the hero derived this useful action: {f['action']}.",
            ),
            QAItem(
                "What proved that the plan worked?",
                f"The ending proved it: {f['result']}. The object was free, and the hero's anxious gut became calm.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a flashback?",
                "A flashback is a return to an earlier moment in a story or memory. It can reveal a lesson that helps with a present problem.",
            ),
            QAItem(
                "What does derive mean?",
                "To derive something means to get an idea, plan, or result from a source such as a memory, clue, or observation.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
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


ASP_RULES = r"""
anxious(hero) :- gut(g), tight(g).
remembered(hero) :- flashback(hero).
magic_rhyme(hero) :- remembered(hero), rhyme(hero).
brave(hero) :- magic_rhyme(hero), derives_plan(hero).
solved(object) :- brave(hero), challenge(object).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("gut", "gut"),
            asp.fact("tight", "gut"),
            asp.fact("flashback", "hero"),
            asp.fact("rhyme", "hero"),
            asp.fact("derives_plan", "hero"),
            asp.fact("challenge", "object"),
        ]
    )


def asp_program(show: str = "#show brave/1.\n#show solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "brave") + asp.atoms(model, "solved"))


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "brave") or not asp.atoms(model, "solved"):
            print("ASP parity failed.")
            return 1
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip() or sample.world.facts["gut"].meters["tightness"] != 0:
            print("Generation verification failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        print(asp_valid_combos())
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            current = argparse.Namespace(**vars(args))
            current.seed = seed + index
            params = resolve_params(current, random.Random(seed + index))
            params.seed = seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
