#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/banjo_happy_ending_sound_effects_kindness_fable.py
===================================================================================

A small Storyweavers storyworld: a fable-like tale about a child, a broken banjo,
kindness from a neighbor, and a happy ending with sound effects.

The world is intentionally tiny and constraint-driven:
- a banjo string snaps or a bridge loosens
- a child worries their song is ruined
- a kind helper suggests a gentle fix
- the repair succeeds, and the ending image proves the change

The story keeps a fable tone: concrete, simple, moral-leaning, and child-facing.
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
SOUND_WORDS = ["plink", "twang", "thrum", "tap-tap", "zing", "bop"]
KIND_HELPERS = ["neighbor", "grandpa", "grandma", "teacher", "friend"]
TONE_TRAITS = ["kind", "gentle", "patient", "helpful", "soft-spoken"]


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
        female = {"girl", "mother", "mom", "woman", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandpa", "uncle"}
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
class Banjo:
    id: str
    label: str
    sound: str
    fixable: bool = True
    strings: int = 5
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class TinyFix:
    id: str
    label: str
    action: str
    sound: str
    power: int
    sense: int
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
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["broken"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_sad_sound(world: World) -> list[str]:
    out: list[str] = []
    if world.get("banjo").meters["broken"] < THRESHOLD:
        return out
    sig = ("silence", "banjo")
    if sig not in world.fired:
        world.fired.add(sig)
        out.append("__silence__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("silence", _r_sad_sound)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predictable_fix(fix: TinyFix, banjo: Banjo) -> bool:
    return fix.power >= 1 and fix.sense >= 2 and banjo.fixable


def sensible_fixes() -> list[TinyFix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for story in STORIES:
        for fix_id, fix in FIXES.items():
            if fix.sense >= 2 and STORY_TO_BANJO[story].fixable and fix.power >= 1:
                combos.append((story, fix_id))
    return combos


@dataclass
class StoryParams:
    story: str
    fix: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    broken_part: str = "string"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable about a banjo, kindness, and a happy ending.")
    ap.add_argument("--story", choices=STORIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=KIND_HELPERS)
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father", "grandma", "grandpa", "neighbor", "teacher", "friend"])
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
    combos = [c for c in valid_combos()
              if (args.story is None or c[0] == args.story)
              and (args.fix is None or c[1] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    story, fix = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "mother", "father", "grandma", "grandpa", "neighbor", "teacher", "friend"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(KIND_HELPERS)
    return StoryParams(story=story, fix=fix, child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper", traits=["kind"]))
    banjo_cfg = STORY_TO_BANJO[params.story]
    banjo = world.add(Entity(id="banjo", kind="thing", type="banjo", label="banjo"))
    banjo.meters["broken"] = 1.0
    child.memes["sad"] += 1
    child.memes["hope"] += 0.5
    world.say(
        f"{child.id} loved the little banjo because it could sing bright songs. "
        f"One afternoon, {banjo_cfg.sound} -- and then {banjo.label_word} fell quiet."
    )
    world.say(
        f'"Oh no," {child.id} whispered. "My {banjo.label_word}!" '
        f'The room felt suddenly still, as if even the chair was listening.'
    )
    world.para()
    world.say(
        f"Then {helper.id}, a {helper.traits[0]} {helper.label_word}, came by with a warm smile."
    )
    world.say(
        f'"Let us be gentle," {helper.id} said. "{FIXES[params.fix].action.capitalize()}." '
        f'{FIXES[params.fix].sound.capitalize()} answered the workbench.'
    )
    apply_fix(world, child, helper, banjo_cfg, FIXES[params.fix])
    world.para()
    ending(world, child, helper, banjo_cfg)
    world.facts.update(child=child, helper=helper, banjo_cfg=banjo_cfg, fix=FIXES[params.fix], outcome="happy")
    return world


def apply_fix(world: World, child: Entity, helper: Entity, banjo: Entity, fix: TinyFix) -> None:
    if not predictable_fix(fix, STORY_TO_BANJO[world.facts.get("story", "market")] if False else BANJO_ITEM):
        raise StoryError("The chosen fix is not reasonable for this banjo.")
    world.get("banjo").meters["broken"] = 0.0
    world.get("banjo").meters["repaired"] = 1.0
    child.memes["sad"] = 0.0
    child.memes["joy"] += 2
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} tightened the loose part and {fix.action}. {fix.sound.capitalize()}!"
    )
    world.say(
        f"The banjo answered with a happy {STORY_TO_BANJO[world.facts.get('story', 'market')].sound}."
    )


def ending(world: World, child: Entity, helper: Entity, banjo: Banjo) -> None:
    world.say(
        f"{child.id} hugged the banjo and played a clean little tune. "
        f"{banjo.sound.capitalize()}, {banjo.sound}, {banjo.sound} -- and the song came back."
    )
    world.say(
        f"The kind helper smiled, and {child.id} learned that gentle hands can mend what worry breaks."
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable for a child about a banjo that goes quiet, kindness that helps, and a happy ending.',
        f"Tell a gentle story where {world.facts['child'].id if world.facts else 'a child'} worries about a banjo, then a kind helper fixes it with care.",
        'Write a simple story that includes the word "banjo" and a few sound effects, ending with kindness and music.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    fix = world.facts["fix"]
    qa = [
        ("What went wrong at the start?",
         f"The banjo went quiet because one part broke, and that made {child.id} sad. The silence was the problem that needed a gentle fix."),
        ("Who helped, and how?",
         f"{helper.id} helped by being patient and {fix.action}. That kindness made the repair feel safe and calm."),
        ("How did the story end?",
         f"It ended happily, with {child.id} playing the banjo again and smiling. The music came back, so the ending felt bright and warm."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a banjo?",
         "A banjo is a string instrument that makes a bright, twangy sound when someone plucks it."),
        ("Why are sound effects in a story fun?",
         "Sound effects help you hear the action in your mind. They make a story feel lively and close."),
        ("What does kindness mean?",
         "Kindness means helping with care, using gentle words, and trying to make someone feel better."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in STORIES:
        lines.append(asp.fact("story", sid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(S, F) :- story(S), fix(F), sensible(F), power(F, P), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python valid-combos match ({len(valid_combos())} combos).")
    sample = generate(CURATED[0])
    if not sample.story or "banjo" not in sample.story.lower():
        print("MISMATCH: smoke test failed.")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


STORIES = ["market", "porch", "village"]
BANJO_ITEM = Banjo(id="banjo", label="banjo", sound="twang")
STORY_TO_BANJO = {
    "market": BANJO_ITEM,
    "porch": Banjo(id="banjo", label="banjo", sound="plink"),
    "village": Banjo(id="banjo", label="banjo", sound="thrum"),
}
FIXES = {
    "tune": TinyFix(id="tune", label="new tuning", action="tuned the strings", sound="plink-plink", power=1, sense=3),
    "glue": TinyFix(id="glue", label="wood glue", action="glued the loose bridge", sound="squish", power=2, sense=3),
    "string": TinyFix(id="string", label="spare string", action="replaced the broken string", sound="zing", power=2, sense=3),
}
GIRL_NAMES = ["Lila", "Mina", "Tia", "Nora", "Ivy", "Sage"]
BOY_NAMES = ["Bram", "Owen", "Leo", "Milo", "Noah", "Eli"]


CURATED = [
    StoryParams(story="market", fix="tune", child="Lila", child_type="girl", helper="grandpa", helper_type="grandpa"),
    StoryParams(story="porch", fix="glue", child="Bram", child_type="boy", helper="neighbor", helper_type="neighbor"),
    StoryParams(story="village", fix="string", child="Mina", child_type="girl", helper="teacher", helper_type="teacher"),
]


def generate(params: StoryParams) -> StorySample:
    if params.story not in STORIES or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    story = args.story or rng.choice(STORIES)
    fix = args.fix or rng.choice(sorted(FIXES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["grandpa", "grandma", "neighbor", "teacher", "friend", "mother", "father"])
    helper = args.helper or rng.choice(KIND_HELPERS)
    return StoryParams(story=story, fix=fix, child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Banjo fable storyworld.")
    ap.add_argument("--story", choices=STORIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=KIND_HELPERS)
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father", "grandma", "grandpa", "neighbor", "teacher", "friend"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        print(f"valid combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
