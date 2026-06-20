#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moan_mandolin_defective_surprise_fairy_tale.py
==============================================================================

A standalone fairy-tale story world about a little music-maker, a defective
mandolin, a sad moan, and a surprise that turns trouble into delight.

The domain is small on purpose:
- one child character
- one helpful elder
- one defective instrument
- one hidden surprise
- one magical fix-or-gift turn

The world model tracks physical meters and emotional memes, and the prose is
driven by those state changes rather than by a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/moan_mandolin_defective_surprise_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/moan_mandolin_defective_surprise_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/moan_mandolin_defective_surprise_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/moan_mandolin_defective_surprise_fairy_tale.py --verify
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
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "bard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Instrument:
    id: str
    name: str
    phrase: str
    sound: str
    defective: bool = False
    fixed: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Surprise:
    id: str
    kind: str
    reveal: str
    gift: str
    magic: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_moan(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    instr = world.entities.get("instrument")
    if not child or not instr:
        return out
    if child.memes["disappointment"] < THRESHOLD or not instr.attrs.get("broken"):
        return out
    sig = ("moan",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sadness"] += 1
    out.append(f"The little room filled with a soft moan.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    instr = world.entities.get("instrument")
    fairy = world.entities.get("fairy")
    gift = world.facts.get("surprise")
    if not child or not instr or not fairy or not gift:
        return out
    if not instr.attrs.get("revealed") or gift.reveal:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.reveal = True
    out.append(
        f"Then the fairy revealed the hidden surprise: {gift.gift}, gleaming "
        f"with {gift.magic}."
    )
    return out


CAUSAL_RULES = [
    Rule("moan", "emotional", _r_moan),
    Rule("surprise", "turn", _r_surprise),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(instrument: Instrument, surprise: Surprise) -> bool:
    return instrument.defective and surprise.kind in {"gift", "repair", "song"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for iid, instr in INSTRUMENTS.items():
        for sid, sp in SURPRISES.items():
            if is_reasonable(instr, sp):
                combos.append((iid, sid))
    return combos


@dataclass
@dataclass
class StoryParams:
    instrument: str
    surprise: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    setting: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "forest": "a mossy forest glade",
    "castle": "a candlelit castle hall",
    "village": "a bright village square",
}

INSTRUMENTS = {
    "mandolin": Instrument(
        "mandolin",
        "mandolin",
        "a little mandolin",
        "tinkling like raindrops",
        defective=True,
        tags={"mandolin", "defective"},
    ),
    "lute": Instrument(
        "lute",
        "lute",
        "an old lute",
        "soft as a whisper",
        defective=True,
        tags={"lute", "defective"},
    ),
    "fiddle": Instrument(
        "fiddle",
        "fiddle",
        "a small fiddle",
        "thin and trembling",
        defective=True,
        tags={"fiddle", "defective"},
    ),
}

SURPRISES = {
    "gift": Surprise(
        "gift",
        "gift",
        False,  # temporary; toggled by the story when revealed
        "a golden tuning key",
        "moon-silver",
        tags={"surprise", "gift"},
    ),
    "repair": Surprise(
        "repair",
        "repair",
        False,
        "a tiny repair kit",
        "starlight glue",
        tags={"surprise", "repair"},
    ),
    "song": Surprise(
        "song",
        "song",
        False,
        "a secret chorus of bells",
        "warm sparkle",
        tags={"surprise", "song"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Elin"]
BOY_NAMES = ["Robin", "Perrin", "Finn", "Milo", "Arlo"]


def tell(setting: str, instrument: Instrument, surprise: Surprise,
         child_name: str, child_gender: str,
         elder_name: str, elder_gender: str) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, label=child_name, role="child"))
    elder = world.add(Entity("elder", kind="character", type=elder_gender, label=elder_name, role="elder"))
    fairy = world.add(Entity("fairy", kind="character", type="fairy", label="the fairy", role="helper"))
    instr = world.add(Entity("instrument", type="thing", label=instrument.name, attrs={"broken": instrument.defective, "revealed": False}))
    world.facts["surprise"] = copy.deepcopy(surprise)
    world.facts.update(setting=setting, child=child, elder=elder, fairy=fairy, instrument=instr)

    child.memes["love"] += 1
    child.memes["hope"] += 1
    world.say(
        f"In {SETTINGS[setting]}, {child.label} loved to carry {instrument.phrase}. "
        f"{elder.label} listened with a kindly smile."
    )
    world.say(
        f"When {child.label} plucked the strings, the tune came out {instrument.sound}, "
        f"and then it gave a sad moan."
    )

    world.para()
    child.memes["disappointment"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.label} lowered {child.pronoun('possessive')} chin. "
        f'"Oh no," {child.pronoun()} whispered, "my {instrument.name} is defective."'
    )
    propagate(world, narrate=True)

    world.para()
    elder.memes["kindness"] += 1
    world.say(
        f"{elder.label} knelt beside {child.label}. "
        f'"Do not fret," {elder.pronoun()} said. "Fair tales keep their surprises for last."'
    )
    world.say(f"The fairy tapped the bridge of the {instrument.name} three times.")
    instr.attrs["revealed"] = True
    propagate(world, narrate=True)

    world.para()
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    instr.attrs["broken"] = False
    instr.attrs["mended"] = True
    world.say(
        f"The little surprise was not a scold at all. "
        f"It was {world.facts['surprise'].gift}, bright with {world.facts['surprise'].magic}, "
        f"and it made the {instrument.name} sing again."
    )
    world.say(
        f"{child.label} laughed, {elder.label} laughed, and the fairy's cloak shone "
        f"like a small dawn."
    )
    world.say(
        f"That night, the {instrument.name} was no longer defective. "
        f"It played a clear song, and the moan was gone."
    )

    world.facts.update(
        outcome="healed",
        revealed=True,
        fixed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the words "moan", "mandolin", and "defective".',
        f"Tell a gentle fairy tale where {f['child'].label} finds out the {f['instrument'].label} is defective, then a surprise makes things better.",
        f'Write a story with a surprise ending in a castle, forest, or village, where a broken mandolin becomes lovely again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    instr = f["instrument"]
    qa = [
        QAItem(
            question="What was wrong with the mandolin at the start?",
            answer=f"It was defective, so its music came out wrong and then slipped into a moan. That sadness is what made the problem feel real before the surprise arrived.",
        ),
        QAItem(
            question="Who helped the child?",
            answer=f"{elder.label} helped with a gentle voice, and the fairy kept the secret until the right moment. The help was kind, not scary, so the child could wait for the surprise.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The {instr.label} was no longer defective, and it could sing clearly again. The moan was replaced by happy music, which showed that the surprise truly fixed the trouble.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mandolin?",
            answer="A mandolin is a small stringed instrument that people pluck to make music. It is a little like a lute, but it has its own bright, tinkling sound.",
        ),
        QAItem(
            question="What does defective mean?",
            answer="Defective means something is broken or not working properly. A defective thing may need a repair or a clever fix before it can work again.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when you do not know it is coming. It can be a gift, a secret helper, or a happy turn in the story.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mandolin", "gift", "Lina", "girl", "Mira", "girl", "forest"),
    StoryParams("lute", "repair", "Robin", "boy", "Elin", "girl", "castle"),
    StoryParams("fiddle", "song", "Tessa", "girl", "Perrin", "boy", "village"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: moan, mandolin, defective, surprise."
    )
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.instrument and args.surprise:
        if not is_reasonable(INSTRUMENTS[args.instrument], SURPRISES[args.surprise]):
            raise StoryError("This tale wants a defective instrument and a kind surprise.")
    combos = [c for c in valid_combos()
              if (args.instrument is None or c[0] == args.instrument)
              and (args.surprise is None or c[1] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    instrument, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    elder_name = args.elder or rng.choice(GIRL_NAMES if elder_gender == "girl" else BOY_NAMES)
    setting = args.setting or rng.choice(sorted(SETTINGS))
    return StoryParams(instrument, surprise, child_name, gender, elder_name, elder_gender, setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.setting,
        INSTRUMENTS[params.instrument],
        SURPRISES[params.surprise],
        params.child_name,
        params.child_gender,
        params.elder_name,
        params.elder_gender,
    )
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
defective(I) :- instrument(I), is_defective(I).
reasonable(I,S) :- defective(I), surprise(S), good_surprise(S).
outcome(healed) :- defective(I), surprise(S), reasonable(I,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for iid, instr in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if instr.defective:
            lines.append(asp.fact("is_defective", iid))
    for sid, sp in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if sp.kind in {"gift", "repair", "song"}:
            lines.append(asp.fact("good_surprise", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in ASP gate.")
        if py - cl:
            print(" only python:", sorted(py - cl))
        if cl - py:
            print(" only clingo:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test succeeded.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} reasonable instrument-surprise pairs:")
        for iid, sid in asp_valid_combos():
            print(f"  {iid} {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.elder_name}: {p.instrument} with {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
