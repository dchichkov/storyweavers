#!/usr/bin/env python3
"""
A small heartwarming story world about a child learning a social norm by
listening to an inner monologue and choosing a kind, reasonable action.

Seed tale sketch:
- A child wants something important right away.
- The child notices a norm: waiting, sharing, or asking before taking.
- Their inner monologue helps them understand another person's feelings.
- They choose the kinder move, and the ending shows a warmer relationship.

The world tracks both physical state ("meters") and emotional state ("memes").
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "person": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, mapping["person"])[case]
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
    place: str
    norm: str
    situation: str
    object_name: str
    object_label: str
    helper_label: str
    emotional_need: str
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
    trace: list[str] = field(default_factory=list)

    w: object | None = None
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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
    child_type: str
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


SETTINGS = {
    "library_line": Setting(
        place="the library",
        norm="wait your turn",
        situation="a long line for the picture book",
        object_name="book",
        object_label="the bright picture book",
        helper_label="the librarian",
        emotional_need="be patient",
    ),
    "cookie_table": Setting(
        place="the kitchen table",
        norm="ask before taking",
        situation="a plate of warm cookies",
        object_name="cookie",
        object_label="the last warm cookie",
        helper_label="mom",
        emotional_need="be considerate",
    ),
    "block_corner": Setting(
        place="the playroom",
        norm="share the toy",
        situation="a tower of blue blocks",
        object_name="block",
        object_label="the shiny blue block",
        helper_label="a friend",
        emotional_need="be fair",
    ),
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Ben", "Luna", "Owen"]
HELPER_NAMES = ["Ms. Green", "Mom", "Dad", "Ava", "Noah", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming norm story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy", "person"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "person"])
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
    s = _safe_lookup(SETTINGS, setting)
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or "person"
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_name = getattr(args, "helper_name", None) or s.helper_label
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _inner_monologue(child: Entity, setting: Setting) -> str:
    if setting.norm == "wait your turn":
        return (
            f"{child.pronoun().capitalize()} took a slow breath. "
            f'"If I wait, everyone gets a turn," {child.pronoun()} thought. '
            f'"I can be patient."'
        )
    if setting.norm == "ask before taking":
        return (
            f"{child.pronoun().capitalize()} looked at {setting.object_label} and thought, "
            f'"It is nicer to ask first. I would want someone to ask me."'
        )
    return (
        f"{child.pronoun().capitalize()} hugged {child.pronoun('possessive')} arms and thought, "
        f'"Sharing can keep the fun going for both of us."'
    )


def _predict_outcome(world: World) -> bool:
    child = world.get("child")
    helper = world.get("helper")
    setting = world.setting
    want = child.memes.get("want", 0) >= 1
    if setting.norm == "wait your turn":
        return want and helper.memes.get("waiting", 0) < 1
    if setting.norm == "ask before taking":
        return want and helper.memes.get("asked", 0) < 1
    return want and helper.memes.get("sharing", 0) < 1


def _resolve_turn(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    setting = world.setting
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["warmth"] = child.memes.get("warmth", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    child.memes["frustration"] = 0
    if setting.norm == "wait your turn":
        helper.memes["waiting"] = 1
        world.say(
            f'{child.pronoun().capitalize()} decided to wait. '
            f"The line moved one small step, and then another."
        )
        world.say(
            f"When it was finally {child.pronoun('possessive')} turn, "
            f"{setting.helper_label} smiled and handed over {setting.object_label}."
        )
    elif setting.norm == "ask before taking":
        helper.memes["asked"] = 1
        world.say(
            f"{child.pronoun().capitalize()} asked first with a tiny voice. "
            f"{setting.helper_label} nodded and broke the cookie in two."
        )
        world.say(
            f"They shared the warm cookie, and the sweet smell made the table feel gentle."
        )
    else:
        helper.memes["sharing"] = 1
        world.say(
            f"{child.pronoun().capitalize()} slid {setting.object_label} across the floor. "
            f"{setting.helper_label} smiled and offered the next turn."
        )
        world.say(
            f"Soon the two children were building together, and the tower stood taller than before."
        )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    child = world.add(Entity(id="child", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", type=params.helper_type, label=params.helper_name))

    child.memes["want"] = 1
    child.memes["curious"] = 1
    helper.memes["care"] = 1

    world.say(
        f"{child.label} was a little {child.type} who came to {setting.place} "
        f"and noticed {setting.situation}."
    )
    world.say(
        f"{child.pronoun().capitalize()} really wanted {setting.object_label}, "
        f"but {setting.helper_label} held it safely for now."
    )

    world.para()
    world.say(
        f"As {child.label} stood there, {child.pronoun('possessive')} thoughts grew loud."
    )
    world.say(_inner_monologue(child, setting))
    world.say(
        f"That was {setting.norm}, and {child.label} knew it would be kind to follow it."
    )

    world.para()
    if _predict_outcome(world):
        _resolve_turn(world)
    else:
        pass

    world.para()
    world.say(
        f"At the end, {child.label} felt proud, and {setting.helper_label} looked happy too."
    )
    world.say(
        f"The {setting.place} felt warmer with that small, careful choice."
    )

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = _safe_fact(world, f, "setting")
    child: Entity = _safe_fact(world, f, "child")
    return [
        f"Write a heartwarming story about {child.label} learning to {s.norm} at {s.place}.",
        f"Tell a gentle story where {child.label} thinks carefully, listens to an inner monologue, "
        f"and does the kind thing near {s.object_label}.",
        f"Write a short child-friendly story about a social norm and a warm ending at {s.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Setting = _safe_fact(world, f, "setting")
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What norm did {child.label} learn at {s.place}?",
            answer=f"{child.label} learned to {s.norm}.",
        ),
        QAItem(
            question=f"What helped {child.label} choose the kind action?",
            answer=(
                f"{child.label}'s inner monologue helped {child.pronoun()} think about how "
                f"someone else might feel, so {child.pronoun()} chose the kind action."
            ),
        ),
        QAItem(
            question=f"Who was with {child.label} in the story?",
            answer=f"{helper.label} was with {child.label}, and they helped make the choice gentle and warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    s = world.setting
    return [
        QAItem(
            question="What is a norm?",
            answer="A norm is a usual rule or expected way to behave that helps people get along.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside your head that helps you think through a choice.",
        ),
        QAItem(
            question="Why do people share or wait their turn?",
            answer="People share or wait their turn so everyone can feel respected and included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
norm_followed(C) :- child(C), inner_monologue(C), kind_choice(C).
warm_ending(C) :- norm_followed(C), helper(H), cares(H).
compatible_story(S) :- setting(S), norm(SN), child(C), helper(H), warm_ending(C).
#show compatible_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("norm", setting.norm.replace(" ", "_")))
        lines.append(asp.fact("place", sid, setting.place))
        lines.append(asp.fact("situation", sid, setting.situation))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("inner_monologue", "child"))
    lines.append(asp.fact("cares", "helper"))
    lines.append(asp.fact("kind_choice", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    ok = True
    if not model:
        ok = False
    if ok:
        print("OK: ASP gate is satisfiable.")
        return 0
    print("MISMATCH: ASP gate is not satisfiable.")
    return 1


def resolve_samples(args: argparse.Namespace, base_seed: int) -> list[StoryParams]:
    rng = random.Random(base_seed)
    if getattr(args, "all", None):
        return [
            StoryParams(setting=s, child_name="Maya", child_type="girl", helper_name="Mom", helper_type="person")
            for s in SETTINGS
        ]
    return [resolve_params(args, random.Random(base_seed + i)) for i in range(getattr(args, "n", None))]


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible_story/1."))
        print(model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    params_list = resolve_samples(args, base_seed)

    samples: list[StorySample] = []
    for i, params in enumerate(params_list):
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
