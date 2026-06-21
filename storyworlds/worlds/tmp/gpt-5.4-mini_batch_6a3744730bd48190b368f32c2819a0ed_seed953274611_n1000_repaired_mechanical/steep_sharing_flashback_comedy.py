#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/steep_sharing_flashback_comedy.py
==================================================================

A small comedy storyworld about two children, a steep path, a shared snack,
and a flashback that explains why they are so careful now.

Seed words/features/style:
- steep
- Sharing
- Flashback
- Comedy

The premise is simple: two kids climb a steep hill to reach a picnic spot.
One child brings something yummy, the other brings something useful, and a
funny flashback reveals why they learned to share the smart way. A helpful
adult or helper can nudge the ending, but the world stays small, concrete, and
state-driven.
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
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    steep: bool = False
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
class Treat:
    id: str
    label: str
    shareable: bool = True
    messy: bool = False
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
class Helper:
    id: str
    label: str
    use_text: str
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


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["climb"] < THRESHOLD:
            continue
        sig = ("tired", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        out.append(f"{e.id} got a little tired from the steep climb.")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    if not snack:
        return out
    a = world.entities.get("kid_a")
    b = world.entities.get("kid_b")
    if not a or not b:
        return out
    if a.memes["share"] < THRESHOLD or b.memes["share"] < THRESHOLD:
        return out
    sig = ("shared", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["shared"] += 1
    out.append("The snack got split into two happy halves.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("flashback_done"):
        return out
    a = world.entities.get("kid_a")
    b = world.entities.get("kid_b")
    if not a or not b:
        return out
    if a.memes["embarrassed"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["flashback_done"] = True
    out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("tired", _r_tired), Rule("shared", _r_shared), Rule("flashback", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(place: Place, treat: Treat, helper: Helper) -> bool:
    return place.steep and treat.shareable and "sharing" in helper.tags


def flashback_reason(world: World) -> str:
    return world.facts.get(
        "flashback_reason",
        "They remembered a much sillier day when they had both tried to carry the same jar and spilled the jam.",
    )


def tell(place: Place, treat: Treat, helper: Helper, child_a: str = "Mina", child_b: str = "Jo") -> World:
    world = World()
    a = world.add(Entity(id="kid_a", kind="character", type="girl", label=child_a, role="sharer"))
    b = world.add(Entity(id="kid_b", kind="character", type="boy", label=child_b, role="sharer"))
    snack = world.add(Entity(id="snack", type="thing", label=treat.label, tags=set(treat.tags)))
    hill = world.add(Entity(id="hill", type="place", label=place.label, tags=set(place.tags)))
    h = world.add(Entity(id="helper", kind="character", type="mother", label=helper.label, role="helper"))
    a.memes["share"] = 1
    b.memes["share"] = 1

    world.say(
        f"On a bright morning, {a.label} and {b.label} climbed {place.label}, which was so steep that even the squirrels looked impressed."
    )
    world.say(
        f"{a.label} carried {treat.label}, and {b.label} carried a little map with one arrow drawn too large for the paper."
    )
    world.say(
        f"They wanted to reach the top and share a picnic, but the hill kept making their feet do tiny squeaky protests."
    )

    world.para()
    a.meters["climb"] += 1
    b.meters["climb"] += 1
    if place.steep:
        a.memes["wobble"] += 1
        b.memes["wobble"] += 1
    world.say(
        f"Halfway up, {b.label} sniffed the air and said, 'I can smell {treat.label} being brave.'"
    )
    world.say(
        f"{a.label} laughed so hard that {treat.label} nearly did a roll in the wrapper."
    )

    world.para()
    a.memes["share"] += 1
    b.memes["share"] += 1
    world.say(
        f"{a.label} offered the first bite to {b.label}, and {b.label} offered the map because, honestly, {b.label} trusted the path less than the snack."
    )
    propagate(world)

    world.para()
    a.memes["embarrassed"] += 1
    world.say(
        f"That made {a.label} pause, and then {a.label} remembered something from before."
    )
    world.say(flashback_reason(world))
    world.say(
        f"In that old memory, they had tried to share without looking, and the juice box had squirted like a tiny comic volcano."
    )
    world.say(
        f"So this time, {a.label} held the snack steady, {b.label} held the wrapper open, and both of them tried not to giggle and fall over."
    )
    propagate(world)

    world.para()
    h.say if False else None
    world.say(
        f"At the top, {helper.label} was waiting with napkins and a proud smile, because somebody had clearly learned the art of not fighting a sandwich."
    )
    world.say(
        f"They shared {treat.label} into neat pieces, sat in the sunshine, and watched the steep hill look less scary now that they had conquered it together."
    )
    world.say(
        f"By the end, the snack was smaller, the hill was still steep, and both kids were grinning like they had invented sharing all by themselves."
    )

    world.facts.update(
        place=place,
        treat=treat,
        helper=helper,
        a=a,
        b=b,
        flashback=True,
        flashback_reason=flashback_reason(world),
        shared=True,
    )
    return world


PLACES = {
    "hill": Place(id="hill", label="the steep hill", steep=True, tags={"steep"}),
    "path": Place(id="path", label="the steep garden path", steep=True, tags={"steep"}),
    "steps": Place(id="steps", label="the steep front steps", steep=True, tags={"steep"}),
}

TREATS = {
    "cookies": Treat(id="cookies", label="two chocolate cookies", shareable=True, tags={"sharing"}),
    "apple": Treat(id="apple", label="one giant apple", shareable=True, tags={"sharing"}),
    "sandwich": Treat(id="sandwich", label="a picnic sandwich", shareable=True, tags={"sharing"}),
}

HELPERS = {
    "mom": Helper(id="mom", label="Mom", use_text="handed out napkins", tags={"sharing"}),
    "dad": Helper(id="dad", label="Dad", use_text="held the bag open", tags={"sharing"}),
    "grandma": Helper(id="grandma", label="Grandma", use_text="clapped once and laughed", tags={"sharing"}),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Jo", "Max", "Theo", "Sam", "Ben"]


@dataclass
class StoryParams:
    place: str
    treat: str
    helper: str
    child_a: str = "Mina"
    child_b: str = "Jo"
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


CURATED = [
    StoryParams(place="hill", treat="cookies", helper="mom", child_a="Mina", child_b="Jo"),
    StoryParams(place="path", treat="apple", helper="dad", child_a="Lily", child_b="Theo"),
    StoryParams(place="steps", treat="sandwich", helper="grandma", child_a="Ava", child_b="Sam"),
]


KNOWLEDGE = {
    "steep": [("What does steep mean?", "Steep means a hill or path goes up fast, so it can be hard to climb.")],
    "sharing": [("What is sharing?", "Sharing means letting someone else have some of what you have.")],
    "flashback": [("What is a flashback in a story?", "A flashback is when the story briefly remembers something that happened earlier.")],
    "cookie": [("Why are cookies easy to share?", "Cookies can be broken into pieces, so two people can each get some.")],
    "hill": [("Why do steep hills make kids slow down?", "Steep hills take more effort to climb, so people often need more careful steps.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TREATS:
            for h in HELPERS:
                if reasonable(PLACES[p], TREATS[t], HELPERS[h]):
                    combos.append((p, t, h))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child about {f["a"].label} and {f["b"].label} climbing a steep place and sharing {f["treat"].label}.',
        f'Tell a comedy story that includes the word "steep" and a flashback about learning to share better.',
        f"Write a short cheerful story where two kids, a snack, and a steep hill end with everyone laughing and sharing nicely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    return [
        ("Who are the story about?", f"The story is about {a.label} and {b.label}, two kids climbing a very steep hill together."),
        ("What did they bring?", f"They brought a picnic snack, and they also brought a map and a whole lot of bravery."),
        ("Why did the story flash back?", f"It flashed back because {a.label} got embarrassed and remembered an earlier time they made a sharing mess. That old memory helped them choose a smarter way to share this time."),
        ("How did it end?", f"It ended with the kids sharing the snack at the top of the hill and laughing with {f['helper'].label}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"steep", "sharing", "flashback"}
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
steep_place(P) :- place(P), steep(P).
shared_snack(T) :- treat(T), shareable(T).
flashback_needed :- embarrassed(kid_a).
valid(P, T, H) :- steep_place(P), shared_snack(T), helper(H).
outcome(comedy) :- valid(_,_,_), flashback_needed.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.steep:
            lines.append(asp.fact("steep", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import inspect
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
    if asp_outcome() != "comedy":
        print("MISMATCH in ASP outcome.")
        rc = 1
    print("OK: verify completed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a steep climb, sharing, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              and (args.treat is None or c[1] == args.treat)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat, helper = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        treat=treat,
        helper=helper,
        child_a=args.name_a or rng.choice(GIRL_NAMES),
        child_b=args.name_b or rng.choice(BOY_NAMES),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("treat", TREATS), ("helper", HELPERS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], TREATS[params.treat], HELPERS[params.helper], params.child_a, params.child_b)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
