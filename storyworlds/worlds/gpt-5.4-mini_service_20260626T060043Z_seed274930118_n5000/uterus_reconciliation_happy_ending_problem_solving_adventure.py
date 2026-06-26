#!/usr/bin/env python3
"""
storyworlds/worlds/uterus_reconciliation_happy_ending_problem_solving_adventure.py
===================================================================================

A small adventure storyworld about a child exploring a body-themed science setting,
meeting the word "uterus", solving a misunderstanding, and ending in reconciliation
with a happy finish.

Seed-tale shape used to build the world:
---
A child visits a science exhibit with an older sibling and sees the word uterus on a
bright sign. The child first thinks it looks scary, but the sibling explains it gently.
Together they follow clues, fix a broken poster, and end with the child feeling brave,
curious, and glad they asked for help.

World model:
---
This world tracks a few typed entities with physical meters and emotional memes.

Physical meters:
- clue
- mess
- repair
- tidy

Emotional memes:
- curiosity
- worry
- trust
- joy
- hurt
- apology
- reconciliation

The story is driven by state changes:
- seeing a strange word increases curiosity and worry
- asking for help can lower worry and raise trust
- apologizing and explaining can create reconciliation
- solving the exhibit problem can complete the adventure and produce the happy ending
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    exhibits: set[str] = field(default_factory=set)


@dataclass
class StoryObject:
    id: str
    label: str
    phrase: str
    role: str
    helps_with: set[str] = field(default_factory=set)
    needed_for: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    exhibit: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_apology(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    guide = world.get("guide")
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    if guide.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("apology")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["apology"] = child.memes.get("apology", 0) + 1
    guide.memes["trust"] = guide.memes.get("trust", 0) + 1
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0) - 1)
    out.append("The child took a breath and said sorry for getting scared so fast.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    guide = world.get("guide")
    if child.memes.get("apology", 0) < THRESHOLD:
        return out
    if guide.memes.get("trust", 0) < THRESHOLD:
        return out
    sig = ("reconcile")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["reconciliation"] = child.memes.get("reconciliation", 0) + 1
    guide.memes["reconciliation"] = guide.memes.get("reconciliation", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    guide.memes["joy"] = guide.memes.get("joy", 0) + 1
    out.append("The child and the guide smiled at each other again.")
    return out


def _r_finish_exhibit(world: World) -> list[str]:
    out: list[str] = []
    poster = world.get("poster")
    child = world.get("child")
    if poster.meters.get("repair", 0) < THRESHOLD:
        return out
    sig = ("finish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    poster.meters["tidy"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    out.append("The poster was fixed, and the exhibit looked bright and neat again.")
    return out


RULES = [
    Rule("apology", _r_apology),
    Rule("reconcile", _r_reconcile),
    Rule("finish_exhibit", _r_finish_exhibit),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "museum": Setting(place="the science museum", indoor=True, exhibits={"body-map", "poster"}),
    "library": Setting(place="the library corner", indoor=True, exhibits={"body-map"}),
    "classroom": Setting(place="the classroom", indoor=True, exhibits={"poster", "body-map"}),
}

EXHIBITS = {
    "body-map": "a big body map with bright labels",
    "poster": "a colorful poster with missing stickers",
}

OBJECTS = {
    "sticker": StoryObject(
        id="sticker",
        label="star sticker",
        phrase="a shiny star sticker",
        role="repair piece",
        helps_with={"poster"},
        needed_for={"repair"},
    ),
    "card": StoryObject(
        id="card",
        label="hint card",
        phrase="a little hint card",
        role="helper note",
        helps_with={"body-map"},
        needed_for={"clue"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Rosa", "Tia", "Nina", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Theo", "Finn", "Leo"]
TRAITS = ["curious", "brave", "gentle", "careful", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for exhibit in setting.exhibits:
            for obj in OBJECTS:
                if exhibit in OBJECTS[obj].helps_with or exhibit in OBJECTS[obj].needed_for or True:
                    combos.append((place, exhibit, obj))
    return combos


def explain_invalid(place: str, exhibit: str, obj: str) -> str:
    return f"(No story: {OBJECTS[obj].label} does not make sense with {exhibit} at {place}.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", params.trait],
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0, "joy": 0.0, "hurt": 0.0, "apology": 0.0, "reconciliation": 0.0},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type="sister" if params.helper == "sister" else "brother",
        label=f"the {params.helper}",
        traits=["kind", "patient"],
        memes={"kindness": 1.0, "trust": 0.0, "joy": 0.0, "reconciliation": 0.0},
    ))
    exhibit = world.add(Entity(
        id="exhibit",
        kind="thing",
        type="display",
        label=params.exhibit,
        phrase=EXHIBITS[params.exhibit],
        meters={"clue": 0.0, "mess": 0.0, "repair": 0.0, "tidy": 0.0},
    ))
    poster = world.add(Entity(
        id="poster",
        kind="thing",
        type="poster",
        label="poster",
        phrase="the poster with one missing corner",
        caretaker="guide",
        meters={"repair": 0.0, "tidy": 0.0},
    ))
    obj = world.add(Entity(
        id="object",
        kind="thing",
        type="object",
        label=OBJECTS[params.object].label,
        phrase=OBJECTS[params.object].phrase,
        owner="guide",
        meters={"repair": 1.0 if params.object == "sticker" else 0.0, "clue": 1.0 if params.object == "card" else 0.0},
    ))

    world.facts.update(child=child, guide=guide, exhibit=exhibit, poster=poster, object=obj, params=params)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    child, guide = f["child"], f["guide"]
    setting = world.setting
    exhibit = f["exhibit"]
    obj = f["object"]

    world.say(
        f"{child.label} went to {setting.place} with {guide.label} for a little adventure."
    )
    world.say(
        f"Inside, they found {exhibit.phrase}, and one word on the sign was {f['params'].exhibit}: uterus."
    )
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.label} stared at the word uterus and felt a small wobble of worry, even though curiosity tugged harder."
    )
    world.say(
        f"{guide.label} picked up {obj.phrase} and said the day would be easier if they solved the exhibit problem together."
    )


def narrate_middle(world: World) -> None:
    f = world.facts
    child, guide, poster, obj = f["child"], f["guide"], f["poster"], f["object"]

    world.para()
    world.say(
        f"{child.label} asked, 'Is uterus a scary thing?'"
    )
    guide.memes["trust"] = guide.memes.get("trust", 0) + 1
    world.say(
        f"{guide.label} shook {guide.pronoun('possessive')} head kindly and explained that uterus is a real word for a soft place inside a body."
    )
    world.say(
        f"That answer helped, but the poster still had a broken corner, so they needed problem solving too."
    )
    world.say(
        f"{child.label} looked at the missing corner, then at {obj.label}, and began to search for how the pieces could fit."
    )
    poster.meters["repair"] += 1
    world.say(
        f"Together they placed the {obj.label} on the poster, smoothing it down carefully."
    )
    propagate(world, narrate=True)


def narrate_end(world: World) -> None:
    f = world.facts
    child, guide, poster = f["child"], f["guide"], f["poster"]
    world.para()
    if child.memes.get("reconciliation", 0) >= THRESHOLD:
        world.say(
            f"{child.label} smiled at {guide.label} and said sorry for getting frightened."
        )
        world.say(
            f"{guide.label} smiled back, and the two of them felt reconciled."
        )
    world.say(
        f"The poster was neat again, the word uterus no longer seemed scary, and {child.label} walked home feeling brave, proud, and happy."
    )
    world.say(
        f"It was a small adventure, but it ended with a happy ending and a better understanding."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    narrate_middle(world)
    narrate_end(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle adventure story for a young child about the word uterus, a problem to solve, and a happy ending.",
        f"Tell a short story where {world.facts['child'].label} visits {world.setting.place} and learns what uterus means with help from {world.facts['guide'].label}.",
        f"Write a child-friendly adventure about curiosity, worry, reconciliation, and fixing a poster that includes the word uterus.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, obj = f["child"], f["guide"], f["object"]
    return [
        QAItem(
            question=f"Where did {child.label} go for the adventure?",
            answer=f"{child.label} went to {world.setting.place} with {guide.label}.",
        ),
        QAItem(
            question="What word made the child feel worried at first?",
            answer="The word uterus made the child feel worried at first, even though curiosity was strong too.",
        ),
        QAItem(
            question=f"How did {child.label} and {guide.label} solve the poster problem?",
            answer=f"They solved it by using {obj.phrase} and working together carefully.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation, a fixed poster, and a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a uterus?",
            answer="A uterus is a real body part inside the body. It is a soft place where a baby can grow before birth.",
        ),
        QAItem(
            question="Why can a child ask questions when they see a new word?",
            answer="A child can ask questions because new words can be confusing, and asking helps them learn safely.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a problem and trying different ways to fix it.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people stop being upset and feel friendly and connected again.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
exhibit(E) :- exhibit_name(E).
needs_repair(O) :- object(O), repair_piece(O).
supports_clue(O) :- object(O), clue_piece(O).
compat(Place, Exhibit, Object) :- setting(Place), exhibits(Place, Exhibit), object(Object),
                                  (needs_repair(Object); supports_clue(Object)).
story_ok(Place, Exhibit, Object) :- compat(Place, Exhibit, Object), exhibits(Place, Exhibit).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for ex in sorted(setting.exhibits):
            lines.append(asp.fact("exhibits", place, ex))
    for obj_id, obj in OBJECTS.items():
        lines.append(asp.fact("object", obj_id))
        if "repair" in obj.needed_for:
            lines.append(asp.fact("repair_piece", obj_id))
        if "clue" in obj.needed_for:
            lines.append(asp.fact("clue_piece", obj_id))
    for ex in EXHIBITS:
        lines.append(asp.fact("exhibit_name", ex))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibles() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    import asp
    py = set((p, e, o) for p, e, o in valid_combos())
    asps = set(asp_compatibles())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asps:
        print("  only in python:", sorted(py - asps))
    if asps - py:
        print("  only in clingo:", sorted(asps - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about uterus, problem solving, reconciliation, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--exhibit", choices=list(EXHIBITS))
    ap.add_argument("--object", dest="object_name", choices=list(OBJECTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["sister", "brother"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.exhibit:
        combos = [c for c in combos if c[1] == args.exhibit]
    if args.object_name:
        combos = [c for c in combos if c[2] == args.object_name]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, exhibit, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["sister", "brother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, exhibit=exhibit, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="museum", exhibit="body-map", object="sticker", name="Maya", gender="girl", helper="sister", trait="curious"),
    StoryParams(place="classroom", exhibit="poster", object="sticker", name="Noah", gender="boy", helper="brother", trait="brave"),
    StoryParams(place="library", exhibit="body-map", object="card", name="Ivy", gender="girl", helper="sister", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_compatibles()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.exhibit} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
