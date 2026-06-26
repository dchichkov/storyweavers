#!/usr/bin/env python3
"""
storyworlds/worlds/yenta_tenure_bale_misunderstanding_flashback_adventure.py
=============================================================================

A small adventure storyworld built from the seed words:
yenta, tenure, bale

Premise:
A young adventurer is traveling with a talking yenta through a windy hill town.
They are trying to keep a paper of tenure safe while crossing a barnyard path
where a bale of hay keeps blocking the way.

The tension:
The yenta and the hero misunderstand each other. One thinks the other wants to
trade away the tenure paper; the other only wants help carrying the bale.

The turn:
A flashback reveals why the hero is so careful with the paper: it proves the
hero's right to stay in the old watch tower.

Resolution:
They work together, move the bale, and protect the tenure paper. The story ends
with the hero keeping the paper safe and the path open.

This world uses two narrative instruments:
- Misunderstanding
- Flashback

It stays in an adventure tone: a journey, a risky path, a helpful companion,
and a practical win at the end.
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    travel: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    keyword: str


@dataclass
class Obstacle:
    id: str
    label: str
    move: str
    story_role: str
    causes: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_type: str
    name: str
    yenta_name: str
    goal: str
    obstacle: str
    seed: Optional[int] = None


PLACES = {
    "hill_town": Place(
        name="the hill town",
        travel="the old stone road",
        weather="windy",
        affords={"carry", "cross"},
    ),
    "barn_path": Place(
        name="the barn path",
        travel="the dirt lane",
        weather="blustery",
        affords={"carry", "cross"},
    ),
    "tower_road": Place(
        name="the road to the watch tower",
        travel="the narrow trail",
        weather="cloudy",
        affords={"carry", "cross"},
    ),
}

GOALS = {
    "tenure": Goal(
        id="tenure",
        label="tenure paper",
        phrase="the old tenure paper",
        risk="blown away",
        region="hands",
        keyword="tenure",
    ),
    "bale": Goal(
        id="bale",
        label="hay bale",
        phrase="the heavy bale of hay",
        risk="stuck in the path",
        region="path",
        keyword="bale",
    ),
}

OBSTACLES = {
    "misunderstanding": Obstacle(
        id="misunderstanding",
        label="misunderstanding",
        move="misunderstand",
        story_role="confusion",
        causes="a wrong guess about the plan",
    ),
    "flashback": Obstacle(
        id="flashback",
        label="flashback",
        move="remember",
        story_role="memory",
        causes="a remembered reason to keep going",
    ),
}

NAMES = ["Milo", "Nia", "Tess", "Jory", "Lina", "Pip", "Rae", "Oren"]
YENTA_NAMES = ["Yetta", "Mara", "Bess", "Tulla", "Sera", "Nessa"]
HERO_TYPES = ["boy", "girl"]
TRAITS = ["brave", "curious", "steady", "quick", "hopeful", "earnest"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with yenta, tenure, bale, misunderstanding, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--name")
    ap.add_argument("--yenta-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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


def select_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    goal = args.goal or rng.choice(list(GOALS))
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(NAMES)
    yenta_name = args.yenta_name or rng.choice(YENTA_NAMES)
    return StoryParams(place=place, hero_type=hero_type, name=name, yenta_name=yenta_name, goal=goal, obstacle=obstacle)


def valid_combo(params: StoryParams) -> bool:
    return params.place in PLACES and params.goal in GOALS and params.obstacle in OBSTACLES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = select_combo(args, rng)
    if not valid_combo(params):
        raise StoryError("No valid story combination matches the given options.")
    return params


def _safe_name(ent: Entity) -> str:
    return ent.id


def _intro(world: World, hero: Entity, yenta: Entity, goal: Goal) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'brave')} little {hero.type} traveling through {world.place.name}."
    )
    world.say(
        f"Beside {hero.pronoun('object')} went {yenta.id}, a clever yenta who knew every bend in the road."
    )
    world.say(
        f"They were guarding {hero.pronoun('possessive')} {goal.label}, which had to stay safe for the journey ahead."
    )


def _travel(world: World, hero: Entity, yenta: Entity, goal: Goal) -> None:
    world.para()
    world.say(
        f"One windy afternoon, they set out along {world.place.travel}, with the breeze tugging at cloaks and sleeves."
    )
    world.say(
        f"{hero.id} wanted to keep moving toward the old tower, but the path narrowed beside a tall stack of hay."
    )
    world.say(
        f"That made the {goal.label} feel extra important, because if it slipped, it could be lost in the dust."
    )


def _misunderstanding(world: World, hero: Entity, yenta: Entity, goal: Goal, obstacle: Obstacle) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    yenta.memes["worry"] = yenta.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} asked for help with the {goal.label}, but {yenta.id} heard only a hurried voice and guessed wrong."
    )
    world.say(
        f"That was a misunderstanding: {yenta.id} thought {hero.id} wanted to leave the {goal.label} behind."
    )
    world.say(
        f"{hero.id} stared in alarm, because {hero.pronoun('possessive')} hands tightened around the paper instead."
    )
    world.facts["misunderstanding"] = True
    world.facts["obstacle"] = obstacle.id


def _flashback(world: World, hero: Entity, yenta: Entity, goal: Goal) -> None:
    world.para()
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"Then came a flashback."
    )
    world.say(
        f"{hero.id} remembered the old watch tower, where the keeper once said the {goal.label} proved who could stay there."
    )
    world.say(
        f"That memory explained why {hero.id} had been so careful; the paper was not junk, but a promise."
    )
    world.facts["flashback"] = True
    world.facts["remembered_reason"] = True


def _resolve(world: World, hero: Entity, yenta: Entity, goal: Goal) -> None:
    world.para()
    hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)
    yenta.memes["worry"] = max(0, yenta.memes.get("worry", 0) - 1)
    world.say(
        f"{hero.id} spoke up at once and told {yenta.id} the truth about the {goal.label}."
    )
    world.say(
        f"{yenta.id} nodded, then used {yenta.pronoun('possessive')} staff to nudge the hay bale aside."
    )
    world.say(
        f"Together they carried the {goal.label} above the dust, and the road opened like a safe green ribbon."
    )
    world.say(
        f"By sunset, {hero.id} still had the {goal.label}, the bale was out of the way, and the old tower was waiting ahead."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    obstacle = OBSTACLES[params.obstacle]
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        memes={"trait": random.choice(TRAITS)},
    ))
    yenta = world.add(Entity(
        id=params.yenta_name,
        kind="character",
        type="woman",
        label="yenta",
    ))
    item = world.add(Entity(
        id=goal.id,
        type="paper" if goal.id == "tenure" else "bale",
        label=goal.label,
        phrase=goal.phrase,
        owner=hero.id,
        caretaker=yenta.id,
    ))
    world.facts.update(hero=hero, yenta=yenta, item=item, goal=goal, obstacle=obstacle, place=place)
    _intro(world, hero, yenta, goal)
    _travel(world, hero, yenta, goal)
    _misunderstanding(world, hero, yenta, goal, obstacle)
    _flashback(world, hero, yenta, goal)
    _resolve(world, hero, yenta, goal)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    yenta: Entity = f["yenta"]
    goal: Goal = f["goal"]
    return [
        f'Write a short adventure story for a child that includes "{goal.keyword}" and a helpful yenta.',
        f"Tell a story where {hero.id} and {yenta.id} face a misunderstanding over the {goal.label}.",
        f"Write a gentle adventure with a flashback that explains why the {goal.label} matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    yenta: Entity = f["yenta"]
    goal: Goal = f["goal"]
    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"It is mainly about {hero.id}, a {hero.memes.get('trait', 'brave')} young adventurer traveling with {yenta.id}.",
        ),
        QAItem(
            question=f"What was the misunderstanding about?",
            answer=f"{yenta.id} thought {hero.id} wanted to leave the {goal.label} behind, but that was not true.",
        ),
        QAItem(
            question=f"What did the flashback explain?",
            answer=f"The flashback explained why the {goal.label} mattered so much: it proved {hero.id} had a right to stay in the old watch tower.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} and {yenta.id} moved the hay bale aside, kept the {goal.label} safe, and continued toward the tower.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yenta in this storyworld?",
            answer="A yenta is a clever older helper who listens closely, gives advice, and helps solve travel problems.",
        ),
        QAItem(
            question="What is tenure here?",
            answer="Tenure is a paper that shows someone has the right to keep a position or stay in a place.",
        ),
        QAItem(
            question="What is a bale?",
            answer="A bale is a large bundled block of hay or straw that can be heavy to move.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
goal(g_tenure).
goal(g_bale).

misunderstanding(happens) :- heard_wrongly(_,_).
flashback(happens) :- remembered(_).

adventure_story(P, G, O) :- place(P), goal(G), obstacle(O).
shows_resolution(P, G) :- adventure_story(P, G, _), flashback(happens), not unresolved(P, G).

#show adventure_story/3.
#show shows_resolution/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    lines.append(asp.fact("heard_wrongly", "hero", "yenta"))
    lines.append(asp.fact("remembered", "tower"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"Unable to import clingo helper: {exc}")
        return 1
    model = asp.one_model(asp_program("#show adventure_story/3.\n#show shows_resolution/2."))
    atoms = set((sym.name, tuple(a.number if a.type.name == "Number" else (a.string if a.type.name == "String" else a.name) for a in sym.arguments)) for sym in model)
    expected = {("adventure_story", ("place", "goal", "obstacle")), ("shows_resolution", ("place", "goal"))}
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP program produced no shown atoms.")
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, o) for p in PLACES for g in GOALS for o in OBSTACLES]


def aspire() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show adventure_story/3.\n#show shows_resolution/2."))
    out = []
    for sym in model:
        args = []
        for a in sym.arguments:
            if a.type == a.type.Number:
                args.append(a.number)
            elif a.type == a.type.String:
                args.append(a.string)
            else:
                args.append(a.name)
        out.append((sym.name, tuple(args)))
    return sorted(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill_town", hero_type="girl", name="Lina", yenta_name="Bess", goal="tenure", obstacle="misunderstanding"),
    StoryParams(place="barn_path", hero_type="boy", name="Milo", yenta_name="Yetta", goal="bale", obstacle="flashback"),
    StoryParams(place="tower_road", hero_type="girl", name="Tess", yenta_name="Mara", goal="tenure", obstacle="flashback"),
]


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show adventure_story/3.\n#show shows_resolution/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure_story/3.\n#show shows_resolution/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.goal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
