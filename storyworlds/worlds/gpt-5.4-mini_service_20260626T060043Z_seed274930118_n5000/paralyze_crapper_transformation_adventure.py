#!/usr/bin/env python3
"""
Standalone storyworld: a little adventure, a troublesome transformation, and a
careful rescue plan.

Premise:
- A curious child goes on a small adventure with a beloved helper or prize.
- A magical mishap can transform something important into an awkward state.
- The hero wants to keep going, but the parent or helper warns that the risky
  path will leave the prize stuck, helpless, or unusable.
- A compatible tool or action reverses the trouble and ends the adventure well.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["weight", "stuck", "shiny", "tainted", "broken", "mess", "heat"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "courage", "worry", "hope", "conflict", "relief", "curiosity"]:
            self.memes.setdefault(k, 0.0)

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
    name: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    verb: str
    gerund: str
    trouble: str
    risk: str
    affected_region: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    restores: set[str]
    protects: set[str]
    covers: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


def _pron_name(name: str) -> str:
    return name


def story_pronoun(entity: Entity) -> str:
    return entity.pronoun("subject")


def object_pronoun(entity: Entity) -> str:
    return entity.pronoun("object")


def possessive_pronoun(entity: Entity) -> str:
    return entity.pronoun("possessive")


def transform_target(world: World, hero: Entity, trans: Transformation) -> None:
    hero.meters["stuck"] += 1
    hero.memes["worry"] += 1
    world.zone = {trans.affected_region}
    world.say(
        f"As the path grew stranger, {hero.id} felt a strange tug in {possessive_pronoun(hero)} steps."
    )
    world.say(
        f"Then the magic of the place made {object_pronoun(hero)} nearly paralyzed, as if {trans.trouble} had wrapped around the adventure."
    )


def predict_trouble(world: World, hero: Entity, prize: Entity, trans: Transformation) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["stuck"] += 1
    sim.get(prize.id).meters["tainted"] += 1
    sim.get(prize.id).meters["broken"] += 1
    return {
        "stuck": sim.get(hero.id).meters["stuck"] >= THRESHOLD,
        "tainted": sim.get(prize.id).meters["tainted"] >= THRESHOLD,
    }


def can_repair(trans: Transformation, tool: Tool, prize: Entity) -> bool:
    return trans.tag in tool.restores and prize.type in tool.protects or prize.label in tool.protects


def choose_tool(trans: Transformation, prize: Entity) -> Optional[Tool]:
    for tool in TOOLS:
        if can_repair(trans, tool, prize):
            return tool
    return None


def discover(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a curious little {hero.type} who loved adventure, maps, and the idea of finding hidden paths."
    )
    world.say(
        f"With {helper.id} beside {object_pronoun(hero)}, {hero.id} carried {possessive_pronoun(hero)} {prize.label} like it was a treasure from a brave quest."
    )


def travel(world: World, hero: Entity, helper: Entity, trans: Transformation, prize: Entity) -> None:
    world.para()
    world.say(
        f"One day, {hero.id} and {helper.id} went to {world.place.name}, where the stones shimmered and the air felt full of secrets."
    )
    world.say(
        f"{hero.id} wanted to {trans.verb}, because {trans.gerund} sounded like the fastest way to see what waited ahead."
    )
    if predict_trouble(world, hero, prize, trans)["stuck"]:
        world.say(
            f"But {helper.id} warned that if they rushed forward, the magic could leave {object_pronoun(hero)} stuck and make {possessive_pronoun(hero)} {prize.label} {trans.risk}."
        )


def cause_transformation(world: World, hero: Entity, prize: Entity, trans: Transformation) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["stuck"] += 1
    prize.meters["tainted"] += 1
    prize.meters["broken"] += 1
    world.say(
        f"{hero.id} still crept toward the odd place, and the adventure suddenly turned into a transformation."
    )
    world.say(
        f"{possessive_pronoun(hero).capitalize()} feet slowed to a crawl, almost paralyzed by the spell, while {possessive_pronoun(hero)} {prize.label} became {trans.risk}."
    )


def offer_fix(world: World, helper: Entity, hero: Entity, prize: Entity, trans: Transformation) -> Optional[Tool]:
    tool = choose_tool(trans, prize)
    if tool is None:
        return None
    world.say(
        f"{helper.id} knelt down and held up {tool.phrase}, saying it could help them undo the trouble."
    )
    return tool


def accept_fix(world: World, hero: Entity, helper: Entity, prize: Entity, tool: Tool, trans: Transformation) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.meters["stuck"] = 0.0
    prize.meters["tainted"] = 0.0
    prize.meters["broken"] = 0.0
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} smiled and took {tool.phrase}, and the two of them used it carefully."
    )
    world.say(
        f"Little by little, the spell loosened, {possessive_pronoun(hero)} steps were free again, and {possessive_pronoun(hero)} {prize.label} was safe."
    )
    world.say(
        f"In the end, {hero.id} kept the adventure, but the scary transformation was gone."
    )


def tell(place: Place, trans: Transformation, prize_cfg: Entity,
         hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Tavi", helper_type: str = "boy") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    prize.worn_by = hero.id

    discover(world, hero, helper, prize)
    travel(world, hero, helper, trans, prize)
    world.para()
    cause_transformation(world, hero, prize, trans)
    tool = offer_fix(world, helper, hero, prize, trans)
    if tool:
        accept_fix(world, hero, helper, prize, tool, trans)

    world.facts.update(hero=hero, helper=helper, prize=prize, trans=trans, tool=tool, place=place)
    return world


PLACES = {
    "old_bridge": Place("the old bridge", outdoors=True, affords={"crossing", "searching"}),
    "cave_path": Place("the cave path", outdoors=False, affords={"searching", "careful_walking"}),
    "forest_trail": Place("the forest trail", outdoors=True, affords={"crossing", "searching"}),
}

TRANSFORMATIONS = {
    "paralyze": Transformation(
        id="paralyze",
        verb="cross the glowing stones",
        gerund="crossing the glowing stones",
        trouble="paralysis",
        risk="stiff and stuck",
        affected_region="legs",
        tag="paralyze",
    ),
    "crapper": Transformation(
        id="crapper",
        verb="open the rusty door",
        gerund="opening the rusty door",
        trouble="a crapper-clang of bad luck",
        risk="muddy and smelly",
        affected_region="hands",
        tag="crapper",
    ),
    "transformation": Transformation(
        id="transformation",
        verb="follow the secret trail",
        gerund="following the secret trail",
        trouble="a sudden transformation",
        risk="shiny but wrong",
        affected_region="torso",
        tag="transformation",
    ),
}

TOOLS = [
    Tool(
        id="warm_blanket",
        label="warm blanket",
        phrase="a warm blanket",
        restores={"paralyze"},
        protects={"prize", "cloak"},
        covers={"legs", "torso"},
    ),
    Tool(
        id="soap_brush",
        label="soap brush",
        phrase="a soap brush",
        restores={"crapper"},
        protects={"prize", "boots", "gloves"},
        covers={"hands", "feet"},
    ),
    Tool(
        id="silver_key",
        label="silver key",
        phrase="a silver key",
        restores={"transformation"},
        protects={"prize", "amulet"},
        covers={"torso"},
    ),
]

PRIZES = {
    "cloak": Entity(id="cloak", type="cloak", label="cloak", phrase="a bright travel cloak"),
    "boots": Entity(id="boots", type="boots", label="boots", phrase="a pair of sturdy boots", plural=True),
    "amulet": Entity(id="amulet", type="amulet", label="amulet", phrase="a small silver amulet"),
}

PEOPLE = ["Mina", "Tavi", "Lumi", "Niko", "Iris", "Oren"]
TYPES = {"Mina": "girl", "Tavi": "boy", "Lumi": "girl", "Niko": "boy", "Iris": "girl", "Oren": "boy"}


@dataclass
class StoryParams:
    place: str
    transformation: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, trans in TRANSFORMATIONS.items():
            for prid, prize in PRIZES.items():
                if choose_tool(trans, prize) is not None and tid in {"paralyze", "crapper", "transformation"}:
                    if pid in PLACES:
                        combos.append((pid, tid, prid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a small child involving {f['trans'].id}, a hidden danger, and a kind helper.",
        f"Tell a child-facing adventure where {f['hero'].id} wants to {f['trans'].verb} but a transformation makes trouble.",
        f"Write a simple story with the word '{f['trans'].id}' that ends with a safe rescue and a happy adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    trans: Transformation = f["trans"]
    tool: Optional[Tool] = f["tool"]
    qa = [
        QAItem(
            question=f"Who went on the adventure in {world.place.name}?",
            answer=f"{hero.id} went there with {helper.id}, carrying {possessive_pronoun(hero)} {prize.label} for the journey.",
        ),
        QAItem(
            question=f"What problem did the transformation cause for {hero.id}?",
            answer=f"It made {hero.id} nearly paralyzed and left {possessive_pronoun(hero)} {prize.label} {trans.risk}.",
        ),
        QAItem(
            question=f"Who helped fix the trouble?",
            answer=f"{helper.id} helped by bringing {tool.phrase if tool else 'the right tool'} and staying calm.",
        ),
    ]
    if tool:
        qa.append(QAItem(
            question=f"How did the safe ending happen?",
            answer=f"They used {tool.phrase} carefully, so the transformation loosened and the adventure could continue safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    trans: Transformation = f["trans"]
    out = [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change, when one thing becomes different from what it was before.",
        ),
        QAItem(
            question="What does paralyze mean?",
            answer="To paralyze something means to make it unable to move normally.",
        ),
        QAItem(
            question="What is a crapper?",
            answer="A crapper is an old-fashioned word for a toilet or an outhouse.",
        ),
    ]
    if trans.id == "paralyze":
        out.append(QAItem(
            question="Why can a paralyze spell be scary in a story?",
            answer="It can be scary because it makes someone stuck and unable to move when they need to keep going.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
transformation(T) :- trans(T).
prize(P) :- prize_item(P).

compatible(P, T, R) :- place(P), transformation(T), prize(R), fix(T, R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("trans", tid))
    for rid in PRIZES:
        lines.append(asp.fact("prize_item", rid))
    for t in TOOLS:
        lines.append(asp.fact("fix", t.restores.pop() if t.restores else "none", "prize"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with transformation trouble.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=PEOPLE)
    ap.add_argument("--helper", choices=PEOPLE)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid adventure combinations exist.")
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, trans, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(PEOPLE)
    helper_choices = [p for p in PEOPLE if p != hero]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(place=place, transformation=trans, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TRANSFORMATIONS[params.transformation],
        PRIZES[params.prize],
        hero_name=params.hero,
        hero_type=TYPES[params.hero],
        helper_name=params.helper,
        helper_type=TYPES[params.helper],
    )
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this storyworld uses a simple compatibility gate.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, trans, prize in [
            ("old_bridge", "paralyze", "cloak"),
            ("forest_trail", "crapper", "boots"),
            ("cave_path", "transformation", "amulet"),
        ]:
            params = StoryParams(place=place, transformation=trans, prize=prize, hero="Mina", helper="Tavi")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
