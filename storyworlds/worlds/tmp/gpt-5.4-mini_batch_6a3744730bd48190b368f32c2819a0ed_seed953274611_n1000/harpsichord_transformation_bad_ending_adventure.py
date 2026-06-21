#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/harpsichord_transformation_bad_ending_adventure.py
===================================================================================

A small standalone storyworld about a child adventurer, a mysterious
harpsichord, a transformation spell, and a bad ending that follows when the
wrong key is pressed.

The domain is intentionally tiny:
- a child explores an old hall
- a harpsichord promises music and a secret door
- a glowing key causes a transformation
- the adventure ends badly when the transformed child cannot safely continue

The world is state-driven: physical meters track what changed in the room and on
the character, while emotional memes track fear, wonder, and confusion.
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
SCARED_MIN = 1.0
TRANSFORM_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    dark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    lure: str
    hidden: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    label: str
    trigger: str
    effect: str
    bad_effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Escape:
    id: str
    label: str
    phrase: str
    power: int
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


SETTINGS = {
    "hall": Setting(id="hall", place="an old hall", detail="Dusty banners hung high, and moonlight shone through cracked windows.", dark="the far end of the hall", tags={"hall", "dark"}),
    "attic": Setting(id="attic", place="a dusty attic", detail="The beams creaked overhead, and boxes made a maze between the rafters.", dark="the back corner of the attic", tags={"attic", "dark"}),
}

INSTRUMENTS = {
    "harpsichord": Instrument(
        id="harpsichord",
        label="harpsichord",
        phrase="an ancient harpsichord",
        sound="it rang like tiny silver bells",
        lure="the shining keys seemed to promise a secret door",
        hidden="behind a velvet curtain",
        tags={"harpsichord", "music", "adventure"},
    ),
}

SPELLS = {
    "glow_change": Spell(
        id="glow_change",
        label="glow-change spell",
        trigger="the glowing key",
        effect="the child changed into a small owl",
        bad_effect="the child changed into a small owl and could no longer reach the safe ladder",
        tags={"transformation", "bad_ending"},
    ),
}

ESCAPES = {
    "ladder": Escape(
        id="ladder",
        label="the attic ladder",
        phrase="the attic ladder",
        power=1,
        tags={"escape"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Theo", "Finn", "Max", "Eli", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an adventure with a harpsichord, a transformation, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--escape", choices=ESCAPES)
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


@dataclass
class StoryParams:
    setting: str
    instrument: str
    spell: str
    escape: str
    name: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INSTRUMENTS:
            for sp in SPELLS:
                for e in ESCAPES:
                    combos.append((s, i, sp, e))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports the harpsichord transformation adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    setting, instrument, spell, escape = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=args.setting or setting,
        instrument=args.instrument or instrument,
        spell=args.spell or spell,
        escape=args.escape or escape,
        name=name,
        gender=gender,
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        hero = world.entities.get("hero")
        if not hero:
            continue
        sig = ("fear", hero.id)
        if hero.meters["transformed"] >= THRESHOLD and sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            hero.memes["confusion"] += 1
            changed = True


def predict_transform(world: World, spell: Spell) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["transformed"] += 1
    hero.meters["mobility"] = 0.0
    propagate(sim)
    return {
        "transformed": hero.meters["transformed"] >= THRESHOLD,
        "can_escape": hero.meters["mobility"] >= THRESHOLD,
        "fear": hero.memes["fear"],
    }


def tell(setting: Setting, instrument: Instrument, spell: Spell, escape: Escape, name: str, gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=gender, role="adventurer"))
    hall = world.add(Entity(id="hall", type="place", label=setting.place, tags=set(setting.tags)))
    harp = world.add(Entity(id="harp", type="instrument", label=instrument.label, tags=set(instrument.tags)))
    curse = world.add(Entity(id="curse", type="spell", label=spell.label, tags=set(spell.tags)))
    ladder = world.add(Entity(id="ladder", type="escape", label=escape.label, tags=set(escape.tags)))

    hero.memes["curiosity"] = 1.0
    hero.memes["wonder"] = 1.0

    world.say(
        f"{hero.id} wandered into {setting.place}, where {setting.detail} "
        f"Near the shadows stood {instrument.phrase}."
    )
    world.say(
        f"{hero.id} brushed the keys, and {instrument.sound}. {instrument.lure}"
    )

    world.para()
    pred = predict_transform(world, spell)
    world.facts["pred"] = pred
    world.say(
        f"Inside the harpsichord, {spell.trigger} flashed. {hero.id} thought it was part of the adventure."
    )
    hero.meters["transformed"] += 1
    hero.meters["mobility"] = 0.0
    hero.meters["glitter"] += 1
    hero.memes["wonder"] += 1
    propagate(world)

    world.say(
        f"Then {spell.effect}. {hero.id} looked down and saw {hero.pronoun('possessive')} small owl wings."
    )

    world.para()
    if hero.memes["fear"] >= SCARED_MIN:
        world.say(
            f"{hero.id} tried to hurry to {escape.phrase}, but {hero.pronoun()} could only wobble and flap."
        )
        world.say(
            f"The ladder stayed too far away, and the secret door slammed shut behind {hero.pronoun('object')}."
        )
        world.say(
            f"By morning, the hall was empty again. The harpsichord sat silent, and the adventure had ended badly."
        )
        world.say(
            f"{hero.id} was safe, but {hero.pronoun()} remained trapped in owl-shape and never found the way home that night."
        )

    world.facts.update(
        hero=hero,
        setting=setting,
        instrument=instrument,
        spell=spell,
        escape=escape,
        hall=hall,
        harp=harp,
        curse=curse,
        ladder=ladder,
        outcome="bad",
        transformed=True,
        can_escape=False,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the word "{f["instrument"].label}" and ends badly after a transformation.',
        f"Tell a mysterious adventure where {f['hero'].id} finds {f['instrument'].phrase}, touches a glowing key, and is changed into something small.",
        f"Write a short story with a harpsichord, a magical transformation, and a bad ending in an old hall.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    instrument = f["instrument"]
    spell = f["spell"]
    return [
        ("Who is the story about?", f"It is about {hero.id}, a curious child who went exploring in an old hall. The child found a harpsichord and touched the wrong key."),
        ("What happened when the child played the harpsichord?", f"{instrument.sound.capitalize()}. Then {spell.effect}. The music opened the way to a transformation instead of a safe treasure."),
        ("Why did the ending turn bad?", f"The transformation made {hero.id} too small and awkward to keep going. The child could not safely reach the ladder, so the adventure ended in a bad, lonely way."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a harpsichord?", "A harpsichord is a keyboard instrument that makes bright plucked sounds when its keys are pressed. It is an old kind of music machine."),
        ("What is a transformation?", "A transformation is a big change from one form to another. In stories, magic can transform a person or creature into something else."),
        ("Why is a tiny owl in a big hall a problem?", "A tiny owl may not be able to reach a ladder or open a heavy door. Small size can make escape hard when the place is dangerous."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
transformed(hero) :- hero(hero), touch(hero).
bad_ending(hero) :- transformed(hero), not can_escape(hero).
can_escape(hero) :- mobility(hero, M), M >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for spid in SPELLS:
        lines.append(asp.fact("spell", spid))
    for eid in ESCAPES:
        lines.append(asp.fact("escape", eid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    _ = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    print("OK: normal story generation smoke test passed.")
    return 0


def asp_choices() -> list[tuple]:
    return valid_combos()


def build_sample(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.instrument not in INSTRUMENTS or params.spell not in SPELLS or params.escape not in ESCAPES:
        raise StoryError("Invalid params for this world.")
    world = tell(SETTINGS[params.setting], INSTRUMENTS[params.instrument], SPELLS[params.spell], ESCAPES[params.escape], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(setting="hall", instrument="harpsichord", spell="glow_change", escape="ladder", name="Lily", gender="girl"),
    StoryParams(setting="attic", instrument="harpsichord", spell="glow_change", escape="ladder", name="Theo", gender="boy"),
]


def resolve_params_for_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for c in asp_choices():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
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
