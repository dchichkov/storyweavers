#!/usr/bin/env python3
"""
storyworlds/worlds/rank_foreshadowing_inner_monologue_fairy_tale.py
===================================================================

A small fairy-tale storyworld about rank, a quiet warning, and the courage to
listen to one's own thoughts before choosing a better path.

Seed tale inspiration:
- A low-ranking child in a fairy-tale castle wants to prove worth.
- The child notices a foreshadowing sign before a risky errand.
- Inner monologue shapes the decision.
- The ending proves the rank changed because of a careful choice, not brute force.
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
    rank: int = 0
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    kind: str  # castle, tower, wood, garden, hall
    dark: bool = False
    omen: str = ""


@dataclass
class Task:
    id: str
    verb: str
    risky_verb: str
    setting: str
    danger: str
    omen: str
    clue: str
    rank_gain: int


@dataclass
class Crown:
    label: str
    title: str
    rank_needed: int
    phrase: str


@dataclass
class StoryParams:
    place: str
    task: str
    crown: str
    name: str
    gender: str
    station: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def maybe_rank_up(world: World, hero: Entity, task: Task, crown: Crown) -> list[str]:
    out: list[str] = []
    sig = ("rank_up", hero.id, task.id)
    if sig in world.fired:
        return out
    if hero.meters.get(task.id, 0) < THRESHOLD:
        return out
    world.fired.add(sig)
    hero.rank += task.rank_gain
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    out.append(f"{hero.name_or_label()} felt a little taller inside.")
    if hero.rank >= crown.rank_needed:
        out.append(f"A new title waited for {hero.name_or_label()}.")
    return out


def foreshadow(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"That morning, {task.omen} drifted across {world.place.name}, and {hero.name_or_label()} noticed it at once."
    )
    world.say(
        f"Somewhere in {hero.name_or_label()}'s heart, a small voice whispered, "
        f'"This looks like the kind of day that will ask for caution."'
    )
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1


def inner_monologue(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"'{hero.name_or_label()} told {hero.pronoun('object')}self that {task.clue}.'"
    )
    hero.memes["thoughtfulness"] = hero.memes.get("thoughtfulness", 0) + 1


def attempt_task(world: World, hero: Entity, task: Task) -> None:
    hero.meters[task.id] = hero.meters.get(task.id, 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    if task.id == "dash":
        hero.meters["wind"] = hero.meters.get("wind", 0) + 1
    maybe_rank_up(world, hero, task, world.facts["crown"])


def choose_carefully(world: World, hero: Entity, task: Task) -> None:
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0) - 1)
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.name_or_label()} slowed down, listened to {hero.pronoun('possessive')} own thoughts, and chose the careful way."
    )
    if task.id == "dash":
        world.say("Instead of running straight through the dark wood, the child took the lamp-lit path by the stones.")
    elif task.id == "deliver":
        world.say("Instead of hurrying past the sparrows, the child waited until they had flown clear.")
    else:
        world.say("Instead of touching the strange thing at once, the child watched it first.")
    attempt_task(world, hero, task)


def tell(place: Place, task: Task, crown: Crown,
         hero_name: str = "Mira", hero_type: str = "girl",
         trait: str = "careful", station: str = "page") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        rank=0,
        traits=["small", trait],
    ))
    steward = world.add(Entity(
        id="Steward",
        kind="character",
        type="woman",
        label="the steward",
        rank=3,
    ))
    world.facts.update(hero=hero, steward=steward, task=task, crown=crown, station=station)

    world.say(
        f"In {place.name}, little {trait} {hero_type} {hero_name} served as a lowly {station} and dreamed of a better rank."
    )
    world.say(
        f"{hero_name} wished to earn {crown.phrase}, for fairy-tale bells always sounded sweeter to those with a noble title."
    )
    foreshadow(world, hero, task)
    inner_monologue(world, hero, task)

    world.para()
    world.say(
        f"Then the steward gave {hero.pronoun('object')} a task: {task.verb}."
    )
    world.say(
        f"It sounded easy, but {task.danger} lurked nearby."
    )
    choose_carefully(world, hero, task)

    world.para()
    if hero.rank >= crown.rank_needed:
        world.say(
            f"By dusk, {hero_name} had earned enough rank to stand before the court, and the steward placed {crown.label} upon {hero.pronoun('possessive')} head."
        )
        world.say(
            f"{hero_name} smiled at the shining crown and thought that listening first had made {hero.pronoun('object')} brave enough to rise."
        )
    else:
        world.say(
            f"By dusk, {hero_name} had not won the crown, but {hero.pronoun('subject')} had won something better: a wiser rank in {hero.pronoun('possessive')} own heart."
        )
        world.say(
            f"The steward nodded, because in fairy tales, careful courage is the kind that grows."
        )

    world.facts["hero_rank"] = hero.rank
    world.facts["resolved"] = hero.rank >= crown.rank_needed
    return world


PLACES = {
    "castle_gate": Place(name="the castle gate", kind="castle", dark=False, omen="a raven feather"),
    "wood_path": Place(name="the lantern path through the wood", kind="wood", dark=True, omen="a hush of leaves"),
    "rose_garden": Place(name="the rose garden", kind="garden", dark=False, omen="one rose facing the wrong way"),
    "high_hall": Place(name="the high hall", kind="hall", dark=False, omen="a candle flame leaning sideways"),
}

TASKS = {
    "dash": Task(
        id="dash",
        verb="dash across the lantern path with the royal ribbon",
        risky_verb="run",
        setting="wood",
        danger="a fox's den waited near the roots",
        omen="a raven feather",
        clue="the safest road is not always the fastest one",
        rank_gain=2,
    ),
    "deliver": Task(
        id="deliver",
        verb="carry the silver cup to the high hall",
        risky_verb="hurry",
        setting="hall",
        danger="the floor was slick with spilled honey",
        omen="a candle flame leaning sideways",
        clue="steady hands keep treasure from falling",
        rank_gain=1,
    ),
    "gather": Task(
        id="gather",
        verb="gather moon-flowers before the moon rose high",
        risky_verb="pluck",
        setting="garden",
        danger="the thornbush would scratch careless fingers",
        omen="one rose facing the wrong way",
        clue="some pretty things want to be watched before they are touched",
        rank_gain=1,
    ),
}

CROWNS = {
    "page": Crown(label="a page's cap", title="page", rank_needed=1, phrase="a page's cap"),
    "squire": Crown(label="a silver badge", title="squire", rank_needed=2, phrase="a silver badge"),
    "knight": Crown(label="a small gold crown", title="knight", rank_needed=3, phrase="a small gold crown"),
}

GIRL_NAMES = ["Mira", "Elin", "Tilda", "Nora", "Lena"]
BOY_NAMES = ["Eamon", "Finn", "Toby", "Bram", "Cedric"]
TRAITS = ["careful", "curious", "earnest", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for c in CROWNS:
                if TASKS[t].rank_gain >= 1 and CROWNS[c].rank_needed <= 3:
                    combos.append((p, t, c))
    return combos


def explain_rejection(task: Task, crown: Crown) -> str:
    return (
        f"(No story: the task '{task.id}' cannot reasonably lead to {crown.title}; "
        f"the fairy-tale court would not hand out that rank for such a mismatch.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld with rank, foreshadowing, and inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--crown", choices=CROWNS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--station", choices=["page", "helper", "messenger"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.crown is None or c[2] == args.crown)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, crown = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    station = args.station or rng.choice(["page", "helper", "messenger"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, crown=crown, name=name, gender=gender, station=station, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, crown = f["hero"], f["task"], f["crown"]
    return [
        f'Write a fairy tale for a young child about rank, a warning, and a choice, using the word "{task.id}".',
        f"Tell a gentle story where {hero.name_or_label()} notices a clue, thinks quietly to {hero.pronoun('object')}self, and earns {crown.phrase}.",
        f"Write a small castle story about a low-ranking helper who listens to an omen before completing a task.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, task, crown, steward = f["hero"], f["task"], f["crown"], f["steward"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.name_or_label()}, a young {hero.type} who starts at a low rank and learns to choose carefully.",
        ),
        QAItem(
            question=f"What warning clue foreshadowed trouble?",
            answer=f"The foreshadowing clue was {task.omen}, which made the day feel like one that needed caution.",
        ),
        QAItem(
            question=f"What did {hero.name_or_label()} think privately before acting?",
            answer=f"{hero.name_or_label()} told {hero.pronoun('object')}self that {task.clue}.",
        ),
        QAItem(
            question=f"Who gave the task that changed the rank?",
            answer=f"The steward gave the task and watched to see whether {hero.name_or_label()} would use care instead of haste.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rank in a fairy-tale court?",
            answer="Rank is a person's place in the court or household, like page, squire, or knight, and it can show trust and responsibility.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later, like a strange feather or a candle that leans sideways.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet speech a character has inside their own mind before they decide what to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = [f"rank={e.rank}"]
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood_path", task="dash", crown="squire", name="Mira", gender="girl", station="page", trait="careful"),
    StoryParams(place="rose_garden", task="gather", crown="page", name="Eamon", gender="boy", station="helper", trait="curious"),
    StoryParams(place="high_hall", task="deliver", crown="page", name="Tilda", gender="girl", station="messenger", trait="gentle"),
]


ASP_RULES = r"""
% A story is valid when the task and crown fit a plausible rank gain.
valid(Place, Task, Crown) :- place(Place), task(Task), crown(Crown).

% A stronger crown requires at least one point of rank gain from the task.
can_gain(Task, Gain) :- task_gain(Task, Gain), Gain >= 1.

% This world's declarative twin is intentionally simple:
% if a task exists and a crown exists, the generated story is feasible.
story_ok(P, T, C) :- valid(P, T, C), can_gain(T, _).
#show story_ok/3.
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_gain", tid, task.rank_gain))
    for cid in CROWNS:
        lines.append(asp.fact("crown", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3.\n"))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    task = TASKS[params.task]
    crown = CROWNS[params.crown]
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        rank=0,
        traits=["small", params.trait],
    ))
    steward = world.add(Entity(id="Steward", kind="character", type="woman", label="the steward", rank=3))
    world.facts.update(hero=hero, steward=steward, task=task, crown=crown, params=params)

    hero.meters["hope"] = 1
    world.say(
        f"Once in {place.name}, {params.trait} little {params.gender} {params.name} served as a {params.station} with only the lowest rank."
    )
    world.say(
        f"{params.name} longed for {crown.phrase}, because the old castle seemed to promise that careful hearts could rise."
    )
    foreshadow(world, hero, task)
    inner_monologue(world, hero, task)

    world.para()
    world.say(f"The steward set a task before {params.name}: {task.verb}.")
    world.say(f"But {task.danger}.")
    if task.id == "dash":
        world.say(f"{params.name} wanted to hurry, yet the raven feather made {hero.pronoun('object')} hesitate.")
    elif task.id == "deliver":
        world.say(f"{params.name} felt a rush in the feet, then remembered the leaning candle flame.")
    else:
        world.say(f"{params.name} reached toward the flowers, then thought of the rose turned the wrong way.")

    choose_carefully(world, hero, task)

    world.para()
    if hero.rank >= crown.rank_needed:
        world.say(f"At sunset, the steward smiled and placed {crown.label} upon {params.name}'s head.")
        world.say(f"The new rank fit {params.name} like a song, because {hero.pronoun('subject')} had listened before {hero.pronoun('subject')} leaped.")
    else:
        world.say(f"At sunset, {params.name} had not earned {crown.label}, but {hero.pronoun('subject')} had earned the steward's trust.")
        world.say(f"In the fairy-tale hall, that too was a kind of treasure.")

    world.facts["hero_rank"] = hero.rank
    world.facts["resolved"] = hero.rank >= crown.rank_needed

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
        print(asp_program("#show story_ok/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n"))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, task, crown) combos:\n")
        for p, t, c in triples:
            print(f"  {p:12} {t:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
