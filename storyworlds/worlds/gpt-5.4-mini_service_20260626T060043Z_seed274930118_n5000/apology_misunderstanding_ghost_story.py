#!/usr/bin/env python3
"""
apology_misunderstanding_ghost_story.py
======================================

A tiny story world about a child, a misunderstanding, and a ghostly apology.

Seed-tale premise:
---
A child hears a ghostly bump in an old house and thinks a ghost is being scary.
The "ghost" is really a shy helper making sounds while trying to return a lost toy.
When the child apologizes for jumping to conclusions, the ghost apologizes too.
They clear up the misunderstanding, and the house feels warm again.

This world keeps the prose close to a ghost story, but child-friendly:
quiet rooms, moonlight, soft footsteps, creaky boards, and a kind ghost who
turns out to be misunderstood rather than frightening.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True
    friendly: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "moonlit"
    sounds: str = "soft creaks"
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
    setting: str
    child_name: str
    child_gender: str
    parent_type: str
    ghost_name: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    child = world.get("child")
    ghost = world.get("ghost")
    toy = world.get("toy")
    if child.memes.get("fear", 0) < THRESHOLD:
        return out
    if toy.meters.get("hidden", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["misunderstanding"] = 1.0
    ghost.memes["sad"] = ghost.memes.get("sad", 0) + 1
    out.append("The child had misunderstood the bumping sound.")
    return out


RULES = [Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "old_house": Setting(place="the old house", mood="moonlit", sounds="soft creaks"),
    "attic": Setting(place="the attic", mood="dusty and moonlit", sounds="tiny creaks"),
    "hall": Setting(place="the narrow hall", mood="quiet", sounds="wooden sighs"),
}

CHILDREN = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Ben"],
}

GHOST_NAMES = ["Murmur", "Pale Poppy", "Boo", "Willow", "Pip"]

TRAITS = ["curious", "brave", "small", "sleepy", "gentle"]

# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, ghost: Entity, toy: Entity) -> None:
    world.say(
        f"{child.id} lived near {world.setting.place} and liked listening when "
        f"{world.setting.sounds} drifted through the rooms."
    )
    world.say(
        f"One evening, {child.id} found {child.pronoun('possessive')} little "
        f"flashlight and a lost toy tucked under a chair."
    )
    world.say(
        f"{child.id} did not know that {ghost.id}, a shy ghost, was trying to "
        f"return {toy.it()} to its owner."
    )


def setup_unease(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["curious"] = 1.0
    child.memes["fear"] = 1.0
    world.say(
        f"When a bump came from the dark hall, {child.id} froze. "
        f"{child.pronoun().capitalize()} thought {ghost.id} was trying to scare "
        f"{child.pronoun('object')}."
    )


def misunderstanding_turn(world: World, child: Entity, ghost: Entity, toy: Entity) -> None:
    child.memes["misunderstanding"] = 1.0
    ghost.memes["sad"] = 1.0
    toy.meters["hidden"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"The bump was only {ghost.id} nudging a loose box with {toy.it()} inside it."
    )
    world.say(
        f"But {child.id} could not see that in the dark, so {child.id} stepped back "
        f"and whispered, 'Go away.'"
    )


def apology_scene(world: World, child: Entity, ghost: Entity, toy: Entity) -> None:
    child.memes["regret"] = 1.0
    ghost.memes["regret"] = 1.0
    world.para()
    world.say(
        f"Then {child.id} took a breath and said, 'I'm sorry. I thought you were "
        f"being spooky, but I was wrong.'"
    )
    world.say(
        f"{ghost.id} bowed its glowing head and answered, 'I'm sorry too. I should "
        f"have shown you the toy instead of bumping around in the dark.'"
    )
    ghost.friendly = True
    child.memes["fear"] = 0.0
    child.memes["trust"] = 1.0
    ghost.memes["sad"] = 0.0


def resolution(world: World, child: Entity, ghost: Entity, toy: Entity) -> None:
    world.para()
    toy.meters["hidden"] = 0.0
    toy.location = "in the child's hands"
    world.say(
        f"{ghost.id} floated to the box, lifted {toy.it()}, and placed it in "
        f"{child.id}'s hands."
    )
    world.say(
        f"{child.id} smiled at the kind ghost, and together they carried the toy "
        f"back through the moonlit hall."
    )
    world.say(
        f"After that, the old house felt less frightening and more like a quiet "
        f"place where a mistake had been fixed."
    )


def tell(setting: Setting, child_name: str, child_gender: str, parent_type: str, ghost_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, traits=["little", "curious"]
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type, label="the parent"
    ))
    ghost = world.add(Entity(
        id=ghost_name, kind="character", type="ghost", friendly=False, visible=True
    ))
    toy = world.add(Entity(
        id="toy", type="toy", label="toy", phrase="a small toy", location="under a chair"
    ))
    toy.meters["hidden"] = 1.0

    world.facts.update(child=child, parent=parent, ghost=ghost, toy=toy)

    intro(world, child, ghost, toy)
    world.para()
    setup_unease(world, child, ghost)
    misunderstanding_turn(world, child, ghost, toy)
    apology_scene(world, child, ghost, toy)
    resolution(world, child, ghost, toy)
    return world


# ---------------------------------------------------------------------------
# Question answering
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    return [
        f'Write a short ghost story for a young child about a misunderstanding and an apology in {world.setting.place}.',
        f"Tell a gentle spooky story where {child.id} thinks {ghost.id} is scary, but it turns out to be a mistake.",
        "Write a moonlit story that includes a misunderstanding, an apology, and a friendly ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    ghost: Entity = _safe_fact(world, f, "ghost")
    toy: Entity = _safe_fact(world, f, "toy")
    return [
        QAItem(
            question=f"Why did {child.id} think there was a ghostly problem in {world.setting.place}?",
            answer=(
                f"{child.id} heard a bump in the dark hall and could not see the full "
                f"picture, so {child.id} thought {ghost.id} was trying to scare "
                f"{child.pronoun('object')}."
            ),
        ),
        QAItem(
            question=f"What was {ghost.id} really doing with the toy?",
            answer=(
                f"{ghost.id} was trying to return {toy.it()} instead of being mean. "
                f"The ghost had only made bumping sounds while moving the toy box."
            ),
        ),
        QAItem(
            question="How did the misunderstanding get fixed?",
            answer=(
                f"{child.id} apologized for jumping to conclusions, and {ghost.id} "
                f"apologized for not explaining sooner. Then they talked kindly and "
                f"shared the toy."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {ghost.id} felt friendly, {child.id} felt brave again, "
                f"and the old house seemed warm instead of scary."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone gets the wrong idea about "
                "what is happening."
            ),
        ),
        QAItem(
            question="What is an apology?",
            answer=(
                "An apology is when someone says sorry because they know they hurt "
                "someone's feelings or made a mistake."
            ),
        ),
        QAItem(
            question="Why do old houses sometimes feel spooky?",
            answer=(
                "Old houses can creak, whisper, and make shadows, so quiet sounds "
                "can feel spooky even when nothing bad is happening."
            ),
        ),
        QAItem(
            question="Why can moonlight make a room look strange?",
            answer=(
                "Moonlight is dim and silver, so it can make furniture and corners "
                "look different from how they do in daytime."
            ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.friendly:
            bits.append("friendly=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_fear(C) :- fear(C).
misunderstanding(C) :- child_fear(C), hidden(T).
apology(C) :- regret(C).
resolved(C) :- apology(C), friendly(G), child(C), ghost(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("fear", "child"))
    lines.append(asp.fact("hidden", "toy"))
    lines.append(asp.fact("regret", "child"))
    lines.append(asp.fact("regret", "ghost"))
    lines.append(asp.fact("friendly", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import only for ASP mode
    import asp

    model = asp.one_model(asp_program("#show misunderstanding/1. #show resolved/1."))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    expected = {("misunderstanding", ("child",)), ("resolved", ("child",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python checks.")
    print(" ASP:", sorted(atoms))
    print(" PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="old_house", child_name="Mia", child_gender="girl", parent_type="mother", ghost_name="Murmur"),
    StoryParams(setting="attic", child_name="Leo", child_gender="boy", parent_type="father", ghost_name="Pale Poppy"),
    StoryParams(setting="hall", child_name="Nora", child_gender="girl", parent_type="mother", ghost_name="Willow"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child, a misunderstanding, and an apology in a ghost story.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--ghost")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILDREN[gender])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    ghost = getattr(args, "ghost", None) or rng.choice(GHOST_NAMES)
    return StoryParams(setting=setting, child_name=name, child_gender=gender, parent_type=parent, ghost_name=ghost)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.child_name, params.child_gender, params.parent_type, params.ghost_name)
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
        print(asp_program("#show misunderstanding/1. #show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/1. #show resolved/1."))
        print("ASP atoms:", [str(s) for s in model])
        return

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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name} in {p.setting} with {p.ghost_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
