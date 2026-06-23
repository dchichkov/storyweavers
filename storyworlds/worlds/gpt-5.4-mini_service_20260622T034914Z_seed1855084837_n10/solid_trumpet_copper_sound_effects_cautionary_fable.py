#!/usr/bin/env python3
"""
storyworlds/worlds/solid_trumpet_copper_sound_effects_cautionary_fable.py
========================================================================

A small, standalone story world inspired by a fable: a child, a solid little
trumpet, a copper bell, sound effects, and a warning about noisy shortcuts.

The tale stays compact and state-driven. A craftsperson makes a sturdy
trumpet, a young animal-like hero wants to show it off, the loud sound causes a
problem, and a careful helper teaches a safer, quieter way to use it.

Core premise:
- The hero loves the shiny copper trumpet.
- The trumpet can make strong sound effects: "toot", "peep", "BRAAAM".
- If the hero uses the loudest blast at the wrong time, it startles nearby
  creatures and breaks the calm.
- A warning from an older helper leads to a gentler ending image where the
  trumpet is still solid, but used wisely.

The world model tracks physical meters and emotional memes, a few entities,
and a tiny cause/effect chain. It also includes a Python reasonableness gate
and an inline ASP twin, plus a verify mode that exercises generation.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    material: str
    solid: bool
    loudness: int
    sound_effects: tuple[str, ...]
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Warning:
    id: str
    label: str
    phrase: str
    caution_text: str
    safe_method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    instrument: str
    warning: str
    pressure: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", indoors=False, tags={"meadow", "field"}),
    "barnyard": Place(id="barnyard", label="the barnyard", indoors=False, tags={"barnyard", "farm"}),
    "village": Place(id="village", label="the village square", indoors=False, tags={"village", "square"}),
}

INSTRUMENTS = {
    "trumpet": Instrument(
        id="trumpet",
        label="trumpet",
        phrase="a solid copper trumpet",
        material="copper",
        solid=True,
        loudness=3,
        sound_effects=("toot", "peep", "BRAAAM"),
        tags={"trumpet", "copper", "solid", "sound"},
    ),
}

WARNINGS = {
    "donkey": Warning(
        id="donkey",
        label="old donkey",
        phrase="the old donkey's warning",
        caution_text="The old donkey warned that loud sound can scare the flock.",
        safe_method="play a soft toot near the fence instead of blasting it at the chicks",
        tags={"caution", "warning", "sound"},
    ),
}

HEROES = [
    ("Pip", "boy"),
    ("Mina", "girl"),
    ("Lark", "girl"),
    ("Tobin", "boy"),
]

HELPERS = [
    ("Aunt Reed", "woman"),
    ("Uncle Bram", "man"),
    ("Nell", "girl"),
    ("Orin", "boy"),
]

PRESSURES = [
    "the chicks were sleeping in a warm line",
    "the calves were dozing beside the fence",
    "the hives were quiet under the sun",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place_id, "trumpet", "donkey") for place_id in PLACES]


def explain_rejection(place_id: str, instrument_id: str, warning_id: str) -> str:
    place = PLACES.get(place_id)
    inst = INSTRUMENTS.get(instrument_id)
    warn = WARNINGS.get(warning_id)
    if place is None or inst is None or warn is None:
        return "(No story: one or more choices were unknown.)"
    if not inst.solid:
        return "(No story: the instrument must be solid for this fable.)"
    return "(No story: this world wants a solid copper trumpet and a cautionary warning.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary fable about a solid copper trumpet and its sound."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["man", "woman", "boy", "girl"])
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--pressure", choices=[str(i) for i in range(len(PRESSURES))])
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
    if args.place and args.instrument and args.warning:
        if (args.place, args.instrument, args.warning) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.instrument, args.warning))
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, instrument_id, warning_id = rng.choice(sorted(combos))
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper_name, args.helper_type) if args.helper_name and args.helper_type else rng.choice(HELPERS)
    pressure = args.pressure if args.pressure is not None else str(rng.randrange(len(PRESSURES)))
    return StoryParams(
        place=place_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        instrument=instrument_id,
        warning=warning_id,
        pressure=pressure,
    )


def _rule_echo(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    instr = world.facts["instrument"]
    if hero.memes["showoff"] >= THRESHOLD and instr.meters["played"] >= THRESHOLD:
        sig = ("echo", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["startled"] += 1
            out.append("__echo__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _rule_echo(world):
            changed = True
            if s != "__echo__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def advise(world: World, helper: Entity, hero: Entity, warning: Warning, pressure: str) -> None:
    world.say(f"{helper.id} listened to the quiet place and said, \"{warning.caution_text}\"")
    world.say(f"The helper pointed at {pressure} and showed a safer way: {warning.safe_method}.")


def play_loud(world: World, hero: Entity, instrument: Entity, warning: Warning) -> None:
    hero.memes["showoff"] += 1
    instrument.meters["played"] += 1
    world.say(f"{hero.id} lifted the {instrument.label} and blew a bright {instrument.attrs['sound']}.")
    world.say("The sound rolled over the grass like a shiny wave.")
    propagate(world, narrate=False)


def reaction(world: World, helper: Entity, hero: Entity, pressure: str) -> None:
    hero.memes["regret"] += 1
    helper.memes["caution"] += 1
    world.say(f"But {pressure} moved and the little ones jerked awake.")
    world.say(f"{helper.id} covered {helper.pronoun('possessive')} ears and frowned at the noise.")


def ending(world: World, hero: Entity, helper: Entity, instrument: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["peace"] += 1
    world.say(f"After that, {hero.id} kept the trumpet close and learned that a strong tool still needs a gentle hand.")
    world.say(f"The trumpet stayed solid and bright, and its copper shone in the afternoon like a coin that had remembered to be quiet.")


def cautionary_turn(world: World, helper: Entity, hero: Entity, instrument: Entity, warning: Warning, pressure: str) -> None:
    world.say(f"One morning in {world.place.label}, {hero.id} found {instrument.phrase} on a bench.")
    world.say(f"It was {instrument.material} and {('solid' if instrument.solid else 'hollow')}, with a smooth bell that flashed in the sun.")
    world.say(f"{hero.id} loved the way it could say {' and '.join(instrument.sound_effects)}.")
    world.para()
    world.say(f"{hero.id} wanted to show the whole place a huge sound.")
    advise(world, helper, hero, warning, pressure)
    play_loud(world, hero, instrument, warning)
    reaction(world, helper, hero, pressure)
    world.para()
    world.say(f"Then {helper.id} taught a simpler lesson: good things are best when they do no harm.")
    ending(world, hero, helper, instrument)


def tell(place: Place, hero_name: str, hero_type: str, helper_name: str, helper_type: str, instrument_cfg: Instrument, warning_cfg: Warning, pressure: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    instrument = world.add(Entity(id=instrument_cfg.id, type="instrument", label=instrument_cfg.label, phrase=instrument_cfg.phrase, solid=instrument_cfg.solid, tags=set(instrument_cfg.tags), attrs={"material": instrument_cfg.material, "sound": instrument_cfg.sound_effects[0]}))
    warning = warning_cfg
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["instrument"] = instrument
    world.facts["warning"] = warning
    world.facts["pressure"] = pressure
    cautionary_turn(world, helper, hero, instrument, warning, pressure)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    instr = f["instrument"]
    return [
        f'Write a fable for a young child about a solid copper {instr.label} and its loud sound effects.',
        f"Tell a cautionary story where {hero.id} wants to blast the {instr.label}, but {helper.id} teaches a gentler way.",
        f'Write a small fable that includes the words "solid", "trumpet", and "copper" and ends with a wise lesson about sound.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    instr = f["instrument"]
    pressure = f["pressure"]
    qas = [
        QAItem(
            question=f"What did {hero.id} find in {world.place.label}?",
            answer=f"{hero.id} found a solid copper trumpet. It was a sturdy little instrument that could make loud sound effects.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} before the trumpet blast?",
            answer=f"{helper.id} warned {hero.id} because the loud sound could disturb {pressure}. The helper wanted the trumpet to be used in a kinder way.",
        ),
        QAItem(
            question=f"What did {hero.id} do after hearing the warning?",
            answer=f"{hero.id} still played the trumpet, but then listened when the noise caused trouble. After that, {hero.id} learned to use a softer blast and keep the peace.",
        ),
    ]
    if f["instrument"].meters["played"] >= THRESHOLD:
        qas.append(QAItem(
            question=f"Which sound did the trumpet make when {hero.id} blew it?",
            answer=f"It made a bright {instr.attrs['sound']} and then the bigger sound rolled out across {world.place.label}. That loudness is why the warning mattered.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does solid mean?",
            answer="Solid means something is hard all the way through, so it keeps its shape and does not wobble like water.",
        ),
        QAItem(
            question="What is a trumpet?",
            answer="A trumpet is a brass instrument that makes sound when someone blows into it. It can be soft or very loud.",
        ),
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish metal. People use it to make shiny, lasting things like bells and old coins.",
        ),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
loud_sound(I) :- instrument(I), played(I).
warning_needed(H) :- hero(H), loud_sound(I).
wise_end(H) :- hero(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.solid:
            lines.append(asp.fact("solid", iid))
        lines.append(asp.fact("material", iid, inst.material))
        for s in inst.sound_effects:
            lines.append(asp.fact("sound", iid, s))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    # simple smoke test for ordinary generation
    sample = generate(resolve_params(argparse.Namespace(place=None, hero_name=None, hero_type=None, helper_name=None, helper_type=None, instrument=None, warning=None, pressure=None), random.Random(7)))
    assert sample.story
    cl = set(asp_valid_combos())
    if cl != py:
        print("MISMATCH between ASP and Python gate")
        return 1
    print(f"OK: ASP matches Python gate ({len(py)} combos).")
    print("OK: generate() smoke test succeeded.")
    return 0


def build_story(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        INSTRUMENTS[params.instrument],
        WARNINGS[params.warning],
        PRESSURES[int(params.pressure)],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams(place=p, hero_name="Pip", hero_type="boy", helper_name="Nell", helper_type="girl", instrument="trumpet", warning="donkey", pressure="0")
            for p in PLACES
        ]
        samples = [generate(s) for s in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(rng_base + i))
            except StoryError as err:
                print(err)
                return
            p.seed = rng_base + i
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
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
