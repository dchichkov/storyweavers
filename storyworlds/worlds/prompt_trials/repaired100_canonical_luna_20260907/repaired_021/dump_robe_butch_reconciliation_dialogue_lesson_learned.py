#!/usr/bin/env python3
"""
A small mythic story world about Butch, a mistaken dump, and a robe that
helps two friends find reconciliation through honest dialogue.

The story turns on a physical mistake: Butch dumps a bundle of washed cloth
beside the river and accidentally soils a ceremonial robe. A calm exchange
reveals what happened, and a shared repair becomes the lesson learned.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    hero: str = "Butch"
    companion: str = "Luna"
    robe: str = "moon-white robe"
    setting: str = "the river of reeds"
    seed: Optional[int] = None


NAMES = ["Butch", "Luna", "Mara", "Orin", "Tavi", "Nell"]
ROBES = [
    ("moon-white robe", "the moon-white robe"),
    ("sun-gold robe", "the sun-gold robe"),
    ("blue-star robe", "the blue-star robe"),
]
SETTINGS = [
    "the river of reeds",
    "the hill of old stones",
    "the cedar clearing",
]


@dataclass(frozen=True)
class Arc:
    title: str
    opening: str
    dump: str
    consequence: str
    dialogue: str
    repair: str
    lesson: str
    ending: str


ARCS = (
    Arc(
        "the robe at the river",
        "Long ago, when the river still remembered every name, {hero} carried clean cloth to its bank.",
        "{hero} made a careless dump beside the washing stones and set the folded robe on top of the pile.",
        "A sudden rain loosened the bank, and brown water climbed over the robe before {hero} saw the danger.",
        '"Why did you hide the robe beneath a dump?" {companion} asked. "Tell me what happened, and I will listen."',
        "{hero} admitted the mistake. Together they carried the robe upstream, rinsed it in clear water, and spread it on a warm stone.",
        "A mistake grows heavier when it is hidden, but an honest word gives two hands a place to begin.",
        "By moonrise, the robe shone clean beside the river, and the friends walked home without the old weight between them.",
    ),
    Arc(
        "the hill of ashes",
        "At dawn, {hero} climbed the hill where the village kept its festival cloth.",
        "{hero} hurried and made a dump of baskets beneath the shrine, then tucked the robe into the nearest basket.",
        "A gust scattered ash across the hill, dusting the robe and making the shrine look sorrowful.",
        '"You were rushing," {companion} said. "Did fear make you choose a quick dump instead of a careful place?"',
        "{hero} spoke plainly. The friends shook the robe beneath a pine, sorted the baskets, and rebuilt the shrine path.",
        "Care is not slowness alone; it is remembering what may be harmed by a hurried choice.",
        "When the first bell rang, the robe lifted in the clean wind like a bright flag of peace.",
    ),
    Arc(
        "the cedar clearing",
        "In the cedar clearing, {companion} guarded a robe said to hold the color of dawn.",
        "{hero} tried to help by moving fallen branches, but the last load became a rough dump beside the robe.",
        "A thorn caught the cloth, and one golden thread pulled loose.",
        '"I am angry about the torn thread," {companion} said, "but I want the truth more than a blame-song."',
        "{hero} confessed and held the cloth steady while {companion} rewove the thread with red cedar fiber.",
        "Reconciliation begins when people name the harm without turning one another into the harm.",
        "The repaired robe rested beneath the cedars, where its new red thread looked like a tiny sunrise.",
    ),
)


def choose_arc(seed: Optional[int]) -> Arc:
    return ARCS[(seed or 0) % len(ARCS)]


def build_world(params: StoryParams) -> World:
    if not params.hero.strip() or not params.companion.strip():
        raise StoryError("hero and companion names must not be empty")
    if params.hero == params.companion:
        raise StoryError("hero and companion must have different names")
    if not params.robe.strip():
        raise StoryError("robe must have a name")

    world = World()
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="traveler",
            label="the one who made the mistake",
            location=params.setting,
            meters={"care": 0.4, "calm": 0.5},
            memes={"pride": 0.7, "worry": 0.2, "trust": 0.6},
            traits=["strong", "hasty"],
        )
    )
    companion = world.add(
        Entity(
            id=params.companion,
            kind="character",
            type="keeper",
            label="the keeper of the robe",
            location=params.setting,
            meters={"care": 0.9, "calm": 0.8},
            memes={"worry": 0.3, "trust": 0.7},
            traits=["patient", "truthful"],
        )
    )
    robe = world.add(
        Entity(
            id="robe",
            kind="thing",
            type="robe",
            label=params.robe,
            phrase=f"the {params.robe}" if not params.robe.startswith("the ") else params.robe,
            owner=companion.id,
            location=params.setting,
            meters={"clean": 1.0, "whole": 1.0},
            memes={"memory": 0.8, "honor": 0.8},
        )
    )
    bundle = world.add(
        Entity(
            id="dump",
            kind="thing",
            type="dump",
            label="a careless dump of cloth and branches",
            location=params.setting,
            meters={"order": 0.2},
            memes={"confusion": 0.3},
        )
    )

    arc = choose_arc(params.seed)
    values = {
        "hero": hero.id,
        "companion": companion.id,
        "robe": robe.phrase,
        "setting": params.setting,
    }

    world.say(arc.opening.format(**values))
    world.say(
        f"{hero.id} was known for a sturdy heart, but even a sturdy heart can hurry past a small warning."
    )
    world.para()
    world.say(arc.dump.format(**values))
    hero.memes["pride"] += 0.2
    hero.memes["worry"] += 0.5
    robe.meters["clean"] -= 0.4
    robe.meters["whole"] -= 0.1
    world.say(arc.consequence.format(**values))
    world.say(arc.dialogue.format(**values))
    world.para()
    world.say(
        f"{hero.id} lowered their eyes. The silence did not become a wall, because {companion.id} waited for an answer instead of a punishment."
    )
    world.say(
        f'"I made the dump, and I should have moved the robe first," {hero.id} said. "I am sorry."'
    )
    world.say(
        f'"I accept your words," {companion.id} replied. "Now let us make the next choice together."'
    )
    world.say(arc.repair.format(**values))
    hero.meters["care"] = 0.9
    hero.meters["calm"] = 0.8
    hero.memes["pride"] = 0.3
    hero.memes["worry"] = 0.1
    hero.memes["trust"] = 0.9
    companion.memes["trust"] = 0.9
    robe.meters["clean"] = 1.0
    robe.meters["whole"] = 1.0
    bundle.meters["order"] = 0.9
    world.para()
    world.say(arc.lesson.format(**values))
    world.say(arc.ending.format(**values))

    world.facts.update(
        hero=hero,
        companion=companion,
        robe=robe,
        dump=bundle,
        arc=arc,
        setting=params.setting,
        dialogue=arc.dialogue.format(**values),
        repair=arc.repair.format(**values),
        lesson=arc.lesson.format(**values),
        ending=arc.ending.format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    robe: Entity = f["robe"]  # type: ignore[assignment]
    return [
        f"Write a myth about {hero.id}, {companion.id}, a dump, and {robe.phrase}.",
        f"Tell a child-friendly story in which dialogue leads to reconciliation after a robe is damaged.",
        f"Create a myth with a clear lesson learned: honest words can help repair a mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    robe: Entity = f["robe"]  # type: ignore[assignment]
    arc: Arc = f["arc"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {hero.id}, who made the careless dump, and {companion.id}, who cared for {robe.phrase} and listened honestly.",
        ),
        QAItem(
            question=f"What happened to {robe.phrase}?",
            answer=f"{robe.phrase.capitalize()} was placed near the dump and was harmed by the trouble that followed. The friends then cleaned or repaired it together.",
        ),
        QAItem(
            question=f"How did dialogue change the situation?",
            answer=f"{companion.id} asked what happened instead of only blaming {hero.id}. {arc.dialogue.format(hero=hero.id, companion=companion.id, robe=robe.phrase, setting=f['setting'])}",
        ),
        QAItem(
            question="How did reconciliation happen?",
            answer=f"{hero.id} admitted the mistake, apologized, and worked beside {companion.id}. Together they carried out the repair: {arc.repair.format(hero=hero.id, companion=companion.id, robe=robe.phrase, setting=f['setting'])}",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=str(f["lesson"]),
        ),
        QAItem(
            question="What final image proves that the friends made peace?",
            answer=str(f["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the making of peace after a hurt, usually through truth, apology, listening, and a changed action.",
        ),
        QAItem(
            question="Why is dialogue useful after a mistake?",
            answer="Dialogue lets people explain what happened, hear one another, and choose a fair way to repair the harm.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is an idea gained from an experience that helps someone make a wiser choice later.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic story world about a dump, a robe, and reconciliation.")
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--robe", choices=[r[0] for r in ROBES])
    parser.add_argument("--setting", choices=SETTINGS)
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
    hero = args.hero or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    companion = args.companion or rng.choice(choices)
    robe = args.robe or rng.choice([r[0] for r in ROBES])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero=hero, companion=companion, robe=robe, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) "
            f"location={entity.location!r} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
character(hero).
character(companion).
thing(dump).
thing(robe).

mistake(hero, dump, robe).
dialogue(companion, hero).
reconciliation(hero, companion) :- mistake(hero, dump, robe), dialogue(companion, hero).
lesson_learned(hero, honesty) :- reconciliation(hero, companion).
robe_safe(robe) :- reconciliation(hero, companion).

#show reconciliation/2.
#show lesson_learned/2.
#show robe_safe/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("character", "hero"),
        asp.fact("character", "companion"),
        asp.fact("thing", "dump"),
        asp.fact("thing", "robe"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        from dataclasses import asdict

        symbols = asp.one_model(asp_program())
        if not symbols:
            print("ASP verification failed: no answer set.")
            return 1
        names = {symbol.name for symbol in symbols}
        required = {"reconciliation", "lesson_learned", "robe_safe"}
        if not required.issubset(names):
            print("ASP verification failed: missing derived atoms.")
            return 1

        sample = generate(StoryParams(seed=7))
        if "reconciliation" not in sample.story.lower():
            print("ASP verification failed: generated story lacks reconciliation.")
            return 1
        if not asdict(sample.params):
            print("ASP verification failed: params did not serialize.")
            return 1
        print("OK: ASP/Python reconciliation parity verified.")
        return 0
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show reconciliation/2."))
        if args.show_asp:
            return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, robe in enumerate(ROBES):
            samples.append(
                generate(
                    StoryParams(
                        hero=NAMES[index % len(NAMES)],
                        companion=NAMES[(index + 1) % len(NAMES)],
                        robe=robe[0],
                        setting=SETTINGS[index % len(SETTINGS)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
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
