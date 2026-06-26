#!/usr/bin/env python3
"""
storyworlds/worlds/passion_hearth_perceive_happy_ending_mystery_to.py
======================================================================

A small fable-like story world about a village hearth, a keen-eyed child, and a
mystery to solve. The hero's passion is to keep the hearth warm for everyone;
the tension is a puzzling coldness or missing spark; the turn is careful
perception; the ending is happy and proven by the hearth glowing again.

The seed words are woven into the world model:
- passion
- hearth
- perceive

The domain is intentionally small and classical: one problem, one investigation,
one clear resolution.
"""

from __future__ import annotations

import argparse
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "shepherdess"}
        male = {"boy", "father", "man", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    gift: str
    name: str
    gender: str
    age: str
    seed: Optional[int] = None


SETTINGS = {
    "cottage": Setting(place="the cottage", indoors=True, affords={"hearth"}),
    "hall": Setting(place="the village hall", indoors=True, affords={"hearth"}),
    "barn": Setting(place="the old barn", indoors=True, affords={"hearth"}),
}

MYSTERIES = {
    "draft": Mystery(
        id="draft",
        clue="a cold breath near the stones",
        cause="a cracked shutter let the wind in",
        reveal="the shutter had slipped open",
        fix="close the shutter and bank the coals",
        tags={"wind", "cold"},
    ),
    "ashes": Mystery(
        id="ashes",
        clue="gray ash falling in little piles",
        cause="the grate was full and needed clearing",
        reveal="the grate was clogged with ash",
        fix="sweep the grate clean and feed the fire",
        tags={"ash", "fire"},
    ),
    "spark": Mystery(
        id="spark",
        clue="a tiny blink hidden under the embers",
        cause="a sleeping spark was waiting for air",
        reveal="the spark was still alive",
        fix="blow gently and add dry sticks",
        tags={"spark", "fire"},
    ),
}

GIFTS = {
    "wood": Gift(id="wood", label="dry wood", phrase="a bundle of dry wood", region="hands"),
    "blanket": Gift(id="blanket", label="wool blanket", phrase="a warm wool blanket", region="shoulders"),
    "matchbox": Gift(id="matchbox", label="matchbox", phrase="a little matchbox", region="hands"),
}

NAMES = {
    "girl": ["Mina", "Luna", "Tara", "Iris", "Nora"],
    "boy": ["Robin", "Pip", "Jory", "Tobin", "Eli"],
}
Ages = ["young", "small", "curious", "kind", "bright"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_cold(world: World) -> list[str]:
    out = []
    hearth = world.get("hearth")
    myst = world.facts["mystery"]
    if hearth.meters.get("warmth", 0) < THRESHOLD and ("cold", myst.id) not in world.fired:
        world.fired.add(("cold", myst.id))
        out.append("The hearth felt cold and lonely.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    hearth = world.get("hearth")
    myst = world.facts["mystery"]
    if hero.memes.get("perceive", 0) >= THRESHOLD and ("solve", myst.id) not in world.fired:
        if myst.id == "draft":
            hearth.meters["warmth"] = max(hearth.meters.get("warmth", 0), 1.5)
        elif myst.id == "ashes":
            hearth.meters["warmth"] = max(hearth.meters.get("warmth", 0), 1.2)
        elif myst.id == "spark":
            hearth.meters["warmth"] = max(hearth.meters.get("warmth", 0), 1.3)
        world.fired.add(("solve", myst.id))
        out.append("The mystery began to open its door.")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold), Rule("solve", _r_solve)]


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


def predict_resolution(world: World, hero: Entity, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("hero").memes["perceive"] = 1.0
    propagate(sim, narrate=False)
    hearth = sim.get("hearth")
    return {"warm": hearth.meters.get("warmth", 0) >= THRESHOLD}


def tell(setting: Setting, mystery: Mystery, gift: Gift, name: str, gender: str, age: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label="the old keeper"))
    hearth = world.add(Entity(id="hearth", type="hearth", label="the hearth"))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue))
    present = world.add(Entity(id="gift", type=gift.id, label=gift.label, phrase=gift.phrase, owner=hero.id))
    hearth.meters["warmth"] = 0.0
    hero.memes["passion"] = 1.0
    hero.memes["perceive"] = 0.0
    world.facts.update(hero=hero, elder=elder, hearth=hearth, mystery=mystery, gift=present)

    world.say(f"{name} was a {age} child with a deep passion for the village hearth.")
    world.say(f"{hero.pronoun().capitalize()} loved how the fire gathered neighbors close on cold evenings.")
    world.say(f"One day, {hero.pronoun('possessive')} {elder.label} gave {hero.pronoun('object')} {gift.phrase}.")
    world.say(f"{name} kept it near the hearth, because {hero.pronoun('possessive')} heart wanted to help the flame stay kind and bright.")

    world.para()
    world.say(f"That night, the hearth grew strangely quiet.")
    world.say(f"{hero.pronoun().capitalize()} noticed {mystery.clue} and frowned.")
    world.say(f"{hero.pronoun().capitalize()} could perceive that something hidden was making the fire weak.")
    hero.memes["worry"] = 1.0

    if mystery.id == "draft":
        world.say("A thin shiver curled through the room near the shutter.")
    elif mystery.id == "ashes":
        world.say("Gray ash lay thick and heavy around the grate.")
    else:
        world.say("A tiny spark hid under the embers, blinking like a sleepily watched star.")

    world.para()
    world.say(f"{name} did not rush away. {hero.pronoun().capitalize()} looked carefully, as if listening with {hero.pronoun('possessive')} eyes.")
    hero.memes["perceive"] = 1.0
    propagate(world, narrate=True)

    if mystery.id == "draft":
        world.say(f"{hero.pronoun().capitalize()} found the cracked shutter and closed it tight.")
        world.say(f"Then {hero.pronoun()} banked the coals and set the {gift.label} beside the hearth.")
    elif mystery.id == "ashes":
        world.say(f"{hero.pronoun().capitalize()} swept the grate clean and fed the fire with dry wood.")
        world.say(f"The {gift.label} waited nearby in case the flames needed one more kind hand.")
    else:
        world.say(f"{hero.pronoun().capitalize()} blew gently, and the spark woke up.")
        world.say(f"Then {hero.pronoun()} added dry wood and let the little flame grow brave again.")

    hearth.meters["warmth"] = max(hearth.meters.get("warmth", 0), 1.5)
    hero.memes["joy"] = 1.0
    hero.memes["worry"] = 0.0

    world.para()
    world.say(f"By morning, the hearth glowed again.")
    world.say(f"The {elder.label} smiled, and {name} smiled back, pleased that careful perceiving had solved the mystery.")
    world.say(f"The whole room felt warmer, and the story ended as a good fable should: with a wise eye, a steady heart, and a happy fire.")

    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            for gid in GIFTS:
                combos.append((place, mid, gid))
    return combos


def explain_rejection(params: argparse.Namespace) -> str:
    return "(No story: this world only tells hearth mysteries inside the cottage, hall, or barn.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, myst, gift = f["hero"], f["mystery"], f["gift"]
    return [
        f'Write a short fable for a child named {hero.label} about a hearth, a mystery, and the word "perceive".',
        f"Tell a gentle story where {hero.label} notices a problem at the hearth and solves it with careful looking.",
        f"Write a happy-ending story in which a child with passion for the hearth discovers {myst.clue} and sets things right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, myst, gift, hearth = f["hero"], f["elder"], f["mystery"], f["gift"], f["hearth"]
    return [
        QAItem(
            question=f"What did {hero.label} care about most in the story?",
            answer=f"{hero.label} cared deeply about the hearth and wanted it to stay warm for everyone.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} perceive the mystery?",
            answer=f"{hero.label} noticed {myst.clue}, which showed that something hidden was affecting the hearth.",
        ),
        QAItem(
            question=f"What did the old keeper give {hero.label}?",
            answer=f"The old keeper gave {hero.label} {gift.phrase}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"The mystery was solved when {hero.label} looked carefully, found the cause, and helped the hearth glow again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hearth?",
            answer="A hearth is the place where a fire burns safely, often in a cottage or hall, so people can share warmth.",
        ),
        QAItem(
            question="What does it mean to perceive something?",
            answer="To perceive something means to notice it carefully using your senses and attention.",
        ),
        QAItem(
            question="Why do people keep dry wood near a fire?",
            answer="Dry wood catches more easily and helps a fire burn better than damp wood.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", mystery="draft", gift="wood", name="Mina", gender="girl", age="curious"),
    StoryParams(place="hall", mystery="ashes", gift="blanket", name="Robin", gender="boy", age="kind"),
    StoryParams(place="barn", mystery="spark", gift="matchbox", name="Tara", gender="girl", age="bright"),
]


ASP_RULES = r"""
warm_hearth(H) :- hearth(H), warmth(H,W), W >= 1.
mystery_solved(M) :- mystery(M), clue_seen(M), cause_found(M).
happy_ending(S) :- warm_hearth(H), hero(S,H), mystery_solved(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_region", gid, g.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warm_hearth/1.\n#show happy_ending/1.\n"))
    atoms = set((sym.name, tuple(a.name if a.type != 1 else a.string for a in sym.arguments)) for sym in model)
    ok = bool(atoms)
    python_ok = bool(CURATED)
    if ok and python_ok:
        print("OK: ASP and Python gates are present.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like hearth mystery story world with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--age", choices=Ages)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gift = args.gift or rng.choice(list(GIFTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    age = args.age or rng.choice(Ages)
    return StoryParams(place=place, mystery=mystery, gift=gift, name=name, gender=gender, age=age)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], GIFTS[params.gift], params.name, params.gender, params.age)
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
        print(asp_program("#show warm_hearth/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show warm_hearth/1.\n#show happy_ending/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
