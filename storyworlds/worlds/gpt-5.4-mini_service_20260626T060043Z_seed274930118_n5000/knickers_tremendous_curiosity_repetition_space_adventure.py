#!/usr/bin/env python3
"""
Storyworld: a tiny space adventure about curiosity, repetition, and a
tremendous pair of knickers.

The seed tale premise:
- A small space kid is fascinated by a tremendous pair of knickers in a ship
  locker.
- Curiosity makes them keep asking about it and reaching for it.
- Repetition builds a problem: they keep trying the wrong thing again.
- A helper offers a sensible space-safe plan, and the child learns a better way.

This script simulates that small world, narrates from state changes, and exposes
grounded Q&A plus an ASP twin for the reasonableness gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    deck: str
    storage: str
    exterior: str


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    risky: str = "stuck"
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    safe_action: str
    supports: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        import copy as _copy

        c = World(self.ship)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


THRESHOLD = 1.0


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SHIP = Ship(
    name="the Star Lantern",
    place="the Star Lantern",
    deck="main deck",
    storage="locker bay",
    exterior="star window",
)

PLACES = {
    "ship": SHIP,
}

PRIZES = {
    "knickers": Prize(
        label="knickers",
        phrase="a tremendous pair of knickers",
        region="hips",
        plural=True,
        risky="tangled",
        genders={"girl", "boy"},
    )
}

TOOLS = [
    Tool(
        id="fold",
        label="folding board",
        prep="set the knickers on a folding board first",
        tail="folded the knickers neatly and put them back in the locker",
        safe_action="fold",
        supports={"knickers"},
    ),
    Tool(
        id="tag",
        label="label tag",
        prep="add a label tag to the locker",
        tail="tagged the locker so the right thing could be found quickly",
        safe_action="label",
        supports={"knickers"},
    ),
]

NAMES_GIRL = ["Mina", "Tess", "Lia", "Nora"]
NAMES_BOY = ["Pip", "Jules", "Ari", "Cato"]


def _do_curiosity(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    child.memes["repeat"] = child.memes.get("repeat", 0.0) + 1.0
    child.meters["reach"] = child.meters.get("reach", 0.0) + 1.0


def _predicted_mess(world: World, child: Entity, prize: Entity) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    _do_curiosity(sim, sim_child)
    if sim_child.meters.get("reach", 0.0) >= THRESHOLD and not sim_child.memes.get("guided", 0.0):
        prize.meters["tangled"] = prize.meters.get("tangled", 0.0) + 1.0
        child_mess = True
    else:
        child_mess = False
    return {"tangled": child_mess}


def _choose_tool(prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if prize.label in tool.supports:
            return tool
    return None


def tell(name: str, gender: str, parent: str) -> World:
    world = World(SHIP)
    child_type = gender
    hero = world.add(Entity(id=name, kind="character", type=child_type, meters={}, memes={"curiosity": 0.0, "repeat": 0.0}))
    parent_ent = world.add(Entity(id="Parent", kind="character", type=parent, label="the parent", meters={}, memes={}))

    prize = world.add(Entity(
        id="knickers",
        type="knickers",
        label="knickers",
        phrase="a tremendous pair of knickers",
        owner=hero.id,
        caretaker=parent_ent.id,
        plural=True,
    ))

    world.say(
        f"On the Star Lantern, {hero.id} was a small space kid with a big, curious heart."
    )
    world.say(
        f"In the locker bay sat {prize.phrase}, and {hero.id} thought it looked tremendous."
    )

    world.para()
    world.say(
        f"{hero.id} kept asking about the knickers again and again, because curiosity made the question feel shiny."
    )
    _do_curiosity(world, hero)
    _do_curiosity(world, hero)
    world.say(
        f"{hero.id} reached for them once, then reached again, as if repeating the same move might unlock a secret."
    )

    pred = _predicted_mess(world, hero, prize)
    if pred["tangled"]:
        world.say(
            f'"If you pull at them like that, they could get tangled," {parent_ent.pronoun("subject")} said.'
        )
        world.say(
            f'{hero.id} paused, but the wish to touch the tremendous knickers was still there.'
        )

    world.para()
    hero.memes["guided"] = 1.0
    tool = _choose_tool(PRIZES["knickers"])
    if tool is None:
        raise StoryError("No safe tool fits this space story.")
    world.say(
        f'{parent_ent.pronoun("possessive").capitalize()} parent smiled and said, "{tool.prep}."'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} nodded, because this time the answer was better than the repeated tugging."
    )
    world.say(
        f"Together they used the {tool.label}, and soon {tool.tail}."
    )

    world.facts.update(
        hero=hero,
        parent=parent_ent,
        prize=prize,
        tool=tool,
        ship=SHIP,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short space adventure for a young child about {hero.id}, curiosity, and a tremendous pair of knickers.',
        f"Tell a gentle story where {hero.id} keeps asking about something in a ship locker until a wiser helper offers a safer way.",
        f"Write a tiny story set on a spaceship that uses the words 'curiosity', 'repetition', and 'tremendous'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} keep noticing in the locker bay?",
            answer=f"{hero.id} kept noticing {prize.phrase}. It looked tremendous and made {hero.id} feel curious.",
        ),
        QAItem(
            question=f"Why did the parent worry when {hero.id} kept tugging again and again?",
            answer=f"The parent worried because repeating the same tug could make the knickers tangled in the locker bay.",
        ),
        QAItem(
            question=f"What safer plan helped {hero.id} with the knickers?",
            answer=f"They used the {tool.label}, so {hero.id} could handle the knickers carefully instead of pulling at them.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm, because curiosity got a kind answer and the tremendous knickers were handled safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, or ask another question.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing again and again.",
        ),
        QAItem(
            question="What is a spaceship for?",
            answer="A spaceship is a vehicle that carries people through space.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("prize", "knickers"))
    lines.append(asp.fact("tool", "fold"))
    lines.append(asp.fact("tool", "tag"))
    lines.append(asp.fact("at_risk", "knickers"))
    lines.append(asp.fact("safe_for", "fold", "knickers"))
    lines.append(asp.fact("safe_for", "tag", "knickers"))
    lines.append(asp.fact("feature", "curiosity"))
    lines.append(asp.fact("feature", "repetition"))
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice(T, P) :- tool(T), prize(P), safe_for(T, P).
valid_story :- at_risk(P), safe_choice(T, P), feature(curiosity), feature(repetition).
#show valid_story/0.
#show safe_choice/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0.\n#show safe_choice/2."))
    return any(sym.name == "valid_story" for sym in model)


def asp_verify() -> int:
    ok = asp_valid()
    if ok:
        print("OK: ASP gate agrees that the story is reasonable.")
        return 0
    print("MISMATCH: ASP gate failed to derive a valid story.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with curiosity and repetition.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place="ship", name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/0.\n#show safe_choice/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0.\n#show safe_choice/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(place="ship", name="Mina", gender="girl", parent="mother"),
            StoryParams(place="ship", name="Pip", gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
