#!/usr/bin/env python3
"""
Storyworld: Gouda, Peace, and Sound Effects

A small superhero-style story world where a hero hears trouble, uses gadgets,
and learns that peace can be the strongest power of all.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Hero:
    name: str
    type: str
    trait: str
    hero_title: str


@dataclass
class Villain:
    name: str
    type: str
    trouble: str
    sound: str


@dataclass
class Gadget:
    label: str
    phrase: str
    effect: str
    sound: str


@dataclass
class StoryParams:
    hero_name: str = "Mila"
    hero_type: str = "girl"
    trait: str = "brave"
    setting: str = "city"
    villain: str = "clatter"
    gadget: str = "gouda shield"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Entity
    sidekick: Entity
    villain: Entity
    gadget: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "city": Setting(place="the city", detail="Tall buildings shined in the afternoon light."),
    "rooftop": Setting(place="the rooftop", detail="The wind hummed between the chimneys."),
    "museum": Setting(place="the museum", detail="The big hall was quiet except for the echo of footsteps."),
}

HEROES = {
    "girl": ["Mila", "Zoe", "Nina", "Tia"],
    "boy": ["Kai", "Leo", "Ben", "Noah"],
}

VILLAINS = {
    "clatter": Villain(name="Captain Clatter", type="villain", trouble="loud clattering noise", sound="CLANG-CLANG"),
    "rumble": Villain(name="Doctor Rumble", type="villain", trouble="deep rumbling noise", sound="RUMBLE-RUMBLE"),
    "whirr": Villain(name="The Whirler", type="villain", trouble="fast whirring noise", sound="WHIRR-WHIRR"),
}

GADGETS = {
    "gouda shield": Gadget(label="gouda shield", phrase="a round gouda shield", effect="calm the crowd", sound="SNAP"),
    "peace beam": Gadget(label="peace beam", phrase="a peace beam", effect="turn anger into calm", sound="ZING"),
    "cheese cape": Gadget(label="cheese cape", phrase="a bright cheese cape", effect="help the hero glide in safely", sound="WHOOSH"),
}

CURATED = [
    StoryParams(hero_name="Mila", hero_type="girl", trait="brave", setting="city", villain="clatter", gadget="gouda shield"),
    StoryParams(hero_name="Kai", hero_type="boy", trait="kind", setting="rooftop", villain="rumble", gadget="peace beam"),
    StoryParams(hero_name="Zoe", hero_type="girl", trait="clever", setting="museum", villain="whirr", gadget="cheese cape"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with gouda, peace, and sound effects.")
    ap.add_argument("--hero-name", choices=sorted({n for names in HEROES.values() for n in names}))
    ap.add_argument("--hero-type", choices=sorted(HEROES))
    ap.add_argument("--trait", choices=["brave", "kind", "clever", "steady", "quick"])
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--villain", choices=sorted(VILLAINS))
    ap.add_argument("--gadget", choices=sorted(GADGETS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    villain = args.villain or rng.choice(list(VILLAINS))
    gadget = args.gadget or rng.choice(list(GADGETS))
    hero_type = args.hero_type or rng.choice(list(HEROES))
    hero_name = args.hero_name or rng.choice(HEROES[hero_type])
    trait = args.trait or rng.choice(["brave", "kind", "clever", "steady", "quick"])

    if villain == "clatter" and gadget == "peace beam":
        pass
    elif villain == "rumble" and gadget == "gouda shield":
        pass
    elif villain == "whirr" and gadget == "cheese cape":
        pass
    elif args.villain and args.gadget:
        raise StoryError("That gadget does not fit this villain's trouble well enough for a believable superhero fix.")

    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        trait=trait,
        setting=setting,
        villain=villain,
        gadget=gadget,
    )


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    hero = Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=[params.trait, "superhero"],
        meters={"courage": 1.0, "peace": 0.0, "noise": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0},
    )
    sidekick = Entity(
        id="sidekick",
        kind="character",
        type="friend",
        label="Bean",
        traits=["small", "helpful"],
        meters={"courage": 0.5, "peace": 1.0},
        memes={"hope": 1.0, "joy": 0.5},
    )
    villain_cfg = VILLAINS[params.villain]
    villain = Entity(
        id="villain",
        kind="character",
        type="villain",
        label=villain_cfg.name,
        traits=["noisy"],
        meters={"noise": 2.0},
        memes={"stubbornness": 2.0, "grumpiness": 1.5},
    )
    gadget_cfg = GADGETS[params.gadget]
    gadget = Entity(
        id="gadget",
        kind="thing",
        type="gadget",
        label=gadget_cfg.label,
        phrase=gadget_cfg.phrase,
        owner=hero.id,
        meters={"shine": 1.0},
        memes={"peace": 1.0},
    )
    world = World(setting=setting, hero=hero, sidekick=sidekick, villain=villain, gadget=gadget)
    world.facts = {
        "params": params,
        "setting": setting,
        "villain_cfg": villain_cfg,
        "gadget_cfg": gadget_cfg,
    }
    return world


def narrate_story(world: World) -> None:
    p = world.facts["params"]
    villain_cfg = world.facts["villain_cfg"]
    gadget_cfg = world.facts["gadget_cfg"]

    world.say(f"On {world.setting.place}, {p.hero_name} was a {p.trait} little superhero who loved helping people.")
    world.say(f"Beside {p.hero_name}, the tiny sidekick Bean carried {gadget_cfg.phrase} because it had a funny little shine.")
    world.say(f"Then {villain_cfg.name} burst in and made a terrible sound: {villain_cfg.sound}! The air shook with {villain_cfg.trouble}.")
    world.para()
    world.say(f"{p.hero_name} took a deep breath and said, \"Peace first.\"")
    world.say(f"{p.hero_name} lifted the {gadget_cfg.label} and it went {gadget_cfg.sound}! The bright circle of gouda light glowed like a friendly moon.")
    world.say(f"The noisy trouble started to soften, because {gadget_cfg.effect}.")
    world.say(f"Bean clapped and shouted, \"Go, hero, go!\"")
    world.para()
    world.say(f"{villain_cfg.name} blinked, the loud chaos stopped, and the whole place grew quiet.")
    world.say(f"At last, {p.hero_name} smiled, the city felt safe again, and peace stood stronger than any noise.")
    world.say(f"The {gadget_cfg.label} stayed warm in {p.hero_name}'s hands while the people cheered: \"Hooray!\"")

    world.hero.meters["peace"] += 2.0
    world.hero.memes["joy"] += 2.0
    world.hero.memes["hope"] += 1.0
    world.villain.meters["noise"] = 0.0
    world.villain.memes["grumpiness"] = 0.0
    world.sidekick.memes["joy"] += 1.0
    world.sidekick.meters["peace"] += 1.0
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    villain_cfg = world.facts["villain_cfg"]
    gadget_cfg = world.facts["gadget_cfg"]
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {p.hero_name}, a {p.trait} little superhero who wanted to help everyone keep peace."
        ),
        QAItem(
            question=f"What kind of trouble did {villain_cfg.name} make?",
            answer=f"{villain_cfg.name} made {villain_cfg.trouble}, and it sounded like {villain_cfg.sound}."
        ),
        QAItem(
            question=f"What did {p.hero_name} use to solve the problem?",
            answer=f"{p.hero_name} used {gadget_cfg.phrase}, which helped {gadget_cfg.effect}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the noise gone, the people cheering, and peace standing stronger than before."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gouda?",
            answer="Gouda is a kind of cheese. In stories, it can be silly, tasty, or even part of a hero's gadget."
        ),
        QAItem(
            question="What is peace?",
            answer="Peace means things are calm, safe, and not fighting or making trouble."
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are words that help a story feel loud, soft, fast, or magical, like BOOM, ZING, or WHOOSH."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short superhero story with {p.hero_name}, gouda, peace, and a big sound effect.",
        f"Tell a child-friendly superhero story where a hero uses a cheese-themed gadget to stop noisy trouble.",
        f"Write a gentle action story with sound effects that ends in peace instead of a fight.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.sidekick, world.villain, world.gadget]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
setting(S) :- setting_name(S).
villain(V) :- villain_name(V).
gadget(G) :- gadget_name(G).

compatible(clatter, peace_beam).
compatible(rumble, gouda_shield).
compatible(whirr, cheese_cape).

valid_story(H,S,V,G) :- hero_name(H), setting_name(S), villain_name(V), gadget_name(G), compatible(V,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for v in VILLAINS:
        lines.append(asp.fact("villain_name", v))
    for g in GADGETS:
        lines.append(asp.fact("gadget_name", g.replace(" ", "_")))
    for names in HEROES.values():
        for n in names:
            lines.append(asp.fact("hero_name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for h_type, names in HEROES.items():
        for h in names:
            for s in SETTINGS:
                for v, g in [("clatter", "peace_beam"), ("rumble", "gouda_shield"), ("whirr", "cheese_cape")]:
                    py_set.add((h, s, v, g))
    if asp_set:
        print(f"OK: ASP produced {len(asp_set)} candidate story shapes.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    narrate_story(world)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
