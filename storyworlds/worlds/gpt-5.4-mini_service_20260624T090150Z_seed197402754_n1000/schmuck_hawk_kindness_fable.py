#!/usr/bin/env python3
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
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, amount: float) -> None:
        self.meters[key] = self.m(key) + amount

    def add_e(self, key: str, amount: float) -> None:
        self.memes[key] = self.e(key) + amount


@dataclass
class Setting:
    place: str
    season: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    noun: str
    phrase: str
    kind: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "hill": Setting(place="the hill", season="spring", affords={"watch", "share"}),
    "orchard": Setting(place="the orchard", season="autumn", affords={"watch", "share"}),
    "cliff": Setting(place="the cliff", season="windy", affords={"watch", "share"}),
}

TRAITS = ["small", "brave", "quiet", "gentle", "curious", "bright"]


@dataclass
class StoryState:
    hero: Entity
    hawk: Entity
    gift: Entity
    setting: Setting
    helped: bool = False
    learned: bool = False


def make_world(place: str) -> World:
    return World(SETTINGS[place])


def setup_state(world: World) -> StoryState:
    hero = world.add(Entity(id="schmuck", kind="character", type="schmuck", label="schmuck"))
    hawk = world.add(Entity(id="hawk", kind="character", type="hawk", label="hawk"))
    gift = world.add(Entity(id="seedcake", kind="thing", type="seedcake", label="seed cake"))
    hero.meters = {"food": 1.0, "worry": 0.0, "kindness": 0.0}
    hero.memes = {"pride": 1.0, "kindness": 0.0, "fear": 0.0, "joy": 0.0, "understanding": 0.0}
    hawk.meters = {"hunger": 1.0, "wind": 0.0}
    hawk.memes = {"patience": 0.0, "gratitude": 0.0, "trust": 0.0}
    gift.owner = hero.id
    return StoryState(hero=hero, hawk=hawk, gift=gift, setting=world.setting)


def _warn_of_hunger(world: World) -> None:
    hero = world.get("schmuck")
    hawk = world.get("hawk")
    if hero.e("kindness") >= THRESHOLD:
        return
    hero.add_e("worry", 1.0)
    hero.add_e("fear", 1.0)
    world.say(
        f"On {world.setting.place}, a little schmuck walked under a wide sky and saw a hawk circling above."
    )
    world.say(
        "The hawk was hungry, and the schmuck clutched a seed cake close, not wanting to share."
    )
    if hawk.m("hunger") >= THRESHOLD:
        world.say(
            "The bird looked tired from the wind, and the hill felt lonelier because no one had offered help."
        )


def _choose_kindness(world: World) -> None:
    hero = world.get("schmuck")
    hawk = world.get("hawk")
    gift = world.get("seedcake")
    hero.add_e("kindness", 1.0)
    hero.add_e("understanding", 1.0)
    hero.add_e("pride", -0.5)
    world.say(
        "Then the schmuck remembered that a small kindness can make a big sky feel warmer."
    )
    world.say(
        "The schmuck broke the seed cake in two and held out the larger piece to the hawk."
    )
    gift.owner = hawk.id
    hawk.add_m("hunger", -1.0)
    hawk.add_e("trust", 1.0)
    hawk.add_e("gratitude", 1.0)
    hero.add_e("joy", 1.0)


def _resolve(world: World) -> None:
    hero = world.get("schmuck")
    hawk = world.get("hawk")
    world.say(
        "The hawk landed gently, ate the crumbly gift, and folded its wings with a soft nod."
    )
    world.say(
        "Soon the schmuck and the hawk sat together on the hill, and the wind felt less sharp."
    )
    if hero.e("kindness") >= THRESHOLD and hawk.e("gratitude") >= THRESHOLD:
        hero.add_e("joy", 1.0)
        hero.add_e("understanding", 1.0)
        world.say(
            "The schmuck smiled, because kindness had turned a lonely afternoon into a true friendship."
        )


def _moral(world: World) -> None:
    world.para()
    world.say("And the lesson was simple: kindness shared in time never grows smaller in the heart.")


def tell(place: str) -> World:
    world = make_world(place)
    state = setup_state(world)
    world.say(
        f"On a bright day at {world.setting.place}, a schmuck found a seed cake and watched a hawk circle overhead."
    )
    world.say(
        "The schmuck wanted to keep the treat all to itself, because the little crumbs looked precious."
    )
    _warn_of_hunger(world)
    world.para()
    _choose_kindness(world)
    _resolve(world)
    _moral(world)
    world.facts.update(hero=state.hero, hawk=state.hawk, gift=state.gift, setting=world.setting)
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("character", "schmuck"))
    lines.append(asp.fact("character", "hawk"))
    lines.append(asp.fact("virtue", "kindness"))
    lines.append(asp.fact("token", "seedcake"))
    lines.append(asp.fact("wants", "schmuck", "share_or_keep"))
    lines.append(asp.fact("needs", "hawk", "food"))
    return "\n".join(lines)


ASP_RULES = r"""
share_possible(P) :- setting(P), affords(P, share).
kind_action(schmuck) :- share_possible(P), character(schmuck), character(hawk), needs(hawk, food).
kind_story(P) :- setting(P), kind_action(schmuck).
#show kind_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_kind_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_story/1."))
    return sorted(set(asp.atoms(model, "kind_story")))


def asp_verify() -> int:
    py = {(p,) for p in SETTINGS}
    cl = set(asp_kind_places())
    if py == cl:
        print(f"OK: ASP parity matches Python ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about a schmuck, a hawk, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    return StoryParams(place=place, seed=args.seed)


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short fable about a schmuck and a hawk at {world.setting.place} that teaches kindness.",
        "Tell a child-friendly story where sharing food helps a hungry hawk and changes a stubborn heart.",
        "Write a simple fable ending with a moral about kindness and a bird in need.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about a schmuck who meets a hungry hawk at the hill and learns to be kind.",
        ),
        QAItem(
            question="What did the schmuck share?",
            answer="The schmuck shared a seed cake with the hawk.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The schmuck stopped being selfish, the hawk felt grateful, and they ended the story as friends.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or be gentle with someone else.",
        ),
        QAItem(
            question="What does a hawk do?",
            answer="A hawk is a bird that can fly high and look for food from the sky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place)
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
    if args.show_asp:
        print(asp_program("#show kind_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show kind_story/1."))
        print(asp.atoms(model, "kind_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(SETTINGS):
            p = StoryParams(place=place, seed=base_seed)
            samples.append(generate(p))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
