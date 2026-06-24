#!/usr/bin/env python3
"""
paprika_flashback_quest_rhyming_story.py
========================================

A small storyworld about a child on a quest for paprika, told in a gentle,
rhyming, flashback-tinted style.

The world is built from a simple premise:
- someone needs paprika for a dish,
- a small quest goes out to find it,
- a flashback explains why the spice matters,
- the ending returns with paprika in hand and the meal made bright.

This script is self-contained and uses only the standard library plus the
shared Storyweavers result containers.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = False
    has_market: bool = False
    has_kitchen: bool = False


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    kind: str
    color: str
    scent: str
    place_hint: str = ""


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_missing_spice(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"])
    target = world.get(world.facts["paprika"])
    if hero.memes.get("quest_started", 0) >= THRESHOLD and target.meters.get("found", 0) < THRESHOLD:
        sig = ("missing", target.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The jar was not where it ought to be; the little quest felt wobbly in the air.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"])
    if hero.memes.get("memory_tug", 0) >= THRESHOLD and ("flashback", hero.id) not in world.fired:
        world.fired.add(("flashback", hero.id))
        out.append("Back in the blink of an earlier day, the same bright spice had saved a soup from being plain.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and ("relief", world.facts["hero"]) not in world.fired:
        world.fired.add(("relief", world.facts["hero"]))
        out.append("With paprika returned, the kitchen felt merry and warm, like sunset in a bowl.")
    return out


CAUSAL_RULES = [
    Rule("missing_spice", _r_missing_spice),
    Rule("flashback", _r_flashback),
    Rule("relief", _r_relief),
]


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
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy=True, has_kitchen=True),
    "market": Place(id="market", label="the market lane", has_market=True),
    "garden": Place(id="garden", label="the garden patch", cozy=True),
}


OBJECTS = {
    "paprika": ObjectSpec(
        id="paprika",
        label="paprika",
        phrase="a tiny jar of paprika",
        kind="spice",
        color="red",
        scent="smoky",
        place_hint="market",
    ),
    "teapot": ObjectSpec(
        id="teapot",
        label="teapot",
        phrase="a blue teapot",
        kind="kitchen_thing",
        color="blue",
        scent="warm",
        place_hint="kitchen",
    ),
    "lantern": ObjectSpec(
        id="lantern",
        label="lantern",
        phrase="a round lantern",
        kind="light",
        color="gold",
        scent="bright",
        place_hint="garden",
    ),
}


HERO_NAMES = ["Mina", "Noor", "Tali", "Lio", "Ravi", "Pia", "Eden", "Milo"]
TRAITS = ["bright", "curious", "gentle", "spry", "brave", "cheery"]


def rhyme(a: str, b: str) -> str:
    return f"{a} ... {b}"


def intro_line(hero: Entity, place: Place, obj: ObjectSpec) -> str:
    return (
        f"{hero.id} lived by {place.label}, with a heart light as a kite. "
        f"{hero.pronoun('subject').capitalize()} longed for {obj.label}, red and bright."
    )


def quest_line(hero: Entity, obj: ObjectSpec, place: Place) -> str:
    return (
        f"So off went {hero.id} on a quest down the lane, "
        f"to find the red spice before the supper was plain."
    )


def flashback_line(hero: Entity) -> str:
    return (
        f"Then came a flashback, soft as a bell: "
        f"last week {hero.id} had tasted a soup that did not swell with flavor or cheer."
    )


def turning_line(hero: Entity, obj: ObjectSpec) -> str:
    return (
        f"{hero.id} remembered the soup and the smile that it wore, "
        f"and searched with more care than before."
    )


def ending_line(hero: Entity, obj: ObjectSpec) -> str:
    return (
        f"At last the little jar came home in the light. "
        f"{hero.id} stirred in {obj.label}, and the soup turned right."
    )


def tell(place: Place, obj: ObjectSpec, hero_name: str, hero_type: str, companion_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "questing", "bright"]))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type))
    paprika = world.add(Entity(id="Paprika", kind="thing", type="spice", label=obj.label, phrase=obj.phrase))

    world.facts.update(hero=hero.id, companion=companion.id, paprika=paprika.id, place=place.id, object=obj.id)

    hero.memes["quest_started"] = 1
    world.say(intro_line(hero, place, obj))
    world.say(quest_line(hero, obj, place))

    world.para()
    if place.has_market:
        world.say("The market had stalls that swayed, with baskets and jars in a tidy parade.")
        world.say("But the first shelf was bare, and the second looked cold, so the search went on and on.")
    else:
        world.say("The path was short and the clues were few, so the quest had to think what to do.")
    hero.memes["memory_tug"] = 1
    propagate(world, narrate=True)
    world.say(flashback_line(hero))
    world.say(turning_line(hero, obj))

    world.para()
    paprika.meters["found"] = 1
    hero.memes["joy"] = 1
    world.say(
        f"{hero.id} found the jar at {place.label if place.has_market else 'a small shop'}; "
        f"{companion.id} gave a nod and a happy clap."
    )
    world.say(ending_line(hero, obj))
    world.facts["resolved"] = True
    propagate(world, narrate=True)
    return world


def generate_prompts(world: World) -> list[str]:
    p = world.place.label
    return [
        f"Write a short rhyming story about a child who goes on a quest for paprika at {p}.",
        "Tell a gentle story with a flashback that explains why paprika matters for supper.",
        "Write a simple quest tale where something red and spicy is found just in time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    obj = world.get(world.facts["paprika"])
    place = world.place.label
    return [
        QAItem(
            question=f"Who went on the quest for paprika?",
            answer=f"{hero.id} went on the quest for paprika at {place}.",
        ),
        QAItem(
            question="Why did the story pause for a flashback?",
            answer="The story paused for a flashback to remember that paprika made an earlier soup taste much better.",
        ),
        QAItem(
            question=f"What was found at the end of the quest?",
            answer=f"{hero.id} found {obj.label}, and the jar went into the supper at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is paprika?",
            answer="Paprika is a red spice made from dried peppers. People add it to food to give it color and a warm taste.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. A quest story usually has a goal, a try, and a happy find.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier, so readers can understand why it matters now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming flashback quest storyworld about paprika.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--object", choices=OBJECTS.keys(), default="paprika")
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--companion-type", choices=["mother", "father", "sister", "brother"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    obj = args.object or "paprika"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or rng.choice(["mother", "father", "sister", "brother"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    if obj != "paprika":
        raise StoryError("This world is built around paprika; choose --object paprika.")
    return StoryParams(place=place, object=obj, hero_name=hero_name, hero_type=hero_type, companion_type=companion_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], params.hero_name, params.hero_type, params.companion_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
place(kitchen).
place(market).
place(garden).

object(paprika).
hero_type(girl).
hero_type(boy).
companion_type(mother).
companion_type(father).
companion_type(sister).
companion_type(brother).

valid_story(P,O) :- place(P), object(O), O = paprika.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if SETTINGS[pid].has_market:
            lines.append(asp.fact("has_market", pid))
        if SETTINGS[pid].has_kitchen:
            lines.append(asp.fact("has_kitchen", pid))
    lines.append(asp.fact("object", "paprika"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p, "paprika") for p in SETTINGS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


CURATED = [
    StoryParams(place="market", object="paprika", hero_name="Mina", hero_type="girl", companion_type="mother"),
    StoryParams(place="kitchen", object="paprika", hero_name="Ravi", hero_type="boy", companion_type="father"),
    StoryParams(place="garden", object="paprika", hero_name="Pia", hero_type="girl", companion_type="sister"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for p, o in vals:
            print(f"  {p:8} {o}")
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
