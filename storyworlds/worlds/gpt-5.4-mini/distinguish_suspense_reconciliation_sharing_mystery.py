#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distinguish_suspense_reconciliation_sharing_mystery.py
======================================================================================

A standalone story world for a small mystery about distinguishing clues,
suspense, reconciliation, and sharing.

The premise: a child suspects a missing shared item is lost, then notices clues,
distinguishes the real cause, makes peace with a friend, and shares the final
find.

This script follows the storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- world model with meters and memes
- reasonableness gate and inline ASP twin
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    dark_place: str
    shared_place: str
    clues: list[str]
    atmosphere: str

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    owner: str
    hidden_in: str
    distinguishable_clue: str
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
class ConflictCfg:
    id: str
    suspicion_line: str
    suspense_line: str
    reveal_line: str
    reconciliation_line: str
    share_line: str
    can_share: bool = True
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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
    out = []
    if world.facts.get("suspense", 0.0) >= SUSPENSE_MIN and ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        for c in world.characters():
            c.memes["unease"] += 1
        out.append("__suspense__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    if world.facts.get("reconciled") and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        for c in world.characters():
            c.memes["warmth"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def search_world(world: World, seeker: Entity, item: ObjectCfg, friend: Entity, conflict: ConflictCfg) -> None:
    seeker.memes["worry"] += 1
    world.say(
        f"On a quiet evening in {world.setting.place}, {seeker.id} noticed that {item.phrase} was missing. "
        f"{conflict.suspense_line}"
    )
    world.say(
        f'{seeker.id} and {friend.id} looked in {world.setting.dark_place}, where the shadows made every small sound feel important.'
    )


def distinguish_clue(world: World, seeker: Entity, item: ObjectCfg, friend: Entity) -> None:
    seeker.memes["focus"] += 1
    world.facts["suspense"] = 1.0
    world.say(
        f'Then {seeker.id} saw a clue: {item.distinguishable_clue}. That helped {seeker.id} distinguish the real answer from a scary guess.'
    )


def reveal(world: World, seeker: Entity, friend: Entity, item: ObjectCfg, conflict: ConflictCfg) -> None:
    world.say(conflict.reveal_line.format(item=item.label))
    seeker.meters["certainty"] += 1
    friend.memes["relief"] += 1


def reconcile(world: World, seeker: Entity, friend: Entity) -> None:
    seeker.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.facts["reconciled"] = True
    world.say(
        f"{seeker.id} looked at {friend.id} and said sorry for jumping to conclusions. {friend.id} smiled back, and the two friends felt better at once."
    )


def share(world: World, seeker: Entity, friend: Entity, item: ObjectCfg, conflict: ConflictCfg) -> None:
    if not conflict.can_share:
        return
    seeker.meters["sharing"] += 1
    friend.meters["sharing"] += 1
    world.say(
        f"Then they shared the good news: {item.label} had not been stolen at all, and they could both enjoy it together."
    )
    world.say(
        f"{conflict.share_line.format(item=item.label)}"
    )


SETTINGS = {
    "library": Setting("library", "the library", "the back stacks", "the reading nook",
                       ["a bookmark", "a sticky note", "a dropped ribbon"], "soft and hushed"),
    "garden": Setting("garden", "the garden", "the shed corner", "the bench",
                      ["a petal trail", "a muddy print", "a broken twig"], "still and leafy"),
    "attic": Setting("attic", "the attic", "the old trunk", "the small table",
                     ["a dust line", "a loose button", "a bright thread"], "quiet and creaky"),
}

OBJECTS = {
    "book": ObjectCfg("book", "storybook", "a storybook with a blue cover", "friend", "the bench", "a blue ribbon tucked in the pages", {"book", "shared"}),
    "lantern": ObjectCfg("lantern", "lantern", "a little lantern", "mom", "the shelf", "a bit of wax on the handle", {"light", "shared"}),
    "shells": ObjectCfg("shells", "shells", "a little tin of shells", "friend", "the reading nook", "sand near the lid", {"shells", "shared"}),
}

CONFLICTS = {
    "missing": ConflictCfg(
        "missing",
        "The missing thing made the room feel secret and uneasy.",
        "Every clue seemed to whisper a different answer, which made the wait feel long.",
        "But the truth was kinder than the worry: {item} had simply been put down in the wrong place.",
        "The two friends laughed softly, then promised to ask before guessing next time.",
        "After that, they shared {item} and the mystery became a happy story to tell.",
        True,
        {"mystery", "sharing", "reconciliation", "distinguish"},
    ),
    "misplaced": ConflictCfg(
        "misplaced",
        "A little mistake was hiding somewhere, and that made the search feel suspenseful.",
        "They followed the clues one by one, trying not to worry too soon.",
        "Then they found the answer: {item} had been moved during cleanup and was waiting in the open.",
        "The apology came first, and the smile came right after it.",
        "At the end, they shared {item} and put it back where everyone could find it.",
        True,
        {"mystery", "sharing", "reconciliation", "distinguish"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Sam", "Max", "Eli", "Theo"]
TRAITS = ["careful", "curious", "kind", "thoughtful", "brave"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    conflict: str
    seeker: str
    seeker_gender: str
    friend: str
    friend_gender: str
    trait: str
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
    return [(s, o, c) for s in SETTINGS for o in OBJECTS for c in CONFLICTS]


def explain_rejection() -> str:
    return "(No story: this mystery domain only uses supported settings, objects, and a gentle suspense/reconciliation pattern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about distinguishing clues, suspense, reconciliation, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
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
    combos = valid_combos()
    choice = rng.choice(combos)
    setting = args.setting or choice[0]
    obj = args.object_ or choice[1]
    conflict = args.conflict or choice[2]
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if seeker_gender == "girl" else "girl")
    seeker = args.seeker or rng.choice(GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != seeker]
    friend = args.friend or rng.choice(friend_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, obj, conflict, seeker, seeker_gender, friend, friend_gender, trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    seeker = world.add(Entity(params.seeker, kind="character", type=params.seeker_gender, role="seeker", traits=[params.trait]))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend_gender, role="friend", traits=["kind"]))
    item = OBJECTS[params.object]
    conflict = CONFLICTS[params.conflict]
    world.facts.update(seeker=seeker, friend=friend, item=item, conflict=conflict)

    world.say(
        f"{seeker.id} was a {params.trait} child who loved quiet mysteries. One evening, {seeker.id} and {friend.id} went to {world.setting.place} to look for {item.phrase}."
    )
    world.say(
        f"The place felt {world.setting.atmosphere}, and the missing thing made everyone slow down and listen."
    )
    world.para()
    search_world(world, seeker, item, friend, conflict)
    distinguish_clue(world, seeker, item, friend)
    reveal(world, seeker, friend, item, conflict)
    reconcile(world, seeker, friend)
    share(world, seeker, friend, item, conflict)
    world.para()
    world.say(
        f"In the end, the clue made sense, the worry went quiet, and {item.label} shone like a solved secret."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "distinguish" and ends with sharing {f["item"].label}.',
        f"Tell a suspenseful story set in {world.setting.place} where {f['seeker'].id} and {f['friend'].id} follow clues, then reconcile and share what they find.",
        f"Write a gentle mystery where a worried child learns to distinguish a real clue from a scary guess, then makes up with a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    seeker = f["seeker"]
    friend = f["friend"]
    conflict = f["conflict"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a mystery story with suspense, because the missing {item.label} makes everyone wonder what happened. It also ends with reconciliation and sharing, so the scary feeling turns kind and warm."
        ),
        QAItem(
            question=f"How did {seeker.id} distinguish the answer?",
            answer=f"{seeker.id} noticed the clue {item.distinguishable_clue} and used it to tell the true answer from the scary guess. That mattered because in a mystery, one good clue can make the whole problem clearer."
        ),
        QAItem(
            question=f"What happened after {seeker.id} and {friend.id} stopped arguing?",
            answer=f"They apologized, smiled, and shared {item.label} together. The reconciliation made the ending peaceful instead of tense."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps you solve a puzzle or mystery. It can be a mark, a sound, a trail, or something out of place."
        ),
        QAItem(
            question="What does distinguish mean?",
            answer="Distinguish means to tell one thing from another by noticing how they are different. It helps you choose the true answer instead of a guess."
        ),
        QAItem(
            question="Why do people share things?",
            answer="People share things so everyone can enjoy them and nobody feels left out. Sharing can also help friends feel closer after a misunderstanding."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "book", "missing", "Mia", "girl", "Leo", "boy", "curious"),
    StoryParams("garden", "shells", "misplaced", "Noah", "boy", "Ava", "girl", "careful"),
    StoryParams("attic", "lantern", "missing", "Lily", "girl", "Finn", "boy", "thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
valid(S,O,C) :- setting(S), object(O), conflict(C).
suspense(S,O) :- valid(S,O,_).
reconcile(S,O) :- valid(S,O,_).
sharing(S,O) :- valid(S,O,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, o, c in combos:
            print(f"  {s:8} {o:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
