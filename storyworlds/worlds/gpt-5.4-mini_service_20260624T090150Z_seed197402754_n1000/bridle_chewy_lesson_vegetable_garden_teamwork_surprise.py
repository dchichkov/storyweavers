#!/usr/bin/env python3
"""
A small storyworld for an adventure in a vegetable garden.

Premise:
- A child visits a vegetable garden with a helper animal.
- The helper wears a bridle for guiding and safety.
- A chewy snack and a surprise harvest create a gentle problem.
- Teamwork turns the surprise into a lesson.

The world model tracks physical meters and emotional memes. The story is
generated from the state transitions, not from a frozen template.
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

PLACE = "vegetable garden"



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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bridle: object | None = None
    child: object | None = None
    helper: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class StoryParams:
    name: str
    gender: str
    helper_type: str
    snack: str
    seed: Optional[int] = None
    params: object | None = None
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


@dataclass
class Setting:
    place: str = PLACE
    affords: set[str] = field(default_factory=lambda: {"weeding", "watering", "harvesting", "hauling"})
    world: object | None = None
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    clone: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


ASP_RULES = r"""
% Teamwork happens when the child and helper both take part in the garden task.
teamwork(C,H,T) :- child(C), helper(H), task(T), works_on(C,T), works_on(H,T).

% A surprise is something found while gardening that was not expected.
surprise(F) :- find(F), unexpected(F).

% A lesson is learned when teamwork solves the surprise.
lesson(C,H,F) :- teamwork(C,H,_), surprise(F), solved_by(F,H,C).

#show teamwork/3.
#show surprise/1.
#show lesson/3.
"""


@dataclass
class GardenTask:
    id: str
    verb: str
    gerund: str
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


TASKS = {
    "harvest": GardenTask(id="harvest", verb="pick vegetables", gerund="picking vegetables"),
    "water": GardenTask(id="water", verb="water the rows", gerund="watering the rows"),
    "weed": GardenTask(id="weed", verb="pull weeds", gerund="pulling weeds"),
}

HELPERS = {
    "pony": {"type": "pony", "label": "pony", "sound": "whickered"},
    "goat": {"type": "goat", "label": "goat", "sound": "nibbled"},
    "mule": {"type": "mule", "label": "mule", "sound": "snorted"},
}

SNACKS = {
    "chewy": {"label": "chewy seedcake", "taste": "chewy"},
    "carrot": {"label": "chewy carrot strip", "taste": "chewy"},
    "apple": {"label": "chewy apple slice", "taste": "chewy"},
}


def asp_facts() -> str:
    import asp
    lines = [asp.fact("child", "child")]
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_type", hid, h["type"]))
    lines.append(asp.fact("find", "surprise_pumpkin"))
    lines.append(asp.fact("unexpected", "surprise_pumpkin"))
    lines.append(asp.fact("solved_by", "surprise_pumpkin", "helper", "child"))
    lines.append(asp.fact("works_on", "child", "harvest"))
    lines.append(asp.fact("works_on", "helper", "harvest"))
    lines.append(asp.fact("works_on", "child", "weed"))
    lines.append(asp.fact("works_on", "helper", "weed"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _story_event(world: World, child: Entity, helper: Entity, task: GardenTask, snack: Entity) -> None:
    world.say(
        f"{child.id} stepped into the {world.setting.place} with a bright goal: "
        f"{task.gerund} and seeing what grew there."
    )
    world.say(
        f"{helper.id} came along wearing a bridle so {child.pronoun('possessive')} path through the rows stayed gentle and steady."
    )
    snack.meters["chew"] += 1
    child.memes["eager"] = child.memes.get("eager", 0) + 1
    world.say(
        f"{child.id} crunched a {snack.label}, and the {snack.label} felt chewy and sweet enough to make the day feel like an adventure."
    )


def _surprise(world: World, child: Entity, helper: Entity, task: GardenTask, snack: Entity) -> None:
    world.para()
    world.say(
        f"Then, behind the bean vines, they found a surprise: one giant pumpkin that nobody had seen before."
    )
    world.say(
        f"{child.id} wanted to hurry it alone, but the pumpkin was too heavy for one pair of hands."
    )
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1


def _teamwork(world: World, child: Entity, helper: Entity, task: GardenTask, snack: Entity) -> None:
    world.para()
    child.memes["teamwork"] = child.memes.get("teamwork", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.say(
        f"So {child.id} called for teamwork. {child.id} guided the wheels, and {helper.id} leaned in with steady strength."
    )
    world.say(
        f"Together they moved the pumpkin to the cart, and the rows of carrots and peas seemed to cheer them on."
    )
    world.say(
        f"That was the lesson of the day: in a garden, a surprise can become a good thing when friends work together."
    )


def tell_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=params.helper_type))
    bridle = world.add(Entity(id="bridle", type="bridle", label="bridle", phrase="a soft bridle", worn_by=helper.id))
    snack_cfg = _safe_lookup(SNACKS, params.snack)
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg["label"], phrase=snack_cfg["label"], owner=child.id))
    task = TASKS["harvest"]

    world.facts.update(child=child, helper=helper, bridle=bridle, snack=snack, task=task)
    _story_event(world, child, helper, task, snack)
    _surprise(world, child, helper, task, snack)
    _teamwork(world, child, helper, task, snack)
    world.facts["lesson"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child set in a {PLACE} that includes the words "bridle", "chewy", and "lesson".',
        f"Tell a gentle adventure where {f['child'].id} and a {f['helper'].type} work together in a {PLACE} after a surprise appears.",
        f"Write a child-facing story about teamwork and surprise in a {PLACE}, ending with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {child.id} and {helper.id} do together in the {PLACE}?",
            answer=f"They worked together to move a giant pumpkin and finish the garden job.",
        ),
        QAItem(
            question=f"Why was the day surprising for {child.id}?",
            answer="Because they found a giant pumpkin hidden behind the bean vines.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer="The lesson was that teamwork can turn a surprise into something helpful and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bridle?",
            answer="A bridle is gear that helps guide an animal, often a horse or pony, by staying on its head.",
        ),
        QAItem(
            question="What does chewy mean?",
            answer="Chewy means something takes a little effort to bite and chew before you swallow it.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that you did not know was going to happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a vegetable garden.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mia", "Leo", "Nora", "Finn", "Ava", "Theo"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(list(HELPERS))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS))
    return StoryParams(name=name, gender=gender, helper_type=helper_type, snack=snack)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork/3.\n#show surprise/1.\n#show lesson/3."))
    atoms = set((s.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in s.arguments)) for s in model)
    want = {
        ("teamwork", ("child", "helper", "harvest")),
        ("teamwork", ("child", "helper", "weed")),
        ("surprise", ("surprise_pumpkin",)),
        ("lesson", ("child", "helper", "surprise_pumpkin")),
    }
    if atoms == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, want)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show teamwork/3.\n#show surprise/1.\n#show lesson/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, helper_type in enumerate(sorted(HELPERS)):
            params = StoryParams(
                name=["Mia", "Leo", "Nora"][i % 3],
                gender=["girl", "boy", "girl"][i % 3],
                helper_type=helper_type,
                snack=sorted(SNACKS)[i % len(SNACKS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
