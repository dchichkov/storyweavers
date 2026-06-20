#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/court_strain_kindness_repetition_folk_tale.py
===============================================================================

A standalone story world for a small folk-tale domain: a village court is
stretched by strain, a kind gesture is repeated more than once, and the ending
shows how kindness changes the room.

The story model is intentionally small and classical:
- a helper has a hard task in a court or hall
- the task strains them physically and emotionally
- another character repeats a kind action, which lowers strain
- the court ends with a concrete change that proves the lesson

This script follows the Storyweavers contract:
- stdlib only
- eager results import
- StoryParams/build_parser/resolve_params/generate/emit/main
- Python reasonableness gate plus inline ASP twin
- story, prompts, story_qa, and world_qa generated from simulated state
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    crowd: str
    kind: str = "court"
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    name: str
    strain_word: str
    physical: float
    emotional: float
    duration: int
    repeated: int
    requires_kindness: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Kindness:
    id: str
    name: str
    repeated_phrase: str
    effect: float
    lift: float
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_strain(world: World) -> list[str]:
    out = []
    helper = world.entities.get("helper")
    if helper and helper.meters["carrying"] >= THRESHOLD:
        sig = ("strain",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["strain"] += 1
            helper.memes["worry"] += 1
            out.append("__strain__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.entities.get("helper")
    if not helper:
        return out
    if helper.memes["kindness_received"] >= THRESHOLD and helper.meters["strain"] >= THRESHOLD:
        sig = ("kindness_soothe",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["strain"] = max(0.0, helper.meters["strain"] - 1)
            helper.memes["hope"] += 1
            out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("strain", "physical", _r_strain), Rule("kindness", "social", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def kind_repetition(level: int) -> int:
    return max(1, level)


def reasonableness_ok(setting: Setting, task: Task, kindness: Kindness) -> bool:
    return setting.kind == "court" and task.requires_kindness and task.physical > 0 and kindness.effect > 0


def do_task(world: World, helper: Entity, task: Task) -> None:
    helper.meters["carrying"] += task.physical
    helper.meters["work"] += task.duration
    helper.memes["duty"] += 1
    propagate(world, narrate=False)


def repeat_kindness(world: World, giver: Entity, helper: Entity, kindness: Kindness) -> None:
    repeats = kindness.repeated_phrase
    for _ in range(kind_repetition(2)):
        helper.memes["kindness_received"] += 1
        helper.memes["calm"] += kindness.effect
        helper.meters["strain"] = max(0.0, helper.meters["strain"] - kindness.lift)
    giver.memes["kindness"] += 1
    world.say(f'{giver.id} smiled and said, "{repeats}."')
    world.say(f"{giver.id} said it again, softer than before, and {helper.id} felt steadier.")


def court_opening(world: World, setting: Setting, helper: Entity, giver: Entity, task: Task) -> None:
    helper.memes["hope"] += 1
    world.say(
        f"In a small village court, {setting.detail} filled the room, and the crowd watched quietly. "
        f"{helper.id} came before the court with a hard task in hand."
    )
    world.say(
        f"{helper.id} had to carry {task.name}, and the load began to strain {helper.pronoun('object')} at once."
    )


def court_strain(world: World, helper: Entity, task: Task) -> None:
    world.say(
        f"The longer {helper.id} stood there, the more the strain grew in {helper.pronoun('possessive')} arms and in {helper.pronoun('possessive')} chest."
    )


def court_turn(world: World, giver: Entity, helper: Entity, kindness: Kindness) -> None:
    repeat_kindness(world, giver, helper, kindness)
    repeat_kindness(world, giver, helper, kindness)


def court_resolution(world: World, helper: Entity, task: Task, giver: Entity) -> None:
    helper.meters["carrying"] = 0.0
    helper.meters["strain"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"At last, {helper.id} lifted {task.name} once more, and this time the load felt lighter."
    )
    world.say(
        f"The court grew warm with gratitude, and the old strain was gone from {helper.id}'s face."
    )
    world.say(
        f"{giver.id} stayed beside {helper.id}, and the village remembered that kindness said twice can hold a weary heart upright."
    )


def tell(setting: Setting, task: Task, kindness: Kindness, helper_name: str, helper_gender: str,
         giver_name: str, giver_gender: str, ruler_name: str, ruler_gender: str) -> World:
    world = World(setting)
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    giver = world.add(Entity(id=giver_name, kind="character", type=giver_gender, role="giver"))
    ruler = world.add(Entity(id=ruler_name, kind="character", type=ruler_gender, role="ruler", label="the ruler"))

    court_opening(world, setting, helper, giver, task)
    do_task(world, helper, task)
    court_strain(world, helper, task)
    world.para()
    world.say(f"{giver.id} saw the strain and stepped forward with a kind word.")
    court_turn(world, giver, helper, kindness)
    world.para()
    court_resolution(world, helper, task, giver)
    world.facts.update(setting=setting, task=task, kindness=kindness, helper=helper, giver=giver, ruler=ruler)
    return world


SETTINGS = {
    "oak_court": Setting("oak_court", "the oak court", "the hall smelled of old wood and warm bread", "villagers", tags={"court", "folk"}),
    "river_court": Setting("river_court", "the river court", "the hall was bright with river light on the stone floor", "neighbors", tags={"court", "folk"}),
    "hill_court": Setting("hill_court", "the hill court", "the high room looked down over the village rooftops", "elders", tags={"court", "folk"}),
}

TASKS = {
    "carve_seals": Task("carve_seals", "three wax seals", "strain", physical=2.0, emotional=1.0, duration=2, repeated=2, requires_kindness=True, tags={"strain"}),
    "carry_scrolls": Task("carry_scrolls", "a stack of heavy scrolls", "strain", physical=3.0, emotional=1.5, duration=3, repeated=2, requires_kindness=True, tags={"strain"}),
    "lift_box": Task("lift_box", "a big wooden box", "strain", physical=2.5, emotional=1.2, duration=2, repeated=2, requires_kindness=True, tags={"strain"}),
}

KINDNESSES = {
    "tea": Kindness("tea", "tea", "tea and a soft chair", effect=1.0, lift=0.8, tags={"kindness"}),
    "song": Kindness("song", "song", "a kind song", effect=1.0, lift=0.9, tags={"kindness"}),
    "blanket": Kindness("blanket", "blanket", "a warm blanket", effect=1.2, lift=1.0, tags={"kindness"}),
}

NAMES = ["Mira", "Ivo", "Nina", "Pavel", "Sora", "Toma", "Lina", "Ravi"]
GENDERS = ["girl", "boy", "woman", "man"]


@dataclass
class StoryParams:
    setting: str
    task: str
    kindness: str
    helper: str
    helper_gender: str
    giver: str
    giver_gender: str
    ruler: str
    ruler_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for k in KINDNESSES:
                if reasonableness_ok(SETTINGS[s], TASKS[t], KINDNESSES[k]):
                    combos.append((s, t, k))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale court story about strain and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--helper")
    ap.add_argument("--giver")
    ap.add_argument("--ruler")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--giver-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--ruler-gender", choices=["woman", "man"])
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
    if args.setting and args.task and args.kindness:
        if not reasonableness_ok(SETTINGS[args.setting], TASKS[args.task], KINDNESSES[args.kindness]):
            raise StoryError("This court tale needs a task that truly causes strain and a kindness that can help.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, kindness = rng.choice(sorted(combos))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy", "woman", "man"])
    giver_gender = args.giver_gender or rng.choice(["girl", "boy", "woman", "man"])
    ruler_gender = args.ruler_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(NAMES)
    giver = args.giver or rng.choice([n for n in NAMES if n != helper])
    ruler = args.ruler or rng.choice(["Queen Elen", "King Bram", "Queen Mira", "King Oren"])
    return StoryParams(setting, task, kindness, helper, helper_gender, giver, giver_gender, ruler, ruler_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child that takes place in {f["setting"].place} and includes the words "court" and "strain".',
        f"Tell a story where {f['helper'].id} comes to the court with {f['task'].name}, grows weary from strain, and hears a kind voice repeat itself.",
        f"Write a gentle repetition story about kindness in a village court, where a helper feels strain until repeated kindness makes the work possible.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper, giver, setting, task, kindness = f["helper"], f["giver"], f["setting"], f["task"], f["kindness"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer=f"It was set in a village court. The hall was {setting.detail}, so it felt serious but still warm."
        ),
        QAItem(
            question=f"Why did {helper.id} feel strain?",
            answer=f"{helper.id} had to carry {task.name}, and that heavy work strained {helper.pronoun('object')} right away. The task was hard enough that the strain showed in both {helper.pronoun('possessive')} arms and {helper.pronoun('possessive')} face."
        ),
        QAItem(
            question="What did the kind character do twice?",
            answer=f"{giver.id} repeated a kind phrase twice. That repetition helped {helper.id} calm down and made the work feel possible again."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the task finished, the strain gone, and the court feeling grateful. {giver.id} stayed near {helper.id}, and kindness was remembered as something strong."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a court?",
            answer="A court is a place where people gather to listen, decide, or settle matters. In a folk tale it can feel official, quiet, and important."
        ),
        QAItem(
            question="What does strain mean?",
            answer="Strain is the feeling of effort when something is hard to carry or do. It can make a person tired in both body and heart."
        ),
        QAItem(
            question="Why can kindness help?",
            answer="Kindness can make someone feel safer and less alone. When a hard task feels lighter in the heart, the body often feels steadier too."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
strain(helper) :- carrying(helper), carrying(helper, X), X >= 1.
kindness_helps(helper) :- kindness_received(helper), kindness_count(helper, C), C >= 2.
outcome(steady) :- strain(helper), kindness_helps(helper).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("carry", tid, int(t.physical)))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("kindness_strength", kid, int(k.effect * 10)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    # Gate parity
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in gate:")
        rc = 1
    # smoke test generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def explain_rejection() -> str:
    return "This tale needs a court task that causes real strain, plus a kindness that truly eases it."


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("oak_court", "carve_seals", "tea", "Mira", "girl", "Lina", "girl", "Queen Elen", "woman"),
    StoryParams("river_court", "carry_scrolls", "song", "Ivo", "boy", "Nina", "girl", "King Bram", "man"),
    StoryParams("hill_court", "lift_box", "blanket", "Sora", "woman", "Toma", "man", "Queen Mira", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        KINDNESSES[params.kindness],
        params.helper,
        params.helper_gender,
        params.giver,
        params.giver_gender,
        params.ruler,
        params.ruler_gender,
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


if __name__ == "__main__":
    main()
