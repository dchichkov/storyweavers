#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spank_chaotic_twist_lesson_learned_nursery_rhyme.py
==========================================================================================================

A small nursery-rhyme storyworld with a playful rhyme-voice, a chaotic mishap,
a twist, and a lesson learned.

The story premise is simple:
- A little child and a helper live in a cozy cottage.
- The child wants to make music and bake at once.
- A chaotic tumble turns the kitchen into a mess.
- A twist reveals the helper's clever plan.
- The ending proves the lesson learned: slower, kinder, tidier play works better.

This world models physical meters and emotional memes, and it includes an inline
ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

NURSERY_OPENERS = [
    "Hush now, hush, in a cottage bright,",
    "Tick-tock, tick-tock, in the morning light,",
    "Tip-tip toes on the wooden floor,",
    "Sing-song voices near the kitchen door,",
]

NURSERY_CLOSERS = [
    "And that's how the day grew calm and clear.",
    "So the little one learned to slow down near.",
    "And the cottage shone by candlelight.",
    "So the lesson stayed warm in the heart that night.",
]

GIVEN_NAMES = ["Mina", "Pip", "Toby", "Nell", "Wren", "Lulu", "Hugo", "Poppy"]
HELPER_NAMES = ["Gran", "Auntie Dot", "Mama", "Papa", "Uncle Ned", "The Neighbored Cat"]

LOCATIONS = {
    "cottage": "the cozy cottage",
    "kitchen": "the little kitchen",
    "garden": "the back garden",
    "porch": "the sunlit porch",
}

ACTIVITIES = {
    "bake": {
        "verb": "bake buns",
        "gerund": "baking buns",
        "rush": "dash to the flour tin",
        "mess": "floury",
        "soil": "all floury",
        "zone": {"hands", "torso"},
        "word": "flour",
        "tags": {"flour", "bake"},
    },
    "paint": {
        "verb": "paint a sign",
        "gerund": "painting signs",
        "rush": "grab the paint pot",
        "mess": "painted",
        "soil": "splashed with paint",
        "zone": {"hands", "torso"},
        "word": "paint",
        "tags": {"paint", "craft"},
    },
    "jam": {
        "verb": "stir jam",
        "gerund": "stirring jam",
        "rush": "run to the jam jar",
        "mess": "sticky",
        "soil": "sticky and sweet",
        "zone": {"hands", "torso"},
        "word": "jam",
        "tags": {"jam", "cook"},
    },
}

PROPS = {
    "apron": {
        "label": "a small apron",
        "phrase": "a small apron with blue ties",
        "region": "torso",
        "plural": False,
    },
    "shirt": {
        "label": "a bright shirt",
        "phrase": "a bright shirt with tiny stars",
        "region": "torso",
        "plural": False,
    },
    "trousers": {
        "label": "little trousers",
        "phrase": "little trousers with soft knees",
        "region": "legs",
        "plural": True,
    },
    "shoes": {
        "label": "shiny shoes",
        "phrase": "shiny shoes with velcro tabs",
        "region": "feet",
        "plural": True,
    },
}

GEAR = [
    {
        "id": "apron",
        "label": "a clean apron",
        "covers": {"torso"},
        "guards": {"floury", "painted", "sticky"},
        "prep": "tie on a clean apron first",
        "tail": "walked back for a clean apron",
        "plural": False,
    },
    {
        "id": "old_shirt",
        "label": "an old shirt",
        "covers": {"torso"},
        "guards": {"floury", "painted", "sticky"},
        "prep": "put on an old shirt first",
        "tail": "dug out an old shirt",
        "plural": False,
    },
    {
        "id": "play_clothes",
        "label": "old play clothes",
        "covers": {"torso", "legs"},
        "guards": {"floury", "painted", "sticky"},
        "prep": "change into old play clothes",
        "tail": "changed into old play clothes",
        "plural": True,
    },
]

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    g: object | None = None
    helper: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    child_name: str
    child_type: str
    helper_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _meters_add(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _memes_add(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _rule_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for kind, value in list(actor.meters.items()):
            if value < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                _meters_add(item, kind, 1)
                _meters_add(item, "dirty", 1)
                out.append(f"{actor.id}'s {item.label} got messy.")
    return out


def _rule_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        _meters_add(carer, "workload", 1)
        out.append("That meant more washing and more wiping.")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_soil, _rule_workload):
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def prize_risk(activity: dict, prop: dict) -> bool:
    return prop["region"] in activity["zone"]


def gear_fix(activity: dict, prop: dict) -> Optional[dict]:
    for gear in GEAR:
        if activity["mess"] in gear["guards"] and prop["region"] in gear["covers"]:
            return gear
    return None


def predict(world: World, child: Entity, activity: dict, prop: Entity) -> dict:
    sim = World()
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(activity["zone"])
    sim.get(child.id).meters[activity["mess"]] = 1.0
    propagate(sim)
    return {
        "soiled": bool(sim.get(prop.id).meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sim.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper").id).meters.get("workload", 0.0),
    }


def tell(params: StoryParams) -> World:
    if params.place not in LOCATIONS:
        pass
    if params.activity not in ACTIVITIES:
        pass
    if params.prop not in PROPS:
        pass

    activity = _safe_lookup(ACTIVITIES, params.activity)
    prop_cfg = _safe_lookup(PROPS, params.prop)

    world = World()
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="adult",
        label=params.helper_name,
    ))
    prop = world.add(Entity(
        id="prop",
        type=params.prop,
        label=prop_cfg["label"],
        phrase=prop_cfg["phrase"],
        owner=child.id,
        caretaker=helper.id,
        region=prop_cfg["region"],
        plural=prop_cfg["plural"],
    ))
    prop.worn_by = child.id

    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["prop"] = prop
    world.facts["activity"] = activity
    world.facts["params"] = params

    opener = random.choice(NURSERY_OPENERS)
    world.say(opener)
    world.say(
        f"{child.id} was a little {child.type} with a heart full of song, "
        f"and {helper.id} kept the kettle warm and the table long."
    )
    world.say(
        f"{child.id} loved {activity['gerund']}, and the word of the day was {activity['word']}."
    )
    world.say(
        f"{helper.id} had bought {child.pronoun('object')} {prop.phrase}, and {child.id} wore {(getattr(prop, 'it')() if callable(getattr(prop, 'it', None)) else getattr(prop, 'it', 'it'))} proudly."
    )

    world.para()
    world.say(
        f"One bright day in {_safe_lookup(LOCATIONS, params.place)}, {child.id} wanted to {activity['verb']} at once."
    )
    world.say(
        f"Down went the spoon with a spank, spank sound, and the whole room grew a little chaotic."
    )
    _memes_add(child, "eager", 1)
    _memes_add(child, "joy", 1)
    _meters_add(child, activity["mess"], 1)
    world.zone = set(activity["zone"])

    pre = predict(world, child, activity, prop)
    if pre["soiled"]:
        world.say(
            f"{helper.id} frowned, for {prop.label} would get {activity['soil']} if the rush kept up."
        )
        _memes_add(child, "worry", 1)
    else:
        world.say(f"{helper.id} still watched closely, just in case the day turned twisty.")

    world.say(
        f"{child.id} nearly dashed to the {activity['word']} tin, but {helper.id} held up a gentle hand."
    )
    _memes_add(child, "defiance", 1)
    world.say(
        f"Then came the twist: under the tea towel sat a tidy helper plan, with bowls already lined in a row."
    )

    gear = gear_fix(activity, prop_cfg)
    if gear is None:
        _fallback_pool = globals().get("GEARS") or globals().get("GEARES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        gear = next(iter(_fallback_pool), None)
        if gear is None:
            raise StoryError
    g = world.add(Entity(
        id=gear["id"],
        kind="thing",
        type="gear",
        label=gear["label"],
        phrase=gear["label"],
        owner=child.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear["covers"]),
        plural=gear["plural"],
    ))
    g.worn_by = child.id

    world.say(
        f"{helper.id} said, 'First, we {gear['prep']}, and then we may {activity['verb']} together.'"
    )
    _memes_add(child, "love", 1)
    _memes_add(child, "joy", 1)
    child.memes["defiance"] = 0.0
    world.say(
        f"{child.id} nodded and smiled, for the lesson learned was plain: slow paws make fewer messes."
    )
    world.say(
        f"So they {gear['tail']}, and soon {child.id} was {activity['gerund']}, while {prop.label} stayed clean."
    )
    world.say(random.choice(NURSERY_CLOSERS))

    world.facts["gear"] = g
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    a = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity")
    return [
        f'Write a short nursery-rhyme story about a child named {p.child_name} who wants to {a["verb"]}.',
        f"Tell a gentle rhyme where {p.child_name} makes a chaotic mess, then learns a lesson with {p.helper_name}.",
        f'Write a child-friendly story that uses the words "spank", "chaotic", "twist", and "lesson learned".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    a = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity")
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prop")
    gear = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gear")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, a little {child.type}, and {helper.id}, who helps keep the cottage calm.",
        ),
        QAItem(
            question=f"What did {child.id} want to do in the story?",
            answer=f"{child.id} wanted to {a['verb']}, but the day turned chaotic before the helper stepped in.",
        ),
        QAItem(
            question=f"What did {helper.id} buy or provide for {child.id}?",
            answer=f"{helper.id} provided {prop.phrase}, and later a tidy plan so {child.id} could play safely.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that a tidy helper plan was already waiting under the tea towel, so the problem could be solved without any extra fuss.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that slowing down and choosing the tidy way helps keep clothes clean and play happy.",
        ),
        QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} helped by covering the right part of the body, so {child.id} could {a['verb']} without ruining {prop.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flour?",
            answer="Flour is a soft powder made from grain. It is used for bread, buns, and cakes.",
        ),
        QAItem(
            question="Why do people wear aprons?",
            answer="People wear aprons to keep clothes clean when they cook, paint, or do other messy work.",
        ),
        QAItem(
            question="What does it mean when something is chaotic?",
            answer="Chaotic means noisy and messy, with many things happening at once in a way that is hard to keep tidy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
risk(A,P) :- activity(A), prop(P), splashes(A,R), worn_on(P,R).
fix(A,P) :- risk(A,P), activity(A), prop(P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
valid_story(Place,A,P) :- setting(Place), affords(Place,A), risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in LOCATIONS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "bake"))
        lines.append(asp.fact("affords", sid, "paint"))
        lines.append(asp.fact("affords", sid, "jam"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a["mess"]))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("worn_on", pid, p["region"]))
    for g in GEAR:
        lines.append(asp.fact("gear", g["id"]))
        for m in sorted(g["guards"]):
            lines.append(asp.fact("guards", g["id"], m))
        for r in sorted(g["covers"]):
            lines.append(asp.fact("covers", g["id"], r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Mirror the Python gate with the ASP twin.
    py = set()
    for place in LOCATIONS:
        for aid, act in ACTIVITIES.items():
            for pid, prop in PROPS.items():
                if prize_risk(act, prop) and gear_fix(act, prop):
                    py.add((place, aid, pid))
    asp_set = set(asp_valid_stories())
    if asp_set == py:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Only in ASP:", sorted(asp_set - py))
    print("Only in Python:", sorted(py - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with a chaotic twist and a lesson learned.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--child-type", choices=["girl", "boy"], default=None)
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
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    name = getattr(args, "name", None) or rng.choice(GIVEN_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    act = _safe_lookup(ACTIVITIES, activity)
    pr = _safe_lookup(PROPS, prop)
    if not prize_risk(act, pr):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if gear_fix(act, pr) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, prop=prop, child_name=name, child_type=child_type, helper_name=helper)


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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:\n")
        for place, act, prop in stories:
            print(place, act, prop)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("cottage", "bake", "apron", "Mina", "girl", "Gran"),
            StoryParams("kitchen", "paint", "shirt", "Pip", "boy", "Mama"),
            StoryParams("garden", "jam", "trousers", "Nell", "girl", "Papa"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {sample.params.child_name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
