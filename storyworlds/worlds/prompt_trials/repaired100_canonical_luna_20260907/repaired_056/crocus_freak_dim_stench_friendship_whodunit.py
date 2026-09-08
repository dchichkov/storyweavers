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
    "crocus garden": {
        "setting": "the old crocus garden",
        "flower": "crocus",
        "has_lamp": True,
        "has_shed": True,
    },
    "school courtyard": {
        "setting": "the school courtyard",
        "flower": "crocus",
        "has_lamp": True,
        "has_shed": False,
    },
    "hill greenhouse": {
        "setting": "the hill greenhouse",
        "flower": "crocus",
        "has_lamp": False,
        "has_shed": True,
    },
}

NAMES = ("Luna", "Milo", "Pip", "Nora", "Jasper", "Tess", "Robin", "Aya")
MOODS = ("careful", "curious", "patient", "brave")

CASES = (
    {
        "name": "the missing seed packet",
        "opening": "The gardener found a seed packet missing from the locked potting table.",
        "stench": "a sharp stench near the crocus beds",
        "suspect": "the greenhouse cat",
        "clue": "yellow soil dust on the cat's blanket did not match the damp soil by the table",
        "turn": "the stench came from a spilled bottle of flower food, not from the missing packet",
        "culprit": "a gust had pushed the packet beneath a wooden bench",
        "action": "lifted the bench carefully and found the packet sealed and dry",
        "ending": "By sunset, the crocus seeds rested safely in their labeled drawer.",
        "lesson": "a strong smell can distract a detective from the real clue",
    },
    {
        "name": "the dim lantern",
        "opening": "At dusk, the garden lantern went freak-dim just as someone noticed a muddy footprint beside the crocus sign.",
        "stench": "a sour stench under the lantern shelf",
        "suspect": "the night watcher's old boot",
        "clue": "the footprint ended at a loose drain cover, while the boot had a clean sole",
        "turn": "the stench was wet compost trapped beneath the cover",
        "culprit": "a fallen twig had blocked the lantern's air vent",
        "action": "cleared the vent and asked an adult to check the wiring",
        "ending": "The lantern shone warmly over the crocus sign, and the footprint led nowhere mysterious.",
        "lesson": "a strange smell and a strange shadow are clues to test, not proof of guilt",
    },
    {
        "name": "the vanished friendship badge",
        "opening": "Luna's friendship badge disappeared before the garden's welcome walk.",
        "stench": "a faint stench of pond mud near the notice board",
        "suspect": "Milo, who had carried the garden map",
        "clue": "Milo's map had a clean ribbon mark, but the badge's muddy pin lay beside the pond path",
        "turn": "the stench came from a wet rope hung behind the board",
        "culprit": "the badge had caught on the map's ribbon and fallen near the pond",
        "action": "returned the badge and apologized for suspecting a friend before checking the path",
        "ending": "Luna pinned the badge beside Milo's, and the two friends led the walk together.",
        "lesson": "friendship grows when people check facts and repair hurt feelings",
    },
    {
        "name": "the crooked crocus label",
        "opening": "A row of crocus labels had been shuffled before the flower judging began.",
        "stench": "a rotten-leaf stench beside the smallest pot",
        "suspect": "the wind-up display cart",
        "clue": "wheel tracks stopped before the labels moved, but a hedgehog trail crossed the soil",
        "turn": "the stench came from a leaf pile opened by the hedgehog",
        "culprit": "the hedgehog had brushed the loose labels while searching for beetles",
        "action": "matched each label to its planting card and left a safe leaf corner for the visitor",
        "ending": "The crocus labels stood straight again, with a tiny trail curling away from the pots.",
        "lesson": "a careful solution can protect a small visitor as well as solve a puzzle",
    },
    {
        "name": "the freak-dim window",
        "opening": "The greenhouse window became freak-dim, hiding the prize crocus from view.",
        "stench": "a sweet stench of overripe fruit by the sill",
        "suspect": "someone carrying a dark cloth",
        "clue": "the cloth was a clean watering towel, while sticky fruit juice covered the glass",
        "turn": "the dimness came from juice and dust on the window, not from a secret curtain",
        "culprit": "a fruit basket had tipped when the sill shook",
        "action": "asked the caretaker for safe cleaner and polished one small pane",
        "ending": "A purple crocus appeared in the bright square of glass like a little star.",
        "lesson": "look closely at the surface hiding the truth before blaming a person",
    },
)

OPENINGS = (
    "A small mystery began where ordinary garden work should have been easy.",
    "The clue appeared just before the friends were ready to go home.",
    "Nobody expected a whodunit among the spring flowers.",
    "The first sign was tiny, but Luna knew tiny clues could matter.",
)

DIALOGUE = (
    ("Milo, did you take it?", "I did not, but I can help you look."),
    ("That stench makes me think something bad happened.", "It tells us where to inspect, not whom to blame."),
    ("The lantern is freak-dim!", "Then let us compare what changed with what stayed still."),
    ("A friend should be trusted.", "Yes, and friends also deserve honest questions and honest apologies."),
    ("The clue points at the nearest suspect.", "A clue points toward a question, not a final answer."),
)

ASP_RULES = r"""
kind(crocus).
kind(freak_dim).
kind(stench).
kind(friendship).
kind(whodunit).

feature(crocus) :- kind(crocus).
feature(freak_dim) :- kind(freak_dim).
feature(stench) :- kind(stench).
feature(friendship) :- kind(friendship).
feature(whodunit) :- kind(whodunit).

usable_place(P) :- place(P), crocus_ok(P), safe_for_friends(P).
mystery_ready(P) :- usable_place(P), clue_source(P), friendship_possible(P).

place("crocus_garden").
place("school_courtyard").
place("hill_greenhouse").

crocus_ok("crocus_garden").
crocus_ok("school_courtyard").
crocus_ok("hill_greenhouse").

safe_for_friends("crocus_garden").
safe_for_friends("school_courtyard").
safe_for_friends("hill_greenhouse").

clue_source("crocus_garden").
clue_source("school_courtyard").
clue_source("hill_greenhouse").

friendship_possible("crocus_garden").
friendship_possible("school_courtyard").
friendship_possible("hill_greenhouse").

#show usable_place/1.
#show mystery_ready/1.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A friendship whodunit among crocuses.")
    parser.add_argument("--place", choices=tuple(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--mood", choices=MOODS)
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
        safe = place.replace(" ", "_")
        lines.append(asp.fact("place", safe))
        lines.append(asp.fact("crocus_ok", safe))
        lines.append(asp.fact("safe_for_friends", safe))
        lines.append(asp.fact("clue_source", safe))
        lines.append(asp.fact("friendship_possible", safe))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    python_places = {p.replace(" ", "_") for p in PLACES}
    model = asp.one_model(asp_program("#show usable_place/1.\n#show mystery_ready/1."))
    usable = {row[0] for row in asp.atoms(model, "usable_place")}
    ready = {row[0] for row in asp.atoms(model, "mystery_ready")}
    if usable == python_places and ready == python_places:
        print(f"OK: clingo gate matches Python reasoning ({len(usable)} places).")
        return 0
    print("MISMATCH:")
    print("usable in clingo:", sorted(usable))
    print("expected:", sorted(python_places))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    if hero == friend:
        raise StoryError("The detective and friend must have different names.")
    if not hero or not friend:
        raise StoryError("Both the detective and friend need names.")
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, friend=friend, mood=mood, seed=args.seed)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.friend, params.mood))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"This whodunit has no setting named {params.place}.")
    if params.hero == params.friend:
        raise StoryError("Friendship needs two different people.")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")

    seed = _story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    words = DIALOGUE[(seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUE)]
    place = PLACES[params.place]

    hero = Entity(
        id=params.hero,
        kind="character",
        label="young detective",
        type="detective",
        meters={"attention": 1.0, "distance_to_clue": 2.0},
        memes={"curiosity": 1.0, "trust": 0.8},
        location=params.place,
    )
    friend = Entity(
        id=params.friend,
        kind="character",
        label="friend",
        type="helper",
        meters={"attention": 0.8, "distance_to_clue": 2.0},
        memes={"friendship": 1.0, "trust": 0.8},
        location=params.place,
    )
    crocus = Entity(
        id="crocus",
        kind="plant",
        label="purple crocus",
        type="flower",
        meters={"height": 0.18},
        memes={"protected": 1.0},
        location=params.place,
    )
    clue = Entity(
        id="clue",
        kind="object",
        label="unexplained clue",
        type="clue",
        meters={"visibility": 0.4},
        memes={"tested": 0.0},
        location=params.place,
    )
    world = World(place=place["setting"], entities={e.id: e for e in (hero, friend, crocus, clue)})

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} young detective, visited {world.place} with "
        f"{params.friend}, their closest garden friend."
    )
    world.say(case["opening"])
    world.say(
        f"Near the purple crocus, they noticed {case['stench']}. The nearby clue made "
        f"{case['suspect']} seem suspicious."
    )

    world.para()
    world.say(f"'{words[0]}' {params.hero} said. '{words[1]}' replied {params.friend}.")
    world.say(
        f"They did not accuse anyone. Instead, they compared the smell, the marks, and "
        f"the places each person had visited."
    )
    world.say(f"Then they found that {case['clue']}.")
    world.say(
        f"The evidence changed the case: {case['turn']}. The real explanation was that "
        f"{case['culprit']}."
    )

    world.para()
    world.say(f"{params.hero} and {params.friend} {case['action']}.")
    world.say(
        f"{params.hero} apologized for the first suspicion, and {params.friend} smiled. "
        f"They both understood that friendship can survive a mistake when people tell the truth."
    )
    world.say(f"The mystery ended this way: {case['ending']}")
    world.say(f"The lesson was simple: {case['lesson'].capitalize()}.")

    hero.meters["attention"] = 1.5
    friend.meters["attention"] = 1.2
    hero.memes["careful_reasoning"] = 1.0
    friend.memes["friendship"] = 1.5
    clue.memes["tested"] = 1.0
    world.trace = [
        f"noticed: {case['stench']}",
        f"considered: {case['suspect']}",
        f"checked: {case['clue']}",
        f"discovered: {case['turn']}",
        f"resolved: {case['culprit']}",
        f"friendship_repaired: {case['lesson']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": place["setting"],
        "hero": params.hero,
        "friend": params.friend,
        "case": case["name"],
        "stench": case["stench"],
        "suspect": case["suspect"],
        "clue": case["clue"],
        "turn": case["turn"],
        "culprit": case["culprit"],
        "resolution": case["ending"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a child-friendly whodunit about {params.hero} and {params.friend} investigating a crocus mystery in {place['setting']}.",
        f"Include the words crocus, freak-dim, and stench while showing how friendship helps solve {case['name']}.",
        f"Tell how the friends replace a quick suspicion with evidence and end with a warm friendship resolution.",
    ]
    story_qa = [
        QAItem(
            question=f"What mystery did {params.hero} and {params.friend} investigate?",
            answer=f"They investigated {case['name']} in {place['setting']}, where a crocus and an unusual clue drew their attention.",
        ),
        QAItem(
            question="What did the stench tell the friends?",
            answer=f"The stench marked a place worth inspecting, but it did not prove anyone was guilty. They discovered that {case['turn']}.",
        ),
        QAItem(
            question="What evidence changed their minds?",
            answer=f"They found that {case['clue']}. This evidence helped them understand that {case['culprit']}.",
        ),
        QAItem(
            question="How did the friends protect their friendship?",
            answer=f"They checked the facts before accusing anyone, and then {params.hero} apologized for the first suspicion. They solved the mystery honestly.",
        ),
        QAItem(
            question="How did the whodunit end?",
            answer=f"{params.hero} and {params.friend} {case['action']}. {case['ending']}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a crocus?",
            answer="A crocus is a small spring flower that often opens in bright colors close to the ground.",
        ),
        QAItem(
            question="What does freak-dim mean in this storyworld?",
            answer="Freak-dim describes something that suddenly becomes unusually dark or weakly lit, such as a lantern or window.",
        ),
        QAItem(
            question="Why is a stench useful but not conclusive?",
            answer="A stench can point detectives toward a place or object to inspect, but it cannot by itself prove who caused a mystery.",
        ),
        QAItem(
            question="What helps friendship during a mystery?",
            answer="Careful questions, honest evidence, and apologies help friends solve a mystery without blaming one another unfairly.",
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
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.label:
                details.append(f"label={entity.label}")
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(details)}")
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="crocus garden", hero="Luna", friend="Milo", mood="careful"),
    StoryParams(place="school courtyard", hero="Nora", friend="Pip", mood="curious"),
    StoryParams(place="hill greenhouse", hero="Jasper", friend="Tess", mood="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show usable_place/1.\n#show mystery_ready/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show usable_place/1.\n#show mystery_ready/1."))
        print(asp.atoms(model, "usable_place"))
        print(asp.atoms(model, "mystery_ready"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        count = max(1, args.n)
        seed_base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for index in range(count):
            local = random.Random(seed_base + index)
            params = resolve_params(args, local)
            params.seed = seed_base + index
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
