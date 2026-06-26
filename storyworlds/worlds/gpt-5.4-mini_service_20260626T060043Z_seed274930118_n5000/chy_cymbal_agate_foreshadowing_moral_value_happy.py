#!/usr/bin/env python3
"""
A small bedtime-story world: Chy, a cymbal, and an agate charm.

The domain centers on a gentle child named Chy who wants to put on a tiny
bedtime music show with a toy cymbal. The agate is a treasured smooth stone
that matters emotionally: Chy keeps it safe, and the story uses that value to
drive the foreshadowing, tension, moral, and happy ending.
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


# ---------------------------------------------------------------------------
# World model
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    broken: bool = False
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    agate: object | None = None
    child: object | None = None
    cymbal: object | None = None
    lamp: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    name: str
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


PLACES = {
    "bedroom": "a cozy bedroom",
    "nursery": "a sleepy nursery",
    "attic": "a little attic room",
}

NAMES = ["Chy", "Mina", "Noa", "Lumi", "Taro", "Ivy"]
TRAITS = ["gentle", "curious", "sleepy", "patient", "soft-spoken"]


@dataclass
class ItemSpec:
    label: str
    phrase: str
    type: str
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


ITEMS = {
    "cymbal": ItemSpec(label="cymbal", phrase="a tiny brass cymbal", type="toy"),
    "agate": ItemSpec(label="agate", phrase="a smooth agate stone", type="stone"),
    "lamp": ItemSpec(label="lamp", phrase="a little lamp with a warm glow", type="lamp"),
}


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _rule_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    cymbal = world.get("cymbal")
    agate = world.get("agate")
    if cymbal.carried_by == child.id and agate.carried_by == child.id and not agate.found:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = child.memes.get("worry", 0) + 1
            out.append("A tiny worry fluttered in Chy's chest, as if something important might slip away.")
    return out


def _rule_drop(world: World) -> list[str]:
    out = []
    child = world.get("child")
    cymbal = world.get("cymbal")
    agate = world.get("agate")
    if child.meters.get("rush", 0) >= 1 and cymbal.carried_by == child.id and agate.carried_by == child.id:
        sig = ("drop",)
        if sig not in world.fired:
            world.fired.add(sig)
            agate.carried_by = None
            agate.found = False
            child.memes["surprise"] = child.memes.get("surprise", 0) + 1
            out.append("With a little rush, the agate slipped from Chy's fingers and rolled under the bed.")
    return out


def _rule_learn(world: World) -> list[str]:
    out = []
    child = world.get("child")
    agate = world.get("agate")
    if not agate.found and (("learn",) not in world.fired):
        if child.memes.get("worry", 0) >= 1:
            world.fired.add(("learn",))
            child.memes["moral"] = child.memes.get("moral", 0) + 1
            out.append("Chy remembered that careful hands keep special things safe.")
    return out


def _rule_happy(world: World) -> list[str]:
    out = []
    child = world.get("child")
    agate = world.get("agate")
    if agate.found and child.memes.get("moral", 0) >= 1 and ("happy",) not in world.fired:
        world.fired.add(("happy",))
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        out.append("Chy's heart grew light again, because the little stone was safe and the bedtime song could begin.")
    return out


RULES = [_rule_worry, _rule_drop, _rule_learn, _rule_happy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(params.place)
    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    cymbal = world.add(Entity(id="cymbal", type="toy", label="cymbal", phrase=ITEMS["cymbal"].phrase, owner="child"))
    agate = world.add(Entity(id="agate", type="stone", label="agate", phrase=ITEMS["agate"].phrase, owner="child", carried_by="child"))
    lamp = world.add(Entity(id="lamp", type="lamp", label="lamp", phrase=ITEMS["lamp"].phrase, owner="child"))
    world.facts.update(child=child, cymbal=cymbal, agate=agate, lamp=lamp)
    return world


def tell(world: World) -> World:
    child = world.get("child")
    cymbal = world.get("cymbal")
    agate = world.get("agate")
    lamp = world.get("lamp")

    world.say(f"{child.label} lived in {world.setting}, where the evenings were soft and quiet.")
    world.say(f"{child.label} loved a tiny cymbal, and {child.pronoun('possessive')} smooth agate stone, too.")
    world.say("Before bedtime, Chy set the agate beside the lamp, as if the stone were waiting to listen.")
    world.say("That small choice was a clue, because the night would soon ask for careful hands.")

    world.para()
    cymbal.carried_by = child.id
    agate.carried_by = child.id
    world.say(f"One night, {child.label} wanted to tap the cymbal and make a gentle song for the room.")
    world.say("But Chy also wanted to carry the agate, because it felt lucky and warm in the palm.")
    child.meters["rush"] = 1
    world.say("The little wish to do everything at once made the child hurry.")
    propagate(world, narrate=True)

    world.para()
    if not agate.found:
        world.say("Then Chy knelt down, looked under the bed, and peered beside the slipper.")
        agate.found = True
        agate.carried_by = child.id
        world.say("There it was, shining softly in the lamp light, as if it had been waiting patiently all along.")
    world.say("Chy took a slower breath, held the stone with two careful fingers, and chose not to rush again.")
    child.meters["rush"] = 0
    propagate(world, narrate=True)

    world.para()
    world.say("At last, Chy tapped the cymbal as softly as a falling feather.")
    world.say("The little note sounded sweet, the agate stayed safe, and the room felt ready for dreams.")
    world.say("The moral was simple: when something matters, gentle care is the best kind of bravery.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a bedtime story about {child.label}, a cymbal, and an agate stone.',
        f"Tell a gentle story where {child.label} wants to play a tiny cymbal but must be careful with an agate.",
        f"Write a short bedtime tale with foreshadowing, a moral, and a happy ending in {world.setting}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        QAItem(
            question=f"What did {child.label} want to do with the cymbal?",
            answer=f"{child.label} wanted to tap the cymbal and make a gentle bedtime song.",
        ),
        QAItem(
            question="Why was the agate important in the story?",
            answer="The agate was a special smooth stone that Chy cared about, so it needed careful hands and a safe place.",
        ),
        QAItem(
            question="What was the moral of the story?",
            answer="The moral was that when something matters, gentle care and patience keep it safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the agate safe, the cymbal softly played, and the room calm for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cymbal?",
            answer="A cymbal is a round metal instrument or toy that makes a bright ringing sound when tapped.",
        ),
        QAItem(
            question="What is an agate?",
            answer="An agate is a kind of stone that can be smooth and pretty, often with soft bands or colors.",
        ),
        QAItem(
            question="Why do bedtime stories often end gently?",
            answer="Bedtime stories often end gently so the child listener feels calm, safe, and ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.found:
            bits.append("found=True")
        if e.broken:
            bits.append("broken=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(chy).
setting(bedroom).
setting(nursery).
setting(attic).

item(cymbal).
item(agate).
item(lamp).

special(cymbal).
special(agate).

foreshadowing(S) :- setting(S), item(agate).
moral_value(agate).
happy_ending(S) :- setting(S), special(cymbal), special(agate).

show_story(S) :- foreshadowing(S), moral_value(agate), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in PLACES:
        lines.append(asp.fact("setting", s))
    for item in ITEMS:
        lines.append(asp.fact("item", item))
    lines.append(asp.fact("child", "chy"))
    lines.append(asp.fact("special", "cymbal"))
    lines.append(asp.fact("special", "agate"))
    lines.append(asp.fact("moral_value", "agate"))
    lines.append(asp.fact("happy_ending", "bedroom"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show show_story/1."))
    asp_set = set(asp.atoms(model, "show_story"))
    py_set = {(p,) for p in valid_places()}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def valid_places() -> list[str]:
    return sorted(PLACES.keys())


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about Chy, a cymbal, and an agate stone.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(valid_places())
    name = getattr(args, "name", None) or "Chy"
    if name != "Chy" and rng.random() < 0.5:
        name = rng.choice(NAMES)
    return StoryParams(place=place, name=name)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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
        print(asp_program("#show show_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show show_story/1."))
        vals = sorted(asp.atoms(model, "show_story"))
        print(vals)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in valid_places():
            params = StoryParams(place=place, name="Chy", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
