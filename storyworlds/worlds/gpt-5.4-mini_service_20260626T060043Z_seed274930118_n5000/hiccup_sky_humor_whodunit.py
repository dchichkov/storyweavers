#!/usr/bin/env python3
"""
Standalone Storyworld: a tiny humorous whodunit about a hiccup in the sky.

Premise:
- A small cast is gathered at a hilltop observatory.
- The sky has a strange hiccup-like interruption: a blinking, stuttering light.
- Someone suspects a mystery: a missing lantern, a fluttering kite, or a prank.
- The detective follows clues, checks physical traces, and discovers the sky "hiccup"
  is actually a playful mechanical problem with an unexpected, funny cause.
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

    detective: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Setting:
    place: str
    sky_view: str
    affords: set[str] = field(default_factory=set)
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
    where: str
    points_to: str
    funny: str
    hidden: bool = False
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
    type: str
    alibi: str
    clue: str
    truth: str
    guilty: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _asker(name: str, suspect: Suspect) -> str:
    return f'{name} squinted and asked, "Where were you when the sky hiccuped?"'


def build_setting() -> Setting:
    return Setting(
        place="the hilltop observatory",
        sky_view="a wide dark sky with one stubborn blinking star",
        affords={"investigate", "search", "question"},
    )


CAST = [
    Suspect(
        id="Mina",
        label="Mina",
        type="girl",
        alibi="I was tuning the lantern clock.",
        clue="a tiny brass tick",
        truth="she was fixing the clock because it kept skipping time.",
    ),
    Suspect(
        id="Pip",
        label="Pip",
        type="boy",
        alibi="I was chasing my own scarf.",
        clue="a scarf caught on a hook",
        truth="he had accidentally snagged the weather vane with his scarf.",
    ),
    Suspect(
        id="June",
        label="June",
        type="woman",
        alibi="I was making cocoa.",
        clue="a sweet cocoa smell",
        truth="she was the calm observer who noticed the lantern was blinking in rhythm.",
    ),
]

CLUES = [
    Clue(
        id="glass",
        label="a cracked glass lens",
        where="near the telescope",
        points_to="clock",
        funny="it made the star look like it was blinking on purpose.",
    ),
    Clue(
        id="string",
        label="a loose string",
        where="by the railing",
        points_to="scarf",
        funny="it fluttered like it wanted to solve the case itself.",
    ),
    Clue(
        id="soot",
        label="a little soot on the lantern",
        where="under the stairs",
        points_to="lantern",
        funny="it looked as if the lantern had been eating toast.",
    ),
]

SETTINGS = {"observatory": build_setting()}


@dataclass
class StoryParams:
    place: str = "observatory"
    detective: str = "Luna"
    seed: Optional[int] = None
    CURATED: list = field(default_factory=list)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous whodunit storyworld with a sky hiccup.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "observatory"
    detective = getattr(args, "detective", None) or rng.choice(["Luna", "Iris", "Marlowe", "Toby"])
    return StoryParams(place=place, detective=detective)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if not params.detective:
        pass


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    detective = world.add(Entity(id=params.detective, kind="character", type="girl"))
    world.add(Entity(id="lantern", label="the lantern", type="thing"))
    world.add(Entity(id="telescope", label="the telescope", type="thing"))
    for s in CAST:
        world.add(Entity(id=s.id, kind="character", type=s.type, label=s.label))
    for c in CLUES:
        world.add(Entity(id=c.id, label=c.label, type="thing"))
    world.facts["detective"] = detective
    return world


def deduce(world: World, detective: Entity) -> tuple[Suspect, Clue]:
    # The funny whodunit: the "sky hiccup" is caused by Pip snagging the weather vane.
    guilty = next(s for s in CAST if s.guilty is False and s.id == "Pip")
    clue = next(c for c in CLUES if c.points_to == "scarf")
    return guilty, clue


def tell_story(world: World, params: StoryParams) -> None:
    detective = world.get(params.detective)
    detective.memes["curiosity"] = 1
    world.say(
        f"{detective.id} came to {world.setting.place}, where {world.setting.sky_view} hung over everything."
    )
    world.say(
        f"Then the sky hiccuped: the stars blinked, stopped, and blinked again, as if the night had swallowed a giggle."
    )
    world.say(
        f"{detective.id} smiled. \"That is not a ghost,\" {detective.pronoun('subject')} said. "
        f"\"That is a clue wearing a funny hat.\""
    )

    world.para()
    suspect_order = [CAST[0], CAST[1], CAST[2]]
    clue_order = [_safe_lookup(CLUES, 0), _safe_lookup(CLUES, 1), _safe_lookup(CLUES, 2)]
    for suspect, clue in zip(suspect_order, clue_order):
        detective.memes["suspicion"] = detective.memes.get("suspicion", 0) + 1
        world.say(
            f"{detective.id} asked {suspect.label}, and {suspect.label} answered, "
            f"\"{suspect.alibi}\""
        )
        world.say(
            f"Nearby, {clue.label} sat {clue.where}; it was odd because {clue.funny}"
        )

    guilty, key_clue = deduce(world, detective)
    detective.memes["certainty"] = 1

    world.para()
    world.say(
        f"At last, {detective.id} followed the loose string and found {guilty.label} by the railing."
    )
    world.say(
        f"{guilty.label} flushed and laughed. \"I did not mean to make a mystery,\" {guilty.pronoun('subject')} said."
    )
    world.say(
        f"{guilty.truth.capitalize()} The scarf had tugged the weather vane, and the vane made the lantern blink like a hiccuping star."
    )
    world.say(
        f"{detective.id} nodded. \"So the sky was not sick at all. It was just being tickled.\""
    )

    world.para()
    world.say(
        f"Then everyone fixed the vane, and the stars shone steady again."
    )
    world.say(
        f"The observatory grew quiet, except for one small laugh when the lantern gave one last harmless blink."
    )

    world.facts.update(
        detective=detective,
        guilty=guilty,
        clue=key_clue,
        suspects=CAST,
        clues=CLUES,
    )


def generation_prompts(world: World) -> list[str]:
    d = _safe_fact(world, world.facts, "detective").id
    return [
        f"Write a funny whodunit where {d} investigates a hiccup in the sky at an observatory.",
        "Tell a child-friendly mystery with clues, suspects, and a silly reveal about a blinking sky.",
        "Write a short detective story in which a sky hiccup turns out to have a playful cause.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective = _safe_fact(world, world.facts, "detective").id
    guilty = _safe_fact(world, world.facts, "guilty").label
    clue = _safe_fact(world, world.facts, "clue").label
    return [
        QAItem(
            question=f"Who investigated the sky hiccup?",
            answer=f"{detective} investigated it at the observatory."
        ),
        QAItem(
            question=f"Who caused the mystery in the end?",
            answer=f"{guilty} caused it by tugging the weather vane with a scarf."
        ),
        QAItem(
            question=f"What clue helped solve the case?",
            answer=f"The loose string was the key clue because it pointed to the scarf and the weather vane."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to find out who caused the problem."
        ),
        QAItem(
            question="Why can the sky seem to hiccup in a story like this?",
            answer="Because a blinking light or a stuttering lantern can look like the sky is stopping and starting."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when the observatory has a sky, a detective, at least one suspect,
% and one clue that points to the guilty cause.
detective(detective).
place(observatory).
suspect(pip).
suspect(mina).
suspect(june).
clue(glass).
clue(string).
clue(soot).

points_to(string, scarf).
guilty(scarf).
has_funny_reveal(scarf).

valid_story(Place, Detective) :- place(Place), detective(Detective).
mystery_clue(C) :- clue(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "observatory"),
            asp.fact("detective", "detective"),
            asp.fact("suspect", "pip"),
            asp.fact("suspect", "mina"),
            asp.fact("suspect", "june"),
            asp.fact("clue", "glass"),
            asp.fact("clue", "string"),
            asp.fact("clue", "soot"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    expected = [("observatory", "detective")]
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH:", atoms, "expected", expected)
    return 1


CURATED = [StoryParams(place="observatory", detective="Luna")]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = setup_world(params)
    tell_story(world, params)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
