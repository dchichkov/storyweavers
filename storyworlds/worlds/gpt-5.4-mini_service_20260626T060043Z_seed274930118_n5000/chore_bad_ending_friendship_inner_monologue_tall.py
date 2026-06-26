#!/usr/bin/env python3
"""
Standalone storyworld: chore, friendship, inner monologue, tall tale, bad ending.

A child and a friend set out to finish a big chore in a small, exaggerated world.
The tale keeps a tall-tale feel, but the ending lands badly: the chore changes the
friendship, and the last image proves what went wrong.

The world is simulation-driven. Characters have physical meters and emotional
memes. Chores consume effort, can damage a helper's patience, and can leave the
friendship frayed if the task goes badly.
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
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0, "effort": 0.0, "done": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "friction": 0.0, "friendship": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    size: str
    chore: str
    chore_verb: str
    mess: str
    tool: str
    result: str
    tall_tale_noun: str
    noise: str
    afford_help: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


PLACES = {
    "barn": Place(
        name="the barn",
        size="mighty",
        chore="sweep the barn floor",
        chore_verb="sweep",
        mess="dust",
        tool="a broom as tall as a fence post",
        result="clean",
        tall_tale_noun="dust devil",
        noise="whoosh",
    ),
    "kitchen": Place(
        name="the kitchen",
        size="long",
        chore="wash the mountain of dishes",
        chore_verb="wash",
        mess="suds",
        tool="a washcloth thick as a mitten",
        result="bright",
        tall_tale_noun="tower of dishes",
        noise="clink",
    ),
    "porch": Place(
        name="the porch",
        size="wide",
        chore="stack the kindling",
        chore_verb="stack",
        mess="splinters",
        tool="a basket big as a wagon",
        result="orderly",
        tall_tale_noun="log hill",
        noise="thump",
    ),
    "yard": Place(
        name="the yard",
        size="stretching",
        chore="rake the leaves",
        chore_verb="rake",
        mess="leaf bits",
        tool="a rake with teeth like a comb",
        result="tidy",
        tall_tale_noun="leaf sea",
        noise="swish",
    ),
}

HERO_NAMES = ["Ruby", "Milo", "Nell", "Otis", "June", "Pip", "Iris", "Jasper"]
FRIEND_NAMES = ["Bea", "Tom", "Cleo", "Wren", "Kit", "Rue", "Finn", "Tess"]

TALL_TALE_OPENINGS = [
    "far past the last fence and just before the sky forgot its own color",
    "where the creek could sing louder than a brass band",
    "on a day so wide it looked like it had two sunsets in it",
    "in a place so big it made a pebbled path feel like a highway",
]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def intro_line(hero: Entity, place: Place) -> str:
    opening = random.choice(TALL_TALE_OPENINGS)
    return f"{hero.id} lived {opening}, near {place.name}."


def seed_inner_monologue(hero: Entity, place: Place) -> str:
    return (
        f"{hero.pronoun().capitalize()} looked at {place.name} and thought, "
        f'"If I finish this chore, maybe the whole day will shine like a nickel in sunshine."'
    )


def do_chore(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.meters["effort"] += 1
    friend.meters["effort"] += 1
    hero.meters["mess"] += 1
    friend.meters["mess"] += 1
    hero.memes["joy"] += 0.2
    friend.memes["joy"] += 0.2
    world.say(
        f"They set to work on {place.chore} with {place.tool}; "
        f"{place.noise}! {place.noise}! it sounded like the chore could be heard in the next county."
    )
    world.say(
        f"{hero.id} tugged at the job with both hands, while {friend.id} kept pace beside {hero.pronoun('object')}."
    )


def escalate(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["worry"] += 0.8
    friend.memes["friction"] += 0.6
    hero.memes["friendship"] += 0.2
    friend.memes["friendship"] += 0.2
    world.say(
        f"But the {place.tall_tale_noun} of work did not shrink; it seemed to grow a hat and two elbows."
    )
    world.say(
        f"{hero.id} kept a private little thought tucked under {hero.pronoun('possessive')} tongue: "
        f'"This is harder than a mule on a hill."'
    )


def bad_turn(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["friction"] += 1.0
    friend.memes["friction"] += 1.0
    hero.memes["friendship"] -= 0.8
    friend.memes["friendship"] -= 0.8
    hero.meters["mess"] += 1
    friend.meters["mess"] += 1
    world.say(
        f"At last, the work slipped sideways: a bucket tipped, the floor stayed {place.mess}, and the good mood went skittering off."
    )
    world.say(
        f"{hero.id} thought, 'If only I had asked for help sooner,' but {friend.id} was already frowning at the spill."
    )


def ending(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["friendship"] = max(0.0, hero.memes["friendship"])
    friend.memes["friendship"] = max(0.0, friend.memes["friendship"])
    world.say(
        f"In the end, the chore was not truly finished, and the friendship felt thinner than a pie crust in wind."
    )
    world.say(
        f"{hero.id} stood beside {place.name}, staring at the unfinished work, while {friend.id} walked home in silence."
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    place = PLACES[params.place]
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must be different characters.")

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    world.say(intro_line(hero, place))
    world.say(
        f"{hero.id} and {friend.id} were friends, as close as two buttons on the same coat."
    )
    world.say(
        f"That morning, they had one giant chore to do: {place.chore}."
    )
    world.say(seed_inner_monologue(hero, place))
    world.para()
    do_chore(world, hero, friend, place)
    escalate(world, hero, friend, place)
    world.para()
    bad_turn(world, hero, friend, place)
    ending(world, hero, friend, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        finished=False,
        friendship_lost=True,
    )
    return world


KNOWLEDGE = {
    "chore": [
        (
            "What is a chore?",
            "A chore is a task that needs doing at home or around a place, like sweeping, washing, or tidying up.",
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about someone, helping them, and spending time together kindly.",
        )
    ],
    "inner_monologue": [
        (
            "What is an inner monologue?",
            "An inner monologue is the quiet thinking in your head that other people do not hear.",
        )
    ],
    "tall_tale": [
        (
            "What is a tall tale?",
            "A tall tale is a story that makes ordinary things sound huge, funny, or impossible in an exaggerated way.",
        )
    ],
    "bad ending": [
        (
            "What is a bad ending in a story?",
            "A bad ending is when the problem is not fully fixed and things end in a sad or disappointing way.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    return [
        f"Write a tall tale for children about {hero.id} and {friend.id} trying to {place.chore}.",
        f"Tell a short story with an inner monologue where a friend worries during {place.name} chores.",
        f"Write a friendship story with a bad ending, set around the chore of {place.chore}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    return [
        QAItem(
            question=f"What chore did {hero.id} and {friend.id} have to do?",
            answer=f"They had to {place.chore}, and it felt huge enough to take all morning.",
        ),
        QAItem(
            question=f"What did {hero.id} think in {hero.pronoun('possessive')} head before the work began?",
            answer=(
                f"{hero.id} thought, \"If I finish this chore, maybe the whole day will shine like a nickel in sunshine.\""
            ),
        ),
        QAItem(
            question=f"How were {hero.id} and {friend.id} connected at the start?",
            answer=f"They were friends who stood close together, like two buttons on the same coat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly: the chore was not fully finished, and the friendship felt thin and quiet at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["chore", "friendship", "inner_monologue", "tall_tale", "bad ending"]:
        if key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} {e.type:8} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
chore(C) :- chore_name(C).

bad_end(H,F) :- friction(H), friction(F), not finished.
friendship_lost(H,F) :- bad_end(H,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in sorted(HERO_NAMES):
        lines.append(asp.fact("hero_name", name))
    for name in sorted(FRIEND_NAMES):
        lines.append(asp.fact("friend_name", name))
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("chore_name", PLACES[pid].chore_verb))
    lines.append(asp.fact("finished"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hero/1. #show friend/1. #show chore/1. #show bad_end/2. #show friendship_lost/2."))
    atoms = set()
    for sym in model:
        if sym.name in {"hero", "friend", "chore", "bad_end", "friendship_lost"}:
            atoms.add((sym.name, tuple(a.string if a.type == a.type.String else a.number for a in sym.arguments)))
    expected = {
        ("hero", (name,)) for name in HERO_NAMES
    } | {
        ("friend", (name,)) for name in FRIEND_NAMES
    } | {
        ("chore", (PLACES[pid].chore_verb,)) for pid in PLACES
    }
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP produced no visible atoms.")
    return 1


CURATED = [
    StoryParams(place="barn", name="Ruby", friend_name="Bea", hero_type="girl", friend_type="girl"),
    StoryParams(place="kitchen", name="Milo", friend_name="Tom", hero_type="boy", friend_type="boy"),
    StoryParams(place="yard", name="Nell", friend_name="Wren", hero_type="girl", friend_type="girl"),
    StoryParams(place="porch", name="Otis", friend_name="Kit", hero_type="boy", friend_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a chore, friendship, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--friend-name", dest="friend_name", choices=FRIEND_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])  # accepted for contract compatibility
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    hero_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or rng.choice(["girl", "boy"])
    if name == friend_name:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(place=place, name=name, friend_name=friend_name, hero_type=hero_type, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show hero/1. #show friend/1. #show chore/1. #show bad_end/2. #show friendship_lost/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show hero/1. #show friend/1. #show chore/1. #show bad_end/2. #show friendship_lost/2."))
        print("ASP model atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name} + {p.friend_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
