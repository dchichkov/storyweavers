#!/usr/bin/env python3
"""
A small fable-style storyworld about a frantic stag, a remembered mistake,
and a calmer ending.

The domain is intentionally tiny: a stag wants to cross a stream for sweet
reeds, but a slippery bank and a falling branch trigger panic. A flashback to
an earlier lesson helps the stag slow down, listen, and choose a safer path.
The ending proves the change in state: the stag is no longer frantic, the
stream crossing is safe, and the moral lands cleanly.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "stag":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "stream"
    prize: str = "reeds"
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "stream": Place(id="stream", label="the stream", features={"water", "slippery_bank"}),
    "hill": Place(id="hill", label="the hill", features={"grass", "wind"}),
}

PRIZES = {
    "reeds": {
        "label": "reeds",
        "phrase": "sweet reeds",
        "plural": True,
        "location": "across the stream",
    },
    "apples": {
        "label": "apples",
        "phrase": "red apples",
        "plural": True,
        "location": "near the hill",
    },
}


# ---------------------------------------------------------------------------
# Fable logic
# ---------------------------------------------------------------------------

def _narrate_flashback(world: World) -> None:
    stag = world.get("stag")
    world.say(
        f"Flashback: once, when {stag.id} had rushed too fast, {stag.pronoun()} "
        f"slipped on wet stones and scared the little birds away."
    )
    world.say(
        f"Since then, {stag.id} had tried to remember that hurry could make a proud heart stumble."
    )


def _panic(world: World) -> None:
    stag = world.get("stag")
    if world.facts.get("panic_done"):
        return
    world.facts["panic_done"] = True
    stag.memes["frantic"] = 2.0
    stag.memes["worry"] = 1.0
    world.say(
        f"Then a branch cracked nearby, and {stag.id} became frantic."
    )
    world.say(
        f"{stag.id} stamped the ground, looking this way and that, as if the whole wood were chasing {stag.pronoun('object')}."
    )


def _remember(world: World) -> None:
    stag = world.get("stag")
    if world.facts.get("flashback_done"):
        return
    world.facts["flashback_done"] = True
    _narrate_flashback(world)
    stag.memes["remembering"] = 1.0
    world.say(
        f"The old memory returned just in time: {stag.id} knew that running while frantic only made the stones more slippery."
    )


def _calm_and_choose(world: World) -> None:
    stag = world.get("stag")
    if world.facts.get("calm_done"):
        return
    world.facts["calm_done"] = True
    stag.memes["frantic"] = 0.0
    stag.memes["courage"] = 1.0
    world.say(
        f"{stag.id} took a slow breath, lowered {stag.pronoun('possessive')} head, and walked carefully instead of rushing."
    )
    world.say(
        f"This time, {stag.id} crossed by the narrow stepping stones and reached the reeds without slipping."
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.prize not in PRIZES:
        raise StoryError(f"Unknown prize: {params.prize}")

    world = World(place=PLACES[params.place])

    stag = world.add(
        Entity(
            id="stag",
            kind="character",
            type="stag",
            label="the stag",
            phrase="a proud stag",
            meters={"distance": 0.0},
            memes={"frantic": 0.0, "worry": 0.0, "courage": 0.0, "remembering": 0.0},
        )
    )

    prize = world.add(
        Entity(
            id=params.prize,
            kind="thing",
            type=params.prize,
            label=PRIZES[params.prize]["label"],
            phrase=PRIZES[params.prize]["phrase"],
            plural=PRIZES[params.prize]["plural"],
        )
    )

    world.say(
        f"Once in {world.place.label}, there lived {stag.phrase} who loved quiet mornings."
    )
    world.say(
        f"{stag.id} wanted {prize.phrase} and thought the walk would be easy."
    )

    world.para()
    world.say(
        f"But the path led to {PRIZES[params.prize]['location']}, where the ground was not so kind."
    )
    _panic(world)
    _remember(world)

    world.para()
    _calm_and_choose(world)
    world.say(
        f"By the time the sun climbed higher, {stag.id} was no longer frantic; {stag.pronoun()} was thoughtful and safe."
    )
    world.say(
        f"And that is how the stag learned that a still heart crosses farther than a frantic one."
    )

    world.facts.update(stag=stag, prize=prize, place=world.place)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable for children about a frantic stag who remembers an old mistake.',
        'Tell a gentle story where a stag calms down after a flashback and chooses a safer path.',
        f'Write a simple fable set at {world.place.label} with a clear lesson about patience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    stag = world.facts["stag"]
    prize = world.facts["prize"]
    place = world.facts["place"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {stag.phrase}, a stag who visits {place.label}.",
        ),
        QAItem(
            question="What did the stag want?",
            answer=f"The stag wanted {prize.phrase}.",
        ),
        QAItem(
            question="Why did the stag feel frantic?",
            answer="The branch cracked nearby, and the old fear of slipping returned.",
        ),
        QAItem(
            question="What helped the stag calm down?",
            answer="A flashback to an earlier slip reminded the stag to slow down and be careful.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The stag crossed safely, was no longer frantic, and reached the prize without slipping.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a stag?",
        answer="A stag is an adult male deer with a strong body and, often, antlers.",
    ),
    QAItem(
        question="What does frantic mean?",
        answer="Frantic means very rushed, panicked, or hard to calm down.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is a short look back at something that happened earlier.",
    ),
    QAItem(
        question="Why do careful steps help on a slippery path?",
        answer="Careful steps help because slow feet are less likely to slip on wet or uneven ground.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(stream).
place(hill).

prize(reeds).
prize(apples).

frantic_after_noise(stag) :- branch_crack.
flashback_help(stag) :- frantic_after_noise(stag), remembers_mistake(stag).
safe_choice(stag) :- flashback_help(stag), slow_steps(stag).
resolved(stag) :- safe_choice(stag), reaches_prize(stag).

#show frantic_after_noise/1.
#show flashback_help/1.
#show safe_choice/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("branch_crack"), asp.fact("remembers_mistake", "stag"), asp.fact("reaches_prize", "stag")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show frantic_after_noise/1.\n#show flashback_help/1.\n#show safe_choice/1.\n#show resolved/1."))
    return sorted(set(
        [(sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model]
    ))


def python_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.prize in PRIZES


def asp_reasonable() -> bool:
    return sorted(asp_model()) == [
        ("flashback_help", ("stag",)),
        ("frantic_after_noise", ("stag",)),
        ("resolved", ("stag",)),
        ("safe_choice", ("stag",)),
    ]


def asp_verify() -> int:
    if not asp_reasonable():
        print("ASP mismatch")
        return 1
    params = StoryParams()
    sample = generate(params)
    if "Flashback:" not in sample.story or "frantic" not in sample.story:
        print("Verification story check failed")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld: a frantic stag and a flashback.")
    ap.add_argument("--place", choices=sorted(PLACES), default="stream")
    ap.add_argument("--prize", choices=sorted(PRIZES), default="reeds")
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
    return StoryParams(place=args.place or "stream", prize=args.prize or "reeds", seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    story = world.render()
    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  place={world.place.label}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
    StoryParams(place="stream", prize="reeds"),
    StoryParams(place="hill", prize="apples"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show frantic_after_noise/1.\n#show flashback_help/1.\n#show safe_choice/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
