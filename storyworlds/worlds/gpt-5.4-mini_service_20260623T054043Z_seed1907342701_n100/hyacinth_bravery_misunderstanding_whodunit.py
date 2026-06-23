#!/usr/bin/env python3
"""
storyworlds/worlds/hyacinth_bravery_misunderstanding_whodunit.py
===============================================================

A small whodunit storyworld about bravery, misunderstandings, and a missing
hyacinth. The world is intentionally simple: one mystery, a few plausible
settings, a small cast, and a state-driven resolution that proves what changed.

The seed premise:
- A child notices a hyacinth has gone missing.
- A misunderstanding points suspicion at the wrong person.
- The child uses bravery to ask careful questions.
- The real cause turns out to be ordinary and concrete, not sinister.
- The ending image shows the hyacinth restored and the misunderstanding gone.

This script follows the Storyweavers world contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    surface: str
    clue: str
    wind: bool = False
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    verb: str
    cause: str
    mistaken_sign: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    action: str
    effect: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting("garden", "the garden", "the damp path", "a little blue petal", wind=True, affords={"wind", "mud"}),
    "greenhouse": Setting("greenhouse", "the greenhouse", "the potting bench", "a broken latch", indoors=True, affords={"tool", "water"}),
    "porch": Setting("porch", "the front porch", "the step", "a muddy footprint", wind=True, affords={"wind", "mud"}),
    "shed": Setting("shed", "the shed", "the shelf", "an open window", indoors=True, affords={"tool", "wind"}),
}

MYSTERIES = {
    "hyacinth": Mystery(
        "hyacinth", "the hyacinth pot", "find the missing hyacinth",
        "a gust of wind tipped the pot",
        "a smear of dirt on the windowsill looked like theft",
        "The hyacinth had only rolled behind a crate.",
        tags={"hyacinth", "flower", "wind"},
    ),
    "lantern": Mystery(
        "lantern", "the little lantern", "find the missing lantern",
        "a helper moved it for safekeeping",
        "a dark stain looked like soot",
        "The lantern was tucked under a cloth by the sink.",
        tags={"lantern", "tool"},
    ),
    "seedbag": Mystery(
        "seedbag", "the seed bag", "find the missing seed bag",
        "a rabbit nudged it into the grass",
        "a torn corner looked like a theft note",
        "The seed bag was under the bench, safe and dry.",
        tags={"seed", "garden"},
    ),
    "key": Mystery(
        "key", "the brass key", "find the missing key",
        "it slipped into a crack in the boards",
        "a shiny line on the floor looked deliberate",
        "The brass key had fallen beside the porch step.",
        tags={"key", "porch"},
    ),
}

RESPONSES = {
    "ask": Response("ask", "asked careful questions", "the truth came out", tags={"bravery", "talk"}),
    "look": Response("look", "looked under the right things", "the hidden item was found", tags={"search"}),
    "call": Response("call", "called a grown-up", "the grown-up explained the clue", tags={"help"}),
}

GIRL_NAMES = ["Mina", "Iris", "Nina", "Lena", "Maya", "Ruby"]
BOY_NAMES = ["Owen", "Eli", "Toby", "Noah", "Finn", "Theo"]
HELPER_NAMES = ["June", "Paul", "Sana", "Marta", "Luca", "Jules"]
TRAITS = ["brave", "curious", "careful", "steady"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    setting = world.setting
    mystery = world.facts["mystery"]
    if child.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("misunderstanding", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("helper").memes["worry"] += 1
    return [f"__misunderstanding__"]


def _r_bravery(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["bravery"] < THRESHOLD:
        return []
    sig = ("brave", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["confidence"] += 1
    return []


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery.id == "hyacinth" and not setting.wind:
                continue
            if mystery.id == "key" and setting.id != "porch":
                continue
            if mystery.id == "lantern" and setting.id not in {"greenhouse", "shed"}:
                continue
            combos.append((sid, mid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.wind:
            lines.append(asp.fact("windy", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if mid == "hyacinth":
            lines.append(asp.fact("needs_wind", mid))
        if mid == "key":
            lines.append(asp.fact("needs_porch", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M), needs_wind(M), windy(S).
valid(S, M) :- setting(S), mystery(M), needs_porch(M), S = porch.
valid(S, M) :- setting(S), mystery(M), not needs_wind(M), not needs_porch(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a missing hyacinth.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = rng.choice(["girl", "boy"])
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mystery=mystery, response=response,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def _story_setup(world: World) -> None:
    child = world.add(Entity(id="child", kind="character", type=world.facts["child_gender"], label=world.facts["child_name"], role="detective", meters={}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type=world.facts["helper_gender"], label=world.facts["helper_name"], role="helper", meters={}, memes={}))
    mystery = world.facts["mystery"]
    child.meters["attention"] = 1
    child.memes["bravery"] = 0
    child.memes["suspicion"] = 0
    child.memes["confidence"] = 0
    helper.meters["attention"] = 1
    helper.memes["worry"] = 0
    world.say(f"{child.label_word} noticed that {mystery.missing} was gone from {world.setting.place}.")
    world.say(f"{world.setting.place.capitalize()} was quiet except for {world.setting.surface}, and {mystery.missing} should have been easy to see.")
    world.para()
    if world.setting.wind:
        world.say("A breeze moved the leaves and made the scene feel strange.")
    else:
        world.say("Everything looked still, which made the missing thing seem even more suspicious.")


def tell(world: World, params: StoryParams) -> World:
    world.facts.update(child_name=params.child_name, child_gender=params.child_gender,
                       helper_name=params.helper_name, helper_gender=params.helper_gender)
    mystery = MYSTERIES[params.mystery]
    world.facts["mystery"] = mystery
    world.facts["response"] = RESPONSES[params.response]
    _story_setup(world)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["suspicion"] += 1
    world.say(f"{child.label_word} thought the clue might mean someone had taken {mystery.missing}.")
    world.say(f"{helper.label_word} frowned, because {mystery.mistaken_sign} looked bad at first.")
    propagate(world)
    world.para()
    child.memes["bravery"] += 1
    world.say(f"But {child.label_word} took a breath and decided to {world.facts['response'].action}.")
    world.say(f"{child.label_word.capitalize()} asked one brave question after another.")
    helper.memes["worry"] += 1
    if params.mystery == "hyacinth":
        world.say("The answer turned the misunderstanding around.")
    world.para()
    if params.mystery == "hyacinth":
        world.say("Behind a crate, the hyacinth was there all along, tipped on its side but unharmed.")
        world.say("The wind had nudged it, and the dirt on the windowsill had only come from the pot.")
    elif params.mystery == "lantern":
        world.say("Under a cloth near the sink, the lantern waited where it had been set down for safety.")
        world.say("The dark stain was only an old water mark, not soot.")
    elif params.mystery == "seedbag":
        world.say("Under the bench, the seed bag sat where a rabbit had nudged it.")
        world.say("The torn corner came from rough grass, not from theft.")
    else:
        world.say("Beside the porch step, the brass key had slipped into a crack between the boards.")
        world.say("The shiny line on the floor was only a reflection from the morning light.")
    world.say(f"{helper.label_word} laughed softly, and {child.label_word} smiled because the mystery had an ordinary answer.")
    world.say(f"By the end, the {mystery.missing} was back where it belonged, and the room felt honest again.")
    world.facts["solved"] = True
    world.facts["ended_near"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    if (setting.id, mystery.id) not in valid_combos():
        raise StoryError("That setting and mystery do not make a reasonable story.")
    world = World(setting)
    world.facts.update(mystery=mystery, response=RESPONSES[params.response],
                       child_name=params.child_name, child_gender=params.child_gender,
                       helper_name=params.helper_name, helper_gender=params.helper_gender)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f'Write a short whodunit for a young child that includes the word "hyacinth" and ends with a clear clue explained.',
        f"Tell a gentle mystery where {world.facts['child_name']} notices that {m.missing} is missing and uses bravery to solve the misunderstanding.",
        f"Write a simple detective story about a missing hyacinth, a mistaken clue, and a calm true answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    child = world.get("child")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"What was missing from {world.setting.place}?",
            answer=f"The missing thing was {m.missing}. The story keeps coming back to that one missing detail until it is found again.",
        ),
        QAItem(
            question=f"Why did {child.label_word} think there was trouble at first?",
            answer=f"{child.label_word} misunderstood the clue and thought someone had taken the hyacinth. The smear of dirt looked suspicious before the real cause was explained.",
        ),
        QAItem(
            question=f"How did {child.label_word} show bravery?",
            answer=f"{child.label_word} showed bravery by asking careful questions instead of guessing. That brave choice let the truth replace the misunderstanding.",
        ),
        QAItem(
            question=f"How did the story end after the answer was found?",
            answer=f"The {m.id} was back where it belonged, and the room felt honest again. The ending image proves the mistake was fixed and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hyacinth?",
            answer="A hyacinth is a flower with a thick, pretty cluster of blossoms. People often keep one in a pot or garden because it smells sweet and looks bright.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the hard or scary thing when it matters. It does not mean pretending not to be afraid; it means moving carefully anyway.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what they saw or heard. Asking questions can clear it up.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", mystery="hyacinth", response="ask", child_name="Mina", child_gender="girl", helper_name="June", helper_gender="girl"),
    StoryParams(setting="greenhouse", mystery="lantern", response="look", child_name="Owen", child_gender="boy", helper_name="Paul", helper_gender="boy"),
    StoryParams(setting="porch", mystery="key", response="call", child_name="Iris", child_gender="girl", helper_name="Sana", helper_gender="girl"),
    StoryParams(setting="shed", mystery="seedbag", response="ask", child_name="Theo", child_gender="boy", helper_name="Marta", helper_gender="girl"),
]


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: {mystery.id} does not fit a reasonable whodunit in {setting.place}.)"


ASP_RULES2 = r"""
valid(S, M) :- setting(S), mystery(M), needs_wind(M), windy(S).
valid(S, M) :- setting(S), mystery(M), needs_porch(M), S = porch.
valid(S, M) :- setting(S), mystery(M), not needs_wind(M), not needs_porch(M).
"""


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py != cl:
        print("MISMATCH: valid_combos differ.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        ok = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    else:
        print("OK: generation smoke test passed.")
    return ok


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid settings/mystery combos:")
        for s, m in asp_valid_combos():
            print(f"  {s} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
