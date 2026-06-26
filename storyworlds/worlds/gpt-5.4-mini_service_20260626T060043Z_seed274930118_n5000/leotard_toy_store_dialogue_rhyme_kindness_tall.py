#!/usr/bin/env python3
"""
Toy-store tall tale world: a child, a leotard, a little trouble, and a kind fix.

This world is built as a tiny simulation with physical meters and emotional
memes. The story is state-driven: the child wants the leotard, the toy store
creates a snag, dialogue turns the trouble, and kindness resolves it.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    display: object | None = None
    helper: object | None = None
    leotard: object | None = None
    def __post_init__(self):
        for k in ("sparkle", "tangle", "dust", "tidy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "kindness", "pride", "embarrassment", "peace"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the toy store"
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
class StoryParams:
    name: str
    gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def _r_tangle(world: World) -> list[str]:
    out = []
    leotard = world.entities.get("leotard")
    child = world.entities.get("child")
    display = world.entities.get("display")
    if not leotard or not child or not display:
        return out
    if child.memes["excitement"] >= THRESHOLD and display.meters["crowd"] >= THRESHOLD:
        if leotard.worn_by == "child" and leotard.meters["tangle"] < THRESHOLD:
            leotard.meters["tangle"] += 1
            child.memes["embarrassment"] += 1
            out.append("The leotard snagged on a shiny hook, and the child blushed as bright as a red balloon.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    child = world.entities["child"]
    helper = world.entities["helper"]
    leotard = world.entities["leotard"]
    if helper.memes["kindness"] >= THRESHOLD and leotard.meters["tangle"] >= THRESHOLD:
        if ("kindness_fix",) not in getattr(world, "_fired", set()):
            world._fired = getattr(world, "_fired", set())
            world._fired.add(("kindness_fix",))
            leotard.meters["tangle"] = 0
            leotard.meters["sparkle"] += 1
            child.memes["peace"] += 1
            child.memes["joy"] += 1
            helper.memes["pride"] += 1
            out.append("The helper unhooked the leotard with careful fingers, and the shine came back like moonlight on a merry river.")
    return out


def propagate(world: World) -> list[str]:
    out: list[str] = []
    for _ in range(3):
        produced = []
        produced.extend(_r_tangle(world))
        produced.extend(_r_kindness(world))
        if not produced:
            break
        out.extend(produced)
    for s in out:
        world.say(s)
    return out


def introduce(world: World, child: Entity, helper: Entity, leotard: Entity) -> None:
    world.say(
        f"In the biggest little toy store in town, {child.id} was a {child.type} with a grand grin and a heart full of hop."
    )
    world.say(
        f"{child.pronoun().capitalize()} had spotted a glittery leotard in the dress-up aisle, and {child.pronoun('possessive')} eyes shone like twin lanterns."
    )
    world.say(
        f"The storekeeper, {helper.id}, had a voice like a bell and a smile like a warm pie crust."
    )
    world.say(
        f'"A leotard for a star?" {helper.id} asked. "Why, that is fine, but mind the toys and keep the day kind."'
    )


def desire(world: World, child: Entity, leotard: Entity) -> None:
    child.memes["excitement"] += 1
    child.memes["joy"] += 1
    leotard.worn_by = "child"
    leotard.meters["sparkle"] += 1
    world.say(
        f'{child.id} slipped on the leotard and declared, "I feel tall as a tower, bright as a firefly shower!"'
    )


def trouble(world: World, child: Entity, helper: Entity, leotard: Entity) -> None:
    world.say(
        f"Then {child.id} hurried past a parade of plush giraffes, and the leotard brushed a hanging hook with a tiny zip-zap."
    )
    world.entities["display"].meters["crowd"] += 1
    world.entities["display"].meters["dust"] += 1
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    propagate(world)


def dialogue_and_turn(world: World, child: Entity, helper: Entity, leotard: Entity) -> None:
    world.say(
        f'"Oops!" said {child.id}. "I did not mean to make a snag of this rag."'
    )
    world.say(
        f'"No thunder here," said {helper.id}. "We can fix a snag with a gentle drag."'
    )
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} knelt beside the child and added, "A kindly hand can mend a strand."'
    )
    propagate(world)


def resolution(world: World, child: Entity, helper: Entity, leotard: Entity) -> None:
    world.say(
        f'Together they brushed the dust from the display, straightened the little stage, and made the aisle as neat as new snow.'
    )
    world.say(
        f'{child.id} placed the leotard back on the velvet hook for the next child to see, then shared a bow with {helper.id}.'
    )
    world.say(
        f'"A borrowed thing is best when it is returned with care," said {helper.id}, "and a kind deed is a treasure that never wears thin."'
    )
    world.say(
        f'{child.id} nodded. "I came for a sparkle," {child.id} said, "and I found a friend besides."'
    )
    child.memes["peace"] += 1
    child.memes["pride"] += 1
    helper.memes["pride"] += 1


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label="the storekeeper"))
    leotard = world.add(Entity(id="leotard", type="leotard", label="leotard", phrase="a glittery leotard", owner=child.id))
    display = world.add(Entity(id="display", type="display", label="display table"))
    display.meters["crowd"] = 0.0

    world.facts.update(child=child, helper=helper, leotard=leotard)
    introduce(world, child, helper, leotard)
    world.para()
    desire(world, child, leotard)
    trouble(world, child, helper, leotard)
    world.para()
    dialogue_and_turn(world, child, helper, leotard)
    resolution(world, child, helper, leotard)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a short tall tale for a child named {child.label} in a toy store, with dialogue, rhyme, and kindness, using the word "leotard".',
        f"Tell a big-hearted story about {child.label} wanting a leotard at the toy store, then finding a kind fix after a small snag.",
        'Write a playful toy-store story where a leotard, a rhyme, and a kind helper turn trouble into a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    leotard = _safe_fact(world, f, "leotard")
    return [
        QAItem(
            question=f"What did {child.label} want at the toy store?",
            answer=f"{child.label} wanted the glittery leotard because it made {child.pronoun('object')} feel grand and star-bright."
        ),
        QAItem(
            question=f"Who helped when the leotard snagged?",
            answer=f"{helper.label} the storekeeper helped with careful fingers and a gentle voice."
        ),
        QAItem(
            question="How did the story turn out?",
            answer=f"The snag was fixed, the aisle was tidied, and the leotard went back shining for the next child."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toy store?",
            answer="A toy store is a shop filled with toys, dress-up things, games, and other fun things for children."
        ),
        QAItem(
            question="What is a leotard?",
            answer="A leotard is a snug piece of clothing often used for dance, gymnastics, or dress-up play."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to someone else."
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme means words that sound alike at the end, like time and rhyme or star and far."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
story_kind(child).
story_kind(helper).
story_kind(leotard).

snagged(L) :- leotard(L), worn(L), brush_hook(L).
kind_fix(H, L) :- helper(H), snagged(L), kind(H).
happy_end :- kind_fix(_, _), not snagged(leotard).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("story_kind", "child"),
        asp.fact("story_kind", "helper"),
        asp.fact("story_kind", "leotard"),
        asp.fact("worn", "leotard"),
        asp.fact("brush_hook", "leotard"),
        asp.fact("kind", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show happy_end/0."))
    ok = any(sym.name == "happy_end" for sym in model)
    if ok:
        print("OK: ASP gate recognizes the kind resolution.")
        return 0
    print("MISMATCH: ASP gate failed to derive the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy-store tall tale world with leotard, dialogue, rhyme, and kindness.")
    ap.add_argument("--name", default="Pip")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--helper-name", default="Mabel")
    ap.add_argument("--helper-gender", choices=["girl", "boy"], default="girl")
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
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(["Pip", "Milo", "June", "Lena", "Toby"]),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        helper_name=getattr(args, "helper_name", None) or rng.choice(["Mabel", "Otis", "Nora", "Bennie"]),
        helper_gender=getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"]),
        seed=getattr(args, "seed", None),
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
        print(asp_program("#show happy_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show happy_end/0."))
        print("happy_end" if any(sym.name == "happy_end" for sym in model) else "no model")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        params = resolve_params(args, random.Random(base_seed))
        samples = [generate(params)]
    else:
        for i in range(max(1, getattr(args, "n", None))):
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
