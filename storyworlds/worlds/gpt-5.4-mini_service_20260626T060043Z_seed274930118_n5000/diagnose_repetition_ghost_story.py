#!/usr/bin/env python3
"""
Ghost story world: a small haunting with a repetition problem that must be
diagnosed before it can be gently resolved.

Seed premise:
A child keeps hearing the same ghostly message again and again in an old room.
The repeated knocking, whispering, or floating note is not evil; it is a clue.
The child and a helper diagnose what the ghost is trying to say, then fix the
simple problem so the room can rest.

This world models:
- physical state with meters: noise, chill, dust, glow, brokenness, fixed
- emotional state with memes: fear, courage, care, relief, curiosity

The narrative keeps a close, child-facing ghost-story style: dark setting,
repeated eerie signs, a careful diagnosis, and a calm ending image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    helper: object | None = None
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
class Room:
    label: str
    dim: bool = True
    repeats: str = "knock"
    clue: str = "a loose window latch"
    fix: str = "close the latch"
    ghost_name: str = "Moth"
    weather: str = "night"
    room: object | None = None
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
    def __init__(self, room: Room) -> None:
        self.room = room
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
        import copy
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _narrate_repeat(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    if ghost.meters.get("restless", 0.0) < THRESHOLD:
        return out
    sig = ("repeat", world.room.repeats)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["noise"] = ghost.meters.get("noise", 0.0) + 1
    out.append(f"Again and again, the same {world.room.repeats} echoed from the dark hall.")
    return out


def _narrate_diagnose(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    ghost = world.get("ghost")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if child.memes.get("diagnosed", 0.0) >= THRESHOLD:
        return out
    sig = ("diagnose",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["courage"] = child.memes.get("courage", 0.0) + 1
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1)
    out.append(
        f"{child.id} listened closely instead of running away. "
        f"{helper.id} held up a small lamp and helped {child.pronoun('object')} notice the pattern."
    )
    out.append(
        f"The ghost was not angry at all. {ghost.id} was repeating the same sound to point at {world.room.clue}."
    )
    child.memes["diagnosed"] = 1.0
    return out


def _narrate_fix(world: World) -> list[str]:
    out = []
    child = world.get("child")
    helper = world.get("helper")
    ghost = world.get("ghost")
    if child.memes.get("diagnosed", 0.0) < THRESHOLD:
        return out
    if world.facts.get("fixed"):
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["fixed"] = True
    ghost.meters["restless"] = 0.0
    ghost.meters["glow"] = ghost.meters.get("glow", 0.0) + 1
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    out.append(
        f"They {world.room.fix}, and the repeated sound stopped at once."
    )
    out.append(
        f"{ghost.id} gave one soft shimmer, like a candle breathed steady again."
    )
    out.append(
        f"{child.id} smiled, because the strange house had only needed a careful diagnosis."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_narrate_repeat, _narrate_diagnose, _narrate_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    child_name: str
    helper_name: str
    ghost_name: str
    repeat: str
    clue: str
    fix: str
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
    "attic": Room(label="the attic", repeats="knock", clue="a loose window latch", fix="close the latch", ghost_name="Moth"),
    "hall": Room(label="the long hall", repeats="tap", clue="a swinging picture frame", fix="straighten the frame", ghost_name="Pale Lily"),
    "cellar": Room(label="the cellar", repeats="scrape", clue="a dragged broom", fix="hang up the broom", ghost_name="Ash"),
    "nursery": Room(label="the nursery", repeats="whisper", clue="an open music box", fix="wind it down and shut the lid", ghost_name="June"),
}

CHILD_NAMES = ["Mina", "Owen", "Ruby", "Eli", "Nora", "Theo"]
HELPER_NAMES = ["Grandma", "Grandpa", "Auntie", "Uncle", "Mom", "Dad"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a repetition mystery to diagnose.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--ghost-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    room = _safe_lookup(SETTINGS, setting)
    return StoryParams(
        setting=setting,
        child_name=getattr(args, "child_name", None) or rng.choice(CHILD_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        ghost_name=getattr(args, "ghost_name", None) or room.ghost_name,
        repeat=room.repeats,
        clue=room.clue,
        fix=room.fix,
    )


def tell(params: StoryParams) -> World:
    room = _safe_lookup(SETTINGS, params.setting)
    room = Room(label=room.label, dim=room.dim, repeats=params.repeat, clue=params.clue, fix=params.fix, ghost_name=params.ghost_name)
    world = World(room)

    child = world.add(Entity(id=params.child_name, kind="character", type="girl" if params.child_name in {"Mina", "Ruby", "Nora"} else "boy"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="mother" if params.helper_name == "Mom" else "father" if params.helper_name == "Dad" else "woman"))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label=params.ghost_name))
    ghost.meters["restless"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["curiosity"] = 1.0

    world.say(f"It was late in {room.label}, and the air felt cool and still.")
    world.say(f"{child.id} heard a {room.repeats} from the dark, then heard it again, just the same.")
    world.para()
    world.say(f"{child.id} wanted to run, but {helper.id} lifted a lamp and said to listen first.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"Together, they found {room.clue} and fixed it.")
    propagate(world, narrate=True)
    world.facts.update(child=child, helper=helper, ghost=ghost, room=room, fixed=True)
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room = _safe_fact(world, f, "room")
    return [
        f"Write a small ghost story for a child where the same {room.repeats} keeps repeating until the hidden clue is diagnosed.",
        f"Tell a gentle haunted-house story in {room.label} where a child notices a repeating sound and solves it with a helper.",
        f"Write a story with a repetition mystery, a careful diagnosis, and a calm ending in {room.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    room = _safe_fact(world, f, "room")
    ghost = _safe_fact(world, f, "ghost")
    return [
        QAItem(
            question=f"What kept happening again and again in {room.label}?",
            answer=f"The same {room.repeats} kept repeating from the dark, which made the room feel spooky at first.",
        ),
        QAItem(
            question=f"How did {child.id} help diagnose the problem?",
            answer=f"{child.id} listened closely instead of fleeing, then noticed that the repeated sound was pointing to {room.clue}.",
        ),
        QAItem(
            question=f"What did {helper.id} do when the strange sound would not stop?",
            answer=f"{helper.id} held up a lamp, stayed calm, and helped {child.id} look for the clue hidden in {room.label}.",
        ),
        QAItem(
            question=f"Why was {ghost.id} repeating the sound?",
            answer=f"{ghost.id} was not trying to frighten anyone; the repetition was a clue that something needed to be fixed.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"After they fixed the clue, the repeating sound stopped, and the ghost's restless feeling turned into a soft, gentle glow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does diagnose mean?",
            answer="To diagnose something means to figure out what is causing a problem by looking carefully and thinking about the clues.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens again and again in the same way, like a knock, a whisper, or a song that keeps returning.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky even when nothing bad happens?",
            answer="A ghost story can feel spooky because of dark rooms, strange sounds, and things that repeat before the reason is understood.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  room: {world.room.label}, repeats={world.room.repeats}, clue={world.room.clue}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", child_name="Mina", helper_name="Grandma", ghost_name="Moth", repeat="knock", clue="a loose window latch", fix="close the latch"),
    StoryParams(setting="hall", child_name="Owen", helper_name="Dad", ghost_name="Pale Lily", repeat="tap", clue="a swinging picture frame", fix="straighten the frame"),
    StoryParams(setting="cellar", child_name="Ruby", helper_name="Auntie", ghost_name="Ash", repeat="scrape", clue="a dragged broom", fix="hang up the broom"),
    StoryParams(setting="nursery", child_name="Theo", helper_name="Mom", ghost_name="June", repeat="whisper", clue="an open music box", fix="wind it down and shut the lid"),
]


ASP_RULES = r"""
repeats(R) :- room_repeat(R).
diagnosed :- observes_pattern, clue_found.
fixed :- diagnosed, repair_done.
ghost_restless :- repeats(_), not fixed.
#show repeats/1.
#show diagnosed/0.
#show fixed/0.
#show ghost_restless/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, room in SETTINGS.items():
        lines.append(asp.fact("room", key))
        lines.append(asp.fact("room_repeat", room.repeats))
        lines.append(asp.fact("room_clue", room.clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repeats/1.\n#show diagnosed/0.\n#show fixed/0.\n#show ghost_restless/0."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    if ("repeats", 1) in atoms:
        print("OK: ASP rules compiled and produced repetition facts.")
        return 0
    print("MISMATCH: ASP did not produce expected facts.")
    return 1


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
        print(asp_program("#show repeats/1.\n#show diagnosed/0.\n#show fixed/0.\n#show ghost_restless/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
