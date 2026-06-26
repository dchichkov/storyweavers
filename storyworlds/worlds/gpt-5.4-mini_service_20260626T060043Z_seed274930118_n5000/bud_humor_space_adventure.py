#!/usr/bin/env python3
"""
bud_humor_space_adventure.py
============================

A small Storyweavers world about a tiny space adventure with a bud, humor,
and a gentle problem that can be fixed with a clever choice.

Seed premise:
- A small bud is traveling aboard a quirky spaceship.
- The captain wants to help the bud open safely.
- Something silly and risky happens in zero gravity.
- The crew solves it with a simple, causal turn.
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
    protective: bool = False
    region: str = ""
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"safe": 0.0, "sparkly": 0.0, "opened": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0


@dataclass
class StoryParams:
    place: str = "orbital greenhouse"
    name: str = "Milo"
    captain_type: str = "captain"
    crewmate: str = "Pip"
    seed: Optional[int] = None


PLACES = {
    "orbital greenhouse": {
        "room": "the orbital greenhouse",
        "detail": "The glass dome showed a bright swirl of stars, and tiny pots floated in neat little rows.",
    },
    "moon dock": {
        "room": "the moon dock",
        "detail": "The moon dock hummed softly, and a squeaky cargo crane waved like a polite robot arm.",
    },
    "comet cabin": {
        "room": "the comet cabin",
        "detail": "The comet cabin rattled in a friendly way, like a spoon in a cereal bowl.",
    },
}

NAMES = ["Milo", "Nova", "Tia", "Bex", "Zuri", "Rin", "Ollie", "Ada"]
CREW = ["Pip", "Juno", "Cleo", "Mira", "Tuck", "Sage"]

ASP_RULES = r"""
bud(B).
crew(C).
place(P).
at(P,B) :- bud(B), place(P).
safe_to_open(B) :- bud(B), not too_silly(B).
too_silly(B) :- bud(B), humor(H), H > 0.
resolve(B) :- bud(B), safe_to_open(B).
#show at/2.
#show resolve/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("bud", "bud"),
        asp.fact("crew", "captain"),
        asp.fact("place", "greenhouse"),
        asp.fact("humor", 1),
        asp.fact("at", "greenhouse", "bud"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def story_is_reasonable(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.name:
        raise StoryError("A hero name is required.")
    if params.name == params.crewmate:
        raise StoryError("The hero and crewmate must be different people.")


def build_world(params: StoryParams) -> World:
    story_is_reasonable(params)
    world = World(PLACES[params.place]["room"])
    captain = world.add(Entity(id=params.name, kind="character", type="captain", label=params.name))
    crew = world.add(Entity(id=params.crewmate, kind="character", type="crewmate", label=params.crewmate))
    bud = world.add(Entity(id="bud", kind="thing", type="bud", label="bud", phrase="a tiny green bud"))
    visor = world.add(Entity(id="visor", kind="thing", type="gear", label="bubble visor", protective=True, covers={"face"}))
    world.facts.update(captain=captain, crew=crew, bud=bud, visor=visor, place=params.place)
    return world


def _humor_beats(world: World) -> None:
    captain = world.get(world.facts["captain"].id)
    crew = world.get(world.facts["crew"].id)
    bud = world.get("bud")
    if bud.meters["opened"] >= THRESHOLD:
        return
    if ("wobble", bud.id) in world.fired:
        return
    world.fired.add(("wobble", bud.id))
    captain.memes["humor"] += 1
    crew.memes["humor"] += 1
    world.say("The bud bobbed in zero gravity and spun once like a tiny green top.")
    world.say(f"{crew.id} giggled, 'That bud is trying to moonwalk!'")
    bud.meters["sparkly"] += 1


def grow_bud(world: World, narrate: bool = True) -> None:
    bud = world.get("bud")
    captain = world.get(world.facts["captain"].id)
    crew = world.get(world.facts["crew"].id)
    if ("open", bud.id) in world.fired:
        return
    if bud.meters["sparkly"] < THRESHOLD:
        return
    world.fired.add(("open", bud.id))
    bud.meters["opened"] += 1
    captain.memes["pride"] += 1
    crew.memes["joy"] += 1
    if narrate:
        world.say("When the lights dimmed, the captain gently turned the pot toward the sun-window.")
        world.say("The bud opened at last into a bright little flower, as cheerful as a star blinking awake.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    captain = world.get(world.facts["captain"].id)
    crew = world.get(world.facts["crew"].id)
    bud = world.get("bud")

    world.say(f"{captain.id} was the captain of a small ship that traveled through shiny space.")
    world.say(f"One day, {captain.id} found {bud.phrase} tucked beside a pot on the greenhouse shelf.")
    world.say(f"{bud.id} wanted to grow, and {captain.id} wanted to help {bud.pronoun('object')} safely.")
    world.say(f"{crew.id} said, 'This ship has a very important job: protecting the universe and one tiny bud.'")

    world.para()
    world.say(PLACES[params.place]["detail"])
    world.say(f"But the air recycler made the pot wobble, and the bud kept doing a silly little spin.")
    world.say(f"{captain.id} worried that too much wobble would keep {bud.pronoun('object')} from opening.")

    world.para()
    world.say(f"So {captain.id} clipped on a bubble visor for the work lights and asked {crew.id} to hold the pot steady.")
    world.say(f"{crew.id} saluted and said, 'Aye aye, chief of gardening in outer space!'")
    bud.meters["safe"] += 1
    captain.memes["worry"] += 1
    captain.memes["humor"] += 1

    _humor_beats(world)
    grow_bud(world)

    world.para()
    if bud.meters["opened"] >= THRESHOLD:
        world.say(f"At last, the bud opened into a small pink flower, and the whole greenhouse smelled sweet.")
        world.say(f"{captain.id} laughed, {crew.id} clapped, and the ship floated on through space with a brighter little corner than before.")
    else:
        world.say("The captain kept the pot steady, and the bud stayed safe while it gathered strength for tomorrow.")

    world.facts.update(place=params.place)
    return world


KNOWLEDGE = {
    "bud": [
        QAItem(
            question="What is a bud?",
            answer="A bud is a young part of a plant that has not opened yet. It can grow into a leaf, flower, or new stem.",
        ),
        QAItem(
            question="Why do people smile when a bud opens?",
            answer="People smile because an opening bud means the plant is growing and something pretty may bloom.",
        ),
    ],
    "space": [
        QAItem(
            question="Why do things float in a spaceship?",
            answer="Things float because there is much less gravity pulling them down inside a spacecraft.",
        ),
        QAItem(
            question="What is a spaceship for?",
            answer="A spaceship is a vehicle that carries people or cargo through space.",
        ),
    ],
    "humor": [
        QAItem(
            question="Why are silly jokes fun?",
            answer="Silly jokes can make people laugh, and laughing can help a tricky moment feel lighter.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short humorous space adventure about a tiny bud in {world.place}.",
        "Tell a child-friendly story where a captain helps a bud grow safely in space.",
        "Write a playful outer-space tale that ends with a bud opening into a flower.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain = world.facts["captain"]
    crew = world.facts["crew"]
    bud = world.get("bud")
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was trying to help the bud in {place}?",
            answer=f"{captain.id} was trying to help the bud in {place}, with {crew.id} helping too.",
        ),
        QAItem(
            question="What problem made the bud’s pot tricky?",
            answer="The air recycler made the pot wobble, so the bud kept spinning and needed steady help.",
        ),
        QAItem(
            question="How did the crew fix the problem?",
            answer="They used a bubble visor and held the pot steady so the bud could grow safely.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The bud opened into a small pink flower, and the ship felt brighter and happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["bud"])
    out.extend(KNOWLEDGE["space"])
    out.extend(KNOWLEDGE["humor"])
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, "bud") for p in PLACES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at/2.\n#show resolve/1."))
    return sorted(set(asp.atoms(model, "at")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((place, "bud") for place, bud in asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def asp_facts_only() -> str:
    import asp
    lines = [asp.fact("bud", "bud")]
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("humor", 1))
    lines.append(asp.fact("at", "orbital_greenhouse", "bud"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts_only()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous space adventure about a bud.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--crewmate", choices=CREW)
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
    name = args.name or rng.choice(NAMES)
    crewmate = args.crewmate or rng.choice([c for c in CREW if c != name])
    if name == crewmate:
        raise StoryError("The captain and crewmate must be different.")
    return StoryParams(place=place, name=name, crewmate=crewmate, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="orbital greenhouse", name="Milo", crewmate="Pip"),
    StoryParams(place="moon dock", name="Nova", crewmate="Juno"),
    StoryParams(place="comet cabin", name="Tia", crewmate="Cleo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show at/2.\n#show resolve/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story locations:")
        for place, _ in triples:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
