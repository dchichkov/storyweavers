#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10/mound_crinkle_mystery_to_solve_mystery.py
==============================================================================================================

A small mystery storyworld: a child hears a crinkle near a mound, follows clues,
asks a grown-up, and the mystery is solved safely.

The story leans on a simple premise:
- a mound in a garden or yard
- a crinkle sound from something hidden
- a cautious search
- a calm helper
- a reveal that changes the final image

It is designed as a standalone storyworld script for the Storyweavers repo.
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
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_results_import() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists():
            sys.path.insert(0, str(parent))
            return
        if (parent / "storyworlds" / "results.py").exists():
            sys.path.insert(0, str(parent / "storyworlds"))
            return


_bootstrap_results_import()
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2

KIND_CHILD = "child"
KIND_ADULT = "adult"
KIND_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str = KIND_OBJECT
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    hidden: bool = False
    openable: bool = False
    crumbly: bool = False
    soft: bool = False

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
class PlaceCfg:
    id: str
    scene: str
    mound: str
    cover: str
    sound_place: str
    ending_image: str


@dataclass
class MysteryCfg:
    id: str
    hint: str
    suspect: str
    reveal: str
    safe_method: str
    method_text: str
    clue_word: str


@dataclass
class HelperCfg:
    id: str
    label: str
    role: str
    method: str
    calm_text: str
    solve_text: str
    knows: set[str] = field(default_factory=set)


@dataclass
class ResultCfg:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tremble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["disturbed"] < THRESHOLD:
            continue
        sig = ("tremble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["curiosity"] += 1
        out.append("")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    mound = world.entities.get("mound")
    clue = world.entities.get("clue")
    if not child or not mound or not clue:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("discover",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    mound.meters["touched"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("tremble", _r_tremble), Rule("discover", _r_discover)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for helper in HELPERS:
                if mystery in REASONABLE_MYSTERIES and helper in REASONABLE_HELPERS:
                    combos.append((place, mystery, helper))
    return combos


def mystery_safe(mystery: MysteryCfg) -> bool:
    return mystery.id in REASONABLE_MYSTERIES


def helper_sensible(helper: HelperCfg) -> bool:
    return helper.id in REASONABLE_HELPERS


def outcome_of(params: "StoryParams") -> str:
    if params.mystery == "noise_box":
        return "solved"
    if params.mystery == "lost_note":
        return "solved"
    return "solved"


def _build_story(world: World, child: Entity, adult: Entity, place: PlaceCfg,
                 mystery: MysteryCfg, helper: HelperCfg) -> None:
    child.memes["curiosity"] = 2.0
    child.memes["worry"] = 1.0
    adult.memes["calm"] = 2.0

    world.say(
        f"{child.id} was playing at {place.scene}. Near {place.mound}, a little {mystery.clue_word} of sound went crinkle."
    )
    world.say(
        f"{child.id} froze and looked again. The {place.mound} seemed to hide something, and {mystery.hint} made the mystery feel bigger."
    )
    world.para()

    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} knelt by the mound and listened. The crinkle came again, soft and sneaky, from somewhere under the cover."
    )
    world.say(
        f'"What is hiding there?" {child.id} whispered. {child.id} did not dig fast; {child.id} called for {adult.label_word} instead.'
    )
    world.para()

    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over with a smile and {helper.calm_text}."
    )
    world.say(
        f'"Let us solve it gently," {adult.label_word} said. {helper.method} and then {helper.solve_text}.'
    )
    child.memes["trust"] += 1

    clue = world.get("clue")
    clue.hidden = False
    clue.meters["revealed"] = 1.0
    world.get("mound").meters["disturbed"] += 1
    world.para()

    world.say(
        f"Together they lifted the cover just enough to see the answer: {mystery.reveal}."
    )
    world.say(
        f"The crinkle was not a monster at all. It was only {mystery.suspect}, safe and ordinary, waiting under the mound."
    )
    world.say(
        f"By the end, {place.ending_image}."
    )

    world.facts.update(
        child=child.id,
        adult=adult.id,
        place=place.id,
        mystery=mystery.id,
        helper=helper.id,
        clue_word=mystery.clue_word,
        reveal=mystery.reveal,
        solved=True,
        crinkle=True,
        mound=place.mound,
        cover=place.cover,
        method=helper.method,
    )


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


PLACES = {
    "garden": PlaceCfg(
        id="garden",
        scene="the garden path",
        mound="the little dirt mound",
        cover="a leaf pile",
        sound_place="under the leaves",
        ending_image="the leaf pile was open and the garden looked calm again",
    ),
    "yard": PlaceCfg(
        id="yard",
        scene="the backyard",
        mound="the soft mound by the fence",
        cover="a blanket of grass clippings",
        sound_place="under the grass clippings",
        ending_image="the mound was smaller and the yard felt tidy and bright",
    ),
    "shed": PlaceCfg(
        id="shed",
        scene="the shed door",
        mound="the tiny mound of old boxes",
        cover="a stack of ruffled paper",
        sound_place="inside the paper",
        ending_image="the boxes were neatly sorted and the shed was no longer mysterious",
    ),
}

MYSTERIES = {
    "noise_box": MysteryCfg(
        id="noise_box",
        hint="something round and tiny kept tapping inside",
        suspect="a toy box that had swallowed a metal ball",
        reveal="a marble rolling inside a tin box",
        safe_method="peek with a lantern",
        method_text="They used a lantern to look under the cover",
        clue_word="crinkle",
    ),
    "lost_note": MysteryCfg(
        id="lost_note",
        hint="the sound was soft, like paper folding itself",
        suspect="a folded note trapped under the cover",
        reveal="a note that had blown into the mound and made a crinkle",
        safe_method="lift the cover slowly",
        method_text="They lifted the cover slowly",
        clue_word="crinkle",
    ),
    "seed_packet": MysteryCfg(
        id="seed_packet",
        hint="the mound smelled like wet earth and garden paths",
        suspect="a seed packet with a shiny wrapper",
        reveal="a packet of flower seeds that crinkled when touched",
        safe_method="careful hands and a little brush",
        method_text="They brushed the dirt aside with careful hands",
        clue_word="crinkle",
    ),
}

HELPERS = {
    "mom": HelperCfg(
        id="mom",
        label="mom",
        role="helper",
        method="mom lifted the cover slowly",
        calm_text="she looked close without hurrying",
        solve_text="the hiding place opened up and showed the answer",
        knows={"crinkle", "garden"},
    ),
    "dad": HelperCfg(
        id="dad",
        label="dad",
        role="helper",
        method="dad used a little stick to nudge the cover",
        calm_text="he listened before he touched anything",
        solve_text="the hidden thing popped into view",
        knows={"crinkle", "yard"},
    ),
    "grandma": HelperCfg(
        id="grandma",
        label="grandma",
        role="helper",
        method="grandma brushed the top of the mound with a soft hand",
        calm_text="she liked to solve little puzzles slowly",
        solve_text="the answer was clear at last",
        knows={"crinkle", "shed"},
    ),
}

REASONABLE_MYSTERIES = {"noise_box", "lost_note", "seed_packet"}
REASONABLE_HELPERS = {"mom", "dad", "grandma"}

CHILD_NAMES = ["Lily", "Mia", "Tom", "Nora", "Ben", "Ava", "Leo", "Zoe"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a mound and a crinkle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother"])
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
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, helper = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_gender = "girl" if helper == "mom" else "boy"
    adult_name = args.adult or HELPERS[helper].label
    return StoryParams(
        place=place,
        mystery=mystery,
        helper=helper,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]
    world = World()
    child = world.add(Entity(id=params.child_name, kind=KIND_CHILD, type=params.child_gender, role="child"))
    adult = world.add(Entity(id=helper.label, kind=KIND_ADULT, type=params.adult_gender, role="adult", label=helper.label))
    mound = world.add(Entity(id="mound", kind=KIND_OBJECT, type="thing", label=place.mound, hidden=True, soft=True, crumbly=True))
    clue = world.add(Entity(id="clue", kind=KIND_OBJECT, type="thing", label=mystery.reveal, hidden=True, openable=True))
    _build_story(world, child, adult, place, mystery, helper)
    prompts = generation_prompts(world)
    story_qa = story_qa_items(world)
    world_qa = world_knowledge_qa(world)
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "{f["mound"]}" and "crinkle".',
        f"Tell a calm mystery where {f['child']} hears a crinkle near a mound and asks {f['adult']} for help.",
        f"Write a gentle solve-the-mystery story with a hidden clue, a mound, and a safe reveal.",
    ]


def story_qa_items(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['child']} hear near the mound?",
            answer=f"{f['child']} heard a crinkle near the mound. That sound made the child curious, so {f['child']} looked more closely and called for help.",
        ),
        QAItem(
            question=f"Who helped solve the mystery for {f['child']}?",
            answer=f"{f['adult']} helped solve it. The grown-up used a calm method instead of rushing in, and that made the hidden thing safe to see.",
        ),
        QAItem(
            question="What was hiding under the mound?",
            answer=f"It was {f['reveal']}. The crinkle came from something ordinary, so the mystery ended with a small, clear answer.",
        ),
        QAItem(
            question=f"How did the story end around the {f['mound']}?",
            answer=f"The mound was opened carefully, and the answer was found without any trouble. By the end, the place looked calm and tidy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mound?",
            answer="A mound is a little hill or pile. It can be made of dirt, leaves, sand, or other things that have been gathered together.",
        ),
        QAItem(
            question="What does crinkle mean?",
            answer="Crinkle is a soft wrinkly sound. Paper, wrappers, and leaves can crinkle when they move.",
        ),
        QAItem(
            question="Why is it smart to ask a grown-up about a mystery?",
            answer="A grown-up can help look carefully and keep things safe. That way, you can solve the mystery without making a mess or getting hurt.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden")
        if e.openable:
            bits.append("openable")
        if e.crumbly:
            bits.append("crumbly")
        if e.soft:
            bits.append("soft")
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,H) :- place(P), mystery(M), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, cfg in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        if cfg.id in REASONABLE_MYSTERIES:
            lines.append(asp.fact("reasonable", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        if h in REASONABLE_HELPERS:
            lines.append(asp.fact("sensible", h))
    return "\n".join(lines)


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
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, helper=None, name=None, gender=None, adult=None), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verify passed.")
    return rc


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
    StoryParams(place="garden", mystery="noise_box", helper="mom", child_name="Lily", child_gender="girl", adult_name="mom", adult_gender="girl"),
    StoryParams(place="yard", mystery="lost_note", helper="dad", child_name="Tom", child_gender="boy", adult_name="dad", adult_gender="boy"),
    StoryParams(place="shed", mystery="seed_packet", helper="grandma", child_name="Nora", child_gender="girl", adult_name="grandma", adult_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
