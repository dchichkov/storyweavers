#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baby_jagged_actual_curiosity_misunderstanding_humor_comedy.py
==============================================================================================

A small comedy storyworld about a curious baby, a jagged object, and an actual
misunderstanding that turns into a safe, funny ending.

The domain is intentionally tiny:
- a baby sees a jagged object and wants to inspect the "actual" thing closely
- a misunderstanding makes the baby think the object is a toy or snack
- a calm helper clarifies what it is and swaps in a safe, silly alternative
- the ending proves the baby learned something without any harm

This world is built to be child-facing, concrete, and state-driven.
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
SCARED_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    light: str
    prop: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CuriosityObject:
    id: str
    label: str
    phrase: str
    texture: str
    actual: str
    harmless: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    label: str
    mistaken_for: str
    line: str
    correction: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HumorBeat:
    id: str
    line: str
    payoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    baby = world.entities.get("baby")
    obj = world.entities.get("object")
    if not baby or not obj:
        return out
    if baby.memes["curiosity"] < THRESHOLD or obj.meters["revealed"] < THRESHOLD:
        return out
    sig = ("startle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if obj.tags.intersection({"jagged"}):
        baby.memes["surprise"] += 1
        baby.memes["care"] += 1
        out.append("__startle__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("startle", _r_startle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if obj.harmless and mis.mistaken_for == "toy":
                    combos.append((sid, oid, mid))
    return combos


def needs_correction(obj: CuriosityObject, mis: Misunderstanding) -> bool:
    return obj.harmless and mis.mistaken_for == "toy"


def predict_misunderstanding(world: World, obj_id: str) -> dict:
    sim = world.copy()
    sim.get("baby").memes["curiosity"] += 1
    sim.get("object").meters["revealed"] += 1
    propagate(sim, narrate=False)
    return {
        "surprised": sim.get("baby").memes["surprise"] >= THRESHOLD,
        "care": sim.get("baby").memes["care"],
    }


def tell(world: World, obj: CuriosityObject, mis: Misunderstanding, humor: HumorBeat) -> World:
    baby = world.add(Entity(id="baby", kind="character", type="baby", label="the baby", role="curious"))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="the grown-up", role="helper"))
    item = world.add(Entity(id="object", kind="thing", type="thing", label=obj.label, tags=set(obj.tags)))
    baby.memes["curiosity"] = 1.0

    world.say(
        f"On a bright afternoon in {world.setting.place}, the baby spotted {obj.phrase} near {world.setting.prop}."
    )
    world.say(
        f"{baby.label_word.capitalize()} leaned closer because the little thing looked so interesting, "
        f"especially with its {obj.texture} edges."
    )

    world.para()
    world.say(
        f'The baby pointed and made a very serious face. "{mis.line}"'
    )
    world.say(
        f"But that was the misunderstanding: the actual thing was {obj.actual}, not {mis.mistaken_for}."
    )
    world.say(
        f'The grown-up laughed and said, "{mis.correction}"'
    )

    item.meters["revealed"] += 1
    baby.memes["curiosity"] += 1
    baby.memes["humor"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{humor.line} The baby blinked, then giggled, because the baby had been wrong in a very funny way."
    )
    world.say(
        f"{humor.payoff} So the baby touched only the safe side of it and learned to ask first."
    )

    world.para()
    safe = "a soft spoon" if "spoon" in obj.tags else "a squeaky rattle"
    world.say(
        f"After that, the grown-up brought out {safe}, and the baby clapped at the much less jagged adventure."
    )
    world.say(
        f"The jagged object stayed where it belonged, the baby stayed safe, and the day ended with a tiny, proud grin."
    )

    world.facts.update(
        baby=baby,
        helper=helper,
        item=item,
        object_cfg=obj,
        misunderstanding=mis,
        humor=humor,
        setting=world.setting,
        corrected=True,
        surprised=baby.memes["surprise"] >= THRESHOLD,
        humorous=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj: CuriosityObject = f["object_cfg"]
    mis: Misunderstanding = f["misunderstanding"]
    return [
        f'Write a comedy story for a 3-to-5-year-old that includes the words "baby", "jagged", and "actual".',
        f"Tell a small humorous story where a curious baby thinks {obj.label} is {mis.mistaken_for}, but a grown-up explains the actual thing.",
        f'Write a gentle story about curiosity, misunderstanding, and humor, ending with a safe toy instead of {obj.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj: CuriosityObject = f["object_cfg"]
    mis: Misunderstanding = f["misunderstanding"]
    qa = [
        QAItem(
            question="Why did the baby get so interested?",
            answer=(
                f"The baby got interested because {obj.phrase} looked unusual and a little mysterious. "
                f"Its jagged edges made the baby want a closer look."
            ),
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=(
                f"The baby thought the object was {mis.mistaken_for}, but it was actually {obj.actual}. "
                f"The grown-up corrected that idea before anything unsafe could happen."
            ),
        ),
        QAItem(
            question="How did the story turn funny?",
            answer=(
                f"It turned funny when the baby made a very serious guess that was totally wrong. "
                f"Then everyone laughed once the actual thing was explained."
            ),
        ),
    ]
    if f.get("corrected"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    "It ended safely, with the baby getting a harmless toy instead. "
                    "The baby stayed cheerful, and the jagged object was left alone."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj: CuriosityObject = f["object_cfg"]
    mis: Misunderstanding = f["misunderstanding"]
    qs = [
        QAItem(
            question="What does jagged mean?",
            answer=(
                "Jagged means uneven and rough with sharp little points or edges. "
                "A jagged thing can scratch, so careful hands should not grab it fast."
            ),
        ),
        QAItem(
            question="Why do people say actual?",
            answer=(
                "Actual means real or true, not just guessed or imagined. "
                "It helps people explain what something really is."
            ),
        ),
    ]
    if "toy" in mis.mistaken_for:
        qs.append(
            QAItem(
                question="Why should a baby ask a grown-up about a strange object?",
                answer=(
                    "A grown-up can explain what the object really is and whether it is safe. "
                    "That helps the baby stay curious without getting hurt."
                ),
            )
        )
    if obj.harmless:
        qs.append(
            QAItem(
                question="Can a harmless object still look strange?",
                answer=(
                    "Yes. Something can look odd or jagged and still be safe if a grown-up says so. "
                    "Even then, it is smart to check first."
                ),
            )
        )
    return qs


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        light="sunlight",
        prop="the chair",
        mood="busy",
        tags={"home"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        light="lamplight",
        prop="the soft rug",
        mood="cozy",
        tags={"home"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden table",
        light="afternoon light",
        prop="the wooden bench",
        mood="bright",
        tags={"outside"},
    ),
}

OBJECTS = {
    "spoon": CuriosityObject(
        id="spoon",
        label="a metal spoon",
        phrase="a shiny metal spoon",
        texture="jagged-looking",
        actual="just a spoon with a bumpy edge pattern",
        harmless=True,
        tags={"spoon", "jagged"},
    ),
    "lid": CuriosityObject(
        id="lid",
        label="a jar lid",
        phrase="an actual jar lid",
        texture="jagged",
        actual="the lid from a snack jar",
        harmless=True,
        tags={"lid", "jagged"},
    ),
    "keychain": CuriosityObject(
        id="keychain",
        label="a keychain",
        phrase="a tiny keychain with a jagged charm",
        texture="jagged",
        actual="a pocket keychain shaped like a star",
        harmless=True,
        tags={"keychain", "jagged"},
    ),
}

MISUNDERSTANDINGS = {
    "snack": Misunderstanding(
        id="snack",
        label="snack mistake",
        mistaken_for="a snack",
        line="Is that actual snack?",
        correction="Nope, it's actual metal, not dinner.",
        tags={"misunderstanding", "actual"},
    ),
    "toy": Misunderstanding(
        id="toy",
        label="toy mistake",
        mistaken_for="a toy",
        line="Is that a toy for me?",
        correction="Nope, that is the actual object, and it is not a toy.",
        tags={"misunderstanding", "actual"},
    ),
}

HUMOR = {
    "giggle": HumorBeat(
        id="giggle",
        line="The baby made the tiniest dramatic gasp in the whole kitchen.",
        payoff="The grown-up laughed so hard the spoon almost became a microphone.",
        tags={"humor"},
    ),
    "blink": HumorBeat(
        id="blink",
        line="The baby stared as if the object had just told a joke.",
        payoff="Then the baby giggled at the silly mistake and pointed at the real shape.",
        tags={"humor"},
    ),
}

CURATED = [
    StoryParams(seed=1),
]

@dataclass
class StoryParams:
    setting: str = "kitchen"
    object: str = "spoon"
    misunderstanding: str = "toy"
    humor: str = "giggle"
    baby_name: str = "Mimi"
    helper_name: str = "Mom"
    seed: Optional[int] = None


def valid_params(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.object in OBJECTS and params.misunderstanding in MISUNDERSTANDINGS and params.humor in HUMOR and needs_correction(OBJECTS[params.object], MISUNDERSTANDINGS[params.misunderstanding])


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.harmless:
            lines.append(asp.fact("harmless", oid))
        if "jagged" in obj.tags:
            lines.append(asp.fact("jagged", oid))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("mistaken_for", mid, mis.mistaken_for))
    for hid in HUMOR:
        lines.append(asp.fact("humor", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,M,H) :- setting(S), object(O), misunderstanding(M), humor(H), harmless(O), mistaken_for(M,toy).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(
        (s, o, m, h)
        for s in SETTINGS
        for o in OBJECTS
        for m in MISUNDERSTANDINGS
        for h in HUMOR
        if valid_params(StoryParams(setting=s, object=o, misunderstanding=m, humor=h))
    )
    if cset != pset:
        print("MISMATCH in ASP parity:")
        print(" only in clingo:", sorted(cset - pset))
        print(" only in python:", sorted(pset - cset))
        rc = 1
    try:
        sample = generate(StoryParams())
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a curious baby, a jagged object, and a funny misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--humor", choices=HUMOR)
    ap.add_argument("--baby-name")
    ap.add_argument("--helper-name")
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
    obj = args.object or rng.choice(list(OBJECTS))
    mis = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    humor = args.humor or rng.choice(list(HUMOR))
    params = StoryParams(
        setting=setting,
        object=obj,
        misunderstanding=mis,
        humor=humor,
        baby_name=args.baby_name or rng.choice(["Mimi", "Nino", "Lulu", "Pip"]),
        helper_name=args.helper_name or rng.choice(["Mom", "Dad", "Auntie"]),
    )
    if not valid_params(params):
        raise StoryError("This combination does not make a safe, funny misunderstanding story.")
    return params


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("object", OBJECTS), ("misunderstanding", MISUNDERSTANDINGS), ("humor", HUMOR)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = World(SETTINGS[params.setting])
    world.setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    hum = HUMOR[params.humor]
    world = tell(world, obj, mis, hum)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams())]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
