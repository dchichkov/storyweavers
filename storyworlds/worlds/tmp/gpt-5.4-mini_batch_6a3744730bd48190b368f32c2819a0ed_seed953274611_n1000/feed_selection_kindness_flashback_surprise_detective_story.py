#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/feed_selection_kindness_flashback_surprise_detective_story.py
============================================================================================

A small storyworld in a detective-story style.

Premise:
- A child detective investigates a missing pet feeding plan.
- The case turns on a selection of treats/feeds, a kindness choice, a flashback clue,
  and a surprise reveal.
- The generated story is state-driven, with a clear setup, turn, and resolution.

Seed words:
- feed
- selection

Features:
- Kindness
- Flashback
- Surprise

Style:
- Detective Story
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
class FeedItem:
    id: str
    label: str
    kind: str
    scent: str
    appeal: int
    wholesome: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Selection:
    id: str
    label: str
    note: str
    fit: int
    items: tuple[str, ...]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    case: str
    selection: str
    kindness: str
    flashback: str
    surprise: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    caretaker: str
    seed: Optional[int] = None


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    if case.meters["missing"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["focus"] += 1
    helper.memes["curiosity"] += 1
    out.append("The room felt quiet enough for a clue to whisper.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["remembered"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["memory"] += 1
    out.append("A little flashback opened in the detective's mind, bright as a tucked-away lantern.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    if case.meters["solved"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.get("helper")
    helper.memes["surprise"] += 1
    out.append("Then came a surprise so small and sudden it made everyone blink.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("flashback", _r_flashback), Rule("surprise", _r_surprise)]


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


def select_feed(world: World, detective: Entity, option: FeedItem, selection: Selection) -> None:
    detective.memes["analysis"] += 1
    world.say(
        f"{detective.id} studied the {selection.label} with a detective's care. "
        f"It was a {option.label} kind of choice, and the word feed fit it perfectly."
    )


def flashback_clue(world: World, detective: Entity, helper: Entity, flashback: str) -> None:
    detective.meters["remembered"] += 1
    world.get("clue").meters["remembered"] += 1
    world.say(
        f"That made {detective.id} remember a {flashback} from earlier. "
        f"{helper.id} had seen the same bowl and the same careful pause."
    )


def kindness_turn(world: World, detective: Entity, helper: Entity, caretaker: Entity) -> None:
    detective.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f'"Let us be kind," {helper.id} said. "{caretaker.label_word.capitalize()} '
        f"would want the pet fed, not hurried."
    )


def solve_case(world: World, detective: Entity, option: FeedItem, selection: Selection) -> None:
    case = world.get("case")
    case.meters["solved"] += 1
    world.say(
        f"{detective.id} matched the clues at last. The {selection.label} was the right selection, "
        f"because the {option.label} was gentle and safe."
    )


def surprise_reveal(world: World, detective: Entity, helper: Entity, caretaker: Entity, option: FeedItem) -> None:
    world.say(
        f"Then came the surprise: the missing piece was not gone at all. "
        f"{caretaker.id} had already left a note, and {helper.id} had tucked the {option.label} by the bowl."
    )
    world.say(
        f"{detective.id} smiled. The case was simple now: feed first, ask questions second, and always choose kindly."
    )


def tell(case: str, selection: Selection, kindness: str, flashback: str, surprise: str,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         caretaker: str = "Mom") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective", traits=["sharp", "kind"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["helpful", "curious"]))
    keeper = world.add(Entity(id="Caretaker", kind="character", type="mother" if caretaker.lower() in {"mom", "mother"} else "father", label=f"the {caretaker.lower()}"))
    case_ent = world.add(Entity(id="case", type="case", label=case, role="mystery"))
    clue = world.add(Entity(id="clue", type="memory", label="memory clue"))
    world.add(Entity(id="choice", type="selection", label=selection.label))
    world.facts.update(
        detective=detective,
        helper=helper,
        caretaker=keeper,
        case=case_ent,
        clue=clue,
        selection=selection,
        kindness=kindness,
        flashback=flashback,
        surprise=surprise,
        option=FEEDS[selection.items[0]],
    )

    option = FEEDS[selection.items[0]]
    detective.memes["curiosity"] += 1
    helper.memes["hope"] += 1

    world.say(
        f"Detective {detective.id} looked at the kitchen like it was a quiet crime scene. "
        f"The pet bowl was waiting, and the day's feed selection felt strangely important."
    )
    world.say(
        f"{helper.id} pointed to the shelf. \"There are two choices,\" {helper.pronoun()} said, "
        f"\"but only one is the kind selection we should make.\""
    )
    select_feed(world, detective, option, selection)

    world.para()
    kindness_turn(world, detective, helper, keeper)
    flashback_clue(world, detective, helper, flashback)
    if selection.fit >= 2:
        solve_case(world, detective, option, selection)
    else:
        world.say(
            f"{detective.id} almost chose too quickly, but {helper.id} slowed the room down with a kind word."
        )
        solve_case(world, detective, option, selection)

    world.para()
    world.get("case").meters["missing"] = 0.0
    world.get("case").meters["solved"] = 1.0
    world.get("clue").meters["remembered"] = 1.0
    propagate(world, narrate=False)
    surprise_reveal(world, detective, helper, keeper, option)

    world.facts["outcome"] = "solved"
    return world


FEEDS = {
    "kibble": FeedItem(id="kibble", label="kibble", kind="dry food", scent="plain", appeal=2, wholesome=True, tags={"feed"}),
    "carrot": FeedItem(id="carrot", label="carrot bits", kind="crunchy snack", scent="sweet", appeal=1, wholesome=True, tags={"feed", "kindness"}),
    "fish": FeedItem(id="fish", label="fish flakes", kind="soft food", scent="bright", appeal=3, wholesome=True, tags={"feed", "surprise"}),
    "treat": FeedItem(id="treat", label="tiny treats", kind="reward snack", scent="warm", appeal=3, wholesome=True, tags={"feed", "selection"}),
}

SELECTIONS = {
    "careful": Selection(id="careful", label="careful selection", note="The careful selection keeps the pet calm.", fit=3, items=("kibble", "treat"), tags={"selection", "kindness"}),
    "gentle": Selection(id="gentle", label="gentle selection", note="The gentle selection slows the room down.", fit=3, items=("carrot", "kibble"), tags={"selection", "flashback"}),
    "bright": Selection(id="bright", label="bright selection", note="The bright selection makes a small surprise.", fit=2, items=("fish", "treat"), tags={"selection", "surprise"}),
}

CASES = {
    "pet_bowl": "the missing pet bowl feed",
    "kitchen_note": "the kitchen note mystery",
    "midnight_feed": "the midnight feed selection",
}

KID_NAMES_GIRL = ["Mina", "Ivy", "Nora", "Lena", "Tess"]
KID_NAMES_BOY = ["Pip", "Otto", "Finn", "Theo", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CASES:
        for s in SELECTIONS:
            combos.append((c, s, "kindness"))
    return combos


def explain_rejection(case: str, selection: str) -> str:
    return f"(No story: the selection '{selection}' does not fit the case '{case}' well enough for a detective story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a detective, a feed selection, kindness, flashback, and surprise.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--selection", choices=SELECTIONS)
    ap.add_argument("--kindness", choices=["kindness"])
    ap.add_argument("--flashback", choices=["memory", "earlier", "before"])
    ap.add_argument("--surprise", choices=["small", "big", "gentle"])
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["Mom", "Dad"])
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
    case = args.case or rng.choice(list(CASES))
    selection = args.selection or rng.choice(list(SELECTIONS))
    if args.selection and args.selection not in SELECTIONS:
        raise StoryError("(Unknown selection.)")
    flashback = args.flashback or rng.choice(["memory", "earlier", "before"])
    surprise = args.surprise or rng.choice(["small", "big", "gentle"])
    kindness = "kindness"
    det_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if det_gender == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(KID_NAMES_GIRL if det_gender == "girl" else KID_NAMES_BOY)
    helper_name = args.helper_name or rng.choice(KID_NAMES_BOY if helper_gender == "boy" else KID_NAMES_GIRL)
    caretaker = args.caretaker or rng.choice(["Mom", "Dad"])
    return StoryParams(case=case, selection=selection, kindness=kindness, flashback=flashback, surprise=surprise,
                       detective_name=detective_name, detective_gender=det_gender,
                       helper_name=helper_name, helper_gender=helper_gender, caretaker=caretaker)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that uses the words "feed" and "selection" and shows kindness.',
        f"Tell a small mystery where {f['detective'].id} makes a careful feed selection, remembers a flashback clue, and gets a surprise at the end.",
        f"Write a child-facing detective story where a kind helper helps solve the feed selection case.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    caretaker = f["caretaker"]
    sel = f["selection"]
    option = f["option"]
    return [
        ("Who is the story about?", f"It is about detective {det.id} and {helper.id}, who work on a small mystery together."),
        ("What did they need to do?", f"They needed to choose the right feed selection for the pet and make sure it was done kindly."),
        ("What did the flashback do?", f"It reminded {det.id} of an earlier clue. That helped the detective slow down and make a better choice."),
        ("How did kindness matter?", f"{helper.id} used a kind voice and {caretaker.id} wanted the pet fed calmly. That kept the case gentle instead of rushed."),
        ("What was surprising at the end?", f"The surprise was that the missing piece was already there. The note and the tucked-away {option.label} showed the mystery had a simple answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does feed mean?", "To feed means to give food to a person or animal."),
        ("What is a selection?", "A selection is a choice made from a group of things."),
        ("What is kindness?", "Kindness means being gentle, caring, and helpful to others."),
        ("What is a flashback?", "A flashback is when a story or a person remembers something from earlier."),
        ("What is a surprise?", "A surprise is something you did not expect to happen."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
choice(C) :- case(C).
pick(S) :- selection(S).
valid(C,S) :- choice(C), pick(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CASES:
        lines.append(asp.fact("case", c))
    for s in SELECTIONS:
        lines.append(asp.fact("selection", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp as aspmod
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(case=None, selection=None, kindness=None, flashback=None, surprise=None,
                                                           detective_name=None, detective_gender=None, helper_name=None, helper_gender=None,
                                                           caretaker=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES or params.selection not in SELECTIONS:
        raise StoryError("(Invalid story parameters.)")
    world = tell(
        case=CASES[params.case],
        selection=SELECTIONS[params.selection],
        kindness=params.kindness,
        flashback=params.flashback,
        surprise=params.surprise,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        caretaker=params.caretaker,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(case="pet_bowl", selection="careful", kindness="kindness", flashback="memory", surprise="small",
                detective_name="Mina", detective_gender="girl", helper_name="Pip", helper_gender="boy", caretaker="Mom"),
    StoryParams(case="kitchen_note", selection="gentle", kindness="kindness", flashback="earlier", surprise="gentle",
                detective_name="Ivy", detective_gender="girl", helper_name="Theo", helper_gender="boy", caretaker="Dad"),
    StoryParams(case="midnight_feed", selection="bright", kindness="kindness", flashback="before", surprise="big",
                detective_name="Jude", detective_gender="boy", helper_name="Nora", helper_gender="girl", caretaker="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
