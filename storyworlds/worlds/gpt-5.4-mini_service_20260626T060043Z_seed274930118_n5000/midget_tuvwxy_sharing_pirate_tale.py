#!/usr/bin/env python3
"""
A small Storyweavers world for a pirate tale about sharing.

Premise:
A tiny pirate crew has a treasure chest, and one small pirate wants to keep
everything for themself. The crew finds a way to share the loot, the map, and
the fun so nobody feels left out.

This script builds a compact simulated world with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    sea: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    kind: str
    shareable: bool = True


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    kind: str
    can_split: bool = False
    can_take_turns: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    treasure: str
    share_item: str
    seed: Optional[int] = None


PLACES = {
    "deck": Place(id="deck", label="the sunlit deck", sea=True, affords={"sharing"}),
    "cove": Place(id="cove", label="the quiet cove", sea=True, affords={"sharing"}),
    "island": Place(id="island", label="the small island", sea=True, affords={"sharing"}),
}

TREASURES = {
    "gold": Treasure(id="gold", label="gold coins", phrase="a little pouch of gold coins", kind="gold", shareable=True),
    "map": Treasure(id="map", label="map", phrase="a treasure map with a big red X", kind="map", shareable=True),
    "pearls": Treasure(id="pearls", label="pearls", phrase="a string of bright pearls", kind="pearls", shareable=True),
}

SHARE_ITEMS = {
    "cookies": ShareItem(id="cookies", label="cookies", phrase="a plate of coconut cookies", kind="cookies", can_split=True, can_take_turns=False),
    "lantern": ShareItem(id="lantern", label="lantern", phrase="a lantern for the night watch", kind="lantern", can_split=False, can_take_turns=True),
    "rope": ShareItem(id="rope", label="rope", phrase="one sturdy rope", kind="rope", can_split=False, can_take_turns=True),
}

NAMES = ["Midge", "Toby", "Pip", "Nina", "Bo", "Rae", "Jory", "Lina"]
TRAITS = ["little", "brave", "cheery", "curious", "bossy", "shy"]


def share_reasonable(place: Place, treasure: Treasure, share_item: ShareItem) -> bool:
    return "sharing" in place.affords and treasure.shareable and (share_item.can_split or share_item.can_take_turns)


def explain_rejection(place: Place, treasure: Treasure, share_item: ShareItem) -> str:
    return (
        f"(No story: {treasure.label} and {share_item.label} do not support a fair sharing tale at {place.label}. "
        f"Choose a shareable treasure and a useful shared item.)"
    )


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_jealous(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("greedy", 0) < THRESHOLD:
        return out
    sig = ("jealous",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["stingy"] = hero.memes.get("stingy", 0) + 1
    out.append("The pirate hugged the treasure close and would not share.")
    return out


def _r_warm(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    side = world.get("sidekick")
    if hero.memes.get("sharing", 0) < THRESHOLD:
        return out
    sig = ("warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    side.memes["happy"] = side.memes.get("happy", 0) + 1
    hero.memes["kind"] = hero.memes.get("kind", 0) + 1
    out.append("When they shared, the deck felt bright and kind.")
    return out


CAUSAL_RULES = [Rule("jealous", _r_jealous), Rule("warm", _r_warm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_share(world: World, hero: Entity, treasure: Treasure) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["greedy"] = sim.get(hero.id).memes.get("greedy", 0) + 1
    propagate(sim, narrate=False)
    return sim.get(hero.id).memes.get("stingy", 0) >= THRESHOLD


def tell(place: Place, treasure: Treasure, share_item: ShareItem, hero_name: str, side_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    side = world.add(Entity(id="sidekick", kind="character", type="girl", label=side_name))
    chest = world.add(Entity(id="treasure", kind="thing", type=treasure.kind, label=treasure.label, phrase=treasure.phrase, owner=hero.id))
    shared = world.add(Entity(id="shared", kind="thing", type=share_item.kind, label=share_item.label, phrase=share_item.phrase, owner=hero.id))
    world.facts.update(hero=hero, sidekick=side, treasure=chest, share_item=shared)

    hero.memes["greedy"] = 1
    world.say(f"{hero.label} was a little pirate who loved shiny things.")
    world.say(f"{side.label} was {random.choice(TRAITS if False else ['brave', 'curious'])} and liked helping on the deck.")
    world.say(f"One morning, the crew found {treasure.phrase} and {share_item.phrase} beside the mast.")
    world.say(f"{hero.label} wanted to keep {treasure.label} all to {hero.pronoun('possessive')}self, but {side.label} wanted everyone to have a turn.")

    world.para()
    world.say(f"At {place.label}, the wind was soft and the ropes creaked like sleepy voices.")
    hero.memes["greedy"] += 1
    if predict_share(world, hero, treasure):
        world.say(f'"We should share," said {side.label}, pointing at the treasure and the snack.')
        world.say(f"{hero.label} frowned at first, because {hero.pronoun('subject')} did not want to give up the best pieces.")
        propagate(world, narrate=True)
        hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
        hero.memes["greedy"] = 0
        world.say(f"Then {hero.label} cut the cookies into halves and let {side.label} hold the map.")
        world.say(f"They took turns naming the stars, and the treasure felt bigger when it was shared.")
    else:
        world.say(f"The pirates had no fair way to share, so they sat down and thought until they found one.")

    world.para()
    world.say(f"In the end, {hero.label} smiled and passed {treasure.label} around the crew.")
    world.say(f"{side.label} laughed, because the best part of the treasure was the happy feeling on the {place.label}.")
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for t in TREASURES.values():
            for s in SHARE_ITEMS.values():
                if share_reasonable(p, t, s):
                    combos.append((p.id, t.id, s.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a small child about "sharing" that includes the word "{f["share_item"].label}".',
        f"Tell a gentle pirate tale where {f['hero'].label} learns to share {f['treasure'].label} with {f['sidekick'].label}.",
        f"Write a short story about a tiny crew on {world.place.label} who choose sharing over selfishness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    side = f["sidekick"]
    treasure = f["treasure"]
    share_item = f["share_item"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who learned to share at {place}?",
            answer=f"{hero.label} learned to share at {place} with help from {side.label}.",
        ),
        QAItem(
            question=f"What treasure did the pirates find?",
            answer=f"They found {treasure.phrase}.",
        ),
        QAItem(
            question=f"What did the crew do to be fair with {share_item.label}?",
            answer=f"They shared {share_item.label} and took turns, so everybody got a chance.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or have part of something too.",
        ),
        QAItem(
            question="Why do pirates use a map?",
            answer="Pirates use a map to help find where a treasure might be hidden.",
        ),
        QAItem(
            question="What is a crew?",
            answer="A crew is a group of people who work together on a ship or in an adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for (name, *_) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="deck", hero="Midget", sidekick="Tuvvxy", treasure="gold", share_item="cookies"),
    StoryParams(place="cove", hero="Midget", sidekick="Tuvvxy", treasure="map", share_item="lantern"),
    StoryParams(place="island", hero="Midget", sidekick="Tuvvxy", treasure="pearls", share_item="rope"),
]


ASP_RULES = r"""
prize_ok(T) :- treasure(T), shareable(T).
share_ok(S) :- share_item(S), split(S).
share_ok(S) :- share_item(S), turns(S).
valid(Place,T,S) :- place(Place), affords(Place,sharing), prize_ok(T), share_ok(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.sea:
            lines.append(asp.fact("sea", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for sid, s in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", sid))
        if s.can_split:
            lines.append(asp.fact("split", sid))
        if s.can_take_turns:
            lines.append(asp.fact("turns", sid))
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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale about sharing.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--treasure", choices=TREASURES.keys())
    ap.add_argument("--share-item", dest="share_item", choices=SHARE_ITEMS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if args.share_item:
        combos = [c for c in combos if c[2] == args.share_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treasure, share_item = rng.choice(sorted(combos))
    hero = args.hero or "Midget"
    sidekick = args.sidekick or "Tuvvxy"
    return StoryParams(place=place, hero=hero, sidekick=sidekick, treasure=treasure, share_item=share_item)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        TREASURES[params.treasure],
        SHARE_ITEMS[params.share_item],
        params.hero,
        params.sidekick,
    )
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
        print(f"{len(asp_valid_combos())} compatible (place, treasure, share_item) combos:")
        for triple in asp_valid_combos():
            print(" ", triple)
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
