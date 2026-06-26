#!/usr/bin/env python3
"""
A small slice-of-life storyworld about proximity, teamwork, curiosity, and humor.

Premise:
- A child wants to reach or share something nearby.
- Because the object or task is close, they can solve it with a helper.
- Curiosity causes a tiny detour; humor softens the moment.
- Teamwork changes the final state: an unreachable or awkward thing becomes usable,
  a lonely task becomes shared, and the ending image proves the change.

This world keeps one compact domain with:
- places that determine what is nearby
- items that can be out of reach, shared, or checked together
- emotional state driven by the simulation, not a fixed template
- a reasonableness gate: the chosen task must actually be doable with nearby help
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    near: Optional[str] = None
    usable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "dust": 0.0, "order": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "joy": 0.0, "humor": 0.0, "teamwork": 0.0}

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    name: str
    indoor: bool = True
    nearby: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    setup: str
    outcome: str
    requires: set[str]
    nearby_ok: bool = True
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    needs_help: bool = True
    portable: bool = True
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


PLACES = {
    "kitchen": Place("the kitchen", indoor=True, nearby={"table", "stool", "jar", "spoon"}),
    "hallway": Place("the hallway", indoor=True, nearby={"coat hook", "shoe rack", "mirror", "basket"}),
    "balcony": Place("the balcony", indoor=False, nearby={"chair", "planter", "watering can"}),
    "living_room": Place("the living room", indoor=True, nearby={"couch", "lamp", "shelf", "remote"}),
}

TASKS = {
    "jar": Task(
        id="jar",
        verb="open the jar",
        gerund="opening jars",
        setup="the lid was stuck and wiggled only a little",
        outcome="the lid finally gave with a soft pop",
        requires={"hands"},
        nearby_ok=True,
        keyword="jar",
        tags={"jar", "kitchen"},
    ),
    "shelf": Task(
        id="shelf",
        verb="reach the book on the shelf",
        gerund="reaching for books",
        setup="the book sat just a little too high",
        outcome="the book slid into waiting hands",
        requires={"height"},
        nearby_ok=True,
        keyword="shelf",
        tags={"book", "shelf"},
    ),
    "plant": Task(
        id="plant",
        verb="water the plant",
        gerund="watering the plant",
        setup="the pot was light and the leaves looked a bit droopy",
        outcome="the soil darkened and the leaves lifted",
        requires={"water"},
        nearby_ok=True,
        keyword="plant",
        tags={"plant", "water"},
    ),
    "basket": Task(
        id="basket",
        verb="sort the laundry",
        gerund="sorting laundry",
        setup="the basket had a funny mountain of socks",
        outcome="the socks were matched into neat little pairs",
        requires={"sorting"},
        nearby_ok=True,
        keyword="basket",
        tags={"laundry", "socks"},
    ),
}

ITEMS = {
    "jar": Item("jar", "a jam jar with a slippery lid", "jar"),
    "book": Item("book", "a picture book from the high shelf", "book"),
    "plant": Item("plant", "a thirsty little plant", "plant"),
    "basket": Item("basket", "a basket of mismatched laundry", "basket", plural=False),
}

AIDS = [
    Aid("stool", "a small stool", "pull over a small stool", "pulled over the small stool", {"height"}),
    Aid("two_hands", "two hands", "ask for two hands to twist", "worked together with two hands", {"hands"}),
    Aid("cup", "a little cup of water", "fill a little cup of water", "carried a little cup of water", {"water"}),
    Aid("partner", "a helper", "sort it together with a helper", "sorted it together", {"sorting"}),
]

NAMES = ["Mina", "Owen", "Iris", "Noah", "Tia", "Luca", "Nora", "Ezra"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "cheerful", "gentle", "spunky", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_name, place in PLACES.items():
        for task_id in place.nearby:
            if task_id not in TASKS:
                continue
            task = TASKS[task_id]
            for item_id, item in ITEMS.items():
                if task.id == item_id and item.needs_help and select_aid(task, item):
                    combos.append((place_name, task_id, item_id))
    return combos


def select_aid(task: Task, item: Item) -> Optional[Aid]:
    for aid in AIDS:
        if aid.helps & task.requires:
            return aid
    return None


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def reasonableness_check(task: Task, item: Item) -> bool:
    return task.id == item.type and task.nearby_ok and select_aid(task, item) is not None


def explain_rejection(task: Task, item: Item) -> str:
    return (
        f"(No story: {task.gerund} does not pair reasonably with {item.phrase} in this small world. "
        f"The task needs a nearby helper or tool that can actually solve the problem.)"
    )


def pick_place_task_item(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.item:
        task = TASKS[args.task]
        item = ITEMS[args.item]
        if not reasonableness_check(task, item):
            raise StoryError(explain_rejection(task, item))
    place, task_id, item_id = pick_place_task_item(args, rng)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, item=item_id, name=name, gender=gender, parent=parent, trait=trait)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def setup_line(task: Task, item: Item) -> str:
    return f"{task.setup.capitalize()}, and {item.phrase} was right there but just a little inconvenient."


def introduce(world: World, hero: Entity, parent: Entity, item: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} who noticed small things."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked being near {hero.pronoun('possessive')} {parent.label_word} and making little tasks feel lighter."
    )
    world.say(
        f"One day, {hero.id} saw {item.phrase} and wanted to {task.verb}."
    )


def curious_glance(world: World, hero: Entity, task: Task) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} leaned closer to look, because curious eyes always wanted to know how things worked."
    )
    if task.id in {"jar", "basket"}:
        world.say("That made the moment feel a little funny, like the room itself was waiting for a tiny decision.")


def warn(world: World, parent: Entity, hero: Entity, item: Entity, aid: Aid) -> None:
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} noticed the trouble and said, "
        f"\"We can do that, but we should use {aid.label} so it goes more easily.\""
    )


def teamwork(world: World, hero: Entity, parent: Entity, aid: Aid, task: Task, item: Entity) -> None:
    hero.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    world.say(
        f"{hero.id} smiled, and {hero.pronoun('possessive')} {parent.label_word} helped with {aid.prep}."
    )
    world.say(
        f"Together they {aid.tail}, and the small problem started to feel shared instead of stuck."
    )


def finish(world: World, hero: Entity, parent: Entity, task: Task, item: Entity, aid: Aid) -> None:
    hero.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"{task.outcome.capitalize()}, and {hero.id} laughed at how simple it had been once they worked side by side."
    )
    world.say(
        f"In the end, {hero.id} was {task.gerund}, {item.phrase} was no longer a problem, and {hero.pronoun('possessive')} {parent.label_word} was right there beside {hero.pronoun('object')}."
    )


def tell(place: Place, task: Task, item_cfg: Item, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "helpful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent", traits=["patient"]))
    item = world.add(Entity(id="item", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))
    aid = select_aid(task, item_cfg)
    if aid is None:
        raise StoryError(explain_rejection(task, item_cfg))

    intro(world, hero, parent, item, task)
    world.para()
    world.say(setup_line(task, item_cfg))
    curious_glance(world, hero, task)
    warn(world, parent, hero, item, aid)
    world.para()
    teamwork(world, hero, parent, aid, task, item)
    finish(world, hero, parent, task, item, aid)

    world.facts.update(hero=hero, parent=parent, item=item, task=task, place=place, aid=aid)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, task, item = f["hero"], f["parent"], f["task"], f["item"]
    return [
        f'Write a short slice-of-life story about {hero.id}, {parent.label_word}, and {item.phrase} near {world.place.name}.',
        f"Tell a gentle story where {hero.id} wants to {task.verb} but learns to do it with help.",
        f'Write a child-friendly story about a nearby problem, teamwork, curiosity, and a small laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, task, item, aid = f["hero"], f["parent"], f["task"], f["item"], f["aid"]
    trait = next(t for t in hero.traits if t != "little")
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {world.place.name}?",
            answer=f"{hero.id} wanted to {task.verb}, because {item.phrase} was right nearby and the task felt like a small daily moment.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} suggest {aid.label}?",
            answer=f"Because {task.setup.lower()}, and {aid.label} was the helpful thing that made the task easier to do together.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after working with {parent.label_word}?",
            answer=f"{hero.id} felt happy and a little proud. {trait.capitalize()} little teamwork turned the awkward task into a shared win.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend([
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about things.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can make a small problem feel lighter, because a funny moment can help people relax and keep going.",
        ),
        QAItem(
            question="What does proximity mean?",
            answer="Proximity means being close to something or someone. When something is nearby, it is easier to notice and use.",
        ),
    ])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
nearby_task(P, T) :- place(P), nearby(P, T), task(T).
needs_help(T) :- requires(T, R), aid(A), helps(A, R).

valid(P, T, I) :- nearby_task(P, T), item(I), item_type(I, T), needs_help(T).

"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p_id, p in PLACES.items():
        lines.append(asp.fact("place", p_id))
        if p.indoor:
            lines.append(asp.fact("indoor", p_id))
        for near in sorted(p.nearby):
            lines.append(asp.fact("nearby", p_id, near))
    for t_id, t in TASKS.items():
        lines.append(asp.fact("task", t_id))
        for r in sorted(t.requires):
            lines.append(asp.fact("requires", t_id, r))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", t_id, tag))
    for i_id, i in ITEMS.items():
        lines.append(asp.fact("item", i_id))
        lines.append(asp.fact("item_type", i_id, i.type))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for h in sorted(a.helps):
            lines.append(asp.fact("helps", a.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about proximity and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams("kitchen", "jar", "jar", "Mina", "girl", "mother", "curious"),
    StoryParams("hallway", "shelf", "book", "Owen", "boy", "father", "cheerful"),
    StoryParams("balcony", "plant", "plant", "Iris", "girl", "mother", "gentle"),
    StoryParams("living_room", "basket", "basket", "Ezra", "boy", "father", "spunky"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.item:
        task = TASKS[args.task]
        item = ITEMS[args.item]
        if not reasonableness_check(task, item):
            raise StoryError(explain_rejection(task, item))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, item=item, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, item) combos:\n")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
