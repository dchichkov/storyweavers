#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fag_dinky_inner_monologue_rhyming_story.py
===========================================================================

A standalone storyworld for a tiny rhyming, inner-monologue story domain:
a small child wants to use a very dinky thing, thinks through the idea in
their head, gets guided by a calm caregiver, and ends with a safe, cheerful
replacement.

This world keeps the prose child-facing, state-driven, and lightly musical.
It models:
- a child entity with meters and memes,
- a small object and a larger/safer alternative,
- an inner-monologue turn that shows desire, worry, and choice,
- a simple resolution that proves what changed.

The seed words are preserved in the world vocabulary through a harmless
storybook-style title card and a toy label, while the story itself stays
gentle and concrete.
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
    age: int = 0
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
    mood: str
    afford: set[str] = field(default_factory=set)

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
class Toy:
    id: str
    label: str
    phrase: str
    tiny: bool = False
    noisy: bool = False
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
class Replacement:
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["want"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return out
    sig = ("nervous", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["tug"] += 1
    out.append("__tug__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["calm"] < THRESHOLD:
        return out
    sig = ("relief", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous), Rule("relief", _r_relief)]


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


def inner_voice(child: Entity, toy: Toy, replacement: Replacement, setting: Setting) -> str:
    return (
        f"I want the {toy.label}, the dinky little thing, "
        f"but {setting.mood} weather and a brave heart can still bring a smile. "
        f"Maybe the {replacement.label} will sing a kinder tune."
    )


def setup(world: World, child: Entity, caregiver: Entity, toy: Toy, setting: Setting) -> None:
    child.memes["want"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On a {setting.mood} day at {setting.place}, {child.id} found a {toy.label}."
    )
    world.say(
        f"{child.id} held it up and listened to a tiny thought inside: "
        f'"It is so {toy.id}, so small, so neat."'
    )


def temptation(world: World, child: Entity, caregiver: Entity, toy: Toy) -> None:
    child.memes["want"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} wanted to play with the {toy.label} by the window."
    )
    world.say(
        f'Inside {child.pronoun("possessive")} head, a soft rhyme began: '
        f'"I want a little bit of glitter, I want a little bit of cheer, '
        f'but maybe this is not the place to keep it near."'
    )
    world.say(
        f'{caregiver.id} looked up and said, "{child.id}, what are you thinking?"'
    )


def warn(world: World, caregiver: Entity, child: Entity, toy: Toy) -> None:
    world.say(
        f'{caregiver.id} smiled kindly. "{toy.label.capitalize()} is so tiny, '
        f'but not every tiny thing belongs on the sill. Let us choose a safer thrill."'
    )


def choose_safe(world: World, child: Entity, caregiver: Entity, replacement: Replacement) -> None:
    child.memes["calm"] += 1
    child.memes["want"] = 0
    world.say(
        f"{child.id} listened, and the wiggly wish got small."
    )
    world.say(
        f'In {child.pronoun("possessive")} head came another line: '
        f'"A safer choice can still be fun; a gentle glow can light the sun."'
    )
    world.say(
        f"{caregiver.id} brought out {replacement.phrase}, and it {replacement.glow}."
    )
    world.say(
        f"{child.id} smiled at the bright new play and kept the dinky toy put away."
    )


def tell(setting: Setting, toy: Toy, replacement: Replacement,
         child_name: str = "Mia", child_gender: str = "girl",
         caregiver_name: str = "Mom", caregiver_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    caregiver = world.add(Entity(id=caregiver_name, kind="character", type=caregiver_gender, role="caregiver"))
    item = world.add(Entity(id="toy", type="thing", label=toy.label))
    lamp = world.add(Entity(id="replacement", type="thing", label=replacement.label))

    setup(world, child, caregiver, toy, setting)
    world.para()
    temptation(world, child, caregiver, toy)
    warn(world, caregiver, child, toy)
    propagate(world, narrate=False)
    world.para()
    choose_safe(world, child, caregiver, replacement)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        toy_cfg=toy,
        replacement_cfg=replacement,
        setting=setting,
        toy=item,
        replacement=lamp,
        voice=inner_voice(child, toy, replacement, setting),
    )
    return world


SETTINGS = {
    "window": Setting("window", "the sunny window", "bright", {"toy", "replacement"}),
    "table": Setting("table", "the kitchen table", "cozy", {"toy", "replacement"}),
    "porch": Setting("porch", "the porch", "breezy", {"toy", "replacement"}),
}

TOYS = {
    "dinky_car": Toy("dinky", "dinky toy car", "dinky", tiny=True, tags={"dinky", "tiny"}),
    "fag_flag": Toy("fag", "fag-shaped paper flag", "fag", tiny=True, tags={"fag", "flag"}),
    "dinky_box": Toy("dinky_box", "dinky puzzle box", "dinky", tiny=True, tags={"dinky", "tiny"}),
}

REPLACEMENTS = {
    "lantern": Replacement("lantern", "little lantern", "a little lantern", "glowed warm and steady", tags={"light"}),
    "glowball": Replacement("glowball", "glow ball", "a glow ball", "glowed like a moon", tags={"light"}),
    "storylight": Replacement("storylight", "storybook lamp", "a storybook lamp", "shone soft and kind", tags={"light"}),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Pia"],
    "boy": ["Noah", "Theo", "Eli", "Finn"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOYS:
            for r in REPLACEMENTS:
                combos.append((s, t, r))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    toy: str
    replacement: str
    child_name: str
    child_gender: str
    caregiver_name: str
    caregiver_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child that includes the words "{f["toy_cfg"].label}" and "{f["replacement_cfg"].label}".',
        f"Tell an inner-monologue story where {f['child'].id} wants the {f['toy_cfg'].label} but chooses a safer light instead.",
        f"Write a gentle rhyming story set at {f['setting'].place} where a child thinks aloud in their head and ends happy and calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    toy = f["toy_cfg"]
    repl = f["replacement_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question="What did the child want at first?",
            answer=f"{child.id} wanted the {toy.label}, because it looked tiny and fun. But the child also worried it might not be the best thing to play with near the window.",
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{caregiver.id} answered with a calm rhyme and offered {repl.phrase} instead. That gave {child.id} a safer choice that still felt special.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{child.id} kept the dinky toy put away and chose the new light instead. The ending is bright and quiet, with happy play at {setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dinky mean?",
            answer="Dinky means very small and neat. People use it for something tiny in a cute way.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice in your head that says what you think and feel. It is like silent talking inside yourself.",
        ),
        QAItem(
            question="What makes a rhyme?",
            answer="A rhyme is when words sound alike at the end. Rhymes can make a story feel bouncy and fun.",
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
    lines.append("== (3) World knowledge questions ==")
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
    return "\n".join(lines)


CURATED = [
    StoryParams("window", "dinky_car", "lantern", "Mia", "girl", "Mom", "mother"),
    StoryParams("table", "fag_flag", "storylight", "Noah", "boy", "Dad", "father"),
    StoryParams("porch", "dinky_box", "glowball", "Luna", "girl", "Mom", "mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming inner-monologue story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--replacement", choices=REPLACEMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["Mom", "Dad"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    toy = args.toy or rng.choice(list(TOYS))
    replacement = args.replacement or rng.choice(list(REPLACEMENTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    caregiver = args.caregiver or rng.choice(["Mom", "Dad"])
    caregiver_gender = "mother" if caregiver == "Mom" else "father"
    return StoryParams(setting, toy, replacement, name, gender, caregiver, caregiver_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TOYS[params.toy],
        REPLACEMENTS[params.replacement],
        params.child_name,
        params.child_gender,
        params.caregiver_name,
        params.caregiver_gender,
    )
    story = (
        f"{params.child_name} had a dinky little thought and a gentle rhyme in mind.\n\n"
        f"{world.render()}"
    )
    return StorySample(
        params=params,
        story=story,
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
valid(S, T, R) :- setting(S), toy(T), replacement(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    for rid in REPLACEMENTS:
        lines.append(asp.fact("replacement", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def explain_rejection() -> str:
    return "(No story: this world does not use a restrictive compatibility gate.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
