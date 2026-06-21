#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hereditary_midst_repetition_happy_ending_sound_effects.py
=========================================================================================

A tiny detective-story storyworld: a child detective notices a hereditary clue
in the midst of a noisy search, repeats the clue to others, and ends with a
happy resolution. The domain is small on purpose: one case, a few suspect
features, a family trait, a sound-filled investigation, and a gentle ending.

The story keeps a classical shape:
- premise: a little mystery begins
- middle: a clue is tested in the midst of confusion
- turn: the detective spots the inherited trait
- resolution: the right suspect is found and the ending is happy

This file is standalone and uses only stdlib plus the shared repo helpers.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Suspect:
    id: str
    label: str
    has_trait: bool = False
    noise: str = ""
    clue: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Case:
    id: str
    setting: str
    mystery: str
    repeated_phrase: str
    sound: str
    happy_image: str
    family_line: str
    resolution_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    if not detective:
        return out
    if detective.meters["searching"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["alert"] += 1
    out.append("__noise__")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    if not detective or detective.memes["clue_seen"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["confidence"] += 1
    out.append("__repeat__")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    detective = world.entities.get("detective")
    if not culprit or not detective:
        return out
    if culprit.meters["caught"] < THRESHOLD:
        return out
    sig = ("happy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["joy"] += 1
    out.append("__happy__")
    return out


CAUSAL_RULES = [_r_noise, _r_repetition, _r_happy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, case in CASES.items():
        for sid, suspect in SUSPECTS.items():
            if case.id in {"case1", "case2"} and suspect.has_trait:
                combos.append((cid, sid, "detective"))
    return combos


@dataclass
class StoryParams:
    case: str
    suspect: str
    detective: str
    name: str
    helper: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CASES = {
    "case1": Case(
        id="case1",
        setting="the old museum hall",
        mystery="a vanished silver spoon",
        repeated_phrase="the same spoon-shaped dent",
        sound="clack-clack",
        happy_image="the spoon shining on the table",
        family_line="it was hereditary",
        resolution_line="the family lock fit the family box",
        tags={"mystery", "repetition", "happy"},
    ),
    "case2": Case(
        id="case2",
        setting="the quiet bakery",
        mystery="a missing lemon tart",
        repeated_phrase="the same crumb trail",
        sound="tap-tap",
        happy_image="the tart back in its box",
        family_line="the trick was hereditary",
        resolution_line="the kitchen drawer was the right hiding place",
        tags={"mystery", "repetition", "happy"},
    ),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the baker's cat", has_trait=False, noise="mew", clue="crumbs", tags={"animal"}),
    "uncle": Suspect(id="uncle", label="the uncle", has_trait=True, noise="hum", clue="the same pocket watch", tags={"family", "hereditary"}),
    "aunt": Suspect(id="aunt", label="the aunt", has_trait=True, noise="tap", clue="the same knit gloves", tags={"family", "hereditary"}),
}

NAMES = ["Mia", "Lena", "Noah", "Ivy", "Theo", "Ruby"]
HELPERS = ["the officer", "the shopkeeper", "the guard"]


def reasonableness_gate(case: Case, suspect: Suspect) -> None:
    if not suspect.has_trait:
        raise StoryError("This suspect does not fit the hereditary clue, so the mystery has no fair solution.")
    if "mystery" not in case.tags:
        raise StoryError("This case does not support a detective story.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.case not in CASES:
        raise StoryError("Unknown case.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    case_id = args.case or rng.choice(sorted(CASES))
    suspect_id = args.suspect or rng.choice(sorted([k for k, v in SUSPECTS.items() if v.has_trait]))
    reasonableness_gate(CASES[case_id], SUSPECTS[suspect_id])
    detective = args.detective or "detective"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(case=case_id, suspect=suspect_id, detective=detective, name=name, helper=helper)


def tell(case: Case, suspect: Suspect, detective_name: str, helper: str) -> World:
    world = World()
    det = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    det.meters["searching"] += 1
    det.memes["curious"] += 1
    ally = world.add(Entity(id="helper", kind="character", type="woman", role="helper", label=helper))
    culprit = world.add(Entity(id="culprit", kind="character", type="man" if suspect.id == "uncle" else "woman", role="culprit", label=suspect.label))
    clue = world.add(Entity(id="clue", kind="thing", label=case.repeated_phrase))
    world.say(
        f"In the midst of the crowd at {case.setting}, {detective_name} began a small detective story. "
        f"A mystery waited: {case.mystery}."
    )
    world.say(
        f'"{case.sound}," went the room as {detective_name} looked again and again at {case.repeated_phrase}. '
        f'The clue came back, and back, and back.'
    )
    world.para()
    det.meters["searching"] += 1
    det.memes["clue_seen"] += 1
    world.say(
        f'{detective_name} whispered, "{case.family_line}." The words mattered because {suspect.label} had the same habit, '
        f"the same clue, the same family way of moving."
    )
    world.say(
        f'"{case.sound}!" said {helper}, and {detective_name} followed the sound through the midst of the hall.'
    )
    world.para()
    culprit.meters["caught"] += 1
    det.memes["confidence"] += 1
    world.say(
        f"At last, the right pocket opened, and the missing thing was there all along. {case.resolution_line}."
    )
    world.say(
        f"{detector_ending(detective_name, suspect, case)}"
    )
    world.facts.update(
        detective=det,
        helper=ally,
        culprit=culprit,
        clue=clue,
        suspect=suspect,
        case=case,
        happy=True,
    )
    return world


def detector_ending(detective_name: str, suspect: Suspect, case: Case) -> str:
    return (
        f'{detective_name} smiled, because the answer was simple at last: the clue was hereditary, '
        f"so the family detail led to the culprit, and {case.happy_image} made the ending feel warm."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    suspect: Suspect = f["suspect"]
    return [
        f'Write a child-friendly detective story that uses the words "hereditary" and "midst".',
        f"Tell a short mystery where {case.mystery} is found in the midst of a noisy search and the clue turns out to be hereditary.",
        f"Write a happy detective story with repetition and sound effects, where {suspect.label} is identified by a family trait.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    case: Case = f["case"]
    suspect: Suspect = f["suspect"]
    det: Entity = f["detective"]
    qa = [
        ("What kind of story is this?",
         f"It is a detective story about a small mystery and a child who keeps looking carefully until the answer appears."),
        ("What clue mattered most?",
         f"The clue was {case.repeated_phrase}. It mattered because it was hereditary, which means it came from the family and helped point to the right suspect."),
        ("What happened in the midst of the search?",
         f"In the midst of the crowd and noise, {det.id} kept listening and looking. The repeated sound and the repeated clue helped the detective stay focused."),
        ("How did the story end?",
         f"It ended happily when {suspect.label} was connected to the family clue and the missing thing was found. The ending image was {case.happy_image}."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does hereditary mean?",
         "Hereditary means something is passed down in a family from parents to children."),
        ("What is a detective?",
         "A detective is someone who looks for clues and solves mysteries."),
        ("Why do repeated clues matter?",
         "Repeated clues can help a detective notice a pattern. A pattern can make the answer easier to find."),
        ("What do sound effects do in a story?",
         "Sound effects help the reader hear the action in their mind. They can make a scene feel lively and fun."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("setting", cid, case.setting))
        lines.append(asp.fact("family_line", cid, case.family_line))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if suspect.has_trait:
            lines.append(asp.fact("hereditary", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid_case(C,S) :- case(C), suspect(S), hereditary(S).
sensible_case(C,S) :- valid_case(C,S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_case/2."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(case=None, suspect=None, detective=None, name=None, helper=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld with hereditary clues and a happy ending.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective")
    ap.add_argument("--name")
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
    case = args.case or rng.choice(sorted(CASES))
    suspect = args.suspect or rng.choice(sorted([k for k, v in SUSPECTS.items() if v.has_trait]))
    if suspect not in SUSPECTS or case not in CASES:
        raise StoryError("Unknown story choice.")
    if not SUSPECTS[suspect].has_trait:
        raise StoryError("This suspect cannot fit the hereditary clue.")
    detective = args.detective or "detective"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(case=case, suspect=suspect, detective=detective, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    case = CASES.get(params.case)
    suspect = SUSPECTS.get(params.suspect)
    if case is None or suspect is None:
        raise StoryError("Invalid parameters.")
    world = tell(case, suspect, params.name, params.helper)
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
    StoryParams(case="case1", suspect="uncle", detective="detective", name="Mia", helper="the officer"),
    StoryParams(case="case2", suspect="aunt", detective="detective", name="Noah", helper="the shopkeeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_case/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid case/suspect combos:")
        for case, suspect in asp_valid_combos():
            print(f"  {case:6} {suspect}")
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
