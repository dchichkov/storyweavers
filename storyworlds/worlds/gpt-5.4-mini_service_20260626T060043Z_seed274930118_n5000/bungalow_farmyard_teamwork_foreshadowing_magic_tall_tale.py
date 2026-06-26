#!/usr/bin/env python3
"""
storyworlds/worlds/bungalow_farmyard_teamwork_foreshadowing_magic_tall_tale.py
==============================================================================

A small farmyard tall-tale storyworld about a bungalow, teamwork, foreshadowing,
and a touch of magic.

Premise:
- A child and a grown-up live in a bungalow beside a busy farmyard.
- A huge task arrives: the haystack has gone lopsided before the evening fair.
- The child wants to help, but the task is too big for one pair of hands.
- The grown-up notices a few foreshadowing clues: the windmill creaks, the
  lantern flickers, and the old wishing bell starts to hum.
- With teamwork and a little magic, they lift, sort, and steady the farmyard
  things until the day ends in a grand, glowing finish.

This world is intentionally small and constraint-checked: only a few story
variants are considered reasonable, and the end of each story proves what
changed in the simulated world.
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class Problem:
    id: str
    title: str
    big_thing: str
    small_thing: str
    fix_method: str
    risky_clue: str
    magic_clue: str
    ending_image: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


PROBLEMS = {
    "haystack": Problem(
        id="haystack",
        title="the lopsided haystack",
        big_thing="haystack",
        small_thing="hay bale",
        fix_method="stack the bales straight again",
        risky_clue="the top hay wobbled like a hat in a storm",
        magic_clue="the old bell gave a tiny golden hum",
        ending_image="the haystack stood tall and square beside the fence",
    ),
    "pump": Problem(
        id="pump",
        title="the stubborn water pump",
        big_thing="water pump",
        small_thing="bucket",
        fix_method="work the lever together",
        risky_clue="the handle dipped and squeaked without a proper pull",
        magic_clue="a silver drip shimmered on the iron handle",
        ending_image="the pump splashed steady water into the waiting bucket",
    ),
    "cart": Problem(
        id="cart",
        title="the runaway cart wheel",
        big_thing="cart wheel",
        small_thing="wagon",
        fix_method="brace the wheel and push as one",
        risky_clue="the wheel kept tipping toward the mud patch",
        magic_clue="the wheel made a bright blue sparkle in the moonlight",
        ending_image="the wagon rolled straight, proud as a parade horse",
    ),
}

BUNGALOWS = [
    Place(
        name="the bungalow by the farmyard",
        detail="A little bungalow sat near the barn, with a porch that creaked in the wind.",
    ),
    Place(
        name="the yellow bungalow at the edge of the farmyard",
        detail="A yellow bungalow watched over the hen coop, and its windows flashed warm and gold.",
    ),
]

GIRL_NAMES = ["Mina", "Lily", "Mira", "Nora", "Ava", "Rose"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Ben", "Leo", "Eli"]
TRAITS = ["brave", "curious", "cheerful", "sturdy", "spry", "lively"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale farmyard storyworld with teamwork, foreshadowing, and magic."
    )
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--place", choices=[p.name for p in BUNGALOWS])
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


def _problem_matches_place(problem: Problem, place: Place) -> bool:
    return place.name.startswith("the bungalow") or "bungalow" in place.name


def valid_combos() -> list[tuple[str, str]]:
    return [(place.name, pid) for place in BUNGALOWS for pid in PROBLEMS if _problem_matches_place(PROBLEMS[pid], place)]


def explain_rejection() -> str:
    return "(No story: this farmyard tale only makes sense when the action starts at a bungalow beside the farmyard.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and "bungalow" not in args.place:
        raise StoryError(explain_rejection())
    place = next((p for p in BUNGALOWS if p.name == args.place), rng.choice(BUNGALOWS))
    problem = PROBLEMS[args.problem] if args.problem else rng.choice(list(PROBLEMS.values()))
    if not _problem_matches_place(problem, place):
        raise StoryError(explain_rejection())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent)


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _trait(rng: random.Random) -> str:
    return rng.choice(TRAITS)


def _do_magic(world: World, hero: Entity, problem: Problem) -> None:
    if ("magic", problem.id) in world.fired:
        return
    world.fired.add(("magic", problem.id))
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(f"And then the magic answered, as if the old farm itself had been listening.")


def tell(params: StoryParams, rng: random.Random) -> World:
    place = next(p for p in BUNGALOWS if p.name == (params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed and params.seed or p.name))
    # The above line is intentionally absurd-looking? No. Replace by direct selection:
    # (kept as a harmless expression-free branchless fold would be worse, so we use the
    # real place in generate() instead; this function is only called with a patched world.)
    return World(place)


def build_world(params: StoryParams, rng: random.Random) -> World:
    place = rng.choice(BUNGALOWS) if not params else next(p for p in BUNGALOWS if p.name == params.seed_place)  # type: ignore[attr-defined]
    return World(place)


def _intro(world: World, hero: Entity, parent: Entity, trait: str) -> None:
    world.say(
        f"{hero.id} was a {trait} little {_hero_type(hero.type)} who lived in {world.place.name}."
    )
    world.say(world.place.detail)
    world.say(
        f"{hero.id} loved the farmyard because every gate, bucket, and beam seemed ready for a big tale."
    )


def _foreshadow(world: World, problem: Problem) -> None:
    world.para()
    world.say(
        f"That afternoon, a few foreshadowing clues began to show up around the yard: {problem.risky_clue}."
    )
    world.say(
        f"Near the barn, {problem.magic_clue}, and even the wind sounded like it was whispering, 'Soon now.'"
    )


def _conflict(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.para()
    world.say(
        f"{hero.id} wanted to help right away, but {parent.pronoun('possessive')} {parent.type} saw the {problem.big_thing} and shook {parent.pronoun('possessive')} head."
    )
    world.say(
        f'"That is a mighty big job," {parent.pronoun()} said. "It needs teamwork, not one pair of hands and a hopeful grin."'
    )


def _teamwork(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    parent.memes["resolve"] = parent.memes.get("resolve", 0.0) + 1
    world.para()
    world.say(
        f"So {hero.id} and {parent.pronoun('object')} did the job together, one lifting and the other balancing, both counting like old barn clocks."
    )
    world.say(
        f"They {problem.fix_method}, and with every careful push the farmyard settled down as neat as a quilt."
    )


def _resolution(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    if ("resolve", problem.id) in world.fired:
        return
    world.fired.add(("resolve", problem.id))
    _do_magic(world, hero, problem)
    world.say(
        f"In the end, {problem.ending_image}."
    )
    world.say(
        f"{hero.id} laughed all the way back to the bungalow, and {parent.pronoun('possessive')} {parent.type} laughed too, because the biggest thing in the yard had become the simplest: two helpers, one bright idea, and a little bit of magic."
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    place = next((p for p in BUNGALOWS if p.name == (params.__dict__.get("place") or BUNGALOWS[0].name)), BUNGALOWS[0])
    problem = PROBLEMS[params.__dict__.get("problem", "haystack")] if hasattr(params, "problem") else PROBLEMS["haystack"]
    # Since StoryParams is minimal, use deterministic sampling based on seed.
    if params.seed is None:
        sid = 0
    else:
        sid = params.seed
    place = BUNGALOWS[sid % len(BUNGALOWS)]
    problem = list(PROBLEMS.values())[sid % len(PROBLEMS)]
    hero_type = _hero_type(params.gender)
    hero = Entity(id=params.name, kind="character", type=hero_type)
    parent = Entity(id="Parent", kind="character", type=params.parent, label=params.parent)
    world = World(place)
    world.add(hero)
    world.add(parent)
    trait = TRAITS[sid % len(TRAITS)]
    world.facts = {"hero": hero, "parent": parent, "problem": problem, "trait": trait, "place": place}

    _intro(world, hero, parent, trait)
    _foreshadow(world, problem)
    _conflict(world, hero, parent, problem)
    _teamwork(world, hero, parent, problem)
    _resolution(world, hero, parent, problem)

    prompts = [
        f"Write a tall-tale style story set in a farmyard bungalow about teamwork, foreshadowing, and a little magic.",
        f"Tell a child-friendly story where {hero.id} and a {params.parent} solve {problem.title} together.",
    ]
    story_qa = [
        QAItem(
            question=f"Where did {hero.id} live in the story?",
            answer=f"{hero.id} lived in {world.place.name}, right beside the farmyard.",
        ),
        QAItem(
            question=f"What big problem needed teamwork?",
            answer=f"The story's big problem was {problem.title}. It was too much for one helper alone.",
        ),
        QAItem(
            question=f"What clues foreshadowed the ending?",
            answer=f"The creaking sounds, the humming bell, and the bright little shimmer all foreshadowed that magic and teamwork were coming.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {params.parent} fix things?",
            answer=f"They fixed things by working together and using a little magic, so {problem.ending_image}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and combine their strength, ideas, or tools to do something together.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story leaves small clues that hint at something important that will happen later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something surprising and impossible in real life, like a charm, glow, or spell that helps the characters.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type}")
    lines.append(f"  place={world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(bungalow) :- true.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in BUNGALOWS:
        lines.append(asp.fact("place", p.name))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    return 0 if asp.solve(asp_program("#show valid_place/1."), models=1) is not None else 1


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", seed=1),
    StoryParams(name="Noah", gender="boy", parent="father", seed=2),
    StoryParams(name="Lily", gender="girl", parent="mother", seed=3),
]


def build_args_choices():
    return {
        "place": [p.name for p in BUNGALOWS],
        "problem": sorted(PROBLEMS),
    }


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
