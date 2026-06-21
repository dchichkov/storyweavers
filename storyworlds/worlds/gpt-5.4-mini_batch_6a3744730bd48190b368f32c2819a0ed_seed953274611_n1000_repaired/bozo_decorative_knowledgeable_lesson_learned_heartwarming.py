#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bozo_decorative_knowledgeable_lesson_learned_heartwarming.py
==============================================================================================

A small heartwarming storyworld about a child, a shy mishap, a decorative fix,
and a lesson learned. The seed words are woven into the premise: a bozo moment,
a decorative object, and a knowledgeable helper.

The world model keeps track of:
- a child's confidence and embarrassment
- the mess or damage around a decorative project
- a helpful character who knows how to fix things
- a lesson learned that turns the ending into a warmer image

This is a standalone script intended for the Storyweavers repo.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    damage: str
    keyword: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
    decorative: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    kind: str
    knowledgeable: bool = True
    fix_text: str = ""
    lesson_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.helper: Optional[Helper] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

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
        clone.objects = copy.deepcopy(self.objects)
        clone.helper = copy.deepcopy(self.helper)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in list(world.entities.values()):
        if actor.meters["messy"] < THRESHOLD:
            continue
        sig = ("mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for obj in world.objects.values():
            if obj.decorative and not obj.fragile:
                continue
            if obj.meters["clean"] < THRESHOLD:
                continue
            obj.meters["smeared"] += 1
            actor.memes["embarrassed"] += 1
            out.append("__smudge__")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            if act_id not in SETTINGS[setting].affords:
                continue
            for obj_id, obj in OBJECTS.items():
                if act.keyword == "paint" and obj.decorative and obj.fragile:
                    combos.append((setting, act_id, obj_id))
                if act.keyword == "glue" and obj.decorative:
                    combos.append((setting, act_id, obj_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    activity: str
    object_id: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", mood="soft and warm", affords={"paint", "glue"}),
    "workshop": Setting(id="workshop", place="the little workshop", mood="busy but cozy", affords={"paint", "glue"}),
    "living_room": Setting(id="living_room", place="the living room", mood="sunny and calm", affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(id="paint", verb="paint the frame", gerund="painting the frame", mess="painty", damage="paint on everything", keyword="paint", tags={"paint"}),
    "glue": Activity(id="glue", verb="glue on the stars", gerund="gluing on the stars", mess="sticky", damage="sticky spots", keyword="glue", tags={"glue"}),
}

OBJECTS = {
    "banner": ObjectThing(id="banner", label="decorative banner", phrase="a decorative banner", kind="decoration", fragile=True, decorative=True),
    "frame": ObjectThing(id="frame", label="decorative frame", phrase="a decorative frame", kind="decoration", fragile=True, decorative=True),
    "mobile": ObjectThing(id="mobile", label="decorative mobile", phrase="a decorative mobile", kind="decoration", fragile=True, decorative=True),
}

HELPERS = {
    "grandma": Helper(id="grandma", label="grandma", phrase="Grandma", kind="adult", knowledgeable=True, fix_text="carefully wiped the smudges away and added a fresh ribbon", lesson_text="showed how to slow down and ask before using the tricky glue", tags={"help"}),
    "uncle": Helper(id="uncle", label="uncle", phrase="Uncle", kind="adult", knowledgeable=True, fix_text="brushed the paint off and made the decoration sparkle again", lesson_text="explained that a little patience keeps pretty things pretty", tags={"help"}),
}

GIRL_NAMES = ["Maya", "Lina", "Iris", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Leo", "Ben"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("keyword", "bozo"))
    lines.append(asp.fact("keyword", "decorative"))
    lines.append(asp.fact("keyword", "knowledgeable"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,O) :- setting(S), activity(A), object(O).
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
    if py != cl:
        print("MISMATCH between python and ASP valid combos.")
        print("only in python:", sorted(py - cl))
        print("only in ASP:", sorted(cl - py))
        return 1
    print(f"OK: valid combo parity ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming decorative lesson world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--child", dest="child_name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", dest="helper_name")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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
              and (args.activity is None or c[1] == args.activity)
              and (args.object_id is None or c[2] == args.object_id)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, activity, object_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(list(HELPERS))
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    return StoryParams(setting=setting, activity=activity, object_id=object_id,
                       child_name=child_name, child_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper_cfg = HELPERS[params.helper_name]
    helper_type = params.helper_gender
    if helper_type in {"woman", "man"}:
        helper_ent = world.add(Entity(id=helper_cfg.label, kind="character", type=helper_type, role="helper"))
    else:
        helper_ent = world.add(Entity(id=helper_cfg.label, kind="character", type="woman", role="helper"))
    world.helper = helper_cfg
    obj = world.add_object(copy.deepcopy(OBJECTS[params.object_id]))
    act = ACTIVITIES[params.activity]

    child.memes["curious"] += 1
    obj.meters["clean"] = 1
    world.say(
        f"{child.id} was making something pretty in {world.setting.place}, "
        f"and {world.setting.mood} made the room feel extra kind."
    )
    world.say(
        f"{child.id} wanted to {act.verb}, because {obj.phrase} needed one more lovely touch."
    )
    world.say(
        f"But the idea was a little bozo, and soon {child.id}'s hands got {act.damage}."
    )
    child.meters["messy"] += 1

    world.para()
    world.say(
        f"Then {helper_cfg.label} came in, smiling with a knowledgeable look."
    )
    world.say(
        f"{helper_cfg.label_word.capitalize()} said it was all right, and helped {child.id} clean up."
    )
    helper_ent.memes["kind"] += 1
    obj.meters["smeared"] += 1
    world.say(
        f"Together they {helper_cfg.fix_text}, so the {obj.label} looked beautiful again."
    )

    world.para()
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} laughed softly, a little embarrassed but happy. "
        f"{child.id} learned that asking a knowledgeable helper early keeps decorative things safe."
    )
    world.say(
        f"By bedtime, the {obj.label} was bright, tidy, and glowing in the warm room."
    )
    world.facts.update(child=child, helper=helper_cfg, object=obj, activity=act, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "bozo", "decorative", and "knowledgeable".',
        f"Tell a gentle story where {f['child'].id} makes a bozo mistake with a decorative item, then a knowledgeable helper fixes it kindly.",
        f"Write a short lesson-learned story in a cozy setting where a child protects a decorative object by listening to a knowledgeable adult.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, obj, act = f["child"], f["helper"], f["object"], f["activity"]
    return [
        QAItem(question="What was the child doing?", answer=f"{child.id} was trying to {act.verb} to make the decorative item look even nicer."),
        QAItem(question="Why was the mistake called bozo?", answer=f"It was bozo because the child rushed in and got {act.damage} on their hands. The good news was that a knowledgeable helper was there to fix the problem kindly."),
        QAItem(question="What lesson did the child learn?", answer=f"{child.id} learned to ask for help before a small mistake could bother a decorative thing. That made the ending warm instead of sad."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does knowledgeable mean?", answer="Knowledgeable means someone knows a lot and can help with a problem in a smart way."),
        QAItem(question="What does decorative mean?", answer="Decorative means something is meant to look pretty or special, not to be used roughly."),
        QAItem(question="Why should you be careful with decorations?", answer="Some decorations can be delicate, so gentle hands help them stay nice for a long time."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    for o in world.objects.values():
        lines.append(f"  {o.id}: meters={dict((k,v) for k,v in o.meters.items() if v)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", activity="glue", object_id="banner", child_name="Maya", child_gender="girl", helper_name="grandma", helper_gender="woman"),
    StoryParams(setting="workshop", activity="paint", object_id="frame", child_name="Theo", child_gender="boy", helper_name="uncle", helper_gender="man"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.object_id not in OBJECTS or params.helper_name not in HELPERS:
        raise StoryError("Invalid parameters.")
    world = tell(params)
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
    if trace and sample.world:
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
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
