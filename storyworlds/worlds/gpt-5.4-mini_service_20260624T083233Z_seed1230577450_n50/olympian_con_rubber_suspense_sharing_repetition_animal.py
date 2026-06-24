#!/usr/bin/env python3
"""
A small Animal-Story-style world about an olympian, a con, and a rubber prize.

Premise:
A young animal athlete prepares for a big game, but a sly con artist claims
the athlete's special rubber ball is missing. The real tension is whether the
athlete can keep calm, share wisely, and notice the repeated little clues that
reveal the trick.

The storyworld uses:
- typed entities with meters and memes
- a state-driven suspense turn
- sharing as the causal resolution
- repetition as a clue pattern
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
    kind: str = "thing"
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "owl"}
        male = {"boy", "father", "dad", "man", "fox", "wolf", "lion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    features: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    material: str = "rubber"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    hero_type: str
    con_type: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _get_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _get_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def _rule_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if _get_meme(ent, "suspense") < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _set_meme(ent, "nervous", _get_meme(ent, "nervous") + 1)
        out.append(f"{ent.label} held still and listened for the next clue.")
    return out


def _rule_repetition(world: World) -> list[str]:
    out: list[str] = []
    count = 0
    for ent in world.entities.values():
        if ent.kind == "thing" and ent.type == "rubber":
            if _get_meter(ent, "bounced") >= 2:
                count += 1
    if count and ("repetition", count) not in world.fired:
        world.fired.add(("repetition", count))
        out.append("Bump, bump, bump — the rubber ball made the same little sound again.")
    return out


def _rule_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    con = world.facts.get("con")
    prize = world.facts.get("prize")
    if not hero or not con or not prize:
        return out
    if _get_meme(hero, "sharing") < THRESHOLD:
        return out
    if prize.owner == hero.id and con.meters.get("caught", 0) >= THRESHOLD:
        sig = ("sharing", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        _set_meme(hero, "calm", _get_meme(hero, "calm") + 1)
        _set_meme(con, "shame", _get_meme(con, "shame") + 1)
        out.append(f"{hero.label} chose to share the game and keep everyone together.")
    return out


CAUSAL_RULES = [_rule_suspense, _rule_repetition, _rule_sharing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "stadium": Place("stadium", "the little stadium", indoor=False, features={"crowd", "track"}),
    "field": Place("field", "the grassy field", indoor=False, features={"grass", "goal"}),
    "gym": Place("gym", "the bright gym", indoor=True, features={"floor", "bench"}),
}

PRIZES = {
    "ball": Prize("ball", "rubber ball", "a bright rubber ball", "paws", "rubber"),
    "ring": Prize("ring", "rubber ring", "a small rubber ring", "neck", "rubber"),
}

ANIMALS = {
    "fox": "fox",
    "wolf": "wolf",
    "lion": "lion",
    "hare": "hare",
    "otter": "otter",
    "rabbit": "rabbit",
    "bear": "bear",
    "owl": "owl",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for hero in ANIMALS:
            for con in ANIMALS:
                for prize in PRIZES:
                    if hero != con:
                        combos.append((place, hero, prize))
    return combos


def reasonableness_gate(place: str, hero_type: str, con_type: str, prize_id: str) -> None:
    if hero_type == con_type:
        raise StoryError("The hero and the con should be different animals.")
    if prize_id not in PRIZES:
        raise StoryError("Unknown prize.")
    if place not in PLACES:
        raise StoryError("Unknown place.")


def tell(place: Place, hero_name: str, hero_type: str, con_type: str, prize_cfg: Prize) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["young", "brave"],
    ))
    con = world.add(Entity(
        id="Con",
        kind="character",
        type=con_type,
        label=f"the sly {con_type}",
        traits=["sly", "quiet"],
    ))
    prize = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize_cfg.material,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))
    hero.memes["suspense"] = 1
    hero.memes["sharing"] = 0
    con.memes["suspense"] = 1

    world.facts.update(hero=hero, con=con, prize=prize, place=place, prize_cfg=prize_cfg)

    world.say(f"{hero.label} was a young {hero.type} who loved the little stadium.")
    world.say(f"Before the big race, {hero.pronoun('possessive')} coach had brought {hero.pronoun('object')} {prize_cfg.phrase}.")
    world.say(f"{hero.label} liked the way the rubber felt in {hero.pronoun('possessive')} paws.")
    world.para()

    world.say(f"One afternoon at {place.label}, {hero.label} noticed something strange.")
    world.say(f"The sly {con_type} kept circling the bench and saying, \"Your {prize_cfg.label} is missing, your {prize_cfg.label} is missing.\"")
    _set_meme(hero, "suspense", 1)
    _set_meme(con, "suspense", 1)
    propagate(world)
    world.say(f"{hero.label} looked and looked, but the same little clue kept turning up: a tiny rubber mark, then another, then another.")
    _set_meter(prize, "bounced", 2)
    propagate(world)

    world.para()
    world.say(f"{hero.label} stopped and took a slow breath.")
    world.say(f"Instead of rushing, {hero.label} shared the problem with the coach and with the other animals at {place.label}.")
    _set_meme(hero, "sharing", 1)
    con.meters["caught"] = 1
    propagate(world)

    world.say(f"Then the truth appeared: the sly {con_type} had hidden the {prize_cfg.label} behind the bench and hoped everybody would panic.")
    world.say(f"But nobody did. {hero.label} repeated the clue one more time, followed it, and found the bright rubber prize.")
    world.say(f"At the end, {hero.label} shared the {prize_cfg.label} with the team, and the whole crowd cheered as the rubber ball bounced safely back into the game.")
    _set_meme(hero, "joy", 1)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    prize = world.facts["prize_cfg"]
    place = world.facts["place"]
    con = world.facts["con"]
    return [
        f"Write an Animal Story about {hero.label} at {place.label} with a rubber {prize.label} and a sly {con.type}.",
        f"Tell a suspenseful story where {hero.label} keeps seeing the same clue and learns to share instead of panic.",
        f"Write a short child-friendly story about an animal olympian, a con, and a rubber prize at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    con = world.facts["con"]
    prize = world.facts["prize_cfg"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.label}, a young {hero.type} who loves the game and keeps trying to stay calm.",
        ),
        QAItem(
            question=f"What did the sly {con.type} do?",
            answer=f"The sly {con.type} kept saying the rubber {prize.label} was missing, even though it had been hidden nearby.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the problem at {place.label}?",
            answer=f"{hero.label} shared the problem with the others, followed the repeated clues, and found the {prize.label} behind the bench.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rubber?",
            answer="Rubber is a bendy material that can stretch, bounce, and make toys like balls and rings.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too, so everyone can take part.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the worried, wait-and-see feeling a story gives when something important is about to be found out.",
        ),
        QAItem(
            question="Why do repeated clues matter?",
            answer="Repeated clues matter because when the same small thing happens again and again, it can help someone notice the pattern and solve the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"place={world.place.label}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: olympian, con, rubber, suspense, sharing, repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=ANIMALS)
    ap.add_argument("--con-type", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
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
    hero_type = args.hero_type or rng.choice(list(ANIMALS))
    con_type = args.con_type or rng.choice([a for a in ANIMALS if a != hero_type])
    prize = args.prize or rng.choice(list(PRIZES))
    reasonableness_gate(place, hero_type, con_type, prize)
    name = args.name or rng.choice(["Ari", "Milo", "Pip", "Tara", "Nori", "Kito"])
    return StoryParams(place=place, name=name, hero_type=hero_type, con_type=con_type, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.name, params.hero_type, params.con_type, PRIZES[params.prize])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
place(stadium). place(field). place(gym).

animal(fox). animal(wolf). animal(lion). animal(hare). animal(otter). animal(rabbit). animal(bear). animal(owl).

prize(ball). prize(ring).
material(ball, rubber). material(ring, rubber).

valid_story(Place, Hero, Con, Prize) :-
    place(Place), animal(Hero), animal(Con), Hero != Con, prize(Prize), material(Prize, rubber).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for prize in PRIZES.values():
        lines.append(asp.fact("prize", prize.id))
        lines.append(asp.fact("material", prize.id, "rubber"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="stadium", name="Ari", hero_type="fox", con_type="wolf", prize="ball"),
    StoryParams(place="field", name="Milo", hero_type="hare", con_type="bear", prize="ring"),
    StoryParams(place="gym", name="Pip", hero_type="otter", con_type="owl", prize="ball"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
            header = f"### {p.name}: {p.hero_type} vs {p.con_type} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
