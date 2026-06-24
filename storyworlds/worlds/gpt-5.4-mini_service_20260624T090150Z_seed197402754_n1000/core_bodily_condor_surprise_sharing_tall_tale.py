#!/usr/bin/env python3
"""
storyworlds/worlds/core_bodily_condor_surprise_sharing_tall_tale.py
===================================================================

A tiny tall-tale storyworld about a condor, a surprise, and a sharing-based
turn toward kindness.

The seed words for this world are:
- core
- bodily
- condor

The story premise is a classic tall tale: a very large condor guards a strong
core, a surprise arrives, and the solution is sharing. Physical state (meters)
and emotional state (memes) both drive the narration.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    sky: str
    affordance: str


@dataclass
class Treasure:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Offer:
    id: str
    label: str
    action: str
    benefit: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    treasure: str
    offer: str
    seed: Optional[int] = None


PLACES = {
    "canyon": Place(name="the canyon", sky="wide blue sky", affordance="soar"),
    "mesa": Place(name="the mesa", sky="golden sky", affordance="glide"),
    "mountain": Place(name="the mountain", sky="icy sky", affordance="circle"),
}

HEROES = {
    "condor": Entity(id="Condor", kind="character", type="condor", label="Condor"),
}

TREASURES = {
    "core": Treasure(label="core", phrase="a shiny apple core", region="beak", plural=False),
    "bodily": Treasure(label="bodily bundle", phrase="a bodily bundle of berries", region="talons", plural=False),
    "surprise": Treasure(label="surprise bag", phrase="a surprise bag of seeds", region="talons", plural=False),
}

OFFERS = {
    "sharing": Offer(id="sharing", label="sharing", action="share", benefit="everyone gets a bite"),
}


ASP_RULES = r"""
hero(condor).
place(canyon). place(mesa). place(mountain).
treasure(core). treasure(bodily). treasure(surprise).
offer(sharing).

at_risk(T) :- treasure(T), T = core.
at_risk(T) :- treasure(T), T = bodily.
at_risk(T) :- treasure(T), T = surprise.

fix(T, sharing) :- at_risk(T), offer(sharing).
valid_story(P, T, sharing) :- place(P), treasure(T), fix(T, sharing).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for o in OFFERS:
        lines.append(asp.fact("offer", o))
    lines.append(asp.fact("hero", "condor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def aspiration_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    print("  only in ASP:", sorted(clingo_set - python_set))
    print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, "sharing") for p in PLACES for t in TREASURES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale condor storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--offer", choices=OFFERS)
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
    if args.offer and args.offer != "sharing":
        raise StoryError("This world only resolves through sharing.")
    if args.treasure and args.offer and args.offer != "sharing":
        raise StoryError("The chosen offer cannot solve the surprise.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if args.offer:
        combos = [c for c in combos if c[2] == args.offer]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, treasure, offer = rng.choice(sorted(combos))
    return StoryParams(place=place, hero="condor", treasure=treasure, offer=offer)


def predict_surprise(world: World, hero: Entity, treasure: Entity) -> bool:
    return treasure.meters.get("held_close", 0.0) < THRESHOLD


def tell_story(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="Condor", kind="character", type="condor", label="Condor"))
    treasure = world.add(Entity(
        id=params.treasure,
        kind="thing",
        type=params.treasure,
        label=TREASURES[params.treasure].label,
        phrase=TREASURES[params.treasure].phrase,
        plural=TREASURES[params.treasure].plural,
        owner=hero.id,
    ))
    offer = OFFERS[params.offer]
    world.facts.update(hero=hero, treasure=treasure, offer=offer, place=world.place)

    hero.meters["wing_span"] = 9.0
    hero.memes["pride"] = 1.0

    world.say(
        f"High above {world.place.name}, a giant condor named Condor rode the {world.place.sky} "
        f"like a kite with a brave heartbeat."
    )
    world.say(
        f"Condor guarded {treasure.phrase} in {hero.pronoun('possessive')} talons, because that core "
        f"felt like the bright middle of the whole day."
    )

    world.para()
    hero.memes["curiosity"] = 1.0
    treasure.meters["held_close"] = 1.0
    world.say(
        f"Then, with a trumpet of feathers, a surprise floated down from a crack in the clouds: "
        f"a little basket with crumbs, berries, and a note that said, 'Share.'"
    )
    world.say(
        f"Condor stared so hard that even the dust on the mesa seemed to hold still."
    )

    world.para()
    if predict_surprise(world, hero, treasure):
        hero.memes["worry"] = 1.0
        world.say(
            f"At first Condor feared the surprise would spoil the treasure, so {hero.pronoun()} flapped "
            f"{hero.pronoun('possessive')} huge wings and cried, 'Mine, mine, mine!'"
        )
        world.say(
            f"But the basket did not vanish. It waited patiently, as if it had all the time in the sky."
        )
        hero.memes["greed"] = 0.0
        hero.memes["kindness"] = 1.0
        hero.meters["shared"] = 1.0
        world.say(
            f"Then Condor understood the note. {hero.pronoun().capitalize()} split the surprise into halves, "
            f"shared the berries with the little canyon birds, and kept the core for the long flight home."
        )
        world.say(
            f"The birds cheered, the sky seemed taller, and even the old rock walls looked pleased."
        )
        world.say(
            f"By sunset, Condor was soaring lighter than a ribbon, and the core was safe because it had been shared wisely."
        )
    else:
        world.say("The surprise was gentle, and nothing needed changing.")

    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story about a condor, a surprise, and sharing.',
        f"Tell a child-friendly story set at {world.place.name} where a condor discovers a surprise and learns to share.",
        "Write a simple story that uses the words core, bodily, and condor, and ends with a kind shared ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Condor, a giant condor who lives a tall-tale sort of life in the sky.",
        ),
        QAItem(
            question=f"What did Condor guard in the story?",
            answer=f"Condor guarded {treasure.phrase}, which the story treats as the important core of the day.",
        ),
        QAItem(
            question="What did Condor do when the surprise arrived?",
            answer="Condor first worried, then shared the surprise with the little birds, which made the ending happy.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with Condor soaring lighter, the birds cheered, and the treasure kept safe through sharing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condor?",
            answer="A condor is a very large bird that can glide high in the sky on broad wings.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else so more than one creature can enjoy it.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you were not ready for it.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="canyon", hero="condor", treasure="core", offer="sharing"),
    StoryParams(place="mesa", hero="condor", treasure="surprise", offer="sharing"),
    StoryParams(place="mountain", hero="condor", treasure="bodily", offer="sharing"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


def build_story_facts() -> str:
    return asp_facts()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
