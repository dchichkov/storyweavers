#!/usr/bin/env python3
"""
storyworlds/worlds/innuendo_arrival_cautionary_animal_story.py
===============================================================

A small animal-story world about arrival, caution, and a gentle innuendo:
one animal arrives somewhere new, notices a subtle warning, and chooses the
safer path.

The world is state-driven:
- animals have meters and memes,
- arrival changes who is present and what they notice,
- caution can prevent a small problem from becoming a bigger one,
- innuendo is modeled as a soft hint that may be missed at first.

The stories are short, child-facing, and complete: beginning, tension,
turn, resolution.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carrying: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "cat", "rabbit", "mouse", "squirrel", "bird", "hen", "duck"}
        male = {"dog", "bear", "wolf", "goat", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    kind: str
    welcomes: set[str] = field(default_factory=set)
    warns_about: set[str] = field(default_factory=set)
    description: str = ""


@dataclass
class Travel:
    id: str
    verb: str
    arrival_phrase: str
    risk: str
    consequence: str
    caution_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hint:
    id: str
    line: str
    meaning: str
    action: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    traveler: str
    travel: str
    companion: str
    hint: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the meadow",
        kind="outdoor",
        welcomes={"walk", "arrival"},
        warns_about={"burrow"},
        description="The meadow was bright and soft, with grass swaying like little waves.",
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        kind="outdoor",
        welcomes={"arrival", "walk"},
        warns_about={"slip"},
        description="The pond shimmered under the trees, and the bank looked damp.",
    ),
    "barnyard": Place(
        id="barnyard",
        label="the barnyard",
        kind="outdoor",
        welcomes={"arrival", "walk"},
        warns_about={"henhouse"},
        description="The barnyard was busy, with pebbles, straw, and many careful footprints.",
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        kind="outdoor",
        welcomes={"arrival", "walk"},
        warns_about={"nest"},
        description="The orchard smelled sweet, and apples shone between the leaves.",
    ),
}

TRAVELS = {
    "arrival": Travel(
        id="arrival",
        verb="arrive",
        arrival_phrase="came to the place",
        risk="miss a warning",
        consequence="wander into a tricky spot",
        caution_key="arrival",
        tags={"arrival", "caution"},
    ),
    "walk": Travel(
        id="walk",
        verb="walk",
        arrival_phrase="came walking along the path",
        risk="go too fast",
        consequence="bump into something small",
        caution_key="walk",
        tags={"arrival", "walk"},
    ),
    "peek": Travel(
        id="peek",
        verb="peek around",
        arrival_phrase="peeked around the corner",
        risk="startle a friend",
        consequence="scare the little animals",
        caution_key="peek",
        tags={"arrival", "peek"},
    ),
}

HINTS = {
    "innuendo": Hint(
        id="innuendo",
        line="The old owl gave a soft hint: “That path is for careful paws, not busy feet.”",
        meaning="a gentle warning that the path could be risky",
        action="choose the safer side path",
    ),
    "warning": Hint(
        id="warning",
        line="The hedgehog said, “I would slow down here if I were you.”",
        meaning="a clear sign that something ahead might be tricky",
        action="slow down and look first",
    ),
    "sign": Hint(
        id="sign",
        line="A little sign said, “Mind the roots.”",
        meaning="a message that the ground could trip you",
        action="step carefully",
    ),
}

ANIMALS = {
    "fox": {"type": "fox", "label": "a fox", "traits": ["curious", "quick", "bright"]},
    "rabbit": {"type": "rabbit", "label": "a rabbit", "traits": ["small", "gentle", "swift"]},
    "duck": {"type": "duck", "label": "a duck", "traits": ["cheery", "round", "waddly"]},
    "bear": {"type": "bear", "label": "a bear", "traits": ["big", "slow", "kind"]},
    "squirrel": {"type": "squirrel", "label": "a squirrel", "traits": ["busy", "light", "nimble"]},
    "cat": {"type": "cat", "label": "a cat", "traits": ["careful", "proud", "soft"]},
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for travel in TRAVELS.values():
            for hint in HINTS.values():
                if travel.id in place.welcomes and hint.id in {"innuendo", "warning", "sign"}:
                    combos.append((place.id, travel.id, hint.id))
    return combos


def choose_animal(rng: random.Random) -> tuple[str, dict]:
    return rng.choice(sorted(ANIMALS.items()))


def animal_entity(name: str, animal_type: str, label: str, traits: list[str]) -> Entity:
    return Entity(
        id=name,
        kind="character",
        type=animal_type,
        label=name,
        traits=traits,
        meters={"travel": 0.0, "alert": 0.0, "risk": 0.0, "safe": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "calm": 0.0, "pride": 0.0},
    )


def scout_arrival(world: World, traveler: Entity, travel: Travel) -> None:
    traveler.meters["travel"] += 1
    traveler.memes["curiosity"] += 1
    world.say(
        f"{traveler.name_word()} {travel.arrival_phrase} at {world.place.label}."
    )
    world.say(world.place.description)


def reveal_innuendo(world: World, companion: Entity, hint: Hint) -> None:
    companion.memes["calm"] += 1
    world.say(hint.line)


def notice_risk(world: World, traveler: Entity, travel: Travel, hint: Hint) -> None:
    traveler.meters["risk"] += 1
    traveler.memes["worry"] += 1
    world.say(
        f"{traveler.name_word()} paused, because the hint meant it would be easy to "
        f"{travel.risk} and {travel.consequence}."
    )


def choose_carefully(world: World, traveler: Entity, hint: Hint) -> None:
    traveler.meters["safe"] += 1
    traveler.memes["calm"] += 1
    traveler.memes["pride"] += 1
    world.say(
        f"So {traveler.name_word()} listened to the innuendo and chose to {hint.action}."
    )


def end_image(world: World, traveler: Entity, companion: Entity) -> None:
    world.say(
        f"In the end, {traveler.name_word()} was safe, and {companion.name_word()} "
        f"walked beside {traveler.pronoun('object')} with an easy smile."
    )


def tell(world: World, traveler: Entity, companion: Entity, travel: Travel, hint: Hint) -> World:
    world.say(
        f"One day, {traveler.name_word()} and {companion.name_word()} went toward {world.place.label}."
    )
    scout_arrival(world, traveler, travel)
    world.para()
    reveal_innuendo(world, companion, hint)
    notice_risk(world, traveler, travel, hint)
    world.say(
        f"{traveler.name_word()} almost rushed ahead, but {companion.name_word()} stayed close."
    )
    world.para()
    choose_carefully(world, traveler, hint)
    end_image(world, traveler, companion)
    traveler.memes["worry"] = 0.0
    world.facts.update(
        traveler=traveler,
        companion=companion,
        travel=travel,
        hint=hint,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t: Entity = f["traveler"]
    c: Entity = f["companion"]
    travel: Travel = f["travel"]
    hint: Hint = f["hint"]
    return [
        f'Write a short animal story with the word "innuendo" and an arrival at {world.place.label}.',
        f"Tell a cautionary story where {t.name_word()} arrives, hears a soft warning, and {c.name_word()} helps {t.pronoun('object')} stay safe.",
        f'Write a child-friendly story about an animal arrival, a subtle hint, and a careful choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t: Entity = f["traveler"]
    c: Entity = f["companion"]
    travel: Travel = f["travel"]
    hint: Hint = f["hint"]
    return [
        QAItem(
            question=f"Who arrived at {world.place.label} in the story?",
            answer=f"{t.name_word()} arrived at {world.place.label}, and {c.name_word()} came along too.",
        ),
        QAItem(
            question=f"What did the innuendo mean in the story?",
            answer=f"It was a soft hint that meant {hint.meaning}.",
        ),
        QAItem(
            question=f"What careful choice did {t.name_word()} make after hearing the hint?",
            answer=f"{t.name_word()} decided to {hint.action} instead of rushing ahead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an innuendo?",
            answer="An innuendo is a soft hint that suggests something without saying it very directly.",
        ),
        QAItem(
            question="What does arrival mean?",
            answer="Arrival means coming to a place and being there at last.",
        ),
        QAItem(
            question="Why should an animal slow down near a warning?",
            answer="Slowing down gives the animal time to notice danger and choose a safer path.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(meadow). place(pond). place(barnyard). place(orchard).
travel(arrival). travel(walk). travel(peek).
hint_innuendo(innuendo). hint_innuendo(warning). hint_innuendo(sign).

welcomes(meadow,arrival). welcomes(meadow,walk). welcomes(pond,arrival). welcomes(pond,walk).
welcomes(barnyard,arrival). welcomes(barnyard,walk). welcomes(orchard,arrival). welcomes(orchard,walk).

valid(P,T,H) :- place(P), travel(T), hint_innuendo(H), welcomes(P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TRAVELS:
        lines.append(asp.fact("travel", tid))
    for hid in HINTS:
        lines.append(asp.fact("hint_innuendo", hid))
    for p in PLACES.values():
        for t in p.welcomes:
            lines.append(asp.fact("welcomes", p.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary animal story world with arrival and innuendo.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--traveler", choices=ANIMALS)
    ap.add_argument("--travel", choices=TRAVELS)
    ap.add_argument("--companion", choices=ANIMALS)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--name")
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
    if args.place and args.travel and args.hint:
        if (args.place, args.travel, args.hint) not in combos:
            raise StoryError("(No valid combination matches the given options.)")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.travel is None or c[1] == args.travel)
        and (args.hint is None or c[2] == args.hint)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, travel, hint = rng.choice(sorted(filtered))
    traveler = args.traveler or rng.choice(sorted(ANIMALS))
    companion = args.companion or rng.choice([a for a in sorted(ANIMALS) if a != traveler])
    name = args.name or rng.choice(["Pip", "Milo", "Tansy", "Nell", "Bram", "Wren"])
    return StoryParams(place=place, traveler=traveler, travel=travel, companion=companion, hint=hint, name=name)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    travel = TRAVELS[params.travel]
    hint = HINTS[params.hint]
    world = World(place)
    traveler_info = ANIMALS[params.traveler]
    companion_info = ANIMALS[params.companion]
    traveler = world.add(Entity(
        id=params.name,
        kind="character",
        type=traveler_info["type"],
        label=params.name,
        traits=traveler_info["traits"],
        meters={"travel": 0.0, "alert": 0.0, "risk": 0.0, "safe": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "calm": 0.0, "pride": 0.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=companion_info["type"],
        label=companion_info["type"],
        traits=companion_info["traits"],
        meters={"travel": 0.0, "alert": 0.0, "risk": 0.0, "safe": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "calm": 0.0, "pride": 0.0},
    ))
    tell(world, traveler, companion, travel, hint)
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
    StoryParams(place="meadow", traveler="rabbit", travel="arrival", companion="fox", hint="innuendo", name="Pip"),
    StoryParams(place="pond", traveler="duck", travel="walk", companion="cat", hint="warning", name="Nell"),
    StoryParams(place="orchard", traveler="squirrel", travel="peek", companion="bear", hint="sign", name="Wren"),
]


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, travel, hint) combos:\n")
        for c in combos:
            print(" ", c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            p = sample.params
            header = f"### {p.name}: {p.traveler} at {p.place} (hint: {p.hint})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
