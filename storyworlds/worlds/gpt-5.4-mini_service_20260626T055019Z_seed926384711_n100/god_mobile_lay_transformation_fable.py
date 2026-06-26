#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/god_mobile_lay_transformation_fable.py
===============================================================================================================

A small fable-like story world about a gentle god, a mobile, and a needed
transformation.

Seed story used to shape the model:
---
A little god tended a quiet grove. In the grove hung a bright mobile of shells
and leaves. One windy day the mobile spun too fast, fell apart, and lay on the
ground in sad pieces. The god could have left it there, but instead the god
transformed the broken pieces into a new mobile made of soft vines and blue
flowers. The grove grew calm again, and the mobile danced more kindly in the
breeze.

World model:
---
- A deity has divine patience, pride, and care.
- A hanging mobile can be damaged, dusty, bright, or calm.
- A transformation may repair, brighten, or re-form the mobile.
- If the mobile is broken in the wind, the god worries.
- A thoughtful transformation restores balance and leaves a simple moral.

Fable instruments:
---
- Clear beginning, tension, wise turn, and ending image.
- A brief moral-like closing sentence is acceptable and grounded in the world.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hanging: bool = False
    broken: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"god", "deity"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    quiet: bool = True


@dataclass
class MobileForm:
    id: str
    label: str
    phrase: str
    material: str
    sway: str
    risk: str
    transformed_into: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    verb: str
    method: str
    result_phrase: str
    guards: set[str] = field(default_factory=set)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "grove": Setting(place="the quiet grove", weather="windy", quiet=True),
    "hill": Setting(place="the little hill", weather="breezy", quiet=True),
    "temple_yard": Setting(place="the temple yard", weather="windy", quiet=False),
}

MOBILE_FORMS = {
    "shells": MobileForm(
        id="shells",
        label="shell mobile",
        phrase="a bright mobile of shells and leaves",
        material="shells",
        sway="spiraled softly in the wind",
        risk="too wild",
        transformed_into="vines and blue flowers",
        tags={"mobile", "wind", "shell"},
    ),
    "paper": MobileForm(
        id="paper",
        label="paper mobile",
        phrase="a light mobile of paper birds",
        material="paper",
        sway="turned and turned like a slow song",
        risk="too sharp",
        transformed_into="silk ribbons",
        tags={"mobile", "paper"},
    ),
    "wood": MobileForm(
        id="wood",
        label="wood mobile",
        phrase="a small mobile of painted wood moons",
        material="wood",
        sway="tapped the air with tiny clicks",
        risk="too stiff",
        transformed_into="feather loops",
        tags={"mobile", "wood"},
    ),
}

TRANSFORMATIONS = {
    "mend": Transformation(
        id="mend",
        label="mend",
        verb="mend",
        method="gently touch the broken pieces and ask them to come together",
        result_phrase="whole and calm",
        guards={"broken"},
        tags={"transformation", "mend"},
    ),
    "brighten": Transformation(
        id="brighten",
        label="brighten",
        verb="brighten",
        method="let a warm glow pass through the hanging strings",
        result_phrase="bright and kind",
        guards={"dim"},
        tags={"transformation", "light"},
    ),
    "reform": Transformation(
        id="reform",
        label="reform",
        verb="reshape",
        method="gather the old parts into a new and gentler pattern",
        result_phrase="newly made",
        guards={"broken", "tangled"},
        tags={"transformation", "craft"},
    ),
}

GOD_NAMES = ["Aru", "Nema", "Ilo", "Sela", "Miro", "Oren"]
TRAITS = ["patient", "wise", "gentle", "careful", "humble"]


@dataclass
class StoryParams:
    setting: str
    mobile_form: str
    transformation: str
    name: str
    trait: str
    seed: Optional[int] = None


def mob_at_risk(mobile: MobileForm) -> bool:
    return True


def select_transformation(mobile: MobileForm, trans: Transformation) -> bool:
    return bool(trans.guards & {"broken", "dim", "tangled"}) or trans.id == "mend"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MOBILE_FORMS:
            for t in TRANSFORMATIONS:
                if select_transformation(MOBILE_FORMS[m], TRANSFORMATIONS[t]):
                    combos.append((s, m, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about a god, a mobile, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mobile-form", choices=MOBILE_FORMS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
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
    if args.setting and args.mobile_form and args.transformation:
        m = MOBILE_FORMS[args.mobile_form]
        t = TRANSFORMATIONS[args.transformation]
        if not select_transformation(m, t):
            raise StoryError("That transformation does not fit the mobile's problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mobile_form is None or c[1] == args.mobile_form)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, mobile_form, transformation = rng.choice(sorted(combos))
    name = args.name or rng.choice(GOD_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mobile_form=mobile_form, transformation=transformation, name=name, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    god = world.add(Entity(id=params.name, kind="character", type="god", label=params.name))
    mobile_def = MOBILE_FORMS[params.mobile_form]
    trans_def = TRANSFORMATIONS[params.transformation]
    mobile = world.add(Entity(
        id="mobile",
        type="mobile",
        label=mobile_def.label,
        phrase=mobile_def.phrase,
        owner=god.id,
        caretaker=god.id,
        hanging=True,
    ))
    world.facts.update(god=god, mobile=mobile, mobile_def=mobile_def, trans_def=trans_def, params=params)

    world.say(
        f"{god.label} was a {params.trait} little god who kept watch over {world.setting.place}."
    )
    world.say(
        f"Under the eaves hung {mobile.phrase}, and it {mobile_def.sway}."
    )
    world.para()
    world.say(
        f"One windy day, the gusts grew rough. The {mobile.label} tangled, snapped at the strings, and lay on the ground in pieces."
    )
    mobile.broken = True
    mobile.meters["damage"] = 1.0
    mobile.memes["worry"] = 1.0
    god.memes["sorrow"] = 1.0
    world.say(
        f"{god.label} saw the broken mobile and felt a small ache. The grove had gone quiet in the wrong way."
    )
    world.para()
    if trans_def.id == "mend":
        world.say(
            f"Instead of leaving it there, {god.label} chose to {trans_def.verb} it."
        )
    elif trans_def.id == "brighten":
        world.say(
            f"Instead of leaving it there, {god.label} chose to {trans_def.verb} it."
        )
    else:
        world.say(
            f"Instead of leaving it there, {god.label} chose to {trans_def.verb} it."
        )
    world.say(
        f"With one careful thought, {god.label} could {trans_def.method}."
    )
    mobile.broken = False
    mobile.meters["damage"] = 0.0
    mobile.meters["beauty"] = 1.0
    mobile.memes["worry"] = 0.0
    god.memes["sorrow"] = 0.0
    god.memes["peace"] = 1.0
    world.say(
        f"The old mobile became {trans_def.result_phrase}; it now hung as {mobile_def.transformed_into} and moved with a softer grace."
    )
    world.para()
    world.say(
        f"By sunset, the breeze found a kinder toy to touch, and the little god smiled at the calm above the path. A thing that changes well can still stay beautiful."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mobile_def"]
    t = world.facts["trans_def"]
    return [
        f"Write a short fable about a god named {p.name} who watches a {m.label} and uses transformation wisely.",
        f"Tell a gentle story in which a small god sees a mobile lay broken and chooses to {t.verb} it.",
        f"Write a child-friendly fable about care, change, and a mobile in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    m = world.facts["mobile_def"]
    t = world.facts["trans_def"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.name}, a {p.trait} little god who watches over {world.setting.place}.",
        ),
        QAItem(
            question=f"What happened to the {m.label} before the transformation?",
            answer=f"It got tangled in the wind, snapped, and lay broken on the ground.",
        ),
        QAItem(
            question=f"What did {p.name} do to help the mobile?",
            answer=f"{p.name} chose to {t.verb} it by {t.method}.",
        ),
        QAItem(
            question=f"What was the mobile like at the end?",
            answer=f"At the end it was {t.result_phrase} and moved as {m.transformed_into}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mobile?",
            answer="A mobile is a hanging object with pieces that can move gently when air or motion passes by.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change that turns something into a new form or makes it work in a new way.",
        ),
        QAItem(
            question="Why can wind be a problem for a hanging mobile?",
            answer="Strong wind can twist, tangle, or break a mobile if it is delicate.",
        ),
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
    for e in world.entities.values():
        bits = []
        if e.hanging:
            bits.append("hanging=True")
        if e.broken:
            bits.append("broken=True")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
broken_mobile(M) :- mobile(M), broken(M).
needs_transformation(M, T) :- broken_mobile(M), transformation(T).
good_fix(M, T) :- broken_mobile(M), transformation(T), can_mend(T).
valid_story(S, M, T) :- setting(S), mobile(M), transformation(T), good_fix(M, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MOBILE_FORMS.items():
        lines.append(asp.fact("mobile", mid))
        lines.append(asp.fact("mobile_label", mid, m.label))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        if t.id in {"mend", "reform"}:
            lines.append(asp.fact("can_mend", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for s in SETTINGS:
        for m in MOBILE_FORMS:
            for t in TRANSFORMATIONS:
                if select_transformation(MOBILE_FORMS[m], TRANSFORMATIONS[t]) and TRANSFORMATIONS[t].id in {"mend", "reform"}:
                    python_set.add((s, m, t))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="grove", mobile_form="shells", transformation="mend", name="Aru", trait="gentle"),
    StoryParams(setting="hill", mobile_form="paper", transformation="reform", name="Sela", trait="wise"),
    StoryParams(setting="temple_yard", mobile_form="wood", transformation="mend", name="Nema", trait="patient"),
]


def explain_rejection() -> str:
    return "No valid story: the chosen transformation does not fit the mobile's problem."


def resolve_genderless_placeholder(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mobile_form} / {p.transformation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
