#!/usr/bin/env python3
"""
javelin_suspense_sharing_whodunit.py
====================================

A tiny whodunit-style story world about a missing javelin, a shared search,
and a suspenseful reveal. The domain is deliberately small: one track field,
a few suspects, and one object that changes hands as the story unfolds.

Seed tale imagined from the prompt:
- A school track club is preparing for a relay-day practice.
- The coach's lightweight javelin vanishes from the shed.
- Two children search in suspense, share clues, and discover who moved it.
- The ending proves the change in world state: the javelin is found, shared
  politely, and the worried mood dissolves.

The script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- lazy asp import in ASP helpers
- StoryParams + parser + resolve_params + generate + emit + main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
            keys = [upper + "S", upper + "ES"]
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child1: object | None = None
    child2: object | None = None
    j: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    indoors: bool = False
    details: str = ""
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
class Suspect:
    id: str
    label: str
    role: str
    clue: str
    secret: str
    shares: bool = False
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
class Javelin:
    label: str
    phrase: str
    material: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    setting: str
    suspect: str
    mover: str
    name1: str
    name2: str
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


SETTINGS = {
    "track": Setting(place="the track field", indoors=False, details="The lanes shone pale in the morning light."),
    "shed": Setting(place="the equipment shed", indoors=True, details="The shed smelled like dust, chalk, and old grass."),
    "gym": Setting(place="the school gym", indoors=True, details="The gym was bright, but the far corner looked shadowy."),
}

SUSPECTS = {
    "coach": Suspect(id="coach", label="the coach", role="coach", clue="a whistle hung from a hook", secret="the javelin had been moved for a lesson", shares=False),
    "older_child": Suspect(id="older_child", label="an older child", role="captain", clue="muddy shoes were by the door", secret="they had carried it to the field", shares=True),
    "assistant": Suspect(id="assistant", label="the assistant", role="helper", clue="a notebook lay open on a bench", secret="they borrowed it and forgot to tell anyone", shares=True),
}

JAVELINS = {
    "practice": Javelin(label="javelin", phrase="a light practice javelin", material="foam-tipped", safe=True, tags={"javelin", "sport"}),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ava", "Eli", "Zoe", "Theo", "Iris", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, x, "practice") for s in SETTINGS for x in SUSPECTS]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if "missing" in world.fired:
        return out
    j = world.get("javelin")
    for e in list(world.entities.values()):
        if e.memes.get("worry", 0.0) >= THRESHOLD and j.meters.get("hidden", 0.0) >= THRESHOLD:
            world.fired.add("missing")
            e.memes["suspense"] = e.memes.get("suspense", 0.0) + 1
            out.append("The missing javelin made everyone whisper and look around twice.")
            break
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, suspect: Suspect, mover: Suspect, name1: str, name2: str) -> World:
    w = World(setting)
    child1 = w.add(Entity(id=name1, kind="character", type="girl" if name1 in {"Mia", "Lena", "Ava", "Zoe", "Iris"} else "boy", label=name1))
    child2 = w.add(Entity(id=name2, kind="character", type="girl" if name2 in {"Mia", "Lena", "Ava", "Zoe", "Iris"} else "boy", label=name2))
    adult = w.add(Entity(id="adult", kind="character", type="adult", label="the coach"))
    j = w.add(Entity(id="javelin", type="object", label="javelin"))
    j.meters["hidden"] = 1.0
    child1.memes["worry"] = 1.0
    child2.memes["worry"] = 1.0
    adult.memes["worry"] = 1.0

    w.say(f"{setting.details} {name1} and {name2} found a strange empty spot where the javelin should have been.")
    w.say(f'"Who took it?" {name1} asked, and {name2} held the shed door open to look for clues.')
    w.say(f"They noticed that {suspect.clue}, which felt like the first clue in a little mystery.")
    w.para()
    propagate(w)
    w.say(f"{name2} said they should share the search instead of rushing in alone, so each child checked a different corner.")
    w.say(f"At last, they found the javelin where {suspect.secret}.")
    j.meters["hidden"] = 0.0
    j.meters["found"] = 1.0
    j.attrs["shared"] = True
    mover_tag = mover.role
    if mover.shares:
        w.say(f"{mover.label} smiled and said the javelin could be shared for practice, as long as everyone took turns.")
    else:
        w.say(f"{mover.label} looked sheepish and admitted they should have asked before moving it.")
    w.para()
    child1.memes["worry"] = 0.0
    child2.memes["worry"] = 0.0
    child1.memes["relief"] = 1.0
    child2.memes["relief"] = 1.0
    w.say(f"In the end, {name1} and {name2} carried the javelin back together, and the mystery was solved.")
    w.say(f"The empty spot was gone, the clues made sense, and the day felt calm again.")
    w.facts.update(
        child1=child1,
        child2=child2,
        adult=adult,
        javelin=j,
        setting=setting,
        suspect=suspect,
        mover=mover,
        found=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit-style story for a young child about a missing {f["javelin"].label} at {f["setting"].place}.',
        f"Tell a suspenseful story where {f['child1'].id} and {f['child2'].id} share the search and solve the mystery of who moved the javelin.",
        f'Write a child-facing mystery about clues, sharing, and a {f["javelin"].phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, adult, suspect, mover, j = f["child1"], f["child2"], f["adult"], f["suspect"], f["mover"], f["javelin"]
    return [
        QAItem(question=f"What was missing in {f['setting'].place}?", answer=f"The javelin was missing, and that made the children feel curious and worried."),
        QAItem(question=f"Who shared the search?", answer=f"{c1.id} and {c2.id} shared the search so they could solve the mystery together."),
        QAItem(question=f"What clue pointed them toward the answer?", answer=f"They noticed that {suspect.clue}, which helped them think about who had moved the javelin."),
        QAItem(question=f"How did the story end?", answer=f"They found the javelin, learned who moved it, and carried it back together in a calm ending."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a javelin?", answer="A javelin is a long throwing sports object used in track-and-field practice."),
        QAItem(question="Why is sharing helpful?", answer="Sharing helps because more than one person can help, take turns, and solve a problem together."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps you figure out a mystery."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    lines += ["", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines += ["", "== world qa =="]
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="shed", suspect="coach", mover="assistant", name1="Mia", name2="Noah"),
    StoryParams(setting="track", suspect="older_child", mover="older_child", name1="Lena", name2="Eli"),
    StoryParams(setting="gym", suspect="assistant", mover="assistant", name1="Ava", name2="Finn"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld about a missing javelin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--mover", choices=SUSPECTS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "suspect", None) is None or c[1] == getattr(args, "suspect", None))
              and (getattr(args, "mover", None) is None or c[1] == getattr(args, "mover", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, suspect, mover = rng.choice(list(combos))
    n1 = getattr(args, "name1", None) or rng.choice(NAMES)
    n2 = getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != n1])
    return StoryParams(setting=setting, suspect=suspect, mover=mover, name1=n1, name2=n2)


def generate(params: StoryParams) -> StorySample:
    w = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SUSPECTS, params.suspect), _safe_lookup(SUSPECTS, params.mover), params.name1, params.name2)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_knowledge_qa(w), world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for k in SUSPECTS:
        lines.append(asp.fact("suspect", k))
    for k in JAVELINS:
        lines.append(asp.fact("javelin", k))
    for s in SETTINGS:
        for k in SUSPECTS:
            lines.append(asp.fact("valid", s, k, "practice"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, U, J) :- setting(S), suspect(U), javelin(J).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("ASP/Python mismatch")
        return 1
    sample = generate(CURATED[0])
    if not sample.story or "javelin" not in sample.story:
        print("Smoke test failed")
        return 1
    print(f"OK: {len(a)} combos; smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
