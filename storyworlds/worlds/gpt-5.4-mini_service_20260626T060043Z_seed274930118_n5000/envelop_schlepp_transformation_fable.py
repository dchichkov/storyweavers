#!/usr/bin/env python3
"""
storyworlds/worlds/envelop_schlepp_transformation_fable.py
==========================================================

A small fable-style storyworld about a patient helper, a burdensome task, and a
gentle transformation.

Seed tale:
---
A little beetle named Bram lived beside a windy hill path. Every morning, he
would schlepp seeds up the slope for the other animals, even when the load made
his back ache. One day, a bright moth queen gave him a soft cloak and said,
"Let the cloak envelop you when the wind bites." Bram wore it and felt brave,
but the hill still felt heavy.

Then Bram met a worried caterpillar who wanted to cross the path before dark.
Bram wanted to help, yet he was too tired to schlepp both the seeds and the
caterpillar's leaf basket. He paused, listened, and tried a new way: he let the
cloak wrap around the basket, tied it with a vine, and rolled the load on a
round seed cart. The basket rode safely, the wind could not shake it, and Bram
felt his tiredness begin to change into pride.

From that day on, the animals said a wise helper is not the one who never gets
tired, but the one who finds a better shape for the work.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {
                "weight": 0.0,
                "wind": 0.0,
                "strain": 0.0,
                "miles": 0.0,
            }
        if not self.memes:
            self.memes = {
                "hope": 0.0,
                "pride": 0.0,
                "worry": 0.0,
                "tiredness": 0.0,
                "calm": 0.0,
                "change": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "mouse": ("he", "him", "his"),
            "beetle": ("he", "him", "his"),
            "moth": ("she", "her", "her"),
            "caterpillar": ("they", "them", "their"),
            "rabbit": ("she", "her", "her"),
            "fox": ("he", "him", "his"),
            "bird": ("she", "her", "her"),
        }
        sub, obj, pos = mapping.get(self.type, ("it", "it", "its"))
        return {"subject": sub, "object": obj, "possessive": pos}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill path"
    windy: bool = True
    affords: set[str] = field(default_factory=lambda: {"schlepp", "cross", "carry"})


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    burden: str
    risk: str
    weather_word: str
    keyword: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    covers: set[str]
    helps: set[str]
    tone: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.active_zone: set[str] = set()
        self.active_task: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.active_zone = set(self.active_zone)
        clone.active_task = self.active_task
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["weight"] < THRESHOLD:
            continue
        sig = ("strain", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["tiredness"] += 1
        actor.meters["strain"] += 1
        out.append(f"{actor.id} felt the load pressing hard.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if world.active_task != "schlepp":
        return out
    for actor in world.characters():
        if actor.memes["calm"] < THRESHOLD:
            continue
        if actor.memes["change"] >= THRESHOLD:
            continue
        sig = ("change", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["change"] += 1
        actor.memes["hope"] += 1
        out.append(f"A small change began inside {actor.id}.")
    return out


CAUSAL_RULES = [
    _r_strain,
    _r_transform,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.windy:
        return "The wind kept nudging the grass and making the path tremble."
    return "The path was still and quiet."


def task_harm(task: Task) -> str:
    return {
        "seeds": "the sacks could tear and spill",
        "leaf-basket": "the basket could tip and lose its leaves",
        "lantern": "the flame could wink out",
    }.get(task.id, "the burden could get ruined")


def can_use_transformation(task: Task, trans: Transformation) -> bool:
    return task.keyword in trans.helps and bool(task.zone & trans.covers)


def predict(world: World, actor: Entity, task: Task, item_id: str) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(actor.id), task, item_id, narrate=False)
    item = sim.entities[item_id]
    return {
        "ruined": item.meters.get("wind", 0) >= THRESHOLD and item.meters.get("protected", 0) < THRESHOLD,
        "change": sim.get(actor.id).memes["change"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who liked to help the other animals."
    )
    world.say(
        f"Most days {hero.pronoun().capitalize()} would {task.verb} for them, even when {task.burden}."
    )


def gift(world: World, giver: Entity, hero: Entity, trans: Transformation) -> None:
    hero.worn_by = hero.id
    hero.memes["hope"] += 1
    world.say(
        f"One day, a bright {giver.type} gave {hero.id} {trans.phrase}."
    )
    world.say(
        f'"Let the cloak {trans.action}," said the {giver.type}, "when the wind bites."'
    )


def arrive(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} saw {task.burden} waiting by the trail."
    )
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, task: Task, item: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to help, but {hero.pronoun('possessive')} first thought was that {task.risk}."
    )


def warning(world: World, hero: Entity, task: Task, item: Entity) -> bool:
    pred = predict(world, hero, task, item.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_ruin"] = task.risk
    world.say(
        f'"If you {task.verb}, {task.risk}," said the rabbit by the gate.'
    )
    return True


def do_task(world: World, actor: Entity, task: Task, item_id: str, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} does not support {task.verb}.")
    world.active_zone = set(task.zone)
    world.active_task = task.id
    actor.meters["weight"] += 1
    actor.meters["wind"] += 1 if world.setting.windy else 0
    actor.memes["calm"] += 1
    propagate(world, narrate=narrate)
    item = world.entities[item_id]
    if actor.memes["change"] >= THRESHOLD and item.meters.get("protected", 0) >= THRESHOLD:
        item.meters["protected"] = 1


def choose_transformation(task: Task, item: Entity) -> Transformation:
    for t in TRANSFORMATIONS:
        if can_use_transformation(task, t):
            return t
    raise StoryError("No transformation in this world honestly fits the burden.")


def resolve(world: World, hero: Entity, task: Task, item: Entity, trans: Transformation) -> None:
    hero.memes["calm"] += 1
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    item.meters["protected"] = 1
    world.say(
        f"{hero.id} paused, listened, and tried a new way."
    )
    world.say(
        f"{hero.id} let the cloak {trans.action} the {item.label}, tied it with a vine, and rolled the load on a round seed cart."
    )
    world.say(
        f"Then the {item.label} rode safely, the wind could not shake it, and {hero.id} felt {trans.result}."
    )
    world.say(
        f"From that day on, the animals said a wise helper is not the one who never gets tired, but the one who finds a better shape for the work."
    )


SETTING = Setting()

TASKS = {
    "schlepp": Task(
        id="schlepp",
        verb="schlepp seeds up the hill",
        gerund="schlepping seeds up the hill",
        burden="the sacks were heavy",
        risk="the wind could shake the sacks loose",
        weather_word="windy",
        keyword="schlepp",
        zone={"back", "shoulders"},
        tags={"work", "wind"},
    ),
    "carry": Task(
        id="carry",
        verb="carry berries across the bridge",
        gerund="carrying berries across the bridge",
        burden="the basket was lopsided",
        risk="the basket could tip",
        weather_word="breezy",
        keyword="carry",
        zone={"hands", "arms"},
        tags={"work"},
    ),
}

TRANSFORMATIONS = [
    Transformation(
        id="cloak",
        label="cloak",
        phrase="a soft cloak that could envelop the cold shoulders",
        action="envelop",
        result="brave and light",
        covers={"back", "shoulders", "chest"},
        helps={"schlepp"},
        tone="gentle",
    ),
    Transformation(
        id="wrap",
        label="wrap",
        phrase="a warm wrap that could envelop the whole bundle",
        action="envelop",
        result="steady and glad",
        covers={"hands", "arms", "back", "shoulders"},
        helps={"carry"},
        tone="gentle",
    ),
]

CHARACTER_NAMES = ["Bram", "Pip", "Tess", "Milo", "Nia", "Otis"]
GIVERS = [
    ("moth", "moth queen"),
    ("rabbit", "old rabbit"),
    ("bird", "nesting bird"),
]

ITEMS = {
    "seeds": Entity(id="seeds", type="thing", label="seeds", phrase="heavy seed sacks", plural=True),
    "leafbasket": Entity(id="leafbasket", type="thing", label="leaf basket", phrase="a leaf basket"),
    "lantern": Entity(id="lantern", type="thing", label="lantern", phrase="a small lantern"),
}


@dataclass
class StoryParams:
    task: str
    hero_name: str
    hero_type: str
    giver_type: str
    item: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for task_id, task in TASKS.items():
        for trans in TRANSFORMATIONS:
            if task.keyword in trans.helps:
                combos.append((task_id, trans.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    item = f["item"]
    trans = f["transformation"]
    return [
        f'Write a short fable for children about "{task.keyword}" and the word "envelop".',
        f"Tell a gentle animal story where {hero.id} must {task.verb}, but a soft {trans.label} helps.",
        f"Write a fable about hard work, a windy path, and a clever way to keep the {item.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    item = f["item"]
    trans = f["transformation"]
    giver = f["giver"]
    return [
        QAItem(
            question=f"Who was the little helper in the story?",
            answer=f"The little helper was {hero.id}, a kind {hero.type} who wanted to help the other animals.",
        ),
        QAItem(
            question=f"What heavy job did {hero.id} need to do?",
            answer=f"{hero.id} needed to {task.verb}. The sacks were heavy, and the wind could shake them loose.",
        ),
        QAItem(
            question=f"What gift helped {hero.id} face the wind?",
            answer=f"{giver.label.capitalize()} gave {hero.id} {trans.phrase}, and that helped the helper find a better way to work.",
        ),
        QAItem(
            question=f"What did {hero.id} do to keep the {item.label} safe?",
            answer=f"{hero.id} let the cloak envelop the {item.label}, tied it with a vine, and rolled the load on a round seed cart.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave, proud, and lighter because the work changed shape instead of getting harder.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to envelop something?",
            answer="To envelop something means to wrap around it or cover it completely.",
        ),
        QAItem(
            question="What does it mean to schlepp something?",
            answer="To schlepp something means to carry or drag a heavy load with effort.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or way of being into another.",
        ),
        QAItem(
            question="Why can wind make work harder?",
            answer="Wind can push, wobble, and shake things, so carrying a load becomes more difficult and less steady.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    giver_label = next(lbl for typ, lbl in GIVERS if typ == params.giver_type)
    giver = world.add(Entity(id="giver", kind="character", type=params.giver_type, label=giver_label))
    task = TASKS[params.task]
    trans = next(t for t in TRANSFORMATIONS if t.id == "cloak")
    item = world.add(copy.deepcopy(ITEMS[params.item]))
    item.caretaker = hero.id
    item.owner = hero.id
    world.facts.update(hero=hero, giver=giver, task=task, transformation=trans, item=item)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    giver = world.get("giver")
    task = TASKS[params.task]
    item = world.get(params.item)
    trans = choose_transformation(task, item)

    introduce(world, hero, task)
    world.para()
    gift(world, giver, hero, trans)
    arrive(world, hero, task)
    wants(world, hero, task, item)
    warning(world, hero, task, item)
    world.para()
    resolve(world, hero, task, item, trans)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing" and e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: envelop, schlepp, and transformation.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--hero-type", choices=["beetle", "mouse", "rabbit", "bird"])
    ap.add_argument("--giver-type", choices=[g[0] for g in GIVERS])
    ap.add_argument("--item", choices=ITEMS)
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
    task = args.task or rng.choice(list(TASKS))
    hero_name = args.name or rng.choice(CHARACTER_NAMES)
    hero_type = args.hero_type or rng.choice(["beetle", "mouse"])
    giver_type = args.giver_type or rng.choice([g[0] for g in GIVERS])
    item = args.item or rng.choice(list(ITEMS))
    if task not in TASKS:
        raise StoryError("Unknown task.")
    if task == "schlepp" and item != "seeds":
        raise StoryError("This story's schlepp turn works best with seeds.")
    return StoryParams(task=task, hero_name=hero_name, hero_type=hero_type, giver_type=giver_type, item=item)


ASP_RULES = r"""
task(task_schlepp).
task(task_carry).

transformation(cloak).
transformation(wrap).

helps(cloak,schlepp).
helps(wrap,carry).

compatible(T, X) :- task(T), transformation(X), helps(X, K), task_key(T, K).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", f"task_{task_id}"))
        lines.append(asp.fact("task_key", f"task_{task_id}", task.keyword))
    for trans in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", trans.id))
        for h in sorted(trans.helps):
            lines.append(asp.fact("helps", trans.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_story_combos() -> list[tuple[str, str]]:
    return sorted(valid_combos())


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python for {len(py)} combos.")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("only Python:", sorted(py - cl))
    if cl - py:
        print("only ASP:", sorted(cl - py))
    return 1


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
    StoryParams(task="schlepp", hero_name="Bram", hero_type="beetle", giver_type="moth", item="seeds"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
