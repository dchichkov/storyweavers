#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/satisfy_lesson_learned_nursery_rhyme.py
===============================================================================================================

A small story world in a nursery-rhyme style about a wish, a gentle test,
and a lesson learned when the wish is finally satisfied in a better way.

Premise:
- A little child wants something right away.
- The child learns that grabbing too fast can spoil the moment.

Turn:
- A parent or helper offers a patient, fair way to satisfy the wish.

Resolution:
- The child accepts the lesson learned, and the wish is satisfied without harm.

The world uses typed entities with physical meters and emotional memes, and
it provides a Python reasonableness gate plus an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    verb: str
    gerund: str
    rush: str
    need: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    satisfaction: str = ""


@dataclass
class Lesson:
    id: str
    label: str
    offer: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    wish: str
    treat: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, affords={"cookie", "milk", "song"}),
    "bedroom": Place(id="bedroom", label="the bedroom", indoors=True, affords={"teddy", "song"}),
    "garden": Place(id="garden", label="the garden", indoors=False, affords={"apple", "song"}),
}

WISHES = {
    "cookie": Wish(
        id="cookie",
        verb="eat the cookie",
        gerund="eating cookies",
        rush="snatch the cookie from the plate",
        need="a patient nibble",
        risk="crumbs and tears",
        keyword="cookie",
        tags={"sweet", "food"},
    ),
    "milk": Wish(
        id="milk",
        verb="drink the milk",
        gerund="drinking milk",
        rush="tip the cup too fast",
        need="a careful sip",
        risk="a spill on the floor",
        keyword="milk",
        tags={"food", "drink"},
    ),
    "teddy": Wish(
        id="teddy",
        verb="hug the teddy",
        gerund="hugging teddies",
        rush="squeeze the teddy too hard",
        need="a gentle cuddle",
        risk="a torn seam",
        keyword="teddy",
        tags={"toy", "soft"},
    ),
    "apple": Wish(
        id="apple",
        verb="eat the apple",
        gerund="eating apples",
        rush="bite before it is washed",
        need="a tidy bite",
        risk="a sticky chin",
        keyword="apple",
        tags={"food", "fruit"},
    ),
    "song": Wish(
        id="song",
        verb="sing the song",
        gerund="singing songs",
        rush="shout over the tune",
        need="a quiet chorus",
        risk="a muddled rhyme",
        keyword="song",
        tags={"sound", "music"},
    ),
}

TREATS = {
    "cookie": Treat(id="cookie", label="cookie", phrase="a round honey cookie", region="hand"),
    "milk": Treat(id="milk", label="cup of milk", phrase="a small cup of milk", region="hand"),
    "teddy": Treat(id="teddy", label="teddy", phrase="a soft little teddy", region="arms"),
    "apple": Treat(id="apple", label="apple", phrase="a red apple", region="hand"),
    "song": Treat(id="song", label="song card", phrase="a bright song card", region="voice"),
}

LESSONS = {
    "wait": Lesson(
        id="wait",
        label="wait a moment",
        offer="count three and then have it",
        tail="counted three and smiled",
        guards={"crumbs", "spill", "tear", "muddle"},
        covers=set(),
    ),
    "share": Lesson(
        id="share",
        label="share kindly",
        offer="break it in half and share it together",
        tail="shared the treat and laughed",
        guards={"crumbs", "spill", "tear", "muddle"},
        covers=set(),
    ),
    "wash": Lesson(
        id="wash",
        label="wash first",
        offer="wash it first and then taste it",
        tail="washed first and took a happy bite",
        guards={"sticky", "spill"},
        covers=set(),
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Rose", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Noah", "Max"]
HELPERS = {"mother": "mother", "father": "father", "grandma": "grandma", "grandpa": "grandpa"}
TRAITS = ["little", "cheery", "curious", "restless", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for wish_id in place.affords:
            wish = WISHES[wish_id]
            for treat_id in TREATS:
                if treat_id == wish_id:
                    combos.append((place_id, wish_id, treat_id))
    return combos


def reasonableness_gate(place_id: str, wish_id: str, treat_id: str) -> bool:
    return (place_id, wish_id, treat_id) in valid_combos()


def explain_rejection(place_id: str, wish_id: str, treat_id: str) -> str:
    return (
        f"(No story: {wish_id} does not fit the setting or treat choice "
        f"({place_id}, {treat_id}). Please choose a matched pair.)"
    )


def possible_lessons(wish_id: str) -> list[Lesson]:
    if wish_id in {"cookie", "milk", "apple"}:
        return [LESSONS["wait"], LESSONS["share"], LESSONS["wash"]]
    return [LESSONS["wait"], LESSONS["share"]]


def choose_lesson(wish: Wish, treat: Treat) -> Optional[Lesson]:
    # A lesson is reasonable only if it directly helps satisfy the wish safely.
    for lesson in possible_lessons(wish.id):
        if wish.id in {"cookie", "milk", "apple"}:
            return lesson
        if wish.id == "teddy" and lesson.id in {"wait", "share"}:
            return lesson
        if wish.id == "song" and lesson.id in {"wait", "share"}:
            return lesson
    return None


def aspirational_ending(wish: Wish, treat: Treat) -> str:
    return {
        "cookie": "the cookie crunched sweet and neat",
        "milk": "the milk was sipped with care",
        "teddy": "the teddy stayed soft and fair",
        "apple": "the apple shone and tasted bright",
        "song": "the song came round and fit just right",
    }[wish.id]


def predict_outcome(world: World, child: Entity, wish: Wish, treat: Treat) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.memes["impatience"] = child2.memes.get("impatience", 0) + 1
    soiled = wish.id in {"cookie", "milk", "apple"}
    lesson = choose_lesson(wish, treat)
    return {"soiled": soiled, "lesson": lesson.id if lesson else None}


def tell(place: Place, wish: Wish, treat: Treat, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"want": 1.0}))
    adult = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}", memes={}))
    prize = world.add(Entity(
        id=treat.id,
        type=treat.id,
        label=treat.label,
        phrase=treat.phrase,
        owner=hero.id,
        caretaker=adult.id,
        plural=treat.plural,
    ))

    world.facts.update(hero=hero, adult=adult, prize=prize, wish=wish, treat=treat, place=place)

    world.say(f"{name} was a {trait} little {gender} who loved a sweet little wish.")
    world.say(
        f"{hero.pronoun('possessive').capitalize()} heart went tap-tap-tap, "
        f"for {hero.pronoun()} wanted to {wish.verb}."
    )
    world.say(
        f"In {place.label}, there was {treat.phrase}, and it seemed to call, "
        f"'{wish.keyword}, {wish.keyword}, come and see!'"
    )

    world.para()
    world.say(
        f"But the little one tried to {wish.rush}, and that could lead to {wish.risk}."
    )
    pred = predict_outcome(world, hero, wish, treat)
    if pred["soiled"]:
        hero.memes["frustration"] = 1.0
        world.say(
            f"The {helper} noticed at once and gave a gentle warning, "
            f"for a fast grab would not be nice."
        )

    world.para()
    lesson = choose_lesson(wish, treat)
    if lesson is None:
        raise StoryError("No lesson fits this wish.")

    world.say(
        f"'{lesson.label.capitalize()},' said {helper}. 'We can {lesson.offer}.'"
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["lesson"] = 1.0

    world.say(
        f"{name} listened close and chose the kinder way, because a lesson learned is worth a day."
    )
    world.say(
        f"So {name} did not rush; instead, {name} {lesson.tail}, and the wish was satisfied at last."
    )

    if wish.id == "cookie":
        world.say("The cookie crunched sweet and neat, and the plate stayed bright and clean.")
    elif wish.id == "milk":
        world.say("The milk was sipped with care, and not a drop was left to glare.")
    elif wish.id == "teddy":
        world.say("The teddy got a gentle hug, soft as a cloud and snug as a rug.")
    elif wish.id == "apple":
        world.say("The apple shone and tasted bright, and every bite felt just right.")
    else:
        world.say("The song came round and fit just right, like a star in the quiet night.")

    hero.memes["satisfied"] = 1.0
    hero.memes["lesson_learned"] = 1.0
    hero.memes["joy"] = 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    wish = f["wish"]
    place = f["place"]
    treat = f["treat"]
    return [
        f"Write a short nursery-rhyme story about {hero.id} who wants to {wish.verb} in {place.label}.",
        f"Tell a gentle rhyme where a child learns a lesson and still gets {treat.phrase}.",
        f"Make a tiny story with the word '{wish.keyword}' where the wish is satisfied in a safe, kind way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    wish = f["wish"]
    treat = f["treat"]
    helper = f["adult"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {place.label}?",
            answer=f"{hero.id} wanted to {wish.verb}.",
        ),
        QAItem(
            question=f"What did the {helper.type} offer so the wish could be satisfied safely?",
            answer=f"The {helper.type} said to {possible_lessons(wish.id)[0].offer}.",
        ),
        QAItem(
            question=f"What was the treat that made the story feel sweet?",
            answer=f"It was {treat.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer="A lesson learned helped the child be patient, and the wish was satisfied in a kinder way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    wish = f["wish"]
    out = [
        QAItem(
            question="What does it mean to satisfy a wish?",
            answer="To satisfy a wish means to make that wish come true or feel fulfilled.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something useful that a person understands after listening or trying again.",
        ),
    ]
    if wish.id == "cookie":
        out.append(QAItem(
            question="Why should a cookie be handled carefully?",
            answer="A cookie can crumble if someone grabs it too fast, so careful hands help keep it neat.",
        ))
    if wish.id == "milk":
        out.append(QAItem(
            question="Why should milk be poured carefully?",
            answer="Milk can spill easily, so careful pouring keeps the floor clean.",
        ))
    if wish.id == "teddy":
        out.append(QAItem(
            question="Why should a teddy be hugged gently?",
            answer="A teddy is soft, so gentle hugs help keep the seam safe.",
        ))
    if wish.id == "apple":
        out.append(QAItem(
            question="Why wash an apple first?",
            answer="Washing an apple first helps make it clean before eating.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A wish is eligible when the place affords it and the treat matches it.
eligible(P, W, T) :- place(P), wish(W), treat(T), affords(P, W), same(W, T).

% A lesson is reasonable if it helps satisfy the wish safely.
safe_lesson(W, L) :- wish(W), lesson(L), helps(L, W).

valid_story(P, W, T, L) :- eligible(P, W, T), safe_lesson(W, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for w in sorted(p.affords):
            lines.append(asp.fact("affords", pid, w))
    for wid in WISHES:
        lines.append(asp.fact("wish", wid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("same", tid, tid))
    for lid, l in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        for w in WISHES:
            if lid in {"wait", "share"} and w in {"cookie", "milk", "teddy", "apple", "song"}:
                lines.append(asp.fact("helps", lid, w))
            if lid == "wash" and w in {"cookie", "milk", "apple"}:
                lines.append(asp.fact("helps", lid, w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set()
    for p in PLACES:
        for w in WISHES:
            for t in TREATS:
                if reasonableness_gate(p, w, t):
                    for l in possible_lessons(w):
                        py.add((p, w, t, l.id))
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about satisfaction and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or rng.choice(list(PLACES))
    place = PLACES[place_id]

    wish_id = args.wish or rng.choice(sorted(place.affords))
    if wish_id not in place.affords:
        raise StoryError(explain_rejection(place_id, wish_id, args.treat or wish_id))

    treat_id = args.treat or wish_id
    if not reasonableness_gate(place_id, wish_id, treat_id):
        raise StoryError(explain_rejection(place_id, wish_id, treat_id))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place_id, wish=wish_id, treat=treat_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        WISHES[params.wish],
        TREATS[params.treat],
        params.name,
        params.gender,
        params.helper,
        rng_trait(params.seed),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def rng_trait(seed: Optional[int]) -> str:
    r = random.Random(seed)
    return r.choice(TRAITS)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", wish="cookie", treat="cookie", name="Lily", gender="girl", helper="mother"),
    StoryParams(place="kitchen", wish="milk", treat="milk", name="Leo", gender="boy", helper="father"),
    StoryParams(place="bedroom", wish="teddy", treat="teddy", name="Mia", gender="girl", helper="grandma"),
    StoryParams(place="garden", wish="apple", treat="apple", name="Theo", gender="boy", helper="grandpa"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.wish} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
