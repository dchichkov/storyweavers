#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chirp_transformation_inner_monologue_bedtime_story.py
=====================================================================================

A standalone story world for a tiny bedtime tale built from the seed word
"chirp" with two narrative instruments: transformation and inner monologue.

Premise:
- A sleepy child hears a small chirp at bedtime.
- The child thinks privately about whether the sound is lonely or just lost.
- The child and a parent choose a gentle, practical response.
- The little bird transforms from damp and wobbly into warm and settled, and
  the ending image proves the change.

This world is intentionally small and child-facing. It models a few entities,
their physical meters and emotional memes, a couple of forward causal rules,
three QA sets, and a declarative ASP twin for parity checks.
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
INNER_THRESHOLD = 1.0


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    dim: str
    quiet: str

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
class BirdKind:
    id: str
    label: str
    color: str
    chirp: str
    needs_warmth: bool = True
    can_transform: bool = True

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
    warmth: int

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

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


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    chick = world.entities.get("bird")
    if not chick:
        return out
    if chick.meters["warmth"] < THRESHOLD:
        return out
    sig = ("warmth_settled", chick.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chick.meters["settled"] += 1
    chick.memes["sleepy"] += 1
    out.append("__settled__")
    return out


def _r_transformation(world: World) -> list[str]:
    bird = world.entities.get("bird")
    if not bird:
        return []
    if bird.meters["settled"] < THRESHOLD:
        return []
    sig = ("transform", bird.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bird.meters["transformed"] += 1
    bird.label = "little bird"
    bird.attrs["form"] = "feathered"
    return ["__transform__"]


CAUSAL_RULES = [
    Rule("warmth", "physical", _r_warmth),
    Rule("transformation", "physical", _r_transformation),
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


def inner_voice(child: Entity, text: str) -> str:
    return f'{child.id} thought, "{text}"'


def gentle_help(world: World, child: Entity, parent: Entity, bird: Entity, comfort: Comfort) -> None:
    child.memes["care"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"At bedtime, {child.id} heard a tiny chirp from outside the window. "
        f"It came from a small wet bird on the sill, no bigger than a leaf."
    )
    world.say(inner_voice(child, "It sounds lonely. I should not ignore it."))
    world.say(
        f'{parent.label_word.capitalize()} came closer with {comfort.phrase}. '
        f'"We can help it be warm," {parent.pronoun()} said softly.'
    )


def move_inside(world: World, child: Entity, bird: Entity, comfort: Comfort) -> None:
    child.memes["hope"] += 1
    bird.meters["wetness"] += 1
    world.say(
        f"{child.id} lifted the tiny bird into a little box lined with {comfort.label}. "
        f"The bird gave one more chirp, then tucked its head under a wing."
    )


def warm_up(world: World, child: Entity, bird: Entity, comfort: Comfort) -> None:
    bird.meters["warmth"] += comfort.warmth
    bird.memes["safe"] += 1
    world.say(
        f"They set the box near the lamp, not too close, just warm enough. "
        f"{child.id} watched the feathers dry and whispered, "
        f'"You can rest now."'
    )
    propagate(world, narrate=False)


def change(world: World, bird_kind: BirdKind) -> None:
    bird = world.get("bird")
    if bird.meters["transformed"] >= THRESHOLD:
        world.say(
            f"The little bird changed from shivery and still into a bright, fluffy "
            f"{bird_kind.label}. Its eyes opened, and its chirp turned into a soft, "
            f"sleepy song."
        )


def ending(world: World, child: Entity, parent: Entity, bird_kind: BirdKind) -> None:
    world.say(
        f"Then {parent.label_word.capitalize()} turned off the bright lamp and left "
        f"just the moonlight. The {bird_kind.label} was warm, dry, and snuggled in "
        f"its nest of cloth."
    )
    world.say(
        f'{child.id} smiled sleepily. In the quiet room, the last little chirp '
        f'sounded happy, and {child.id} felt ready for dreams.'
    )


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "small", "quiet"),
    "attic": Setting("attic", "the attic room", "cozy", "hushed"),
    "nursery": Setting("nursery", "the nursery", "soft", "still"),
}

BIRDS = {
    "sparrow": BirdKind("sparrow", "sparrow", "brown", "chirp"),
    "wren": BirdKind("wren", "wren", "golden", "chirp"),
    "finch": BirdKind("finch", "finch", "red", "chirp"),
}

COMFORTS = {
    "blanket": Comfort("blanket", "blanket", "a blanket", 2),
    "scarf": Comfort("scarf", "scarf", "a soft scarf", 2),
    "towel": Comfort("towel", "towel", "a little towel", 2),
}

NAMES = ["Mina", "Lily", "Noah", "Ben", "Maya", "Zoe", "Theo", "Ava"]
TRAITS = ["gentle", "sleepy", "curious", "kind", "careful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    bird: str
    comfort: str
    child: str
    child_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BIRDS:
            for c in COMFORTS:
                combos.append((s, b, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world about a chirping bird and a gentle transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.bird and (args.setting not in SETTINGS or args.bird not in BIRDS):
        raise StoryError("Invalid setting or bird.")
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.bird in (None, c[1])
              and args.comfort in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bird, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, bird, comfort, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent"))
    bird_kind = BIRDS[params.bird]
    comfort = COMFORTS[params.comfort]
    bird = world.add(Entity(id="bird", kind="thing", type="bird", label=f"a tiny {bird_kind.label}", attrs={"kind": bird_kind.id}))
    world.say(
        f"{child.id} was already in bed when a tiny chirp reached the window."
    )
    gentle_help(world, child, parent, bird, comfort)
    world.para()
    move_inside(world, child, bird, comfort)
    warm_up(world, child, bird, comfort)
    change(world, bird_kind)
    world.para()
    ending(world, child, parent, bird_kind)
    world.facts.update(
        child=child, parent=parent, bird=bird, bird_kind=bird_kind, comfort=comfort,
        setting=world.setting, outcome="transformed", chirp=True
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "chirp" and a gentle transformation.',
        f"Tell a cozy story where {f['child'].id} hears a chirp, thinks about it in a private inner voice, and helps a little bird become warm and settled.",
        f"Write a soft bedtime story about a child and a parent helping a bird at the window, with a calm change at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, bird_kind, comfort = f["child"], f["parent"], f["bird_kind"], f["comfort"]
    return [
        ("What did the child hear at bedtime?",
         "The child heard a tiny chirp at the window. It turned out to come from a small wet bird that needed warmth."),
        ("What was the child thinking to themself?",
         f'{child.id} thought, "It sounds lonely. I should not ignore it." That thought helped {child.id} choose a gentle way to help.'),
        ("How did the child and parent help the bird?",
         f"They put it in a little box lined with {comfort.label} and kept it warm near the lamp. The safe warmth let the bird settle instead of shivering."),
        ("What changed by the end?",
         f"The bird transformed into a bright, fluffy {bird_kind.label}. Its chirp turned into a soft, sleepy song, which shows the change clearly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chirp?",
         "A chirp is a small, quick bird sound. Birds often chirp when they call to one another."),
        ("Why do birds need warmth?",
         "A small bird can get cold when it is wet or tired. Warmth helps it rest and dry its feathers."),
        ("What is a bedtime story?",
         "A bedtime story is a calm story told at night. It usually has gentle feelings and a soothing ending."),
        ("What is transformation?",
         "Transformation means something changes into a new form or state. In stories, it can show a character becoming different in a clear way."),
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
    lines.append("== (3) World knowledge ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
warm(chick) :- hears_chirp(chick), help(chick).
transform(bird) :- warm(bird), settled(bird).
outcome(transformed) :- transform(bird).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BIRDS:
        lines.append(asp.fact("bird_kind", bid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, bird=None, comfort=None, child=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    if set(valid_combos()) == set((s, b, c) for s in SETTINGS for b in BIRDS for c in COMFORTS):
        print("OK: valid_combos ok.")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    return rc


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
    StoryParams("bedroom", "sparrow", "blanket", "Mina", "girl", "mother"),
    StoryParams("nursery", "wren", "scarf", "Noah", "boy", "father"),
    StoryParams("attic", "finch", "towel", "Ava", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
