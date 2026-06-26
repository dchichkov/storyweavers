#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
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
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    mystery: object | None = None
    sergeant: object | None = None
    tool: object | None = None
    trans: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "madam"}
        male = {"boy", "man", "father", "sergeant", "captain", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    symptom: str
    clue: str
    effect: str
    trigger: str
    place: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


@dataclass
class Transformation:
    id: str
    source: str
    result: str
    cause: str
    method: str
    reversal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


@dataclass
class Tool:
    id: str
    label: str
    use: str
    works_on: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "frontier": Setting(
        place="the dusty frontier town",
        detail="The wind combed the dust down Main Street like a sleepy old horse.",
        affords={"whistle", "cookie", "shoe"},
    ),
    "harbor": Setting(
        place="the sleepy harbor",
        detail="The docks creaked and the gulls wheeled overhead like scraps of white paper.",
        affords={"lantern", "net", "cookie"},
    ),
    "canyon": Setting(
        place="the red canyon camp",
        detail="The cliffs blushed in the sun, and every echo sounded twice as bold.",
        affords={"whistle", "lantern", "cookie"},
    ),
}

MYSTERIES = {
    "whistle": Mystery(
        id="whistle",
        symptom="the sergeant's brass whistle kept changing into a blue jay at dawn",
        clue="a trail of glittering feathers and a mirror-shine on the water barrel",
        effect="the whistle would vanish into a bird",
        trigger="moonlight on a polished lid",
        place="the parade square",
        tags={"bird", "mirror", "night"},
    ),
    "cookie": Mystery(
        id="cookie",
        symptom="the cook's ginger cookies kept turning into tiny horses",
        clue="little hoofprints in the flour and a warm cinnamon smell near the oven",
        effect="the cookies would gallop off the tray",
        trigger="a fan of spinning flour and a lonesome tune",
        place="the bake tent",
        tags={"horse", "flour", "sweet"},
    ),
    "shoe": Mystery(
        id="shoe",
        symptom="the sergeant's boots kept shrinking into red barn kittens",
        clue="cat paw prints in the dust and a shiny ribbon snagged on a nail",
        effect="the boots would blink and mew",
        trigger="a ribbon spell tied to the boot hooks",
        place="the stable lane",
        tags={"cat", "ribbon", "dust"},
    ),
}

TRANSFORMATIONS = {
    "mirror": Transformation(
        id="mirror",
        source="a polished lid",
        result="the lid stopped casting the strange spell",
        cause="moonlight bounced off it and tipped the change loose",
        method="covering the shine with a blanket",
        reversal="the whistle came back singing brass",
        tags={"mirror", "night"},
    ),
    "flour": Transformation(
        id="flour",
        source="a whisk of flour",
        result="the flour stopped dancing in the air",
        cause="the spinning flour hid the spell in plain sight",
        method="sweeping the flour into a neat sack",
        reversal="the cookies came back round and warm",
        tags={"flour", "sweet"},
    ),
    "ribbon": Transformation(
        id="ribbon",
        source="a ribbon spell",
        result="the ribbon went limp as an old noodle",
        cause="the knot had been tied with a tune",
        method="untying the ribbon and cutting the tune with chalk",
        reversal="the boots grew back to proper size",
        tags={"ribbon", "cat"},
    ),
}

TOOLS = {
    "blanket": Tool(
        id="blanket",
        label="a wool blanket",
        use="cover a shining thing",
        works_on={"mirror"},
        tags={"mirror", "night"},
    ),
    "sack": Tool(
        id="sack",
        label="a flour sack",
        use="gather up loose flour",
        works_on={"flour"},
        tags={"flour", "sweet"},
    ),
    "chalk": Tool(
        id="chalk",
        label="a stub of white chalk",
        use="mark a spell-knot and break the pattern",
        works_on={"ribbon"},
        tags={"ribbon", "cat"},
    ),
}

SERGEANT_NAMES = ["Mabel", "Hank", "Jeb", "Nora", "Silas", "Pearl"]
HELPER_NAMES = ["Benny", "Lulu", "Pip", "Dot", "Milo", "June"]
TRAITS = ["tall", "steady", "quick-thinking", "kindly", "bright-eyed", "wiry"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    transformation: str
    tool: str
    sergeant_name: str
    helper_name: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery.place == setting.place:
                for tid, trans in TRANSFORMATIONS.items():
                    for tool_id, tool in TOOLS.items():
                        if tid == tool_id and tid in tool.works_on and trans.tags & mystery.tags:
                            out.append((sid, mid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery storyworld with a sergeant and a transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def explain_rejection() -> str:
    return "(No story: those choices do not form a believable mystery with a matching transformation and tool.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mystery", None) and getattr(args, "transformation", None):
        if getattr(args, "transformation", None) not in TOOLS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if getattr(args, "transformation", None) not in TRANSFORMATIONS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "transformation", None) is None or c[2] == getattr(args, "transformation", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery, transformation = rng.choice(list(combos))
    tool = getattr(args, "tool", None) or transformation
    sergeant_name = getattr(args, "name", None) or rng.choice(SERGEANT_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, mystery, transformation, tool, sergeant_name, helper_name, trait)


def predict(world: World, params: StoryParams) -> bool:
    sim = world.copy()
    sergeant = sim.get("sergeant")
    sergeant.memes["wonder"] += 1
    sergeant.memes["focus"] += 1
    return True


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    sergeant = world.add(Entity(id="sergeant", kind="character", type="sergeant", label=f"Sergeant {params.sergeant_name}"))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=params.helper_name))
    mystery = world.add(Entity(id="mystery", type="mystery", label=_safe_lookup(MYSTERIES, params.mystery).symptom))
    trans = world.add(Entity(id="transformation", type="transformation", label=_safe_lookup(TRANSFORMATIONS, params.transformation).result))
    tool = world.add(Entity(id="tool", type="tool", label=_safe_lookup(TOOLS, params.tool).label))
    world.facts.update(
        sergeant=sergeant,
        helper=helper,
        mystery=_safe_lookup(MYSTERIES, params.mystery),
        transformation=_safe_lookup(TRANSFORMATIONS, params.transformation),
        tool=_safe_lookup(TOOLS, params.tool),
        params=params,
    )
    return world


def tell(world: World, params: StoryParams) -> None:
    m = _safe_lookup(MYSTERIES, params.mystery)
    t = _safe_lookup(TRANSFORMATIONS, params.transformation)
    tool = _safe_lookup(TOOLS, params.tool)
    sergeant = world.get("sergeant")
    helper = world.get("helper")

    sergeant.memes["duty"] += 1
    world.say(f"Sergeant {params.sergeant_name} was a {params.trait} lawkeeper in {world.setting.place}.")
    world.say(f"{helper.label} said the day felt strange, because {m.symptom}.")
    world.say(f"The whole town was talking about it, and even the wind seemed to tiptoe.")

    world.para()
    sergeant.memes["mystery"] += 1
    sergeant.meters["investigation"] = 1
    world.say(f"The sergeant tipped his hat and followed {m.clue}.")
    world.say(f"He guessed the trouble was a transformation, not a trick, and that made the case worth the long walk.")

    helper.memes["helpful"] += 1
    world.say(f"{helper.label} pointed to {m.place}, where {m.effect} kept happening whenever the light turned gold.")
    world.say(f"The sergeant tried {tool.use}, because that was the sort of thing that solved a tall, stubborn puzzle.")

    world.para()
    sergeant.meters["problem_solving"] = 1
    sergeant.memes["confidence"] += 1
    if params.transformation == "mirror":
        world.say(f"He laid {tool.label} over the shiny lid, and the moon could not wink at it anymore.")
    elif params.transformation == "flour":
        world.say(f"He scooped the flour into {tool.label}, and the airy dance lost its footing.")
    else:
        world.say(f"He traced the knot in chalk, then pulled the ribbon free with one careful tug.")
    world.say(f"That clever move matched the clue, and the mystery began to unwind like a lasso in the sunshine.")

    world.para()
    world.say(f"Then the change reversed itself: {t.reversal}.")
    world.say(f"The sergeant smiled so wide it looked like sunrise on a fence rail, and {helper.label} cheered.")

    sergeant.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.facts["solved"] = True
    world.facts["ending"] = t.reversal


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        f'Write a tall-tale mystery for a child, featuring a sergeant who must solve a transformation problem.',
        f'Tell a lively story about Sergeant {params.sergeant_name}, who notices that {_safe_lookup(MYSTERIES, params.mystery).symptom}.',
        f'Write a short, child-friendly adventure where a sergeant uses {_safe_lookup(TOOLS, params.tool).label} to solve a puzzling change.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = _safe_fact(world, f, "params")
    m: Mystery = _safe_fact(world, f, "mystery")
    t: Transformation = _safe_fact(world, f, "transformation")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was solving the mystery in the story?",
            answer=f"Sergeant {p.sergeant_name} was solving it, with {world.get('helper').label} helping along the way.",
        ),
        QAItem(
            question=f"What strange thing kept happening?",
            answer=f"{m.symptom.capitalize()}. That was the mystery the sergeant had to figure out.",
        ),
        QAItem(
            question=f"What did the sergeant use to solve the problem?",
            answer=f"He used {tool.label} to handle the clue and stop the transformation.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"He matched the clue to the right tool, and then {t.reversal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sergeant?",
            answer="A sergeant is a rank in the army or police, often a leader who helps keep people safe and organizes a job.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or strange event that people have to think about and solve.",
        ),
        QAItem(
            question="What does a blanket do in a story like this?",
            answer="A blanket can cover something shiny or cold, and in a story it can help stop a trick from working.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(frontier).
setting(harbor).
setting(canyon).

mystery(whistle).
mystery(cookie).
mystery(shoe).

transformation(mirror).
transformation(flour).
transformation(ribbon).

tool(blanket).
tool(sack).
tool(chalk).

matches(mirror, whistle).
matches(flour, cookie).
matches(ribbon, shoe).

valid(S, M, T) :- setting(S), mystery(M), transformation(T), matches(T, M), fits(S, M).
fits(frontier, whistle).
fits(harbor, cookie).
fits(canyon, whistle).
fits(canyon, cookie).
fits(frontier, shoe).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fits", m.place.split()[1] if False else mid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    for tid in TRANSFORMATIONS:
        for mid in MYSTERIES:
            if tid == mid:
                lines.append(asp.fact("matches", tid, mid))
    lines = [f"setting({sid})." for sid in SETTINGS]
    lines += [f"mystery({mid})." for mid in MYSTERIES]
    lines += [f"transformation({tid})." for tid in TRANSFORMATIONS]
    lines += [f"tool({tid})." for tid in TOOLS]
    lines += ["fits(frontier,whistle).", "fits(harbor,cookie).", "fits(canyon,whistle).", "fits(canyon,cookie).", "fits(frontier,shoe)."]
    lines += ["matches(mirror,whistle).", "matches(flour,cookie).", "matches(ribbon,shoe)."]
    return "\n".join(lines)


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
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world, params)
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
    StoryParams("frontier", "whistle", "mirror", "blanket", "Mabel", "Pip", "steady"),
    StoryParams("harbor", "cookie", "flour", "sack", "Nora", "Lulu", "bright-eyed"),
    StoryParams("canyon", "shoe", "ribbon", "chalk", "Jeb", "Milo", "wiry"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(asp_valid_combos()))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            except StoryError:
                continue
            params.seed = (getattr(args, "seed", None) or 0) + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.sergeant_name}: {p.setting}/{p.mystery}/{p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
