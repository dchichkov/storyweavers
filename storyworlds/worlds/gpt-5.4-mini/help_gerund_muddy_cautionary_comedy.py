#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/help_gerund_muddy_cautionary_comedy.py
=======================================================================

A standalone story world for a tiny cautionary-comedy domain: a child tries to
help with a muddy chore, gets into a slapstick mess, listens to a grown-up's
warning, and then helps in a safer way.

The storyworld is intentionally small and constraint-driven. It models:
- one child
- one grown-up helper
- one muddy hazard
- one task that is tempting to "help" with
- one sensible safer helping method

The style leans comedic, but the beat is cautionary: the story makes a clear
warning, shows the consequences in the world state, and ends with a safer form
of help that proves what changed.

It supports the standard Storyweavers CLI:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    mud_level: int
    afford_help: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    hazard: str
    warning: str
    consequence: str
    splash: str
    mess: str
    requires_muddy: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gear:
    id: str
    label: str
    action: str
    helps: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_muddy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["muddy"] < THRESHOLD:
            continue
        sig = ("muddy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["embarrassment"] += 1
        out.append("__muddy__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["muddy"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["oops"] += 1
    if "floor" in world.entities:
        world.get("floor").meters["mud"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [Rule("muddy", "physical", _r_muddy), Rule("slip", "physical", _r_slip)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def valid_combo(setting: Setting, task: Task) -> bool:
    return task.id in setting.afford_help and (not task.requires_muddy or setting.mud_level > 0)


def sensible_response_ids() -> list[str]:
    return [r.id for r in RESPONSES.values() if r.sense >= 2]


def predict(world: World, task: Task, response: Response) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("child"), task, narrate=False)
    return {
        "muddy": sim.get("child").meters["muddy"] >= THRESHOLD,
        "oops": sim.get("child").memes["oops"],
    }


def _do_task(world: World, child: Entity, task: Task, narrate: bool = True) -> None:
    child.meters["muddy"] += 1
    child.memes["eager"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {child.id} and {adult.id} were at {setting.place}. "
        f"The place looked {setting.mood}, but the path by the shed was already muddy."
    )
    world.say(
        f"{child.id} loved {setting.afford_help and 'helping' or 'helping anyway'}, especially when there was a job to do."
    )


def want_help(world: World, child: Entity, adult: Entity, task: Task) -> None:
    child.memes["hope"] += 1
    world.say(
        f'{child.id} pointed at the {task.hazard} and said, "I can help! I can '
        f'{task.verb}!"'
    )
    world.say(f'{adult.id} smiled, but {adult.pronoun().capitalize()} knew the mud could be sneaky.')


def warn(world: World, adult: Entity, child: Entity, task: Task) -> None:
    pred = predict(world, task, RESPONSES["towel"])
    world.facts["predicted_oops"] = pred["oops"]
    world.say(
        f'"Careful," said {adult.id}. "{task.warning} If you rush, {task.consequence}."'
    )


def attempt(world: World, child: Entity, task: Task) -> None:
    child.memes["stubborn"] += 1
    world.say(f"{child.id} tried to help anyway and stepped straight into the muddy patch.")
    world.say(f"{child.id} wanted to {task.verb}, but {task.splash}.")


def comedic_mess(world: World, child: Entity) -> None:
    if child.meters["muddy"] >= THRESHOLD:
        world.say(
            f"With one silly squish, {child.id}'s shoes looked like they had been borrowed by a swamp."
        )
        world.say(
            f"Even {child.id}'s socks seemed to be auditioning for the role of tiny brown clouds."
        )


def offer_safer_help(world: World, adult: Entity, child: Entity, task: Task, gear: Gear) -> None:
    child.memes["calm"] += 1
    world.say(
        f'Then {adult.id} pointed to the {gear.label}. "{gear.action}," '
        f"{adult.id} said. \"That is a safer way to help.\""
    )
    world.say(
        f"{child.id} nodded, grabbed the {gear.label}, and {gear.helps} instead."
    )


def finish(world: World, child: Entity, adult: Entity, task: Task) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"At the end, {child.id} was still muddy, but now the muddy part was in the bucket, not on the floor."
    )
    world.say(
        f"{child.id} laughed, {adult.id} laughed, and the job got done without turning the whole day into a mud parade."
    )


def tell(setting: Setting, task: Task, response: Response, gear: Gear,
         child_name: str = "Milo", child_gender: str = "boy",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.add(Entity(id="floor", type="thing", label="the floor"))
    world.add(Entity(id="bucket", type="thing", label="the bucket"))

    introduce(world, child, adult, setting)
    world.para()
    want_help(world, child, adult, task)
    warn(world, adult, child, task)
    attempt(world, child, task)
    child.meters["muddy"] += 1
    comedic_mess(world, child)
    world.para()

    if response.power >= 1:
        world.say(
            f"{adult.id} did not yell. {adult.pronoun().capitalize()} just handed over the {gear.label} and showed a better way."
        )
        offer_safer_help(world, adult, child, task, gear)
        finish(world, child, adult, task)
        outcome = "safe"
    else:
        world.say(
            f"{adult.id} tried to fix it, but the muddy trouble kept spreading."
        )
        outcome = "messy"

    world.facts.update(
        child=child, adult=adult, setting=setting, task=task, response=response,
        gear=gear, outcome=outcome, muddy=child.meters["muddy"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "backyard": Setting("backyard", "the backyard", "cheerful", 1, {"bucket_help", "towel_help"}),
    "garden": Setting("garden", "the garden", "sunny", 2, {"bucket_help", "towel_help"}),
    "shed": Setting("shed", "the shed path", "busy", 1, {"bucket_help"}),
}

TASKS = {
    "bucket": Task("bucket_help", "carry the bucket", "helping carry the bucket",
                   "the bucket was heavy and wobbly", "the bucket tipped and splashed mud",
                   "the muddy water would splash everywhere", "a muddy splash",
                   "muddy", True, {"bucket", "help"}),
    "towel": Task("towel_help", "carry the towel", "helping carry the towel",
                  "the towel dragged low in the mud", "the towel would get muddy",
                  "the muddy path would stain it", "a muddy swish", "muddy", True, {"towel", "help"}),
}

RESPONSES = {
    "towel": Response("towel", 3, 2, "picked up the towel and kept it off the ground",
                      "picked up the towel, but it still got mud all over it",
                      "What did the grown-up do?"),
    "slow": Response("slow", 2, 1, "showed them how to walk slowly and keep the load level",
                     "showed them how to walk slowly, but the mud still splashed",
                     "What did the grown-up do?"),
    "bad": Response("bad", 1, 0, "tried to fix everything at once", "made the mess worse", "What did the grown-up do?"),
}

GEARS = {
    "tray": Gear("tray", "tray", "Use the tray as a helper", "hold the bucket level", {"help"}),
    "cart": Gear("cart", "little cart", "Put it on the cart", "roll it safely", {"help"}),
}

GIRL_NAMES = ["Luna", "Maya", "Tess", "Pia", "Mina"]
BOY_NAMES = ["Milo", "Finn", "Owen", "Theo", "Jack"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    response: str
    gear: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if valid_combo(setting, task):
                out.append((sid, tid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, adult, task = f["child"], f["adult"], f["task"]
    return [
        f'Write a cautionary comedy for a 3-to-5-year-old that includes the word "muddy" and the idea of helping.',
        f"Tell a funny but gentle story where {child.id} wants to {task.verb}, gets muddy, and then learns a safer way to help {adult.id}.",
        f"Write a short story about helping carefully, with a muddy mistake and a safer ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, task, gear = f["child"], f["adult"], f["task"], f["gear"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who wanted to help, and {adult.id}, who knew the muddy path could cause trouble."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to {task.verb}. That sounded helpful, but the muddy ground made it tricky."),
        (f"Why did {adult.id} warn {child.id}?",
         f"{adult.id} warned {child.id} because {task.warning}. If {child.id} rushed, {task.consequence}."),
        ("How did they solve the problem?",
         f"They used the {gear.label} and chose a safer way to help. That kept the job moving without making the mess bigger."),
    ]
    if f["outcome"] == "safe":
        qa.append(("How did the story end?",
                   f"It ended happily and a little silly: {child.id} was muddy, but the real work stayed tidy. The laughter showed the caution had worked."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"muddy", "help"}
    out = []
    if "muddy" in tags:
        out.extend([
            ("What does muddy mean?",
             "Muddy means covered with wet dirt. Muddy things can be slippery and messy."),
        ])
    out.extend([
        ("What does it mean to help?",
         "To help means to do something useful for someone else. Helping can be kind, careful, and useful."),
        ("Why should you walk carefully on muddy ground?",
         "Muddy ground can be slippery, so careful steps can help you avoid slipping and making a bigger mess."),
    ])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("backyard", "bucket", "towel", "tray", "Milo", "boy", "Mom", "mother"),
    StoryParams("garden", "towel", "slow", "cart", "Luna", "girl", "Dad", "father"),
    StoryParams("shed", "bucket", "towel", "tray", "Theo", "boy", "Mom", "mother"),
]


def explain_rejection(setting: Setting, task: Task) -> str:
    return f"(No story: the place and task do not make a sensible muddy-help situation.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(sensible_response_ids()))
    return f"(Refusing response '{rid}': it is too weak on common sense (sense={r.sense}). Try: {better}.)"


ASP_RULES = r"""
valid(S, T) :- setting(S), task(T), afford(S, T).
muddy_needed(T) :- task(T), needs_muddy(T).
valid(S, T) :- afford(S, T), not muddy_needed(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in s.afford_help:
            lines.append(asp.fact("afford", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        if t.requires_muddy:
            lines.append(asp.fact("needs_muddy", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        s = generate(CURATED[0])
        _ = s.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary-comedy muddy-help storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid muddy-help stories exist.")
    setting_id, task_id = rng.choice([c for c in combos if (not args.setting or c[0] == args.setting) and (not args.task or c[1] == args.task)])
    response = args.response or rng.choice(sorted(sensible_response_ids()))
    gear = args.gear or rng.choice(sorted(GEARS))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = args.adult or ( "Mom" if adult_gender == "mother" else "Dad")
    return StoryParams(setting_id, task_id, response, gear, child, gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], RESPONSES[params.response], GEARS[params.gear], params.child, params.child_gender, params.adult, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible settings/tasks:")
        for s, t in asp_valid_combos():
            print(f"  {s:10} {t}")
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
