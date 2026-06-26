#!/usr/bin/env python3
"""
A small superhero story world about a surprise, an inner monologue, and a rhyme.

Seed premise:
A young hero wants to save the day with a cheesy surprise, but the surprise
keeps getting complicated until the hero chooses a clever, kind ending.

This world simulates:
- a hero, a helper, a surprise gift, and a small place to hide it
- physical state in meters (hidden, ready, safe, ruined)
- emotional state in memes (worry, hope, pride, relief)
- a tiny causal chain that turns a surprise plan into a happy reveal

The featured word is "gruyere".
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Place:
    name: str
    indoor: bool = True
    hides_well: bool = True
    smells: str = "warm and quiet"


@dataclass
class SurprisePlan:
    label: str
    gift: str
    rhyme_word: str
    hiding_spot: str
    reveal_spot: str
    helper_label: str
    danger: str
    fix: str


@dataclass
class StoryParams:
    place: str = "kitchen"
    hero_name: str = "Nova"
    helper_name: str = "Milo"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "kitchen": Place(name="the kitchen", indoor=True, hides_well=True, smells="buttery and calm"),
    "roof": Place(name="the moonlit roof", indoor=False, hides_well=False, smells="cool and windy"),
    "hideout": Place(name="the secret hideout", indoor=True, hides_well=True, smells="dusty and safe"),
}

PLANS = [
    SurprisePlan(
        label="a surprise snack",
        gift="gruyere",
        rhyme_word="cheese",
        hiding_spot="behind the blue crate",
        reveal_spot="the center table",
        helper_label="the helper",
        danger="the cheese could be found too soon",
        fix="move it into a cooler tin",
    ),
    SurprisePlan(
        label="a surprise badge toast",
        gift="gruyere",
        rhyme_word="squeak",
        hiding_spot="under the red cape",
        reveal_spot="the trophy stand",
        helper_label="the helper",
        danger="the cheese might get warm and soft",
        fix="wrap it in a neat paper pouch",
    ),
]


HEROES = ["Nova", "Flash", "Mira", "Bolt", "Pip", "Comet"]
HELPERS = ["Milo", "Tess", "June", "Rex", "Ivy", "Zane"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a cheesy surprise.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(PLACES.keys()))
    name = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if name == helper:
        helper = rng.choice([h for h in HELPERS if h != name])
    return StoryParams(place=place, hero_name=name, helper_name=helper)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That place does not exist in this story world.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")


ASP_RULES = r"""
place(kitchen). place(roof). place(hideout).

surprise_plan(kitchen, snack). surprise_plan(roof, toast). surprise_plan(hideout, snack).

valid(P) :- place(P), surprise_plan(P, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p, plan in zip(PLACES.keys(), PLANS):
        lines.append(asp.fact("surprise_plan", p, plan.label.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, SurprisePlan]:
    place = PLACES[params.place]
    plan = random.Random((params.seed or 0) ^ 0xA5A5).choice(PLANS)
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper", label=params.helper_name))
    gift = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=f"gruyere",
            phrase="a little wheel of gruyere",
            owner=hero.id,
            caretaker=helper.id,
        )
    )
    return world, hero, helper, gift, plan


def _narrate_begin(world: World, hero: Entity, helper: Entity, gift: Entity, plan: SurprisePlan) -> None:
    world.say(
        f"{hero.id} was a small superhero with a bright cape and a big secret."
    )
    world.say(
        f"That day, {hero.id} and {helper.id} had a plan for {plan.label}: a surprise with {gift.label}."
    )
    world.say(
        f"{hero.id} tucked the {gift.label} away so the surprise would stay hidden."
    )


def _narrate_turn(world: World, hero: Entity, helper: Entity, gift: Entity, plan: SurprisePlan) -> None:
    hero.memes["worry"] = hero.meme("worry") + 1
    hero.memes["hope"] = hero.meme("hope") + 1
    world.say(
        f"But then {hero.id} frowned a little. {hero.id} thought, "
        f'"What if the surprise is found too soon?"'
    )
    world.say(
        f"The {gift.label} sat {plan.hiding_spot}, and that made the secret feel extra fragile."
    )
    world.say(
        f"{helper.id} noticed the wobble in {hero.id}'s face and leaned in close."
    )
    world.say(
        f'"We can make it safer," {helper.id} said, because a good surprise needs a good hide.'
    )
    gift.meters["hidden"] = 1
    gift.meters["safe"] = 1


def _narrate_rhyme(world: World, hero: Entity, helper: Entity, gift: Entity, plan: SurprisePlan) -> None:
    world.say(
        f"{hero.id} took a breath and thought, "
        f'"A hero can pause, then fix the cause."'
    )
    world.say(
        f"Then {hero.id} smiled and answered with a rhyme: "
        f'"No loud parade, no noisy scene, just gruyere kept cool and clean."'
    )
    world.say(
        f"{helper.id} packed the cheese into {plan.fix}, and the secret felt steady again."
    )
    gift.meters["safe"] = gift.meter("safe") + 1
    gift.memes["pride"] = gift.meme("pride") + 1
    hero.memes["relief"] = hero.meme("relief") + 1


def _narrate_reveal(world: World, hero: Entity, helper: Entity, gift: Entity, plan: SurprisePlan) -> None:
    world.say(
        f"At last, they carried the surprise to {plan.reveal_spot}."
    )
    world.say(
        f"When the time was right, {hero.id} opened the lid, and the gruyere surprise sparkled like treasure."
    )
    world.say(
        f"{hero.id} stood tall in the cape, {helper.id} grinning nearby, and the whole secret turned into a happy cheer."
    )
    gift.meters["revealed"] = 1
    gift.memes["joy"] = 1
    hero.memes["pride"] = hero.meme("pride") + 1


def tell_story(params: StoryParams) -> World:
    world, hero, helper, gift, plan = _setup_world(params)
    _narrate_begin(world, hero, helper, gift, plan)
    world.say("")
    _narrate_turn(world, hero, helper, gift, plan)
    world.say("")
    _narrate_rhyme(world, hero, helper, gift, plan)
    world.say("")
    _narrate_reveal(world, hero, helper, gift, plan)

    world.facts.update(
        hero=hero,
        helper=helper,
        gift=gift,
        plan=plan,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    plan: SurprisePlan = f["plan"]
    return [
        'Write a superhero story for a small child that includes a surprise and the word "gruyere".',
        f"Tell a gentle story where {hero.id} and {helper.id} protect a cheesy surprise and the hero thinks carefully before acting.",
        f"Write a short, rhyming superhero story ending with gruyere being revealed as a happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    plan: SurprisePlan = f["plan"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was a little {gift.label} treat that the hero and {helper.id} wanted to keep hidden until the right moment.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the surprise?",
            answer=f"{hero.id} worried that the surprise might be found too soon, so the secret would not stay special.",
        ),
        QAItem(
            question=f"How did the hero fix the problem?",
            answer=f"{hero.id} thought carefully, then {helper.id} helped {world.place.name if False else ''}".strip(),
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    plan: SurprisePlan = f["plan"]
    place: Place = f["place"]
    return [
        QAItem(
            question="What was the surprise in the story?",
            answer=f"The surprise was a little {gift.label} treat that {hero.id} and {helper.id} wanted to keep hidden until the right moment.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the surprise?",
            answer=f"{hero.id} worried that the surprise might be found too soon, so the secret would not stay special.",
        ),
        QAItem(
            question="How did the hero fix the problem?",
            answer=f"{hero.id} listened to the worried feeling, then {helper.id} helped move the gruyere into a safer container so the surprise could wait.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the gruyere surprise being revealed at {plan.reveal_spot}, and everyone felt happy and proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gruyere?",
            answer="Gruyere is a kind of cheese. It can be cut, wrapped, and served as food.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something kept hidden for a little while so someone can discover it later.",
        ),
        QAItem(
            question="Why do superheroes pause and think?",
            answer="A superhero may pause and think so they can choose a kind, safe, and clever plan instead of rushing in.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind}, type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% A place is valid when the world can hold a surprise there.
valid_place(P) :- place(P).

% A gruyere surprise is valid in any listed place, but the story still uses
% the place's mood to choose a safe reveal.
valid_story(P) :- valid_place(P).
"""


def asp_facts_text() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in PLANS:
        lines.append(asp.fact("surprise", p.label.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts_text()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_place/1."))
    asp_places = sorted(set(asp.atoms(model, "valid_place")))
    py_places = sorted((p,) for p in PLACES.keys())
    if asp_places != py_places:
        print("MISMATCH between ASP and Python.")
        print("ASP:", asp_places)
        print("PY :", py_places)
        return 1
    print(f"OK: ASP and Python agree on {len(py_places)} valid places.")
    sample = generate(StoryParams(place="kitchen", hero_name="Nova", helper_name="Milo", seed=1))
    if "gruyere" not in sample.story.lower():
        print("Verification failed: generated story did not mention gruyere.")
        return 1
    print("OK: generated story mentions gruyere.")
    return 0


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return

    if args.asp:
        try:
            import asp
        except Exception as err:
            raise SystemExit(f"ASP unavailable: {err}")
        model = asp.one_model(asp_program("#show valid_place/1."))
        places = sorted(set(asp.atoms(model, "valid_place")))
        for p in places:
            print(p[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(place=place, hero_name=HEROES[i % len(HEROES)], helper_name=HELPERS[i % len(HELPERS)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
