#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/speculate_dialogue_slice_of_life.py
====================================================================

A small standalone story world for a slice-of-life scene built around the word
"speculate" and dialogue: a child makes a guess about a neighbor's day, another
person gently corrects them, and the guess turns into a kind, ordinary plan.

The world is intentionally tiny and state-driven. It simulates:
- a place
- a child with an assumption and a feeling
- a second speaker who either confirms or corrects the speculation
- a small ordinary action that resolves the moment

The prose is written from the changing world state, not from a frozen template.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



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
    cozy: bool = True
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
class Speculation:
    id: str
    guess: str
    question: str
    tag: str
    wrong_if: Optional[str] = None
    right_if: Optional[str] = None

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
class SmallAction:
    id: str
    text: str
    effect: str
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["worry"] < THRESHOLD:
        return out
    if ("relief",) in world.fired:
        return out
    if child.memes["clarified"] >= THRESHOLD:
        world.fired.add(("relief",))
        child.memes["worry"] = 0.0
        child.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


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


def speculate_guard(speculation: Speculation, actual: str) -> bool:
    return actual in {speculation.wrong_if, speculation.right_if, speculation.tag}


def predict(world: World, actual: str) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    if actual == "wrong":
        sim.get("child").memes["confused"] += 1
    else:
        sim.get("child").memes["clarified"] += 1
    propagate(sim, narrate=False)
    return {"relief": sim.get("child").memes["relief"], "worry": sim.get("child").memes["worry"]}


def introduce(world: World, child: Entity, listener: Entity, place: Place, spec: Speculation) -> None:
    child.memes["curious"] += 1
    world.say(
        f"At {place.label}, {child.id} looked across the room and said, "
        f'"I {spec.guess} about {listener.id}."'
    )
    world.say(
        f'{listener.id} smiled a little. "{spec.question}" {listener.pronoun()} asked.'
    )


def worry(world: World, child: Entity, spec: Speculation) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip. "
        f'"Well," {child.pronoun()} said, "I was just trying to figure things out."'
    )
    world.say(
        f"It was the kind of quiet morning where a child could speculate out loud "
        f"and still hear the kettle click in the kitchen."
    )


def correct(world: World, listener: Entity, child: Entity, spec: Speculation) -> None:
    child.memes["clarified"] += 1
    predicted = predict(world, "right")
    world.facts["predicted_relief"] = predicted["relief"]
    world.say(
        f'"Not quite," {listener.id} said kindly. "{spec.tag.capitalize()} is close, '
        f'but I meant something simpler than that."'
    )


def explain(world: World, listener: Entity, child: Entity, spec: Speculation) -> None:
    world.say(
        f'"I was going to {spec.tag} the whole afternoon," {listener.id} said. '
        f'"But first I needed a cup of tea and a quiet seat by the window."'
    )
    world.say(
        f'{child.id} laughed softly. "Oh! I thought it was bigger than that."'
    )


def action(world: World, child: Entity, listener: Entity, move: SmallAction) -> None:
    child.memes["joy"] += 1
    listener.memes["joy"] += 1
    world.say(
        f"Then {child.id} did the little helpful thing instead: {move.text}."
    )
    world.say(move.effect)


def ending(world: World, child: Entity, listener: Entity, place: Place) -> None:
    world.say(
        f"By the end, the morning felt ordinary again -- {place.label} stayed warm, "
        f"the kettle was quiet, and {child.id}'s guess had turned into a better understanding."
    )


def tell(place: Place, spec: Speculation, move: SmallAction,
         child_name: str = "Mina", child_gender: str = "girl",
         listener_name: str = "Grandma", listener_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    listener = world.add(Entity(id=listener_name, kind="character", type=listener_gender, role="listener"))
    world.facts["place"] = place
    world.facts["speculation"] = spec
    world.facts["move"] = move

    introduce(world, child, listener, place, spec)
    world.para()
    worry(world, child, spec)
    correct(world, listener, child, spec)
    explain(world, listener, child, spec)
    world.para()
    action(world, child, listener, move)
    ending(world, child, listener, place)

    world.facts.update(
        child=child,
        listener=listener,
        clarified=child.memes["clarified"] >= THRESHOLD,
        worry=child.memes["worry"],
        relief=child.memes["relief"],
    )
    return world


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", cozy=True, tags={"tea", "home"}),
    "porch": Place("porch", "the porch", cozy=True, tags={"neighbors", "home"}),
    "library": Place("library", "the library corner", cozy=True, tags={"quiet", "books"}),
}

SPECULATIONS = {
    "tea": Speculation(
        "tea",
        "speculate",
        "Do you think I was making tea?",
        tag="tea",
        wrong_if="mail",
        right_if="tea",
    ),
    "garden": Speculation(
        "garden",
        "speculate",
        "Are you going to the garden next?",
        tag="garden",
        wrong_if="store",
        right_if="garden",
    ),
    "nap": Speculation(
        "nap",
        "speculate",
        "Were you about to take a nap?",
        tag="nap",
        wrong_if="game",
        right_if="nap",
    ),
}

ACTIONS = {
    "pour": SmallAction("pour", "pour hot water into the mug", "The steam rose in a tiny silver ribbon.", tags={"tea"}),
    "water": SmallAction("water", "water the little pot of basil", "The basil looked brighter right away.", tags={"garden"}),
    "blanket": SmallAction("blanket", "bring a soft blanket from the chair", "The listener tucked it around the child with a warm grin.", tags={"nap"}),
}

GIRL_NAMES = ["Mina", "Tessa", "Lena", "Ruby", "Ivy", "Nora"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Ben", "Milo", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, spec) for place in PLACES for spec in SPECULATIONS if speculate_guard(SPECULATIONS[spec], spec)]


@dataclass
@dataclass
class StoryParams:
    place: str
    speculation: str
    action: str
    child: str
    child_gender: str
    listener: str
    listener_gender: str
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


KNOWLEDGE = {
    "speculate": [("What does speculate mean?",
                  "To speculate means to make a guess about something when you do not know for sure. It is a thoughtful kind of wondering.")],
    "tea": [("What is tea?",
             "Tea is a warm drink people make by steeping leaves in hot water. Many people drink it slowly and quietly.")],
    "garden": [("What is a garden?",
                 "A garden is a place where people grow flowers, herbs, and other plants.")],
    "nap": [("What is a nap?",
              "A nap is a short sleep taken during the day when someone feels tired.")],
    "kitchen": [("What do people do in a kitchen?",
                  "People in a kitchen cook, wash dishes, make warm drinks, and gather for small meals.")],
    "library": [("What is a library?",
                 "A library is a quiet place where people read and borrow books.")],
}
KNOWLEDGE_ORDER = ["speculate", "tea", "garden", "nap", "kitchen", "library"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    spec: Speculation = f["speculation"]
    return [
        f'Write a slice-of-life story for a young child that uses the word "{spec.tag}" and includes dialogue.',
        f"Tell a gentle everyday story set at {place.label} where one person says they can {spec.guess}, but another person corrects the guess kindly.",
        f'Write a calm story where someone says "{spec.question}" and the guess turns into a friendly little conversation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    listener: Entity = f["listener"]
    place: Place = f["place"]
    spec: Speculation = f["speculation"]
    move: SmallAction = f["move"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {listener.id}, who are sharing an ordinary moment at {place.label}. The whole story stays close to a small conversation and a gentle choice.",
        ),
        QAItem(
            question=f"What did {child.id} speculate about?",
            answer=f"{child.id} said {spec.guess} and was trying to make sense of what {listener.id} was doing. It was a guess, not a sure thing, so the answer needed a little clarification.",
        ),
        QAItem(
            question="How did the conversation end?",
            answer=f"It ended with a small helpful action: {move.text}. That made the moment feel settled and warm instead of uncertain.",
        ),
    ]
    if f.get("clarified"):
        qa.append(
            QAItem(
                question=f"Why did {listener.id} correct {child.id} kindly?",
                answer=f"{listener.id} corrected {child.id} because the first guess was close but not exact. The correction turned the speculation into understanding, which made the child feel better.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["speculation"].tag}
    tags |= f["place"].tags
    tags |= f["move"].tags
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "tea", "pour", "Mina", "girl", "Grandma", "woman"),
    StoryParams("porch", "garden", "water", "Owen", "boy", "Aunt", "aunt"),
    StoryParams("library", "nap", "blanket", "Nora", "girl", "Dad", "man"),
]


def explain_rejection(place: Place, spec: Speculation) -> str:
    return f"(No story: the set-up does not support a calm speculation about {spec.tag} at {place.label}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, t))
    for sid, s in SPECULATIONS.items():
        lines.append(asp.fact("speculation", sid))
        lines.append(asp.fact("speculate_word", sid, s.tag))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("action_tag", aid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, S) :- place(P), speculation(S), place_tag(P, T), speculate_word(S, T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, speculation=None, action=None, child=None, child_gender=None, listener=None, listener_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with speculate and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--speculation", choices=SPECULATIONS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--listener")
    ap.add_argument("--listener-gender", dest="listener_gender", choices=["woman", "man", "aunt", "uncle"])
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
              and (args.speculation is None or c[1] == args.speculation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spec_id = rng.choice(sorted(combos))
    spec = SPECULATIONS[spec_id]
    action = args.action or {"tea": "pour", "garden": "water", "nap": "blanket"}[spec.tag]
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    listener_gender = args.listener_gender or rng.choice(["woman", "man", "aunt", "uncle"])
    listener = args.listener or {"woman": "Grandma", "man": "Dad", "aunt": "Aunt", "uncle": "Uncle"}[listener_gender]
    return StoryParams(place, spec_id, action, child, child_gender, listener, listener_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPECULATIONS[params.speculation], ACTIONS[params.action],
                 params.child, params.child_gender, params.listener, params.listener_gender)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, speculation) combos:\n")
        for place, spec in combos:
            print(f"  {place:10} {spec}")
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
            header = f"### {p.child} and {p.listener}: {p.speculation} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
