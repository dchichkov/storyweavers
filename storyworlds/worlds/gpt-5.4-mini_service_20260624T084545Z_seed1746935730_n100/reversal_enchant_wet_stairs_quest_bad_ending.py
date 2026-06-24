#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a quest on wet stairs, where a little
reversal and an enchantment lead to a bad ending.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "wet stairs"
    hero: str = "Mina"
    hero_type: str = "girl"
    guide: str = "Grandma"
    guide_type: str = "woman"
    prize: str = "silver key"
    seed: Optional[int] = None


PLACES = {
    "wet stairs": {
        "detail": "The wet stairs shone like ribbons after the rain.",
        "risk": "slipping",
    },
}

HEROES = [("Mina", "girl"), ("Toby", "boy"), ("Lila", "girl"), ("Nico", "boy")]
GUIDES = [("Grandma", "woman"), ("Papa", "man"), ("Mom", "woman"), ("Dad", "man")]
PRIZES = [
    ("silver key", "key"),
    ("little bell", "bell"),
    ("golden spoon", "spoon"),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is bad when the stairs are wet and the traveler is not steady.
bad_ending(H) :- hero(H), on_wet_stairs, quest(H), not steady(H).

% Reversal enchantment flips the path and makes the prize harder to reach.
reversed(H) :- enchanted(H), quest(H), on_wet_stairs.

% A helpful ending would require steadiness and an unlocked route.
good_end(H) :- quest(H), steady(H), not reversed(H).

% We only show bad endings in this tiny world.
shown_bad(H) :- bad_ending(H).
#show shown_bad/1.
#show reversed/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("on_wet_stairs"),
    ]
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_bad_ending() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "shown_bad"))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(place=params.place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide))
    prize = world.add(Entity(id="prize", type="thing", label=params.prize, phrase=f"the {params.prize}"))
    world.facts.update(hero=hero, guide=guide, prize=prize)
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    prize: Entity = world.facts["prize"]

    world.say(f"On the wet stairs, little {hero.label} began a quest.")
    world.say(f"{hero.pronoun().capitalize()} wanted {prize.phrase}, for it glittered at the top step.")
    world.para()
    world.say("But the rain had made the stairs slick and sly.")
    world.say(f"{guide.label} warned, \"Soft steps, soft steps, and hold the rail close.\"")
    hero.memes["hope"] = 1
    hero.memes["brave"] = 1
    world.say(f"Yet a strange reversal enchant had been whispered in the air.")
    world.say(f"It turned the safe way back to front, and {hero.label} took the wrong turn.")
    world.para()
    hero.meters["slip"] = 1
    hero.memes["fear"] = 1
    world.say(f"{hero.label} slipped one step, then two, with a tiny yelp in the rain.")
    world.say(f"The prize rolled away, and the quest went sadly wrong.")
    world.say(f"{guide.label} caught {hero.pronoun('object')} at the rail, but the bell could not be reached.")
    world.say(f"So the night ended with wet hems, a lost prize, and a bad ending on the stairs.")
    world.facts["bad"] = True
    world.facts["reversal"] = True
    world.facts["enchant"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme style story about a quest on wet stairs with a reversal enchant and a bad ending.',
        'Tell a short rhyme where a child climbs wet stairs, hears a warning, and the magic goes wrong.',
        'Write a gentle story with the words "reversal" and "enchant" that ends sadly on wet stairs.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    prize: Entity = world.facts["prize"]
    return [
        QAItem(
            question=f"Who went on the quest on the wet stairs?",
            answer=f"Little {hero.label} went on the quest on the wet stairs.",
        ),
        QAItem(
            question=f"What did {guide.label} warn {hero.label} about?",
            answer=f"{guide.label} warned {hero.label} to take soft steps and hold the rail close because the stairs were wet.",
        ),
        QAItem(
            question=f"What went wrong in the middle of the story?",
            answer=f"A reversal enchant made {hero.label} take the wrong turn, so the quest went badly and the {prize.label} rolled away.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with a bad ending: wet hems, a lost prize, and no happy climb to the top.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are wet stairs like?",
            answer="Wet stairs can be slippery, so people need to walk carefully and hold the rail.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important.",
        ),
        QAItem(
            question="What does an enchantment do in a fairy-tale story?",
            answer="An enchantment is magic that can change what happens, sometimes in a surprising way.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a story or poem with sounds that match at the ends of words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness / generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "wet stairs":
        raise StoryError("This world only supports the wet stairs setting.")
    hero, hero_type = (args.hero, args.hero_type) if args.hero else rng.choice(HEROES)
    guide, guide_type = (args.guide, args.guide_type) if args.guide else rng.choice(GUIDES)
    prize = args.prize or rng.choice([p[0] for p in PRIZES])
    return StoryParams(place="wet stairs", hero=hero, hero_type=hero_type, guide=guide, guide_type=guide_type, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    py = True
    asp_ok = asp_bad_ending()
    if py == asp_ok:
        print("OK: ASP and Python both agree on the bad ending.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld on wet stairs.")
    ap.add_argument("--place", choices=["wet stairs"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=["woman", "man"])
    ap.add_argument("--prize", choices=[p[0] for p in PRIZES])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="wet stairs", hero="Mina", hero_type="girl", guide="Grandma", guide_type="woman", prize="silver key"),
            StoryParams(place="wet stairs", hero="Toby", hero_type="boy", guide="Dad", guide_type="man", prize="little bell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        shown = asp.atoms(model, "shown_bad")
        print(f"{len(shown)} bad-ending model(s)")
        for atom in shown:
            print(atom)
        return

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
