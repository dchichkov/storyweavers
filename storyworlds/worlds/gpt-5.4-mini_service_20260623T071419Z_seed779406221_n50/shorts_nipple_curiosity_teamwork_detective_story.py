#!/usr/bin/env python3
"""
storyworlds/worlds/shorts_nipple_curiosity_teamwork_detective_story.py
======================================================================

A small detective-style storyworld about curiosity, teamwork, and a missing
baby-bottle nipple found by following clues in a sunny neighborhood.

Premise:
- A curious child detective and a helpful partner search for a missing bottle
  nipple before nap time.
- The search passes through a playground, laundry basket, and backyard path.
- A pair of shorts, a pocket, and a sticky clue shape the mystery.
- Curiosity notices the trail; teamwork solves it.

This world uses typed entities with physical meters and emotional memes,
a forward-chained causal model, a Python reasonableness gate, and an inline
ASP twin for parity checks.
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

REGIONS = {"pocket", "hand", "floor", "basket", "table", "backyard"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    carries: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_find_clue(world: World) -> list[str]:
    out: list[str] = []
    for detective in world.characters():
        if detective.memes["curiosity"] < THRESHOLD:
            continue
        if world.facts.get("trail_seen") and ("clue", detective.id) not in world.fired:
            world.fired.add(("clue", detective.id))
            detective.memes["confidence"] += 1
            out.append(f"{detective.id} noticed the clue trail and leaned in closer.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("teamwork_step"):
        return out
    if ("teamwork",) in world.fired:
        return out
    world.fired.add(("teamwork",))
    for kid in world.characters():
        kid.memes["joy"] += 1
    out.append("The two detectives worked side by side, and the search got easier.")
    return out


CAUSAL_RULES = [
    Rule(name="find_clue", apply=_r_find_clue),
    Rule(name="teamwork", apply=_r_teamwork),
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


def valid_choice(clue: Clue, helper: HelperCfg, obj: ObjectCfg) -> bool:
    return clue.kind == "lost" and obj.kind == "nipple" and "search" in helper.helps_with


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for clue in CLUES:
            for helper in HELPERS:
                for obj in OBJECTS:
                    if valid_choice(CLUES[clue], HELPERS[helper], OBJECTS[obj]):
                        combos.append((setting, clue, helper, obj))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    helper: str
    object: str
    detective_name: str
    partner_name: str
    detective_gender: str
    partner_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "house": Setting(place="the cozy house", indoors=True, affordances={"search"}),
    "yard": Setting(place="the backyard", indoors=False, affordances={"search"}),
    "playground": Setting(place="the playground", indoors=False, affordances={"search"}),
}

CLUES = {
    "shorts": Clue(
        id="shorts",
        label="shorts",
        phrase="a pair of blue shorts",
        where="the pocket",
        kind="lost",
        tags={"shorts", "fabric"},
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumbs",
        phrase="tiny crumbs on the table",
        where="the table",
        kind="lost",
        tags={"crumbs"},
    ),
    "mud": Clue(
        id="mud",
        label="mud",
        phrase="a muddy print near the door",
        where="the floor",
        kind="lost",
        tags={"mud"},
    ),
}

HELPERS = {
    "magnifier": HelperCfg(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        helps_with={"search"},
        tags={"curiosity"},
    ),
    "flashlight": HelperCfg(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        helps_with={"search"},
        tags={"search"},
    ),
    "notebook": HelperCfg(
        id="notebook",
        label="notebook",
        phrase="a little notebook",
        helps_with={"search"},
        tags={"notes"},
    ),
}

OBJECTS = {
    "nipple": ObjectCfg(
        id="nipple",
        label="bottle nipple",
        phrase="the soft bottle nipple",
        kind="nipple",
        location="basket",
        fragile=True,
        tags={"baby", "bottle", "nipple"},
    ),
    "sock": ObjectCfg(
        id="sock",
        label="sock",
        phrase="a tiny sock",
        kind="sock",
        location="basket",
        fragile=False,
        tags={"sock"},
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Ivy", "Lina", "June", "Ruby"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Sam", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child detective story that includes "{f["clue"].label}" and "{f["object"].label}".',
        f"Tell a gentle mystery where {f['detective'].id} and {f['partner'].id} use {f['helper'].label} to find a missing {f['object'].label}.",
        f'Write a teamwork-and-curiosity story set at {f["setting"].place} and end with the found {f["object"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, par, helper, obj, clue = f["detective"], f["partner"], f["helper"], f["object"], f["clue"]
    return [
        QAItem(
            question=f"Who solved the little mystery at {world.setting.place}?",
            answer=(
                f"{det.id} and {par.id} solved it together. They followed the clue from "
                f"{clue.label} and kept looking until they found the {obj.label}."
            ),
        ),
        QAItem(
            question=f"What clue helped {det.id} search for the missing {obj.label}?",
            answer=(
                f"The clue was {clue.phrase}. It pointed the detectives toward the basket, "
                f"so their search had a clear direction."
            ),
        ),
        QAItem(
            question=f"How did {helper.label} help the search?",
            answer=(
                f"{helper.phrase} helped them look carefully and notice small details. "
                f"That made the curious search turn into teamwork."
            ),
        ),
        QAItem(
            question=f"Where was the missing {obj.label} found?",
            answer=(
                f"It was found in the basket. The detectives looked there after following "
                f"the clue trail, and the tiny part was safe and clean."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass helps you look at small things more closely.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other reach the same goal.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions and find out how things work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="house",
        clue="shorts",
        helper="magnifier",
        object="nipple",
        detective_name="Ivy",
        partner_name="Theo",
        detective_gender="girl",
        partner_gender="boy",
    ),
    StoryParams(
        setting="yard",
        clue="mud",
        helper="flashlight",
        object="nipple",
        detective_name="Maya",
        partner_name="Noah",
        detective_gender="girl",
        partner_gender="boy",
    ),
]


def explain_rejection(clue: Clue, helper: HelperCfg, obj: ObjectCfg) -> str:
    return (
        f"(No story: this mystery needs a lost clue, a search helper, and a "
        f"missing bottle nipple. Try the shorts clue with a search helper.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for a in sorted(h.helps_with):
            lines.append(asp.fact("helps_with", hid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_kind", oid, o.kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,H,O) :- setting(S), clue(C), helper(H), object(O), clue_kind(C,lost), object_kind(O,nipple), helps_with(H,search).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    helper = HELPERS[params.helper]
    obj = OBJECTS[params.object]
    world = World(setting=setting)

    det = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_gender, role="detective"))
    par = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_gender, role="partner"))

    det.memes["curiosity"] = 2
    par.memes["curiosity"] = 1
    det.meters["attention"] = 1
    par.meters["attention"] = 1

    clue_ent = world.add(Entity(id="clue", label=clue.label, kind="thing", location=clue.where))
    obj_ent = world.add(Entity(id="object", label=obj.label, kind="thing", location=obj.location))
    helper_ent = world.add(Entity(id="helper", label=helper.label, kind="thing"))

    world.say(
        f"At {setting.place}, {det.id} was a curious little detective, and {par.id} was ready to help."
    )
    world.say(
        f"They found a clue: {clue.phrase}. {det.id} opened {det.pronoun('possessive')} eyes wide and said the case was interesting."
    )
    world.para()
    world.say(
        f"With {helper.phrase} in hand, the two detectives looked again. They checked the {clue.where}, then the basket, then the quiet corners nearby."
    )
    world.facts["trail_seen"] = True
    world.facts["teamwork_step"] = True
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"At last, they found {obj.phrase} in the basket. The missing part was safe, and the mystery was over."
    )

    world.facts.update(
        setting=setting,
        clue=clue,
        helper=helper,
        object=obj,
        detective=det,
        partner=par,
        clue_ent=clue_ent,
        object_ent=obj_ent,
        helper_ent=helper_ent,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.helper and args.object:
        if not valid_choice(CLUES[args.clue], HELPERS[args.helper], OBJECTS[args.object]):
            raise StoryError(explain_rejection(CLUES[args.clue], HELPERS[args.helper], OBJECTS[args.object]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.helper is None or c[2] == args.helper)
              and (args.object is None or c[3] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, helper, obj = rng.choice(sorted(combos))
    det_name = args.detective_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    par_name = args.partner_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != det_name])
    det_gender = args.detective_gender or rng.choice(["girl", "boy"])
    par_gender = args.partner_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        clue=clue,
        helper=helper,
        object=obj,
        detective_name=det_name,
        partner_name=par_name,
        detective_gender=det_gender,
        partner_gender=par_gender,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-style curiosity and teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
