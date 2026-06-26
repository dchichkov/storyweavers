#!/usr/bin/env python3
"""
Storyworld: Moo Foreshadowing Surprise Superhero Story

A tiny superhero tale domain with a clue-driven setup, a surprising reveal,
and a hopeful resolution. The world simulates characters, objects, hints, and
emotional/physical state so the prose is driven by state changes rather than a
fixed template.

Premise:
- A child hero sees odd clues around a barnyard-themed city.
- A looming "moo" signal hints that something unusual is coming.
- The hero follows the clues, meets a surprise helper, and stops a small but
  dramatic problem before it grows.

The story is intentionally small and classical: beginning, turn, ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "Skyway City"
    vibe: str = "bright rooftops"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    clue: str
    reveal: str
    danger: str
    method: str
    foreshadow: str
    surprise: str
    keyword: str = "moo"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    helps: set[str]
    effect: str
    reveal: str
    surprise: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        return c


def _r_alarm(world: World) -> list[str]:
    out = []
    for hero in world.chars():
        if hero.memes.get("alarm", 0) < THRESHOLD:
            continue
        if ("alarm", hero.id) in world.fired:
            continue
        world.fired.add(("alarm", hero.id))
        hero.memes["focus"] = hero.memes.get("focus", 0) + 1
        out.append(f"{hero.pronoun().capitalize()} stood straighter and listened harder.")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    for hero in world.chars():
        if hero.memes.get("mystery", 0) < THRESHOLD:
            continue
        if ("reveal", hero.id) in world.fired:
            continue
        world.fired.add(("reveal", hero.id))
        hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
        out.append("The clue turned out to mean something far stranger than anyone guessed.")
    return out


CAUSAL_RULES = [
    _r_alarm,
    _r_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    name: str
    sidekick: str
    place: str
    challenge: str
    gadget: str
    seed: Optional[int] = None


HERO_NAMES = ["Maya", "Leo", "Nia", "Finn", "Zara", "Toby"]
SIDEKICKS = ["a tiny robot", "a bat-shaped drone", "a clever kid reporter", "a striped cat"]
SETTINGS = {
    "city": Setting(place="Skyway City", vibe="bright rooftops", affords={"signal", "dash"}),
}
CHALLENGES = {
    "barn_signal": Challenge(
        id="barn_signal",
        clue="a low moo from the alleyway",
        reveal="a hidden speaker had been tucked into a toy barn",
        danger="someone was using the moo sound to lure people away",
        method="follow the echo",
        foreshadow="moo",
        surprise="the sound did not come from a cow at all",
        tags={"moo", "signal", "sound"},
    )
}
GADGETS = {
    "cape": Gadget(
        id="cape",
        label="a silver cape",
        phrase="a silver cape that could carry a hero across the wind",
        helps={"dash", "signal"},
        effect="it let the hero swoop over the rooftops",
        reveal="the cape had been waiting folded inside the mailbox all along",
        surprise=True,
    ),
}

GIRL_NAMES = ["Maya", "Nia", "Zara"]
BOY_NAMES = ["Leo", "Finn", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with foreshadowing and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = args.place or "city"
    challenge = args.challenge or "barn_signal"
    gadget = args.gadget or "cape"
    if challenge not in CHALLENGES:
        raise StoryError("Unknown challenge.")
    if gadget not in GADGETS:
        raise StoryError("Unknown gadget.")
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(name=name, sidekick=sidekick, place=place, challenge=challenge, gadget=gadget)


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, challenge: Challenge, gadget: Gadget, hero_name: str, sidekick: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in GIRL_NAMES else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="thing", label=sidekick))
    clue = world.add(Entity(id="clue", type="thing", label="clue", phrase=challenge.clue))
    tool = world.add(Entity(id=gadget.id, type="thing", label=gadget.label, phrase=gadget.phrase, owner=hero.id))

    world.say(f"{hero_name} was a young superhero who loved {setting.place} and watched every rooftop with care.")
    world.say(f"One evening, {hero_name} heard {challenge.foreshadow} {challenge.clue}.")
    hero.memes["mystery"] = hero.memes.get("mystery", 0) + 1
    world.say(f"That strange sound was the first hint that something hidden was nearby.")
    world.para()

    world.say(f"{hero_name} followed the clue with {sidekick}, because the echo kept bouncing toward the old toy barn.")
    hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1
    propagate(world, narrate=True)
    world.say(f"{challenge.danger.capitalize()}, so {hero_name} kept going instead of turning back.")
    world.para()

    world.say(f"Then came the surprise: {challenge.surprise}.")
    world.say(f"It was {challenge.reveal}, and the noise was only a trick to make the city panic.")
    world.say(f"{hero_name} used {gadget.label} at once; {gadget.effect}.")
    hero.meters["rescue"] = hero.meters.get("rescue", 0) + 1
    helper.memes["proud"] = helper.memes.get("proud", 0) + 1
    world.say(f"Together, they stopped the trick and laughed when the true source of the moo sound was found.")
    world.say(f"In the end, {hero_name} stood on the rooftop with {sidekick}, and the quiet city felt safe again.")

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        tool=tool,
        setting=setting,
        challenge=challenge,
        gadget=gadget,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    gadget = f["gadget"]
    return [
        f'Write a short superhero story for a young child that includes the word "{challenge.keyword}".',
        f"Tell a story where {hero.id} follows a clue, gets a surprise, and uses {gadget.label} to help save the city.",
        f"Write a gentle action story with foreshadowing, a hidden trick, and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    challenge = f["challenge"]
    gadget = f["gadget"]
    return [
        QAItem(
            question=f"What clue did {hero.id} hear first?",
            answer=f"{hero.id} first heard {challenge.clue}. It was a small foreshadowing hint that something odd was happening.",
        ),
        QAItem(
            question=f"Why was the moo sound surprising in the story?",
            answer=f"It was surprising because {challenge.surprise}. The sound was only part of a trick, not a real cow.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem with {gadget.label}?",
            answer=f"{hero.id} used {gadget.label} right away, and {gadget.effect}. Then {hero.id} and {helper.label} stopped the trick together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early so readers can guess that something important may happen later.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a moment when something happens that the characters or readers did not expect.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero helps other people, faces danger bravely, and tries to make things safe again.",
        ),
    ]


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
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(S) :- sidekick(S).
clue_seen(H) :- clue_word(moo), hero_name(H).
surprise_event(H) :- clue_seen(H), gadget(G), helps(G, rescue), has_reveal(G).
resolved(H) :- surprise_event(H).
#show clue_seen/1.
#show surprise_event/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    lines.append(asp.fact("clue_word", "moo"))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
        if g.surprise:
            lines.append(asp.fact("has_reveal", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue_seen/1. #show surprise_event/1. #show resolved/1."))
    atoms = {(s.name, tuple(a.string if a.type == a.type.String else a.number for a in s.arguments)) for s in model}
    expected = {("clue_seen", (name,)) for name in HERO_NAMES}
    expected |= {("surprise_event", (name,)) for name in HERO_NAMES}
    expected |= {("resolved", (name,)) for name in HERO_NAMES}
    if atoms == expected:
        print("OK: ASP gate matches Python assumptions.")
        return 0
    print("MISMATCH between ASP and Python assumptions.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue_seen/1. #show surprise_event/1. #show resolved/1."))
    return [(s.name, tuple(a.string if a.type == a.type.String else a.number for a in s.arguments)) for s in model]


CURATED = [
    StoryParams(name="Maya", sidekick="a tiny robot", place="city", challenge="barn_signal", gadget="cape"),
    StoryParams(name="Leo", sidekick="a bat-shaped drone", place="city", challenge="barn_signal", gadget="cape"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], GADGETS[params.gadget], params.name, params.sidekick)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue_seen/1. #show surprise_event/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue_seen/1. #show surprise_event/1. #show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} with {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
