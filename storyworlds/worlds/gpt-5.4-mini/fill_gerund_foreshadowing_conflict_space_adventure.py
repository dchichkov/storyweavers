#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fill_gerund_foreshadowing_conflict_space_adventure.py
====================================================================================

A small space-adventure storyworld with foreshadowing and conflict.

Premise:
- A child crew prepares a tiny rover or ship for a moon hop.
- A warning sign foreshadows trouble: something is low, loose, or cracked.
- The child ignores or notices it, conflict rises, and a calm helper fixes it.
- The ending shows the crew safely continuing their adventure.

The seed words ask for "fill-gerund"; this world uses phrases like
"filling the fuel tank", "filling the water pack", and "filling the map
scanner" as part of the narrated action.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    sky: str
    vibe: str
    travel: str
    launch_word: str
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
class Hazard:
    id: str
    label: str
    cue: str
    risk: str
    kind: str
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
class Fix:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    sense: int
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTING_REGISTRY = {
    "orbital_station": Setting(
        "orbital_station",
        "the little orbital station",
        "clear and black",
        "busy and bright",
        "dock",
        "launch",
        tags={"space", "station"},
    ),
    "moon_base": Setting(
        "moon_base",
        "the moon base",
        "silver and quiet",
        "echoing and chilly",
        "rover",
        "roll out",
        tags={"space", "moon"},
    ),
}

HAZARD_REGISTRY = {
    "low_fuel": Hazard(
        "low_fuel",
        "low fuel",
        "the fuel gauge blinking red",
        "the ship could stop far from home",
        "fuel",
        tags={"fuel", "warning"},
    ),
    "cracked_window": Hazard(
        "cracked_window",
        "a cracked window",
        "a tiny crack in the glass",
        "air could leak out",
        "window",
        tags={"window", "warning"},
    ),
    "stuck_hatch": Hazard(
        "stuck_hatch",
        "a stuck hatch",
        "the hatch handle sticking",
        "the door might not open later",
        "hatch",
        tags={"hatch", "warning"},
    ),
}

FIX_REGISTRY = {
    "fill_tank": Fix(
        "fill_tank",
        "the fuel tank",
        "filling the fuel tank",
        "the ship had enough power",
        power=3,
        sense=3,
        tags={"fuel", "fix"},
    ),
    "patch_window": Fix(
        "patch_window",
        "the window patch kit",
        "patching the crack with a clear kit",
        "the air stayed inside",
        power=4,
        sense=3,
        tags={"window", "fix"},
    ),
    "oil_hatch": Fix(
        "oil_hatch",
        "the hatch oil",
        "oiling the hatch carefully",
        "the door slid open again",
        power=2,
        sense=2,
        tags={"hatch", "fix"},
    ),
    "fill_water_pack": Fix(
        "fill_water_pack",
        "the water pack",
        "filling the water pack first",
        "they stayed calm and hydrated",
        power=1,
        sense=1,
        tags={"water", "weak"},
    ),
}

CHILD_NAMES = ["Mia", "Nia", "Zoe", "Ava", "Leo", "Sam", "Tari", "Nova"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["brave", "curious", "careful", "bold", "inventive"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
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
    for sid, setting in SETTING_REGISTRY.items():
        for hid, hazard in HAZARD_REGISTRY.items():
            for fid, fix in FIX_REGISTRY.items():
                if hazard.id == "low_fuel" and fix.id == "fill_tank":
                    combos.append((sid, hid, fid))
                elif hazard.id == "cracked_window" and fix.id == "patch_window":
                    combos.append((sid, hid, fid))
                elif hazard.id == "stuck_hatch" and fix.id == "oil_hatch":
                    combos.append((sid, hid, fid))
    return combos


def sensible_fixes() -> list[Fix]:
    return [f for f in FIX_REGISTRY.values() if f.sense >= SENSE_MIN]


def explain_rejection(hazard: Hazard, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not honestly solve {hazard.label}. "
        f"Pick the matching fix for that problem.)"
    )


def explain_fix(fid: str) -> str:
    f = FIX_REGISTRY[fid]
    better = ", ".join(x.id for x in sensible_fixes())
    return f"(Refusing fix '{fid}': sense={f.sense} < {SENSE_MIN}. Try: {better}.)"


def predicted_risk(hazard: Hazard) -> str:
    return hazard.risk


def _spread_conflict(world: World) -> list[str]:
    out = []
    crew = world.get("child")
    if crew.memes["worry"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            crew.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _spread_conflict(world):
            changed = True
            if not s.startswith("__"):
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def preview_fix(world: World, hazard: Hazard, fix: Fix) -> bool:
    sim = world.copy()
    sim.get("hazard").meters["risk"] += 1
    sim.get("child").memes["worry"] += 1
    return fix.power >= 2


def setup(world: World, setting: Setting, child: Entity, helper: Entity) -> None:
    world.say(
        f"In {setting.place}, {child.id} and {helper.id} were getting ready for a small space adventure. "
        f"{setting.sky} was above them, and the station felt {setting.vibe}."
    )


def foreshadow(world: World, hazard: Hazard, fix: Fix, setting: Setting) -> None:
    world.say(
        f"Before they left, {hazard.cue} flashed on the panel."
    )
    world.say(
        f"{fix.phrase} sat nearby, ready if someone remembered to use it."
    )
    world.facts["foreshadow"] = hazard.label


def conflict(world: World, child: Entity, helper: Entity, hazard: Hazard, fix: Fix) -> None:
    child.memes["worry"] += 1
    child.memes["stubborn"] += 1
    world.say(
        f'{child.id} wanted to keep going. "{helper.id}, we do not have time for that," '
        f"{child.pronoun()} said, pointing at {hazard.label}."
    )
    world.say(
        f'{helper.id} frowned. "If we ignore it, {predicted_risk(hazard)}," '
        f"{helper.pronoun()} said, and the air inside the cabin felt tense."
    )


def fix_problem(world: World, helper: Entity, fix: Fix, hazard: Hazard) -> None:
    world.say(
        f"Then {helper.id} chose the sensible thing: {fix.phrase}."
    )
    world.say(
        f"The ship steadied, and {fix.effect}."
    )


def ending(world: World, setting: Setting, child: Entity, helper: Entity, fix: Fix) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the crew could {setting.launch_word} in a safe way, with {fix.label} done and the stars waiting."
    )
    world.say(
        f"{child.id} grinned at {helper.id}, and the little ship drifted onward, bright and ready."
    )


def tell(setting: Setting, hazard: Hazard, fix: Fix,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Nia", helper_gender: str = "girl",
         parent_name: str = "Mom", trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, role="hero", traits=[trait]))
    child.id = child_name
    world.entities[child_name] = world.entities.pop("child")
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(parent_name, kind="character", type="parent", label=parent_name))
    world.add(Entity("hazard", type="thing", label=hazard.label))
    world.add(Entity("fix", type="thing", label=fix.label))
    world.get(child_name).memes["worry"] = 0.0
    setup(world, setting, world.get(child_name), helper)
    world.para()
    foreshadow(world, hazard, fix, setting)
    conflict(world, world.get(child_name), helper, hazard, fix)
    world.para()
    fix_problem(world, helper, fix, hazard)
    ending(world, setting, world.get(child_name), helper, fix)
    world.facts.update(
        setting=setting, hazard=hazard, fix=fix, child=world.get(child_name),
        helper=helper, parent=parent, outcome="resolved"
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a child where {f["hazard"].label} foreshadows trouble and {f["fix"].phrase} solves it.',
        f'Tell a gentle conflict story set at {f["setting"].place} that includes the phrase "fill-gerund" by showing someone {f["fix"].phrase}.',
        f'Write a small science-fiction story where a warning light, a disagreement, and a clever fix lead to a safe launch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    hazard = f["hazard"]
    fix = f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What warning foreshadowed trouble in the story?",
            answer=f"The story foreshadowed trouble with {hazard.label}. The flashing clue made it clear something needed attention before the crew could launch safely.",
        ),
        QAItem(
            question=f"Why did {child.id} and {helper.id} argue?",
            answer=f"{child.id} wanted to keep going, but {helper.id} wanted to stop and fix the problem first. The conflict came from choosing between rushing ahead and taking care of the ship.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They solved it by {fix.phrase}. That worked because it matched the danger and let them continue the adventure without getting stuck.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a safe launch from {setting.place}. The crew was calm again, and the ship was ready for the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about something important that will happen later. It helps readers feel the warning before the bigger moment arrives.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or disagreement that makes the characters struggle for a while. It gives the story tension before the solution comes.",
        ),
        QAItem(
            question="Why do astronauts and space crews check their ship first?",
            answer="They check it because space is dangerous and far from help. A small problem can become a big one if nobody fixes it before launch.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_station", "low_fuel", "fill_tank", "Mia", "girl", "Nia", "girl", "Mom", "curious"),
    StoryParams("moon_base", "cracked_window", "patch_window", "Leo", "boy", "Nova", "girl", "Dad", "careful"),
    StoryParams("orbital_station", "stuck_hatch", "oil_hatch", "Sam", "boy", "Ava", "girl", "Mom", "bold"),
]


def explain_outcome(params: StoryParams) -> str:
    return "resolved"


ASP_RULES = r"""
valid(S,H,F) :- setting(S), hazard(H), fix(F), compatible(H,F).
compatible(low_fuel, fill_tank).
compatible(cracked_window, patch_window).
compatible(stuck_hatch, oil_hatch).
"""


def asp_facts() -> str:
    import asp
    parts = []
    for sid in SETTING_REGISTRY:
        parts.append(asp.fact("setting", sid))
    for hid in HAZARD_REGISTRY:
        parts.append(asp.fact("hazard", hid))
    for fid in FIX_REGISTRY:
        parts.append(asp.fact("fix", fid))
    parts.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with foreshadowing and conflict.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--hazard", choices=HAZARD_REGISTRY)
    ap.add_argument("--fix", choices=FIX_REGISTRY)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--trait", choices=TRAITS)
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
    fix = args.fix or rng.choice(list(FIX_REGISTRY))
    hazard = args.hazard or {"fill_tank": "low_fuel", "patch_window": "cracked_window", "oil_hatch": "stuck_hatch"}[fix]
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    if (setting, hazard, fix) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in CHILD_NAMES if n != child])
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if FIX_REGISTRY[fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(fix))
    return StoryParams(setting, hazard, fix, child, child_gender, helper, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTING_REGISTRY[params.setting]
    hazard = HAZARD_REGISTRY[params.hazard]
    fix = FIX_REGISTRY[params.fix]
    world = tell(setting, hazard, fix, params.child, params.child_gender, params.helper, params.helper_gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
