#!/usr/bin/env python3
"""
A standalone storyworld about an animal helper, a dangerous mercury spill,
and a careful moral choice that turns suspense into problem solving.

The seed tale:
---
A little raccoon named Poppy found a shiny silver bead under a broken lamp.
She wanted to poke it, but her older brother Fox said to stop, because the bead
looked like mercury and might be dangerous. Poppy felt worried and curious at
the same time. Together they fetched a grown-up, blocked the spill with a towel,
and kept the pet cat away. In the end, the room was safe again, and Poppy was
proud that she had chosen to do the right thing.

This world keeps the same core shape:
- a small animal character wants to touch or hide a strange shiny spill
- another character notices the risk and creates suspense
- a moral choice leads to careful problem solving
- the ending proves the spill was handled safely
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
    touched: bool = False
    fenced: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "raccoon", "fox", "cat", "bird", "mouse", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Creature:
    type: str
    name: str
    trait: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    prize: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


CREATURES = {
    "raccoon": Creature("raccoon", "Poppy", "curious"),
    "fox": Creature("fox", "Finn", "careful"),
    "cat": Creature("cat", "Mimi", "small"),
    "dog": Creature("dog", "Bram", "kind"),
    "mouse": Creature("mouse", "Tilly", "tiny"),
    "bird": Creature("bird", "Wren", "bright"),
}

PLACES = {
    "shed": "the garden shed",
    "kitchen": "the kitchen",
    "attic": "the attic",
    "garage": "the garage",
}

PRIZES = {
    "mercury": ObjectCfg("mercury", "mercury bead", "a shiny silver bead that looked like mercury", True),
    "glass": ObjectCfg("glass", "broken glass", "a sharp broken glass pane", True),
    "paint": ObjectCfg("paint", "paint can", "a tipped paint can", True),
}

GEAR = {
    "towel": "a thick towel",
    "box": "a cardboard box",
    "bowl": "a glass bowl",
    "rope": "a little rope barrier",
}


ASP_RULES = r"""
place(X) :- room(X).
hero(X) :- animal(X).
helper(X) :- animal(X).
prize(P) :- risk_object(P).

suspense(P) :- prize(P), risky(P).
moral_good(P) :- notices_risk(P).
problem_solving(P) :- suspense(P), moral_good(P), safe_fix(P).

valid_story(Place, Hero, Helper, Prize) :-
    room(Place), animal(Hero), animal(Helper), risk_object(Prize),
    Hero != Helper, risky(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("room", p))
    for k, c in CREATURES.items():
        lines.append(asp.fact("animal", k))
        lines.append(asp.fact("creature", k, c.name))
    for p in PRIZES:
        lines.append(asp.fact("risk_object", p))
        lines.append(asp.fact("risky", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: mercy, suspense, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=CREATURES)
    ap.add_argument("--helper", choices=CREATURES)
    ap.add_argument("--prize", choices=PRIZES)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(CREATURES))
    helper = args.helper or rng.choice([k for k in CREATURES if k != hero])
    prize = args.prize or rng.choice(list(PRIZES))
    if hero == helper:
        raise StoryError("The helper must be a different animal from the hero.")
    return StoryParams(place=place, hero=hero, helper=helper, prize=prize)


def _story_setup(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked exploring {world.place}.")
    world.say(f"{helper.id} was a careful {helper.type} who watched out for little dangers.")
    world.say(f"One day, {hero.id} found {prize.phrase} near a broken lamp.")
    world.say(f"It glimmered so brightly that {hero.id} wanted to touch it at once.")


def _story_turn(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["wanting"] = 1
    helper.memes["warning"] = 1
    world.para()
    world.say(f"Then {helper.id} saw the shiny bead and froze.")
    world.say(f'"Stop," {helper.id} said. "That might be mercury, and we should not mangle the room by touching it."')
    world.say(f"{hero.id} felt a twist of suspense in {hero.id}'s tummy, because the bead looked harmless but might not be.")
    hero.memes["worry"] = 1
    helper.memes["moral"] = 1


def _story_solution(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.para()
    world.say(f"Instead of touching it, {hero.id} chose the safe thing and listened.")
    world.say(f"{helper.id} fetched {GEAR['towel']} to block the spill, then hurried to get a grown-up.")
    world.say(f"They kept the cat away, because tiny paws should not go near mercury.")
    world.say(f"The grown-up cleaned the spill carefully, and soon the room was safe again.")
    world.say(f"In the end, {hero.id} felt proud for helping with the problem instead of making it worse.")
    hero.memes["pride"] = 1
    helper.memes["relief"] = 1
    prize.touched = False


def tell(place: str, hero_key: str, helper_key: str, prize_key: str) -> World:
    world = World(PLACES[place])
    hero_cfg = CREATURES[hero_key]
    helper_cfg = CREATURES[helper_key]
    prize_cfg = PRIZES[prize_key]

    hero = world.add(Entity(id=hero_cfg.name, kind="character", type=hero_cfg.type))
    helper = world.add(Entity(id=helper_cfg.name, kind="character", type=helper_cfg.type))
    prize = world.add(Entity(id=prize_cfg.id, kind="thing", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=helper.id))

    world.facts.update(place=place, hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg)
    _story_setup(world, hero, helper, prize)
    _story_turn(world, hero, helper, prize)
    _story_solution(world, hero, helper, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize_cfg: ObjectCfg = f["prize_cfg"]
    return [
        f"Write a short animal story about {hero.id} finding {prize_cfg.label} and learning to be careful.",
        f"Tell a gentle story where {helper.id} warns {hero.id} about mercury and they solve the problem together.",
        f"Write a child-friendly story with suspense, moral choice, and problem solving in {world.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"Who found the shiny thing in {world.place}?",
            answer=f"{hero.id} found {prize.phrase} in {world.place}.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {hero.id} not to touch it?",
            answer=f"{helper.id} thought it might be mercury, so touching it could be dangerous.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They blocked the spill with a towel, kept the cat away, and got a grown-up to clean it safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mercury?",
            answer="Mercury is a shiny silver metal that can be dangerous, so people should not touch it with bare hands.",
        ),
        QAItem(
            question="What should you do if you see a strange spill?",
            answer="You should stay away, tell a grown-up, and let an adult handle it safely.",
        ),
        QAItem(
            question="Why is a towel useful in an emergency?",
            answer="A towel can help block a spill or keep people from getting too close while help is coming.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero, params.helper, params.prize)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in CREATURES:
            for helper in CREATURES:
                if helper == hero:
                    continue
                for prize in PRIZES:
                    combos.append((place, hero, helper, prize))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            hero, helper, prize = "raccoon", "fox", "mercury"
            params = StoryParams(place=place, hero=hero, helper=helper, prize=prize, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
