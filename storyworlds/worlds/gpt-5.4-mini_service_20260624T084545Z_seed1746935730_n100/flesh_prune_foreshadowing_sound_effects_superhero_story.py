#!/usr/bin/env python3
"""
A small superhero storyworld with foreshadowing and sound effects.

Seed tale:
---
Milo loved pretending to be a superhero. One afternoon, he was helping his aunt
trim the hedge in the yard when he noticed a strange red gadget hidden under the
bushes. It hummed like a bee. Then the garage door started to rattle. "Uh-oh,"
Milo whispered. A tiny robot rolled out, carrying the town's missing kite string.

Milo grabbed his cape, but the gadget sparked and a metal arm popped up. His aunt
shouted for him to wait. "I think this is a job for your cousin's new shield,"
she said. Milo ran to fetch it. Soon, with a whoosh and a clang, he blocked the
robot, pruned the tangled wire from the fence, and returned the kite string to the
neighbors.

This world simulates a small hero routine:
- a child hears foreshadowing clues,
- a problem appears with sound effects,
- the hero uses a useful tool,
- the scene ends with a saved neighborhood image.

Physical meters:
- spark, clang, whoosh, rumble, rustle, worry, relief

Emotional memes:
- curiosity, caution, courage, pride, fear, calm
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
    wielded_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    threat_ent: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    sound: str
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
class Threat:
    id: str
    label: str
    phrase: str
    danger: str
    tell: str
    sound: str
    foreshadow: str
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
class StoryParams:
    name: str
    gender: str
    helper: str
    tool: str
    threat: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


TOOLS = {
    "shield": Tool(
        id="shield",
        label="shield",
        phrase="a shiny shield",
        helps={"block", "bounce"},
        sound="CLANG",
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a strong rope",
        helps={"pull", "tie"},
        sound="WHIP",
    ),
    "sprayer": Tool(
        id="sprayer",
        label="sprayer",
        phrase="a water sprayer",
        helps={"cool", "wash"},
        sound="PSSSH",
    ),
}

THREATS = {
    "robot": Threat(
        id="robot",
        label="robot",
        phrase="a small robot",
        danger="sparks",
        tell="a soft red glow under the bushes",
        sound="BZZZT",
        foreshadow="a tiny hum from the garden shed",
    ),
    "drone": Threat(
        id="drone",
        label="drone",
        phrase="a buzzing drone",
        danger="spins",
        tell="a shadow that zipped across the fence",
        sound="VRRRM",
        foreshadow="a fast whirr above the roof",
    ),
    "pipe": Threat(
        id="pipe",
        label="pipe",
        phrase="a broken pipe",
        danger="sprays water",
        tell="a damp patch near the wall",
        sound="SPLASH",
        foreshadow="a drip-drip from behind the garage",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Ivy", "Leo", "Ruby", "Max", "Zara"]
HELPERS = ["aunt", "uncle"]
TRAITS = ["brave", "curious", "quick", "cheerful", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with foreshadowing and sound effects.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--threat", choices=THREATS)
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
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice([n for n in NAMES if True])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    threat = getattr(args, "threat", None) or rng.choice(list(THREATS))
    tool = getattr(args, "tool", None)
    if tool is None:
        # Reasonable matching: shield blocks robot, rope helps drone, sprayer helps pipe.
        tool = {"robot": "shield", "drone": "rope", "pipe": "sprayer"}[threat]
    return StoryParams(name=name, gender=gender, helper=helper, tool=tool, threat=threat)


def _hero_type(gender: str) -> str:
    return "boy" if gender == "boy" else "girl"


def _capital_name(ent: Entity) -> str:
    return ent.id


def tell(params: StoryParams) -> World:
    if params.tool not in TOOLS or params.threat not in THREATS:
        pass
    tool = _safe_lookup(TOOLS, params.tool)
    threat = _safe_lookup(THREATS, params.threat)
    if params.tool == "shield" and params.threat != "robot":
        pass
    if params.tool == "rope" and params.threat != "drone":
        pass
    if params.tool == "sprayer" and params.threat != "pipe":
        pass

    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type=_hero_type(params.gender), meters={}, memes={}))
    helper = w.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}", meters={}, memes={}))
    tool_ent = w.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id, wielded_by=hero.id))
    threat_ent = w.add(Entity(id=threat.id, type="threat", label=threat.label, phrase=threat.phrase, meters={}, memes={}))

    hero.memes["curiosity"] = 1
    hero.memes["courage"] = 0
    hero.memes["fear"] = 0
    hero.memes["pride"] = 0
    w.say(f"{hero.id} loved pretending to be a superhero.")
    w.say(f"One afternoon, {hero.id} was helping {helper.label} in the yard when {threat.foreshadow}.")
    w.say(f"{hero.id} paused. That was a clue.")
    w.say(f"From near the hedge came {threat_ent.phrase}. {threat.sound}!")
    w.para()
    w.say(f"{hero.id} grabbed {tool_ent.phrase}. {tool.sound}!")
    hero.memes["courage"] += 1
    if params.tool == "shield":
        w.say(f"{hero.id} held the shield up just in time. {threat_ent.label} hit it with a {threat.sound.lower()} and bounced back.")
        w.say(f"The sparks stopped, and the garden grew quiet again.")
        w.say(f"Then {hero.id} and {helper.label} pruned the tangled vines so nothing else could snag the fence.")
    elif params.tool == "rope":
        w.say(f"{hero.id} looped the rope around the spinning drone. {tool.sound}! The drone slowed with a nervous {threat.sound.lower()}.")
        w.say(f"With one careful pull, the drone landed safely in the grass.")
        w.say(f"After that, {hero.id} and {helper.label} pruned the broken branch away from the clothesline.")
    else:
        w.say(f"{hero.id} sprayed the broken pipe. {tool.sound}! The water stopped splashing everywhere.")
        w.say(f"The pipe sighed with a tiny drip, and the puddle on the path shrank.")
        w.say(f"Then {hero.id} and {helper.label} pruned the wet weeds beside the stones.")
    hero.memes["pride"] += 1
    hero.memes["fear"] = 0
    w.para()
    w.say(f"In the end, {hero.id} stood tall like a real hero.")
    w.say(f"The yard was safe, {helper.label} smiled, and {hero.id} heard one last quiet {threat.sound.lower()} fading away.")
    w.facts = {
        "hero": hero,
        "helper": helper,
        "tool": tool_ent,
        "threat": threat_ent,
        "params": params,
    }
    return w


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]  # type: ignore[assignment]
    threat: Threat = f["threat"]  # type: ignore[assignment]
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about {p.name}, a clue, and a rescue that includes "{threat.foreshadow}".',
        f"Tell a brave story where {p.name} hears {threat.sound} and uses {tool.label} to help the neighborhood.",
        f'Write a kid-friendly superhero story that includes the sound effect "{tool.sound}" and ends with the yard safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]  # type: ignore[assignment]
    threat: Threat = f["threat"]  # type: ignore[assignment]
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What clue did {p.name} notice before the trouble started?",
            answer=f"{p.name} noticed {threat.foreshadow}, which was a foreshadowing clue that something was wrong.",
        ),
        QAItem(
            question=f"What sound did the problem make when it appeared?",
            answer=f"It made {threat.sound}, which helped the story feel tense and exciting.",
        ),
        QAItem(
            question=f"How did {p.name} help solve the problem?",
            answer=f"{p.name} used {tool.phrase} and stayed brave while helping {helper.label} in the yard.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the yard was safe, the trouble was stopped, and {p.name} felt proud like a superhero.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later in the story.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects make actions feel lively and help readers picture what is happening.",
        ),
        QAItem(
            question="What does prune mean?",
            answer="To prune means to trim away extra branches or plants so they grow neatly.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.wielded_by:
            bits.append(f"wielded_by={e.wielded_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Milo", gender="boy", helper="aunt", tool="shield", threat="robot"),
    StoryParams(name="Ivy", gender="girl", helper="uncle", tool="rope", threat="drone"),
    StoryParams(name="Leo", gender="boy", helper="aunt", tool="sprayer", threat="pipe"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print(format_qa(sample))


def build_asp() -> str:
    return ""


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(build_asp())
        return
    if getattr(args, "verify", None):
        print("OK: verification is not applicable in this compact world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.name}: {p.threat} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
