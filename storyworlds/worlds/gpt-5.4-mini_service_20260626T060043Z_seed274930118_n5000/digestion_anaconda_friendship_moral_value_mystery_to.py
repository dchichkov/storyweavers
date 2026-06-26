#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/digestion_anaconda_friendship_moral_value_mystery_to.py
==============================================================================================================================

A small Space Adventure storyworld about friendship, a moral choice, and a
mystery caused by digestion trouble for an anaconda aboard a starship.

Premise:
- A young crew member and a friendly anaconda are traveling in a small ship.
- A missing snack crystal becomes a mystery to solve.
- The anaconda's digestion turns the situation into a gentle problem.
- Friendship, honesty, and teamwork resolve the story.

The story is generated from simulated world state, not from a frozen paragraph.
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

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    setting: str
    compartments: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    solution: str
    involved: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ship: str
    crew_name: str
    crew_type: str
    friend_name: str
    friend_type: str
    mystery: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.ship)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SHIP_REGISTRY = {
    "comet-runner": Ship(
        name="Comet Runner",
        setting="deep space",
        compartments={"bridge", "galley", "cargo bay", "observation dome"},
        hazards={"stomach_flare", "missing_snack"},
    ),
    "star-finch": Ship(
        name="Star Finch",
        setting="near a blue moon",
        compartments={"bridge", "galley", "cargo bay", "window nook"},
        hazards={"stomach_flare", "missing_snack"},
    ),
}

MYSTERIES = {
    "missing_crystal": Mystery(
        id="missing_crystal",
        clue="a tiny trail of sugar sparks",
        cause="the snack crystal was eaten too quickly",
        solution="the anaconda needed time to digest it and a warm cup of moon broth",
        involved={"digestion", "anaconda"},
    ),
    "sealed_map": Mystery(
        id="sealed_map",
        clue="a map tube stuck shut with jam",
        cause="someone closed it without checking the latch",
        solution="the crew opened it gently and told the truth about the mistake",
        involved={"mystery", "friendship"},
    ),
}

SETTINGS = {
    "bridge": "bridge",
    "galley": "galley",
    "cargo bay": "cargo bay",
    "observation dome": "observation dome",
}

CREW_NAMES = ["Mina", "Tess", "Nova", "Kai", "Rin", "Lio", "Pip", "Sora"]
FRIEND_NAMES = ["Anzu", "Milo", "Polo", "Zia", "Bram", "Nori", "Echo", "Vera"]
CREW_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["anaconda"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(params: StoryParams) -> bool:
    return (
        params.ship in SHIP_REGISTRY
        and params.setting in SHIP_REGISTRY[params.ship].compartments
        and params.mystery in MYSTERIES
    )


def explain_rejection(params: StoryParams) -> str:
    if params.ship not in SHIP_REGISTRY:
        return "(No story: that ship is not part of this world.)"
    if params.setting not in SHIP_REGISTRY[params.ship].compartments:
        return "(No story: the chosen setting does not exist on that ship.)"
    if params.mystery not in MYSTERIES:
        return "(No story: the mystery does not belong to this world.)"
    return "(No story: the requested choices do not make a reasonable story.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _append_digestive_state(world: World, anaconda: Entity) -> None:
    if anaconda.meters.get("full_belly", 0.0) >= THRESHOLD:
        anaconda.memes["uncomfortable"] = 1.0
        world.say(f"{anaconda.id}'s belly felt too full, and {anaconda.pronoun('possessive')} coils went still.")
    if anaconda.meters.get("digesting", 0.0) >= THRESHOLD:
        anaconda.memes["relief_pending"] = 1.0


def _maybe_trace_mystery(world: World, crew: Entity, friend: Entity, mystery: Mystery) -> None:
    if mystery.id == "missing_crystal":
        crew.memes["curious"] = 1.0
        friend.memes["embarrassed"] = 1.0
        world.say(
            f"{crew.id} spotted {mystery.clue} near the galley floor. "
            f"{friend.id} blinked slowly, as if remembering a small mistake."
        )
    elif mystery.id == "sealed_map":
        crew.memes["curious"] = 1.0
        crew.memes["honest"] = 1.0
        world.say(
            f"{crew.id} found {mystery.clue} in the cargo bay, and the old tube would not open."
        )


def tell(world: World, crew: Entity, friend: Entity, mystery: Mystery) -> None:
    ship = world.ship
    world.say(
        f"On the {ship.name}, {crew.id} was a little explorer who loved quiet stars and brave questions."
    )
    world.say(
        f"{friend.id} was a friendly anaconda who could curl into a soft green spiral and watch the universe by {crew.id}'s side."
    )
    world.say(
        f"One day in the {ship.setting}, the two friends went to the {world.facts['place']} together."
    )

    world.para()
    world.say(
        f"Then a mystery appeared: {mystery.clue}."
    )
    if mystery.id == "missing_crystal":
        world.say(
            f"{crew.id} knew the snack crystal had been in the galley, but now it was gone."
        )
        world.say(
            f"{friend.id} had eaten it because it smelled sweet, but {friend.id} did not mean to cause trouble."
        )
        friend.meters["full_belly"] = 1.0
        friend.meters["digesting"] = 1.0
        _append_digestive_state(world, friend)
    else:
        world.say(
            f"{crew.id} wanted to solve it before the ship's evening lights came on."
        )
        crew.memes["honesty"] = 1.0

    world.para()
    _maybe_trace_mystery(world, crew, friend, mystery)

    if mystery.id == "missing_crystal":
        world.say(
            f"{crew.id} did not get angry. Instead, {crew.id} sat beside {friend.id} and asked gentle questions."
        )
        crew.memes["friendship"] = 1.0
        friend.memes["friendship"] = 1.0
        world.say(
            f"That was the right choice, because friendship meant helping {friend.id} feel better, not shaming {friend.id} for a mistake."
        )
        world.say(
            f"{crew.id} made warm moon broth, and {friend.id} drank it slowly while {crew.id} waited."
        )
        friend.meters["digesting"] = 0.0
        friend.meters["full_belly"] = 0.0
        friend.memes["relief"] = 1.0
        world.say(
            f"After a while, the sugar sparks were gone, the stomach ache faded, and the mystery was solved."
        )
        world.say(
            f"The crystal had been eaten too fast, but the truth, the broth, and the patient waiting fixed the problem."
        )
    else:
        world.say(
            f"{crew.id} opened the tube carefully and found that the map had been sealed by accident."
        )
        world.say(
            f"{crew.id} told the truth, and the friends laughed softly because the answer was simple once they looked closely."
        )
        crew.memes["moral_value"] = 1.0
        friend.memes["friendship"] = 1.0
        world.say(
            f"They shared a snack after that, and the ship felt calm again under the stars."
        )

    world.facts.update(
        crew=crew,
        friend=friend,
        mystery=mystery,
        ship=ship,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crew: Entity = f["crew"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short Space Adventure story about {crew.id} and a friendly anaconda solving a mystery on a ship.',
        f"Tell a child-friendly story where {crew.id} and {friend.id} use friendship to solve {mystery.id}.",
        f"Write a gentle story about digestion, an anaconda, and a moral choice in deep space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: Entity = f["crew"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {crew.id} and {friend.id}, two friends on the ship {f['ship'].name}.",
        ),
        QAItem(
            question=f"What mystery did they try to solve?",
            answer=f"They tried to solve {mystery.id.replace('_', ' ')}, and the clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel unwell?",
            answer=f"{friend.id} felt unwell because {mystery.cause}, which caused digestion trouble.",
        ),
        QAItem(
            question=f"What good choice did {crew.id} make?",
            answer=f"{crew.id} chose friendship and patience instead of anger, which helped the problem get better.",
        ),
    ]
    if mystery.id == "missing_crystal":
        qa.append(
            QAItem(
                question=f"How did they fix the trouble?",
                answer=f"They made warm moon broth, waited for digestion to settle, and spoke kindly until {friend.id} felt better.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"What did they learn?",
                answer="They learned that honesty helps solve a mystery more easily than hiding a mistake.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "digestion": [
        (
            "What is digestion?",
            "Digestion is the way a body breaks down food into smaller parts so it can use the food for energy and growth.",
        )
    ],
    "anaconda": [
        (
            "What is an anaconda?",
            "An anaconda is a very large snake. It is strong, moves slowly, and can be gentle when it is calm.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people care about each other, help each other, and try to be kind together.",
        )
    ],
    "moral value": [
        (
            "Why is honesty a good choice?",
            "Honesty is a good choice because it helps other people trust you and makes it easier to fix a problem.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzling thing that is not understood at first, so people have to look for clues.",
        )
    ],
}

WORLD_ORDER = ["digestion", "anaconda", "friendship", "moral value", "mystery"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = {"digestion", "anaconda", "friendship", "moral value", "mystery"}
    out: list[QAItem] = []
    for k in WORLD_ORDER:
        if k in keys:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[k])
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
crew(C) :- crew_name(C).
friend(F) :- friend_name(F).

mystery(missing_crystal) :- mystery_id(missing_crystal).
mystery(sealed_map) :- mystery_id(sealed_map).

resolved(C,F,M) :- crew(C), friend(F), mystery(M), friendship(C,F), clue(M,C1), clue_seen(C,C1), honest_choice(C), help_wait(C,F).

friendship(C,F) :- crew(C), friend(F), shared_ship(C,F).
moral_choice(C) :- honest_choice(C).
mystery_solved(C,F,M) :- resolved(C,F,M).

#show friendship/2.
#show moral_choice/1.
#show mystery_solved/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in CREW_NAMES:
        lines.append(asp.fact("crew_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    lines.append(asp.fact("shared_ship", "Mina", "Anzu"))
    lines.append(asp.fact("clue_seen", "Mina", "a tiny trail of sugar sparks"))
    lines.append(asp.fact("honest_choice", "Mina"))
    lines.append(asp.fact("help_wait", "Mina", "Anzu"))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    syms = set((s.name, len(s.arguments)) for s in model)
    expected = {("friendship", 2), ("moral_choice", 1), ("mystery_solved", 3)}
    if expected <= syms:
        print("OK: ASP twin produced the expected shown predicates.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected predicates.")
    return 1


# ---------------------------------------------------------------------------
# Parsing, generation, and output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with digestion, anaconda, friendship, and mystery.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--crew-name")
    ap.add_argument("--crew-type", choices=CREW_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    setting = args.setting or rng.choice(sorted(SHIP_REGISTRY[ship].compartments))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    crew_type = args.crew_type or rng.choice(CREW_TYPES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    friend_type = args.friend_type or "anaconda"
    params = StoryParams(
        ship=ship,
        crew_name=crew_name,
        crew_type=crew_type,
        friend_name=friend_name,
        friend_type=friend_type,
        mystery=mystery,
        setting=setting,
    )
    if not valid_combo(params):
        raise StoryError(explain_rejection(params))
    return params


def generate(params: StoryParams) -> StorySample:
    ship = SHIP_REGISTRY[params.ship]
    world = World(ship)
    crew = world.add(Entity(id=params.crew_name, kind="character", type=params.crew_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    mystery = MYSTERIES[params.mystery]
    world.facts["place"] = params.setting

    tell(world, crew, friend, mystery)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("comet-runner", "Mina", "girl", "Anzu", "anaconda", "missing_crystal"),
            StoryParams("star-finch", "Kai", "boy", "Vera", "anaconda", "sealed_map"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            seed = base_seed + i
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
            header = f"### {p.crew_name} on {p.ship} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
