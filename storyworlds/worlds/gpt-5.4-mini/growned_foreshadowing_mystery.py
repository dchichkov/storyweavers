#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py
=================================================================

A standalone tiny storyworld for a child-friendly mystery with foreshadowing.

Premise
-------
A child notices odd little clues around a house or yard, follows them with a
careful helper, and discovers what was really happening. The story always
includes a clear setup, a trail of clues, a reveal that connects earlier hints,
and an ending image that proves the mystery changed something.

This world is intentionally small:
- one child detective
- one helper
- one mystery object or missing thing
- one earlier clue that foreshadows the reveal
- one sensible resolution

The seed word "growned" is treated as a deliberate odd note in the mystery:
the child may see a sign or hear a strange phrase like "growned" before the
reveal explains it in a child-friendly way. The story never uses it as a debug
artifact; it is woven into the mystery as a clue word.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/growned_foreshadowing_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    hidey: str
    backdrop: str

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
class Mystery:
    id: str
    missing: str
    clue1: str
    clue2: str
    clue3: str
    reveal: str
    odd_word: str = "growned"
    tags: set[str] = field(default_factory=set)

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
class Helper:
    id: str
    label: str
    kind: str
    method: str
    calm_phrase: str
    tags: set[str] = field(default_factory=set)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mystery = world.facts["mystery"]
    clue = mystery.clue1
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("foreshadow", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["attention"] += 1
    out.append(clue)
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["attention"] < THRESHOLD:
        return out
    sig = ("reveal", world.facts["mystery"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "story", _r_foreshadow),
    Rule("reveal", "story", _r_reveal),
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


def can_solve(mystery: Mystery, helper: Helper) -> bool:
    return "helpful" in helper.tags and mystery.id in MYSTERIES


def _do_search(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} noticed something strange near {world.facts['setting'].hidey}. "
        f"{world.facts['setting'].backdrop}"
    )
    world.say(
        f"{child.id} and {helper.id} started to look for the missing {mystery.missing}."
    )
    world.para()
    world.say(
        f"The first clue was {mystery.clue2}. It seemed small, but it did not feel accidental."
    )
    world.say(
        f"Then {child.id} saw the odd word {mystery.odd_word} written nearby, and {child.pronoun()} frowned."
    )
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)


def _do_reveal(world: World, child: Entity, helper: Entity, mystery: Mystery, reveal_reason: str) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At last, {child.id} followed the clues back to {reveal_reason}. That was the answer all along."
    )
    world.say(
        f"{mystery.reveal} {helper.id} smiled and {helper.pronoun()} helped put everything right."
    )
    world.say(
        f"By the end, the whole place felt different: the mystery was solved, and the little trail of clues made sense."
    )


def tell(setting: Setting, mystery: Mystery, helper: Helper,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Aunt June", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    htype = "mother" if helper_gender == "woman" else "father"
    if helper_name.lower().startswith("aunt"):
        htype = "woman"
    helper_ent = world.add(Entity(id=helper_name, kind="character", type=htype, role="helper"))
    world.facts["setting"] = setting
    world.facts["mystery"] = mystery
    world.facts["helper"] = helper
    world.facts["child"] = child

    world.say(
        f"{child.id} lived in {setting.place}, where even the {setting.mood} corners seemed to keep secrets."
    )
    world.say(
        f"One morning, {child.id} noticed the missing {mystery.missing} and a tiny clue tucked beside {setting.hidey}."
    )
    world.say(
        f"{helper_ent.id} knelt beside {child.id}. '{helper.calm_phrase}' {helper_ent.pronoun()} said."
    )

    _do_search(world, child, helper_ent, mystery)
    world.para()
    _do_reveal(world, child, helper_ent, mystery, setting.hidey)

    world.facts.update(
        child=child, helper=helper_ent, solved=True,
        ending="solved", odd_word=mystery.odd_word,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "quiet", "the bread box",
                       "Sunlight touched the table, but the pantry stayed shadowy."),
    "attic": Setting("attic", "the attic", "dusty", "the old trunk",
                     "The rafters creaked softly, like the house was whispering."),
    "garden": Setting("garden", "the garden", "still", "the rose bush",
                      "The wind brushed the leaves, and the fence cast long stripes."),
}

MYSTERIES = {
    "spoon": Mystery(
        "spoon", "silver spoon",
        "A tiny bell rang once from the next room.",
        "There was a small line of crumbs leading toward the table.",
        "The word growned was written in shaky letters on a napkin.",
        "The spoon had not vanished at all; it was inside the sugar jar, where the baker had left it after stirring."),
    "key": Mystery(
        "key", "little brass key",
        "A faint clink came from somewhere high up.",
        "A dusty ribbon lay on the floor, pointing to the old shelf.",
        "The word growned was scratched beside the shelf in pencil.",
        "The key was stuck behind a jar, hiding where nobody looked."),
    "toy": Mystery(
        "toy", "blue toy car",
        "A small wheel mark curved under the chair.",
        "A tiny blanket hill looked oddly lumpy.",
        "The word growned was on a note clipped to the laundry basket.",
        "The toy car was under the blanket, waiting like a secret treasure."),
}

HELPERS = {
    "aunt": Helper("aunt", "aunt", "woman", "checked the clues one by one", "Let's follow the clues calmly.", {"helpful", "calm"}),
    "dad": Helper("dad", "dad", "man", "looked under the shelves", "No rush. Mysteries like slow footsteps.", {"helpful", "calm"}),
    "mom": Helper("mom", "mom", "woman", "searched the table first", "We just need to look closely.", {"helpful", "calm"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    helper: str
    child_name: str
    child_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, h) for s in SETTINGS for m in MYSTERIES for h in HELPERS if can_solve(MYSTERIES[m], HELPERS[h])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, mystery, helper = f["setting"], f["mystery"], f["helper"]
    return [
        f'Write a child-friendly mystery story set in {setting.place} that uses the word "{mystery.odd_word}" as an early clue.',
        f"Tell a short mystery where {f['child'].id} searches for a missing {mystery.missing} and a helpful adult keeps the mood calm.",
        f'Write a foreshadowing story: show a tiny clue first, then reveal why {mystery.odd_word} mattered at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    qa = [
        ("What kind of story is this?",
         f"It is a mystery story with clues, a careful search, and a reveal at the end. The clue trail makes the answer feel earned."),
        ("Where does the story happen?",
         f"It happens in {setting.place}, where a quiet hidden spot made the missing thing hard to notice. That setting helped the clues feel secret and important."),
        ("What was missing?",
         f"The missing thing was {mystery.missing}. The whole search was about finding where it had been tucked away."),
        (f"Why did {child.id} notice the word {mystery.odd_word}?",
         f"{child.id} noticed {mystery.odd_word} because it was an odd clue that did not belong. It foreshadowed the answer by pointing toward the place where the missing thing was hidden."),
        (f"How did {helper.id} help?",
         f"{helper.id} stayed calm and helped {child.pronoun('object')} look one clue at a time. That steady method kept the mystery from feeling scary."),
        ("How did the story end?",
         f"It ended with the missing thing found and the mystery solved. The last image proves the answer by showing that the clue trail finally made sense."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery = f["mystery"]
    return [
        ("What is a mystery?",
         "A mystery is a story about something strange or missing, where clues help you figure out the answer."),
        ("What is foreshadowing?",
         "Foreshadowing is when a story gives you a small hint early on about something that will matter later."),
        ("Why are clues useful?",
         "Clues are useful because they help you connect little facts and discover what really happened."),
        ("What does a helper do in a mystery?",
         "A helper looks carefully, stays calm, and helps connect the clues so the answer can be found."),
        ("Why might a story repeat a strange word like growned?",
         f"A strange word like {mystery.odd_word} can stand out and make you pay attention. Later, the story can explain why it mattered."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowed(C, M) :- child(C), mystery(M), clue1(M).
revealed(M) :- mystery(M), clue2(M), clue3(M).
solved(M) :- revealed(M), foreshadowed(_, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    # Add a smoke test using normal generation.
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, helper=None, child_name=None, child_gender=None, seed=None), random.Random(7)))
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    try:
        import asp
        cl = set(asp_valid_combos())
        if cl != py:
            rc = 1
            print("MISMATCH in valid_combos():")
            if cl - py:
                print("  only in clingo:", sorted(cl - py))
            if py - cl:
                print("  only in python:", sorted(py - cl))
        else:
            print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    except Exception as exc:  # noqa: BLE001
        print(f"ASP VERIFY FAILED: {exc}")
        return 1
    return rc


GIRL_NAMES = ["Mia", "Luna", "Nora", "Ada", "Ruby", "Ivy", "Zoe"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Leo", "Noah", "Ezra", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery world with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, mystery, helper, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], HELPERS[params.helper],
                 params.child_name, params.child_gender)
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
    StoryParams("kitchen", "spoon", "aunt", "Milo", "boy"),
    StoryParams("attic", "key", "dad", "Nora", "girl"),
    StoryParams("garden", "toy", "mom", "Theo", "boy"),
]


def valid_sample(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.mystery in MYSTERIES and params.helper in HELPERS


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show foreshadowed/2.\n#show revealed/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show foreshadowed/2.\n#show revealed/1.\n#show solved/1."))
        print("model:")
        print("\n".join(sorted(asp.atoms(model, "foreshadowed") + asp.atoms(model, "revealed") + asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED if valid_sample(p)]
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting} / {p.mystery} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
