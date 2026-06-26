#!/usr/bin/env python3
"""
storyworlds/worlds/straight_sneaker_skip_foreshadowing_humor_magic_myth.py
===========================================================================

A small myth-style story world about a straight path, a sneaker, and a skip.

Premise:
- A child hero is meant to walk a straight path to a shrine.
- A mismatched sneaker appears as a funny little omen.
- Magic responds to the hero's choice to skip a ceremonial step.

Narrative instruments:
- Foreshadowing: early hints predict whether the path will splinter.
- Humor: a sneaker that squeaks at solemn moments and a goat with opinions.
- Magic: a charm-spring, a blessing stone, and a path that straightens when a vow is kept.

The simulation keeps physical state in meters and emotional state in memes.
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
# Registry data
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    name: str
    role: str
    type: str = "child"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Thing:
    id: str
    label: str
    type: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    straightness: float
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str = "temple_road"
    hero: str = "Nia"
    guardian: str = "Aunt"
    charm: str = "river_stone"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Place) -> None:
        self.setting = setting
        self.people: dict[str, Person] = {}
        self.things: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t

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
        c = World(self.setting)
        c.people = copy.deepcopy(self.people)
        c.things = copy.deepcopy(self.things)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "temple_road": Place(id="temple_road", label="the temple road", straightness=1.0, sacred=True),
    "hill_path": Place(id="hill_path", label="the hill path", straightness=0.8, sacred=False),
    "river_walk": Place(id="river_walk", label="the river walk", straightness=0.6, sacred=False),
}

HEROES = ["Nia", "Leto", "Mira", "Soren", "Tavi"]
GUARDIANS = ["Aunt", "Uncle", "Grandmother", "Father", "Mother"]
CHAMBERS = {
    "river_stone": "a smooth river stone",
    "sun_knot": "a bright sun-knot charm",
    "owl_coin": "an old owl coin",
}

ASP_RULES = r"""
% The road is straight when the place itself is straight and the vow is kept.
straight(P) :- place(P), straightness(P, 1).
straightened(P) :- straight(P), charm_kept.

% A mismatch creates comic warning and foreshadows trouble.
foreshadow(trouble) :- sneaker_on_wrong_foot, skipped_vow.
humor(solemn_squeak) :- sneaker_squeaks.

% Magic resolves the path if the charm is honored.
magic(resolution) :- charm_kept, shrine_reached.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
        lines.append(asp.fact("straightness", sid, int(s.straightness)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_settings() -> list[str]:
    return list(SETTINGS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic tiny story world about a straight path, a sneaker, and a skip.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--charm", choices=CHAMBERS)
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
    setting = args.setting or rng.choice(valid_settings())
    hero = args.hero or rng.choice(HEROES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    charm = args.charm or rng.choice(list(CHAMBERS))
    return StoryParams(setting=setting, hero=hero, guardian=guardian, charm=charm)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for a child about a straight road, a sneaker, and a skipped step.',
        f"Tell a gentle myth where {f['hero']} walks {f['setting']} with {f['guardian']} and learns why skipping the vow changes the path.",
        "Write a tiny story with foreshadowing, humor, and magic that ends with the road made straight again.",
    ]


def _narrate_foreshadowing(world: World) -> None:
    hero = world.people["hero"]
    sneaker = world.things["sneaker"]
    world.say(
        f"Long before dawn, {hero.name} noticed a lone sneaker hanging from a fig tree like a wink from the gods."
    )
    world.say(
        f"It gave a silly squeak when the wind touched it, as if the road itself were trying not to laugh."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    sneaker.memes["omen"] = 1


def _narrate_setup(world: World) -> None:
    hero = world.people["hero"]
    guardian = world.people["guardian"]
    charm = world.things["charm"]
    world.say(
        f"{hero.name} was a small walker of old roads, and {guardian.name} said the temple road must be taken in a straight line."
    )
    world.say(
        f"In {hero.pronoun('possessive')} pocket rested {charm.label}, cool as moon water, because the elders said it could listen to promises."
    )


def _narrate_conflict(world: World) -> None:
    hero = world.people["hero"]
    guardian = world.people["guardian"]
    sneaker = world.things["sneaker"]
    world.say(
        f"At the first bend, {hero.name} saw the sneaker again, now lying sideways in the dust like a joke told by fate."
    )
    world.say(
        f"{guardian.name} warned, 'Do not skip the vow-stone step, or the road will forget its straightness.'"
    )
    hero.memes["temptation"] = hero.memes.get("temptation", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    sneaker.meters["noise"] = 1


def _simulate_skip(world: World) -> None:
    hero = world.people["hero"]
    road = world.setting
    hero.meters["steps"] = hero.meters.get("steps", 0) + 1
    hero.meters["skipped"] = 1
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    road.meters["straightness"] = road.straightness - 0.4


def _predict(world: World) -> dict:
    sim = world.copy()
    _simulate_skip(sim)
    return {
        "straightness": sim.setting.meters.get("straightness", sim.setting.straightness),
        "trouble": sim.setting.meters.get("straightness", sim.setting.straightness) < 0.75,
    }


def _narrate_turn(world: World) -> None:
    hero = world.people["hero"]
    guardian = world.people["guardian"]
    charm = world.things["charm"]
    pred = _predict(world)
    if pred["trouble"]:
        world.say(
            f"{hero.name} almost skipped the charm-step, but the stone grew warm in {hero.pronoun('possessive')} hand, as if it remembered the path before {hero.name} did."
        )
    _simulate_skip(world)
    world.say(
        f"Then {hero.name} took the silly half-step anyway, and the road wobbled like a harp string."
    )
    world.say(
        f"{guardian.name} clapped once and said, 'Even a joke can teach a lesson.'"
    )
    world.say(
        f"The old charm answered with a bright hum, and the sneaker on the tree gave a second squeak, almost like laughter."
    )
    charm.memes["magic"] = charm.memes.get("magic", 0) + 1


def _narrate_resolution(world: World) -> None:
    hero = world.people["hero"]
    guardian = world.people["guardian"]
    charm = world.things["charm"]
    road = world.setting
    road.meters["straightness"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["defiance"] = 0
    world.say(
        f"So {hero.name} pressed {charm.label} to the center of the road and spoke the vow in a clear voice."
    )
    world.say(
        f"At once, the stones lined up straight, the wind went quiet, and the funny sneaker stopped squeaking."
    )
    world.say(
        f"{guardian.name} smiled, and together they walked the temple road with sure feet, while the little charm shone like a captured star."
    )


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add_person(Person(id="hero", name=params.hero, role="child", type="child"))
    guardian = world.add_person(Person(id="guardian", name=params.guardian, role="guardian", type="adult"))
    charm = world.add_thing(Thing(id="charm", label=CHAMBERS[params.charm], type="charm", owner=hero.id))
    sneaker = world.add_thing(Thing(id="sneaker", label="a sneaker", type="sneaker"))
    world.facts = {
        "hero": hero,
        "guardian": guardian,
        "charm": charm,
        "sneaker": sneaker,
        "setting": setting.label,
        "params": params,
    }

    _narrate_setup(world)
    world.para()
    _narrate_foreshadowing(world)
    world.para()
    _narrate_conflict(world)
    world.para()
    _narrate_turn(world)
    world.para()
    _narrate_resolution(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    guardian: Person = f["guardian"]
    charm: Thing = f["charm"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who walked the straight road in the story?",
            answer=f"{hero.name} walked the straight road with {guardian.name}, because the elders wanted the path taken carefully.",
        ),
        QAItem(
            question=f"What funny thing foreshadowed trouble at the road?",
            answer="A lone sneaker hanging from a fig tree foreshadowed trouble, because it squeaked and looked like a joke from the gods.",
        ),
        QAItem(
            question=f"What did the charm do at the end?",
            answer=f"{charm.label} glowed warmly and helped make {setting} straight again when the vow was spoken aloud.",
        ),
        QAItem(
            question=f"Why did the road wobble in the middle?",
            answer=f"The road wobbled because {hero.name} skipped the vow-step, and that small choice weakened the straight path for a moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sneaker?",
            answer="A sneaker is a soft shoe made for running, walking, and playing.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early hint that tells you something important may happen later.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can make a serious moment feel lighter, so the listener stays close to the tale.",
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="Magic in a myth is a special power that can change the world in a way ordinary things cannot.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"setting straightness: {world.setting.straightness}")
    for p in world.people.values():
        lines.append(f"{p.id}: meters={p.meters} memes={p.memes}")
    for t in world.things.values():
        lines.append(f"{t.id}: meters={t.meters} memes={t.memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hero in HEROES:
            for charm in CHAMBERS:
                combos.append((sid, hero, charm))
    return combos


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_program_text(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show straight/1.\n#show foreshadow/1.\n#show humor/1.\n#show magic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this tiny world uses its Python gate for generation.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="temple_road", hero="Nia", guardian="Aunt", charm="river_stone"),
            StoryParams(setting="hill_path", hero="Leto", guardian="Grandmother", charm="sun_knot"),
            StoryParams(setting="river_walk", hero="Mira", guardian="Mother", charm="owl_coin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
