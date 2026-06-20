#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lint_deduction_repetition_mystery.py
=====================================================================

A small mystery storyworld about a child detective, a curious bit of lint, and a
repeating clue pattern that leads to a gentle deduction.

Seed words:
- lint
- deduction

Style:
- Mystery

Feature:
- Repetition

The domain is intentionally tiny: a missing small object in a cozy place, a
series of repeated clues, and a careful child who uses pattern-based deduction to
find the answer. The story should feel like a complete miniature mystery with a
clear beginning, a clue-driven middle, and an ending image that proves what was
learned.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    repeated_sound: str
    hiding_spot: str

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
class Clue:
    id: str
    text: str
    hint: str
    repeat_count: int
    leads_to: str

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
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue_style: str
    honest: bool = False

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
class Outcome:
    id: str
    label: str
    truth: str
    ending_image: str

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
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    if not clue:
        return out
    signal = clue.text
    key = ("repeat", clue.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    watcher = world.get("detective")
    watcher.memes["pattern"] += 1
    watcher.memes["focus"] += 1
    world.say(signal)
    world.say(signal)
    out.append("__repeat__")
    return out


def _r_deduction(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    suspect = world.facts.get("suspect")
    if not clue or not suspect:
        return out
    key = ("deduce", clue.id, suspect.id)
    if key in world.fired:
        return out
    detective = world.get("detective")
    if detective.memes["pattern"] < THRESHOLD:
        return out
    world.fired.add(key)
    detective.memes["certainty"] += 1
    world.facts["deduced"] = True
    out.append(f"That same clue again made {detective.id} think harder.")
    return out


CAUSAL_RULES = [
    _r_repetition,
    _r_deduction,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_deduction(world: World) -> str:
    detective = world.get("detective")
    clue = world.facts["clue"]
    suspect = world.facts["suspect"]
    if detective.memes["certainty"] < THRESHOLD:
        raise StoryError("The detective never reached a real deduction.")
    return f"{detective.id} knew the answer: {suspect.label} was the one who left the {clue.leads_to} behind."


def set_up(world: World, detective: Entity, helper: Entity, clue: Clue, suspect: Suspect) -> None:
    detective.memes["curious"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"On a quiet afternoon, {detective.id} and {helper.id} were in {world.setting.place}. "
        f"The room felt {world.setting.mood}, and something small had gone missing."
    )
    world.say(
        f"{helper.id} noticed a little {clue.leads_to} near {world.setting.hiding_spot}, and said it in a whisper."
    )


def inspect(world: World, detective: Entity, clue: Clue, suspect: Suspect) -> None:
    world.say(
        f"{detective.id} looked once, then looked again, because the same thing kept showing up: {clue.text}"
    )
    world.say(
        f"It happened {clue.repeat_count} times, which was enough for a careful deduction."
    )
    world.say(
        f"{suspect.label} seemed important, but {suspect.motive} did not fit the little trail."
    )


def reveal(world: World, detective: Entity, suspect: Suspect, clue: Clue, outcome: Outcome) -> None:
    world.say(
        f"{detective.id} tapped the lint from the table edge and smiled."
        f" {mystery_deduction(world)}"
    )
    world.say(
        f"The answer was simple at last: {outcome.truth}."
    )
    world.say(outcome.ending_image)


def tell(setting: Setting, clue: Clue, suspect: Suspect, outcome: Outcome,
         detective_name: str = "Mina", detective_type: str = "girl",
         helper_name: str = "Ned", helper_type: str = "boy") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="lint", type="thing", label="lint"))
    world.facts.update(clue=clue, suspect=suspect, outcome=outcome)

    set_up(world, detective, helper, clue, suspect)
    world.para()
    inspect(world, detective, clue, suspect)
    world.para()
    propagate(world, narrate=True)
    reveal(world, detective, suspect, clue, outcome)
    world.facts.update(detective=detective, helper=helper, deduced=True)
    return world


SETTINGS = {
    "laundry_room": Setting(
        "laundry_room",
        "the laundry room",
        "warm and a little echoey",
        "tap-tap",
        "the dryer door",
    ),
    "bedroom": Setting(
        "bedroom",
        "the bedroom",
        "soft and sleepy",
        "shhh-shhh",
        "the bedspread fold",
    ),
    "playroom": Setting(
        "playroom",
        "the playroom",
        "bright but puzzling",
        "tick-tick",
        "the toy basket edge",
    ),
}

CLUES = {
    "lint": Clue(
        "lint",
        "lint",
        "tiny lint",
        2,
        "lint",
    ),
    "thread": Clue(
        "thread",
        "thread",
        "a short thread",
        2,
        "thread",
    ),
    "crumb": Clue(
        "crumb",
        "crumb",
        "a crumb",
        2,
        "crumb",
    ),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "cat", "curiosity", "paws and whiskers", False),
    "sweater": Suspect("sweater", "the sweater", "thing", "hiding in a basket", "fuzzy fibers", False),
    "helper": Suspect("helper", "the helper", "person", "neat hands", "careful steps", True),
}

OUTCOMES = {
    "found": Outcome("found", "found", "the missing thing had been tucked under the bed", "The bed looked neat again, with one tiny lint speck left to shine like a clue."),
    "basket": Outcome("basket", "basket", "the missing thing had slipped into the basket", "The basket sat still and honest, while the lint rested on top like a final note."),
    "chair": Outcome("chair", "chair", "the missing thing had been nudged under the chair", "The chair stood in the sun, and the lint twinkled on the floorboards."),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Ned", "Theo", "Finn", "Max", "Eli", "Jack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for su in SUSPECTS:
                combos.append((s, c, su))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    outcome: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
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


KNOWLEDGE = {
    "lint": [("What is lint?", "Lint is a tiny bit of fluff from cloth. It often gathers in pockets, baskets, and corners.")],
    "deduction": [("What is deduction?", "Deduction is when you think carefully from clues to figure out what is true.")],
    "mystery": [("What is a mystery?", "A mystery is a story about a puzzle that needs clues and careful thinking to solve.")],
    "repeat": [("Why repeat a clue?", "Repeating a clue makes it easier to notice a pattern. A pattern can help someone solve a mystery.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that uses the words "lint" and "deduction".',
        f"Tell a cozy mystery where {f['detective'].id} notices a repeated clue and solves the puzzle by deduction.",
        f"Write a gentle story with repetition, a small clue, and a clear ending where the answer is finally revealed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    outcome: Outcome = f["outcome"]
    return [
        ("Who is the story about?",
         f"It is about {detective.id}, who likes solving small mysteries, and {helper.id}, who helps notice details."),
        ("What clue kept appearing?",
         f"The clue was {clue.text}. It repeated {clue.repeat_count} times, and that repetition helped {detective.id} see a pattern."),
        ("How did the detective solve the mystery?",
         f"{detective.id} used deduction by comparing the repeated clue with the place and the suspect. That careful thinking made the answer clear."),
        ("What was the answer?",
         f"{outcome.truth}. The ending showed that the puzzle was solved and the room felt calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lint", "deduction", "mystery", "repeat"}
    out: list[tuple[str, str]] = []
    for key in ["lint", "deduction", "mystery", "repeat"]:
        out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("laundry_room", "lint", "cat", "found", "Mina", "girl", "Ned", "boy"),
    StoryParams("bedroom", "thread", "sweater", "basket", "Lily", "girl", "Theo", "boy"),
    StoryParams("playroom", "crumb", "helper", "chair", "Nora", "girl", "Max", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this mystery needs a repeated clue and a clear deduction, but the chosen options do not form a stable puzzle.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    clue = args.clue or rng.choice(sorted(CLUES))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    det_name = args.detective_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    det_type = args.detective_type or ("girl" if det_name in GIRL_NAMES else "boy")
    help_name = args.helper_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != det_name])
    help_type = args.helper_type or ("girl" if help_name in GIRL_NAMES else "boy")
    return StoryParams(setting, clue, suspect, outcome, det_name, det_type, help_name, help_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        SUSPECTS[params.suspect],
        OUTCOMES[params.outcome],
        params.detective_name,
        params.detective_type,
        params.helper_name,
        params.helper_type,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with lint, deduction, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


ASP_RULES = r"""
repeat(C) :- clue(C), repeat_count(C, N), N >= 2.
deduced(D) :- detective(D), repeat(C).
valid(S, C, U) :- setting(S), clue(C), suspect(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeat_count", cid, c.repeat_count))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for oid in OUTCOMES:
        lines.append(asp.fact("outcome", oid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show repeat/1.\n#show deduced/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.setting}, {p.clue}, {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
