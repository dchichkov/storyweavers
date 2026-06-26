#!/usr/bin/env python3
"""
A small storyworld for an Animal Story with horn-driven suspense.

Premise:
A young animal hears a horn sound near a field or path and becomes worried.
The horn may mean danger, a lost parent, or a surprise helper. The animal
investigates, waits, and learns what the horn is really for.

This script models:
- typed entities with physical meters and emotional memes
- a short state-driven suspense arc
- a reasonableness gate for valid story combinations
- an inline ASP twin for parity checking
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "noise": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "relief": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "cow", "doe", "sow"}
        male = {"boy", "buck", "ram", "boar"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Habitat:
    place: str
    afforded_sounds: set[str] = field(default_factory=set)
    outdoor: bool = True


@dataclass
class Animal:
    id: str
    species: str
    sound: str
    phrase: str
    home: str
    friends: list[str] = field(default_factory=list)
    horn_sensitive: bool = False


@dataclass
class HornEvent:
    id: str
    source: str
    meaning: str
    loudness: str
    distance: int
    reassuring: bool


class World:
    def __init__(self, habitat: Habitat) -> None:
        self.habitat = habitat
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.horn_sound: str = ""
        self.horn_meaning_known: bool = False

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
        clone = World(self.habitat)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.horn_sound = self.horn_sound
        clone.horn_meaning_known = self.horn_meaning_known
        return clone


@dataclass
class StoryParams:
    place: str
    animal: str
    horn_event: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "field": Habitat(place="the field", afforded_sounds={"horn"}, outdoor=True),
    "forest": Habitat(place="the forest edge", afforded_sounds={"horn"}, outdoor=True),
    "farm": Habitat(place="the farm lane", afforded_sounds={"horn"}, outdoor=True),
    "hill": Habitat(place="the hill path", afforded_sounds={"horn"}, outdoor=True),
}

ANIMALS = {
    "goat": Animal(id="goat", species="goat", sound="bleat", phrase="a small goat", home="the barn", horn_sensitive=True),
    "fawn": Animal(id="fawn", species="fawn", sound="whimper", phrase="a young fawn", home="the woods", horn_sensitive=True),
    "rabbit": Animal(id="rabbit", species="rabbit", sound="thump", phrase="a little rabbit", home="a burrow", horn_sensitive=False),
    "calf": Animal(id="calf", species="calf", sound="moo", phrase="a curious calf", home="the pen", horn_sensitive=True),
}

HORN_EVENTS = {
    "farmer": HornEvent(id="farmer", source="a farmer", meaning="a call to come home", loudness="softly", distance=4, reassuring=True),
    "tram": HornEvent(id="tram", source="a passing tram", meaning="a warning to step aside", loudness="loudly", distance=2, reassuring=True),
    "storm": HornEvent(id="storm", source="a rescue cart", meaning="a signal that help is near", loudness="sharply", distance=3, reassuring=True),
    "lost_friend": HornEvent(id="lost_friend", source="a lost little friend", meaning="a call asking for help", loudness="faintly", distance=5, reassuring=False),
}

TRAITS = ["brave", "curious", "gentle", "careful", "nervous", "spry"]
FRIENDS = ["Mina", "Pip", "Toby", "June", "Sage", "Bram"]

GENDERLESS_NAMES = ["Benny", "Milo", "Momo", "Pippa", "Nori", "Lumi", "Clover"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for animal_id, animal in ANIMALS.items():
            for event_id, ev in HORN_EVENTS.items():
                if animal.horn_sensitive or ev.reassuring:
                    combos.append((place, animal_id, event_id))
    return combos


def explain_rejection(animal: Animal, event: HornEvent) -> str:
    return (
        f"(No story: {animal.species} does not naturally make a strong suspense beat "
        f"with a {event.source} unless the horn matters to the animal or the horn is "
        f"clearly reassuring. Try a horn-sensitive animal or a calmer horn event.)"
    )


def explain_randomness() -> str:
    return "(No story: the chosen options do not leave room for a clear horn suspense arc.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world with a horn of suspense."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--horn-event", choices=HORN_EVENTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.animal and args.horn_event:
        animal = ANIMALS[args.animal]
        ev = HORN_EVENTS[args.horn_event]
        if not (animal.horn_sensitive or ev.reassuring):
            raise StoryError(explain_rejection(animal, ev))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.animal is None or c[1] == args.animal)
        and (args.horn_event is None or c[2] == args.horn_event)
    ]
    if not combos:
        raise StoryError(explain_randomness())

    place, animal_id, horn_event = rng.choice(sorted(combos))
    name = args.name or rng.choice(GENDERLESS_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, animal=animal_id, horn_event=horn_event, name=name, friend=friend, trait=trait)


def _make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    animal = ANIMALS[params.animal]
    event = HORN_EVENTS[params.horn_event]

    hero = world.add(Entity(
        id=params.name, kind="character", type=animal.species,
        label=params.name, phrase=animal.phrase, traits=[params.trait, "small"],
    ))
    friend = world.add(Entity(
        id=params.friend, kind="character", type="rabbit", label=params.friend,
        phrase="a small friend", traits=["helpful"],
    ))
    horn = world.add(Entity(
        id="horn", kind="thing", type="horn", label="horn",
        phrase="a shining horn", owner=event.source,
    ))

    world.facts.update(hero=hero, friend=friend, horn=horn, event=event, animal=animal, params=params)
    return world


def _heard_horn(world: World, hero: Entity, event: HornEvent) -> None:
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.horn_sound = event.loudness
    world.say(f"{hero.id} was at {world.habitat.place} when a horn sounded {event.loudness}.")
    world.say(f"{hero.pronoun().capitalize()} froze and listened, because the sound came from {event.source}.")


def _suspense_step(world: World, hero: Entity, friend: Entity, event: HornEvent) -> None:
    hero.meters["distance"] += event.distance
    world.say(
        f"{hero.id} took one careful step at a time and looked toward the path, "
        f"wondering if {event.source} meant trouble."
    )
    if event.reassuring:
        hero.memes["hope"] += 1
        world.say(f"Then {friend.id} called from the edge of the grass, and that made the horn feel less scary.")
    else:
        hero.memes["worry"] += 1
        world.say(f"The horn stayed faint, so {hero.id} listened even harder and kept looking for a sign.")


def _resolve(world: World, hero: Entity, friend: Entity, event: HornEvent, animal: Animal) -> None:
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.horn_meaning_known = True
    world.say(
        f"At last, {hero.id} found out that the horn was {event.source}, and it meant {event.meaning}."
    )
    if event.reassuring:
        world.say(
            f"{friend.id} walked beside {hero.id}, and together they went where the horn had pointed."
        )
    else:
        world.say(
            f"{friend.id} helped {hero.id} answer the call, and the tiny search ended with both friends safe together."
        )
    world.say(
        f"By the end, {hero.id} was no longer worrying. {hero.id} stood in the quiet air, "
        f"and the horn was only a sound in the distance."
    )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    event = world.facts["event"]
    animal = world.facts["animal"]

    world.say(f"{hero.id} was {params.trait} and liked quiet places.")
    world.say(f"{hero.id} loved {animal.sound}ing to {friend.id} and exploring near {world.habitat.place}.")
    world.para()

    _heard_horn(world, hero, event)
    _suspense_step(world, hero, friend, event)
    world.para()
    _resolve(world, hero, friend, event, animal)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short Animal Story for a child about {p.name} the {f["animal"].species} hearing a horn at {PLACES[p.place].place}.',
        f"Tell a suspenseful story where {p.name} worries about a horn sound, watches carefully, and learns what it means.",
        f'Write a gentle story using the word "horn" where a small animal and a friend end safely together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    event: HornEvent = f["event"]
    animal: Animal = f["animal"]
    params: StoryParams = f["params"]
    place = PLACES[params.place].place

    return [
        QAItem(
            question=f"What made {hero.id} stop and listen at {place}?",
            answer=f"{hero.id} stopped because a horn sounded {event.loudness} and seemed important.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried at first?",
            answer=f"{hero.id} felt worried because the horn might have meant trouble before the meaning was clear.",
        ),
        QAItem(
            question=f"Who stayed with {hero.id} while the horn story was unfolding?",
            answer=f"{friend.id} stayed near {hero.id} and helped {hero.id} keep looking until the horn made sense.",
        ),
        QAItem(
            question=f"What did the horn really mean in the end?",
            answer=f"The horn meant {event.meaning}, and that turned the suspense into relief.",
        ),
        QAItem(
            question=f"What kind of animal was {hero.id}?",
            answer=f"{hero.id} was {animal.phrase}, a {animal.species} in this story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a horn?",
            answer="A horn is a hard thing on some animals, and it can also be a sound-making tool or signal.",
        ),
        QAItem(
            question="Why can a horn sound make a story suspenseful?",
            answer="A horn sound can make a story suspenseful because the character may not know what is coming yet.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  horn_sound={world.horn_sound!r} known={world.horn_meaning_known}")
    return "\n".join(lines)


ASP_RULES = r"""
place(field). place(forest). place(farm). place(hill).

animal(goat). animal(fawn). animal(rabbit). animal(calf).
horn_event(farmer). horn_event(tram). horn_event(storm). horn_event(lost_friend).

suspenseful(A,H) :- animal(A), horn_event(H), horn_sensitive(A).
suspenseful(A,H) :- animal(A), horn_event(H), reassuring(H).

valid(P,A,H) :- place(P), suspenseful(A,H).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a, animal in ANIMALS.items():
        lines.append(asp.fact("animal", a))
        if animal.horn_sensitive:
            lines.append(asp.fact("horn_sensitive", a))
    for h in HORN_EVENTS:
        lines.append(asp.fact("horn_event", h))
    for h, ev in HORN_EVENTS.items():
        if ev.reassuring:
            lines.append(asp.fact("reassuring", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="field", animal="goat", horn_event="farmer", name="Nia", friend="Pip", trait="curious"),
    StoryParams(place="forest", animal="fawn", horn_event="lost_friend", name="Lumi", friend="Mina", trait="nervous"),
    StoryParams(place="farm", animal="calf", horn_event="tram", name="Bram", friend="June", trait="careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.horn_event:
        animal = ANIMALS[args.animal]
        ev = HORN_EVENTS[args.horn_event]
        if not (animal.horn_sensitive or ev.reassuring):
            raise StoryError(explain_rejection(animal, ev))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.animal is None or c[1] == args.animal)
        and (args.horn_event is None or c[2] == args.horn_event)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal_id, horn_event = rng.choice(sorted(combos))
    name = args.name or rng.choice(GENDERLESS_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, animal=animal_id, horn_event=horn_event, name=name, friend=friend, trait=trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with horn suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--horn-event", choices=HORN_EVENTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, animal, horn_event) combos:\n")
        for t in triples:
            print("  ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
