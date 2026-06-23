#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/shingle_pediatric_prosciutto_rhyme_inner_monologue_mystery.py
===============================================================================================================

A tiny mystery storyworld for a pediatric-clinic case with rhyme, inner monologue,
and a solve-it turn. The seed words are woven into a small, state-driven domain:
a child notices a missing prosciutto snack, follows a shingle-shaped clue, and
learns what really happened in the clinic.

The world models:
- physical meters: hunger, mess, worry, wetness, solved clues
- emotional memes: curiosity, worry, pride, relief, care

The story is generated from simulated state, not from a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    id: str
    label: str
    smell: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    missing: str
    worry: str
    rhyme: str
    reveal: str
    clue_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    source: str
    leads_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = ""
    mystery: str = ""
    clue: str = ""
    method: str = ""
    name: str = ""
    gender: str = "child"
    helper: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _ensure(e: Entity, key: str) -> None:
    e.meters.setdefault(key, 0.0)
    e.memes.setdefault(key, 0.0)


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["curiosity"] >= THRESHOLD and child.meters["missing"] >= THRESHOLD:
        sig = ("worry",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_findcrumb(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    if child.memes["curiosity"] < THRESHOLD or clue.meters["noticed"] >= THRESHOLD:
        return []
    sig = ("noticed", clue.id)
    if sig in world.fired:
        return []
    if child.meters["missing"] >= THRESHOLD:
        world.fired.add(sig)
        clue.meters["noticed"] += 1
        child.memes["pride"] += 1
        return ["__clue__"]
    return []


def _r_resolve(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    item = world.get("item")
    if clue.meters["noticed"] < THRESHOLD or item.meters["returned"] >= THRESHOLD:
        return []
    sig = ("resolved", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["returned"] += 1
    child.memes["relief"] += 1
    return ["__resolved__"]


CAUSAL_RULES = [
    ("worry", _r_worry),
    ("findcrumb", _r_findcrumb),
    ("resolve", _r_resolve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend(msgs)
    if narrate:
        for msg in produced:
            if msg == "__worry__":
                world.say("The waiting room felt too quiet, and the missing thing tugged at the child's mind.")
            elif msg == "__clue__":
                world.say("A small clue finally stood out, as if it had been waiting to be seen.")
            elif msg == "__resolved__":
                world.say("The last piece clicked into place, and the puzzle stopped biting.")
    return produced


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for clue in CLUES:
                for method in METHODS:
                    if clue.leads_to == mystery and method.id in METHODS_FOR[mystery]:
                        combos.append((setting, mystery, clue, method))
    return combos


SETTINGS: dict[str, Setting] = {
    "pediatric": Setting(
        id="pediatric",
        label="the pediatric clinic",
        smell="soap and crayons",
        afford={"prosciutto", "shingle", "puzzle", "lost"},
    ),
    "lobby": Setting(
        id="lobby",
        label="the clinic lobby",
        smell="clean shoes and paper",
        afford={"prosciutto", "shingle", "puzzle", "lost"},
    ),
    "hallway": Setting(
        id="hallway",
        label="the bright hallway",
        smell="mint and bandages",
        afford={"prosciutto", "shingle", "puzzle", "lost"},
    ),
    "exam": Setting(
        id="exam",
        label="the examination room",
        smell="soap and tape",
        afford={"prosciutto", "shingle", "puzzle", "lost"},
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "prosciutto": Mystery(
        id="prosciutto",
        label="the missing prosciutto sandwich",
        missing="prosciutto",
        worry="the lunch box felt empty",
        rhyme="No ham, no jam, no snack to eat; where did the prosciutto go so neat?",
        reveal="the prosciutto was kept safe for later",
        clue_word="prosciutto",
        tags={"prosciutto", "snack", "food"},
    ),
    "shingle": Mystery(
        id="shingle",
        label="the loose shingle-shaped tile",
        missing="shingle",
        worry="the roof made a tiny tapping sound",
        rhyme="A shingle, a tingle, a tap on the wall; what made the little piece fall?",
        reveal="the shingle had slipped from a display roof model",
        clue_word="shingle",
        tags={"shingle", "roof", "tile"},
    ),
    "sticker": Mystery(
        id="sticker",
        label="the lost dinosaur sticker",
        missing="sticker",
        worry="the notebook looked too plain",
        rhyme="A sticker, a flicker, a shiny small part; who took the dino from the art?",
        reveal="the sticker had stuck to the clipboard",
        clue_word="sticker",
        tags={"sticker", "paper", "lost"},
    ),
    "spoon": Mystery(
        id="spoon",
        label="the missing spoon",
        missing="spoon",
        worry="the cup could not be stirred",
        rhyme="A spoon, a tune, a clink on the tray; where did the little spoon go away?",
        reveal="the spoon had slipped into the snack cart",
        clue_word="spoon",
        tags={"spoon", "metal", "lost"},
    ),
}

CLUES: dict[str, Clue] = {
    "crumbs": Clue(
        id="crumbs",
        label="tiny crumbs",
        phrase="tiny crumbs on the chair",
        source="the snack bag",
        leads_to="prosciutto",
        tags={"crumbs", "food"},
    ),
    "tap": Clue(
        id="tap",
        label="a tapping sound",
        phrase="a tiny tap above the shelf",
        source="the ceiling",
        leads_to="shingle",
        tags={"tap", "roof"},
    ),
    "sticker": Clue(
        id="sticker",
        label="a sticky corner",
        phrase="a sticky corner on the clipboard",
        source="the clipboard",
        leads_to="sticker",
        tags={"sticker", "paper"},
    ),
    "tray": Clue(
        id="tray",
        label="a shiny spoon mark",
        phrase="a shiny mark on the snack cart",
        source="the cart",
        leads_to="spoon",
        tags={"spoon", "metal"},
    ),
}

METHODS: dict[str, Method] = {
    "ask_nurse": Method(
        id="ask_nurse",
        label="ask the nurse",
        action="ask the nurse about the clue",
        ending="The nurse smiled and pointed to the right place.",
        tags={"help", "clinic"},
    ),
    "check_cart": Method(
        id="check_cart",
        label="check the snack cart",
        action="look by the snack cart",
        ending="The cart held the answer right away.",
        tags={"cart", "food"},
    ),
    "follow_sound": Method(
        id="follow_sound",
        label="follow the sound",
        action="listen and follow the little sound",
        ending="The sound led straight to the answer.",
        tags={"sound", "roof"},
    ),
    "peek_clipboard": Method(
        id="peek_clipboard",
        label="peek at the clipboard",
        action="peek at the clipboard",
        ending="The clipboard had the answer stuck to it.",
        tags={"paper", "sticker"},
    ),
}

METHODS_FOR = {
    "prosciutto": {"ask_nurse", "check_cart"},
    "shingle": {"follow_sound"},
    "sticker": {"peek_clipboard"},
    "spoon": {"check_cart"},
}

GIRL_NAMES = ["Mia", "Nora", "Lena", "Ava", "Zoe"]
BOY_NAMES = ["Eli", "Leo", "Noah", "Finn", "Max"]
HELPERS = ["mother", "father", "nurse"]


def story_at_risk(mystery: Mystery, clue: Clue) -> bool:
    return clue.leads_to == mystery.id


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pediatric-clinic mystery with rhyme and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, clue, method = rng.choice(sorted(combos))
    q = MYSTERIES[mystery]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, clue=clue, method=method, name=name, gender=gender, helper=helper)


def _init_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[params.clue].label))
    item = world.add(Entity(id="item", type="thing", label=MYSTERIES[params.mystery].label))
    for e in (child, helper, clue, item):
        for k in ["missing", "noticed", "returned", "curiosity", "worry", "relief", "pride"]:
            _ensure(e, k)
    child.meters["missing"] = 1
    child.memes["curiosity"] = 1
    world.facts = {
        "params": params,
        "child": child,
        "helper": helper,
        "clue": clue,
        "item": item,
        "setting": setting,
        "mystery": MYSTERIES[params.mystery],
        "clue_def": CLUES[params.clue],
        "method_def": METHODS[params.method],
    }
    return world


def tell(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    m = world.facts["mystery"]
    c = world.facts["clue_def"]
    meth = world.facts["method_def"]

    world.say(f"{child.label} sat in {world.setting.label}, where the air smelled like {world.setting.smell}.")
    world.say(f"{child.label} noticed {m.worry}, and the little mystery felt as big as a shadow.")
    world.say(f"Inside {child.label}'s head, a small voice said, 'Why is {m.missing} gone? Where did it go?'")
    world.say(f"{m.rhyme}")

    world.para()
    world.say(f"{helper.label.capitalize()} came near and listened.")
    world.say(f"{child.label} whispered, 'If I am patient and bright, maybe I can spot the right sight.'")
    child.meters["missing"] += 1
    propagate(world, narrate=True)

    world.para()
    if c.leads_to == "prosciutto":
        world.say(f"A clue appeared: {c.phrase}.")
        world.say(f"{meth.ending}")
        world.say("At last, the answer was simple: the snack had been set aside, not stolen.")
        world.say(f"{child.label} found the prosciutto and felt their worry melt into relief.")
    elif c.leads_to == "shingle":
        world.say(f"A clue appeared: {c.phrase}.")
        world.say(f"{meth.ending}")
        world.say("The tiny piece had dropped from a display roof model, and the mystery was solved.")
        world.say("The clinic stayed calm, and the child could breathe again.")
    elif c.leads_to == "sticker":
        world.say(f"A clue appeared: {c.phrase}.")
        world.say(f"{meth.ending}")
        world.say("The sticker had simply stuck to the clipboard, hiding in plain sight.")
        world.say(f"{child.label} smiled, proud of the careful looking.")
    else:
        world.say(f"A clue appeared: {c.phrase}.")
        world.say(f"{meth.ending}")
        world.say("The spoon had rolled into the snack cart, and the mystery stopped being mysterious.")

    child.memes["curiosity"] += 1
    helper.memes["relief"] += 1
    world.facts["solved"] = True
    world.facts["ending"] = c.leads_to


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    c = world.facts["clue_def"]
    return [
        f'Write a short mystery for a child in {world.setting.label} that includes the word "{m.clue_word}".',
        f"Tell a pediatric-clinic story where {p.name} solves a small mystery by noticing {c.phrase}.",
        f'Write a rhyme-filled mystery where the missing "{m.missing}" is found by following a clue in {world.setting.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    c = world.facts["clue_def"]
    meth = world.facts["method_def"]
    child = world.get("child")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"What mystery was {p.name} trying to solve in the pediatric clinic?",
            answer=f"{p.name} was trying to solve the mystery of {m.label}. {m.worry} made the case feel important until the answer appeared.",
        ),
        QAItem(
            question=f"What clue helped {p.name} notice the answer?",
            answer=f"{c.phrase} was the clue. It led {p.name} to use {meth.label}, which matched the problem and helped the story turn toward the answer.",
        ),
        QAItem(
            question=f"How did {p.name} feel when the mystery was solved?",
            answer=f"{p.name} felt proud and relieved. The answer meant the worry could settle down, and the child could keep the snack or clue in the right place.",
        ),
        QAItem(
            question=f"Why did {helper.label} help instead of leaving {p.name} alone?",
            answer=f"{helper.label.capitalize()} helped because the clinic felt quieter and the child needed a steady helper. That made the clue easier to follow and the mystery easier to solve.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does pediatric mean?",
            answer="Pediatric means it has to do with children and their care, especially in a clinic or doctor's office.",
        ),
        QAItem(
            question="What is prosciutto?",
            answer="Prosciutto is a thin slice of cured ham. People often eat it in sandwiches or on a snack plate.",
        ),
        QAItem(
            question="What is a shingle?",
            answer="A shingle is a flat piece that helps cover a roof. It keeps rain out and helps a roof stay dry.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps someone figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"{e.id}: meters={meters} memes={memes}")
    parts.append(f"fired={sorted(world.fired)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(setting="pediatric", mystery="prosciutto", clue="crumbs", method="ask_nurse", name="Mia", gender="girl", helper="nurse"),
    StoryParams(setting="lobby", mystery="shingle", clue="tap", method="follow_sound", name="Eli", gender="boy", helper="father"),
    StoryParams(setting="hallway", mystery="sticker", clue="sticker", method="peek_clipboard", name="Nora", gender="girl", helper="mother"),
    StoryParams(setting="exam", mystery="spoon", clue="tray", method="check_cart", name="Leo", gender="boy", helper="nurse"),
]


ASP_RULES = r"""
solved(M) :- clue(C), leads_to(C, M), method_ok(M, C).
method_ok(prosciutto, crumbs).
method_ok(prosciutto, ask_nurse).
method_ok(prosciutto, check_cart).
method_ok(shingle, tap).
method_ok(shingle, follow_sound).
method_ok(sticker, sticker).
method_ok(sticker, peek_clipboard).
method_ok(spoon, tray).
method_ok(spoon, check_cart).
valid(S, M, C, Me) :- setting(S), mystery(M), clue(C), method(Me), solved(M), clue_ok(C, M), method_ok(M, C).
clue_ok(C, M) :- leads_to(C, M).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("leads_to", c, CLUES[c].leads_to))
    for me in METHODS:
        lines.append(asp.fact("method", me))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp())
    ok = 0
    if py != cl:
        print("MISMATCH between Python and ASP valid combos:")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
        ok = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, clue=None, method=None, name=None, gender=None, helper=None), random.Random(7)))
        assert sample.story
        _ = format_qa(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: {len(py)} valid combos; story generation smoke test passed.")
    return ok


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.clue not in CLUES or params.method not in METHODS:
        raise StoryError("Invalid story parameters.")
    if CLUES[params.clue].leads_to != params.mystery:
        raise StoryError("That clue does not match that mystery.")
    if params.method not in METHODS_FOR[params.mystery]:
        raise StoryError("That method does not fit the mystery.")
    world = _init_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
