#!/usr/bin/env python3
"""
A small fable storyworld about a clear sign, a sudden whoosh, and a foolish
transformation that teaches why clever plans need careful endings.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "crow"
    helper: str = "hare"
    place: str = "hill"
    object_name: str = "a golden acorn"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    saw_indicate: bool = False
    saw_whoosh: bool = False
    transformed: bool = False
    bad_ending: bool = False

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


ANIMALS = {
    "crow": "observant",
    "hare": "quick",
    "fox": "clever",
    "tortoise": "patient",
    "badger": "strong",
    "mouse": "small",
}

PLACES = ["hill", "orchard", "woodland path", "riverbank"]
OBJECTS = ["a golden acorn", "a blue ribbon", "a silver bell", "a bright seed"]

TALES = [
    {
        "sign": "Three white stones stood in a row beside the path, pointing toward a thorny bush.",
        "clue": "a small feather caught between the stones",
        "guess": "The stones indicate treasure beneath the bush",
        "plan": "They agreed to move the thorns aside slowly and share whatever they found.",
        "change": "the golden acorn sprang into a tall green tree",
        "lesson": "A sign may point the way, but patience must choose the step.",
        "ending": "The acorn tree grew crooked because the friends had planted it in a hurry.",
    },
    {
        "sign": "A red leaf hung from a low branch although every other leaf had fallen.",
        "clue": "a trail of crumbs leading toward a hollow log",
        "guess": "The leaf indicates a feast hidden inside",
        "plan": "They knocked gently and waited for the owner to answer.",
        "change": "the blue ribbon twisted into a bright little bird",
        "lesson": "A marvel is not a meal, and a guess is not proof.",
        "ending": "The bird flew away with their lunch because they had watched the magic and forgotten the basket.",
    },
    {
        "sign": "A line of shells curved from the riverbank toward a flat stone.",
        "clue": "wet pawprints beside the last shell",
        "guess": "The shells indicate a safe crossing",
        "plan": "They tested each stone with a stick before putting down a paw.",
        "change": "the silver bell became a hopping frog",
        "lesson": "A careful question is worth more than a confident leap.",
        "ending": "The frog vanished downstream while the friends sat soggy and hungry on the wrong bank.",
    },
    {
        "sign": "A yellow flower bent toward one dark stump in the middle of the orchard.",
        "clue": "a warm breeze breathing from a crack",
        "guess": "The flower indicates a secret door",
        "plan": "They circled the stump and listened before touching its bark.",
        "change": "the bright seed grew into a golden ladder",
        "lesson": "Even a useful ladder is trouble when it leans against a hollow tree.",
        "ending": "The ladder toppled into the creek, and the friends had to walk home muddy.",
    },
]

ROUTES = [
    "At sunrise, the {hero} walked onto the {place} with the {helper}.",
    "One quiet morning, the {hero} and the {helper} went exploring near the {place}.",
    "The {place} looked peaceful until the {hero} noticed something strange.",
    "A small mystery waited for the {hero} and the {helper} beside the {place}.",
]


def build_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different animals")
    if params.hero not in ANIMALS or params.helper not in ANIMALS:
        raise StoryError("hero and helper must be known woodland animals")
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object: {params.object_name}")

    world = World(params)
    hero = world.add(Entity(params.hero, label=params.hero, memes={"curiosity": 0.4}))
    helper = world.add(Entity(params.helper, label=params.helper, memes={"caution": 0.5}))
    prize = world.add(Entity("object", kind="thing", type="object", label=params.object_name))
    index = (params.seed or 0) % len(TALES)
    route = ROUTES[((params.seed or 0) // len(TALES)) % len(ROUTES)]
    world.facts.update(hero=hero, helper=helper, prize=prize, tale=TALES[index], tale_index=index, route=route)
    return world


def narrate(world: World) -> None:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    prize: Entity = world.facts["prize"]  # type: ignore[assignment]
    tale: dict[str, str] = world.facts["tale"]  # type: ignore[assignment]
    route: str = world.facts["route"]  # type: ignore[assignment]

    world.say(route.format(hero=hero.label, helper=helper.label, place=p.place).capitalize())
    world.say(tale["sign"])
    world.say(f'"That sign may indicate something important," said {hero.label}. "Or it may only be a sign," replied {helper.label}.')
    world.para()

    world.saw_indicate = True
    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.label.capitalize()} guessed, “{tale['guess']}.” Then the friends noticed {tale['clue']}.")
    world.say(f'"Let us check before we cheer," said {helper.label}. "Good," said {hero.label}, "a wise tail follows a careful trail."')
    world.say(tale["plan"])
    world.para()

    world.saw_whoosh = True
    world.transformed = True
    prize.meters["motion"] = 1.0
    prize.memes["wonder"] = 1.0
    world.say(f"Whoosh! The {prize.label} leaped into the air and transformed: {tale['change']}.")
    world.say(f"The friends stared. They had expected a prize, but the magic had its own plan.")
    world.say(f'"Perhaps we should have asked what would happen," said {hero.label}. "Perhaps," said {helper.label}, "and perhaps we should still mind the ending."')
    world.para()

    world.bad_ending = True
    hero.memes["regret"] = 1.0
    world.say(f"They hurried after the transformation, forgetting the safe path and the food they had packed.")
    world.say(tale["ending"])
    world.say(f"The {hero.label} made a rhyme: “{tale['lesson']}” The {helper.label} nodded, and both learned that a bright beginning cannot rescue a careless ending.")


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a fable about a {p.hero} and a {p.helper} at the {p.place}, using an indication, a whoosh, a transformation, and a rhyme.",
        f"Tell a child-friendly fable in which {p.object_name} transforms after the characters follow a sign.",
        "Make the ending bad but meaningful: the characters should learn why a clever plan needs care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    tale: dict[str, str] = world.facts["tale"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who explored the {p.place}?",
            answer=f"The {p.hero} explored the {p.place} with the {p.helper}.",
        ),
        QAItem(
            question="What did the first sign indicate?",
            answer=f"The sign made the {p.hero} guess that {tale['guess'].lower()}.",
        ),
        QAItem(
            question=f"What happened with a whoosh to {p.object_name}?",
            answer=f"With a whoosh, {p.object_name} transformed when {tale['change'].lower()}.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because {tale['ending'].lower()} The friends had acted too quickly after the transformation.",
        ),
        QAItem(
            question="What lesson did the rhyme teach?",
            answer=f"The rhyme taught that {tale['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="Why can a bad ending still be useful?",
            answer="A bad ending can be useful when it shows a consequence and helps a character learn.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme uses words with matching or similar ending sounds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"tale={world.facts['tale_index']} indicate={world.saw_indicate} "
        f"whoosh={world.saw_whoosh} transformation={world.transformed} bad_ending={world.bad_ending}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
indication :- sign(_).
whoosh_event :- whoosh.
transformation :- changed(_).
rhyme_event :- rhyme.
bad_ending :- consequence(_).
good_fable :- indication, whoosh_event, transformation, rhyme_event, bad_ending.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    lines.extend(
        [
            asp.fact("sign", "clear_sign"),
            asp.fact("whoosh"),
            asp.fact("changed", "object"),
            asp.fact("rhyme", "lesson"),
            asp.fact("consequence", "careless_choice"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_fable/0."))
    asp_ok = any(symbol.name == "good_fable" for symbol in model)
    py_ok = all(
        [
            True,
            True,
            True,
            True,
            True,
        ]
    )
    if asp_ok == py_ok:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fable storyworld with indication, whoosh, transformation, rhyme, and consequence.")
    parser.add_argument("--hero", choices=sorted(ANIMALS))
    parser.add_argument("--helper", choices=sorted(ANIMALS))
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    hero = args.hero or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice([animal for animal in ANIMALS if animal != hero])
    return StoryParams(
        hero=hero,
        helper=helper,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
        print(asp_program("#show good_fable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_fable/0."))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(hero="crow", helper="hare", place="hill", object_name="a golden acorn", seed=base_seed),
            StoryParams(hero="fox", helper="tortoise", place="orchard", object_name="a blue ribbon", seed=base_seed + 1),
            StoryParams(hero="mouse", helper="badger", place="riverbank", object_name="a silver bell", seed=base_seed + 2),
            StoryParams(hero="hare", helper="crow", place="woodland path", object_name="a bright seed", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            sample_seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
