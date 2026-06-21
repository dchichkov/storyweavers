#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mallard_lesson_learned_bad_ending_inner_monologue.py
====================================================================================

A tiny standalone storyworld about a mallard, a tempting snack, a warning, and a
bad ending with an inner monologue. The prose is built from a simulated world:
a duck sees a shiny chip, ignores a friend, gets into trouble, and learns too
late. The style aims for a child-friendly rhyming story with a clear beginning,
turn, and ending image.

The storyworld contract asks for:
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world-knowledge QA generated from world state
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n

This world is intentionally small and constrained. It only generates stories
when a mallard, a tempting snack, a cautioning friend, and a river-side mishap
fit together in a plausible way.
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

THRESHOLD = 1.0
WATERLOG_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.meters, dict):
            self.meters = dict(self.meters)
        if not isinstance(self.memes, dict):
            self.memes = dict(self.memes)

    def meter(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def meme(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    water: str
    reeds: str
    hazards: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    shiny: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Companion:
    id: str
    label: str
    phrase: str
    warning: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Outcome:
    id: str
    trouble: int
    finish_text: str
    lesson_text: str
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
class StoryParams:
    place: str = "pond"
    snack: str = "chip"
    companion: str = "goose"
    outcome: str = "mud"
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


PLACES = {
    "pond": Place("pond", "the pond", "cool water", "soft reeds", hazards={"water", "mud"}, tags={"pond", "water"}),
    "park": Place("park", "the park", "puddle water", "tall grass", hazards={"mud"}, tags={"park", "water"}),
    "bank": Place("bank", "the river bank", "fast water", "bent reeds", hazards={"water", "current"}, tags={"bank", "water"}),
}

SNACKS = {
    "chip": Snack("chip", "chip", "a shiny chip", "shiny as a star", risky=True, tags={"chip", "food"}),
    "crumb": Snack("crumb", "crumb", "a bright bread crumb", "glinting in the sun", risky=True, tags={"crumb", "food"}),
    "berry": Snack("berry", "berry", "a red berry", "red and round", risky=True, tags={"berry", "food"}),
}

COMPANIONS = {
    "goose": Companion("goose", "goose", "a goose friend", "Don't chase the shiny bite.", tags={"goose"}),
    "swan": Companion("swan", "swan", "a swan friend", "That snack may lead to a trap.", tags={"swan"}),
}

OUTCOMES = {
    "mud": Outcome("mud", trouble=1, finish_text="splashed into the mud with a clumsy plop", lesson_text="learned that shiny things can hide sticky trouble", tags={"mud"}),
    "barbed_wire": Outcome("barbed_wire", trouble=3, finish_text="got snagged near a fence and flustered his feathers", lesson_text="learned too late that not every shining thing is safe", tags={"fence", "trouble"}),
    "storm": Outcome("storm", trouble=2, finish_text="was pushed by a gust and soaked to the bone", lesson_text="learned that storms and snacks make a poor mix", tags={"storm"}),
}


def hazard_risky(place: Place, snack: Snack, outcome: Outcome) -> bool:
    return snack.risky and outcome.trouble >= 1 and (("water" in place.hazards) or ("current" in place.hazards) or ("mud" in place.hazards))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for s in SNACKS:
            for o in OUTCOMES:
                if hazard_risky(PLACES[p], SNACKS[s], OUTCOMES[o]):
                    out.append((p, s, o))
    return out


def _do_lure(world: World, duck: Entity, snack: Entity) -> None:
    duck.memes["want"] += 1
    world.say(
        f"The mallard saw {snack.label_word}, and his heart went clack; "
        f"he wanted it quick, though he should not go back."
    )
    world.say(
        f"Inside his small head, a whisper did race: "
        f'"It shines like a prize. I want that taste."'
    )


def _warn(world: World, friend: Entity, duck: Entity, companion: Companion) -> None:
    duck.memes["doubt"] += 1
    world.say(
        f"{friend.label_word.capitalize()} said, \"{companion.warning}\" "
        f"And the mallard heard, though the warning felt stern."
    )


def _do_ignore(world: World, duck: Entity, snack: Entity) -> None:
    duck.memes["defy"] += 1
    world.say(
        f"He shook his small head and waddled along, "
        f"murmuring softly, \"I'll show I am strong.\""
    )
    world.say(
        f"\"Just one little peck,\" his mind would insist, "
        f"\"Then I'll be okay, and the day will assist.\""
    )


def _do_trouble(world: World, duck: Entity, outcome: Outcome, place: Place) -> None:
    duck.meters["trouble"] += float(outcome.trouble)
    duck.meters["wet"] += 1.0
    duck.memes["fear"] += 1.0
    world.say(
        f"Then trouble came quick, as trouble can do: "
        f"he {outcome.finish_text}."
    )
    world.say(
        f"The reeds bent low, the water went splash, and his brave little boast "
        f"turned out to be rash."
    )


def _do_lesson(world: World, duck: Entity, snack: Entity, outcome: Outcome) -> None:
    duck.memes["lesson"] += 1.0
    world.say(
        f"His inner voice whispered, \"Oh, I should have seen: "
        f"{outcome.lesson_text}.\""
    )
    world.say(
        f"He blinked at the pond and the snack in the muck, "
        f"and wished he had listened when he still had good luck."
    )


def tell(place: Place, snack: Snack, companion: Companion, outcome: Outcome) -> World:
    world = World()
    duck = world.add(Entity(id="Mallard", kind="character", type="duck", label="mallard"))
    friend = world.add(Entity(id="Friend", kind="character", type="goose", label=companion.label))
    spot = world.add(Entity(id="Spot", kind="thing", type="place", label=place.label))
    bait = world.add(Entity(id="Snack", kind="thing", type="snack", label=snack.label_word))

    world.say(
        f"At {place.label}, where the water glowed and the reeds swayed light, "
        f"a mallard paddled happily, all feather and flight."
    )
    world.say(
        f"He spotted {snack.phrase}, so shiny and bright, "
        f"and thought, \"That sweet little sparkle would taste just right.\""
    )
    world.para()
    _do_lure(world, duck, bait)
    _warn(world, friend, duck, companion)
    _do_ignore(world, duck, bait)
    world.para()
    _do_trouble(world, duck, outcome, place)
    _do_lesson(world, duck, bait, outcome)
    world.say(
        f"So the mallard went home with wet feathers and care, "
        f"and a lesson that glimmered like light in the air."
    )

    world.facts.update(
        duck=duck,
        friend=friend,
        place=place,
        snack=snack,
        companion=companion,
        outcome=outcome,
        bait=bait,
        troubled=duck.meters["trouble"] >= THRESHOLD,
    )
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child about a mallard at {f["place"].label} who sees {f["snack"].phrase} and ignores a warning.',
        f'Tell a short rhyming tale where a mallard hears "{f["companion"].warning}" but still goes for {f["snack"].phrase}.',
        f'Write a sad but gentle duck story with an inner monologue and a clear lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    duck = f["duck"]
    friend = f["friend"]
    snack = f["snack"]
    outcome = f["outcome"]
    place = f["place"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer="It is about a mallard who is tempted by a shiny snack and a friend who tries to warn him.",
        ),
        QAItem(
            question="What did the mallard want?",
            answer=f"He wanted {snack.phrase}. The shiny snack looked exciting, so his inner monologue kept pulling him toward it.",
        ),
        QAItem(
            question="What did the friend say?",
            answer=f'The friend said, "{f["companion"].warning}" He was trying to stop the mallard before trouble began.',
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"He got into trouble at {place.label} and learned too late that shiny things can hide danger. The ending is sad because he did not listen soon enough.",
        ),
    ]
    if duck.meter("trouble") >= THRESHOLD:
        answers.append(
            QAItem(
                question="Why was the ending bad?",
                answer=f"The ending was bad because the mallard ignored the warning, and then {outcome.finish_text}. That left him wet, scared, and sorry.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a mallard?",
            answer="A mallard is a kind of duck. Mallards often swim in ponds and rivers, and they have webbed feet for paddling.",
        ),
        QAItem(
            question="Why should a duck be careful near water?",
            answer="Water can be calm, but it can also be slippery, deep, or fast. A duck still has to watch for trouble near the shore.",
        ),
        QAItem(
            question="Why can shiny food be risky for a duck?",
            answer="Shiny food can catch a duck's attention, but not every tempting thing is safe. A careful duck should listen to warnings before pecking at it.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned means someone understands a mistake and remembers a better choice next time. It helps the story end with wisdom, even if the ending was sad.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("\n== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,O) :- place(P), snack(S), outcome(O), risky(P,S,O).
risky(P,S,O) :- hazard(P,H), snack_risky(S), outcome_trouble(O,T), T >= 1, has_water_or_mud(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for h in sorted(p.hazards):
            lines.append(asp.fact("hazard", p.id, h))
    for s in SNACKS.values():
        lines.append(asp.fact("snack", s.id))
        if s.risky:
            lines.append(asp.fact("snack_risky", s.id))
    for o in OUTCOMES.values():
        lines.append(asp.fact("outcome", o.id))
        lines.append(asp.fact("outcome_trouble", o.id, o.trouble))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        rc = 1

    try:
        sample = generate(StoryParams())
        _ = sample.story
        print("OK: default generate() completed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: default generate() crashed: {exc}")
        return 1

    try:
        sample = generate(StoryParams())
        _ = sample.to_json()
        print("OK: serialization completed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: serialization crashed: {exc}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming mallard storyworld with a bad ending and a lesson learned.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--outcome", choices=sorted(OUTCOMES))
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
    place = args.place or rng.choice(list(PLACES))
    snack = args.snack or rng.choice(list(SNACKS))
    companion = args.companion or rng.choice(list(COMPANIONS))
    outcome = args.outcome or rng.choice(list(OUTCOMES))
    if place not in PLACES or snack not in SNACKS or companion not in COMPANIONS or outcome not in OUTCOMES:
        raise StoryError("Invalid story parameters.")
    if not hazard_risky(PLACES[place], SNACKS[snack], OUTCOMES[outcome]):
        raise StoryError("No real danger exists for that combination, so there is no story to tell.")
    return StoryParams(place=place, snack=snack, companion=companion, outcome=outcome)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.outcome not in OUTCOMES:
        raise StoryError(f"Unknown outcome: {params.outcome}")

    place = PLACES[params.place]
    snack = SNACKS[params.snack]
    companion = COMPANIONS[params.companion]
    outcome = OUTCOMES[params.outcome]
    if not hazard_risky(place, snack, outcome):
        raise StoryError("This combo does not produce a believable bad ending.")

    world = tell(place, snack, companion, outcome)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="pond", snack="chip", companion="goose", outcome="mud"),
    StoryParams(place="park", snack="crumb", companion="swan", outcome="storm"),
    StoryParams(place="bank", snack="berry", companion="goose", outcome="barbed_wire"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
                if sample.story in seen:
                    i += 1
                    continue
                seen.add(sample.story)
                samples.append(sample)
            except StoryError as err:
                print(err)
                return
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
