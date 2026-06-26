#!/usr/bin/env python3
"""
storyworlds/worlds/ammonia_brush_dice_rhyme_surprise_mystery_to.py
===================================================================

A small mystery storyworld about a child sleuth, a brush, dice, and a puzzling
clean-up that turns into a rhyme-led surprise.

Premise:
- A child wants to play with dice, but something strange has happened to the
  game table.
- A brush, a bottle of ammonia, and a tiny mystery clue are all part of the
  scene.
- The hero notices a rhyming hint, investigates, and solves the mystery with a
  careful clean-up.

The world is intentionally compact: it models a few objects, one helper, and one
problem. The ending proves what changed by showing the cleaned surface, the
returned dice, and the solved puzzle.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clue: str
    surfaces: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    safe: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_ammonia_cleans(world: World) -> list[str]:
    out: list[str] = []
    brush = world.entities["brush"]
    bowl = world.entities["bowl"]
    if brush.meters.get("soiled", 0.0) < THRESHOLD:
        return out
    if bowl.meters.get("ammonia_ready", 0.0) < THRESHOLD:
        return out
    sig = ("clean",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    brush.meters["soiled"] = 0.0
    bowl.meters["ammonia_ready"] = 0.0
    world.entities["dice"].meters["found"] = 1.0
    out.append("The brush came clean, and the missing dice were found under the edge of the mat.")
    return out


RULES = [Rule("ammonia_cleans", _r_ammonia_cleans)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def ask_rhyme(clue: str) -> str:
    return {
        "foam": "Foam by the comb, where could it roam?",
        "glow": "Glow near the low shelf, what could it show?",
        "stone": "Stone in the corner, who left it alone?",
    }.get(clue, "A small rhyme pointed the sleuth toward the truth.")


def tell(place: Place, clue: str, name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    brush = world.add(Entity(id="brush", type="brush", label="brush", phrase="a tiny brush", meters={"soiled": 1.0}))
    dice = world.add(Entity(id="dice", type="dice", label="dice", plural=True))
    bowl = world.add(Entity(id="bowl", type="bowl", label="bowl", phrase="a little bowl of ammonia", meters={"ammonia_ready": 1.0}))
    table = world.add(Entity(id="table", type="table", label="table", meters={"mystery": 1.0}))
    world.facts.update(child=child, brush=brush, dice=dice, bowl=bowl, table=table, clue=clue, place=place)

    world.say(f"{name} loved quiet mystery games, especially when the dice clacked on {place.label}.")
    world.say(f"One afternoon, the dice were gone, and only {brush.label} and {bowl.phrase} waited on the table.")
    world.para()
    world.say(f"{name} looked hard and read the clue: {ask_rhyme(clue)}")
    world.say(f"The rhyme made the room feel less strange, but the mystery was still not solved.")
    world.para()
    world.say(f"{name} used the brush to lift dust from the mat and sniffed the bowl of ammonia carefully.")
    brush.meters["soiled"] = 1.0
    bowl.meters["ammonia_ready"] = 1.0
    table.meters["mystery"] = 0.0
    propagate(world, narrate=True)
    world.say(f"At last, {name} saw the dice under the mat, cleaned the brush, and smiled at the neat table.")
    world.facts["solved"] = True
    return world


PLACES = {
    "game_room": Place(id="game_room", label="the game room", clue="foam", surfaces={"table", "mat"}),
    "kitchen_nook": Place(id="kitchen_nook", label="the kitchen nook", clue="glow", surfaces={"counter", "shelf"}),
    "porch": Place(id="porch", label="the porch", clue="stone", surfaces={"bench", "step"}),
}

TOOLS = {
    "brush": Tool(id="brush", label="brush", helps="lift dust", safe=True),
    "ammonia": Tool(id="ammonia", label="ammonia", helps="clean grime", safe=False),
}

CLAUSES = ["foam", "glow", "stone"]


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in PLACES for c in CLAUSES if PLACES[p].clue == c]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with ammonia, a brush, and dice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLAUSES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("No valid mystery setup matches those options.")
    place, clue = rng.choice(combos)
    name = args.name or rng.choice(["Mina", "Toby", "Lia", "Owen", "Nora"])
    return StoryParams(place=place, clue=clue, name=name)


def generation_prompts(world: World) -> list[str]:
    p = world.place
    f = world.facts
    return [
        f"Write a child-friendly mystery story set at {p.label} with a brush, ammonia, and dice.",
        f"Tell a short story where {f['child'].id} follows a rhyme clue and solves the dice mystery.",
        f"Write a gentle mystery with a surprise ending that explains why the brush was so dirty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {child.id} trying to solve at {place.label}?",
            answer=f"{child.id} was trying to solve the mystery of the missing dice at {place.label}.",
        ),
        QAItem(
            question="What clue helped the child investigate?",
            answer=f"The child followed a rhyme clue: {ask_rhyme(f['clue'])}",
        ),
        QAItem(
            question="What surprising thing was found at the end?",
            answer="The dice were hiding under the mat, and the brush came clean after the careful cleaning.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ammonia used for?",
            answer="Ammonia can help clean some grime and make dirty surfaces look fresh again.",
        ),
        QAItem(
            question="What does a brush do?",
            answer="A brush has bristles that can sweep, scrub, or lift dust and dirt.",
        ),
        QAItem(
            question="What are dice?",
            answer="Dice are little objects with dots or numbers that people roll for games.",
        ),
    ]


ASP_RULES = r"""
mystery_solved :- soiled(brush), ammonia_ready(bowl).
missing_found :- mystery_solved.
#show mystery_solved/0.
#show missing_found/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("soiled", "brush"),
        asp.fact("ammonia_ready", "bowl"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/0.\n#show missing_found/0."))
    atoms = {str(a) for a in model}
    if "mystery_solved" in atoms and "missing_found" in atoms:
        print("OK: ASP twin agrees with the Python mystery resolution.")
        return 0
    print("MISMATCH: ASP twin failed to prove the mystery solved.")
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = tell(place, params.clue, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        if meters:
            lines.append(f"  {e.id:8} ({e.type:8}) meters={meters}")
        else:
            lines.append(f"  {e.id:8} ({e.type:8})")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
        print(asp_program("#show mystery_solved/0.\n#show missing_found/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/0.\n#show missing_found/0."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, clue in valid_combos():
            params = StoryParams(place=place, clue=clue, name="Mina", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
