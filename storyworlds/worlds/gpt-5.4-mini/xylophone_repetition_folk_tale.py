#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/xylophone_repetition_folk_tale.py
=================================================================

A standalone story world for a tiny folk-tale pattern: a child or small troupe
wants to make music with a xylophone, a repeated search or helping task goes
wrong, a wise helper notices the pattern, and the ending turns into a warm,
repeated refrain that proves the change.

Domain seed: xylophone
Style: folk tale
Feature: repetition

The world is intentionally small: one instrument, a few characters, one missing
or muffled piece, and a repeated sequence of tries that gives the tale its folk
rhythm.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"missing": 0.0, "noise": 0.0, "joy": 0.0, "hope": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "calm": 0.0, "delight": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    name: str
    place: str
    mood: str
    repeated_phrase: str


@dataclass
class Instrument:
    id: str
    label: str
    sound: str
    missing_piece: str
    found_piece: str
    has_missing: bool = True


@dataclass
class Helper:
    id: str
    label: str
    role_name: str
    method: str
    gift: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _check_reasonable(setting: Setting, instrument: Instrument, helper: Helper) -> None:
    if not instrument.has_missing:
        raise StoryError("No story: the xylophone has no missing piece, so there is no problem to repeat and resolve.")
    if setting.id == "silent_hill" and helper.id == "mouse":
        raise StoryError("No story: the mouse cannot carry the helper gift over Silent Hill in this tiny tale.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in INSTRUMENTS:
            for hid in HELPERS:
                setting = SETTINGS[sid]
                instrument = INSTRUMENTS[iid]
                helper = HELPERS[hid]
                try:
                    _check_reasonable(setting, instrument, helper)
                except StoryError:
                    continue
                combos.append((sid, iid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    instrument: str
    helper: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: xylophone, repetition, and a folk-tale ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.instrument and args.helper:
        _check_reasonable(SETTINGS[args.setting], INSTRUMENTS[args.instrument], HELPERS[args.helper])
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, iid, hid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or ("girl" if gender == "boy" else "boy")
    name = args.name or _pick_name(rng, gender)
    elder = args.elder or _pick_name(rng, elder_gender, avoid=name)
    return StoryParams(sid, iid, hid, name, gender, elder, elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child that includes the word "xylophone" and a repeating pattern of trying, listening, and trying again.',
        f"Tell a warm village story where {f['child'].id} wants to play the xylophone, something is missing, and {f['elder'].id} helps after a repeated search.",
        f"Write a simple story in a folk-tale style that repeats a phrase three times and ends with music returning to the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    inst = f["instrument"]
    helper = f["helper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who lives near the old lane, and {elder.id}, who knows how to solve small village troubles."),
        ("What did the child want to do?",
         f"{child.id} wanted to play the {inst.label} and make the village hear its bright sound again."),
        ("What was wrong at first?",
         f"The {inst.label} was missing its {inst.missing_piece}, so when {child.id} tried to play it, the song came out thin and sad."),
        ("How did the elder help?",
         f"{elder.id} used {helper.method} and found the {inst.found_piece}. After that, the {inst.label} could sing properly again."),
        ("How did the story end?",
         f"It ended with music and relief. The village heard the {inst.label} sounding bright, and the child smiled as the repeated trouble was finally fixed."),
    ]
    if f.get("repetition"):
        qa.append((
            "Why is the story repeated three times?",
            f"Because this is a folk tale, the same try and the same answer come again and again. The repeating pattern makes the change feel stronger when the missing piece is finally found."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    inst = f["instrument"]
    helper = f["helper"]
    return [
        ("What is a xylophone?",
         "A xylophone is a musical instrument with bars that make bright notes when you strike them."),
        ("What does a mallet do?",
         "A mallet is a soft stick used to tap an instrument gently so it can make sound without being hurt."),
        ("Why can a missing piece matter on an instrument?",
         "If an instrument is missing a piece, it may sound wrong or not work well until the piece is put back."),
        ("What does a helper do in a folk tale?",
         "A helper notices the problem, finds a clever way to fix it, and helps the characters end with joy."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(setting: Setting, instrument: Instrument, helper: Helper, child_name: str, child_gender: str,
         elder_name: str, elder_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["curious"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder", traits=["wise"]))
    inst = world.add(Entity(id="xylophone", type="instrument", label=instrument.label))
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["instrument"] = instrument
    world.facts["helper"] = helper
    child.memes["hope"] += 1
    child.memes["worry"] += 1
    world.say(f"Once in {setting.place}, {child.id} found the old {instrument.label} waiting in the light. {setting.mood}.")
    world.say(f'{child.id} tapped it once, then twice, then once more, but the tune sounded wrong and the bars answered with a thin little note.')
    world.para()
    world.say(f'"Maybe the missing {instrument.missing_piece} is somewhere near the well," said {child.id}. "Maybe," said {elder.id}, and the two of them went to look.')
    world.say(f'They looked under the bench, then beside the gate, then behind the blue jar, and each time they came back with empty hands.')
    world.para()
    world.say(f"At last {elder.id} smiled and used {helper.method}; there, tucked away where the dust liked to sleep, was {instrument.found_piece}.")
    world.say(f"{child.id} fitted it back where it belonged, and the {instrument.label} gave out {instrument.sound} as bright as morning bells.")
    world.say(f'Then the village heard the tune three times over: "Tap, sing, and listen," "Tap, sing, and listen," "Tap, sing, and listen."')
    world.say(f"{child.id} laughed, {elder.id} laughed, and the little road seemed to dance with them.")
    world.facts["repetition"] = True
    return world


SETTINGS = {
    "green_hill": Setting("green_hill", "Green Hill", "the green hill", "The grass was soft, and the wind told old stories.", "listen, look, and listen again"),
    "silver_lane": Setting("silver_lane", "Silver Lane", "the silver lane", "The lane was quiet, and every window kept a secret glow.", "tap, pause, and tap again"),
    "fox_village": Setting("fox_village", "Fox Village", "Fox Village", "The cottages leaned together like friends.", "walk, ask, and walk on"),
}

INSTRUMENTS = {
    "xylophone": Instrument("xylophone", "xylophone", "plink-plonk music", "little wooden key", "lost wooden key"),
    "bright_xylophone": Instrument("bright_xylophone", "bright xylophone", "bright plink-plonk music", "soft cloth cover", "soft cloth cover"),
    "river_xylophone": Instrument("river_xylophone", "river xylophone", "water-clear notes", "highest bar", "highest bar"),
}

HELPERS = {
    "grandmother": Helper("grandmother", "grandmother", "grandmother", "a careful search with a candle and a basket", "a warm shawl"),
    "fox": Helper("fox", "fox", "fox", "a trail of paw prints", "a red ribbon"),
    "mouse": Helper("mouse", "mouse", "mouse", "tiny nibbling clues", "a crumb trail"),
}

GIRL_NAMES = ["Mina", "Lila", "Suri", "Nora", "Anya", "Tessa"]
BOY_NAMES = ["Pip", "Milo", "Jasper", "Oren", "Tobin", "Leif"]


def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams("green_hill", "xylophone", "grandmother", "Mina", "girl", "Oren", "boy"),
    StoryParams("silver_lane", "bright_xylophone", "fox", "Pip", "boy", "Lila", "girl"),
    StoryParams("fox_village", "river_xylophone", "mouse", "Suri", "girl", "Tobin", "boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("missing_piece", iid, inst.missing_piece))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, H) :- setting(S), instrument(I), helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        assert sample.prompts
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    try:
        _ = format_qa(sample)
        print("OK: QA formatting passed.")
    except Exception as exc:
        print(f"QA FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], INSTRUMENTS[params.instrument], HELPERS[params.helper],
                 params.child_name, params.child_gender, params.elder_name, params.elder_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story shapes.")
        for sid, iid, hid in asp_valid_combos():
            print(f"  {sid:12} {iid:18} {hid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
