#!/usr/bin/env python3
"""
storyworlds/worlds/damper_bravery_fairy_tale.py
================================================

A small fairy-tale story world about a brave child, a smoky hearth, and a
damper that must be set just right.

Seed image:
- In a little castle kitchen, a child who wants to be brave must help the cook
  with the hearth.
- If the damper is left wrong, smoke fills the room.
- The child learns that bravery is not roaring loudly; it is doing the careful
  thing even when it feels spooky.

This world keeps the simulation tiny and state-driven:
- physical meters: smoke, warmth, soot, courage-gear readiness
- emotional memes: bravery, worry, pride, trust

The story is generated from the world state, not from a frozen template.
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
    wore: Optional[str] = None
    role: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the castle kitchen"
    dark: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


# World content
SETTINGS = {
    "castle_kitchen": Setting(place="the castle kitchen", dark=True, affords={"hearth"}),
    "tower_room": Setting(place="the tower room", dark=True, affords={"hearth"}),
    "garden_kitchen": Setting(place="the garden kitchen", dark=False, affords={"hearth"}),
}

PROBLEMS = {
    "hearth": Problem(
        id="hearth",
        verb="help with the hearth",
        gerund="tending the hearth",
        risk="smoke",
        zone={"room"},
        keyword="damper",
        tags={"smoke", "hearth", "fire"},
    )
}

TOOLS = [
    Tool(
        id="damper_lever",
        label="the iron damper",
        phrase="a little iron lever in the chimney",
        helps={"smoke"},
        prep="reach up and set the damper just right",
        ending="set the damper just right",
    ),
    Tool(
        id="bellows",
        label="the bellows",
        phrase="soft leather bellows",
        helps={"fire"},
        prep="pump the bellows gently",
        ending="pumped the bellows gently",
    ),
]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Lina", "Ava", "Tessa", "Nora", "Elin"]
BOY_NAMES = ["Finn", "Otto", "Perrin", "Levi", "Bram", "Theo"]
TRAITS = ["brave", "gentle", "curious", "steadfast", "kind"]


def _meters(e: Entity) -> dict[str, float]:
    return e.meters


def _memes(e: Entity) -> dict[str, float]:
    return e.memes


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _add_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def _add_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


def _problem_risk(problem: Problem, tool: Tool) -> bool:
    return problem.keyword == "damper" and "smoke" in tool.helps


def _select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if _problem_risk(problem, tool):
            return tool
    return None


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    world.zone = set(problem.zone)
    _add_meter(hero, "smoke", 1.0)
    _add_meme(hero, "worry", 1.0)
    if narrate:
        world.say(
            f"As {hero.pronoun('subject').capitalize()} worked, the room grew smoky and "
            f"{hero.pronoun('possessive')} eyes began to sting."
        )


def predict_turn(world: World, hero: Entity, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem, narrate=False)
    hero2 = sim.get(hero.id)
    return {
        "smoke": hero2.meters.get("smoke", 0.0),
        "bravery": hero2.memes.get("bravery", 0.0),
        "worry": hero2.memes.get("worry", 0.0),
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once upon a time, there was a little {hero.type} named {hero.id} "
        f"who was known in the castle for being {hero.memes.get('bravery_word', 'brave')} "
        f"when the candles flickered low."
    )


def setup(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} loved the old stories and wanted to be brave like the knights. "
        f"{companion.name_or_label().capitalize()} watched kindly from the doorway."
    )
    world.say(
        f"That evening, {hero.id} and {companion.name_or_label()} went to {world.setting.place}, "
        f"where a little hearth waited like a glowing eye."
    )


def warn(world: World, hero: Entity, companion: Entity, problem: Problem) -> bool:
    pred = predict_turn(world, hero, problem)
    if pred["smoke"] < THRESHOLD:
        return False
    world.facts["pred_smoke"] = pred["smoke"]
    world.say(
        f'"If the {problem.keyword} stays wrong," {companion.pronoun("subject")} said, '
        f'"the smoke will fill the room."'
    )
    return True


def hesitate(world: World, hero: Entity) -> None:
    _add_meme(hero, "worry", 1.0)
    world.say(
        f"{hero.id} swallowed hard. The chimney looked dark, and the little {hero.id} "
        f"felt a wobble in {hero.pronoun('possessive')} knees."
    )


def brave_step(world: World, hero: Entity, companion: Entity, problem: Problem, tool: Tool) -> None:
    _add_meme(hero, "bravery", 1.0)
    _add_meme(hero, "worry", -0.5)
    world.say(
        f"Still, {hero.id} took a brave breath and climbed onto the stool. "
        f"{companion.name_or_label().capitalize()} held the lantern high."
    )
    world.say(
        f"Then {hero.id} reached up and chose to {tool.prep}; {tool.label} was the right "
        f"thing for the smoke."
    )


def resolve(world: World, hero: Entity, companion: Entity, problem: Problem, tool: Tool) -> None:
    _set_meter(hero, "smoke", 0.0)
    _set_meter(hero, "warmth", 1.0)
    _add_meme(hero, "pride", 1.0)
    _add_meme(companion, "trust", 1.0)
    world.say(
        f"The smoke thinned at once. Soon the fire burned clear and warm, and the room "
        f"smelled of bread instead of soot."
    )
    world.say(
        f"{hero.id} smiled, proud and a little taller, because {hero.pronoun('subject')} had "
        f"{tool.ending} all by {hero.pronoun('object')}. "
        f"{companion.name_or_label().capitalize()} smiled too, because bravery had made the night safe."
    )


def tell(setting: Setting, problem: Problem, hero_name: str, gender: str, companion_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        meters={"smoke": 0.0, "warmth": 0.0},
        memes={"bravery": 0.0, "worry": 0.0, "pride": 0.0, "bravery_word": 0.0},
    ))
    hero.memes["bravery_word"] = 1.0
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=companion_type,
        label="the cook" if companion_type == "woman" else "the old keeper",
        memes={"trust": 0.0},
    ))

    intro_traits = {
        "brave": "brave",
        "gentle": "gentle",
        "curious": "curious",
        "steadfast": "steadfast",
        "kind": "kind",
    }
    hero.memes["bravery_word"] = 1.0
    world.say(
        f"Once upon a time, there was a little {gender} named {hero_name} who was "
        f"{intro_traits.get(trait, trait)} and longed to do something worthy of a tale."
    )
    setup(world, hero, companion)
    world.para()
    world.say(
        f"{hero_name} wanted to {problem.verb}, but the hearth was breathing out smoke in the wrong way."
    )
    warn(world, hero, companion, problem)
    hesitate(world, hero)
    tool = _select_tool(problem)
    if tool is None:
        raise StoryError("No reasonable tool exists for this problem.")
    brave_step(world, hero, companion, problem, tool)
    world.para()
    resolve(world, hero, companion, problem, tool)
    world.facts.update(hero=hero, companion=companion, problem=problem, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    return [
        f'Write a short fairy tale about a child named {hero.id} and the word "damper".',
        f"Tell a gentle story where {hero.id} must {problem.verb} and show real bravery.",
        f"Write a child-friendly tale in a castle kitchen where a smoky hearth is fixed by setting the damper just right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do in the castle kitchen?",
            answer=f"{hero.id} was trying to {problem.verb}.",
        ),
        QAItem(
            question=f"Why did the cook or keeper worry about the hearth?",
            answer="They worried because the smoke was building up and could fill the room.",
        ),
        QAItem(
            question=f"What did {hero.id} choose to do to help?",
            answer=f"{hero.id} chose to {tool.prep}, and that was the brave thing to do.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and brave after fixing the damper.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a damper in a hearth or chimney?",
            answer="A damper is a little metal flap or lever that helps control how smoke moves through a fire's chimney.",
        ),
        QAItem(
            question="What does bravery mean in a fairy tale?",
            answer="Bravery means doing the needed thing even when it feels scary or hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:8} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(castle_kitchen).
place(tower_room).
place(garden_kitchen).

problem(hearth).
keyword(hearth, damper).
tool(damper_lever).

risk(hearth, smoke).
helps(damper_lever, smoke).

reasonable(P, Prob, Tool) :- problem(Prob), tool(Tool),
    keyword(Prob, damper), risk(Prob, smoke), helps(Tool, smoke),
    place(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("keyword", pid, prob.keyword))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for help_kind in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, help_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def python_valid() -> list[tuple]:
    out = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            for tool in TOOLS:
                if _problem_risk(PROBLEMS[prob], tool):
                    out.append((place, prob, tool.id))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - p:
        print(" only in asp:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about bravery and a damper.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["woman", "man"])
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
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    place = args.place or rng.choice(list(SETTINGS.keys()))
    problem = args.problem or "hearth"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        params.name,
        params.gender,
        params.companion,
        params.trait,
    )
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
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} reasonable combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("castle_kitchen", "hearth", "Mira", "girl", "woman", "brave"),
            StoryParams("tower_room", "hearth", "Finn", "boy", "man", "curious"),
            StoryParams("garden_kitchen", "hearth", "Tessa", "girl", "woman", "kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
