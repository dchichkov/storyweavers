#!/usr/bin/env python3
"""
storyworlds/worlds/labor_chocolate_glower_curiosity_mystery_to_solve.py
=======================================================================

A compact comedy storyworld about curious children, chocolate, a glowering
grown-up, and a small mystery that gets solved by noticing the work in the room.

Seed image used to build the world:
---
A curious child visits a place where people are doing labor with chocolate.
Something funny goes missing or looks strange.
A glower or stern face raises the tension.
Curiosity keeps poking at the mystery until the child notices the clue.
The ending proves what changed, and the room feels lighter.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    clue: str
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    question: str
    false_alarm: str
    answer: str
    culprit: str
    fix: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    weather: str = ""

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
        w = World(self.setting)
        w.entities = dataclasses.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.weather = self.weather
        return w


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_glower(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("glower", 0.0) >= THRESHOLD and not ("glower", e.id) in world.fired:
            world.fired.add(("glower", e.id))
            out.append(f"{e.id} glowered so hard the room felt like it had folded its arms.")
    return out


def _r_sticky(world: World) -> list[str]:
    out = []
    candy = world.entities.get("chocolate")
    if not candy:
        return out
    if candy.meters.get("melted", 0.0) < THRESHOLD:
        return out
    if ("sticky", candy.id) in world.fired:
        return out
    world.fired.add(("sticky", candy.id))
    out.append("The chocolate was warm and sticky, which made everything look suspiciously guilty.")
    return out


RULES = [Rule("glower", _r_glower), Rule("sticky", _r_sticky)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_mystery(world: World, mystery: Mystery, clue_seen: bool) -> bool:
    return clue_seen and world.facts.get("story_answer") == mystery.answer


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"stir"}),
    "bakery": Setting(place="the bakery", indoor=True, affords={"stir", "box"}),
    "cafe": Setting(place="the cafe", indoor=True, affords={"stir"}),
}

ACTIVITIES = {
    "labor": Activity(
        id="labor",
        verb="help with the chocolate labor",
        gerund="working at the chocolate table",
        mess="melted",
        clue="warm spoon",
        keyword="labor",
        tags={"labor", "chocolate", "work"},
    ),
    "chocolate": Activity(
        id="chocolate",
        verb="make chocolate treats",
        gerund="making chocolate treats",
        mess="melted",
        clue="missing wrapper",
        keyword="chocolate",
        tags={"chocolate", "work"},
    ),
}

MYSTERIES = {
    "solve": Mystery(
        id="solve",
        question="Why did the tray look empty?",
        false_alarm="a missing tray meant someone had stolen the sweets",
        answer="the sweets had been moved to cool before they melted",
        culprit="the cooler",
        fix="put the chocolate in the cool room",
    )
}

NAMES = ["Mina", "Toby", "Lena", "Ollie", "Pia", "Noah"]
WORKERS = ["baker", "chef", "helper", "parent"]
TRAITS = ["curious", "bright-eyed", "nosy", "cheerful", "bouncy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    mystery: str
    name: str
    worker: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about labor, chocolate, and a curious mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--worker", choices=WORKERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    mystery = args.mystery or "solve"
    name = args.name or rng.choice(NAMES)
    worker = args.worker or rng.choice(WORKERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, mystery=mystery, name=name, worker=worker, trait=trait)


def _story_intro(world: World, hero: Entity, worker: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} was a {hero.type} with a very {hero.memes.get('curiosity_word', 'curious')} mind.")
    world.say(f"{hero.id} came to {world.setting.place} while {worker.label} was doing chocolate labor.")
    world.say(f"{hero.id} loved {activity.gerund} because it looked like a delicious kind of work.")


def _story_problem(world: World, hero: Entity, worker: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    worker.memes["glower"] = worker.memes.get("glower", 0) + 1
    world.para()
    world.say(f"Then {hero.id} saw the empty tray and asked, \"{mystery.question}\"")
    world.say(f"{worker.id} glowered and said, \"It was right here a minute ago.\"")
    world.say(f"That made the mystery feel much bigger, and also a little sillier.")


def _story_clue(world: World, hero: Entity, activity: Activity, mystery: Mystery) -> None:
    world.para()
    world.say(f"{hero.id} kept looking, because curiosity was stronger than the glower.")
    world.say(f"Then {hero.id} noticed {activity.clue} by the cooler.")
    world.say(f"The clue was funny: the chocolate had been moved to cool so it would not melt into a puddly mess.")


def _story_resolution(world: World, hero: Entity, worker: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(f"{hero.id} pointed to the cooler, and the answer popped out of the mystery like a jack-in-the-box.")
    world.say(f"{worker.id} stopped glowering and laughed. \"Oh! I thought someone had taken it.\"")
    world.say(f"They put the chocolate away properly, and the whole room looked less grumpy right away.")
    world.say(f"{hero.id} left smiling, happy to have solved a very sweet mystery.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    mystery = MYSTERIES[params.mystery]
    world = World(setting=setting)
    world.weather = "warm"

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    hero.memes["curiosity_word"] = 1
    worker = world.add(Entity(id=params.worker.capitalize(), kind="character", type=params.worker, label=params.worker))
    chocolate = world.add(Entity(id="chocolate", type="treat", label="chocolate", phrase="a tray of chocolate"))
    chocolate.meters["melted"] = 1 if params.activity == "chocolate" else 0

    _story_intro(world, hero, worker, activity)
    _story_problem(world, hero, worker, mystery)
    _story_clue(world, hero, activity, mystery)
    world.facts["story_answer"] = mystery.answer
    if solve_mystery(world, mystery, clue_seen=True):
        _story_resolution(world, hero, worker, mystery)
    propagate(world)
    world.facts.update(hero=hero, worker=worker, chocolate=chocolate, activity=activity, mystery=mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f"Write a funny short story for a child named {hero.id} who is curious about chocolate labor.",
        f"Tell a comedy story where {hero.id} sees a glowering worker and solves a mystery to do with chocolate.",
        f"Write a gentle mystery story with the words labor, chocolate, and glower in a child-friendly way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    worker = f["worker"]
    mystery = f["mystery"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep looking around the room?",
            answer=f"{hero.id} was curious and wanted to solve the mystery about the empty tray.",
        ),
        QAItem(
            question=f"What did the worker do when the tray was gone?",
            answer=f"The worker glowered at first because the missing chocolate looked alarming.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The chocolate had been moved to the cooler so it would not melt.",
        ),
        QAItem(
            question=f"What kind of work was happening at {world.setting.place}?",
            answer=f"People were doing chocolate labor, which meant careful work with sweets and trays.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more.",
        ),
        QAItem(
            question="What does a glower mean?",
            answer="A glower is a very stern, unhappy look on someone's face.",
        ),
        QAItem(
            question="Why do people cool chocolate?",
            answer="Chocolate is cooled so it stays firm and does not melt into a sticky puddle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- curious_person(X).
mystery_solved(M) :- clue_seen(M), answer_known(M).
glower(X) :- stern(X).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("answer_known", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    ok = bool(asp.atoms(model, "mystery_solved"))
    if ok:
        print("OK: ASP rules are syntactically alive.")
        return 0
    print("MISMATCH: no ASP conclusion.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


CURATED = [
    StoryParams(place="bakery", activity="labor", mystery="solve", name="Mina", worker="baker", trait="curious"),
    StoryParams(place="cafe", activity="chocolate", mystery="solve", name="Toby", worker="chef", trait="bouncy"),
    StoryParams(place="kitchen", activity="labor", mystery="solve", name="Lena", worker="parent", trait="nosy"),
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show mystery_solved/1."))
        return
    if args.asp:
        try:
            combos = asp_valid()
        except Exception as e:
            raise SystemExit(str(e))
        print(f"{len(combos)} ASP facts shown.")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 50:
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
