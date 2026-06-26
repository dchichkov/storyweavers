#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hockey_jug_curious_repetition_moral_value_surprise.py
================================================================================================

A standalone story world for a fairy-tale hockey-and-jug tale with:
- curiosity
- repetition
- moral value
- surprise

Seed tale sketch:
---
A curious child wanted to play hockey on the frozen pond. The child had a
precious jug that sat near the ice house, and a kind guardian warned that the
stick and puck might crack it. The child tried again and again to hurry onto
the ice, but at last discovered a surprising reason for the warning: inside
the jug was warm broth for a tiny injured fox. The child chose care over haste,
helped carry the jug safely, and then shared the game only after the fox was
safe and smiling.

This file models that premise as a small simulation, then narrates a
story-driven beginning, turn, and resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["shaken", "safe", "cold", "risk", "care", "joy", "curiosity", "worry", "repetition", "surprise", "moral", "helpfulness"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the frozen pond"


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    guardian: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


def make_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian, label="the guardian"))
    jug = world.add(Entity(
        id="jug",
        type="jug",
        label="jug",
        phrase="a small blue jug with a cork stopper",
        owner=child.id,
        caretaker=guardian.id,
        region="hands",
    ))
    fox = world.add(Entity(id="fox", kind="character", type="fox", label="the fox"))
    puck = world.add(Entity(id="puck", type="puck", label="puck", phrase="a wooden puck"))
    stick = world.add(Entity(id="stick", type="stick", label="stick", phrase="a smooth hockey stick"))

    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    jug.meters["safe"] += 1

    world.facts.update(child=child, guardian=guardian, jug=jug, fox=fox, puck=puck, stick=stick)
    return world


def _do_hockey(world: World, actor: Entity, narrate: bool = True) -> None:
    actor.memes["repetition"] += 1
    actor.memes["joy"] += 1
    actor.meters["risk"] += 1
    jug = world.get("jug")
    if jug.worn_by is None:
        jug.meters["risk"] += 1
    if narrate:
        world.say("Again and again, the child chased the puck across the ice.")


def _warning(world: World) -> None:
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    jug = world.facts["jug"]
    child.memes["worry"] += 1
    guardian.memes["care"] += 1
    world.say(
        f'"Careful," {guardian.label} said. "If you swing that stick too wildly, '
        f"you may crack the {jug.label}.""
    )


def _surprise(world: World) -> None:
    fox = world.facts["fox"]
    jug = world.facts["jug"]
    fox.memes["surprise"] += 1
    jug.meters["safe"] += 1
    world.say(
        "Then came a surprising thing: the jug did not hold water at all. "
        "Inside it was warm broth for a tiny fox with a bandaged paw."
    )


def _resolution(world: World) -> None:
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    jug = world.facts["jug"]
    fox = world.facts["fox"]
    child.memes["moral"] += 1
    child.memes["helpfulness"] += 1
    child.memes["joy"] += 1
    jug.meters["safe"] += 1
    fox.meters["safe"] += 1
    world.say(
        f"The child slowed down, carried the {jug.label} with both hands, "
        f"and helped the guardian bring the broth to the fox."
    )
    world.say(
        "After that, the child played hockey more gently, so the game stayed fun, "
        "the jug stayed whole, and the little fox lapped its broth in peace."
    )


def tell_story(world: World) -> World:
    child = world.facts["child"]
    guardian = world.facts["guardian"]

    world.say(
        f"Once upon a time, {child.id} was a curious child who loved bright winter days."
    )
    world.say(
        f"{child.id} wanted to play hockey on {world.setting.place}, and the thought made "
        f"{child.pronoun('possessive')} feet dance."
    )
    world.say(
        f"Near the ice sat a {world.facts['jug'].phrase}, and {guardian.label} watched it with care."
    )

    world.para()
    _do_hockey(world, child)
    _warning(world)
    _do_hockey(world, child)
    world.say(
        f"Still the child tried again and again, because curiosity is a strong little spark."
    )

    world.para()
    _surprise(world)
    world.say(
        f"The child blinked, then nodded, because a kind heart listens when surprise tells the truth."
    )
    _resolution(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        'Write a fairy-tale story about hockey, a curious child, and a jug, with a surprising turn.',
        f'Write a gentle story where {child.id} wants hockey on ice but learns to be careful with a jug.',
        'Tell a short fairy tale that repeats a small action and ends with a moral lesson about kindness and care.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    jug = world.facts["jug"]
    fox = world.facts["fox"]
    return [
        QAItem(
            question=f"Who wanted to play hockey on the frozen pond?",
            answer=f"{child.id} wanted to play hockey on {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {guardian.label} warn {child.id} about the jug?",
            answer=f"{guardian.label.capitalize()} warned {child.id} because swinging a hockey stick too wildly could crack the {jug.label}.",
        ),
        QAItem(
            question="What was surprising about the jug?",
            answer="The jug did not hold water. It held warm broth for a tiny fox with a bandaged paw.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end?",
            answer=f"{child.id} carried the {jug.label} carefully, helped the guardian, and then played hockey more gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hockey?",
            answer="Hockey is a game where players use sticks to guide a puck and try to score goals.",
        ),
        QAItem(
            question="What is a jug?",
            answer="A jug is a container with a handle and a mouth for pouring drinks or broth.",
        ),
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more and asking questions or looking closely.",
        ),
        QAItem(
            question="What is moral value in a story?",
            answer="Moral value is the good lesson a story teaches, like being careful, kind, or helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


SETTINGS = {
    "frozen_pond": Setting(place="the frozen pond"),
}

OBJECTS = {
    "jug": ObjectCfg(label="jug", phrase="a small blue jug with a cork stopper", region="hands", fragile=True),
}

NAMES = ["Mira", "Finn", "Lila", "Noel", "Toby", "Iris"]
GENDERS = ["girl", "boy"]
GUARDIANS = ["mother", "father"]
CURATED = [
    StoryParams(place="frozen_pond", name="Mira", gender="girl", guardian="mother", object="jug"),
    StoryParams(place="frozen_pond", name="Finn", gender="boy", guardian="father", object="jug"),
]


ASP_RULES = r"""
% A story is valid when the child wants hockey, the jug is at risk, and a
% surprise turn reveals the jug is not merely a jug.
wants_hockey(C) :- child(C).
at_risk(J) :- jug(J).
surprising(J) :- jug(J).
valid_story(C, J) :- wants_hockey(C), at_risk(J), surprising(J).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "child"),
        asp.fact("jug", "jug"),
        asp.fact("hockey"),
        asp.fact("curious"),
        asp.fact("repetition"),
        asp.fact("moral_value"),
        asp.fact("surprise"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("That setting does not exist in this little world.")
    if params.object != "jug":
        raise StoryError("This story world only supports the jug as the treasured object.")
    if params.gender not in GENDERS:
        raise StoryError("Invalid child gender.")
    if params.guardian not in GUARDIANS:
        raise StoryError("Invalid guardian type.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "frozen_pond"
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    guardian = args.guardian or rng.choice(GUARDIANS)
    obj = args.object or "jug"
    params = StoryParams(place=place, name=name, gender=gender, guardian=guardian, object=obj)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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
    ap = argparse.ArgumentParser(description="Fairy-tale hockey/jug story world.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--object", choices=OBJECTS.keys())
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


def verify_asp() -> int:
    py = {("child", "jug")}
    cl = set(asp_valid())
    if cl == py:
        print("OK: ASP and Python gates match.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
