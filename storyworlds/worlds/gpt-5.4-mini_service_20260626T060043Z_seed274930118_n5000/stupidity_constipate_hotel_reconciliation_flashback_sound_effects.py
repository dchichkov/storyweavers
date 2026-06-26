#!/usr/bin/env python3
"""
A standalone storyworld about a small hotel day with a silly mistake, a tummy
trouble, a flashback, and a reconciliation.

The premise is slice-of-life: a child and a grown-up (or two friends) stay in a
hotel, something awkward happens, feelings get bumpy, and they make up.
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
    kind: str = "person"  # person | thing
    type: str = "person"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class HotelRoom:
    number: str
    name: str
    has_balcony: bool = False
    has_snack_cart: bool = True
    has_elevator: bool = True
    sound_effects: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    room: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    problem: str
    seed: Optional[int] = None


ROOMS = {
    "lobby": HotelRoom(number="Lobby", name="the hotel lobby", has_balcony=False),
    "suite": HotelRoom(number="204", name="the sunny suite", has_balcony=True),
    "hall": HotelRoom(number="3B", name="the quiet hallway", has_balcony=False),
}

PROBLEMS = {
    "stupid_spill": {
        "title": "a stupid spill",
        "action": "carry the juice cup without looking",
        "effect": "spilled juice on the map",
        "flashback": "a time when they shared the last cookie and laughed together",
        "sound": "sploosh",
        "turn": "the map got sticky",
        "repair": "wipe the table and fold a fresh towel over the wet spot",
    },
    "constipate": {
        "title": "a constipated tummy",
        "action": "wait too long to ask for the bathroom",
        "effect": "felt uncomfortable and grumpy",
        "flashback": "a day when the hotel clerk had kindly shown them where the bathroom was",
        "sound": "grr-umble",
        "turn": "the tummy pinch made every little thing feel bigger",
        "repair": "take a slow walk to the restroom and drink warm water",
    },
    "hotel_mixup": {
        "title": "a hotel mix-up",
        "action": "pick up the wrong key card",
        "effect": "could not open the room door",
        "flashback": "the moment they had tagged their bags so they would not get lost",
        "sound": "beep-beep",
        "turn": "the wrong card made the hallway feel confusing",
        "repair": "check the door number and swap the card at the desk",
    },
}


class World:
    def __init__(self, room: HotelRoom) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def para(self) -> None:
        if self.lines and not self.lines[-1].endswith("\n\n"):
            self.lines.append("\n\n")


def make_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    hero = world.add(Entity(id=params.hero_name, kind="person", type=params.hero_type))
    companion = world.add(Entity(id=params.companion_name, kind="person", type=params.companion_type))
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["problem"] = params.problem
    world.facts["room"] = room
    return world


def introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    room: HotelRoom = world.facts["room"]
    world.say(f"{hero.id} was staying at {room.name} with {companion.id}.")
    world.say(f"The place felt neat and calm, with soft carpet and a tiny lamp that made the room glow.")


def problem_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    problem = PROBLEMS[world.facts["problem"]]
    hero.memes["worry"] = 1
    companion.memes["worry"] = 1
    if world.facts["problem"] == "stupid_spill":
        world.say(f"One afternoon, {hero.id} did something {problem['title']}: {hero.pronoun('subject')} forgot to hold the cup steady.")
        world.say(f"{problem['sound'].upper()}! The juice slid across the table, and {problem['effect']}.")
    elif world.facts["problem"] == "constipate":
        world.say(f"Later, {hero.id} had {problem['title']} and tried to be brave about it.")
        world.say(f"{problem['sound'].capitalize()}... {hero.id} kept sitting still, but {problem['turn']}.")
    else:
        world.say(f"At the door, {hero.id} made {problem['title']} and picked up the wrong key card.")
        world.say(f"{problem['sound'].upper()}! The card blinked back, and {problem['turn']}.")
    world.say(f"{companion.id} looked surprised, and the little hotel moment turned tense.")


def flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    problem = PROBLEMS[world.facts["problem"]]
    hero.memes["memory"] = 1
    world.say(f"{hero.id} paused, and then a flashback popped into mind:")
    world.say(f"{hero.id} remembered {problem['flashback']}.")
    world.say(f"That memory made {hero.id} think {companion.id} was not angry for good, just startled for a moment.")


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    problem = PROBLEMS[world.facts["problem"]]
    hero.memes["reconcile"] = 1
    companion.memes["reconcile"] = 1
    if world.facts["problem"] == "stupid_spill":
        world.say(f"{hero.id} said sorry and grabbed a towel.")
        world.say(f"Together they wiped the table, and the sticky spot disappeared bit by bit.")
    elif world.facts["problem"] == "constipate":
        world.say(f"{companion.id} softened right away and guided {hero.id} toward the bathroom.")
        world.say(f"{hero.id} took a slow breath, then went to drink warm water and feel better.")
    else:
        world.say(f"{hero.id} laughed a little, then went with {companion.id} to the front desk.")
        world.say(f"They checked the number, swapped the card, and the door clicked open at last.")
    world.say(f"The room felt kinder again because they worked on {problem['repair']}.")
    world.say(f"After that, they sat together in the hotel quiet, and the day felt normal and warm again.")


def tell_story(world: World) -> None:
    introduce(world)
    world.para()
    problem_setup(world)
    world.para()
    flashback(world)
    world.para()
    reconcile(world)


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    problem = PROBLEMS[world.facts["problem"]]
    room: HotelRoom = world.facts["room"]
    return [
        f"Write a slice-of-life story about {hero.id} and {companion.id} in {room.name} with a small problem, a flashback, and a reconciliation.",
        f"Tell a gentle hotel story where {hero.id} faces {problem['title']} and the sound {problem['sound']} matters to the scene.",
        f"Write a short child-friendly story about a hotel day that ends with {hero.id} and {companion.id} making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    problem = PROBLEMS[world.facts["problem"]]
    room: HotelRoom = world.facts["room"]
    return [
        QAItem(
            question=f"Where was {hero.id} staying?",
            answer=f"{hero.id} was staying at {room.name} with {companion.id}.",
        ),
        QAItem(
            question=f"What problem happened in the hotel story?",
            answer=f"The problem was {problem['title']}, and it made the day feel bumpy for a while.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {problem['flashback']}. That helped {hero.id} calm down and try again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {companion.id} making up and settling back into the quiet hotel day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hotel?",
            answer="A hotel is a place where people can stay for a short time, sleep in rooms, and get help from the front desk.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and make peace again.",
        ),
        QAItem(
            question="Why can sound effects help a story?",
            answer="Sound effects like beep-beep or sploosh can make a scene feel more alive and easier to imagine.",
        ),
        QAItem(
            question="What does constipate mean?",
            answer="To constipate means to have trouble going to the bathroom, which can make someone feel uncomfortable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"room={world.room.name}")
    lines.append(f"problem={world.facts['problem']}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.has_balcony:
            lines.append(asp.fact("has_balcony", rid))
        if room.has_snack_cart:
            lines.append(asp.fact("has_snack_cart", rid))
        if room.has_elevator:
            lines.append(asp.fact("has_elevator", rid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mentions", pid, "hotel"))
        lines.append(asp.fact("mentions", pid, "flashback"))
        lines.append(asp.fact("mentions", pid, "reconciliation"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_problem(P) :- problem(P).
story_kind(slice_of_life) :- valid_problem(_).
mentions_required(P) :- mentions(P, hotel), mentions(P, flashback), mentions(P, reconciliation).
ok(P) :- valid_problem(P), mentions_required(P).
#show ok/1.
"""


def asp_program(show: str = "#show ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "ok"))
    py = {(pid,) for pid in PROBLEMS}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} problems).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


def valid_problem_ids() -> list[str]:
    return list(PROBLEMS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    room = args.room or rng.choice(list(ROOMS))
    hero_name = args.hero_name or rng.choice(["Mina", "Leo", "Nora", "Ben", "Tia"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_name = args.companion_name or rng.choice(["Mom", "Dad", "Auntie", "Mr. Reed", "Ms. Kim"])
    companion_type = args.companion_type or ("mother" if companion_name in {"Mom", "Auntie", "Ms. Kim"} else "father")
    problem = args.problem or rng.choice(valid_problem_ids())
    return StoryParams(
        room=room,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        problem=problem,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life hotel storyworld with flashback, sound effects, and reconciliation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def generate_all() -> list[StorySample]:
    samples = []
    names = [("Mina", "girl", "Mom", "mother"), ("Leo", "boy", "Dad", "father"), ("Nora", "girl", "Auntie", "mother")]
    for room in ROOMS:
        for prob in PROBLEMS:
            hero_name, hero_type, companion_name, companion_type = random.choice(names)
            params = StoryParams(room=room, hero_name=hero_name, hero_type=hero_type,
                                 companion_name=companion_name, companion_type=companion_type,
                                 problem=prob)
            samples.append(generate(params))
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(" ".join(sorted(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = generate_all()
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.hero_name} in {p.room} with {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
