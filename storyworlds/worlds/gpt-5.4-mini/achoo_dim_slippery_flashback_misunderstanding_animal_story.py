#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/achoo_dim_slippery_flashback_misunderstanding_animal_story.py
==============================================================================================

A small standalone storyworld in an animal-story style.

Domain sketch
-------------
A few animal friends are making their way across a slippery path to help a
friend. One animal remembers a past "achoo-dim" sneezing moment in a flashback,
and another animal misunderstands the sound as a sign that the helper is upset.
The misunderstanding causes a brief pause and a small mishap on the slippery
ground, but the friends sort it out, help one another, and finish with a warm,
clear ending.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven causal narration
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in world state, story state, and general knowledge
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class AnimalKind:
    id: str
    species: str
    adjective: str
    noun: str
    voice: str
    home: str
    likes: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Place:
    id: str
    name: str
    slippery: bool = False
    setting_line: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Event:
    id: str
    label: str
    flashback: bool = False
    misunderstanding: bool = False
    trigger_word: str = ""
    memory_line: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ObjectThing:
    id: str
    label: str
    kind: str
    slippery: bool = False
    helpful: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["slip"] < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["embarrassed"] += 1
        for other in world.characters():
            if other.id != e.id:
                other.memes["worry"] += 0.5
        out.append("__slip__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["understanding"] < THRESHOLD:
            continue
        sig = ("mend", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        out.append("__mend__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("slip", "physical", _r_slip),
    Rule("mend", "social", _r_mend),
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


def reasonableness_gate(event: Event, place: Place, helper: ObjectThing) -> bool:
    return place.slippery and helper.helpful


def event_nature(event: Event) -> str:
    return "flashback" if event.flashback else "present"


def would_misunderstand(listener: Entity, speaker: Entity) -> bool:
    return listener.memes["assumption"] > speaker.memes["clarity"]


def setup(world: World, hero: Entity, friend: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a breezy day, {hero.id} the {hero.attrs['kind'].adjective} {hero.attrs['kind'].noun} "
        f"and {friend.id} the {friend.attrs['kind'].adjective} {friend.attrs['kind'].noun} "
        f"trotted to {place.name}."
    )
    world.say(place.setting_line)


def flashback(world: World, hero: Entity, event: Event) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Then {hero.id} had a sudden flashback: {event.memory_line}"
    )
    world.say(
        f'"{event.trigger_word}!" {hero.id} sneezed, and the old memory came back all at once.'
    )


def misunderstanding(world: World, friend: Entity, hero: Entity, helper: Entity, event: Event) -> None:
    friend.memes["assumption"] += 1
    world.say(
        f'{friend.id} looked up at {hero.id} and frowned. "{hero.id}, are you saying the path is too hard?"'
    )
    if would_misunderstand(friend, hero):
        friend.memes["worry"] += 1
        world.say(
            f"{friend.id} misunderstood the little sneeze and thought {hero.id} wanted to turn back."
        )


def slip_event(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.meters["slip"] += 1
    world.say(
        f"{hero.id} stepped onto a slippery patch and skidded with a tiny yelp."
    )
    propagate(world, narrate=False)


def explain(world: World, hero: Entity, friend: Entity, helper: Entity, event: Event) -> None:
    hero.memes["understanding"] += 1
    friend.memes["understanding"] += 1
    world.say(
        f'{hero.id} laughed softly and said, "{event.trigger_word} was just a sneeze from the wind in my nose."'
    )
    world.say(
        f'"I thought you meant stop," {friend.id} admitted. "I misunderstood you."'
    )


def rescue(world: World, helper: Entity, hero: Entity, friend: Entity) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} padded over with a steady paw and helped {hero.id} back onto firm ground."
    )
    world.say(
        f"Together they brushed off the mud, and the slippery spot became only a small story to laugh about."
    )


def ending(world: World, hero: Entity, friend: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, the three friends kept walking across {place.name}, slower and safer, with bright eyes and quiet paws."
    )
    world.say(
        f"This time, the path was still slippery, but nobody felt lost, and the little group arrived together, smiling."
    )


def tell(animal: AnimalKind, companion: AnimalKind, helper_kind: AnimalKind, place: Place, event: Event) -> World:
    world = World()
    hero = world.add(Entity(id="Milo", kind="character", type="boy", role="hero", attrs={"kind": animal}))
    friend = world.add(Entity(id="Pip", kind="character", type="boy", role="friend", attrs={"kind": companion}))
    helper = world.add(Entity(id="Nora", kind="character", type="girl", role="helper", attrs={"kind": helper_kind}))
    world.add(Entity(id="path", type="place", label=place.name))
    world.facts["event"] = event
    world.facts["place"] = place
    world.facts["hero_kind"] = animal
    world.facts["friend_kind"] = companion
    world.facts["helper_kind"] = helper_kind

    setup(world, hero, friend, helper, place)
    world.para()
    flashback(world, hero, event)
    misunderstanding(world, friend, hero, helper, event)
    slip_event(world, hero, friend, place)
    world.para()
    explain(world, hero, friend, helper, event)
    rescue(world, helper, hero, friend)
    world.para()
    ending(world, hero, friend, helper, place)
    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        slipped=hero.meters["slip"] >= THRESHOLD,
        understanding=friend.memes["understanding"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "rabbit": AnimalKind("rabbit", "rabbit", "soft", "rabbit", "hop", "burrow", "carrots"),
    "fox": AnimalKind("fox", "fox", "bright", "fox", "trot", "den", "berries"),
    "bear": AnimalKind("bear", "bear", "gentle", "bear", "amble", "cave", "honey"),
    "squirrel": AnimalKind("squirrel", "squirrel", "quick", "squirrel", "scurry", "tree hollow", "nuts"),
    "badger": AnimalKind("badger", "badger", "steady", "badger", "plod", "nest", "worms"),
}

PLACES = {
    "forest_path": Place("forest_path", "the forest path", True, "The forest path had wet leaves, and the stones were slippery."),
    "riverbank": Place("riverbank", "the riverbank", True, "The riverbank shone after rain, and the mud made it slippery."),
    "hill_trail": Place("hill_trail", "the hill trail", True, "The hill trail wound downhill, and the grass was slippery in the drizzle."),
}

EVENTS = {
    "achoo_dim": Event(
        "achoo_dim",
        "achoo-dim",
        flashback=True,
        misunderstanding=True,
        trigger_word="achoo-dim",
        memory_line="a dim lantern had flickered when a sneeze puffed the smoke sideways.",
    ),
}

HELPFUL_OBJECTS = {
    "lantern": ObjectThing("lantern", "lantern", "light", helpful=True),
    "moss_pad": ObjectThing("moss_pad", "moss pad", "cushion", helpful=True),
}

TRAITS = ["careful", "curious", "gentle", "brave"]


@dataclass
@dataclass
class StoryParams:
    animal: str
    companion: str
    helper: str
    place: str
    event: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for a in ANIMALS:
        for b in ANIMALS:
            if b == a:
                continue
            for h in ANIMALS:
                for p in PLACES:
                    for e in EVENTS:
                        if reasonableness_gate(EVENTS[e], PLACES[p], HELPFUL_OBJECTS["lantern"]):
                            combos.append((a, b, h, p, e))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a flashback, a misunderstanding, and a slippery path.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--companion", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
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
    if args.event and args.place:
        if not reasonableness_gate(EVENTS[args.event], PLACES[args.place], HELPFUL_OBJECTS["lantern"]):
            raise StoryError("No story: the path must be slippery and the helper must be useful.")
    combos = [c for c in valid_combos()
              if (args.animal is None or c[0] == args.animal)
              and (args.companion is None or c[1] == args.companion)
              and (args.helper is None or c[2] == args.helper)
              and (args.place is None or c[3] == args.place)
              and (args.event is None or c[4] == args.event)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    animal, companion, helper, place, event = rng.choice(sorted(combos))
    return StoryParams(animal, companion, helper, place, event)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "achoo-dim" and "slippery".',
        f"Tell a gentle story where {f['hero'].id} remembers an old moment and "
        f"{f['friend'].id} misunderstands a sneeze on a slippery path.",
        f"Write a child-friendly animal story with a flashback, a misunderstanding, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who are the story friends?",
               f"It is about {f['hero'].id}, {f['friend'].id}, and {f['helper'].id}. They are animal friends who travel together."),
        QAItem("Why did the path cause trouble?",
               f"The path was slippery, so one friend skidded a little. That made the others slow down and help."),
        QAItem("What was the misunderstanding?",
               f"{f['friend'].id} thought the sneeze meant something else, but it was only {f['event'].trigger_word} from a memory and the wind."),
        QAItem("How did the story end?",
               f"They talked it through, helped one another, and kept walking safely together. The slippery path was still there, but the friends understood each other now."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does slippery mean?",
               "Slippery means smooth or wet so feet can slide easily."),
        QAItem("What is a flashback?",
               "A flashback is when a story suddenly remembers something that happened before."),
        QAItem("What is a misunderstanding?",
               "A misunderstanding is when someone thinks a message means one thing, but it really means something else."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v.id if hasattr(v, 'id') else v for k, v in e.attrs.items()}
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
slippery_place(P) :- place(P), slippery(P).
valid(A, C, H, P, E) :- animal(A), animal(C), animal(H), place(P), event(E),
                        A != C, A != H, C != H, slippery(P), helpful(lantern).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.slippery:
            lines.append(asp.fact("slippery", pid))
    for eid in EVENTS:
        lines.append(asp.fact("event", eid))
    lines.append(asp.fact("helpful", "lantern"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {e}")
    return rc


CURATED = [
    StoryParams("rabbit", "fox", "bear", "forest_path", "achoo_dim"),
    StoryParams("squirrel", "badger", "rabbit", "riverbank", "achoo_dim"),
    StoryParams("fox", "rabbit", "bear", "hill_trail", "achoo_dim"),
]


def story_text(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    world = tell(ANIMALS[params.animal], ANIMALS[params.companion], ANIMALS[params.helper], PLACES[params.place], EVENTS[params.event])
    return StorySample(
        params=params,
        story=story_text(world),
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible animal combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
