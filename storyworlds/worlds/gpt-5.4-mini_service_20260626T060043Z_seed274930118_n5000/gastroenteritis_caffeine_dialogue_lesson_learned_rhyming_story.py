#!/usr/bin/env python3
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


RHYMES = {
    "start": [
        "At dawn in the kitchen, the day was bright and clear.",
        "A little one woke with a grin from ear to ear.",
    ],
    "sip": [
        "A fizzy drink sparkled, all bubbly and sweet.",
        "It tickled the tongue and felt like a treat.",
    ],
    "ache": [
        "But soon came a rumble that made the belly bend.",
        "A twisty tummy trouble began around the end.",
    ],
    "talk": [
        "“Maybe that drink was too much for me,” the child did say.",
        "“My tummy feels wobbly in a very grumbly way,” came the reply.",
    ],
    "lesson": [
        "“When your belly is sore, choose water and rest,” said the grown-up with care.",
        "“Caffeine can bother a sick little stomach, so we should be gentle there,” they shared.",
    ],
    "end": [
        "So the cup was put aside, and the lesson stayed in sight.",
        "With water, a hug, and a quiet nap, the day grew calm and right.",
    ],
}



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

    child: object | None = None
    drink: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    child_name: str
    child_type: str
    parent_type: str
    drink: str
    setting: str
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


CHILD_NAMES_GIRL = ["Mia", "Luna", "Nora", "Ava", "Tess", "Ruby"]
CHILD_NAMES_BOY = ["Theo", "Finn", "Noah", "Liam", "Max", "Ezra"]
SETTINGS = {
    "kitchen": "the kitchen",
    "bedroom": "the bedroom",
    "porch": "the porch",
}
DRINKS = {
    "soda": {"label": "soda", "caffeine": 1.0, "sweet": 1.0, "rhymes": "glow"},
    "cola": {"label": "cola", "caffeine": 1.0, "sweet": 0.8, "rhymes": "flow"},
    "iced tea": {"label": "iced tea", "caffeine": 0.8, "sweet": 0.2, "rhymes": "breeze"},
    "coffee": {"label": "coffee", "caffeine": 1.2, "sweet": 0.0, "rhymes": "free"},
    "hot chocolate": {"label": "hot chocolate", "caffeine": 0.1, "sweet": 1.0, "rhymes": "glow"},
}
LESSON = {
    "question": "What should you choose when your belly feels bad?",
    "answer": "Water, rest, and gentle food are better choices than caffeine when a tummy is upset.",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about a child, caffeine, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def _valid_combo(setting: str, drink: str) -> bool:
    # All settings support the compact domestic scene; only caffeine-bearing drinks matter.
    return setting in SETTINGS and drink in DRINKS and _safe_lookup(DRINKS, drink)["caffeine"] > 0.0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    drink = getattr(args, "drink", None) or rng.choice(list(DRINKS))
    if not _valid_combo(setting, drink):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(child_name=name, child_type=gender, parent_type=parent, drink=drink, setting=setting)


def _intonation_line(kind: str, child: Entity, parent: Entity, drink_label: str) -> str:
    if kind == "start":
        return f"{RHYMES['start'][0]} {child.id} spotted {drink_label} and smiled with cheer."
    if kind == "sip":
        return f"{RHYMES['sip'][0]} {child.id} took a sip, then took another near."
    if kind == "ache":
        return f"{RHYMES['ache'][0]} {child.id} held {child.pronoun('possessive')} belly and tried not to frown."
    if kind == "talk":
        return f"{RHYMES['talk'][0]} “I think my drink is the reason I feel down,” said the child."
    if kind == "lesson":
        return f"{RHYMES['lesson'][0]} “When a tummy is troubled, skip caffeine,” said {parent.id} with a smile."
    return f"{RHYMES['end'][0]} {RHYMES['end'][1]}"


def _propagate(world: World) -> None:
    child = world.get("child")
    if child.meters.get("caffeine", 0.0) >= 1.0 and child.meters.get("stomach_upset", 0.0) >= 1.0:
        sig = ("lesson",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["lesson_learned"] = 1.0
            child.memes["relief"] = 1.0


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="parent", meters={}, memes={}))
    drink = world.add(Entity(id="drink", kind="thing", type="drink", label=_safe_lookup(DRINKS, params.drink)["label"], phrase=params.drink))
    world.facts.update(child=child, parent=parent, drink=drink, setting=params.setting, params=params)

    world.say(f"{child.id} was small and spry, with a grin that could glow.")
    world.say(f"In {_safe_lookup(SETTINGS, params.setting)}, {child.id} found {drink.label} and gave it a go.")
    world.say(f"{child.id} loved the fizzy taste; it felt fun, fast, and bright.")
    world.say(f"But caffeine can wake a body up, and not always in a good-luck light.")

    world.para()
    child.meters["caffeine"] = _safe_lookup(DRINKS, params.drink)["caffeine"]
    world.say(_intonation_line("sip", child, parent, drink.label))
    child.meters["stomach_upset"] = 1.0
    world.say(_intonation_line("ache", child, parent, drink.label))
    world.say(f"{parent.id} leaned close and asked, “How does your tummy feel today?”")
    world.say(f"“It feels twisty and icky,” said {child.id}, “like a knot in my plate.”")
    world.say(f"“Then let's pause,” said {parent.id}. “Caffeine can make a sore belly worse, so water will be great.”")

    world.para()
    world.say(_intonation_line("lesson", child, parent, drink.label))
    world.say(f"{child.id} nodded and traded the cup for a glass of plain water.")
    world.say(f"After a quiet rest, the rumble grew soft, the ache drifted away, and the room felt light.")
    world.say(f"{child.id} learned a gentle rule: when gastroenteritis or belly upset comes near, caffeine is not a kind choice at night.")
    world.say(_intonation_line("end", child, parent, drink.label))

    _propagate(world)
    world.facts["lesson_learned"] = bool(child.memes.get("lesson_learned"))
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    drink = _safe_lookup(DRINKS, p.drink)["label"]
    return [
        f'Write a short rhyming story for children about {p.child_name}, {drink}, and a sore tummy.',
        f"Tell a dialogue-driven rhyme where a {p.child_type} named {p.child_name} learns that caffeine can bother an upset stomach.",
        f"Create a gentle lesson-learned story set in {_safe_lookup(SETTINGS, p.setting)} about choosing water after a bad belly feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    drink = _safe_lookup(DRINKS, p.drink)["label"]
    return [
        QAItem(
            question=f"What did {p.child_name} drink before the tummy trouble started?",
            answer=f"{p.child_name} drank {drink}, which had caffeine and made the belly feel worse.",
        ),
        QAItem(
            question=f"Who talked with {p.child_name} about the sore belly?",
            answer=f"{world.facts['parent'].id} talked with {p.child_name} and suggested water and rest.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that caffeine is not a good choice when the stomach already feels upset.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is caffeine?",
            answer="Caffeine is a natural chemical in some drinks that can make people feel more awake.",
        ),
        QAItem(
            question="What is gastroenteritis?",
            answer="Gastroenteritis is an illness that can cause stomach pain, vomiting, or diarrhea.",
        ),
        QAItem(
            question="What is a gentle choice for a sick tummy?",
            answer="Water and rest are gentle choices when the stomach feels upset.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
drink_has_caffeine(D) :- drink(D), caffeine(D, C), C > 0.
upset_stomach(C) :- drink(D), drink_has_caffeine(D), child(C).
lesson_learned(C) :- upset_stomach(C), parent(P), dialogue(C, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("caffeine", did, d["caffeine"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, d) for s in SETTINGS for d in DRINKS if _valid_combo(s, d)]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show drink_has_caffeine/1."))
    return sorted(set(asp.atoms(model, "drink_has_caffeine")))


def asp_verify() -> int:
    import asp
    py = set((d,) for _, d in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} caffeine drinks).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


CURATED = [
    StoryParams(child_name="Mia", child_type="girl", parent_type="mother", drink="cola", setting="kitchen"),
    StoryParams(child_name="Theo", child_type="boy", parent_type="father", drink="iced tea", setting="porch"),
    StoryParams(child_name="Ruby", child_type="girl", parent_type="mother", drink="coffee", setting="bedroom"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "drink", None) and not _valid_combo(getattr(args, "setting", None), getattr(args, "drink", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    drink = getattr(args, "drink", None) or rng.choice(list(DRINKS))
    if _safe_lookup(DRINKS, drink)["caffeine"] <= 0:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(child_name=name, child_type=gender, parent_type=parent, drink=drink, setting=setting)


def build_curated() -> list[StorySample]:
    return [generate(p) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show drink_has_caffeine/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show drink_has_caffeine/1."))
        return

    if getattr(args, "all", None):
        samples = build_curated()
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
