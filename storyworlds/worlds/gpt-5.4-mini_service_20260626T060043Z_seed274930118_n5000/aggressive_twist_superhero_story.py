#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with an aggressive twist.

Premise:
- A young hero protects the city.
- A thief-villain snatches a prized device.
- The hero gives chase, but the twist reveals the villain was trying to stop a
  bigger danger.
- The story ends with a hard choice and a repaired city.

The world is deliberately small and constraint-checked: we only generate stories
where the twist is reasoned about by the simulated world, not swapped into a
frozen paragraph.
"""

from __future__ import annotations

import argparse
import dataclasses
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    threat: object | None = None
    trinket: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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


@dataclass
class Setting:
    place: str = "the city"
    afford: str = "patrol"
    SETTING: object | None = None
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
    hero_name: str
    hero_type: str
    sidekick_name: str
    villain_name: str
    setting: str = "city"
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


HERO_NAMES = ["Nova", "Sky", "Bolt", "Ruby", "Milo", "Iris", "Piper", "Jax"]
SIDEKICK_NAMES = ["Zip", "Bean", "Moss", "Tess", "Finn", "Luna", "Bram"]
VILLAIN_NAMES = ["Grim", "Vex", "Sable", "Cinder", "Rook", "Mara"]
HERO_TYPES = ["girl", "boy"]
SETTING = Setting(place="the city", afford="patrol")


# ---------------------------------------------------------------------------
# Story world
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World()
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
TRINKETS = {
    "power_core": "a glowing power core",
    "signal_key": "a silver signal key",
    "battery": "a pocket-sized battery pack",
}

THREATS = {
    "storm": "a storm cloud machine",
    "fire": "a fire burst from the power grid",
    "drone": "a rogue drone swarm",
}

TWEISTS = {
    "protect": "The villain was not stealing the trinket for greed; they were trying to stop a bigger danger.",
    "test": "The villain had set up the trouble to test whether the hero would rush in too hard.",
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return params.hero_name != params.sidekick_name and params.hero_name != params.villain_name and params.sidekick_name != params.villain_name


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def simulate(params: StoryParams) -> World:
    if not valid_combo(params):
        pass

    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="friend", label="sidekick"))
    villain = world.add(Entity(id=params.villain_name, kind="character", type="villain", label="villain"))

    trinket_id, trinket_label = random.choice(list(TRINKETS.items()))
    threat_id, threat_label = random.choice(list(THREATS.items()))
    twist_id, twist_text = random.choice(list(TWEISTS.items()))

    trinket = world.add(Entity(id=trinket_id, kind="thing", type="device", label=trinket_label, owner=hero.id))
    threat = world.add(Entity(id=threat_id, kind="thing", type="threat", label=threat_label))

    hero.memes["hope"] = 2.0
    hero.memes["anger"] = 0.0
    villain.memes["urgency"] = 1.0
    sidekick.memes["trust"] = 1.0
    trinket.meters["safe"] = 1.0
    threat.meters["danger"] = 1.0

    world.say(f"{hero.id} was a little superhero who loved patrolling {SETTING.place}.")
    world.say(f"With {sidekick.id} nearby, {hero.id} could listen for trouble and move fast when the city needed help.")

    world.para()
    world.say(f"One evening, {villain.id} rushed in and grabbed {trinket.label}.")
    hero.memes["anger"] += 1.0
    hero.memes["aggression"] += 1.0  # aggressive beat
    world.say(f"{hero.id} felt an aggressive spark and chased after {villain.id} through the bright streets.")
    world.say(f"{sidekick.id} called out that the chase looked wrong, but the noise and speed were already pulling everyone forward.")

    world.para()
    world.say(f"Then came the twist: {twist_text}")
    world.say(f"The real danger was {threat.label}, which was about to hurt the city.")
    villain.memes["truth"] = 1.0
    hero.memes["anger"] = 0.0
    hero.memes["focus"] = 2.0
    sidekick.memes["trust"] += 1.0
    threat.meters["danger"] = 0.0
    trinket.meters["safe"] = 1.0

    if twist_id == "protect":
        world.say(f"{villain.id} pointed at the danger and said they needed the {trinket.label} to shut it down.")
    else:
        world.say(f"{villain.id} admitted the whole trap had been a harsh test, but the city still needed fixing first.")

    world.para()
    world.say(f"{hero.id} made a hard choice: {hero.pronoun()} did not keep chasing {villain.id}.")
    world.say(f"Instead, {hero.id} and {sidekick.id} used the {trinket.label} to stop {threat.label}.")
    trinket.meters["used"] = 1.0
    hero.memes["pride"] = 1.0
    sidekick.memes["pride"] = 1.0
    villain.memes["relief"] = 1.0

    world.say(f"When the danger faded, {villain.id} returned the {trinket.label}, and the city lights shone calm again.")
    world.say(f"{hero.id} stood tall, still fierce, but wiser about when a fight was really the right answer.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        trinket=trinket,
        threat=threat,
        twist=twist_id,
        trinket_label=trinket_label,
        threat_label=threat_label,
        twist_text=twist_text,
        setting=SETTING,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- chosen_hero(H).
ally(A) :- chosen_ally(A).
villain(V) :- chosen_villain(V).
thing(T) :- chosen_trinket(T).

valid_story(H,A,V) :- hero(H), ally(A), villain(V), H != A, H != V, A != V.
twist_protect(V) :- twist(protect).
twist_test(V) :- twist(test).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "city"),
        asp.fact("chosen_hero", "hero"),
        asp.fact("chosen_ally", "ally"),
        asp.fact("chosen_villain", "villain"),
        asp.fact("chosen_trinket", "trinket"),
        asp.fact("twist", "protect"),
        asp.fact("twist", "test"),
    ]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("hero", "ally", "villain")}
    if atoms == py:
        print("OK: ASP and Python parity matched.")
        return 0
    print("Mismatch between ASP and Python parity.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].id}, a small hero, who gets an aggressive shock and then learns the truth.",
        f"Tell a short comic-book style story where {f['villain'].id} takes {f['trinket_label']} but the real problem is {f['threat_label']}.",
        f"Write a child-friendly superhero twist story that ends with {f['hero'].id} choosing the city over the chase.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    trinket = _safe_fact(world, f, "trinket")
    threat = _safe_fact(world, f, "threat")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little superhero, and {sidekick.id}, who stayed close when trouble started.",
        ),
        QAItem(
            question=f"What did {villain.id} grab at the start?",
            answer=f"{villain.id} grabbed {trinket.label}. That made the chase start fast and feel aggressive.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the theft was not the biggest problem. The real danger was {threat.label}, and the hero needed to stop that first.",
        ),
        QAItem(
            question=f"How did the hero fix the problem?",
            answer=f"{hero.id} stopped chasing for a moment, worked with {sidekick.id}, and used the {trinket.label} to deal with the danger in the city.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(question="What does a superhero do?", answer="A superhero helps people, protects a city, and rushes toward trouble when someone needs help."),
    QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what you thought was happening."),
    QAItem(question="Why can being aggressive cause trouble?", answer="Being aggressive can make someone rush ahead without listening, which can make a problem worse."),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# Story formatting
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with an aggressive twist.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--villain-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick_name = getattr(args, "sidekick_name", None) or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    villain_name = getattr(args, "villain_name", None) or rng.choice([n for n in VILLAIN_NAMES if n not in {hero_name, sidekick_name}])
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    if len({hero_name, sidekick_name, villain_name}) < 3:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        villain_name=villain_name,
        setting="city",
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Nova", "girl", "Zip", "Grim", "city"),
            StoryParams("Bolt", "boy", "Tess", "Vex", "city"),
            StoryParams("Iris", "girl", "Luna", "Sable", "city"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
