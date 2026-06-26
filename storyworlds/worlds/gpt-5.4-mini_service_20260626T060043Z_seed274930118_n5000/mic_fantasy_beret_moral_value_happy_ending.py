#!/usr/bin/env python3
"""
storyworlds/worlds/mic_fantasy_beret_moral_value_happy_ending.py
=================================================================

A small heartwarming story world about a child, a fantasy pretend-play setup,
and the gentle lesson that sharing can make play better.

Seed tale used to build the world:
---
A child finds a shiny toy mic and a soft beret in a fantasy costume box.
The child wants to be the star of a pretend castle show, but a friend also
wants to use the props. At first, both children want the same things at the
same time. Then they decide to share the mic and the beret, take turns, and
make the show together. The ending is warm and happy, because both children
feel proud, included, and kind.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sparkle": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    parent_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_share_joy(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("sharing", 0.0) >= THRESHOLD and ent.memes.get("conflict", 0.0) >= THRESHOLD:
            sig = ("share_joy", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["conflict"] = 0.0
            ent.memes["joy"] = ent.memes.get("joy", 0.0) + 1.0
            out.append(f"Sharing helped {ent.label or ent.id} feel calm again.")
    return out


def _r_together(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    mic = world.facts.get("mic")
    beret = world.facts.get("beret")
    if not (hero and friend and mic and beret):
        return out
    if hero.memes.get("sharing", 0.0) >= THRESHOLD and friend.memes.get("sharing", 0.0) >= THRESHOLD:
        sig = ("together", hero.id, friend.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
        friend.memes["pride"] = friend.memes.get("pride", 0.0) + 1.0
        out.append("__together__")
    return out


CAUSAL_RULES = [Rule("share_joy", _r_share_joy), Rule("together", _r_together)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__together__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "castle_playroom": Setting(place="the castle playroom", indoors=True, affords={"pretend_show"}),
    "storybook_corner": Setting(place="the storybook corner", indoors=True, affords={"pretend_show"}),
}

PROPS = {
    "mic": Prop(id="mic", label="toy mic", phrase="a shiny toy mic", kind="mic", tags={"mic", "share"}),
    "beret": Prop(id="beret", label="beret", phrase="a soft red beret", kind="beret", tags={"beret", "costume", "share"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Finn", "Theo"]
TRAITS = ["curious", "gentle", "playful", "kind", "bright"]
FRIEND_NAMES = ["Eli", "June", "Pip", "Zoe", "Mina"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "pretend_show") for place in SETTINGS]


@dataclass
class ASPRules:
    pass


ASP_RULES = r"""
% A story is valid when the setting affords the pretend show.
valid(Place, Activity) :- affords(Place, Activity).

% Sharing is the compatible moral turn.
shared(Actor) :- sharing(Actor), not conflict(Actor).
happy_ending(Actor, Friend) :- shared(Actor), shared(Friend), valid(Place, pretend_show).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for tag in sorted(prop.tags):
            lines.append(asp.fact("tagged", pid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming fantasy sharing story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-role", choices=["mother", "father"], default="mother")
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent_role=args.parent_role,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=["little", "kind"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name, traits=["little", "patient"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_role, label=params.parent_role))
    mic = world.add(Entity(id="mic", type="mic", label="toy mic", phrase="a shiny toy mic", owner=hero.id))
    beret = world.add(Entity(id="beret", type="beret", label="beret", phrase="a soft red beret", owner=hero.id))
    world.facts.update(hero=hero, friend=friend, parent=parent, mic=mic, beret=beret)
    return world


def _begin(world: World) -> None:
    h, f, p, mic, beret = world.facts["hero"], world.facts["friend"], world.facts["parent"], world.facts["mic"], world.facts["beret"]
    world.say(f"{h.label} was a little {h.pronoun('possessive')} {world.setting.place.replace('the ', '')} favorite, because the room felt like a fantasy castle on show day.")
    world.say(f"{h.label} found {mic.phrase} and {beret.phrase} in a costume box, and {h.pronoun()} loved how both props made play feel magical.")
    world.say(f"{f.label} smiled too, because {f.pronoun()} wanted to join the pretend show and share the fun.")
    world.facts["hero"].meters["sparkle"] += 1
    world.facts["friend"].meters["sparkle"] += 1


def _conflict(world: World) -> None:
    h, f, p, mic, beret = world.facts["hero"], world.facts["friend"], world.facts["parent"], world.facts["mic"], world.facts["beret"]
    world.para()
    h.memes["wanting"] = 1.0
    f.memes["wanting"] = 1.0
    world.say(f"At first, {h.label} wanted to be the only star of the fantasy show, so {h.pronoun()} hugged the mic and the beret close.")
    world.say(f"Then {f.label} reached for the beret, because {f.pronoun()} wanted to be a castle knight in the play too.")
    h.memes["conflict"] = 1.0
    f.memes["conflict"] = 1.0
    world.say(f"{p.label.capitalize()} saw the frowns and reminded them that a kind game grows bigger when people share.")
    h.memes["sharing"] = 1.0
    f.memes["sharing"] = 1.0
    world.say(f"{h.label} listened, and {h.pronoun()} began to think about taking turns instead of keeping everything."


    )


def _resolution(world: World) -> None:
    h, f, p, mic, beret = world.facts["hero"], world.facts["friend"], world.facts["parent"], world.facts["mic"], world.facts["beret"]
    world.para()
    propagate(world, narrate=False)
    world.say(f"{h.label} passed the beret to {f.label}, and then they swapped the mic back and forth while making brave castle voices.")
    world.say(f"One friend sang while the other wore the beret, and then they traded, laughing when their voices echoed around the room.")
    world.say(f"By the end, the fantasy show had two stars, one shared mic, one shared beret, and a happy feeling that fit both children.")
    world.say(f"{p.label.capitalize()} clapped because the children had solved the problem with sharing, and the room felt warm and bright.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _begin(world)
    _conflict(world)
    _resolution(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    h, f = world.facts["hero"], world.facts["friend"]
    return [
        'Write a short heartwarming story about a child, a fantasy costume box, a toy mic, and a beret.',
        f"Tell a gentle story where {h.label} and {f.label} learn to share a mic and a beret during pretend castle play.",
        "Write a simple moral story with a happy ending about sharing fantasy props.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, p, mic, beret = world.facts["hero"], world.facts["friend"], world.facts["parent"], world.facts["mic"], world.facts["beret"]
    return [
        QAItem(
            question=f"What did {h.label} find in the costume box?",
            answer=f"{h.label} found {mic.phrase} and {beret.phrase} in the costume box, and both props made the game feel like fantasy play.",
        ),
        QAItem(
            question=f"Why did {h.label} and {f.label} start to feel upset?",
            answer=f"They both wanted to use the same fantasy props at the same time, so the mic and the beret caused a small conflict.",
        ),
        QAItem(
            question=f"How did they solve the problem in the end?",
            answer=f"They shared by taking turns with the mic and the beret, which let both of them join the pretend show happily.",
        ),
        QAItem(
            question=f"What did {p.label} notice about their choice?",
            answer=f"{p.label.capitalize()} noticed that sharing helped the children turn the argument into a kind and happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, or taking turns so everyone can enjoy it.",
        ),
        QAItem(
            question="What is a beret?",
            answer="A beret is a soft, round hat that can be part of a costume or outfit.",
        ),
        QAItem(
            question="What is a microphone used for?",
            answer="A microphone helps people make their voice louder so others can hear them better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for (n, *_rest) in world.fired})}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Mia", gender="girl", friend_name="Pip", friend_gender="boy", parent_role="mother")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
