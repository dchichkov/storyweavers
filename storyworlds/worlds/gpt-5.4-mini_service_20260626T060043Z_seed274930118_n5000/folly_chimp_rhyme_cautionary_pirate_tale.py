#!/usr/bin/env python3
"""
A small cautionary pirate tale world with rhyme, centered on a chimp whose
folly leads to trouble and a wiser ending.

The simulated domain:
- A pirate ship setting with one chimp, one captain, one treasure chest, and a
  risky action.
- Physical meters track things like balance, soaked, tangled, and secure.
- Emotional memes track pride, caution, worry, shame, relief, and trust.
- The story is generated from world state, not from a fixed paragraph template.

The tale style:
- Pirate-tale voice
- Gentle rhyme in a few key beats
- Cautionary structure: warning -> folly -> consequence -> wiser turn
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["balance", "soaked", "tangled", "secure", "dusty"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "pride", "caution", "worry", "shame", "relief", "trust", "folly"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    setting: str
    rhyme: str = ""
    caution: str = ""


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    gender: str = "chimp"
    captain: str = "Captain Reed"
    ship: str = "the Ruby Gull"
    treasure: str = "golden map"
    folly: str = "swing from the mast in a storm"
    rhyme: bool = True
    cautionary: bool = True


NAMES = ["Milo", "Kiki", "Bram", "Nori", "Pip", "Tiki", "Bobo", "Sage"]
CAPTAINS = ["Captain Reed", "Captain Mire", "Captain Sol", "Captain Vale"]
SHIPS = ["the Ruby Gull", "the Sea Lantern", "the Briny Star", "the Drifted Comet"]
TREASURES = [
    ("golden map", "map"),
    ("silver key", "key"),
    ("pearl compass", "compass"),
    ("bronze coin pouch", "pouch"),
]


def _r_slip(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.meters["balance"] < THRESHOLD:
        sig = ("slip",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        chimp.meters["soaked"] += 1
        chimp.meters["tangled"] += 1
        chimp.memes["worry"] += 1
        out.append("The deck gave a creak and a sneaky squeal; down went the chimp in a foamy gale.")
    return out


def _r_shame(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.meters["soaked"] >= THRESHOLD and ("shame",) not in world.fired:
        world.fired.add(("shame",))
        chimp.memes["shame"] += 1
        captain = world.get("captain")
        captain.memes["worry"] += 1
        out.append("The captain frowned, not hard or grim, but said, 'A fool's tide can drown a trim.'")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.memes["caution"] >= THRESHOLD and chimp.memes["trust"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        chimp.memes["relief"] += 1
        chimp.memes["worry"] = max(0.0, chimp.memes["worry"] - 1.0)
        out.append("With steady paws and a softer sway, the chimp chose sense and saved the day.")
    return out


RULES = [_r_slip, _r_shame, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_folly(world: World) -> dict[str, float]:
    sim = world.copy()
    chimp = sim.get("chimp")
    chimp.meters["balance"] = 0.0
    propagate(sim, narrate=False)
    return {
        "soaked": sim.get("chimp").meters["soaked"],
        "shame": sim.get("chimp").memes["shame"],
    }


def make_world(params: StoryParams) -> World:
    ship = Ship(name=params.ship, place="at sea", setting="pirate ship", rhyme="rhyme", caution="caution")
    world = World(ship)
    chimp = world.add(Entity(id="chimp", kind="character", type="chimp", label=params.name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain))
    chest = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=params.treasure,
        phrase=f"the {params.treasure}",
        owner=captain.id,
        caretaker=captain.id,
        region="hold",
    ))

    chimp.memes["joy"] += 1
    chimp.memes["pride"] += 1
    chimp.memes["caution"] += 1
    captain.memes["trust"] += 1
    chest.meters["secure"] += 1

    world.say(f"On {world.ship.name}, a clever chimp named {chimp.label} spied the sea.")
    world.say(f"The {captain.label_word if hasattr(captain, 'label_word') else 'captain'} kept the {chest.label} safe below.")
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    chimp = world.get("chimp")
    captain = world.get("captain")
    treasure = world.get("treasure")

    world.para()
    world.say(
        f"{chimp.label} loved the salt and spray, and hummed a merry tune at play;"
        f" yet the captain warned, 'Mind the mast, or folly may make your footing cast.'"
    )
    world.say(
        f"{chimp.label} heard the warning, but pride grew tall; "
        f"{chimp.label} chose the folly {params.folly}, thinking it grand and brave for all."
    )

    world.para()
    chimp.meters["balance"] = 0.0
    chimp.memes["folly"] += 1
    captain.memes["worry"] += 1
    world.say(
        f"The wind went whoosh, the ropes went snap, and overboard tumbled the cheeky chap."
        f" Down he splashed in the briny foam, with tangled fur and a soggy comb."
    )
    propagate(world, narrate=True)

    world.para()
    chimp.memes["caution"] += 1
    chimp.memes["trust"] += 1
    captain.memes["relief"] += 1
    world.say(
        f"Then {chimp.label} learned a better way: to heed the watch and guard the day;"
        f" he climbed by steps, not daring leaps, and kept the {treasure.label} safe in the keep."
    )
    chimp.meters["balance"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"So the voyage glowed with a wiser light, and folly lost its swashbuckling fight;"
        f" for a chimp who listens at sea, mates with caution sails more merrily."
    )

    world.facts.update(
        chimp=chimp,
        captain=captain,
        treasure=treasure,
        params=params,
        predicted=predict_folly(world),
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    chimp = world.facts["chimp"]
    captain = world.facts["captain"]
    treasure = world.facts["treasure"]
    params = world.facts["params"]
    qa = [
        QAItem(
            question=f"Who is the story mainly about on {params.ship}?",
            answer=f"It is about {chimp.label}, a chimp aboard {params.ship} who makes a poor choice and then learns a wiser one.",
        ),
        QAItem(
            question=f"What did {chimp.label} do out of folly?",
            answer=f"{chimp.label} tried to {params.folly}, even after the captain warned that the deck and ropes could make that choice dangerous.",
        ),
        QAItem(
            question=f"What happened after the chimp ignored the warning?",
            answer=f"The chimp slipped into the sea, got soaked and tangled, and felt embarrassed before choosing a safer way to move.",
        ),
        QAItem(
            question=f"What did the captain want to keep safe?",
            answer=f"The captain wanted to keep the {treasure.label} safe below deck, away from the storm and the chimp's foolish leap.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {chimp.label} climbing more carefully, listening better, and keeping the voyage steady instead of reckless.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used for sailing on the sea, often with ropes, sails, and a deck that can get slippery.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking about danger before acting.",
        ),
        QAItem(
            question="What is folly?",
            answer="Folly is a very foolish choice that ignores good advice and can lead to trouble.",
        ),
        QAItem(
            question="Why can the sea be dangerous?",
            answer="The sea can be dangerous because waves, wind, and wet decks can make people slip or get lost.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    return [
        f"Write a short pirate tale in rhyme about a chimp named {params.name} and a mistake at sea.",
        f"Tell a cautionary story where a chimp on {params.ship} ignores warning and learns from folly.",
        f"Write a child-friendly pirate adventure with a rhyming warning, a tumble, and a wiser ending.",
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A chimp is in folly if the story chooses a risky action after a warning.
folly(chimp) :- warned(chimp), ignores_warning(chimp).

% The consequence follows when folly meets the ship's danger.
trouble(chimp) :- folly(chimp), stormy_sea, slippery_deck.

% Caution and trust support a safer ending.
resolved(chimp) :- learns(chimp), cautious(chimp), trusts_captain(chimp).

#show folly/1.
#show trouble/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("warned", "chimp"),
        asp.fact("ignores_warning", "chimp"),
        asp.fact("stormy_sea"),
        asp.fact("slippery_deck"),
        asp.fact("learns", "chimp"),
        asp.fact("cautious", "chimp"),
        asp.fact("trusts_captain", "chimp"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"folly/1", "trouble/1", "resolved/1"}
    if atoms == expected:
        print("OK: ASP twin matches the intended tiny pirate logic.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale world with rhyme and a chimp.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--treasure", choices=[t[0] for t in TREASURES])
    ap.add_argument("--folly", choices=[
        "swing from the mast in a storm",
        "dance on the rail while the sea heaves",
        "reach for the map without looking down",
        "race the gulls across the deck",
    ])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(CAPTAINS)
    ship = args.ship or rng.choice(SHIPS)
    treasure = args.treasure or rng.choice([t[0] for t in TREASURES])
    folly = args.folly or rng.choice([
        "swing from the mast in a storm",
        "dance on the rail while the sea heaves",
        "reach for the map without looking down",
        "race the gulls across the deck",
    ])
    gender = "chimp"
    return StoryParams(
        seed=args.seed,
        name=name,
        gender=gender,
        captain=captain,
        ship=ship,
        treasure=treasure,
        folly=folly,
        rhyme=True,
        cautionary=True,
    )


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
    StoryParams(name="Milo", captain="Captain Reed", ship="the Ruby Gull", treasure="golden map", folly="swing from the mast in a storm"),
    StoryParams(name="Kiki", captain="Captain Mire", ship="the Sea Lantern", treasure="silver key", folly="dance on the rail while the sea heaves"),
    StoryParams(name="Bram", captain="Captain Sol", ship="the Briny Star", treasure="pearl compass", folly="reach for the map without looking down"),
]


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
        print(" ".join(str(sym) for sym in model))
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
