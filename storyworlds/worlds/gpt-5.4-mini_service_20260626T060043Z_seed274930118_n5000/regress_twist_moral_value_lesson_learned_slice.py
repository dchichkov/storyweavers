#!/usr/bin/env python3
"""
storyworlds/worlds/regress_twist_moral_value_lesson_learned_slice.py
=====================================================================

A small slice-of-life story world about a child doing an ordinary task,
hitting a twist when progress regresses, and learning a gentle moral value
by the end.

Seed tale to model:
---
A child starts a tiny daily job with confidence, then a small mistake makes
the job regress. A patient helper suggests a slower way. The child tries
again, fixes the problem, and learns a lesson about care, patience, and
not rushing.
---

The world is intentionally compact:
- one child, one helpful adult, one task, one small object, one setting
- physical meters track task progress and mess
- emotional memes track confidence, frustration, patience, pride, and warmth
- the story is narrated from the evolving world state, not from a frozen
  template with swapped nouns

The core narrative instruments are:
- Twist: a backward slip that reverses progress
- Moral Value: a child-facing value such as patience, care, or honesty
- Lesson Learned: the final remembered takeaway that changes future behavior
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    helper: Optional[str] = None
    plural: bool = False
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
class Setting:
    place: str
    time_of_day: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    progress_meter: str
    mess_meter: str
    twist: str
    moral_value: str
    lesson: str
    tag: str


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    risky_when: str = ""


@dataclass
class StoryParams:
    setting: str
    task: str
    object: str
    name: str
    gender: str
    helper: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _do_task(world: World, actor: Entity, task: Task, obj: Entity, narrate: bool = True) -> None:
    _inc(actor, task.progress_meter, 1.0)
    _mem(actor, "confidence", 1.0)
    _mem(actor, "patience", 0.5)
    if narrate:
        world.say(f"{actor.id} began to {task.verb} with a neat little smile.")
    propagate(world, narrate=narrate)


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("progress", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("twist", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["progress"] = max(0.0, actor.meters.get("progress", 0.0) - 1.0)
        _mem(actor, "frustration", 1.0)
        _mem(actor, "confidence", -0.5)
        out.append(f"Then came the twist: a small mistake made the progress regress.")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.memes.get("patience", 0.0) < THRESHOLD:
            continue
        sig = ("moral", actor.id)
        if sig in world.fired:
            continue
        if actor.memes.get("frustration", 0.0) < THRESHOLD:
            continue
        world.fired.add(sig)
        _mem(actor, "warmth", 1.0)
        out.append("The helper reminded them that a careful, slow try was kinder than a rushed one.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("progress", 0.0) < 2.0:
            continue
        if actor.memes.get("warmth", 0.0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1.0
        out.append("By the end, the child remembered the lesson learned: patience kept little jobs from slipping backward.")
    return out


CAUSAL_RULES = [
    Rule("twist", _r_twist),
    Rule("moral", _r_moral),
    Rule("lesson", _r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_regress(world: World, actor: Entity, task: Task, obj: Entity) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, sim.get(obj.id), narrate=False)
    return sim.get(actor.id).meters.get("progress", 0.0) < 2.0


SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="morning", afford={"tidy", "bake"}),
    "laundry_room": Setting(place="the laundry room", time_of_day="afternoon", afford={"fold"}),
    "garden_shed": Setting(place="the garden shed", time_of_day="evening", afford={"sort"}),
}

TASKS = {
    "tidy": Task(
        id="tidy",
        verb="tidy the table",
        gerund="tidying the table",
        rush="sweep too fast",
        progress_meter="progress",
        mess_meter="mess",
        twist="a bowl tipped and crumbs slid back across the cloth",
        moral_value="patience",
        lesson="slow steps keep a clean space tidy",
        tag="cleaning",
    ),
    "fold": Task(
        id="fold",
        verb="fold the laundry",
        gerund="folding the laundry",
        rush="pull the shirt corners too hard",
        progress_meter="progress",
        mess_meter="mess",
        twist="one shirt slipped open again after being folded neatly",
        moral_value="care",
        lesson="small careful folds make the pile stay neat",
        tag="home",
    ),
    "sort": Task(
        id="sort",
        verb="sort the crayons",
        gerund="sorting the crayons",
        rush="dump the box in a hurry",
        progress_meter="progress",
        mess_meter="mess",
        twist="the colors mixed into one jumbled pile",
        moral_value="order",
        lesson="taking turns and sorting slowly keeps things easy to find",
        tag="play",
    ),
}

OBJECTS = {
    "table": ObjectDef("table", "table", "a little tablecloth", "cloth", "table", risky_when="crumbs"),
    "laundry": ObjectDef("laundry", "laundry", "a stack of folded shirts", "clothes", "basket", plural=True, risky_when="wrinkles"),
    "crayons": ObjectDef("crayons", "crayons", "a box of crayons", "box", "shelf", plural=True, risky_when="jumbled"),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Theo", "Ben"]
HELPERS = {"mother": "mother", "father": "father", "grandma": "grandma", "grandpa": "grandpa", "aunt": "aunt", "uncle": "uncle"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for t in setting.afford:
            for o in OBJECTS:
                if t == "tidy" and o == "table":
                    combos.append((s, t, o))
                if t == "fold" and o == "laundry":
                    combos.append((s, t, o))
                if t == "sort" and o == "crayons":
                    combos.append((s, t, o))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a twist, moral value, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=list(HELPERS))
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(setting=setting, task=task, object=obj, name=name, gender=gender, helper=helper)


def tell(setting: Setting, task: Task, objdef: ObjectDef, hero_name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={"progress": 0.0, "mess": 0.0}, memes={"confidence": 0.0}))
    adult = world.add(Entity(id=helper, kind="character", type=helper, label=helper))
    obj = world.add(Entity(id=objdef.id, type=objdef.type, label=objdef.label, phrase=objdef.phrase, plural=objdef.plural))
    hero.owner = obj.id
    obj.caretaker = adult.id

    world.say(f"On {setting.time_of_day} in {setting.place}, {hero.id} wanted to {task.verb}.")
    world.say(f"{hero.id} liked the quiet little job because it felt like helping.")
    world.para()
    world.say(f"{hero.id} started {task.gerund} beside {obj.phrase}.")
    _do_task(world, hero, task, obj, narrate=True)

    world.para()
    if predict_regress(world, hero, task, obj):
        world.say(f"But the twist came quickly: {task.twist}.")
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1.0
    _mem(hero, "frustration", 1.0)
    propagate(world, narrate=True)

    world.para()
    adult_ent = world.get(helper)
    world.say(f"{adult_ent.id} smiled and showed {hero.id} a slower way.")
    world.say(f"They took a breath, fixed the small problem, and tried again without rushing.")
    hero.meters["progress"] = max(hero.meters.get("progress", 0.0), 2.0)
    _mem(hero, "patience", 1.0)
    _mem(hero, "warmth", 1.0)
    propagate(world, narrate=True)

    world.para()
    world.say(f"In the end, {hero.id} finished the task and looked pleased with the neat result.")
    world.say(f"{hero.id} remembered the lesson learned: {task.lesson}.")
    world.facts.update(hero=hero, helper=adult_ent, obj=obj, task=task, setting=setting, lesson=task.lesson)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    obj = f["obj"]
    return [
        f'Write a short slice-of-life story for a young child about {hero.id} {task.gerund} and learning a gentle lesson.',
        f"Tell a simple story where a small task goes well at first, then regresses, and a helper shows a calmer way.",
        f'Write a child-friendly story that includes the word "regress" and ends with {hero.id} remembering the lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    obj = f["obj"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {setting.place}?",
            answer=f"{hero.id} was trying to {task.verb}.",
        ),
        QAItem(
            question=f"What happened when the work started to regress?",
            answer=f"A small mistake made the progress slip backward, and the helper gently showed a slower way.",
        ),
        QAItem(
            question=f"What did {hero.id} remember at the end?",
            answer=f"{hero.id} remembered the lesson learned: {task.lesson}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the twist?",
            answer=f"{helper.id} helped by staying calm and showing a careful way to keep going.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel proud at the end?",
            answer=f"{hero.id} felt proud because the job was finished neatly after trying again with patience.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does regress mean?",
            answer="To regress means to slide backward after making progress.",
        ),
        QAItem(
            question="What is patience?",
            answer="Patience means waiting calmly and taking your time instead of rushing.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the helpful idea someone remembers after an experience.",
        ),
    ]


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
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen).
setting(laundry_room).
setting(garden_shed).

affords(kitchen, tidy).
affords(kitchen, bake).
affords(laundry_room, fold).
affords(garden_shed, sort).

task(tidy).
task(fold).
task(sort).

object(table).
object(laundry).
object(crayons).

valid(S, T, O) :- affords(S, T), compat(T, O).
compat(tidy, table).
compat(fold, laundry).
compat(sort, crayons).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for t in sorted(SETTINGS[sid].afford):
            lines.append(asp.fact("affords", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("compat", "tidy", "table"))
    lines.append(asp.fact("compat", "fold", "laundry"))
    lines.append(asp.fact("compat", "sort", "crayons"))
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


CURATED = [
    StoryParams(setting="kitchen", task="tidy", object="table", name="Mia", gender="girl", helper="mother"),
    StoryParams(setting="laundry_room", task="fold", object="laundry", name="Leo", gender="boy", helper="grandma"),
    StoryParams(setting="garden_shed", task="sort", object="crayons", name="Nora", gender="girl", helper="father"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], OBJECTS[params.object], params.name, params.gender, params.helper)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, task, object) combos:\n")
        for s, t, o in combos:
            print(f"  {s:12} {t:8} {o:8}")
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
            header = f"### {p.name}: {p.task} in {p.setting} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
