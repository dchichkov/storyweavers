#!/usr/bin/env python3
"""
Standalone story world: a pirate tale with a curious quest, an asymmetric twist,
and a strange stegosaurus foil.

The world is small and classical: a childlike pirate crew sails to a little bay,
hunts for a hidden treasure, faces a twist, and resolves it with a clever foil.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    shore: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    tag: str
    zone: set[str]
    weather: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str


@dataclass
class Foil:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


SETTINGS = {
    "harbor": Setting(place="the harbor", shore="the bright dock", afford={"quest", "twist"}),
    "cove": Setting(place="the cove", shore="the hidden cove shore", afford={"quest", "twist"}),
    "isle": Setting(place="the little isle", shore="the sandy isle shore", afford={"quest", "twist"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="seek the lost map",
        gerund="seeking the lost map",
        rush="dash toward the old cave",
        tag="quest",
        zone={"hands"},
        weather="breezy",
    ),
    "twist": Quest(
        id="twist",
        verb="follow the strange tracks",
        gerund="following the strange tracks",
        rush="hurry after the tracks",
        tag="twist",
        zone={"feet", "hands"},
        weather="windy",
    ),
    "curiosity": Quest(
        id="curiosity",
        verb="peek at the shiny shell",
        gerund="peeking at the shiny shell",
        rush="lean over the railing",
        tag="curiosity",
        zone={"hands"},
        weather="calm",
    ),
}

PRIZES = {
    "treasure": Prize(id="treasure", label="treasure chest", phrase="a little treasure chest", region="hands"),
    "lantern": Prize(id="lantern", label="lantern", phrase="a brass lantern", region="hands"),
    "hat": Prize(id="hat", label="hat", phrase="a fancy pirate hat", region="head"),
}

FOILS = {
    "foil": Foil(
        id="foil",
        label="a foil sail-sheen",
        covers={"hands"},
        guards={"scratched", "soggy"},
        prep="wrap the map in a foil sail-sheen",
        tail="tied the foil sail-sheen tight",
    ),
    "foil_box": Foil(
        id="foil_box",
        label="a foil-lined box",
        covers={"hands", "head"},
        guards={"scratched", "soggy", "bent"},
        prep="place the prize in a foil-lined box",
        tail="set the foil-lined box on deck",
    ),
}

NAMES = ["Mina", "Jory", "Pip", "Nell", "Toby", "Rin"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Validity gate
# ---------------------------------------------------------------------------
def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_foil(quest: Quest, prize: Prize) -> Optional[Foil]:
    for foil in FOILS.values():
        if prize.region in foil.covers and ("soggy" in foil.guards or "scratched" in foil.guards):
            return foil
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for q in QUESTS.values():
            for p in PRIZES.values():
                if prize_at_risk(q, p) and select_foil(q, p):
                    out.append((place, q.id, p.id))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_twist(world: World, hero: Entity, quest: Quest, prize: Prize) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] = 1.0
    sim.get(hero.id).meters["rush"] = 1.0
    return prize_at_risk(quest, prize)


def _do_quest(world: World, hero: Entity, quest: Quest, prize: Entity, narrate: bool = True) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.meters["quest"] = hero.meters.get("quest", 0.0) + 1.0
    if quest.tag == "twist":
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.id} set out to {quest.gerund} at {world.place}.")


def tell(world: World, hero_name: str, quest: Quest, prize: Prize) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", traits=["young", "curious"]))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label="the captain"))
    prize_ent = world.add(Entity(
        id=prize.id,
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        location=world.place,
    ))

    world.say(f"{hero.id} was a small pirate with a bright grin and a very curious nose.")
    world.say(f"{hero.id} loved a good {quest.tag} and kept dreaming about the next quest.")
    world.say(f"One day, {hero.id}'s crew found {prize.phrase} on deck, and everyone stared at it.")

    world.para()
    world.say(f"At {world.place}, the air smelled like salt and tar.")
    world.say(f"{hero.id} wanted to {quest.verb}, but {hero.pronoun('possessive')} eyes kept sliding back to the prize.")
    if predict_twist(world, hero, quest, prize):
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        world.say(f"Then the path turned into an asymmetric twist: one side of the deck was safe, but the other side was full of sharp ropes and wet boards.")
        world.say(f'"If we rush now, the {prize.label} may get {quest.tag} marks," the captain said.')
        world.say(f"{hero.id} bit {hero.pronoun('possessive')} lip, because the quest looked exciting and the danger looked real.")

    world.para()
    foil = select_foil(quest, prize)
    if foil is None:
        raise StoryError("No reasonable foil exists for this quest and prize.")
    world.say(f"Then the captain smiled and said, \"Let's use {foil.label} first.\"")
    world.say(f"They {foil.prep}, so the prize would stay safe during the quest.")
    world.say(f"{hero.id} nodded, and the crew {foil.tail} before stepping forward together.")
    _do_quest(world, hero, quest, prize, narrate=False)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"Soon {hero.id} was {quest.gerund}, and the {prize.label} stayed dry and neat. "
        f"The captain laughed, and the little pirate felt proud of {hero.pronoun('possessive')} clever curiosity."
    )

    world.facts.update(hero=hero, captain=captain, prize=prize_ent, quest=quest, foil=foil)
    return world


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, prize = f["hero"], f["quest"], f["prize"]
    return [
        f'Write a short pirate tale for a child named {hero.id} that includes the word "curiosity".',
        f"Tell a pirate story where {hero.id} wants to {quest.verb} but must protect {prize.phrase}.",
        f'Write a gentle quest story with an asymmetric twist and a foil that keeps a prize safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, prize, foil = f["hero"], f["quest"], f["prize"], f["foil"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place}?",
            answer=f"{hero.id} wanted to {quest.verb}, because {hero.pronoun('possessive')} curiosity kept tugging at {hero.pronoun('possessive')} nose and hands.",
        ),
        QAItem(
            question=f"Why did the captain worry about the prize?",
            answer=f"The captain worried because the asymmetric twist on the deck could have left the {prize.label} scratched or soggy during the quest.",
        ),
        QAItem(
            question=f"How did {foil.label} help?",
            answer=f"It wrapped the prize safely so {hero.id} could keep going on the quest without ruining {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more or to look closely at something interesting.",
        ),
        QAItem(
            question="What is a twist in a path?",
            answer="A twist is a turn or bend that changes how you move forward.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important.",
        ),
        QAItem(
            question="What is a stegosaurus?",
            answer="A stegosaurus was a plant-eating dinosaur with big plates on its back and a spiky tail.",
        ),
        QAItem(
            question="Why can foil be useful?",
            answer="Foil can help cover and protect something from water, dirt, or scratches.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(Q,P) :- quest(Q), prize(P), zone(Q,R), region(P,R).
needs_foil(Q,P) :- prize_at_risk(Q,P).
has_foil(Q,P) :- needs_foil(Q,P), foil(F), covers(F,R), region(P,R), guards(F,soggy).
valid(Place,Q,P) :- setting(Place), quest(Q), prize(P), prize_at_risk(Q,P), has_foil(Q,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("zone", qid, *sorted(q.zone)[0:1]))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone", qid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for fid, f in FOILS.items():
        lines.append(asp.fact("foil", fid))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", fid, c))
        for g in sorted(f.guards):
            lines.append(asp.fact("guards", fid, g))
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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with curiosity, twist, quest, and a stegosaurus foil.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    return StoryParams(place=place, quest=quest, prize=prize, name=args.name or rng.choice(NAMES))


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place].place)
    tell(world, params.name, QUESTS[params.quest], PRIZES[params.prize])
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
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
    StoryParams(place="harbor", quest="quest", prize="treasure", name="Mina"),
    StoryParams(place="cove", quest="twist", prize="lantern", name="Pip"),
    StoryParams(place="isle", quest="curiosity", prize="hat", name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
