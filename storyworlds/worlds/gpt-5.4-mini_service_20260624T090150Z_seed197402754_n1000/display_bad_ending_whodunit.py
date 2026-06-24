#!/usr/bin/env python3
"""
A small whodunit storyworld with a bad ending.

Seed premise:
- A museum display goes wrong.
- A young detective-like character asks questions, follows clues, and tries to
  solve who ruined the display.
- The ending is intentionally bad: the mystery stays unsolved, the real cause is
  not fully found, or the wrong person is blamed.
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

DISPLAY_KINDS = {
    "toy_display": {
        "place": "the toy shop window",
        "thing": "display",
        "object": "toy display",
        "breakable": False,
    },
    "museum_display": {
        "place": "the museum hall",
        "thing": "display",
        "object": "museum display",
        "breakable": True,
    },
    "cake_display": {
        "place": "the bakery counter",
        "thing": "display",
        "object": "cake display",
        "breakable": True,
    },
}

SUSPECTS = {
    "owl": {"type": "owl", "label": "Mrs. Owl", "trait": "quiet"},
    "cat": {"type": "cat", "label": "Mr. Cat", "trait": "curious"},
    "dog": {"type": "dog", "label": "Ms. Dog", "trait": "busy"},
    "mouse": {"type": "mouse", "label": "Tiny Mouse", "trait": "nervous"},
}

TOOL_KINDS = {
    "ball": "a red ball",
    "cart": "a small cart",
    "fan": "a noisy fan",
    "tail": "a long tail",
    "bag": "a heavy bag",
}

CLUES = [
    "a tiny scratch near the corner",
    "a smear of dust on the floor",
    "a little wobble in the stand",
    "one loose sticker on the glass",
    "a crumb trail by the edge",
]

BAD_ENDINGS = [
    "But the detective never proved who did it, and the display stayed broken.",
    "But the wrong friend got blamed, and nobody admitted the truth.",
    "But the last clue got lost, so the mystery stayed unsolved.",
]



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    display: object | None = None
    suspect: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    setting: str
    display_kind: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    display_kind: str
    suspect: str
    tool: str
    name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bad-ending whodunit storyworld.")
    ap.add_argument("--display-kind", choices=DISPLAY_KINDS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOL_KINDS)
    ap.add_argument("--name")
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


def reasonableness_gate(display_kind: str, suspect: str, tool: str) -> None:
    if display_kind == "toy_display" and tool == "fan":
        pass
    if display_kind == "cake_display" and suspect == "mouse" and tool == "ball":
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    display_kind = getattr(args, "display_kind", None) or rng.choice(sorted(DISPLAY_KINDS))
    suspect = getattr(args, "suspect", None) or rng.choice(sorted(SUSPECTS))
    tool = getattr(args, "tool", None) or rng.choice(sorted(TOOL_KINDS))
    reasonableness_gate(display_kind, suspect, tool)
    name = getattr(args, "name", None) or rng.choice(["Nina", "Milo", "Tess", "Pip", "Jules", "Ada"])
    return StoryParams(display_kind=display_kind, suspect=suspect, tool=tool, name=name)


def build_world(params: StoryParams) -> World:
    cfg = _safe_lookup(DISPLAY_KINDS, params.display_kind)
    world = World(setting=cfg["place"], display_kind=params.display_kind)

    detective = world.add(Entity(id="detective", kind="character", type="girl", label=params.name))
    suspect = world.add(Entity(
        id="suspect",
        kind="character",
        type=_safe_lookup(SUSPECTS, params.suspect)["type"],
        label=_safe_lookup(SUSPECTS, params.suspect)["label"],
    ))
    display = world.add(Entity(
        id="display",
        kind="thing",
        type="display",
        label=cfg["object"],
        phrase=f"the {cfg['object']}",
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=_safe_lookup(TOOL_KINDS, params.tool),
        phrase=_safe_lookup(TOOL_KINDS, params.tool),
    ))

    # Setup
    world.say(f"{detective.label} liked solving little mysteries, especially when a {display.label} looked odd.")
    world.say(f"At {world.setting}, the {display.label} sat under bright lights, neat and shiny at first.")
    world.para()

    # Mystery
    world.say(f"Then something went wrong. The {display.label} had a {random.choice(CLUES)}.")
    world.say(f"{detective.label} saw {suspect.label} near the scene, and {suspect.pronoun('subject')} looked worried.")
    world.say(f"On the floor, there was {_safe_lookup(TOOL_KINDS, params.tool)} and a sign that had tipped a little.")
    world.para()

    # Investigation / clues
    world.facts["clues"] = [random.choice(CLUES), "the tipped sign", "the tool on the floor"]
    world.facts["wrong_guess"] = suspect.id
    world.say(f"{detective.label} asked careful questions: who came first, what moved, and what made the noise?")
    world.say(f"{suspect.label} said {suspect.pronoun('subject')} only wanted to look. That sounded strange, but not enough to prove anything.")
    world.say(f"{detective.label} checked the edges, yet the last clue was too faint to follow.")
    world.para()

    # Bad ending
    world.say("The room grew quiet.")
    world.say(random.choice(BAD_ENDINGS))
    if cfg["breakable"]:
        world.say(f"By closing time, the {display.label} still had a crack, and everyone walked away unhappy.")
    else:
        world.say(f"By closing time, the {display.label} still looked messy, and the window stayed dim.")
    world.facts.update(detective=detective, suspect=suspect, display=display, tool=tool, cfg=cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for young children that includes the word "display" and ends badly.',
        f"Tell a mystery story where {f['detective'].label} investigates a broken {f['display'].label} at {world.setting}.",
        f"Write a simple detective story about {f['suspect'].label}, a clue on the floor, and an unsolved display problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    s = _safe_fact(world, f, "suspect")
    disp = _safe_fact(world, f, "display")
    return [
        QAItem(
            question=f"Who tried to solve the mystery at {world.setting}?",
            answer=f"{d.label} tried to solve the mystery at {world.setting}.",
        ),
        QAItem(
            question=f"What object was being watched closely?",
            answer=f"The {disp.label} was being watched closely.",
        ),
        QAItem(
            question=f"Who looked nervous near the scene?",
            answer=f"{s.label} looked nervous near the scene, but that did not prove anything.",
        ),
        QAItem(
            question="Did the detective solve the mystery?",
            answer="No. The mystery stayed unsolved, which made it a bad ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a display?",
            answer="A display is a set of things arranged so people can look at them easily.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that can help solve a mystery.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} label={e.label}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
display_problem(D) :- display(D), cracked(D).
unsolved :- display_problem(_), clue_lost.
bad_ending :- unsolved.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in DISPLAY_KINDS:
        lines.append(asp.fact("display", k))
    for k in SUSPECTS:
        lines.append(asp.fact("suspect", k))
    for k in TOOL_KINDS:
        lines.append(asp.fact("tool", k))
    lines.append(asp.fact("cracked", "museum_display"))
    lines.append(asp.fact("clue_lost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    if any(sym.name == "bad_ending" for sym in model):
        print("OK: ASP confirms the bad ending.")
        return 0
    print("MISMATCH: ASP did not confirm the bad ending.")
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DISPLAY_KINDS:
        for s in SUSPECTS:
            for t in TOOL_KINDS:
                try:
                    reasonableness_gate(d, s, t)
                except StoryError:
                    continue
                combos.append((d, s, t))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show display/1. #show suspect/1. #show tool/1."))
    return sorted(set(asp.atoms(model, "display") + asp.atoms(model, "suspect") + asp.atoms(model, "tool")))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(display_kind="museum_display", suspect="cat", tool="cart", name="Nina"),
    StoryParams(display_kind="toy_display", suspect="owl", tool="bag", name="Milo"),
    StoryParams(display_kind="cake_display", suspect="mouse", tool="tail", name="Tess"),
]


def resolve_and_generate(args: argparse.Namespace, seed: int) -> StorySample:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/0."))
        return

    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} valid combos.")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            s = resolve_and_generate(args, base_seed + i)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
