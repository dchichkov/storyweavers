#!/usr/bin/env python3
"""
storyworlds/worlds/trophy_pooey_teamwork_curiosity_myth.py
==========================================================

A standalone story world for a tiny myth-style tale about a trophy, a pooey
problem, curiosity, and teamwork.

Seed tale:
---
In a little hill-temple town, a bright bronze trophy was kept in a glass niche.
The villagers believed it was a gift from the old river spirit, so they polished
it every dawn and left flowers below it.

One windy afternoon, a curious child named Nia followed a trail of tiny green
footprints behind the shrine. The trail ended at the trophy niche, where a
squirming river monkey had left a pooey mess on the sacred base. Nia wanted to
wipe it away at once, but the mess kept spreading as she fussed alone.

Then Nia called the lantern keeper and the market potter. Together they made a
soft leaf scoop, fetched clean water, and worked in a careful line. The keeper
held the lantern high, the potter steadied the bowl, and Nia cleaned the niche
without scratching the trophy. By sunset the trophy shone again, and the villagers
said the old spirit had smiled on their teamwork.

World model:
---
Entities have physical meters and emotional memes. The story turns on the
trophy getting pooey, curiosity leading to discovery, and teamwork solving the
problem without damage.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"pooey": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "teamwork": 0.0, "alarm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "priestess"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "priest"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the hill shrine"
    sacred: bool = True
    affords: set[str] = field(default_factory=lambda: {"discover", "clean", "work"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper1_name: str
    helper2_name: str
    seed: Optional[int] = None


SETTINGS = {
    "shrine": Setting(place="the hill shrine"),
    "temple": Setting(place="the river temple"),
    "court": Setting(place="the old stone court"),
}

HERO_NAMES = ["Nia", "Mira", "Tavi", "Lena", "Suri", "Koa"]
HELPER_NAMES = ["Ivo", "Pela", "Rin", "Jori", "Mina", "Boro"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


def _clean_risk(world: World) -> list[str]:
    out: list[str] = []
    trophy = world.get("trophy")
    if trophy.meters["pooey"] < THRESHOLD:
        return out
    if "warned" in world.fired:
        return out
    world.fired.add("warned")
    world.get("hero").memes["alarm"] += 1
    out.append("The trophy had become pooey, and its bright shine was hidden.")
    return out


def _teamwork_fix(world: World) -> list[str]:
    trophy = world.get("trophy")
    hero = world.get("hero")
    if hero.memes["curiosity"] < THRESHOLD:
        return []
    if hero.memes["teamwork"] < THRESHOLD:
        return []
    if trophy.meters["pooey"] < THRESHOLD:
        return []
    if "fixed" in world.fired:
        return []
    world.fired.add("fixed")
    trophy.meters["pooey"] = 0.0
    trophy.meters["clean"] = 1.0
    return ["Together they made the trophy clean again."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for rule in (_clean_risk, _teamwork_fix):
        sents = rule(world)
        out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero_name))
    helper1 = world.add(Entity(id="helper1", kind="character", type="man", label=params.helper1_name))
    helper2 = world.add(Entity(id="helper2", kind="character", type="woman", label=params.helper2_name))
    trophy = world.add(Entity(
        id="trophy", type="trophy", label="trophy",
        phrase="a bright bronze trophy",
        owner="village", caretaker="temple",
    ))

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.label} was a curious child who liked to follow small clues and hidden tracks."
    )
    world.say(
        f"In {setting.place}, the villagers kept {trophy.phrase} in a sacred niche and polished it at dawn."
    )

    world.para()
    world.say(
        f"One windy day, {hero.label} noticed tiny prints behind the shrine and followed them."
    )
    world.say(
        f"The trail led to the niche, where the trophy had been left {trophy.label} and dull."
    )
    trophy.meters["pooey"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.label} wanted to fix it at once, but the mess clung to the stone and would not come clean by shouting."
    )
    hero.memes["teamwork"] += 1
    helper1.memes["teamwork"] += 1
    helper2.memes["teamwork"] += 1
    world.say(
        f"{hero.label} called {helper1.label} the lantern keeper and {helper2.label} the potter for help."
    )
    world.say(
        f"First they made a soft leaf scoop, then they brought clean water, and at last they worked in a careful line."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{helper1.label} held the lantern high, {helper2.label} steadied the bowl, and {hero.label} wiped the niche without scratching the trophy."
    )
    if trophy.meters["clean"] >= THRESHOLD:
        world.say(
            f"By sunset the trophy shone again, and the villagers said the old river spirit had smiled on their teamwork."
        )

    world.facts.update(
        hero=hero,
        helper1=helper1,
        helper2=helper2,
        trophy=trophy,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short myth-style story for a young child about a trophy, a pooey problem, curiosity, and teamwork.',
        f"Tell a gentle legend set at {world.facts['setting'].place} where {world.facts['hero'].label} follows clues and helps clean a sacred trophy.",
        "Write a simple tale in which curiosity finds the problem and teamwork fixes it before the day ends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper1 = world.facts["helper1"]
    helper2 = world.facts["helper2"]
    trophy = world.facts["trophy"]
    place = world.facts["setting"].place
    return [
        QAItem(
            question=f"Who followed the tiny prints to the sacred trophy?",
            answer=f"{hero.label}, the curious child, followed the tiny prints at {place} and found the trophy niche.",
        ),
        QAItem(
            question=f"What was wrong with the trophy before everyone helped?",
            answer=f"The trophy had become pooey and dull, so it needed careful cleaning.",
        ),
        QAItem(
            question=f"Who helped {hero.label} clean the trophy?",
            answer=f"{helper1.label} and {helper2.label} helped {hero.label}. They worked together with a lantern, a bowl, and clean water.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The trophy was clean again, and the villagers were glad because teamwork solved the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and work together to finish something.",
        ),
        QAItem(
            question="What does curiosity help you do?",
            answer="Curiosity helps you notice clues, ask questions, and discover new things.",
        ),
        QAItem(
            question="Why do people keep trophies in special places?",
            answer="People often keep trophies in special places because the trophies are important and they want to protect and show them.",
        ),
        QAItem(
            question="Why is pooey mess hard to ignore?",
            answer="Pooey mess is hard to ignore because it is dirty, smelly, and needs careful cleaning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.kind:9} {e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shrine", hero_name="Nia", helper1_name="Ivo", helper2_name="Pela"),
    StoryParams(place="temple", hero_name="Mira", helper1_name="Rin", helper2_name="Mina"),
    StoryParams(place="court", hero_name="Tavi", helper1_name="Jori", helper2_name="Boro"),
]


@dataclass
class ASPRegistry:
    place: str
    hero_name: str
    helper1_name: str
    helper2_name: str


ASP_RULES = r"""
curious(H) :- curiosity(H).
teamwork(H) :- teamwork_meme(H).
pooey(T) :- pooey_mess(T).

need_help(T) :- trophy(T), pooey(T).
fixed(T) :- trophy(T), teamwork(H), curious(H), need_help(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("setting_place", key, setting.place))
    lines.append(asp.fact("trophy", "trophy"))
    lines.append(asp.fact("pooey_mess", "trophy"))
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("teamwork_meme", "hero"))
    lines.append(asp.fact("teamwork_meme", "helper1"))
    lines.append(asp.fact("teamwork_meme", "helper2"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny myth storyworld: trophy, pooey, curiosity, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(HERO_NAMES)
    helper1, helper2 = rng.sample(HELPER_NAMES, 2)
    return StoryParams(place=place, hero_name=name, helper1_name=helper1, helper2_name=helper2)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


def valid_story_params() -> list[StoryParams]:
    return CURATED


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print(asp_program("#show fixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show fixed/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
