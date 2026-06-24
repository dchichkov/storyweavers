#!/usr/bin/env python3
"""
storyworlds/worlds/algae_thunk_inner_monologue_teamwork_repetition_fairy.py
============================================================================

A small fairy-tale story world about a gentle problem involving algae,
a thunking bucket, inner monologue, teamwork, and repeated tries.

Premise:
- A child-like fairy or helper notices a pond is growing too much algae.
- The pond friend needs a clear path, but the gathered tools make a thunk.
- The helper thinks privately, tries once, tries again, and then asks for help.
- With teamwork and repetition, the pond is cleaned and the ending image
  proves the change.

This world keeps story state alive: the pond, tools, helpers, and the helper's
feelings all change as the story unfolds.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"girl", "fairy", "princess", "maid"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "prince", "boy-fairy"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pond"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    first_try: str
    second_try: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    clears: set[str]
    sound: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pond": Setting(place="the pond", affords={"gather", "skim"}),
    "grove": Setting(place="the grove by the pond", affords={"gather", "skim"}),
    "garden": Setting(place="the garden pond", affords={"gather"}),
}

TASKS = {
    "algae": Task(
        id="algae",
        verb="skim the algae from the pond",
        gerund="skimming algae",
        first_try="dip the little net once",
        second_try="dip the little net again and again",
        mess="green",
        soil="cloudy and green",
        keyword="algae",
        tags={"algae", "pond", "green"},
    ),
    "moss": Task(
        id="moss",
        verb="brush the moss from the stones",
        gerund="brushing moss",
        first_try="scrape the stone once",
        second_try="scrape the stone again and again",
        mess="slimy",
        soil="slimy and dull",
        keyword="moss",
        tags={"moss", "stone"},
    ),
}

TOOLS = [
    Tool(
        id="net",
        label="a little net",
        phrase="a little net with a round handle",
        action="scoop",
        clears={"green"},
        sound="thunk",
    ),
    Tool(
        id="pail",
        label="a tin pail",
        phrase="a tin pail with a bright rim",
        action="carry",
        clears={"green", "slimy"},
        sound="clink",
    ),
    Tool(
        id="brush",
        label="a soft brush",
        phrase="a soft brush with a blue ribbon",
        action="brush",
        clears={"slimy"},
        sound="swish",
    ),
]

HERO_NAMES = ["Mira", "Luna", "Ivy", "Nina", "Elin", "Pippa", "Faye", "Tia"]
HELPER_NAMES = ["Moss", "Nell", "Robin", "Perry", "Tobin"]
TRAITS = ["gentle", "brave", "curious", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def task_needs_help(task: Task) -> bool:
    return task.id == "algae"


def compatible_tool(task: Task, tool: Tool) -> bool:
    return task.mess in tool.clears


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id, task in TASKS.items():
            if task.id != "algae":
                continue
            if task.id in setting.affords:
                pass
            for tool in TOOLS:
                if compatible_tool(task, tool):
                    combos.append((place, task_id))
                    break
    return combos


def explain_rejection(task: Task) -> str:
    return (
        "(No story: this fairy-tale world centers on algae, because the pond must "
        "grow cloudy before the helper can notice, think, repeat, and ask for teamwork.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def _do_try(world: World, hero: Entity, task: Task, tool: Tool, attempt: int) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0.0) + 1.0
    if attempt == 1:
        hero.memes["uncertainty"] = hero.memes.get("uncertainty", 0.0) + 1.0
    elif attempt >= 2:
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.facts["attempts"] = attempt


def _cleaning_success(world: World, task: Task, tool: Tool) -> bool:
    return compatible_tool(task, tool)


def tell_story(setting: Setting, task: Task, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="fairy", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="fairy", label=helper_name))
    pond = world.add(Entity(id="pond", kind="thing", type="pond", label="the pond"))
    algae = world.add(Entity(id="algae", kind="thing", type="algae", label="the algae", plural=False, owner="pond"))

    tool = next(t for t in TOOLS if compatible_tool(task, t))
    world.facts.update(hero=hero, helper=helper, pond=pond, algae=algae, task=task, tool=tool, setting=setting)

    world.say(
        f"Once in a little fairy tale, {hero_name} was a {trait} fairy who loved {task.gerund} at {setting.place}."
    )
    world.say(
        f"{hero_name} noticed the pond had too much algae, and the water looked {task.soil}."
    )
    world.say(
        f"In {hero_name}'s private inner monologue, {hero_name} wondered if a tiny helper could make the pond bright again."
    )

    world.para()
    world.say(
        f"{hero_name} picked up {tool.label}, and it made a small {tool.sound} when it tapped the stone."
    )
    _do_try(world, hero, task, tool, attempt=1)
    world.say(
        f"{hero_name} tried to {task.first_try}, but the algae still clung to the water."
    )
    world.say(
        f"{hero_name} thought, quietly, that one try was not enough."
    )
    world.say(
        f"So {hero_name} tried again, this time with patient repetition: {task.second_try}."
    )

    world.para()
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"Then {helper_name} came to help, and together they worked as a team."
    )
    world.say(
        f"{helper_name} held the pail steady while {hero_name} kept skimming, thunk after thunk."
    )
    _do_try(world, hero, task, tool, attempt=2)
    if _cleaning_success(world, task, tool):
        pond.meters["clear"] = pond.meters.get("clear", 0.0) + 1.0
        pond.meters["green"] = 0.0
        algae.meters["gone"] = 1.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
        world.say(
            f"At last, the pond grew clear, and the algae drifted away from the lily pads."
        )
        world.say(
            f"{hero_name} and {helper_name} smiled at the bright water, where a frog could hop happily again."
        )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    task = f["task"].keyword
    tool = f["tool"].label
    return [
        f'Write a fairy-tale story about {hero} and {helper}, where a pond has {task} and a {tool} goes "thunk".',
        f"Tell a gentle story that uses inner monologue, teamwork, and repetition while {hero} cleans {task} from a pond.",
        f"Write a short fairy tale about a child fairy who hears a thunk, thinks quietly, tries again, and works with a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    task = f["task"]
    tool = f["tool"]
    setting = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero} notice at {setting}?",
            answer=f"{hero} noticed that the pond had too much algae, and it looked cloudy and green.",
        ),
        QAItem(
            question=f"What sound did the tool make when {hero} tapped the stone?",
            answer=f"The little net made a small thunk when it tapped the stone.",
        ),
        QAItem(
            question=f"How did {hero} and {helper} fix the pond?",
            answer=f"They worked together, repeated the skimming, and used the tool again until the algae drifted away.",
        ),
        QAItem(
            question=f"Why did {hero} keep trying after the first attempt?",
            answer=f"{hero} thought quietly that one try was not enough, so {hero} tried again with patience and help.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer="The pond became clear and bright again, and the frog had a happy place to hop.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is algae?",
            answer="Algae are tiny water plants that can make pond water look green or cloudy when there is too much of them.",
        ),
        QAItem(
            question="What does thunk mean?",
            answer="Thunk is a short, dull sound something makes when it taps or bumps into something solid.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do one job.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same action again and again until it works better.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking inside a character's mind, not spoken out loud.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task(algae).
task(mess) :- false.

tool(net). tool(pail). tool(brush).
clears(net, green).
clears(pail, green). clears(pail, slimy).
clears(brush, slimy).

valid_combo(Place, algae) :- place(Place), affords(Place, gather), clears(_, green).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("mess", task_id, task.mess))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.clears):
            lines.append(asp.fact("clears", tool.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    clingo_set = set(asp.atoms(model, "valid_combo"))
    python_set = set((place, task) for place, task in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale algae story world with thunking tools.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    if args.task and args.task != "algae":
        raise StoryError(explain_rejection(TASKS[args.task]))
    choices = [(p, t) for p, t in valid_combos()
               if (args.place is None or p == args.place)
               and (args.task is None or t == args.task)]
    if not choices:
        raise StoryError("(No valid fairy-tale combination matches the given options.)")
    place, task = rng.choice(sorted(choices))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, hero=hero, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.place], TASKS[params.task], params.hero, params.helper, params.trait)
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
    StoryParams(place="pond", task="algae", hero="Mira", helper="Robin", trait="gentle"),
    StoryParams(place="grove", task="algae", hero="Luna", helper="Moss", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/2."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for place, task in combos:
            print(f"  {place:10} {task}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
