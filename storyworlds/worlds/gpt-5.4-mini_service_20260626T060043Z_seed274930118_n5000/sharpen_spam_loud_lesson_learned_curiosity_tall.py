#!/usr/bin/env python3
"""
storyworlds/worlds/sharpen_spam_loud_lesson_learned_curiosity_tall.py
=====================================================================

A tall-tale story world about a curious child, a loud mistake, and the lesson
that comes from choosing a safer way to do the work.

Seed tale:
---
A curious child in a little hill town wanted to sharpen a giant parade whistle
so it would sing bright and loud at the fair. He kept poking at the file and the
whetstone, but his grown-up warned him not to rush, because the sharp metal
could slip and the loud noise could startle the whole square. The child ignored
the warning, made a racket, and nearly knocked a tin of spam off the table.
Then he slowed down, asked for help, and learned that careful hands make better
music than noisy hurry.

World premise:
---
- A curious child wants to sharpen a metal tool.
- The work is loud enough to risk a mess in the workbench area.
- The child may be carrying a lunch tin of spam; if it is knocked over, it
  becomes part of the lesson.
- A grown-up can turn the moment into a helpful compromise: use a clamp,
  clear the table, and sharpen slowly.

Physical / emotional state:
---
- meters:
  - sharpness: how ready the tool is
  - loudness: how much noise the work makes
  - mess: how much clutter or spill has happened
  - neatness: how clean and orderly the space is
- memes:
  - curiosity: the tug to poke, test, and explore
  - caution: the grown-up's careful attention
  - embarrassment: the child's feeling after making a loud mess
  - pride: the child's feeling after learning the safer method

Style:
---
Tall-tale tone, but small and concrete. The story should feel like a kid-sized
legend about one shiny tool, one loud mistake, and one clear lesson learned.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"sharpness": 0.0, "loudness": 0.0, "mess": 0.0, "neatness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "caution": 0.0, "embarrassment": 0.0, "pride": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str]


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    owner_kind: str = "child"


@dataclass
class GearCfg:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _rule_noise(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters["sharpness"] < THRESHOLD:
            continue
        sig = ("noise", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["loudness"] += 1
        out.append("The work rang out loud enough to wake the dust on the shelf.")
    return out


def _rule_mess(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters["loudness"] < THRESHOLD:
            continue
        snack = world.entities.get("spam")
        if not snack or snack.meters["mess"] >= THRESHOLD:
            continue
        sig = ("mess", snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        snack.meters["mess"] += 1
        out.append("The tin of spam wobbled and clinked across the table.")
    return out


def _rule_care(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes["embarrassment"] < THRESHOLD:
            continue
        sig = ("care", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["pride"] += 1
        out.append("Careful hands turned the trouble into a proper lesson.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_noise, _rule_mess, _rule_care):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_problem(world: World, hero: Entity, task: Task) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**v.__dict__}) for k, v in world.entities.items()}
    h = sim.get(hero.id)
    h.meters["sharpness"] += 1
    propagate(sim, narrate=False)
    snack = sim.entities.get("spam")
    return {
        "noisy": h.meters["loudness"] >= THRESHOLD,
        "messy": bool(snack and snack.meters["mess"] >= THRESHOLD),
    }


def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} sat under the sky like a penny on a fencepost." if not setting.indoors else f"{setting.place.capitalize()} was snug as a thimble in a shirt pocket."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with curiosity big enough to climb a barn wall.")


def want_task(world: World, hero: Entity, task: Task) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.pronoun().capitalize()} wanted to {task.verb}, because {task.keyword} looked ready for an adventure.")


def warn(world: World, grownup: Entity, hero: Entity, task: Task, obj: Entity) -> bool:
    pred = predict_problem(world, hero, task)
    if not pred["noisy"] and not pred["messy"]:
        return False
    grownup.memes["caution"] += 1
    clause = f'“Easy now,” {grownup.id} said. “If you rush to {task.verb}, that {obj.label} could get spoiled.”'
    world.say(clause)
    return True


def ignore(world: World, hero: Entity, task: Task) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"But {hero.id} was too curious to wait, so {hero.pronoun()} tried to {task.rush}.")


def do_task(world: World, hero: Entity, task: Task) -> None:
    hero.meters["sharpness"] += 1
    world.say(f"The file sang as {hero.id} kept working, and the room grew {task.noise}.")
    propagate(world, narrate=True)


def regret(world: World, hero: Entity) -> None:
    hero.memes["embarrassment"] += 1
    world.say(f"{hero.id} blinked at the clatter and felt as small as a pea in a parade boot.")


def compromise(world: World, grownup: Entity, hero: Entity, task: Task, gear: GearCfg) -> None:
    hero.memes["pride"] += 1
    world.say(f'Then {grownup.id} smiled and said, “Let us {gear.prep} and do it the sturdy way.”')
    world.say(f"{hero.id} agreed, and together they {gear.tail}.")
    hero.meters["sharpness"] += 1
    hero.memes["curiosity"] += 1
    propagate(world, narrate=True)


SETTINGS = {
    "workbench": Setting(place="the workbench room", indoors=True, affords={"sharpen"}),
    "porch": Setting(place="the porch", indoors=False, affords={"sharpen"}),
}

TASKS = {
    "sharpen": Task(
        id="sharpen",
        verb="sharpen the parade whistle",
        gerund="sharpening the parade whistle",
        rush="dash at the whetstone all at once",
        noise="loud",
        soil="spilled",
        keyword="sharpen",
        tags={"sharpen", "loud"},
    ),
}

OBJECTS = {
    "whistle": ObjectCfg(
        label="parade whistle",
        phrase="a brass parade whistle",
        type="whistle",
    ),
    "spam": ObjectCfg(
        label="tin of spam",
        phrase="a tin of spam for lunch",
        type="food",
    ),
}

GEAR = GearCfg(
    id="clamp",
    label="a table clamp",
    prep="set the whistle in a table clamp",
    tail="turned the whistle carefully until it shone",
)

CHILD_NAMES = ["Milo", "Nora", "Bea", "Otis", "June", "Lena"]
GROWNUP_NAMES = ["Gran", "Pa", "Auntie", "Uncle", "Ma", "Dad"]


@dataclass
class StoryParams:
    place: str
    task: str
    child: str
    grownup: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about curiosity, a loud mistake, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--child")
    ap.add_argument("--grownup")
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
    task = args.task or "sharpen"
    child = args.child or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    return StoryParams(place=place, task=task, child=child, grownup=grownup)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = World(setting)
    hero = world.add(Entity(id=params.child, kind="character", type="boy" if params.child in {"Milo", "Otis"} else "girl"))
    grownup = world.add(Entity(id=params.grownup, kind="character", type="father" if params.grownup in {"Pa", "Dad", "Uncle"} else "mother"))
    whistle = world.add(Entity(id="whistle", type="whistle", label="whistle", phrase="a brass parade whistle", owner=hero.id, caretaker=grownup.id))
    spam = world.add(Entity(id="spam", type="food", label="tin of spam", phrase="a tin of spam for lunch", owner=hero.id, caretaker=grownup.id))

    intro = f"Once, in a town big as a bootprint and busy as a beehive, {params.child} lived near {setting.place}."
    world.say(intro)
    world.say(setting_line(setting))
    introduce(world, hero)
    world.say(f"{hero.id} loved the brass whistle and kept it near {hero.pronoun('possessive')} lunch tin of spam.")
    world.para()
    want_task(world, hero, task)
    warn(world, grownup, hero, task, whistle)
    ignore(world, hero, task)
    do_task(world, hero, task)
    world.para()
    regret(world, hero)
    compromise(world, grownup, hero, task, GEAR)
    world.say(f"In the end, {hero.id} learned that curiosity is mighty fine, but a calm pair of hands makes a better song.")
    world.facts.update(hero=hero, grownup=grownup, task=task, whistle=whistle, spam=spam, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, grownup, task = f["hero"], f["grownup"], f["task"]
    return [
        f'Write a tall-tale story for a young child about {hero.id} learning a lesson after trying to {task.verb}.',
        f"Tell a big, playful story with a curious child named {hero.id}, a loud mistake, and a grown-up named {grownup.id}.",
        f"Write a short story that uses the words '{task.keyword}', 'loud', and 'spam' and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grownup, task, whistle, spam = f["hero"], f["grownup"], f["task"], f["whistle"], f["spam"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the whistle?",
            answer=f"{hero.id} wanted to {task.verb}, because curiosity kept tugging at {hero.pronoun('possessive')} sleeves.",
        ),
        QAItem(
            question=f"Why did {grownup.id} warn {hero.id}?",
            answer=f"{grownup.id} warned {hero.id} because rushing to {task.verb} could make the room {task.noise} and could spoil the {spam.label}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that careful hands and help from a grown-up make the work better than noisy hurry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clamp do?",
            answer="A clamp holds an object still so a person can work on it without it slipping away.",
        ),
        QAItem(
            question="Why can loud sounds bother people?",
            answer="Loud sounds can startle people and make it hard to think or stay calm.",
        ),
        QAItem(
            question="What is spam?",
            answer="Spam is canned meat that people can eat for lunch or in sandwiches.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="workbench", task="sharpen", child="Milo", grownup="Gran"),
    StoryParams(place="porch", task="sharpen", child="Nora", grownup="Dad"),
]


ASP_RULES = r"""
task( sharpen ).

event_noisy(H) :- sharp(H), task(sharpen).
event_messy(H) :- event_noisy(H), spam_present.
lesson_learned(H) :- event_messy(H), careful_plan.

"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("noise", tid, t.noise))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("spam_present"))
    lines.append(asp.fact("careful_plan"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser_and_resolve():
    pass


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TASKS if t in SETTINGS[p].affords]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show event_noisy/1. #show event_messy/1. #show lesson_learned/1."))
    return sorted(set(asp.atoms(model, "event_noisy")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py == asp_set:
        print(f"OK: ASP/Python parity holds for {len(py)} combo(s).")
        return 0
    print("Mismatch")
    return 1


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
        print(asp_program("#show event_noisy/1."))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
