#!/usr/bin/env python3
"""
storyworlds/worlds/rigger_conflict_bravery_fable.py
====================================================

A small fable-like story world about a rigger, a disagreement, and the brave
choice that turns trouble into help.

The seed image:
---
A village bridge hangs over a narrow river. A careful young rigger keeps the
ropes tight so travelers can cross. One day, a proud crow and a stubborn goat
both want the bridge at once. Their pushing shakes the planks, the rigger sees
the danger, and the rigger must choose whether to step in.

Causal shape:
---
- Conflict rises when two characters want the same narrow path.
- Bravery is a small action: speaking up, stepping close, and fixing the rope.
- If the rigger acts bravely, the bridge is steadied and the conflict softens.
- The ending should show the bridge safe and the village calmer.
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
# Data model
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the river bridge"
    details: str = "A narrow bridge of planks and ropes"
    affords: set[str] = field(default_factory=lambda: {"cross", "repair"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "bridge": Setting(
        place="the river bridge",
        details="The bridge was narrow, and the ropes sang softly in the wind.",
        affords={"cross", "repair"},
    ),
    "dock": Setting(
        place="the old dock",
        details="The dock boards were slick, and the water lapped below.",
        affords={"cross", "repair"},
    ),
    "hillpath": Setting(
        place="the hill path",
        details="The path was steep, with a leaning gate beside it.",
        affords={"cross", "repair"},
    ),
}

ACTIONS = {
    "cross": Action(
        id="cross",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="rush onto the planks",
        risk="shake the ropes",
        zone={"bridge"},
        keyword="bridge",
        tags={"bridge", "rope"},
    ),
    "cart": Action(
        id="cart",
        verb="pull the cart across",
        gerund="pulling the cart across",
        rush="push the cart forward",
        risk="strain the boards",
        zone={"bridge"},
        keyword="cart",
        tags={"bridge", "work"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a spare rope",
        phrase="a spare rope from the rigger's bag",
        covers={"bridge"},
        guards={"shake", "strain"},
        prep="lay a spare rope along the weak side",
        tail="laid the spare rope along the weak side",
    ),
    "peg": Tool(
        id="peg",
        label="wooden pegs",
        phrase="a handful of wooden pegs",
        covers={"bridge"},
        guards={"shake", "strain"},
        prep="drive in wooden pegs and tie the line tight",
        tail="drove in the wooden pegs and tied the line tight",
    ),
}

HEROES = ["Milo", "Rina", "Taro", "Lena", "Bram", "Mina"]
SECONDARIES = ["crow", "goat", "fox", "duck", "mule"]
TRAITS = ["careful", "bold", "kind", "patient", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, action: str) -> bool:
    return place in SETTINGS and action in ACTIONS and "bridge" in ACTIONS[action].zone


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in SETTINGS for a in ACTIONS if valid_combo(p, a)]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
bridge_action(A) :- action(A), zone(A, bridge).
valid(Place, Action) :- setting(Place), bridge_action(Action), affords(Place, Action).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
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


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def _do_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to {action.verb}, and the bridge trembled a little.")


def predict_tension(world: World, hero: Entity, action: Action) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    return sim.entities[hero.id].memes.get("impulse", 0.0) >= 1.0


def introduce(world: World, hero: Entity, helper: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'steady')} rigger who knew every knot "
        f"on {world.setting.place}."
    )
    world.say(
        f"{hero.id} liked quiet mornings, when the ropes hummed and the world stayed balanced."
    )
    world.say(
        f"One day, {helper.id} and a second traveler both wanted to go at once, and that was a problem."
    )


def conflict_scene(world: World, hero: Entity, helper: Entity, action: Action) -> None:
    hero.memes["concern"] = hero.memes.get("concern", 0.0) + 1
    helper.memes["push"] = helper.memes.get("push", 0.0) + 1
    world.say(
        f"{helper.id} stomped forward and {action.rush}, while the other traveler kept tugging the same way."
    )
    world.say(
        f"The planks {action.risk}, and the village birds went quiet."
    )
    world.say(
        f"{hero.id} saw the {action.keyword} danger and felt a small, brave lift in the chest."
    )


def brave_step(world: World, hero: Entity, action: Action) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"Instead of hiding, {hero.id} stepped onto the bridge and spoke in a calm voice."
    )
    world.say(
        f'"Please wait," {hero.pronoun()} said. "If you all rush, the bridge will not hold."'
    )


def fix_bridge(world: World, hero: Entity, action: Action, tool: Tool) -> None:
    world.say(
        f"{hero.id} reached for {tool.phrase} and chose the careful way."
    )
    world.say(
        f"{tool.prep.capitalize()}, and the shaking eased."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["conflict"] = 0.0


def resolve(world: World, hero: Entity, helper: Entity, action: Action) -> None:
    world.say(
        f"After that, {helper.id} waited, the other traveler crossed slowly, and the bridge stayed true."
    )
    world.say(
        f"{hero.id} smiled, because bravery had not meant loudness; it had meant doing the needed thing."
    )
    world.say(
        f"By dusk, the river moved on below, and everyone crossed one by one, safely and kindly."
    )


def tell(setting: Setting, action: Action, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="person"))
    helper = world.add(Entity(id=helper_name, kind="character", type="person"))
    hero.memes["trait_word"] = trait

    introduce(world, hero, helper, action)
    world.para()
    conflict_scene(world, hero, helper, action)
    world.para()
    brave_step(world, hero, action)
    tool = TOOLS["rope"] if action.id == "cross" else TOOLS["peg"]
    fix_bridge(world, hero, action, tool)
    resolve(world, hero, helper, action)

    world.facts.update(hero=hero, helper=helper, action=action, setting=setting, tool=tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    act = f["action"].verb
    place = f["setting"].place
    return [
        f"Write a short fable about a rigger named {hero} who must help when {helper} and another traveler create conflict on {place}.",
        f"Tell a gentle story where bravery means speaking up before {act} goes wrong.",
        f"Write a child-friendly fable about ropes, a bridge, and a brave choice that keeps everyone safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["action"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the rigger in the story?",
            answer=f"{hero.id} was the rigger who watched over {place} and knew how to keep it safe.",
        ),
        QAItem(
            question=f"What caused the conflict on {place}?",
            answer=f"The conflict began because {helper.id} and another traveler both tried to cross at the same time, and that made the bridge shake.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do?",
            answer=f"{hero.id} stepped onto the bridge, spoke calmly, and fixed the danger before anyone got hurt.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The bridge stayed steady, the travelers took turns, and everyone crossed safely by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a rigger do?",
            answer="A rigger ties, checks, and repairs ropes or lines so something can stay steady and safe.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous or afraid.",
        ),
        QAItem(
            question="Why do people take turns on a narrow bridge?",
            answer="People take turns on a narrow bridge so it does not get crowded or unsafe.",
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def explain_rejection(place: str, action: str) -> str:
    return f"(No story: {action} is not a reasonable action for {place} in this tiny bridge world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    action = args.action or rng.choice(sorted(ACTIONS))
    if not valid_combo(place, action):
        raise StoryError(explain_rejection(place, action))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(SECONDARIES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, hero=hero, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        params.hero,
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos_runtime() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a rigger, conflict, and bravery in a tiny fable."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=SECONDARIES)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="bridge", action="cross", hero="Milo", helper="goat", trait="careful"),
    StoryParams(place="dock", action="cross", hero="Rina", helper="crow", trait="bold"),
    StoryParams(place="hillpath", action="cart", hero="Lena", helper="fox", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos_runtime()
        print(f"{len(combos)} compatible combos:\n")
        for place, action in combos:
            print(f"  {place:10} {action}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
