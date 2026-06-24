#!/usr/bin/env python3
"""
storyworlds/worlds/abs_swallow_misunderstanding_superhero_story.py
===================================================================

A small, standalone story world in a superhero style with a single core
misunderstanding: a young hero notices a swallow and mistakes what it is doing,
then learns the truth and fixes the trouble.

Seed tale idea:
---
A little superhero had very strong abs from practicing hero poses. One morning,
the hero saw a swallow swoop by the window and thought it was stealing a badge.
It turned out the swallow was only carrying a ribbon back to its nest. After a
quick misunderstanding, the hero helped untangle the ribbon and learned to look
closer before jumping to conclusions.

World model:
---
- Physical meters track things like balance, tiredness, and whether objects are
  tangled or safe.
- Emotional memes track confidence, worry, pride, and relief.
- The story begins with a hero proud of strong abs, turns on a mistaken guess
  about the swallow, and ends with help, apology, and a calm ending image.

Narrative instruments:
---
- abs: the hero's training and strength are described in the story
- swallow: the bird that causes the misunderstanding
- misunderstanding: the tension that drives the turn
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

HERO_NAMES = ["Nova", "Piper", "Milo", "Zara", "Theo", "Luna", "Kai", "Ruby"]
SIDEKICK_NAMES = ["Bean", "Dot", "Max", "Bee"]
PLACES = {
    "rooftop": "the rooftop",
    "city_park": "the city park",
    "alley_garden": "the little alley garden",
}
BADGES = {
    "star_badge": "a shiny star badge",
    "gold_badge": "a gold badge",
    "silver_badge": "a silver badge",
}
RIBBONS = {
    "red_ribbon": "a red ribbon",
    "blue_ribbon": "a blue ribbon",
    "yellow_ribbon": "a yellow ribbon",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    badge: str
    ribbon: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about abs, a swallow, and a misunderstanding.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--badge", choices=sorted(BADGES))
    ap.add_argument("--ribbon", choices=sorted(RIBBONS))
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    badge = args.badge or rng.choice(list(BADGES))
    ribbon = args.ribbon or rng.choice(list(RIBBONS))
    return StoryParams(place=place, hero_name=hero_name, sidekick_name=sidekick_name, badge=badge, ribbon=ribbon)


def _make_world(params: StoryParams) -> World:
    setting = Setting(
        place=PLACES[params.place],
        sky="bright morning",
        affords={"flyby", "message", "nesting"},
    )
    w = World(setting)
    hero = w.add(Entity(
        id="hero", kind="character", label=params.hero_name, phrase=f"a young superhero named {params.hero_name}",
        meters={"abs": 3.0, "balance": 1.0}, memes={"pride": 1.0, "care": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    sidekick = w.add(Entity(
        id="sidekick", kind="character", label=params.sidekick_name, phrase=f"the sidekick {params.sidekick_name}",
        meters={"balance": 1.0}, memes={"curiosity": 1.0},
    ))
    badge = w.add(Entity(
        id="badge", label=BADGES[params.badge], phrase=BADGES[params.badge], owner=hero.id,
        meters={"safe": 1.0}, memes={},
    ))
    ribbon = w.add(Entity(
        id="ribbon", label=RIBBONS[params.ribbon], phrase=RIBBONS[params.ribbon],
        meters={"tangled": 1.0}, memes={},
    ))
    swallow = w.add(Entity(
        id="swallow", kind="bird", label="a swallow", phrase="a quick swallow bird",
        meters={"flight": 1.0}, memes={"busy": 1.0},
    ))
    w.facts.update(hero=hero, sidekick=sidekick, badge=badge, ribbon=ribbon, swallow=swallow, params=params)
    return w


def _intro(w: World) -> None:
    h = w.get("hero")
    w.say(f"{h.label} was a young superhero with strong abs from practicing hero poses every day.")
    w.say(f"On {w.setting.place}, {h.label} liked to stand tall and feel brave under the {w.setting.sky}.")
    w.say("That morning, the air felt light and shiny, like a day that might hold a tiny adventure.")


def _misunderstanding(w: World) -> None:
    h = w.get("hero")
    s = w.get("sidekick")
    swallow = w.get("swallow")
    badge = w.get("badge")
    ribbon = w.get("ribbon")

    h.memes["worry"] += 1.0
    h.memes["pride"] += 1.0
    w.say(f"Then {h.label} saw {swallow.label} swoop past the window with {ribbon.phrase} in its beak.")
    w.say(
        f"{h.label} gasped and thought, \"That swallow is stealing {badge.phrase}!\" "
        f"{s.label} pointed and said it looked more like a bird carrying something home."
    )
    w.say(
        f"But {h.label} was so eager to be the bravest hero that {h.label} jumped to a fast misunderstanding."
    )


def _turn(w: World) -> None:
    h = w.get("hero")
    s = w.get("sidekick")
    ribbon = w.get("ribbon")
    swallow = w.get("swallow")
    badge = w.get("badge")

    w.para()
    h.memes["worry"] += 1.0
    h.meters["balance"] -= 0.5
    w.say(f"{h.label} chased after the swallow across the rooftop, but the bird was not a thief at all.")
    w.say(
        f"The swallow was trying to carry {ribbon.phrase} back to its nest, and the ribbon had snagged on a small pipe."
    )
    w.say(
        f"{s.label} called out, \"Look closer!\" so {h.label} slowed down and watched the bird's careful little hops."
    )
    w.say(
        f"At last {h.label} understood the mistake: the swallow had not stolen {badge.phrase}; it had only found a wayward ribbon."
    )
    w.facts["misunderstanding"] = True
    w.facts["badge_safe"] = True
    w.facts["ribbon_tangled"] = True
    w.facts["swallow"] = swallow


def _resolution(w: World) -> None:
    h = w.get("hero")
    s = w.get("sidekick")
    ribbon = w.get("ribbon")

    w.para()
    h.memes["worry"] = max(0.0, h.memes["worry"] - 1.0)
    h.memes["relief"] += 1.0
    h.memes["care"] += 1.0
    ribbon.meters["tangled"] = 0.0
    w.say(
        f"{h.label} gently freed the ribbon from the pipe and placed it near the nest so the swallow could reach it."
    )
    w.say(
        f"Then {h.label} smiled, took a slow breath, and promised {s.label} to look carefully before making another guess."
    )
    w.say(
        f"By the end, {h.label}'s strong abs were still ready for hero work, and the swallow was flying home safely above the rooftops."
    )


def tell(params: StoryParams) -> World:
    w = _make_world(params)
    _intro(w)
    _misunderstanding(w)
    _turn(w)
    _resolution(w)
    return w


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for badge in BADGES:
            for ribbon in RIBBONS:
                combos.append((place, badge, ribbon))
    return combos


ASP_RULES = r"""
place(rooftop;city_park;alley_garden).
badge(star_badge;gold_badge;silver_badge).
ribbon(red_ribbon;blue_ribbon;yellow_ribbon).

valid(P,B,R) :- place(P), badge(B), ribbon(R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BADGES:
        lines.append(asp.fact("badge", b))
    for r in RIBBONS:
        lines.append(asp.fact("ribbon", r))
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
    print("MISMATCH between clingo and valid_combos()")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short superhero story for a child that includes "abs" and "swallow".',
        f"Tell a gentle story about {p.hero_name}, a young superhero with strong abs, who sees a swallow and has a misunderstanding.",
        f"Write a story where {p.sidekick_name} helps {p.hero_name} notice the truth before the hero makes a big mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Why did {p.hero_name} think the swallow was causing trouble?",
            answer=f"{p.hero_name} saw the swallow carrying {RIBBONS[p.ribbon]} and wrongly guessed it was stealing {BADGES[p.badge]}. That was the misunderstanding.",
        ),
        QAItem(
            question=f"What helped {p.hero_name} calm down and understand the truth?",
            answer=f"{p.sidekick_name} told {p.hero_name} to look closer, and then the hero saw that the swallow was only carrying a ribbon back to its nest.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{p.hero_name} still had strong abs and hero courage, but now also had patience. The swallow went home safely, and the ribbon was no longer tangled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are abs?",
            answer="Abs are the muscles in the front of your belly. People can make them stronger by moving, stretching, and exercising.",
        ),
        QAItem(
            question="What is a swallow?",
            answer="A swallow is a small bird that flies fast and catches insects in the air. It often builds a nest high up and brings small things to it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true, but they are wrong because they did not see or hear all the facts.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="rooftop", hero_name="Nova", sidekick_name="Bean", badge="star_badge", ribbon="red_ribbon"),
    StoryParams(place="city_park", hero_name="Zara", sidekick_name="Dot", badge="gold_badge", ribbon="blue_ribbon"),
    StoryParams(place="alley_garden", hero_name="Milo", sidekick_name="Bee", badge="silver_badge", ribbon="yellow_ribbon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
