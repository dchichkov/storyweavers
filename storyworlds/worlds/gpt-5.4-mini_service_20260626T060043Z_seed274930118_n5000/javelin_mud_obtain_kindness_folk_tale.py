#!/usr/bin/env python3
"""
Standalone storyworld: a small folk tale about a javelin, mud, and the effort
to obtain kindness.
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


@dataclass
class Place:
    id: str
    name: str
    mood: str
    has_stream: bool = False
    has_mud: bool = False


@dataclass
class Token:
    id: str
    word: str
    type: str  # treasure | tool | virtue
    held_by: Optional[str] = None
    hidden: bool = False


@dataclass
class Person:
    id: str
    name: str
    role: str
    meter: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "worry": 0.0, "kindness": 0.0})
    memories: dict[str, float] = field(default_factory=lambda: {"courage": 0.0, "shame": 0.0, "joy": 0.0})


@dataclass
class World:
    place: Place
    people: dict[str, Person] = field(default_factory=dict)
    tokens: dict[str, Token] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    helper: str
    seed: Optional[int] = None


PLACES = {
    "village": Place(id="village", name="the village green", mood="gentle", has_mud=False),
    "brook": Place(id="brook", name="the brook bank", mood="wet", has_stream=True, has_mud=True),
    "marsh": Place(id="marsh", name="the marsh path", mood="soft", has_stream=True, has_mud=True),
}

HEROES = ["Ari", "Bela", "Milo", "Nia", "Perrin", "Tala"]
HELPERS = ["Grandmother", "Old Fisher", "Kind Weaver", "Heron Keeper"]

TOKENS = {
    "javelin": Token(id="javelin", word="javelin", type="tool"),
    "mud": Token(id="mud", word="mud", type="treasure"),
    "kindness": Token(id="kindness", word="kindness", type="virtue"),
}


class FolkWorld(World):
    pass


def build_world(params: StoryParams) -> FolkWorld:
    place = PLACES[params.place]
    world = FolkWorld(place=place)
    hero = Person(id="hero", name=params.hero, role="young traveler")
    helper = Person(id="helper", name=params.helper, role="wise elder")
    world.people[hero.id] = hero
    world.people[helper.id] = helper
    for k, tok in TOKENS.items():
        world.tokens[k] = Token(**tok.__dict__)
    world.facts.update(hero=hero, helper=helper, place=place)
    return world


def tell_story(world: FolkWorld) -> None:
    hero = world.people["hero"]
    helper = world.people["helper"]
    place = world.place
    javelin = world.tokens["javelin"]
    mud = world.tokens["mud"]
    kindness = world.tokens["kindness"]

    world.say(
        f"Long ago, in {place.name}, there lived a {hero.role} named {hero.name} who loved a bright javelin."
    )
    world.say(
        f"{hero.name} had heard that a true gift was not gold, but the courage to obtain kindness when the day turned hard."
    )

    world.para()
    hero.meter["hope"] += 1
    hero.meter["worry"] += 1
    javelin.held_by = hero.id
    world.say(
        f"One morning, {hero.name} carried the javelin toward the {place.mood} path, hoping to win the old spring mud for the village games."
    )
    if place.has_mud:
        world.say(
            f"Yet the ground was slick with mud, and every step made {hero.name}'s boots sink and slip."
        )
    else:
        world.say(
            f"Yet the road beyond the green was muddy from last night's rain, and every step made {hero.name}'s boots sink and slip."
        )
    hero.meter["worry"] += 1
    hero.memories["courage"] += 1

    world.para()
    world.say(
        f"When {hero.name} nearly lost the javelin in the mud, {helper.name} came walking with a shawl and a patient smile."
    )
    world.say(
        f'"A sharp arm can win a throw," said {helper.name}, "but only a gentle heart can obtain kindness from a frightened crowd."'
    )
    helper.meter["kindness"] += 1

    world.para()
    hero.memories["shame"] += 1
    hero.meter["kindness"] += 1
    world.say(
        f"{hero.name} bowed the head and admitted the trouble. Instead of boasting, {hero.name} asked the villagers for help and offered to mend the broken fence beside the lane."
    )
    if place.has_mud:
        world.say(
            f"While the work went on, the mud stuck to their sleeves and the javelin lay safe in the grass."
        )
    else:
        world.say(
            f"While the work went on, rain-dark mud clung to their sleeves, and the javelin lay safe in the cart."
        )

    world.para()
    kindness.held_by = hero.id
    hero.memories["joy"] += 1
    hero.meter["kindness"] += 2
    world.say(
        f"The villagers saw the honest labor and gave {hero.name} the spring prize: not silver, but kindness enough to mend old quarrels."
    )
    world.say(
        f"At dusk, {hero.name} carried the javelin home clean and light, while the mud on the boots seemed like a small memory of a better day."
    )

    world.facts.update(obtained_kindness=True, javelin_safe=True, mud_present=place.has_mud)


def generation_prompts(world: FolkWorld) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    return [
        f"Write a short folk tale about {hero.name}, a javelin, and a muddy road at {place.name}.",
        f"Tell a gentle story where {hero.name} learns to obtain kindness with help from {helper.name}.",
        "Write a child-friendly folk tale that ends with a muddy problem turning into kindness.",
    ]


def story_qa(world: FolkWorld) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was the young traveler in the story?",
            answer=f"The young traveler was {hero.name}, and the tale followed {hero.name} at {place.name}.",
        ),
        QAItem(
            question="What was the hero carrying?",
            answer="The hero was carrying a bright javelin.",
        ),
        QAItem(
            question="What did the wise helper teach the hero to obtain?",
            answer=f"The wise helper taught the hero to obtain kindness, not just a prize.",
        ),
        QAItem(
            question="What made the road hard to walk on?",
            answer="The road was hard to walk on because of the mud.",
        ),
        QAItem(
            question=f"How did {hero.name} earn the villagers' good feeling?",
            answer="By admitting the trouble, asking for help, and mending the broken fence with honest work.",
        ),
    ]


def world_knowledge_qa(world: FolkWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a javelin?",
            answer="A javelin is a long, light spear used for throwing.",
        ),
        QAItem(
            question="What is mud?",
            answer="Mud is wet, soft earth that can stick to shoes and clothes.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.has_mud:
            lines.append(asp.fact("muddy_place", pid))
        if place.has_stream:
            lines.append(asp.fact("waterside", pid))
    for tid, tok in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("token_word", tid, tok.word))
    return "\n".join(lines)


ASP_RULES = r"""
has_story(P) :- muddy_place(P).
can_obtain_kindness(H) :- token(kindness), token(javelin), has_story(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.one_model(asp_program("#show has_story/1."))
    asp_places = set(asp.atoms(models, "has_story"))
    py_places = {("brook",), ("marsh",)}
    if asp_places == py_places:
        print(f"OK: ASP matches Python reasoning ({len(py_places)} muddy places).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(asp_places))
    print("PY :", sorted(py_places))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about a javelin, mud, and kindness.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if place not in ("brook", "marsh"):
        if args.place == "village":
            raise StoryError("This tale needs mud, so choose a muddy place like brook or marsh.")
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, hero=hero, helper=helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for p in sample.world.people.values():
            print(f"{p.name}: meter={p.meter} memories={p.memories}")
        for t in sample.world.tokens.values():
            print(f"{t.id}: held_by={t.held_by}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show has_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show has_story/1."))
        print(sorted(set(asp.atoms(model, "has_story"))))
        return

    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(place="brook", hero="Ari", helper="Grandmother"),
            StoryParams(place="marsh", hero="Bela", helper="Kind Weaver"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
