#!/usr/bin/env python3
"""
Storyworld: a fairy-tale teamwork story with a freckled hero, a suspenseful
problem, and a happy ending.

This world models a tiny classical tale in which a small cast of typed
entities use both physical meters and emotional memes to resolve a problem
together. The featured word is "freckle".
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


# ---------------------------------------------------------------------------
# Core domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

HERO_NAMES = ["Mira", "Nell", "Poppy", "Lina", "Tessa", "Wren"]
HELPER_NAMES = ["Finn", "Hugo", "Jules", "Oren", "Pip", "Robin"]
CREATURE_NAMES = ["Sprite", "Moth", "Hare", "Mouse", "Bird", "Fox"]
SETTINGS = ["meadow", "moonlit woods", "stone bridge", "rose garden", "castle gate"]
TASKS = ["find the lost lantern", "mend the torn banner", "lift the cursed gate", "guide the lost lamb"]
FOILS = ["the fog", "the hush", "the twisting path", "the locked gate", "the dark ditch"]
TREASURES = ["a silver lantern", "a gold ribbon", "a tiny crown", "a little loaf", "a bright key"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    misty: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    name: str
    suspense: str
    teamwork_need: str
    danger: str
    fix: str
    keyword: str = "freckle"


@dataclass
class Treasure:
    label: str
    phrase: str
    risk_zone: str
    kind: str = "treasure"


@dataclass
class StoryParams:
    place: str
    task: str
    treasure: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0.0) + 1
        out.append("The air felt very still.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("hope", 0.0) < THRESHOLD or helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    helper.memes["courage"] = helper.memes.get("courage", 0.0) + 1
    out.append("Together they felt braver.")
    return out


def _r_happy_end(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    treasure = world.entities.get("treasure")
    if not hero or not treasure:
        return out
    if hero.memes.get("joy", 0.0) < THRESHOLD:
        return out
    sig = ("happy_end",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The night turned kind and bright.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_suspense, _r_teamwork, _r_happy_end):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, task: Task, treasure_cfg: Treasure, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=params.hero_type, label=params.hero_name,
        traits=["freckled", "gentle"],
        meters={"steps": 0.0},
        memes={"hope": 1.0, "fear": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=params.helper_type, label=params.helper_name,
        traits=["kind", "quick"],
        memes={"kindness": 1.0, "fear": 0.0, "joy": 0.0},
    ))
    treasure = world.add(Entity(
        id="treasure", kind="thing", type=treasure_cfg.kind, label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
    ))

    world.say(f"Once upon a time, in {setting.place}, there lived {hero.label}, a freckled little {hero.type}.")
    world.say(f"{hero.label} loved the old stories of brave friends who shared hard work, and {hero.pronoun('subject')} carried a warm hope in {hero.pronoun('possessive')} chest.")
    world.say(f"One evening, the villagers whispered that {task.suspense} at {setting.place}, and only teamwork could make it safe again.")
    world.para()
    world.say(f"{hero.label} went closer and saw {FOILS[0]} hiding the way. The darkness made even the {treasure.label} seem far away.")
    hero.memes["fear"] += 1
    propagate(world)
    world.say(f"Then {helper.label} arrived with a lantern and a steady voice. {helper.label} said, \"I will help you.\"")
    helper.memes["kindness"] += 1
    hero.memes["hope"] += 1
    world.say(f"Together, they chose {task.teamwork_need} so the danger would not win.")
    if task.id == "lantern":
        treasure.meters["found"] = 1
        world.say(f"{hero.label} held the lantern high while {helper.label} watched the path.")
    elif task.id == "banner":
        treasure.meters["mended"] = 1
        world.say(f"{helper.label} tied the torn ribbon, and {hero.label} tucked the last knot tight.")
    elif task.id == "gate":
        treasure.meters["opened"] = 1
        world.say(f"{hero.label} and {helper.label} pushed together until the gate gave a friendly creak.")
    else:
        treasure.meters["guided"] = 1
        world.say(f"{helper.label} sang softly while {hero.label} led the lamb by the lantern glow.")
    world.para()
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    propagate(world)
    world.say(f"In the end, {setting.place} was safe, {treasure.label} shone like a promise, and the freckled hero smiled beside a true friend.")
    world.facts.update(hero=hero, helper=helper, treasure=treasure, task=task, setting=setting)
    return world


TASKS_REGISTRY = {
    "lantern": Task(
        id="lantern",
        name="find the lost lantern",
        suspense="the lantern had gone missing before sunset",
        teamwork_need="one to search and one to light the way",
        danger="the dark path",
        fix="share the light",
    ),
    "banner": Task(
        id="banner",
        name="mend the torn banner",
        suspense="the royal banner hung in two pieces above the gate",
        teamwork_need="one to hold the cloth and one to tie the thread",
        danger="the windy tower",
        fix="hold it steady",
    ),
    "gate": Task(
        id="gate",
        name="lift the cursed gate",
        suspense="the castle gate would not open at dawn",
        teamwork_need="one to push and one to guide the wheels",
        danger="the stuck hinges",
        fix="push together",
    ),
    "lamb": Task(
        id="lamb",
        name="guide the lost lamb",
        suspense="a little lamb had wandered into the hush of the woods",
        teamwork_need="one to call softly and one to follow the bells",
        danger="the twisting brambles",
        fix="walk in step",
    ),
}

TREASURES = {
    "lantern": Treasure(label="lantern", phrase="a silver lantern", risk_zone="darkness"),
    "banner": Treasure(label="banner", phrase="a gold ribbon banner", risk_zone="wind"),
    "gate": Treasure(label="gate", phrase="a castle gate", risk_zone="stone"),
    "lamb": Treasure(label="lamb", phrase="a tiny lamb", risk_zone="woods"),
}

SETTINGS_REGISTRY = {
    "meadow": Setting(place="the moonlit meadow", affords={"lantern", "lamb"}),
    "woods": Setting(place="the moonlit woods", affords={"lantern", "lamb"}),
    "bridge": Setting(place="the stone bridge", affords={"banner", "gate"}),
    "garden": Setting(place="the rose garden", affords={"banner", "lantern"}),
    "castle": Setting(place="the castle gate", affords={"gate", "banner"}),
}


@dataclass
class Choice:
    kind: str
    place: str
    task: str
    treasure: str


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS_REGISTRY.items():
        for task_id in setting.affords:
            out.append((place, task_id, task_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world of freckled teamwork and suspense.")
    ap.add_argument("--place", choices=SETTINGS_REGISTRY)
    ap.add_argument("--task", choices=TASKS_REGISTRY)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "fairy", "knight"])
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
    combos = valid_combos()
    if args.place or args.task or args.treasure:
        combos = [c for c in combos if (args.place is None or c[0] == args.place)
                  and (args.task is None or c[1] == args.task)
                  and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches the given options.")
    place, task_id, treasure_id = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy", "princess", "prince"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "fairy", "knight"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        task=task_id,
        treasure=treasure_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task = f["hero"], f["helper"], f["task"]
    return [
        f'Write a short fairy tale about a freckled {hero.type} named {hero.label} and a kind {helper.type} who solve a problem together.',
        f"Tell a suspenseful but gentle story where {hero.label} and {helper.label} work as a team to {task.name}.",
        f'Write a happy-ending story that includes the word "freckle" and shows two friends helping each other in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, treasure = f["hero"], f["helper"], f["task"], f["treasure"]
    return [
        QAItem(
            question=f"Who is the freckled hero in the story?",
            answer=f"The freckled hero is {hero.label}, a little {hero.type} who wanted to help in {world.setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.label} with the problem?",
            answer=f"{helper.label} helped by joining in and using teamwork, so the two friends could solve the trouble together.",
        ),
        QAItem(
            question=f"What was the suspenseful problem at {world.setting.place}?",
            answer=f"The problem was that {task.suspense}, so the friends had to work carefully instead of hurrying alone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {treasure.label} was safe again, the danger was gone, and everyone felt happy and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do different parts of a job together.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important might happen soon, so you want to know what comes next.",
        ),
        QAItem(
            question="What is a freckle?",
            answer="A freckle is a tiny spot on a person's skin, often seen on faces, arms, or noses.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish the story safely or joyfully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS_REGISTRY[params.place], TASKS_REGISTRY[params.task], TREASURES[params.treasure], params)
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


ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- task_name(T).
treasure(X) :- treasure_name(X).

compatible(P,T) :- affords(P,T).
valid(P,T,X) :- compatible(P,T), treasure_for(T,X).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS_REGISTRY.items():
        lines.append(asp.fact("setting", pid))
        for task in sorted(s.affords):
            lines.append(asp.fact("affords", pid, task))
    for tid, t in TASKS_REGISTRY.items():
        lines.append(asp.fact("task_name", tid))
        lines.append(asp.fact("treasure_for", tid, tid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure_name", tid))
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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="woods", task="lantern", treasure="lantern", hero_name="Mira", hero_type="girl", helper_name="Pip", helper_type="fairy"),
    StoryParams(place="castle", task="gate", treasure="gate", hero_name="Nell", hero_type="princess", helper_name="Hugo", helper_type="knight"),
    StoryParams(place="bridge", task="banner", treasure="banner", hero_name="Lina", hero_type="boy", helper_name="Robin", helper_type="boy"),
    StoryParams(place="meadow", task="lamb", treasure="lamb", hero_name="Poppy", hero_type="girl", helper_name="Finn", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
