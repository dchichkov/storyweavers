#!/usr/bin/env python3
"""
storyworlds/worlds/chump_queer_proper_inner_monologue_quest_adventure.py
========================================================================

A standalone story world for a small Adventure-style domain built from the seed
words "chump", "queer", and "proper".

Premise:
A young underdog (the "chump") heads out on a quest with a queer friend and a
proper plan. The tension is not violence or danger from people, but whether the
chump can trust their own inner monologue, ask for help, and finish the quest
without losing the one object that makes the journey possible.

This world uses:
- typed entities with physical meters and emotional memes
- a simple forward rule engine
- an inner-monologue beat
- a quest beat
- a reasonableness gate
- inline ASP rules mirroring the Python gate
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
INNER_NOISE_LIMIT = 2.0
QUEST_PROGRESS_GOAL = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    quest_name: str
    affords: set[str] = field(default_factory=set)
    shelter: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    helps: set[str] = field(default_factory=set)
    at_risk: bool = True


@dataclass
class Companion:
    id: str
    label: str
    phrase: str
    trait: str
    monologue_style: str
    helps: set[str] = field(default_factory=set)


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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_query(world: World) -> list[str]:
    out: list[str] = []
    quest = world.facts["quest_item"]
    hero = world.facts["hero"]
    if hero.meters["travel"] >= QUEST_PROGRESS_GOAL and hero.meters["focus"] >= 1:
        sig = ("quest", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["quest_done"] += 1
            out.append(f"{hero.label_word.capitalize()} found the lost way at last.")
    if hero.memes["worry"] >= INNER_NOISE_LIMIT and hero.memes["courage"] >= 1:
        sig = ("calm", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
            hero.memes["resolve"] += 1
            out.append("__calm__")
    if quest.meters["lost"] >= THRESHOLD and hero.meters["quest_done"] >= THRESHOLD:
        sig = ("return", quest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            quest.carried_by = hero.id
            out.append(f"{hero.id} carried {quest.label_word} back home.")
    return out


CAUSAL_RULES = [Rule("quest_query", "social", _r_query)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_route(world: World, steps: int = 1) -> dict:
    sim = world.copy()
    hero = sim.facts["hero"]
    hero.meters["travel"] += steps
    propagate(sim, narrate=False)
    return {
        "done": hero.meters["quest_done"] >= THRESHOLD,
        "calm": hero.memes["resolve"] >= THRESHOLD,
    }


def valid_combo(place: Place, item: QuestItem, companion: Companion) -> bool:
    return item.at_risk and item.region in {"hands", "pack"} and bool(item.helps & companion.helps)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for cid, comp in COMPANIONS.items():
                if valid_combo(place, item, comp):
                    combos.append((pid, iid, cid))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    companion: str
    hero_name: str
    hero_gender: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "harbor": Place("harbor", "the harbor", "the silver key", affords={"walk", "ask"}),
    "market": Place("market", "the market lane", "the silver key", affords={"walk", "ask"}),
    "cave": Place("cave", "the cave path", "the silver key", affords={"walk", "ask"}, shelter=True),
}

ITEMS = {
    "key": QuestItem("key", "silver key", "a silver key on a blue cord", "mud", "hands", helps={"ask", "walk"}),
    "map": QuestItem("map", "folded map", "a folded map in a wax sleeve", "rain", "pack", helps={"walk", "ask"}),
    "lantern": QuestItem("lantern", "small lantern", "a small lantern with a brass latch", "dust", "hands", helps={"ask", "walk"}),
}

COMPANIONS = {
    "queer_guide": Companion("queer_guide", "queer guide", "a queer guide with a bright scarf", "queer", "gentle", helps={"ask", "walk"}),
    "proper_scout": Companion("proper_scout", "proper scout", "a proper scout with a tidy notebook", "proper", "careful", helps={"walk", "ask"}),
}

HERO_NAMES = ["Mina", "Jules", "Pip", "Ravi", "Nora", "Tess", "Arlo", "Sage"]
TRAITS = ["chump", "brave", "careful", "curious", "proper"]


def explain_rejection() -> str:
    return "(No story: this quest needs a companion who can help with the same task, and an item that can actually be carried on the road.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style quest story world with inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "person"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError(explain_rejection())
    place, item, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy", "person"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, companion=companion, hero_name=name, hero_gender=gender, trait=trait)


def tell(place: Place, item: QuestItem, companion: Companion, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    guide = world.add(Entity(companion.id, kind="character", type="person", label=companion.label, role="companion", traits=[companion.trait]))
    quest = world.add(Entity(item.id, kind="thing", type="thing", label=item.label, phrase=item.phrase, owner=hero.id))
    hero.meters["travel"] = 0.0
    hero.meters["focus"] = 0.0
    hero.meters["quest_done"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["resolve"] = 0.0
    quest.meters["lost"] = 1.0
    hero.attrs["quest_item"] = quest.id
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["quest_item"] = quest
    world.facts["companion"] = companion
    world.facts["place"] = place

    world.say(f"{hero.name if hasattr(hero,'name') else hero.id} was a {trait} chump who stood at {place.label} with {quest.label_word}.")
    world.say(f"{guide.label.capitalize()} looked queer in the best way, with a bright scarf and a proper smile.")
    world.say(f"{hero.id} wanted the quest to feel proper, but the road looked long.")

    world.para()
    hero.memes["worry"] += 1.0
    hero.memes["courage"] += 1.0
    world.say(f"Inside {hero.id}'s head, a small voice muttered, \"You can do this, even if you feel like a chump.\"")
    world.say(f"{guide.id} said they could ask, listen, and keep going step by proper step.")
    world.say(f"{hero.id} took one breath and started the quest.")
    hero.meters["travel"] += 1.0
    hero.meters["focus"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"They crossed on toward {place.quest_name} with {quest.label} held tight.")
    hero.meters["travel"] += 1.0
    hero.meters["focus"] += 1.0
    hero.memes["courage"] += 1.0
    propagate(world, narrate=True)

    if hero.meters["quest_done"] < THRESHOLD:
        world.para()
        world.say(f"At the end, {hero.id} found the missing way and learned that a proper quest can begin with a shaky chump.")
        hero.meters["quest_done"] = 1.0

    world.facts["done"] = hero.meters["quest_done"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    item = f["quest_item"]
    place = f["place"]
    return [
        f'Write an Adventure-style story for a 3-to-5-year-old about a chump who goes on a quest at {place.label} with a queer friend and a proper plan.',
        f"Tell a gentle quest story where {hero.id} hears an inner monologue, then keeps going with {comp.label} and {item.label}.",
        f'Write a story that includes the words "chump", "queer", and "proper" and ends with a quest success image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    item = f["quest_item"]
    place = f["place"]
    return [
        QAItem(question=f"Who went on the quest at {place.label}?", answer=f"{hero.id} went on the quest with {comp.label}. They carried {item.label} and kept going together."),
        QAItem(question=f"What did {hero.id} tell {the_inner()}?", answer=f"{hero.id} told {the_inner()} to be brave and keep the plan proper, even when the road felt hard."),
        QAItem(question=f"How did the quest end?", answer=f"It ended with {hero.id} finding the missing way and finishing the quest in a proper, happy way."),
    ]


def the_inner() -> str:
    return "the inner monologue"


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a journey with a goal to find, fix, or bring something back."),
        QAItem(question="What does inner monologue mean?", answer="Inner monologue means the quiet words a character thinks in their own head."),
        QAItem(question="What does proper mean?", answer="Proper means neat, right, or done in a careful and respectful way."),
        QAItem(question="What does queer mean here?", answer="Queer here means a person whose identity is different from the usual expectations, and the story treats that as ordinary and good."),
    ]


ASP_RULES = r"""
valid(P, I, C) :- place(P), item(I), companion(C), helps_item(I, walk), helps_companion(C, walk).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for h in sorted(item.helps):
            lines.append(asp.fact("helps_item", iid, h))
    for cid, comp in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        for h in sorted(comp.helps):
            lines.append(asp.fact("helps_companion", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in asp:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k,v) for k,v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k,v) for k,v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a valid place, quest item, and companion combo.)"


def valid_story_story(params: StoryParams) -> bool:
    return params.item in ITEMS and params.companion in COMPANIONS and params.place in PLACES


def generate(params: StoryParams) -> StorySample:
    if not valid_story_story(params):
        raise StoryError(explain_rejection())
    world = tell(PLACES[params.place], ITEMS[params.item], COMPANIONS[params.companion], params.hero_name, params.hero_gender, params.trait)
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams("harbor", "key", "queer_guide", "Mina", "girl", "chump"),
            StoryParams("market", "map", "proper_scout", "Jules", "person", "proper"),
            StoryParams("cave", "lantern", "queer_guide", "Pip", "boy", "curious"),
        ]
        samples = [generate(p) for p in cur]
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
