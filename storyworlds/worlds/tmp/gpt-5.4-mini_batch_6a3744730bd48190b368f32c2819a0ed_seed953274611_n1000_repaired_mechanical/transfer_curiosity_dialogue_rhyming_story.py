#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/transfer_curiosity_dialogue_rhyming_story.py
=============================================================================

A small storyworld for a curiosity-and-dialogue tale about transfer: a child
finds something, wonders about it, asks questions, and learns to pass it along
safely to the right place or person.

The stories are written in a light rhyming style, but the world model is still
state-driven: curiosity rises, dialogue changes intent, and a transfer either
happens to a helper or is redirected to a safer place.

Core premise
------------
A child notices a small interesting object or note, gets curious, and talks
with a friend or adult. The dialogue turns the moment from "keep it" into
"transfer it" -- usually by moving it to a better owner, box, shelf, or helper.

This world keeps the action tiny and concrete:
- typed entities have physical meters and emotional memes
- transfer is a simulated state change, not a frozen sentence swap
- the story has a beginning, a middle turn, and an ending image proving change
- the prose keeps a gentle rhyme flavor without becoming sing-song scaffolding

It supports:
    python ...py
    python ...py -n 10 --seed 777 --qa
    python ...py --json
    python ...py --trace
    python ...py --asp
    python ...py --verify
    python ...py --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}
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
class Thing:
    id: str
    label: str
    category: str
    curious: bool = False
    transferable_to: set[str] = field(default_factory=set)
    transfer_reason: str = ""
    safe_place: str = ""
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
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    adult_role: str
    thing: str
    transfer_mode: str
    ending: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.role != "child":
            continue
        if child.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("curious", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
        out.append("__curious__")
    return out


def _r_dialogue(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    other = world.entities.get("other")
    thing = world.entities.get("thing")
    if not child or not other or not thing:
        return out
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if other.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("dialogue", child.id, other.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["courage"] = child.memes.get("courage", 0.0) + 1
    other.memes["care"] = other.memes.get("care", 0.0) + 1
    out.append("__dialogue__")
    return out


def _r_transfer(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    other = world.entities.get("other")
    thing = world.entities.get("thing")
    if not child or not other or not thing:
        return out
    if thing.meters.get("held", 0.0) < THRESHOLD:
        return out
    sig = ("transfer", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["held"] = 0.0
    thing.meters["transferred"] = thing.meters.get("transferred", 0.0) + 1
    other.meters["received"] = other.meters.get("received", 0.0) + 1
    out.append("__transfer__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    thing = world.entities.get("thing")
    child = world.entities.get("child")
    other = world.entities.get("other")
    if not thing or not child or not other:
        return out
    if thing.meters.get("transferred", 0.0) < THRESHOLD:
        return out
    sig = ("settle", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    other.memes["gratitude"] = other.memes.get("gratitude", 0.0) + 1
    out.append("__settle__")
    return out


CAUSAL_RULES = [
    Rule("curiosity", _r_curiosity),
    Rule("dialogue", _r_dialogue),
    Rule("transfer", _r_transfer),
    Rule("settle", _r_settle),
]


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


def make_transfer_possible(thing: Thing, mode: str) -> bool:
    return mode in thing.transferable_to


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in CHILDREN:
        for other in OTHERS:
            for thing_id, thing in THINGS.items():
                for mode in TRANSFER_MODES:
                    if make_transfer_possible(thing, mode):
                        combos.append((child, other, thing_id, mode))
    return combos


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(thing: Thing, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id="child", kind="character", type=params.child_gender,
        role="child", attrs={"name": params.child_name},
        memes={"curiosity": 1.0, "joy": 1.0},
    ))
    other = world.add(Entity(
        id="other", kind="character", type=params.friend_gender,
        role="other", attrs={"name": params.friend_name, "role": params.adult_role},
        memes={"kindness": 1.0},
    ))
    world.add(Entity(
        id="thing", kind="thing", type=thing.category, label=thing.label,
        attrs={"safe_place": thing.safe_place},
        meters={"held": 1.0},
    ))

    # Beginning
    world.say(
        f"{params.child_name} found a little {thing.label} in the light of day, "
        f"and wondered aloud in a curious way."
    )
    world.say(
        f"{params.friend_name} came near with a gentle grin; "
        f'"What is it for? Can we peek within?"'
    )

    # Middle turn
    world.para()
    world.say(
        f"{params.child_name} asked, " +
        f'"Should we keep it here, or send it along?" '
        f'{params.friend_name} said, "Let us do what is kind and strong."'
    )
    child.memes["curiosity"] += 1
    other.memes["kindness"] += 1
    if params.transfer_mode == "to_adult":
        world.say(
            f'They chose to carry it to {params.adult_role}, with careful feet and a '
            f"steady pace; the grown-up could tell them the proper place."
        )
    elif params.transfer_mode == "to_box":
        world.say(
            f'They slid it into a bright little box, so it could rest and not get lost; '
            f"that tidy transfer kept its shine, and cost them naught."
        )
    else:
        world.say(
            f'They passed it to the right helper near, so someone else could use it here; '
            f"the little thing felt safer then, as if it had found its peer."
        )
    world.get("thing").meters["held"] = 1.0
    propagate(world, narrate=False)

    # Resolution
    world.para()
    if params.ending == "warm":
        world.say(
            f"At the end they smiled with a settled glow, for transfer made the right thing grow."
        )
        world.say(
            f"{params.child_name} learned that asking first was wise, and helping others was a prize."
        )
    else:
        world.say(
            f"The little {thing.label} moved from hand to hand, till all agreed it fit the plan."
        )
        world.say(
            f"{params.friend_name} waved and said, " +
            f'"That was the neatest choice today."'
        )

    world.facts.update(
        child=child, other=other, thing=world.get("thing"), params=params, thing_cfg=thing
    )
    return world


# Registries
CHILDREN = ["Ava", "Milo", "Nina", "Leo", "Zoe", "Eli"]
OTHERS = ["Mia", "Noah", "Ivy", "Owen", "Sage", "June"]
ADULT_ROLES = ["mom", "dad", "teacher", "helper"]
TRANSFER_MODES = ["to_adult", "to_box", "to_helper"]

THINGS = {
    "shell": Thing(
        id="shell", label="shell", category="treasure",
        curious=True, transferable_to={"to_box", "to_helper"},
        transfer_reason="it was meant to be shared and shown",
        safe_place="a little box on the shelf", tags={"shell", "curiosity"},
    ),
    "note": Thing(
        id="note", label="note", category="message",
        curious=True, transferable_to={"to_adult", "to_helper"},
        transfer_reason="it had words for a grown-up to read",
        safe_place="an adult's hand", tags={"note", "message", "curiosity"},
    ),
    "key": Thing(
        id="key", label="key", category="object",
        curious=True, transferable_to={"to_adult", "to_box"},
        transfer_reason="it belonged somewhere else",
        safe_place="a labeled hook by the door", tags={"key", "curiosity"},
    ),
}

CURATED = [
    StoryParams(
        child_name="Ava", child_gender="girl",
        friend_name="Mia", friend_gender="girl",
        adult_role="mom", thing="shell", transfer_mode="to_box", ending="warm", seed=11
    ),
    StoryParams(
        child_name="Leo", child_gender="boy",
        friend_name="Noah", friend_gender="boy",
        adult_role="dad", thing="note", transfer_mode="to_adult", ending="bright", seed=12
    ),
    StoryParams(
        child_name="Nina", child_gender="girl",
        friend_name="Sage", friend_gender="girl",
        adult_role="teacher", thing="key", transfer_mode="to_box", ending="warm", seed=13
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.thing not in THINGS:
        raise StoryError("(No story: unknown thing.)")
    if args.transfer and args.transfer not in TRANSFER_MODES:
        raise StoryError("(No story: unknown transfer mode.)")

    thing_id = args.thing or rng.choice(sorted(THINGS))
    thing = THINGS[thing_id]
    transfer_mode = args.transfer or rng.choice(sorted(thing.transferable_to))
    if not make_transfer_possible(thing, transfer_mode):
        raise StoryError(
            f"(No story: the {thing.label} does not fit the transfer '{transfer_mode}'. "
            f"Choose a mode that matches its safe path.)"
        )
    child_name = args.child or rng.choice(CHILDREN)
    friend_name = args.friend or rng.choice([n for n in OTHERS if n != child_name])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    adult_role = args.adult or rng.choice(ADULT_ROLES)
    ending = args.ending or rng.choice(["warm", "bright"])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_role=adult_role,
        thing=thing_id,
        transfer_mode=transfer_mode,
        ending=ending,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params = f["params"]
    thing = f["thing_cfg"]
    return [
        f'Write a rhyming story for a young child that includes the word "transfer" and '
        f'features a curious child asking questions about a {thing.label}.',
        f"Tell a gentle dialogue story where {params.child_name} and {params.friend_name} "
        f"wonder what to do with the {thing.label} and decide to transfer it the right way.",
        f'Create a short rhyming story with curiosity, questions, and a safe transfer of '
        f'a {thing.label} to its proper place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params = f["params"]
    thing = f["thing_cfg"]
    child = f["child"]
    other = f["other"]
    answer1 = (
        f"The story is about {params.child_name} and {params.friend_name}, who got curious "
        f"about a {thing.label}. Their talk led them to transfer it where it belonged."
    )
    answer2 = (
        f"{params.child_name} asked questions because {child.memes.get('curiosity', 0.0) > 1.0} "
        f"curiosity was growing in the world. The dialogue helped turn wondering into a calm, "
        f"useful choice."
    )
    answer3 = (
        f"They transferred the {thing.label} to the proper safe place, and that changed "
        f"{params.child_name}'s feeling from plain curiosity to relief."
    )
    return [
        QAItem(question=f"Who is the story about?", answer=answer1),
        QAItem(question=f"Why did {params.child_name} keep asking questions?", answer=answer2),
        QAItem(question=f"What changed by the end?", answer=answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    thing = world.facts["thing_cfg"]
    return [
        QAItem(
            question="What does transfer mean in this story world?",
            answer=(
                "Transfer means to move something from one hand or place to another "
                "when that new place is better or safer."
            ),
        ),
        QAItem(
            question=f"Why was the {thing.label} moved instead of kept?",
            answer=(
                f"It was curious and needed the right place. Moving it kept the little "
                f"story world neat and made sure it got to the helper or box that fit."
            ),
        ),
        QAItem(
            question="What helps the child make a good choice?",
            answer=(
                "Curiosity starts the question, and dialogue helps answer it. When the "
                "characters talk kindly, they can choose the safer transfer."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell_story(params: StoryParams) -> World:
    if params.thing not in THINGS:
        raise StoryError("(No story: invalid thing choice.)")
    if params.transfer_mode not in TRANSFER_MODES:
        raise StoryError("(No story: invalid transfer choice.)")
    thing = THINGS[params.thing]
    if not make_transfer_possible(thing, params.transfer_mode):
        raise StoryError("(No story: the chosen transfer does not fit the thing.)")
    return tell(thing, params)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming storyworld about curiosity, dialogue, and transfer."
    )
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_ROLES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--transfer", choices=TRANSFER_MODES)
    ap.add_argument("--ending", choices=["warm", "bright"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        if thing.curious:
            lines.append(asp.fact("curious_thing", thing_id))
        for mode in sorted(thing.transferable_to):
            lines.append(asp.fact("can_transfer", thing_id, mode))
    for mode in TRANSFER_MODES:
        lines.append(asp.fact("transfer_mode", mode))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, M) :- thing(T), transfer_mode(M), can_transfer(T, M).
curious(T) :- curious_thing(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_curious() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show curious/1."))
    return sorted(t for (t,) in asp.atoms(model, "curious"))


def valid_thing_mode_pairs() -> list[tuple[str, str]]:
    pairs = []
    for thing_id, thing in THINGS.items():
        for mode in TRANSFER_MODES:
            if make_transfer_possible(thing, mode):
                pairs.append((thing_id, mode))
    return pairs


def asp_verify() -> int:
    rc = 0
    py = set(valid_thing_mode_pairs())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid pairs ({len(py)}).")
    else:
        rc = 1
        print("MISMATCH in valid pairs:")
        print("  only python:", sorted(py - cl))
        print("  only ASP:", sorted(cl - py))

    if set(asp_curious()) == {tid for tid, t in THINGS.items() if t.curious}:
        print("OK: ASP curious set matches.")
    else:
        rc = 1
        print("MISMATCH in curious set.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke generate succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.thing not in THINGS:
        raise StoryError("(No story: unknown thing.)")
    if args.transfer and args.transfer not in TRANSFER_MODES:
        raise StoryError("(No story: unknown transfer mode.)")
    if args.thing and args.transfer:
        if not make_transfer_possible(THINGS[args.thing], args.transfer):
            raise StoryError("(No story: that transfer does not fit the chosen thing.)")

    thing_id = args.thing or rng.choice(sorted(THINGS))
    thing = THINGS[thing_id]
    transfer = args.transfer or rng.choice(sorted(thing.transferable_to))
    if not make_transfer_possible(thing, transfer):
        raise StoryError("(No story: no reasonable transfer option here.)")

    child_name = args.child or rng.choice(sorted(CHILDREN))
    friend_name = args.friend or rng.choice([n for n in OTHERS if n != child_name])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(ADULT_ROLES)
    ending = args.ending or rng.choice(["warm", "bright"])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_role=adult,
        thing=thing_id,
        transfer_mode=transfer,
        ending=ending,
    )


CHILDREN = ["Ava", "Milo", "Nina", "Leo", "Zoe", "Eli"]
OTHERS = ["Mia", "Noah", "Ivy", "Owen", "Sage", "June"]

CURATED = [
    StoryParams(
        child_name="Ava", child_gender="girl",
        friend_name="Mia", friend_gender="girl",
        adult_role="mom", thing="shell", transfer_mode="to_box", ending="warm", seed=11,
    ),
    StoryParams(
        child_name="Leo", child_gender="boy",
        friend_name="Noah", friend_gender="boy",
        adult_role="dad", thing="note", transfer_mode="to_adult", ending="bright", seed=12,
    ),
    StoryParams(
        child_name="Nina", child_gender="girl",
        friend_name="Sage", friend_gender="girl",
        adult_role="teacher", thing="key", transfer_mode="to_box", ending="warm", seed=13,
    ),
]


def generation_story(world: World) -> str:
    return world.render()


def tell(thing: Thing, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id="child", kind="character", type=params.child_gender, role="child",
        attrs={"name": params.child_name}, memes={"curiosity": 1.0, "joy": 1.0},
    ))
    other = world.add(Entity(
        id="other", kind="character", type=params.friend_gender, role="other",
        attrs={"name": params.friend_name, "adult_role": params.adult_role},
        memes={"kindness": 1.0},
    ))
    thing_ent = world.add(Entity(
        id="thing", kind="thing", type=thing.category, label=thing.label,
        meters={"held": 1.0}, attrs={"safe_place": thing.safe_place},
    ))

    world.say(
        f"{params.child_name} found a little {thing.label} and paused to stare, "
        f"with curious eyes and wondering air."
    )
    world.say(
        f"{params.friend_name} came close and asked in tune, "
        f'"What is it for? Tell me soon."'
    )

    world.para()
    world.say(
        f'{params.child_name} said, "Should we keep it tight, or transfer it to the right?" '
        f'{params.friend_name} replied, "Let us ask and do what feels polite."'
    )
    child.memes["curiosity"] += 1
    other.memes["kindness"] += 1

    if params.transfer_mode == "to_adult":
        world.say(
            f"They carried it to {params.adult_role}, neat and slow, so a grown-up could say where it should go."
        )
    elif params.transfer_mode == "to_box":
        world.say(
            f"They placed it in a little box with care, so it could rest and wait right there."
        )
    else:
        world.say(
            f"They handed it to a helper who knew the spot, and the helper smiled: "
            f'"That fits the plan a lot."'
        )

    thing_ent.meters["held"] = 0.0
    thing_ent.meters["transferred"] = 1.0
    other.meters["received"] = 1.0
    propagate(world, narrate=False)

    world.para()
    if params.ending == "warm":
        world.say(
            f"At day’s end the little thing was set in place, and both children shone with a calmer face."
        )
        world.say(
            f"{params.child_name} learned that a curious start can bloom, and dialogue can clear the room."
        )
    else:
        world.say(
            f"The tiny transfer made the right path gleam, and everyone smiled at the tidy dream."
        )
        world.say(
            f"By the end, {params.child_name} knew to ask before a keep, so kindness could run deep."
        )

    world.facts.update(
        child=child,
        other=other,
        thing=thing_ent,
        params=params,
        thing_cfg=thing,
    )
    return world


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def world_knowledge_qa(world: World) -> list[QAItem]:
    thing = world.facts["thing_cfg"]
    return [
        QAItem(
            question="What does transfer mean here?",
            answer="It means moving something from one place or hand to another place that suits it better.",
        ),
        QAItem(
            question=f"Why did the children talk before moving the {thing.label}?",
            answer="They were curious, and dialogue helped them choose the right next step instead of guessing.",
        ),
        QAItem(
            question="What did the ending prove?",
            answer="It proved that the object had been moved to its proper place, and the child felt calmer after the transfer.",
        ),
    ]


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for child in CHILDREN:
        for other in OTHERS:
            if other == child:
                continue
            for thing_id, thing in THINGS.items():
                for mode in TRANSFER_MODES:
                    if make_transfer_possible(thing, mode):
                        out.append((child, other, thing_id, mode))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show curious/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show valid/2.\n#show curious/1."))
        valid = sorted(set(asp.atoms(model, "valid")))
        curious = sorted(set(asp.atoms(model, "curious")))
        print(f"valid pairs: {len(valid)}")
        for thing_id, mode in valid:
            print(f"  {thing_id:8} {mode}")
        print(f"\ncurious things: {', '.join(t for (t,) in curious)}")
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
