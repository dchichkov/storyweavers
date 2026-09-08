#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about pampering, slumber, dialogue, and
reconciliation.

Luna wants to pamper a sleepy moon-bunny with a grand bedtime plan, but her
noisy kindness keeps the bunny awake. A gentle conversation reveals the
mistake, and the friends repair it with quiet care.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Rhyme:
    id: str
    place: str
    child_need: str
    first_plan: str
    noisy_result: str
    clue: str
    friend_line: str
    quiet_repair: str
    lesson: str
    ending: str
    rhyme: str


@dataclass
class World:
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


RHYMES = [
    Rhyme(
        "silver_pillow",
        "the moonlit nursery",
        "a soft pillow and a quiet song",
        "fluffed three pillows, rang a tiny bell, and sang a merry welcome",
        "the little moon-bunny blinked and could not slumber",
        "one long yawn hiding beneath the bell's bright ring",
        "I love your care, Luna, but pampering me means making the room quiet",
        "she lowered the bell, smoothed one pillow, and hummed only one tiny line",
        "kind care listens to what a tired friend needs",
        "the bunny slept beneath a silver quilt while Luna guarded the hush",
        "Hush-a-bye, moonlight; sleep softly tonight.",
    ),
    Rhyme(
        "velvet_blanket",
        "the cloud-top nursery",
        "a warm blanket and a peaceful nest",
        "wrapped the bunny in velvet, sprinkled star dust, and danced around the bed",
        "the blanket slipped loose and the bunny's ears stayed wide awake",
        "a small paw pressing firmly over one ear",
        "A warm blanket helps, dear Luna, but the dancing feet are too loud for slumber",
        "she stopped dancing, tucked the corners, and spoke in a whisper",
        "reconciliation begins when a loving helper accepts a true answer",
        "the bunny curled in the blanket, and two quiet shadows rested by the bed",
        "Soft as a cloud, warm as a feather, sleep joins two friends together.",
    ),
    Rhyme(
        "lavender_lullaby",
        "the garden of stars",
        "a lavender sachet and a slow lullaby",
        "tossed flower petals high and played a bright tune on a silver flute",
        "the stars wobbled while the bunny watched instead of dreaming",
        "the bunny's sleepy eyes following every flying petal",
        "The flowers smell sweet, but I need stillness before I can slumber",
        "she placed the sachet beside the nest and let the last flute note fade",
        "a dialogue can turn a proud plan into gentle help",
        "the bunny drifted off as lavender rested beside the moon-white nest",
        "Petal low, music slow; now to slumber we both go.",
    ),
    Rhyme(
        "candle_warmth",
        "the little lantern room",
        "a warm glow and a calm good-night",
        "lit four candles, clapped a rhythm, and told a grand bedtime tale",
        "the bright room made the bunny squint and hide beneath the quilt",
        "the quilt trembling whenever Luna clapped",
        "Your warm light is kind, but fewer flames and softer words will help me rest",
        "she blew out three candles, dimmed the last, and finished the tale in a whisper",
        "reconciliation makes room for both the giver's love and the sleeper's need",
        "one small candle glowed while the bunny slept peacefully beside it",
        "Little flame, gentle gleam; peace can cradle every dream.",
    ),
]


GIRL_NAMES = ["Luna", "Mira", "Nell", "Poppy"]
BOY_NAMES = ["Bram", "Milo", "Toby", "Ollie"]
TRAITS = ["eager", "tender", "cheerful", "thoughtful"]


@dataclass
class StoryParams:
    place: str = "nursery"
    activity: str = "pamper"
    name: str = "Luna"
    friend_name: str = "Bram"
    trait: str = "tender"
    seed: Optional[int] = None


def reasonable(params: StoryParams) -> bool:
    return params.place == "nursery" and params.activity == "pamper" and params.name != params.friend_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme storyworld about pampering and slumber.")
    parser.add_argument("--place", choices=["nursery"])
    parser.add_argument("--activity", choices=["pamper"])
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(GIRL_NAMES)
    friend_name = args.friend_name or rng.choice(BOY_NAMES)
    if name == friend_name:
        raise StoryError("The caring child and the moon-bunny must have different names.")
    return StoryParams(
        place=args.place or "nursery",
        activity=args.activity or "pamper",
        name=name,
        friend_name=friend_name,
        trait=args.trait or rng.choice(TRAITS),
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    if not reasonable(params):
        raise StoryError("This world needs a nursery, a pampering activity, and two different friends.")

    world = World()
    luna = world.add(Entity(params.name, "character", "girl"))
    bunny = world.add(Entity(params.friend_name, "character", "moon-bunny"))
    moon = world.add(Entity("moon", "thing", "moon", label="round moon"))
    route = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.friend_name)
    rhyme = RHYMES[route % len(RHYMES)]

    world.say(f"In {rhyme.place}, {params.trait} {params.name} watched the moon-bunny {params.friend_name} rub sleepy eyes.")
    world.say(f'"Tonight I shall pamper you until your dreams are bright!" {params.name} cried.')
    world.say(f"The moon winked through the window, and {params.name} began to {rhyme.first_plan}.")
    add_meter(luna, "helpful_effort", 1)
    add_meme(luna, "eager_love", 1)

    world.para()
    world.say(f"But {rhyme.noisy_result}.")
    world.say(f'{params.friend_name} needed slumber, yet {rhyme.clue}.')
    add_meter(luna, "noise", 1)
    add_meme(bunny, "tiredness", 1)
    world.say(f'"Why do you not smile at my splendid pampering?" {params.name} asked.')
    world.say(f'"Because I need quiet more than a grand surprise," {params.friend_name} answered.')
    world.say(f"The words made {params.name} pause beside the bed.")

    world.para()
    world.say(f'{params.friend_name} added, "{rhyme.friend_line}"')
    world.say(f'{params.name} replied, "I thought more treats would show more love. I hear you now."')
    add_meme(luna, "understanding", 1)
    add_meme(bunny, "trust", 1)
    world.say("Their dialogue softened the room, and their little quarrel began to mend.")
    world.say(f"{params.name} and {params.friend_name} chose to reconcile: {rhyme.quiet_repair}.")
    add_meter(luna, "quiet_care", 1)
    add_meme(luna, "relief", 1)
    add_meme(bunny, "peace", 1)

    world.para()
    world.say(f"{rhyme.rhyme} whispered {params.name}.")
    world.say(f"They learned that {rhyme.lesson}.")
    world.say(f"At last, {rhyme.ending}.")
    world.facts.update(rhyme=rhyme, child=luna, bunny=bunny, moon=moon, reconciled=True)
    return world


def generation_prompts(world: World) -> list[str]:
    rhyme = world.facts["rhyme"]
    child = world.facts["child"].id
    bunny = world.facts["bunny"].id
    return [
        f"Write a child-friendly nursery rhyme about {child} trying to pamper {bunny} before slumber.",
        f"Use a brief dialogue in which {bunny} explains what kind of care is needed.",
        f"Show reconciliation through a quiet action and end with this image: {rhyme.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    rhyme = world.facts["rhyme"]
    child = world.facts["child"].id
    bunny = world.facts["bunny"].id
    return [
        QAItem(
            f"Why could {bunny} not slumber at first?",
            f"{bunny} could not slumber because {child}'s grand pampering plan was too noisy or busy. The bunny needed quiet care instead.",
        ),
        QAItem(
            f"What did {bunny} tell {child} in their dialogue?",
            f"{bunny} said, \"{rhyme.friend_line}\" The honest words helped {child} understand the real need.",
        ),
        QAItem(
            "How did the friends reconcile?",
            f"They reconciled when {child} listened and {rhyme.quiet_repair}.",
        ),
        QAItem(
            "What showed that the problem was solved?",
            f"{rhyme.ending}. The peaceful ending showed that the bunny could finally rest.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does pamper mean?",
            "To pamper someone means to give them extra comfort and kind care.",
        ),
        QAItem(
            "What does slumber mean?",
            "Slumber means peaceful, gentle sleep.",
        ),
        QAItem(
            "Why is dialogue useful in a disagreement?",
            "Dialogue lets people explain what they need, listen to one another, and choose a kinder solution.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is the process of repairing a disagreement so people can feel close and peaceful again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
child(C) :- child_name(C).
bunny(B) :- bunny_name(B).
wanted_pampering(C) :- child(C).
needed_slumber(B) :- bunny(B).
dialogue(C,B) :- child(C), bunny(B), spoke(C), spoke(B).
reconciliation(C,B) :- dialogue(C,B), listened(C), quiet_care(C).
resolved(B) :- needed_slumber(B), reconciliation(_,B).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child_name", "luna"),
            asp.fact("bunny_name", "bram"),
            asp.fact("spoke", "luna"),
            asp.fact("spoke", "bram"),
            asp.fact("listened", "luna"),
            asp.fact("quiet_care", "luna"),
        ]
    )


def asp_program(show: str = "#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = bool(asp.atoms(model, "resolved"))
    print("OK: ASP and Python reconciliation agree." if ok else "MISMATCH between ASP and Python reconciliation.")
    return 0 if ok else 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(name="Luna", friend_name="Bram", trait="tender", seed=0),
        StoryParams(name="Mira", friend_name="Milo", trait="thoughtful", seed=1),
        StoryParams(name="Nell", friend_name="Toby", trait="cheerful", seed=2),
        StoryParams(name="Poppy", friend_name="Ollie", trait="eager", seed=3),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + offset)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + offset
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
