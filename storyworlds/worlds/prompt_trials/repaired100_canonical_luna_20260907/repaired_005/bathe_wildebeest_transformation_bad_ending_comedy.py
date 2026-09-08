#!/usr/bin/env python3
"""
A comic story world about bathing a wildebeest, a surprising transformation,
and a bad ending that is still safe enough to laugh about.

Seed tale:
---
Luna promised to bathe a dusty wildebeest before the village photo.
The wildebeest disliked soap, buckets, and especially Luna's singing.
When Luna added too much bubble powder, the animal transformed into a huge
walking foam cloud. Everyone chased it through the market until it sneezed
bubbles onto the mayor's hat. The photo was ruined, but nobody was hurt.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    name: str = "Luna"
    title: str = "bubbly"
    seed: Optional[int] = None
    scenario: str = "foam"
    place: str = "village"
    bath: int = 0
    reaction: int = 0
    transformation: int = 0
    ending: int = 0
    witness: int = 0


@dataclass(frozen=True)
class Beat:
    setup: str
    trouble: str
    attempts: tuple[str, str, str]
    setbacks: tuple[str, str, str]
    clue: str
    cause: str
    transformation: str
    chase: str
    bad_ending: str
    image: tuple[str, str, str, str]


@dataclass(frozen=True)
class Scenario:
    id: str
    beats: tuple[Beat, ...]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    "village": Setting("the village", "a crooked fountain, a busy market, and a very serious photo booth"),
    "savanna": Setting("the savanna camp", "yellow grass, canvas tents, and a picnic table with one wobbly leg"),
    "fair": Setting("the county fair", "striped tents, a brass band, and a prize booth shaped like a giant boot"),
}

SCENARIOS = {
    "foam": Scenario(
        "foam",
        (
            Beat(
                setup="the village photo was scheduled for noon, and the dusty wildebeest was supposed to stand beside the mayor",
                trouble="the wildebeest refused to step into the bath",
                attempts=(
                    "offer a warm bucket and a polite smile",
                    "rub a little soap on one dusty horn",
                    "sing a cheerful washing song while carrying the biggest sponge",
                ),
                setbacks=(
                    "the wildebeest backed into a flower cart",
                    "the soap landed on Luna's nose instead",
                    "the singing made the wildebeest trot backward into a stack of empty baskets",
                ),
                clue="the bubble powder rattling in Luna's pocket",
                cause="Luna had poured in a whole scoop meant for a bathtub, not a wildebeest",
                transformation="the wildebeest puffed into a towering foam cloud with four hooves underneath",
                chase="the foam beast bounced through the market, leaving soap mustaches on melons",
                bad_ending="the village photo showed only bubbles, a crooked mayor's hat, and one surprised hoof",
                image=(
                    "A bubble settled on the mayor's hat like a shiny little crown.",
                    "The photo booth curtain hung open while foam peeked out from every side.",
                    "The wildebeest sneezed one last bubble onto Luna's clean hair.",
                    "The ruined photo became the village's funniest picture of the year.",
                ),
            ),
            Beat(
                setup="the fair's animal parade needed a clean wildebeest to lead the brass band",
                trouble="the wildebeest planted all four hooves beside the wash tub",
                attempts=(
                    "tempt it with a carrot floating in the water",
                    "show that the sponge was soft",
                    "ask the brass band to play a gentle washing march",
                ),
                setbacks=(
                    "the carrot vanished, but the wildebeest did not move",
                    "the sponge flew onto the drummer's hat",
                    "the loud trumpet made the wildebeest leap over the tub",
                ),
                clue="the shiny packet of fast-acting bath crystals",
                cause="someone had mistaken parade sparkle crystals for ordinary soap",
                transformation="the wildebeest turned silver, sparkly, and twice as fluffy as a parade float",
                chase="the glittery animal galloped between the fair tents while bells jingled from its tail",
                bad_ending="the parade reached the finish line without its banner, its band, or its clean schedule",
                image=(
                    "Silver suds coated the prize booth's giant boot.",
                    "The brass band played a final note directly into a bubble.",
                    "The sparkly wildebeest posed proudly beside the wrong parade.",
                    "Luna found a glittery hoofprint on every fairground map.",
                ),
            ),
            Beat(
                setup="the camp visitors wanted a clean wildebeest for their afternoon nature sketch",
                trouble="the animal snorted at every basin Luna carried toward it",
                attempts=(
                    "place a basin beneath the shade tree",
                    "invite the wildebeest to splash one hoof",
                    "ask the cook to demonstrate a careful bath",
                ),
                setbacks=(
                    "the wildebeest dragged the basin into the grass",
                    "one splash soaked the sketch paper",
                    "the cook slipped, sat down, and declared the bath impossible",
                ),
                clue="a bright red label on the bottle Luna had borrowed",
                cause="the bottle was costume color wash, not gentle animal soap",
                transformation="the wildebeest became striped blue and pink from nose to tail",
                chase="it trotted around the tents like a runaway circus painting",
                bad_ending="the nature sketch became a colorful blur, and the visitors drew the empty shade tree instead",
                image=(
                    "The blue-and-pink wildebeest posed beside a sign that said, 'Please do not paint.'",
                    "A pink tail swished over the picnic table's wobbly leg.",
                    "The empty sketch page showed one excellent drawing of a leaf.",
                    "Luna's washcloth came back clean, but her plan did not.",
                ),
            ),
        ),
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comedy story world about bathing a transformed wildebeest.")
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--scenario", choices=SCENARIOS, default=None)
    parser.add_argument("--place", choices=SETTINGS, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--bath", type=int, default=None)
    parser.add_argument("--reaction", type=int, default=None)
    parser.add_argument("--transformation", type=int, default=None)
    parser.add_argument("--ending", type=int, default=None)
    parser.add_argument("--witness", type=int, default=None)
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
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    return StoryParams(
        name=args.name,
        seed=args.seed,
        scenario=scenario,
        place=args.place or rng.choice(list(SETTINGS)),
        bath=args.bath if args.bath is not None else rng.randrange(4),
        reaction=args.reaction if args.reaction is not None else rng.randrange(4),
        transformation=args.transformation if args.transformation is not None else rng.randrange(4),
        ending=args.ending if args.ending is not None else rng.randrange(4),
        witness=args.witness if args.witness is not None else rng.randrange(4),
    )


def reasonableness_gate(params: StoryParams, scenario: Scenario) -> None:
    if not params.name.strip():
        raise StoryError("Luna needs a name.")
    if params.scenario not in SCENARIOS:
        raise StoryError("Unknown bath scenario.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not 0 <= params.bath < 4:
        raise StoryError("Bath style must be between 0 and 3.")
    if not 0 <= params.reaction < 4:
        raise StoryError("Reaction style must be between 0 and 3.")
    if not 0 <= params.transformation < 4:
        raise StoryError("Transformation style must be between 0 and 3.")
    if not 0 <= params.ending < 4:
        raise StoryError("Ending style must be between 0 and 3.")
    if not 0 <= params.witness < 4:
        raise StoryError("Witness style must be between 0 and 3.")


ASP_RULES = r"""
character(luna).
animal(wildebeest).
action(bathe).
feature(transformation).
feature(bad_ending).
style(comedy).

valid_story :- character(luna), animal(wildebeest), action(bathe),
               feature(transformation), feature(bad_ending), style(comedy).

#show valid_story/0.
#show animal/1.
#show action/1.
#show feature/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("animal", "wildebeest"),
            asp.fact("action", "bathe"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "bad_ending"),
            asp.fact("style", "comedy"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    found = bool(asp.atoms(model, "valid_story"))
    expected = True
    if found == expected:
        print("OK: ASP confirms the comedy bath, transformation, and bad ending domain.")
        return 0
    print("MISMATCH")
    return 1


def build_world(params: StoryParams, scenario: Scenario, setting: Setting) -> World:
    beat = scenario.beats[params.transformation % len(scenario.beats)]
    world = World(setting)
    luna = world.add(Entity("hero", "character", params.name, "girl"))
    wildebeest = world.add(Entity("wildebeest", "animal", "the wildebeest", "wildebeest"))
    mayor = world.add(Entity("mayor", "character", "the mayor", "person"))
    place = world.add(Entity("place", "setting", setting.place, "place"))

    luna.memes.update({"confidence": 1.0, "patience": 0.3, "embarrassment": 0.0, "laughter": 0.0})
    wildebeest.meters.update({"dust": 1.0, "cleanliness": 0.0, "foam": 0.0, "cooperation": 0.1})
    wildebeest.memes.update({"suspicion": 0.8, "surprise": 0.0, "dignity": 1.0})
    place.meters.update({"schedule": 1.0, "order": 1.0, "photo_quality": 1.0})

    openings = (
        f"{params.name} carried a bucket toward the animal with both hands and a brave smile.",
        f"{params.name} tied on an apron, tucked in a sponge, and announced that this would be the easiest bath in history.",
        f"{params.name} inspected the wash tub, the soap, and the wildebeest's suspicious eyebrows.",
        f"{params.name} promised the village a clean wildebeest before anyone could say, 'That sounds difficult.'",
    )
    world.say(f"{params.name} lived near {setting.place}, where {setting.detail}.")
    world.say(openings[params.bath])
    world.say(f"The plan was to bathe {wildebeest.label} before the important picture.")
    world.para()

    world.say(f"{beat.setup}.")
    world.say(f"But {beat.trouble}.")
    world.say(f'"Please step into the bath," {params.name} said.')
    world.say(f'"I would rather wear the dust," said the wildebeest.')
    world.say("That answer did not make the bucket any lighter.")

    reactions = (
        "Luna nodded as if stubborn animals were part of her training.",
        "Luna tried to look professional, although one soap bubble had already landed on her eyebrow.",
        "Luna whispered, 'A calm bath is still possible,' while the wildebeest watched her very carefully.",
        "Luna smiled so hard that the mayor began taking a step backward.",
    )
    world.say(reactions[params.reaction])
    for attempt, setback in zip(beat.attempts, beat.setbacks):
        world.say(f"First, {params.name} tried to {attempt}.")
        world.say(f"But {setback}.")
    world.para()

    world.say(f"Then {params.name} noticed {beat.clue}.")
    world.say(f'"That bottle is not ordinary soap," said the mayor.')
    world.say(f'"It is still soap-ish," {params.name} replied.')
    world.say(f'"That is not a scientific word," said the mayor.')
    world.say(f"The real cause was clear: {beat.cause}.")
    world.say(f"{params.name} reached for the bottle anyway, and {beat.transformation}.")
    wildebeest.meters["foam"] = 1.0
    wildebeest.meters["cleanliness"] = 0.2
    wildebeest.memes["surprise"] = 1.0
    place.meters["order"] = 0.2
    world.para()

    world.say(f"Everyone shouted as {beat.chase}.")
    world.say(f'"Come back!" called {params.name}.')
    world.say(f'"I am clean enough!" called the wildebeest, although it was hard to tell where its face had gone.')
    world.say(f"The transformation ended in a bad way for the plan: {beat.bad_ending}.")
    place.meters["photo_quality"] = 0.0
    luna.memes["embarrassment"] = 1.0
    luna.memes["laughter"] = 1.0
    wildebeest.memes["dignity"] = 0.2
    world.say(beat.image[params.ending])
    world.say("Nobody was hurt, but the bath was declared a comedy and the photo was declared unusable.")
    world.say(f"{params.name} put down the soap and promised to read every label before the next bath.")

    world.facts.update(
        hero=luna,
        wildebeest=wildebeest,
        mayor=mayor,
        place=place,
        setting=setting,
        beat=beat,
        scenario=scenario,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    beat: Beat = world.facts["beat"]
    return [
        "Write a child-friendly comedy about Luna trying to bathe a wildebeest.",
        f"Include a funny transformation caused by {beat.cause}.",
        "End with a harmless bad ending in which the original plan fails but everyone remains safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    beat: Beat = facts["beat"]
    return [
        QAItem(
            "Who tried to bathe the wildebeest?",
            f"{facts['hero'].label} tried to bathe the wildebeest before the important picture.",
        ),
        QAItem(
            "Why did the bathing plan go wrong?",
            f"It went wrong because {beat.cause}.",
        ),
        QAItem(
            "What transformation happened?",
            f"{beat.transformation.capitalize()}.",
        ),
        QAItem(
            "What did the wildebeest do after transforming?",
            f"It {beat.chase}.",
        ),
        QAItem(
            "How did the story end?",
            f"It had a bad ending for the plan: {beat.bad_ending}. Nobody was hurt, and the event became a funny memory.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a wildebeest?",
            "A wildebeest is a large grass-eating animal with a strong body and curved horns.",
        ),
        QAItem(
            "What is a transformation in a story?",
            "A transformation is a change in a character or thing, such as an animal becoming covered in foam.",
        ),
        QAItem(
            "What is a bad ending in a comedy?",
            "A bad ending means the main plan fails, but in a gentle comedy the characters can still be safe and laugh afterward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) " + " ".join(parts))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scenario = SCENARIOS.get(params.scenario)
    if scenario is None:
        raise StoryError("Unknown scenario.")
    reasonableness_gate(params, scenario)
    world = build_world(params, scenario, SETTINGS[params.place])
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print(asp.atoms(model, "valid_story"))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for scenario_id in SCENARIOS:
            for place_id in SETTINGS:
                rng = random.Random(seed + index)
                params = StoryParams(
                    seed=seed + index,
                    scenario=scenario_id,
                    place=place_id,
                    bath=rng.randrange(4),
                    reaction=rng.randrange(4),
                    transformation=rng.randrange(4),
                    ending=rng.randrange(4),
                    witness=rng.randrange(4),
                )
                samples.append(generate(params))
                index += 1
    else:
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
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
