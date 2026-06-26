#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a clever little keeper, a dim sweet lantern,
and a path that seems to go on forever.

The tale shape is built from a short imagined source story:
- Flashback: the keeper remembers how the lantern once guided them.
- Humor: a tiny joke or silly mishap lightens the worry.
- Foreshadowing: the world hints that the lantern's missing spark matters later.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    prize: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    mood: str
    spans: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    dim: bool = False
    sweet: bool = False
    infinity: bool = False
    intelligence: bool = False


PLACES = {
    "tower": Place("tower", "the old tower", "moonlit", "the stairs"),
    "forest": Place("forest", "the pine forest", "whispery", "the path"),
    "bridge": Place("bridge", "the silver bridge", "shiny", "the river"),
}

PRIZES = {
    "lantern": Prize("lantern", "lantern", "a little lantern", dim=True, sweet=True),
    "map": Prize("map", "map", "a folded map", intelligence=True),
    "star_key": Prize("star_key", "star key", "a tiny star-shaped key", infinity=True, intelligence=True),
}

HEROES = ["Mina", "Pip", "Lila", "Nico", "Elin", "Toby", "Sora", "Milo"]
HELPERS = ["owl", "rabbit", "sparrow", "cat", "mole"]
KIND_BY_HELPER = {"owl": "bird", "rabbit": "animal", "sparrow": "bird", "cat": "animal", "mole": "animal"}

TRAITS = ["sweet", "brave", "curious", "gentle", "bright", "clever"]
HELPER_TRAITS = ["sly", "kind", "tiny", "fussy", "polite"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_risk(place: Place, prize: Prize) -> bool:
    if prize.id == "lantern":
        return place.id in {"tower", "forest", "bridge"}
    if prize.id == "map":
        return place.id == "forest"
    if prize.id == "star_key":
        return place.id == "tower"
    return False


def select_fix(place: Place, prize: Prize) -> Optional[str]:
    if prize.id == "lantern":
        return "new_wick"
    if prize.id == "map":
        return "dry_case"
    if prize.id == "star_key":
        return "moon_pouch"
    return None


def explain_rejection(place: Place, prize: Prize) -> str:
    return (
        f"(No story: {prize.label} does not have a believable problem at {place.label}, "
        f"so there is no honest turn and fix.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _flashback_line(hero: Entity, prize: Entity) -> str:
    return (
        f"{hero.id} remembered a softer day from long ago, when {hero.pronoun('possessive')} "
        f"{prize.label} had glowed like a tiny moon and the path had felt less long."
    )


def _humor_line(hero: Entity, helper: Entity) -> str:
    return (
        f"Then {helper.id} tried to look serious, but a leaf stuck to {helper.pronoun('possessive')} "
        f"nose and made {hero.id} giggle."
    )


def _foreshadow_line(prize: Entity) -> str:
    return (
        f"Still, the lantern's dim little spark trembled, as if it knew a darker step was waiting ahead."
    )


def tell(place: Place, hero_name: str, hero_kind: str, helper_name: str, helper_kind: str, prize_cfg: Prize) -> World:
    world = World(place=place.label)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_kind, label=helper_name))
    prize = world.add(Entity(id=prize_cfg.id, type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    fix = select_fix(place, prize_cfg)

    hero.memes["love"] = 1.0
    hero.memes["worry"] = 0.0
    prize.meters["shine"] = 1.0 if not prize_cfg.dim else 0.2
    if prize_cfg.dim:
        prize.meters["shine"] = 0.2

    world.say(
        f"Once upon a time, in {place.label}, there lived a sweet little {hero_kind} named {hero.id}. "
        f"{hero.id} loved {prize.phrase}, because it seemed to carry a little bit of {place.mood} wonder."
    )
    world.say(
        f"One evening, {hero.id} and {helper.id} went to {place.spans}, where the road seemed to run on toward infinity."
    )

    world.para()
    world.say(_flashback_line(hero, prize))
    world.say(_humor_line(hero, helper))
    world.say(_foreshadow_line(prize))

    hero.memes["worry"] += 1.0
    world.para()
    world.say(
        f"But when they reached the far arch, the lantern's light shrank to a dim gold dot, and {hero.id} frowned."
    )
    world.say(
        f'"If the path goes on forever," {helper.id} said, "then we had better not let the dark chew on our shoes."'
    )
    world.say(
        f"{hero.id} blinked, and even that silly line made the worry feel a little smaller."
    )

    if prize_cfg.id == "lantern":
        world.say(
            f"{hero.id} knew the old lantern needed a new wick, because a weak flame cannot guide a long road."
        )
    elif prize_cfg.id == "map":
        world.say(
            f"The folded map had begun to curl at the corners, so {hero.id} tucked it into a dry case."
        )
    else:
        world.say(
            f"The star key had to be kept in a moon pouch, or its bright edges would vanish in the dark."
        )

    world.para()
    if fix == "new_wick":
        prize.meters["shine"] = 1.0
        hero.memes["worry"] = 0.0
        world.say(
            f"{hero.id} found a new wick, and the lantern woke up with a warm little glow."
        )
        world.say(
            f"With that bright light, they crossed the long road, and the old tower looked kindly instead of huge."
        )
    elif fix == "dry_case":
        prize.meters["safe"] = 1.0
        hero.memes["worry"] = 0.0
        world.say(
            f"{hero.id} slipped the map into a dry case, and the pages stayed crisp as toast."
        )
        world.say(
            f"Then the two friends followed it home before the rain could turn the ink into puddles."
        )
    else:
        prize.meters["safe"] = 1.0
        hero.memes["worry"] = 0.0
        world.say(
            f"{hero.id} tucked the star key into a moon pouch, and it lay there like a quiet little comet."
        )
        world.say(
            f"That kept its shine safe, so they could unlock the gate and step into the last bright garden."
        )

    world.say(
        f"In the end, {hero.id} still had {prize.label}, {helper.id} still had the leaf joke, and the road no longer felt endless."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        place=place,
        fix=fix,
        risk=prize_risk(place, prize_cfg),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    place = f["place"]
    return [
        f"Write a fairy-tale story about {hero.id}, {helper.id}, and a dim {prize.label} at {place.label}.",
        f"Tell a sweet story with a flashback, a joke, and a safe fix for a problem in {place.label}.",
        f"Write a child-friendly fairy tale where a little hero keeps going toward infinity without losing a cherished thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    place = f["place"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, who goes with {helper.id} through {place.label} and tries to keep {prize.label} safe.",
        ),
        QAItem(
            question=f"What problem did the story hint at before the turn?",
            answer=f"The story hinted that {prize.label} was getting dim or fragile on the long road, so it needed help before the dark grew bigger.",
        ),
        QAItem(
            question=f"What did they do to solve the problem?",
            answer=(
                {
                    "new_wick": f"They put in a new wick so the lantern could shine again.",
                    "dry_case": f"They tucked the map into a dry case so the pages would stay safe.",
                    "moon_pouch": f"They carried the star key in a moon pouch so it would not lose its shine.",
                }[fix]
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prize = f["prize"]
    place = f["place"]
    out = [
        QAItem(
            question="What does it mean when something is dim?",
            answer="Dim means it is not very bright, like a weak lamp or a sleepy little flame.",
        ),
        QAItem(
            question="What is infinity?",
            answer="Infinity means something goes on and on without an ending that you can see.",
        ),
        QAItem(
            question="What is intelligence?",
            answer="Intelligence means being able to notice, think, and solve problems carefully.",
        ),
    ]
    if prize.sweet:
        out.append(QAItem(
            question="Why might a story call a thing sweet?",
            answer="A sweet thing feels gentle and pleasing, like a kind light or a happy memory.",
        ))
    if prize.infinity:
        out.append(QAItem(
            question="Why would a fairy tale mention infinity?",
            answer="It can make a place feel vast and magical, as if the road or sky could keep going forever.",
        ))
    out.append(QAItem(
        question=f"Why is {place.label} a good place for a fairy tale?",
        answer=f"{place.label} feels magical because it has room for wonder, long paths, and a little danger that can be solved with cleverness.",
    ))
    return out


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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.

place(tower). place(forest). place(bridge).
prize(lantern). prize(map). prize(star_key).

risk(tower, lantern).
risk(forest, lantern).
risk(bridge, lantern).
risk(forest, map).
risk(tower, star_key).

fix(lantern, new_wick).
fix(map, dry_case).
fix(star_key, moon_pouch).

valid(P, R) :- risk(P, R), fix(R, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {
        (p.id, r.id)
        for p in PLACES.values()
        for r in PRIZES.values()
        if prize_risk(p, r)
    }
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld with flashback, humor, and foreshadowing.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-kind", choices=sorted(set(KIND_BY_HELPER.values())))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    place = args.place or rng.choice(list(PLACES))
    prize_id = args.prize or rng.choice([p.id for p in PRIZES.values() if prize_risk(PLACES[place], p)])
    place_obj = PLACES[place]
    prize_obj = PRIZES[prize_id]
    if not prize_risk(place_obj, prize_obj):
        raise StoryError(explain_rejection(place_obj, prize_obj))
    hero = args.hero or rng.choice(HEROES)
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPERS)
    helper_kind = args.helper_kind or KIND_BY_HELPER[helper]
    return StoryParams(place=place, hero=hero, hero_kind=hero_kind, helper=helper, helper_kind=helper_kind, prize=prize_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero, params.hero_kind, params.helper, params.helper_kind, PRIZES[params.prize])
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
    StoryParams(place="tower", hero="Mina", hero_kind="girl", helper="owl", helper_kind="bird", prize="lantern"),
    StoryParams(place="forest", hero="Pip", hero_kind="boy", helper="rabbit", helper_kind="animal", prize="map"),
    StoryParams(place="bridge", hero="Lila", hero_kind="girl", helper="cat", helper_kind="animal", prize="star_key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid place/prize pairs:\n")
        for p, r in pairs:
            print(f"  {p:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.prize} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
