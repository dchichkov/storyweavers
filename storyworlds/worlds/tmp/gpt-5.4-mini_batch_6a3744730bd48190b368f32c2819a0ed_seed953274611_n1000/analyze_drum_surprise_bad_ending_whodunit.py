#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/analyze_drum_surprise_bad_ending_whodunit.py
=============================================================================

A tiny whodunit storyworld: a child detective tries to analyze a strange drum
sound, finds a surprise clue, and sometimes the case ends badly when the wrong
suspect gets blamed too soon.

The world is built around a small mystery in a music room. A drum keeps making a
surprising noise, the detective checks evidence, and a reveal either clears the
room or leaves a bad ending where the real cause remains hidden. The prose is
state-driven: clues, suspicion, and emotional shifts are all simulated before
rendering.

This script follows the storyworld contract:
- stdlib-only
- uses storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily only inside ASP helpers
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --trace, --qa, --json, --asp, --verify, --show-asp, -n, --all, --seed
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
SUSPICION_HIGH = 2.0


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
    hidden: bool = False

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
class Setting:
    id: str
    place: str
    room_name: str
    mood: str
    detail: str


@dataclass
class Clue:
    id: str
    label: str
    description: str
    kind: str
    surprise: int = 0
    points_to: str = ""


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    could_do_it: bool = False
    innocent_sign: str = ""


@dataclass
class Cause:
    id: str
    label: str
    sound: str
    hidden: bool = True
    bad_ending: bool = False
    reveal_text: str = ""


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


SETTINGS = {
    "music_room": Setting(
        id="music_room",
        place="the music room",
        room_name="music room",
        mood="quiet",
        detail="A little drum sat by the wall, and the room smelled faintly of dust and wood."
    ),
    "band_room": Setting(
        id="band_room",
        place="the band room",
        room_name="band room",
        mood="busy",
        detail="A drum kit waited in the corner, and shiny stands cast long shadows."
    ),
}

DETECTIVES = {
    "lena": {"name": "Lena", "type": "girl", "traits": ["careful", "curious"]},
    "milo": {"name": "Milo", "type": "boy", "traits": ["bright", "careful"]},
    "ivy": {"name": "Ivy", "type": "girl", "traits": ["observant", "brave"]},
}

DRUMS = {
    "snare": {
        "label": "snare drum",
        "surface": "the snare head",
        "sound": "tap-tap",
        "kind": "drum",
        "detail": "its skin was tight and white",
    },
    "big_drum": {
        "label": "big drum",
        "surface": "the drum skin",
        "sound": "thump-thump",
        "kind": "drum",
        "detail": "its round body looked like a small moon",
    },
}

CAUSES = {
    "mouse": Cause(
        id="mouse",
        label="a mouse under the drum",
        sound="scratch-scratch",
        hidden=True,
        bad_ending=False,
        reveal_text="A tiny mouse had been brushing the floor with its feet."
    ),
    "string": Cause(
        id="string",
        label="a loose string inside the stand",
        sound="tick-tick",
        hidden=True,
        bad_ending=True,
        reveal_text="A loose string in the stand was knocking whenever the drum shook."
    ),
    "wind": Cause(
        id="wind",
        label="a draft from the open door",
        sound="whuff",
        hidden=False,
        bad_ending=False,
        reveal_text="A draft from the open door had been moving the page of clues."
    ),
}

SUSPECTS = {
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        role="helper",
        could_do_it=True,
        innocent_sign="his keys jingled loudly"
    ),
    "music_teacher": Suspect(
        id="music_teacher",
        label="the music teacher",
        role="adult",
        could_do_it=False,
        innocent_sign="her hands were full of lesson cards"
    ),
    "friend": Suspect(
        id="friend",
        label="the friend",
        role="child",
        could_do_it=True,
        innocent_sign="they were holding the detective's notebook"
    ),
}

QUESTIONS = [
    "analyze",
    "drum",
    "surprise",
    "bad ending",
    "whodunit",
]

REASONABLE_COMBOS = [("music_room", "snare", "mouse"), ("music_room", "big_drum", "string"), ("band_room", "snare", "wind")]


@dataclass
class StoryParams:
    setting: str
    drum: str
    cause: str
    detective: str
    suspect: str
    seed: Optional[int] = None
    surprise: bool = True
    bad_ending: bool = False


def _choose_name(rng: random.Random) -> str:
    return rng.choice(sorted(DETECTIVES))


def _choose_suspect(rng: random.Random) -> str:
    return rng.choice(sorted(SUSPECTS))


def valid_combos() -> list[tuple[str, str, str]]:
    return list(REASONABLE_COMBOS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about a drum, clues, and a surprise reveal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drum", choices=DRUMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--surprise", action="store_true", default=True)
    ap.add_argument("--bad-ending", action="store_true")
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


def explain_rejection() -> str:
    return "(No story: that drum-and-cause pair does not support a believable mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drum and args.cause:
        combo = (args.setting or "music_room", args.drum, args.cause)
        if combo not in valid_combos():
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.drum is None or c[1] == args.drum)
              and (args.cause is None or c[2] == args.cause)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, drum, cause = rng.choice(sorted(combos))
    detective = args.detective or _choose_name(rng)
    suspect = args.suspect or _choose_suspect(rng)
    return StoryParams(
        setting=setting,
        drum=drum,
        cause=cause,
        detective=detective,
        suspect=suspect,
        seed=args.seed,
        surprise=args.surprise,
        bad_ending=args.bad_ending or CAUSES[cause].bad_ending,
    )


def _do_examine(world: World, detective: Entity, drum: Entity) -> None:
    detective.memes["focus"] += 1
    world.say(f"{detective.id} leaned in and tried to analyze the drum like a real detective.")
    world.say(f"The {drum.label} made a strange sound: {drum.attrs['sound']}.")
    world.say("That was enough to turn a quiet room into a mystery.")


def _gather_clue(world: World, clue: Clue) -> None:
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="clue", label=clue.label, attrs={"points_to": clue.points_to}))
    clue_ent.meters["noted"] += 1
    world.say(f"The first clue was {clue.description}.")


def _accuse(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["suspicion"] += 1
    suspect.memes["hurt"] += 1
    world.say(f"{detective.id} looked at {suspect.label} and almost said the wrong name.")


def _reveal(world: World, cause: Cause, suspect: Entity, detective: Entity) -> None:
    detective.memes["relief"] += 1
    if cause.bad_ending:
        world.say(f"Then the truth arrived like a surprise: {cause.reveal_text}")
        world.say(f"But it was too late to save the scene, and the ending turned bad before anyone could fix it.")
    else:
        world.say(f"Then the surprise came clear: {cause.reveal_text}")
        world.say(f"{suspect.label} was innocent, and the room finally made sense.")


def _bad_finish(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["regret"] += 1
    suspect.memes["dread"] += 1
    world.say(f"The bad ending left {detective.id} staring at the drum, wishing the case had been solved sooner.")
    world.say("The mystery stayed open, and the room felt colder than before.")


def tell(setting: Setting, drum_cfg: dict, cause: Cause, detective_name: str, suspect_name: str, bad_ending: bool) -> World:
    world = World(setting)
    det_info = DETECTIVES[detective_name]
    detective = world.add(Entity(id=det_info["name"], kind="character", type=det_info["type"], role="detective", traits=det_info["traits"]))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=SUSPECTS[suspect_name].role, role="suspect", label=SUSPECTS[suspect_name].label))
    drum = world.add(Entity(id="drum", kind="thing", type="drum", label=drum_cfg["label"], attrs={"sound": drum_cfg["sound"], "surface": drum_cfg["surface"]}))
    clue = Clue(id="clue1", label="a dusty footprint", description="a dusty footprint by the drum stand", kind="footprint", surprise=1, points_to=cause.id)
    world.facts["cause"] = cause
    world.facts["bad_ending"] = bad_ending

    world.say(f"In {setting.place}, {detective.id} found {drum.label} in a quiet corner.")
    world.say(f"{setting.detail}")
    world.para()
    _do_examine(world, detective, drum)
    _gather_clue(world, clue)
    if setting.id == "music_room":
        world.say(f"A surprise waited under the cloth: {cause.label}.")
    else:
        world.say(f"The room held a surprise, and it pointed toward {cause.label}.")
    world.para()
    _accuse(world, detective, suspect)
    if bad_ending:
        _bad_finish(world, detective, suspect)
    _reveal(world, cause, suspect, detective)
    if not bad_ending:
        world.say("By the end, the drum was just a drum again, and the mystery was neatly put away.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a whodunit for a young child that uses the words analyze and drum, and includes a surprise clue in {world.setting.room_name}.",
        f"Tell a mystery story where a detective tries to analyze a {DRUMS[f['drum'] if 'drum' in f else 'snare']['label']} and learns who made the sound.",
        "Write a short surprise mystery with a bad ending where the wrong suspect is blamed before the real cause is discovered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cause: Cause = world.facts["cause"]
    bad = world.facts["bad_ending"]
    qa = [
        QAItem(question="What was the detective trying to do?", answer="The detective was trying to analyze the drum and figure out why it made such a strange sound. The whole story turns on careful looking and listening."),
        QAItem(question="What surprise did the detective find?", answer=f"The surprise was that {cause.label} was behind the noise. That clue changed the case from a simple guess into a real whodunit."),
    ]
    if bad:
        qa.append(QAItem(question="How did the story end?", answer="It ended badly, because the wrong idea came first and the truth arrived too late. The mystery was not neatly solved in time, so the ending felt sad and unfinished."))
    else:
        qa.append(QAItem(question="How did the story end?", answer="It ended with the drum mystery solved and the room making sense again. The detective could stop worrying once the surprise clue was understood."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to analyze something?", answer="To analyze something means to look at it carefully and think about its parts so you can understand it better."),
        QAItem(question="What is a drum?", answer="A drum is a musical instrument you tap or hit to make a sound."),
        QAItem(question="What is a whodunit?", answer="A whodunit is a mystery story where the reader tries to figure out who caused the problem."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="music_room", drum="snare", cause="mouse", detective="lena", suspect="janitor", bad_ending=False),
    StoryParams(setting="music_room", drum="big_drum", cause="string", detective="milo", suspect="friend", bad_ending=True),
    StoryParams(setting="band_room", drum="snare", cause="wind", detective="ivy", suspect="music_teacher", bad_ending=False),
]


ASP_RULES = r"""
valid(S,D,C) :- setting(S), drum(D), cause(C), compatible(S,D,C).
bad(C) :- cause(C), bad_ending(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DRUMS:
        lines.append(asp.fact("drum", did))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.bad_ending:
            lines.append(asp.fact("bad_ending", cid))
    for s, d, c in valid_combos():
        lines.append(asp.fact("compatible", s, d, c))
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
        rc = 1
        print("MISMATCH in ASP validity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, drum=None, cause=None, detective=None, suspect=None, surprise=True, bad_ending=False, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False, n=1), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return list(REASONABLE_COMBOS)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.drum not in DRUMS or params.cause not in CAUSES or params.detective not in DETECTIVES or params.suspect not in SUSPECTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], DRUMS[params.drum], CAUSES[params.cause], params.detective, params.suspect, params.bad_ending)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mysteries:")
        for s, d, c in asp_valid_combos():
            print(f"  {s:10} {d:8} {c}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
