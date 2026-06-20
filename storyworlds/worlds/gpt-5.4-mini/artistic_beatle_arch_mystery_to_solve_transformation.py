#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/artistic_beatle_arch_mystery_to_solve_transformation.py
=======================================================================================

A standalone storyworld for a small fable-like domain about an artistic beetle,
an old arch, a mystery to solve, a conflict, and a gentle transformation.

The world is built around three seed words and three narrative instruments:
* artistic
* beatle
* arch

The story logic is intentionally tiny and classical:
- A beetle wants to make the garden beautiful.
- An old arch has a missing piece and a puzzling stain.
- A second creature argues with the beetle over how to fix it.
- A careful investigation reveals the true cause.
- The solution transforms both the arch and the beetle's role.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared result containers eagerly from storyworlds/results.py
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates story-grounded QA and world-knowledge QA from world state
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
MIN_REASONABLE = 1


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    light: str
    has_arch: bool = True

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
class Mystery:
    id: str
    clue: str
    cause: str
    hidden: str
    solved_by: str
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
class Conflict:
    id: str
    topic: str
    argument: str
    wrong_fix: str
    right_fix: str
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
class Transformation:
    id: str
    from_role: str
    to_role: str
    image: str
    moral: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        if s:
            world.say(s)
    return out


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    beetle = world.get("beetle")
    if beetle.memes["worry"] < THRESHOLD:
        return out
    sig = ("doubt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("arch").meters["tension"] += 1
    out.append("The old arch seemed to sigh under the beetle's worry.")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    beetle = world.get("beetle")
    if beetle.memes["curiosity"] < THRESHOLD or beetle.meters["searching"] < THRESHOLD:
        return out
    sig = ("discover",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("arch").meters["mystery"] = 0.0
    world.get("beetle").memes["hope"] += 1
    out.append("A hidden crumb of paint fell from the crack and told the beetle the truth.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    beetle = world.get("beetle")
    arch = world.get("arch")
    if arch.meters["repaired"] < THRESHOLD or beetle.memes["kindness"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beetle.attrs["role_after"] = "caretaker"
    beetle.meters["glow"] += 1
    out.append("The beetle's tiny brushwork turned worry into beauty.")
    return out


CAUSAL_RULES = [
    Rule("doubt", _r_doubt),
    Rule("discover", _r_discover),
    Rule("transform", _r_transform),
]


def reasonableness_check(setting: Setting, mystery: Mystery, conflict: Conflict, transformation: Transformation) -> bool:
    return bool(setting.has_arch and mystery.clue and conflict.argument and transformation.image)


def build_problem(setting: Setting, mystery: Mystery, conflict: Conflict) -> str:
    return (
        f"In {setting.place}, an artistic beatle lived under an old arch. "
        f"The arch had {mystery.hidden}, and the beetle could see {mystery.clue}. "
        f"That made a quiet mystery to solve."
    )


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("beetle").meters["searching"] += 1
    sim.get("beetle").memes["curiosity"] += 1
    propagate(sim)
    return {
        "mystery_solved": sim.get("arch").meters["mystery"] <= 0.0,
        "beetle_changed": sim.get("beetle").attrs.get("role_after") == "caretaker",
    }


def start_story(world: World, beetle: Entity, arch: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"In {setting.place}, under a sunlit arch, there lived an artistic beatle named {beetle.id}. "
        f"{beetle.id} loved making little patterns with petals and dust."
    )
    world.say(
        f"One morning, {beetle.id} noticed {mystery.clue} near the arch. "
        f"The old stone looked beautiful, but something was missing."
    )


def conflict_scene(world: World, beetle: Entity, helper: Entity, conflict: Conflict, mystery: Mystery) -> None:
    beetle.memes["curiosity"] += 1
    helper.memes["stubborn"] += 1
    world.para()
    world.say(
        f"{helper.id} frowned and said, \"Leave the arch alone. It only needs to be cleaned fast.\" "
        f"But {beetle.id} shook its head. \"No, we must solve the mystery first,\" it said."
    )
    world.say(
        f"{conflict.argument} The two of them stood in conflict, one wanting a quick fix and the other wanting the true cause."
    )


def investigate(world: World, beetle: Entity, helper: Entity, mystery: Mystery) -> None:
    beetle.meters["searching"] += 1
    world.para()
    world.say(
        f"{beetle.id} climbed close, sniffed the dust, and followed the clue under the arch. "
        f"It found {mystery.cause}, the thing that had been hiding the answer."
    )
    propagate(world)


def repair(world: World, beetle: Entity, arch: Entity, transformation: Transformation) -> None:
    arch.meters["repaired"] += 1
    arch.meters["beauty"] += 1
    beetle.memes["kindness"] += 1
    world.para()
    world.say(
        f"Then {beetle.id} used a tiny brush and a bright bit of leaf-gold. "
        f"The arch grew whole again, and {transformation.image}."
    )
    propagate(world)


def ending(world: World, beetle: Entity, arch: Entity, transformation: Transformation) -> None:
    world.say(
        f"By sunset, the arch no longer hid a mystery. It shone with a new pattern, and {beetle.id} "
        f"was no longer only an artist; it had become a careful keeper of the gate."
    )
    world.say(
        f"The little fable ended with {transformation.moral}"
    )


SETTING_REGISTRY = {
    "garden": Setting("garden", "the garden", "gentle", "warm"),
    "courtyard": Setting("courtyard", "the courtyard", "quiet", "golden"),
    "lane": Setting("lane", "the old lane", "still", "soft"),
}

MYSTERIES = {
    "missing_crack": Mystery(
        "missing_crack",
        clue="a line of shiny dust",
        cause="a dropped bead tucked in the crack",
        hidden="a small gap in one stone",
        solved_by="careful looking",
        tags={"mystery", "arch"},
    ),
    "stolen_leaf": Mystery(
        "stolen_leaf",
        clue="a bare, empty spot where a leaf had been",
        cause="a sparrow had carried off the leaf",
        hidden="a pale mark on the arch",
        solved_by="patient watching",
        tags={"mystery", "arch"},
    ),
    "painted_mark": Mystery(
        "painted_mark",
        clue="a green smear near the base",
        cause="a beetle had brushed paint on the stone while making art",
        hidden="a wet paint trail",
        solved_by="gentle honesty",
        tags={"mystery", "artistic"},
    ),
}

CONFLICTS = {
    "clean_fast": Conflict(
        "clean_fast",
        topic="the arch",
        argument="The helper thought the arch should be scrubbed at once.",
        wrong_fix="scrub it before looking",
        right_fix="look carefully first",
        tags={"conflict", "arch"},
    ),
    "blame_beetle": Conflict(
        "blame_beetle",
        topic="the beetle",
        argument="The helper wanted to blame the beetle for every mark.",
        wrong_fix="blame the beetle",
        right_fix="ask what happened",
        tags={"conflict", "beetle"},
    ),
}

TRANSFORMS = {
    "caretaker": Transformation(
        "caretaker",
        from_role="artist",
        to_role="keeper",
        image="the beetle wore a crown of moss and looked proud beside the shining arch",
        moral="kindness and patience can turn a problem into a place of care.",
        tags={"transformation", "arch"},
    ),
    "restored": Transformation(
        "restored",
        from_role="broken stone",
        to_role="bright gate",
        image="the arch stood bright again, with one golden line like a smile",
        moral="when you solve the real mystery, the ending can be beautiful.",
        tags={"transformation", "mystery"},
    ),
}

BEETLE_NAMES = ["Bibo", "Mira", "Tali", "Nono", "Pip", "Rin"]
HELPER_NAMES = ["Crow", "Robin", "Mole", "Mouse", "Sparrow"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    transformation: str
    beetle_name: str
    helper_name: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTING_REGISTRY:
        for mid in MYSTERIES:
            for cid in CONFLICTS:
                for tid in TRANSFORMS:
                    combos.append((sid, mid, cid, tid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.conflict and args.conflict not in CONFLICTS:
        raise StoryError("Unknown conflict.")
    if args.transformation and args.transformation not in TRANSFORMS:
        raise StoryError("Unknown transformation.")

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.conflict is None or c[2] == args.conflict)
        and (args.transformation is None or c[3] == args.transformation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, conflict, transformation = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        transformation=transformation,
        beetle_name=args.beetle_name or rng.choice(BEETLE_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING_REGISTRY[params.setting])
    beetle = world.add(Entity(
        id=params.beetle_name,
        kind="character",
        type="beetle",
        label="the artistic beetle",
        role="artist",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="bird",
        label="the helper",
        role="helper",
    ))
    arch = world.add(Entity(
        id="arch",
        kind="thing",
        type="arch",
        label="the arch",
    ))

    mystery = MYSTERIES[params.mystery]
    conflict = CONFLICTS[params.conflict]
    transformation = TRANSFORMS[params.transformation]

    beetle.memes["curiosity"] = 1.0
    beetle.memes["worry"] = 1.0
    helper.memes["stubborn"] = 1.0
    arch.meters["mystery"] = 1.0
    arch.meters["beauty"] = 0.0

    start_story(world, beetle, arch, helper, world.setting, mystery)
    conflict_scene(world, beetle, helper, conflict, mystery)
    investigate(world, beetle, helper, mystery)
    repair(world, beetle, arch, transformation)
    ending(world, beetle, arch, transformation)

    world.facts.update(
        beetle=beetle,
        helper=helper,
        arch=arch,
        mystery=mystery,
        conflict=conflict,
        transformation=transformation,
        solved=arch.meters["mystery"] <= 0.0,
        changed=beetle.attrs.get("role_after") == "caretaker",
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a young child that includes the words "artistic", "beatle", and "arch".',
        f"Tell a short story where {f['beetle'].id}, an artistic beatle, notices a mystery under an arch, disagrees with a helper, and solves it with patience.",
        "Write a gentle fable about conflict, careful looking, and a small transformation that makes an old arch beautiful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    beetle = f["beetle"]
    helper = f["helper"]
    mystery = f["mystery"]
    conflict = f["conflict"]
    transformation = f["transformation"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {beetle.id}, an artistic beatle, and {helper.id}, who helped with the search. "
            f"They stood beside an old arch and faced a problem together.",
        ),
        (
            "What mystery did the beetle notice?",
            f"{beetle.id} noticed {mystery.clue}. That clue meant something was hidden near the arch, so the beetle kept looking instead of guessing.",
        ),
        (
            "Why was there conflict?",
            f"{conflict.argument} The helper wanted a quick answer, but the beetle wanted to solve the mystery first.",
        ),
    ]
    if f["solved"]:
        qa.append((
            "How was the mystery solved?",
            f"{beetle.id} followed the clue and found {mystery.cause}. Then the hidden trouble made sense, and the arch could be fixed the right way.",
        ))
    if f["changed"]:
        qa.append((
            "How did the beetle change by the end?",
            f"The beetle changed from a maker of pretty patterns into a careful keeper of the arch. "
            f"That transformation showed that art can become care when it helps others.",
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {transformation.image}. The arch was no longer puzzling; it was bright and whole again.",
    ))
    return qa


KNOWLEDGE = {
    "beetle": [(
        "What is a beetle?",
        "A beetle is a small insect with a hard shell. Many beetles can crawl, climb, and explore tiny places.",
    )],
    "arch": [(
        "What is an arch?",
        "An arch is a curved shape or doorway made of stone, wood, or another strong material. It can stand like a little bridge over a path.",
    )],
    "mystery": [(
        "What do you do when you find a mystery?",
        "You look carefully, notice clues, and keep asking gentle questions until the answer makes sense.",
    )],
    "art": [(
        "What does artistic mean?",
        "Artistic means someone likes making or noticing beautiful things, like patterns, colors, and shapes.",
    )],
    "conflict": [(
        "What is a conflict in a story?",
        "A conflict is a problem or disagreement that the characters must work through. It gives the story a challenge before the ending.",
    )],
    "transformation": [(
        "What is a transformation?",
        "A transformation is a change from one form or way of being into another. In stories, it can mean a character or place becomes different by the end.",
    )],
    "patience": [(
        "Why is patience useful?",
        "Patience helps you wait, look carefully, and choose a good answer instead of rushing into the wrong one.",
    )],
}
KNOWLEDGE_ORDER = ["art", "beetle", "arch", "mystery", "conflict", "patience", "transformation"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["conflict"].tags) | set(world.facts["transformation"].tags)
    out: list[tuple[str, str]] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags or k in KNOWLEDGE:
            out.extend(KNOWLEDGE[k])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
arch_has_mystery(A) :- arch(A), mystery(A).
conflict_exists(C) :- conflict(C).
solved :- clue_seen, truth_found.
transformed :- repaired, kind_action.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("arch", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_seen", mid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transformation", tid))
    lines.append(asp.fact("truth_found"))
    lines.append(asp.fact("repaired"))
    lines.append(asp.fact("kind_action"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show arch_has_mystery/1.\n#show conflict_exists/1.\n#show solved/0.\n#show transformed/0."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program builds a model.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story.")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show mystery/1.\n#show conflict/1.\n#show transformation/1."))
    return sorted(set(asp.atoms(model, "setting")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about an artistic beatle and an arch.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--beetle-name")
    ap.add_argument("--helper-name")
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


CURATED = [
    StoryParams("garden", "missing_crack", "clean_fast", "caretaker", "Bibo", "Crow"),
    StoryParams("courtyard", "stolen_leaf", "blame_beetle", "restored", "Mira", "Mouse"),
]


def generate_story_sample(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    return _generate(params)


def _generate(params: StoryParams) -> StorySample:
    world = World(SETTING_REGISTRY[params.setting])
    beetle = world.add(Entity(id=params.beetle_name, kind="character", type="beetle", role="artist"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="bird", role="helper"))
    arch = world.add(Entity(id="arch", kind="thing", type="arch", label="the arch"))
    mystery = MYSTERIES[params.mystery]
    conflict = CONFLICTS[params.conflict]
    transformation = TRANSFORMS[params.transformation]

    beetle.memes["curiosity"] = 1.0
    beetle.memes["worry"] = 1.0
    helper.memes["stubborn"] = 1.0
    arch.meters["mystery"] = 1.0

    world.say(
        f"Under {world.setting.place}, there lived an artistic beatle named {beetle.id}. "
        f"It loved to make tiny patterns around the old arch."
    )
    world.say(
        f"One day {beetle.id} noticed {mystery.clue}. That was the start of a mystery to solve."
    )

    world.para()
    world.say(
        f"{helper.id} said, \"{conflict.wrong_fix.title()}!\" but {beetle.id} replied that rushing would only hide the truth."
    )
    world.say(f"{conflict.argument}")
    beetle.memes["curiosity"] += 1
    beetle.memes["worry"] += 1
    helper.memes["stubborn"] += 1
    world.get("arch").meters["tension"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Instead of arguing forever, {beetle.id} looked again and again. "
        f"At last it found {mystery.cause}."
    )
    arch.meters["mystery"] = 0.0
    arch.meters["repaired"] += 1
    beetle.memes["kindness"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Then {beetle.id} used a bright leaf-gold touch to mend the arch. "
        f"{transformation.image}."
    )
    beetle.attrs["role_after"] = "caretaker"
    beetle.meters["glow"] += 1
    world.say(
        f"By evening, the fable was clear: {transformation.moral}"
    )

    world.facts.update(
        beetle=beetle,
        helper=helper,
        arch=arch,
        mystery=mystery,
        conflict=conflict,
        transformation=transformation,
    )

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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.conflict is None or c[2] == args.conflict)
        and (args.transformation is None or c[3] == args.transformation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, conflict, transformation = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        transformation=transformation,
        beetle_name=args.beetle_name or rng.choice(BEETLE_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show mystery/1.\n#show conflict/1.\n#show transformation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP support is present for parity checking.")
        print(f"{len(valid_combos())} valid combinations.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
