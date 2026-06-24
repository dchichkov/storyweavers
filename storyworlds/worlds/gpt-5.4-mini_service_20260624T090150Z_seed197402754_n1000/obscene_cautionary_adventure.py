#!/usr/bin/env python3
"""
storyworlds/worlds/obscene_cautionary_adventure.py
===================================================

A small cautionary adventure world about a brave child, a risky trail, and a
wise turn back from a scribbled obscene warning.

Seed tale:
---
Mina loved adventure stories, especially ones about secret paths and hidden
maps. One afternoon she found a narrow trail behind the old hill fort, and
someone had painted an obscene word on the stone gate. Mina's brother warned
her not to copy the mark or go inside alone, because the fort was old and the
stairs were broken. Mina wanted to see the treasure room anyway, but then she
noticed that a loose step could make anyone fall. She chose a safer plan:
she covered the rude word with a paper star, told a grown-up, and explored the
courtyard with a lantern instead. The fort still felt mysterious, but Mina got
to have an adventure without making a bad choice.

World model:
---
This world tracks a single child on a short adventure. The child has a desire
meter, a caution meme, and a bravery meme. The setting can contain a risky
object or place with a warning sign. The story turns when the child notices the
hazard, resists a bad impulse, and chooses a safer route with help.

Notes:
- The story is cautionary, but child-facing and concrete.
- "obscene" is kept as a story-world word for the rude mark/sign, not as
  explicit content.
- State drives prose: the ending proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str
    risky_feature: str
    rescue_feature: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper: str
    setting_key: str
    seed: Optional[int] = None


SETTINGS = {
    "old_fort": Setting(
        place="the old hill fort",
        afford="explore",
        risky_feature="broken stairs",
        rescue_feature="lantern",
    ),
    "cave_path": Setting(
        place="the narrow cave path",
        afford="explore",
        risky_feature="slippery stones",
        rescue_feature="rope",
    ),
    "harbor_ruins": Setting(
        place="the harbor ruins",
        afford="search",
        risky_feature="loose boards",
        rescue_feature="guide rope",
    ),
}

HERO_NAMES_GIRL = ["Mina", "Tia", "Nora", "Lena", "June", "Ari"]
HERO_NAMES_BOY = ["Leo", "Finn", "Owen", "Milo", "Ezra", "Noah"]
HELPERS = ["brother", "sister", "dad", "mom", "grandpa", "grandma"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w.entities = dataclasses.replace(self.entities) if False else {}
        import copy
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def choose_setting(key: str) -> Setting:
    if key not in SETTINGS:
        raise StoryError("Unknown setting.")
    return SETTINGS[key]


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    setting = SETTINGS[setting_key]
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES_GIRL if gender == "girl" else HERO_NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=setting.place,
        hero_name=hero_name,
        hero_gender=gender,
        helper=helper,
        setting_key=setting_key,
    )


def build_world(params: StoryParams) -> World:
    setting = choose_setting(params.setting_key)
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    warning = world.add(Entity(id="warning", type="sign", label="obscene warning", phrase="an obscene scribble"))
    prize = world.add(Entity(id="prize", type="treasure", label="treasure room", phrase="the treasure room"))
    hazard = world.add(Entity(id="hazard", type="hazard", label=setting.risky_feature, phrase=setting.risky_feature))
    rescue = world.add(Entity(id="rescue", type="gear", label=setting.rescue_feature, phrase=setting.rescue_feature))

    hero.meters["curiosity"] = 1.0
    hero.memes["bravery"] = 1.0
    world.facts.update(hero=hero, helper=helper, warning=warning, prize=prize, hazard=hazard, rescue=rescue)

    world.say(f"{params.hero_name} loved adventure stories and always looked for a new path to follow.")
    world.say(f"One afternoon, {params.hero_name} went to {setting.place} with {params.helper}.")
    world.say(f"Near the gate, {params.hero_name} saw {warning.phrase} painted on the stone.")
    world.para()

    hero.meters["curiosity"] += 1.0
    hero.memes["impulse"] = 1.0
    world.say(f"{params.hero_name} wanted to go on right away and see {prize.label}.")
    world.say(f"But {params.helper} frowned and warned, \"Don't follow rude marks or ignore {setting.risky_feature}.\"")
    world.say(f"{params.helper} pointed out that {setting.risky_feature} could hurt someone who rushed ahead.")
    world.para()

    hero.memes["caution"] = 1.0
    hero.meters["curiosity"] = 0.0
    world.say(f"{params.hero_name} looked again and noticed the danger more clearly.")
    world.say(f"Instead of copying the obscene scribble, {params.hero_name} covered it with a paper star.")
    world.say(f"Then {params.hero_name} took {rescue.label} and explored the safe courtyard with {params.helper}.")
    hero.memes["pride"] = 1.0
    hero.memes["fear"] = 0.0
    world.say(f"The fort still felt like an adventure, but now it felt like a wise one.")
    world.say(f"At the end, {params.hero_name} came home with a brave story and no scraped knees.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short cautionary adventure about {hero.label} discovering an obscene warning and choosing a safer path.',
        f"Tell a child-friendly story where {hero.label} wants to explore {world.setting.place} but listens when {helper.label} warns about the danger.",
        f"Write an adventure story that starts with a rude mark, includes a risky place feature, and ends with a careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    warning: Entity = f["warning"]
    hazard: Entity = f["hazard"]
    rescue: Entity = f["rescue"]
    return [
        QAItem(
            question=f"What did {hero.label} see near the gate at {world.setting.place}?",
            answer=f"{hero.label} saw {warning.phrase} painted on the stone gate.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.label} not to rush ahead?",
            answer=f"{helper.label} warned {hero.label} because {world.setting.risky_feature} could hurt someone who hurried into the place.",
        ),
        QAItem(
            question=f"What safer choice did {hero.label} make instead of following the rude mark?",
            answer=f"{hero.label} covered the obscene scribble with a paper star and explored the safe courtyard with {rescue.label}.",
        ),
        QAItem(
            question=f"How did the adventure end for {hero.label}?",
            answer=f"It ended well because {hero.label} listened, stayed careful, and came home with a brave story and no scraped knees.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word caution mean?",
            answer="Caution means being careful and thinking about danger before you act.",
        ),
        QAItem(
            question="Why should people listen when a grown-up warns about a broken place?",
            answer="People should listen because broken stairs, slippery stones, or loose boards can cause a fall.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is a tale about going somewhere exciting, facing a problem, and finding a brave solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    return "\n".join(lines)


ASP_RULES = r"""
warning(obscene).
hazard(broken_stairs).
rescue(lantern).
safe_choice(C) :- rescue(C).
cautionary_story :- warning(obscene), hazard(broken_stairs), safe_choice(lantern).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", key)
        for key in SETTINGS
    ]
    for key, s in SETTINGS.items():
        lines.append(asp.fact("place_name", key, s.place))
        lines.append(asp.fact("affords", key, s.afford))
        lines.append(asp.fact("risk", key, s.risky_feature))
        lines.append(asp.fact("rescue", key, s.rescue_feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary adventure story world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper", choices=HELPERS)
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
    return valid_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show cautionary_story/0.")
    model = asp.one_model(program)
    got = bool(asp.atoms(model, "cautionary_story"))
    want = True
    if got == want:
        print("OK: ASP reasoner matches Python world premise.")
        return 0
    print("Mismatch between ASP and Python story premise.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for the cautionary story premise.")
        print(asp_program("#show cautionary_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place=SETTINGS["old_fort"].place, hero_name="Mina", hero_gender="girl", helper="brother", setting_key="old_fort"),
            StoryParams(place=SETTINGS["cave_path"].place, hero_name="Leo", hero_gender="boy", helper="dad", setting_key="cave_path"),
            StoryParams(place=SETTINGS["harbor_ruins"].place, hero_name="Nora", hero_gender="girl", helper="mom", setting_key="harbor_ruins"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
