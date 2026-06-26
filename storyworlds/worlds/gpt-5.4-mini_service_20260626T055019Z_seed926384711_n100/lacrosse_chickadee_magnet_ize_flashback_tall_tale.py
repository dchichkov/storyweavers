#!/usr/bin/env python3
"""
A standalone story world for a tall-tale about lacrosse, a chickadee, and a
magnet-izing surprise with a flashback.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
class World:
    setting: str
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "field": "the windy field behind the school",
    "pond": "the silver pond edge",
    "barnyard": "the red barnyard lane",
}

HEROES = [
    ("boy", "Eli"),
    ("girl", "Mara"),
    ("boy", "Ned"),
    ("girl", "June"),
]

HELPERS = ["chickadee", "pint-sized chickadee", "brave little chickadee"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

@dataclass
class TaleParts:
    lacrosse_ready: bool = True
    chickadee_present: bool = True
    magnet_can_bother_net: bool = True


def valid_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.hero_type in {"boy", "girl"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/2.
valid_story(Place, HeroType) :- place(Place), hero_type(HeroType).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h, _ in HEROES:
        lines.append(asp.fact("hero_type", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, h) for p in SETTINGS for h in {"boy", "girl"}}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} valid story pairs).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - clingo:
        print("  only in Python:", sorted(py - clingo))
    if clingo - py:
        print("  only in ASP:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Core narrative simulation
# ---------------------------------------------------------------------------

def flashback_line(hero: Entity) -> str:
    return (
        f"Long before the game began, {hero.id} remembered the first time "
        f"a chickadee had landed on {hero.pronoun('possessive')} glove and "
        f"stolen a crumb right out of the air."
    )


def magnetize_lax(hero: Entity, stick: Entity, charm: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    stick.meters["magnetized"] = stick.meters.get("magnetized", 0) + 1
    charm.meters["glow"] = charm.meters.get("glow", 0) + 1


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="Chickadee", kind="character", type="chickadee", label="a chickadee"))
    stick = world.add(Entity(id="Stick", type="lacrosse stick", label="lacrosse stick"))
    ball = world.add(Entity(id="Ball", type="ball", label="bright ball", plural=False))
    magnet = world.add(Entity(id="Magnet", type="magnet", label="little barn magnet"))

    world.say(
        f"{hero.id} was a tall-tale player who could hear laughter in the grass "
        f"and could throw a lacrosse ball farther than most folks could walk."
    )
    world.say(
        f"One bright morning at {world.setting}, {hero.id} brought a lacrosse stick, "
        f"a bright ball, and a pocket full of sunflower seeds."
    )
    world.say(
        f"A tiny chickadee fluttered down and peeped, as if it had been waiting "
        f"for the whole wide morning to begin."
    )

    world.para()
    world.say(flashback_line(hero))
    world.say(
        f"That was why {hero.id} smiled at the little bird instead of shooing it away."
    )

    world.para()
    world.say(
        f"{hero.id} tossed the ball, and the wind snapped it back like a boomerang."
    )
    world.say(
        f"The chickadee hopped onto the netting and pecked at the shining fibers."
    )
    world.say(
        f"Then the barn magnet rolled out from a patch of dust and clinked to the metal end of the stick."
    )
    magnetize_lax(hero, stick, magnet)
    world.say(
        f"All at once the stick seemed to magnet-ize the air around it, and the ball wobbled nearer, as if the world had turned playful."
    )

    if stick.meters.get("magnetized", 0) >= THRESHOLD:
        world.say(
            f"{hero.id} laughed so hard {hero.pronoun('possessive')} hat nearly tipped into the grass."
        )
    if magnet.meters.get("glow", 0) >= THRESHOLD:
        world.say(
            f"The chickadee gave a tiny proud chirp, like it had planned the trick all along."
        )

    world.para()
    world.say(
        f"Instead of calling it a mess, {hero.id} set the magnet down, offered seed to the chickadee, "
        f"and used the odd little pull to gather the ball back from the weeds."
    )
    world.say(
        f"By sunset, the lacrosse stick was plain again, the chickadee was snug in the elm, "
        f"and {hero.id} was still telling anybody who would listen about the day a bird and a magnet-ize spell helped save the game."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        stick=stick,
        ball=ball,
        magnet=magnet,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a tall-tale style story about a child, a chickadee, and a lacrosse game with a surprising magnet-ize moment.",
        f"Tell a child-friendly flashback story where {hero.id} remembers an old bird moment during a lacrosse day.",
        "Make the ending feel big and silly, as if the wind, the bird, and the stick are all part of the same trick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} play lacrosse?",
            answer=f"{hero.id} played lacrosse at {place}, with wind, grass, and a very curious chickadee close by.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the chickadee in the middle of the story?",
            answer=f"{hero.id} had a flashback to the first time the chickadee had landed nearby and stolen a crumb, so the bird felt like an old friend.",
        ),
        QAItem(
            question="What strange thing happened to the lacrosse stick?",
            answer="A little barn magnet clung to the stick and made it feel magnet-ized, which pulled the play into a silly new rhythm.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the chickadee?",
            answer=f"By the end, {hero.id} shared seeds, the chickadee perched safely in the elm, and the game felt like a happy tall tale instead of trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chickadee?",
            answer="A chickadee is a small bird with a quick voice and quick feet.",
        ),
        QAItem(
            question="What is lacrosse?",
            answer="Lacrosse is a game where players use a stick with a net to carry, catch, and throw a ball.",
        ),
        QAItem(
            question="What does it mean to magnet-ize something?",
            answer="To magnet-ize something means to make it act like a magnet or seem to pull nearby things toward it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that looks back to something that happened earlier.",
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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: lacrosse, chickadee, and magnet-ize with a flashback.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.gender or rng.choice(["boy", "girl"])
    if args.name:
        name = args.name
    else:
        candidates = [n for t, n in HEROES if t == hero_type]
        name = rng.choice(candidates)
    if not valid_story(StoryParams(place=place, hero_name=name, hero_type=hero_type, helper_name="chickadee")):
        raise StoryError("Invalid story request.")
    return StoryParams(place=place, hero_name=name, hero_type=hero_type, helper_name="chickadee")


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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="field", hero_name="Eli", hero_type="boy", helper_name="chickadee"),
    StoryParams(place="pond", hero_name="Mara", hero_type="girl", helper_name="chickadee"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} valid story pairs.")
        for p, h in asp_valid_stories():
            print(p, h)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
