#!/usr/bin/env python3
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
class Place:
    key: str
    label: str
    clue_source: str
    sound_kind: str
    sound: str
    reason: str
    mystery_noun: str
    mood: str
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
class Team:
    key: str
    label: str
    helper_verb: str
    together_line: str
    fix_line: str
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
class StoryParams:
    place: str
    team: str
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    friend: object | None = None
    hero: object | None = None
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


class World:
    def __init__(self, place: Place, team: Team) -> None:
        self.place = place
        self.team = team
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, str] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACES = {
    "kitchen": Place(
        key="kitchen",
        label="the kitchen",
        clue_source="the tin cup",
        sound_kind="clink",
        sound="clink-clink",
        reason="a spoon tapped the tin cup by the sink",
        mystery_noun="cooking sound",
        mood="bright",
    ),
    "garden": Place(
        key="garden",
        label="the garden",
        clue_source="the gate",
        sound_kind="creak",
        sound="creak-creak",
        reason="the little gate swung in the breeze",
        mystery_noun="garden sound",
        mood="soft",
    ),
    "playroom": Place(
        key="playroom",
        label="the playroom",
        clue_source="the music box",
        sound_kind="hum",
        sound="hum-hum",
        reason="the music box was turning all by itself",
        mystery_noun="playroom sound",
        mood="cozy",
    ),
    "attic": Place(
        key="attic",
        label="the attic",
        clue_source="the loose board",
        sound_kind="bump",
        sound="bump-bump",
        reason="a loose board answered with a sleepy bounce",
        mystery_noun="attic sound",
        mood="mystery",
    ),
}

TEAMS = {
    "siblings": Team(
        key="siblings",
        label="two siblings",
        helper_verb="look together",
        together_line="They held hands and looked around.",
        fix_line="One listened up high while the other listened low, and that made the puzzle small.",
    ),
    "friends": Team(
        key="friends",
        label="two friends",
        helper_verb="peek together",
        together_line="They tiptoed side by side, as light as two feathers.",
        fix_line="One pointed at the clue while the other listened for the sound again.",
    ),
    "neighbors": Team(
        key="neighbors",
        label="two neighbors",
        helper_verb="work together",
        together_line="They split the job in half and took turns finding the clue.",
        fix_line="One found the source, and the other smiled, because teamwork was the key.",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Toby", "Zoe", "Finn"]
COMPANION_NAMES = ["Ava", "Max", "Ivy", "Owen", "Ruby", "Sam", "Elsa", "Noah"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme teamwork mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--team", choices=TEAMS)
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
    team = getattr(args, "team", None) or rng.choice(list(TEAMS))
    return StoryParams(place=place, team=team)


def rhyme_opening(place: Place) -> str:
    return f"Come, come, come to {place.label}, where the day was {place.mood} and warm."


def story_title_line(place: Place, team: Team) -> str:
    return f"In {place.label}, {team.label} heard a mystery sound."


def narrate_world(world: World) -> None:
    p = world.place
    t = world.team
    hero = world.get("hero")
    friend = world.get("friend")

    world.say(story_title_line(p, t))
    world.say(f"{rhyme_opening(p)}")
    world.say(f"{hero.label} came with {friend.label}, and they began to {t.helper_verb}.")
    world.para()
    world.say(f"First came a tiny {p.sound_kind}. {p.sound} went the sound, soft and sweet.")
    world.say(f"{hero.label} said, “What can it be?”")
    world.say(f"{friend.label} said, “Let us see.”")
    world.say(f"{t.together_line}")
    world.say(f"Then came the clue: {p.reason}.")
    world.say(f"{t.fix_line}")
    world.para()
    world.say(f"At last they found the answer, and the little {p.mystery_noun} was no more a fright.")
    world.say(f"They laughed in the light, and {p.sound} sounded merry instead of strange.")
    world.say(f"So come, come, come to {p.label}; with teamwork, a mystery can turn bright.")


def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    team = _safe_lookup(TEAMS, params.team)
    world = World(place, team)
    hero = world.add(Entity(id="hero", kind="character", label=random.choice(NAMES)))
    friend = world.add(Entity(id="friend", kind="character", label=random.choice(COMPANION_NAMES)))
    world.facts.update(
        place=place.key,
        team=team.key,
        hero=hero.label,
        friend=friend.label,
        sound=place.sound,
        reason=place.reason,
        clue_source=place.clue_source,
    )
    narrate_world(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.place
    t = world.team
    return [
        f"Write a nursery-rhyme story about coming to {p.label}, hearing {p.sound}, and solving the mystery together.",
        f"Tell a gentle story where {t.label} and a friend use teamwork to find why {p.sound} kept sounding.",
        f"Make a short rhyme for children that begins with 'Come, come, come' and ends with a solved mystery in {p.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.place
    t = world.team
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    return [
        QAItem(
            question=f"Who came to {p.label} to solve the mystery sound?",
            answer=f"{hero} came with {friend}, and they solved it together by teamwork.",
        ),
        QAItem(
            question=f"What sound did they hear first in {p.label}?",
            answer=f"They heard {p.sound}, a little {p.sound_kind} sound.",
        ),
        QAItem(
            question=f"How did they solve the mystery in {p.label}?",
            answer=f"They worked as {t.label}, looked for the clue, and found that {p.reason}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not know at first, so you look for clues.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special sounds that help tell a story, like clink, bump, or creak.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: {e.label}")
    lines.append(f"  place: {world.place.key}")
    lines.append(f"  team: {world.team.key}")
    lines.append(f"  sound: {world.place.sound}")
    lines.append(f"  clue: {world.place.reason}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
team(T) :- teamwork(T).
solved(P) :- place(P), clue(P,_), sound(P,_).
valid(P,T) :- place(P), team(T), solved(P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, place in PLACES.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("clue", key, place.clue_source))
        lines.append(asp.fact("sound", key, place.sound_kind))
    for key in TEAMS:
        lines.append(asp.fact("teamwork", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, t) for p in PLACES for t in TEAMS)


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    if py - asps:
        print("  only in python:", sorted(py - asps))
    if asps - py:
        print("  only in clingo:", sorted(asps - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [
    StoryParams(place="attic", team="siblings"),
    StoryParams(place="garden", team="friends"),
    StoryParams(place="playroom", team="neighbors"),
    StoryParams(place="kitchen", team="siblings"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for p, t in vals:
            print(f"  {p}  {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i - 1
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.place} / {p.team}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
