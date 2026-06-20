#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hospital_alternative_mystery_to_solve_rhyming_story.py
======================================================================================

A small storyworld for a rhyming mystery set in a hospital.

Premise:
- A child arrives at the hospital worried about a missing comfort item.
- A parent or helper notices clues, and the pair solve the mystery by finding
  the item or discovering a kind alternative that works just as well.
- The story stays concrete and state-driven: clues accumulate, feelings change,
  and the ending proves what changed.

This world is intentionally tiny and constraint-checked. It produces only
reasonable combinations and includes an ASP twin for parity checks.
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
    detail: str
    mood: str

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
    missing: str
    clue: str
    found_where: str
    rhyme_a: str
    rhyme_b: str

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
class Alternative:
    id: str
    label: str
    phrase: str
    action: str
    comfort: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role != "child":
            continue
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["search"] += 1
        out.append("__mystery__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role != "child":
            continue
        if e.meters["clue"] < THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__clue__")
    return out


def _r_alternative(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role != "child":
            continue
        if e.memes["relief"] < THRESHOLD:
            continue
        sig = ("alt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        out.append("__alt__")
    return out


RULES = [Rule("worry", "social", _r_worry), Rule("clue", "mystery", _r_clue), Rule("alt", "ending", _r_alternative)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solveable(mystery: Mystery, alternative: Alternative) -> bool:
    return "comfort" in alternative.tags or alternative.id == "find_item"


SETTINGS = {
    "ward": Setting("ward", "the hospital ward", "Soft lights glowed along the hall.", "quiet"),
    "lobby": Setting("lobby", "the hospital lobby", "The desk bell gave a tiny ding.", "busy"),
    "playroom": Setting("playroom", "the playroom", "Toy blocks sat in a bright square.", "cheery"),
}

MYSTERIES = {
    "bear": Mystery("bear", "a teddy bear", "a scarf on a chair", "the waiting-room bench", "bear / chair", "stair"),
    "cup": Mystery("cup", "a blue cup", "a note by the sink", "the nurse's shelf", "cup / note", "float"),
    "book": Mystery("book", "a picture book", "a page with crumbs", "under the blanket", "book / book", "moon"),
}

ALTERNATIVES = {
    "find_item": Alternative("find_item", "a quick search", "look in the room together", "search", "hope", {"comfort"}),
    "blanket": Alternative("blanket", "a warm blanket", "wrap up in a warm blanket", "wrap", "warmth", {"comfort"}),
    "song": Alternative("song", "a soft song", "sing a soft song together", "sing", "calm", {"comfort"}),
    "gown": Alternative("gown", "a hospital gown", "wear a soft hospital gown", "wear", "ease", {"hospital"}),
}

NAMES = ["Lily", "Mia", "Noah", "Ben", "Ava", "Zoe", "Eli", "Maya"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    alternative: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


def reason_ok(mystery: Mystery, alternative: Alternative) -> bool:
    return solveable(mystery, alternative)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for mid, mystery in MYSTERIES.items():
            for aid, alt in ALTERNATIVES.items():
                if reason_ok(mystery, alt):
                    out.append((sid, mid, aid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming hospital mystery with an alternative ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for aid, alt in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", aid))
        if "comfort" in alt.tags:
            lines.append(asp.fact("comfort", aid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, A) :- setting(S), mystery(M), alternative(A), comfort(A).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    params = resolve_params(build_parser().parse_args([]), random.Random(7))
    sample = generate(params)
    if not sample.story.strip():
        print("MISMATCH: generated story is empty.")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def story_rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(setting: Setting, mystery: Mystery, alternative: Alternative, child: Entity, helper: Entity) -> World:
    world = World(setting)
    child.memes["worry"] = 1
    helper.memes["care"] = 1
    world.add(child)
    world.add(helper)
    world.say(
        f"In the {setting.place}, soft and still, "
        f"{child.id} felt a twinge of worry spill."
    )
    world.say(
        f"{child.id} could not find {mystery.missing}, oh dear, "
        f"and looked for a clue with a trembling tear."
    )
    world.para()
    child.meters["clue"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} said, with a gentle glow, "
        f'"Let’s follow the clue and see what we know."'
    )
    world.say(
        f"They found {mystery.clue}, neat as could be, "
        f"and that was the clue in the mystery."
    )
    world.para()
    world.say(
        f'"Maybe we try {alternative.phrase}," said {helper.id}, bright and sweet, '
        f'"a kinder idea that feels complete."'
    )
    child.meters["choice"] += 1
    if solveable(mystery, alternative):
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        world.say(
            f"{child.id} tried the new way, with a hopeful grin, "
            f"and calm came softly drifting in."
        )
        world.say(
            f"At last they found {mystery.found_where}, tucked up tight, "
            f"and {child.id} smiled in the hospital light."
        )
        world.say(
            f"So {child.id} kept {mystery.missing}, safe and near, "
            f"and the little worry melted clear."
        )
    else:
        child.memes["relief"] += 1
        world.say(
            f"The first idea helped, but not quite right, "
            f"so they chose another, warm and bright."
        )
        world.say(
            f"With {alternative.label}, the room felt kind, "
            f"and {child.id} still felt peace of mind."
        )
    world.facts.update(setting=setting, mystery=mystery, alternative=alternative, child=child, helper=helper)
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in a hospital that includes the words "hospital" and "alternative" and solves a small mystery.',
        f"Tell a gentle hospital mystery in rhyme where {f['child'].id} loses {f['mystery'].missing} and then finds it with help.",
        f"Write a child-friendly rhyming story about an alternative that helps solve a mystery in a hospital.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    alt = f["alternative"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was the mystery?",
            answer=f"The mystery was finding {mystery.missing}. The clues led them through the hospital until they solved it."
        ),
        QAItem(
            question=f"What did {helper.id} offer as an alternative?",
            answer=f"{helper.id} offered {alt.phrase}. It gave {child.id} a calmer way to keep going while they searched."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {mystery.missing} found and {child.id} feeling relieved. The hospital felt quiet and safe again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hospital?",
            answer="A hospital is a place where people go to get help, rest, and care from doctors and nurses."
        ),
        QAItem(
            question="What is an alternative?",
            answer="An alternative is another choice you can try when the first idea does not fit well."
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help people figure out what is happening and solve the puzzle."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    child = Entity(id=params.child, kind="character", type=params.child_gender, role="child")
    helper = Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], ALTERNATIVES[params.alternative], child, helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.alternative is None or c[2] == args.alternative)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, alternative = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.name or rng.choice(NAMES)
    helper = args.helper or ("mother" if helper_gender == "mother" else "father")
    return StoryParams(setting, mystery, alternative, child, child_gender, helper, helper_gender, args.seed)


CURATED = [
    StoryParams("ward", "bear", "find_item", "Lily", "girl", "mother", "mother"),
    StoryParams("lobby", "cup", "song", "Noah", "boy", "father", "father"),
    StoryParams("playroom", "book", "blanket", "Mia", "girl", "mother", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
