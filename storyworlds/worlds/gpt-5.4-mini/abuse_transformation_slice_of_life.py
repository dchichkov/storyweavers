#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/abuse_transformation_slice_of_life.py
====================================================================

A small storyworld about a gentle slice-of-life day in which a child notices an
abused, worn-out toy or plant, helps it recover, and watches it transform into
something cared for and loved again.

The world is intentionally tiny and state-driven:
- a child, a caretaker, and one fragile object
- physical meters for wear, dirt, water, and bloom/shine
- emotional memes for hurt, care, relief, and pride
- one causal turn where respectful care changes the object's state

The story keeps the tone soft and everyday while still using the required word
"abuse" in a child-appropriate way: the object was mistreated before the story
begins, and the child chooses gentle care instead.
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
    activity: str

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
class ObjectSpec:
    id: str
    label: str
    kind: str
    starting_state: str
    hurt_kind: str
    repair_kind: str
    recovered_state: str
    transformed_state: str
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
class CareAction:
    id: str
    sense: int
    repair_power: int
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


def _r_recovery(world: World) -> list[str]:
    out: list[str] = []
    for obj in list(world.entities.values()):
        if obj.meters["hurt"] >= THRESHOLD and ("recovery", obj.id) not in world.fired:
            world.fired.add(("recovery", obj.id))
            obj.meters["sad"] += 1
            world.get("child").memes["concern"] += 1
            out.append("__recovery__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for obj in list(world.entities.values()):
        if obj.meters["clean"] >= THRESHOLD and obj.meters["fixed"] >= THRESHOLD:
            sig = ("transform", obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["bloom"] += 1
            obj.meters["warm"] += 1
            out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("recovery", "physical", _r_recovery), Rule("transformation", "physical", _r_transformation)]


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


def abuse_hurts(obj: ObjectSpec) -> bool:
    return obj.hurt_kind in {"torn", "dirty", "droopy", "scratched"}


def sensible_actions() -> list[CareAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    act = ACTIONS[params.action]
    spec = OBJECTS[params.obj]
    if act.repair_power >= 2 or (spec.kind == "plant" and act.id == "water_and_sun"):
        return "healed"
    return "mended"


def _care(world: World, obj: Entity, action: CareAction, narrate: bool = True) -> None:
    obj.meters["clean"] += 1
    obj.meters["fixed"] += 1 if action.repair_power >= 2 else 0.5
    obj.memes["trusted"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, caretaker: Entity, setting: Setting, obj: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {caretaker.label_word} sat at {setting.place}. "
        f"{setting.mood.capitalize()} light filled the room, and the day moved at a slow, ordinary pace."
    )
    world.say(
        f"{child.id} noticed {obj.label}, a little {obj.attrs.get('state_word', 'worn')}, {obj.attrs.get('thing_word', 'thing')}."
    )


def reveal_abuse(world: World, child: Entity, obj: Entity) -> None:
    child.memes["concern"] += 1
    world.say(
        f"{child.id} leaned closer and saw that {obj.label} had been hurt by abuse before."
        f" It looked tired, and the child felt a soft ache of worry."
    )


def ask_help(world: World, caretaker: Entity, child: Entity, obj: Entity) -> None:
    world.say(
        f'"We can help gently," {caretaker.label_word} said. "{obj.label} needs care, not more rough hands."'
    )


def choose_care(world: World, child: Entity, action: CareAction, obj: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f'{child.id} nodded. "{action.text.format(target=obj.label)}"'
    )


def apply_care(world: World, caretaker: Entity, child: Entity, obj: Entity, action: CareAction, spec: ObjectSpec) -> None:
    _care(world, obj, action)
    obj.meters["hurt"] = max(0.0, obj.meters["hurt"] - action.repair_power)
    world.say(
        f"{caretaker.label_word.capitalize()} helped {child.id} {action.qa_text.format(target=obj.label)}."
    )


def transform(world: World, child: Entity, caretaker: Entity, obj: Entity, spec: ObjectSpec) -> None:
    child.memes["pride"] += 1
    caretaker.memes["warmth"] += 1
    obj.attrs["state_word"] = spec.transformed_state
    world.say(
        f"By the end, {obj.label} was no longer just {spec.starting_state}; it had become {spec.transformed_state}."
    )
    world.say(
        f"{child.id} smiled at the small change. The room felt calmer, and the little rescued thing looked loved again."
    )


SETTINGS = {
    "window_seat": Setting("window_seat", "the window seat", "sunny", "reading"),
    "kitchen_table": Setting("kitchen_table", "the kitchen table", "soft", "snacking"),
    "balcony": Setting("balcony", "the balcony", "warm", "watering plants"),
}

OBJECTS = {
    "plant": ObjectSpec("plant", "the little plant", "plant", "droopy and dusty", "dry", "watered", "healthy and green", "bright and leafier", {"plant", "abuse", "transformation"}),
    "toy": ObjectSpec("toy", "the old toy bunny", "toy", "scratched and sad", "torn", "stitched", "whole again", "clean and smiling", {"toy", "abuse", "transformation"}),
    "lamp": ObjectSpec("lamp", "the tiny lamp", "lamp", "smudged and dim", "dirty", "polished", "shiny again", "bright and glowing", {"lamp", "abuse", "transformation"}),
}

ACTIONS = {
    "water_and_sun": CareAction("water_and_sun", 3, 3, "Let's give {target} a drink and move it to the sunlight.", "tried to rush the fix", "watered {target} and set it in the sun", {"plant"}),
    "wash_and_wipe": CareAction("wash_and_wipe", 3, 2, "Let's wash {target} with warm water and wipe it dry.", "scrubbed without patience", "washed {target} and wiped it dry", {"toy", "lamp"}),
    "stitch_and_hug": CareAction("stitch_and_hug", 2, 2, "Let's stitch up {target} and hold it carefully.", "pulled at the seams too hard", "stitched {target} with steady hands", {"toy"}),
}

CHILD_NAMES = ["Mia", "Leo", "Ava", "Noah", "Lily", "Ben", "Zoe", "Finn"]
CARETAKER_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa", "Older Sister"]
SENSE_MIN = 2


@dataclass
@dataclass
class StoryParams:
    setting: str
    obj: str
    action: str
    child: str
    child_gender: str
    caretaker: str
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
    for sid, s in SETTINGS.items():
        for oid, o in OBJECTS.items():
            for aid, a in ACTIONS.items():
                if o.kind in a.tags:
                    combos.append((sid, oid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about gentle care, abuse, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
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
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    caretaker = args.caretaker or rng.choice(CARETAKER_NAMES)
    return StoryParams(setting, obj, action, name, gender, caretaker)


def tell(setting: Setting, spec: ObjectSpec, action: CareAction, child_name: str, child_gender: str, caretaker_name: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    caretaker = world.add(Entity(id=caretaker_name, kind="character", type="adult", role="caretaker", label=caretaker_name))
    obj = world.add(Entity(id="obj", type=spec.kind, label=spec.label, attrs={"state_word": spec.starting_state, "thing_word": spec.kind}))
    obj.meters["hurt"] = 1
    obj.memes["sad"] = 1

    intro(world, child, caretaker, setting, obj)
    world.para()
    reveal_abuse(world, child, obj)
    ask_help(world, caretaker, child, obj)
    choose_care(world, child, action, obj)
    world.para()
    apply_care(world, caretaker, child, obj, action, spec)
    transform(world, child, caretaker, obj, spec)
    world.facts.update(child=child, caretaker=caretaker, obj=obj, spec=spec, action=action, setting=setting, outcome="healed")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.obj], ACTIONS[params.action], params.child, params.child_gender, params.caretaker)
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
    return [
        f'Write a slice-of-life story for a young child about kindness, the word "abuse", and a gentle transformation involving {f["spec"].label}.',
        f"Tell a calm everyday story where {f['child'].id} notices {f['spec'].label} has been mistreated and helps {f['spec'].label} change for the better.",
        f'Write a small story with a soft ending in which care replaces abuse and {f["spec"].label} becomes something lovely again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, caretaker, obj, spec, action = f["child"], f["caretaker"], f["obj"], f["spec"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {caretaker.label_word}, and {spec.label}. The story stays close to an ordinary day and a small act of care."),
        (f"Why did {child.id} feel worried?",
         f"{child.id} felt worried because {spec.label} had been hurt by abuse before. It looked worn out, so {child.id} wanted to make it better instead of ignoring it."),
        (f"What did they do to help {spec.label}?",
         f"They used gentle care: {action.qa_text.format(target=spec.label)}. That kind treatment is what changed the object in the story."),
        (f"How did {spec.label} change by the end?",
         f"{spec.label.capitalize()} changed from {spec.starting_state} to {spec.transformed_state}. The new state shows that careful help can transform something that was badly treated."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spec"].tags) | set(f["action"].tags)
    out = []
    for tag in ["abuse", "transformation", "plant", "toy", "lamp"]:
        if tag in tags:
            if tag == "abuse":
                out.append(("What does abuse mean?", "Abuse means hurting, mistreating, or handling someone or something in a cruel way. It is wrong, and people should choose care instead."))
            if tag == "transformation":
                out.append(("What is a transformation?", "A transformation is a big change in how something looks or is. It can happen when time, care, or a helpful action changes it for the better."))
            if tag == "plant":
                out.append(("What does a plant need to grow well?", "A plant usually needs water, sunlight, and gentle care. If it gets those things, it can grow healthy and green."))
            if tag == "toy":
                out.append(("How do you take care of a toy?", "You take care of a toy by handling it gently, keeping it clean, and fixing small problems before they get worse."))
            if tag == "lamp":
                out.append(("How can you make a lamp look bright again?", "You can carefully clean a lamp so dust and smudges do not block the light. Gentle cleaning can make it shine again."))
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,A) :- setting(S), object(O), action(A), compatible(O,A).
healed(O) :- chosen(O), action(A), strong(A).
transformed(O) :- healed(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("compat_kind", oid, o.kind))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("strong", aid) if a.repair_power >= 2 else asp.fact("weak", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("window_seat", "plant", "water_and_sun", "Mia", "girl", "Mom"),
    StoryParams("kitchen_table", "toy", "stitch_and_hug", "Leo", "boy", "Dad"),
    StoryParams("balcony", "lamp", "wash_and_wipe", "Ava", "girl", "Aunt June"),
]


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life world about abuse, gentle care, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obj in OBJECTS.items():
            for aid, act in ACTIONS.items():
                if obj.kind in act.tags:
                    combos.append((sid, oid, aid))
    return combos


def story_knowledge_gate() -> None:
    return


if __name__ == "__main__":
    main()
