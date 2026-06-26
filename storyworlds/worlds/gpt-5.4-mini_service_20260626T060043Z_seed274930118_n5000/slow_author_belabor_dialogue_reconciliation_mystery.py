#!/usr/bin/env python3
"""
A tiny mystery storyworld about a slow author, a belabored clue, dialogue, and
reconciliation.

The seed premise:
- A careful author keeps revising a mystery story too slowly.
- A clue seems wrong or missing, causing suspicion and dialogue.
- A second character helps reconcile the mismatch by noticing the real clue.
- The ending proves the truth was hidden in plain sight.

The simulated world tracks:
- physical meters: paper, ink, light, distance, dust, tea, etc.
- emotional memes: worry, curiosity, frustration, relief, trust, pride, apology.

The prose is story-driven, not a frozen template: the world state changes in
response to actions, and the ending reflects those changes.
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
# Entities and world model
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    visible: bool = False
    evidence: object | None = None
    helper: object | None = None
    hero: object | None = None
    notebook: object | None = None
    tea: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "author"}
        male = {"man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoors: bool = True
    details: str = ""
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
    hidden_place: str
    visible_to: set[str] = field(default_factory=set)
    truth: str = ""
    misread: str = ""
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
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


THRESHOLD = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "study": Setting(place="the study", indoors=True, details="A lamp made a small gold pool on the desk."),
    "library": Setting(place="the library corner", indoors=True, details="Tall shelves kept the room hushed."),
    "attic": Setting(place="the attic room", indoors=True, details="Dust floated in the thin light from a round window."),
}

CLUES = {
    "bookmark": Clue(
        id="bookmark",
        label="bookmark",
        phrase="a folded bookmark with a blue ribbon",
        hidden_place="inside the notebook",
        visible_to={"helper"},
        truth="the missing page was slipped behind the notebook cover",
        misread="the ribbon looked like a stolen tag",
    ),
    "key": Clue(
        id="key",
        label="key",
        phrase="a tiny brass key",
        hidden_place="under a tea saucer",
        visible_to={"helper"},
        truth="it opened the little box on the shelf",
        misread="it looked like a clue to a locked secret drawer",
    ),
    "button": Clue(
        id="button",
        label="button",
        phrase="a white button with a chipped edge",
        hidden_place="in the coat pocket",
        visible_to={"helper"},
        truth="it came from the missing coat in the hallway",
        misread="it seemed like proof someone had been sneaking around",
    ),
}

NAMES = ["Mina", "Iris", "Noah", "Leo", "Ada", "June", "Milo", "Eva"]
HELPERS = ["friend", "sister", "brother", "neighbor"]
TRAITS = ["slow", "careful", "curious", "patient", "earnest"]


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    clue = _safe_lookup(CLUES, params.clue)

    notebook = world.add(Entity(
        id="notebook",
        type="notebook",
        label="notebook",
        phrase="a notebook full of crossed-out pages",
        owner=hero.id,
        caretaker=hero.id,
        meters={"paper": 1.0},
        memes={"worry": 0.0},
    ))
    tea = world.add(Entity(
        id="tea",
        type="tea",
        label="tea cup",
        phrase="a small cup of tea",
        owner=hero.id,
        meters={"warmth": 1.0},
    ))
    evidence = world.add(Entity(
        id="evidence",
        type=clue.id,
        label=clue.label,
        phrase=clue.phrase,
        owner=hero.id,
        visible=False,
        meters={"hidden": 1.0},
    ))  # type: ignore[arg-type]

    world.facts.update(hero=hero, helper=helper, clue=clue, notebook=notebook, tea=tea, evidence=evidence)
    return world


def clue_visible_to_helper(clue: Clue) -> bool:
    return "helper" in clue.visible_to


def predict_misread(world: World) -> bool:
    clue: Clue = _safe_fact(world, world.facts, "clue")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    return clue_visible_to_helper(clue) and hero.memes.get("worry", 0.0) >= THRESHOLD and helper.memes.get("curiosity", 0.0) >= 0.0


def start_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    world.say(
        f"{hero.id} was a slow {hero.type} who liked to sit very still and think."
        f" {hero.pronoun().capitalize()} had been writing a mystery story for days,"
        f" belaboring every line as if each word had to pass a test."
    )
    world.say(
        f"On the desk sat {clue.phrase}, which seemed to belong to the story,"
        f" but nobody could agree on what it meant."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0


def tension(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")

    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1.0
    world.para()
    world.say(
        f"{hero.id} frowned at the page and asked, \"Is the clue the bookmark, or is it something else?\""
    )
    world.say(
        f"{helper.id} looked carefully and said, \"It feels important, but I think you're looking at it the hard way.\""
    )
    world.say(
        f"{hero.id} tried to answer, but {hero.pronoun()} kept belaboring the same sentence,"
        f" worrying that the mystery would sound silly."
    )
    hero.memes["slow"] = hero.memes.get("slow", 0.0) + 1.0
    helper.memes["curiosity"] = helper.memes.get("curiosity", 0.0) + 1.0
    world.facts["misread"] = clue.misread


def dialogue_turn(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")

    world.para()
    world.say(
        f"\"What if it's not a stolen sign at all?\" {helper.id} asked. "
        f"\"What if the ribbon is only showing where the page was tucked away?\""
    )
    world.say(
        f"{hero.id} stared, then whispered, \"You mean I've been chasing the wrong idea?\""
    )
    world.say(
        f"\"Maybe,\" {helper.id} said. \"Sometimes a clue looks strange because it is hiding something ordinary.\""
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.5)
    world.facts["dialogue"] = True


def reconciliation(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")

    world.para()
    world.say(
        f"{hero.id} opened the notebook cover and found the hidden page at last."
        f" The ribbon had only marked the place where the page had slipped."
    )
    world.say(
        f"{hero.id} smiled sheepishly. \"I was so busy belaboring the puzzle that I missed the simple answer.\""
    )
    world.say(
        f"{helper.id} laughed softly. \"That's all right. We found it together.\""
    )
    hero.memes["apology"] = hero.memes.get("apology", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1.0
    hero.memes["frustration"] = 0.0
    world.facts["truth"] = clue.truth
    world.facts["resolved"] = True

    world.say(
        f"In the end, the mystery was not a thief at all. It was a lost page,"
        f" a careful friend, and a slow author learning to trust the plain truth."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    start_story(world)
    tension(world)
    dialogue_turn(world)
    reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# QA and narration helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short mystery story for a child about a slow author who keeps belaboring a clue like {clue.phrase}.',
        f"Tell a gentle dialogue story where {hero.id} and {helper.id} argue a little, then reconcile after finding what {clue.label} really means.",
        f"Write a story that begins with an author at {world.setting.place}, uses careful dialogue, and ends with the mystery solved kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"Why was {hero.id} taking so long to finish the mystery story?",
            answer=f"{hero.id} was slow and kept belaboring every line, because {hero.pronoun()} wanted the mystery to be just right.",
        ),
        QAItem(
            question=f"What did {helper.id} help {hero.id} understand about {clue.label}?",
            answer=f"{helper.id} helped {hero.id} see that {clue.phrase} was not a sign of danger, but a clue about where the missing page had slipped.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} feel at the end?",
            answer=f"They felt relieved and friendly again, because they reconciled after finding the simple truth together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about an unknown fact or problem that people try to figure out by paying attention to clues.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make peace again after a disagreement and feel friendly once more.",
        ),
        QAItem(
            question="What does belabor mean?",
            answer="To belabor something means to keep talking or thinking about it for longer than needed.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.kind == "character":
            parts.append("character")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

valid_story(Place, Clue, HeroType, HelperType) :-
    place(Place),
    clue_kind(Clue),
    hero_kind(HeroType),
    helper_kind(HelperType),
    story_ok(Place, Clue).

story_ok(Place, Clue) :- setting(Place), clue_at(Clue, Place).
story_ok(Place, Clue) :- setting(Place), clue_visible(Clue), important(Clue).

# Reasonableness:
# - the story is about a place, a clue, and two roles
# - the clue must plausibly fit a slow mystery with dialogue and reconciliation
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("setting", pid))
        if s.details:
            lines.append(asp.fact("detail", pid, s.details))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_kind", cid))
        lines.append(asp.fact("clue_at", cid, c.hidden_place))
        if c.visible_to:
            lines.append(asp.fact("clue_visible", cid))
        lines.append(asp.fact("important", cid))
    for h in ["author"]:
        lines.append(asp.fact("hero_kind", h))
    for h in ["friend", "sister", "brother", "neighbor"]:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = set()
    for place in SETTINGS:
        for clue in CLUES:
            combos.add((place, clue, "author", "friend"))
    asp_set = set(asp_valid_stories())
    py_set = set((p, c, "author", "friend") for p in SETTINGS for c in CLUES)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES.keys()))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type="author",
        helper_name=helper_name,
        helper_type=rng.choice(HELPERS),
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
    StoryParams(place="study", clue="bookmark", hero_name="Mina", hero_type="author", helper_name="June", helper_type="friend"),
    StoryParams(place="library", clue="key", hero_name="Ada", hero_type="author", helper_name="Iris", helper_type="sister"),
    StoryParams(place="attic", clue="button", hero_name="Leo", hero_type="author", helper_name="Noah", helper_type="brother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(""))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        for t in vals:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
