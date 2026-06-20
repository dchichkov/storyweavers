#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lee_lesson_learned_surprise_comedy.py
=====================================================================

A tiny comedy storyworld about Lee, a surprise, and a lesson learned.

The domain:
- Lee wants to perform a small comedy trick at home.
- A surprise prop or pet changes the plan.
- A cautious helper predicts the problem, offers a sensible fix, and Lee learns
  a lesson with a funny ending image.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- QA generated from world state, not rendered English
- Python reasonableness gate plus inline ASP twin
- --verify exercises both parity and ordinary story generation
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Theme:
    id: str
    scene: str
    setup: str
    act_title: str
    helper_title: str
    surprise_kind: str
    ending: str

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
class Prop:
    id: str
    label: str
    setup_phrase: str
    surprise_phrase: str
    risky: bool = False
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
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["chaos"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"instigator", "helper"}:
                kid.memes["alarm"] += 1
        out.append("__chaos__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess)]


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


def hazard_at_risk(prop: Prop) -> bool:
    return prop.risky


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fire_severity(prop: Prop, delay: int) -> int:
    return 1 + delay if prop.risky else 0


def is_contained(fix: Fix, prop: Prop, delay: int) -> bool:
    return fix.power >= fire_severity(prop, delay)


def predict_surprise(world: World, prop_id: str) -> dict:
    sim = world.copy()
    _do_surprise(sim, sim.get(prop_id), narrate=False)
    return {
        "mess": sim.get(prop_id).meters["mess"] >= THRESHOLD,
        "chaos": sim.get("room").meters["chaos"],
    }


def _do_surprise(world: World, prop: Entity, narrate: bool = True) -> None:
    prop.meters["mess"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, lee: Entity, helper: Entity, theme: Theme) -> None:
    lee.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Lee was ready for a silly afternoon in {theme.scene}. "
        f"{theme.setup}"
    )
    world.say(
        f'"{theme.act_title}!" Lee said. "{theme.helper_title} and me, we are the stars of this joke!"'
    )


def build_tension(world: World, lee: Entity, helper: Entity, prop: Prop) -> None:
    world.say(
        f"But then {prop.surprise_phrase} showed up, and the whole plan wobbled like a wobbly chair."
    )
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip. "
        f'"If you use that, Lee, the whole bit will turn messy," {helper.pronoun()} said.'
    )
    helper.memes["caution"] += 1


def temptation(world: World, lee: Entity, prop: Prop) -> None:
    lee.memes["curiosity"] += 1
    world.say(
        f'Lee grinned. "A surprise is just another punch line," Lee said, and reached for {prop.label}.'
    )


def warn(world: World, helper: Entity, lee: Entity, prop: Prop) -> None:
    pred = predict_surprise(world, prop.id)
    world.facts["predicted_chaos"] = pred["chaos"]
    world.say(
        f'"Wait," {helper.id} said. "That surprise prop will make a real mess, and then we will have to clean the whole room."'
    )


def defy(world: World, lee: Entity, prop: Prop) -> None:
    lee.memes["defiance"] += 1
    world.say(
        f"Lee ignored the warning and flicked {prop.label} anyway."
    )


def accept(world: World, lee: Entity, helper: Entity, theme: Theme, fix: Fix) -> None:
    lee.memes["joy"] += 1
    lee.memes["lesson"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'Lee blinked, laughed, and said, "Oh! You were right. I learned my lesson."'
    )
    world.say(
        f"They switched to {fix.qa_text}. {theme.ending}"
    )


def surprise_event(world: World, prop: Entity) -> None:
    _do_surprise(world, prop)
    world.say(
        f"Whoops! {prop.label.capitalize()} did not stay tidy. It popped open with a noisy splat."
    )


def rescue(world: World, helper: Entity, fix: Fix, prop: Prop) -> None:
    if "room" in world.entities:
        world.get("room").meters["chaos"] = 0
    world.get(prop.id).meters["mess"] = 0
    world.say(
        f"{helper.label_word.capitalize()} came in fast and {fix.text}."
    )
    world.say(
        f"The silly surprise settled down, and the room looked calm again."
    )


def rescue_fail(world: World, helper: Entity, fix: Fix, prop: Prop) -> None:
    world.say(
        f"{helper.label_word.capitalize()} tried to help, but {fix.fail}."
    )
    world.say(
        f"The joke got messier and messier until everyone had to back away."
    )


THEMES = {
    "living_room": Theme(
        "living_room",
        "the living room",
        "The sofa was a tiny stage, a blanket was a curtain, and a cardboard crown sat on the table.",
        "The Great Squeaky Bow",
        "Captain Snack",
        "a surprise prop",
        "In the end, the room was tidy, the joke was funnier, and Lee was bowing to a laughing audience.",
    ),
    "backyard": Theme(
        "backyard",
        "the backyard",
        "A plastic bucket was the drum, two sticks were the beat, and the porch step was the stage.",
        "The Mighty Pop",
        "Drum Coach",
        "a surprise balloon",
        "In the end, the stage stayed neat, and Lee bowed while the balloon rolled safely by.",
    ),
    "kitchen": Theme(
        "kitchen",
        "the kitchen",
        "A mixing bowl became a helmet, a spoon became a microphone, and the chair was the spotlight.",
        "The Noodle News",
        "Chef Sidekick",
        "a surprise carton",
        "In the end, the counter was clean again, and Lee finished the act with a proud grin.",
    ),
}

PROPS = {
    "pie": Prop("pie", "a pie", "the pie was sitting on the sill", "the surprise pie on the windowsill", risky=True, tags={"mess", "food"}),
    "soda": Prop("soda", "a fizzy soda", "the soda was waiting in a cup", "the fizzy soda on the table", risky=True, tags={"mess", "drink"}),
    "confetti": Prop("confetti", "a confetti tube", "the confetti was in a paper tube", "the confetti tube behind the chair", risky=True, tags={"mess", "party"}),
    "soap": Prop("soap", "a soap bar", "the soap was by the sink", "the slippery soap near the sink", risky=True, tags={"mess", "bath"}),
}

FIXES = {
    "tray": Fix("tray", 3, 3, "set the pie on a tray and kept it from sliding everywhere",
                "set the tray down, but the mess had already splashed across the table",
                "set the pie on a tray", tags={"clean"}),
    "napkins": Fix("napkins", 2, 2, "stacked napkins under the cup and saved the table",
                   "grabbed napkins, but the fizz was already all over the floor",
                   "stacked napkins under the cup", tags={"clean"}),
    "box": Fix("box", 3, 4, "pushed the confetti tube into a box and closed the lid",
               "found a box, but the confetti had already exploded like a tiny storm",
               "pushed the confetti tube into a box", tags={"clean"}),
    "towel": Fix("towel", 2, 2, "wrapped the soap in a towel so it would stop skidding away",
                 "wrapped the towel too late, and the soap had already scooted under the chair",
                 "wrapped the soap in a towel", tags={"clean"}),
}


GIRL_NAMES = ["Mia", "Zoe", "Ava", "Lena", "Nora"]
BOY_NAMES = ["Lee", "Max", "Finn", "Theo", "Owen"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    prop: str
    fix: str
    lee_name: str = "Lee"
    helper_name: str = "Mina"
    lee_gender: str = "boy"
    helper_gender: str = "girl"
    parent: str = "mother"
    delay: int = 0
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
    for theme in THEMES:
        for prop_id, prop in PROPS.items():
            if not hazard_at_risk(prop):
                continue
            for fix in FIXES.values():
                if fix.sense >= SENSE_MIN:
                    combos.append((theme, prop_id, fix.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small comedy storyworld about Lee, a surprise, and a lesson learned."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError("That fix is too silly to be a sensible ending.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.prop is None or c[1] == args.prop)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, prop, fix = rng.choice(sorted(combos))
    return StoryParams(
        theme=theme,
        prop=prop,
        fix=fix,
        lee_name="Lee",
        helper_name=rng.choice(["Mina", "June", "Nina", "Tess"]),
        lee_gender="boy",
        helper_gender="girl",
        parent=args.parent or rng.choice(["mother", "father"]),
        delay=rng.randint(0, 1),
    )


def tell(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.theme]
    prop = PROPS[params.prop]
    fix = FIXES[params.fix]

    lee = world.add(Entity(id=params.lee_name, kind="character", type=params.lee_gender, role="instigator"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    item = world.add(Entity(id=prop.id, type="prop", label=prop.label))
    world.facts["parent"] = parent
    world.facts["lee"] = lee
    world.facts["helper"] = helper
    world.facts["theme"] = theme
    world.facts["prop"] = prop
    world.facts["fix"] = fix
    world.facts["delay"] = params.delay

    opening(world, lee, helper, theme)
    world.para()
    build_tension(world, lee, helper, prop)
    temptation(world, lee, prop)
    warn(world, helper, lee, prop)
    defy(world, lee, prop)
    surprise_event(world, item)
    world.para()
    if is_contained(fix, prop, params.delay):
        rescue(world, helper, fix, prop)
        accept(world, lee, helper, theme, fix)
    else:
        rescue_fail(world, helper, fix, prop)
        world.say("Lee learned that funny ideas work better when they do not spill everywhere.")

    world.facts["outcome"] = "contained" if is_contained(fix, prop, params.delay) else "failed"
    world.facts["chaos"] = room.meters["chaos"]
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    theme, prop, fix = f["theme"], f["prop"], f["fix"]
    return [
        f'Write a comedy story for a small child about Lee in {theme.scene} that includes a surprise and a lesson learned.',
        f"Tell a funny story where Lee meets {prop.label} as a surprise and learns to use a sensible fix.",
        f'Write a child-friendly comedy with the word "lee" and a happy ending where the surprise turns into a lesson.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lee, helper, theme, prop, fix = f["lee"], f["helper"], f["theme"], f["prop"], f["fix"]
    return [
        ("Who is the story about?", f"It is about Lee and {helper.id}. They were trying to put on a funny show in {theme.scene}."),
        ("What surprise changed the plan?", f"The surprise was {prop.label}. It made the joke messy and turned the scene into a comic scramble."),
        ("What did Lee learn?", f"Lee learned that a funny idea still needs a careful plan. After that, Lee used {fix.qa_text} instead of making a bigger mess."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["prop"].tags) | set(f["fix"].tags) | {"lesson", "surprise", "comedy"}
    out = []
    if "surprise" in tags:
        out.append(("What is a surprise?", "A surprise is something unexpected. It can make people laugh, gasp, or stop and think for a moment."))
    if "lesson" in tags:
        out.append(("What is a lesson learned?", "A lesson learned is a good idea a character remembers after something happens. It helps them do better next time."))
    if "comedy" in tags:
        out.append(("What makes a story funny?", "A story can be funny when something unexpected happens and the characters react in a silly, harmless way."))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("living_room", "pie", "tray"),
    StoryParams("backyard", "confetti", "box"),
    StoryParams("kitchen", "soda", "napkins"),
]


ASP_RULES = r"""
valid(T,P,F) :- theme(T), prop(P), fix(F), risky(P), sensible(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for p, prop in PROPS.items():
        lines.append(asp.fact("prop", p))
        if prop.risky:
            lines.append(asp.fact("risky", p))
    for f, fix in FIXES.items():
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{sensitive_asp()}\n{extra}\n{show}\n"


def sensitive_asp() -> str:
    return "sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M."


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print("MISMATCH: generate smoke test failed:", e)
        rc = 1
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


def explain_rejection() -> str:
    return " (No story: this setup is not sensible enough for a comedy lesson.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, p, f in asp_valid_combos():
            print(f"  {t} {p} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
