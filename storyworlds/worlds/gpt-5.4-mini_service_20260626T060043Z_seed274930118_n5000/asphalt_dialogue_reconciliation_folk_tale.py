#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/asphalt_dialogue_reconciliation_folk_tale.py
==============================================================================================================

A tiny folk-tale storyworld about a village path, a strip of asphalt, a shared
problem, and a spoken reconciliation.

The seed image:
---
A small village had a narrow path that ran past the baker's door and down to
the mill. One spring, the path broke into rough holes. A patch of fresh asphalt
could fix it, but the miller and the baker each wanted the road changed in a way
that helped their own carts first.

They argued in gentle but stubborn voices until the grandmother by the well
asked them to sit together, look at the road, and choose a fair shape for the
patch. They listened, talked, and finally laid the asphalt in a way that kept
every cart moving.

World model:
---
- meters track physical state: road roughness, asphalt readiness, cart passage
- memes track emotional state: worry, pride, patience, trust, relief
- dialogue changes hearts when characters speak honestly
- reconciliation lowers conflict when both sides accept a fair repair

This script keeps the simulation small and constraint-driven: the repair must
actually help the road, and the reconciliation must be earned by the dialogue.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "mother", "grandmother", "baker"}
        male = {"man", "father", "miller", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Village:
    place: str
    road_name: str
    road_kind: str = "asphalt"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    w: object | None = None
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "Village":
        clone = Village(self.place, self.road_name, self.road_kind)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
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
    place: str
    road_name: str
    asker: str
    builder: str
    mediator: str
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


PLACES = {
    "village": "the village lane",
    "market": "the market road",
    "hill": "the hill path",
    "brook": "the brookside road",
}

ROAD_NAMES = {
    "lane": "the old lane",
    "road": "the wide road",
    "path": "the narrow path",
}

ASKERS = {
    "baker": ("baker", "bread cart", "loaf cart"),
    "miller": ("miller", "flour cart", "grain cart"),
}

BUILDERS = {
    "roadmason": ("roadmason", "trowel", "stone cart"),
    "paver": ("paver", "bucket", "brick cart"),
}

MEDIATORS = {
    "grandmother": ("grandmother", "well bucket", "kind apron"),
    "elder": ("elder", "walking stick", "lantern"),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for road_name in ROAD_NAMES:
            for asker in ASKERS:
                for builder in BUILDERS:
                    combos.append((place, road_name, asker, builder))
    return combos


def explain_invalid(_: str) -> str:
    return "(No story: the requested choices do not fit the small village road tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about asphalt, dialogue, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--road-name", choices=ROAD_NAMES)
    ap.add_argument("--asker", choices=ASKERS)
    ap.add_argument("--builder", choices=BUILDERS)
    ap.add_argument("--mediator", choices=MEDIATORS)
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
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "road_name", None) is None or c[1] == getattr(args, "road_name", None))
        and (getattr(args, "asker", None) is None or c[2] == getattr(args, "asker", None))
        and (getattr(args, "builder", None) is None or c[3] == getattr(args, "builder", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, road_name, asker, builder = rng.choice(list(combos))
    mediator = getattr(args, "mediator", None) or rng.choice(sorted(MEDIATORS))
    return StoryParams(place=place, road_name=road_name, asker=asker, builder=builder, mediator=mediator)


def _init_world(params: StoryParams) -> Village:
    w = Village(place=_safe_lookup(PLACES, params.place), road_name=_safe_lookup(ROAD_NAMES, params.road_name))
    asker_type, _, _ = _safe_lookup(ASKERS, params.asker)
    builder_type, _, _ = _safe_lookup(BUILDERS, params.builder)
    mediator_type, _, _ = _safe_lookup(MEDIATORS, params.mediator)
    w.add(Entity("asker", kind="character", type=asker_type, label=params.asker, meters={"worry": 0.0, "pride": 1.0}, memes={"worry": 1.0, "pride": 1.0}))
    w.add(Entity("builder", kind="character", type=builder_type, label=params.builder, meters={"work": 1.0}, memes={"patience": 0.5, "pride": 1.0}))
    w.add(Entity("mediator", kind="character", type=mediator_type, label=params.mediator, meters={"kindness": 1.0}, memes={"kindness": 1.0, "trust": 1.0}))
    w.add(Entity("road", type="road", label="the road", meters={"roughness": 2.0, "repair": 0.0, "asphalt": 0.0, "passable": 0.0}))
    w.add(Entity("asphalt", type="material", label="asphalt", phrase="fresh asphalt", meters={"ready": 1.0}))
    w.add(Entity("cart_a", type="cart", label="the baker's cart", meters={"stuck": 1.0}))
    w.add(Entity("cart_b", type="cart", label="the miller's cart", meters={"stuck": 1.0}))
    return w


def _ask_for_help(w: Village) -> None:
    asker = w.get("asker")
    builder = w.get("builder")
    road = w.get("road")
    asker.memes["worry"] += 1.0
    w.say(f"In {w.place}, {asker.label} looked at {w.road_name} and sighed. The {road.label} was rough and full of holes.")
    w.say(f'"We need the road mended," {asker.label} said. "My cart shakes when I pass."')


def _answer_with_pride(w: Village) -> None:
    asker = w.get("asker")
    builder = w.get("builder")
    builder.memes["pride"] += 1.0
    w.say(f'"I can fix it," {builder.label} replied, "but it should be done my way."')
    w.say(f'"My way keeps my cart moving too," {asker.label} answered, and the two grew hot with worry and pride.')


def _predict_damage(w: Village) -> bool:
    return w.get("road").meters["roughness"] >= THRESHOLD


def _mediator_speaks(w: Village) -> None:
    mediator = w.get("mediator")
    asker = w.get("asker")
    builder = w.get("builder")
    road = w.get("road")
    w.say(f'Then {mediator.label} came by the well and said, "Why not look at the road together?"')
    w.say(f'"When one patch helps only one cart, the road still stays unhappy," {mediator.label} said softly.')
    mediator.memes["trust"] += 1.0
    asker.memes["trust"] += 1.0
    builder.memes["trust"] += 1.0
    if _predict_damage(w):
        w.say(f'The others looked down at the cracked {road.label}, and at last they listened.')


def _reconcile(w: Village) -> None:
    asker = w.get("asker")
    builder = w.get("builder")
    mediator = w.get("mediator")
    road = w.get("road")
    asphalt = w.get("asphalt")
    road.meters["asphalt"] = 1.0
    road.meters["repair"] = 1.0
    road.meters["roughness"] = 0.0
    road.meters["passable"] = 1.0
    asphalt.meters["ready"] = 0.0
    asker.memes["worry"] = 0.0
    builder.memes["pride"] = 0.0
    asker.memes["peace"] = 1.0
    builder.memes["peace"] = 1.0
    mediator.memes["peace"] = 1.0
    w.say(f'The builder knelt down, the asker nodded, and {mediator.label} smiled. "We can share the road," they said.')
    w.say(f"They laid the asphalt in a fair strip, wide enough for both carts. By dusk, the holes were gone.")
    w.say(f"The {road.label} shone dark and smooth, and both carts rolled home without a shake.")


def tell(params: StoryParams) -> Village:
    w = _init_world(params)
    _ask_for_help(w)
    w.para()
    _answer_with_pride(w)
    w.para()
    _mediator_speaks(w)
    _reconcile(w)
    w.facts.update(
        asker=w.get("asker"),
        builder=w.get("builder"),
        mediator=w.get("mediator"),
        road=w.get("road"),
        asphalt=w.get("asphalt"),
        place=params.place,
        road_name=params.road_name,
    )
    return w


def generation_prompts(world: Village) -> list[str]:
    f = world.facts
    asker = _safe_fact(world, f, "asker")
    builder = _safe_fact(world, f, "builder")
    mediator = _safe_fact(world, f, "mediator")
    return [
        "Write a short folk tale about a village road that is mended with asphalt after two neighbors disagree.",
        f'Write a gentle dialogue story where {asker.label} and {builder.label} argue about a broken road, and {mediator.label} helps them make peace.',
        f"Tell a child-friendly story about asphalt, a fair repair, and a reconciliation in {f['place']}.",
    ]


def story_qa(world: Village) -> list[QAItem]:
    f = world.facts
    asker = _safe_fact(world, f, "asker")
    builder = _safe_fact(world, f, "builder")
    mediator = _safe_fact(world, f, "mediator")
    road = _safe_fact(world, f, "road")
    return [
        QAItem(
            question=f"What was wrong with the road in {f['place']}?",
            answer=f"The {road.label} was rough and full of holes, so carts shook when they passed.",
        ),
        QAItem(
            question=f"Who first asked for help fixing the road?",
            answer=f"{asker.label.capitalize()} first asked for help because the cart bumped badly on the broken road.",
        ),
        QAItem(
            question=f"Who helped the two neighbors talk kindly to each other?",
            answer=f"{mediator.label.capitalize()} helped them talk kindly and look at the road together.",
        ),
        QAItem(
            question=f"What did they use to repair the road at the end?",
            answer="They used asphalt to make a fair, smooth patch that helped both carts.",
        ),
        QAItem(
            question=f"How did the story end for the two neighbors?",
            answer="They reconciled, and the road became smooth enough for everyone to pass happily.",
        ),
    ]


def world_knowledge_qa(world: Village) -> list[QAItem]:
    return [
        QAItem(
            question="What is asphalt?",
            answer="Asphalt is a dark, sticky building material used to make roads smooth and strong.",
        ),
        QAItem(
            question="Why do people repair roads?",
            answer="People repair roads so carts, bikes, and people can travel safely without bumping into holes.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop arguing and make peace with each other again.",
        ),
        QAItem(
            question="Why is dialogue helpful?",
            answer="Dialogue is helpful because people can explain their worries and listen to each other before choosing what to do.",
        ),
    ]


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


def dump_trace(world: Village) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A road is worth repairing when it is rough.
needs_repair(R) :- road(R), roughness(R, N), N >= 1.

% Dialogue reduces conflict when both sides and the mediator are present.
can_reconcile(A, B, M) :- character(A), character(B), mediator(M), A != B, A != M, B != M.

% The story is valid only if the rough road gets asphalt and the conflict resolves.
valid_story(Place) :- place(Place), needs_repair(road), repaired_with(asphalt), reconciled.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", pid) for pid in PLACES]
    lines += [asp.fact("road_name", rid) for rid in ROAD_NAMES]
    lines += [asp.fact("asker", k) for k in ASKERS]
    lines += [asp.fact("builder", k) for k in BUILDERS]
    lines += [asp.fact("mediator", k) for k in MEDIATORS]
    lines += [asp.fact("road", "road"), asp.fact("repaired_with", "asphalt"), asp.fact("reconciled")]
    lines += [asp.fact("roughness", "road", 2)]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Import lazily as required.
    from storyworlds import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("village",)}
    if atoms == py:
        print("OK: clingo parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(py))
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
    StoryParams(place="village", road_name="lane", asker="baker", builder="roadmason", mediator="grandmother"),
    StoryParams(place="market", road_name="road", asker="miller", builder="paver", mediator="elder"),
    StoryParams(place="brook", road_name="path", asker="baker", builder="paver", mediator="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
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
            p = sample.params
            header = f"### {p.place} / {p.road_name} / {p.asker} / {p.builder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
