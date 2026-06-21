#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oat_reconciliation_sharing_bad_ending_rhyming_story.py
======================================================================================

A tiny storyworld for a rhyming, child-facing reconciliation tale about sharing
an oat snack. The world has a small simulated state: two children want the same
oat bowl, feelings rise and fall in memes, sharing changes ownership and hunger,
and a bad ending is possible when the conflict is not repaired in time.

The narrative stays state-driven:
- premise: a warm snack is found
- tension: both want the same oats
- turn: they either share and reconcile, or refuse and lose the snack
- resolution: the ending image proves what changed

This file is self-contained and uses the shared Storyweavers result containers.
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
GOOD_MIN = 2
BAD_MAX = 1


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    scene: str
    light: str
    props: str
    ending_image: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    warm: bool = True
    shareable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    snack: str
    response: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    trait_a: str
    trait_b: str
    delay: int = 0
    seed: Optional[int] = None
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("a")
    b = world.get("b")
    if a.memes["sad"] >= THRESHOLD and b.memes["sad"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["soft"] += 1
            b.memes["soft"] += 1
            out.append("__soften__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("oat_bowl")
    a = world.get("a")
    b = world.get("b")
    if bowl.meters["shared"] >= THRESHOLD and bowl.meters["eaten"] < THRESHOLD:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["relief"] += 1
            b.memes["relief"] += 1
            out.append("__share__")
    return out


CAUSAL_RULES = [Rule("soften", "social", _r_soften), Rule("share", "social", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def want_share(world: World, child: Entity, snack: Snack) -> None:
    child.memes["want"] += 1
    world.say(
        f'{child.id} saw the {snack.label} and smiled so wide. '
        f'"I want some oat," {child.pronoun()} sighed.'
    )


def tug(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    a.memes["greedy"] += 1
    b.memes["greedy"] += 1
    world.say(
        f'Both reached at once for the warm oat bowl. '
        f'No one would wait, and no one would share.'
    )


def ask_share(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    world.say(
        f'{a.id} said, "Let\'s split the oat and each take a side." '
        f'{b.id} frowned, then looked down.'
    )


def reconcile(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then {b.id} took a breath and nodded. '
        f'"I was rude. You may have the first spoon," {b.id} said.'
    )
    world.say(
        f'{a.id} smiled back and moved the bowl between them. '
        f'They shared the oat and made the room feel bright.'
    )
    bowl = world.get("oat_bowl")
    bowl.meters["shared"] = 1.0
    bowl.meters["eaten"] = 1.0
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["anger"] = 0.0
    b.memes["anger"] = 0.0


def bad_ending(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    bowl = world.get("oat_bowl")
    bowl.meters["dropped"] = 1.0
    bowl.meters["eaten"] = 0.0
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    world.say(
        f'But the two kept tugging, and the bowl tipped with a plop. '
        f'The oat rolled on the floor, and nobody got a bite.'
    )
    world.say(
        f'After that, {a.id} and {b.id} stood quiet and low. '
        f'The snack was lost, and the day felt gray.'
    )


def closing(world: World, place: Place, snack: Snack, happy: bool) -> None:
    if happy:
        world.say(
            f'By the soft lamp glow, the oat bowl sat half empty and nice. '
            f'Two friends, once cross, now shared it with spice.'
        )
    else:
        world.say(
            f'By the dim room light, the empty bowl made a sad little face. '
            f'Their shiny chance to share was gone without a trace.'
        )


PLACES = {
    "kitchen": Place(
        id="kitchen",
        scene="a cozy kitchen",
        light="warm yellow light",
        props="A spoon, a small chair, and a blue napkin waited by the table.",
        ending_image="the bowl sat on the floor by the table leg",
    ),
    "porch": Place(
        id="porch",
        scene="the sunny porch",
        light="soft afternoon light",
        props="A tiny bench, a straw mat, and a little cup waited near the steps.",
        ending_image="the bowl sat by the porch rail",
    ),
}

SNACKS = {
    "oat_bowl": Snack(
        id="oat_bowl",
        label="bowl of oats",
        phrase="a warm bowl of oats",
        smell="sweet and toasty",
        tags={"oat", "sharing"},
    ),
    "oat_cookie": Snack(
        id="oat_cookie",
        label="oat cookie",
        phrase="one oat cookie on a plate",
        smell="sweet and crumbly",
        tags={"oat", "sharing"},
    ),
}

RESPONSES = {
    "share_turn": Response(
        id="share_turn",
        sense=3,
        power=3,
        text="pushed the bowl closer and spoke kindly, then shared the spoon",
        fail="tried to share, but the quarrel was too big",
        qa_text="pushed the bowl closer and shared the spoon",
        tags={"share"},
    ),
    "pause": Response(
        id="pause",
        sense=2,
        power=2,
        text="paused and listened, then suggested a fair turn",
        fail="paused too late, and the snack spilled away",
        qa_text="paused and suggested a fair turn",
        tags={"reconcile"},
    ),
    "too_late": Response(
        id="too_late",
        sense=1,
        power=1,
        text="spoke softly, but the bowl had already been knocked over",
        fail="spoke softly, but the bowl had already been knocked over",
        qa_text="spoke softly, but it was already too late",
        tags={"bad_ending"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Tia", "Ava"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Noah"]
TRAITS = ["gentle", "proud", "quick", "careful", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid in PLACES:
        for sid, snack in SNACKS.items():
            if "oat" in snack.tags:
                combos.append((pid, sid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about sharing oats and making peace.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.snack is None or c[1] == args.snack)]
    if not combos:
        raise StoryError("(No valid oat story matches the given options.)")
    place, snack = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    a_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    a_gender = "girl" if a_name in GIRL_NAMES else "boy"
    b_gender = "girl" if b_name in GIRL_NAMES else "boy"
    return StoryParams(
        place=place,
        snack=snack,
        response=response,
        child_a=a_name,
        child_a_gender=a_gender,
        child_b=b_name,
        child_b_gender=b_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        delay=rng.randint(0, 2),
    )


def _make_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = World()
    a = world.add(Entity(id="a", kind="character", type=params.child_a_gender, label=params.child_a, traits=[params.trait_a]))
    b = world.add(Entity(id="b", kind="character", type=params.child_b_gender, label=params.child_b, traits=[params.trait_b]))
    world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    bowl = world.add(Entity(id="oat_bowl", kind="thing", type="snack", label=SNACKS[params.snack].label))
    place = PLACES[params.place]
    snack = SNACKS[params.snack]

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"At {place.scene}, the air was light and bright.")
    world.say(f"{place.props}")
    world.say(f"A sweet oat smell drifted near, from {snack.phrase}.")

    world.para()
    want_share(world, a, snack)
    want_share(world, b, snack)
    tug(world, a, b, snack)
    ask_share(world, a, b, snack)

    if params.response == "too_late" or params.delay >= 2:
        world.para()
        bad_ending(world, a, b, snack)
        closing(world, place, snack, happy=False)
        bowl.meters["shared"] = 0.0
        bowl.meters["eaten"] = 0.0
        outcome = "bad"
    else:
        world.para()
        reconcile(world, a, b, snack)
        closing(world, place, snack, happy=True)
        outcome = "shared"

    world.facts.update(
        place=place,
        snack=snack,
        response=RESPONSES[params.response],
        a=a,
        b=b,
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    snack = f["snack"]
    return [
        f'Write a rhyming story for a child about sharing {snack.label} in {place.scene}.',
        f"Tell a short rhyme where two children want {snack.phrase}, then either share it kindly or lose it in a bad ending.",
        f'Write a gentle rhyming tale that includes the word "oat" and ends with either a happy sharing moment or a sad spilled snack.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    snack = f["snack"]
    out = [
        ("Who was in the story?", f"It was about {a.label_word if hasattr(a, 'label_word') else a.id} and {b.label_word if hasattr(b, 'label_word') else b.id}, two children who wanted the same oat snack."),
        ("What did they want?", f"They both wanted {snack.phrase}. The warm oat bowl looked good to both of them, which started the problem."),
    ]
    if f["outcome"] == "shared":
        out.append((
            "How did they fix the problem?",
            f"They reconciled and shared the bowl. One child moved it closer, they took turns, and the oat stayed on the table instead of becoming a fight.",
        ))
        out.append((
            "How did the story end?",
            "It ended with peace and sharing. The bowl was half empty, and the two children were sitting close together again.",
        ))
    else:
        out.append((
            "What went wrong at the end?",
            "They would not calm down in time, so the bowl tipped over. The oat spilled away, and nobody got to eat it.",
        ))
        out.append((
            "How did the children feel last?",
            "They felt sad and quiet. The lost snack left them with a bad ending instead of a friendly one.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is oat?", "Oat is a grain people cook into breakfast food or bake into cookies. It can be warm, soft, and good to share."),
        ("Why is sharing nice?", "Sharing helps two people both enjoy something instead of fighting over it. It can turn a grumpy moment into a friendly one."),
        ("What happens if a bowl is knocked over?", "If a bowl is knocked over, the food may spill and get wasted. Then nobody can eat it from the floor."),
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


ASP_RULES = r"""
valid(P, S) :- place(P), snack(S), oat_snack(S).
outcome(shared) :- chosen_response(R), response(R), sense(R, S), good_min(M), S >= M, not too_late(R).
outcome(bad) :- chosen_response(R), response(R), too_late(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if "oat" in snack.tags:
            lines.append(asp.fact("oat_snack", sid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        if rid == "too_late":
            lines.append(asp.fact("too_late", rid))
    lines.append(asp.fact("good_min", GOOD_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_response", params.response)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            print("MISMATCH: outcome parity failed.")
            rc = 1
            break
    if rc == 0:
        print("OK: ASP/Python parity and generation verified.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if params.response == "too_late" or params.delay >= 2:
        return "bad"
    return "shared"


CURATED = [
    StoryParams(place="kitchen", snack="oat_bowl", response="share_turn", child_a="Mia", child_a_gender="girl", child_b="Noah", child_b_gender="boy", parent="mother", trait_a="gentle", trait_b="curious", delay=0),
    StoryParams(place="porch", snack="oat_cookie", response="pause", child_a="Owen", child_a_gender="boy", child_b="Luna", child_b_gender="girl", parent="father", trait_a="proud", trait_b="careful", delay=1),
    StoryParams(place="kitchen", snack="oat_bowl", response="too_late", child_a="Ava", child_a_gender="girl", child_b="Finn", child_b_gender="boy", parent="mother", trait_a="quick", trait_b="curious", delay=2),
]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.label:
                bits.append(f"label={e.label}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)]
    if not combos:
        raise StoryError("(No valid oat story matches the given options.)")
    place, snack = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    a_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    return StoryParams(
        place=place,
        snack=snack,
        response=response,
        child_a=a_name,
        child_a_gender="girl" if a_name in GIRL_NAMES else "boy",
        child_b=b_name,
        child_b_gender="girl" if b_name in GIRL_NAMES else "boy",
        parent=args.parent or rng.choice(["mother", "father"]),
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        delay=rng.randint(0, 2),
    )


def build_parser_alias() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_from_args(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} and {p.child_b}: oat story ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
