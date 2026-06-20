#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chewy_arm_misunderstanding_foreshadowing_twist_detective_story.py
=================================================================================================

A standalone storyworld for a tiny detective tale with a misunderstanding,
foreshadowing, and a twist. The seed words are **chewy** and **arm**.

Core premise:
- A child detective follows a strange clue.
- A chewy scrap on an arm looks suspicious.
- The first guess is wrong; the real explanation is harmless and surprising.
- The story ends with the clue making sense in a new way.

This world is designed to produce short, child-facing detective stories with:
- a clear mystery
- a mistaken suspicion
- a planted hint
- a twist reveal
- a tidy ending image showing what changed

The world model tracks:
- physical meters: clue strength, suspicion, relief, etc.
- emotional memes: curiosity, worry, confidence, delight

It also includes:
- a Python reasonableness gate
- an inline ASP twin
- story-grounded and world-knowledge QA
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
        return self.label or self.id



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
    light: str
    hiding_spot: str
    atmosphere: str

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
class Clue:
    id: str
    label: str
    texture: str
    place: str
    hint: str
    misread: str
    truth: str
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
class Suspect:
    id: str
    label: str
    type: str
    harmless: bool
    twist_line: str
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
class Reveal:
    id: str
    label: str
    method: str
    ending_image: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective: str
    helper: str
    suspect: str
    clue: str
    reveal: str
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


SETTINGS = {
    "library": Setting("library", "the little library", "lamp light", "behind the chair", "quiet and warm"),
    "kitchen": Setting("kitchen", "the kitchen", "window light", "under the table", "bright and busy"),
    "hall": Setting("hall", "the hallway", "wall light", "near the coat rack", "narrow and echoey"),
}

CLUES = {
    "chewy_band": Clue(
        "chewy_band", "a chewy band", "chewy",
        "on the armrest", "a soft chew mark on the armrest",
        "It looked like someone had been biting the chair arm.",
        "The chewy mark came from a dog toy tucked into the couch.",
        tags={"chewy", "arm"},
    ),
    "chewy_sticker": Clue(
        "chewy_sticker", "a chewy sticker", "chewy",
        "on the sleeve", "a chewy sticker stuck to the sleeve",
        "It looked like a clue from a messy thief.",
        "The sticker came from a toy packet and had slipped onto the sleeve.",
        tags={"chewy"},
    ),
    "arm_trace": Clue(
        "arm_trace", "a crumb trail by the arm", "chewy",
        "beside the armchair", "crumbs by the armchair arm",
        "It looked like a rough clue left by a sneaky guest.",
        "The crumbs were from a cookie hidden in a pocket.",
        tags={"arm"},
    ),
}

SUSPECTS = {
    "dog": Suspect(
        "dog", "the dog", "animal", True,
        "The dog only wanted the chewy toy and wagged its tail.",
        tags={"chewy"},
    ),
    "robot": Suspect(
        "robot", "the toy robot", "toy", True,
        "The robot had one arm that clicked when it moved.",
        tags={"arm"},
    ),
    "kid": Suspect(
        "kid", "the neighbor kid", "child", True,
        "The neighbor kid was just helping and had left a note.",
        tags={"arm", "chewy"},
    ),
}

REVEALS = {
    "toy": Reveal(
        "toy", "the toy box", "open the toy box",
        "The chewy clue was only a toy piece, and the arm was part of a plush robot.",
        tags={"chewy", "arm"},
    ),
    "pet": Reveal(
        "pet", "the pet basket", "lift the blanket",
        "The chewy clue belonged to the dog, and the arm was only the chair arm.",
        tags={"chewy", "arm"},
    ),
    "snack": Reveal(
        "snack", "the snack tin", "peek into the tin",
        "The chewy clue was from a snack, and the arm was where the crumbs fell.",
        tags={"chewy", "arm"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for rid, reveal in REVEALS.items():
                if clue.tags & reveal.tags:
                    combos.append((sid, cid, rid))
    return combos


def reasonableness_ok(clue: Clue, reveal: Reveal) -> bool:
    return bool(clue.tags & reveal.tags)


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_cfg")
    if clue and world.get("clue").meters["noticed"] >= THRESHOLD:
        if ("suspicion", clue.id) in world.fired:
            return out
        world.fired.add(("suspicion", clue.id))
        world.get("detective").memes["worry"] += 1
        world.get("detective").meters["suspicion"] += 1
        out.append("__suspect__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("detective").meters["truth"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        world.get("detective").memes["relief"] += 1
        world.get("helper").memes["relief"] += 1
        out.append("__relief__")
    return out


RULES = [_r_suspicion, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def preview_misunderstanding(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    sim.get("detective").meters["suspicion"] += 1
    return {
        "suspicion": sim.get("detective").meters["suspicion"],
        "noticed": sim.get("clue").meters["noticed"],
    }


def setup(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {detective.id} and {helper.id} were solving a tiny case in "
        f"{world.setting.place}. {world.setting.atmosphere.capitalize()}, and {world.setting.light} "
        f"fell across {world.setting.hiding_spot}."
    )
    world.say(
        f"{detective.id} was a little detective who noticed everything, while {helper.id} kept the notebook ready."
    )


def find_clue(world: World, clue: Clue, detective: Entity) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"Then {detective.id} found {clue.texture} in {clue.place}. "
        f"It was {clue.hint}."
    )
    world.say(
        f'"That looks odd," {detective.id} said. "{clue.misread}"'
    )


def foreshadow(world: World, clue: Clue, suspect: Suspect, helper: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} pointed at a small detail before anyone made a guess. "
        f"{suspect.twist_line} That was a tiny hint that the first answer might not be right."
    )


def misunderstanding(world: World, detective: Entity, suspect: Suspect, clue: Clue) -> None:
    detective.memes["worry"] += 1
    world.say(
        f"{detective.id} frowned and pointed at the clue. \"It must be {suspect.label},\" "
        f"{detective.id} whispered, sure that the {clue.label} meant trouble."
    )
    world.say(
        f"For a moment, the case felt bigger and scarier than it really was."
    )


def twist(world: World, reveal: Reveal, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.meters["truth"] += 1
    helper.meters["truth"] += 1
    detective.memes["relief"] += 1
    world.say(
        f"At last, they followed the clue and {reveal.method}. "
        f"Then the truth appeared: {reveal.ending_image}"
    )
    world.say(
        f'{detective.id} blinked, then laughed. The mystery was not dangerous at all; it only looked that way at first.'
    )


def ending(world: World, detective: Entity, helper: Entity, reveal: Reveal) -> None:
    detective.memes["delight"] += 1
    helper.memes["delight"] += 1
    world.say(
        f"In the end, {detective.id} closed the notebook, {helper.id} smiled, and the room felt calm again. "
        f"{reveal.ending_image}"
    )


def tell(setting: Setting, clue: Clue, suspect: Suspect, reveal: Reveal,
         detective_name: str = "Nina", helper_name: str = "Milo") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", role="helper"))
    world.add(Entity(id="clue", type="thing", label=clue.label))
    world.add(Entity(id="suspect", type=suspect.type, label=suspect.label))
    world.add(Entity(id="reveal", type="thing", label=reveal.label))

    world.facts.update(setting=setting, clue_cfg=clue, suspect_cfg=suspect, reveal_cfg=reveal,
                       detective=detective, helper=helper)

    setup(world, detective, helper, clue)
    world.para()
    find_clue(world, clue, detective)
    foreshadow(world, clue, suspect, helper)
    misunderstanding(world, detective, suspect, clue)
    world.para()
    twist(world, reveal, detective, helper, clue)
    ending(world, detective, helper, reveal)

    outcome = "twist"
    world.facts.update(outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue_cfg"]
    return [
        f'Write a child-friendly detective story that uses the word "{clue.texture}" and includes a misunderstanding.',
        f"Tell a short mystery where a detective thinks the {clue.label} means something alarming, but the clue turns out harmless.",
        f"Write a story with foreshadowing and a twist in which the word \"chewy\" appears and the word \"arm\" matters to the clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue: Clue = f["clue_cfg"]
    suspect: Suspect = f["suspect_cfg"]
    reveal: Reveal = f["reveal_cfg"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        ("What kind of story is this?",
         "It is a detective story about following a clue, making a wrong guess, and then finding the real answer."),
        (f"What did {detective.id} first think the clue meant?",
         f"{detective.id} first thought it meant {suspect.label}. That was the misunderstanding, because the clue only looked suspicious at first."),
        ("What was the foreshadowing?",
         f"{helper.id} noticed a small detail that hinted the first guess might be wrong. That hint prepared the reader for the twist."),
        ("What was the twist?",
         f"The clue turned out to be harmless and ordinary, not a danger. The chewy mark and the arm detail had a simple explanation."),
        ("How did the story end?",
         f"It ended calmly, with the mystery solved and everyone smiling. The notebook closed, and the scary guess was replaced by the true answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What does a detective do?",
         "A detective looks for clues, asks questions, and tries to figure out what really happened."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone guesses the wrong meaning and later learns the truth."),
        ("What is foreshadowing?",
         "Foreshadowing is a small hint that helps the reader guess that something important may happen later."),
        ("What is a twist in a story?",
         "A twist is a surprise that changes what you thought was true."),
        ("What does chewy mean?",
         "Chewy means soft and a little bendy, like something you can bite or squeeze."),
        ("What is an arm?",
         "An arm is the body part between the shoulder and the hand."),
    ]
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, reveal: Reveal) -> str:
    return f"(No story: the clue and the reveal do not support a believable twist yet.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with a chewy clue and an arm twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
    if args.clue and args.reveal:
        if not reasonableness_ok(CLUES[args.clue], REVEALS[args.reveal]):
            raise StoryError(explain_rejection(CLUES[args.clue], REVEALS[args.reveal]))
    filtered = [c for c in combos
                if (args.setting is None or c[0] == args.setting)
                and (args.clue is None or c[1] == args.clue)
                and (args.reveal is None or c[2] == args.reveal)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, reveal = rng.choice(sorted(filtered))
    detective = args.detective or rng.choice(["Nina", "Ruby", "Tess", "Ivy", "Mina"])
    helper = args.helper or rng.choice(["Milo", "Owen", "Theo", "Ben", "Jules"])
    if args.suspect:
        suspect = args.suspect
    else:
        suspect = rng.choice(sorted(SUSPECTS))
    return StoryParams(setting, detective, helper, suspect, clue, reveal)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], SUSPECTS[params.suspect], REVEALS[params.reveal], params.detective, params.helper)
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


ASP_RULES = r"""
support(C) :- clue(C).
support(C) :- reveal(R), clue(C), shares(C, R).

valid(S, C, R) :- setting(S), clue(C), reveal(R), support(C).
twist_ok(C, R) :- clue(C), reveal(R), shares(C, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("shares", cid, tag))
    for rid, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", rid))
        for tag in sorted(reveal.tags):
            lines.append(asp.fact("shares", rid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python gate differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, reveal=None, suspect=None, detective=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def CURATED_PARAMS() -> list[StoryParams]:
    return [
        StoryParams("library", "Nina", "Milo", "dog", "chewy_band", "pet"),
        StoryParams("kitchen", "Ivy", "Ben", "robot", "arm_trace", "toy"),
        StoryParams("hall", "Tess", "Jules", "kid", "chewy_sticker", "snack"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show twist_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED_PARAMS()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.detective}: {p.clue} in {p.setting} ({p.reveal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
