#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lean_patch_repetition_bravery_inner_monologue_nursery.py
=========================================================================================

A tiny nursery-rhyme storyworld about a child, a little tear, a brave decision,
and a patch that makes things right again.

Seed words:
- lean
- patch

Features:
- Repetition
- Bravery
- Inner Monologue

Style:
- Nursery Rhyme
"""

from __future__ import annotations

import argparse
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class PatchKit:
    id: str
    label: str
    material: str
    fix_verb: str
    glow: str
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
class Fault:
    id: str
    label: str
    tear_word: str
    tiny_sound: str
    risky: bool = True
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
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    fault: str
    patchkit: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World()
        w.entities = {k: Entity(**{**v.__dict__, "attrs": dict(v.attrs), "meters": defaultdict(float, v.meters), "memes": defaultdict(float, v.memes)}) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_patch(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["torn"] < THRESHOLD:
            continue
        sig = ("patch", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["mended"] = 1.0
        out.append("__mended__")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["fear"] >= THRESHOLD and hero.memes["brave_try"] < THRESHOLD:
        sig = ("bravery", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["brave_try"] += 1
            out.append("__brave__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    lines: list[str] = []
    while changed:
        changed = False
        for fn in (_r_bravery, _r_patch):
            bits = fn(world)
            if bits:
                changed = True
                for b in bits:
                    if not b.startswith("__"):
                        lines.append(b)
    if narrate:
        for line in lines:
            world.say(line)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about brave patching.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--patchkit", choices=PATCHKITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


HEROES = {
    "Milo": {"gender": "boy"},
    "Nina": {"gender": "girl"},
    "Toby": {"gender": "boy"},
    "Luna": {"gender": "girl"},
}
HELPERS = {
    "Pip": {"gender": "boy"},
    "Wren": {"gender": "girl"},
    "Bea": {"gender": "girl"},
    "Finn": {"gender": "boy"},
}
FAULTS = {
    "kite": Fault(id="kite", label="kite", tear_word="tear", tiny_sound="flap-flap", tags={"kite", "wind"}),
    "blanket": Fault(id="blanket", label="blanket", tear_word="patch", tiny_sound="flutter-flutter", tags={"blanket", "cloth"}),
}
PATCHKITS = {
    "gold_patch": PatchKit(id="gold_patch", label="a gold patch", material="gold cloth", fix_verb="patched", glow="glowed like a little moon", tags={"patch"}),
    "red_patch": PatchKit(id="red_patch", label="a red patch", material="red cloth", fix_verb="patched", glow="glowed like a berry", tags={"patch"}),
}

CURATED = [
    StoryParams(hero="Milo", hero_gender="boy", helper="Wren", helper_gender="girl", fault="kite", patchkit="gold_patch"),
    StoryParams(hero="Nina", hero_gender="girl", helper="Pip", helper_gender="boy", fault="blanket", patchkit="red_patch"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HEROES:
        for he in HELPERS:
            for f in FAULTS:
                for p in PATCHKITS:
                    combos.append((h, he, f))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for f in FAULTS:
        lines.append(asp.fact("fault", f))
    for p in PATCHKITS:
        lines.append(asp.fact("patchkit", p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, He, F) :- hero(H), helper(He), fault(F).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    ok = clingo_set == python_set
    smoke = generate(resolve_params(build_parser().parse_args([]), random.Random(1))).story
    if ok and smoke:
        print(f"OK: ASP matches Python and smoke test passed ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH or smoke failure.")
    if clingo_set != python_set:
        print("only clingo:", sorted(clingo_set - python_set))
        print("only python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted([k for k in HELPERS if k != hero]))
    fault = args.fault or rng.choice(sorted(FAULTS))
    patchkit = args.patchkit or rng.choice(sorted(PATCHKITS))
    return StoryParams(
        hero=hero,
        hero_gender=HEROES[hero]["gender"],
        helper=helper,
        helper_gender=HELPERS[helper]["gender"],
        fault=fault,
        patchkit=patchkit,
    )


def _story_setup(world: World, p: StoryParams) -> None:
    hero = world.add(Entity(id="hero", kind="character", type=p.hero_gender, role="hero", label=p.hero))
    helper = world.add(Entity(id="helper", kind="character", type=p.helper_gender, role="helper", label=p.helper))
    fault = world.add(Entity(id="fault", kind="thing", type="thing", label=FAULTS[p.fault].label))
    kit = world.add(Entity(id="patchkit", kind="thing", type="thing", label=PATCHKITS[p.patchkit].label))
    hero.memes["brave"] = 0.0
    hero.memes["fear"] = 1.0
    fault.meters["torn"] = 1.0
    world.facts.update(hero=hero, helper=helper, fault=fault, kit=kit, params=p)


def tell(world: World, p: StoryParams) -> None:
    h = world.get("hero")
    he = world.get("helper")
    fault = world.get("fault")
    kit = world.get("patchkit")
    fcfg = FAULTS[p.fault]
    kcfg = PATCHKITS[p.patchkit]

    world.say(f"Little {h.label} leaned, leaned, lean, by the window in the rain.")
    world.say(f"{he.label} came near and gave a grin. \"A patch can help again.\"")
    world.say(f"But {fault.label} had a tiny {fcfg.tear_word}. It went flap-flap in the breeze.")
    world.para()
    world.say(f"{h.label} thought, \"Oh dear, oh dear, what if the tear grows wide?\"")
    world.say(f"Then {h.label} thought, \"I can be brave. I can lean in, and try.\"")
    h.memes["brave"] += 1
    h.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(f"{h.label} took the {kit.label} and {kcfg.fix_verb} the little tear with care.")
    world.say(f"It {kcfg.glow}. The tiny wind stopped singing through the air.")
    world.para()
    world.say(f"\"Lean, lean, lean,\" sang {he.label}. \"Patch, patch, patch,\" sang {h.label}.")
    world.say(f"And there was the {fault.label}, snug and smart, all tidy, mended, and fair.")
    h.memes["fear"] = 0.0
    h.memes["joy"] += 1
    h.meters["mended"] = 1.0
    world.facts["outcome"] = "mended"


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a nursery-rhyme story with the words "lean" and "patch" about {p.hero} and a small tear.',
        f"Tell a brave little story where {p.hero} feels a worry, leans in anyway, and uses a patch to fix it.",
        f"Write a rhyme for children where a character says a quiet inner monologue, then acts bravely and patches something up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    h = world.facts["hero"]
    he = world.facts["helper"]
    fault = world.facts["fault"]
    kit = world.facts["kit"]
    return [
        ("Who is the story about?", f"It is about {h.label} and {he.label}, who watch a little {fault.label}."),
        ("What did {0} think before acting?".format(h.label), f"{h.label} worried the tear might grow, but then {h.pronoun()} chose to be brave. That quiet thought pushed {h.pronoun('object')} to lean in and try."),
        ("What fixed the problem?", f"The {kit.label} fixed it. {h.label} patched the tear carefully until it was snug again."),
        ("How did the story end?", f"It ended with the {fault.label} neat and mended, and everyone singing softly about lean and patch."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to patch something?", "To patch something means to mend a tear or hole with another piece of cloth or material."),
        ("What does brave mean?", "Brave means you do a hard or scary thing even when you feel a little afraid."),
        ("What is an inner monologue?", "An inner monologue is the quiet talk a person has inside their own head."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id}: {e.label or e.type} meters={meters} memes={memes}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES or params.helper not in HELPERS or params.fault not in FAULTS or params.patchkit not in PATCHKITS:
        raise StoryError("Unknown story parameter.")
    world = World()
    _story_setup(world, params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for combo in valid_combos():
            print("  ", combo)
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
