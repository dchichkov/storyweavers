#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/warn_gerund_demographic_reconciliation_humor_fable.py
=====================================================================================

A small fable-style storyworld about a crowd of animals arguing over a warning
sign, a funny misunderstanding, and a reconciliation that ends with a shared
garden rule.

Seed words: warn-gerund, demographic
Features: Reconciliation, Humor
Style: Fable
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "hen", "goat", "hare"}
        male = {"wolf", "crow", "bear", "donkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Creature:
    id: str
    type: str
    label: str
    demographic: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    kind: str = "character"
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hen", "goat", "hare"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"wolf", "crow", "bear", "donkey"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    meadow: str
    warning: str
    intruder: str
    host: str
    crowd: str
    humor: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_mend(world: World) -> list[str]:
    out = []
    if world.get("field").meters["tension"] < THRESHOLD:
        return out
    sig = ("mend",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("field").meters["peace"] += 1
    for eid in ("host", "intruder"):
        world.get(eid).memes["softness"] += 1
        world.get(eid).memes["regret"] += 1
    out.append("__mend__")
    return out


CAUSAL_RULES = [("mend", _r_mend)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_fable(world: World, host: Creature, intruder: Creature, place: Place, warning: str, humor: str) -> None:
    world.say(
        f"In a green meadow, the {host.demographic} {host.label} kept a little path neat for the spring bees."
    )
    world.say(
        f"The {intruder.demographic} {intruder.label} came along, grinning at the sign that said, "
        f'"{warning}."'
    )
    world.say(
        f'"That sounds like a song," {intruder.id} said, and {intruder.pronoun()} started {humor}.'
    )


def worry(world: World, host: Creature, intruder: Creature, place: Place) -> None:
    intruder.memes["mischief"] += 1
    world.get("field").meters["tension"] += 1
    world.say(
        f"{host.id} blinked. " f'"Please do not ignore the sign," {host.pronoun()} said. '
        f'"It is there to warn the whole {host.demographic} of the meadow."'
    )


def joke(world: World, host: Creature, intruder: Creature) -> None:
    world.say(
        f"{intruder.id} looked embarrassed, then laughed. "
        f'"I thought the warning was about a squirrel choir," {intruder.id} said.'
    )
    world.say(
        f"{host.id} snorted, then laughed too, because even serious meadows can have silly mistakes."
    )


def reconcile(world: World, host: Creature, intruder: Creature) -> None:
    world.get("field").meters["tension"] = 0.0
    world.get("field").meters["peace"] += 1
    for eid in ("host", "intruder"):
        world.get(eid).memes["joy"] += 1
    world.say(
        f"After the laughing, {host.id} and {intruder.id} sat under the old oak and shared a berry tart."
    )
    world.say(
        f'{host.id} said, "You were not foolish on purpose. Next time, let us read the sign together."'
    )
    world.say(
        f'{intruder.id} nodded. "And next time I will ask before I warn-gerund around the meadow," '
        f'{intruder.id} said, making the bees seem less grumpy and a little more amused.'
    )
    world.say(
        "So the meadow kept its peace, and the animals learned that a true warning is kinder than a hurried guess."
    )


def tell(params: StoryParams) -> World:
    world = World()
    host = world.add(Creature(id="host", type="goat", label="goat", demographic=params.host))
    intruder = world.add(Creature(id="intruder", type="crow", label="crow", demographic=params.crowd))
    field = world.add(Place(id="field", label=params.meadow))
    world.facts.update(host=host, intruder=intruder, field=field, warning=params.warning, humor=params.humor)

    build_fable(world, host, intruder, field, params.warning, params.humor)
    world.para()
    worry(world, host, intruder, field)
    joke(world, host, intruder)
    propagate(world, narrate=True)
    world.para()
    reconcile(world, host, intruder)
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        ("sunny meadow", "Keep to the path", "fox", "crow"),
        ("apple field", "Stay off the sprouts", "goat", "crow"),
        ("clover hill", "Do not trample the clover", "hare", "wolf"),
    ]


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: this fable needs a warning that fits the meadow and a crowd that can misunderstand it.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about warning, humor, and reconciliation.")
    ap.add_argument("--meadow", choices={m for m, _, _, _ in valid_combos()})
    ap.add_argument("--warning")
    ap.add_argument("--intruder", choices=["fox", "crow", "hare", "wolf", "goat"])
    ap.add_argument("--host", choices=["fox", "crow", "hare", "wolf", "goat"])
    ap.add_argument("--crowd", choices=["fox", "crow", "hare", "wolf", "goat"])
    ap.add_argument("--humor")
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
    if args.meadow and args.warning is None:
        pass
    combos = valid_combos()
    if args.meadow:
        combos = [c for c in combos if c[0] == args.meadow]
    if not combos:
        raise StoryError(explain_rejection(args))
    meadow, warning, intruder, crowd = rng.choice(combos)
    host = args.host or "goat"
    humor = args.humor or "dancing in circles"
    if args.intruder:
        intruder = args.intruder
    if args.crowd:
        crowd = args.crowd
    if args.warning:
        warning = args.warning
    return StoryParams(meadow=meadow, warning=warning, intruder=intruder, host=host, crowd=crowd, humor=humor)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    prompts = [
        f'Write a short fable for children that includes the words "{params.warning}" and "warn-gerund".',
        f"Tell a humorous animal story where a {params.crowd} misunderstands a meadow warning and then reconciles with the {params.host}.",
        f"Write a gentle fable about a meadow, a warning, and two animals who end as friends again.",
    ]
    story_qa = [
        QAItem(
            question="What was the misunderstanding?",
            answer="The crow thought the warning was a joke about something fun, so it ignored the sign at first. That mistake made the host feel worried until the animals talked and laughed together."
        ),
        QAItem(
            question="How did the story end?",
            answer="The two animals reconciled by sitting down, sharing food, and agreeing to read the warning together next time. The meadow ended peaceful and calm."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a warning sign do?",
            answer="A warning sign helps creatures notice danger or important rules before they make a bad choice. It is meant to keep everyone safer."
        ),
        QAItem(
            question="Why can humor help in a disagreement?",
            answer="Humor can soften a tense moment and help two sides see that a mistake was not meant as cruelty. A shared laugh can make it easier to apologize and reconcile."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    return "\n".join(out)


ASP_RULES = r"""
mended :- tension(1), host(goat), intruder(crow).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("tension", 1),
        asp.fact("host", "goat"),
        asp.fact("intruder", "crow"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
    except Exception as exc:
        print(f"FAIL: normal generation crashed: {exc}")
        return 1
    print(sample.story[:60])
    return 0


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
    StoryParams(meadow="sunny meadow", warning="Keep to the path", intruder="crow", host="goat", crowd="crow", humor="dancing in circles"),
    StoryParams(meadow="apple field", warning="Stay off the sprouts", intruder="fox", host="goat", crowd="crow", humor="bowing too low"),
    StoryParams(meadow="clover hill", warning="Do not trample the clover", intruder="wolf", host="hare", crowd="fox", humor="pretending to sneeze"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show mended/0."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
