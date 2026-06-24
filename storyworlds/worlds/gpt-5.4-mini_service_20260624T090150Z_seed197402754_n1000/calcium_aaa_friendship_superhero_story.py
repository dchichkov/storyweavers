#!/usr/bin/env python3
"""
A standalone Storyweavers world: a tiny superhero friendship tale about
calcium, a shouted "aaa", and a team-up that helps a friend feel strong.
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
class Hero:
    name: str
    kind: str = "hero"
    power: str = "high jumps"
    cape_color: str = "blue"
    meters: dict[str, float] = field(default_factory=lambda: {"strength": 0.0, "distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "friendship": 0.0})


@dataclass
class Friend:
    name: str
    kind: str = "friend"
    power: str = "quick thinking"
    cape_color: str = "red"
    meters: dict[str, float] = field(default_factory=lambda: {"strength": 0.0, "distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "friendship": 0.0})


@dataclass
class ObjectThing:
    name: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: {"crunch": 0.0, "power": 0.0})
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    weather: str
    hero: Hero
    friend: Friend
    calcium: ObjectThing
    alarm: str = "aaa"
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_event(self, text: str) -> None:
        self.events.append(text)

    def copy(self) -> "World":
        import copy
        return copy.deepcopy(self)


@dataclass
class StoryParams:
    place: str = "the city"
    weather: str = "bright"
    hero_name: str = "Mira"
    friend_name: str = "Zed"
    seed: Optional[int] = None


PLACES = {
    "the city": {"skyline", "bridge", "rooftop"},
    "the park": {"bench", "path", "tree"},
    "the schoolyard": {"slide", "wall", "court"},
}

WEATHERS = ["bright", "windy", "rainy"]

HERO_NAMES = ["Mira", "Nova", "Rin", "Tala", "Ivy", "Luna"]
FRIEND_NAMES = ["Zed", "Pip", "Arlo", "Bea", "Sage", "Noa"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero friendship storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(PLACES))
    weather = args.weather or rng.choice(WEATHERS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    if hero_name == friend_name:
        raise StoryError("The hero and the friend must be different people.")
    return StoryParams(place=place, weather=weather, hero_name=hero_name, friend_name=friend_name)


def make_world(params: StoryParams) -> World:
    hero = Hero(name=params.hero_name)
    friend = Friend(name=params.friend_name)
    calcium = ObjectThing(name="calcium", label="a calcium snack")
    w = World(place=params.place, weather=params.weather, hero=hero, friend=friend, calcium=calcium)

    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.meters["strength"] += 1
    friend.meters["strength"] += 0.2 if params.weather == "windy" else 0.0

    w.say(f"On a {params.weather} day at {params.place}, {hero.name} wore a bright cape and looked after {friend.name}.")
    w.say(f"They were not just teammates; they were best friends who loved to save the day together.")
    w.para()

    if params.weather == "rainy":
        w.say(f"Then the sky boomed, and a long {w.alarm} drifted over the rooftops.")
        friend.memes["worry"] += 1
        w.say(f"{friend.name} frowned because the slippery ground made every step feel harder.")
    else:
        w.say(f"Suddenly, a giant sign fell sideways with a loud clang, and somebody shouted {w.alarm}!")
        friend.memes["worry"] += 1
        w.say(f"{friend.name} hesitated, because the tall sign blocked the path to the little library.")

    w.say(f"{hero.name} reached out and said, 'I am here with you.'")
    hero.memes["joy"] += 0.5
    friend.memes["joy"] += 0.2
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    w.para()
    w.say(f"{hero.name} opened a small pouch and found {calcium.label}.")
    calcium.meters["crunch"] += 1
    calcium.meters["power"] += 1
    w.say(f"'This can help us stay strong,' {hero.name} said. {friend.name} took a bite and stood a little taller.")
    friend.meters["strength"] += 1

    if params.weather == "rainy":
        w.say(f"With steadier feet, {friend.name} could jump over the slick puddle and reach the trapped cat on the ledge.")
        friend.meters["distance"] += 1
    else:
        w.say(f"With brighter courage, {friend.name} squeezed under the fallen sign while {hero.name} held it up.")
        friend.meters["distance"] += 1

    hero.meters["distance"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1

    w.para()
    w.say(f"At the end, the danger was gone, the city was safe, and the two friends laughed together in their capes.")
    w.say(f"{hero.name} and {friend.name} even shared the last crumb of calcium before flying home side by side.")

    w.facts = {
        "place": params.place,
        "weather": params.weather,
        "hero": hero,
        "friend": friend,
        "calcium": calcium,
        "alarm": w.alarm,
    }
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "calcium" and the call "{f["alarm"]}".',
        f"Tell a friendship story where {f['hero'].name} helps {f['friend'].name} feel brave at {f['place']}.",
        f"Write a gentle superhero tale in which two friends solve a problem together after somebody shouts {f['alarm']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    fr = world.facts["friend"]
    place = world.facts["place"]
    weather = world.facts["weather"]
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {h.name} and {fr.name}, two friends who work together like superhero teammates.",
        ),
        QAItem(
            question=f"What problem happened at {place} on the {weather} day?",
            answer=f"A problem happened when somebody shouted {world.alarm}, and {fr.name} felt unsure about what to do next.",
        ),
        QAItem(
            question="What helped the friend become stronger?",
            answer=f"{h.name} shared a calcium snack, and that helped {fr.name} stand taller and feel ready to help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is calcium?",
            answer="Calcium is a mineral your body uses to help build strong bones and teeth.",
        ),
        QAItem(
            question="Why do friends help each other?",
            answer="Friends help each other because caring together makes hard things easier and makes everyone feel less alone.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero helps people, solves problems, and uses courage to keep others safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in [world.hero, world.friend, world.calcium]:
        lines.append(f"{ent.name}: meters={ent.meters} memes={ent.memes}")
    lines.append(f"events={world.events}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the city", weather="bright", hero_name="Mira", friend_name="Zed"),
    StoryParams(place="the park", weather="windy", hero_name="Nova", friend_name="Bea"),
    StoryParams(place="the schoolyard", weather="rainy", hero_name="Rin", friend_name="Arlo"),
]


ASP_RULES = r"""
hero_friend_story(P) :- place(P), weather(W), good_weather(W).
friendship_help(H,F) :- hero(H), friend(F), together(H,F).
needs_calcium(F) :- friend(F), worried(F).
better(F) :- needs_calcium(F), has(calcium).
ok_story(P,H,F) :- place(P), hero(H), friend(F), together(H,F), better(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    lines.append(asp.fact("good_weather", "bright"))
    lines.append(asp.fact("good_weather", "windy"))
    lines.append(asp.fact("has", "calcium"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ok_story/3."))
    atoms = sorted(set(asp.atoms(model, "ok_story")))
    py = sorted((p, h, f) for p in PLACES for h in HERO_NAMES[:1] for f in FRIEND_NAMES[:1])
    if atoms:
        print("OK: ASP program runs.")
        return 0
    print("MISMATCH: ASP produced no model atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show ok_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ok_story/3."))
        print(sorted(set(asp.atoms(model, "ok_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
