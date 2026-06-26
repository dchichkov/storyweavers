#!/usr/bin/env python3
"""
storyworlds/worlds/few_inner_monologue_problem_solving_adventure.py
===================================================================

A small adventure storyworld about a child adventurer who has a few supplies,
faces a simple obstacle, thinks through the problem, and finds a brave,
child-friendly solution.

The story premise is intentionally compact:
- a curious child goes on a little adventure
- they have only a few useful items
- something blocks the path
- an inner monologue helps them reason through the problem
- a practical fix lets them continue and return with a win

The world is modeled with physical meters and emotional memes so that the prose
comes from simulated state rather than a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    feature: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    obstacle: str
    obstacle_verb: str
    thought: str
    risk: str
    solves: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str] = field(default_factory=set)
    keywords: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: str = ""
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.zone = self.zone
        clone.fired = set(self.fired)
        return clone


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("distance", 0.0) < 3.0:
            continue
        if hero.meters.get("tired", 0.0) >= THRESHOLD:
            continue
        sig = ("tired", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["tired"] = hero.meters.get("tired", 0.0) + 1.0
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        out.append(f"The long walk made {hero.id} feel a little tired.")
    return out


def _r_problem_clear(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("plan", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("obstacle_handled", 0.0) >= THRESHOLD:
            continue
        sig = ("clear", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["obstacle_handled"] = 1.0
        out.append(f"{hero.id} found a way through.")
    return out


CAUSAL_RULES = [
    _r_tired,
    _r_problem_clear,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def resolve_blockage(challenge: Challenge, tool: Optional[Tool]) -> bool:
    return tool is not None and challenge.id in tool.helps


def choose_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS:
        if challenge.id in tool.helps:
            return tool
    return None


def predict_world(world: World, hero: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    _attempt(sim, sim.get(hero.id), challenge, narrate=False)
    return {
        "solved": sim.entities[hero.id].meters.get("obstacle_handled", 0.0) >= THRESHOLD,
        "worry": sim.entities[hero.id].memes.get("worry", 0.0),
    }


def _attempt(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1.0
    if challenge.id == "river" and world.setting.place != "forest path":
        hero.meters["distance"] += 1.0
    if challenge.id == "dark_tunnel":
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved little adventures."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked to notice paths, stones, and hidden turns."
    )


def setup_few_supplies(world: World, hero: Entity, pack: Entity) -> None:
    world.say(
        f"{hero.id} packed a few things for the trip: {pack.phrase}."
    )
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    pack.carried_by = hero.id


def arrive(world: World, hero: Entity, challenge: Challenge) -> None:
    world.say(
        f"One bright day, {hero.id} went to {world.setting.place}, where the {challenge.obstacle} waited."
    )
    world.say(f"{world.setting.feature.capitalize()} made the place feel like a real adventure.")


def want_forward(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to {challenge.obstacle_verb}, but the {challenge.obstacle} stood in the way."
    )


def inner_monologue(world: World, hero: Entity, challenge: Challenge) -> None:
    pred = predict_world(world, hero, challenge)
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1.0
    hero.memes["plan"] = hero.memes.get("plan", 0.0) + 1.0
    world.facts["predicted_solved"] = pred["solved"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{hero.id} paused and thought, '{challenge.thought}'"
    )
    world.say(
        f"'If I rush, I might {challenge.risk},' {hero.pronoun()} told {hero.pronoun('object')}self."
    )


def problem_solving(world: World, hero: Entity, challenge: Challenge) -> Optional[Tool]:
    tool = choose_tool(challenge)
    if tool is None:
        return None
    world.say(
        f"{hero.id} looked at {tool.phrase} and had an idea."
    )
    world.say(
        f"{hero.pronoun().capitalize()} used {tool.label} to {tool.use}."
    )
    hero.meters["obstacle_handled"] = 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    return tool


def finish(world: World, hero: Entity, challenge: Challenge, tool: Tool) -> None:
    world.say(
        f"Soon {hero.id} could {challenge.obstacle_verb} and keep going."
    )
    world.say(
        f"With {tool.label}, the problem was solved, and {hero.id} felt proud of thinking it through."
    )
    world.say(
        f"At the end, the path was open again, and the little adventurer went on with a smile."
    )


def tell(setting: Setting, challenge: Challenge, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    pack = world.add(Entity(
        id="pack",
        type="backpack",
        label="a tiny backpack",
        phrase="a map, a cracker, and a little flashlight",
        portable=True,
    ))

    introduction(world, hero)
    setup_few_supplies(world, hero, pack)
    world.para()
    arrive(world, hero, challenge)
    want_forward(world, hero, challenge)
    inner_monologue(world, hero, challenge)
    tool = problem_solving(world, hero, challenge)
    if tool is not None:
        finish(world, hero, challenge, tool)
    world.facts.update(hero=hero, pack=pack, challenge=challenge, setting=setting, tool=tool)
    return world


SETTINGS = {
    "forest path": Setting(place="the forest path", feature="tall trees and soft moss", affords={"river", "dark_tunnel"}),
    "hillside trail": Setting(place="the hillside trail", feature="windy slopes and bright rocks", affords={"river"}),
    "cave mouth": Setting(place="the cave mouth", feature="cool shadows and echoing stone", affords={"dark_tunnel"}),
}


CHALLENGES = {
    "river": Challenge(
        id="river",
        obstacle="wide stream",
        obstacle_verb="cross the stream",
        thought="Maybe I can find stepping stones, or a log, or a safer little bridge",
        risk="slip into the water",
        solves="cross the stream safely",
        keyword="few",
        tags={"water", "bridge"},
    ),
    "dark_tunnel": Challenge(
        id="dark_tunnel",
        obstacle="dark tunnel",
        obstacle_verb="walk through the tunnel",
        thought="Maybe I can use my flashlight and go one careful step at a time",
        risk="bump into the stone wall",
        solves="walk through the tunnel safely",
        keyword="few",
        tags={"light", "stone"},
    ),
}


TOOLS = [
    Tool(
        id="flashlight",
        label="the little flashlight",
        phrase="the tiny flashlight from the pack",
        use="shine light ahead",
        helps={"dark_tunnel"},
        keywords={"light", "few"},
    ),
    Tool(
        id="stick",
        label="a sturdy stick",
        phrase="a sturdy stick lying near the trail",
        use="test the stepping stones",
        helps={"river"},
        keywords={"water", "few"},
    ),
    Tool(
        id="rope",
        label="a short rope",
        phrase="a short rope tucked in the backpack",
        use="steady the crossing",
        helps={"river"},
        keywords={"water", "bridge", "few"},
    ),
]


GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Tia", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Ben", "Theo", "Max", "Finn"]
TRAITS = ["curious", "brave", "quick-thinking", "careful", "spirited"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge_id in setting.affords:
            combos.append((place, challenge_id))
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    return [
        f'Write a short adventure story for a small child that includes the word "few".',
        f"Tell a story where {hero.id} has a few supplies, faces a {challenge.obstacle}, thinks carefully, and solves it.",
        f"Write a gentle adventure with inner monologue and problem solving about {hero.id} at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    challenge: Challenge = f["challenge"]
    tool: Optional[Tool] = f.get("tool")
    qa = [
        QAItem(
            question=f"What kind of adventure did {hero.id} go on?",
            answer=(
                f"{hero.id} went on a little adventure to {world.setting.place}, where {challenge.obstacle} waited."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} have with {hero.pronoun('possessive')} pack?",
            answer=(
                f"{hero.id} had a few things in {hero.pronoun('possessive')} pack, including {f['pack'].phrase}."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} think about before solving the problem?",
            answer=(
                f"{hero.id} thought about how to stay safe and what tool might help with the {challenge.obstacle}."
            ),
        ),
    ]
    if tool is not None:
        qa.append(QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=(
                f"{hero.id} used {tool.label} to {tool.use}, which helped {hero.id} {challenge.solves}."
            ),
        ))
    qa.append(QAItem(
        question=f"How did {hero.id} feel at the end?",
        answer=(
            f"{hero.id} felt proud and relieved because the problem was solved by careful thinking."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    challenge: Challenge = f["challenge"]
    out = [
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight makes a bright beam of light so you can see in dark places.",
        ),
        QAItem(
            question="Why do people use a map on an adventure?",
            answer="People use a map to help them know where they are and choose the right path.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to figure out a good way to fix it or get past it.",
        ),
    ]
    if challenge.id == "river":
        out.append(QAItem(
            question="What is a stepping stone?",
            answer="A stepping stone is a stone you can step on to cross water without getting your feet wet.",
        ))
    if challenge.id == "dark_tunnel":
        out.append(QAItem(
            question="Why can dark places feel scary?",
            answer="Dark places can feel scary because it is harder to see what is around you.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.portable:
            bits.append("portable=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest path", challenge="river", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="cave mouth", challenge="dark_tunnel", name="Eli", gender="boy", trait="careful"),
    StoryParams(place="hillside trail", challenge="river", name="Zoe", gender="girl", trait="brave"),
]


ASP_RULES = r"""
challenge(Place, C) :- affords(Place, C).

tool_fits(T, C) :- tool(T), helps(T, C).

solved(Place, C) :- challenge(Place, C), tool_fits(T, C).

adventure_story(Place, C, Gender) :- solved(Place, C), hero_gender(Gender), challenge(Place, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge_type", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.helps):
            lines.append(asp.fact("helps", tid, c))
    for g in ("girl", "boy"):
        lines.append(asp.fact("hero_gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show challenge/2.\n#show solved/2."))
    return sorted(set(asp.atoms(model, "challenge")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a child with a few supplies solves a small obstacle."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], params.name, params.gender, [params.trait, "thoughtful"])
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
        print(asp_program("#show challenge/2.\n#show solved/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show challenge/2.\n"))
        combos = sorted(set(asp.atoms(model, "challenge")))
        print(f"{len(combos)} compatible (place, challenge) combos:\n")
        for place, chall in combos:
            print(f"  {place:14} {chall}")
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
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
