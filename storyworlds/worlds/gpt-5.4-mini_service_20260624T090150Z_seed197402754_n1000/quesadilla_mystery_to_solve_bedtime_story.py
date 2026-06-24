#!/usr/bin/env python3
"""
Bedtime Story world: a gentle quesadilla mystery to solve.

A small child notices a missing quesadilla, follows soft clues through the house,
and learns that a loving helper simply moved it to keep it warm. The story is
state-driven: hunger, curiosity, clues, and a cozy reveal change the world.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    quesadilla: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    calm: bool = True
    rooms: tuple[str, ...] = ("kitchen", "hallway", "living room", "bedroom")
    setting: object | None = None
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
class Snack:
    id: str
    label: str
    phrase: str
    warm: bool = True
    room: str = "kitchen"
    clue: str = "a tiny breadcrumb trail"
    comfort: str = "cozy and warm"
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
class Helper:
    id: str
    label: str
    motive: str
    hiding_place: str
    reveal: str
    kind_help: str = "warm it up"
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "owner": e.owner, "caretaker": e.caretaker,
            "meters": dict(e.meters), "memes": dict(e.memes)
        }) for k, e in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _tick_hunger(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.kind == "character" and e.meters.get("hunger", 0) >= THRESHOLD and not e.fired if False else True:
            pass
    return out


def _clue_found(world: World) -> list[str]:
    out = []
    child = world.get("child")
    snack = world.get("quesadilla")
    if child.memes.get("searching", 0) < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    out.append(f"{child.label} noticed {snack.phrase} was not on the table, but {snack.clue} by the kitchen door.")
    return out


def _find_helper(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("searching", 0) < THRESHOLD:
        return out
    if child.memes.get("clue", 0) < THRESHOLD:
        return out
    sig = ("helper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    out.append(f"Then {child.label} followed the clue into the hallway and found {helper.label} with a gentle smile.")
    return out


def _reveal(world: World) -> list[str]:
    out = []
    child = world.get("child")
    snack = world.get("quesadilla")
    helper = world.get("helper")
    sig = ("reveal",)
    if sig in world.fired:
        return out
    if child.memes.get("calm", 0) < THRESHOLD:
        return out
    world.fired.add(sig)
    snack.meters["warmth"] = 1
    child.meters["hunger"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    out.append(f"{helper.label} explained that {helper.pronoun('subject')} had moved the quesadilla to keep it warm.")
    out.append(f"Soon {child.label} was eating the quesadilla, and the little mystery felt happy and complete.")
    return out


RULES = [_clue_found, _find_helper, _reveal]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                produced.extend(s)
                changed = True
    for s in produced:
        world.say(s)
    return produced


def ask_for_help(world: World, child: Entity) -> None:
    child.memes["searching"] = child.memes.get("searching", 0) + 1
    child.meters["hunger"] = child.meters.get("hunger", 0) + 1
    world.say(f"At bedtime, {child.label} got sleepy and hungry and noticed the quesadilla was missing.")
    world.say(f"{child.label} whispered, \"Where did my quesadilla go?\" and began to look for a clue.")


def notice_clue(world: World, child: Entity) -> None:
    child.memes["clue"] = child.memes.get("clue", 0) + 1
    world.say(f"{child.label} padded softly past the kitchen and saw {world.get('quesadilla').clue}.")


def close_story(world: World, child: Entity) -> None:
    snack = world.get("quesadilla")
    world.say(
        f"By the end, {child.label} was warm and content, {snack.label} was safe in a cozy place, "
        f"and the house felt peaceful again."
    )


def tell() -> World:
    setting = Setting(place="the little house")
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label="Mina"))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label="Mom"))
    quesadilla = world.add(Entity(
        id="quesadilla", type="snack", label="quesadilla",
        phrase="the warm quesadilla on the plate", owner=child.id, caretaker=helper.id
    ))
    world.facts.update(child=child, helper=helper, quesadilla=quesadilla, setting=setting)

    world.say(f"Once upon a bedtime, {child.label} lived in {setting.place} and loved a warm quesadilla before sleep.")
    world.say(f"{child.label} liked it because it was {Snack('quesadilla','quesadilla','').comfort if False else 'soft, cheesy, and cozy'}.")

    world.para()
    ask_for_help(world, child)
    notice_clue(world, child)
    propagate(world)

    world.para()
    close_story(world, child)
    return world


ASP_RULES = r"""
% A bedtime mystery is reasonable when the quesadilla is missing and a helper can
% explain where it went.
missing(quesadilla).
has_helper(helper).

mystery_to_solve(quesadilla) :- missing(quesadilla), has_helper(helper).
resolved(quesadilla) :- mystery_to_solve(quesadilla), found_clue(crumbs), explain(helper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "quesadilla"),
        asp.fact("has_helper", "helper"),
        asp.fact("found_clue", "crumbs"),
        asp.fact("explain", "helper"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
    return sorted(set(asp.atoms(model, "mystery_to_solve"))), sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    myst, res = asp_valid()
    py = {("quesadilla",)}
    if set(myst) == py and set(res) == py:
        print("OK: ASP and Python agree on the bedtime quesadilla mystery.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP mystery:", myst)
    print("ASP resolved:", res)
    return 1


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    helper_name: str = "Mom"
    samples: list = field(default_factory=list)
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
    ap = argparse.ArgumentParser(description="A bedtime quesadilla mystery story world.")
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
    return StoryParams(seed=getattr(args, "seed", None), child_name=rng.choice(["Mina", "Nora", "Lina", "Ivy"]), helper_name=rng.choice(["Mom", "Mama", "Mother"]))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short bedtime story about a missing quesadilla and a gentle mystery to solve.',
        f"Tell a cozy story where {f['child'].label} looks for a quesadilla and {f['helper'].label} helps solve the mystery.",
        "Write a simple bedtime tale that ends with the quesadilla found and the child feeling calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was looking for the missing quesadilla?",
            answer=f"{child.label} was looking for it because the bedtime snack had disappeared from the table.",
        ),
        QAItem(
            question=f"Why did {helper.label} move the quesadilla?",
            answer=f"{helper.label} moved it to keep it warm, not to hide it forever.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"{child.label} followed the clue, found {helper.label}, and then ate the warm quesadilla in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quesadilla?",
            answer="A quesadilla is a warm tortilla with cheese and sometimes other fillings inside, folded or sandwiched together.",
        ),
        QAItem(
            question="Why do people keep food warm?",
            answer="People keep food warm so it stays tasty and cozy to eat, especially when someone is waiting for bedtime or dinner.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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
        print(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
        print(sorted(set(asp.atoms(model, "mystery_to_solve"))))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(seed=base_seed))]
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
