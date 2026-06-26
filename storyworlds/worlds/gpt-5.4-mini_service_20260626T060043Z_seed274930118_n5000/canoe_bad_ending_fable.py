#!/usr/bin/env python3
"""
storyworlds/worlds/canoe_bad_ending_fable.py
=============================================

A small fable-style storyworld about a canoe trip that goes wrong.

Seed tale:
---
A little rabbit found a canoe by the river and wanted to ride it to the far bank.
A careful heron warned that the river was fast and the canoe was old. The rabbit
laughed, climbed in anyway, and pushed off. The canoe scraped a rock, filled
with water, and tipped over. The rabbit lost the basket of clover and crawled
home cold and embarrassed.

This world keeps the fable shape: a simple desire, a warning, a stubborn choice,
a bad ending, and a short moral.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "fox", "wolf", "badger", "otter"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"heron", "crow", "owl"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    current: str
    has_reeds: bool = False
    has_rocks: bool = False


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    danger: str
    needed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    goal: str
    prize: str
    hero: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


def _warn_about_river(world: World) -> list[str]:
    hero = world.get("hero")
    guide = world.get("guide")
    goal = world.facts["goal"]
    if hero.memes.get("impulse", 0.0) < THRESHOLD:
        return []
    sig = ("warned", hero.id, goal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    return [f'"{goal.risk}," said {guide.label}. "{goal.danger}."']


def _damage_canoe(world: World) -> list[str]:
    hero = world.get("hero")
    canoe = world.get("canoe")
    goal = world.facts["goal"]
    setting = world.setting
    if hero.meters.get("determined", 0.0) < THRESHOLD:
        return []
    if canoe.meters.get("launched", 0.0) < THRESHOLD:
        return []
    sig = ("damage", canoe.id, goal.id)
    if sig in world.fired:
        return []
    if setting.current == "fast" and setting.has_rocks:
        world.fired.add(sig)
        canoe.meters["scraped"] = canoe.meters.get("scraped", 0.0) + 1
        canoe.meters["leaky"] = canoe.meters.get("leaky", 0.0) + 1
        hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1
        return [f"The canoe scraped a hidden rock and began to leak."]
    return []


def _tip_boat(world: World) -> list[str]:
    hero = world.get("hero")
    canoe = world.get("canoe")
    prize = world.facts["prize"]
    if canoe.meters.get("leaky", 0.0) < THRESHOLD:
        return []
    sig = ("tip", canoe.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    prize.meters["lost"] = prize.meters.get("lost", 0.0) + 1
    return [
        f"Water rushed in, the canoe tipped, and {hero.id} dropped {prize.phrase} into the river."
    ]


RULES = [
    ("warn", _warn_about_river),
    ("damage", _damage_canoe),
    ("tip", _tip_boat),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup_text(hero: Entity, guide: Entity, prize: Entity, setting: Setting) -> list[str]:
    return [
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who loved the river.",
        f"Near {setting.place}, {hero.id} found an old canoe and longed to cross the water.",
        f"{hero.id} had brought {prize.phrase}, hoping to keep {prize.it()} safe on the trip.",
        f"{guide.label.capitalize()} watched the current and looked worried.",
    ]


def do_story(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    canoe = world.get("canoe")
    prize = world.get("prize")
    goal = world.facts["goal"]

    for line in setup_text(hero, guide, prize, world.setting):
        world.say(line)

    world.para()
    world.say(f"{hero.id} wanted to {goal.verb}, but the river was not kind.")
    world.say(f"The current pulled hard, and {guide.label} warned, \"{goal.risk} {goal.danger}.\"")

    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    world.say(f"Still, {hero.id} climbed into the canoe and pushed off.")
    canoe.meters["launched"] = canoe.meters.get("launched", 0.0) + 1
    hero.meters["determined"] = hero.meters.get("determined", 0.0) + 1

    propagate(world, narrate=True)

    world.para()
    if prize.meters.get("lost", 0.0) >= THRESHOLD:
        world.say(
            f"When the river finally calmed, {hero.id} was shivering on the bank, "
            f"the canoe was broken and wet, and the basket was gone."
        )
        world.say(
            f"{guide.label} gently helped {hero.id} crawl home, and {hero.id} "
            f"learned that a fast river does not care about a stubborn wish."
        )
    else:
        world.say(
            f"When the river finally calmed, {hero.id} was still safe, but the day "
            f"had turned gray and sad."
        )
    world.para()
    world.say(f"Moral: A wise traveler listens before the river teaches the hard way.")


SETTINGS = {
    "riverbank": Setting(place="the riverbank", current="fast", has_reeds=True, has_rocks=True),
    "bend": Setting(place="the river bend", current="fast", has_reeds=False, has_rocks=True),
    "marsh": Setting(place="the marsh edge", current="slow", has_reeds=True, has_rocks=False),
}

GOALS = {
    "cross": Goal(
        id="cross",
        verb="cross the river",
        gerund="crossing the river",
        rush="push the canoe into the water",
        risk="The water is moving too fast",
        danger="the canoe could scrape a rock and leak",
        needed="canoe",
        tags={"river", "canoe"},
    ),
    "collect_reeds": Goal(
        id="collect_reeds",
        verb="gather reeds across the water",
        gerund="gathering reeds",
        rush="paddle toward the far reeds",
        risk="the reeds are tempting but the channel is narrow",
        danger="the canoe could snag and tip",
        needed="canoe",
        tags={"river", "reeds", "canoe"},
    ),
}

PRIZES = {
    "clover": Prize(id="clover", label="clover", phrase="a basket of clover", region="lap"),
    "berries": Prize(id="berries", label="berries", phrase="a small basket of berries", region="lap", plural=True),
}

HEROES = {
    "rabbit": ("rabbit", ["small", "stubborn"]),
    "hare": ("hare", ["quick", "proud"]),
    "otter": ("otter", ["bright-eyed", "restless"]),
}

GUIDES = {
    "heron": "Heron",
    "crow": "Crow",
    "owl": "Owl",
}


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((p, g, pr) for p in SETTINGS for g in GOALS for pr in PRIZES)


@dataclass
class PromptState:
    hero: Entity
    guide: Entity
    prize: Entity
    goal: Goal
    setting: Setting


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_kind, traits = HEROES[params.hero]
    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=params.hero, traits=[params.trait] + traits))
    guide = world.add(Entity(id="guide", kind="character", type="guide", label=params.guide))
    canoe = world.add(Entity(id="canoe", label="the canoe", phrase="the old canoe"))
    prize = world.add(Entity(id="prize", label=params.prize, phrase=PRIZES[params.prize].phrase, plural=PRIZES[params.prize].plural))
    goal = GOALS[params.goal]
    world.add(canoe)
    world.add(prize)
    world.facts.update(hero=hero, guide=guide, canoe=canoe, prize=prize, goal=goal)
    do_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    prize = f["prize"]
    return [
        f'Write a short fable about a {hero.type} who finds a canoe and tries to {goal.verb}.',
        f'Tell a child-friendly story where a warning about a canoe on a fast river is ignored.',
        f'Write a simple fable that ends badly after someone risks {prize.phrase} in a canoe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    prize = f["prize"]
    goal = f["goal"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the canoe?",
            answer=f"{hero.id} wanted to {goal.verb}.",
        ),
        QAItem(
            question=f"Why did {guide.label} warn {hero.id}?",
            answer=f"{guide.label} warned {hero.id} because {goal.risk.lower()}, and {goal.danger}.",
        ),
        QAItem(
            question=f"What happened to {prize.phrase} in the end?",
            answer=f"{prize.phrase.capitalize()} was lost when the canoe tipped in the river.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canoe?",
            answer="A canoe is a small boat that one or more animals or people can paddle on water.",
        ),
        QAItem(
            question="Why can a fast river be dangerous for a canoe?",
            answer="A fast river can push a canoe toward rocks or banks, which can make it scrape, leak, or tip over.",
        ),
        QAItem(
            question="What is a moral in a fable?",
            answer="A moral is the lesson at the end that tells what the story teaches.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("current", sid, s.current))
        if s.has_reeds:
            lines.append(asp.fact("has_reeds", sid))
        if s.has_rocks:
            lines.append(asp.fact("has_rocks", sid))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("verb", gid, g.verb))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, G, Pr) :- setting(P), goal(G), prize(Pr).
bad_ending(P, G) :- current(P, fast), has_rocks(P), goal(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like canoe storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, prize = rng.choice(combos)
    hero = args.hero or rng.choice(list(HEROES))
    guide = args.guide or rng.choice(list(GUIDES))
    trait = args.trait or rng.choice(["stubborn", "bold", "proud", "reckless"])
    return StoryParams(place=place, goal=goal, prize=prize, hero=hero, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="riverbank", goal="cross", prize="clover", hero="rabbit", guide="heron", trait="stubborn"),
    StoryParams(place="bend", goal="collect_reeds", prize="berries", hero="hare", guide="crow", trait="proud"),
    StoryParams(place="riverbank", goal="cross", prize="berries", hero="otter", guide="owl", trait="reckless"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for p, g, pr in combos:
            print(f"  {p:10} {g:18} {pr}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
