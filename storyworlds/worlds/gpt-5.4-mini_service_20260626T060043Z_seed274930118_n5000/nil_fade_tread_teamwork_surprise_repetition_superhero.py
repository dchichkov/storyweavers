#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale.

Premise:
A small team of heroes must stop a surprise problem in the city. Their powers
are modest, their teamwork matters, and repeated tries gradually make the danger
fade. The seed words nil, fade, and tread are woven into the world as names,
actions, and outcomes.

This script is self-contained except for the shared result containers and the
optional ASP helper.
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
    alias: str
    power: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Threat:
    name: str
    description: str
    intensity: float
    spread: float
    surprise: bool = True


@dataclass
class Place:
    name: str
    setting_line: str
    affordance: str


@dataclass
class StoryParams:
    place: str
    threat: str
    hero_a: str
    hero_b: str
    seed: Optional[int] = None


PLACES = {
    "city": Place(
        name="the city",
        setting_line="The city was bright by day and full of roofs, bridges, and narrow alleys.",
        affordance="crowds and corners",
    ),
    "harbor": Place(
        name="the harbor",
        setting_line="The harbor glittered with water, cranes, and stacked crates.",
        affordance="docks and wind",
    ),
    "museum": Place(
        name="the museum",
        setting_line="The museum stood quiet, with tall halls and glass cases that caught the light.",
        affordance="halls and echoes",
    ),
}

THREATS = {
    "smoke": Threat(
        name="smoke cloud",
        description="a rolling smoke cloud that blurred windows and made people cough",
        intensity=3.0,
        spread=1.0,
    ),
    "shadow": Threat(
        name="shadow swarm",
        description="a skittering shadow swarm that hid in every corner",
        intensity=2.5,
        spread=1.2,
    ),
    "glitch": Threat(
        name="signal glitch",
        description="a buzzing signal glitch that scrambled lights and doors",
        intensity=2.0,
        spread=0.9,
    ),
}

HEROES = [
    ("Nil", "Captain Nil", "quiet focus"),
    ("Fade", "Lady Fade", "dim light"),
    ("Tread", "Tread Runner", "careful steps"),
    ("Spark", "Spark Shield", "quick bursts"),
    ("Mira", "Mira Flash", "bright signals"),
    ("Stone", "Stone Ward", "steady strength"),
]

TRAITS = ["brave", "clever", "calm", "bold", "kind", "quick"]


class World:
    def __init__(self, place: Place, threat: Threat) -> None:
        self.place = place
        self.threat = threat
        self.heroes: list[Hero] = []
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turns: int = 0
        self.surprise_seen: bool = False
        self.teamwork_count: int = 0
        self.repeated_attempts: int = 0
        self.threat_level: float = threat.intensity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_hero(self, hero: Hero) -> Hero:
        self.heroes.append(hero)
        return hero

    def copy(self) -> "World":
        w = World(self.place, self.threat)
        w.heroes = [Hero(h.name, h.alias, h.power, h.role, dict(h.meters), dict(h.memes)) for h in self.heroes]
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.turns = self.turns
        w.surprise_seen = self.surprise_seen
        w.teamwork_count = self.teamwork_count
        w.repeated_attempts = self.repeated_attempts
        w.threat_level = self.threat_level
        return w


def pronoun(name: str, case: str = "subject") -> str:
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def build_hero(choice: tuple[str, str, str], role: str) -> Hero:
    name, alias, power = choice
    return Hero(name=name, alias=alias, power=power, role=role)


def setup_story(world: World) -> None:
    a = world.heroes[0]
    b = world.heroes[1]
    world.say(f"{world.place.setting_line}")
    world.say(
        f"On that day, {a.alias} and {b.alias} were watching over {world.place.name}. "
        f"{a.name} was known for {a.power}, and {b.name} was known for {b.power}."
    )
    world.say(
        f"They were a small team, but they trusted each other. "
        f"When trouble came, they knew one hero could help the other."
    )


def introduce_surprise(world: World) -> None:
    th = world.threat
    a, b = world.heroes[:2]
    world.para()
    world.say(
        f"Then, with no warning, {th.name} rolled in. It was {th.description}."
    )
    world.say(
        f"{a.alias} blinked at the surprise. {b.alias} steadied {pronoun(b.name, 'object')} and said, "
        f"\"We can handle this together.\""
    )
    world.surprise_seen = True
    world.threat_level += 0.5


def act_repetition(world: World) -> None:
    a, b = world.heroes[:2]
    moves = [
        f"{a.alias} lifted a hand and sent a thin beam across the smoke.",
        f"{b.alias} followed with a slow, steady sweep to push the haze aside.",
        f"{a.alias} tried again, this time aiming at the thickest patch.",
        f"{b.alias} repeated the sweep so the path would stay open.",
    ]
    world.para()
    for line in moves[:2]:
        world.say(line)
    world.repeated_attempts += 2
    world.threat_level -= 0.6
    world.say(
        f"They did not give up after the first try. Instead, they repeated the plan, "
        f"because one careful step was not enough."
    )


def act_teamwork(world: World) -> None:
    a, b = world.heroes[:2]
    world.para()
    world.say(
        f"{a.alias} spotted the next gap while {b.alias} guarded the people below."
    )
    world.say(
        f"Working as one, they passed signals back and forth. "
        f"{a.alias} moved where {b.alias} pointed, and {b.alias} moved where {a.alias} cleared."
    )
    world.teamwork_count += 1
    world.threat_level -= 0.8


def act_fade(world: World) -> None:
    th = world.threat
    a, b = world.heroes[:2]
    world.para()
    world.say(
        f"Bit by bit, the {th.name} began to fade. The dark edges thinned, and the air grew easier to breathe."
    )
    world.say(
        f"{a.alias} and {b.alias} kept going until the last gray curl drifted away from the street."
    )
    world.threat_level = max(0.0, world.threat_level - 1.2)


def resolution(world: World) -> None:
    a, b = world.heroes[:2]
    world.para()
    world.say(
        f"At last, the danger was gone. The city lights shone again, and the people cheered for the team."
    )
    world.say(
        f"{a.alias} and {b.alias} stood side by side, tired but smiling, "
        f"knowing the surprise had faded because they stayed together."
    )
    world.say(
        f"Their small repeat-and-help plan had worked: when one hero slipped, the other caught the moment, and the whole city became calm again."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    threat = THREATS[params.threat]
    world = World(place, threat)
    world.add_hero(build_hero(HEROES[0], "leader"))
    world.add_hero(build_hero(HEROES[1], "partner"))
    setup_story(world)
    introduce_surprise(world)
    act_repetition(world)
    act_teamwork(world)
    act_fade(world)
    resolution(world)
    world.facts.update(
        place=place,
        threat=threat,
        hero_a=world.heroes[0],
        hero_b=world.heroes[1],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short superhero story for children set in {world.place.name} with a surprise threat and a teamwork ending.",
        f"Tell a gentle superhero tale where {world.heroes[0].alias} and {world.heroes[1].alias} face {world.threat.name} and keep trying until it fades.",
        f"Create a simple hero story that includes repetition, surprise, and teamwork, and uses the words nil, fade, and tread.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b = world.heroes[:2]
    th = world.threat
    place = world.place.name
    return [
        QAItem(
            question=f"Who worked together to protect {place}?",
            answer=f"{a.alias} and {b.alias} worked together to protect {place}. They shared the job and trusted each other.",
        ),
        QAItem(
            question=f"What surprise did the heroes face?",
            answer=f"They faced {th.name}, which was {th.description}. It arrived suddenly and made the day harder.",
        ),
        QAItem(
            question=f"How did the heroes make the danger fade?",
            answer=(
                f"They made the danger fade by repeating their plan and helping each other. "
                f"{a.alias} and {b.alias} kept trying until the last of it disappeared."
            ),
        ),
        QAItem(
            question=f"Why did the plan work?",
            answer=(
                f"The plan worked because of teamwork and repetition. "
                f"One hero cleared the way while the other guarded people and repeated the same careful move."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something that happens when you do not expect it.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, which can help you learn or finish a task.",
        ),
        QAItem(
            question="What does fade mean?",
            answer="To fade means to become weaker, dimmer, or less noticeable over time.",
        ),
        QAItem(
            question="What does tread mean?",
            answer="To tread means to step carefully or walk on something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.name}")
    lines.append(f"threat={world.threat.name}")
    lines.append(f"threat_level={world.threat_level:.2f}")
    lines.append(f"surprise_seen={world.surprise_seen}")
    lines.append(f"teamwork_count={world.teamwork_count}")
    lines.append(f"repeated_attempts={world.repeated_attempts}")
    for h in world.heroes:
        lines.append(f"{h.name}: role={h.role}, power={h.power}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for i, (_, alias, _) in enumerate(HEROES):
        lines.append(asp.fact("hero", f"h{i+1}", alias))
    return "\n".join(lines)


ASP_RULES = r"""
% Tiny declarative twin for the reasonableness gate.
teamwork_story(P,T) :- place(P), threat(T).
surprise_story(T) :- threat(T).
repetition_story(H1,H2) :- hero(H1,_), hero(H2,_), H1 != H2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryConfig:
    place: str
    threat: str
    hero_a: str
    hero_b: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero-a", choices=[h[0].lower() for h in HEROES])
    ap.add_argument("--hero-b", choices=[h[0].lower() for h in HEROES])
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
    threat = args.threat or rng.choice(list(THREATS))
    a = args.hero_a or "nil"
    b = args.hero_b or "fade"
    if a == b:
        raise StoryError("Need two different heroes for teamwork.")
    return StoryParams(place=place, threat=threat, hero_a=a, hero_b=b)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    story = world.render()
    prompts = generation_prompts(world)
    storyqa = story_qa(world)
    worldqa = world_knowledge_qa(world)
    return StorySample(params=params, story=story, prompts=prompts, story_qa=storyqa, world_qa=worldqa, world=world)


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
    StoryParams(place="city", threat="smoke", hero_a="nil", hero_b="fade"),
    StoryParams(place="harbor", threat="shadow", hero_a="fade", hero_b="tread"),
    StoryParams(place="museum", threat="glitch", hero_a="tread", hero_b="nil"),
]


def verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show teamwork_story/2.\n#show surprise_story/1.\n#show repetition_story/2."))
        return
    if args.verify:
        sys.exit(verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.threat} / {p.hero_a}+{p.hero_b}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
