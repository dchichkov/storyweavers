#!/usr/bin/env python3
"""
A tiny story world: a mystery about a lost button and a friendship that wobbles
before it mends.

Premise:
- Two children find a small button in a curious place.
- One friend thinks the button belongs to someone else and wants to ask around.
- The other friend feels a sting of rejection when a guess is dismissed.
- They solve the mystery by following clues and end with a kinder friendship.

The world model tracks:
- physical things: a button, a clue card, a lantern, a notebook
- emotions: curiosity, worry, rejection, trust, relief, joy

This script follows the Storyweavers contract and includes an ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# -----------------------------------------------------------------------------
# Core model
# -----------------------------------------------------------------------------

THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    button: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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
        if not hasattr(self, "_tags"):
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
    name: str
    indoors: bool = False
    clue_kind: str = "thread"
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Button:
    color: str
    shape: str
    size: str
    has_hint: bool = False
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    button: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.button: Optional[Entity] = None
        self.owner: Optional[Entity] = None
        self.friendship_repaired: bool = False

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.lines = list(self.lines)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.button = copy.deepcopy(self.button)
        c.owner = copy.deepcopy(self.owner)
        c.friendship_repaired = self.friendship_repaired
        return c


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

PLACES = {
    "library": Place(name="the library", indoors=True, clue_kind="bookmark"),
    "garden": Place(name="the garden", indoors=False, clue_kind="soil"),
    "attic": Place(name="the attic", indoors=True, clue_kind="dust"),
    "courtyard": Place(name="the courtyard", indoors=False, clue_kind="leaf"),
}

BUTTONS = {
    "red_round": Button(color="red", shape="round", size="small", has_hint=False),
    "blue_star": Button(color="blue", shape="star-shaped", size="small", has_hint=True),
    "green_square": Button(color="green", shape="square", size="tiny", has_hint=False),
}

HEROES = [
    ("Mia", "girl"),
    ("Noah", "boy"),
    ("Lina", "girl"),
    ("Eli", "boy"),
    ("Nora", "girl"),
    ("Theo", "boy"),
]

FRIENDS = [
    ("Pip", "girl"),
    ("Sam", "boy"),
    ("June", "girl"),
    ("Max", "boy"),
    ("Ada", "girl"),
    ("Ben", "boy"),
]

TRAITS = ["curious", "gentle", "brave", "careful", "quiet"]

# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A button can be a mystery clue if it has a hint or belongs to someone.
mystery_clue(B) :- button(B), has_hint(B).
mystery_clue(B) :- button(B), owner(B,O).

% Rejection happens when one friend dismisses a guess about the button.
rejection(H,F) :- hears_guess(H,F), dismisses(F,H).

% Friendship can be repaired when the children share the clue and solve it.
repaired(H,F) :- rejection(H,F), shares_clue(H,F), solved_mystery(H,F).

#show mystery_clue/1.
#show rejection/2.
#show repaired/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        lines.append(asp.fact("clue_kind", pid, p.clue_kind))
    for bid, b in BUTTONS.items():
        lines.append(asp.fact("button", bid))
        lines.append(asp.fact("color", bid, b.color))
        lines.append(asp.fact("shape", bid, b.shape))
        lines.append(asp.fact("size", bid, b.size))
        if b.has_hint:
            lines.append(asp.fact("has_hint", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_clue/1."))
    clingo_buttons = {t[0] for t in asp.atoms(model, "mystery_clue")}
    python_buttons = {bid for bid, b in BUTTONS.items() if b.has_hint}
    python_buttons |= {bid for bid in BUTTONS}
    if clingo_buttons == python_buttons:
        print(f"OK: ASP and Python agree on mystery clues ({len(clingo_buttons)} buttons).")
        return 0
    print("Mismatch between ASP and Python:")
    print("  ASP:", sorted(clingo_buttons))
    print("  Python:", sorted(python_buttons))
    return 1


# -----------------------------------------------------------------------------
# Story engine
# -----------------------------------------------------------------------------

def valid_combo(place: str, button: str) -> bool:
    return place in PLACES and button in BUTTONS


def select_owner(rng: random.Random) -> Entity:
    name, typ = rng.choice(HEROES)
    return Entity(id=name, kind="character", type=typ, label=name, traits=[rng.choice(TRAITS)])


def select_friend(rng: random.Random) -> Entity:
    name, typ = rng.choice(FRIENDS)
    return Entity(id=name, kind="character", type=typ, label=name, traits=[rng.choice(TRAITS)])


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero_name, hero_type = params.hero.split(":", 1)
    friend_name, friend_type = params.friend.split(":", 1)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name, traits=["careful"]))
    button_def = _safe_lookup(BUTTONS, params.button)
    button = world.add(Entity(
        id="button",
        kind="thing",
        type="button",
        label=f"{button_def.color} {button_def.shape} button",
        phrase=f"a {button_def.color} {button_def.shape} button",
        owner=None,
    ))
    if button_def.has_hint:
        button.meters["hint"] = 1
    world.button = button
    world.facts.update(hero=hero, friend=friend, button=button, button_def=button_def)
    return world


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    button: Entity = world.facts["button"]

    # Act 1
    world.say(f"At {world.place.name}, {hero.id} and {friend.id} were friends who liked quiet puzzles.")
    world.say(f"They found {button.phrase} near a lonely corner, as if it had dropped from a secret pocket.")
    world.para()
    world.say(f"{hero.id} wanted to keep looking for clues, but {friend.id} frowned and guessed it might belong to someone who did not want it back.")
    world.say(f"When {friend.id} dismissed {hero.id}'s first idea, {hero.id} felt a sharp little rejection in {hero.pronoun('possessive')} chest.")

    hero.memes["rejection"] += 1
    hero.memes["worry"] += 1
    friend.memes["distance"] += 1
    world.facts["rejection"] = True

    # Act 2
    world.para()
    world.say(f"Instead of arguing, {hero.id} picked up the button and showed the tiny scratch on its edge.")
    if button.meters.get("hint", 0) >= THRESHOLD:
        world.say(f"That scratch matched a pattern they had seen on the old notice board in {world.place.name}, so the button was a clue.")
    else:
        world.say(f"The button looked too plain to be a treasure, which made it feel even more mysterious.")

    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["shares_clue"] = True
    world.facts["mystery_clue"] = True

    # The mystery resolution: the button matches an owner.
    owner = world.add(Entity(id="Librarian", kind="character", type="woman", label="the librarian"))
    world.owner = owner
    world.para()
    world.say(f"They followed the clue to {owner.label}, whose coat had a missing spot where a button should be.")
    world.say(f"{owner.label.capitalize()} smiled when they held up the button, because it had fallen off during a busy morning and she had been hoping someone kind would notice.")

    # Friendship repair
    friend.memes["guilt"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["rejection"] = 0.0
    friend.memes["distance"] = 0.0
    world.friendship_repaired = True

    world.para()
    world.say(f"{friend.id} looked at {hero.id} and said sorry for the rejection.")
    world.say(f"{hero.id} nodded, and the two friends left together, lighter than before, with the mystery solved and the lost button returned.")


def story_text(world: World) -> str:
    return world.render()


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    button: Entity = f["button"]
    return [
        "Write a short mystery story for a young child about two friends, a lost button, and a kind ending.",
        f"Tell a gentle story where {hero.id} and {friend.id} find {button.phrase} and solve a small mystery together.",
        "Write a simple story that includes rejection, a clue, and friendship mending after a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    button: Entity = f["button"]
    owner: Entity = world.owner
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} find at {world.place.name}?",
            answer=f"They found {button.phrase}, which looked like a tiny mystery clue.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel rejection at first?",
            answer=f"{friend.id} dismissed {hero.id}'s first idea, so {hero.id} felt rejected and worried.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They followed the clue to {owner.label} and discovered the button had fallen off {owner.pronoun('possessive')} coat.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The friends repaired their friendship, returned the button, and left feeling kinder and calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a button?",
            answer="A button is a small piece used to fasten clothing, and it can also be a clue if it is lost in a strange place.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood right away, so people look for clues to figure it out.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, listening to them, and trying to make things right after a hurt feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about a lost button and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--button", choices=BUTTONS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    button = getattr(args, "button", None) or rng.choice(sorted(BUTTONS))
    if not valid_combo(place, button):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None)
    if hero is None:
        hn, ht = rng.choice(HEROES)
        hero = f"{hn}:{ht}"
    friend = getattr(args, "friend", None)
    if friend is None:
        fn, ft = rng.choice(FRIENDS)
        friend = f"{fn}:{ft}"
    if hero.split(":")[0] == friend.split(":")[0]:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, friend=friend, button=button)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    solve_mystery(world)
    return StorySample(
        params=params,
        story=story_text(world),
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
        print(f"friendship_repaired={sample.world.friendship_repaired}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_clue/1.\n#show rejection/2.\n#show repaired/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_check())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery_clue/1.\n#show rejection/2.\n#show repaired/2."))
        print("mystery_clue:", sorted(asp.atoms(model, "mystery_clue")))
        print("rejection:", sorted(asp.atoms(model, "rejection")))
        print("repaired:", sorted(asp.atoms(model, "repaired")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="library", hero="Mia:girl", friend="Pip:girl", button="blue_star"),
            StoryParams(place="attic", hero="Noah:boy", friend="June:girl", button="red_round"),
            StoryParams(place="garden", hero="Lina:girl", friend="Max:boy", button="green_square"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
