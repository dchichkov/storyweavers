#!/usr/bin/env python3
"""
A small pirate-tale story world with curiosity, magic, and a surrogate helper.

Seed premise:
- A young pirate feels curious.
- A magical object can help or confuse the quest.
- A surrogate captain or helper steps in when the real captain cannot.

The world models:
- physical meters: thirst, tiredness, magic_glow, ship_damage, treasure, splash
- emotional memes: curiosity, joy, worry, trust, wonder, pride

The story shape:
- setup: aboard ship / on an island / near a cove
- tension: curiosity tempts the crew toward magic
- turn: the surrogate helper finds a safer way to enjoy the magic
- resolution: the crew enjoys the treasure without losing the ship

Required seed words are included in the prose and registries:
- surrogate
- stimulate
- enjoy
- Curiosity
- Magic
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they" if self.plural else "it",
                "object": "them" if self.plural else "it",
                "possessive": "their" if self.plural else "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    places: set[str]
    feature: str
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def story_word(word: str) -> str:
    return word


PLACES = {
    "ship": Place("the ship", afford={"glow", "drum"}),
    "cove": Place("the cove", afford={"glow", "drum", "tide"}),
    "island": Place("the island", afford={"glow", "drum", "tide"}),
}

ACTIONS = {
    "glow": Activity(
        id="glow",
        verb="peek at the magic light",
        gerund="peeking at the magic light",
        rush="rush toward the glowing chest",
        mess="dazzled",
        soil="too dazzled to steer",
        places={"ship", "cove", "island"},
        feature="Magic",
        keyword="magic",
    ),
    "drum": Activity(
        id="drum",
        verb="beat the pirate drum",
        gerund="beating the pirate drum",
        rush="dash to the drum",
        mess="bouncy",
        soil="too loud to listen",
        places={"ship", "cove"},
        feature="Curiosity",
        keyword="curiosity",
    ),
    "tide": Activity(
        id="tide",
        verb="follow the moon tide",
        gerund="following the moon tide",
        rush="run after the shining water",
        mess="wet",
        soil="soaked and slippery",
        places={"cove", "island"},
        feature="Curiosity",
        keyword="curiosity",
    ),
}

PRIZES = {
    "map": Prize("map", "treasure map", "a creased treasure map", "hands"),
    "lantern": Prize("lantern", "lantern", "a brass lantern", "hands"),
    "hat": Prize("hat", "captain hat", "a red captain hat", "head"),
}

GEAR = {
    "patch": Gear("patch", "an eye patch", {"dazzled"}, {"eyes"}, "put on an eye patch first", "put on the eye patch"),
    "cloak": Gear("cloak", "a dark cloak", {"wet"}, {"body"}, "wrap up in a dark cloak", "wrapped up in the cloak"),
    "gloves": Gear("gloves", "pirate gloves", {"dazzled", "wet"}, {"hands"}, "pull on pirate gloves", "pulled on the gloves"),
}

NAMES = ["Mira", "Jax", "Nina", "Tobin", "Rae", "Kellan", "Pip", "Luna"]
PARENTS = ["captain", "mate"]
TRAITS = ["curious", "brave", "cheerful", "bold", "spry"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(place: str, activity: str, prize: str) -> bool:
    act = ACTIONS[activity]
    pri = PRIZES[prize]
    return place in act.places and not (activity == "drum" and prize == "hat" and place == "ship")


ASP_RULES = r"""
place(ship). place(cove). place(island).
activity(glow). activity(drum). activity(tide).
prize(map). prize(lantern). prize(hat).

affords(ship, glow). affords(ship, drum).
affords(cove, glow). affords(cove, drum). affords(cove, tide).
affords(island, glow). affords(island, tide).

feature(glow, magic). feature(drum, curiosity). feature(tide, curiosity).

worn_on(map, hands). worn_on(lantern, hands). worn_on(hat, head).

guards(patch, dazzled). covers(patch, eyes).
guards(cloak, wet). covers(cloak, body).
guards(gloves, dazzled). guards(gloves, wet). covers(gloves, hands).

valid(P, A, R) :- affords(P, A), place(P), activity(A), prize(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("feature", aid, a.feature.lower()))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("worn_on", rid, r.region))
    for g in GEAR.values():
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    for pname, p in PLACES.items():
        for a in sorted(p.afford):
            lines.append(asp.fact("affords", pname, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a, r) for p in PLACES for a in ACTIONS for r in PRIZES if reasonableness_gate(p, a, r)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with curiosity and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = [(p, a, r) for p in PLACES for a in ACTIONS for r in PRIZES if reasonableness_gate(p, a, r)]
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate tale matches those choices.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent, trait=trait)


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    if activity.id == "glow":
        hero.meters["magic_glow"] = hero.meters.get("magic_glow", 0) + 1
        hero.meters["dazzled"] = hero.meters.get("dazzled", 0) + 1
    elif activity.id == "drum":
        hero.meters["noise"] = hero.meters.get("noise", 0) + 1
    elif activity.id == "tide":
        hero.meters["wet"] = hero.meters.get("wet", 0) + 1


def _risk_item(activity: Activity, prize: Prize) -> bool:
    return (activity.id == "glow" and prize.id in {"lantern", "hat"}) or (activity.id == "tide" and prize.id in {"hat", "map"})


def tell(place: Place, activity: Activity, prize: Prize, name: str, parent: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="child"))
    elder = world.add(Entity(id="surrogate", kind="character", type="captain", label="the surrogate captain"))
    treasure = world.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=elder.id))
    world.say(f"{name} was a {trait} little pirate who could not stop the Curiosity in {hero.pronoun('possessive')} chest.")
    world.say(f"On the ship, {hero.id} loved the salty wind, and {hero.pronoun()} wanted to enjoy every strange thing with a grin.")
    world.say(f"One bright day, a whisper of Magic came from the deck, and the crew wanted to stimulate the lantern until it shone like a star.")
    world.para()
    world.say(f"{name} and {hero.pronoun('possessive')} {parent} went to {place.name}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the magic and the waves made the deck feel wobbly.")
    _do_activity(world, hero, activity)
    if _risk_item(activity, prize):
        world.say(f"{hero.pronoun('possessive').capitalize()} {treasure.label} looked at risk, because {activity.soil} would be a bad thing for a pirate prize.")
    world.para()
    world.say(f"Then the surrogate captain stepped in.")
    gear = None
    if activity.id == "glow":
        gear = GEAR["patch"]
    elif activity.id == "tide":
        gear = GEAR["cloak"]
    else:
        gear = GEAR["gloves"]
    world.say(f"{hero.pronoun('possessive').capitalize()} surrogate said, \"Let's {gear.prep} and still enjoy the magic, mate.\"")
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["worry"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"{name}'s face lit up, because the plan was safe enough to enjoy.")
    world.say(f"Soon the crew {gear.tail}, and {hero.id} could {activity.gerund} without losing the {treasure.label}.")
    world.say(f"At the end, the ship stayed whole, the treasure stayed bright, and {name} enjoyed the night like a true pirate.")
    world.facts.update(hero=hero, parent=parent, prize=treasure, activity=activity, gear=gear, surrogate=elder)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short pirate tale for a child named {hero.id} that includes the words "surrogate", "stimulate", and "enjoy".',
        f"Tell a gentle pirate story where {hero.id} wants to {act.verb} and a surrogate helper keeps {prize.label} safe.",
        f"Write a story about Curiosity, Magic, and a small pirate crew who can still enjoy the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, act, prize, gear = f["hero"], f["activity"], f["prize"], f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship or shore?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the magic and waves made things tricky?",
            answer=f"The surrogate captain helped {hero.id}.",
        ),
        QAItem(
            question=f"What plan let {hero.id} enjoy the day without ruining the {prize.label}?",
            answer=f"They used {gear.label} and kept the {prize.label} safe while still following the fun.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about new things.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special kind of story power that can make surprising things happen.",
        ),
        QAItem(
            question="What does a surrogate helper mean?",
            answer="A surrogate helper is someone who steps in and does the job for another person for a while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="ship", activity="glow", prize="lantern", name="Mira", parent="captain", trait="curious"),
    StoryParams(place="cove", activity="tide", prize="hat", name="Jax", parent="mate", trait="brave"),
    StoryParams(place="island", activity="glow", prize="map", name="Nina", parent="captain", trait="cheerful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.activity], PRIZES[params.prize], params.name, params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
