#!/usr/bin/env python3
"""
A tiny superhero story world with cautionary conflict, sound effects, and a
small counted team action built around nine helpers.

Seed premise:
A young hero wants to rush into a risky showdown, but a mentor warns them to
stay together, use signal gear, and not abandon the plan. Nine teammates,
sirens, and comic-book sound effects drive the turn and resolution.

The world model tracks:
- physical meters: danger, damage, noise, signal, teamwork, rescue progress
- emotional memes: courage, caution, conflict, trust, relief, pride, fear
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


# ---------------------------------------------------------------------------
# Small reusable world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    allies: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["danger", "damage", "noise", "signal", "teamwork", "rescue"]:
            self.meters.setdefault(key, 0.0)
        for key in ["courage", "caution", "conflict", "trust", "relief", "pride", "fear"]:
            self.memes.setdefault(key, 0.0)


@dataclass
class SoundEffect:
    cue: str
    text: str


@dataclass
class Setting:
    place: str
    indoors: bool
    time: str
    signature: str


@dataclass
class Plan:
    objective: str
    risk: str
    cautionary_warning: str
    sound_cue: str
    team_size: int = 9


@dataclass
class StoryParams:
    place: str
    hero: str
    mentor: str
    villain: str
    plan: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS: dict[str, Setting] = {
    "skybridge": Setting(place="the skybridge", indoors=False, time="late afternoon", signature="windy"),
    "museum": Setting(place="the city museum", indoors=True, time="evening", signature="quiet halls"),
    "harbor": Setting(place="the harbor", indoors=False, time="sunset", signature="salt air"),
}

PLANS: dict[str, Plan] = {
    "signal": Plan(
        objective="restore the beacon light",
        risk="the tower could spark if anyone rushed in alone",
        cautionary_warning="Do not abandon the team, and do not touch the breaker box without a signal",
        sound_cue="BEEP! WHOOOSH!",
    ),
    "rescue": Plan(
        objective="free the trapped captain",
        risk="the doors could slam shut if the hero moved too fast",
        cautionary_warning="Stay together, count to nine, and only go when the signal flashes",
        sound_cue="KRAK! CLANG!",
    ),
    "bridge": Plan(
        objective="steady the broken bridge cables",
        risk="the cables could snap if someone pulled the wrong one",
        cautionary_warning="Use the hand signs, trust the plan, and never abandon the rope line",
        sound_cue="TWANG! ZIP!",
    ),
}

HEROES = ["Nova", "Spark", "Comet", "Vector", "Mira", "Jett"]
MENTORS = ["Captain Lantern", "Aunt Aurora", "Beacon Chief", "Doctor Halo"]
VILLAINS = ["the Shadow Kite", "Static Fang", "Drift, the Storm Fox", "Captain Muck"]
TRAITS = ["brave", "quick", "bright", "kind", "stubborn", "careful", "hopeful"]

SFX = [
    SoundEffect("alert", "WEE-OO! WEE-OO!"),
    SoundEffect("impact", "BAM!"),
    SoundEffect("movement", "WHOOSH!"),
    SoundEffect("surprise", "POP!"),
    SoundEffect("team", "CLICK-CLACK!"),
]

NINE_NAMES = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting, plan: Plan) -> None:
        self.setting = setting
        self.plan = plan
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        clone = World(self.setting, self.plan)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, mentor: Entity, villain: Entity) -> None:
    world.say(
        f"{hero.id} was a {world.facts['hero_trait']} young hero who kept a tiny watch in "
        f"{hero.label} and listened for trouble across {world.setting.place}."
    )
    world.say(
        f"{mentor.label} knew how to read sirens and shadows, while {villain.label} kept making "
        f"{world.facts['villain_noise']} sounds from far away."
    )


def gather_nine(world: World, hero: Entity) -> list[Entity]:
    team: list[Entity] = []
    for i in range(9):
        ally = world.add(Entity(
            id=f"Helper {i + 1}",
            kind="character",
            type="sidekick",
            label=f"Helper {i + 1}",
            owner=hero.id,
        ))
        ally.meters["teamwork"] = 1.0
        ally.memes["trust"] = 1.0
        team.append(ally)
    hero.allies = [a.id for a in team]
    world.facts["team_size"] = len(team)
    world.say(
        f"Nine helpers showed up one by one: {', '.join(NINE_NAMES[:-1])}, and nine. "
        f"They wore bright badges and stood in a careful circle around {hero.id}."
    )
    return team


def warning(world: World, mentor: Entity, hero: Entity) -> None:
    hero.memes["caution"] += 1
    hero.memes["fear"] += 1
    world.say(
        f'"{world.plan.cautionary_warning}," {mentor.label} warned. '
        f'"A hero can be bold without being reckless."'
    )
    world.say(
        f"{hero.id} wanted to rush, but the warning landed like a cold splash of rain."
    )


def false_start(world: World, hero: Entity, villain: Entity) -> None:
    hero.memes["conflict"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} tried to dash ahead anyway, and the air answered with {world.facts['sound_effect'].text}."
    )
    world.say(
        f"At once, {villain.label} fired a glare that made the lights wobble and the danger meter climb."
    )
    hero.meters["danger"] += 1
    hero.meters["noise"] += 1


def regroup(world: World, hero: Entity, mentor: Entity) -> None:
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0
    world.say(
        f"{hero.id} stopped, took a breath, and looked back at the nine helpers. "
        f"{mentor.label} pointed at the signal light, and everyone remembered the plan."
    )


def execute_plan(world: World, hero: Entity, villain: Entity) -> None:
    hero.meters["signal"] += 1
    hero.meters["rescue"] += 2
    hero.meters["danger"] = max(0.0, hero.meters["danger"] - 1)
    hero.memes["pride"] += 1
    world.say(
        f"The signal flashed {world.plan.sound_cue}. Nine helpers pulled together, and {hero.id} followed the rope line."
    )
    world.say(
        f"With no one abandoned and no one alone, they {world.plan.objective}, and {villain.label}'s tricks fell quiet."
    )


def resolve(world: World, hero: Entity, mentor: Entity, villain: Entity) -> None:
    hero.memes["relief"] += 1
    mentor.memes["pride"] += 1
    world.say(
        f"By the end, {hero.id} was laughing again, {mentor.label} was smiling, and {villain.label} had vanished into the dark."
    )
    world.say(
        f"The nine helpers stood together beneath the steady lights, and the city sounded safe at last."
    )


def tell(setting: Setting, plan: Plan, hero_name: str, mentor_name: str, villain_name: str) -> World:
    world = World(setting, plan)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label=f"{hero_name}'s belt"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="mentor", label=mentor_name))
    villain = world.add(Entity(id=villain_name, kind="character", type="villain", label=villain_name))

    world.facts.update(
        hero=hero,
        mentor=mentor,
        villain=villain,
        hero_trait=random.choice(TRAITS),
        villain_noise=random.choice(["clangy", "crackly", "roaring", "humming"]),
        sound_effect=random.choice(SFX),
    )

    introduce(world, hero, mentor, villain)
    world.para()
    gather_nine(world, hero)
    warning(world, mentor, hero)
    false_start(world, hero, villain)
    world.para()
    regroup(world, hero, mentor)
    execute_plan(world, hero, villain)
    resolve(world, hero, mentor, villain)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for children that includes the number nine and the word "abandon".',
        f"Tell a superhero story where {f['hero'].id} nearly rushes into danger, but {f['mentor'].label} gives a cautionary warning.",
        f"Write a comic-book style story with sound effects, teamwork, and a brave choice that saves the day at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mentor: Entity = f["mentor"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, a young hero who had to learn to slow down and trust the team.",
        ),
        QAItem(
            question=f"Why did {mentor.label} give a cautionary warning?",
            answer=f"{mentor.label} warned everyone because the plan was risky and rushing in alone could make the danger worse.",
        ),
        QAItem(
            question=f"What did the nine helpers do?",
            answer=f"The nine helpers gathered around {hero.id}, stayed together, and helped carry out the rescue plan.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} following the signal, the danger fading, and the city becoming safe again.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tried to rush ahead?",
            answer=f"When {hero.id} rushed ahead, the conflict rose, a loud sound effect burst out, and everyone had to regroup.",
        ),
        QAItem(
            question=f"Did anyone abandon the team?",
            answer=f"No, nobody abandoned the team. The story made it clear that the hero should stay with the nine helpers.",
        ),
        QAItem(
            question=f"What did {villain.label} do to cause trouble?",
            answer=f"{villain.label} made the situation more dangerous by throwing scary tricks and noisy distractions into the scene.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cautionary warning?",
            answer="A cautionary warning is a message that tells someone to be careful because something could go wrong.",
        ),
        QAItem(
            question="What are sound effects in a superhero story?",
            answer="Sound effects are lively words like BAM, WHOOSH, or KRAK that make action scenes feel exciting.",
        ),
        QAItem(
            question="Why do heroes use teamwork?",
            answer="Heroes use teamwork so they can solve hard problems together instead of making risky choices alone.",
        ),
        QAItem(
            question="Why is it smart not to abandon a plan in the middle of danger?",
            answer="It is smart to stay with the plan because changing course too soon can make everyone less safe.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.allies:
            bits.append(f"allies={len(e.allies)}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  plan={world.plan.objective}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts from registries:
% place(P). plan(Plan). hero(H). mentor(M). villain(V).
% sound(Cue).

% A full story is reasonable when the setting, plan, and team size exist together.
valid_story(P, Plan, nine) :- place(P), plan(Plan), team_size(nine).

% A cautionary conflict story must include a warning and a risky rush.
cautionary_conflict(P, Plan) :- valid_story(P, Plan, nine), cautionary(Plan), conflict(Plan).

% Sound-heavy superhero stories use at least one sound effect.
sound_story(P, Plan) :- valid_story(P, Plan, nine), sound_effect(Plan).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
    for key in PLANS:
        lines.append(asp.fact("plan", key))
        lines.append(asp.fact("cautionary", key))
        lines.append(asp.fact("conflict", key))
        lines.append(asp.fact("sound_effect", key))
    lines.append(asp.fact("team_size", 9))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, plan, 9) for p in SETTINGS for plan in PLANS}
    if asp_set != py_set:
        print("MISMATCH between clingo and python:")
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: clingo gate matches python ({len(py_set)} combos).")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with nine helpers and cautionary conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--plan", choices=PLANS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HEROES)
    mentor = args.mentor or rng.choice(MENTORS)
    villain = args.villain or rng.choice(VILLAINS)
    plan = args.plan or rng.choice(list(PLANS))

    if len({hero, mentor, villain}) < 3:
        raise StoryError("Choose different names for the hero, mentor, and villain.")
    return StoryParams(place=place, hero=hero, mentor=mentor, villain=villain, plan=plan)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    plan = PLANS[params.plan]
    world = tell(setting, plan, params.hero, params.mentor, params.villain)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for triple in asp_valid_stories():
            print(triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        combos = [
            StoryParams(place=p, hero=h, mentor=m, villain=v, plan=pl)
            for p in SETTINGS
            for h in HEROES[:2]
            for m in MENTORS[:2]
            for v in VILLAINS[:2]
            for pl in PLANS
        ]
        samples = [generate(cp) for cp in combos[: max(1, args.n)]]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
