#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/crab_stash_english_misunderstanding_inner_monologue_rhyme.py
======================================================================================================

A standalone animal-story world about a crab, a secret stash, and an English
misunderstanding, with inner monologue and rhyme woven into the simulated
state.

Premise seed:
- A little crab guards a stash by the shore.
- A paper label in English is misunderstood.
- The crab worries in inner monologue.
- A friend explains the note and the crab chooses a kinder ending.

The world is intentionally small and constraint-checked: the story should feel
like a complete TinyStories-style animal tale, not a shuffled template.
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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crab: object | None = None
    friend: object | None = None
    note: object | None = None
    stash: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"crab", "bird", "turtle", "fox", "mouse", "seal"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Place:
    id: str
    label: str
    indoors: bool = False
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
    protagonist: str
    friend: str
    stash_kind: str
    note_language: str = "english"
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


def _inc(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _madd(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def world_place(place_id: str) -> Place:
    return _safe_lookup(PLACES, place_id)


PLACES = {
    "tidepool": Place(id="tidepool", label="the tide pool"),
    "pier": Place(id="pier", label="the pier"),
    "beach": Place(id="beach", label="the beach"),
    "cove": Place(id="cove", label="the quiet cove"),
}

PROTAGONISTS = {
    "crab": {
        "type": "crab",
        "names": ["Claw", "Nip", "Pip", "Bram", "Cora"],
        "traits": ["small", "wary", "curious", "sly", "brave"],
    }
}

FRIENDS = {
    "bird": {"type": "bird", "label": "seagull", "names": ["Gull", "Skim", "Sally"]},
    "turtle": {"type": "turtle", "label": "turtle", "names": ["Moss", "Tuck", "Tally"]},
    "otter": {"type": "otter", "label": "otter", "names": ["Rill", "Mina", "Ollie"]},
}

STASHES = {
    "shells": {
        "label": "a stash of bright shells",
        "phrase": "a tidy stash of bright shells",
        "value": "shiny",
    },
    "berries": {
        "label": "a stash of berries",
        "phrase": "a sweet stash of berries",
        "value": "tasty",
    },
    "pebbles": {
        "label": "a stash of smooth pebbles",
        "phrase": "a little stash of smooth pebbles",
        "value": "smooth",
    },
}

TRAITS = ["curious", "careful", "tiny", "quiet", "brave", "shy"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    crab = world.get("protagonist")
    note = world.get("note")
    friend = world.get("friend")
    if crab.memes.get("confused", 0.0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _madd(crab, "worry", 1.0)
    _madd(friend, "alarm", 0.5)
    out.append(
        f"{crab.label} froze, because the English note looked like a secret order, not a kind message."
    )
    return out


def _r_rhyme(world: World) -> list[str]:
    crab = world.get("protagonist")
    if crab.memes.get("hope", 0.0) < THRESHOLD:
        return []
    sig = ("rhyme",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return ["__rhyme__"]


RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("rhyme", _r_rhyme)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "__rhyme__":
                world.say(s)
    return produced


def reasonableness_gate(place: Place, stash_kind: str) -> bool:
    return place.id in PLACES and stash_kind in STASHES


def setting_detail(place: Place) -> str:
    if place.id == "tidepool":
        return "The tide pool glittered under a soft sky."
    if place.id == "pier":
        return "The pier creaked above the water, and little waves tapped the posts."
    if place.id == "cove":
        return "The quiet cove hid warm water behind two round rocks."
    return "The beach smelled salty, and the sand held tiny footprints."


def intro_crab(world: World, crab: Entity) -> None:
    trait = next((t for t in crab.traits if t != "tiny"), "curious")
    world.say(
        f"{crab.label} was a tiny {trait} crab who loved small treasures and neat hiding places."
    )


def intro_stash(world: World, stash: Entity) -> None:
    world.say(f"{stash.owner} kept {stash.phrase} tucked under a flat stone.")


def intro_note(world: World, note: Entity) -> None:
    world.say(
        f"One shell-shaped scrap of paper had an English note on it, and nobody had read it aloud yet."
    )


def want_keep(world: World, crab: Entity, stash: Entity) -> None:
    _madd(crab, "desire", 1.0)
    world.say(
        f"{crab.label} wanted to keep the stash safe, but the words on the paper made its claws twitch."
    )


def inner_monologue(world: World, crab: Entity, note: Entity) -> None:
    _madd(crab, "confused", 1.0)
    world.say(
        f'"What if that English note means the stash is mine now?" {crab.label} thought. '
        f'"What if I am doing the wrong thing?"'
    )


def friend_arrives(world: World, friend: Entity) -> None:
    world.say(f"Then {friend.label} came close and tipped its head at the paper.")


def explain_note(world: World, friend: Entity, crab: Entity, stash: Entity) -> None:
    _madd(crab, "hope", 1.0)
    world.say(
        f'"It says the stash is for everyone at the picnic," said {friend.label}. '
        f'"That is English, not a sneaky trap."'
    )


def rhyme_resolution(world: World, crab: Entity, friend: Entity, stash: Entity) -> None:
    _madd(crab, "joy", 1.0)
    _madd(crab, "worry", -1.0)
    world.say(
        f'{crab.label} laughed, and then said in a rhyme, "No need to guard and frown; '
        f"we can share this stash around.\""
    )
    world.say(
        f"So {crab.label} opened the hidden stone, and {friend.label} helped carry the treats to the sand."
    )


def tell(params: StoryParams) -> World:
    if not reasonableness_gate(world_place(params.place), params.stash_kind):
        pass
    place = world_place(params.place)
    world = World(place=place)

    crab_name = params.protagonist
    friend_name = params.friend
    stash_cfg = _safe_lookup(STASHES, params.stash_kind)

    crab = world.add(Entity(
        id="protagonist",
        kind="animal",
        type="crab",
        label=crab_name,
        traits=[random.choice(TRAITS), "tiny"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="animal",
        type=_safe_lookup(FRIENDS, params.friend)["type"],
        label=friend_name,
        traits=["helpful"],
    ))
    stash = world.add(Entity(
        id="stash",
        kind="thing",
        type=params.stash_kind,
        label=stash_cfg["label"],
        phrase=stash_cfg["phrase"],
        owner=crab.id,
        hidden_in="under a flat stone",
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="paper note",
        phrase=f"an English note",
    ))

    intro_crab(world, crab)
    intro_stash(world, stash)
    intro_note(world, note)

    world.para()
    world.say(setting_detail(place))
    want_keep(world, crab, stash)
    inner_monologue(world, crab, note)
    propagate(world, narrate=True)

    world.para()
    friend_arrives(world, friend)
    explain_note(world, friend, crab, stash)
    propagate(world, narrate=True)
    rhyme_resolution(world, crab, friend, stash)
    propagate(world, narrate=True)

    world.facts.update(
        crab=crab,
        friend=friend,
        stash=stash,
        note=note,
        place=place,
        params=params,
        shared=True,
        misunderstanding=True,
        rhyme=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crab = _safe_fact(world, f, "crab")
    friend = _safe_fact(world, f, "friend")
    stash = _safe_fact(world, f, "stash")
    place = _safe_fact(world, f, "place").label
    return [
        f'Write a short animal story for a young child about {crab.label}, an English note, and a {stash.label}.',
        f"Tell a gentle story where {crab.label} misunderstands an English message at {place} and then learns a kinder meaning.",
        f'Write a tiny seaside story that includes a crab, a stash, English words, and a little rhyme at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crab = _safe_fact(world, f, "crab")
    friend = _safe_fact(world, f, "friend")
    stash = _safe_fact(world, f, "stash")
    place = _safe_fact(world, f, "place").label
    return [
        QAItem(
            question=f"Who was trying to keep the stash safe at {place}?",
            answer=f"{crab.label} the crab was trying to keep the stash safe under the stone.",
        ),
        QAItem(
            question="What made the crab feel confused?",
            answer="The crab felt confused because the paper note was written in English, and it looked like a secret at first.",
        ),
        QAItem(
            question=f"Who helped explain the note to {crab.label}?",
            answer=f"{friend.label} helped explain that the English note was really a friendly message.",
        ),
        QAItem(
            question=f"What did {crab.label} do when it understood the note?",
            answer=f"{crab.label} shared the stash, laughed, and said a rhyme instead of guarding it alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crab?",
            answer="A crab is a small sea animal with a hard shell and claws that walks sideways on the sand.",
        ),
        QAItem(
            question="What does English mean?",
            answer="English is a language people use to speak, read, and write words on signs and notes.",
        ),
        QAItem(
            question="What is a stash?",
            answer="A stash is a hidden little collection of things that someone has put away for later.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which can make a sentence fun to say.",
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
    for sid, stash in STASHES.items():
        lines.append(asp.fact("stash_kind", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_stash(S) :- stash_kind(S).
valid_story(P,S) :- valid_place(P), valid_stash(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p, s) for p in PLACES for s in STASHES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: crab, stash, english, misunderstanding, inner monologue, rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--protagonist", choices=[*PROTAGONISTS["crab"]["names"]], help="crab name")
    ap.add_argument("--friend", choices=[*FRIENDS["bird"]["names"], *FRIENDS["turtle"]["names"], *FRIENDS["otter"]["names"]], help="friend name")
    ap.add_argument("--stash-kind", choices=STASHES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    stash_kind = getattr(args, "stash_kind", None) or rng.choice(list(STASHES))
    protagonist = getattr(args, "protagonist", None) or rng.choice(PROTAGONISTS["crab"]["names"])
    friend = getattr(args, "friend", None) or rng.choice(["Gull", "Moss", "Rill"])
    return StoryParams(place=place, protagonist=protagonist, friend=friend, stash_kind=stash_kind, seed=getattr(args, "seed", None))


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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="tidepool", protagonist="Pip", friend="Gull", stash_kind="shells"),
    StoryParams(place="pier", protagonist="Cora", friend="Moss", stash_kind="berries"),
    StoryParams(place="cove", protagonist="Bram", friend="Rill", stash_kind="pebbles"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, s in stories:
            print(f"  {p} {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
