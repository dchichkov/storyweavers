#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/keel_tuckus_happy_ending_foreshadowing_myth.py
==============================================================================

A small myth-flavored storyworld about a river boat, a cracked keel, a helpful
tuckus cloth, and a foreshadowed storm that can be handled in time.

The domain is intentionally tiny:
- A child or young helper discovers a problem on a boat.
- Early clues foreshadow trouble.
- A sensible fix protects the keel before the storm.
- The story ends happily, with the boat safely gliding on.

This script follows the shared Storyweavers contract:
- standard CLI shape
- typed entities with meters and memes
- state-driven narrative
- grounded Q&A sets
- inline ASP twin with a Python reasonableness gate
- --verify smoke-tests generation and ASP parity
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
FORESHADOW_MIN = 1.0
REPAIR_MIN = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    vessel: str
    keel: str
    tuckus: str
    omen: str
    remedy: str
    storm: str
    seed: Optional[int] = None


@dataclass
class Vessel:
    id: str
    label: str
    name: str
    keel_word: str
    afloat: bool = True
    protected: bool = False
    cracked: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Omen:
    id: str
    label: str
    sign: str
    type: str
    makes_foreshadowing: bool = True


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    power: int
    sense: int
    text: str
    qa_text: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.vessel: Optional[Vessel] = None
        self.omen: Optional[Omen] = None
        self.remedy: Optional[Remedy] = None
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
        c.vessel = copy.deepcopy(self.vessel)
        c.omen = copy.deepcopy(self.omen)
        c.remedy = copy.deepcopy(self.remedy)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    if not world.vessel or not world.omen:
        return out
    if world.vessel.meters["vibration"] < FORESHADOW_MIN:
        return out
    sig = ("foreshadow", world.vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide = world.get("guide")
    guide.memes["unease"] += 1
    world.facts["foreshadowed"] = True
    out.append("__omen__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    if not world.vessel:
        return out
    if world.vessel.meters["strain"] < THRESHOLD:
        return out
    sig = ("crack", world.vessel.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.vessel.cracked = True
    world.vessel.meters["leak"] += 1
    out.append("__crack__")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "social", _r_foreshadow),
    Rule("crack", "physical", _r_crack),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(keel: str, omen: Omen) -> bool:
    return keel in {"oak-keel", "cedar-keel"} and omen.makes_foreshadowing


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def storm_strength(storm: str) -> int:
    return {"drizzle": 1, "wind": 2, "gale": 3}.get(storm, 2)


def can_hold(remedy: Remedy, storm: str) -> bool:
    return remedy.power >= storm_strength(storm)


def predict_issue(world: World) -> dict:
    sim = world.copy()
    if sim.vessel:
        sim.vessel.meters["strain"] += 1
        propagate(sim, narrate=False)
    return {
        "foreshadowed": bool(sim.facts.get("foreshadowed")),
        "cracked": bool(sim.vessel and sim.vessel.cracked),
    }


def nudge(world: World, hero: Entity, guide: Entity, omen: Omen) -> None:
    world.say(
        f"At dawn, {hero.id} and {guide.id} climbed to the riverbank and found "
        f"the {world.vessel.label} waiting like an old song. Yet a small sign "
        f"kept returning: {omen.sign}."
    )
    world.say(
        f"The sign was only a whisper, but it felt like a warning. "
        f"{guide.id} touched {guide.pronoun('possessive')} chin and watched the water."
    )
    guide.memes["caution"] += 1


def discover(world: World, hero: Entity, guide: Entity, omen: Omen) -> None:
    world.say(
        f"{hero.id} leaned over the side and saw that the river had begun to tap "
        f"the {world.vessel.keel_word}. The boat shivered once, then twice."
    )
    world.vessel.meters["vibration"] += 1
    world.say(
        f'"{omen.label}," {guide.id} murmured. "When the water speaks that way, '
        f'something below may be asking for help."'
    )


def inspect(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"{hero.id} knelt low and traced the dark line under the boat. There, in "
        f"the {world.vessel.keel_word}, was a thin crack like a sleeping snake."
    )
    world.vessel.meters["strain"] += 1
    world.vessel.cracked = True


def fix(world: World, guide: Entity, remedy: Remedy) -> None:
    world.say(
        f"{guide.id} did not wait for the river to grow cruel. {guide.pronoun().capitalize()} "
        f"{remedy.text}."
    )
    if remedy.id == "tuckus_wrap":
        world.vessel.protected = True
    world.vessel.meters["strain"] = 0
    world.vessel.meters["repair"] += 1


def sail(world: World, hero: Entity, guide: Entity, storm: str) -> None:
    world.say(
        f"By noon the storm rose exactly as the old sign had promised: {storm} on "
        f"the water, bright clouds over dark waves."
    )
    if world.vessel and world.vessel.protected and can_hold(world.remedy, storm):
        world.say(
            f"But the {world.vessel.label} held firm. Its wrapped {world.vessel.keel_word} "
            f"kept the boat true, and the spray slid off like silver beads."
        )
        hero.memes["joy"] += 1
        guide.memes["pride"] += 1
    else:
        world.say(
            f"The boat would have struggled badly, but the river had already been "
            f"tamed by the careful work."
        )


def ending(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"When the storm passed, {hero.id} laughed and looked back at the shining "
        f"wake. The little crack was mended, the omen was understood, and the river "
        f"carried them home in peace."
    )
    world.say(
        f"That evening, the {world.vessel.label} rested by the shore, safe at last, "
        f"while {hero.id} and {guide.id} watched the stars and felt the old fear turn "
        f"into a story they could keep."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    world.vessel = Vessel(id="vessel", label="river boat", name=params.vessel, keel_word=params.keel)
    world.omen = OMENS[params.omen]
    world.remedy = REMEDIES[params.remedy]

    nudge(world, hero, guide, world.omen)
    discover(world, hero, guide, world.omen)
    world.para()
    inspect(world, hero, guide)
    propagate(world, narrate=True)
    world.para()
    fix(world, guide, world.remedy)
    sail(world, hero, guide, params.storm)
    world.para()
    ending(world, hero, guide)

    world.facts.update(
        hero=hero, guide=guide, vessel=world.vessel, omen=world.omen, remedy=world.remedy,
        storm=params.storm, foreshadowed=True, cracked=world.vessel.cracked
    )
    return world


OMENS = {
    "gulls": Omen(id="gulls", label="the gulls", sign="three gulls circling twice", type="bird"),
    "ring": Omen(id="ring", label="the water-ring", sign="a round ring on the river", type="water"),
    "whisper": Omen(id="whisper", label="the whisper", sign="a soft whisper under the mast", type="wind"),
}

REMEDIES = {
    "tuckus_wrap": Remedy(
        id="tuckus_wrap",
        label="tuckus cloth",
        action="wrapped the crack with tuckus cloth",
        power=3,
        sense=3,
        text="wrapped the crack with tuckus cloth and tied it tight with river cord",
        qa_text="wrapped the crack with tuckus cloth and tied it tight",
    ),
    "harbor_patch": Remedy(
        id="harbor_patch",
        label="harbor patch",
        action="patched the keel at the harbor",
        power=2,
        sense=2,
        text="patched the keel at the harbor with resin and a flat wooden plate",
        qa_text="patched the keel at the harbor",
    ),
    "song_hold": Remedy(
        id="song_hold",
        label="song hold",
        action="sang to steady the boat",
        power=1,
        sense=1,
        text="sang a brave old song, but singing alone could not hold a crack",
        qa_text="sang a brave old song",
    ),
}

HERO_NAMES = ["Nia", "Milo", "Ira", "Sera", "Toma", "Lena"]
GUIDE_NAMES = ["Aunt", "Uncle", "Elder", "Captain", "Grandma", "Grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for omen_id, omen in OMENS.items():
        for remedy_id, remedy in REMEDIES.items():
            if remedy.sense >= 2 and hazard_at_risk("oak-keel", omen) and remedy.power >= 2:
                combos.append((omen_id, "oak-keel", remedy_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child that includes the words "keel" and "tuckus".',
        f"Tell a short, hopeful river myth about {f['hero'].id}, {f['guide'].id}, "
        f"and a warning sign that turns out to matter before the storm.",
        f"Write a story with foreshadowing and a happy ending where a boat's keel is "
        f"protected with tuckus cloth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, vessel, omen, remedy = f["hero"], f["guide"], f["vessel"], f["omen"], f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} and {guide.id} see before the storm?",
            answer=f"They saw {omen.sign}, which was a small sign that trouble might be coming. "
                   f"It mattered because it warned them to look closely at the boat before the water got rough.",
        ),
        QAItem(
            question="What was wrong with the boat?",
            answer=f"The boat had a crack in its {vessel.keel_word}. That was dangerous because the keel helps keep the boat steady and safe in the water.",
        ),
        QAItem(
            question=f"What did they do to help the boat?",
            answer=f"They {remedy.qa_text}. That kept the crack safe before the storm arrived.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily. The boat held together, the storm passed, and everyone got home safely with a bright, peaceful feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a keel?",
            answer="A keel is the strong part along the bottom of a boat. It helps the boat stay steady in the water.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue before something important happens. It helps the reader notice that a later event may matter.",
        ),
        QAItem(
            question="Why is tuckus cloth useful here?",
            answer="The tuckus cloth helps cover and protect the broken place. In this story, it keeps the keel from getting worse before the storm.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.vessel:
        lines.append(f"  vessel    (boat   ) cracked={world.vessel.cracked} protected={world.vessel.protected} meters={dict(world.vessel.meters)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Nia",
        hero_gender="girl",
        guide="Elder",
        guide_gender="woman",
        vessel="Wave-Song",
        keel="oak-keel",
        tuckus="tuckus cloth",
        omen="gulls",
        remedy="tuckus_wrap",
        storm="gale",
    ),
    StoryParams(
        hero="Milo",
        hero_gender="boy",
        guide="Grandpa",
        guide_gender="man",
        vessel="River Crown",
        keel="oak-keel",
        tuckus="tuckus cloth",
        omen="ring",
        remedy="harbor_patch",
        storm="wind",
    ),
]


def explain_rejection(omen: Omen, keel: str) -> str:
    return (
        f"(No story: this setup would not give a meaningful foreshadowing tale. "
        f"The omen and the keel need to create a real warning and a real risk.)"
    )


def explain_remedy(remedy_id: str) -> str:
    r = REMEDIES[remedy_id]
    return (
        f"(Refusing remedy '{remedy_id}': it is too weak for this storyworld's "
        f"storm-and-keel problem. Try {', '.join(x.id for x in sensible_remedies())}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
valid(O, K, R) :- omen(O), keel(K), remedy(R), foreshadow(O), sense(R, S), S >= 2, power(R, P), P >= 2.
foreshadowed :- omen(O), foreshadow(O).
safe_end :- valid(_, _, R), remedy(R), power(R, P), P >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("foreshadow", oid))
    lines.append(asp.fact("keel", "oak-keel"))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: generate smoke test failed: {exc}")
        rc = 1
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"MISMATCH: emit smoke test failed: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic keel-and-tuckus storyworld.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--guide", choices=GUIDE_NAMES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--storm", choices=["drizzle", "wind", "gale"])
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
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError(explain_remedy(args.remedy))
    choices = [c for c in valid_combos()
               if (args.omen is None or c[0] == args.omen)
               and (args.remedy is None or c[2] == args.remedy)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    omen, keel, remedy = rng.choice(choices)
    return StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_gender="girl" if (args.hero in {"Nia", "Sera", "Lena"}) else "boy",
        guide=args.guide or rng.choice(GUIDE_NAMES),
        guide_gender="woman" if (args.guide in {"Aunt", "Grandma", "Elder"}) else "man",
        vessel="Wave-Song",
        keel=keel,
        tuckus="tuckus cloth",
        omen=omen,
        remedy=args.remedy or remedy,
        storm=args.storm or rng.choice(["wind", "gale"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.omen not in OMENS or params.remedy not in REMEDIES:
        raise StoryError("invalid story params")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (omen, keel, remedy) combos:\n")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
