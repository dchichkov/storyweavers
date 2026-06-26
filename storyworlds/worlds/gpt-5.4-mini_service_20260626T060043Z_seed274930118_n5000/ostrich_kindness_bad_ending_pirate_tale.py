#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld with an ostrich hero, kindness, and a bad ending.

The world simulates a short source tale:
- an ostrich aboard a pirate ship is gentle and helpful,
- a storm or trick turns the kindness into a costly choice,
- the crew or treasure situation worsens,
- the story ends with a concrete image of what was lost.

The story is intentionally close to a Pirate Tale tone: sea wind, ship deck,
captain, map, dock, cargo, and a small crew.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ostrich"}
        male = {"boy", "father", "man", "pirate", "captain", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    deck: bool
    stormy: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    trouble: str
    risk: str
    place_key: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    action: str
    helps: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "harbor": Place("the harbor", deck=True, stormy=False, affords={"gather", "share", "sail"}),
    "ship": Place("the ship deck", deck=True, stormy=True, affords={"gather", "share", "sail"}),
    "cove": Place("the cove", deck=False, stormy=False, affords={"gather", "share"}),
}

ACTIONS = {
    "share_water": Event(
        id="share_water",
        verb="share the water",
        gerund="sharing the water",
        trouble="ran low",
        risk="thirst",
        place_key="ship",
        keyword="water",
        tags={"kindness", "sea"},
    ),
    "help_lift": Event(
        id="help_lift",
        verb="help lift the crate",
        gerund="lifting the crate",
        trouble="slipped",
        risk="loss",
        place_key="harbor",
        keyword="crate",
        tags={"kindness", "cargo"},
    ),
    "warn_storm": Event(
        id="warn_storm",
        verb="warn the captain",
        gerund="warning the captain",
        trouble="came fast",
        risk="storm",
        place_key="ship",
        keyword="storm",
        tags={"kindness", "storm"},
    ),
}

PRIZES = {
    "map": Prize("map", "treasure map", "a folded treasure map", "torso"),
    "rope": Prize("rope", "rope bundle", "a thick rope bundle", "hands"),
    "lantern": Prize("lantern", "lantern", "a brass lantern", "hands"),
}

FIXES = {
    "bucket": Fix("bucket", "a bucket", "carry water in a bucket", {"thirst"}, {"hands"}, False),
    "strap": Fix("strap", "a rope strap", "tie the crate down with a rope strap", {"loss"}, {"torso", "hands"}, False),
    "sail_tie": Fix("sail_tie", "a sail tie", "tie the sail down with a sail tie", {"storm"}, {"hands", "torso"}, False),
}

CURATED = [
    ("ship", "share_water", "map"),
    ("harbor", "help_lift", "rope"),
    ("ship", "warn_storm", "lantern"),
]

OSTRICH_NAMES = ["Oona", "Tilly", "Mara", "Pip", "Sage"]
PIRATE_NAMES = ["Captain Brine", "Bosun Bell", "Mister Rook", "Ada Hook"]


def valid_combo(place: str, act: str, prize: str) -> bool:
    event = ACTIONS[act]
    if place not in SETTINGS:
        return False
    # Reasonable only if place supports the action and the prize is plausibly at risk.
    if act not in SETTINGS[place].affords:
        return False
    if event.risk == "thirst" and prize != "map":
        return False
    if event.risk == "loss" and prize != "rope":
        return False
    if event.risk == "storm" and prize != "lantern":
        return False
    return True


def choose_fix(event: Event, prize: Prize) -> Optional[Fix]:
    if event.risk == "thirst" and prize.id == "map":
        return FIXES["bucket"]
    if event.risk == "loss" and prize.id == "rope":
        return FIXES["strap"]
    if event.risk == "storm" and prize.id == "lantern":
        return FIXES["sail_tie"]
    return None


def predict_bad(world: World, hero: Entity, event: Event, prize: Prize) -> bool:
    sim = world.copy()
    _do_event(sim, hero.id, event, prize, narrate=False)
    return sim.facts.get("bad", False)


def _do_event(world: World, hero_id: str, event: Event, prize: Prize, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    if event.id == "share_water":
        hero.meters["water"] = hero.meters.get("water", 0) - 1
        world.facts["shared"] = True
        if prize.id == "map":
            world.facts["bad"] = True
    elif event.id == "help_lift":
        hero.meters["tired"] = hero.meters.get("tired", 0) + 1
        world.facts["shared"] = True
        if prize.id == "rope":
            world.facts["bad"] = True
    elif event.id == "warn_storm":
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.facts["shared"] = True
        if prize.id == "lantern":
            world.facts["bad"] = True
    if narrate:
        world.say(f"{hero.id} {event.gerund}, because {hero.pronoun('subject')} was kind.")


def tell(place_key: str, act_key: str, prize_key: str, name: str, pirate_name: str) -> World:
    place = SETTINGS[place_key]
    event = ACTIONS[act_key]
    prize = PRIZES[prize_key]
    world = World(place)

    hero = world.add(Entity(id=name, kind="character", type="ostrich", label=name))
    pirate = world.add(Entity(id=pirate_name, kind="character", type="pirate", label=pirate_name))
    treasure = world.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, owner=pirate.id))

    hero.meters["hope"] = 1
    pirate.memes["greed"] = 1

    world.say(f"{hero.id} lived with the pirates on {place.name}, and {hero.pronoun('subject')} had a gentle heart.")
    world.say(f"{hero.id} liked helping {pirate.label} and the crew when the decks got busy.")
    world.say(f"One day, {hero.id} watched {treasure.phrase} and noticed it could cause trouble.")

    world.para()
    world.say(f"The wind picked up near {place.name}, and the sea smelled sharp.")
    world.say(f"{hero.id} wanted to {event.verb}, even though {event.trouble}.")
    _do_event(world, hero.id, event, treasure)

    fix = choose_fix(event, treasure)
    if fix is not None:
        if predict_bad(world, hero, event, treasure):
            world.say(f"{pirate.label} offered {fix.label}, but the plan came too late.")
            world.say(f"By then, {hero.id} had already made the kind choice that caused a bad ending.")
    world.para()
    world.say(f"At the end, the ship was smaller in the dark water, and {hero.id} was left with the quiet deck.")
    if world.facts.get("bad"):
        world.say(f"{treasure.phrase} was gone, and the only light left was the moon on the waves.")
    else:
        world.say(f"{treasure.phrase} stayed safe, but the story still ended with a hush over the sea.")

    world.facts.update(hero=hero, pirate=pirate, prize=treasure, event=event, place=place, fix=fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a young child about an ostrich whose kindness leads to a bad ending.',
        f"Tell a sea story where {f['hero'].id} tries to {f['event'].verb} on {f['place'].name} and something goes wrong.",
        f"Write a gentle pirate story with {f['hero'].id}, {f['pirate'].label}, and {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    pirate: Entity = f["pirate"]
    prize: Entity = f["prize"]
    event: Event = f["event"]
    place: Place = f["place"]
    bad = f.get("bad", False)
    return [
        QAItem(
            question=f"Who was the kind ostrich in the story?",
            answer=f"The kind ostrich was {hero.id}. {hero.id} lived with the pirates near {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on {place.name}?",
            answer=f"{hero.id} wanted to {event.verb}, because {hero.pronoun('subject')} was trying to help the crew.",
        ),
        QAItem(
            question=f"What treasure was in danger?",
            answer=f"The treasure was {prize.phrase}. That was the thing the pirates hoped to keep safe.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because {hero.id}'s kind choice made trouble for {prize.phrase}, "
                f"and the story ended with loss on the sea."
                if bad else
                f"The story ended quietly, but in this version the loss never fully happened."
            ),
        ),
    ]


KNOWLEDGE = {
    "ostrich": [
        QAItem(
            question="What is an ostrich?",
            answer="An ostrich is a very large bird with long legs and a long neck.",
        )
    ],
    "pirate": [
        QAItem(
            question="What does a pirate usually do?",
            answer="A pirate is a sailor who travels on the sea and looks for treasure.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping others, being gentle, and trying to do good things for them.",
        )
    ],
    "map": [
        QAItem(
            question="What is a treasure map?",
            answer="A treasure map is a drawing that shows where someone thinks treasure might be hidden.",
        )
    ],
    "storm": [
        QAItem(
            question="What is a storm at sea?",
            answer="A storm at sea brings strong wind, rain, and rough waves that can shake a ship.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"ostrich", "pirate", "kindness"}
    if f["prize"].id == "map":
        tags.add("map")
    if f["event"].id == "warn_storm":
        tags.add("storm")
    out: list[QAItem] = []
    for tag in ["ostrich", "pirate", "kindness", "map", "storm"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


ASP_RULES = r"""
place(ship). place(harbor). place(cove).
affords(harbor,gather). affords(harbor,share). affords(harbor,sail).
affords(ship,gather). affords(ship,share). affords(ship,sail).
affords(cove,gather). affords(cove,share).

action(share_water). action(help_lift). action(warn_storm).
risk(share_water,thirst). risk(help_lift,loss). risk(warn_storm,storm).

prize(map). prize(rope). prize(lantern).
at_risk(share_water,map).
at_risk(help_lift,rope).
at_risk(warn_storm,lantern).

valid(P,A,R) :- affords(P,A), at_risk(A,R), risk(A,th), prize(R), th = thirst.
valid(P,A,R) :- affords(P,A), at_risk(A,R), risk(A,lo), prize(R), lo = loss.
valid(P,A,R) :- affords(P,A), at_risk(A,R), risk(A,st), prize(R), st = storm.
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k, p in SETTINGS.items():
        lines.append(asp.fact("place", k))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", k, a))
    for k, a in ACTIONS.items():
        lines.append(asp.fact("action", k))
        lines.append(asp.fact("risk", k, a.risk))
    for k in PRIZES:
        lines.append(asp.fact("prize", k))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a, r) for p in SETTINGS for a in ACTIONS for r in PRIZES if valid_combo(p, a, r)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def valid_combo(place: str, act: str, prize: str) -> bool:
    if place not in SETTINGS or act not in ACTIONS or prize not in PRIZES:
        return False
    return place == ACTIONS[act].place_key and (
        (act == "share_water" and prize == "map") or
        (act == "help_lift" and prize == "rope") or
        (act == "warn_storm" and prize == "lantern")
    )


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    pirate: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with an ostrich, kindness, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--pirate")
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
    combos = [
        (p, a, r) for p in SETTINGS for a in ACTIONS for r in PRIZES
        if valid_combo(p, a, r)
        and (args.place is None or p == args.place)
        and (args.action is None or a == args.action)
        and (args.prize is None or r == args.prize)
    ]
    if not combos:
        raise StoryError("No valid pirate story matches those options.")
    place, action, prize = rng.choice(combos)
    name = args.name or rng.choice(OSTRICH_NAMES)
    pirate = args.pirate or rng.choice(PIRATE_NAMES)
    return StoryParams(place=place, action=action, prize=prize, name=name, pirate=pirate)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.action, params.prize, params.name, params.pirate)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, action, prize in CURATED:
            p = StoryParams(
                place=place,
                action=action,
                prize=prize,
                name=OSTRICH_NAMES[0],
                pirate=PIRATE_NAMES[0],
            )
            samples.append(generate(p))
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
