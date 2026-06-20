#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scuff_snake_dim_volunteer_dialogue_bad_ending.py
================================================================================

A standalone storyworld for a small folk-tale domain: a village volunteer,
a scuff on a dark path, a snake-dim lamp, dialogue, and a bad ending.

The world is built to be classical and state-driven:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate plus inline ASP twin
- three Q&A sets grounded in world state and trace facts
- child-facing prose with a folk-tale cadence

The seed words are woven into the simulation:
- scuff
- snake-dim
- volunteer

The narrative features are:
- Dialogue
- Bad Ending
- Folk Tale style
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elderwoman"}
        male = {"boy", "father", "man", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    windy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    scuffs: bool = False
    startles: bool = False
    dims: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    fragile: bool = False
    edible: bool = False
    luminous: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    strength: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scuff(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["scuff"] < THRESHOLD:
            continue
        sig = ("scuff", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "path" in world.entities:
            world.get("path").meters["unease"] += 1
        out.append("__scuff__")
    return out


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    if "lamp" in world.entities and "snake" in world.entities:
        lamp = world.get("lamp")
        snake = world.get("snake")
        if snake.meters["startled"] >= THRESHOLD and lamp.meters["glow"] >= THRESHOLD:
            sig = ("dim",)
            if sig not in world.fired:
                world.fired.add(sig)
                lamp.meters["glow"] = max(0.0, lamp.meters["glow"] - 1.0)
                lamp.meters["dimness"] += 1
                out.append("__dim__")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    if "bread" in world.entities:
        bread = world.get("bread")
        if world.get("lamp").meters["glow"] < THRESHOLD and world.get("bread").meters["safe"] < THRESHOLD:
            sig = ("spoil",)
            if sig not in world.fired:
                world.fired.add(sig)
                bread.meters["dropped"] += 1
                bread.meters["spoiled"] += 1
                out.append("__spoil__")
    return out


CAUSAL_RULES = [
    Rule("scuff", "physical", _r_scuff),
    Rule("dim", "physical", _r_dim),
    Rule("spoil", "physical", _r_spoil),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    hazard: str
    object_name: str
    aid: str
    seed: Optional[int] = None


PLACES = {
    "lane": Place("lane", "the narrow lane", dark=True, tags={"lane", "dark"}),
    "bridge": Place("bridge", "the old bridge", windy=True, tags={"bridge"}),
    "field": Place("field", "the hay field", windy=True, tags={"field"}),
}

HAZARDS = {
    "snake": Hazard("snake", "a little snake", scuffs=True, startles=True, dims=True, tags={"snake"}),
    "root": Hazard("root", "a twisted root", scuffs=True, startles=False, dims=False, tags={"root"}),
}

OBJECTS = {
    "bread": ObjectThing("bread", "a loaf of bread", edible=True, fragile=True, tags={"bread"}),
    "milk": ObjectThing("milk", "a small jug of milk", fragile=True, tags={"milk"}),
    "eggs": ObjectThing("eggs", "a basket of eggs", fragile=True, tags={"eggs"}),
}

AIDS = {
    "lantern": Aid("lantern", "a little lantern", 1, tags={"light"}),
    "torch": Aid("torch", "a torch", 1, tags={"light"}),
}

GIRL_NAMES = ["Mara", "Tess", "Lina", "Sera", "Nell"]
BOY_NAMES = ["Pip", "Galen", "Hugh", "Oren", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HAZARDS:
            for o in OBJECTS:
                if HAZARDS[h].startles and OBJECTS[o].fragile:
                    combos.append((p, h, o))
    return combos


def explain_rejection(place: Place, hazard: Hazard, obj: ObjectThing) -> str:
    return (
        f"(No story: this tale needs a real danger, and {hazard.label} only makes sense "
        f"here when a fragile thing like {obj.label} is being carried through a dark place. "
        f"Try a fragile object and a startling hazard.)"
    )


def reasonableness_gate(place: Place, hazard: Hazard, obj: ObjectThing) -> bool:
    return hazard.startles and obj.fragile and place.dark


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with scuff, snake-dim, and a volunteer.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combo = None
    if args.place and args.hazard and args.object_name:
        if not reasonableness_gate(PLACES[args.place], HAZARDS[args.hazard], OBJECTS[args.object_name]):
            raise StoryError(explain_rejection(PLACES[args.place], HAZARDS[args.hazard], OBJECTS[args.object_name]))
        combo = (args.place, args.hazard, args.object_name)
    else:
        combo = rng.choice(valid_combos())
    place, hazard, obj = combo
    aid = args.aid or rng.choice(list(AIDS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    return StoryParams(place, hazard, obj, aid, None)


def tell(params: StoryParams) -> World:
    world = World()
    hero_gender = "girl" if params.aid == "lantern" else "boy"
    hero = world.add(Entity(params.aid, kind="character", type=hero_gender, role="volunteer"))
    elder = world.add(Entity("Elder", kind="character", type="elderwoman", role="elder", label="the elder"))
    place = world.add(Entity("place", type="place", label=PLACES[params.place].label))
    hazard = world.add(Entity("hazard", type="hazard", label=HAZARDS[params.hazard].label))
    obj = world.add(Entity("object", type="thing", label=OBJECTS[params.object_name].label))
    lamp = world.add(Entity("lamp", type="thing", label=AIDS[params.aid].label))
    hero.memes["duty"] = 1.0
    lamp.meters["glow"] = 1.0
    world.say(f"Long ago, in a small village, {hero.id} was the volunteer of the day.")
    world.say(f'"I will carry {obj.label} through {PLACES[params.place].label}," {hero.id} said. "It is only a short walk."')
    world.say(f'{elder.label_word.capitalize()} looked up from the door. "Mind your feet," {elder.pronoun()} warned, "for this lane is snake-dim at dusk."')
    world.para()
    world.say(f"{hero.id} nodded and went on, but the ground made a little scuff beneath {hero.pronoun('possessive')} shoe.")
    hazard.meters["startled"] += 1
    obj.meters["safe"] = 0.0
    propagate(world, narrate=False)
    world.say(f'Then there was a whisper in the grass: "{hazard.label}!"')
    world.say(f'"I am not afraid," {hero.id} whispered, though {hero.pronoun('possessive')} voice shook.')
    if world.get("lamp").meters["glow"] < THRESHOLD:
        world.say("But the little lantern grew snake-dim in the frightened dark.")
    world.para()
    world.say(f"The volunteer hurried, missed a stone, and the {obj.label} slipped from {hero.pronoun('possessive')} hands.")
    world.say(f"It struck the ground, and the village supper was ruined before it reached the cottage.")
    world.say(f"{elder.label_word.capitalize()} called from behind, \"A kind heart is good, child, but a poor road can still break what is meant for sharing.\"")
    world.say("And so the neighbor waited hungry that night, while the moon went pale over the lane.")
    world.facts.update(hero=hero, elder=elder, place=PLACES[params.place], hazard=HAZARDS[params.hazard], obj=OBJECTS[params.object_name], aid=AIDS[params.aid], outcome="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk-tale story that includes the words "scuff", "snake-dim", and "volunteer".',
        "Tell a village story where a volunteer carries something fragile at dusk, hears a warning, and the road turns bad.",
        "Write a dialogue-heavy fairy-tale style story with a bad ending about a lantern, a dark lane, and a broken delivery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    obj = f["obj"]
    hazard = f["hazard"]
    qa = [
        ("Who was the story about?",
         f"It was about {hero.id}, the volunteer of the day, and the elder who warned {hero.pronoun('object')}."),
        ("What did the volunteer carry?",
         f"{hero.id} carried {obj.label} through the dark lane, hoping to deliver it safely."),
        ("Why did the lantern become snake-dim?",
         f"The little {hazard.label} was startled by the scuff on the path, and the frightened light seemed to go dim."),
        ("What was the bad ending?",
         f"The {obj.label} fell and was ruined before it reached the cottage, so the neighbor did not get the supper that night."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a volunteer?",
         "A volunteer is someone who chooses to help without being made to do it."),
        ("What does scuff mean?",
         "A scuff is a scraping sound or mark made when something drags or rubs along the ground."),
        ("What does snake-dim mean in this story?",
         "It means the light is weak and spooky, as if a snake has made the road feel dark."),
        ("Why can a fragile object break on a rough road?",
         "A fragile thing can crack or spill when it is dropped or bumped, especially on a hard path."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
scuff_happens(H) :- hazard(H), startles(H).
dim_lamp :- scuff_happens(H), dims(H).
bad_ending :- dim_lamp.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].dark:
            lines.append(asp.fact("dark", pid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        if HAZARDS[hid].startles:
            lines.append(asp.fact("startles", hid))
        if HAZARDS[hid].dims:
            lines.append(asp.fact("dims", hid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        if OBJECTS[oid].fragile:
            lines.append(asp.fact("fragile", oid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("lane", "snake", "bread", "lantern"),
    StoryParams("bridge", "snake", "milk", "lantern"),
    StoryParams("field", "snake", "eggs", "torch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
