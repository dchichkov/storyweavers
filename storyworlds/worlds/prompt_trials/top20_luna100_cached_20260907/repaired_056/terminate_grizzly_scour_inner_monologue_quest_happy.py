#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "moonlit valley": {
        "setting": "the moonlit valley",
        "danger": "a runaway storm machine",
        "landmark": "the silver bridge",
    },
    "pine harbor": {
        "setting": "pine harbor",
        "danger": "a giant magnet crane",
        "landmark": "the lighthouse hill",
    },
    "cloud city": {
        "setting": "cloud city",
        "danger": "a buzzing sky engine",
        "landmark": "the golden tower",
    },
    "crystal canyon": {
        "setting": "crystal canyon",
        "danger": "a rumbling rock drill",
        "landmark": "the echo gate",
    },
}

HEROES = ("Luna", "Mira", "Sol", "Nova", "Tess", "Kai")
HELPERS = ("Pip", "Milo", "Robin", "Juno", "Ash", "Remy")
MOODS = ("brave", "thoughtful", "hopeful", "careful")

QUESTS = (
    {
        "name": "the grizzly rescue",
        "opening": "A huge grizzly had become trapped inside a ring of glowing delivery crates.",
        "clue": "The grizzly was not attacking; it was guarding a tiny cub hidden behind the crates.",
        "mistake": "Luna first thought the bear was the cause of the trouble.",
        "action": "scoured the valley for the crate controller while keeping a wide, safe distance from the bear",
        "turn": "a pawprint led to a broken control box beneath the bridge",
        "fix": "used her signal flare to call the harbor crew, who opened the crates from far away",
        "result": "the grizzly and its cub walked safely back into the pine woods",
        "ending": "The bear lifted one paw beneath the moon, and Luna felt like a hero who had rescued trust as well as a family.",
        "lesson": "look closely before deciding who needs help",
    },
    {
        "name": "the silent shield",
        "opening": "The town's protective shield went quiet while a grizzly wandered toward the power station.",
        "clue": "The grizzly followed the humming cable because a loose wire had startled it from its den.",
        "mistake": "Luna worried that the bear wanted to break the shield.",
        "action": "scoured the station's snowy path for the missing safety switch",
        "turn": "she found the switch caught beneath a fallen sign near the silver bridge",
        "fix": "lifted the sign with her strength and asked her helper to reconnect the safe switch",
        "result": "the shield glowed again, and the grizzly returned peacefully to the forest",
        "ending": "The shield shone like a second sunrise, and Luna smiled as the grizzly disappeared among the trees.",
        "lesson": "a frightening sight may have a gentle reason",
    },
    {
        "name": "the storm beacon",
        "opening": "A dark storm rolled toward the valley, and the warning beacon refused to shine.",
        "clue": "A grizzly had carried the beacon's missing lens away from the wet path.",
        "mistake": "Luna imagined the grizzly had stolen it out of mischief.",
        "action": "scoured the muddy trail for the shining lens",
        "turn": "she discovered the grizzly had placed it beside its cub to keep it above the floodwater",
        "fix": "gave the cub a dry shelter, then carried the lens to the beacon",
        "result": "the warning light flashed, and every family reached the safe hill",
        "ending": "When the storm passed, the beacon blinked over a happy valley and the grizzly watched from a dry meadow.",
        "lesson": "kindness can hide inside a puzzling choice",
    },
)

INNER_THOUGHTS = (
    "Luna thought, I must be strong enough to help, but I must also be wise enough to listen.",
    "Inside, Luna wondered, What if the biggest thing here is scared instead of cruel?",
    "Luna told herself, A true hero does not rush toward danger without understanding it.",
    "Her thoughts raced: I can face this quest one careful clue at a time.",
)

DIALOGUES = (
    ("That grizzly looks dangerous", "It may be frightened. Let us watch before we act"),
    ("Should I fly in and end this", "First find out what the bear is protecting"),
    ("The trail stops here", "Then the missing clue may be underneath us"),
    ("I want everyone safe", "Your careful plan can make that happen"),
)

OPENINGS = (
    "Every superhero quest begins with a choice.",
    "The moon rose just as the town needed a hero.",
    "A quiet evening changed when the warning bell rang.",
    "Luna had hoped for an ordinary patrol, but the valley had another plan.",
)

ASP_RULES = r"""
kind(terminate).
kind(grizzly).
kind(scour).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
setting("moonlit_valley").
setting("pine_harbor").
setting("cloud_city").
setting("crystal_canyon").
compatible(P) :- setting(P), has_grizzly(P), has_quest(P).
ending(P) :- compatible(P), has_happy_ending(P).
has_grizzly("moonlit_valley").
has_grizzly("pine_harbor").
has_grizzly("cloud_city").
has_grizzly("crystal_canyon").
has_quest("moonlit_valley").
has_quest("pine_harbor").
has_quest("cloud_city").
has_quest("crystal_canyon").
has_happy_ending("moonlit_valley").
has_happy_ending("pine_harbor").
has_happy_ending("cloud_city").
has_happy_ending("crystal_canyon").
#show compatible/1.
#show ending/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest about Luna, a grizzly, and a careful rescue.")
    parser.add_argument("--place", choices=PLACES)
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


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        atom = place.replace(" ", "_")
        lines.extend(
            [
                asp.fact("setting", atom),
                asp.fact("has_grizzly", atom),
                asp.fact("has_quest", atom),
                asp.fact("has_happy_ending", atom),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    model = asp.one_model(asp_program("#show compatible/1."))
    actual = set(asp.atoms(model, "compatible"))
    if expected != actual:
        print("MISMATCH:")
        print("only in clingo:", sorted(actual - expected))
        print("only in python:", sorted(expected - actual))
        return 1
    print(f"OK: clingo gate matches Python reasoning ({len(actual)} settings).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown setting: {place}.")
    hero = rng.choice(HEROES)
    helper = rng.choice([name for name in HELPERS if name != hero])
    return StoryParams(place=place, hero=hero, helper=helper, mood=rng.choice(MOODS), seed=args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(raw.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("The quest needs a known setting.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")

    seed = story_seed(params)
    rng = random.Random(seed)
    quest = QUESTS[seed % len(QUESTS)]
    intro = OPENINGS[(seed // len(QUESTS)) % len(OPENINGS)]
    thought = INNER_THOUGHTS[(seed // 7) % len(INNER_THOUGHTS)]
    dialogue = DIALOGUES[(seed // 11) % len(DIALOGUES)]
    place = PLACES[params.place]

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="superhero",
        type="hero",
        meters={"energy": 1.0, "distance_to_danger": 12.0},
        memes={"courage": 0.8, "kindness": 0.7},
        location=params.place,
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label="helper",
        type="partner",
        meters={"energy": 0.8, "distance_to_danger": 12.0},
        memes={"curiosity": 0.8, "trust": 0.7},
        location=params.place,
    )
    bear = Entity(
        id="grizzly",
        kind="animal",
        label="a grizzly",
        type="grizzly",
        meters={"distance_to_danger": 8.0, "calm": 0.3},
        memes={"fear": 0.7, "protectiveness": 0.9},
        location=params.place,
    )
    beacon = Entity(
        id="quest_beacon",
        kind="object",
        label="the quest beacon",
        type="beacon",
        meters={"working": 0.0},
        memes={"hope": 0.4},
        location=params.place,
    )
    world.entities = {item.id: item for item in (hero, helper, bear, beacon)}

    world.say(intro)
    world.say(f"{params.hero}, a {params.mood} superhero, patrolled {world.place} with {params.helper}.")
    world.say(quest["opening"])
    world.say(f"The danger seemed close to {place['landmark']}, where {place['danger']} had already frightened the townspeople.")
    world.say(thought)

    world.para()
    world.say(f"'{dialogue[0]},' {params.helper} whispered. '{dialogue[1]},' {params.hero} answered.")
    world.say(f"{params.hero} remembered that the quest was to protect everyone, not simply to {('terminate' if seed % 2 else 'defeat')} the nearest danger.")
    world.say(f"{params.hero} {quest['mistake']}")
    world.say(f"Instead of charging ahead, the partners {quest['action']}.")
    world.say(f"They followed the evidence until {quest['turn']}.")

    world.para()
    world.say(f"Then they learned the truth: {quest['clue']}")
    world.say(f"{params.hero} lowered their hands and spoke gently to the grizzly.")
    world.say(f"Together, the partners {quest['fix']}.")
    world.say(f"As the danger faded, {quest['result']}.")
    world.say(f"The quest ended with a happy ending: {quest['ending']}")
    world.say(f"{params.hero} knew the lesson was simple: {quest['lesson']}.")

    hero.meters.update({"energy": 0.65, "distance_to_danger": 20.0})
    hero.memes.update({"courage": 1.0, "kindness": 1.0, "wisdom": 1.0})
    helper.meters.update({"energy": 0.7, "distance_to_danger": 20.0})
    helper.memes.update({"trust": 1.0})
    bear.meters["calm"] = 1.0
    bear.memes["fear"] = 0.1
    beacon.meters["working"] = 1.0
    beacon.memes["hope"] = 1.0

    world.trace = [
        f"quest_started:{quest['name']}",
        f"first_guess:{quest['mistake']}",
        f"evidence:{quest['turn']}",
        f"truth:{quest['clue']}",
        f"resolution:{quest['result']}",
    ]
    world.facts = {
        "hero": params.hero,
        "helper": params.helper,
        "place": params.place,
        "quest": quest["name"],
        "grizzly": "a frightened grizzly protecting its family",
        "turn": quest["turn"],
        "resolution": quest["result"],
        "ending": "happy",
    }

    prompts = [
        f"Write a child-friendly superhero story about {params.hero} helping a grizzly in {place['setting']}.",
        f"Include an inner monologue, a quest, a careful investigation, and a happy ending for {params.hero}.",
        f"Use the words terminate, grizzly, and scour in a gentle story where kindness is stronger than rushing.",
    ]
    story_qa = [
        QAItem(
            question=f"What quest did {params.hero} and {params.helper} undertake?",
            answer=f"They undertook {quest['name']}: they had to understand the grizzly's situation and make the dangerous problem safe.",
        ),
        QAItem(
            question="What did Luna first misunderstand?",
            answer=f"{params.hero} first thought that {quest['mistake'].removeprefix(params.hero + ' ')} This was a guess, not the final truth.",
        ),
        QAItem(
            question="What clue changed the heroes' plan?",
            answer=f"They discovered that {quest['turn']}. That clue showed why the grizzly was nearby.",
        ),
        QAItem(
            question="How did the heroes help?",
            answer=f"They {quest['fix']}. Their plan protected both the people and the grizzly.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily because {quest['result']}. The heroes learned that {quest['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear. It can be powerful, but it may also be frightened or protective.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully and thoroughly for something.",
        ),
        QAItem(
            question="Why should a superhero investigate before acting?",
            answer="A superhero should investigate first so the solution protects innocent people and does not harm an animal or another helper.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind} "
                f"location={entity.location} meters={entity.meters} memes={entity.memes}"
            )
        for event in sample.world.trace:
            print(f"  event: {event}")
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


CURATED = [
    StoryParams("moonlit valley", "Luna", "Pip", "brave"),
    StoryParams("pine harbor", "Mira", "Robin", "careful"),
    StoryParams("cloud city", "Sol", "Juno", "hopeful"),
    StoryParams("crystal canyon", "Nova", "Ash", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/1.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/1.\n#show ending/1."))
        print(asp.atoms(model, "compatible"))
        print(asp.atoms(model, "ending"))
        return

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples = []
        seen = set()
        base = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(max(1, args.n)):
            local = random.Random(base + index)
            params = resolve_params(args, local)
            params.seed = base + index
            sample = generate(params)
            if sample.story in seen:
                continue
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
