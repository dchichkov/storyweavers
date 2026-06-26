#!/usr/bin/env python3
"""
A standalone storyworld for a small space-adventure tale about arrogance,
a magical transformation, and teamwork.

The domain premise:
- A proud young captain rushes into a strange space mission.
- A magical force transforms something important about the captain.
- The crew must work together to fix the problem and land safely.
- The ending proves humility and teamwork changed the outcome.

This script is self-contained and follows the Storyweavers world contract.
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
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ShipPart:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    transformed: bool = False


@dataclass
class Transformation:
    id: str
    label: str
    from_state: str
    to_state: str
    trigger: str
    consequence: str


@dataclass
class Magic:
    id: str
    label: str
    source: str
    effect: str
    requires_team: bool = False


@dataclass
class CrewMove:
    id: str
    label: str
    actor_role: str
    verb: str
    result: str


@dataclass
class Setting:
    place: str = "the starport"
    backdrop: str = "a ring of bright stars"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    parts: dict[str, ShipPart] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_part(self, part: ShipPart) -> ShipPart:
        self.parts[part.id] = part
        return part

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "starport": Setting(place="the starport", backdrop="a lane of blinking dock lights"),
    "moonbase": Setting(place="the moonbase", backdrop="a field of silver dust and glass domes"),
    "asteroid": Setting(place="the asteroid outpost", backdrop="a canyon of rock lit by ship lamps"),
}

TRANSFORMATIONS = {
    "tiny": Transformation(
        id="tiny",
        label="tiny",
        from_state="too big for the tunnel",
        to_state="small enough to fit",
        trigger="the magic pulse",
        consequence="she could slip through the narrow hatch",
    ),
    "glow": Transformation(
        id="glow",
        label="glow",
        from_state="hard to see in the dark",
        to_state="bright enough to guide the ship",
        trigger="the magic spark",
        consequence="the crew could follow the shining trail home",
    ),
    "float": Transformation(
        id="float",
        label="float",
        from_state="stuck near the broken panel",
        to_state="light enough to reach the controls",
        trigger="the magic wind",
        consequence="the repair could happen in zero gravity",
    ),
}

MAGICS = {
    "comet": Magic(
        id="comet",
        label="comet magic",
        source="a falling comet shard",
        effect="changed a proud captain into a smaller, kinder helper",
        requires_team=True,
    ),
    "luna": Magic(
        id="luna",
        label="luna magic",
        source="moon dust",
        effect="made one part of the ship glow like a tiny lantern",
        requires_team=False,
    ),
    "spark": Magic(
        id="spark",
        label="starlight magic",
        source="a bright star crystal",
        effect="lifted heavy things just enough to fix them",
        requires_team=True,
    ),
}

TEAMWORK_MOVES = {
    "guide": CrewMove(
        id="guide",
        label="guide the way",
        actor_role="navigator",
        verb="pointed out the safe path",
        result="the captain could move without getting lost",
    ),
    "hold": CrewMove(
        id="hold",
        label="hold the panel",
        actor_role="engineer",
        verb="held the broken panel steady",
        result="the magic could reach the wires cleanly",
    ),
    "carry": CrewMove(
        id="carry",
        label="carry the tools",
        actor_role="robot",
        verb="carried the toolkit across the deck",
        result="everyone had what they needed at the right moment",
    ),
}

GLOVES = ShipPart(
    id="gloves",
    label="gloves",
    phrase="a pair of shiny pilot gloves",
)
HELMET = ShipPart(
    id="helmet",
    label="helmet",
    phrase="a round silver helmet",
    fragile=False,
)
BADGE = ShipPart(
    id="badge",
    label="badge",
    phrase="a polished captain badge",
    fragile=True,
)

SPACE_NOISE = [
    "The engines hummed softly.",
    "Tiny lights blinked across the control room.",
    "A calm beep drifted through the cabin.",
]

NAMES = ["Nova", "Iris", "Pip", "Mira", "Jett", "Sol", "Orin", "Luna"]
CREW_ROLES = ["captain", "navigator", "engineer", "robot"]
CREW_TRAITS = ["proud", "brave", "careful", "quick", "clever", "stubborn"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    transformation: str
    magic: str
    teamwork: str
    name: str
    crewmate: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="captain", label=params.name))
    crew = world.add(Entity(id=params.crewmate, kind="character", type="crew", label=params.crewmate))
    badge = world.add_part(BADGE)
    gloves = world.add_part(GLOVES)
    helmet = world.add_part(HELMET)

    world.facts.update(
        hero=hero,
        crew=crew,
        badge=badge,
        gloves=gloves,
        helmet=helmet,
        transformation=TRANSFORMATIONS[params.transformation],
        magic=MAGICS[params.magic],
        teamwork=TEAMWORK_MOVES[params.teamwork],
        setting=world.setting,
    )
    return world


def narrate(world: World, params: StoryParams) -> None:
    hero: Entity = world.facts["hero"]
    crew: Entity = world.facts["crew"]
    tf: Transformation = world.facts["transformation"]
    mg: Magic = world.facts["magic"]
    mv: CrewMove = world.facts["teamwork"]
    badge: ShipPart = world.facts["badge"]

    hero.meme["arrogance"] = 1.0
    hero.meme["confidence"] = 1.0
    world.say(
        f"{hero.id} was a {params.trait} young captain at {world.setting.place}, "
        f"and {hero.pronoun('subject')} thought {hero.pronoun('subject')} could do everything alone."
    )
    world.say(f"{SPACE_NOISE[0]} {SPACE_NOISE[1]} {hero.id} wore {badge.phrase} and smiled too proudly at the crew.")
    world.say(
        f"Then a strange {mg.source} flashed near the airlock, and {mg.label} changed {hero.id} so {hero.pronoun('subject')} became {tf.to_state}."
    )
    hero.meter["small"] = 1.0
    hero.meme["arrogance"] = 0.0
    hero.meme["surprise"] = 1.0
    world.para()
    world.say(
        f"That was a problem, because {tf.consequence}, but the ship still needed a careful landing."
    )
    crew.meme["teamwork"] = 1.0
    world.say(
        f"{crew.id} did not laugh. Instead, {crew.pronoun('subject')} {mv.verb}, and together they kept the ship steady."
    )
    world.say(
        f"The {mg.label} needed teamwork, so the crew split the jobs: one held the panel, one guided the route, and one carried the tools."
    )
    world.para()
    hero.meme["humility"] = 1.0
    hero.meme["joy"] = 1.0
    hero.meter["safe"] = 1.0
    badge.transformed = True
    world.say(
        f"At last, {hero.id} thanked the crew and asked for help in a small voice. "
        f"The magic faded, {hero.pronoun('subject')} was back to normal size, and the ship landed safely under {world.setting.backdrop}."
    )
    world.say(
        f"By the end, {hero.id} kept the shiny badge, but now {hero.pronoun('subject')} knew that teamwork made space travel safer than arrogance ever could."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    tf: Transformation = f["transformation"]
    mg: Magic = f["magic"]
    return [
        f'Write a child-friendly space adventure story about arrogance, magic, and teamwork featuring {hero.id}.',
        f"Tell a short story where {hero.id} is too proud, then a {mg.label} spell causes a {tf.label} transformation and the crew must work together.",
        f"Create a gentle spaceship story that ends with humility and a safe landing at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    crew: Entity = f["crew"]
    tf: Transformation = f["transformation"]
    mg: Magic = f["magic"]
    mv: CrewMove = f["teamwork"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a proud captain who learned to work with the crew.",
        ),
        QAItem(
            question=f"What magical thing happened to {hero.id}?",
            answer=f"{mg.label.capitalize()} changed {hero.id} so {hero.pronoun('subject')} became {tf.to_state}.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"{crew.id} and the others used teamwork. One {mv.verb.lower()}, and that helped the ship stay safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} thanking the crew, feeling humble, and landing safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that can make strange and wonderful things happen in a story.",
        ),
        QAItem(
            question="What does arrogance mean?",
            answer="Arrogance means acting as if you are better than everyone else and do not need help.",
        ),
        QAItem(
            question="Why do spaceships need crews?",
            answer="Spaceships need crews because one person cannot watch everything, fix every problem, and steer safely at the same time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero_proud(H) :- proud(H).
transforms(H,T) :- transformation(T), hero(H), magic_used(H,M), magic_transforms(M,T).
teamwork_needed(H) :- transforms(H,_), arrogance(H).
safe_landing(H) :- teamwork(H), teamwork_needed(H), crew_helped(H).
valid_story(P, T, M, W) :- place(P), transformation(T), magic(M), teamwork(W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for wid in TEAMWORK_MOVES:
        lines.append(asp.fact("teamwork", wid))
    for mid, mg in MAGICS.items():
        lines.append(asp.fact("magic_transforms", mid, "tiny" if mid == "comet" else "glow" if mid == "luna" else "float"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = asp_valid_combos()
    python_combos = [
        (p, t, m, w)
        for p in SETTINGS
        for t in TRANSFORMATIONS
        for m in MAGICS
        for w in TEAMWORK_MOVES
    ]
    s1, s2 = set(combos), set(python_combos)
    if s1 == s2:
        print(f"OK: clingo gate matches Python registries ({len(s1)} combos).")
        return 0
    print("MISMATCH between clingo and Python registries.")
    return 1


# ---------------------------------------------------------------------------
# Parameter helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about arrogance, magic, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--teamwork", choices=TEAMWORK_MOVES)
    ap.add_argument("--name")
    ap.add_argument("--crewmate")
    ap.add_argument("--trait", choices=CREW_TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    magic = args.magic or rng.choice(list(MAGICS))
    teamwork = args.teamwork or rng.choice(list(TEAMWORK_MOVES))
    name = args.name or rng.choice(NAMES)
    crewmate = args.crewmate or rng.choice(["Rin", "Tao", "Bea", "Zed", "Moss"])
    trait = args.trait or rng.choice(CREW_TRAITS)
    return StoryParams(place=place, transformation=transformation, magic=magic, teamwork=teamwork, name=name, crewmate=crewmate, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meme={dict(e.meme)} meter={dict(e.meter)}")
    for p in world.parts.values():
        lines.append(f"{p.id}: transformed={p.transformed}")
    return "\n".join(lines)


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
    StoryParams(place="starport", transformation="tiny", magic="comet", teamwork="guide", name="Nova", crewmate="Rin", trait="proud"),
    StoryParams(place="moonbase", transformation="glow", magic="luna", teamwork="hold", name="Iris", crewmate="Bea", trait="stubborn"),
    StoryParams(place="asteroid", transformation="float", magic="spark", teamwork="carry", name="Pip", crewmate="Tao", trait="quick"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
