#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/compare_superb_curiosity_space_adventure.py
===============================================================================================================

A tiny space-adventure storyworld about a curious child comparing strange star
finds and choosing the superb one for the mission. The setting is a small
orbital dock, where a scout's curiosity can turn hesitation into a bright,
useful discovery.

The seed tale in brief:
---
Mina, a curious young space scout, was sorting two mystery gadgets from a cargo
crate. One looked ordinary, the other looked superb. She compared them by weight,
shine, and the little lights on each side. The superb one turned out to be a
compact star map projector, perfect for their next trip. Mina took it to the
observation window, and the crew grinned when the map lit up the route ahead.

Causal state updates:
---
    compare two objects   -> actor.curiosity += 1
                             actor.confidence += 1
    choose superb object  -> chosen.valued += 1
                             actor.joy += 1
    use projector         -> route.visible += 1
                             crew.wonder += 1
    visible route         -> mission.progress += 1

Scripted social/emotional beats:
---
    curious setup         -> actor.curiosity += 1
    comparison made       -> actor.focus += 1
    superb choice         -> actor.pride += 1
    route revealed        -> actor.joy += 1 ; crew.relief += 1
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Dock:
    name: str = "the orbital dock"
    view: str = "the observation window"
    afford: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    shine: int = 0
    weight: int = 0
    useful: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class DeviceConfig:
    id: str
    label: str
    phrase: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, dock: Dock) -> None:
        self.dock = dock
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
        c = World(self.dock)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_compare(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["compared"] < THRESHOLD:
            continue
        sig = ("compare", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["curiosity"] += 1
        actor.memes["confidence"] += 1
        out.append(f"{actor.id}'s questions got sharper after comparing the two objects.")
    return out


def _r_choose_superb(world: World) -> list[str]:
    out: list[str] = []
    chosen_id = world.facts.get("chosen")
    if not chosen_id:
        return out
    chosen = world.entities[chosen_id]
    if chosen.meters["picked"] < THRESHOLD:
        return out
    sig = ("superb", chosen.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chosen.meters["valued"] += 1
    out.append(f"The superb choice made the little room feel ready for a mission.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("route_visible"):
        if ("reveal",) in world.fired:
            return out
        world.fired.add(("reveal",))
        world.get("mission").meters["progress"] += 1
        for actor in world.characters():
            actor.memes["joy"] += 1
        crew = world.get("crew")
        crew.memes["wonder"] += 1
        out.append("The route lit up, and the crew could finally see where to go.")
    return out


CAUSAL_RULES = [
    Rule("compare", "mind", _r_compare),
    Rule("superb", "choice", _r_choose_superb),
    Rule("reveal", "space", _r_reveal),
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


def compare_at_risk(a: ObjectConfig, b: ObjectConfig) -> bool:
    return True


def valid_choices() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for a in OBJECTS:
            for b in OBJECTS:
                if a != b:
                    combos.append((scene, a, b))
    return combos


@dataclass
class StoryParams:
    scene: str
    left: str
    right: str
    name: str
    gender: str
    title: str
    seed: Optional[int] = None


SCENES = {
    "dock": Dock("the orbital dock", "the observation window", {"compare", "superb"}),
    "bay": Dock("the moon bay", "the control porthole", {"compare", "superb"}),
    "station": Dock("the quiet station hall", "the glass dome", {"compare", "superb"}),
}

OBJECTS = {
    "scanner": ObjectConfig(
        id="scanner", label="scanner", phrase="a pocket scanner",
        shine=3, weight=2, useful=False, tags={"tool", "compare"}
    ),
    "map": ObjectConfig(
        id="map", label="star map projector", phrase="a compact star map projector",
        shine=5, weight=1, useful=True, tags={"tool", "superb"}
    ),
    "cube": ObjectConfig(
        id="cube", label="signal cube", phrase="a tiny signal cube",
        shine=2, weight=4, useful=False, tags={"cargo", "compare"}
    ),
}

DEVICES = {
    "projector": DeviceConfig(
        id="projector", label="projector", phrase="the star map projector",
        result="route_visible", tags={"superb", "map"}
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Iris", "Nova", "Tara", "Rin"]
BOY_NAMES = ["Kai", "Ezra", "Oren", "Pax", "Jace", "Nico"]
TITLES = ["scout", "pilot", "navigator", "helper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for left in OBJECTS:
            for right in OBJECTS:
                if left != right:
                    combos.append((scene, left, right))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about comparing a superb find.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--left", choices=OBJECTS)
    ap.add_argument("--right", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.left is None or c[1] == args.left)
              and (args.right is None or c[2] == args.right)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, left, right = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    title = args.title or rng.choice(TITLES)
    return StoryParams(scene=scene, left=left, right=right, name=name, gender=gender, title=title)


def _setup_world(params: StoryParams) -> World:
    dock = SCENES[params.scene]
    world = World(dock)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="scout"))
    crew = world.add(Entity(id="crew", kind="character", type="team", label="the crew"))
    mission = world.add(Entity(id="mission", type="mission", label="the mission"))
    left = world.add(Entity(id="left", type="thing", label=OBJECTS[params.left].label, phrase=OBJECTS[params.left].phrase))
    right = world.add(Entity(id="right", type="thing", label=OBJECTS[params.right].label, phrase=OBJECTS[params.right].phrase))
    chosen = right if OBJECTS[params.right].useful else left
    world.facts.update(hero=hero, crew=crew, mission=mission, left=left, right=right,
                       chosen=chosen.id, route_visible=chosen.id == "map", scene=params.scene)
    return world


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.facts["hero"]
    left = world.facts["left"]
    right = world.facts["right"]
    chosen = world.get(world.facts["chosen"])
    hero.memes["curiosity"] += 1
    world.say(f"At {SCENES[params.scene].name}, {hero.id} was a curious {params.title} who liked to compare new things.")
    world.say(f"On a table near the {SCENES[params.scene].view}, {hero.id} found {left.phrase} and {right.phrase}.")
    world.para()
    world.say(f'{hero.id} tilted {hero.pronoun("possessive")} head and said, "Let me compare them first."')
    hero.meters["compared"] += 1
    compare_score_left = OBJECTS[params.left].shine + OBJECTS[params.left].weight
    compare_score_right = OBJECTS[params.right].shine + OBJECTS[params.right].weight
    if compare_score_left == compare_score_right:
        world.say("They looked close enough to compare by shine and weight.")
    else:
        world.say("The little lights and the weight made one choice feel clearer.")
    propagate(world, narrate=True)
    world.para()
    chosen.meters["picked"] += 1
    hero.memes["pride"] += 1
    if chosen.id == "map":
        world.say(f"{hero.id} picked the superb one, the star map projector.")
        world.say(f'It was superb because it showed the route without wobbling in {SCENES[params.scene].name}.')
        world.facts["route_visible"] = True
        propagate(world, narrate=True)
        world.para()
        world.say(f'When the projector lit up, {hero.id} grinned and the crew could compare the stars to the map at once.')
        world.say("The dock suddenly looked brighter, and the mission moved forward.")
    else:
        world.say(f"{hero.id} chose the other object, but it still helped the crew sort the cargo.")
        world.say("Even then, curiosity had made the room calmer and the next step easier.")
        world.facts["route_visible"] = False
        propagate(world, narrate=True)
    world.facts.update(chosen=chosen.id)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    left = f["left"].phrase
    right = f["right"].phrase
    return [
        f'Write a short space adventure for a curious child named {hero.id} that includes the words "compare" and "superb".',
        f"Tell a story where {hero.id} compares {left} and {right} at the orbital dock and chooses the superb one.",
        "Write a gentle space story about curiosity, a careful comparison, and a bright route that appears at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    left = f["left"]
    right = f["right"]
    chosen = f["chosen"]
    qs = [
        QAItem(
            question=f"What did {hero.id} do before making a choice at the dock?",
            answer=f"{hero.id} compared {left.phrase} and {right.phrase} carefully. That curiosity helped {hero.id} notice which one was superb.",
        ),
        QAItem(
            question=f"Which object was superb in the story?",
            answer=f"The superb object was {world.get(chosen).phrase}. It turned out to be the useful space tool that could help the mission."
        ),
        QAItem(
            question=f"Why did the crew feel happier at the end?",
            answer="The chosen tool revealed the route ahead, so the crew could see where to go. That made the whole mission feel safer and brighter."
        ),
    ]
    if world.facts.get("route_visible"):
        qs.append(QAItem(
            question="How did the superb object change the ending?",
            answer="It made the star route visible in the window. Because of that, the crew could move on with confidence instead of guessing."
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does compare mean?", "To compare means to look at two things and notice how they are alike or different."),
        QAItem("What does superb mean?", "Superb means very, very good or impressive."),
        QAItem("What is curiosity?", "Curiosity is the wish to know more, ask questions, and look closely at things."),
        QAItem("What is a star map for?", "A star map helps space travelers know where to go by showing the way among the stars."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k,v) for k,v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k,v) for k,v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
compare_boost(A) :- hero(A), compared(A).
superb_choice(O) :- chosen(O), useful(O).
route_visible :- superb_choice(O), map(O).
progress :- route_visible.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.useful:
            lines.append(asp.fact("useful", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        ok = False
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, left=None, right=None, gender=None, name=None, title=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


CURATED = [
    StoryParams(scene="dock", left="scanner", right="map", name="Mina", gender="girl", title="scout"),
    StoryParams(scene="bay", left="cube", right="map", name="Kai", gender="boy", title="navigator"),
    StoryParams(scene="station", left="scanner", right="cube", name="Luna", gender="girl", title="helper"),
]


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.left not in OBJECTS or params.right not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    if params.left == params.right:
        raise StoryError("The two compared objects must be different.")
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid compare combos.")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: compare {p.left} vs {p.right} ({p.scene})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
