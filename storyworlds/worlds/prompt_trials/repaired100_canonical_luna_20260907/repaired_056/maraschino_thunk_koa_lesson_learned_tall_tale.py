#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "koa grove": {
        "setting": "the windy koa grove",
        "surface": "broad koa leaves",
        "safe": True,
    },
    "harbor hill": {
        "setting": "the tall hill above the harbor",
        "surface": "a bright wooden lookout",
        "safe": True,
    },
    "coconut field": {
        "setting": "the sunny coconut field",
        "surface": "a sturdy koa rail",
        "safe": True,
    },
}

HEROES = ("Mara", "Luna", "Koa", "Niko", "Pia", "Tala")
HELPERS = ("Ari", "Milo", "Ika", "Noa", "Suri", "Piko")
MOODS = ("bold", "curious", "patient", "cheerful")
TREASURES = (
    "a jar of maraschino cherries",
    "a red maraschino cherry pie",
    "a basket of maraschino cherries",
)
SOUNDS = ("thunk", "clonk", "bonk", "thump")

TALES = (
    {
        "name": "the cherry bell",
        "opening": "Mara had the strongest picnic basket on the island, or so everyone said.",
        "problem": "A gust lifted the basket toward the highest branch of a koa tree, where it landed with a loud thunk.",
        "mistake": "Mara tried to pull the branch down with one heroic tug.",
        "clue": "the branch bent lower when the basket was emptied, not when Mara pulled harder",
        "turn": "the basket was heavy because its maraschino cherries had rolled into one corner",
        "action": "Mara and the helper tied a long vine to the basket and gently swung it toward the soft leaves",
        "result": "the basket floated down safely, and not one maraschino cherry was squashed",
        "lesson": "great strength is useful, but careful thinking can make a hard job lighter",
        "ending": "That evening, the cherries shone like tiny red lanterns while the koa leaves rustled approval.",
    },
    {
        "name": "the impossible drum",
        "opening": "Luna claimed she could hear every sound on the island, even a crab whispering under a stone.",
        "problem": "A distant thunk rolled across the koa grove, and everyone feared that the old picnic drum had fallen into a ravine.",
        "mistake": "Luna shouted toward the ravine until her own echo answered back.",
        "clue": "the sound came again whenever a breeze tapped a hanging maraschino jar against the wooden sign",
        "turn": "the mysterious drum was only a jar swinging on its cord",
        "action": "Luna steadied the sign and padded the jar with a folded cloth",
        "result": "the grove became quiet, and the picnic music could begin without frightening anyone",
        "lesson": "a loud sound may have a small cause, so look before making a big guess",
        "ending": "When the musicians played, the quiet jar kept time with one tiny, polite thunk.",
    },
    {
        "name": "the cherry moon",
        "opening": "Koa the climber boasted that he could reach the moon before supper.",
        "problem": "He climbed a tall koa tree to rescue a lantern filled with maraschino cherries, then froze when the trunk gave a deep thunk.",
        "mistake": "Koa tried to climb higher, believing the moonlight would make the tree stronger.",
        "clue": "the thunk came from a loose branch rubbing against the trunk below him",
        "turn": "the safest path was down to the wide branch, not up toward the sky",
        "action": "Koa listened to the helper, moved slowly, and passed the lantern down one branch at a time",
        "result": "the lantern reached the ground, and Koa came down with both feet steady",
        "lesson": "bravery is not climbing higher than fear; it is choosing the safe next step",
        "ending": "The lantern glowed beneath the koa tree, looking almost as round and bright as the moon.",
    },
)

DIALOGUE = (
    ("I can fix this by being stronger", "Maybe we should first find out what is making it difficult"),
    ("That thunk sounds enormous", "Then let us discover whether the cause is enormous too"),
    ("I promised I could do it", "Changing your plan when you learn more is part of doing it well"),
    ("Should we hurry", "We should move carefully so our help does not make things worse"),
    ("The tallest way must be the fastest", "The safest way is usually the one worth taking"),
)

OPENERS = (
    "On that island, ordinary chores often became legendary before lunch.",
    "People said the island breeze could turn a small problem into a tall tale.",
    "Every child in the village knew that the koa trees made excellent shade and terrible hiding places.",
    "The morning began peacefully, which was unusual for a place where baskets sometimes flew.",
)

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
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASP_RULES = r"""
kind(maraschino).
kind(thunk).
kind(koa).
kind(lesson_learned).
kind(tall_tale).

has_feature(story, maraschino).
has_feature(story, thunk).
has_feature(story, koa).
has_feature(story, lesson_learned).
has_feature(story, tall_tale).

safe_place(koa_grove).
safe_place(harbor_hill).
safe_place(coconut_field).

supports_story(P) :- safe_place(P).
supports_lesson(P) :- supports_story(P).

#show supports_story/1.
#show supports_lesson/1.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall tale about maraschino, thunk, koa, and a lesson learned.")
    parser.add_argument("--place", choices=sorted(PLACES))
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
    return "\n".join(
        asp.fact("safe_place", place.replace(" ", "_"))
        for place in PLACES
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show supports_story/1.\n#show supports_lesson/1."))
    stories = set(asp.atoms(model, "supports_story"))
    lessons = set(asp.atoms(model, "supports_lesson"))
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    if stories == expected and lessons == expected:
        print(f"OK: ASP and Python agree on {len(expected)} safe story places.")
        return 0
    print("MISMATCH:")
    print("ASP stories:", sorted(stories))
    print("Python stories:", sorted(expected))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = rng.choice(HEROES)
    helper = rng.choice(tuple(name for name in HELPERS if name != hero))
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, helper=helper, mood=mood, seed=args.seed)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("A tall tale needs a known, safe setting.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different people.")

    seed = story_seed(params)
    rng = random.Random(seed)
    tale = TALES[seed % len(TALES)]
    opener = OPENERS[(seed // len(TALES)) % len(OPENERS)]
    dialogue = DIALOGUE[(seed // (len(TALES) * len(OPENERS))) % len(DIALOGUE)]
    sound = SOUNDS[(seed // (len(TALES) * len(OPENERS) * len(DIALOGUE))) % len(SOUNDS)]
    prize = TREASURES[seed % len(TREASURES)]
    place = PLACES[params.place]

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="hero",
        type="child",
        meters={"balance": 0.7, "reach": 1.0},
        memes={"confidence": 0.8, "carefulness": 0.3},
        location=params.place,
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label="helper",
        type="friend",
        meters={"balance": 0.8, "reach": 0.8},
        memes={"patience": 0.9, "carefulness": 0.9},
        location=params.place,
    )
    cherry = Entity(
        id="maraschino_jar",
        kind="object",
        label=prize,
        type="maraschino",
        meters={"weight": 0.8},
        memes={"importance": 0.8},
        location=params.place,
    )
    tree = Entity(
        id="koa_tree",
        kind="plant",
        label="a koa tree",
        type="koa",
        meters={"height": 8.0, "strength": 0.9},
        memes={"shade": 1.0},
        location=params.place,
    )
    world.entities = {item.id: item for item in (hero, helper, cherry, tree)}

    world.say(opener)
    world.say(f"{tale['opening']} {params.hero} was feeling {params.mood}, and {params.helper} was carrying {prize} through {place['setting']}.")
    world.say(f"The {place['surface']} gleamed in the sun, while the koa branches waved as if they already knew a grand adventure was coming.")

    world.para()
    world.say(tale["problem"])
    world.say(f"The noise was a mighty {sound}, followed by a second, suspicious {tale['name'].split()[0]} thunk.")
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.helper}.")
    world.say(f"Still, {params.hero} {tale['mistake']} The attempt made the problem wobble, but it did not solve it.")

    world.para()
    world.say(f"They paused and watched. Then they noticed that {tale['clue']}.")
    world.say(f"That small clue changed the whole tall tale: {tale['turn']}.")
    world.say(f"'{dialogue[1]},' said {params.helper} again. This time, {params.hero} listened instead of rushing.")

    world.para()
    world.say(f"Together, they {tale['action']}.")
    world.say(f"Because they changed their plan, {tale['result']}.")
    world.say(f"The lesson learned was this: {tale['lesson'].capitalize()}.")
    world.say(tale["ending"])

    hero.memes["confidence"] = 0.9
    hero.memes["carefulness"] = 1.0
    helper.memes["carefulness"] = 1.0
    cherry.location = "safe_ground"
    tree.memes["lesson_learned"] = 1.0
    world.trace = [
        f"problem:{tale['problem']}",
        f"first_attempt:{tale['mistake']}",
        f"clue:{tale['clue']}",
        f"turn:{tale['turn']}",
        f"resolution:{tale['result']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": place["setting"],
        "hero": params.hero,
        "helper": params.helper,
        "treasure": prize,
        "sound": sound,
        "problem": tale["problem"],
        "clue": tale["clue"],
        "turn": tale["turn"],
        "resolution": tale["result"],
        "lesson": tale["lesson"],
    }

    prompts = [
        f"Write a child-friendly Tall Tale about {params.hero} and {params.helper} in {place['setting']}, using maraschino, thunk, and koa.",
        f"Tell how a loud thunk creates a problem involving {prize}, and show the lesson learned.",
        f"Write a tall tale in which careful observation changes a bold first plan.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.helper} face?",
            answer=f"They faced this problem: {tale['problem']}.",
        ),
        QAItem(
            question="What did the first attempt get wrong?",
            answer=f"The first attempt was not enough because {tale['mistake'].capitalize()} It rushed ahead before the characters understood the cause.",
        ),
        QAItem(
            question="What clue changed their minds?",
            answer=f"They noticed that {tale['clue']}. That clue revealed what was really happening.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"They solved it when they {tale['action']}. As a result, {tale['result']}.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"They learned that {tale['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is maraschino?",
            answer="Maraschino usually describes cherries preserved in a sweet syrup, often bright red and used as a treat or decoration.",
        ),
        QAItem(
            question="What is koa?",
            answer="Koa is a Hawaiian tree known for strong, beautiful wood and broad branches.",
        ),
        QAItem(
            question="What does thunk describe?",
            answer="Thunk is a word for a heavy, dull sound made when something bumps, drops, or strikes wood.",
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
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  - {item}")
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
    StoryParams(place="koa grove", hero="Mara", helper="Ari", mood="bold"),
    StoryParams(place="harbor hill", hero="Luna", helper="Milo", mood="curious"),
    StoryParams(place="coconut field", hero="Koa", helper="Suri", mood="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show supports_story/1.\n#show supports_lesson/1."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show supports_story/1.\n#show supports_lesson/1."))
        print(asp.atoms(model, "supports_story"))
        print(asp.atoms(model, "supports_lesson"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    samples = []
    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        for index in range(args.n):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            sample = generate(params)
            while sample.story in seen:
                params.seed += 1
                sample = generate(params)
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
