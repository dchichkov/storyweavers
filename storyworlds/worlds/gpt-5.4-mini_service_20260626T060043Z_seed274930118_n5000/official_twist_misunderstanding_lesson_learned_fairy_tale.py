#!/usr/bin/env python3
"""
A fairy-tale storyworld about an official village task, a misunderstanding, a
twist, and a lesson learned.

The domain is intentionally small and classical:
- a village helper receives an official request,
- a mistaken clue leads to a wrong assumption,
- the twist reveals the true need,
- the lesson learned changes what the characters choose to do.

Stories are built from a live world model with physical meters and emotional
memes, and the prose is driven by simulated state rather than a frozen template.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Town:
    place: str
    official_task: str
    misunderstanding: str
    twist: str
    lesson: str
    clue: str
    reward: str
    warning: str


@dataclass
class World:
    town: Town
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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    task: str
    clue: str
    twist: str
    lesson: str
    reward: str
    seed: Optional[int] = None


PLACES = {
    "castle": Town(
        place="the castle gate",
        official_task="deliver the official royal banner",
        misunderstanding="the torn ribbon must mean someone was rude",
        twist="the ribbon was torn by a windy branch, not by any mischief",
        lesson="it is wise to ask before guessing",
        clue="a ribbon caught on a rosebush",
        reward="a silver thank-you coin",
        warning="Do not blame a friend before you know the truth.",
    ),
    "mill": Town(
        place="the old mill",
        official_task="carry the official flour sack",
        misunderstanding="the dusty floor must mean the miller was careless",
        twist="the flour sack split because a mouse nibbled the corner",
        lesson="a small clue can hide a bigger cause",
        clue="tiny teeth marks on the sack",
        reward="a warm loaf of bread",
        warning="Look closely before you speak too fast.",
    ),
    "harbor": Town(
        place="the harbor",
        official_task="bring the official lantern to the dock",
        misunderstanding="the dark water must mean the lantern was already lost",
        twist="the lantern was safe; the fog had only made the harbor look dim",
        lesson="not every shadow is trouble",
        clue="fog curled over the stones",
        reward="a pearl pin",
        warning="A gloomy look is not always a gloomy truth.",
    ),
}

HEROES = ["Mira", "Tobin", "Elsa", "Nico", "Lina", "Rowan", "Pippa", "Galen"]
HELPERS = ["baker", "miller", "gardener", "harbor master", "tailor", "keeper"]
TRAITS = ["kind", "careful", "curious", "brave", "patient", "gentle"]


class ReasoningGate:
    @staticmethod
    def valid_town(town: Town) -> bool:
        return bool(town.place and town.official_task and town.clue and town.twist and town.lesson)

    @staticmethod
    def compatible(params: StoryParams) -> bool:
        if params.hero == params.helper:
            return False
        if not params.task or not params.clue or not params.twist or not params.lesson:
            return False
        return True


ASP_RULES = r"""
place_ok(P) :- town(P).
story_ok(P,H,A) :- place_ok(P), hero(H), helper(A), H != A.
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, town in PLACES.items():
        lines.append(asp.fact("town", key))
        if town.place:
            lines.append(asp.fact("has_place", key, town.place))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show story_ok/3."))
    atoms = set(asp.atoms(model, "story_ok"))
    py = {(p, h, a) for p in PLACES for h in HEROES for a in HELPERS if h != a}
    if atoms == py:
        print(f"OK: ASP parity matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if atoms - py:
        print("  only in ASP:", sorted(atoms - py))
    if py - atoms:
        print("  only in Python:", sorted(py - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld with an official task, misunderstanding, twist, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["baker", "miller", "gardener", "harbor master", "tailor", "keeper"])
    ap.add_argument("--task")
    ap.add_argument("--clue")
    ap.add_argument("--twist")
    ap.add_argument("--lesson")
    ap.add_argument("--reward")
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
    places = [args.place] if args.place else list(PLACES)
    place_key = args.place or rng.choice(places)
    town = PLACES[place_key]

    if args.task and args.task != town.official_task:
        raise StoryError("The chosen task does not match this town's official request.")
    if args.clue and args.clue != town.clue:
        raise StoryError("The chosen clue does not fit the town's misunderstanding.")
    if args.twist and args.twist != town.twist:
        raise StoryError("The chosen twist does not fit the town's true cause.")
    if args.lesson and args.lesson != town.lesson:
        raise StoryError("The chosen lesson does not fit this fairy tale.")
    if args.reward and args.reward != town.reward:
        raise StoryError("The chosen reward does not match this town.")

    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HEROES if h != hero])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPERS)

    return StoryParams(
        place=place_key,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        task=town.official_task,
        clue=town.clue,
        twist=town.twist,
        lesson=town.lesson,
        reward=town.reward,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    town = PLACES[params.place]
    if not ReasoningGate.valid_town(town) or not ReasoningGate.compatible(params):
        raise StoryError("Invalid story parameters.")

    world = World(town=town)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, meters={"hope": 1.0}, memes={"curiosity": 1.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, meters={"duty": 1.0}, memes={"worry": 1.0}))
    official = world.add(Entity(id="official_request", type="scroll", label="official request", phrase=town.official_task))
    clue = world.add(Entity(id="clue", type="thing", label="clue", phrase=town.clue))

    world.say(f"Once, in a small village by {town.place}, there came an official request for {town.official_task}.")
    world.say(f"{hero.id} was a {params.hero_type} who wanted to help, and {hero.pronoun().capitalize()} carried the official notice with great care.")
    world.say(f"At the same time, {helper.id} the {params.helper_type} watched the road and hoped the day would stay calm.")

    world.para()
    world.say(f"But {hero.id} saw {town.clue} and thought that {town.misunderstanding}.")
    hero.memes["confusion"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(f"So {hero.id} hurried to {town.place} with a worried heart, certain the wrongness had already begun.")

    world.para()
    world.say(f"Then came the twist: {town.twist}.")
    hero.meters["understanding"] = 1.0
    hero.memes["shame"] = 0.5
    helper.memes["relief"] = 1.0
    world.say(f"{hero.id} paused, looked again, and realized {town.warning.lower()}")

    world.para()
    world.say(f"{hero.id} apologized, and {helper.id} smiled kindly instead of scolding.")
    hero.memes["gratitude"] = 1.0
    helper.memes["love"] = 1.0
    world.say(f"Together they finished the official task, and the village gave them {town.reward}.")
    world.say(f"By evening, {hero.id} remembered the lesson learned: {town.lesson}.")

    world.facts.update(
        hero=hero,
        helper=helper,
        town=town,
        official=official,
        clue_entity=clue,
        params=params,
    )

    prompts = [
        f'Write a fairy tale with an official request, a misunderstanding, a twist, and a lesson learned using the word "official".',
        f"Tell a short story where {params.hero} helps with an official task but first makes a mistake about {town.clue}.",
        f"Create a gentle fairy tale about {params.hero} and {params.helper} that ends with {town.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"What official task was the village asking for?",
            answer=f"The village was asking for {town.official_task}.",
        ),
        QAItem(
            question=f"What did {params.hero} misunderstand at first?",
            answer=f"{params.hero} misunderstood {town.clue} and thought that {town.misunderstanding}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {town.twist}.",
        ),
        QAItem(
            question=f"What lesson did {params.hero} learn?",
            answer=f"{params.hero} learned that {town.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does 'official' mean?",
            answer="Official means something is connected to a person or message that has authority, like a king, queen, mayor, or other trusted office.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they do not have the right idea yet.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful idea a character remembers after something happens, so they can do better next time.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:16} {e.type:12} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="castle",
        hero="Mira",
        hero_type="girl",
        helper="Bram",
        helper_type="keeper",
        task=PLACES["castle"].official_task,
        clue=PLACES["castle"].clue,
        twist=PLACES["castle"].twist,
        lesson=PLACES["castle"].lesson,
        reward=PLACES["castle"].reward,
    ),
    StoryParams(
        place="mill",
        hero="Tobin",
        hero_type="boy",
        helper="Nell",
        helper_type="miller",
        task=PLACES["mill"].official_task,
        clue=PLACES["mill"].clue,
        twist=PLACES["mill"].twist,
        lesson=PLACES["mill"].lesson,
        reward=PLACES["mill"].reward,
    ),
    StoryParams(
        place="harbor",
        hero="Elsa",
        hero_type="girl",
        helper="Roan",
        helper_type="harbor master",
        task=PLACES["harbor"].official_task,
        clue=PLACES["harbor"].clue,
        twist=PLACES["harbor"].twist,
        lesson=PLACES["harbor"].lesson,
        reward=PLACES["harbor"].reward,
    ),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
