#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T045816Z_seed1855084837_n10/tilt_tulip_lesson_learned_quest_transformation_mystery.py
================================================================================

A small mystery-flavored storyworld about a missing tulip clue, a tilted sign,
a careful quest, and a lesson learned that changes how the search ends.

The story premise:
- A child notices something odd in a garden or greenhouse.
- A tilted object hides or points to a tulip-related clue.
- The child goes on a quest with a helper or tool.
- The search causes a small transformation in the world or the child.
- The ending proves the lesson learned.

This file is standalone, stdlib-only, and uses the shared Storyweavers
results/asp helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make imports robust from nested output directories.
_HERE = os.path.abspath(__file__)
_SEARCH = os.path.dirname(_HERE)
while True:
    if os.path.exists(os.path.join(_SEARCH, "results.py")):
        sys.path.insert(0, _SEARCH)
        break
    parent = os.path.dirname(_SEARCH)
    if parent == _SEARCH:
        break
    _SEARCH = parent

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    helps: str = ""
    transforms: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"tilt": 0.0, "disorder": 0.0, "stain": 0.0, "found": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0, "relief": 0.0, "resolve": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    features: set[str] = field(default_factory=set)
    light: str = ""


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    reveals: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    transforms: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []
        self.pointers: dict[str, str] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

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
        clone.history = list(self.history)
        clone.pointers = dict(self.pointers)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, features={"tilt", "tulip", "mystery"}, light="sunlight"),
    "greenhouse": Setting(place="the greenhouse", indoor=True, features={"tilt", "tulip", "mystery"}, light="glass light"),
    "yard": Setting(place="the backyard", indoor=False, features={"tilt", "tulip", "mystery"}, light="evening light"),
}

CLUES = {
    "tulip_bulb": Clue(
        id="tulip_bulb",
        label="tulip bulb",
        phrase="a tiny tulip bulb wrapped in damp paper",
        location="under the tilted pot",
        reveals="the hidden note was about planting a new tulip bed",
        risk="it might dry out and be lost",
        tags={"tulip", "garden"},
    ),
    "key_tag": Clue(
        id="key_tag",
        label="key tag",
        phrase="a brass key tag tucked behind the tilted sign",
        location="behind the tilted sign",
        reveals="the key fit the shed and opened the little mystery box",
        risk="someone could miss the clue if the sign stayed tilted",
        tags={"mystery"},
    ),
    "petal_note": Clue(
        id="petal_note",
        label="petal note",
        phrase="a folded note with a pressed tulip petal",
        location="inside the tilted watering can",
        reveals="the note explained where the missing seed packet had gone",
        risk="the paper could get wet and blur",
        tags={"tulip", "mystery"},
    ),
}

TOOLS = {
    "level": Tool(
        id="level",
        label="small level",
        phrase="a small level",
        helps="it showed which way the sign leaned",
        transforms="the child learned to look for clues before touching anything",
        tags={"tilt"},
    ),
    "gloves": Tool(
        id="gloves",
        label="garden gloves",
        phrase="garden gloves",
        helps="they kept muddy hands from smudging the clue",
        transforms="the child learned to handle clues carefully",
        tags={"careful"},
    ),
    "lamp": Tool(
        id="lamp",
        label="hand lamp",
        phrase="a hand lamp",
        helps="it lit the shadowy corner where the clue hid",
        transforms="the child learned that a mystery needs careful looking",
        tags={"mystery"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Owen", "Theo", "Sam"]
TRAITS = ["curious", "careful", "patient", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                if "tulip" in CLUES[c].tags and s == "garden":
                    out.append((s, c, t))
                elif c == "key_tag" and t in {"level", "lamp"}:
                    out.append((s, c, t))
                elif c == "petal_note" and s in {"garden", "greenhouse"}:
                    out.append((s, c, t))
    return out


def explain_rejection(setting: str, clue: str, tool: str) -> str:
    return f"(No story: the setting, clue, and tool do not make a believable mystery. Try a tulip clue in the garden or greenhouse, with a level or lamp.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    tool = f["tool"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "tilt" and "tulip".',
        f"Tell a gentle quest story where {hero.id} follows a clue about {clue.label} with {helper.id} and {tool.label}.",
        f"Write a child-friendly mystery where a tilted object hides something about a tulip, and the search changes how {hero.id} thinks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What made {hero.id} start the quest in {setting.place}?",
            answer=f"{hero.id} noticed that something was tilted in {setting.place}, and that odd tilt seemed to point to {clue.label}. That made {hero.id} curious enough to begin looking carefully.",
        ),
        QAItem(
            question=f"How did {tool.label} help {hero.id} search for the {clue.label}?",
            answer=f"{tool.label.capitalize()} helped because {tool.helps}. It gave {hero.id} a careful way to solve the mystery without rushing past the clue.",
        ),
        QAItem(
            question=f"What did {hero.id} learn after finding the clue with {helper.id}?",
            answer=f"{hero.id} learned that a mystery needs patient looking and gentle hands. By the end, the search changed {hero.id} from simply curious to truly thoughtful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags) | set(world.facts["tool"].tags) | {"tilt", "tulip"}
    out: list[QAItem] = []
    if "tilt" in tags:
        out.append(QAItem("What does it mean if something is tilted?", "If something is tilted, it leans to one side instead of standing straight. A tilt can make a hidden clue easier to notice."))
    if "tulip" in tags:
        out.append(QAItem("What is a tulip?", "A tulip is a flower with smooth petals and a tall stem. Tulips often grow from bulbs in a garden bed."))
    if "mystery" in tags:
        out.append(QAItem("What is a mystery?", "A mystery is something puzzling that you have to think about and solve. You look for clues until the answer becomes clear."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    lines.append(f"  history_count={len(world.history)}")
    return "\n".join(lines)


def _ensure_story_state(world: World, hero: Entity, helper: Entity, clue: Entity, tool: Entity) -> None:
    for e in (hero, helper, clue, tool):
        e.meters.setdefault("tilt", 0.0)
        e.meters.setdefault("disorder", 0.0)
        e.meters.setdefault("stain", 0.0)
        e.meters.setdefault("found", 0.0)
        e.memes.setdefault("curiosity", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("lesson", 0.0)
        e.memes.setdefault("relief", 0.0)
        e.memes.setdefault("resolve", 0.0)
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["clue"] = clue
    world.facts["tool"] = tool
    world.facts["setting"] = world.setting


def tell(setting: Setting, clue_cfg: Clue, tool_cfg: Tool, hero_name: str, hero_gender: str, helper_name: str, helper_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=["little", trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, traits=["neighbor", "patient"]))
    clue = world.add(Entity(id=clue_cfg.id, type="thing", label=clue_cfg.label, phrase=clue_cfg.phrase, location=clue_cfg.location, tags=set(clue_cfg.tags)))
    tool = world.add(Entity(id=tool_cfg.id, type="thing", label=tool_cfg.label, phrase=tool_cfg.phrase, tags=set(tool_cfg.tags), helps=tool_cfg.helps, transforms=tool_cfg.transforms))
    _ensure_story_state(world, hero, helper, clue, tool)

    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a little {trait} child who liked quiet afternoons in {setting.place}.")
    world.say(f"One day, {hero.id} noticed that something in the garden was tilted, and the odd tilt felt like a secret.")

    world.para()
    helper.memes["resolve"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id} called {helper.id} to help with the quest.")
    world.say(f"Together they carried {tool.phrase} and looked for what the tilted clue might hide.")

    world.para()
    if clue_cfg.id == "tulip_bulb":
        world.say(f"Behind the tilted pot, they found {clue.phrase}.")
    elif clue_cfg.id == "key_tag":
        world.say(f"Behind the tilted sign, they found {clue.phrase}.")
    else:
        world.say(f"In the tilted watering can, they found {clue.phrase}.")
    hero.meters["found"] += 1
    clue.meters["found"] += 1

    world.say(f"The clue said that {clue_cfg.reveals}.")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.para()
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"{tool_cfg.transforms.capitalize()}.")
    world.say(f"{hero.id} fixed the tilted pot, tucked the clue safely away, and smiled at the little tulip patch.")
    world.say(f"By the end, {hero.id} was not just searching anymore; {hero.pronoun()} had learned to solve mysteries with patience and care.")

    world.facts["ending"] = f"{hero.id} left the {setting.place} tidier, with the tulips safe and the clue understood."
    return world


CURATED = [
    StoryParams(setting="garden", clue="tulip_bulb", tool="level", name="Lily", gender="girl", helper="Mina", helper_gender="girl", trait="curious"),
    StoryParams(setting="greenhouse", clue="petal_note", tool="lamp", name="Finn", gender="boy", helper="Rae", helper_gender="girl", trait="careful"),
    StoryParams(setting="yard", clue="key_tag", tool="gloves", name="Ava", gender="girl", helper="Noah", helper_gender="boy", trait="thoughtful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with tilt, tulip, quest, transformation, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    valid = [c for c in valid_combos()
             if (args.setting is None or c[0] == args.setting)
             and (args.clue is None or c[1] == args.clue)
             and (args.tool is None or c[2] == args.tool)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    if args.setting and args.clue and args.tool and (args.setting, args.clue, args.tool) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.clue, args.tool))
    setting, clue, tool = rng.choice(sorted(valid))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, tool=tool, name=name, gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def generation_story(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.tool not in TOOLS:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], CLUES[params.clue], TOOLS[params.tool], params.name, params.gender, params.helper, params.helper_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


generate = generation_story


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
setting(garden). setting(greenhouse). setting(yard).
clue(tulip_bulb). clue(key_tag). clue(petal_note).
tool(level). tool(gloves). tool(lamp).
valid(S,C,T) :- setting(S), clue(C), tool(T), S = garden, C = tulip_bulb.
valid(S,C,T) :- setting(S), clue(C), tool(T), C = key_tag, (T = level; T = lamp).
valid(S,C,T) :- setting(S), clue(C), tool(T), C = petal_note, (S = garden; S = greenhouse).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("MISMATCH between Python and ASP valid combos.")
        print("only python:", sorted(py - asp_set))
        print("only asp:", sorted(asp_set - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, tool=None, name=None, gender=None, helper=None, helper_gender=None, trait=None), random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"Smoke test failed: {err}")
        return 1
    if ok:
        print(f"OK: {len(py)} valid combos; smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        payload = [s.to_dict() for s in samples]
        if len(payload) == 1:
            print(json.dumps(payload[0], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
