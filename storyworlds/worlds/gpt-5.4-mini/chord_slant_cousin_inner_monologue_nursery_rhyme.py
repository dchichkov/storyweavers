#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chord_slant_cousin_inner_monologue_nursery_rhyme.py
===================================================================================

A tiny standalone storyworld for a nursery-rhyme style tale with an inner
monologue beat.  The domain is small and classical: two children share a little
music corner, a tilted object creates a small problem, a cousin notices the
risk, and the ending proves the turn by changing what they do next.

The seed words are present in the world model:
- chord
- slant
- cousin

Style goal:
- Nursery-rhyme cadence
- Child-facing concrete prose
- Clear premise, tension, turn, resolution
- Inner monologue shown as a brief thought beat, not as meta-commentary
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
    room: str
    rhyme_open: str
    rhyme_close: str
    quiet_need: str


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    can_startle: bool = False
    made_of: str = "strings"
    tags: set[str] = field(default_factory=set)


@dataclass
class TiltedThing:
    id: str
    label: str
    phrase: str
    slant: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["worry"] >= THRESHOLD:
            sig = ("worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def safe_to_play(setting: Setting, tilted: TiltedThing) -> bool:
    return setting.id in {"nursery", "music_room"} and tilted.id in {"picture_frame", "toy_lamp"}


def would_spook(instr: Instrument, tilted: TiltedThing, quiet: bool) -> bool:
    return instr.can_startle and not quiet and tilted.id == "sleeping_baby_mobile"


def stop_and_listen(world: World, child: Entity, cousin: Entity, instrument: Instrument, tilted: TiltedThing) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} held the little {instrument.label} and thought, '
        f'"If I play too loud, the room may shake."'
    )
    world.say(
        f'{cousin.id} pointed at the {tilted.label}. "{tilted.risk.capitalize()}," '
        f'{cousin.id} said, soft as rain.'
    )


def play_softly(world: World, child: Entity, cousin: Entity, instrument: Instrument) -> None:
    child.memes["calm"] += 1
    cousin.memes["joy"] += 1
    world.say(
        f'Then {child.id} breathed in and whispered to {self_name(child)}: '
        f'"A small chord can be sweet as honey."'
    )
    world.say(
        f'{child.id} brushed a gentle chord, and the {instrument.label} sang '
        f'{instrument.sound}.'
    )


def self_name(ent: Entity) -> str:
    return ent.id


def fix_slant(world: World, cousin: Entity, tilted: TiltedThing) -> None:
    world.say(
        f'{cousin.id} slid the {tilted.label} straight and made the slant go away.'
    )
    world.get("tilt").meters["slant"] = 0.0


def ending(world: World, child: Entity, cousin: Entity, instrument: Instrument, setting: Setting) -> None:
    world.say(
        f'And the room grew still and bright, as a nursery should be at night. '
        f'{child.id} and {cousin.id} smiled at the song they had made. '
        f'The little chord was safe, the slant was gone, and {setting.rhyme_close}'
    )


def tell(setting: Setting, instrument: Instrument, tilted: TiltedThing,
         child_name: str = "Mina", child_gender: str = "girl",
         cousin_name: str = "Pip", cousin_gender: str = "boy",
         quiet: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    cousin = world.add(Entity(id=cousin_name, kind="character", type=cousin_gender, role="cousin"))
    world.add(Entity(id="room", type="room", label=setting.room))
    world.add(Entity(id="tilt", type="thing", label=tilted.label))
    child.memes["hope"] += 1
    cousin.memes["care"] += 1
    world.say(setting.rhyme_open)
    world.say(
        f'In the {setting.room}, {child.id} and {cousin.id} found {instrument.phrase}, '
        f'and the {tilted.label} with its {tilted.slant}.'
    )
    world.say(
        f'{child.id} wanted a chord for the corner, but the corner was asking for quiet.'
    )
    world.para()
    stop_and_listen(world, child, cousin, instrument, tilted)
    if would_spook(instrument, tilted, quiet):
        child.memes["worry"] += 1
    world.para()
    play_softly(world, child, cousin, instrument)
    fix_slant(world, cousin, tilted)
    ending(world, child, cousin, instrument, setting)
    world.facts.update(
        child=child, cousin=cousin, setting=setting, instrument=instrument, tilted=tilted,
        quiet=quiet, soft_play=True, slant_fixed=True
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "nursery", "Hush-a-bye, the room was dim and kind,", "Lullaby-lights, and happy hearts behind.", "keep the room as soft as a lullaby"),
    "music_room": Setting("music_room", "music room", "Sing-a-song, with windows wide and free,", "Tap-tap-tap, and smiling as can be.", "let the music stay gentle"),
}

INSTRUMENTS = {
    "ukulele": Instrument("ukulele", "ukulele", "a tiny ukulele", "tinkly twinkle", tags={"chord", "music"}),
    "guitar": Instrument("guitar", "guitar", "a small guitar", "soft plink-plunk", tags={"chord", "music"}),
    "harp": Instrument("harp", "harp", "a little harp", "silvery ring", tags={"chord", "music"}),
}

TILTED = {
    "picture_frame": TiltedThing("picture_frame", "picture frame", "a picture frame", "a slant on the wall", "It might tumble if the music got bouncy", tags={"slant"}),
    "toy_lamp": TiltedThing("toy_lamp", "toy lamp", "a toy lamp", "a slant on the shelf", "It might wobble if the table shook", tags={"slant"}),
    "sleeping_baby_mobile": TiltedThing("sleeping_baby_mobile", "mobile", "a baby mobile", "a careful slant over the crib", "It could stir the sleeping baby", tags={"slant"}),
}

RESPONSES = {
    "soften": Response("soften", 3, 3, "lowered the hands and played the chord softly", "played the chord softly", tags={"music"}),
    "straighten": Response("straighten", 3, 2, "straightened the slant and then played on", "straightened the slant and then played on", tags={"slant"}),
}

CURATED = [
    ("nursery", "ukulele", "picture_frame", "Mina", "girl", "Pip", "boy", True),
    ("music_room", "harp", "toy_lamp", "Lena", "girl", "Noah", "boy", True),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for iid, inst in INSTRUMENTS.items():
            if "chord" not in inst.tags:
                continue
            for tid, t in TILTED.items():
                if safe_to_play(s, t):
                    combos.append((sid, iid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    instrument: str
    tilted: str
    child_name: str
    child_gender: str
    cousin_name: str
    cousin_gender: str
    quiet: bool = True
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world with a cousin, a chord, and a slant.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--tilted", choices=TILTED)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--cousin-name")
    ap.add_argument("--cousin-gender", choices=["girl", "boy"])
    ap.add_argument("--quiet", action="store_true", default=False)
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
              and (args.instrument is None or c[1] == args.instrument)
              and (args.tilted is None or c[2] == args.tilted)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, instrument, tilted = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    cousin_gender = args.cousin_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(["Mina", "Lila", "Tess", "Milo", "Nico"])
    cousin_name = args.cousin_name or rng.choice(["Pip", "June", "Rory", "Nell", "Ari"])
    if child_name == cousin_name:
        cousin_name = cousin_name + "y"
    return StoryParams(setting, instrument, tilted, child_name, child_gender, cousin_name, cousin_gender, quiet=not args.quiet)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "chord", "slant", and "cousin".',
        f"Tell a gentle story where {f['child'].id} and {f['cousin'].id} share music, notice a slant, and keep the song soft.",
        f"Write a short story with an inner monologue beat in which a child thinks about a chord before choosing the kinder, quieter choice.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    cousin = f["cousin"]
    tilted = f["tilted"]
    instrument = f["instrument"]
    setting = f["setting"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {cousin.id}, two children in the {setting.room}."),
        ("What did {0} think about before playing?".format(child.id), f"{child.id} thought about making a chord, but also about keeping the room calm and safe."),
        ("What problem did the cousin notice?", f"{cousin.id} noticed the {tilted.label} and its slant, and worried it could wobble or fall."),
        ("How did they solve it?", f"They played the {instrument.label} softly and {cousin.id} straightened the slant, so the room felt peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chord?", "A chord is when several musical notes sound together at the same time."),
        ("What does slant mean?", "A slant means something is tilted instead of standing straight."),
        ("What is a cousin?", "A cousin is a family member who is the child of your aunt or uncle."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I,T) :- setting(S), instrument(I), tilted(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("chord_word", iid))
    for tid in TILTED:
        lines.append(asp.fact("tilted", tid))
        lines.append(asp.fact("slant_word", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        print("MISMATCH: ASP does not match valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], INSTRUMENTS[params.instrument], TILTED[params.tilted],
        params.child_name, params.child_gender, params.cousin_name, params.cousin_gender, params.quiet
    )
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
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, "Mina", "girl", "Pip", "boy", True)) for c in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
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
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
