#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sing_hand_ful_inner_monologue_repetition_animal.py
===================================================================================

A standalone storyworld for a tiny animal-story domain: an animal wants to sing,
but a small hand-ful of stage fright or shyness gets in the way, until a gentle
helper, a repeated chant, and an inner monologue turn the moment into a warm
performance.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes,
- a forward-chained causal model,
- a reasonableness gate plus inline ASP twin,
- three Q&A sets grounded in world state rather than rendered prose.

The seed words are honored directly in story text and structure:
- "sing"
- "hand-ful"

The style leans animal-story: child-friendly, concrete, and cozy.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        animalish = {"fox", "rabbit", "bear", "mouse", "bird", "cat", "dog", "squirrel"}
        if self.type in animalish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    echo: bool = False
    stage: bool = False
    night: bool = False

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
class Perform:
    id: str
    label: str
    verb: str
    sound: str
    repeat: str
    crowd_warmth: int
    helps: set[str] = field(default_factory=set)

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
class Helper:
    id: str
    label: str
    line: str
    chant: str
    boost: int
    helps: set[str] = field(default_factory=set)

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
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.echo:
        return out
    for ent in list(world.entities.values()):
        if ent.memes["song"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["brave"] += 1
        out.append("__echo__")
    return out


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["shy"] < THRESHOLD:
            continue
        sig = ("warmth", ent.id)
        if sig in world.fired:
            continue
        helper_id = world.facts.get("helper_id")
        if not helper_id:
            continue
        helper = world.get(helper_id)
        world.fired.add(sig)
        ent.memes["shy"] = max(0.0, ent.memes["shy"] - helper.memes["boost"])
        ent.memes["hope"] += 1
        helper.memes["kindness"] += 1
        out.append("__warm__")
    return out


def _r_crowd(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["song"] < THRESHOLD:
            continue
        sig = ("crowd", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["crowd_warm"] = world.facts.get("crowd_warm", 0) + 1
        ent.meters["applause"] += 1
        out.append("__applause__")
    return out


CAUSAL_RULES = [
    Rule("echo", "sound", _r_echo),
    Rule("warmth", "social", _r_warmth),
    Rule("crowd", "social", _r_crowd),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inner_monologue(animal: Entity, perform: Perform) -> str:
    if animal.memes["shy"] >= 2:
        return (
            f"Maybe I can sing, the little voice inside {animal.pronoun('possessive')} "
            f"head whispered. Maybe just one note. Maybe a hand-ful of notes."
        )
    return (
        f"I can sing, the little voice inside {animal.pronoun('possessive')} head said. "
        f"One note, then another, then another."
    )


def predict(world: World, animal_id: str, perform_id: str) -> dict:
    sim = world.copy()
    animal = sim.get(animal_id)
    perform = PERFORMANCES[perform_id]
    animal.memes["song"] += 1
    if sim.place.echo:
        propagate(sim, narrate=False)
    return {
        "brave": animal.memes["brave"],
        "applause": animal.meters["applause"],
    }


def start(world: World, animal: Entity, perform: Perform, helper: Entity) -> None:
    animal.memes["joy"] += 1
    world.say(
        f"On a quiet evening, {animal.id} stood near the little stage in {world.place.label}."
    )
    world.say(
        f"{animal.id} wanted to {perform.verb}, but {animal.pronoun('possessive')} "
        f"tail felt twisty and small."
    )
    world.say(inner_monologue(animal, perform))


def nudge(world: World, animal: Entity, perform: Perform, helper: Entity) -> None:
    animal.memes["shy"] += 1
    world.say(
        f"{animal.id} looked at the floor and thought, "
        f'"Just a hand-ful of sounds. Just a hand-ful. Just a hand-ful."'
    )
    world.say(
        f"Then {helper.id} came close and said, \"{helper.label}. {helper.label}. "
        f"{helper.label}.\""
    )
    world.say(helper.label + " " + helper.line)
    world.facts["helper_id"] = helper.id


def sing(world: World, animal: Entity, perform: Perform) -> None:
    animal.memes["song"] += 1
    world.say(
        f"{animal.id} took a breath and began to sing: {perform.repeat}."
    )
    world.say(
        f"The little tune went {perform.sound}, and it sounded brighter every time "
        f"{animal.id} repeated it."
    )
    propagate(world, narrate=True)


def cheer(world: World, animal: Entity, perform: Perform, helper: Entity) -> None:
    applause = world.facts.get("crowd_warm", 0)
    if applause:
        animal.memes["pride"] += 1
        world.say(
            f"The crowd smiled, and soon the whole {world.place.label} felt warm with applause."
        )
    world.say(
        f"{helper.id} grinned and said, \"Again! Again!\" because the song had become brave."
    )


def ending(world: World, animal: Entity, perform: Perform) -> None:
    if animal.meters["applause"] >= THRESHOLD:
        world.say(
            f"By the end, {animal.id} was singing without shaking, and the little stage "
            f"felt as safe as a nest."
        )
    else:
        world.say(
            f"By the end, {animal.id} still sang, and even the quiet room seemed to listen."
        )


def tell(place: Place, animal_name: str = "Milo", animal_type: str = "rabbit",
         helper_name: str = "Pip", helper_type: str = "bird",
         perform_id: str = "singing") -> World:
    world = World(place)
    animal = world.add(Entity(id=animal_name, kind="character", type=animal_type, role="performer"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    perform = PERFORMANCES[perform_id]
    world.facts["perform_id"] = perform_id

    animal.memes["shy"] = 2.0
    animal.memes["song"] = 0.0
    helper.memes["boost"] = float(perform.crowd_warmth)

    start(world, animal, perform, helper)
    world.para()
    nudge(world, animal, perform, helper)
    sing(world, animal, perform)
    world.para()
    cheer(world, animal, perform, helper)
    ending(world, animal, perform)

    world.facts.update(
        animal=animal,
        helper=helper,
        perform=perform,
        outcome="brave" if animal.meters["applause"] >= THRESHOLD else "soft",
    )
    return world


PLACES = {
    "meadow": Place("meadow", "the meadow", echo=True, stage=True, night=False),
    "barn": Place("barn", "the barn loft", echo=True, stage=True, night=True),
    "garden": Place("garden", "the garden fence", echo=False, stage=True, night=False),
}

PERFORMANCES = {
    "singing": Perform("singing", "sing", "sing", "la-la-la", "la-la-la, la-la-la", 2, helps={"hope", "brave"}),
    "chirp": Perform("chirp", "chirp", "chirp", "tweet-tweet", "tweet-tweet, tweet-tweet", 1, helps={"hope"}),
    "hum": Perform("hum", "hum", "hum", "mmm-mmm", "mmm-mmm, mmm-mmm", 2, helps={"hope", "brave"}),
}

HELPERS = {
    "bird": Entity(id="Pip", kind="character", type="bird", label="pip-pip encouragement"),
    "mouse": Entity(id="Nia", kind="character", type="mouse", label="tiny mouse courage"),
    "fox": Entity(id="Rae", kind="character", type="fox", label="calm fox breath"),
}

GIRLISH = ["Milo", "Pip", "Nia", "Rae", "Toto", "Lulu"]
ANIMAL_NAMES = ["Milo", "Pip", "Nia", "Rae", "Toto", "Lulu", "Bibi", "Kiki"]
TYPES = ["rabbit", "bird", "mouse", "fox", "cat", "dog", "squirrel"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for perf in PERFORMANCES:
            for h in HELPERS:
                combos.append((p, perf, h))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    performance: str
    helper: str
    animal_name: str
    animal_type: str
    helper_name: str
    helper_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about singing, repetition, and a hand-ful of courage.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--performance", choices=PERFORMANCES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--animal-name")
    ap.add_argument("--animal-type", choices=TYPES)
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
              and (args.performance is None or c[1] == args.performance)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, perf, helper = rng.choice(sorted(combos))
    animal_type = args.animal_type or rng.choice(TYPES)
    animal_name = args.animal_name or rng.choice(ANIMAL_NAMES)
    helper_ent = HELPERS[helper]
    return StoryParams(place, perf, helper, animal_name, animal_type, helper_ent.id, helper_ent.type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal, perform, helper = f["animal"], f["perform"], f["helper"]
    return [
        f'Write a gentle animal story for a child where {animal.id} wants to {perform.verb} and learns courage with repetition.',
        f"Tell a story that uses the words 'sing' and 'hand-ful' in a cozy animal scene with {animal.id} and {helper.id}.",
        f"Write an inner-monologue story where {animal.id} thinks, repeats a small phrase, and finally sings aloud.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal, helper, perform = f["animal"], f["helper"], f["perform"]
    return [
        QAItem(
            question=f"What did {animal.id} want to do?",
            answer=f"{animal.id} wanted to {perform.verb}, even though {animal.pronoun('possessive')} feelings were shy at first."
        ),
        QAItem(
            question=f"What helped {animal.id} get started?",
            answer=f"{helper.id} stayed close, repeated a gentle phrase, and helped turn a hand-ful of courage into a real song."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {animal.id} singing more bravely, while the little stage and the cheering crowd showed the change."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is singing?",
            answer="Singing is making music with your voice. People and animals in stories can sing to share a tune or feeling."
        ),
        QAItem(
            question="What does hand-ful mean here?",
            answer="Here, hand-ful means just a small amount. The story uses it to show that the animal only needed a little courage."
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help because saying or doing the same small thing again and again makes it feel easier and more familiar."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
song_started(A) :- performer(A), performed_song(A).
brave(A) :- song_started(A), echo_place.
crowd_warmed(A) :- song_started(A), helper_boost(A, B), B > 0.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for k, perf in PERFORMANCES.items():
        lines.append(asp.fact("performance", k))
        if perf.crowd_warmth > 1:
            lines.append(asp.fact("helper_boost", k, perf.crowd_warmth))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
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
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    # smoke test ordinary generation
    try:
        s = generate(resolve_params(argparse.Namespace(place=None, performance=None, helper=None,
                                                      animal_name=None, animal_type=None),
                                    random.Random(7)))
        _ = s.story
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKETEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.animal_name, params.animal_type, params.helper)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, perf, h, "Milo", "rabbit", "Pip", "bird")) for p, perf, h in [
            ("meadow", "singing", "bird"),
            ("barn", "hum", "mouse"),
            ("garden", "chirp", "fox"),
        ]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
if __name__ == "__main__":
    main()
