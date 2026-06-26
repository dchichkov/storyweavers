#!/usr/bin/env python3
"""
storyworlds/worlds/rabbit_ferry_mug_lesson_learned_twist_animal.py
===================================================================

A small animal-story world about a rabbit, a ferry ride, and a mug,
with a lesson learned and a gentle twist.

Premise:
- A rabbit wants to cross the water on a ferry while carrying a special mug.
- The mug is important, but the ferry rocks and makes careful holding matter.
- A twist can change the outcome: the mug may be empty, full, warm, or fragile,
  and the rabbit may need help from another animal.

Story shape:
- Beginning: introduce the rabbit, the ferry, and the mug.
- Middle: the rabbit boards, the ferry rocks, and the mug is at risk.
- Turn: the rabbit makes a different choice after learning a lesson.
- Ending: the crossing succeeds, and the final image proves the change.

The world model uses physical meters and emotional memes, and the story is
driven by state updates rather than by a frozen template.
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


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    fragile: bool = False
    liquid: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "hare"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"captain", "goat", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the ferry"
    water: str = "the river"


@dataclass
class Lesson:
    lesson: str
    prompt: str
    turn: str


@dataclass
class Twist:
    id: str
    title: str
    reveal: str
    effect: str


@dataclass
class StoryParams:
    name: str
    companion: str
    mug: str
    lesson: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the ferry", water="the river")

LESSONS = {
    "careful": Lesson(
        lesson="careful hands keep treasures safe",
        prompt="hold the mug with both paws",
        turn="slow down and steady the mug",
    ),
    "ask_for_help": Lesson(
        lesson="asking for help can make a hard trip easier",
        prompt="ask the captain for a steadier seat",
        turn="sit beside someone calm",
    ),
    "share": Lesson(
        lesson="sharing a small kindness can turn worry into friendship",
        prompt="offer the mug to a friend for a moment",
        turn="share the warm drink before the crossing ends",
    ),
}

TWISTS = {
    "empty_mug": Twist(
        id="empty_mug",
        title="The mug was empty all along",
        reveal="the mug held no drink, only a few crumbs of honey",
        effect="the rabbit learned that the weight it feared was only worry",
    ),
    "kind_captain": Twist(
        id="kind_captain",
        title="The captain had a soft blanket",
        reveal="the ferry captain tucked a small blanket around the mug",
        effect="the rabbit learned that helpers can make a shaky ride feel safe",
    ),
    "friend_onboard": Twist(
        id="friend_onboard",
        title="A friend was already waiting",
        reveal="a little mouse was riding too and offered to help",
        effect="the rabbit learned that sharing a problem makes it smaller",
    ),
}

MUGS = {
    "blue_mug": {"label": "blue mug", "phrase": "a blue mug with a tiny chip", "fragile": True, "liquid": True},
    "red_mug": {"label": "red mug", "phrase": "a red mug with a shiny handle", "fragile": True, "liquid": True},
    "tin_mug": {"label": "tin mug", "phrase": "a small tin mug", "fragile": False, "liquid": False},
}

COMPANIONS = {
    "mouse": {"type": "mouse", "label": "mouse", "phrase": "a tiny mouse"},
    "duck": {"type": "duck", "label": "duck", "phrase": "a calm duck"},
    "goat": {"type": "goat", "label": "goat", "phrase": "a steady goat"},
}

NAMES = ["Ruby", "Pip", "Nibbles", "Milo", "Hazel", "Bun", "Clover", "Skye"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(lesson: str, twist: str, mug_id: str, companion: str) -> bool:
    mug = MUGS[mug_id]
    if lesson == "share" and twist == "empty_mug" and mug_id == "tin_mug":
        return False
    if twist == "kind_captain" and companion == "goat":
        return True
    if twist == "friend_onboard" and companion == "mouse":
        return True
    if twist == "empty_mug" and mug["liquid"]:
        return True
    if lesson == "careful" and mug["fragile"]:
        return True
    if lesson == "ask_for_help":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for lesson in LESSONS:
        for twist in TWISTS:
            for mug_id in MUGS:
                for companion in COMPANIONS:
                    if valid_combo(lesson, twist, mug_id, companion):
                        combos.append((SETTING.place, lesson, twist, mug_id, companion))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
lesson_ok(L) :- lesson(L).
twist_ok(T) :- twist(T).
mug_ok(M) :- mug(M).
companion_ok(C) :- companion(C).

compatible(L,T,M,C) :- lesson_ok(L), twist_ok(T), mug_ok(M), companion_ok(C), not blocked(L,T,M,C).

blocked(share, empty_mug, tin_mug, _) :- true.
blocked(_, _, _, _) :- false.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "ferry"))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for m in MUGS:
        lines.append(asp.fact("mug", m))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((l, t, m, c) for _, l, t, m, c in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_character(world: World, name: str, companion: str) -> Entity:
    rabbit = world.add(Entity(
        id=name,
        kind="character",
        type="rabbit",
        label="rabbit",
        phrase=f"a little rabbit named {name}",
        location="shore",
        memes={"curiosity": 1.0, "hope": 1.0, "worry": 0.0, "lesson": 0.0},
    ))
    buddy = world.add(Entity(
        id="companion",
        kind="character",
        type=COMPANIONS[companion]["type"],
        label=COMPANIONS[companion]["label"],
        phrase=COMPANIONS[companion]["phrase"],
        location="ferry deck",
        memes={"kindness": 1.0},
    ))
    return rabbit


def predict_spill(world: World, rabbit: Entity, mug: Entity) -> bool:
    sim = world.copy()
    sim.get(rabbit.id).memes["worry"] += 1
    sim.get(mug.id).meters["sway"] = 1.0
    return sim.get(mug.id).meters.get("spilled", 0) >= THRESHOLD


def setup_story(world: World, rabbit: Entity, companion: Entity, mug: Entity, lesson: Lesson) -> None:
    world.say(f"{rabbit.id} was a little rabbit who loved ferry rides and warm things in small mugs.")
    world.say(f"One morning, {rabbit.id} brought {mug.phrase} to {world.setting.place} and hoped for a calm crossing.")
    world.say(f"{companion.id.capitalize()} was already there, and {rabbit.id} liked having a quiet friend nearby.")
    world.facts.update(rabbit=rabbit, companion=companion, mug=mug, lesson=lesson)


def board_ferry(world: World, rabbit: Entity, mug: Entity) -> None:
    rabbit.location = "ferry deck"
    mug.carried_by = rabbit.id
    mug.location = "rabbit paws"
    world.say(f"{rabbit.id} climbed onto the ferry and held {mug.phrase} tight against {rabbit.pronoun('possessive')} chest.")


def rock_and_worry(world: World, rabbit: Entity, mug: Entity) -> None:
    rabbit.memes["worry"] += 1
    mug.meters["sway"] = 1.0
    world.say(f"The ferry rocked on {world.setting.water}, and the mug bobbed with every bump.")
    if mug.fragile:
        world.say(f"{rabbit.id} felt a tiny pinch of fear, because {mug.label} could tip if {rabbit.pronoun()} was not careful.")


def twist_reveal(world: World, twist: Twist, companion: Entity, mug: Entity) -> None:
    if twist.id == "empty_mug":
        mug.liquid = False
        mug.meters["weight"] = 0.0
        world.say(f"Then came the twist: {twist.reveal}.")
    elif twist.id == "kind_captain":
        world.say(f"Then came the twist: {twist.reveal}.")
        world.say(f"The blanket made the mug stop clinking, and the ferry felt steadier right away.")
    elif twist.id == "friend_onboard":
        world.say(f"Then came the twist: {twist.reveal}.")
        world.say(f"{companion.id.capitalize()} smiled and said it could help hold the mug while the ferry rocked.")
    world.say(f"That changed the whole ride, because {twist.effect}.")


def lesson_turn(world: World, rabbit: Entity, mug: Entity, lesson: Lesson, companion: Entity) -> None:
    rabbit.memes["lesson"] += 1
    if lesson.lesson == "careful hands keep treasures safe":
        world.say(f"{rabbit.id} remembered the lesson and gripped the mug with both paws instead of one.")
    elif lesson.lesson == "asking for help can make a hard trip easier":
        world.say(f"{rabbit.id} asked {companion.id} for help and sat closer to the middle of the deck.")
    else:
        world.say(f"{rabbit.id} offered a sip to {companion.id}, and the kindness made the worry feel lighter.")
    world.say(f"After that, {rabbit.id} could ride without shaking the mug so much.")


def resolve(world: World, rabbit: Entity, mug: Entity, lesson: Lesson, twist: Twist, companion: Entity) -> None:
    rabbit.memes["worry"] = 0.0
    rabbit.memes["peace"] = 1.0
    world.say(f"In the end, {rabbit.id} crossed the river safely.")
    if mug.liquid:
        world.say(f"{mug.label} stayed dry enough to bring home, and {rabbit.id} learned to be careful with little treasures.")
    else:
        world.say(f"The little mug turned out to be lighter than fear, and {rabbit.id} learned that some worries are bigger than the thing itself.")
    world.say(f"{companion.id.capitalize()} stayed beside {rabbit.id} as the ferry reached the far shore, and the water shone behind them.")


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    rabbit = build_character(world, params.name, params.companion)
    companion = world.get("companion")
    mug_cfg = MUGS[params.mug]
    mug = world.add(Entity(
        id="mug",
        kind="thing",
        type="mug",
        label=mug_cfg["label"],
        phrase=mug_cfg["phrase"],
        location="shore",
        fragile=mug_cfg["fragile"],
        liquid=mug_cfg["liquid"],
        meters={"weight": 1.0 if mug_cfg["liquid"] else 0.2, "sway": 0.0, "spilled": 0.0},
    ))

    setup_story(world, rabbit, companion, mug, LESSONS[params.lesson])
    world.para()
    board_ferry(world, rabbit, mug)
    rock_and_worry(world, rabbit, mug)

    if params.twist == "empty_mug":
        twist_reveal(world, TWISTS[params.twist], companion, mug)
    elif params.twist == "kind_captain":
        twist_reveal(world, TWISTS[params.twist], companion, mug)
    else:
        twist_reveal(world, TWISTS[params.twist], companion, mug)

    world.para()
    lesson_turn(world, rabbit, mug, LESSONS[params.lesson], companion)
    resolve(world, rabbit, mug, LESSONS[params.lesson], TWISTS[params.twist], companion)

    world.facts.update(
        rabbit=rabbit,
        companion=companion,
        mug=mug,
        lesson=LESSONS[params.lesson],
        twist=TWISTS[params.twist],
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story about a rabbit named {f["rabbit"].id}, a ferry ride, and a mug.',
        f"Tell a short story where a rabbit learns the lesson '{f['lesson'].lesson}' while crossing the river.",
        f"Write a child-friendly animal story with a twist about {f['twist'].title.lower()}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rabbit: Entity = f["rabbit"]
    companion: Entity = f["companion"]
    mug: Entity = f["mug"]
    lesson: Lesson = f["lesson"]
    twist: Twist = f["twist"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little rabbit named {rabbit.id}, who rode the ferry with a small mug and a helpful friend.",
        ),
        QAItem(
            question=f"What was {rabbit.id} carrying on the ferry?",
            answer=f"{rabbit.id} was carrying {mug.phrase}. The mug mattered because the ferry rocked on the river.",
        ),
        QAItem(
            question=f"What lesson did {rabbit.id} learn?",
            answer=f"{rabbit.id} learned that {lesson.lesson}. That helped turn a wobbly ride into a safe crossing.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}. That changed how {rabbit.id} understood the trip.",
        ),
        QAItem(
            question=f"Who helped {rabbit.id} on the ferry?",
            answer=f"{companion.id.capitalize()} helped by staying close and making the ride feel calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ferry?",
            answer="A ferry is a boat that carries people or animals across water.",
        ),
        QAItem(
            question="What is a mug?",
            answer="A mug is a cup with a handle, often used for warm drinks.",
        ),
        QAItem(
            question="Why should a fragile mug be held carefully?",
            answer="A fragile mug can slip, tip, or crack more easily than a strong cup, so careful hands help keep it safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:8}) loc={e.location!r} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: rabbit, ferry, mug, lesson learned, twist.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--mug", choices=sorted(MUGS))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.lesson is None or c[1] == args.lesson)
        and (args.twist is None or c[2] == args.twist)
        and (args.mug is None or c[3] == args.mug)
        and (args.companion is None or c[4] == args.companion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, lesson, twist, mug, companion = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(name=name, companion=companion, mug=mug, lesson=lesson, twist=twist)


def asp_program_text() -> str:
    return asp_program("#show compatible/4.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for _, lesson, twist, mug, companion in valid_combos():
            params = StoryParams(
                name="Ruby",
                companion=companion,
                mug=mug,
                lesson=lesson,
                twist=twist,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
