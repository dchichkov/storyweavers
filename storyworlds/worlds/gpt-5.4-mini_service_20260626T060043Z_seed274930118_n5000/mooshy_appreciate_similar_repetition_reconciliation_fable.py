#!/usr/bin/env python3
"""
A small fable-style storyworld about a mooshy bridge, repeated mistakes, and
reconciliation.

Core premise:
- A young critter wants to cross a path and solve a small problem.
- The path is mooshy, and a repeated attempt makes the problem worse.
- A helper notices a similar need on both sides and offers a repair.
- The ending shows reconciliation: the characters appreciate the fix and each
  other.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- StorySample/QAItem/StoryError imported eagerly from results
- inline ASP_RULES twin plus asp_facts()
- --verify checks Python vs ASP parity and validates a generated sample
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    moist: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    repeat: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    aligns: set[str]
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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "riverbank": Place(name="the riverbank", moist=True, affords={"cross"}),
    "orchard": Place(name="the orchard", moist=False, affords={"gather"}),
    "hollow": Place(name="the hollow", moist=True, affords={"cross", "gather"}),
}

TASKS = {
    "cross": Task(
        id="cross",
        verb="cross the mooshy path",
        gerund="crossing the mooshy path",
        repeat="try the same step again",
        mess="mooshy",
        soil="sunk deeper into the mud",
        zone={"feet"},
        keyword="mooshy",
        tags={"mooshy", "mud"},
    ),
    "gather": Task(
        id="gather",
        verb="gather the fallen apples",
        gerund="gathering apples",
        repeat="reach for the same low branch again",
        mess="sticky",
        soil="smudged with sap",
        zone={"hands"},
        keyword="similar",
        tags={"similar", "fruit"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="little brown boots", region="feet", plural=True),
    "satchel": Prize(label="satchel", phrase="a red satchel", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft wool gloves", region="hands", plural=True),
}

FIXES = [
    Fix(
        id="planks",
        label="a set of planks",
        prep="lay down a few planks first",
        tail="carried the planks together and made a steady way across",
        helps={"mooshy"},
        aligns={"feet"},
    ),
    Fix(
        id="basket",
        label="a sturdy basket",
        prep="use a sturdy basket for the apples",
        tail="worked side by side and filled the basket without bruising the fruit",
        helps={"sticky"},
        aligns={"hands"},
    ),
    Fix(
        id="apron",
        label="an apron",
        prep="put on an apron first",
        tail="kept the sap off their clothes while they worked together",
        helps={"sticky"},
        aligns={"torso", "hands"},
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Pip", "Oren", "Milo", "Jude", "Arlo", "Finn"]
TRAITS = ["careful", "curious", "gentle", "brave", "patient", "kind"]


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_fix(task: Task, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if task.mess in fix.helps and prize.region in fix.aligns:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p_name, place in PLACES.items():
        for t_name in place.affords:
            task = TASKS[t_name]
            for pr_name, prize in PRIZES.items():
                if prize_at_risk(task, prize) and select_fix(task, prize):
                    combos.append((p_name, t_name, pr_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about mooshy trouble and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "friend"])
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
    if args.task and args.prize:
        task = TASKS[args.task]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(task, prize) and select_fix(task, prize)):
            raise StoryError("That task and prize do not make a reasonable fable problem.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit the requested hero gender in this world.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")

    place, task, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "friend"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.mess] = actor.meters.get(task.mess, 0.0) + 1.0
    actor.memes["effort"] = actor.memes.get("effort", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} set out {task.gerund}.")


def predict_mess(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    return {"soiled": False, "repeat": sim.get(actor.id).memes.get("effort", 0.0) >= THRESHOLD}


def tell(place: Place, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(id="prize", type=prize_cfg.region, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id, plural=prize_cfg.plural))
    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, place=place, prize_cfg=prize_cfg)

    world.say(f"Once in {place.name}, there lived a little {trait} {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} liked {task.gerund}, and {hero.pronoun('possessive')} {prize.label} was one of the things {hero.pronoun()} loved most.")
    world.say(f"The {prize.label} was {prize.phrase}, and {hero.id} wore {prize.it()} proudly.")

    world.para()
    world.say(f"One day, {hero.id} went to {place.name} to {task.verb}.")
    world.say(f"But the path was mooshy, and when {hero.id} tried to {task.repeat}, {hero.pronoun('subject').capitalize()} sank and had to stop.")
    _do_task(world, hero, task, narrate=False)

    if prize.region in task.zone:
        world.say(f"That was enough to make {hero.pronoun('possessive')} {prize.label} {task.soil}.")
        helper.memes["concern"] = helper.memes.get("concern", 0.0) + 1.0

    world.para()
    world.say(f"{helper.label_word if hasattr(helper, 'label_word') else helper.label} noticed that the trouble was similar each time: the same soft ground made the same problem.")
    world.say(f"{helper.id if helper.id != 'Helper' else 'The helper'} did not scold {hero.id}; instead, {helper.pronoun()} said, 'Let us be wise together.'")
    fix = select_fix(task, prize)
    if not fix:
        raise StoryError("No compatible fix exists for this story.")
    world.say(f"They chose to {fix.prep}, and at once the way looked steadier.")
    world.say(f"{hero.id} and {helper.id if helper.id != 'Helper' else 'the helper'} worked in a similar rhythm, one step after another, until the task felt easy.")

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    hero.memes["reconciled"] = 1.0
    helper.memes["reconciled"] = 1.0
    world.say(f"After that, {hero.id} could {task.verb} without slipping, and everyone appreciated the clever fix.")
    world.say(f"They {fix.tail}, and by the end {hero.id} was smiling beside {helper.id if helper.id != 'Helper' else 'the helper'}, with the {prize.label} still neat and the mooshy trouble gone.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, prize = f["hero"], f["task"], f["prize_cfg"]
    return [
        f'Write a short fable for a young child about a "{task.keyword}" problem and a kind fix.',
        f"Tell a gentle story where {hero.id} tries to {task.verb} but a mooshy place causes repeated trouble, then someone helps.",
        f'Write a simple reconciliation story that includes the words "mooshy", "appreciate", and "similar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, task = f["hero"], f["helper"], f["prize_cfg"], f["task"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.name}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Why was the path a problem for {hero.id}?",
            answer=f"The path was mooshy, so when {hero.id} tried again and again, the same soft ground made it hard to keep going.",
        ),
        QAItem(
            question=f"How did the helper and {hero.id} solve the trouble?",
            answer=f"They chose a fix that fit the task, {select_fix(task, Prize(label=prize.label, phrase=prize.phrase, region=prize.region, plural=prize.plural)).prep}, so they could finish together.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and appreciated the help, because the problem was solved and the ending was calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does mooshy mean?",
            answer="Mooshy means soft, wet, and squishy underfoot, like ground that can sink when you step on it.",
        ),
        QAItem(
            question="What does appreciate mean?",
            answer="To appreciate someone is to notice their kindness or good help and feel thankful for it.",
        ),
        QAItem(
            question="What does similar mean?",
            answer="Similar means alike or nearly the same, like two problems that happen in the same way.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had trouble become friendly again and work together in peace.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", task="cross", prize="boots", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="hollow", task="cross", prize="boots", name="Pip", gender="boy", helper="father", trait="careful"),
    StoryParams(place="orchard", task="gather", prize="gloves", name="Ivy", gender="girl", helper="friend", trait="gentle"),
]


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.verb} does not reasonably threaten {prize.phrase} in this tiny fable world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.moist:
            lines.append(asp.fact("moist", pid))
        for t in sorted(place.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, task.mess))
        for z in sorted(task.zone):
            lines.append(asp.fact("zone", tid, z))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, prize.region))
        if prize.plural:
            lines.append(asp.fact("plural", prid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("fits", g, prid))
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.id))
        for m in sorted(fix.helps):
            lines.append(asp.fact("helps", fix.id, m))
        for a in sorted(fix.aligns):
            lines.append(asp.fact("aligns", fix.id, a))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T, P) :- zone(T, R), worn_on(P, R).
compatible(F, T, P) :- prize_at_risk(T, P), mess_of(T, M), helps(F, M), aligns(F, R), worn_on(P, R).
valid(Place, T, P) :- affords(Place, T), prize_at_risk(T, P), compatible(_, T, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample = generate(resolve_params(argparse.Namespace(place=None, task=None, prize=None, gender=None, helper=None, name=None), random.Random(7)))
    if not sample.story:
        return 1
    if ok:
        print(f"OK: ASP parity matches Python for {len(py)} combos; sample generation succeeded.")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.helper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible stories:")
        for triple in triples:
            print(" ", triple)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
