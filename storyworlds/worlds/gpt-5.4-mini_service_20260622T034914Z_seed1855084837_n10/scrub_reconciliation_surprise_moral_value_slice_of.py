#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/scrub_reconciliation_surprise_moral_value_slice_of.py
===================================================================================================

A small slice-of-life storyworld about a simple household mistake, a surprising
gesture, and a reconciliation that ends with a quiet moral value.

Seed tale:
---
Mina and her older brother Jace shared Saturday chores. Mina was supposed to
scrub the kitchen table after breakfast, but she got distracted by a text from
her friend and left the cloth dripping on the chair. Jace saw the mess and made
a sharp remark that stung her feelings. Mina snapped back. The air in the tiny
apartment felt heavy.

Later, while putting away groceries, Jace found Mina's missing math worksheet
inside the grocery bag. He had secretly picked it up at school for her after she
forgot it in class. That surprised Mina. She apologized for leaving the table
dirty and for talking back. Jace apologized too for being mean. They scrubbed
the table together, laughed at the silly mix-up, and shared cookies with their
mom on the couch.

Causal state updates:
---
    scrub action -> physical cleanliness +1 on object/space, actor.duties += 1
    careless mess -> messiness +1, owner worry +1 if noticed
    sharp remark -> hurt feelings +1, conflict +1
    apology + listening -> conflict -1, hurt feelings -1, reconciliation +1
    kind surprise returned -> surprise +1, trust +1
    shared cleanup -> cleanliness +1, teamwork +1, moral value("care") +1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    home: str
    hero: str
    sibling: str
    parent: str
    task: str
    object: str
    surprise: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.facts = copy.deepcopy(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


SETTINGS = {
    "apartment": {"place": "their small apartment"},
    "kitchen": {"place": "the kitchen"},
    "laundry": {"place": "the laundry room"},
}

TASKS = {
    "table": {
        "verb": "scrub the kitchen table",
        "object": "kitchen table",
        "mess": "crumbs and sticky spots",
        "clean": "shine bright again",
        "zone": {"table"},
    },
    "sink": {
        "verb": "scrub the sink",
        "object": "sink",
        "mess": "soap rings",
        "clean": "look neat and white",
        "zone": {"sink"},
    },
    "floor": {
        "verb": "scrub the floor",
        "object": "floor",
        "mess": "little muddy prints",
        "clean": "feel fresh under bare feet",
        "zone": {"floor"},
    },
}

OBJECTS = {
    "worksheet": {
        "label": "math worksheet",
        "phrase": "her missing math worksheet",
        "kind": "paper",
        "tags": {"school", "paper", "surprise"},
    },
    "note": {
        "label": "kind note",
        "phrase": "a folded note with a doodle",
        "kind": "paper",
        "tags": {"paper", "surprise", "kindness"},
    },
    "keys": {
        "label": "house keys",
        "phrase": "the spare house keys",
        "kind": "keys",
        "tags": {"keys", "surprise"},
    },
}

NAMES = ["Mina", "Sofia", "Leah", "Nora", "Ivy", "Eden", "Ruby", "Maya"]
BROTHERS = ["Jace", "Eli", "Noah", "Owen", "Tariq", "Leo", "Ben", "Kai"]
PARENTS = ["Mom", "Dad"]
HOMES = ["apartment", "kitchen", "laundry"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for home in SETTINGS:
        for hero in NAMES:
            for sibling in BROTHERS:
                for task in TASKS:
                    for obj in OBJECTS:
                        if task == "floor" and obj == "keys":
                            continue
                        out.append((home, hero, sibling, task, obj))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: scrub, surprise, reconciliation.")
    ap.add_argument("--home", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--surprise", choices=OBJECTS)
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


def _choose(rng: random.Random, seq):
    return rng.choice(list(seq))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.home is None or c[0] == args.home)
              and (args.hero is None or c[1] == args.hero)
              and (args.sibling is None or c[2] == args.sibling)
              and (args.task is None or c[3] == args.task)
              and (args.object is None or c[4] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    home, hero, sibling, task, obj = rng.choice(sorted(combos))
    surprise = args.surprise or ("worksheet" if obj != "worksheet" else "note")
    if surprise == obj:
        surprise = "note"
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(home=home, hero=hero, sibling=sibling, parent=parent, task=task, object=obj, surprise=surprise)


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _do_scrub(world: World, hero: Entity, target: Entity) -> None:
    target.meters["cleanliness"] += 1
    hero.meters["duties"] += 1
    world.facts["scrubbed"] = target.id


def _mess_notice(world: World, sibling: Entity, hero: Entity, target: Entity) -> None:
    if target.meters["messy"] >= THRESHOLD:
        sibling.memes["worry"] += 1
        hero.memes["hurt"] += 1
        sibling.memes["conflict"] += 1
        world.say(f"{sibling.id} saw the mess and made a sharp remark that stung {hero.id}.")


def _apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["hurt"] = max(0.0, a.memes["hurt"] - 1)
    b.memes["conflict"] = max(0.0, b.memes["conflict"] - 1)
    a.memes["reconciliation"] += 1
    b.memes["reconciliation"] += 1


def _surprise(world: World, sibling: Entity, hero: Entity, obj: Entity) -> None:
    sibling.memes["surprise"] += 1
    sibling.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.say(f"{sibling.id} found {obj.phrase} in a grocery bag and handed it to {hero.id}.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.home]
    task = TASKS[params.task]
    obj_cfg = OBJECTS[params.object]
    surprise_cfg = OBJECTS[params.surprise]

    hero = world.add(Entity(id=params.hero, kind="character", type="girl", role="hero"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="boy", role="sibling"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent", label=params.parent))
    target = world.add(Entity(id=task["object"], type="thing", label=task["object"]))
    target.meters["messy"] = 1
    target.meters["cleanliness"] = 0
    object_ent = world.add(Entity(id=obj_cfg["label"], type=obj_cfg["kind"], label=obj_cfg["label"], phrase=obj_cfg["phrase"], tags=set(obj_cfg["tags"])))
    surprise_ent = world.add(Entity(id=surprise_cfg["label"], type=surprise_cfg["kind"], label=surprise_cfg["label"], phrase=surprise_cfg["phrase"], tags=set(surprise_cfg["tags"])))
    world.facts.update(setting=setting["place"], task=task, obj=object_ent, surprise=surprise_ent, hero=hero, sibling=sibling, parent=parent)

    world.say(f"On Saturday morning, {hero.id} and {sibling.id} moved around {setting['place']} with quiet chores.")
    world.say(f"{hero.id} was supposed to scrub the {task['object']}, and that would make it {task['clean']}.")
    world.para()
    _mess_notice(world, sibling, hero, target)
    hero.memes["hurt"] += 1
    sibling.memes["conflict"] += 1
    world.say(f"{hero.id} snapped back, and the little apartment felt heavy for a minute.")
    world.para()
    _surprise(world, sibling, hero, surprise_ent)
    world.say(f"{hero.id} looked up, surprised, because {sibling.id} had quietly helped after all.")
    _apology(world, hero, sibling)
    world.say(f"{hero.id} apologized for leaving the chore half-done, and {sibling.id} apologized for being mean.")
    world.para()
    _do_scrub(world, hero, target)
    _do_scrub(world, sibling, target)
    hero.memes["care"] += 1
    sibling.memes["care"] += 1
    world.say(f"Together they scrubbed the {task['object']} until it could {task['clean']}.")
    world.say(f"Later, they shared cookies with {parent.label} on the couch, feeling better and more patient.")
    world.facts.update(task=task, object_cfg=obj_cfg, surprise_cfg=surprise_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    obj = f["object_cfg"]
    return [
        f'Write a gentle slice-of-life story where someone has to scrub a {task["object"]} and learns something kind.',
        f"Tell a story about a small home chore, a surprise from a sibling, and a reconciliation after a sharp remark.",
        f'Write a quiet family story that includes the word "scrub" and ends with a moral value about care.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    task = f["task"]
    obj = f["object_cfg"]
    surprise = f["surprise_cfg"]
    qa = [
        QAItem(
            question=f"What was {hero.id} supposed to scrub?",
            answer=f"{hero.id} was supposed to scrub the {task['object']}, and the goal was to make it look clean and calm again.",
        ),
        QAItem(
            question=f"Why did {sibling.id} and {hero.id} feel tense at first?",
            answer=f"{sibling.id} made a sharp remark after noticing the mess, and that hurt {hero.id}'s feelings. The moment became tense because neither of them felt listened to right away.",
        ),
        QAItem(
            question=f"What surprise did {sibling.id} bring that changed the mood?",
            answer=f"{sibling.id} found {surprise['phrase']} and handed it over. That surprise showed {hero.id} that {sibling.id} had cared all along, which helped them start over.",
        ),
    ]
    if f["parent"].label:
        qa.append(QAItem(
            question=f"How did the story end after the chore was finished?",
            answer=f"{hero.id} and {sibling.id} scrubbed the {task['object']} together, then shared cookies with {f['parent'].label} on the couch. The ending feels warm because the chore turned into reconciliation.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"]["object"] for _ in [0])
    obj = world.facts["object_cfg"]
    qs = []
    if obj["kind"] == "paper":
        qs.append(QAItem(
            question="Why do people keep paper safe from spills?",
            answer="Paper can wrinkle or tear when it gets wet, so people try to keep important papers dry and clean.",
        ))
    qs.append(QAItem(
        question="What does it mean to reconcile?",
        answer="To reconcile means to make up after a disagreement. People listen, apologize, and start treating each other kindly again.",
    ))
    qs.append(QAItem(
        question="What is a moral value?",
        answer="A moral value is a good idea about how to treat people, like caring, honesty, or kindness.",
    ))
    return qs


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
moral_value(care).
reconciliation(A,B) :- apology(A), apology(B).
surprise(X) :- surprise_item(X).
clean(X) :- scrubbed(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("moral_value", "care"),
        asp.fact("surprise_item", "worksheet"),
        asp.fact("surprise_item", "note"),
        asp.fact("surprise_item", "keys"),
        asp.fact("apology", "hero"),
        asp.fact("apology", "sibling"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show moral_value/1.\n#show surprise/1."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP twin loaded and produced a model.")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if not sample.story.strip():
        print("MISMATCH: sample story empty.")
        return 1
    print("OK: generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.home not in SETTINGS or params.hero not in NAMES or params.sibling not in BROTHERS:
        raise StoryError("Invalid parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(home="apartment", hero="Mina", sibling="Jace", parent="Mom", task="table", object="worksheet", surprise="worksheet"),
    StoryParams(home="kitchen", hero="Nora", sibling="Leo", parent="Dad", task="sink", object="note", surprise="note"),
    StoryParams(home="laundry", hero="Ivy", sibling="Ben", parent="Mom", task="floor", object="keys", surprise="keys"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show moral_value/1.\n#show surprise/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
