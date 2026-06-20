#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disc_musk_negative_magic_misunderstanding_slice_of.py
=====================================================================================

A standalone storyworld for a small slice-of-life tale about a child, a
misunderstood magic trick, a scented disc, and a calmer explanation that turns
the day around.

Premise
-------
A child wants to make an ordinary afternoon feel special. A little helper tries
to use a magic word on a disc-shaped toy or keepsake, but someone else mistakes
the plan and thinks the magic is negative or bad. The misunderstanding creates a
brief tense moment, then a patient explanation and a gentle real-world fix
restore the mood.

This world keeps the simulation small and concrete:
- typed entities with physical meters and emotional memes,
- a state-driven story rather than a fixed paragraph,
- a Python reasonableness gate,
- an inline ASP twin,
- three distinct QA sets grounded in the world model,
- a complete CLI with verification and JSON output.

The target seed words are included in the world vocabulary and can appear in the
stories:
- disc
- musk
- negative

The story style is intentionally slice-of-life: a kitchen table, a hallway, a
small mistake, a careful talk, and a soft ending image.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    detail: str


@dataclass
class Disc:
    id: str
    label: str
    phrase: str
    sound: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Scent:
    id: str
    label: str
    phrase: str
    musk_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    word: str
    effect: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    fear: str
    correction: str
    tags: set[str] = field(default_factory=set)


@dataclass
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("tense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["quiet"] += 1
        out.append("__tense__")
    return out


CAUSAL_RULES = [Rule("tense", "social", _r_tense)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


SETTINGS = {
    "table": Setting("table", "the kitchen table", "A plate of toast, a mug, and a bright little disc sat near the window."),
    "bench": Setting("bench", "the front bench", "A watering can, a mailbox, and a small disc-shaped charm rested nearby."),
    "hall": Setting("hall", "the hallway", "A coat hook, a hallway rug, and a disc on a hook made the place feel neat and ordinary."),
}

DISCS = {
    "music": Disc("music", "disc", "a shiny disc", "clicked softly", "glowed like a coin", tags={"disc"}),
    "toy": Disc("toy", "disc", "a toy disc", "spun with a soft whirr", "caught the light", tags={"disc"}),
    "memory": Disc("memory", "disc", "an old disc", "made a tiny humming sound", "looked warm in the palm", tags={"disc"}),
}

SCENTS = {
    "musk": Scent("musk", "musk", "a little bottle of musk", "musk", tags={"musk"}),
    "soap": Scent("soap", "scent", "a soap-scented pouch", "clean musk", tags={"musk"}),
    "negative": Scent("negative", "negative", "a label that said negative", "negative", tags={"negative"}),
}

MAGICS = {
    "shine": Magic("shine", "shine", "make the disc glow softly", harmless=True, tags={"magic"}),
    "spin": Magic("spin", "spin", "make the disc turn once in the air", harmless=True, tags={"magic"}),
    "echo": Magic("echo", "echo", "make the disc seem to hum", harmless=True, tags={"magic"}),
}

MISUNDERSTANDINGS = {
    "bad_magic": Misunderstanding("bad_magic", "thought the magic was bad", "it only meant the scent was off, not that anything was wrong", tags={"misunderstanding"}),
    "negative_label": Misunderstanding("negative_label", "thought the word negative meant no one should touch it", "the word negative was only on the label", tags={"misunderstanding"}),
}

CHILD_NAMES = ["Mina", "Nico", "Ari", "Pia", "Tess", "Luca", "Noa", "Zuri"]
ADULT_NAMES = ["Mom", "Dad"]
TRAITS = ["careful", "curious", "patient", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for did in DISCS:
            for scid in SCENTS:
                for mid in MAGICS:
                    if sid == "hall" and scid == "negative" and did == "memory":
                        combos.append((sid, did, scid, mid))
                    elif sid != "hall":
                        combos.append((sid, did, scid, mid))
    return combos


@dataclass
class StoryParams:
    setting: str
    disc: str
    scent: str
    magic: str
    child: str
    child_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life magic misunderstanding story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--disc", choices=DISCS)
    ap.add_argument("--scent", choices=SCENTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--child")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DISCS:
        lines.append(asp.fact("disc", did))
    for scid in SCENTS:
        lines.append(asp.fact("scent", scid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    lines.append(asp.fact("sensitive_word", "negative"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,D,C,M) :- setting(S), disc(D), scent(C), magic(M).
selected_word(negative) :- scent(negative).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP parity" if ok else "MISMATCH: ASP parity")
    if not ok:
        return 1
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(0))
        s = generate(p)
        assert s.story.strip()
        print("OK: smoke story generation")
    except Exception as exc:
        print(f"SMOKE FAILED: {exc}")
        return 1
    return 0


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(CHILD_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.disc is None or c[1] == args.disc)
              and (args.scent is None or c[2] == args.scent)
              and (args.magic is None or c[3] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, disc, scent, magic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, gender)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, disc, scent, magic, child, gender, adult, trait)


def _can_misunderstand(disc: Disc, scent: Scent, magic: Magic) -> bool:
    return "disc" in disc.tags and "negative" in scent.tags and magic.harmless


def tell(params: StoryParams) -> World:
    if not _can_misunderstand(DISCS[params.disc], SCENTS[params.scent], MAGICS[params.magic]):
        raise StoryError("This combination does not make a believable misunderstanding.")
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=[params.trait]))
    adult = world.add(Entity(id=params.adult, kind="character", type="mother" if params.adult == "Mom" else "father", role="adult"))
    disc = world.add(Entity(id="disc", label=DISCS[params.disc].label, kind="thing", type="toy", attrs={"phrase": DISCS[params.disc].phrase}))
    scent = world.add(Entity(id="scent", label=SCENTS[params.scent].label, kind="thing", type="thing"))
    magic = world.add(Entity(id="magic", label=MAGICS[params.magic].word, kind="thing", type="thing"))

    child.memes["curiosity"] = 1.0
    adult.memes["calm"] = 1.0
    world.say(f"{params.child} sat near {world.setting.place}. {world.setting.detail}")
    world.say(f'{params.child} found {DISCS[params.disc].phrase} and thought it could make the afternoon feel special.')
    world.say(f'{params.child} whispered the magic word, "{MAGICS[params.magic].word}." {DISCS[params.disc].sound.capitalize()} and {DISCS[params.disc].glow}.')
    world.para()
    child.memes["worry"] += 1
    adult.memes["worry"] += 1
    world.say(f"{params.adult} paused. The label said negative, and for a moment {params.adult.lower() if False else params.adult} thought that meant something bad.")
    world.say(f'"I think you\'re making a negative spell," {params.adult} said, sounding unsure.')
    world.say(f'{params.child} frowned. "No, I only meant the word on the scent bottle -- the musk one," {params.child} said.')
    world.para()
    world.say(f"{params.child} held up the disc again and showed that the little musk bottle was just a shelf label, not a warning.")
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(f"{params.adult} laughed softly. " + f'"Oh! I misunderstood." {params.adult} said. "The negative word was only a name, not a problem."')
    world.say(f"They put the disc back on the table, opened the window, and let the clean air replace the musk.")
    world.say(f"After that, the disc just sat there, shining by the toast, while the room felt ordinary and good again.")
    world.facts.update(
        child=child, adult=adult, disc=disc, scent=scent, magic=magic,
        setting=world.setting, outcome="resolved"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "disc", "musk", and "negative".',
        f"Tell a gentle story where {f['child'].id} tries a little magic word near a disc, but {f['adult'].id} misunderstands the label negative and then realizes the mistake.",
        f'Write a calm everyday story with a tiny misunderstanding, a magic word, and an ending that feels safe and ordinary.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult = f["child"], f["adult"]
    return [
        QAItem(question="What did the child want to do?",
               answer=f"{child.id} wanted to make the afternoon feel special by trying a small magic word near the disc. It was a simple idea, not a mean or dangerous one."),
        QAItem(question="Why did the adult get worried?",
               answer=f"{adult.id} saw the word negative and thought it might mean something bad was happening. The worry came from the label, not from real danger."),
        QAItem(question="How was the misunderstanding fixed?",
               answer=f"{child.id} explained that negative was only part of the scent label and not a warning. Then {adult.id} understood, smiled, and the room went back to feeling calm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a disc?",
               answer="A disc is a flat, round object. It can be a toy, a keepsake, or something you put on a table."),
        QAItem(question="What does musk mean?",
               answer="Musk is a strong smell. Some people like it, and some people think it smells too sharp."),
        QAItem(question="What does negative mean?",
               answer="Negative can mean 'not positive' or 'a warning sign' in some places. In this story, it was just a word on a label, which caused the misunderstanding."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def explain_rejection() -> str:
    return "(No story: this combination does not produce a believable slice-of-life misunderstanding.)"


CURATED = [
    StoryParams("table", "music", "negative", "shine", "Mina", "girl", "Mom", "careful"),
    StoryParams("bench", "toy", "musk", "spin", "Nico", "boy", "Dad", "curious"),
    StoryParams("hall", "memory", "negative", "echo", "Ari", "boy", "Mom", "gentle"),
]


def asp_outcome(params: StoryParams) -> str:
    return "resolved" if _can_misunderstand(DISCS[params.disc], SCENTS[params.scent], MAGICS[params.magic]) else "blocked"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
