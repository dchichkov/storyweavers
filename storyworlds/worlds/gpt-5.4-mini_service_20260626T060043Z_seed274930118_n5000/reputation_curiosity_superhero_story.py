#!/usr/bin/env python3
"""
Standalone storyworld: reputation, curiosity, and a superhero-style rescue.

A child-facing superhero story world built from a tiny simulation:
- a hero has a reputation meter that can rise or fall
- curiosity pushes the hero to investigate a mystery
- the hero must avoid a flashy mistake that would damage trust
- the ending proves that careful action and helpfulness restored reputation

The prose is state-driven: the hero notices a problem, follows clues, makes a
choice under pressure, and resolves the scene with an ending image that shows
what changed.
"""

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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    setting: str
    weather: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    source: str
    effect: str
    risk: str
    curiosity_gain: float = 1.0
    reputation_gain: float = 1.0
    fear_gain: float = 1.0


@dataclass
class Tool:
    id: str
    label: str
    helps: str
    safe: bool = True


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    city: str
    mystery: str
    tool: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


CITIES = {
    "skyport": City("Skyport", "the bright city rooftops", "windy", {"fly", "search"}),
    "rivergate": City("Rivergate", "the river bridge and streets below", "cloudy", {"search", "rescue"}),
    "sunspire": City("Sunspire", "the tall sunny plaza", "clear", {"search", "help"}),
}

MYSTERIES = {
    "whisper_alarm": Mystery(
        id="whisper_alarm",
        clue="a soft alarm blinking from a rooftop signal box",
        source="the old signal box",
        effect="it might be warning the city about a hidden problem",
        risk="people could panic if the wrong button is pressed",
        curiosity_gain=2.0,
        reputation_gain=1.0,
        fear_gain=0.5,
    ),
    "lost_banner": Mystery(
        id="lost_banner",
        clue="a banner flapping from one broken corner",
        source="the parade banner",
        effect="it could fall into the street",
        risk="a falling banner could scare the crowd",
        curiosity_gain=1.5,
        reputation_gain=1.0,
        fear_gain=0.5,
    ),
    "blue_glow": Mystery(
        id="blue_glow",
        clue="a blue glow under a manhole cover",
        source="the tunnel below",
        effect="something underneath was humming softly",
        risk="the glow could hide a trapped kitten or a broken wire",
        curiosity_gain=2.0,
        reputation_gain=1.2,
        fear_gain=1.0,
    ),
}

TOOLS = {
    "notebook": Tool(id="notebook", label="a tiny notebook", helps="write clues down"),
    "scanner": Tool(id="scanner", label="a pocket scanner", helps="check a signal safely"),
    "rope": Tool(id="rope", label="a bright rescue rope", helps="reach something without jumping"),
}

HERO_NAMES = ["Nova", "Blaze", "Comet", "Halo", "Spark", "Vector"]
SIDEKICK_NAMES = ["Pip", "Mika", "Tee", "Juno", "Rin", "Sol"]


def city_detail(city: City) -> str:
    return {
        "skyport": "The rooftops shone like little silver boxes, and the wind tugged at every cape.",
        "rivergate": "The river kept sparkling under the bridge, and the streets below were busy and loud.",
        "sunspire": "The plaza was warm and bright, with long shadows and shiny windows all around.",
    }[city.name]


def reasonableness_gate(city: City, mystery: Mystery, tool: Tool) -> None:
    if mystery.id == "blue_glow" and tool.id == "rope":
        raise StoryError("No story: a rope does not help much with a secret glow under a cover.")
    if mystery.id == "whisper_alarm" and tool.id == "rope":
        raise StoryError("No story: a rope cannot safely read a rooftop signal box.")
    if mystery.id == "lost_banner" and tool.id == "scanner":
        raise StoryError("No story: a scanner is not the right fix for a torn banner.")
    if "search" not in city.affordances and mystery.id in {"whisper_alarm", "blue_glow"}:
        raise StoryError("No story: this city setting does not support the needed rooftop or tunnel search.")


def simulate(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    mystery = world.facts["mystery"]
    tool = world.facts["tool"]

    hero.memes["curiosity"] += mystery.curiosity_gain
    hero.memes["reputation"] += 1.0
    world.say(f"{hero.id} was the city hero everyone looked up to, with a cape that fluttered like a red flag.")
    world.say(f"{hero.id} had a strong reputation for helping fast and keeping a cool head.")
    world.say(f"One day, {hero.id} noticed {mystery.clue}.")
    world.say(city_detail(world.city))
    world.say(f"{hero.id} felt curious right away, because {mystery.effect}.")
    world.say(f"{sidekick.id} hurried over with {tool.label} and said, \"Let's find out carefully.\"")

    world.para()
    if mystery.id == "whisper_alarm":
        hero.memes["curiosity"] += 1.0
        world.say(f"{hero.id} climbed to the signal box and used {tool.label} to listen before touching anything.")
        world.say(f"The box whispered a warning about a stuck door on the next roof, not a city emergency.")
        world.say(f"{hero.id} fixed the door, and the rooftops grew calm again.")
    elif mystery.id == "lost_banner":
        world.say(f"{hero.id} and {sidekick.id} followed the flapping sound to the parade banner.")
        world.say(f"Instead of pulling hard, {hero.id} used {tool.label} to tie the torn corner neatly.")
        world.say(f"The banner hung straight again, and the people below smiled up at the bright colors.")
    else:
        hero.memes["curiosity"] += 1.0
        world.say(f"{hero.id} lifted the cover slowly and shone a light inside while {sidekick.id} held back the rope.")
        world.say(f"A kitten was curled beside a broken wire, and the blue glow came from a tiny warning lamp.")
        world.say(f"{hero.id} carried the kitten out first, then called for help with the wire.")
        world.say(f"The little rescue made the tunnel safe, and the kitten purred in {hero.id}'s arms.")

    hero.memes["reputation"] += mystery.reputation_gain + 1.0
    hero.memes["confidence"] += 1.0
    world.say(f"By the end, {hero.id}'s reputation was even better, because the job was done with care instead of a flashy mistake.")
    world.say(f"{hero.id} stood in the sunlight with {sidekick.id}, smiling while the city felt safe again.")

    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery, tool=tool)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short superhero story for a young child about {hero.id} and a secret mystery, using the word "reputation".',
        f"Tell a gentle superhero story where {hero.id}'s curiosity leads to careful helping instead of trouble.",
        f"Write a story about a hero who protects {world.city.name} while keeping a good reputation.",
        f"Make a simple superhero tale about noticing {mystery.clue} and solving it with a sidekick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Why did {hero.id} go to the mystery instead of ignoring it?",
            answer=f"{hero.id} was curious, and the clue looked important. {hero.id} wanted to find out what was happening and help the city safely.",
        ),
        QAItem(
            question=f"What did {sidekick.id} bring to help {hero.id}?",
            answer=f"{sidekick.id} brought {tool.label}, which was useful for careful investigating.",
        ),
        QAItem(
            question=f"What was the mystery in this story?",
            answer=f"The mystery was {mystery.clue}. It turned out to be {mystery.effect}.",
        ),
        QAItem(
            question=f"How did {hero.id}'s reputation change by the end?",
            answer=f"{hero.id}'s reputation got better, because {hero.id} solved the problem carefully and helped people feel safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reputation?",
            answer="A reputation is what other people think about someone based on what they do over time.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask questions, and learn more.",
        ),
        QAItem(
            question="What is a sidekick in a superhero story?",
            answer="A sidekick is a helper who works with the hero, often by giving ideas, tools, or support.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"city={world.city.name} setting={world.city.setting} weather={world.city.weather}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city", cid))
        for a in sorted(city.affordances):
            lines.append(asp.fact("affords", cid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("curious_about", mid))
        if m.source:
            lines.append(asp.fact("source", mid, m.source))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is reasonable for a city if the city supports the needed action.
reasonable(City,Mystery,Tool) :- city(City), mystery(Mystery), tool(Tool),
                                  afford_match(City,Mystery,Tool).
afford_match(City,whisper_alarm,scanner) :- affords(City,search).
afford_match(City,lost_banner,notebook) :- affords(City,help).
afford_match(City,blue_glow,scanner) :- affords(City,search).

#show reasonable/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def python_reasonable() -> list[tuple]:
    out = []
    for cid, city in CITIES.items():
        for mid, m in MYSTERIES.items():
            for tid, t in TOOLS.items():
                if mid == "whisper_alarm" and tid == "scanner" and "search" in city.affordances:
                    out.append((cid, mid, tid))
                elif mid == "lost_banner" and tid == "notebook" and "help" in city.affordances:
                    out.append((cid, mid, tid))
                elif mid == "blue_glow" and tid == "scanner" and "search" in city.affordances:
                    out.append((cid, mid, tid))
    return out


def asp_verify() -> int:
    a = set(asp_reasonable())
    p = set(python_reasonable())
    if a == p:
        print(f"OK: ASP matches Python reasonableness gate ({len(a)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: reputation and curiosity.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, city in CITIES.items():
        for mid in MYSTERIES:
            for tid in TOOLS:
                try:
                    reasonableness_gate(city, MYSTERIES[mid], TOOLS[tid])
                except StoryError:
                    continue
                combos.append((cid, mid, tid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    city, mystery, tool = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(city=city, mystery=mystery, tool=tool, hero_name=hero_name, sidekick_name=sidekick_name)


def generate(params: StoryParams) -> StorySample:
    city = CITIES[params.city]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    reasonableness_gate(city, mystery, tool)

    world = World(city)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick"))
    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery, tool=tool)
    simulate(world)

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
    StoryParams(city="skyport", mystery="whisper_alarm", tool="scanner", hero_name="Nova", sidekick_name="Pip"),
    StoryParams(city="rivergate", mystery="lost_banner", tool="notebook", hero_name="Comet", sidekick_name="Juno"),
    StoryParams(city="sunspire", mystery="blue_glow", tool="scanner", hero_name="Halo", sidekick_name="Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/3."))
        atoms = sorted(set(asp.atoms(model, "reasonable")))
        for a in atoms:
            print(a)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
