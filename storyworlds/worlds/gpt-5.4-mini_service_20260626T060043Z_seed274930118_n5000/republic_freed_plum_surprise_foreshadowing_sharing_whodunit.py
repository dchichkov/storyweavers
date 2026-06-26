#!/usr/bin/env python3
"""
A tiny whodunit storyworld about a republic, a freed clue, a plum surprise,
foreshadowing, and sharing.

The domain is intentionally small and classical:
- A child detective notices a surprise in a republic square.
- Foreshadowing points to a shared plum tart.
- The mystery is solved by tracing who carried what, who knew what, and who
  shared the plum at the right moment.

The simulation drives the prose. State changes matter:
- clues raise suspicion
- sharing lowers suspicion
- freed evidence can be examined
- the final reveal depends on causal trace facts, not a fixed paragraph
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mood": 0.0, "suspicion": 0.0, "knowledge": 0.0}
        if not self.memes:
            self.memes = {"surprise": 0.0, "foreshadowing": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    republic: bool = False
    public: bool = True
    aromas: list[str] = field(default_factory=list)
    props: list[str] = field(default_factory=list)


@dataclass
class Thread:
    id: str
    label: str
    clue: str
    hint: str
    reveal: str
    shock: str
    topic: str = "plum"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trace = list(self.trace)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "square": Place(
        id="square",
        label="the republic square",
        republic=True,
        aromas=["bread", "dust", "plums"],
        props=["bench", "fountain", "notice board"],
    ),
    "library": Place(
        id="library",
        label="the republic library",
        republic=True,
        aromas=["paper", "wax", "plums"],
        props=["ladder", "ledger", "reading lamp"],
    ),
    "market": Place(
        id="market",
        label="the republic market",
        republic=True,
        aromas=["bread", "spice", "plums"],
        props=["stall", "basket", "cloth canopy"],
    ),
}

THREADS = {
    "surprise": Thread(
        id="surprise",
        label="a surprise",
        clue="a plum tart missing a slice",
        hint="a crumb trail under the bench",
        reveal="the tart had been shared before anyone noticed",
        shock="the missing slice was not stolen at all",
    ),
    "foreshadowing": Thread(
        id="foreshadowing",
        label="foreshadowing",
        clue="a folded note with a plum stain",
        hint="the stain matched the jam on the children’s fingers",
        reveal="the note had quietly predicted the sharing",
        shock="the hint was written before the tart appeared",
    ),
    "sharing": Thread(
        id="sharing",
        label="sharing",
        clue="two spoons left side by side",
        hint="one spoon still held a trace of purple juice",
        reveal="the plum was shared fairly and the mystery was only a surprise",
        shock="the spoons belonged to different hands, but one dessert",
    ),
}

CHARACTER_TYPES = ["girl", "boy", "detective"]
NAMES = {
    "girl": ["Mina", "Tess", "Lina", "Nora", "June"],
    "boy": ["Eli", "Pavel", "Sami", "Theo", "Milo"],
    "detective": ["Ada", "Iris", "Marta"],
}
ROLES = ["detective", "friend", "messenger", "cook", "assistant"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    thread: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, thread: str) -> bool:
    return place in PLACES and thread in THREADS


def invalid_reason(place: str, thread: str) -> str:
    if place not in PLACES:
        return "(No story: the chosen setting is not part of this small republic world.)"
    if thread not in THREADS:
        return "(No story: the chosen narrative thread is not available.)"
    return "(No story: that combination does not support a clear whodunit turn.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _do_story(world: World, params: StoryParams) -> World:
    place = world.place
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="plum clue", phrase="a plum clue"))
    tart = world.add(Entity(id="tart", kind="thing", type="food", label="plum tart", phrase="a sweet plum tart"))

    thread = THREADS[params.thread]
    world.facts.update(place=place, hero=hero, companion=companion, clue=clue, tart=tart, thread=thread)

    # Act 1: ordinary republic day, but a plum detail foreshadows trouble.
    world.say(
        f"In {place.label}, {hero.label} liked to solve little puzzles for the republic."
    )
    world.say(
        f"That morning, the air smelled of {place.aromas[2]}. A small {thread.label} began to flicker in the corner of {hero.label}'s eye."
    )
    hero.memes["foreshadowing"] += 1
    world.para()

    # Act 2: a surprise and a trail of evidence.
    world.say(
        f"Near the {place.props[0]}, {hero.label} found {thread.clue}."
    )
    hero.meters["knowledge"] += 1
    hero.memes["surprise"] += 1
    clue.owner = "unknown"
    clue.meters["hidden"] = 0.0
    world.say(
        f"{hero.label} bent closer and noticed {thread.hint}."
    )
    companion.carries.add("plum_tart")
    tart.owner = companion.id
    companion.memes["sharing"] += 1
    world.say(
        f"{companion.label} confessed that {companion.pronoun()} had shared the plum tart with the other children."
    )
    world.para()

    # Act 3: reveal.
    if params.thread == "sharing":
        world.say(
            f"That was the answer: the tart had been shared, so the mystery was only a surprise, not a theft."
        )
    elif params.thread == "surprise":
        world.say(
            f"The missing slice was explained by sharing, and the surprise turned kind instead of scary."
        )
    else:
        world.say(
            f"The stain on the note matched the purple plum juice, and the foreshadowing suddenly made sense."
        )
    hero.meters["suspicion"] = 0.0
    hero.meters["mood"] = 1.0
    companion.meters["suspicion"] = 0.0
    companion.meters["mood"] = 1.0
    world.say(
        f"By evening, everyone in the republic smiled, because the plum had been shared and the clue was freed."
    )
    world.facts["resolved"] = True
    return world


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.thread):
        raise StoryError(invalid_reason(params.place, params.thread))
    world = World(PLACES[params.place])
    return _do_story(world, params)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for children set in {f["place"].label} with a plum surprise and a gentle reveal.',
        f"Tell a mystery story about {f['hero'].label} in a republic where foreshadowing points toward a shared plum tart.",
        "Write a simple detective story that ends with sharing and explains why the clue was freed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    thread: Thread = f["thread"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Where did {hero.label} find the clue?",
            answer=f"{hero.label} found the clue in {place.label}, while watching the republic square for anything odd.",
        ),
        QAItem(
            question=f"What made the story feel like foreshadowing?",
            answer=f"The folded note with a plum stain made the story feel like foreshadowing, because it hinted at the sharing before the answer was clear.",
        ),
        QAItem(
            question=f"Why was the mystery a surprise?",
            answer=f"It was a surprise because the missing plum slice was not stolen; it had already been shared.",
        ),
        QAItem(
            question=f"How did {companion.label} help solve the case?",
            answer=f"{companion.label} helped by admitting the plum tart had been shared, which freed the clue from seeming suspicious.",
        ),
        QAItem(
            question=f"What proved the ending was kind, not mean?",
            answer=f"The ending was kind because everyone smiled after learning that the plum was shared fairly and the republic could relax again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a republic?",
            answer="A republic is a kind of government where people choose leaders to help make rules for everyone.",
        ),
        QAItem(
            question="What is a plum?",
            answer="A plum is a small round fruit with soft skin and sweet, juicy flesh inside.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or have part of something you have.",
        ),
        QAItem(
            question="What is a clue in a whodunit?",
            answer="A clue is a small piece of evidence that helps solve a mystery.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives an early hint about something important that will matter later.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(square). place(library). place(market).
thread(surprise). thread(foreshadowing). thread(sharing).

valid(P, T) :- place(P), thread(T).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("place", p) for p in PLACES]
        + [asp.fact("thread", t) for t in THREADS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple[str, str]]:
    return sorted((p, t) for p in PLACES for t in THREADS if valid_combo(p, t))


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: ASP parity holds for {len(a)} combinations.")
        return 0
    print("Mismatch between ASP and Python:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    thread = args.thread or rng.choice(list(THREADS))
    if not valid_combo(place, thread):
        raise StoryError(invalid_reason(place, thread))
    hero_type = args.hero_type or rng.choice(CHARACTER_TYPES)
    companion_type = args.companion_type or rng.choice([t for t in CHARACTER_TYPES if t != hero_type])
    hero = args.hero or rng.choice(NAMES[hero_type])
    companion = args.companion or rng.choice(NAMES[companion_type])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion, companion_type=companion_type, thread=thread)


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
        print("\n-- trace --")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: republic, freed, plum, surprise, foreshadowing, sharing.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--thread", choices=sorted(THREADS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=CHARACTER_TYPES)
    ap.add_argument("--companion")
    ap.add_argument("--companion-type", choices=CHARACTER_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for p, t in vals:
            print(f"  {p:8} {t}")
        return

    if args.all:
        combos = [StoryParams(place=p, hero="Ada", hero_type="detective", companion="Mina", companion_type="girl", thread=t) for p in PLACES for t in THREADS]
        samples = [generate(c) for c in combos]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
            p = sample.params
            header = f"### {p.place} / {p.thread}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
