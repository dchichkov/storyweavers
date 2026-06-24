#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/haggis_status_suspense_lesson_learned_animal_story.py
==============================================================================================================================

A standalone storyworld: a small animal tale about a haggis feast, a status
worry, suspense, and a lesson learned.

The world follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP_RULES twin
- CLI support for generation, QA, JSON, trace, ASP, and verify modes
- story text driven by simulated state, not a frozen template

Seed words and style targets:
- haggis
- status
- Suspense
- Lesson Learned
- Animal Story

Initial tale imagined from the seed:
A small animal helper is proud of its status at the hill feast, but the haggis
basket goes missing before the gathering. Suspense builds while the animal looks,
then the basket is found and the helper learns that status is not about looking
important; it is about helping safely and kindly.

"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "hedgehog", "rabbit", "fox", "badger", "otter"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    animal: str
    haggis_name: str
    status_title: str
    seed: Optional[int] = None


@dataclass
class Theme:
    id: str
    place: str
    scene: str
    gathering: str
    suspense_line: str
    lesson_line: str


@dataclass
class Creature:
    id: str
    type: str
    label: str
    status: str
    cautious: bool = False


@dataclass
class Prize:
    id: str
    label: str
    edible: bool = True
    valuable: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        w = World()
        w.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THEMES = {
    "hill": Theme(
        id="hill",
        place="the windy hill",
        scene="a grassy hill with heather and stones",
        gathering="the sunset feast",
        suspense_line="The basket was gone, and the grass around the rocks was still.",
        lesson_line="The best status came from helping, not from boasting.",
    ),
    "river": Theme(
        id="river",
        place="the river bank",
        scene="a bright river bank with reeds and pebbles",
        gathering="the moonlight supper",
        suspense_line="The basket had vanished, and the reeds whispered in the wind.",
        lesson_line="True status came from being careful and kind.",
    ),
    "forest": Theme(
        id="forest",
        place="the pine forest",
        scene="a soft pine forest with moss and roots",
        gathering="the acorn feast",
        suspense_line="The basket was missing, and the trees seemed to hold their breath.",
        lesson_line="The lesson learned was that a good helper keeps calm and tells the truth.",
    ),
}

ANIMALS = ["mouse", "rabbit", "fox", "hedgehog", "otter", "badger"]
HEROES = ["Milo", "Pip", "Nia", "Tavi", "Una", "Bram"]
HELPERS = ["Dot", "Mira", "Sora", "Lupin", "Jori", "Bea"]
HAGGIS_NAMES = ["the haggis basket", "the haggis dish", "the warm haggis pot"]
STATUS_TITLES = ["feast helper", "bridge watcher", "berry scout", "lantern keeper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: haggis, status, suspense, lesson learned.")
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--haggis-name")
    ap.add_argument("--status-title")
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
    setting = args.setting or rng.choice(list(THEMES))
    animal = args.animal or rng.choice(ANIMALS)
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([n for n in HELPERS if n != hero])
    haggis_name = args.haggis_name or rng.choice(HAGGIS_NAMES)
    status_title = args.status_title or rng.choice(STATUS_TITLES)
    if args.haggis_name == "nothing":
        raise StoryError("This story needs a haggis object so the suspense has something to revolve around.")
    return StoryParams(setting=setting, hero=hero, helper=helper, animal=animal, haggis_name=haggis_name, status_title=status_title)


def reasonableness_gate(params: StoryParams) -> None:
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal for this small story world.")
    if not params.haggis_name:
        raise StoryError("A haggis object is required.")
    if not params.status_title:
        raise StoryError("A status title is required.")


def make_world(params: StoryParams) -> World:
    theme = THEMES[params.setting]
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.animal, label=params.hero, role="hero",
                        traits=["proud"], memes={"status": 2.0, "worry": 0.5, "relief": 0.0, "lesson": 0.0}))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.animal, label=params.helper, role="helper",
                          traits=["careful"], memes={"status": 1.0, "worry": 0.5, "relief": 0.0, "lesson": 0.0}))
    basket = w.add(Entity(id="haggis", kind="thing", type="prize", label=params.haggis_name, meters={"hidden": 1.0}, memes={"value": 1.0}))
    stone = w.add(Entity(id="stone", kind="thing", type="thing", label="the old stone", meters={"searchable": 1.0}))
    w.facts.update(theme=theme, hero=hero, helper=helper, basket=basket, stone=stone, params=params)
    return w


def search_for_haggis(w: World) -> None:
    hero = w.get(w.facts["hero"].id)
    helper = w.get(w.facts["helper"].id)
    basket = w.facts["basket"]
    theme = w.facts["theme"]
    hero.memes["status"] += 1
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    w.say(f"On {theme.place}, {hero.id} wore {hero.pronoun('possessive')} little badge of status and tried to look important.")
    w.say(f"{theme.scene.capitalize()}. {hero.id} was supposed to carry {basket.label} to {theme.gathering}, but then the basket was not there.")
    w.say(theme.suspense_line)


def suspense_turn(w: World) -> None:
    hero = w.get(w.facts["hero"].id)
    helper = w.get(w.facts["helper"].id)
    basket = w.facts["basket"]
    hero.memes["worry"] += 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1.0
    w.para()
    w.say(f"{helper.id} sniffed the air, looked behind the stones, and listened very hard.")
    w.say(f"At last {helper.id} found {basket.label} tucked under the old stone, safe but hidden.")
    w.say(f"The wait had felt long, so the little search was full of suspense.")


def lesson_learned(w: World) -> None:
    hero = w.get(w.facts["hero"].id)
    helper = w.get(w.facts["helper"].id)
    theme = w.facts["theme"]
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    w.para()
    w.say(f"{hero.id} gave {helper.id} a grateful nudge and said that real status came from using a calm head.")
    w.say(f'The animals carried {w.facts["basket"].label} to {theme.gathering}, and everybody cheered.')
    w.say(f"By the end, {theme.lesson_line}")


def tell(params: StoryParams) -> World:
    w = make_world(params)
    search_for_haggis(w)
    suspense_turn(w)
    lesson_learned(w)
    w.facts["outcome"] = "found"
    return w


def valid_combos() -> list[tuple[str, str]]:
    return [(s, a) for s in THEMES for a in ANIMALS]


CURATED = [
    StoryParams(setting="hill", hero="Milo", helper="Dot", animal="mouse", haggis_name="the haggis basket", status_title="feast helper"),
    StoryParams(setting="river", hero="Pip", helper="Mira", animal="otter", haggis_name="the warm haggis pot", status_title="bridge watcher"),
    StoryParams(setting="forest", hero="Nia", helper="Sora", animal="rabbit", haggis_name="the haggis dish", status_title="berry scout"),
]


KNOWLEDGE = [
    QAItem(question="What is haggis in this story world?", answer="Haggis is the special feast food the animals carry to the gathering."),
    QAItem(question="What does status mean here?", answer="Status means a title or feeling of importance, like being the feast helper or bridge watcher."),
    QAItem(question="What should an animal do when something goes missing?", answer="Stay calm, look carefully, and ask a helper for help."),
    QAItem(question="What is suspense?", answer="Suspense is the tense waiting feeling when you do not know what will happen next."),
]


def generation_prompts(w: World) -> list[str]:
    p = w.facts["params"]
    return [
        f"Write an Animal Story about {p.hero} and {p.helper} on {w.facts['theme'].place}, where haggis goes missing and suspense builds before it is found.",
        f"Tell a short child-friendly story that uses the words haggis and status, and ends with a lesson learned.",
        f"Make the animal helper worried about status, then calm the worry with a careful search and a kind ending.",
    ]


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    return [
        QAItem(question=f"Who worried about status?", answer=f"{p.hero} worried about status at first."),
        QAItem(question=f"What went missing?", answer=f"{w.facts['basket'].label} went missing for a little while."),
        QAItem(question="How did the suspense end?", answer=f"{p.helper} found the haggis under an old stone, and the worry ended."),
        QAItem(question="What lesson was learned?", answer="The animals learned that real status comes from helping calmly and kindly."),
    ]


def world_qa(w: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    w = tell(params)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_qa(w), world=w)


def dump_trace(w: World) -> str:
    lines = ["--- world trace ---"]
    for e in w.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role} type={e.type}")
    return "\n".join(lines)


ASP_RULES = r"""
animal(mouse;rabbit;fox;hedgehog;otter;badger).
setting(hill;river;forest).
valid(S,A) :- setting(S), animal(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", s) for s in THEMES
    ] + [
        asp.fact("animal", a) for a in ANIMALS
    ])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        asp = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if py == asp:
        print(f"OK: ASP parity ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


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
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(p)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.helper} in {p.setting} ({p.animal}, haggis, status)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
