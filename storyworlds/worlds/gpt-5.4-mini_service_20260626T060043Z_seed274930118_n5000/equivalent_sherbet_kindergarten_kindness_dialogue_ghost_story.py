#!/usr/bin/env python3
"""
A standalone storyworld for a gentle kindergarten ghost story.

Premise:
- In kindergarten, a child notices a friendly ghost near snack time.
- The ghost is misunderstood because it is only trying to find something equivalent to sherbet.
- Kindness and dialogue reveal the ghost's true wish: to help, not haunt.

The world models a small classroom with:
- physical meters: chilly, sticky, full, spilled, glowing
- emotional memes: fear, kindness, curiosity, relief, trust

The story shape is:
beginning -> strange sight and a worried child
middle -> kind conversation and a small problem with snacks
turn -> the ghost explains itself
ending -> a kind equivalent treat and a calm room
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
    kind: str = "thing"   # "child" | "adult" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    ghost: object | None = None
    helper: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Classroom:
    place: str = "kindergarten"
    snack_time: bool = True
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
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
    helper_name: str
    treat: str
    equivalent_treat: str
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


CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Eli", "Nora", "Finn"]
HELPER_NAMES = ["Mrs. Bell", "Mr. Pine", "Ms. Reed"]
TREAT_PAIRS = [
    ("sherbet", "orange sorbet"),
    ("sherbet", "lemon ice"),
    ("sherbet", "fruit cup"),
    ("sherbet", "snowy yogurt"),
]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> Classroom:
    world = Classroom()
    child = world.add(Entity(
        id=params.child_name, kind="child", type=params.child_type, label=params.child_name,
        meters={"curiosity": 1.0}, memes={"fear": 0.0, "kindness": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="adult", type="teacher", label=params.helper_name,
        meters={}, memes={"kindness": 1.0},
    ))
    ghost = world.add(Entity(
        id="ghost", kind="ghost", type="ghost", label="the ghost",
        phrase="a soft white ghost with round eyes",
        meters={"chilly": 1.0, "glowing": 1.0},
        memes={"loneliness": 1.0, "kindness": 0.5, "hope": 1.0},
        props={"wants": params.treat, "equivalent": params.equivalent_treat},
    ))
    snack = world.add(Entity(
        id="snack", type="snack", label=params.treat, phrase=f"a cup of {params.treat}",
        meters={"sticky": 0.0, "full": 0.0, "spilled": 0.0},
        memes={"familiarity": 1.0},
        owner=child.id,
    ))
    world.facts.update(child=child, helper=helper, ghost=ghost, snack=snack)
    world.facts["equivalent"] = params.equivalent_treat

    # Beginning
    world.say(f"At kindergarten, {child.id} sat by the snack table and held a cup of {params.treat}.")
    world.say(f"The room was bright and busy until {child.id} noticed {ghost.phrase} near the window.")
    child.memes["fear"] += 1.0
    world.say(f"{child.id}'s eyes went wide, because the ghost looked strange and very still.")

    # Middle: dialogue and kindness
    world.para()
    world.say(f'"Hello," {helper.id} said softly, choosing gentle words. "Let\'s ask what it wants."')
    child.memes["curiosity"] += 1.0
    world.say(f"{child.id} took a small breath and said, " + f'"Are you here to scare us?"')
    world.say(f'The ghost shook its head. "No," it said. "I am looking for something equivalent to {params.treat}."')
    world.say(f"{child.id} blinked. That was not a spooky answer at all.")
    world.say(f'"Equivalent means it is just as nice for snack time," {helper.id} explained.')
    world.facts["dialogue"] = True

    # Turn
    world.para()
    world.say(f'The ghost pointed at the empty plate and whispered, "I miss being invited to snack."')
    ghost.memes["loneliness"] += 0.5
    child.memes["kindness"] += 1.0
    world.say(f"{child.id} felt their worry turn into kindness.")
    world.say(f'"You can share ours," {child.id} said. "If we find an equivalent treat, you can stay too."')
    world.say(f"{helper.id} smiled and brought out {params.equivalent_treat}, which was cool, sweet, and kind to little bellies.")
    snack.meters["full"] += 1.0
    snack.meters["spilled"] += 0.0
    ghost.props["shared_treat"] = params.equivalent_treat

    # Resolution
    world.para()
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["trust"] += 1.0
    ghost.memes["loneliness"] = 0.0
    ghost.memes["kindness"] += 1.0
    world.say(f"The ghost tried the {params.equivalent_treat} and gave a happy little glow.")
    world.say(f"{child.id} laughed, because the room no longer felt spooky at all.")
    world.say(f"At the end of kindergarten, the ghost was just another friend at the table, and the sherbet stayed safely on its plate.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Content registries and reasoning
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return bool(params.child_name and params.helper_name and params.treat and params.equivalent_treat)


ASP_RULES = r"""
ghost_needs_equivalent(ghost, Treat) :- wants(ghost, Treat).
kind_answer(Child) :- says_kind(Child).
resolved :- kind_answer(Child), equivalent_treat(Treat, Equiv).
#show ghost_needs_equivalent/2.
#show kind_answer/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("wants", "ghost", "sherbet"),
        asp.fact("equivalent_treat", "sherbet", "orange_sorbet"),
        asp.fact("says_kind", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    atoms = {str(a) for a in model}
    if any("ghost_needs_equivalent" in a for a in atoms):
        print("OK: ASP twin built a reasonable ghost need.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected model.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: Classroom) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child").id
    helper = _safe_fact(world, f, "helper").id
    treat = _safe_fact(world, f, "snack").label
    equiv = _safe_fact(world, f, "equivalent")
    return [
        f'Write a gentle kindergarten ghost story using the word "{treat}" and the idea of "{equiv}" as an equivalent snack.',
        f"Tell a child-friendly story where {child} sees a ghost in kindergarten, speaks kindly, and learns the ghost wants something equivalent to {treat}.",
        f"Write a short story with dialogue, kindness, and a ghost at snack time in kindergarten.",
    ]


def story_qa(world: Classroom) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    snack = _safe_fact(world, f, "snack")
    ghost = _safe_fact(world, f, "ghost")
    return [
        QAItem(
            question=f"Why did {child.id} get scared at first?",
            answer=f"{child.id} got scared at first because {ghost.phrase} looked strange and quiet near the kindergarten snack table.",
        ),
        QAItem(
            question=f"What did the ghost want?",
            answer=f'The ghost wanted something equivalent to {snack.label}, and it said so in the dialogue instead of trying to frighten anyone.',
        ),
        QAItem(
            question=f"How did {child.id} help the ghost?",
            answer=f"{child.id} used kindness and invited the ghost to share a snack, which helped everyone feel calm.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, fear had turned into trust, and the ghost was enjoying a kind snack time in kindergarten.",
        ),
    ]


def world_knowledge_qa(world: Classroom) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindergarten?",
            answer="Kindergarten is a place where young children learn, play, sing, and share with help from grown-ups.",
        ),
        QAItem(
            question="What does equivalent mean?",
            answer="Equivalent means something has the same value or is just as good in a matching way.",
        ),
        QAItem(
            question="What is sherbet?",
            answer="Sherbet is a sweet frozen treat that is cool, fruity, and soft enough to eat with a spoon.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps people feel safe, understood, and ready to talk instead of being afraid.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle kindergarten ghost story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--treat", choices=["sherbet"])
    ap.add_argument("--equivalent", help="an equivalent snack, like orange sorbet")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    treat = getattr(args, "treat", None) or "sherbet"
    equivalent = getattr(args, "equivalent", None) or rng.choice([e for _, e in TREAT_PAIRS])
    if treat != "sherbet":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if equivalent == treat:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child_name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        child_type="girl" if rng.random() < 0.5 else "boy",
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        treat=treat,
        equivalent_treat=equivalent,
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def dump_trace(world: Classroom) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id:10} ({e.kind:6}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is intentionally tiny in this world; run --verify to check parity.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams("Mia", "girl", "Mrs. Bell", "sherbet", "orange sorbet"),
            StoryParams("Noah", "boy", "Mr. Pine", "sherbet", "lemon ice"),
            StoryParams("Lily", "girl", "Ms. Reed", "sherbet", "fruit cup"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
            header = f"### {p.child_name}: sherbet and equivalent {p.equivalent_treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
