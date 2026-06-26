#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trim_gerund_dialogue_problem_solving_rhyme_rhyming.py
=============================================================================================================

A tiny rhyming storyworld about a child, a trim, and a careful problem solved
through dialogue. The world stays small on purpose: one helper, one problem,
one fix, and a gentle ending with a neat new shape.

Seed tale used to build the world model:
---
Mina loved helping in the garden. One breezy day, she noticed the bean vine was
too wild and long. Her grandma handed her small scissors and said, "We trim
carefully, not quickly." Mina tried to trim the vine, but a tangled loop kept
snagging on the trellis. She and Grandma talked it through, loosened the loop,
and trimmed only the extra bits. At the end, the vine looked tidy, and Mina
smiled because the garden was neat again.

World model idea:
---
The key state is a hanging stem or ribbon-like thing with extra length. The
hero wants to trim it, but there is a snag, kink, or tangle. Dialogue helps the
adult and child choose a safer, smaller cut. The final image proves the change:
the plant, ribbon, or fringe is tidy; the hero is proud; and the adult is
relieved.

Narrative instruments:
---
- Dialogue
- Problem Solving
- Rhyme
- Rhyming Story style
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


RHYME_PAIRS = [
    ("neat", "street"),
    ("line", "shine"),
    ("tame", "same"),
    ("tide", "hide"),
    ("sprout", "about"),
    ("snip", "tip"),
    ("trim", "grin"),
    ("snag", "tag"),
    ("glow", "show"),
    ("bend", "friend"),
]

NAMES = ["Mina", "Luna", "Milo", "Nora", "June", "Theo", "Pia", "Owen"]
HELPERS = ["Grandma", "Grandpa", "Mom", "Dad", "Auntie", "Uncle"]
PLACES = ["garden", "backyard", "porch", "patio", "greenhouse"]
OBJECTS = [
    ("bean vine", "bean vine", "plant"),
    ("paper fringe", "paper fringe", "decoration"),
    ("ribbon", "ribbon", "decoration"),
    ("herb sprig", "herb sprig", "plant"),
]
PROBLEMS = [
    ("a tangled loop", "snagged", "snag", "loop"),
    ("a wild curl", "hooked", "kink", "curl"),
    ("a long extra tail", "flapped", "flap", "tail"),
    ("a twisty knot", "caught", "tangle", "knot"),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    target: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the garden"


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    kind: str
    can_trim: bool = True
    can_tangle: bool = True
    can_use_dialogue: bool = True


@dataclass
class StoryParams:
    place: str
    object_id: str
    problem_id: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


OBJECTS_REGISTRY = {
    "bean": ObjectDef("bean", "bean vine", "a bean vine with a long green stem", "plant"),
    "fringe": ObjectDef("fringe", "paper fringe", "a paper fringe with tiny hanging strips", "decoration"),
    "ribbon": ObjectDef("ribbon", "ribbon", "a ribbon with a silky tail", "decoration"),
    "herb": ObjectDef("herb", "herb sprig", "a herb sprig with one extra wild stem", "plant"),
}

PROBLEMS_REGISTRY = {
    "loop": {
        "label": "a tangled loop",
        "verb": "snagged",
        "noun": "loop",
        "fix": "loosen the loop first",
    },
    "kink": {
        "label": "a wild curl",
        "verb": "hooked",
        "noun": "curl",
        "fix": "smooth the curl first",
    },
    "tail": {
        "label": "a long extra tail",
        "verb": "flapped",
        "noun": "tail",
        "fix": "pin the tail back first",
    },
    "knot": {
        "label": "a twisty knot",
        "verb": "caught",
        "noun": "knot",
        "fix": "unwind the knot first",
    },
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming trim-and-fix story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS_REGISTRY)
    ap.add_argument("--problem", dest="problem_id", choices=PROBLEMS_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def pick_rhyme(seed: int) -> tuple[str, str]:
    rng = random.Random(seed)
    return rng.choice(RHYME_PAIRS)


def valid_combo(place: str, object_id: str, problem_id: str) -> bool:
    return object_id in OBJECTS_REGISTRY and problem_id in PROBLEMS_REGISTRY and place in PLACES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, o, pr) for p in PLACES for o in OBJECTS_REGISTRY for pr in PROBLEMS_REGISTRY if valid_combo(p, o, pr)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    object_id = args.object_id or rng.choice(list(OBJECTS_REGISTRY))
    problem_id = args.problem_id or rng.choice(list(PROBLEMS_REGISTRY))
    if not valid_combo(place, object_id, problem_id):
        raise StoryError("No valid story matches those options.")
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, object_id=object_id, problem_id=problem_id, name=name, helper=helper)


def is_reasonable(params: StoryParams) -> bool:
    obj = OBJECTS_REGISTRY[params.object_id]
    prob = PROBLEMS_REGISTRY[params.problem_id]
    return obj.can_trim and obj.can_tangle and obj.can_use_dialogue and bool(prob["fix"])


ASP_RULES = r"""
place(garden;backyard;porch;patio;greenhouse).
object(bean;fringe;ribbon;herb).
problem(loop;kink;tail;knot).

reasonable(P,O,R) :- place(P), object(O), problem(R).
#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS_REGISTRY:
        lines.append(asp.fact("object", o))
    for r in PROBLEMS_REGISTRY:
        lines.append(asp.fact("problem", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def _line_with_rhyme(base: str, rhyme_a: str, rhyme_b: str) -> str:
    return f"{base} {rhyme_a}, {rhyme_b}."


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed or 0)
    world = World(Setting(place=f"the {params.place}"))
    obj = OBJECTS_REGISTRY[params.object_id]
    prob = PROBLEMS_REGISTRY[params.problem_id]
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name, memes={"pride": 0.0, "worry": 0.0, "joy": 0.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper, memes={"calm": 0.0, "joy": 0.0}))
    thing = world.add(Entity(id="thing", kind="thing", type=obj.kind, label=obj.label, phrase=obj.phrase, owner=hero.id, caretaker=helper.id, target=True, meters={"trim_need": 1.0, "snag": 1.0 if params.problem_id == "loop" else 0.0, "kink": 1.0 if params.problem_id == "kink" else 0.0, "tangle": 1.0 if params.problem_id == "knot" else 0.0}))
    world.facts.update(hero=hero, helper=helper, thing=thing, obj=obj, prob=prob, params=params)
    a, b = pick_rhyme(params.seed or 1)

    world.say(f"{hero.id} was helping at {world.setting.place}.")
    world.say(f"{hero.id} looked at {thing.phrase} and said, \"It needs a trim, and I can do it!\"")
    world.say(f"{helper.id} smiled and said, \"Trim with care, nice and slow; we do not want a messy show.\"")
    world.say(_line_with_rhyme(f"The {thing.label} had", a, b))
    world.para()
    world.say(f"{hero.id} picked up the small scissors and whispered, \"Snip the tip, not the whole big ship.\"")
    world.say(f"But {prob['label']} {prob['verb']} the stem, so the cut could not begin.")
    world.say(f"\"What should we do?\" asked {hero.id}. \"We can solve it,\" said {helper.id}, \"with a gentle little trim.\"")
    world.say(f"They worked together to {prob['fix']}, then kept the rest still and slim.")
    world.para()
    hero.memes["worry"] += 1.0
    hero.memes["joy"] += 1.0
    helper.memes["calm"] += 1.0
    thing.meters["trim_need"] = 0.0
    thing.meters["snag"] = 0.0
    thing.meters["kink"] = 0.0
    thing.meters["tangle"] = 0.0
    world.say(f"\"Now snip the tip,\" said {helper.id}, \"and let the tidy part just glow.\"")
    world.say(f"{hero.id} trimmed the extra bit, and the {thing.label} looked neat in a row.")
    world.say(f"{hero.id} grinned and said, \"A small fix works best when we take it slow.\"")
    world.say(f"{helper.id} laughed, \"Right, my dear; that is the way to let a good thing show.\"")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    obj = f["obj"].label
    place = f["params"].place
    return [
        f'Write a short rhyming story for a child named {hero} and {helper} about trimming a {obj} at the {place}.',
        f'Create a gentle dialogue story where {hero} solves a trimming problem with {helper} and the ending rhymes.',
        f'Write a problem-solving rhyme about a small trim, a snag, and a happy tidy finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    thing = f["thing"]
    obj = f["obj"]
    prob = f["prob"]
    place = f["params"].place
    return [
        QAItem(
            question=f"What was {hero.id} helping with at the {place}?",
            answer=f"{hero.id} was helping trim {thing.phrase} at the {place}.",
        ),
        QAItem(
            question=f"What problem kept the trim from starting right away?",
            answer=f"A {prob['label']} kept getting in the way, so {hero.id} and {helper.id} had to solve that first.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They used calm dialogue and careful problem solving to {prob['fix']} before trimming the extra bit.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{thing.label.capitalize()} looked neat and tidy at the end, and {hero.id} felt proud.",
        ),
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a rhyming story with dialogue and a small problem that gets solved carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does trim mean?", answer="To trim means to cut away a little extra part so something looks neat."),
        QAItem(question="Why is it good to go slowly when cutting?", answer="Going slowly helps keep the cut safe and neat, so you only trim what you mean to trim."),
        QAItem(question="What is a snag?", answer="A snag is something that catches or gets in the way, like a loop or a knot."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="garden", object_id="bean", problem_id="loop", name="Mina", helper="Grandma"),
    StoryParams(place="backyard", object_id="ribbon", problem_id="tail", name="Luna", helper="Mom"),
    StoryParams(place="porch", object_id="fringe", problem_id="knot", name="Milo", helper="Dad"),
    StoryParams(place="greenhouse", object_id="herb", problem_id="kink", name="Nora", helper="Auntie"),
]


def build_asp_full() -> str:
    return asp_program("#show reasonable/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_full())
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
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: trim {p.object_id} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
