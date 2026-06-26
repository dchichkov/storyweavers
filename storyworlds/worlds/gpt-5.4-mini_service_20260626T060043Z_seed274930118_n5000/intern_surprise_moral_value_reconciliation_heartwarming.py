#!/usr/bin/env python3
"""
A small storyworld about an intern, a surprising discovery, a moral choice,
and a warm reconciliation.
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
# Parameters and registry content
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    place: str
    light: str
    has_window: bool = False


@dataclass(frozen=True)
class Task:
    id: str
    verb: str
    object: str
    surprise: str
    moral_value: str
    reveal: str
    repair: str
    tension: str


@dataclass(frozen=True)
class Gift:
    id: str
    label: str
    phrase: str
    message: str


SETTINGS = {
    "office": Setting(place="the office", light="soft morning light", has_window=True),
    "studio": Setting(place="the studio", light="golden afternoon light", has_window=True),
    "library": Setting(place="the library corner", light="quiet lamp light", has_window=False),
}

TASKS = {
    "cards": Task(
        id="cards",
        verb="sort",
        object="a stack of thank-you cards",
        surprise="the cards were actually for the intern",
        moral_value="kindness matters most when someone feels unseen",
        reveal="the mentor had been preparing a surprise note of praise",
        repair="the intern helped finish the cards and wrote a note back",
        tension="the intern thought they had messed everything up",
    ),
    "lanterns": Task(
        id="lanterns",
        verb="hang",
        object="paper lanterns",
        surprise="the lanterns were hiding a tiny celebration",
        moral_value="honesty keeps a team gentle and strong",
        reveal="the team had planned a surprise welcome for the intern",
        repair="the intern told the truth and helped set the table",
        tension="the intern worried they had ruined the surprise",
    ),
    "plan": Task(
        id="plan",
        verb="organize",
        object="a project plan",
        surprise="the plan had a secret page full of thank-yous",
        moral_value="sharing credit makes work feel brighter",
        reveal="the mentor wanted the intern to see their good work first",
        repair="the intern added everyone’s names and smiled with relief",
        tension="the intern feared they had changed the plan the wrong way",
    ),
}

GIFTS = {
    "flower": Gift(
        id="flower",
        label="a small flower",
        phrase="a small flower wrapped in paper",
        message="It said, 'You helped this place bloom.'",
    ),
    "cookie": Gift(
        id="cookie",
        label="a warm cookie",
        phrase="a warm cookie on a blue napkin",
        message="It said, 'You make our days sweeter.'",
    ),
    "bookmark": Gift(
        id="bookmark",
        label="a bright bookmark",
        phrase="a bright bookmark tied with ribbon",
        message="It said, 'You kept every page moving forward.'",
    ),
}

NAMES = ["Maya", "Noah", "Lina", "Owen", "Iris", "Eli", "Nina", "Theo"]
MENTOR_NAMES = ["Ms. Chen", "Mr. Alvarez", "Dr. Patel", "Ms. Rivera"]
TRAITS = ["careful", "curious", "kind", "earnest", "gentle"]


@dataclass
class StoryParams:
    setting: str
    task: str
    gift: str
    name: str
    mentor: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    task: Task
    gift: Gift
    intern: Entity
    mentor: Entity
    story_bits: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_bits)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
setting(office). setting(studio). setting(library).
task(cards). task(lanterns). task(plan).
gift(flower). gift(cookie). gift(bookmark).

good_combo(S,T,G) :- setting(S), task(T), gift(G).
valid(S,T,G) :- good_combo(S,T,G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World model and narrative
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, g) for s in SETTINGS for t in TASKS for g in GIFTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming intern surprise storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--mentor", choices=MENTOR_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    gift = args.gift or rng.choice(list(GIFTS))
    name = args.name or rng.choice(NAMES)
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, gift=gift, name=name, mentor=mentor, trait=trait)


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    gift = GIFTS[params.gift]
    intern = Entity(
        id=params.name,
        kind="character",
        label=params.name,
        type="intern",
        meters={"work": 1.0},
        memes={"curiosity": 1.0, "care": 1.0},
    )
    mentor = Entity(
        id=params.mentor,
        kind="character",
        label=params.mentor,
        type="mentor",
        meters={"work": 1.0},
        memes={"warmth": 1.0},
    )
    return World(setting=setting, task=task, gift=gift, intern=intern, mentor=mentor)


def _story_prefix(world: World, params: StoryParams) -> None:
    world.say(
        f"{params.name} was a {params.trait} intern at {world.setting.place}. "
        f"The day felt full of {world.setting.light.lower()}, and {params.name} wanted to help in a useful way."
    )
    world.say(
        f"That morning, {params.name} tried to {world.task.verb} {world.task.object} for {params.mentor}."
    )


def _surprise(world: World, params: StoryParams) -> None:
    world.intern.memes["surprise"] = 1.0
    world.intern.meters["attention"] = 1.0
    world.say(
        f"Then came a surprise: {world.task.surprise}. "
        f"{params.name} blinked, because the room suddenly felt much bigger than before."
    )


def _moral_turn(world: World, params: StoryParams) -> None:
    world.intern.memes["worry"] = 1.0
    world.say(
        f"{params.name} worried they had done something wrong. "
        f"But {world.task.moral_value}, and {params.name} remembered to be honest."
    )
    world.say(
        f"{params.name} took a careful breath and told {params.mentor} what had happened."
    )


def _reconciliation(world: World, params: StoryParams) -> None:
    world.intern.memes["relief"] = 1.0
    world.mentor.memes["warmth"] = 2.0
    world.intern.memes["joy"] = 1.0
    world.say(
        f"{params.mentor} smiled instead of scolding. "
        f"{world.task.reveal}."
    )
    world.say(
        f"Together they fixed the little mistake. {world.task.repair}. "
        f"{params.mentor} set out {world.gift.phrase}, and {world.gift.message}"
    )
    world.say(
        f"{params.name} felt the tight knot in their chest loosen. "
        f"By the end, the intern and mentor were side by side again, "
        f"and the room felt warm with trust."
    )


def generate_world(params: StoryParams) -> World:
    world = _make_world(params)
    _story_prefix(world, params)
    world.say("")
    _surprise(world, params)
    world.say("")
    _moral_turn(world, params)
    world.say("")
    _reconciliation(world, params)
    world.facts = {
        "setting": params.setting,
        "task": params.task,
        "gift": params.gift,
        "name": params.name,
        "mentor": params.mentor,
        "trait": params.trait,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about an intern named {f['name']} who finds a surprise while {world.task.verb} {world.task.object}.",
        f"Tell a gentle story set in {world.setting.place} about an intern, an honest mistake, and a kind reconciliation.",
        f"Write a short story for children where {f['name']} learns a moral value and ends with a warm gift and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {f['name']}, a {f['trait']} intern at {world.setting.place}.",
        ),
        QAItem(
            question=f"What surprise did {f['name']} discover?",
            answer=f"{world.task.surprise.capitalize()}.",
        ),
        QAItem(
            question=f"What did {f['name']} do after feeling worried?",
            answer=f"{f['name']} told {f['mentor']} the truth and helped repair the mistake.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{f['name']} and {f['mentor']} reconciled, shared a warm moment, and ended on a kind, happy note.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an intern?",
            answer="An intern is someone who is learning by helping with real work for a time.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a misunderstanding or hurt feelings.",
        ),
        QAItem(
            question="What does a moral value mean in a story?",
            answer="A moral value is the lesson about being kind, honest, fair, or responsible.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes someone stop and notice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.intern, world.mentor]:
        lines.append(
            f"  {ent.label:10} ({ent.type}) meters={dict(ent.meters)} memes={dict(ent.memes)}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  task: {world.task.id}")
    lines.append(f"  gift: {world.gift.id}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Curated variants
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="office", task="cards", gift="flower", name="Maya", mentor="Ms. Chen", trait="kind"),
    StoryParams(setting="studio", task="lanterns", gift="cookie", name="Noah", mentor="Mr. Alvarez", trait="careful"),
    StoryParams(setting="library", task="plan", gift="bookmark", name="Lina", mentor="Dr. Patel", trait="earnest"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params = StoryParams(
                setting=params.setting,
                task=params.task,
                gift=params.gift,
                name=params.name,
                mentor=params.mentor,
                trait=params.trait,
                seed=seed,
            )
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
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
