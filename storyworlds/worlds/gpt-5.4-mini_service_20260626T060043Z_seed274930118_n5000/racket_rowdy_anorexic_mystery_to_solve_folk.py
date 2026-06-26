#!/usr/bin/env python3
"""
storyworlds/worlds/racket_rowdy_anorexic_mystery_to_solve_folk.py
==================================================================

A small folk-tale storyworld about a noisy village, a missing racket,
and a mystery that can only be solved by listening carefully, following clues,
and choosing a kinder path.

The seed words are woven into the world as required:
- racket: a noisy object used in the village fair and in the clue trail
- rowdy: the troublemaker spirit of the market and crowd
- anorexic: an old folktale word carried by a character's strange byname,
  used as a proper label rather than a medical description

The stories are built from a concrete world model with physical meters and
emotional memes, and the ending changes the state in a way the prose proves.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "witch", "aunt"}
        male = {"boy", "man", "father", "king", "uncle", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    hides: set[str] = field(default_factory=set)
    echoes: set[str] = field(default_factory=set)
    rumor_level: float = 0.0


@dataclass
class Mystery:
    id: str
    clue_kind: str
    culprit_kind: str
    missing_kind: str
    hiding_place: str
    emotional_turn: str
    solved_by: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    culprit: str
    missing: str
    mood: str
    seed: Optional[int] = None


PLACES = {
    "mill": Place(name="the old mill", kind="mill", hides={"loft", "sackroom"}, echoes={"racket"}),
    "wood": Place(name="the dark wood", kind="wood", hides={"hollow", "roots"}, echoes={"rowdy"}),
    "river": Place(name="the riverbank", kind="river", hides={"reedbed", "boat"}, echoes={"racket", "rowdy"}),
    "village": Place(name="the village green", kind="village", hides={"well", "stall"}, echoes={"racket", "rowdy"}),
}

HEROES = [
    ("Mara", "girl", ["sharp-eyed", "kind"]),
    ("Tobin", "boy", ["steady", "curious"]),
    ("Elsa", "girl", ["patient", "brave"]),
    ("Jon", "boy", ["gentle", "thoughtful"]),
]

HELPERS = [
    ("Grandmother Reed", "woman", ["wise", "soft-voiced"]),
    ("Old Fox Anorexic", "thing", ["thin", "strange"]),  # byname only; folktale label
    ("Uncle Bram", "man", ["loud", "laughing"]),
    ("Aunt Sela", "woman", ["clever", "watchful"]),
]

CULPRITS = [
    ("rowdy goblin", "thing", ["rowdy", "restless"]),
    ("mischief crow", "thing", ["watchful", "sly"]),
    ("mud-sprite", "thing", ["sticky", "hungry"]),
]

MISSING = {
    "racket": {"type": "racket", "phrase": "the silver racket", "region": "hand"},
    "lantern": {"type": "lantern", "phrase": "the little brass lantern", "region": "hand"},
    "basket": {"type": "basket", "phrase": "the berry basket", "region": "hand"},
    "key": {"type": "key", "phrase": "the iron key", "region": "pocket"},
}

MOODS = ["rowdy", "quiet", "foggy", "rainy"]


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen place does not exist in this folk world.")
    if params.missing not in MISSING:
        raise StoryError("The missing thing is not known in this storyworld.")
    if params.culprit not in [c[0] for c in CULPRITS]:
        raise StoryError("The culprit is not known in this storyworld.")


def build_world(params: StoryParams) -> World:
    reasonableness_check(params)
    place = PLACES[params.place]
    world = World(place)

    hero_name, hero_type, hero_traits = next(h for h in HEROES if h[0] == params.hero)
    helper_name, helper_type, helper_traits = next(h for h in HELPERS if h[0] == params.helper)
    culprit_name, culprit_type, culprit_traits = next(c for c in CULPRITS if c[0] == params.culprit)
    miss = MISSING[params.missing]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=helper_traits))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_type, traits=culprit_traits))
    item = world.add(Entity(
        id=params.missing,
        type=miss["type"],
        label=params.missing,
        phrase=miss["phrase"],
        owner=helper.id,
        carried_by=None,
    ))

    # Act 1: calm folk setup.
    world.say(f"{hero.id} lived where {place.name} could hear every footstep and every whisper.")
    world.say(f"People said {helper.id} knew old tales, and {helper.pronoun('subject')} kept watch over {item.phrase}.")
    world.say(f"But one evening, the air turned {params.mood}, and a {culprit.label} brought a {params.culprit} racket to the lane.")
    world.say(f"The noise grew so rowdy that {item.phrase} vanished from the table.")

    # Act 2: mystery and clues.
    world.para()
    hero.memes["worry"] += 1
    world.say(f"{hero.id} frowned and listened hard.")
    world.say(f"{hero.pronoun('subject').capitalize()} followed the noise to the {world.place.name.split()[-1]}, where little clues lay in order.")
    world.say(f"First came a scrape by the {next(iter(place.hides))}, then a mark in the dust, and then a hush where the racket should have been.")
    culprit.meters["guilt"] += 1
    world.say(f"{culprit.id} looked less bold when {hero.id} noticed the clue trail.")

    # Act 3: solve.
    world.para()
    helper.memes["hope"] += 1
    world.say(f"{helper.id} said the old rule of the village: 'When a thing goes missing, follow what is left behind.'")
    if params.missing == "racket":
        world.say(f"{hero.id} found the silver racket tucked in the {next(iter(place.hides))}, right where the noise had bounced and died.")
    elif params.missing == "lantern":
        world.say(f"{hero.id} found the brass lantern under the {next(iter(place.hides))}, dim but safe from the wind.")
    elif params.missing == "basket":
        world.say(f"{hero.id} found the berry basket beside the {next(iter(place.hides))}, half-covered but still whole.")
    else:
        world.say(f"{hero.id} found the iron key hidden near the {next(iter(place.hides))}, waiting like a quiet secret.")

    culprit.memes["fear"] += 1
    culprit.memes["shame"] += 1
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1
    item.carried_by = helper.id
    world.say(f"{culprit.id} stopped being so rowdy, and {helper.id} thanked {hero.id} with a warm smile.")
    world.say(f"By the end, {item.phrase} was back where it belonged, and the night felt gentle again.")

    world.facts.update(
        hero=hero,
        helper=helper,
        culprit=culprit,
        item=item,
        place=place,
        params=params,
    )
    return world


def story_prompt(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about {f['hero'].id}, a missing {f['item'].label}, and a {f['culprit'].id} with a {f['params'].mood} racket.",
        f"Tell a mystery story set at {f['place'].name} where {f['helper'].id} helps {f['hero'].id} solve what went missing.",
        f"Write a child-friendly tale that includes the words racket, rowdy, and anorexic in a way that fits a folk story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    culprit = f["culprit"]
    item = f["item"]
    place = f["place"]
    params = f["params"]

    return [
        QAItem(
            question=f"What mystery did {hero.id} try to solve at {place.name}?",
            answer=f"{hero.id} tried to solve the mystery of the missing {item.label} at {place.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} listen for clues?",
            answer=f"{helper.id} helped {hero.id} solve the mystery by sharing an old village rule about following clues.",
        ),
        QAItem(
            question=f"What made the search feel rowdy and strange?",
            answer=f"A {culprit.id} made a {params.mood} racket, and that noisy trail led the children and elders toward the hiding place.",
        ),
        QAItem(
            question=f"Where was the missing {item.label} found?",
            answer=f"The missing {item.label} was found in the {next(iter(place.hides))} at {place.name}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the missing {item.phrase} was back with {helper.id}, and the rowdy trouble had turned into relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a racket in a folk tale?",
            answer="A racket is a loud noise or a noisy object, and in folk tales a racket often helps point to trouble or a clue.",
        ),
        QAItem(
            question="What does rowdy mean?",
            answer="Rowdy means loud, rough, and hard to calm down.",
        ),
        QAItem(
            question="Why do old folk tales use strange bynames like anorexic?",
            answer="Old folk tales sometimes give characters unusual bynames so they feel memorable, mysterious, or a little uncanny.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:16} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A missing object can only be hidden in a place that plausibly hides it.
possible_hide(P, O) :- place(P), object(O), hides(P, H), can_hide(O, H).

% Rowdy noise can disturb a place and point to the culprit.
clue(P, C) :- place(P), culprit(C), makes_noise(C), echoes(P, rowdy).

% The mystery is solved when the hero follows the clue trail and finds the object.
solved(H, O) :- hero(H), object(O), clue(_, _), found(H, O).

#show solved/2.
#show clue/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(place.hides):
            lines.append(asp.fact("hides", pid, h))
        for e in sorted(place.echoes):
            lines.append(asp.fact("echoes", pid, e))
    for hid, _, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for hname, _, _ in HELPERS:
        lines.append(asp.fact("helper", hname))
    for cname, _, traits in CULPRITS:
        lines.append(asp.fact("culprit", cname))
        if "rowdy" in traits:
            lines.append(asp.fact("makes_noise", cname))
    for mid, info in MISSING.items():
        lines.append(asp.fact("object", mid))
        for h in ["loft", "sackroom", "hollow", "roots", "reedbed", "boat", "well", "stall"]:
            if info["region"] in {"hand", "pocket"}:
                lines.append(asp.fact("can_hide", mid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solved/2."))
    solved = set(asp.atoms(model, "solved"))
    if solved:
        print(f"OK: ASP solved facts found: {sorted(solved)}")
        return 0
    print("No solved/2 facts produced by ASP.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mystery world: a rowdy clue trail and a missing object.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--culprit", choices=[c[0] for c in CULPRITS])
    ap.add_argument("--missing", choices=sorted(MISSING))
    ap.add_argument("--mood", choices=MOODS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    culprit = args.culprit or rng.choice([c[0] for c in CULPRITS])
    missing = args.missing or rng.choice(list(MISSING))
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, helper=helper, culprit=culprit, missing=missing, mood=mood)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt(world),
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


CURATED = [
    StoryParams(place="village", hero="Mara", helper="Grandmother Reed", culprit="rowdy goblin", missing="racket", mood="rowdy"),
    StoryParams(place="mill", hero="Tobin", helper="Old Fox Anorexic", culprit="mischief crow", missing="lantern", mood="foggy"),
    StoryParams(place="river", hero="Elsa", helper="Aunt Sela", culprit="mud-sprite", missing="basket", mood="rainy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show clue/2.\n#show solved/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero} at {p.place} -- missing {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
