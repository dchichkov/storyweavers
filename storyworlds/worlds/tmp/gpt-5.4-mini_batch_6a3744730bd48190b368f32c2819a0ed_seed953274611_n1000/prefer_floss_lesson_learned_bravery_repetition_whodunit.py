#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prefer_floss_lesson_learned_bravery_repetition_whodunit.py
==========================================================================================

A tiny whodunit-style storyworld about a child, a missing floss pick, and a
careful clue trail.  The premise is intentionally small: someone prefers one
tool over another, a repeated detail matters, bravery is needed to ask the right
questions, and the final lesson is learned by noticing the same clue twice.

The world is built around a simple mystery:
- a child prefers something easy,
- a wiser helper prefers floss because it works better,
- a missing floss pick leaves a clue,
- the repeated clue reveals where it went,
- and the ending proves the lesson learned.

This file is standalone and stdlib-only.
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
class Tool:
    id: str
    label: str
    phrase: str
    uses: str
    clean: str
    sticky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    trail: str
    repeated_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ending:
    id: str
    power: int
    text: str
    lesson: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.entities.values():
        if clue.kind != "thing" or clue.meters["noticed"] < THRESHOLD:
            continue
        sig = ("repeat", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        clue.memes["importance"] += 1
        out.append("__repeat__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["bravery"] < THRESHOLD:
            continue
        sig = ("brave", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["confidence"] += 1
        out.append("__brave__")
    return out


CAUSAL_RULES = [
    Rule("repeat", "clue", _r_repeat),
    Rule("bravery", "social", _r_bravery),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prefer_check(preferred: Tool, alternate: Tool) -> bool:
    return preferred.id == "floss" and alternate.id == "pick"


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.id == "floss"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for preferred in TOOLS:
            for clue in CLUES:
                if preferred == "floss" and clue in {"gap", "drawer"}:
                    combos.append((setting, preferred, clue))
    return combos


@dataclass
class StoryParams:
    setting: str
    preferred: str
    clue: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    suspect: str
    ending: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about floss, clues, and a learned lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--preferred", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--ending", choices=ENDINGS)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.preferred and args.preferred != "floss":
        raise StoryError("(No story: this whodunit prefers floss; the other tool is too weak for the clue trail.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.preferred is None or c[1] == args.preferred)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, preferred, clue = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if hero_gender == "boy" else "boy"
    hero = args.hero if hasattr(args, "hero") and getattr(args, "hero", None) else _pick_name(rng, hero_gender)
    helper = _pick_name(rng, helper_gender)
    ending = args.ending or rng.choice(sorted(ENDINGS))
    suspect = rng.choice(["the cat", "the dog", "the teddy bear", "the toy robot"])
    return StoryParams(setting=setting, preferred=preferred, clue=clue, hero=hero,
                       hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
                       suspect=suspect, ending=ending)


def _do_search(world: World, hero: Entity, helper: Entity, tool: Tool, clue: Clue) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"On a quiet evening, {hero.id} and {helper.id} searched {world.facts['setting_text']}.")
    world.say(f"{hero.id} looked at the sink and said, \"I prefer the easy pick.\"")
    world.say(f"But {helper.id} shook {helper.pronoun('possessive')} head. \"I prefer floss,\" {helper.pronoun()} said. \"It slides where a pick can miss.\"")
    world.para()
    world.say(f"Then they found the first clue: {clue.label} {clue.trail}.")
    world.say(f"{clue.repeated_line}")
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    if clue.id == "drawer":
        clue_ent.meters["noticed"] += 1
        world.say(f"It was strange that the same detail kept showing up again: {clue.label} by the drawer, {clue.label} by the towel.")
    else:
        world.say(f"The clue kept coming back in the story, and that repetition made it feel important.")
    propagate(world, narrate=False)
    world.para()


def _confront(world: World, hero: Entity, helper: Entity, tool: Tool, clue: Clue, ending: Ending) -> None:
    hero.memes["bravery"] += 1
    world.say(f"{hero.id} took a brave breath and followed the repeated clue to {ending.text}.")
    world.say(f"There, the missing floss pick was hiding near {world.facts['suspect']}.")
    world.say(f"{helper.id} smiled. \"That is why I prefer floss,\" {helper.pronoun()} said. \"It gets between the little places and tells the truth.\"")
    world.para()
    world.say(f"{ending.lesson}")
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(f"At the end, {hero.id} preferred floss too, because the mystery had taught {hero.pronoun('object')} a new lesson.")


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.preferred].label))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[params.clue].label))
    ending = ENDINGS[params.ending]

    world.facts["setting_text"] = SETTINGS[params.setting]
    world.facts["suspect"] = params.suspect
    world.facts["preferred"] = tool
    world.facts["clue_cfg"] = CLUES[params.clue]
    world.facts["ending_cfg"] = ending

    _do_search(world, hero, helper, TOOLS[params.preferred], CLUES[params.clue])
    _confront(world, hero, helper, TOOLS[params.preferred], CLUES[params.clue], ending)
    world.facts["outcome"] = "lesson"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style story for a 3-to-5-year-old that includes the words "prefer" and "floss".',
        f"Tell a small mystery where {f['setting_text']} hides a clue, someone prefers floss over a lesser tool, and bravery helps solve it.",
        "Write a short lesson-learned mystery with a repeated clue and a calm ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = world.get(f["preferred"].id) if isinstance(f.get("preferred"), Entity) else None
    helper = next(e for e in world.characters() if e.role == "helper")
    qa = [
        ("What was the mystery about?",
         f"It was about a missing floss pick and the clue trail it left behind. The children had to notice the same detail more than once to solve it."),
        ("Why did the helper prefer floss?",
         "Because floss slides into tiny spaces better than a pick. That made it the smarter tool for finding the truth in the mystery."),
        ("What did the brave child do?",
         f"{world.facts['preferred'].label_word if hasattr(world.facts['preferred'], 'label_word') else 'The child'} took a brave breath and followed the clues instead of guessing. That brave choice led to the answer."),
        ("What lesson did they learn?",
         "They learned that the best choice is not always the easiest one. When the same clue keeps coming back, it is worth paying attention to it."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"floss", "repetition", "bravery", "lesson"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "bathroom": "the bathroom, where the tiles echoed and the mirror shone",
    "kitchen": "the kitchen, where the table was crowded and the light was warm",
    "hallway": "the hallway, where shoes lined the wall like silent witnesses",
}

TOOLS = {
    "floss": Tool(id="floss", label="floss", phrase="a strand of floss", uses="slip between teeth", clean="clean the tiny gaps", sticky=False, tags={"floss"}),
    "pick": Tool(id="pick", label="toothpick", phrase="a wooden pick", uses="poke around", clean="scrape at crumbs", sticky=True, tags={"pick"}),
}

CLUES = {
    "drawer": Clue(id="drawer", label="the drawer", place="the drawer", trail="had dust on its edge", repeated_line="The drawer line kept appearing, then disappearing, then appearing again.", tags={"drawer", "repetition"}),
    "towel": Clue(id="towel", label="the towel rack", place="the towel rack", trail="was damp and bent", repeated_line="The towel rack showed the same odd mark twice, like a finger had pointed there again.", tags={"towel", "repetition"}),
}

ENDINGS = {
    "closet": Ending(id="closet", power=3, text="the supply closet", lesson="The missing floss pick was tucked inside the supply closet all along, right beside the spare soap.", tags={"closet", "lesson"}),
    "basket": Ending(id="basket", power=3, text="the laundry basket", lesson="The missing floss pick had slipped into the laundry basket, where a sock had hidden it from sight.", tags={"basket", "lesson"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Ben", "Sam"]

KNOWLEDGE = {
    "floss": [("What is floss?", "Floss is a thin string people use to clean between teeth where a brush cannot reach.")],
    "bravery": [("What is bravery?", "Bravery means doing the careful thing even when you feel a little scared.")],
    "repetition": [("What is repetition?", "Repetition means something happens or appears again and again.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a useful idea someone remembers after an experience helps them understand better.")],
}
KNOWLEDGE_ORDER = ["floss", "bravery", "repetition", "lesson"]


CURATED = [
    StoryParams(setting="bathroom", preferred="floss", clue="drawer", hero="Mia", hero_gender="girl", helper="Leo", helper_gender="boy", suspect="the cat", ending="closet"),
    StoryParams(setting="kitchen", preferred="floss", clue="towel", hero="Max", hero_gender="boy", helper="Nora", helper_gender="girl", suspect="the dog", ending="basket"),
]


def explain_rejection() -> str:
    return "(No story: this world needs floss as the preferred tool, because the mystery depends on the tiny gaps it can reach.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("preferred_tool", "floss"))
    lines.append(asp.fact("supports", "floss", "repetition"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, C) :- setting(S), tool(T), clue(C), preferred_tool(T), supports(T, repetition).
reason(T) :- preferred_tool(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid-combo sets differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.preferred not in TOOLS:
        raise StoryError("(No story: unknown tool.)")
    if params.clue not in CLUES:
        raise StoryError("(No story: unknown clue.)")
    if params.ending not in ENDINGS:
        raise StoryError("(No story: unknown ending.)")
    world = tell(params)
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
    if args.preferred and args.preferred != "floss":
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.preferred is None or c[1] == args.preferred)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, preferred, clue = rng.choice(sorted(combos))
    ending = args.ending or rng.choice(sorted(ENDINGS))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero = _pick_name(rng, hero_gender)
    helper = _pick_name(rng, helper_gender)
    suspect = rng.choice(["the cat", "the dog", "the rabbit", "the toy train"])
    return StoryParams(setting=setting, preferred=preferred, clue=clue, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, suspect=suspect, ending=ending)


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
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
