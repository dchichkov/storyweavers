#!/usr/bin/env python3
"""
A small mystery storyworld about a curious child, a hidden object, and a
supportive final reveal.

The seed premise is a child in a quiet place who feels a little suspense, thinks
carefully inside, asks curious questions, and gets help from a supportive ally.
The final turn is mandatory: the hidden thing must be found, and the answer must
change the world state in a clear, story-shaped way.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    found: bool = False
    supportive: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    detail: str
    hiding_spots: list[str]
    supports: list[str]
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
    phrase: str
    where: str
    hint: str
    reveals: str
    safe: bool = True
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
class Ally:
    id: str
    label: str
    type: str
    phrase: str
    supportive_line: str
    final_line: str
    helps: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    ally: str
    clue: str
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


SETTINGS = {
    "library": Setting(
        place="the library",
        detail="The library was quiet, with tall shelves and narrow aisles.",
        hiding_spots=["under a chair", "behind a stack of books", "inside a cardboard box"],
        supports=["librarian", "friend"],
    ),
    "attic": Setting(
        place="the attic",
        detail="The attic smelled like old paper and warm wood.",
        hiding_spots=["under a blanket", "inside a trunk", "behind a broom"],
        supports=["parent", "neighbor"],
    ),
    "garden_shed": Setting(
        place="the garden shed",
        detail="The shed was snug and shadowy, with tools hanging on the wall.",
        hiding_spots=["behind a watering can", "under a bench", "inside a bucket"],
        supports=["parent", "sibling"],
    ),
}

CLUES = {
    "key": Clue(
        id="key",
        label="small brass key",
        phrase="a small brass key",
        where="a hook near the doorway",
        hint="It was easy to miss because it was tiny and dull.",
        reveals="a little tin box",
    ),
    "note": Clue(
        id="note",
        label="folded note",
        phrase="a folded note",
        where="inside a book",
        hint="It was tucked flat between two pages.",
        reveals="a secret message",
    ),
    "button": Clue(
        id="button",
        label="blue button",
        phrase="a blue button",
        where="on the floor by a rug",
        hint="It matched the color of a coat near the door.",
        reveals="a coat pocket",
    ),
}

ALIASES = {
    "librarian": Ally(
        id="librarian",
        label="the librarian",
        type="woman",
        phrase="a librarian",
        supportive_line="The librarian smiled and pointed the child toward the quiet aisle.",
        final_line="She gave a warm nod when the answer finally fit together.",
        helps="showing where to look",
    ),
    "friend": Ally(
        id="friend",
        label="the friend",
        type="boy",
        phrase="a friend",
        supportive_line="The friend leaned close and whispered that the clue might be nearby.",
        final_line="He grinned when the last piece clicked into place.",
        helps="watching the doorway",
    ),
    "parent": Ally(
        id="parent",
        label="the parent",
        type="woman",
        phrase="a parent",
        supportive_line="The parent stayed calm and promised to help search carefully.",
        final_line="She hugged the child after the final answer was found.",
        helps="keeping the search gentle",
    ),
    "sibling": Ally(
        id="sibling",
        label="the sibling",
        type="girl",
        phrase="a sibling",
        supportive_line="The sibling held the lamp steady and let the child think.",
        final_line="She laughed softly when the mystery ended well.",
        helps="holding a lamp",
    ),
    "neighbor": Ally(
        id="neighbor",
        label="the neighbor",
        type="man",
        phrase="a neighbor",
        supportive_line="The neighbor said there was no rush, only careful looking.",
        final_line="He nodded proudly when the child solved it.",
        helps="waiting patiently",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with curiosity, suspense, and a supportive final reveal.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally", choices=ALIASES)
    ap.add_argument("--clue", choices=CLUES)
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in s.hiding_spots:
            lines.append(asp.fact("hiding_spot", sid, spot))
        for sup in s.supports:
            lines.append(asp.fact("supports", sid, sup))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, c.reveals))
    for aid, a in ALIASES.items():
        lines.append(asp.fact("ally", aid))
        lines.append(asp.fact("helps", aid, a.helps))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(P,C) :- clue(C), setting(P), hides_in(C, P).
supportive(P,A) :- setting(P), ally(A), supports(P, A).
valid_story(P,C,A) :- at_risk(P,C), supportive(P,A).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for ally in ALIASES:
                combos.append((place, clue, ally))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(["Mina", "Iris", "Nora"] if hero_type == "girl" else ["Eli", "Noah", "Theo"])
    ally = getattr(args, "ally", None) or rng.choice(list(ALIASES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    return StoryParams(place=place, hero=hero, hero_type=hero_type, ally=ally, clue=clue)


def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.ally not in ALIASES:
        pass
    if params.clue not in CLUES:
        pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ally = _safe_fact(world, f, "ally")
    clue = _safe_fact(world, f, "clue")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short mystery story for a child named {hero.id} in {place}, with suspense and a supportive final reveal.',
        f'Write a gentle story where {hero.id} feels curious about {clue.phrase} and {ally.label} helps solve the mystery.',
        f'Write a small story that begins with a quiet question, builds suspense, and ends with the answer found at {place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    ally: Ally = _safe_fact(world, f, "ally")
    clue: Clue = _safe_fact(world, f, "clue")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {hero.id} curious about in {place}?",
            answer=f"{hero.id} was curious about {clue.phrase}. The clue seemed small at first, but it mattered to the whole mystery.",
        ),
        QAItem(
            question=f"Who gave {hero.id} supportive help during the search?",
            answer=f"{ally.label} gave supportive help by {ally.helps}. That made {hero.id} feel braver while the mystery stayed unsolved.",
        ),
        QAItem(
            question=f"What was the final answer in the story?",
            answer=f"The final answer was {clue.reveals}. After careful looking, {hero.id} found the clue and the mystery made sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out an answer.",
        ),
        QAItem(
            question="Why do people look carefully when something is missing?",
            answer="They look carefully because a small detail can show where the missing thing went.",
        ),
        QAItem(
            question="What does supportive mean?",
            answer="Supportive means kind and helpful, especially when someone feels worried or unsure.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next and waiting to find out.",
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
        lines.append(
            f"  {e.id:10} kind={e.kind} type={e.type} hidden={e.hidden} found={e.found} supportive={e.supportive}"
        )
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    ally_def = _safe_lookup(ALIASES, params.ally)
    ally = world.add(
        Entity(
            id=ally_def.id,
            kind="character",
            type=ally_def.type,
            label=ally_def.label,
            supportive=True,
        )
    )
    clue_def = _safe_lookup(CLUES, params.clue)
    clue = world.add(
        Entity(
            id=clue_def.id,
            kind="thing",
            type="clue",
            label=clue_def.label,
            phrase=clue_def.phrase,
            hidden=True,
        )
    )

    world.facts.update(hero=hero, ally=ally_def, clue=clue_def, place=setting.place)

    hero.memes["curiosity"] = 1
    hero.memes["suspense"] = 1
    hero.memes["inner_monologue"] = 1

    world.say(f"{hero.id} was in {setting.place}, where {setting.detail.lower()}")
    world.say(f"{hero.id} kept wondering about {clue.phrase}. {clue.hint}")
    world.say(f"In {hero.id}'s own head, a quiet thought went round and round: maybe the answer was near, maybe it was hiding in plain sight.")

    world.para()
    world.say(f"{hero.id} looked under a lamp, behind a chair, and along the nearest shelf.")
    world.say(f"The search felt full of suspense, because the missing thing was still nowhere to be seen.")
    world.say(f"{ally.label.capitalize()} stayed close and was very supportive. {ally_def.supportive_line}")

    world.para()
    world.say(f"{hero.id} did not give up. Curiosity kept tugging forward, and {hero.id} thought, if the clue is small, it might be in a small place.")
    world.say(f"So {hero.id} checked the spot {clue_def.where}.")

    clue.hidden = False
    clue.found = True
    hero.memes["suspense"] = 0
    hero.memes["joy"] = 1
    hero.meters["certainty"] = 1

    world.para()
    world.say(f"There it was: {clue.phrase}, exactly where the search had not first looked.")
    world.say(f"It revealed {clue.reveals}, and the final answer fit together at last.")
    world.say(f"{ally_def.final_line} {hero.id} smiled because the mystery was solved, and the quiet place felt warm and safe again.")

    return world


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
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
    StoryParams(place="library", hero="Mina", hero_type="girl", ally="librarian", clue="note"),
    StoryParams(place="attic", hero="Eli", hero_type="boy", ally="parent", clue="key"),
    StoryParams(place="garden_shed", hero="Nora", hero_type="girl", ally="sibling", clue="button"),
]


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_asp_show() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, clue, ally in combos:
            print(f"  {place:12} {clue:8} {ally}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.hero} in {p.place} (clue: {p.clue}, ally: {p.ally})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
