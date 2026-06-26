#!/usr/bin/env python3
"""
storyworlds/worlds/order_cortisone_representative_inner_monologue_quest_sound.py
===============================================================================

A standalone story world for a tiny space-adventure domain:

- A crew member has an itchy space rash.
- The ship needs to place an order for cortisone cream.
- A medical representative brings the order through the docking bay.
- The hero goes on a small quest to fetch it.
- Sound effects and inner monologue carry the story beats.

The story is generated from a simulated world model with physical meters
(itch, distance, package location, etc.) and emotional memes
(worry, relief, courage, pride).
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the Star Lantern"
    deck: str = "the docking deck"
    medbay: str = "the medbay"
    corridor: str = "the silver corridor"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    representative_name: str
    representative_type: str
    item_label: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy

        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.story = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _add_meter(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _add_meme(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def build_world(params: StoryParams) -> World:
    ship = Ship()
    world = World(ship)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            label=params.hero_name,
            location=ship.medbay,
            traits=["curious", "brave"],
        )
    )
    rep = world.add(
        Entity(
            id=params.representative_name,
            kind="character",
            type=params.representative_type,
            label=params.representative_name,
            location=ship.deck,
            traits=["calm", "helpful"],
        )
    )
    package = world.add(
        Entity(
            id="package",
            type="package",
            label="small parcel",
            phrase=f"a small parcel of {params.item_label}",
            location=ship.deck,
        )
    )
    med = world.add(
        Entity(
            id="cortisone",
            type="medicine",
            label="cortisone cream",
            phrase="a little tube of cortisone cream",
            location=ship.deck,
            owner=rep.id,
        )
    )

    world.facts.update(hero=hero, rep=rep, package=package, med=med, params=params)
    return world


def sound_effect(word: str) -> str:
    return {
        "itch": "itch-itch",
        "hatch": "psssht!",
        "step": "clink-clink",
        "pack": "tap-tap",
        "beep": "beep-beep",
        "lift": "whoosh",
        "seal": "fwip",
        "happy": "ding!",
    }.get(word, word)


def inner_monologue(hero: Entity, text: str) -> str:
    return f'({hero.pronoun("subject").capitalize()} thought, "{text}")'


def maybe_place_order(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    rep = world.get(world.facts["rep"].id)
    med = world.get("cortisone")
    _add_meme(hero, "worry", 1)
    world.say(
        f"{hero.id} rubbed {hero.pronoun('possessive')} arm and heard {sound_effect('itch')}."
    )
    world.say(
        inner_monologue(
            hero,
            f"I need to order the cortisone before this itch gets bigger.",
        )
    )
    world.say(
        f"{rep.id} checked the ship tablet and sent the order with {sound_effect('beep')}."
    )
    world.facts["order_placed"] = True
    med.location = world.ship.deck


def quest_to_deck(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    rep = world.get(world.facts["rep"].id)
    package = world.get("package")
    med = world.get("cortisone")

    world.para()
    world.say(
        f"At {world.ship.name}, the corridor lights glowed blue, and {hero.id} started a tiny quest to reach {world.ship.deck}."
    )
    _add_meme(hero, "courage", 1)
    _add_meter(hero, "distance", 1)
    world.say(
        inner_monologue(
            hero,
            "Stay steady. Follow the glowing arrows. The parcel is waiting.",
        )
    )
    world.say(f"{sound_effect('step')} went {hero.id}'s boots down the silver corridor.")

    package.location = world.ship.deck
    med.location = world.ship.deck
    world.say(
        f"On the deck, {rep.id} held up the parcel and said, 'Here comes the order.'"
    )
    world.say(f"The parcel made a soft {sound_effect('pack')} as it landed on the counter.")


def open_package(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    rep = world.get(world.facts["rep"].id)
    med = world.get("cortisone")

    world.para()
    world.say(
        f"{hero.id} took the parcel with careful hands. {sound_effect('seal')} went the wrapper."
    )
    med.carried_by = hero.id
    _add_meme(hero, "relief", 1)
    _add_meme(rep, "pride", 1)
    world.say(
        inner_monologue(
            hero,
            "The little tube is here. The itchy cloud can finally drift away.",
        )
    )
    world.say(
        f"{rep.id} smiled and said the cortisone would help the itchy spot settle down."
    )
    world.say(
        f"{hero.id} held {med.label} close like treasure from a moon mission."
    )
    world.facts["order_received"] = True
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    rep = world.get(params.representative_name)

    world.say(
        f"On {world.ship.name}, {hero.id} was a {params.hero_type} who loved space maps and quiet stars."
    )
    world.say(
        f"But one day {hero.id}'s arm felt itchy, and {sound_effect('itch')} followed {hero.id} everywhere."
    )
    world.say(
        f"{params.representative_name}, a {params.representative_type} and medical representative, knew just what to do."
    )

    maybe_place_order(world)
    quest_to_deck(world)
    open_package(world)

    world.para()
    world.say(
        f"By evening, the deck was calm again. The order had arrived, the cortisone was safe in {hero.id}'s hands, and the itchy trouble had grown small and quiet."
    )
    world.say(
        f"{hero.id} looked out at the stars and listened to the ship hum {sound_effect('happy')}."
    )
    return world


SETTINGS = {
    "ship": Ship(),
}

HEROES = [
    ("Milo", "boy"),
    ("Nina", "girl"),
    ("Tess", "girl"),
    ("Arlo", "boy"),
]

REPS = [
    ("Dr. Vega", "woman"),
    ("Agent Sol", "man"),
    ("Nurse Comet", "woman"),
    ("Mr. Orbit", "man"),
]

ITEMS = [
    "cortisone",
    "cortisone cream",
    "the little tube of cortisone",
]


@dataclass
class _Combo:
    hero_name: str
    hero_type: str
    representative_name: str
    representative_type: str
    item_label: str


def valid_combos() -> list[tuple[str, str, str]]:
    return [("ship", "hero", "cortisone")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure story world about an order for cortisone.")
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--rep-name")
    ap.add_argument("--rep-type", choices=["man", "woman"])
    ap.add_argument("--item", choices=["cortisone", "cortisone cream", "the little tube of cortisone"])
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
    hero_name, hero_type = (args.name, args.hero_type) if args.name and args.hero_type else rng.choice(HEROES)
    rep_name, rep_type = (args.rep_name, args.rep_type) if args.rep_name and args.rep_type else rng.choice(REPS)
    item_label = args.item or rng.choice(ITEMS)
    if args.item and "cortisone" not in args.item:
        raise StoryError("This world only supports cortisone as the medicine at the heart of the order.")
    return StoryParams(
        hero_name=hero_name or "Milo",
        hero_type=hero_type or "boy",
        representative_name=rep_name or "Dr. Vega",
        representative_type=rep_type or "woman",
        item_label=item_label,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    rep = world.facts["rep"]
    return [
        "Write a short space-adventure story about a child who needs to order cortisone.",
        f"Tell a gentle quest story where {hero.id} and {rep.id} work together to get {p.item_label}.",
        "Write a child-friendly story with inner monologue and sound effects on a starship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    rep = world.facts["rep"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to place the order?",
            answer=f"{hero.id} wanted to order cortisone because {hero.pronoun('possessive')} arm felt itchy and uncomfortable.",
        ),
        QAItem(
            question=f"What did the representative do to help?",
            answer=f"{rep.id} checked the tablet, sent the order, and brought the cortisone to the docking deck.",
        ),
        QAItem(
            question=f"What happened on the quest to the deck?",
            answer=f"{hero.id} walked through the glowing corridor, heard the ship go {sound_effect('step')}, and reached the parcel.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and proud, because the cortisone order had arrived safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an order?",
            answer="An order is a request for something you need, like medicine or food, to be sent to you.",
        ),
        QAItem(
            question="What is cortisone?",
            answer="Cortisone is medicine that can help calm itching and swelling.",
        ),
        QAItem(
            question="What is a representative?",
            answer="A representative is a person who works for a company and helps bring or explain what people need.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little words like beep, whoosh, or tap that help the reader imagine the noises.",
        ),
    ]


ASP_RULES = r"""
% World facts
hero(H). rep(R). medicine(M).
needs_order(H,M) :- itchy(H), medicine(M).
order_sent(R,M) :- rep(R), medicine(M), needs_order(_,M).
order_arrives(M) :- order_sent(_,M), docked_ship.

resolved(H,M) :- needs_order(H,M), order_arrives(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("docked_ship")]
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("rep", "rep"))
    lines.append(asp.fact("medicine", "cortisone"))
    lines.append(asp.fact("itchy", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/2."))
    resolved = set(asp.atoms(model, "resolved"))
    py = {("hero", "cortisone")}
    if resolved == py:
        print("OK: ASP gate matches Python story logic.")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("ASP:", sorted(resolved))
    print("PY :", sorted(py))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams("Milo", "boy", "Dr. Vega", "woman", "cortisone cream"),
    StoryParams("Nina", "girl", "Agent Sol", "man", "the little tube of cortisone"),
    StoryParams("Arlo", "boy", "Nurse Comet", "woman", "cortisone"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
