#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bear_groan_rhyme_bedtime_story.py
===================================================================

A small bedtime storyworld: a sleepy little bear has a noisy groan, wants a
quiet rhyming bedtime, gets help from a gentle caretaker, and ends with a calm
rhyme that proves the change.

This world is intentionally compact and classical: typed entities, physical
meters, emotional memes, a tiny causal model, a Python reasonableness gate, and
an inline ASP twin for parity checks.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Bedtime:
    id: str
    place: str
    rhyme: str
    sound: str
    calm_fix: str
    ending_image: str
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
class Nuisance:
    id: str
    label: str
    sound: str
    label_phrase: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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


def _r_groan_echo(world: World) -> list[str]:
    out: list[str] = []
    bear = world.get("bear")
    if bear.meters["groan"] < THRESHOLD:
        return out
    sig = ("echo", "bear")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bear.memes["sleepy"] += 1
    bear.memes["worry"] += 1
    out.append("__echo__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    bear = world.get("bear")
    if bear.meters["groan"] < THRESHOLD or bear.meters["calm"] < THRESHOLD:
        return out
    sig = ("calm", "bear")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bear.memes["sleepy"] += 1
    bear.memes["relief"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("groan_echo", "sound", _r_groan_echo), Rule("calm", "soft", _r_calm)]


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


def valid_bedtimes() -> list[tuple[str, str, str]]:
    combos = []
    for bed in BEDS:
        for nuis in NUISANCES.values():
            for comfort in COMFORTS.values():
                if nuis.noisy and comfort.soft:
                    combos.append((bed.id, nuis.id, comfort.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    bed: str
    nuisance: str
    comfort: str
    child_name: str
    child_type: str
    caregiver_type: str
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


def bedtime_story(world: World, bed: Bedtime, nuis: Nuisance, comfort: Comfort,
                  child: Entity, caregiver: Entity) -> None:
    world.say(f"At {bed.place}, {child.id} was ready for bed, but the room held a small {nuis.label}.")
    world.say(f'{child.id} made a little {nuis.sound.lower()} and gave a sleepy groan. "{bed.rhyme}" {child.id} mumbled.')
    child.meters["groan"] += 1
    child.memes["sleepy"] += 1
    child.memes["sad"] += 1
    propagate(world, narrate=True)


def soothe(world: World, child: Entity, caregiver: Entity, comfort: Comfort, bed: Bedtime) -> None:
    caregiver.memes["care"] += 1
    child.meters["calm"] += 1
    child.memes["relief"] += 1
    world.say(f'{caregiver.id} came softly and said, "{comfort.phrase} can help your heart be still."')
    world.say(f"{caregiver.id} tucked {comfort.label} close, and its {comfort.glow} made the dark corner feel kind.")
    propagate(world, narrate=True)
    world.say(f'Then {caregiver.id} whispered, "{bed.calm_fix}"')
    world.say(f'At last, {bed.ending_image}.')


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    caregiver = world.add(Entity(id="Grown-up", kind="character", type=params.caregiver_type, role="caregiver"))
    bed = BEDS[params.bed]
    nuis = NUISANCES[params.nuisance]
    comfort = COMFORTS[params.comfort]
    world.facts.update(child=child, caregiver=caregiver, bed=bed, nuisance=nuis, comfort=comfort)
    bedtime_story(world, bed, nuis, comfort, child, caregiver)
    world.para()
    soothe(world, child, caregiver, comfort, bed)
    world.facts.update(outcome="calm")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child that includes the words "{f["nuisance"].label}" and "bear", and ends with a calm rhyme.',
        f'Tell a cozy story where {f["child"].id} makes a sleepy groan, then a grown-up helps with {f["comfort"].label}.',
        f'Write a gentle bedtime story in a soft rhyming style, with a bear, a groan, and a peaceful ending image.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    bed = f["bed"]
    nuis = f["nuisance"]
    comfort = f["comfort"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, a sleepy little bear, and {caregiver.id}, who comes to help at bedtime."),
        ("Why did the bear groan?",
         f"{child.id} groaned because bedtime felt hard and the room had a noisy little {nuis.label}. The sound made it tougher to settle down at first."),
        ("How did the grown-up help?",
         f"{caregiver.id} brought {comfort.phrase} and tucked it close so the room felt softer. Then {caregiver.id} gave a calm reminder that matched {bed.rhyme}."),
        ("How did the story end?",
         f"It ended with {bed.ending_image}. The bear was calm and ready for sleep instead of making more groans."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["nuisance"].tags) | set(f["comfort"].tags) | set(f["bed"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


BEDS = {
    "crib": Bedtime("crib", "a tiny crib room", "A bear can bare a sigh, then dream and fly.", "hushes", "a soft song can turn the groan into a yawn", "the bear settled like a quilted cloud", {"bed"}),
    "nest": Bedtime("nest", "a cozy nest room", "A bear can bear the night if stars are near and bright.", "whispers", "a small rhyme can tuck the wobble away", "the bear curled in a moonlit nest", {"bed"}),
    "cabin": Bedtime("cabin", "a pine-scented cabin", "A bear can bear the dark when the warm lamp softly sparks.", "murmurs", "a gentle rhyme and a hug can do the trick", "the bear slept while pine shadows rocked", {"bed"}),
}

NUISANCES = {
    "wind": Nuisance("wind", "wind", "whooosh", "wind", {"noise"}),
    "floor": Nuisance("floor", "floorboard groan", "groan", "floorboard groan", {"noise"}),
    "door": Nuisance("door", "door groan", "groan", "door groan", {"noise"}),
}

COMFORTS = {
    "blanket": Comfort("blanket", "blanket", "a blanket", "a warm, woolly glow", {"blanket"}),
    "pillow": Comfort("pillow", "pillow", "a pillow", "a moonlike glow", {"pillow"}),
    "lamp": Comfort("lamp", "lamp", "a little lamp", "a honey-gold glow", {"lamp"}),
}

KNOWLEDGE = {
    "noise": [("What is a groan?",
               "A groan is a low, drawn-out sound people or animals make when they feel tired, grumpy, or uncomfortable.")],
    "bear": [("What is a bear?",
              "A bear is a big furry animal. In stories, bears can be gentle, sleepy, and cuddly too.")],
    "blanket": [("What does a blanket do at bedtime?",
                 "A blanket helps keep a child warm and snug, which can make falling asleep easier.")],
    "pillow": [("What is a pillow for?",
                "A pillow is something soft you rest your head on while sleeping.")],
    "lamp": [("Why can a lamp help at bedtime?",
               "A lamp gives a gentle light, so the room feels safe and calm without being too bright.")],
    "bed": [("Why do bedtime stories feel soothing?",
             "Bedtime stories often use slow, gentle words and a peaceful ending, which helps the mind settle down.")],
}
KNOWLEDGE_ORDER = ["bear", "noise", "blanket", "pillow", "lamp", "bed"]


@dataclass
class StoryParams:
    bed: str
    nuisance: str
    comfort: str
    child_name: str
    child_type: str
    caregiver_type: str
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


def explain_rejection(nuisance: Nuisance, comfort: Comfort) -> str:
    if not nuisance.noisy:
        return "(No story: the bedtime nuisance must be something noisy enough to hear.)"
    if not comfort.soft:
        return "(No story: the comfort item must be gentle and soothing.)"
    return "(No story: this combination does not fit the bedtime rhyme world.)"


def valid_combo_check(params: StoryParams) -> bool:
    return params.bed in BEDS and params.nuisance in NUISANCES and params.comfort in COMFORTS


def asp_facts() -> str:
    import asp
    lines = []
    for bid in BEDS:
        lines.append(asp.fact("bed", bid))
    for nid, n in NUISANCES.items():
        lines.append(asp.fact("nuisance", nid))
        if True:
            lines.append(asp.fact("noisy", nid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("soft", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(B,N,C) :- bed(B), nuisance(N), comfort(C), noisy(N), soft(C).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only in asp:", sorted(a - b))
        print("only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(bed=None, nuisance=None, comfort=None, child_name=None, child_type=None, caregiver_type=None), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime rhyme storyworld: a bear, a groan, and a calm ending.")
    ap.add_argument("--bed", choices=BEDS)
    ap.add_argument("--nuisance", choices=NUISANCES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["bear"])
    ap.add_argument("--caregiver-type", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid bedtime combinations.)")
    if args.bed and args.bed not in BEDS:
        raise StoryError("Unknown bed choice.")
    if args.nuisance and args.nuisance not in NUISANCES:
        raise StoryError("Unknown nuisance choice.")
    if args.comfort and args.comfort not in COMFORTS:
        raise StoryError("Unknown comfort choice.")
    combos = [c for c in combos if (args.bed is None or c[0] == args.bed)
              and (args.nuisance is None or c[1] == args.nuisance)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    bed, nuisance, comfort = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Bram", "Milo", "Teddy", "Blue", "Pip", "Cubby"])
    child_type = args.child_type or "bear"
    caregiver_type = args.caregiver_type or rng.choice(["mother", "father"])
    return StoryParams(bed, nuisance, comfort, name, child_type, caregiver_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible bedtime combos:")
        for b, n, c in asp_valid_combos():
            print(f"  {b:6} {n:12} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(b, n, c, "Bram", "bear", "mother")) for b, n, c in valid_combos()[:5]]
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
