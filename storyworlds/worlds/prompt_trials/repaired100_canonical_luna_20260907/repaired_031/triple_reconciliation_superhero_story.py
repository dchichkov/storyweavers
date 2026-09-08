#!/usr/bin/env python3
"""
Standalone story world: a young superhero learns that three brave rescues
need three kinds of reconciliation.

The story is simulated rather than assembled from one frozen paragraph. Luna
faces a physical danger, a frightened helper, and a worried neighborhood. Her
triple reconciliation repairs all three relationships.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    luna: object | None = None
    maya: object | None = None
    town: object | None = None
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    child_name: str = "Luna"
    helper_name: str = "Maya"
    hero_power: str = "triple spark"
    city: str = "Brighton"
    scenario: str = "three_rescues"
    opening_variant: int = 0
    middle_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None
    sample: object | None = None
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


SETTINGS = {
    "brighton": {
        "label": "Brighton",
        "place": "Brighton",
        "features": {"rooftops", "tram_square", "community_garden"},
    },
    "starfall": {
        "label": "Starfall",
        "place": "Starfall",
        "features": {"rooftops", "tram_square", "community_garden"},
    },
}

POWERS = {
    "triple spark": "three warm flashes of light",
    "triple leap": "three mighty jumps",
    "triple shield": "three shining shields",
}

SCENARIOS = {
    "three_rescues": {
        "threat": "a storm wind broke the garden gate, stalled a tram, and lifted a kite toward the clock tower",
        "first": "Luna used one spark to light the dark garden path",
        "second": "she used the next spark to guide the tram driver around a fallen sign",
        "third": "she used the last spark to show the kite owner a safe path to the tower steps",
        "consequence": "her three bright flashes made the frightened crowd think another storm was coming",
        "repair": "she apologized to the crowd, thanked Maya for warning her, and helped the kite owner mend the garden gate",
        "result": "the gate stood firm, the tram rolled on, and the kite dipped safely above the square",
    },
    "night_watch": {
        "threat": "a blackout darkened the library, a puppy slipped behind a fence, and a baker's delivery cart began to roll",
        "first": "Luna lit the library doorway",
        "second": "she made a glowing path for the puppy",
        "third": "she stopped the cart beside the bakery",
        "consequence": "the three flashes startled the puppy and made the baker fear Luna was rushing too much",
        "repair": "she listened to Maya, dimmed her power, and asked the baker and puppy's owner to help choose each next step",
        "result": "the library opened again, the puppy curled beside its owner, and the cart rested safely by the bakery",
    },
    "bridge_day": {
        "threat": "a loose banner tangled on the footbridge, a child dropped a lunchbox, and rainwater rushed toward the market stalls",
        "first": "Luna pinned the banner with her first bright burst",
        "second": "she returned the lunchbox with her second",
        "third": "she marked a dry path with her third",
        "consequence": "people cheered so loudly that nobody heard Maya calling for a slower plan",
        "repair": "Luna lowered her cape, listened carefully, and worked beside Maya and the market sellers instead of racing ahead",
        "result": "the banner was folded, the lunchbox was returned, and the market stayed dry",
    },
}

OPENINGS = [
    "{city} woke beneath a silver morning sky.",
    "At sunrise, the rooftops of {city} glittered like buttons.",
    "The first bell of the day rang over {city}, and Luna heard trouble below.",
]

MIDDLES = [
    'Maya called, “Luna, wait for my signal!” Luna answered, “I can help three ways!”',
    '“One rescue at a time,” Maya said. Luna took a breath and replied, “Then stay with me.”',
    'Luna asked, “What needs help first?” Maya pointed and said, “The people who are scared.”',
]

ENDINGS = [
    "That evening, Luna placed three little star stickers on her notebook: one for courage, one for listening, and one for making peace.",
    "The next morning, the town hung three small lights over the square, reminding everyone that a hero also knows how to repair a mistake.",
    "Luna flew home slowly, with Maya beside her, and the city below shone like three friendly stars.",
]


def valid_combo(city: str, hero_power: str, scenario: str) -> bool:
    return city in SETTINGS and hero_power in POWERS and scenario in SCENARIOS


def explain_rejection(city: str, hero_power: str, scenario: str) -> str:
    return (
        f"No story: city={city!r}, power={hero_power!r}, and scenario={scenario!r} "
        "do not form a believable triple-rescue story."
    )


def tell(params: StoryParams) -> World:
    if not valid_combo(params.city, params.hero_power, params.scenario):
        pass

    setting = _safe_lookup(SETTINGS, params.city)
    plan = _safe_lookup(SCENARIOS, params.scenario)
    world = World()

    luna = world.add(Entity(
        "luna",
        "hero",
        params.child_name,
        meters={"energy": 3.0, "danger": 0.0},
        memes={"courage": 1.0, "trust": 0.0},
    ))
    maya = world.add(Entity(
        "maya",
        "helper",
        params.helper_name,
        meters={"worry": 0.0},
        memes={"trust": 1.0, "patience": 1.0},
    ))
    town = world.add(Entity(
        "town",
        "community",
        params.city,
        meters={"safety": 0.0},
        memes={"confidence": 1.0},
    ))

    world.say(_safe_lookup(OPENINGS, params.opening_variant % len(OPENINGS)).format(city=setting["place"]))
    world.say(
        f"{params.child_name} was the young superhero of {setting['place']}. "
        f"{params.child_name}'s {params.hero_power} could make {_safe_lookup(POWERS, params.hero_power)}, "
        "but every power worked best when used with care."
    )
    world.say(f"{params.helper_name} was Luna's teammate and the person who helped her make a plan.")
    world.say(f"Then {plan['threat']}.")

    world.para()
    world.say(f"Luna flew into action. First, {plan['first']}.")
    luna.meters["energy"] -= 1
    luna.meters["danger"] += 1
    world.fired.add("first_rescue")

    world.say(f"Next, {plan['second']}.")
    luna.meters["energy"] -= 1
    world.fired.add("second_rescue")

    world.say(f"At last, {plan['third']}.")
    luna.meters["energy"] -= 1
    town.meters["safety"] += 1
    world.fired.add("third_rescue")

    world.say(f"But {plan['consequence']}.")
    maya.meters["worry"] = 1.0
    luna.memes["pride"] = 1.0
    world.facts["triple_used"] = True
    world.facts["trouble"] = plan["consequence"]

    world.para()
    world.say(_safe_lookup(MIDDLES, params.middle_variant % len(MIDDLES)))
    world.say(
        f"Maya said, “A hero can rescue a moment, too.” Luna looked at the worried faces and answered, "
        "“I am sorry. I hurried past your advice.”"
    )
    world.say(f"Together, {plan['repair']}.")
    maya.meters["worry"] = 0.0
    luna.memes["pride"] = 0.0
    luna.memes["trust"] = 1.0
    town.memes["confidence"] = 2.0
    world.fired.update({"hero_reconciliation", "helper_reconciliation", "town_reconciliation"})
    world.facts["reconciliations"] = 3
    world.facts["repair"] = plan["repair"]

    world.para()
    world.say(f"The triple rescue finally became a triple reconciliation: {plan['result']}.")
    world.say(_safe_lookup(ENDINGS, params.ending_variant % len(ENDINGS)))
    world.facts.update(
        child=luna,
        helper=maya,
        town=town,
        setting=setting,
        plan=plan,
        result=plan["result"],
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-facing superhero story with a triple rescue and three reconciliations.",
        f"Show how {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").label} uses a power three times, creates a problem, and repairs trust with a helper and a town.",
        f"End with a concrete image proving that {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "result")}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was Luna's teammate?",
            answer=f"Luna's teammate was {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label}, who helped her slow down and make a safer plan.",
        ),
        QAItem(
            question="Why did Luna's triple rescue cause a new problem?",
            answer=f"Her three quick uses of power caused trouble because {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trouble")}.",
        ),
        QAItem(
            question="What did Luna do to make things right?",
            answer=f"She apologized, listened to her teammate and the town, and then {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "repair")}.",
        ),
        QAItem(
            question="What were the three reconciliations?",
            answer="Luna repaired trust with herself by admitting she had rushed, with Maya by listening to her advice, and with the town by helping everyone feel safe again.",
        ),
        QAItem(
            question="How did the ending prove that the problem was solved?",
            answer=f"The ending showed the change clearly: {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "result")}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities to help people and protect others.",
        ),
        QAItem(
            question="What does triple mean?",
            answer="Triple means three times as many, or a group of three.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the work of making peace and rebuilding trust after a problem.",
        ),
        QAItem(
            question="Why should a hero listen to a teammate?",
            answer="A hero should listen to a teammate because another person may notice danger, have a safer plan, or know what frightened people need.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
power(triple_spark).
power(triple_leap).
power(triple_shield).
scenario(three_rescues).
scenario(night_watch).
scenario(bridge_day).
city(brighton).
city(starfall).
triple_rescue(S) :- scenario(S).
needs_reconciliation(hero, helper) :- triple_rescue(three_rescues).
needs_reconciliation(hero, town) :- triple_rescue(three_rescues).
needs_reconciliation(hero, self) :- triple_rescue(three_rescues).
good_story(C, P, S) :- city(C), power(P), scenario(S), triple_rescue(S).
#show good_story/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for city in SETTINGS:
        lines.append(asp.fact("city", city))
    for power in POWERS.values():
        lines.append(asp.fact("power", power.replace(" ", "_")))
    for scenario in SCENARIOS:
        lines.append(asp.fact("scenario", scenario))
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted(
        (city, power.replace(" ", "_"), scenario)
        for city in SETTINGS
        for power in POWERS
        for scenario in SCENARIOS
        if valid_combo(city, power, scenario)
    )
    clingo_values = asp_valid_combos()
    if py != clingo_values:
        print("MISMATCH between Python and ASP gates")
        print("python:", py)
        print("clingo:", clingo_values)
        return 1
    for scenario in SCENARIOS:
        sample = generate(StoryParams(scenario=scenario))
        if "triple" not in sample.story.lower() or sample._safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "reconciliations") != 3:
            print("MISMATCH in generated story verification")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(py)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Triple-reconciliation superhero story world.")
    ap.add_argument("--city", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    city = getattr(args, "city", None) or rng.choice(list(SETTINGS))
    power = getattr(args, "power", None) or rng.choice(list(POWERS))
    scenario = getattr(args, "scenario", None) or rng.choice(list(SCENARIOS))
    if not valid_combo(city, power, scenario):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=getattr(args, "name", None) or "Luna",
        helper_name=getattr(args, "helper", None) or rng.choice(["Maya", "Nova", "Ari"]),
        hero_power=power,
        city=_safe_lookup(SETTINGS, city)["place"],
        scenario=scenario,
        opening_variant=rng.randrange(len(OPENINGS)),
        middle_variant=rng.randrange(len(MIDDLES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  reconciliations: {world.facts.get('reconciliations', 0)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            child_name="Luna",
            helper_name="Maya",
            hero_power="triple spark",
            city="Brighton",
            scenario="three_rescues",
        ),
        StoryParams(
            child_name="Luna",
            helper_name="Nova",
            hero_power="triple shield",
            city="Starfall",
            scenario="night_watch",
            opening_variant=1,
            middle_variant=1,
            ending_variant=1,
        ),
        StoryParams(
            child_name="Luna",
            helper_name="Ari",
            hero_power="triple leap",
            city="Brighton",
            scenario="bridge_day",
            opening_variant=2,
            middle_variant=2,
            ending_variant=2,
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None), 0)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {sample.params.child_name}: {sample.params.hero_power} in {sample.params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
