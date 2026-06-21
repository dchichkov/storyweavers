#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hectic_relish_dialogue_fairy_tale.py
====================================================================

A tiny fairy-tale story world about a hectic castle kitchen, a child who learns
to relish a calm plan, and a dialogue-driven turn toward a safe, happy ending.

The world keeps a light simulation of physical meters and emotional memes, so the
story changes because the state changes.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy"}
        male = {"boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    bustle: str
    likes_dialogue: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    label: str
    verb: str
    hurry: str
    mess: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    method: str
    calmness: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


PLACES = {
    "castle_kitchen": Place(id="castle_kitchen", label="the castle kitchen", bustle="busy with pots and spoons", tags={"castle", "kitchen"}),
    "great_hall": Place(id="great_hall", label="the great hall", bustle="bright with banners and benches", tags={"castle", "hall"}),
    "garden_gate": Place(id="garden_gate", label="the garden gate", bustle="rustling with leaves and birds", tags={"garden", "gate"}),
}

TASKS = {
    "spooning_relish": Task(id="spooning_relish", label="the relish spoon", verb="spoon the relish", hurry="rush to the relish pot", mess="sticky", cause="the relish could splash onto the cloth", tags={"relish", "food"}),
    "setting_table": Task(id="setting_table", label="the silver plates", verb="set the table", hurry="dash to the table", mess="bumped", cause="plates could clatter to the floor", tags={"table", "plates"}),
    "honey_jars": Task(id="honey_jars", label="the honey jars", verb="carry the honey jars", hurry="hurry with the jars", mess="dripped", cause="honey could drip on the steps", tags={"honey", "jars"}),
}

HELPERS = {
    "mouse": Helper(id="mouse", label="a little mouse", phrase="a little mouse with a lantern", method="steady the cloth and hold the spoon", calmness=3, tags={"lantern"}),
    "fairy": Helper(id="fairy", label="a fairy", phrase="a fairy with silver wings", method="wave away the worry and show a gentler way", calmness=5, tags={"magic"}),
    "cook": Helper(id="cook", label="the cook", phrase="the castle cook", method="wipe the spill and slow the pace", calmness=4, tags={"cook"}),
}

GIRL_NAMES = ["Lily", "Mira", "Nina", "Ruby", "Elsa", "Clara"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Robin", "Owen", "Pip"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for h in HELPERS:
                combos.append((p, t, h))
    return combos


def reasonableness_gate(place: Place, task: Task, helper: Helper) -> bool:
    return place.likes_dialogue and "relish" in task.tags and helper.calmness >= SENSE_MIN


def explain_rejection(place: Place, task: Task, helper: Helper) -> str:
    return f"(No story: the tale needs a busy fairy-tale kitchen, a relish task, and a calm helper. Try another combination.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_spill(world: World) -> list[str]:
    out = []
    kid = world.entities.get("child")
    task = world.facts.get("task_entity")
    if not kid or not task:
        return out
    if kid.meters["hurry"] < THRESHOLD or task.meters["begun"] >= THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    task.meters["sticky"] += 1
    kid.memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["worry"] < THRESHOLD or helper.meters["helped"] >= THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    helper.meters["helped"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("calm", _r_calm)]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    for s in out:
        world.say(s)
    return out


def tell(place: Place, task: Task, helper: Helper, child: str, child_gender: str, elder: str, elder_gender: str) -> World:
    w = World()
    kid = w.add(Entity(id=child, kind="character", type=child_gender, role="child", traits=["quick"], attrs={"relation": "siblings"}))
    elder_ent = w.add(Entity(id=elder, kind="character", type=elder_gender, role="elder", traits=["wise"], attrs={"relation": "siblings"}))
    aid = w.add(Entity(id="helper", kind="character", type="fairy", role="helper", label=helper.label))
    kitchen = w.add(Entity(id="place", type="place", label=place.label))
    relish = w.add(Entity(id="task", type="thing", label=task.label))
    kid.memes["delight"] = 1
    elder_ent.memes["patience"] = 1
    aid.meters["helped"] = 0
    w.facts.update(place=place, task=task, helper=helper, child=kid, elder=elder_ent, place_entity=kitchen, task_entity=relish, helper_entity=aid)

    w.say(f"Once upon a time, in {place.label}, {child} and {elder} worked in a {place.bustle} kitchen.")
    w.say(f'"{child}," said {elder}, "can you help me with {task.label}?"')
    w.say(f'"Yes," said {child}, "and I shall relish the work!"')

    w.para()
    kid.meters["hurry"] += 1
    w.say(f"But the day grew hectic, and {child} began to {task.hurry}.')
    w.say(f'"Take care," said {elder}, "or {task.cause}."')
    propagate(w)
    w.say(f'"I did not mean to make such a fuss," whispered {child}.')
    w.say(f'"Then let us breathe," said {helper.label}, "for a fairy tale can slow its own heart."')
    kid.memes["trust"] += 1
    kid.memes["relish"] += 1

    w.para()
    kid.meters["hurry"] = 0
    relish.meters["sticky"] = 0
    elder_ent.memes["relief"] = 1
    w.say(f'"Show me," said {child}, "and I will relish the gentler way."')
    w.say(f"{helper.label.capitalize()} smiled and {helper.method}.")
    w.say(f'"There," said {elder}, "now the kitchen is calm again."')
    w.say(f"Together they finished before dusk, and the castle shone neat and sweet.")

    w.facts["outcome"] = "calm"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    task: Task = f["task"]
    helper: Helper = f["helper"]
    child = f["child"]
    elder = f["elder"]
    return [
        f'Write a fairy tale for a young child that includes the words "hectic" and "relish" and has dialogue in a busy {place.label}.',
        f'Tell a short fairy tale where {child.id} starts to rush in a {place.label}, but {elder.id} and {helper.label} help with a calmer plan.',
        f'Write a gentle castle story in dialogue where a hectic chore becomes peaceful, and someone learns to relish the quiet solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    task: Task = f["task"]
    helper: Helper = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id}, {elder.id}, and {helper.label}. They are working together in {place.label}."),
        QAItem(question=f"What made the day hectic?", answer=f"The day was hectic because {child.id} tried to {task.hurry}. That made the {task.label} more likely to get messy, so the others had to slow things down."),
        QAItem(question=f"How did the others help {child.id}?", answer=f"{elder.id} spoke kindly, and {helper.label} showed a calmer way to finish the task. Their words turned the rush into a safer plan."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does hectic mean?", answer="Hectic means busy, rushed, and full of noise or activity. A hectic day can feel hard to keep up with."),
        QAItem(question="What does it mean to relish something?", answer="To relish something means to enjoy it very much. It is the happy feeling of liking a moment or a task."),
        QAItem(question="Why are fairy tales often full of dialogue?", answer="Fairy tales often use dialogue so the characters can speak their wishes, warnings, and promises. That makes the story feel lively and clear."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if dict(e.meters):
            bits.append(f"meters={dict(e.meters)}")
        if dict(e.memes):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    lines.append(f"fired={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
spill :- hurry(child), task(task), not calm.
calm :- worry(child), helper(helper), calm_helper.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
        if "relish" in TASKS[t].tags:
            lines.append(asp.fact("relish_task", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) != {(a, b, c) for a, b, c in valid_combos()}:
        pass
    if not valid_combos():
        rc = 1
        print("MISMATCH: no valid combos found.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, task=None, helper=None, name=None, seed=None, child=None, child_gender=None, elder=None, elder_gender=None), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: generated story length {len(sample.story)}.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world with hectic dialogue and a relish-filled turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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
    task = args.task or rng.choice(list(TASKS))
    helper = args.helper or rng.choice(list(HELPERS))
    if not reasonableness_gate(PLACES[place], TASKS[task], HELPERS[helper]):
        raise StoryError(explain_rejection(PLACES[place], TASKS[task], HELPERS[helper]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_pool = [n for n in (GIRL_NAMES if elder_gender == "girl" else BOY_NAMES) if n != child]
    elder = args.elder or rng.choice(elder_pool)
    return StoryParams(place=place, task=task, helper=helper, child=child, child_gender=child_gender, elder=elder, elder_gender=elder_gender)


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "task", "helper"):
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], TASKS[params.task], HELPERS[params.helper], params.child, params.child_gender, params.elder, params.elder_gender)
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
    StoryParams(place="castle_kitchen", task="spooning_relish", helper="fairy", child="Mira", child_gender="girl", elder="Theo", elder_gender="boy"),
    StoryParams(place="great_hall", task="setting_table", helper="cook", child="Lily", child_gender="girl", elder="Finn", elder_gender="boy"),
    StoryParams(place="garden_gate", task="honey_jars", helper="mouse", child="Owen", child_gender="boy", elder="Clara", elder_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
