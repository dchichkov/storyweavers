#!/usr/bin/env python3
"""A gentle myth about nurture, repetition, and a memory that returns."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Being:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Grove:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Myth:
    sign: str
    cause: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    grove_name: str = "the Moonwell Grove"
    keeper_name: str = "Luna"
    keeper_kind: str = "fox"
    elder_name: str = "Oren"
    elder_kind: str = "tortoise"
    sign: str = "a silver seed that would not wake"
    cause: str = "the seed remembered winter and needed patient warmth"
    case: str = "silver_seed"
    route: str = "old_song"


@dataclass(frozen=True)
class MythCase:
    wonder: str
    danger: str
    first_action: str
    first_result: str
    memory: str
    truth: str
    repeated_words: str
    brave_action: str
    nurture_action: str
    lesson: str
    ending: str


@dataclass
class World:
    grove: Grove
    keeper: Being
    elder: Being
    myth: Myth
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


GROVES = {
    "the Moonwell Grove": Grove("the Moonwell Grove", "enchanted grove"),
    "the Dawnroot Grove": Grove("the Dawnroot Grove", "enchanted grove"),
    "the Star-Apple Grove": Grove("the Star-Apple Grove", "enchanted grove"),
}

KEEPERS = [
    ("Luna", "fox"),
    ("Mira", "hare"),
    ("Sela", "wren"),
]

ELDERS = [
    ("Oren", "tortoise"),
    ("Nima", "deer"),
    ("Tavi", "raven"),
]

CASES = {
    "silver_seed": MythCase(
        "the silver seed would not wake",
        "the grove might lose its spring song",
        "placed the seed beneath clear moonlight",
        "the shell stayed cold because light alone could not reach its sleeping heart",
        "an old winter when the river froze around the roots",
        "the seed had carried a memory of winter and needed steady warmth before it could open",
        "Warmth, water, patience. Warmth, water, patience.",
        "admitted that the seed's silence frightened her and asked Oren what the old memory meant",
        "wrapped the seed in moss, gave it three drops of water each dawn, and sang the same small song",
        "nurture is not one grand gift but a faithful welcome repeated until life feels safe",
        "a silver sprout lifted beside the moonwell and returned a green note to the grove",
    ),
    "blue_feather": MythCase(
        "a blue feather could not rise",
        "the sky messenger might never find its way home",
        "tied the feather to a young branch",
        "it fell because a branch can hold a feather but cannot teach it the wind",
        "a storm long ago that had scattered the sky messengers",
        "the feather needed a sheltered place to dry before the returning breeze could carry it",
        "Shelter, stillness, listening. Shelter, stillness, listening.",
        "stopped trying to force the feather upward and asked the elder about the storm",
        "made a reed cradle, shaded it from rain, and checked it after every sunrise",
        "care means making room for recovery instead of demanding a quick return",
        "the feather rose on a warm breeze and circled once above the listening grove",
    ),
    "sleeping_stone": MythCase(
        "the little singing stone had gone quiet",
        "the grove's protective song might fade",
        "struck the stone three times with a willow twig",
        "the notes were harsh because the stone was buried under dry dust",
        "a drought remembered by the oldest roots",
        "the stone needed damp earth and gentle hands before its voice could return",
        "Soften the earth, moisten the root, wait for the note. Soften the earth, moisten the root, wait for the note.",
        "told the truth about her impatience and let Oren show her the careful way",
        "brushed away the dust, pressed wet clay around the stone, and returned at noon and dusk",
        "repetition can turn a hurried hand into a listening hand",
        "the stone sang one clear note that rested over the grove like a bell",
    ),
    "lost_glowworm": MythCase(
        "a glowworm's light had vanished",
        "the small creature might be lost in the dark reeds",
        "carried a bright lantern through the reeds",
        "the lantern frightened the glowworm farther into the shadows",
        "a night when too much brightness had hidden the stars",
        "the glowworm needed a quiet path marked by soft, low lights",
        "Dim the lantern, call softly, follow the small answer. Dim the lantern, call softly, follow the small answer.",
        "put away the large lantern and confessed that helping had become another kind of noise",
        "placed tiny shells along the safe path and returned without chasing",
        "nurture listens to the size of another creature's fear",
        "the glowworm shone beside the last shell, a small star choosing its own way home",
    ),
}

SIGNS = [
    ("a silver seed that would not wake", "the seed remembered winter and needed patient warmth", "silver_seed"),
    ("a blue feather that could not rise", "the feather needed shelter before the breeze could carry it", "blue_feather"),
    ("a singing stone that had gone quiet", "the stone needed damp earth and gentle hands", "sleeping_stone"),
    ("a glowworm whose light had vanished", "the glowworm needed a quiet path home", "lost_glowworm"),
]

ROUTES = ("old_song", "first_sign", "moon_memory", "question", "refrain")

ASP_RULES = r"""
nurtures(keeper) :- keeper(keeper), repeats_care(keeper), remembers(keeper).
awakens(myth) :- myth(myth), receives_care(myth), safe(myth).
valid_story :- nurtures(keeper), awakens(myth).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("keeper", "keeper"),
        asp.fact("repeats_care", "keeper"),
        asp.fact("remembers", "keeper"),
        asp.fact("receives_care", "myth"),
        asp.fact("safe", "myth"),
        asp.fact("myth", "myth"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show nurtures/1.\n#show awakens/1.\n#show valid_story/0."))
    nurtures = set(asp.atoms(model, "nurtures"))
    awakens = set(asp.atoms(model, "awakens"))
    valid = set(asp.atoms(model, "valid_story"))
    if nurtures == {("keeper",)} and awakens == {("myth",)} and valid == {()}:
        print("OK: clingo gate matches Python nurture reasoning.")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("clingo:", model)
    return 1


def story_rng(params: StoryParams) -> random.Random:
    values = (
        params.seed, params.grove_name, params.keeper_name, params.keeper_kind,
        params.elder_name, params.elder_kind, params.case, params.route,
    )
    return random.Random("|".join(map(str, values)).__hash__() & 0xFFFFFFFF)


def build_world(params: StoryParams) -> World:
    if params.grove_name not in GROVES:
        raise StoryError(f"Unknown grove: {params.grove_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown myth case: {params.case}")
    template = GROVES[params.grove_name]
    return World(
        grove=Grove(template.name, template.kind),
        keeper=Being(params.keeper_name, params.keeper_kind, "young keeper"),
        elder=Being(params.elder_name, params.elder_kind, "elder guide"),
        myth=Myth(params.sign, params.cause),
    )


def tell_story(world: World, params: StoryParams) -> None:
    keeper, elder, grove, myth = world.keeper, world.elder, world.grove, world.myth
    case = CASES[params.case]
    rng = story_rng(params)

    keeper.memes.update(care=0.0, courage=0.0, patience=0.0)
    elder.memes.update(wisdom=1.0, kindness=1.0)

    openings = {
        "old_song": (
            f"Before the first birds called, {keeper.name} heard the old song beneath {grove.name}. "
            f"It told of {myth.sign}, a wonder that had stopped before its work was done."
        ),
        "first_sign": (
            f"{myth.sign.capitalize()} appeared beside the path in {grove.name}. "
            f"{keeper.name} the {keeper.kind} knelt near it, wondering whether {case.danger}."
        ),
        "moon_memory": (
            f"Long ago, the moon had taught the creatures of {grove.name} that every quiet thing "
            f"might be carrying a story. One morning, {keeper.name} found {myth.sign}."
        ),
        "question": (
            f'"Why will you not answer?" {keeper.name} asked {myth.sign}, which rested quietly in {grove.name}. '
            f"The question rose like a small bell through the trees."
        ),
        "refrain": (
            f"{case.repeated_words} {keeper.name} did not yet know what the words meant, "
            f"but the old refrain led the young {keeper.kind} to {myth.sign}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice([
            f"The wonder mattered because {case.danger}.",
            f"The grove grew still, for {case.danger}.",
            f"Even the leaves seemed to listen because {case.danger}.",
        ])
    )
    world.say(
        f'"Do not command a sleeping thing to become ready," {elder.name} said. '
        f'"Tell me what it remembers."'
    )

    world.para()
    world.say(f"First, {keeper.name} {case.first_action}.")
    world.say(f"But {case.first_result}. The easy answer slipped away like mist.")
    world.say(
        f"Then a flashback came to {keeper.name}: {case.memory}. "
        f"For one breath, the present grove wore the colors of that older time."
    )
    world.say(
        f'"I remember now," {keeper.name} said. '
        f'"The silence is not refusal. It is a memory asking for care."'
    )
    world.say(f"{elder.name} nodded. " f'"Then repeat the care until the fear grows smaller."')

    world.para()
    world.say(f"{case.repeated_words}")
    world.say(
        f"{keeper.name} {case.brave_action}. "
        f"The young keeper's courage became larger when it was shared aloud."
    )
    keeper.memes["courage"] = 1.0
    keeper.memes["patience"] = 1.0
    keeper.memes["care"] = 1.0
    keeper.meters["care_cycles"] = 3.0

    world.say(
        f"At dawn, {keeper.name} {case.nurture_action}. "
        f"The same small kindness returned at noon and again when the stars appeared."
    )
    world.say(
        f"{case.repeated_words} Each time, the world changed by only a little, "
        f"but little changes can gather like rain."
    )
    myth.solved = True
    grove.meters["life_restored"] = 1.0
    world.facts.update(
        keeper=keeper,
        elder=elder,
        grove=grove,
        myth=myth,
        case=case,
        truth=case.truth,
        lesson=case.lesson,
        ending=case.ending,
        repetition=case.repeated_words,
        flashback=case.memory,
        solved=True,
    )

    world.para()
    world.say(
        rng.choice([
            f'"What did the old memory teach us?" {elder.name} asked.',
            f"{elder.name} looked toward the waking wonder and asked, "
            f'"What did your repeated care discover?"',
        ])
    )
    world.say(f"{keeper.name} answered, f'"{case.lesson.capitalize()}."')
    world.say(f"At last, {case.ending.capitalize()}.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f"Write a child-facing myth about {f['keeper'].name} nurturing {f['myth'].sign} in {f['grove'].name}.",
        f"Use repetition and a brief flashback to reveal that {case.truth}.",
        f"End with this changed image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    keeper = f["keeper"]
    elder = f["elder"]
    myth = f["myth"]
    return [
        QAItem(
            question=f"What wonder did {keeper.name} find in {f['grove'].name}?",
            answer=f"{keeper.name} found {myth.sign}. It mattered because {case.danger}.",
        ),
        QAItem(
            question=f"What did the flashback help {keeper.name} understand?",
            answer=f"The flashback recalled {case.memory}. It helped {keeper.name} understand that {case.truth}.",
        ),
        QAItem(
            question=f"What words did {keeper.name} repeat while caring for the wonder?",
            answer=f"{keeper.name} repeated, “{case.repeated_words}” The refrain helped turn care into a steady practice.",
        ),
        QAItem(
            question=f"How did {keeper.name} nurture the wonder?",
            answer=f"{keeper.name} {case.nurture_action}. The same kindness was repeated at several times of day.",
        ),
        QAItem(
            question=f"What lesson did {keeper.name} learn from {elder.name}?",
            answer=f"{keeper.name} learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does nurture mean?",
            answer="To nurture means to care for living things patiently so they can grow, heal, or feel safe.",
        ),
        QAItem(
            question="Why can repetition help someone learn?",
            answer="Repetition gives a person or creature more chances to remember a useful pattern and practice it calmly.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story when a character remembers an earlier event that helps explain the present.",
        ),
        QAItem(
            question="Why should care be repeated?",
            answer="Needs often change slowly, so steady care can show that a place or person is safe enough to grow.",
        ),
        QAItem(
            question="What makes this story a myth?",
            answer="It uses an old-sounding wonder, a talking natural world, and a lesson that explains how kindness works.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nurture myth using repetition and flashback."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--grove", choices=sorted(GROVES))
    parser.add_argument("--keeper-name")
    parser.add_argument("--elder-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    grove_name = args.grove or rng.choice(sorted(GROVES))
    keeper_name, keeper_kind = rng.choice(KEEPERS)
    elder_name, elder_kind = rng.choice(ELDERS)
    sign, cause, case = rng.choice(SIGNS)
    return StoryParams(
        seed=args.seed,
        grove_name=grove_name,
        keeper_name=args.keeper_name or keeper_name,
        keeper_kind=keeper_kind,
        elder_name=args.elder_name or elder_name,
        elder_kind=elder_kind,
        sign=sign,
        cause=cause,
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for being in (world.keeper, world.elder):
        lines.append(
            f"{being.name}: meters={being.meters} memes={being.memes}"
        )
    lines.append(
        f"{world.grove.name}: meters={world.grove.meters}"
    )
    lines.append(
        f"myth: sign={world.myth.sign!r} cause={world.myth.cause!r} "
        f"solved={world.myth.solved}"
    )
    lines.append(f"repetition: {world.facts.get('repetition')!r}")
    lines.append(f"flashback: {world.facts.get('flashback')!r}")
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
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show nurtures/1.\n#show awakens/1.\n#show valid_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show nurtures/1.\n#show awakens/1.\n#show valid_story/0.")
        )
        print(sorted(
            set(asp.atoms(model, "nurtures"))
            | set(asp.atoms(model, "awakens"))
            | set(asp.atoms(model, "valid_story"))
        ))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []

    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
