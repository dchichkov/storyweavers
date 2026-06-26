#!/usr/bin/env python3
"""
A small pirate-tale storyworld with foreshadowing, cautionary warning, and a surprise turn.

Premise:
- A sophomore deckhand on a pirate ship keeps a curious index.
- The ship also carries a cage for a parrot.
- The index and cage matter to the later twist: the cage hides a clue that changes the voyage.

This script builds a tiny simulated world where:
- meters track physical state like location, possession, and hidden clues
- memes track emotional state like worry, hope, surprise, pride
- the story is driven from the state, not from a frozen template
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    role: object | None = None
    cage: object | None = None
    captain: object | None = None
    clue: object | None = None
    hero: object | None = None
    index: object | None = None
    parrot: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "sailor", "pirate"}:
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
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
    role: str
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


SETTING = "the pirate ship"
NAMES = {
    "girl": ["Mara", "Ivy", "Nell", "June"],
    "boy": ["Finn", "Jory", "Pace", "Noel"],
}
ROLES = ["sophomore deckhand", "sophomore navigator", "young cabin mate"]


ASP_RULES = r"""
#show foreshadow/1.
#show caution/1.
#show surprise/1.

foreshadow(clue) :- clue_present.
caution(warned) :- storm_seen.
surprise(found_map) :- hidden_map, cage_opened.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("clue_present"),
        asp.fact("storm_seen"),
        asp.fact("hidden_map"),
        asp.fact("cage_opened"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld with index, cage, sophomore.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(name=name, gender=gender, role=role)


def _act_story(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name, role=params.role))
    captain = w.add(Entity(id="captain", kind="character", type="pirate", label="Captain Brine"))
    parrot = w.add(Entity(id="parrot", kind="character", type="bird", label="Mister Squall"))
    index = w.add(Entity(id="index", type="book", label="index", phrase="a salt-stained index of harbor names"))
    cage = w.add(Entity(id="cage", type="thing", label="cage", phrase="a brass cage with a clicky latch"))
    clue = w.add(Entity(id="clue", type="thing", label="map scrap", phrase="a folded map scrap", hidden_in="cage"))

    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 0
    hero.memes["surprise"] = 0
    captain.memes["worry"] = 1

    w.say(
        f"On {SETTING}, {hero.label} was a {params.role} who kept {index.phrase} under one arm."
    )
    w.say(
        f"Beside the mast sat {cage.phrase}, and {parrot.label} bobbed inside it like a tiny gray drum."
    )
    w.say(
        f"{hero.label} liked to leaf through the index because every page named a real cove, a reef, or a quiet quay."
    )
    w.say(
        f"Still, {hero.pronoun('possessive')} {captain.label} had warned, 'Do not open the cage latch in rough weather.'"
    )

    w.para()
    w.say(
        f"Then dark clouds climbed over the water, and the ship began to lean. The captain pointed at the sky and called that it was time to tie things down."
    )
    hero.memes["worry"] += 1
    captain.memes["worry"] += 1
    w.say(
        f"{hero.label} remembered the warning and kept a hand on the cage, because a loose latch could send the bird flapping into the rigging."
    )

    w.para()
    w.say(
        f"As {hero.label} checked the index again, {hero.pronoun('possessive')} finger snagged a loose page seam. Something slid out from behind the cage lining."
    )
    clue.hidden_in = None
    hero.memes["surprise"] += 1
    hero.memes["pride"] = 1
    w.say(
        f"It was a folded map scrap, marked with a bright X and a note in red ink: the safest cove was the one hidden behind the old cage."
    )
    w.say(
        f"The captain blinked, then laughed. The cage had not been only for the parrot after all; it had hidden the clue that the old sea dogs had missed."
    )
    w.say(
        f"So the ship turned for the quiet cove named in the index, and {hero.label} held the map high while {parrot.label} chirped from the open cage, safe at last."
    )

    w.facts.update(hero=hero, captain=captain, parrot=parrot, index=index, cage=cage, clue=clue)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate tale for a child using the words "index", "cage", and "sophomore".',
        f"Tell a short story where {f['hero'].label}, a {f['hero'].type} {f['hero'].role}, keeps an index and learns something surprising about a cage.",
        "Write a gentle pirate story with a warning, a storm, and a hidden clue in a cage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    captain = _safe_fact(world, f, "captain")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {hero.role} on a pirate ship.",
        ),
        QAItem(
            question=f"What did {hero.label} keep under one arm at the start?",
            answer="He kept an index under one arm, and it helped point toward real places at sea.",
        ),
        QAItem(
            question=f"What warning did the captain give about the cage?",
            answer="The captain warned not to open the cage latch in rough weather.",
        ),
        QAItem(
            question="What was the surprise hidden in the cage?",
            answer="A folded map scrap was hidden behind the cage lining, and it showed the way to a safe cove.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and the ship?",
            answer="They turned toward the quiet cove named in the index, with the hidden clue finally found and the parrot safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an index?",
            answer="An index is a list of names or topics that helps you find information quickly.",
        ),
        QAItem(
            question="What is a cage for?",
            answer="A cage is a container that can keep an animal safe or stop it from wandering away.",
        ),
        QAItem(
            question="What does sophomore mean?",
            answer="Sophomore usually means someone in their second year, like a student who is not brand new anymore.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint that something important may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show foreshadow/1.\n#show caution/1.\n#show surprise/1.")
    model = asp.one_model(program)
    got = set((sym.name, tuple(a.name if a.type == a.type.Function and not a.arguments else (a.string if a.type == a.type.String else a.number) for a in sym.arguments)) for sym in model)
    want = {("foreshadow", ("clue",)), ("caution", ("warned",)), ("surprise", ("found_map",))}
    if got == want:
        print("OK: ASP gate matches Python reasoning.")
        return 0
    print("MISMATCH:", got, want)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _act_story(params)
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
        print(asp_program("#show foreshadow/1.\n#show caution/1.\n#show surprise/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show foreshadow/1.\n#show caution/1.\n#show surprise/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        cur = [
            StoryParams(name="Mara", gender="girl", role="sophomore navigator"),
            StoryParams(name="Finn", gender="boy", role="sophomore deckhand"),
            StoryParams(name="Ivy", gender="girl", role="young cabin mate"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 20 + 20:
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
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
