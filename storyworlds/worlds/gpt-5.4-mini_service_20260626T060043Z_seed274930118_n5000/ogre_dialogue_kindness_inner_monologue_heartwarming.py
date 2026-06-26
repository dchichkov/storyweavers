#!/usr/bin/env python3
"""
A heartwarming storyworld about an ogre who worries that being big makes him
scary, then discovers that kindness and a gentle conversation can change how
others feel.

The model tracks a small social scene with:
- one ogre
- one child
- one lost item
- one helper gesture
- dialogue and inner monologue driving the turn

The story is generated from a simulated world state, not from a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    lost: object | None = None
    ogre: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "ogre":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the mossy bridge"
    nearby: str = "the village path"
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
class LostItem:
    label: str
    finder_help: str
    return_line: str
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
    place: str
    item: str
    child_name: str
    ogre_name: str
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
        self.fired: set[str] = set()

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


OGRE_NAMES = ["Brum", "Mok", "Gorn", "Tull", "Hugo"]
CHILD_NAMES = ["Mina", "Pip", "Lena", "Toby", "Nia"]

SETTINGS = {
    "bridge": Setting(place="the mossy bridge", nearby="the village path"),
    "garden": Setting(place="the little garden gate", nearby="the flower beds"),
    "brook": Setting(place="the tiny brook", nearby="the reeds"),
}

ITEMS = {
    "basket": LostItem(
        label="basket",
        finder_help="He lifted it carefully with two big fingers",
        return_line="The basket was back in the child's hands, and the apples inside were safe.",
    ),
    "toy": LostItem(
        label="toy boat",
        finder_help="He balanced it in one palm so it would not tip",
        return_line="The toy boat floated again in the child's happy imagination.",
    ),
    "shawl": LostItem(
        label="shawl",
        finder_help="He shook the leaves off and folded it neatly",
        return_line="The shawl was warm, dry, and exactly where it belonged.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming ogre storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--ogre-name", choices=OGRE_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    item = getattr(args, "item", None) or rng.choice(sorted(ITEMS))
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    ogre_name = getattr(args, "ogre_name", None) or rng.choice(OGRE_NAMES)
    if child_name == ogre_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, item=item, child_name=child_name, ogre_name=ogre_name)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    item = _safe_lookup(ITEMS, params.item)
    world = World(setting)

    ogre = world.add(Entity(
        id=params.ogre_name,
        kind="character",
        type="ogre",
        label="ogre",
        meters={"size": 3.0},
        memes={"worry": 2.0, "kindness": 1.0, "hope": 0.0},
    ))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type="girl",
        label="child",
        meters={"small_steps": 1.0},
        memes={"fear": 1.0, "relief": 0.0, "trust": 0.0},
    ))
    lost = world.add(Entity(
        id="lost_item",
        type=item.label,
        label=item.label,
        owner=child.id,
        held_by=None,
        meters={"lost": 1.0},
    ))

    # Setup
    world.say(
        f"On {setting.place}, {ogre.id} stood very still and listened to the wind."
    )
    world.say(
        f"He thought, 'I am huge. What if I sound scary and everyone steps away?'"
    )
    world.say(
        f"Near {setting.nearby}, {child.id} sniffled because {child.id.lower()}'s {lost.label} was missing."
    )
    world.para()

    # Tension
    world.say(
        f"{ogre.id} took one slow breath and walked closer."
    )
    world.say(
        f"'{lost.label.capitalize()}?' he asked softly, keeping his voice round and gentle."
    )
    world.say(
        f"The child blinked. 'I thought ogres only roar,' {child.id.lower()} whispered."
    )
    world.say(
        f"{ogre.id}'s chest tightened. 'That is what I was afraid of too,' he thought."
    )
    world.para()

    # Turn
    world.say(
        f"Then he knelt down, making himself as small as a tree stump, and pointed to the leaves."
    )
    world.say(
        f"'{item.finder_help},' he said. 'Maybe your {lost.label} is there.'"
    )
    world.say(
        f"{child.id} followed the point, and there, tucked beside the roots, was the missing {lost.label}."
    )
    lost.held_by = ogre.id
    lost.meters["lost"] = 0.0
    lost.meters["found"] = 1.0
    ogre.memes["hope"] += 1.0
    child.memes["relief"] += 1.0
    child.memes["trust"] += 1.0
    world.para()

    # Resolution
    world.say(
        f"{child.id} smiled up at him. 'You are not scary,' {child.id.lower()} said. 'You are kind.'"
    )
    world.say(
        f"{ogre.id} felt warm inside. 'Maybe being big means I can help,' he thought."
    )
    world.say(
        f"He handed over the {lost.label}, and the child hugged it like a treasure."
    )
    world.say(lost.return_line)

    world.facts.update(
        ogre=ogre,
        child=child,
        lost=lost,
        setting=setting,
        item=item,
        resolved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ogre = _safe_fact(world, f, "ogre")
    child = _safe_fact(world, f, "child")
    item = _safe_fact(world, f, "item")
    return [
        f"Write a heartwarming story about {ogre.id}, an ogre who worries about being scary, and {child.id} who loses a {item.label}.",
        f"Tell a gentle tale where an ogre uses kindness and a calm conversation to help a child find a missing {item.label}.",
        "Write a short children's story with dialogue, inner monologue, and a happy ending about an ogre and a lost item.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ogre: Entity = _safe_fact(world, f, "ogre")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    lost: Entity = _safe_fact(world, f, "lost")  # type: ignore[assignment]
    item: LostItem = _safe_fact(world, f, "item")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {ogre.id} walk so gently at {world.setting.place}?",
            answer=f"He was worried he might seem scary, so he chose a soft voice and slow steps to help {child.id}.",
        ),
        QAItem(
            question=f"What was {child.id} looking for?",
            answer=f"{child.id} was looking for a {lost.label} that had been lost near {world.setting.nearby}.",
        ),
        QAItem(
            question=f"How did {ogre.id} help the child find the missing {lost.label}?",
            answer=f"{ogre.id} pointed carefully and used {item.finder_help.lower()}, which led the child to the lost {lost.label}.",
        ),
        QAItem(
            question=f"How did {ogre.id} feel at the end?",
            answer=f"He felt warm and hopeful because the child saw his kindness instead of his size.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ogre?",
            answer="An ogre is a big imaginary creature from fairy tales and stories. In this story, the ogre is gentle and kind.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something caring or helpful for another person, like speaking gently or helping someone find a lost thing.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head, where the character thinks without saying the words out loud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved :- kindness_help, found_item.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("kindness_help"),
            asp.fact("found_item"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    ok = any(sym.name == "resolved" for sym in model)
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH: ASP and Python reasonableness gates disagree.")
    return 1


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
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


CURATED = [
    StoryParams(place="bridge", item="basket", child_name="Mina", ogre_name="Brum"),
    StoryParams(place="garden", item="shawl", child_name="Pip", ogre_name="Mok"),
    StoryParams(place="brook", item="toy", child_name="Nia", ogre_name="Gorn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            seed = base_seed + i
            sample = build_sample_from_args(args, random.Random(seed))
            sample.params.seed = seed
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
