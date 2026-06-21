#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/impossible_kindness_sharing_animal_story.py
===========================================================================

A small animal storyworld about a kindness problem that feels impossible at first:
one cozy thing, two animal friends, and a gentle solution through sharing.

The world models:
- typed entities with physical meters and emotional memes
- a reasonableness gate that only allows plausible sharing problems
- a state-driven story with a clear turn and ending image
- three Q&A sets grounded in the simulated world
- an inline ASP twin for parity checks

The seed prompt inspired this miniature domain:
- Words: impossible
- Features: Kindness, Sharing
- Style: Animal Story
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
IMPOSSIBLE_FEAR = 2.0
KINDNESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "rabbit", "hen", "mouse", "cow", "duck"}
        male = {"bear", "fox", "dog", "wolf", "pig", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    shared_item: str
    mood: str = ""
    seed: Optional[int] = None


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    edible: bool = False
    shareable: bool = True
    tiny: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    weather: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


PLACES = {
    "meadow": Place("meadow", "the meadow", "a sunny meadow with soft grass", "sunny"),
    "riverbank": Place("riverbank", "the riverbank", "a quiet riverbank with smooth stones", "breezy"),
    "orchard": Place("orchard", "the orchard", "an orchard with a little picnic blanket", "warm"),
}

ANIMALS = {
    "bear": {"type": "bear", "label": "bear"},
    "fox": {"type": "fox", "label": "fox"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "duck": {"type": "duck", "label": "duck"},
    "mouse": {"type": "mouse", "label": "mouse"},
    "dog": {"type": "dog", "label": "dog"},
}

ITEMS = {
    "cookie": Item("cookie", "cookie", "one small cookie", edible=True, shareable=True, tiny=True, tags={"food"}),
    "berry_bowl": Item("berry_bowl", "berry bowl", "a little bowl of berries", edible=True, shareable=True, tiny=False, tags={"food"}),
    "blanket": Item("blanket", "blanket", "a soft blanket", shareable=True, tiny=False, tags={"comfort"}),
    "balloon": Item("balloon", "balloon", "a bright balloon", shareable=True, tiny=False, tags={"toy"}),
}

CURATED_ANIMALS = ["bear", "fox", "rabbit", "duck", "mouse", "dog"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in PLACES:
        for a1 in ANIMALS:
            for a2 in ANIMALS:
                if a1 == a2:
                    continue
                for item in ITEMS:
                    if ITEMS[item].shareable:
                        combos.append((setting, a1, a2, item))
    return combos


def explain_rejection(setting: Place, item: Item) -> str:
    return f"(No story: {item.label} is not a plausible sharing problem in {setting.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about kindness and sharing.")
    ap.add_argument("--setting", choices=PLACES)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--shared-item", choices=ITEMS)
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
    if args.shared_item and not ITEMS[args.shared_item].shareable:
        raise StoryError(explain_rejection(PLACES[args.setting] if args.setting else PLACES["meadow"], ITEMS[args.shared_item]))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.animal1:
        combos = [c for c in combos if c[1] == args.animal1]
    if args.animal2:
        combos = [c for c in combos if c[2] == args.animal2]
    if args.shared_item:
        combos = [c for c in combos if c[3] == args.shared_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, a1, a2, item = rng.choice(sorted(combos))
    mood = rng.choice(["hungry", "sleepy", "lonely", "hopeful"])
    return StoryParams(setting=setting, animal1=a1, animal2=a2, shared_item=item, mood=mood)


def _story_state(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.setting]
    i = ITEMS[params.shared_item]
    a1 = world.add(Entity(id="A1", kind="character", type=ANIMALS[params.animal1]["type"], label=params.animal1, role="first"))
    a2 = world.add(Entity(id="A2", kind="character", type=ANIMALS[params.animal2]["type"], label=params.animal2, role="second"))
    item = world.add(Entity(id="item", kind="thing", type=i.label, label=i.label))
    world.facts.update(place=place, item=i, a1=a1, a2=a2, mood=params.mood)

    a1.memes["want"] += 1
    a2.memes["want"] += 1
    a1.memes["kind"] += 1
    a2.memes["kind"] += 1
    item.meters["pieces"] += 1
    item.meters["enough_for_one"] += 1
    return world


def simulate(world: World) -> None:
    a1 = world.get("A1")
    a2 = world.get("A2")
    item = world.get("item")
    place = world.facts["place"]
    item_cfg = world.facts["item"]

    world.say(
        f"{a1.label_word.capitalize()} and {a2.label_word} were in {place.label}. "
        f"{place.scene} made the day feel calm."
    )
    world.say(
        f"On a blanket sat {item_cfg.phrase}. It looked delicious and very small, "
        f"and sharing it seemed almost impossible."
    )

    world.para()
    if item_cfg.edible:
        world.say(
            f"{a1.label_word.capitalize()} reached first and hugged the {item_cfg.label}. "
            f'"I want it," {a1.pronoun()} said.'
        )
    else:
        world.say(
            f"{a1.label_word.capitalize()} reached first and held the {item_cfg.label}. '
            f'"I want it," {a1.pronoun()} said.'
        )
    a1.memes["greedy"] += 1
    a2.memes["sad"] += 1

    world.say(
        f"{a2.label_word.capitalize()} looked down, then took a slow breath. "
        f'"We can share," {a2.pronoun()} said kindly.'
    )
    a2.memes["kind"] += 1
    a2.memes["hope"] += 1

    if item_cfg.tiny:
        world.say(
            f"There was only one little {item_cfg.label}. But kindness can make a small thing bigger."
        )
    else:
        world.say(
            f"The {item_cfg.label} was not huge, but it was enough for a gentle idea."
        )

    world.para()
    world.say(
        f"{a2.label_word.capitalize()} used a simple trick: first one bite, then the other, then back again. "
        f"They took turns and smiled at each turn."
    )
    item.meters["shared"] += 1
    a1.memes["happy"] += 1
    a2.memes["happy"] += 1
    a1.memes["kind"] += 1
    a2.memes["kind"] += 1

    world.say(
        f"At last, {a1.label_word} scooted the {item_cfg.label} into the middle. "
        f"Both animals ate or played with it together, and the impossible feeling disappeared."
    )
    world.say(
        f"Their last picture was simple: two friends side by side, sharing one small treasure."
    )

    world.facts["shared"] = True
    world.facts["ending"] = "shared"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a1, a2, item, place = f["a1"], f["a2"], f["item"], f["place"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the word "impossible" and shows kindness.',
        f"Tell a gentle story where {a1.label_word} and {a2.label_word} learn to share {item.phrase} in {place.label}.",
        f"Write a short animal story about sharing a tiny thing, where kindness helps make the problem feel possible.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a1, a2, item, place = f["a1"], f["a2"], f["item"], f["place"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a1.label_word} and {a2.label_word}, two animals who met in {place.label}. They had to solve a sharing problem together."
        ),
        QAItem(
            question=f"What made sharing {item.label} feel impossible at first?",
            answer=f"There was only one {item.label}, and both animals wanted it right away. That made the first moment tense, because one small thing had to be enough for two."
        ),
        QAItem(
            question="How did the animals solve the problem?",
            answer="They chose kindness and took turns. That let both of them enjoy the same thing without fighting."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about someone else. A kind animal tries to make things fair and peaceful."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting more than one person enjoy the same thing. Sometimes that means taking turns."
        ),
        QAItem(
            question=f"Why can a {item.label} be hard to share?",
            answer=f"A {item.label} is small, so it may not be enough for everyone at once. That is why turn-taking and kindness help."
        ),
        QAItem(
            question=f"What kind of place was {place.label}?",
            answer=f"{place.label.capitalize()} was a calm outdoor place with a gentle feel. It was a good spot for a small animal story."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A1,A2,I) :- setting(S), animal(A1), animal(A2), A1 != A2, item(I), shareable(I).
shared_story(S,A1,A2,I) :- valid(S,A1,A2,I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in PLACES:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("shareable", iid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python gates differ.")
        rc = 1
    try:
        sample = generate(StoryParams(setting="meadow", animal1="bear", animal2="fox", shared_item="cookie"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in PLACES:
        raise StoryError("Unknown setting.")
    if params.animal1 not in ANIMALS or params.animal2 not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.animal1 == params.animal2:
        raise StoryError("The two animals must be different.")
    if params.shared_item not in ITEMS:
        raise StoryError("Unknown shared item.")
    if not ITEMS[params.shared_item].shareable:
        raise StoryError("That item cannot be shared in this storyworld.")

    world = _story_state(params)
    simulate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="meadow", animal1="bear", animal2="rabbit", shared_item="cookie", mood="hungry"),
    StoryParams(setting="riverbank", animal1="fox", animal2="duck", shared_item="berry_bowl", mood="hopeful"),
    StoryParams(setting="orchard", animal1="mouse", animal2="dog", shared_item="blanket", mood="sleepy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in PLACES:
        raise StoryError("Unknown setting.")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.animal1:
        combos = [c for c in combos if c[1] == args.animal1]
    if args.animal2:
        combos = [c for c in combos if c[2] == args.animal2]
    if args.shared_item:
        combos = [c for c in combos if c[3] == args.shared_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, a1, a2, item = rng.choice(sorted(combos))
    mood = rng.choice(["hungry", "sleepy", "lonely", "hopeful"])
    return StoryParams(setting=setting, animal1=a1, animal2=a2, shared_item=item, mood=mood)


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
