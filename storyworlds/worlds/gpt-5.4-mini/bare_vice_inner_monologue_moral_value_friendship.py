#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bare_vice_inner_monologue_moral_value_friendship.py
====================================================================================

A standalone bedtime-style storyworld about two friends, a lonely found tool, and
a small moral choice. The world model keeps typed entities with physical meters
and emotional memes, and the story is driven by state changes rather than a
frozen paragraph with swapped nouns.

Seed words: bare, vice
Features: Inner Monologue, Moral Value, Friendship
Style: Bedtime Story
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
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
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
    label: str
    bare: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class FoundItem:
    id: str
    label: str
    phrase: str
    hidden_place: str
    rightful_owner: str
    tool_kind: str = "vice"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
@dataclass
class StoryParams:
    place: str
    item: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["temptation"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            e.memes["worry"] += 1
            out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    while True:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if x)
        if not changed:
            break
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("worry", "social", _r_worry)]


def setup_story(world: World, a: Entity, b: Entity, place: Place, item: FoundItem) -> None:
    world.say(
        f"On a quiet evening, {a.id} and {b.id} went to {place.label}. "
        f"The little yard was bare and still, and the moon made the grass look silver."
    )
    world.say(
        f"Near a bare bench, they found {item.phrase}. It looked lonely, like it was waiting for someone to come back."
    )
    a.memes["joy"] += 1
    b.memes["joy"] += 1


def notice(world: World, a: Entity, b: Entity, item: FoundItem) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id} leaned closer. \"What if we keep it?\" {a.pronoun()} whispered. "
        f"In {a.pronoun('possessive')} head, a small thought said it would be easy to slip it into {a.pronoun('possessive')} pocket."
    )
    world.say(
        f"{b.id} looked at {item.label} and frowned. \"That belongs to someone,\" {b.pronoun()} said softly."
    )


def inner_monologue(world: World, a: Entity, b: Entity, item: FoundItem) -> bool:
    a.memes["temptation"] += 1
    world.say(
        f"{a.id} stared at the tool and listened to the tiny voice inside. "
        f"\"No one saw us,\" the voice said. \"It would be simple.\""
    )
    world.say(
        f"But another voice answered in {a.pronoun('possessive')} own heart: "
        f"\"If I take it, {b.id} will know I was not kind.\""
    )
    world.facts["tempted"] = True
    return True


def choose_good(world: World, a: Entity, b: Entity, item: FoundItem) -> None:
    a.memes["honesty"] += 1
    a.memes["love"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{a.id} took a breath. \"You're right,\" {a.pronoun()} said. "
        f"\"We should give it back.\""
    )
    world.say(
        f"{b.id} smiled, and the two friends carried {item.label} back together, carefully, as if it were a sleeping bird."
    )


def return_item(world: World, parent: Entity, a: Entity, b: Entity, item: FoundItem) -> None:
    world.say(
        f"At the cottage door, {parent.label_word} opened it with a warm smile. "
        f"\"Oh! There it is,\" {parent.pronoun()} said. \"Thank you for bringing it home.\""
    )
    world.say(
        f"The grown-up set {item.label} back on the workbench, and the little yard felt lighter somehow."
    )
    a.memes["relief"] += 1
    b.memes["relief"] += 1


def lesson(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"That night, {a.id} fell asleep with a quiet, happy feeling. "
        f"{b.id} fell asleep too, glad that friendship had helped the right choice win."
    )
    world.say(
        f"And in the dark, {a.id} remembered the small moral of the evening: it is better to be honest with a friend than to keep something that is not yours."
    )


def tell(place: Place, item: FoundItem, a: Entity, b: Entity, parent: Entity) -> World:
    w = World()
    w.add(a)
    w.add(b)
    w.add(parent)
    w.add(Entity(id=place.id, kind="place", type="place", label=place.label))
    w.add(Entity(id=item.id, kind="thing", type="thing", label=item.label, owner=item.rightful_owner))

    setup_story(w, a, b, place, item)
    w.para()
    notice(w, a, b, item)
    inner_monologue(w, a, b, item)
    choose_good(w, a, b, item)
    w.para()
    return_item(w, parent, a, b, item)
    lesson(w, a, b)

    w.facts.update(
        a=a, b=b, parent=parent, place=place, item=item,
        outcome="returned", moral="honesty", friendship="strengthened",
    )
    return w


PLACES = {
    "garden": Place("garden", "the garden", bare=True),
    "yard": Place("yard", "the yard", bare=True),
    "porch": Place("porch", "the porch", bare=True),
}

ITEMS = {
    "vice": FoundItem("vice", "vice", "a small steel vice", "bare bench", "the neighbor"),
    "toolbox": FoundItem("toolbox", "toolbox", "a dusty toolbox with a red handle", "bare shelf", "the neighbor"),
    "keyring": FoundItem("keyring", "keyring", "a brass keyring", "bare hook", "the neighbor"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Ben", "Theo", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, i) for p in PLACES for i in ITEMS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "bare" and "{f["item"].label}" and shows a friendship choice.',
        f"Tell a gentle story where {f['a'].id} and {f['b'].id} find {f['item'].phrase} and decide to do the honest thing together.",
        "Write a story with an inner monologue, a moral lesson, and a warm ending where friendship helps someone make a good choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, item, place = f["a"], f["b"], f["item"], f["place"]
    return [
        QAItem(
            question="What did the children find?",
            answer=f"They found {item.phrase} near a bare place, and it looked like something that belonged to someone else."
        ),
        QAItem(
            question="What did the first friend think about in their head?",
            answer=f"{a.id} thought about keeping it, but then heard an inner voice saying that taking it would not be kind."
        ),
        QAItem(
            question="How did the friends show their moral value?",
            answer=f"They chose honesty. Instead of hiding the {item.label}, they carried it back together and returned it."
        ),
        QAItem(
            question="How did friendship help in the story?",
            answer=f"{b.id}'s gentle reminder helped {a.id} pause and choose well, so the two friends stayed close and trusted each other more."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vice?",
            answer="A vice is a metal tool that holds something tightly so a person can work on it."
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty helps people trust each other. When you tell the truth and return things that are not yours, friendships stay strong."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, listen to each other, and try to help each other make good choices."
        ),
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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.owner:
            bits.append(f"owner={e.owner!r}")
        out.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P, I) :- place(P), item(I).
choice(I) :- item(I).
returned :- choice(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = False
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, child1=None, child1_gender=None, child2=None, child2_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about honesty, friendship, and an inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", dest="child1_gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", dest="child2_gender", choices=["girl", "boy"])
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
              if args.place in (None, c[0]) and args.item in (None, c[1])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    c1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    c2_gender = args.child2_gender or ("boy" if c1_gender == "girl" else "girl")
    c1 = args.child1 or rng.choice(GIRL_NAMES if c1_gender == "girl" else BOY_NAMES)
    c2 = args.child2 or rng.choice([n for n in (GIRL_NAMES if c2_gender == "girl" else BOY_NAMES) if n != c1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, item, c1, c1_gender, c2, c2_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], ITEMS[params.item],
        Entity(id=params.child1, kind="character", type=params.child1_gender, role="friend"),
        Entity(id=params.child2, kind="character", type=params.child2_gender, role="friend"),
        Entity(id="Parent", kind="character", type=params.parent, role="neighbor", label="the neighbor"),
    )
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
    StoryParams("yard", "vice", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("garden", "toolbox", "Ben", "boy", "Lily", "girl", "father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for p, i in asp_valid_combos():
            print(f"  {p:8} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
