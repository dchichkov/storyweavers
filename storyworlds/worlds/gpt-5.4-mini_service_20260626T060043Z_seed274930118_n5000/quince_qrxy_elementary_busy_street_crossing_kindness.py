#!/usr/bin/env python3
"""
A small storyworld about a busy street crossing where Kindness and Teamwork
help a child safely cross with a quince and a qrxy on the way to elementary
school.

The story grows from a tiny causal model:
- the street is busy
- the child wants to cross
- a helper notices danger and offers Kindness
- Teamwork makes the crossing safe
- the ending shows the child reaching elementary school calmly
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    crowded: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    child_type: str = "girl"
    helper_name: str = "Jun"
    helper_type: str = "boy"
    place: str = "busy street crossing"
    school: str = "elementary school"
    object_a: str = "quince"
    object_b: str = "qrxy"
    mood: str = "sleepy"


PLACES = {
    "busy street crossing": Place(
        name="the busy street crossing",
        crowded=True,
        affords={"cross"},
    )
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Aya", "Zoe"]
NAMES_BOY = ["Jun", "Eli", "Theo", "Milo", "Omar"]
MOODS = ["sleepy", "careful", "curious", "gentle"]


class CrossingRule:
    def apply(self, world: World) -> list[str]:
        return []


def _r_wait(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("rush", 0) >= THRESHOLD and world.facts.get("signal") == "wait":
        sig = ("wait",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["calm"] = child.memes.get("calm", 0) + 1
        out.append(f"{helper.id} asked {child.id} to wait for the cars to pass.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if world.facts.get("held_hand") and world.facts.get("looked_both_ways"):
        sig = ("teamwork",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["safe"] = child.memes.get("safe", 0) + 1
        helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
        out.append("Together, they crossed one careful step at a time.")
    return out


CAUSAL_RULES = [CrossingRule(),]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
        for fn in (_r_wait, _r_teamwork):
            s = fn(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simulate_crossing(world: World, child: Entity, helper: Entity) -> None:
    world.facts["signal"] = "wait"
    world.facts["held_hand"] = True
    world.facts["looked_both_ways"] = True
    propagate(world, narrate=True)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.name,
        memes={"rush": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        memes={"kindness": 0.0, "teamwork": 0.0},
    ))
    quince = world.add(Entity(
        id="quince",
        kind="thing",
        type="quince",
        label="quince",
        phrase="a ripe quince",
        owner=child.id,
    ))
    qrxy = world.add(Entity(
        id="qrxy",
        kind="thing",
        type="qrxy",
        label="qrxy",
        phrase="a tiny qrxy toy",
        owner=child.id,
    ))

    child.memes["rush"] += 1
    child.memes["trust"] += 1

    world.say(
        f"At the busy street crossing, {child.label} carried {quince.phrase} and "
        f"{qrxy.phrase} on the way to elementary school."
    )
    world.say(
        f"{child.label} felt {params.mood}, but {child.pronoun().capitalize()} still wanted to get across."
    )
    world.para()
    world.say(
        f"Then {helper.label} came beside {child.label} and showed kindness."
    )
    world.say(
        f"{helper.label} pointed at the cars, held out a hand, and said they could use teamwork."
    )
    simulate_crossing(world, child, helper)
    world.para()
    world.say(
        f"After that, {child.label} and {helper.label} crossed safely together."
    )
    world.say(
        f"{child.label} reached elementary school with the quince still tucked safely in {child.pronoun('possessive')} bag, "
        f"and the qrxy snug in {child.pronoun('possessive')} pocket."
    )

    world.facts.update(
        child=child,
        helper=helper,
        quince=quince,
        qrxy=qrxy,
        school=params.school,
        place=params.place,
        kindness=True,
        teamwork=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        'Write a bedtime story about kindness and teamwork at a busy street crossing.',
        f"Tell a gentle story where {child.label} wants to cross the street and "
        f"{helper.label} helps with kindness.",
        f"Write a simple story that includes the words quince, qrxy, and elementary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    quince = f["quince"]
    qrxy = f["qrxy"]
    return [
        QAItem(
            question=f"Who was trying to cross the street?",
            answer=f"{child.label} was trying to cross the busy street crossing.",
        ),
        QAItem(
            question=f"What did {child.label} carry?",
            answer=f"{child.label} carried {quince.phrase} and {qrxy.phrase}.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped with kindness and teamwork by waiting, holding a hand, and helping {child.label} look both ways.",
        ),
        QAItem(
            question=f"Where did {child.label} end up at the end?",
            answer=f"{child.label} ended up at elementary school safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something safely or well.",
        ),
        QAItem(
            question="What is a busy street crossing?",
            answer="A busy street crossing is a place where people wait and walk across a road while cars pass by.",
        ),
        QAItem(
            question="What is elementary school?",
            answer="Elementary school is a school for young children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label} ({e.type}) {' '.join(parts)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child story is valid if the crossing is busy and the helper provides
% kindness and teamwork so the child can cross safely.
kindness_ok(C,H) :- child(C), helper(H), kind(C,H).
teamwork_ok(C,H) :- child(C), helper(H), team(C,H).
safe_story(C,H) :- busy_crossing, kindness_ok(C,H), teamwork_ok(C,H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("busy_crossing"),
        asp.fact("child", "child"),
        asp.fact("helper", "helper"),
        asp.fact("kind", "child", "helper"),
        asp.fact("team", "child", "helper"),
        asp.fact("object", "quince"),
        asp.fact("object", "qrxy"),
        asp.fact("school", "elementary"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_ok() -> bool:
    import asp
    model = asp.one_model(asp_program("#show safe_story/2."))
    return bool(asp.atoms(model, "safe_story"))


def asp_verify() -> int:
    ok = asp_story_ok()
    if ok:
        print("OK: ASP twin accepts the kindness/teamwork crossing story.")
        return 0
    print("MISMATCH: ASP twin did not produce a safe_story/2 atom.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-story world: kindness and teamwork at a busy street crossing."
    )
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--school", default="elementary school")
    ap.add_argument("--mood", choices=MOODS)
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice(NAMES_BOY if helper_type == "boy" else NAMES_GIRL)
    mood = args.mood or rng.choice(MOODS)
    place = args.place or "busy street crossing"
    return StoryParams(
        seed=None,
        name=name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        place=place,
        school=args.school or "elementary school",
        object_a="quince",
        object_b="qrxy",
        mood=mood,
    )


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


CURATED = [
    StoryParams(name="Mina", child_type="girl", helper_name="Jun", helper_type="boy", mood="sleepy"),
    StoryParams(name="Owen", child_type="boy", helper_name="Lila", helper_type="girl", mood="curious"),
    StoryParams(name="Nora", child_type="girl", helper_name="Eli", helper_type="boy", mood="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/2."))
        print(sorted(set(asp.atoms(model, "safe_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
