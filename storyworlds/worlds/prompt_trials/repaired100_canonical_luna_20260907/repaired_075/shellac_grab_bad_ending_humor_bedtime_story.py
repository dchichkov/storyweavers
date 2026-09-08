#!/usr/bin/env python3
"""
A gentle bedtime storyworld about shellac, a tempting grab, and a funny bad
ending that teaches a small lesson.
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
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("sticky", "dry", "safe", "embarrassment", "curiosity", "sleepiness"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

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
    name: str
    animal: str
    helper: str
    place: str
    seed: Optional[int] = None
    telling: int = 0
    ending: str = "comic"

    @property
    def label(self) -> str:
        return self.name

    @property
    def phrase(self) -> str:
        return self.name


NAMES = ["Luna", "Mabel", "Pip", "Nell", "Toby"]
ANIMALS = ["bunny", "kitten", "mouse", "hedgehog", "fox"]
HELPERS = ["Grandma", "Uncle Moss", "Aunt Fern", "Dad", "Mama"]
PLACES = ["the sleepy workshop", "the moonlit porch", "the little attic", "the quiet kitchen"]

OPENINGS = [
    "{name} the {animal} was supposed to be asleep, but a silver moonbeam had slipped under the door.",
    "At bedtime, {name} the {animal} heard a tiny squeak from the old craft shelf.",
    "The house was quiet except for {name}, who was wearing one sock and carrying a very important question.",
    "{name} had promised to tidy the sleepy workshop before bed, though promises are hardest to keep when yawns are large.",
]

SCENES = [
    {
        "object": "a wooden music box",
        "shellac": "a fresh coat of shellac still shone on its lid",
        "danger": "the shellac was tacky enough to remember every fingerprint",
        "grab": "grab the music box before the cat knocked it down",
        "bad": "the box stuck to a paw, and the paw stuck to the bedtime blanket",
        "lesson": "a quick grab is not always a clever rescue",
        "ending": "The music box played one brave plink while everyone, including the stuck blanket, tried not to giggle.",
    },
    {
        "object": "a painted spinning top",
        "shellac": "its bright shellac finish was drying beneath a tiny paper tent",
        "danger": "one touch could leave a shiny little moon-print",
        "grab": "grab the spinning top before it rolled beneath the bed",
        "bad": "the top stuck to a sleeve and spun the sleeve in a circle",
        "lesson": "waiting can be kinder to a new finish than grabbing",
        "ending": "The top stopped beside Luna's slipper, which looked very proud of becoming a hat.",
    },
    {
        "object": "a red wooden bird",
        "shellac": "the bird's shellac wings gleamed like cherries",
        "danger": "the finish needed quiet drying time",
        "grab": "grab the bird when a draft pushed it toward the window",
        "bad": "the bird stuck to a mitten and flew nowhere except around the room",
        "lesson": "a warning about wet work deserves a pause",
        "ending": "The wooden bird landed in the laundry basket, where it received a soft applause from the socks.",
    },
    {
        "object": "a tiny toy boat",
        "shellac": "its shellac deck glittered under the lamp",
        "danger": "the deck was still soft and sticky",
        "grab": "grab the boat from a puddle beside the washstand",
        "bad": "the boat stuck to a towel and sailed across the floor on a very wrinkly sea",
        "lesson": "protecting a thing means choosing the safe way, not merely the fastest way",
        "ending": "The boat reached the rug, where the rug declared itself captain and everyone went to bed.",
    },
]


def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown bedtime place: {params.place}")
    if params.animal not in ANIMALS:
        raise StoryError(f"Unknown animal: {params.animal}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.ending != "comic":
        raise StoryError("This world requires its gentle bad ending to remain comic.")


def tell(params: StoryParams) -> World:
    validate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = SCENES[params.telling % len(SCENES)]
    world = World(Setting(params.place, {"paint", "dry", "wait"}))

    hero = world.add(Entity("hero", "character", params.name, params.animal, location=params.place))
    helper = world.add(Entity("helper", "character", params.helper, "adult", location=params.place))
    craft = world.add(Entity("craft", "thing", scene["object"], "shellac_craft", owner=hero.id, location="shelf"))
    cloth = world.add(Entity("cloth", "thing", "the bedtime blanket", "blanket", location="bed"))

    hero.memes["curiosity"] = 1.0
    craft.meters["sticky"] = 1.0
    craft.meters["dry"] = 0.0

    opening = OPENINGS[params.telling % len(OPENINGS)].format(name=params.name, animal=params.animal)
    world.say(opening)
    world.say(
        f"On the craft shelf rested {scene['object']}; {scene['shellac']}. "
        f"It belonged to {params.name}, and it was meant to dry before morning."
    )
    world.say(
        f"{params.name} wanted to {scene['grab']}, because a small draft had begun to wobble it."
    )

    world.para()
    world.say(f'"Wait," said {params.helper}. "The shellac is not ready yet."')
    world.say(f'"But if I do not grab it, it may fall!" said {params.name}.')
    world.say(
        f'"Then tell me what the safe choice is," said {params.helper}. '
        "The question made the room feel less sleepy and more thoughtful."
    )
    world.say(f"{params.name} looked closely. {scene['danger'].capitalize()}.")
    hero.memes["curiosity"] += 1.0
    hero.memes["sleepiness"] += 1.0

    world.para()
    world.say(
        f"Unfortunately, {params.name} was already yawning, and a yawn is a very slippery kind of advice."
    )
    world.say(f"{params.name} made a quick grab anyway.")
    craft.meters["sticky"] += 1.0
    craft.meters["safe"] = 0.0
    craft.location = "stuck to hero"
    hero.memes["embarrassment"] += 1.0
    world.fired.add(("grab", "unsafe"))
    world.say(f"The bad ending arrived, but it arrived wearing a funny hat: {scene['bad'].capitalize()}.")
    world.say(f'"I meant to save it," said {params.name}.')
    world.say(
        f'"I know," said {params.helper}, trying not to laugh. '
        '"Next time, we can save it with patience instead of a grab."'
    )

    world.para()
    craft.location = "drying shelf"
    craft.meters["dry"] = 1.0
    craft.meters["safe"] = 1.0
    hero.memes["sleepiness"] += 1.0
    world.say(
        f"{params.helper} helped loosen the sticky craft with a little warm cloth and a lot of slow breathing."
    )
    world.say(f"{params.name} placed {scene['object']} back on the shelf and kept both paws away.")
    world.say(f"The lesson was clear: {scene['lesson']}.")
    world.say(scene["ending"])
    world.say(f"At last, {params.name} climbed into bed. Even the shellac seemed ready for sleep.")

    world.facts.update(
        hero=hero,
        helper=helper,
        craft=craft,
        cloth=cloth,
        scene=scene,
        place=params.place,
        bad_ending=True,
        humorous=True,
        shellac_present=True,
        grab_attempted=True,
        safe_resolution=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f"Write a bedtime story about {hero.label} and {scene['object']} with shellac that is not dry yet.",
        f"Include a funny bad ending when {hero.label} tries to grab the {scene['object']}.",
        f"End with the concrete lesson: {scene['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    craft = f["craft"]
    scene = f["scene"]
    return [
        QAItem(
            "Who is the bedtime story about?",
            f"It is about {hero.label}, a little {hero.type} who wanted to protect {craft.label}.",
        ),
        QAItem(
            "Why was the craft not ready to touch?",
            f"It had fresh shellac, so {scene['danger']}.",
        ),
        QAItem(
            f"What did {hero.label} try to do?",
            f"{hero.label} tried to {scene['grab']}.",
        ),
        QAItem(
            "What was the bad ending?",
            f"The funny bad ending was that {scene['bad']}.",
        ),
        QAItem(
            f"What did {helper.label} tell {hero.label}?",
            f"{helper.label} explained that the shellac needed time to dry and that patience was safer than a quick grab.",
        ),
        QAItem(
            "What lesson did the story teach?",
            f"The lesson was that {scene['lesson']}.",
        ),
        QAItem(
            "How did the story end?",
            f"{scene['ending']} Then the tired characters went to bed.",
        ),
    ]


KNOWLEDGE = [
    QAItem("What is shellac?", "Shellac is a coating that can make wood shiny, but it needs time to dry."),
    QAItem("What does grab mean?", "To grab means to take hold of something quickly."),
    QAItem("Why should wet finishes be left alone?", "A wet finish can be marked by fingers, cloth, or other objects before it dries."),
    QAItem("What is a bedtime story?", "A bedtime story is a gentle story told before sleep, often with a small lesson and a calm ending."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    sections = ["== (1) Generation prompts =="]
    sections.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== (2) Story questions ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("")
    sections.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("finish", "shellac"),
            asp.fact("needs_drying", "shellac"),
            asp.fact("object", "craft"),
            asp.fact("coated_with", "craft", "shellac"),
            asp.fact("action", "grab"),
            asp.fact("risk", "grab", "sticky_finish"),
            asp.fact("safe_action", "wait"),
            asp.fact("safe_action", "dry"),
        ]
    )


ASP_RULES = r"""
coated(craft) :- coated_with(craft, shellac).
unsafe(grab) :- action(grab), risk(grab, sticky_finish), coated(craft).
reasonable :- safe_action(wait), safe_action(dry), needs_drying(shellac).
bad_ending_possible :- unsafe(grab).
#show coated/1.
#show unsafe/1.
#show reasonable/0.
#show bad_ending_possible/0.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        unsafe = set(asp.atoms(model, "unsafe"))
        reasonable = bool(asp.atoms(model, "reasonable"))
        bad = bool(asp.atoms(model, "bad_ending_possible"))
        if unsafe == {()} and reasonable and bad:
            print("OK: ASP gate agrees with Python reasonableness.")
            return 0
        print("MISMATCH: ASP and Python disagree.")
        print("ASP atoms:", model)
        return 1
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shellac grab bedtime storyworld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--telling", type=int, choices=range(len(OPENINGS)))
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        seed=None,
        telling=args.telling if args.telling is not None else rng.randrange(len(OPENINGS)),
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
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("\n".join(str(atom) for atom in model))
        except ImportError as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i in range(len(SCENES)):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                animal=ANIMALS[i % len(ANIMALS)],
                helper=HELPERS[i % len(HELPERS)],
                place=PLACES[i % len(PLACES)],
                seed=base_seed + i,
                telling=i,
            )
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise SystemExit("-n must be at least 1")
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
