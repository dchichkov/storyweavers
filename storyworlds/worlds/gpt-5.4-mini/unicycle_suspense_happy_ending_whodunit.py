#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/unicycle_suspense_happy_ending_whodunit.py
===========================================================================

A standalone story world for a small whodunit-style children's mystery:
a beloved unicycle seems to be missing, suspense builds through clues,
and the ending is happy when the mystery is solved without blame.

The domain is intentionally tiny and classical:
- one child performer
- one helper adult
- one missing object: a unicycle
- a few plausible hiding places
- a simple chain of clues and a reveal

The world state drives the prose:
- physical meters track whether the unicycle is hidden, found, or in use
- emotional memes track worry, curiosity, relief, and joy
- rules fire forward to produce suspense and resolution

The story remains child-facing, concrete, and complete: setup, clues,
a tense middle, a reveal, and a happy ending image.
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
SUSPENSE_MIN = 1.0
CURIOUS_MIN = 1.0


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
    mood: str
    hiding_spots: list[str]
    clue_text: str
    ending_image: str

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
    text: str
    points_to: str
    suspense: float = 1.0

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
        return clone

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["worry"] < CURIOUS_MIN:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "unicycle" in world.entities:
        world.get("unicycle").meters["missing"] = 1.0
    child.memes["suspense"] += 1
    out.append("__suspense__")
    return out


def _r_clue_chain(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_index", 0) >= len(world.facts.get("clues", [])):
        return out
    idx = world.facts.get("clue_index", 0)
    clue = world.facts["clues"][idx]
    sig = ("clue", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["clue_index"] = idx + 1
    world.facts["last_clue"] = clue.id
    out.append("__clue__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("found") and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] = 0.0
                e.memes["relief"] += 1
                e.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("suspense", "social", _r_suspense),
    Rule("clue_chain", "narrative", _r_clue_chain),
    Rule("relief", "social", _r_relief),
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


def is_plausible_hide(setting: Setting, place: str) -> bool:
    return place in setting.hiding_spots


def _do_search(world: World, clue: Clue, narrate: bool = True) -> None:
    child = world.get("child")
    child.memes["curious"] += 1
    world.say(clue.text)
    propagate(world, narrate=narrate)


def _find_unicycle(world: World, place: str) -> None:
    uni = world.get("unicycle")
    uni.meters["hidden"] = 0.0
    uni.meters["found"] = 1.0
    world.facts["found"] = True
    world.facts["found_place"] = place
    world.say(f"At last, there it was: the unicycle was {place}, just where the clues had led.")


def tell(setting: Setting, child_name: str, child_gender: str, helper_name: str,
         helper_gender: str, place: str, clues: list[Clue], final_reveal: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="detective"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    uni = world.add(Entity(id="unicycle", kind="thing", type="vehicle", label="unicycle"))
    uni.meters["hidden"] = 1.0
    child.memes["worry"] = 1.0
    child.memes["curious"] = 1.0
    world.facts.update(setting=setting, child=child, helper=helper, unicycle=uni, clues=clues,
                       clue_index=0, place=place, final_reveal=final_reveal, found=False,
                       hidden_place=place)

    world.say(
        f"On a quiet afternoon, {child_name} came to {setting.place} and stopped short. "
        f"Their unicycle was gone."
    )
    world.say(
        f"{child_name} looked under the little chairs, behind the curtain, and beside the door, "
        f"but the room only answered with silence."
    )
    world.say(
        f"{helper_name} noticed the worried face and said, "
        f'"Let’s follow the clues one by one."'
    )

    world.para()
    for clue in clues:
        _do_search(world, clue, narrate=True)
        if clue.points_to == place:
            break
        world.say("That clue helped, but not enough yet. The mystery was still not solved.")
        world.para()

    world.para()
    world.say(final_reveal)
    _find_unicycle(world, place)

    world.para()
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{child_name} laughed with relief and climbed onto the unicycle again. "
        f"{setting.ending_image}"
    )
    world.say(
        f"This time, the wheels rolled straight and true, and the little detective smiled at the happy ending."
    )
    return world


SETTINGS = {
    "garage": Setting(
        id="garage",
        place="the garage",
        mood="echoey",
        hiding_spots=["behind the old bike", "under a tarp", "next to the toolbox"],
        clue_text="A dusty wheel mark led toward the back wall.",
        ending_image="The garage lights glowed on the shiny wheel, and everything felt safe again.",
    ),
    "yard": Setting(
        id="yard",
        place="the yard",
        mood="windy",
        hiding_spots=["behind the shed", "under the bench", "beside the watering can"],
        clue_text="A thin trail in the dirt pointed toward the shed.",
        ending_image="The yard looked bright in the sun, and the unicycle stood ready for another ride.",
    ),
    "hall": Setting(
        id="hall",
        place="the hall",
        mood="quiet",
        hiding_spots=["behind the coat rack", "near the umbrella stand", "under the blanket pile"],
        clue_text="A small wobble mark on the floor pointed down the hall.",
        ending_image="The hallway felt cozy again, with the unicycle parked by the wall like a friend returned home.",
    ),
}

CLUES = {
    "garage": [
        Clue("dust", "A dusty line on the floor made the child look toward the back wall.", "behind the old bike"),
        Clue("rattle", "Then came a tiny rattle from under a tarp.", "under a tarp"),
    ],
    "yard": [
        Clue("print", "A little wheel print in the dirt pointed toward the shed.", "behind the shed"),
        Clue("shine", "A flash of metal peeped out from the shadow near the bench.", "under the bench"),
    ],
    "hall": [
        Clue("mark", "A faint wheel mark on the floor led toward the coat rack.", "behind the coat rack"),
        Clue("soft", "A soft bump came from the blanket pile near the wall.", "under the blanket pile"),
    ],
}

REVEALS = {
    "garage": "The clues had led them to the old bike corner, where the unicycle was tucked away safely after the last ride.",
    "yard": "The clues pointed to the shed, where someone had parked the unicycle out of the way so it would not tip over.",
    "hall": "The clues ended at the blanket pile, where the unicycle had been set down carefully and forgotten for a while.",
}

NAMES_GIRL = ["Maya", "Lily", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Noah", "Eli", "Ben", "Theo", "Max"]
HELPERS_GIRL = ["Mom", "Aunt June", "Ms. Lee"]
HELPERS_BOY = ["Dad", "Uncle Ray", "Mr. Cole"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    hidden_place: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        for place in setting.hiding_spots:
            combos.append((sid, place))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    place = f["hidden_place"]
    child: Entity = f["child"]
    return [
        f'Write a whodunit-style story for a young child about a missing unicycle in {setting.place}. Include the word "unicycle".',
        f"Tell a suspenseful but happy story where {child.label} searches for a unicycle and the clues lead to {place}.",
        f"Write a small mystery with clues, suspense, and a happy ending: someone cannot find the unicycle at first, but it is recovered safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    place = f["hidden_place"]
    qa: list[tuple[str, str]] = [
        ("What went missing?",
         "The unicycle went missing, so the child had to search for it like a little detective."),
        ("Where did the mystery take place?",
         f"It took place in {setting.place}, which felt {setting.mood} and full of hiding spots."),
        (f"Who helped {child.label}?",
         f"{helper.label} helped by following the clues calmly and making the search feel less scary."),
        ("Why was the story suspenseful?",
         f"Because nobody knew where the unicycle was at first, and each clue had to be checked before the answer appeared."),
    ]
    if f.get("found"):
        qa.append((
            "How was the mystery solved?",
            f"The clues led to {place}, and there the unicycle was found safely. That ended the suspense and turned the search into relief."
        ))
    qa.append((
        "How did the story end?",
        "It ended happily, with the unicycle found and the child smiling again. The ending showed that the mystery was solved without anyone getting hurt."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a unicycle?",
         "A unicycle is a one-wheeled bike that a rider balances and pedals with careful practice."),
        ("Why is finding a lost thing sometimes a mystery?",
         "Because you have to look for clues, check possible hiding places, and figure out where it could be."),
        ("What helps solve a whodunit story?",
         "Careful noticing helps solve it. The characters use clues instead of guessing wildly."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(unicycle) :- unicycle(U), hidden(U).
suspense :- missing(unicycle), worry(child).
clue_used(C) :- clue(C), points_to(C, P), hidden_place(P).
found(U) :- unicycle(U), clue_used(C), points_to(C, P), hidden_place(P).
happy_end :- found(unicycle).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for spot in setting.hiding_spots:
            lines.append(asp.fact("hiding_spot", sid, spot))
    lines.append(asp.fact("unicycle", "unicycle"))
    lines.append(asp.fact("hidden", "unicycle"))
    lines.append(asp.fact("worry", "child"))
    for sid, clues in CLUES.items():
        for clue in clues:
            lines.append(asp.fact("clue", clue.id))
            lines.append(asp.fact("points_to", clue.id, clue.points_to))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = 0
    # Gate parity
    python_set = set(valid_combos())
    asp_set = set()
    # compute from inline facts via a tiny rule
    model = asp.one_model(asp_program("valid(S,P) :- setting(S), hiding_spot(S,P).", "#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    if python_set != asp_set:
        print("MISMATCH: valid_combos() differs from ASP")
        print(" python only:", sorted(python_set - asp_set))
        print(" asp only:", sorted(asp_set - python_set))
        ok = 1
    else:
        print(f"OK: valid_combos() parity ({len(python_set)} combos).")

    # smoke test generate / render
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, name=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = 1
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about a missing unicycle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hidden-place")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.hidden_place and args.setting:
        if not is_plausible_hide(SETTINGS[args.setting], args.hidden_place):
            raise StoryError("That hiding place does not fit the chosen setting.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hidden_place = args.hidden_place or rng.choice(SETTINGS[setting].hiding_spots)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" else "boy")
    helper_name = args.helper_name or rng.choice(HELPERS_GIRL if helper_gender == "girl" else HELPERS_BOY)
    if child_name == helper_name:
        helper_name = (HELPERS_GIRL if helper_gender == "girl" else HELPERS_BOY)[0]
    return StoryParams(setting, child_name, child_gender, helper_name, helper_gender, hidden_place)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="detective"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    uni = world.add(Entity(id="unicycle", kind="thing", type="vehicle", label="unicycle"))
    clue_list = CLUES[params.setting]
    final_reveal = REVEALS[params.setting]
    world = tell(setting, params.child_name, params.child_gender, params.helper_name,
                 params.helper_gender, params.hidden_place, clue_list, final_reveal)
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


CURATED = [
    StoryParams("garage", "Maya", "girl", "Dad", "boy", "behind the old bike"),
    StoryParams("yard", "Noah", "boy", "Mom", "girl", "under the bench"),
    StoryParams("hall", "Lily", "girl", "Uncle Ray", "boy", "behind the coat rack"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible hidden places:")
        for sid, place in valid_combos():
            print(f"  {sid:7} {place}")
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            header = f"### {sample.params.child_name}: unicycle mystery in {sample.params.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
