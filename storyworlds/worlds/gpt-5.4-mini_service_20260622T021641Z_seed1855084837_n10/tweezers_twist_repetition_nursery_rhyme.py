#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10/tweezers_twist_repetition_nursery_rhyme.py
===============================================================================================================

A small nursery-rhyme-style storyworld about a child, a tiny snag, tweezers,
and a twist ending. The world uses typed entities with physical meters and
emotional memes, a forward-chaining causal model, a reasonableness gate, and a
declarative ASP twin.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

NAMES = ["Mia", "Nora", "Lily", "Ava", "Pip", "Toby", "Milo", "Finn"]
GROWNUPS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["cheery", "gentle", "curious", "bouncy", "busy"]
PLACES = {
    "nursery": "the nursery",
    "playroom": "the playroom",
    "window": "the window nook",
    "bed": "the little bed",
    "chair": "the rocking chair",
}
OBJECTS = {
    "ribbon": {
        "label": "ribbon",
        "phrase": "a bright ribbon",
        "type": "ribbon",
        "region": "hands",
        "risk": "stuck",
        "hook": "tied in a bow",
        "mess": "twisted",
        "end": "the bow sat straight again",
        "tags": {"ribbon", "twist"},
    },
    "string": {
        "label": "string",
        "phrase": "a tangled string",
        "type": "string",
        "region": "hands",
        "risk": "stuck",
        "hook": "caught in a knot",
        "mess": "twisted",
        "end": "the string came loose and neat",
        "tags": {"string", "twist"},
    },
    "locket": {
        "label": "locket",
        "phrase": "a tiny locket chain",
        "type": "locket",
        "region": "neck",
        "risk": "stuck",
        "hook": "caught in a loop",
        "mess": "twisted",
        "end": "the chain lay flat and safe",
        "tags": {"locket", "twist"},
    },
}
TOOLS = {
    "tweezers": {
        "label": "tweezers",
        "phrase": "a little pair of tweezers",
        "type": "tweezers",
        "good_for": {"ribbon", "string", "locket"},
        "care": "careful",
        "tags": {"tweezers", "tool"},
    },
    "spoon": {
        "label": "spoon",
        "phrase": "a shiny spoon",
        "type": "spoon",
        "good_for": set(),
        "care": "clumsy",
        "tags": {"spoon"},
    },
    "hands": {
        "label": "bare hands",
        "phrase": "bare hands",
        "type": "hands",
        "good_for": set(),
        "care": "clumsy",
        "tags": {"hands"},
    },
}

KNOWLEDGE = {
    "tweezers": [
        (
            "What are tweezers?",
            "Tweezers are small tools with two ends that squeeze together so you can pick up tiny things or pull out little bits.",
        )
    ],
    "twist": [
        (
            "What does twist mean?",
            "To twist is to turn or curl something around so it is not straight anymore. A ribbon or string can twist into a knot or a loop.",
        )
    ],
    "repetition": [
        (
            "What is repetition?",
            "Repetition means doing or saying something again and again. In a story, it can make a rhyme feel cozy and easy to remember.",
        )
    ],
    "nursery": [
        (
            "What is a nursery rhyme?",
            "A nursery rhyme is a short, sing-song story or poem for young children. It often repeats words and has a gentle rhythm.",
        )
    ],
}

ASP_RULES = r"""
need_fix(O) :- object(O).
tool_ok(T,O) :- tool(T), object(O), good_for(T,O).
valid(Place,O,T) :- place(Place), need_fix(O), tool_ok(T,O).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    caretaker: str = ""
    target: str = ""
    region: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandma", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandpa", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class StoryParams:
    place: str = "nursery"
    object: str = "ribbon"
    tool: str = "tweezers"
    name: str = "Mia"
    gender: str = "girl"
    grownup: str = "mother"
    trait: str = "cheery"
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            for tool in TOOLS:
                if tool == "tweezers" and obj in TOOLS[tool]["good_for"]:
                    combos.append((place, obj, tool))
    return combos

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for t, data in TOOLS.items():
        for o in sorted(data["good_for"]):
            lines.append(asp.fact("good_for", t, o))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, object=None, tool=None, name=None, gender=None,
            grownup=None, trait=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"FAIL: generate() smoke test crashed: {err}")
        return 1
    return 0

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about tweezers, twist, and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n in NAMES if (gender == "girl") == (n in {"Mia", "Nora", "Lily", "Ava", "Pip"})])
    grownup = args.grownup or rng.choice(GROWNUPS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, tool=tool, name=name, gender=gender, grownup=grownup, trait=trait)

def _setup(world: World, hero: Entity, grownup: Entity, thing: Entity, tool: Entity) -> None:
    world.say(f"In {world.place}, {hero.id} was a {hero.traits[0]} little {hero.type}.")
    world.say(f"{hero.pronoun().capitalize()} loved a sing-song game: twist, twist, twist, and again, twist, twist, twist.")
    world.say(f"One day {hero.id} saw {thing.phrase} {thing.attrs['hook']} and felt a little frown.")
    world.say(f"{hero.id} held up {tool.phrase}. {grownup.label_word.capitalize()} was nearby, listening closely.")

def _predict(world: World, thing_id: str) -> bool:
    sim = world.copy()
    sim.get("hero").memes["desire"] += 1
    sim.get(thing_id).meters["stuck"] += 1
    sim.get("thing").meters["stuck"] += 1
    return sim.get(thing_id).meters["clear"] >= THRESHOLD

def _fix(world: World, hero: Entity, grownup: Entity, thing: Entity, tool: Entity) -> None:
    hero.memes["joy"] += 1
    thing.meters["clear"] += 1
    world.say(f"{hero.id} said, 'Twist, twist, little knot, let's free this tiny tangled spot.'")
    world.say(f"{grownup.label_word.capitalize()} smiled and said, 'Use the {tool.label}, one careful tip at a time.'")
    world.say(f"So {hero.id} used {tool.label} to gently lift the {thing.label}, and the {thing.label} came loose at last.")
    world.say(f"Again and again, the little rhyme went round: twist, twist, twist, and the {thing.attrs['end']}.")

def _warn(world: World, grownup: Entity, hero: Entity, thing: Entity, tool: Entity) -> None:
    if _predict(world, thing.id):
        world.say(f'"{hero.id}, not with {tool.label}," {grownup.label_word.capitalize()} said. "That could help."')
    else:
        world.say(f'"{hero.id}, not with {tool.label}," {grownup.label_word.capitalize()} said. "We need a gentler way."')

def tell(place: str, obj: str, tool_id: str, hero_name: str, hero_gender: str, grownup_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=[trait, "little"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label=f"the {grownup_type}"))
    thing_cfg = OBJECTS[obj]
    thing = world.add(Entity(id="thing", type=thing_cfg["type"], label=thing_cfg["label"], phrase=thing_cfg["phrase"], attrs={"hook": thing_cfg["hook"], "end": thing_cfg["end"], "plural": False}))
    tool_cfg = TOOLS[tool_id]
    tool = world.add(Entity(id="tool", type=tool_cfg["type"], label=tool_cfg["label"], phrase=tool_cfg["phrase"], tags=set(tool_cfg["tags"])))
    world.facts.update(hero=hero, grownup=grownup, thing=thing, tool=tool, place=place, obj=obj, tool_id=tool_id, resolved=True)
    _setup(world, hero, grownup, thing, tool)
    world.para()
    _warn(world, grownup, hero, thing, tool)
    world.say(f"{hero.id} paused, then used {tool.label} the way {grownup.label_word} showed.")
    world.para()
    _fix(world, hero, grownup, thing, tool)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story for a young child about {f["hero"].id}, {f["thing"].label}, and {f["tool"].label}. Include the word "tweezers" and a repeating line.',
        f"Tell a cozy story where {f['hero'].id} uses tweezers to help with a twisty little problem in {f['place']}.",
        f"Write a sing-song tale with repetition, a tiny twist, and a happy ending for {f['hero'].id}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    thing = f["thing"]
    grownup = f["grownup"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"What problem did {hero.id} find in {world.place}?",
            answer=f"{hero.id} found {thing.phrase} {thing.attrs['hook']}. The little twist made the story start with a snag that needed gentle help.",
        ),
        QAItem(
            question=f"How did {hero.id} help with the twisty problem?",
            answer=f"{hero.id} used {tool.label} carefully, just as {grownup.label_word} showed. That let the tiny snag come loose without making the problem worse.",
        ),
        QAItem(
            question=f"Why did the story repeat the words twist, twist, twist?",
            answer="The repeating words made the story feel like a nursery rhyme. Repetition also matched the little turning motion in the problem and in the ending.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {thing.attrs['end']}. {hero.id} looked happier, and the rhyme ended with the snag fixed and the day feeling neat again.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tool"].tags) | set(world.facts["thing"].tags) | {"repetition", "nursery"}
    out: list[QAItem] = []
    for tag in ["tweezers", "twist", "repetition", "nursery"]:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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

def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.object not in OBJECTS or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    if params.tool != "tweezers" or params.object not in TOOLS["tweezers"]["good_for"]:
        raise StoryError("The tweezers need a tiny twisty thing to fix.")
    world = tell(PLACES[params.place], params.object, params.tool, params.name, params.gender, params.grownup, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="nursery", object="ribbon", tool="tweezers", name="Mia", gender="girl", grownup="mother", trait="cheery"),
    StoryParams(place="playroom", object="string", tool="tweezers", name="Pip", gender="boy", grownup="grandma", trait="curious"),
    StoryParams(place="window", object="locket", tool="tweezers", name="Nora", gender="girl", grownup="father", trait="gentle"),
]

def explain_rejection() -> str:
    return "(No story: tweezers need a tiny twisty thing to fix, so the story must choose a snag they can gently solve.)"

def asp_verify_story(sample: StorySample) -> bool:
    return bool(sample.story)

def asp_show_program() -> str:
    return asp_program("#show valid/3.")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object, tool) combos:\n")
        for place, obj, tool in combos:
            print(f"  {place:10} {obj:8} {tool}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object} with {p.tool} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
