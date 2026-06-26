#!/usr/bin/env python3
"""
storyworlds/worlds/pane_stale_procrastinate_kindness_foreshadowing_animal_story.py
===================================================================================

A small animal-story world about a creature who keeps putting off a chore,
notices a warning sign, and is helped by a kind friend before stale food goes to
waste.

Seed premise:
---
A little animal keeps procrastinating about cleaning a sunny window pane. While
it waits, a loaf goes stale on the sill. A kind helper notices a crack in the
pane and foreshadows trouble, so the animals work together before the breeze
makes a mess.

This world keeps the prose child-facing and concrete while the simulated state
drives the turn from delay to action.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Shared result containers: eager import, per contract.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "mouse", "rabbit", "fox", "dog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    delay_verb: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    result: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting(place="the cottage", affords={"clean_pane", "bake"}),
    "barn": Setting(place="the barn", affords={"clean_pane", "feed"}),
    "treehouse": Setting(place="the treehouse", affords={"clean_pane", "rest"}),
}

TASKS = {
    "clean_pane": Task(
        id="clean_pane",
        verb="clean the pane",
        gerund="cleaning the pane",
        delay_verb="keep putting off cleaning the pane",
        risk="a crack would let in a chilly draft",
        keyword="pane",
        tags={"pane", "foreshadowing"},
    ),
    "bake": Task(
        id="bake",
        verb="bake bread",
        gerund="baking bread",
        delay_verb="keep waiting before baking",
        risk="the loaf would go stale on the sill",
        keyword="stale",
        tags={"stale"},
    ),
    "feed": Task(
        id="feed",
        verb="feed the animals",
        gerund="feeding the animals",
        delay_verb="hesitate before feeding",
        risk="the bowls would sit empty too long",
        keyword="kindness",
        tags={"kindness"},
    ),
}

PRIZES = {
    "loaf": Prize(label="loaf", phrase="a warm brown loaf", region="sill"),
    "cloth": Prize(label="cloth", phrase="a soft cleaning cloth", region="paw"),
}

HELPERS = {
    "squirrel": Helper(
        id="squirrel",
        label="a squirrel friend",
        offer="bring a cleaning cloth and point at the crack",
        result="help them clean the pane before the breeze slipped in",
        covers={"pane"},
        guards={"draft"},
    ),
    "rabbit": Helper(
        id="rabbit",
        label="a rabbit friend",
        offer="share a fresh loaf and nudge them to act",
        result="help them keep the bread from going stale",
        covers={"sill"},
        guards={"stale"},
    ),
}

NAMES = ["Milo", "Pip", "Toby", "Mina", "Lulu", "Nori", "Juno", "Clover"]
KINDS = ["cat", "kitten", "mouse", "rabbit", "fox", "dog"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero_name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _ensure(m: dict, key: str) -> float:
    if key not in m:
        m[key] = 0.0
    return m[key]


def _inc(m: dict, key: str, amt: float = 1.0) -> None:
    m[key] = _ensure(m, key) + amt


def _is_stale(world: World) -> bool:
    loaf = world.entities.get("prize")
    return bool(loaf and loaf.meters.get("stale", 0.0) >= THRESHOLD)


def _has_draft(world: World) -> bool:
    pane = world.entities.get("pane")
    return bool(pane and pane.meters.get("cracked", 0.0) >= THRESHOLD)


# ---------------------------------------------------------------------------
# World model rules
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False

        # Delay -> stale bread on the sill
        loaf = world.entities.get("prize")
        if loaf and loaf.meters.get("waiting", 0.0) >= THRESHOLD:
            sig = ("stale", loaf.id)
            if sig not in world.fired:
                world.fired.add(sig)
                _inc(loaf.meters, "stale", 1.0)
                out.append("The loaf went stale on the sill.")

        # Crack -> draft
        pane = world.entities.get("pane")
        if pane and pane.meters.get("cracked", 0.0) >= THRESHOLD:
            sig = ("draft", pane.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("A chilly draft slipped through the crack.")

        # Kindness lowers worry and gets action moving
        hero = world.entities.get("hero")
        helper = world.entities.get(world.facts.get("helper_id", ""))
        if hero and helper and hero.memes.get("worry", 0.0) >= THRESHOLD and helper.memes.get("kindness", 0.0) >= THRESHOLD:
            sig = ("resolve", hero.id)
            if sig not in world.fired:
                world.fired.add(sig)
                hero.memes["worry"] = 0.0
                hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
                out.append("Kindness helped the little animal begin at last.")

        if out:
            changed = False
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, trait: str) -> None:
    world.say(f"{hero.id} was a {trait} little {hero.type} who lived at {world.setting.place}.")
    world.say(f"{hero.id} liked to notice tiny things, like crumbs, wind, and shiny window panes.")


def setup(world: World, hero: Entity, task: Task, prize: Prize) -> None:
    world.say(f"{hero.id} wanted to {task.verb}, but {hero.pronoun('subject')} kept meaning to do it later.")
    world.say(f"On the sill sat {prize.phrase}, waiting for the day to begin.")


def foreshadow(world: World, hero: Entity, task: Task) -> None:
    pane = world.entities["pane"]
    _inc(pane.meters, "cracked", 1.0)
    _inc(hero.memes, "worry", 1.0)
    world.say(f"Then {hero.id} noticed a tiny crack in the pane.")
    world.say(f"{hero.id} knew that if it stayed there, {task.risk}.")


def procrastinate(world: World, hero: Entity, task: Task, prize: Prize) -> None:
    _inc(world.entities["prize"].meters, "waiting", 1.0)
    _inc(hero.memes, "delay", 1.0)
    world.say(f"Still, {hero.id} chose to procrastinate and kept putting off the work.")
    world.say(f"While {hero.id} waited, the loaf began to turn stale.")


def kindness_turn(world: World, helper: Entity, hero: Entity, helper_def: Helper) -> None:
    _inc(helper.memes, "kindness", 1.0)
    world.say(f"Then {helper.id} came by and showed kindness.")
    world.say(f"{helper.id} offered to {helper_def.offer}.")
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    propagate(world, narrate=False)


def resolve(world: World, hero: Entity, helper: Entity, helper_def: Helper, task: Task, prize: Prize) -> None:
    pane = world.entities["pane"]
    loaf = world.entities["prize"]
    _inc(hero.memes, "action", 1.0)
    pane.meters["cracked"] = 0.0
    loaf.meters["waiting"] = 0.0
    loaf.meters["stale"] = 0.0
    world.say(f"At last, {hero.id} and {helper.id} worked together.")
    world.say(f"They fixed the pane, and the chilly draft was gone.")
    world.say(f"Then they finished {task.gerund}, and the loaf stayed fresh instead of stale.")
    world.say(f"In the end, {hero.id} felt proud for acting before the day slipped away.")


# ---------------------------------------------------------------------------
# Full story construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, task: Task, prize: Prize, hero_name: str, hero_type: str, helper_id: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type))
    helper = world.add(Entity(id="helper", kind="character", type="rabbit"))
    pane = world.add(Entity(id="pane", type="pane", label="pane"))
    loaf = world.add(Entity(id="prize", type="loaf", label="loaf", phrase=prize.phrase))
    world.facts["helper_id"] = "helper"

    hero.id = hero_name
    helper.id = helper_id

    introduce(world, hero, trait)
    setup(world, hero, task, prize)
    world.para()
    foreshadow(world, hero, task)
    procrastinate(world, hero, task, prize)
    world.para()
    kindness_turn(world, helper, hero, HELPERS[helper_id])
    resolve(world, hero, helper, HELPERS[helper_id], task, prize)

    world.facts.update(
        hero=hero,
        helper=helper,
        pane=pane,
        prize=loaf,
        task=task,
        prize_cfg=prize,
        setting=setting,
        trait=trait,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write an animal story for young children that includes the words "pane", "stale", and "procrastinate".',
        f"Tell a gentle story about {hero.id}, a little {hero.type}, who keeps procrastinating until a kind friend helps.",
        f"Write a short story with foreshadowing, where a crack in a pane warns that stale bread might happen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    prize = f["prize"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little {hero.type} living at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing at first?",
            answer=f"{hero.id} kept procrastinating and putting off {task.verb}.",
        ),
        QAItem(
            question=f"What warning did {hero.id} notice?",
            answer=f"{hero.id} noticed a tiny crack in the pane, which foreshadowed a chilly draft.",
        ),
        QAItem(
            question=f"What happened to the loaf while {hero.id} waited?",
            answer=f"The loaf went stale on the sill while {hero.id} delayed too long.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} showed kindness, offered help, and worked with {hero.id} to fix the pane and finish the job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pane?",
            answer="A pane is a flat piece of glass in a window or door.",
        ),
        QAItem(
            question="What does stale mean?",
            answer="Stale food is old and not fresh anymore.",
        ),
        QAItem(
            question="What does procrastinate mean?",
            answer="To procrastinate means to keep putting off something you should do now.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

at_risk(task(clean_pane), pane).
at_risk(task(bake), stale).
at_risk(task(feed), kindness).

delay_leads_to_stale(T) :- task(T), T = bake.
warning(T) :- at_risk(task(T), pane).
warning(T) :- at_risk(task(T), stale).

kind_fix(T) :- task(T), warning(T).
valid(Place, Task, Prize) :- setting(Place), task(Task), prize(Prize),
                             affords(Place, Task), at_risk(task(Task), _),
                             kind_fix(Task).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, task_id, prize_id))
    return combos


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about procrastination, kindness, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=KINDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=["quiet", "curious", "timid", "helpful", "gentle"])
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
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(sorted(SETTINGS[place].affords))
    prize = args.prize or rng.choice(list(PRIZES))
    hero_name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(KINDS)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(["quiet", "curious", "timid", "helpful", "gentle"])
    return StoryParams(place=place, task=task, prize=prize, hero_name=hero_name, hero_type=hero_type, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.hero_name, params.hero_type, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="cottage", task="clean_pane", prize="loaf", hero_name="Milo", hero_type="cat", helper="squirrel", trait="curious"),
    StoryParams(place="barn", task="feed", prize="cloth", hero_name="Pip", hero_type="mouse", helper="rabbit", trait="helpful"),
    StoryParams(place="treehouse", task="bake", prize="loaf", hero_name="Lulu", hero_type="fox", helper="rabbit", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
