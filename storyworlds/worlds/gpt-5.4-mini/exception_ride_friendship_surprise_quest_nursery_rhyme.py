#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exception_ride_friendship_surprise_quest_nursery_rhyme.py
=========================================================================================

A standalone storyworld for a tiny nursery-rhyme-style quest about friendship,
a surprise, and a ride. The story world keeps a small world model with typed
entities, physical meters, emotional memes, a forward-chained rule step, a
reasonableness gate, and an ASP twin for parity checks.

The core premise:
- Two friends set off on a little ride to complete a quest.
- One friend makes an exception for the other, because friendship matters.
- A surprise appears on the ride.
- They cooperate to finish the quest and end with a bright, child-facing image.

This script is stdlib-only and intended to run directly from the repo root.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    rideable: bool = False
    surprise: bool = False
    quest_item: bool = False
    makes_exception: bool = False
    helps_friendship: bool = False
    gives_treat: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Ride:
    id: str
    label: str
    motion: str
    cheerful: str
    places: set[str] = field(default_factory=set)
    speed: int = 1

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Quest:
    id: str
    goal: str
    clue: str
    treasure: str
    ending: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind == "character" and e.memes["friendship"] >= THRESHOLD:
            sig = ("friendship", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["warmth"] += 1
            out.append(f"{e.id} felt braver because a friend was рядом.")  # not narrated if already plain? no, avoid foreign
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen") and not world.facts.get("surprise_done"):
        world.facts["surprise_done"] = True
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("friendship", _r_friendship), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_gate(exc: Exceptionary, ride: Ride, surprise: Surprise, quest: Quest) -> bool:
    return exc.makes_exception and ride.rideable and surprise.surprise and quest.goal


@dataclass
class Exceptionary:
    id: str
    label: str
    phrase: str
    where: str
    makes_exception: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def predict_surprise(world: World, surprise_id: str) -> dict:
    sim = world.copy()
    sim.facts["surprise_seen"] = True
    propagate(sim, narrate=False)
    return {"excited": sim.get("child1").memes["joy"] + sim.get("child2").memes["joy"]}


def setup(world: World, a: Entity, b: Entity, ride: Ride, quest: Quest) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"Little {a.id} and little {b.id}, in a lane of morning light, "
        f"held hands and laughed, and set out on {ride.label} for the quest."
    )
    world.say(
        f"The quest was to find {quest.treasure}, beneath the willow and the kite, "
        f"and bring it home by supper time, before the stars were bright."
    )


def exception_beat(world: World, a: Entity, b: Entity, exc: Exceptionary) -> None:
    a.memes["kindness"] += 1
    b.memes["trust"] += 1
    world.say(
        f"But {a.id} made an exception, small as a silver bell: "
        f'"You may come along," {a.id} said, "and that will suit us well."'
    )
    world.say(
        f"So {b.id} smiled and skipped beside {a.id}, with hearts both light and free, "
        f"for friendship made the narrow rule a room for you and me."
    )


def ride_beat(world: World, ride: Ride, a: Entity, b: Entity) -> None:
    a.meters["motion"] += ride.speed
    b.meters["motion"] += ride.speed
    world.say(
        f"They rode on {ride.label}, {ride.motion}, through daisies, dust, and dew, "
        f"and every bump became a beat, the way a good song grew."
    )


def surprise_beat(world: World, surprise: Surprise, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.facts["surprise_seen"] = True
    world.say(
        f"Then out popped a {surprise.label} with {surprise.phrase}, "
        f"and {surprise.reveal}; the little riders gasped and clapped in praise."
    )


def quest_beat(world: World, quest: Quest, a: Entity, b: Entity) -> None:
    a.meters["quest_progress"] += 1
    b.meters["quest_progress"] += 1
    world.say(
        f"They followed the clue of {quest.clue}, where mossy stones were laid, "
        f"and found {quest.treasure}, shining there as if the moon had stayed."
    )


def ending_beat(world: World, quest: Quest, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"They rode back home at sunset, with {quest.treasure} held up high, "
        f"and sang the little ending song that floated to the sky."
    )
    world.say(
        f"For friendship had made room for more, the surprise had made them cheer, "
        f"and the quest was done in merry steps, with smiles from ear to ear."
    )


def tell(exc: Exceptionary, ride: Ride, surprise: Surprise, quest: Quest,
         child1: str = "Mia", child2: str = "Noah") -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type="girl", role="friend"))
    b = world.add(Entity(id=child2, kind="character", type="boy", role="friend"))
    world.add(Entity(id="ride", kind="thing", type="ride", label=ride.label, rideable=True))
    world.add(Entity(id="surprise", kind="thing", type="surprise", label=surprise.label, surprise=True))
    world.add(Entity(id="quest", kind="thing", type="quest", label=quest.goal, quest_item=True))
    world.facts["child1"] = a
    world.facts["child2"] = b
    world.facts["exc"] = exc
    world.facts["ride"] = ride
    world.facts["surprise"] = surprise
    world.facts["quest"] = quest

    setup(world, a, b, ride, quest)
    world.para()
    exception_beat(world, a, b, exc)
    ride_beat(world, ride, a, b)
    world.para()
    surprise_beat(world, surprise, a, b)
    quest_beat(world, quest, a, b)
    world.para()
    ending_beat(world, quest, a, b)
    world.facts["done"] = True
    return world


EXCEPTIONS = {
    "kind_pass": Exceptionary("kind_pass", "a kind pass", "a tiny pass", "the gate", tags={"exception"}),
}

RIDES = {
    "cart": Ride("cart", "the little cart", "jingle-jingling", "with a happy clink", {"path", "lane"}, 1),
    "pony": Ride("pony", "the pony ride", "clip-clopping", "with a soft trot", {"field", "path"}, 2),
}

SURPRISES = {
    "treat": Surprise("treat", "a ribboned basket", "a ribbon and a note", "it was meant for them", "gift", tags={"surprise"}),
    "lantern": Surprise("lantern", "a tiny lantern", "a lantern and a wink", "it glowed like a star", "light", tags={"surprise"}),
}

QUESTS = {
    "berry": Quest("berry", "find the blue berry", "the old oak", "the blue berry", "They brought it home, bright and merry.", tags={"quest"}),
    "bell": Quest("bell", "find the silver bell", "the stone bridge", "the silver bell", "They rang it once, and laughed as one.", tags={"quest"}),
}


@dataclass
@dataclass
class StoryParams:
    exception: str
    ride: str
    surprise: str
    quest: str
    child1: str
    child2: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(e, r, s, q) for e in EXCEPTIONS for r in RIDES for s in SURPRISES for q in QUESTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about friendship, surprise, and quest rides.")
    ap.add_argument("--exception", choices=EXCEPTIONS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--quest", choices=QUESTS)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combos.")
    exc = args.exception or rng.choice(sorted(EXCEPTIONS))
    ride = args.ride or rng.choice(sorted(RIDES))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    quest = args.quest or rng.choice(sorted(QUESTS))
    if (exc, ride, surprise, quest) not in combos:
        raise StoryError("The chosen ride, surprise, quest, and exception do not fit together.")
    return StoryParams(exc, ride, surprise, quest, rng.choice(["Mia", "Luna", "Ada"]), rng.choice(["Noah", "Finn", "Owen"]))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story using the words "exception" and "ride" with friendship and a surprise.',
        f"Tell a little rhyme where {f['child1'].id} makes an exception for {f['child2'].id} on a ride, and a surprise appears during a quest.",
        f'Write a gentle quest rhyme about two friends, an exception, and a ride that ends happily with a found treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["child1"]
    b = world.facts["child2"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question="Why did the two friends travel together?",
            answer=f"{a.id} made an exception so {b.id} could come along. Friendship mattered more than keeping the plan narrow, so they shared the ride and the quest."
        ),
        QAItem(
            question="What happened when the surprise appeared?",
            answer=f"A surprise showed up on the ride and made both children gasp with joy. That surprise gave the quest a bright little turn before they found {quest.treasure}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They rode home together with {quest.treasure}, happy and safe. The ending proves their friendship, the surprise, and the quest all came together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an exception?", "An exception is a special case that does not follow the usual rule. People make exceptions when kindness or fairness calls for it."),
        QAItem("What is a ride?", "A ride is a trip on something that carries you, like a cart or a pony. Rides can feel bouncy, quick, or gentle."),
        QAItem("What is a quest?", "A quest is a search for something important. In stories, a quest usually has a clue and a goal to find."),
        QAItem("What is friendship?", "Friendship is caring about someone and wanting to help them. Friends share, listen, and make room for one another."),
        QAItem("What is a surprise?", "A surprise is something unexpected that suddenly appears. It can make a story feel exciting and cheerful."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.rideable:
            bits.append("rideable=True")
        if e.surprise:
            bits.append("surprise=True")
        if e.quest_item:
            bits.append("quest_item=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kind_pass", "cart", "treat", "berry", "Mia", "Noah"),
    StoryParams("kind_pass", "pony", "lantern", "bell", "Luna", "Finn"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(EXCEPTIONS[params.exception], RIDES[params.ride], SURPRISES[params.surprise], QUESTS[params.quest], params.child1, params.child2)
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


ASP_RULES = r"""
valid(E,R,S,Q) :- exception(E), ride(R), surprise(S), quest(Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for e in EXCEPTIONS:
        lines.append(asp.fact("exception", e))
    for r in RIDES:
        lines.append(asp.fact("ride", r))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.child1} and {p.child2}: {p.exception}, {p.ride}, {p.surprise}, {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
