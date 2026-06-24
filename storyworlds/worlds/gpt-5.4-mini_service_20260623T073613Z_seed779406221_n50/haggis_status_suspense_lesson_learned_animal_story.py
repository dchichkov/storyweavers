#!/usr/bin/env python3
"""
storyworlds/worlds/haggis_status_suspense_lesson_learned_animal_story.py
========================================================================

A standalone story world for a tiny animal tale about haggis, status, suspense,
and a lesson learned.

Seed tale imagined from the prompt:
- A small animal wants to look important at a hill feast.
- It is trusted with a warm haggis and a shiny status ribbon.
- Suspense rises when the ribbon slips and the haggis teeters near a stream.
- A helper animal steadies the load.
- The lesson learned is that status is not the same as kindness, and careful
  help matters more than showing off.

The world uses typed entities with physical meters and emotional memes, a tiny
simulation that drives prose, plus an inline ASP twin for parity checking.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    hot: bool = False
    shiny: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "ewe", "hen"}
        male = {"boy", "father", "dad", "ram", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    feature: str
    hill: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location: str
    hot: bool = False
    shiny: bool = False
    edible: bool = False


@dataclass
class Role:
    id: str
    label: str
    type: str
    traits: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_risk: float = 0.0
        self.status_show: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.path_risk = self.path_risk
        c.status_show = self.status_show
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_slip(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        world.path_risk += 1
        out.append("__suspense__")
    return out


def _r_hot(world: World) -> list[str]:
    out = []
    h = world.entities.get("haggis")
    if h and h.meters["jostle"] >= THRESHOLD and h.meters["wobble"] >= THRESHOLD:
        sig = ("hotspill", h.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        h.meters["spill"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("slip", "social", _r_slip), Rule("hotspill", "physical", _r_hot)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def suspense_risk(world: World, hero: Entity, haggis: Entity) -> bool:
    return hero.meters["wobble"] >= THRESHOLD or haggis.meters["jostle"] >= THRESHOLD


def status_is_real(world: World, hero: Entity) -> bool:
    return hero.memes["kindness"] >= THRESHOLD and hero.memes["showoff"] < hero.memes["kindness"] + 1


def predict_spill(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["wobble"] += 1
    propagate(sim, narrate=False)
    h = sim.get("haggis")
    return {"spilled": h.meters["spill"] >= THRESHOLD, "fear": sum(e.memes["fear"] for e in sim.characters())}


def setup(world: World, hero: Entity, helper: Entity, haggis: Entity, badge: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {world.setting.place}, a little {hero.type} named {hero.id} wanted to look important."
    )
    world.say(
        f"{hero.id} wore {badge.label} and carried {haggis.label} for the hill feast."
    )
    world.say(
        f"The air by {world.setting.feature} smelled sharp and cozy, like a grand day waiting to begin."
    )


def start_suspense(world: World, hero: Entity, helper: Entity, haggis: Entity, badge: Entity) -> None:
    hero.meters["wobble"] += 1
    haggis.meters["jostle"] += 1
    world.say(
        f"But the path grew slick, and {badge.label} started to slide."
    )
    world.say(
        f"{helper.id} looked at the steep path and whispered, 'Easy now. That {haggis.label} is tipping.'"
    )


def warning(world: World, hero: Entity, helper: Entity, haggis: Entity) -> None:
    pred = predict_spill(world, hero)
    world.facts["predicted_spill"] = pred["spilled"]
    world.say(
        f"{helper.id} held out a steady paw. 'If you rush, the {haggis.label} could spill into the stream,' {helper.pronoun()} said."
    )


def choose_kindness(world: World, hero: Entity, helper: Entity, haggis: Entity, badge: Entity) -> None:
    hero.memes["showoff"] += 1
    world.say(f"{hero.id} slowed down and let {helper.id} share the load.")
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    haggis.meters["jostle"] = 0
    hero.meters["wobble"] = 0
    world.say(
        f"Together they balanced {badge.label} straight again and carried {haggis.label} one careful step at a time."
    )


def finish(world: World, hero: Entity, helper: Entity, haggis: Entity, badge: Entity) -> None:
    hero.memes["status"] += 1
    helper.memes["status"] += 1
    world.say(
        f"At the feast, everyone smiled at {hero.id} and {helper.id} because they arrived with the {haggis.label} safe and warm."
    )
    world.say(
        f"{hero.id} learned that true status came from helping well, not from looking grand."
    )
    world.say(
        f"In the end, {badge.label} shone on {hero.id}'s chest, and the {haggis.label} sat steaming beside the feast."
    )


def tell(setting: Setting, hero_cfg: Role, helper_cfg: Role, item_cfg: Item, badge_cfg: Item,
         hero_name: str = "Milo", helper_name: str = "Pip") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_cfg.type, label=hero_name, traits=list(hero_cfg.traits)))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_cfg.type, label=helper_name, traits=list(helper_cfg.traits)))
    haggis = world.add(Entity(id=item_cfg.id, type="food", label=item_cfg.label, edible=item_cfg.edible, hot=item_cfg.hot))
    badge = world.add(Entity(id=badge_cfg.id, type="thing", label=badge_cfg.label, shiny=badge_cfg.shiny))
    world.facts.update(hero=hero, helper=helper, haggis=haggis, badge=badge, setting=setting)

    setup(world, hero, helper, haggis, badge)
    world.para()
    start_suspense(world, hero, helper, haggis, badge)
    warning(world, hero, helper, haggis)
    if suspense_risk(world, hero, haggis):
        world.say("For a breath, nobody moved.")
    choose_kindness(world, hero, helper, haggis, badge)
    world.para()
    finish(world, hero, helper, haggis, badge)
    return world


SETTINGS = {
    "hill": Setting(place="the green hill", feature="the stream"),
    "village": Setting(place="the village square", feature="the stone fountain"),
    "orchard": Setting(place="the orchard path", feature="the little bridge"),
}

ROLES = {
    "sheep": Role(id="sheep", label="a sheep", type="sheep", traits={"gentle", "careful"}),
    "fox": Role(id="fox", label="a fox", type="fox", traits={"quick", "clever"}),
    "goat": Role(id="goat", label="a goat", type="goat", traits={"curious", "sturdy"}),
    "rabbit": Role(id="rabbit", label="a rabbit", type="rabbit", traits={"small", "bright"}),
}

ITEMS = {
    "haggis": Item(id="haggis", label="the haggis", phrase="a warm haggis", location="basket", hot=True, edible=True),
    "badge": Item(id="badge", label="a shiny status badge", phrase="a shiny status badge", location="pouch", shiny=True),
}

NAMES = ["Milo", "Pip", "Nia", "Bea", "Tuck", "Sage", "Dot", "Tia"]


@dataclass
class StoryParams:
    setting: str
    hero_role: str
    helper_role: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "haggis", "badge") for s in SETTINGS]


KNOWLEDGE = {
    "haggis": [("What is haggis?", "Haggis is a savory dish made from oats and spices, often served warm at a feast.")],
    "status": [("What is status?", "Status is how important or respected someone seems to others in a group.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of waiting to see what will happen next.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is something a character understands better after something happens.")],
}

KNOWLEDGE_ORDER = ["haggis", "status", "suspense", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes "{f["haggis"].label}" and a shiny sign of status.',
        f"Tell a suspenseful animal story where {f['hero'].id} nearly loses the {f['haggis'].label} on the hill, but learns a kinder way to act.",
        f"Write a simple lesson-learned tale with animals, haggis, and status that ends safely at a feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, haggis, badge = f["hero"], f["helper"], f["haggis"], f["badge"]
    return [
        QAItem(question=f"Who wanted to look important at the feast?", answer=f"{hero.id} wanted to look important and carried {haggis.label} with a shiny {badge.label}."),
        QAItem(question=f"What made the story feel suspenseful?", answer=f"The path grew slick and the {haggis.label} started to tip, so everyone had to move carefully."),
        QAItem(question=f"What lesson did {hero.id} learn?", answer=f"{hero.id} learned that real status comes from helping well, not from showing off."),
        QAItem(question=f"How did {helper.id} help?", answer=f"{helper.id} shared the load and steadied the {haggis.label} so it stayed warm and safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.hot:
            bits.append("hot")
        if e.shiny:
            bits.append("shiny")
        if e.edible:
            bits.append("edible")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
status_look(H) :- hero(H), has_badge(H).
suspense(H) :- hero(H), wobble(H), path_risk(R), R >= 1.
lesson_learned(H) :- hero(H), kindness(H), status_look(H).
valid_story(S) :- setting(S), haggis_item, badge_item.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("haggis_item"))
    lines.append(asp.fact("badge_item"))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    lines.append(asp.fact("story_topic", "haggis"))
    lines.append(asp.fact("story_topic", "status"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = asp.atoms(model, "valid_story")
    ok = bool(atoms) == bool(valid_combos())
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with haggis, status, suspense, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-role", choices=ROLES)
    ap.add_argument("--helper-role", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_role = args.hero_role or rng.choice(list(ROLES))
    helper_role = args.helper_role or rng.choice([r for r in ROLES if r != hero_role])
    hero_name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(setting=setting, hero_role=hero_role, helper_role=helper_role, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ROLES[params.hero_role], ROLES[params.helper_role], ITEMS["haggis"], ITEMS["badge"], params.hero_name, params.helper_name)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            p = StoryParams(setting=setting, hero_role="sheep", helper_role="goat", hero_name="Milo", helper_name="Pip")
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
