#!/usr/bin/env python3
"""
A tiny whodunit storyworld: a theater matinee, a missing prop, a suspicious
skedaddle, and a flashback that supplies the final clue.

The seed premise:
A child-like audience member and a careful usher are at a matinee when a prop
vanishes from the context of the stage. Everyone has a plausible alibi, but one
memory flashback reveals who moved what, when, and why.
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
# Data model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    adult: object | None = None
    child: object | None = None
    clue: object | None = None
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
    place: str = "the little theater"
    time: str = "matinee"
    indoors: bool = True
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
class Clue:
    id: str
    label: str
    location: str
    conspicuous: bool = False
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
class Suspect:
    id: str
    label: str
    role: str
    mood: str
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
    suspect: str
    clue: str
    setting: str = "theater"
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
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

SUSPECTS = {
    "usher": Suspect(id="usher", label="the usher", role="usher", mood="careful"),
    "actor": Suspect(id="actor", label="the actor", role="actor", mood="busy"),
    "friend": Suspect(id="friend", label="the friend", role="visitor", mood="nervous"),
    "manager": Suspect(id="manager", label="the manager", role="manager", mood="stern"),
}

CLUES = {
    "program": Clue(id="program", label="a folded program", location="under a seat"),
    "key": Clue(id="key", label="a brass key", location="inside a curtain pocket"),
    "glove": Clue(id="glove", label="a velvet glove", location="behind the stage box"),
    "ticket_stub": Clue(id="ticket_stub", label="a torn ticket stub", location="near the aisle"),
}

NAMES = ["Mina", "Toby", "Iris", "Noah", "Nina", "Ezra"]
TRAITS = ["quiet", "curious", "careful", "bold", "shy"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, child: Entity, adult: Entity, clue: Entity) -> None:
    world.say(
        f"{child.id} came to the {world.setting.time} at {world.setting.place} with {adult.label}."
    )
    world.say(
        f"{child.id} liked mysteries, because every little detail felt like context waiting to be solved."
    )
    world.say(
        f"Today, the prize was {clue.phrase}, and it had gone missing just as the curtain rose."
    )


def establish_scene(world: World, clue: Entity) -> None:
    world.say(
        f"The stage was bright, the seats were hushed, and the air felt a little too neat for a true accident."
    )
    world.say(
        f"People pointed at {clue.location}, but nobody could say who had seen the clue last."
    )


def flashback(world: World, suspect: Entity, clue: Entity) -> None:
    world.para()
    world.say(
        f"Then came a flashback: {suspect.label} had been near the curtain before the show."
    )
    world.say(
        f"{suspect.label.capitalize()} had noticed the clue, checked the empty aisle, and given a quick skedaddle."
    )
    world.say(
        f"It had not looked like theft then, only a nervous rush to hide something before the matinee began."
    )


def reveal(world: World, child: Entity, suspect: Entity, clue: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} put the pieces together: {suspect.label} had moved {clue.label} to keep it safe, not to keep it."
    )
    world.say(
        f"When the show ended, {suspect.label} returned with the missing item and explained the whole awkward truth."
    )
    world.say(
        f"The mystery was solved, and the theater felt calm again, with the clue back where everyone could see it."
    )


def close_story(world: World, child: Entity, suspect: Entity, clue: Entity) -> None:
    world.say(
        f"{child.id} smiled at the solved puzzle, because the best whodunit is the one that ends with the right answer and the right prop."
    )


# ---------------------------------------------------------------------------
# Build world
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(SETTING)

    suspect_cfg = _safe_lookup(SUSPECTS, params.suspect)
    clue_cfg = _safe_lookup(CLUES, params.clue)

    child = world.add(Entity(
        id=random.choice(NAMES),
        kind="character",
        type="child",
        meters={"attention": 1.0},
        memes={"curiosity": 1.0},
    ))
    adult = world.add(Entity(
        id=suspect_cfg.id,
        kind="character",
        type=suspect_cfg.role,
        label=suspect_cfg.label,
        meters={"nervousness": 0.6 if suspect_cfg.id != "usher" else 0.2},
        memes={"secrecy": 0.7 if suspect_cfg.id != "usher" else 0.2},
    ))
    clue = world.add(Entity(
        id=clue_cfg.id,
        kind="thing",
        type="prop",
        label=clue_cfg.label,
        phrase=clue_cfg.label,
        owner=adult.id if params.suspect != "usher" else "stage",
    ))

    world.facts.update(
        child=child,
        adult=adult,
        clue=clue,
        suspect_cfg=suspect_cfg,
        clue_cfg=clue_cfg,
    )

    intro(world, child, adult, clue)
    world.para()
    establish_scene(world, clue)
    flashback(world, adult, clue)
    reveal(world, child, adult, clue)
    close_story(world, child, adult, clue)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    adult = _safe_fact(world, f, "adult")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a small whodunit story set at a matinee where {adult.label} and a child notice that {clue.label} is missing.',
        f'Tell a mystery story with the words "context", "skedaddle", and "matinee", and include a flashback that explains the clue.',
        f'Write a child-friendly detective story in which a suspicious moment turns out to be a misunderstanding at the theater.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What kind of story is this one?",
            answer="It is a small whodunit set at a matinee in a theater, with a flashback that helps solve the mystery.",
        ),
        QAItem(
            question=f"What went missing during the show?",
            answer=f"{clue.phrase} went missing, which made the theater feel suspicious and puzzling.",
        ),
        QAItem(
            question=f"How did the flashback help?",
            answer=f"It showed that {adult.label} had moved {clue.label} earlier and then hurried away in a nervous skedaddle.",
        ),
        QAItem(
            question=f"Who figured out the answer?",
            answer=f"{child.id} put the clues together and realized the missing item had only been hidden, not stolen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a matinee?",
            answer="A matinee is a daytime performance, often in a theater, where people come to watch a show in the afternoon.",
        ),
        QAItem(
            question="What does skedaddle mean?",
            answer="To skedaddle means to hurry away quickly, usually because someone is nervous or in a rush.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier, before the current moment.",
        ),
        QAItem(
            question="What is context?",
            answer="Context is the surrounding information that helps you understand what is happening and why it matters.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_at_theater.
matinee(show1).
suspect(usher; actor; friend; manager).
clue(program; key; glove; ticket_stub).

motive(usher, safety).
motive(actor, rehearsal).
motive(friend, fear).
motive(manager, order).

suspect_can_hide(usher, program).
suspect_can_hide(actor, glove).
suspect_can_hide(friend, ticket_stub).
suspect_can_hide(manager, key).

mystery(S, C) :- suspect(S), clue(C), suspect_can_hide(S, C).
shown_mystery(S, C) :- mystery(S, C).
#show mystery/2.
#show shown_mystery/2.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("show", "show1"),
        asp.fact("place", "theater"),
        asp.fact("setting", "matinee"),
    ]
    for s in SUSPECTS.values():
        lines.append(asp.fact("suspect", s.id))
        lines.append(asp.fact("role", s.id, s.role))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("located", c.id, c.location))
    return "\n".join(lines)


def asp_program(show: str = "#show mystery/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_mysteries() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = set((s, c) for s in SUSPECTS for c in CLUES)
    cl = set(asp_mysteries())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} mystery pairs.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld at a matinee.")
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--setting", choices=["theater"], default="theater")
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
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    return StoryParams(suspect=suspect, clue=clue, setting=getattr(args, "setting", None), seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    if params.suspect not in SUSPECTS:
        pass
    if params.clue not in CLUES:
        pass

    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind}, type={e.type}, meters={e.meters}, memes={e.memes}")
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


CURATED = [
    StoryParams(suspect="usher", clue="program"),
    StoryParams(suspect="actor", clue="glove"),
    StoryParams(suspect="friend", clue="ticket_stub"),
    StoryParams(suspect="manager", clue="key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for s, c in asp_mysteries():
            print(f"{s} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
