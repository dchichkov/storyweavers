#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emu_alligator_qrxde_friendship_pirate_tale.py
===============================================================================================================

A small story world in a pirate-tale style about friendship between an emu,
an alligator, and the odd little name qrxde.

The premise:
- An emu and an alligator sail the same small pirate route.
- One of them finds a lost treasure map on the deck of the ship Qrxde.
- A squabble starts because the map points to a cove only one of them can reach.
- Friendship turns the quarrel into a shared plan, and they share the treasure.

This world uses physical meters and emotional memes, with a simple state
simulation that drives the prose rather than swapping nouns in a frozen story.
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

FRIENDSHIP_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"salt": 0.0, "risk": 0.0, "treasure": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "trust": 0.0, "rivalry": 0.0, "friendship": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"emu", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"alligator", "reptile"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str = "the open sea"
    holds_map: bool = True
    has_treasure: bool = False
    wind: str = "fair"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(Ship(self.ship.name, self.ship.place, self.ship.holds_map, self.ship.has_treasure, self.ship.wind))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _c_fight(world: World) -> list[str]:
    out: list[str] = []
    emu = world.get("emu")
    gator = world.get("alligator")
    if emu.memes["rivalry"] >= FRIENDSHIP_THRESHOLD and gator.memes["rivalry"] >= FRIENDSHIP_THRESHOLD:
        sig = ("fight",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("They bickered like two tiny captains over one shining map.")
    return out


def _c_friendship(world: World) -> list[str]:
    out: list[str] = []
    emu = world.get("emu")
    gator = world.get("alligator")
    if emu.memes["trust"] >= FRIENDSHIP_THRESHOLD and gator.memes["trust"] >= FRIENDSHIP_THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            emu.memes["friendship"] += 1
            gator.memes["friendship"] += 1
            emu.memes["rivalry"] = 0.0
            gator.memes["rivalry"] = 0.0
            out.append("Their grumble softened into a warm, true friendship.")
    return out


def _c_treasure_share(world: World) -> list[str]:
    out: list[str] = []
    if not world.ship.has_treasure:
        return out
    emu = world.get("emu")
    gator = world.get("alligator")
    if emu.memes["friendship"] >= FRIENDSHIP_THRESHOLD and gator.memes["friendship"] >= FRIENDSHIP_THRESHOLD:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            emu.meters["treasure"] += 1
            gator.meters["treasure"] += 1
            out.append("So they split the treasure fair and square between feather and tooth.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_c_fight, _c_friendship, _c_treasure_share):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str = "qrxde"
    seed: Optional[int] = None
    wind: str = "fair"
    treasure: str = "gold coin"


NAMES = ["qrxde", "Emu", "Captain Qrxde", "Skiff"]
TREASURES = ["gold coin", "pearls", "a ruby", "a silver key"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale friendship storyworld with emu, alligator, and qrxde.")
    ap.add_argument("--name", choices=["qrxde", "Emu", "Captain Qrxde", "Skiff"])
    ap.add_argument("--wind", choices=["fair", "gusty", "stormy"])
    ap.add_argument("--treasure", choices=TREASURES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        seed=args.seed,
        wind=args.wind or rng.choice(["fair", "gusty", "stormy"]),
        treasure=args.treasure or rng.choice(TREASURES),
    )


def tell(params: StoryParams) -> World:
    ship = Ship(name="qrxde", place="the briny blue", wind=params.wind)
    world = World(ship)

    emu = world.add(Entity(id="emu", kind="character", type="emu", label="emu"))
    gator = world.add(Entity(id="alligator", kind="character", type="alligator", label="alligator"))
    map_ent = world.add(Entity(id="map", type="map", label="treasure map", phrase="a crinkled treasure map"))
    chest = world.add(Entity(id="chest", type="chest", label="chest", phrase=params.treasure))
    chest.owner = "emu"

    emu.memes["joy"] += 1
    gator.memes["joy"] += 1
    emu.memes["trust"] += 1
    gator.memes["trust"] += 1

    world.say("On the little pirate ship qrxde, an emu and an alligator sailed beneath a lively sky.")
    world.say("They were odd shipmates, but they liked each other's jokes and shared the same salt wind.")

    world.para()
    world.say("One day, the emu found a treasure map tucked under a loose plank.")
    world.say("The map pointed to a hidden cove, and the promise of treasure made both friends lean close.")

    emu.memes["rivalry"] += 1
    gator.memes["rivalry"] += 1
    world.say("The emu wanted to keep the map safe, and the alligator wanted to lead the hunt.")
    world.say("Soon they were muttering and blinking at each other across the deck.")

    world.para()
    propagate(world)
    world.say("Then the emu noticed the cove was shallow and muddy, and the alligator could swim in first.")
    world.say("The alligator noticed the map would stay dry in the emu's beak.")
    emu.memes["trust"] += 1
    gator.memes["trust"] += 1
    world.say("That thought cooled their tempers, because friends do better when they listen.")

    world.para()
    propagate(world)
    world.ship.has_treasure = True
    world.say(f"They followed the map to the cove, found {params.treasure}, and laughed so hard the gulls circled twice.")
    world.say("At sunset, the emu and the alligator sat side by side on qrxde's deck, each with an equal share.")

    world.facts.update(
        emu=emu,
        alligator=gator,
        map=map_ent,
        chest=chest,
        ship=ship,
        params=params,
        treasure=params.treasure,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    return [
        'Write a pirate tale for a small child about emu, alligator, and qrxde, with friendship at its heart.',
        f'Write a short story where an emu and an alligator on the ship qrxde find {params.treasure} and learn to cooperate.',
        'Tell a gentle pirate story in which two shipmates quarrel over a map, then become friends again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    emu = world.facts["emu"]
    gator = world.facts["alligator"]
    qa = [
        QAItem(
            question="Who sailed on the pirate ship qrxde?",
            answer="An emu and an alligator sailed together on the pirate ship qrxde.",
        ),
        QAItem(
            question="What did the emu find under the loose plank?",
            answer="The emu found a treasure map under the loose plank.",
        ),
        QAItem(
            question="Why did the emu and alligator start to bicker?",
            answer="They bickered because both of them wanted to lead the treasure hunt and hold the map their own way.",
        ),
        QAItem(
            question="How did the friends solve their argument?",
            answer="They calmed down, listened to each other, and used both of their strengths to follow the map together.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"They reached the cove, found {p.treasure}, and shared it as friends on qrxde's deck.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that travels the sea and can carry a crew, supplies, and treasure.",
        ),
        QAItem(
            question="What is a treasure map for?",
            answer="A treasure map helps travelers find a hidden place or a buried prize.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people or animals care about each other, listen, and try to help each other.",
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
        lines.append(
            f"  {e.id:10} type={e.type:10} meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } "
            f"memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    lines.append(f"  ship={world.ship.name} wind={world.ship.wind} has_treasure={world.ship.has_treasure}")
    lines.append(f"  fired rules={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
emu(E) :- entity(E), type(E,emu).
alligator(E) :- entity(E), type(E,alligator).

friend(E) :- joy(E, J), trust(E, T), J >= 1, T >= 1.
fight(E) :- rivalry(E, R), R >= 1.

shared_treasure :- friend(emu), friend(alligator), treasure_found.

resolved :- shared_treasure.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [
        asp.fact("entity", "emu"),
        asp.fact("entity", "alligator"),
        asp.fact("entity", "map"),
        asp.fact("entity", "qrxde"),
        asp.fact("type", "emu", "emu"),
        asp.fact("type", "alligator", "alligator"),
        asp.fact("type", "map", "map"),
        asp.fact("type", "qrxde", "ship"),
        asp.fact("treasure_found"),
        asp.fact("joy", "emu", 1),
        asp.fact("joy", "alligator", 1),
        asp.fact("trust", "emu", 2),
        asp.fact("trust", "alligator", 2),
        asp.fact("rivalry", "emu", 0),
        asp.fact("rivalry", "alligator", 0),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show resolved/0."))
    ok = any(sym.name == "resolved" for sym in model)
    if ok:
        print("OK: ASP model resolves the friendship treasure story.")
        return 0
    print("MISMATCH: ASP model did not resolve.")
    return 1


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(name="qrxde", wind="fair", treasure="gold coin"),
            StoryParams(name="Emu", wind="gusty", treasure="pearls"),
            StoryParams(name="Captain Qrxde", wind="stormy", treasure="a ruby"),
        ]
        for p in params_list:
            samples.append(generate(p))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 20, 20):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print("resolved:" if any(sym.name == "resolved" for sym in model) else "unresolved")
        return

    samples = build_samples(args)

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
