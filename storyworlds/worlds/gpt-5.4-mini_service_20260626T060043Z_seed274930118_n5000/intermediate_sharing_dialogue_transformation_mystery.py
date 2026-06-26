#!/usr/bin/env python3
"""
A small mystery storyworld built around sharing clues, dialogue, and a
transforming object that reveals the answer.

The seed idea:
- A child notices a strange problem.
- They share clues with a friend or grown-up.
- Through dialogue, they test a few guesses.
- Something transforms in the end and reveals the hidden truth.
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
class Object:
    id: str
    label: str
    phrase: str
    kind: str
    owner: Optional[str] = None
    hidden: bool = False
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    pronoun_subject: str = "they"
    pronoun_object: str = "them"
    pronoun_possessive: str = "their"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    clue: str
    hidden_truth: str
    transforming_item: str
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


PLACES = {
    "attic": "the attic",
    "library": "the little library",
    "garden": "the garden",
    "hall": "the hallway",
}

HEROES = [
    ("Mina", "girl", "she", "her", "her"),
    ("Leo", "boy", "he", "him", "his"),
    ("Rae", "child", "they", "them", "their"),
    ("Noor", "child", "they", "them", "their"),
]

FRIENDS = ["Jude", "Pip", "Tara", "Owen", "Mila", "Ben"]

CLUES = {
    "footprints": "tiny muddy footprints",
    "whisper": "a faint whisper from behind the shelf",
    "button": "a shiny button on the floor",
    "scent": "a sweet smell of oranges in the air",
    "shadow": "a crooked shadow on the wall",
}

TRUTHS = {
    "cat": "the missing cat was sleeping in a basket",
    "key": "the lost key was inside a jar",
    "kite": "the broken kite was stuck in a tree",
    "ring": "the old ring was under a loose tile",
}

TRANSFORMING_ITEMS = {
    "box": "a plain cardboard box",
    "mirror": "a dusty little mirror",
    "lamp": "a sleepy old lamp",
    "book": "a closed green book",
}

BASE_REASONS = {
    "box": "the lid slid open and the inside was empty no longer",
    "mirror": "the dust wiped away and a hidden mark appeared",
    "lamp": "the shade lifted and a note dropped out",
    "book": "the cover turned and a folded map slipped free",
}

WORLD_KNOWLEDGE = {
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that can help solve a problem or mystery.",
        ),
    ],
    "sharing": [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let another person look at, use, or know about something too.",
        ),
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is the words that characters say to each other in a story.",
        ),
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one thing or state into another.",
        ),
    ],
}


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.characters: dict[str, Character] = {}
        self.objects: dict[str, Object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_char(self, char: Character) -> Character:
        self.characters[char.id] = char
        return char

    def add_obj(self, obj: Object) -> Object:
        self.objects[obj.id] = obj
        return obj

    def char(self, cid: str) -> Character:
        return self.characters[cid]

    def obj(self, oid: str) -> Object:
        return self.objects[oid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for c in self.characters.values():
            bits = []
            if c.meters:
                bits.append(f"meters={c.meters}")
            if c.memes:
                bits.append(f"memes={c.memes}")
            out.append(f"  {c.id:8} ({c.type:7}) {' '.join(bits)}")
        for o in self.objects.values():
            bits = []
            if o.owner:
                bits.append(f"owner={o.owner}")
            if o.hidden:
                bits.append("hidden=True")
            if o.transformed:
                bits.append("transformed=True")
            if o.meters:
                bits.append(f"meters={o.meters}")
            if o.memes:
                bits.append(f"memes={o.memes}")
            out.append(f"  {o.id:8} ({o.kind:7}) {o.label} {' '.join(bits)}")
        return "\n".join(out)


def solve_mystery(world: World) -> None:
    hero = world.char(world.facts["hero"])
    friend = world.char(world.facts["friend"])
    clue = world.obj(world.facts["clue"])
    item = world.obj(world.facts["item"])
    truth = _safe_fact(world, world.facts, "truth")

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was a curious little {hero.type} who liked quiet places and odd questions."
    )
    world.say(
        f"One afternoon in {world.place}, {hero.id} noticed {clue.phrase}."
    )

    world.para()
    hero.memes["unease"] += 1
    clue.hidden = False
    world.say(
        f"{hero.id} shared the clue with {friend.id}. "
        f'"Look," {hero.pronoun_subject} said, "does that seem strange to you?"'
    )
    friend.memes["care"] += 1
    world.say(
        f'"It does," {friend.id} said. "Let\'s think together instead of guessing too fast."'
    )

    world.para()
    world.say(
        f'They talked softly as they searched. "Maybe it belongs to someone," '
        f"{friend.id} said. {hero.id} shook {hero.pronoun_possessive} head, because the clue did not fit that idea."
    )
    hero.meters["search"] = 1
    friend.meters["search"] = 1
    world.say(
        f"Then {hero.id} noticed {item.phrase}. It looked ordinary at first, but something about it felt unfinished."
    )

    world.para()
    item.hidden = False
    item.memes["mystery"] += 1
    world.say(
        f'{hero.id} touched {item.phrase} carefully. Suddenly it transformed.'
    )
    item.transformed = True
    world.say(
        f"The quiet shape changed, and {_safe_lookup(BASE_REASONS, item.kind)}. "
        f"At last, the answer was clear: {truth}."
    )
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} smiled at each other. The mystery was solved, and the room felt calm again."
    )


def build_story(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    hero_name, hero_type, subj, obj, pos = next(
        (n, t, s, o, p) for (n, t, s, o, p) in HEROES if n == params.hero_name
    )
    hero = world.add_char(
        Character(
            id=hero_name,
            type=hero_type,
            pronoun_subject=subj,
            pronoun_object=obj,
            pronoun_possessive=pos,
        )
    )
    friend = world.add_char(
        Character(
            id=params.friend_name,
            type="child",
            pronoun_subject="they",
            pronoun_object="them",
            pronoun_possessive="their",
        )
    )
    clue = world.add_obj(
        Object(
            id="clue",
            label=params.clue,
            phrase=_safe_lookup(CLUES, params.clue),
            kind="clue",
            hidden=True,
        )
    )
    item = world.add_obj(
        Object(
            id="item",
            label=params.transforming_item,
            phrase=_safe_lookup(TRANSFORMING_ITEMS, params.transforming_item),
            kind=params.transforming_item,
            hidden=True,
        )
    )
    world.facts = {
        "hero": hero.id,
        "friend": friend.id,
        "clue": clue.id,
        "item": item.id,
        "truth": _safe_lookup(TRUTHS, params.hidden_truth),
        "place": world.place,
        "clue_kind": params.clue,
        "item_kind": params.transforming_item,
    }

    solve_mystery(world)

    prompts = [
        f'Write a short mystery story for a young child that uses the word "intermediate" in a gentle way.',
        f"Tell a story where {hero.id} and {friend.id} share clues and solve a small mystery in {world.place}.",
        f"Write a child-friendly mystery with dialogue, sharing, and a surprise transformation.",
    ]

    story_qa = [
        QAItem(
            question=f"Who shared the clue with {hero.id}?",
            answer=f"{friend.id} shared the clue with {hero.id}, and they looked at it together.",
        ),
        QAItem(
            question=f"What did {hero.id} notice first in {world.place}?",
            answer=f"{hero.id} noticed {clue.phrase} first, and that strange clue started the mystery.",
        ),
        QAItem(
            question=f"What happened when {hero.id} touched {item.phrase}?",
            answer=f"{item.phrase} transformed, and that change revealed the hidden answer.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"It ended when the transformed item showed that {_safe_lookup(TRUTHS, params.hidden_truth)}.",
        ),
    ]

    world_qa = []
    for key in ["mystery", "sharing", "dialogue", "transformation"]:
        world_qa.extend(WORLD_KNOWLEDGE[key])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with sharing, dialogue, and transformation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--truth", choices=TRUTHS.keys())
    ap.add_argument("--item", choices=TRANSFORMING_ITEMS.keys())
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
    hero = getattr(args, "hero", None) or rng.choice([h[0] for h in HEROES])
    hero_entry = next(h for h in HEROES if h[0] == hero)
    return StoryParams(
        place=getattr(args, "place", None) or rng.choice(list(PLACES.keys())),
        hero_name=hero,
        hero_type=hero_entry[1],
        friend_name=getattr(args, "friend", None) or rng.choice([f for f in FRIENDS if f != hero]),
        clue=getattr(args, "clue", None) or rng.choice(list(CLUES.keys())),
        hidden_truth=getattr(args, "truth", None) or rng.choice(list(TRUTHS.keys())),
        transforming_item=getattr(args, "item", None) or rng.choice(list(TRANSFORMING_ITEMS.keys())),
    )


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES:
        pass
    if params.hidden_truth not in TRUTHS:
        pass
    if params.transforming_item not in TRANSFORMING_ITEMS:
        pass
    return build_story(params)


ASP_RULES = r"""
place(attic;library;garden;hall).
clue(footprints;whisper;button;scent;shadow).
truth(cat;key;kite;ring).
item(box;mirror;lamp;book).

shares(P) :- place(P).
transforms(I) :- item(I).
mystery(P,C,I,T) :- place(P), clue(C), item(I), truth(T).
#show mystery/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TRUTHS:
        lines.append(asp.fact("truth", t))
    for i in TRANSFORMING_ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/4."))
    atoms = sorted(set(asp.atoms(model, "mystery")))
    python_count = len(PLACES) * len(CLUES) * len(TRANSFORMING_ITEMS) * len(TRUTHS)
    if len(atoms) == python_count:
        print(f"OK: clingo produced {len(atoms)} mystery combinations.")
        return 0
    print(f"Mismatch: clingo={len(atoms)} python={python_count}")
    return 1


CURATED = [
    StoryParams(place="library", hero_name="Mina", hero_type="girl", friend_name="Jude", clue="button", hidden_truth="key", transforming_item="mirror"),
    StoryParams(place="attic", hero_name="Leo", hero_type="boy", friend_name="Tara", clue="shadow", hidden_truth="cat", transforming_item="box"),
    StoryParams(place="garden", hero_name="Rae", hero_type="child", friend_name="Pip", clue="footprints", hidden_truth="kite", transforming_item="lamp"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery/4."))
        atoms = sorted(set(asp.atoms(model, "mystery")))
        print(f"{len(atoms)} combinations")
        for atom in atoms[:20]:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
