#!/usr/bin/env python3
"""
A small fairy-tale story world about spontaneous surprise, a brief flashback,
and a curious turn that ends in a gentle, complete resolution.

The world:
- A child or young creature wanders near a magical place.
- A surprise appears without planning.
- A flashback explains why the surprise matters.
- Curiosity leads to a safe action that resolves the moment.

The prose stays child-facing and state-driven.
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "knight", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    setting_line: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    noun: str
    verb: str
    surprise_noun: str
    curiosity_object: str
    flashback_line: str
    consequence: str
    tag: str


@dataclass
class StoryParams:
    place: str
    event: str
    hero_name: str
    hero_type: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


PLACES = {
    "grove": Place(
        id="grove",
        label="the moonlit grove",
        setting_line="The moonlit grove was quiet, and silver leaves whispered above the grass.",
        affords={"glow", "song", "riddle"},
    ),
    "castle": Place(
        id="castle",
        label="the old castle garden",
        setting_line="The old castle garden had roses, stone paths, and a round fountain in the middle.",
        affords={"glow", "song", "riddle"},
    ),
    "brook": Place(
        id="brook",
        label="the little brook",
        setting_line="The little brook chimed over smooth stones, like a tiny bell in the woods.",
        affords={"glow", "song", "riddle"},
    ),
}

EVENTS = {
    "glow": Event(
        id="glow",
        noun="a lantern",
        verb="follow the lantern's glow",
        surprise_noun="a lantern that lit itself",
        curiosity_object="the silver path",
        flashback_line="Years ago, the hero had once lost a kindness token in the same place.",
        consequence="the lantern led safely to the hidden token",
        tag="surprise",
    ),
    "song": Event(
        id="song",
        noun="a bird-song",
        verb="listen to the bird-song",
        surprise_noun="a bird singing from a branch that should have been empty",
        curiosity_object="the singing branch",
        flashback_line="The hero remembered a grandparent saying that songs can guide travelers home.",
        consequence="the song opened the way to a warm cottage door",
        tag="flashback",
    ),
    "riddle": Event(
        id="riddle",
        noun="a door",
        verb="solve the little door's riddle",
        surprise_noun="a tiny door in the roots of an oak",
        curiosity_object="the carved words",
        flashback_line="The hero remembered a bedtime tale about doors that open only for patient hearts.",
        consequence="the riddle unlocked a safe hiding place",
        tag="curiosity",
    ),
}

HERO_NAMES = ["Mila", "Toby", "Nia", "Pip", "Elin", "Oren", "Lina", "Bram"]
HERO_TYPES = ["girl", "boy"]
COMPANION_TYPES = ["fox", "rabbit", "bird", "cat"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place_id, event_id) for place_id, place in PLACES.items() for event_id in place.affords]


def explain_rejection(place_id: str, event_id: str) -> str:
    if event_id not in PLACES[place_id].affords:
        return "(No story: that place does not support this fairy-tale turn.)"
    return "(No story: the requested combination is not reasonable.)"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    event = EVENTS[params.event]
    world = World(place)
    world.facts["event"] = event

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        memes={"wonder": 0.0, "curiosity": 0.0, "joy": 0.0, "surprise": 0.0, "memory": 0.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=params.companion_type,
        label=f"the {params.companion_type}",
        memes={"calm": 1.0, "joy": 0.0},
    ))
    treasure = world.add(Entity(
        id="Treasure",
        type="token",
        label="kindness token",
        phrase="a small kindness token",
        owner=hero.id,
    ))
    world.facts.update(hero=hero, companion=companion, treasure=treasure)

    # Act 1: setting and desire.
    world.say(f"{hero.id} was a little {hero.type} who loved wandering near {place.label}.")
    world.say(f"{hero.pronoun().capitalize()} was especially curious about {event.curiosity_object}.")
    world.say(place.setting_line)

    # Act 2: spontaneous surprise and flashback.
    world.para()
    hero.memes["surprise"] += 1.0
    hero.memes["wonder"] += 1.0
    world.say(
        f"Then, quite spontaneously, {event.surprise_noun} appeared, and {hero.id} blinked in surprise."
    )
    world.say(f"{hero.id} wanted to {event.verb}, because {event.noun} felt important.")
    hero.memes["curiosity"] += 1.0
    world.say(event.flashback_line)
    hero.memes["memory"] += 1.0
    world.say(
        f"That old memory made {hero.id} pause and look more carefully instead of rushing ahead."
    )

    # Act 3: curious resolution.
    world.para()
    world.say(
        f"{hero.id} followed {hero.pronoun('possessive')} curiosity and touched {event.curiosity_object} with care."
    )
    hero.memes["joy"] += 1.0
    world.say(
        f"At once, {event.consequence}, and {hero.id} smiled with relief."
    )
    world.say(
        f"{companion.label} came close beside {hero.id}, and together they left the grove with the kindness token safe in hand."
    )
    world.say(
        f"By the end, the surprise had become a helpful gift, the flashback had given courage, and curiosity had led the way home."
    )

    world.facts["resolution"] = event.consequence
    return world


def generation_prompts(world: World) -> list[str]:
    event: Event = world.facts["event"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale for a young child about {hero.id}, a sudden surprise, and a gentle resolution.",
        f"Tell a story where a spontaneous {event.noun} appears, a memory comes back, and curiosity helps {hero.id} move forward.",
        f"Create a child-friendly fairy tale that includes surprise, flashback, and curiosity in a magical place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    event: Event = world.facts["event"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    place = world.place.label
    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} wandered near {place}, a quiet fairy-tale place with a magical feeling.",
        ),
        QAItem(
            question=f"What surprising thing appeared for {hero.id}?",
            answer=f"A spontaneous {event.surprise_noun} appeared, which startled {hero.id} and made the moment feel magical.",
        ),
        QAItem(
            question=f"What helped {hero.id} choose a safe way forward?",
            answer=f"A flashback and {hero.pronoun('possessive')} curiosity helped {hero.id} slow down, look carefully, and choose the safe path.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finding the hidden result of {event.consequence} and leaving happily with the companion.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you do not know it is coming.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory from earlier that comes back into the story for a moment.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    event: Event = world.facts["event"]  # type: ignore[assignment]
    out = list(WORLD_KNOWLEDGE.get(event.tag, []))
    if event.tag != "surprise":
        out.extend(WORLD_KNOWLEDGE["surprise"])
    if event.tag != "flashback":
        out.extend(WORLD_KNOWLEDGE["flashback"])
    if event.tag != "curiosity":
        out.extend(WORLD_KNOWLEDGE["curiosity"])
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", event="glow", hero_name="Mila", hero_type="girl", companion_type="fox"),
    StoryParams(place="castle", event="riddle", hero_name="Toby", hero_type="boy", companion_type="bird"),
    StoryParams(place="brook", event="song", hero_name="Nia", hero_type="girl", companion_type="rabbit"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for ev in sorted(place.affords):
            lines.append(asp.fact("affords", pid, ev))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("tag", eid, ev.tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Event) :- place(Place), event(Event), affords(Place, Event).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in asp:", sorted(asp_set - python_set))
    print("  only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world with surprise, flashback, and curiosity.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--companion-type", choices=COMPANION_TYPES)
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
    if args.place and args.event and (args.place, args.event) not in combos:
        raise StoryError(explain_rejection(args.place, args.event))
    combos = [
        (p, e) for (p, e) in combos
        if (args.place is None or p == args.place)
        and (args.event is None or e == args.event)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    companion_type = args.companion_type or rng.choice(COMPANION_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place,
        event=event,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_type=companion_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, event) combos:\n")
        for place, event in combos:
            print(f"  {place:10} {event}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.event} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
