#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/despise_magic_rhyming_story.py
==============================================================

A standalone story world for a tiny rhyming tale about a child who *despises*
a messy bit of magic, then learns to use it kindly and safely.

Premise
-------
A child is annoyed by a magic trick that keeps causing the wrong kind of sparkle.
A patient helper shows how to do the trick in a better way, and the child ends up
using the same magic for a sweet final surprise.

This world keeps the simulation small:
- typed entities with meters and memes
- a causal turn when magic misfires
- a gentle correction beat
- a rhyme-forward renderer that still reads like a complete story
- three QA sets grounded in world state, not by parsing the rendered story
- an inline ASP twin plus Python reasonableness gate

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/despise_magic_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/despise_magic_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/despise_magic_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/despise_magic_rhyming_story.py --verify
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
    rhyme_end: str
    light: str
    helper_note: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class MagicItem:
    id: str
    label: str
    phrase: str
    spark_kind: str
    rhyme_end: str
    makes_glow: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Trouble:
    id: str
    label: str
    phrase: str
    gets_spoiled_by: str
    rhyme_end: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Fix:
    id: str
    sense: int
    power: int
    line: str
    fail: str
    qa_line: str
    rhyme_end: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    if world.get("trouble").meters["glitter"] < THRESHOLD:
        return out
    if ("spark", "trouble") in world.fired:
        return out
    world.fired.add(("spark", "trouble"))
    world.get("trouble").meters["spoiled"] += 1
    world.get("child").memes["frustration"] += 1
    world.get("helper").memes["concern"] += 1
    out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("spark", "physical", _r_spark)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combo(setting: Setting, magic: MagicItem, trouble: Trouble) -> bool:
    return magic.makes_glow and trouble.fragile and magic.rhyme_end == trouble.rhyme_end


def reasonableness_gate() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MAGIC.items():
            for tid, t in TROUBLES.items():
                if valid_combo(s, m, t):
                    out.append((sid, mid, tid))
    return sorted(out)


def is_saved(fix: Fix, trouble: Trouble, delay: int) -> bool:
    return fix.power >= (2 + delay if trouble.fragile else 1 + delay)


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    _do_magic(sim, narrate=False)
    return {
        "spoiled": sim.get("trouble").meters["spoiled"] >= THRESHOLD,
        "frustration": sim.get("child").memes["frustration"],
    }


def _do_magic(world: World, narrate: bool = True) -> None:
    trouble = world.get("trouble")
    trouble.meters["glitter"] += 1
    trouble.meters["wobble"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, setting: Setting, magic: MagicItem, trouble: Trouble) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a breezy day in {setting.place}, {child.id} found a little magic that loved to rhyme. "
        f"{setting.helper_note}"
    )
    world.say(
        f"{child.id} could make a sparkly trick with {magic.label}, but the trick was sloppy and not too fine. "
        f"{helper.id} smiled, and the day began to chime."
    )
    world.say(
        f'{child.id} frowned at the {trouble.label} and sighed, "I despise this mess," with a tiny grimace in rhyme.'
    )


def want_and_warn(world: World, child: Entity, helper: Entity, magic: MagicItem, trouble: Trouble) -> None:
    pred = predict_mishap(world)
    child.memes["despise"] += 1
    helper.memes["care"] += 1
    world.facts["pred"] = pred
    world.say(
        f'"Please be kind with that {magic.label}," {helper.id} said, "or {trouble.label} may lose its shine. '
        f'This magic should dance, not spill and twine."'
    )


def misfire(world: World, magic: MagicItem, trouble: Trouble) -> None:
    world.say(
        f"{magic.phrase} flickered once, then twice, then went askew in a line. "
        f"It brushed the {trouble.label}, and sparkles jumped like little fish in brine."
    )
    _do_magic(world)


def alarm(world: World, child: Entity, helper: Entity, trouble: Trouble) -> None:
    world.say(
        f'"Oh no!" cried {child.id}. "The {trouble.label} is glowing wrong -- this is not divine!"'
    )
    world.say(f'"Come here," said {helper.id}, "and let us fix it in time."')


def fix_it(world: World, helper: Entity, fix: Fix, trouble: Trouble) -> None:
    trouble.meters["spoiled"] = 0.0
    world.say(
        f"{helper.id} brought out {fix.line}, and the wobble settled down. "
        f"The stray spark dimmed into a neat, soft crown."
    )


def lesson(world: World, child: Entity, helper: Entity, magic: MagicItem) -> None:
    child.memes["joy"] += 1
    child.memes["despise"] = 0.0
    child.memes["lesson"] += 1
    world.say(
        f"Then {helper.id} grinned and said, \"A magic trick can wobble, yet still be kind and bright. "
        f"Try again with care, and make the rhythm right.\""
    )
    world.say(
        f'{child.id} nodded, then learned the tune, and the sparkly spell felt light.'
    )


def ending(world: World, child: Entity, magic: MagicItem, trouble: Trouble) -> None:
    world.say(
        f"At the end, {child.id} used {magic.phrase} to make tiny stars in the air. "
        f"The {trouble.label} stayed neat and shiny, and the room glowed warm and fair."
    )


def tell(setting: Setting, magic: MagicItem, trouble: Trouble, fix: Fix,
         child_name: str = "Maya", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    tr = world.add(Entity(id="trouble", type="thing", label=trouble.label))
    _ = world.add(Entity(id="magic", type="thing", label=magic.label))

    opening(world, child, helper, setting, magic, trouble)
    world.para()
    want_and_warn(world, child, helper, magic, trouble)
    world.say(f"The little room felt tense, but the rhyme kept time.")

    world.para()
    misfire(world, magic, trouble)
    alarm(world, child, helper, trouble)

    world.para()
    fix_it(world, helper, fix, trouble)
    lesson(world, child, helper, magic)
    ending(world, child, magic, trouble)

    world.facts.update(
        child=child, helper=helper, trouble=trouble, fix=fix, magic=magic,
        setting=setting, spoiled=tr.meters["spoiled"] >= THRESHOLD,
        frustration=child.memes["frustration"],
    )
    return world


SETTINGS = {
    "room": Setting("room", "the sunny room", "time", "A paper moon hung on the wall, and a toy drum sat in the corner.", "The helper kept a calm smile, like a bell at school-time."),
    "garden": Setting("garden", "the garden", "bloom", "A little bench waited by the flowers, and the wind smelled sweet as perfume.", "The helper knew a gentle trick and promised, \"We'll sort it out soon.\""),
    "porch": Setting("porch", "the porch", "glow", "A wooden step creaked softly, and lantern bugs blinked below.", "The helper had a steady hand and a patient, rhyming flow."),
}

MAGIC = {
    "wand": MagicItem("wand", "a silver wand", "the silver wand twirled with a shimmer and a spin", "spark", "time", True, {"magic", "spark"}),
    "glove": MagicItem("glove", "a magic glove", "the magic glove made glitter with a giggle and a grin", "glow", "bloom", True, {"magic", "glow"}),
    "bell": MagicItem("bell", "a tiny spell-bell", "the tiny spell-bell sang a twinkle-tune within", "ring", "glow", True, {"magic", "ring"}),
}

TROUBLES = {
    "cake": Trouble("cake", "birthday cake", "the birthday cake", "spark", "time", True, {"cake", "sweet"}),
    "cards": Trouble("cards", "paper cards", "the paper cards", "glow", "bloom", True, {"paper", "cards"}),
    "flowers": Trouble("flowers", "flower petals", "the flower petals", "ring", "glow", True, {"flowers", "petals"}),
}

FIXES = {
    "ribbon": Fix("ribbon", 3, 4, "a ribbon wand with a slower, kinder swirl", "a ribbon wand, but the spell was still too wild", "used a ribbon wand to slow the spell and make it gentle", "time"),
    "hum": Fix("hum", 2, 3, "a humming tune and a count of one, two, three", "tried a humming tune, but the magic stayed bumpy", "used a humming tune to steady the magic", "bloom"),
    "cup": Fix("cup", 3, 5, "a glass cup to catch each spark before it jumped away", "held up a glass cup, but the sparks still escaped", "caught the sparks before they could jump", "glow"),
}



@dataclass
class StoryParams:
    setting: str
    magic: str
    trouble: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    StoryParams("room", "wand", "cake", "ribbon", "Maya", "girl", "Grandma", "woman"),
    StoryParams("garden", "glove", "flowers", "hum", "Leo", "boy", "Auntie", "woman"),
    StoryParams("porch", "bell", "cards", "cup", "Nina", "girl", "Dad", "man"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the word "despise" and the idea of magic gone wrong.',
        f"Tell a small rhyming story where {f['child'].id} despises a messy magic trick, then learns a safer way from {f['helper'].id}.",
        f'Write a gentle magic rhyme that starts with frustration and ends with a bright, kinder sparkle.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    trouble = f["trouble"]
    magic = f["magic"]
    fix = f["fix"]
    return [
        ("Who was the story about?",
         f"It was about {child.id}, who did not like the messy magic at first. {helper.id} stayed close and helped make the spell kinder."),
        (f"Why did {child.id} despise the magic trick?",
         f"{child.id} despised it because the first try made {trouble.label} go wrong and look spoiled. That turned a fun trick into a messy surprise, so {child.id} frowned."),
        (f"How did the helper fix the problem?",
         f"{helper.id} used {fix.line} to steady the magic. That changed the spell from wild sparkles into a small, safe glow."),
        (f"How did the story end?",
         f"It ended with {child.id} using {magic.label} to make neat little stars. The {trouble.label} stayed shiny instead of spoiled, so the ending felt bright and calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does despise mean?",
         "Despise means to strongly dislike something. It is a very strong way to say you do not want it."),
        ("What is magic in a story?",
         "Magic in a story is something wondrous that can make unusual things happen. It often sparkles, surprises, or changes the world in a special way."),
        ("What can a helper do in a hard moment?",
         "A helper can stay calm, explain a better idea, and show a safer way. That can turn a problem into a happy fix."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return reasonableness_gate()


ASP_RULES = r"""
valid(S, M, T) :- setting(S), magic(M), trouble(T), makes_glow(M), fragile(T), same_rhyme(M, T).
same_rhyme(wand, cake).
same_rhyme(glove, flowers).
same_rhyme(bell, cards).

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
outcome(mended) :- chosen_fix(F), fix_power(F, P), delay(D), P >= 2 + D.
outcome(oops) :- chosen_fix(F), fix_power(F, P), delay(D), P < 2 + D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        if m.makes_glow:
            lines.append(asp.fact("makes_glow", mid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("fix_power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    ok = True
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid/3."))
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in gate.")
    # smoke test
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming magic storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.magic is None or c[1] == args.magic)
              and (args.trouble is None or c[2] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, magic, trouble = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(k for k, f in FIXES.items() if f.sense >= SENSE_MIN))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Maya", "Nina", "Leo", "Owen", "Luna", "Theo"])
    helper_name = args.helper_name or rng.choice(["Grandma", "Auntie", "Dad", "Mama", "Uncle Ray"])
    return StoryParams(setting, magic, trouble, fix, child_name, child_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MAGIC[params.magic], TROUBLES[params.trouble], FIXES[params.fix],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, m, t in combos:
            print(f"  {s:8} {m:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.magic} with {p.fix} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
