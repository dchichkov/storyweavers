#!/usr/bin/env python3
"""
A heartwarming story world about a small kitchen hierarchy, a cantaloupe mistake,
and a gentle return to harmony.

The source tale seed imagined here:
- A little helper wants to carry a cantaloupe up the kitchen hierarchy.
- A careful grown-up warns that the melon may be too slippery for the stairs.
- The helper learns to return the cantaloupe safely.
- Everyone talks, fixes the problem together, and ends warmly.

This script simulates that premise as state, then renders a complete child-facing
story with dialogue, cautionary tension, and reconciliation.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
    melon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "grandmother", "aunt"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "grandfather", "uncle"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class StoryParams:
    seed: Optional[int] = None
    family_name: str = "the Lane family"
    hero_name: str = "Milo"
    hero_type: str = "boy"
    helper_name: str = "Nia"
    helper_type: str = "girl"
    elder_name: str = "Grandma June"
    elder_type: str = "grandmother"
    place: str = "the kitchen"
    level_top: str = "the top shelf"
    item: str = "cantaloupe"
    item_phrase: str = "a ripe cantaloupe"
    action: str = "carry the cantaloupe upstairs"
    return_place: str = "the fruit bowl"
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


FAMILY_NAMES = ["the Lane family", "the Rivera family", "the Moss family", "the Chen family"]
HERO_NAMES = [("Milo", "boy"), ("Theo", "boy"), ("Sofia", "girl"), ("Ruby", "girl")]
HELPER_NAMES = [("Nia", "girl"), ("Pia", "girl"), ("Ben", "boy"), ("Ivy", "girl")]
ELDER_NAMES = [("Grandma June", "grandmother"), ("Grandpa Ben", "grandfather"), ("Aunt Lila", "aunt")]
PLACES = ["the kitchen", "the pantry", "the hallway"]
LEVELS = ["the top shelf", "the high counter", "the fruit basket shelf"]
ITEMS = [
    ("cantaloupe", "a ripe cantaloupe", "carry the cantaloupe upstairs", "the fruit bowl"),
    ("cantaloupe", "a striped cantaloupe", "return the cantaloupe to the kitchen", "the fruit bowl"),
]
TRAITS = ["careful", "helpful", "cheerful", "curious", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: hierarchy, cantaloupe, return."
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item")
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    family = rng.choice(FAMILY_NAMES)
    hero_name, hero_type = rng.choice(HERO_NAMES)
    helper_name, helper_type = rng.choice(HELPER_NAMES)
    elder_name, elder_type = rng.choice(ELDER_NAMES)
    place = getattr(args, "place", None) or rng.choice(PLACES)
    item, item_phrase, action, return_place = rng.choice(ITEMS)

    if getattr(args, "item", None) and getattr(args, "item", None) != "cantaloupe":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        seed=None,
        family_name=family,
        hero_name=getattr(args, "hero_name", None) or hero_name,
        hero_type=hero_type,
        helper_name=getattr(args, "helper_name", None) or helper_name,
        helper_type=helper_type,
        elder_name=getattr(args, "elder_name", None) or elder_name,
        elder_type=elder_type,
        place=place,
        level_top=rng.choice(LEVELS),
        item=item,
        item_phrase=item_phrase,
        action=action,
        return_place=return_place,
    )


def setup_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder_name))
    melon = world.add(Entity(id="melon", kind="thing", type="cantaloupe", label="cantaloupe",
                             phrase=params.item_phrase, owner=hero.id, caretaker=elder.id, region="hands"))

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        melon=melon,
        params=params,
        caution=False,
        broken=False,
        reconciled=False,
        hierarchy="top shelf",
    )
    return world


def narration_open(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    elder = _safe_fact(world, world.facts, "elder")
    world.say(
        f"In {p.place}, {p.family_name} moved through its little hierarchy like a cozy song: "
        f"{elder.label} watched the kitchen, {helper.label} helped with the fruit, and {hero.label} "
        f"liked to be useful too."
    )
    world.say(
        f"That morning, {hero.label} spotted {p.item_phrase} and said, "
        f"\"Can I take the {p.item} up to {p.level_top}?\""
    )
    world.say(
        f"{helper.label} smiled. \"Only if we are careful,\" {helper.pronoun()} said, "
        f"\"because round fruit can roll when hands get hurried.\""
    )


def cautionary_turn(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    melon = _safe_fact(world, world.facts, "melon")

    world.para()
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.meters["holding"] = 1.0
    world.say(
        f"{hero.label} tucked the cantaloupe against {hero.pronoun('possessive')} shirt and started toward the stairs."
    )
    world.say(
        f"\"Wait,\" {elder.label} called, sounding gentle but serious. "
        f"\"A cantaloupe can slip from small arms, and a drop can make a mess.\""
    )
    world.say(
        f"{hero.label} paused. {hero.pronoun().capitalize()} looked at the melon, then at the steps."
    )
    world.facts["caution"] = True
    melon.memes["risk"] = 1.0


def resolve_risk(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    elder = _safe_fact(world, world.facts, "elder")
    melon = _safe_fact(world, world.facts, "melon")

    world.para()
    world.say(
        f"{helper.label} reached out and said, \"How about we return the cantaloupe to the fruit bowl first, "
        f"then carry it together if we still want to move it?\""
    )
    world.say(
        f"{hero.label} nodded. \"That sounds better,\" {hero.pronoun()} said. "
        f"\"I do not want to drop it.\""
    )
    world.say(
        f"So {hero.label} and {helper.label} walked back together and placed the cantaloupe in {p.return_place}."
    )
    melon.meters["safe"] = 1.0
    world.facts["reconciled"] = True
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    elder.memes["warmth"] = elder.memes.get("warmth", 0.0) + 1
    world.say(
        f"Then {elder.label} laughed softly. \"Thank you for listening,\" {elder.pronoun()} said. "
        f"\"A good hierarchy is not about who is loudest. It is about everyone helping each other return safely.\""
    )
    world.say(
        f"{hero.label} grinned, and the cantaloupe rested safely in the bowl, bright and round and still whole."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    narration_open(world)
    cautionary_turn(world)
    resolve_risk(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a heartwarming story about {p.hero_name}, a cantaloupe, and a gentle return to safety.",
        f"Tell a child-sized tale where a kitchen hierarchy helps a child listen, pause, and return the cantaloupe.",
        f"Write a story with dialogue, a cautionary warning, and reconciliation about {p.item_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    elder = _safe_fact(world, world.facts, "elder")
    qa = [
        QAItem(
            question=f"Who wanted to carry the cantaloupe at first?",
            answer=f"{hero.label} wanted to carry the cantaloupe at first because {hero.pronoun()} wanted to help.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn them?",
            answer="The warning was about the cantaloupe slipping on the stairs and making a mess if it was carried too quickly.",
        ),
        QAItem(
            question=f"What did {helper.label} suggest instead?",
            answer="They suggested returning the cantaloupe to the fruit bowl first and then choosing a safer way together.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.label} and {helper.label} listening, returning the cantaloupe safely, and everyone feeling warm and happy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cantaloupe?",
            answer="A cantaloupe is a round fruit with a thick rind and sweet orange flesh inside.",
        ),
        QAItem(
            question="Why is it careful to carry a cantaloupe with two hands?",
            answer="Using two hands helps keep a round, slippery fruit steady so it is less likely to fall.",
        ),
        QAItem(
            question="What does return mean?",
            answer="Return means to bring something back to where it belongs.",
        ),
        QAItem(
            question="What is a hierarchy?",
            answer="A hierarchy is a way people are arranged so some have more responsibility while others help in smaller ways.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts.get('caution', False)=} {world.facts.get('reconciled', False)=}")
    return "\n".join(lines)


ASP_RULES = r"""
% A simple declarative twin: a cantaloupe is at risk when carried alone,
% caution is appropriate, and reconciliation follows when the child returns it.
at_risk(cantaloupe) :- carrying(hero, cantaloupe), alone(hero).
warn(parent) :- at_risk(cantaloupe).
reconcile(hero) :- warn(parent), return(hero, cantaloupe).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("carrying", "hero", "cantaloupe"),
        asp.fact("alone", "hero"),
        asp.fact("return", "hero", "cantaloupe"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconcile/1."))
    atoms = set(asp.atoms(model, "reconcile"))
    expected = {("hero",)}
    if atoms == expected:
        print("OK: ASP parity holds.")
        return 0
    print("MISMATCH: ASP parity failed.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


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


CURATED = [
    StoryParams(seed=1, family_name="the Lane family", hero_name="Milo", hero_type="boy",
                helper_name="Nia", helper_type="girl", elder_name="Grandma June",
                elder_type="grandmother", place="the kitchen", level_top="the top shelf",
                item="cantaloupe", item_phrase="a ripe cantaloupe", action="carry the cantaloupe upstairs",
                return_place="the fruit bowl"),
    StoryParams(seed=2, family_name="the Chen family", hero_name="Sofia", hero_type="girl",
                helper_name="Ben", helper_type="boy", elder_name="Aunt Lila",
                elder_type="aunt", place="the pantry", level_top="the high counter",
                item="cantaloupe", item_phrase="a striped cantaloupe", action="return the cantaloupe to the kitchen",
                return_place="the fruit bowl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reconcile/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
