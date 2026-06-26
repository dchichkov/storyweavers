#!/usr/bin/env python3
"""
storyworlds/worlds/quackeroo_scruff_sharing_fable.py
====================================================

A small fable-style story world about Quackeroo and Scruff learning to share.

Premise seed:
- Quackeroo is proud of a fresh pile of sweet plums.
- Scruff is nearby and also wants a taste.
- A fable turn: Quackeroo first clutches the treats, then discovers sharing makes
  the moment brighter for both.

The world is simulated with physical meters and emotional memes:
- meters track fruit count, hunger, and fullness
- memes track greed, worry, kindness, and joy

The story is generated from the changing state, not from a frozen paragraph.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"duck", "quackeroo"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"dog", "scruff"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    count: int = 1
    shareable: bool = True


@dataclass
class StoryParams:
    place: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c


def _py(v):
    return v


def _story_state_text(world: World) -> list[str]:
    out = []
    q = world.get("Quackeroo")
    s = world.get("Scruff")
    treasure = world.get("Treasure")
    if q.meters.get("treasure", 0) >= THRESHOLD:
        out.append(f"Quackeroo kept {treasure.label} close.")
    if q.memes.get("greed", 0) >= THRESHOLD:
        out.append("He felt greedy and a little stiff inside.")
    if s.memes.get("hope", 0) >= THRESHOLD:
        out.append("Scruff hoped there might be enough for both of them.")
    if q.memes.get("kindness", 0) >= THRESHOLD:
        out.append("Quackeroo's heart grew soft enough to share.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        q = world.get("Quackeroo")
        s = world.get("Scruff")
        treasure = world.get("Treasure")

        sig = ("want",)
        if q.meters.get("treasure", 0) >= THRESHOLD and sig not in world.fired:
            world.fired.add(sig)
            q.memes["greed"] = q.memes.get("greed", 0) + 1
            out.append(f"Quackeroo clutched the {treasure.label} a little tighter.")
            changed = True

        sig = ("hungry",)
        if s.meters.get("hunger", 0) >= THRESHOLD and sig not in world.fired:
            world.fired.add(sig)
            s.memes["hope"] = s.memes.get("hope", 0) + 1
            out.append("Scruff looked on with a hungry hope.")
            changed = True

        sig = ("share",)
        if q.memes.get("kindness", 0) >= THRESHOLD and treasure.meters.get("pieces", 0) >= 2 and sig not in world.fired:
            world.fired.add(sig)
            q.meters["pieces"] = q.meters.get("pieces", 0) - 1
            s.meters["pieces"] = s.meters.get("pieces", 0) + 1
            q.memes["joy"] = q.memes.get("joy", 0) + 1
            s.memes["joy"] = s.memes.get("joy", 0) + 1
            out.append(f"Quackeroo split the {treasure.label} and gave Scruff a piece.")
            changed = True

        sig = ("mend",)
        if q.meters.get("pieces", 0) <= 1 and s.meters.get("pieces", 0) >= 1 and sig not in world.fired:
            world.fired.add(sig)
            q.memes["greed"] = max(0.0, q.memes.get("greed", 0) - 1)
            q.memes["kindness"] = q.memes.get("kindness", 0) + 1
            q.memes["joy"] = q.memes.get("joy", 0) + 1
            s.memes["joy"] = s.memes.get("joy", 0) + 1
            out.append("The sharing made the air feel lighter.")
            changed = True

    if narrate:
        for line in out:
            world.say(line)
    return out


def predicate_reasonable(place: Place, treasure: Treasure) -> bool:
    return "sharing" in place.afford and treasure.shareable and treasure.count >= 2


def warn_prediction(world: World) -> str:
    q = world.get("Quackeroo")
    s = world.get("Scruff")
    if q.meters.get("treasure", 0) < THRESHOLD:
        return "No treasure to share."
    if s.meters.get("hunger", 0) >= THRESHOLD:
        return "If Quackeroo keeps everything, Scruff stays hungry."
    return "No warning needed."


def tell(place: Place, treasure: Treasure) -> World:
    if not predicate_reasonable(place, treasure):
        raise StoryError("This fable needs a shareable treasure and a place where sharing can happen.")

    world = World(place)
    q = world.add(Entity(
        id="Quackeroo", kind="character", type="quackeroo", label="Quackeroo",
        meters={"treasure": 0, "pieces": float(treasure.count)},
        memes={"greed": 0, "kindness": 0, "joy": 0},
    ))
    s = world.add(Entity(
        id="Scruff", kind="character", type="scruff", label="Scruff",
        meters={"hunger": 1, "pieces": 0},
        memes={"hope": 0, "joy": 0},
    ))
    t = world.add(Entity(
        id="Treasure", type="fruit", label=treasure.label, phrase=treasure.phrase,
        meters={"pieces": float(treasure.count)},
    ))

    world.say(f"In {place.name}, {q.label} found {t.phrase}.")
    world.say(f"{s.label} stood nearby, and the warm little place felt ready for a choice.")
    q.meters["treasure"] = 1
    world.say(f"{q.label} held the {t.label} and did not mean to let go.")

    world.para()
    world.say(f"{s.label} looked at {q.label} with a hopeful face.")
    world.say(warn_prediction(world))
    q.memes["greed"] = 1
    s.memes["hope"] = 1
    world.say(f"{q.label} wanted the whole prize for himself.")
    world.say(f"But {s.label} stayed patient, because even a small hope can wait.")

    world.para()
    q.memes["kindness"] = 1
    world.say(f"Then {q.label} remembered that a feast is sweeter when two friends eat together.")
    propagate(world, narrate=True)
    world.say(f"{q.label} and {s.label} ate side by side until the crumbs were gone.")
    world.say("And from that day on, Quackeroo learned that a shared treat feels bigger than a kept one.")

    world.facts.update(
        quackeroo=q,
        scruff=s,
        treasure=t,
        place=place,
        shared=(q.meters.get("pieces", 0) <= 1 and s.meters.get("pieces", 0) >= 1),
    )
    return world


PLACE_REGISTRY = {
    "meadow": Place(name="the meadow", mood="gentle", afford={"sharing"}),
    "lantern_lane": Place(name="Lantern Lane", mood="warm", afford={"sharing"}),
}

TREASURE_REGISTRY = {
    "plums": Treasure(id="plums", label="plums", phrase="a small pile of ripe plums", count=2, shareable=True),
    "berries": Treasure(id="berries", label="berries", phrase="a bowl of red berries", count=3, shareable=True),
}

CURATED = [
    StoryParams(place="meadow", treasure="plums"),
    StoryParams(place="lantern_lane", treasure="berries"),
]


@dataclass
class ReasonableGate:
    place: str
    treasure: str


ASP_RULES = r"""
% A story is reasonable when the place supports sharing and the treasure can be split.
shareable(T) :- treasure(T), pieces(T,N), N >= 2.
can_story(P,T) :- place(P), affords(P,sharing), shareable(T).
#show can_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.afford):
            lines.append(asp.fact("affords", pid, a))
    for tid, tr in TREASURE_REGISTRY.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("pieces", tid, tr.count))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for p in PLACE_REGISTRY:
        for t in TREASURE_REGISTRY:
            if predicate_reasonable(PLACE_REGISTRY[p], TREASURE_REGISTRY[t]):
                out.append((p, t))
    return out


def asp_verify() -> int:
    a = set(asp_reasonable_pairs())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} story pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(a - b))
    print(" only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about Quackeroo, Scruff, and sharing.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--treasure", choices=TREASURE_REGISTRY)
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
    pairs = valid_pairs()
    if args.place:
        pairs = [p for p in pairs if p[0] == args.place]
    if args.treasure:
        pairs = [p for p in pairs if p[1] == args.treasure]
    if not pairs:
        raise StoryError("No reasonable sharing fable matches the chosen options.")
    place, treasure = rng.choice(sorted(pairs))
    return StoryParams(place=place, treasure=treasure)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"].name
    t = world.facts["treasure"].label
    return [
        f"Write a short fable set in {p} about Quackeroo, Scruff, and sharing {t}.",
        f"Tell a child-friendly moral story where Quackeroo learns to share {t} with Scruff.",
        f"Write a small fable about two friends, one treat, and a kinder ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.get("Quackeroo")
    s = world.get("Scruff")
    t = world.get("Treasure")
    place = world.facts["place"].name
    return [
        QAItem(
            question=f"Who found the {t.label} in {place}?",
            answer=f"Quackeroo found the {t.phrase} in {place}.",
        ),
        QAItem(
            question="Why was Scruff waiting nearby?",
            answer="Scruff was hungry and hoped Quackeroo would share.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="Quackeroo stopped clutching the treasure and shared it, so both friends felt happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy part of what you have.",
        ),
        QAItem(
            question="Why can sharing make friends happy?",
            answer="Sharing can make friends happy because everyone gets a turn or a taste, and no one feels left out.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACE_REGISTRY[params.place], TREASURE_REGISTRY[params.treasure])
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
        print(asp_program("#show can_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_reasonable_pairs()
        print(f"{len(pairs)} reasonable sharing story pairs:\n")
        for place, treasure in pairs:
            print(f"  {place:12} {treasure}")
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
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            header = f"### {sample.params.place} / {sample.params.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
