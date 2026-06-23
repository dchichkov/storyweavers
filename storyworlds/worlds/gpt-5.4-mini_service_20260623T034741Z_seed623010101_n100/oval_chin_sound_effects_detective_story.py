#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/oval_chin_sound_effects_detective_story.py
======================================================================================================================

A tiny detective-story world where clues are physical objects with meters and
memes, the case moves through sound effects, and the required words "oval" and
"chin" appear as part of the simulated evidence.

Seed tale idea:
---
A child detective hears strange sound effects in a quiet neighborhood. A shiny
oval clue is found on a bench, then a small mark on a chin and a trail of taps
lead the detective to the real problem: a wind-up music box is stuck inside a
mailbox. The detective follows the sounds, solves the case, and the neighborhood
grows calm again.

The world is deliberately small:
- one detective,
- one helper,
- one problem object,
- one suspect or false lead,
- one or more sound-effect driven clues.

The story is built from world state, not from a frozen paragraph.
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
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    title: str
    clue_word: str
    sound_word: str
    source_word: str
    fix_word: str
    clue_type: str
    source_type: str
    helper_action: str
    resolution_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    suspect_name: str
    suspect_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


def _r_sound_trail(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    problem = world.get("problem")
    if detective.meters.get("listening", 0) < THRESHOLD:
        return out
    if problem.meters.get("stuck", 0) < THRESHOLD:
        return out
    sig = ("trail",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["noticed"] = detective.meters.get("noticed", 0) + 1
    problem.meters["heard"] = problem.meters.get("heard", 0) + 1
    out.append("The sound kept pointing the detective toward the source.")
    return out


def _r_freedom(world: World) -> list[str]:
    out: list[str] = []
    problem = world.get("problem")
    if problem.meters.get("fixed", 0) < THRESHOLD:
        return out
    sig = ("freedom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["relief"] = world.get("helper").memes.get("relief", 0) + 1
    out.append("The neighborhood got quiet again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_sound_trail, _r_freedom):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if place_id in case.tags:
                combos.append((place_id, case_id))
    return combos


def choose_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def tell(place: Place, case: Case, params: StoryParams) -> World:
    world = World(place)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_gender,
        label=params.detective_name,
        role="detective",
        attrs={"place": place.id},
        meters={"listening": 0.0, "noticed": 0.0, "calm": 0.0},
        memes={"curiosity": 1.0, "satisfaction": 0.0},
        tags={"detective"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_gender,
        label=params.helper_name,
        role="helper",
        attrs={"place": place.id},
        meters={"helping": 0.0},
        memes={"trust": 1.0},
        tags={"helper"},
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="character",
        type=params.suspect_gender,
        label=params.suspect_name,
        role="suspect",
        attrs={"place": place.id},
        meters={"nervous": 0.0},
        memes={"worry": 0.0},
        tags={"suspect"},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type=case.clue_type,
        label=case.clue_word,
        phrase=f"a {case.clue_word} clue",
        meters={"seen": 0.0},
        tags={"clue", case.clue_word},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type=case.source_type,
        label=case.source_word,
        phrase=f"a {case.source_word}",
        meters={"stuck": 1.0, "fixed": 0.0, "bothering": 1.0},
        memes={"noise": 1.0},
        tags={"problem", case.source_word},
    ))
    world.facts.update(case=case, detective=detective, helper=helper, suspect=suspect, clue=clue, problem=problem)

    world.say(f"On a quiet evening, {detective.label} was the neighborhood detective in {place.label}.")
    world.say(f"{helper.label} came along, and {suspect.label} waited nearby, looking uneasy.")
    world.say(f"Then a strange sound went {case.sound_word} from somewhere close by.")
    world.say(f"Under a bench, {detective.label} spotted {case.clue_word} and tucked the clue into the casebook.")
    detective.meters["listening"] = 1.0
    clue.meters["seen"] = 1.0
    suspect.meters["nervous"] = 1.0
    helper.meters["helping"] = 1.0
    world.say(f"{detective.label} lowered {detective.pronoun('possessive')} chin and listened harder.")
    world.para()
    world.say(f"The sound went {case.sound_word} again, this time by the mailbox.")
    world.say(f"{helper.label} pointed at the corner and said, '{case.sound_word}! It is coming from there.'")
    detective.meters["noticed"] = detective.meters.get("noticed", 0.0) + 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(f"At last, {detective.label} opened the mailbox and found {case.fix_word} {case.helper_action}.")
    problem.meters["fixed"] = 1.0
    problem.meters["stuck"] = 0.0
    detective.meters["calm"] = 1.0
    detective.memes["satisfaction"] = 1.0
    helper.memes["trust"] = 2.0
    world.say(f"With one careful move, the detective solved the case: {case.resolution_image}.")
    propagate(world, narrate=False)
    world.para()
    world.say(f"{detective.label} smiled, {helper.label} laughed, and {suspect.label} finally stopped worrying.")
    world.say(f"The little mystery was over, and the quiet neighborhood felt safe again.")

    world.facts["place"] = place
    world.facts["params"] = params
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    place = world.facts["place"]
    det = world.facts["detective"]
    return [
        f'Write a short detective story for a young child set in {place.label} that includes the words "{case.clue_word}" and "{case.source_word}".',
        f"Tell a simple mystery where {det.label} follows {case.sound_word} sounds and finds the clue {case.clue_word}.",
        f'Write a child-friendly detective story with sound effects and an ending where the case is solved in {place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    det = world.facts["detective"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    problem = world.facts["problem"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who solved the mystery in {place.label}?",
            answer=f"{det.label} solved the mystery by following the sound and paying attention to the clue {case.clue_word}. {helper.label} helped, and that made the answer easier to find.",
        ),
        QAItem(
            question=f"What sound kept leading {det.label} toward the answer?",
            answer=f"The sound went {case.sound_word} and pointed {det.label} toward the source. It mattered because the noise came from {problem.label}, not from the first place the detective looked.",
        ),
        QAItem(
            question=f"What did {det.label} do with the clue {case.clue_word}?",
            answer=f"{det.label} picked up the {case.clue_word} and used it to follow the trail. After that, the detective found {case.fix_word} and solved the case.",
        ),
        QAItem(
            question=f"How did {suspect.label} feel at the end?",
            answer=f"{suspect.label} stopped worrying when the case was solved. The room grew calm again, so the nervous feeling could fade away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    out = []
    if "oval" in case.tags:
        out.append(QAItem(
            question="What is an oval?",
            answer="An oval is a rounded shape, like an egg or a smooth little ring. It has no sharp corners.",
        ))
    if "chin" in case.tags:
        out.append(QAItem(
            question="Where is your chin?",
            answer="Your chin is the small part at the bottom of your face. It sits below your mouth.",
        ))
    if "sound" in case.tags:
        out.append(QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that helps you hear the action in your head, like bang, tap, or click. It makes a story feel lively.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "lantern_lane": Place(id="lantern_lane", label="Lantern Lane", tags={"sound", "oval", "chin"}),
    "station_square": Place(id="station_square", label="Station Square", tags={"sound", "oval", "chin"}),
    "harbor_walk": Place(id="harbor_walk", label="Harbor Walk", tags={"sound", "oval", "chin"}),
}

CASES = {
    "music_box": Case(
        id="music_box",
        title="The Case of the Stuck Music Box",
        clue_word="oval",
        sound_word="tap-tap",
        source_word="music box",
        fix_word="a tiny key",
        clue_type="oval",
        source_type="music_box",
        helper_action="wedged inside the mailbox",
        resolution_image="the music box clicked free and played a soft tune",
        tags={"oval", "sound", "chin"},
    ),
    "bicycle_bell": Case(
        id="bicycle_bell",
        title="The Case of the Missing Bell",
        clue_word="oval",
        sound_word="ding-ding",
        source_word="bicycle bell",
        fix_word="a loose spring",
        clue_type="oval",
        source_type="bell",
        helper_action="caught under the bench slats",
        resolution_image="the bell rang bright and clear again",
        tags={"oval", "sound", "chin"},
    ),
    "toy_train": Case(
        id="toy_train",
        title="The Case of the Lost Train",
        clue_word="oval",
        sound_word="chug-chug",
        source_word="toy train",
        fix_word="a bent track",
        clue_type="oval",
        source_type="train",
        helper_action="stuck behind the mailbox door",
        resolution_image="the train rolled along with a cheerful puff",
        tags={"oval", "sound", "chin"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Eli", "Jack"]


def valid_story_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for c in CASES:
            combos.append((p, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a child detective, sound effects, oval clues, and a chin lowered in concentration.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_story_combos()
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case = rng.choice(sorted(combos))
    dg = rng.choice(["girl", "boy"])
    hg = rng.choice(["girl", "boy"])
    sg = rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        case=case,
        detective_name=choose_name(rng, dg),
        detective_gender=dg,
        helper_name=choose_name(rng, hg),
        helper_gender=hg,
        suspect_name=choose_name(rng, sg),
        suspect_gender=sg,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.case not in CASES:
        raise StoryError("Unknown case.")
    world = tell(PLACES[params.place], CASES[params.case], params)
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for t in sorted(PLACES[p].tags):
            lines.append(asp.fact("tagged", p, t))
    for c in CASES.values():
        lines.append(asp.fact("case", c.id))
        lines.append(asp.fact("clue_word", c.id, c.clue_word))
        lines.append(asp.fact("sound_word", c.id, c.sound_word))
        lines.append(asp.fact("source_word", c.id, c.source_word))
        for t in sorted(c.tags):
            lines.append(asp.fact("case_tag", c.id, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C) :- place(P), case(C), case_tag(C, oval), case_tag(C, sound).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import storyworlds.asp as asp  # lazy, as required
    if set(asp_valid_combos()) != set(valid_story_combos()):
        print("MISMATCH between ASP and Python combo checks.")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True)
    if not buf.getvalue().strip():
        print("Smoke test failed: emit produced no output.")
        return 1
    print(f"OK: verify passed ({len(asp_valid_combos())} combos) and smoke test succeeded.")
    return 0


CURATED = [
    StoryParams(
        place="lantern_lane",
        case="music_box",
        detective_name="Mia",
        detective_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        suspect_name="Nora",
        suspect_gender="girl",
    ),
    StoryParams(
        place="station_square",
        case="bicycle_bell",
        detective_name="Finn",
        detective_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        suspect_name="Max",
        suspect_gender="boy",
    ),
    StoryParams(
        place="harbor_walk",
        case="toy_train",
        detective_name="Lily",
        detective_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        suspect_name="Ella",
        suspect_gender="girl",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for p, c in asp_valid_combos():
            print(f"  {p} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
