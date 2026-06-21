#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/piggy_knuckle_weak_misunderstanding_flashback_curiosity_folk.py
=================================================================================================

A standalone storyworld for a folk-tale style misunderstanding about a small
piggy, a sore knuckle, and a weak-looking thing that turns out not to be what it
seems. The world is built around a tiny simulated scene: curiosity leads a child
(or a piglet) to poke, a misunderstanding makes trouble, a flashback explains
the fear, and a gentle helper resolves the knot.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    plural: bool = False
    weak: bool = False
    fragile: bool = False
    makes_noise: bool = False
    warms: bool = False

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


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
    piggy: str
    weak: str
    misunderstanding: str
    flashback: str
    curiosity: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    opening: str
    dark_spot: str
    helper_reason: str


@dataclass
class Piggy:
    id: str
    label: str
    phrase: str
    sound: str
    kind: str = "piglet"


@dataclass
class WeakThing:
    id: str
    label: str
    phrase: str
    appears: str
    true_use: str
    weak_on_purpose: bool = True


@dataclass
class Misunderstanding:
    id: str
    suspicion: str
    wrong_guess: str
    fear_word: str
    turn: str


@dataclass
class Flashback:
    id: str
    memory: str
    old_truth: str
    tells: str


@dataclass
class Curiosity:
    id: str
    question: str
    action: str
    clue: str


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "barn": Setting(
        id="barn",
        place="the old red barn",
        mood="folk",
        opening="At the edge of the meadow stood an old red barn where the wind sang through the boards.",
        dark_spot="the hay loft",
        helper_reason="the barn held dry hay, an old rope, and shadows that made children curious",
    ),
    "cottage": Setting(
        id="cottage",
        place="the warm cottage",
        mood="folk",
        opening="By the river stood a warm cottage with a little hearth and a crooked stair.",
        dark_spot="the cellar door",
        helper_reason="the cottage had a cellar where jars clinked and little footsteps echoed",
    ),
    "orchard": Setting(
        id="orchard",
        place="the apple orchard",
        mood="folk",
        opening="Beyond the lane lay an apple orchard where the branches whispered above the grass.",
        dark_spot="the root hollow",
        helper_reason="the orchard hid a root hollow where old things could be found",
    ),
}

PIGGIES = {
    "piglet": Piggy("piglet", "piggy", "a little piggy", "oink"),
    "lantern": Piggy("lantern-piggy", "lantern", "a little lantern piggy", "oink"),
}

WEAKS = {
    "straw": WeakThing("straw", "straw ladder", "a weak straw ladder", "leaned in the dark", "was only for reaching apples"),
    "twig": WeakThing("twig", "twig bridge", "a weak twig bridge", "creaked by the creek", "was only for crossing a puddle"),
    "string": WeakThing("string", "string whistle", "a weak string whistle", "hung from a nail", "was only for tying bundles"),
}

MISUNDERSTANDINGS = {
    "knuckle": Misunderstanding(
        "knuckle",
        suspicion="a bump on the knuckle looked like a bite mark",
        wrong_guess="someone had bitten the child",
        fear_word="trouble",
        turn="the child had only bumped a knuckle on the door latch",
    ),
    "weak": Misunderstanding(
        "weak",
        suspicion="the weak-looking thing seemed ready to snap like a bad sign",
        wrong_guess="the old place was about to fall",
        fear_word="worry",
        turn="the thing was weak-looking only because it was made for a small job",
    ),
}

FLASHBACKS = {
    "lesson": Flashback(
        "lesson",
        memory="the child remembered a winter day when a cracked bucket spilled water all over the floor",
        old_truth="then the elder had said that old things can look mean until you know their purpose",
        tells="that memory made the child slow down and look again",
    ),
    "bridge": Flashback(
        "bridge",
        memory="the child remembered crossing a tiny plank at the stream with careful steps",
        old_truth="then the helper had said that weak-looking things can still help if you use them the right way",
        tells="that memory gave the child courage to ask instead of guess",
    ),
}

CURIOSITIES = {
    "peek": Curiosity(
        "peek",
        question="what was behind the hay loft door?",
        action="peeked behind the door",
        clue="a soft green glimmer came from inside",
    ),
    "touch": Curiosity(
        "touch",
        question="what did the weak-looking thing do if someone touched it?",
        action="reached out to touch it",
        clue="it answered with a tiny creak, not a crack",
    ),
}

GIRL_NAMES = ["Mira", "Lily", "Nora", "Pip", "Mabel", "Elsie"]
BOY_NAMES = ["Finn", "Robin", "Theo", "Jasper", "Bram", "Will"]
ELDER_NAMES = ["Gran", "Old Ben", "Aunt Sila", "Uncle Reed"]

TRAITS = ["curious", "gentle", "careful", "brave", "thoughtful", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, w) for s in SETTINGS for p in PIGGIES for w in WEAKS]


def explain_rejection(setting: str, piggy: str, weak: str) -> str:
    return f"(No story: {setting}, {piggy}, and {weak} do not form a valid folk-tale seed.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about piggy, knuckle, weak, curiosity, flashback, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--piggy", choices=PIGGIES)
    ap.add_argument("--weak", choices=WEAKS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and (args.setting, args.piggy or "piglet", args.weak or "straw") not in combos:
        pass
    setting = args.setting or rng.choice(sorted(SETTINGS))
    piggy = args.piggy or rng.choice(sorted(PIGGIES))
    weak = args.weak or rng.choice(sorted(WEAKS))
    misunderstanding = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    flashback = args.flashback or rng.choice(sorted(FLASHBACKS))
    curiosity = args.curiosity or rng.choice(sorted(CURIOSITIES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        setting=setting,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        elder_gender=elder_gender,
        piggy=piggy,
        weak=weak,
        misunderstanding=misunderstanding,
        flashback=flashback,
        curiosity=curiosity,
    )


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.piggy not in PIGGIES or params.weak not in WEAKS:
        raise StoryError("Invalid params for this folk-tale world.")
    world = World()
    setting = SETTINGS[params.setting]
    piggy = PIGGIES[params.piggy]
    weak = WEAKS[params.weak]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    flashback = FLASHBACKS[params.flashback]
    curiosity = CURIOSITIES[params.curiosity]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=["curious", "young"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["kind", "patient"]))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder", traits=["wise"]))
    pig = world.add(Entity(id="piggy", kind="thing", type="piggy", label=piggy.label, plural=False, weak=False))
    weak_ent = world.add(Entity(id="weak", kind="thing", type="thing", label=weak.label, weak=True, fragile=True))
    child.meters["curiosity"] += 1
    child.memes["unease"] += 1

    world.say(setting.opening)
    world.say(f"There lived {params.child}, who loved to ask questions, and {params.helper}, who knew the lanes and fields.")
    world.say(f"One morning, {params.child} saw {piggy.phrase} near {setting.dark_spot} and heard {piggy.sound} in the hush.")

    world.para()
    world.say(f"{params.child} noticed {misunderstanding.suspicion}.")
    world.say(f'"That means {misunderstanding.wrong_guess}," {params.child} thought, and {params.child} felt a knot of {misunderstanding.fear_word}.')
    child.memes["fear"] += 1
    world.say(f"But {curiosity.question if params.curiosity else 'the question would not leave the child alone'}")
    child.memes["curiosity"] += 1

    world.para()
    world.say(f"{params.child} {curiosity.action if params.curiosity else 'leaned closer'} and saw {weak.phrase} by the doorway.")
    world.say(f"It looked weak, but it did not fall. It only gave a tiny answer: {weak.phrase} {weak.appears}.")
    child.meters["touches"] += 1
    if params.misunderstanding == "weak":
        child.memes["doubt"] += 1
    world.say(f"Then {flashback.memory}. {flashback.old_truth}. {flashback.tells}.")
    child.memes["memory"] += 1

    world.para()
    world.say(f"{params.helper} came near and listened to the whole tale.")
    world.say(f'"No harm is meant here," {params.helper} said. "{piggy.phrase} is only a {piggy.kind}, and {weak.phrase} was made to {weak.true_use}."')
    world.say(f"At last {params.elder} added, " f'"A thing can look weak and still be useful. A guess can look sharp and still be wrong."')
    child.memes["relief"] += 1
    helper.memes["love"] += 1
    elder.memes["wisdom"] += 1
    child.meters["curiosity"] += 1

    world.para()
    world.say(f"So {params.child} laughed softly, because the scare had been only a misunderstanding.")
    world.say(f"{params.child} knelt beside {piggy.phrase}, touched the {weak.label}, and asked one better question after another.")
    world.say(f"By sunset, the three of them were walking home together, and {piggy.phrase} was safe, the knuckle was forgotten, and the weak-looking thing had told its true story.")

    world.facts.update(
        setting=setting,
        piggy=piggy,
        weak=weak,
        misunderstanding=misunderstanding,
        flashback=flashback,
        curiosity=curiosity,
        child=child,
        helper=helper,
        elder=elder,
        outcome="resolved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale for a 3-to-5-year-old that includes the words "{f["piggy"].label}", "knuckle", and "weak".',
        f"Tell a gentle story where {f['child'].id} first misunderstands what {f['piggy'].phrase} means, then remembers something from the past and asks a better question.",
        f"Write a story with curiosity, a flashback, and a misunderstanding in a cozy folk-tale setting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    elder = f["elder"]
    piggy = f["piggy"]
    weak = f["weak"]
    mis = f["misunderstanding"]
    flash = f["flashback"]
    cur = f["curiosity"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who got curious, and the {piggy.label} in the old folk-tale place. {helper.id} and {elder.id} help turn the worry into understanding."),
        ("Why did the child get worried?",
         f"{child.id} saw what looked like {mis.suspicion}. That made {child.id} guess {mis.wrong_guess}, even though the guess was not right."),
        ("What helped the child understand better?",
         f"A flashback helped. {flash.memory}, and then {flash.old_truth}, so {child.id} slowed down and looked again."),
        ("What did curiosity do in the story?",
         f"Curiosity pushed {child.id} to ask {cur.question} and to {cur.action}. Because {child.id} kept asking, the mistake could be fixed before it grew larger."),
        ("How did the story end?",
         f"It ended gently: {child.id} learned that a thing can look weak and still be useful, and the {piggy.label} stayed safe. The whole scene changed from worry to calm understanding."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a knuckle?",
         "A knuckle is the part of your finger that bends when you make a fist. It can get bumped if you knock your hand on something hard."),
        ("What does weak mean?",
         "Weak means not strong. Something weak may bend, break, or wobble more easily than something sturdy."),
        ("What is curiosity?",
         "Curiosity is the wish to know more. It makes you ask questions, peek around corners, and look again before deciding."),
        ("What is a flashback in a story?",
         "A flashback is a part of the story that remembers something from before. It helps explain why someone feels scared, careful, or brave now."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks the wrong thing about a person or event. Asking a better question can clear it up."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.weak:
            bits.append("weak=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,W) :- setting(S), piggy(P), weak(W).
curious_turn(C) :- curiosity(C).
misunderstood(M) :- misunderstanding(M).
flashback(F) :- flashback(F).
story_ready(S,P,W) :- valid(S,P,W), curious_turn(_), misunderstood(_), flashback(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PIGGIES:
        lines.append(asp.fact("piggy", p))
    for w in WEAKS:
        lines.append(asp.fact("weak", w))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for f in FLASHBACKS:
        lines.append(asp.fact("flashback", f))
    for c in CURIOSITIES:
        lines.append(asp.fact("curiosity", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def resolve_params_checked(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.piggy and args.weak:
        if (args.setting, args.piggy, args.weak) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.piggy, args.weak))
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show story_ready/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, piggy, weak) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(
                setting="barn", child="Mira", child_gender="girl", helper="Old Ben", helper_gender="boy",
                elder="Gran", elder_gender="girl", piggy="piglet", weak="straw", misunderstanding="knuckle",
                flashback="lesson", curiosity="peek", seed=1,
            )),
            generate(StoryParams(
                setting="cottage", child="Finn", child_gender="boy", helper="Aunt Sila", helper_gender="girl",
                elder="Gran", elder_gender="girl", piggy="lantern", weak="twig", misunderstanding="weak",
                flashback="bridge", curiosity="touch", seed=2,
            )),
            generate(StoryParams(
                setting="orchard", child="Nora", child_gender="girl", helper="Will", helper_gender="boy",
                elder="Uncle Reed", elder_gender="boy", piggy="piglet", weak="string", misunderstanding="knuckle",
                flashback="bridge", curiosity="peek", seed=3,
            )),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params_checked(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
