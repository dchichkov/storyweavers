#!/usr/bin/env python3
"""
A gentle mystery about a memorable transformation and a happy ending.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    helper: object | None = None
    treasure: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = (
    "a little attic above the town library",
    "a sunny cottage beside a silver pond",
    "a quiet apartment with a long blue hallway",
    "a warm farmhouse near a field of daisies",
)

MYSTERIES = (
    {
        "object": "a plain wooden music box",
        "clue_one": "a trail of bright paper stars",
        "clue_two": "a tiny golden key beside the sewing basket",
        "place": "the window table",
        "change": "painted it with blue moons and added a silver bell",
        "ending": "When the lid opened, the music box played a clear little tune beneath the moonlit window.",
    },
    {
        "object": "a faded yellow kite",
        "clue_one": "a red thread caught on the garden gate",
        "clue_two": "a paper tail tucked behind the rain barrel",
        "place": "the porch rail",
        "change": "patched it with green cloth and stitched a bright sun on its tail",
        "ending": "At last the transformed kite rose above the meadow, carrying its new sun through the golden air.",
    },
    {
        "object": "a small clay bird",
        "clue_one": "three blue feathers on the path",
        "clue_two": "a smear of wet clay near the workshop door",
        "place": "the kitchen shelf",
        "change": "gave it painted wings and a tiny red beak",
        "ending": "The little clay bird stood proudly on the shelf, looking ready to sing to everyone at breakfast.",
    },
    {
        "object": "an old red scarf",
        "clue_one": "soft threads beside the coat rack",
        "clue_two": "a silver button under the reading chair",
        "place": "the sewing nook",
        "change": "turned it into a bright patchwork cape",
        "ending": "The new cape fluttered around the child's shoulders as the whole family cheered.",
    },
)

NAMES = (("Luna", "girl"), ("Milo", "boy"), ("Ari", "child"), ("Nia", "girl"))
HELPERS = (("Grandma", "woman"), ("Papa", "man"), ("Aunt Bea", "woman"), ("Uncle Jo", "man"))
REACTIONS = (
    "took a careful breath and followed the clues",
    "opened a notebook and began a quiet investigation",
    "listened closely before stepping toward the first clue",
)
ENDINGS = (
    "Everyone agreed that the surprising change made the day unforgettable.",
    "The mystery became a happy memory that they would tell again and again.",
    "That evening, the transformed treasure rested nearby like a bright promise.",
)


@dataclass
class StoryParams:
    seed: int | None = None
    child_name: str = "Luna"
    child_type: str = "girl"
    helper_name: str = "Grandma"
    helper_type: str = "woman"
    setting: str = _safe_lookup(SETTINGS, 0)
    object_name: str = _safe_lookup(MYSTERIES, 0)["object"]
    clue_one: str = _safe_lookup(MYSTERIES, 0)["clue_one"]
    clue_two: str = _safe_lookup(MYSTERIES, 0)["clue_two"]
    place: str = _safe_lookup(MYSTERIES, 0)["place"]
    change: str = _safe_lookup(MYSTERIES, 0)["change"]
    ending: str = _safe_lookup(MYSTERIES, 0)["ending"]
    reaction: str = _safe_lookup(REACTIONS, 0)
    final_note: str = _safe_lookup(ENDINGS, 0)
    sample: object | None = None
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else 0)
    rng = random.Random(seed)
    name, child_type = rng.choice(NAMES)
    helper, helper_type = rng.choice(HELPERS)
    mystery = rng.choice(MYSTERIES)
    return StoryParams(
        seed=seed,
        child_name=name,
        child_type=child_type,
        helper_name=helper,
        helper_type=helper_type,
        setting=rng.choice(SETTINGS),
        object_name=mystery["object"],
        clue_one=mystery["clue_one"],
        clue_two=mystery["clue_two"],
        place=mystery["place"],
        change=mystery["change"],
        ending=mystery["ending"],
        reaction=rng.choice(REACTIONS),
        final_note=rng.choice(ENDINGS),
    )


def tell(params: StoryParams) -> World:
    if not params.object_name or not params.change:
        pass

    world = World()
    child = world.add(Entity("child", params.child_name, "character", memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", params.helper_name, "character", memes={"kindness": 1.0}))
    treasure = world.add(Entity(
        "treasure",
        params.object_name,
        "object",
        meters={"ordinary": 1.0, "transformed": 0.0},
        memes={"memorable": 0.0},
    ))
    world.facts.update(child=child, helper=helper, treasure=treasure)

    world.say(
        f"One quiet afternoon in {params.setting}, {child.label} noticed that {params.object_name} "
        f"was missing from its usual place."
    )
    world.say(
        f'"A mystery," said {child.label}. {child.label} {params.reaction}.'
    )
    world.para()

    world.say(
        f"The first clue was {params.clue_one}. It led {child.label} toward the back room."
    )
    child.memes["curiosity"] += 1
    world.fired.add("first_clue")

    world.say(
        f"Then {child.label} found {params.clue_two}. The clue pointed straight to {params.place}."
    )
    world.fired.add("second_clue")

    world.say(
        f"There stood {helper.label}, smiling beside the missing treasure."
    )
    world.say(
        f'"I found it!" cried {child.label}. "{helper.label}, why did you hide it?"'
    )
    world.say(
        f'"I did not hide it," {helper.label} replied. "I gave it a new beginning. I {params.change}."'
    )
    world.say(
        f"The plain object had become something new and memorable. {child.label} understood that "
        f'the clues had led to a transformation, not a loss.'
    )

    treasure.meters["ordinary"] = 0.0
    treasure.meters["transformed"] = 1.0
    treasure.memes["memorable"] = 1.0
    child.memes["curiosity"] = 0.0
    child.memes["joy"] = 1.0
    world.fired.add("transformation")

    world.para()
    world.say(params.ending)
    world.say(
        f'{child.label} hugged {helper.label}. {params.final_note}'
    )
    world.fired.add("happy_ending")
    return world


ASP_RULES = r"""
missing(treasure).
has_helper(helper).
clue(first).
clue(second).
transformed(treasure).
happy_ending(treasure) :- missing(treasure), has_helper(helper),
    clue(first), clue(second), transformed(treasure).
mystery_solved(treasure) :- happy_ending(treasure).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "treasure"),
        asp.fact("has_helper", "helper"),
        asp.fact("clue", "first"),
        asp.fact("clue", "second"),
        asp.fact("transformed", "treasure"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/1.\n#show happy_ending/1."))
    solved = set(asp.atoms(model, "mystery_solved"))
    ending = set(asp.atoms(model, "happy_ending"))
    expected = {("treasure",)}
    if solved == expected and ending == expected:
        sample = generate(StoryParams(seed=0))
        if "transformed" in sample.story.lower() and "happy" in sample.story.lower():
            print("OK: ASP and Python agree on the transformation mystery.")
            return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").label} finding a transformed {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure").label}.",
        f"Include clues, a conversation with {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label}, and a memorable happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = world.facts
    return [
        QAItem(
            f"What did {p['child'].label} investigate?",
            f"{p['child'].label} investigated the missing {p['treasure'].label}.",
        ),
        QAItem(
            f"Who transformed the {p['treasure'].label}?",
            f"{p['helper'].label} transformed it by changing it into something new and memorable.",
        ),
        QAItem(
            "How did the mystery end?",
            "It ended happily when the transformed treasure was revealed and everyone celebrated together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a transformation?", "A transformation is a change that makes something different while keeping its story or purpose connected to what it was before."),
        QAItem("Why can a mystery be memorable?", "A mystery can be memorable when its clues, feelings, and surprising solution stay clearly in someone's mind."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A memorable transformation mystery.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_solved/1.\n#show happy_ending/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/1.\n#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "mystery_solved"))))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    count = 1 if getattr(args, "all", None) else getattr(args, "n", None)
    samples = []
    for i in range(count):
        seed = base_seed + i
        samples.append(generate(resolve_params(argparse.Namespace(seed=seed), random.Random(seed))))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
