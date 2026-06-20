#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py
=============================================================================

A standalone bedtime-story world about a small child, a dreary evening, a
fragile promise of honour, and a love-dim mistake that ends badly but teaches a
clear lesson.

The domain is deliberately small: a child wants to keep a promise to look after
a lantern in a rainy little room, but carelessness and pride can make the story
turn sad.  The world supports two outcomes:

- a normal ending, where a grown-up safely fixes the problem and the child
  learns the lesson;
- a bad ending, where the light goes out, the room grows gloomier, and the child
  learns too late.

The story remains bedtime-story-like: concrete objects, short causal beats, and
an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py
    python storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py --all
    python storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/honour_dreary_love_dim_lesson_learned_bad.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    scene: str
    dark: str
    mood: str
    ending_image: str

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
class PromptSource:
    id: str
    kind: str
    label: str
    where: str
    rule: str
    power: int
    sense: int
    safe_alternative: str
    tags: set[str] = field(default_factory=set)

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
class OutcomePlan:
    id: str
    delay: int
    severity: int
    bad: bool

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


def _r_dimming(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lantern")
    room = world.entities.get("room")
    if lamp and lamp.meters["burning"] >= THRESHOLD and ("dimming", "lantern") not in world.fired:
        world.fired.add(("dimming", "lantern"))
        if room:
            room.meters["dreary"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__dim__")
    return out


CAUSAL_RULES = [Rule("dimming", "physical", _r_dimming)]


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


def _burn(world: World, narrate: bool = True) -> None:
    world.get("lantern").meters["burning"] += 1
    world.get("lantern").meters["ruined"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, prompt_id: str) -> dict:
    sim = world.copy()
    _burn(sim, narrate=False)
    return {
        "dreary": sim.get("room").meters["dreary"],
        "ruined": sim.get("lantern").meters["ruined"] >= THRESHOLD,
    }


def careful_enough(source: PromptSource, place: Place) -> bool:
    return source.kind == "light" and place.id in {"nursery", "hall"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for src_id, src in SOURCES.items():
            if source_can_make_story(src, place):
                combos.append((place_id, src_id, "bad" if src.power < 3 else "fixed"))
    return combos


def source_can_make_story(src: PromptSource, place: Place) -> bool:
    return src.kind == "light" and "dreary" in place.mood


def sensible_sources() -> list[PromptSource]:
    return [s for s in SOURCES.values() if s.sense >= SENSE_MIN]


def explain_rejection(src: PromptSource, place: Place) -> str:
    return f"(No story: {src.label} does not fit this dreary little place.)"


@dataclass
@dataclass
class StoryParams:
    place: str
    source: str
    outcome: str
    child: str
    child_gender: str
    parent: str
    trait: str
    delay: int = 0
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


PLACES = {
    "nursery": Place("nursery", "The nursery glowed softly, with a little bed, a sleepy rug, and rain ticking at the pane.", "a corner under the blanket fort", "dreary", "The lantern sat by the bed, bright again beside a woolly toy."),
    "hall": Place("hall", "The hall was narrow and quiet, with a coat hook, a worn bench, and a window that watched the rain.", "the space near the umbrella stand", "dreary", "The hall lantern stood tall and warm, lighting the shoes by the door."),
    "porch": Place("porch", "The porch was small and dim, with puddles on the step and the wind tapping the boards.", "the space by the screen door", "dreary", "The porch light shone steady, while the wet boards gleamed safely."),
}

SOURCES = {
    "candle": PromptSource("candle", "light", "a candle", "on the little shelf", "a flame should be watched", 2, 2, "a lamp", tags={"light", "bad"}),
    "lantern": PromptSource("lantern", "light", "a lantern", "near the bed", "light should stay safe", 3, 3, "a night-light", tags={"light", "safe"}),
    "lamp": PromptSource("lamp", "light", "a lamp", "on the bedside table", "care keeps the glow gentle", 4, 4, "a night-light", tags={"light", "safe"}),
}

CANDIDATE_NAMES = ["Mina", "Nora", "Eli", "Theo", "Lena", "Iris", "Milo", "Owen"]
TRAITS = ["careful", "kind", "proud", "thoughtful", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dreary bedtime story world about honour, light, and lessons learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--outcome", choices=["fixed", "bad"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.source and args.place and not source_can_make_story(SOURCES[args.source], PLACES[args.place]):
        raise StoryError(explain_rejection(SOURCES[args.source], PLACES[args.place]))
    place = args.place or rng.choice(sorted(PLACES))
    source = args.source or rng.choice(sorted(SOURCES))
    outcome = args.outcome or ("bad" if source == "candle" else rng.choice(["fixed", "bad"]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice([n for n in CANDIDATE_NAMES if (child_gender == "girl") == (n in {"Mina", "Nora", "Lena", "Iris"})])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, source, outcome, child, child_gender, parent, trait)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    src = SOURCES[params.source]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=[params.trait], age=5))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    lantern = world.add(Entity(id="lantern", type="thing", label=src.label))
    lantern.meters["burning"] = 0.0

    child.memes["honour"] = 1.0
    child.memes["love"] = 1.0
    child.memes["dim"] = 1.0

    world.say(f"It was a {place.mood} night, and {params.child} sat in the {place.id}, listening to the rain.")
    world.say(f"{params.child} had promised to show {params.child_gender and 'honour'} by keeping {src.label} safe until bedtime.")
    world.say(f"But the light felt love-dim and sleepy, and the room seemed to ask for one careless little choice.")

    world.para()
    world.say(f"{params.child} reached toward {src.label} {src.where} and forgot to be careful.")
    world.say(f'The parent frowned gently. "A flame should be watched," {parent.label_word} said, and pointed to the safer glow by the bed.')

    if params.outcome == "bad":
        world.para()
        _burn(world)
        world.say(f"The flame leaped up, and the {place.id} went dreary and gray.")
        world.say(f"{params.child} called for help, but the lantern was ruined before anyone could save the little light.")
        world.say(f"By the end, the rain sounded louder than the child, and the room held only soot, silence, and a sore lesson.")
    else:
        world.para()
        world.say(f"{params.child} stopped, swallowed {child.pronoun('possessive')} pride, and listened.")
        world.say(f"The parent carried the flame away, set up the safe lamp, and turned the room gentle again.")
        child.memes["lesson"] += 1
        child.memes["honour"] += 1
        world.say(f"In the new glow, {params.child} kept the honour of the promise and learned that care makes light last longer.")
        world.say(f"At bedtime, the {place.id} ended with a warm lamp, a tidy blanket, and a child who felt wiser than before.")

    world.facts.update(
        child=child,
        parent=parent,
        place=place,
        source=src,
        outcome=params.outcome,
        room=room,
        lantern=lantern,
        predicted=predict(world, "lantern"),
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "honour", "dreary", and "love-dim".',
        f"Tell a small story about {f['child'].id} and a light that must be handled with care in a {f['place'].id}.",
        "Write a bedtime story where a child learns that pride is not the same as honour.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    place = f["place"]
    src = f["source"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, the parent, and a small light in the {place.id}."),
        ("What kind of night was it?", f"It was a dreary night, with rain and a soft, sleepy feeling in the air."),
        ("What did the child want to protect?", f"{child.id} wanted to protect {src.label} and keep the promise of honour."),
    ]
    if out == "bad":
        qa.append(("What happened to the light?", "The light was ruined. It burned too hard, and the little room grew even drearier afterward."))
        qa.append(("What did the child learn?", "The child learned too late that one careless choice can break a promise and make a small problem become a sad one."))
    else:
        qa.append(("How did the problem end?", "The parent fixed it safely, and the child chose the gentle way instead of the proud way."))
        qa.append(("What did the child learn?", "The child learned that honour means listening, waiting, and keeping light safe so bedtime can stay calm."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a lantern?", "A lantern is a light that can help you see in the dark. It should be used carefully so it stays safe."),
        ("What does dreary mean?", "Dreary means dull, gray, and a little sad, like a rainy evening that feels sleepy."),
        ("What is honour?", "Honour means doing the right thing and keeping a promise, even when it is tempting to do something else."),
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
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, S) :- place(P), source(S), source_can_make_story(P, S).
outcome(bad) :- chosen_outcome(bad).
outcome(fixed) :- chosen_outcome(fixed).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    for pid, place in PLACES.items():
        for sid, src in SOURCES.items():
            if source_can_make_story(src, place):
                lines.append(asp.fact("source_can_make_story", pid, sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, source=None, outcome=None, child=None, child_gender=None, parent=None, trait=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def valid_combos_public() -> list[tuple[str, str, str]]:
    return valid_combos()


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, src in SOURCES.items():
            if source_can_make_story(src, place):
                combos.append((pid, sid, "bad" if src.sense < 3 else "fixed"))
    return combos


def explain_source_rejection(src: PromptSource, place: Place) -> str:
    return f"(No story: {src.label} does not suit the dreary setting of {place.id}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        if not source_can_make_story(SOURCES[args.source], PLACES[args.place]):
            raise StoryError(explain_source_rejection(SOURCES[args.source], PLACES[args.place]))
    place = args.place or rng.choice(sorted(PLACES))
    source = args.source or rng.choice(sorted(SOURCES))
    outcome = args.outcome or ("bad" if source == "candle" else rng.choice(["fixed", "bad"]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_pool = [n for n in CANDIDATE_NAMES if (n in {"Mina", "Nora", "Lena", "Iris"}) == (child_gender == "girl")]
    child = args.child or rng.choice(child_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, source, outcome, child, child_gender, parent, trait)


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
    StoryParams("nursery", "candle", "bad", "Mina", "girl", "mother", "proud"),
    StoryParams("hall", "lamp", "fixed", "Eli", "boy", "father", "thoughtful"),
    StoryParams("porch", "lantern", "bad", "Nora", "girl", "mother", "quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
