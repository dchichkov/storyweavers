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


MYSTERY_WORDS = {"ease", "slinky", "gymnastic"}



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
    plural: bool = False
    hidden: bool = False
    found: bool = False
    lost: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    clue: object | None = None
    hero: object | None = None
    parent: object | None = None
    shadow: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    clue: str
    shadow: str
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
class Artifact:
    label: str
    phrase: str
    type: str
    hiding_place: str
    clue_word: str
    risk_word: str
    owner_kind: str = "child"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    place: str
    artifact: str
    hero_name: str
    hero_gender: str
    parent_type: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with a lesson learned and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


SETTINGS = {
    "hall": Setting(place="the quiet hall", clue="a draft under the door", shadow="a long shadow on the wall"),
    "attic": Setting(place="the dusty attic", clue="a tiny footprint in dust", shadow="a low beam and a dark corner"),
    "studio": Setting(place="the mirror studio", clue="a scuff near the mat", shadow="a mirror that kept the room doubled"),
}

ARTIFACTS = {
    "slinky": Artifact(
        label="slinky",
        phrase="a silver slinky",
        type="toy",
        hiding_place="behind a box",
        clue_word="slinky",
        risk_word="slipped",
    ),
    "ribbon": Artifact(
        label="ribbon",
        phrase="a blue ribbon",
        type="token",
        hiding_place="under a bench",
        clue_word="ease",
        risk_word="tugged",
    ),
    "ring": Artifact(
        label="ring",
        phrase="a small brass ring",
        type="token",
        hiding_place="inside a shoe",
        clue_word="gymnastic",
        risk_word="tilted",
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Nora", "Pia", "Ivy"],
    "boy": ["Theo", "Milo", "Ezra", "Finn", "Owen"],
}

TRAITS = ["careful", "curious", "quiet", "brave", "patient"]

ASP_RULES = r"""
place(hall). place(attic). place(studio).
artifact(slinky). artifact(ribbon). artifact(ring).
valid(P,A) :- place(P), artifact(A).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {(p, a) for p in SETTINGS for a in ARTIFACTS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    if artifact not in ARTIFACTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, artifact=artifact, hero_name=name, hero_gender=gender, parent_type=parent)


def validate_reasonable(params: StoryParams) -> None:
    if params.artifact == "ring" and params.place == "hall":
        pass
    if params.artifact == "slinky" and params.place == "studio":
        pass
    if params.artifact == "ribbon" and params.place == "attic":
        pass


def generate(params: StoryParams) -> StorySample:
    validate_reasonable(params)
    setting = _safe_lookup(SETTINGS, params.place)
    artifact_def = _safe_lookup(ARTIFACTS, params.artifact)
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    artifact = world.add(Entity(id="artifact", type=artifact_def.type, label=artifact_def.label, phrase=artifact_def.phrase, owner=hero.id))
    clue = world.add(Entity(id="clue", type="clue", label=artifact_def.clue_word, hidden=True))
    shadow = world.add(Entity(id="shadow", type="shadow", label=setting.shadow, hidden=True))

    hero.memes["unease"] = 1
    world.say(f"{hero.label} was a {rng_trait(params.seed, params.hero_name)} {params.hero_gender} who noticed small details.")
    world.say(f"{hero.label} liked {artifact.phrase} because it moved with odd {artifact_def.clue_word} and a little {artifact_def.risk_word} of ease.")
    world.say(f"One evening, the lights were low in {setting.place}, and {setting.shadow} made the room feel like a puzzle.")

    world.para()
    world.say(f"{hero.label} found {setting.clue}.")
    world.say(f"{hero.pronoun().capitalize()} followed it with careful steps, because mysteries felt safer when the answer was close.")
    artifact.hidden = True
    world.say(f"Behind {artifact_def.hiding_place}, {hero.label} saw {artifact.phrase}.")
    artifact.found = True
    hero.memes["hope"] = 1

    world.para()
    world.say(f"But when {hero.label} reached for it, the thing {artifact_def.risk_word} away.")
    world.say(f"{params.parent} came in, saw the mess, and said the room had been turned upside down by too much curiosity.")
    hero.memes["worry"] = 1
    world.say(f"{hero.label} tried to explain the clue with {artifact_def.clue_word}, but the answer did not come out cleanly.")

    world.para()
    world.say(f"Then {hero.label} learned something important: if a secret looks simple, it can still lead to trouble.")
    world.say(f"{params.parent} told {hero.label} to put things back and be more careful next time.")
    world.say(f"{hero.label} nodded, but the final shelf stayed crooked, and the missing thing could not be saved.")
    artifact.lost = True

    world.facts.update(
        hero=hero,
        parent=parent,
        artifact=artifact,
        setting=setting,
        clue=clue,
        shadow=shadow,
        params=params,
        bad_ending=True,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def rng_trait(seed: Optional[int], name: str) -> str:
    r = random.Random((seed or 0) ^ hash(name))
    return r.choice(TRAITS)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about "{f["artifact"].label}" and the words ease, slinky, and gymnastic.',
        f"Tell a gentle but spooky little story in {f['setting'].place} where {f['hero'].label} follows a clue and makes a bad choice.",
        "Write a story that ends with a lesson learned but not a happy rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    artifact = _safe_fact(world, f, "artifact")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, who notices clues in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.label} follow to find the mystery item?",
            answer=f"{hero.label} followed {setting.clue}, which led to {artifact.phrase}.",
        ),
        QAItem(
            question=f"Why is the ending bad?",
            answer=f"The ending is bad because the item {artifact.risk_word} away and could not be saved, even after {hero.label} learned a lesson.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that a small secret can turn into trouble, so it is important to be careful with clues.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slinky?",
            answer="A slinky is a springy toy that can stretch, bounce, and slide down steps.",
        ),
        QAItem(
            question="What does ease mean in this story?",
            answer="Ease means something feels simple or smooth, even though the mystery proved it could still hide trouble.",
        ),
        QAItem(
            question="What does gymnastic suggest?",
            answer="Gymnastic suggests bending, balancing, or moving in a careful, skillful way.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.lost:
            bits.append("lost=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in SETTINGS:
        for a in ARTIFACTS:
            try:
                validate_reasonable(StoryParams(place=p, artifact=a, hero_name="Mina", hero_gender="girl", parent_type="mother"))
            except StoryError:
                continue
            combos.append((p, a))
    return combos


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_world_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    validate_reasonable(params)
    return params


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for place, artifact in combos:
            print(place, artifact)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, a in valid_combos():
            params = StoryParams(place=p, artifact=a, hero_name="Mina", hero_gender="girl", parent_type="mother", seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_world_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
