#!/usr/bin/env python3
"""
storyworlds/worlds/breast_suspense_space_adventure.py
=====================================================

A standalone storyworld for a small Space Adventure-style suspense tale:
a child astronaut, a mysterious sound on the ship, a careful check, and a
safe ending that proves what changed.

This world is intentionally narrow. It models one child-facing premise:
someone hears a suspenseful bump in a small spacecraft, worries about a chest
panel or breast patch on a suit, and discovers a harmless cause before calling
the crew together.

The domain uses typed entities with physical meters and emotional memes,
a forward-chaining causal engine, a reasonableness gate, an inline ASP twin,
and grounded story / world QA.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    backdrop: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class SuspenseBeat:
    id: str
    hint: str
    sound: str
    fear_word: str
    cause: str
    reveal: str
    keyword: str = "breast"
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    location: str
    safe_cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_to_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("mystery", 0.0) < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["suspense"] = ent.memes.get("suspense", 0.0) + 1
        ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1
        out.append("")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    obj = world.entities.get("object")
    if not child or not obj:
        return out
    if obj.meters.get("blocked", 0.0) < THRESHOLD:
        return out
    sig = ("reveal", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    out.append("")
    return out


CAUSAL_RULES = [
    Rule("fear", "emotional", _r_sound_to_fear),
    Rule("reveal", "emotional", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    return produced


def suspense_at_risk(beat: SuspenseBeat, obj: ObjectCfg) -> bool:
    return beat.keyword in {"breast"} and obj.safe_cause in {"loose wire", "small robot", "hatch latch"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid in BEATS:
            for oid in OBJECTS:
                if suspense_at_risk(BEATS[bid], OBJECTS[oid]):
                    combos.append((sid, bid, oid))
    return combos


@dataclass
class StoryParams:
    setting: str
    beat: str
    object: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure suspense storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.beat is None or c[1] == args.beat)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, beat, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting, beat, obj, helper, name, gender)


def tell(setting: Setting, beat: SuspenseBeat, obj: ObjectCfg, helper: HelperCfg, name: str, gender: str) -> World:
    world = World(setting)
    child = world.add(Entity("child", kind="character", type=gender, label=name))
    crew = world.add(Entity("crew", kind="character", type="pilot", label="the crew"))
    thing = world.add(Entity("object", kind="thing", type="thing", label=obj.label))
    helper_ent = world.add(Entity("helper", kind="thing", type="thing", label=helper.label))

    child.meters["mystery"] = 0.0
    child.memes["suspense"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] = 0.0
    crew.memes["calm"] = 1.0
    thing.meters["blocked"] = 0.0
    helper_ent.meters["ready"] = 1.0

    world.say(f"{name} floated beside {setting.place}, where {setting.backdrop}.")
    world.say(f"{name} noticed {beat.hint}, and {beat.sound} made {name} look over {beat.keyword}.")
    world.para()
    child.memes["suspense"] += 1
    child.meters["mystery"] += 1
    propagate(world, narrate=False)
    world.say(f"{name}'s chest went tight with suspense, and {name} wondered if the tiny {beat.keyword} patch was in trouble.")
    world.say(f"Then {name} remembered the quiet rule: check first, call the crew next.")

    world.para()
    thing.meters["blocked"] = 1.0
    child.meters["mystery"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(f"{helper.effect}, and the worry turned out to be only {obj.phrase}.")
    world.say(f"{name} smiled, because the scary sound had a safe cause: {obj.safe_cause} near {obj.location}.")
    world.say(f"{name} and the crew laughed softly, and the ship felt brave again.")

    world.facts.update(
        child=child,
        crew=crew,
        object=thing,
        helper=helper_ent,
        setting=setting,
        beat=beat,
        obj_cfg=obj,
        helper_cfg=helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    beat = f["beat"]
    obj = f["obj_cfg"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old where {child.label} hears a scary sound on a ship and checks what caused it. Include the word "{beat.keyword}".',
        f"Tell a suspenseful space story where {child.label} worries about a breast patch, then discovers that {obj.phrase} made the sound.",
        f'Write a gentle suspense story in space that begins with a mystery sound, includes "{beat.keyword}", and ends with a safe reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    beat = f["beat"]
    obj = f["obj_cfg"]
    helper = f["helper_cfg"]
    return [
        QAItem(
            question=f"What made {child.label} feel suspenseful near {world.setting.place}?",
            answer=f"{beat.sound} made {child.label} think something might be wrong, especially with the breast patch on the suit.",
        ),
        QAItem(
            question=f"What safe cause did {child.label} find for the strange sound?",
            answer=f"The sound came from {obj.phrase}, and the cause was {obj.safe_cause} near {obj.location}.",
        ),
        QAItem(
            question=f"How did {helper.label} help in the story?",
            answer=f"{helper.action}, which helped turn the mystery into a safe and happy answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is a feeling of wondering what will happen next, especially when something seems mysterious or a little scary.",
        ),
        QAItem(
            question="What is a breast patch on a space suit?",
            answer="A breast patch is a small patch or panel on the front of a suit, over the chest, that can hold a name tag, sensor, or cover.",
        ),
        QAItem(
            question="Why do astronauts check mysterious sounds carefully?",
            answer="Astronauts check mysterious sounds carefully so they can find a safe cause before a small problem becomes a bigger one.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BEATS[params.beat], OBJECTS[params.object], HELPERS[params.helper], params.name, params.gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BEATS:
        lines.append(asp.fact("beat", bid))
        lines.append(asp.fact("keyword", bid, BEATS[bid].keyword))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        if suspense_at_risk(BEATS["breast_alarm"], OBJECTS[oid]):
            lines.append(asp.fact("at_risk", oid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,O) :- setting(S), beat(B), object(O), at_risk(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


SETTINGS = {
    "orbital": Setting(place="the orbital cabin", backdrop="the stars flashed past the window", affordances={"check"}),
    "lunar": Setting(place="the moon station", backdrop="the hallway hummed with a soft blue light", affordances={"check"}),
    "starlab": Setting(place="the star lab", backdrop="the control screen blinked quietly", affordances={"check"}),
}

BEATS = {
    "breast_alarm": SuspenseBeat(
        id="breast_alarm",
        hint="a tiny tap from the front of the suit",
        sound="tap-tap",
        fear_word="suspense",
        cause="breast patch",
        reveal="a loose badge clip",
        keyword="breast",
        tags={"breast", "space", "suspense"},
    ),
    "breast_rattle": SuspenseBeat(
        id="breast_rattle",
        hint="a faint rattle from the chest panel",
        sound="rattle-rattle",
        fear_word="suspense",
        cause="breast panel",
        reveal="a floating tool",
        keyword="breast",
        tags={"breast", "space", "suspense"},
    ),
}

OBJECTS = {
    "clip": ObjectCfg(
        id="clip",
        label="badge clip",
        phrase="a loose badge clip",
        location="the pocket seam",
        safe_cause="loose wire",
        tags={"clip", "safe"},
    ),
    "robot": ObjectCfg(
        id="robot",
        label="toy robot",
        phrase="a tiny toy robot",
        location="the shelf rail",
        safe_cause="small robot",
        tags={"robot", "safe"},
    ),
    "hatch": ObjectCfg(
        id="hatch",
        label="hatch latch",
        phrase="a hatch latch",
        location="the door frame",
        safe_cause="hatch latch",
        tags={"hatch", "safe"},
    ),
}

HELPERS = {
    "check": HelperCfg(
        id="check",
        label="a careful check",
        action="the child touched the panel and found nothing broken",
        effect="The child checked the chest panel one more time",
        tags={"check"},
    ),
    "call": HelperCfg(
        id="call",
        label="the crew call",
        action="the child called the crew right away",
        effect="The child called the crew and waited",
        tags={"call"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Luna", "Ava", "Nia"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Max", "Finn"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.beat is None or c[1] == args.beat)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, beat, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, beat=beat, object=obj, helper=helper, name=name, gender=gender)


def generate_all(params_list: list[StoryParams]) -> list[StorySample]:
    return [generate(p) for p in params_list]


CURATED = [StoryParams("orbital", "breast_alarm", "clip", "check", "Mia", "girl")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
