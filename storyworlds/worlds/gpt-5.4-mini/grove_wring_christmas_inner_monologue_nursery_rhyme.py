#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grove_wring_christmas_inner_monologue_nursery_rhyme.py
=====================================================================================

A small standalone story world for a winter grove tale in nursery-rhyme style.

Seed words:
- grove
- wring
- christmas

Feature:
- Inner Monologue

Style:
- Nursery Rhyme

Premise:
A child is helping in a grove on Christmas Eve, wringing wet greenery or a ribbon,
worrying in an inner monologue that the decorations will not be ready in time.
A gentle helper shows a safer method, and the grove ends up bright and festive.

The world model tracks:
- physical meters like wetness, snugness, shine, and tidy
- emotional memes like worry, hope, pride, and relief

The story is generated from state, not from a frozen paragraph with swapped nouns.
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
class Grove:
    id: str
    name: str
    winter: bool = True
    trees: str = "spruce trees"
    lights: str = "tiny lights"
    scent: str = "pine and cocoa"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    action: str
    inner_voice: str
    mess: str
    good_use: str
    risk: str
    result_word: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Helper:
    id: str
    name: str
    role: str
    method: str
    safe_fix: str
    ready_word: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.grove: Optional[Grove] = None

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.grove = copy.deepcopy(self.grove)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    wreath = world.entities.get("wreath")
    if not child or not wreath:
        return out
    if child.meters["wetting"] < THRESHOLD:
        return out
    sig = ("wet",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wreath.meters["wet"] += 1
    wreath.meters["messy"] += 1
    child.memes["worry"] += 1
    out.append("The wreath grew limp and damp.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["helped"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    out.append("The child felt the knot inside grow loose.")
    return out


CAUSAL_RULES = [
    Rule("wet", "physical", _r_wet),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def wring_risk(task: Task) -> bool:
    return task.id in {"wreath", "ribbon"} and task.mess == "wet"


def helper_sane(helper: Helper) -> bool:
    return helper.id in {"dry_towel", "warm_lamp", "gentle_hook"}


def choose_safe_fix(task: Task) -> Helper:
    for helper in HELPERS.values():
        if helper_sane(helper) and task.id in helper.tags:
            return helper
    raise StoryError("No safe fix exists for this task.")


def forecast(world: World, task: Task) -> dict:
    sim = world.copy()
    _do_wring(sim, narrate=False)
    wreath = sim.get("wreath")
    return {
        "wreath_wet": wreath.meters["wet"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def _do_wring(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    wreath = world.get("wreath")
    child.meters["wetting"] += 1
    wreath.meters["wet"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, grove: Grove, child: Entity, task: Task) -> None:
    world.grove = grove
    child.memes["hope"] += 1
    world.say(
        f"In a little grove on Christmas Eve, {child.id} came with a basket and a bow. "
        f"The {grove.trees} stood hush-hush still, and the air smelled of {grove.scent}."
    )
    world.say(
        f"{child.id} looked at the green wreath and thought, "
        f"'{task.inner_voice}'"
    )


def need_fix(world: World, child: Entity, helper: Helper) -> None:
    world.say(
        f"But the wreath was too wet and twisty, and {child.id} thought, "
        f"'If I wring it hard, the ribbons may crack and the grove will look sad.'"
    )
    world.say(
        f"Then {child.id} heard a kind voice nearby. "
        f"'{helper.method}, and we can still make it ready,' it said."
    )


def resist(world: World, child: Entity, task: Task) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip and whispered, "
        f"'I want the wreath to shine, but wringing it might make it worse.'"
    )


def accept_help(world: World, child: Entity, helper: Helper, task: Task) -> None:
    child.memes["helped"] += 1
    child.memes["trust"] += 1
    child.memes["pride"] += 1
    world.say(
        f"So {child.id} nodded and listened. {helper.safe_fix}."
    )
    world.say(
        f"At once, the wreath looked {helper.ready_word}, and {child.id} felt merry as a bell."
    )


def finish(world: World, child: Entity, grove: Grove, helper: Helper) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"Then the grove glowed under the Christmas lights, and {child.id} hung the wreath "
        f"where it could shine. The little grove looked bright, neat, and done."
    )


def tell(grove: Grove, task: Task, helper: Helper, name: str = "Mina", gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    wreath = world.add(Entity(id="wreath", kind="thing", type="thing", label="wreath"))
    child.memes["worry"] = 1.0
    world.say(
        f"In a little grove on Christmas Eve, {name} was busy by the tree."
    )
    setup(world, grove, child, task)
    world.para()
    need_fix(world, child, helper)
    resist(world, child, task)
    _do_wring(world, narrate=True)
    world.para()
    accept_help(world, child, helper, task)
    finish(world, child, grove, helper)
    world.facts.update(
        child=child,
        wreath=wreath,
        grove=grove,
        task=task,
        helper=helper,
        outcome="safe",
    )
    return world


GROVES = {
    "fir": Grove("fir", "fir grove", True, "fir trees", "string lights", "cool pine"),
    "pine": Grove("pine", "pine grove", True, "pine boughs", "gold lights", "sweet sap"),
}

TASKS = {
    "wreath": Task(
        "wreath",
        "wring the wreath dry",
        "I hope the wreath will be ready before the bells.",
        "wet",
        "hang it neatly",
        "wringing could make the needles bend",
        "ready",
        tags={"wreath", "christmas", "grove"},
    ),
    "ribbon": Task(
        "ribbon",
        "wring the ribbon dry",
        "I hope the ribbon will not tangle before Christmas.",
        "wet",
        "tie it gently",
        "wringing could make the loops twist",
        "smooth",
        tags={"ribbon", "christmas", "grove"},
    ),
}

HELPERS = {
    "dry_towel": Helper(
        "dry_towel",
        "dry towel",
        "helper",
        "Do not wring it hard",
        "pat it dry with a soft towel and lay it flat",
        "tidy and bright",
        tags={"wreath", "ribbon"},
    ),
    "warm_lamp": Helper(
        "warm_lamp",
        "warm lamp",
        "helper",
        "Do not squeeze the wet green bits",
        "set it near a warm lamp and let it drip",
        "neater",
        tags={"wreath", "ribbon"},
    ),
    "gentle_hook": Helper(
        "gentle_hook",
        "gentle hook",
        "helper",
        "Do not twist the ribbon tight",
        "hang it on a gentle hook and smooth it with two hands",
        "smooth and sweet",
        tags={"ribbon"},
    ),
}

NAMES = ["Mina", "Ella", "Nora", "Lily", "Ada", "Rose", "Ivy", "Clara"]
TRAITS = ["careful", "cheerful", "tender", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for gid in GROVES:
        for tid in TASKS:
            task = TASKS[tid]
            if wring_risk(task):
                for hid, helper in HELPERS.items():
                    if tid in helper.tags and helper_sane(helper):
                        combos.append((gid, tid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    grove: str
    task: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


KNOWLEDGE = {
    "grove": [("What is a grove?", "A grove is a small group of trees growing close together.")],
    "christmas": [("What is Christmas?", "Christmas is a winter holiday with lights, gifts, songs, and family cheer.")],
    "wreath": [("What is a wreath?", "A wreath is a ring of leaves, flowers, or branches used as decoration.")],
    "ribbon": [("What is a ribbon?", "A ribbon is a strip of cloth that can be tied in bows and loops.")],
    "dry": [("Why do people dry wet things?", "People dry wet things so they feel neat, light, and ready to use.")],
    "wring": [("What does wring mean?", "To wring something means to twist or squeeze it to push water out.")],
}
KNOWLEDGE_ORDER = ["grove", "christmas", "wreath", "ribbon", "wring", "dry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story with inner monologue that uses the words "grove", "wring", and "Christmas".',
        f"Tell a gentle Christmas story about {f['child'].id} in a grove, where {f['child'].id} thinks to {f['task'].action} but chooses a safer way.",
        f"Write a rhyming, child-friendly story where a child worries in an inner monologue, then gets help and ends the grove looking festive.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, task, helper, grove = f["child"], f["task"], f["helper"], f["grove"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who is helping in the {grove.name} on Christmas Eve. The child is the one who worries in an inner monologue and then learns a gentler way.",
        ),
        (
            "What did the child want to do?",
            f"{child.id} wanted to {task.action}. The child thought it might help, but also worried it could make the decorations worse.",
        ),
        (
            "How did the child solve the problem?",
            f"With help from the {helper.name}, the child chose a safer way instead of wringing too hard. That kept the wreath neat and ready for Christmas.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fir", "wreath", "dry_towel", "Mina", "girl", "careful"),
    StoryParams("pine", "ribbon", "gentle_hook", "Lily", "girl", "patient"),
]


def explain_rejection(task: Task) -> str:
    return f"(No story: {task.action} does not fit this little Christmas grove.)"


def explain_helper(helper: Helper, task: Task) -> str:
    if task.id not in helper.tags:
        return f"(No story: the {helper.name} does not help with that task.)"
    return ""


def asp_facts() -> str:
    import asp
    lines = []
    for gid in GROVES:
        lines.append(asp.fact("grove", gid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("action", tid, t.action.replace(" ", "_")))
        lines.append(asp.fact("mess", tid, t.mess))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for tag in sorted(h.tags):
            lines.append(asp.fact("helps", hid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(G,T,H) :- grove(G), task(T), helper(H), tag(T,"christmas"), helps(H,T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in valid_combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme Christmas grove story world with inner monologue.")
    ap.add_argument("--grove", choices=GROVES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.grove and args.task and args.helper:
        if (args.grove, args.task, args.helper) not in combos:
            raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in combos if (args.grove is None or c[0] == args.grove)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    grove, task, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(grove, task, helper, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = World()
    grove = GROVES[params.grove]
    task = TASKS[params.task]
    helper = HELPERS[params.helper]
    story_world = tell(grove, task, helper, params.name, params.gender)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=[QAItem(q, a) for q, a in story_qa(story_world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(story_world)],
        world=story_world,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.grove}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
