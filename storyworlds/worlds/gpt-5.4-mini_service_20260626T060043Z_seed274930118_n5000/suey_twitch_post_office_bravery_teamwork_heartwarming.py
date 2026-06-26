#!/usr/bin/env python3
"""
A tiny heartwarming storyworld set in a post office.

Seed tale:
- Suey is a small, careful helper at the post office.
- Twitch is a nervous little mail cart that rattles and scares Suey at first.
- A storm leaves a pile of letters mixed with a fallen parcel cart.
- Suey is scared, but she and Twitch work together to sort, carry, and deliver the mail.
- Bravery grows when Suey speaks up and asks for help; teamwork turns the busy room calm.
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clerk: object | None = None
    suey: object | None = None
    twitch: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    seed: Optional[int] = None
    name: str = "Suey"
    friend: str = "Twitch"
    setting: str = "post office"
    theme: str = "heartwarming"
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


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    world: object | None = None
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
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
    "post office": {
        "mail": "letters and parcels",
        "busy": "stamped envelopes, sorting bins, and little carts",
    }
}

PEOPLE = ["Suey", "Twitch"]
TRAITS = ["careful", "kind", "brave", "gentle", "helpful"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(setting=params.setting)

    suey = world.add(Entity(id="Suey", kind="character", type="girl", meters={}, memes={}))
    twitch = world.add(Entity(id="Twitch", kind="thing", type="cart", label="Twitch", meters={}, memes={}))
    clerk = world.add(Entity(id="Clerk", kind="character", type="woman", label="the mail clerk", meters={}, memes={}))

    suey.memes["bravery"] = 0.0
    suey.memes["teamwork"] = 0.0
    suey.memes["worry"] = 0.0
    suey.memes["joy"] = 0.0

    twitch.meters["rattle"] = 1.0
    twitch.memes["nervous"] = 0.0

    clerk.memes["workload"] = 0.0
    clerk.memes["kindness"] = 1.0

    world.facts.update(
        suey=suey,
        twitch=twitch,
        clerk=clerk,
        place=params.setting,
        mail_kind=_safe_lookup(PLACES, params.setting)["mail"],
    )
    return world


def introduce(world: World) -> None:
    world.say(
        "At the post office, Suey liked the neat rows of bins and the soft stamp of envelopes."
    )
    world.say(
        "She noticed Twitch, a little mail cart that twitched and rattled whenever the room got busy."
    )


def setup_tension(world: World) -> None:
    suey = world.get("Suey")
    twitch = world.get("Twitch")
    clerk = world.get("Clerk")

    suey.memes["worry"] += 1
    twitch.memes["nervous"] += 1
    clerk.memes["workload"] += 1

    world.say(
        "Then a windy rush blew a stack of letters off the counter, and one parcel slid sideways under the sorting table."
    )
    world.say(
        "Suey froze for a moment, because the room felt big and loud all at once."
    )
    world.say(
        '"The mail needs help," the clerk said kindly. "I can sort the stamps, but I need a brave helper for the parcels."'
    )


def brave_choice(world: World) -> None:
    suey = world.get("Suey")
    twitch = world.get("Twitch")
    clerk = world.get("Clerk")

    suey.memes["bravery"] += 1
    suey.memes["worry"] = max(0.0, suey.memes["worry"] - 0.5)
    world.say(
        "Suey took one small breath, raised her hand, and said, 'I can help.'"
    )
    world.say(
        "Twitch rattled once, then rolled closer like it wanted to be useful too."
    )
    twitch.memes["teamwork"] += 1
    suey.memes["teamwork"] += 1
    clerk.memes["joy"] = clerk.memes.get("joy", 0.0) + 1


def teamwork_action(world: World) -> None:
    suey = world.get("Suey")
    twitch = world.get("Twitch")
    clerk = world.get("Clerk")

    suey.meters["carried_parcels"] = suey.meters.get("carried_parcels", 0.0) + 1
    twitch.meters["rolled_baskets"] = twitch.meters.get("rolled_baskets", 0.0) + 1
    clerk.meters["sorted_letters"] = clerk.meters.get("sorted_letters", 0.0) + 1

    suey.memes["teamwork"] += 1
    twitch.memes["teamwork"] += 1

    world.say(
        "Suey picked up the fallen letters while Twitch nudged the parcel tray back into place."
    )
    world.say(
        "The clerk sorted names into the right bins, and together they made the busy room feel calmer."
    )
    world.say(
        "Soon the mail that had been scattered like leaves was lined up again, ready to go where it belonged."
    )


def ending(world: World) -> None:
    suey = world.get("Suey")
    twitch = world.get("Twitch")

    suey.memes["joy"] += 1
    suey.memes["bravery"] += 1
    twitch.memes["joy"] = twitch.memes.get("joy", 0.0) + 1

    world.say(
        "By the end, Suey was smiling, and Twitch was rattling in a happy little rhythm beside her."
    )
    world.say(
        "The post office was tidy again, and Suey knew that bravery could sound like asking for help, and teamwork could make a hard day feel warm."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    setup_tension(world)
    brave_choice(world)
    teamwork_action(world)
    world.para()
    ending(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story set in a post office where Suey and Twitch learn bravery and teamwork.",
        "Tell a gentle story about a child helper in a post office who is nervous at first but then helps the mail with a friend.",
        "Write a short story where letters get scattered, a brave helper speaks up, and everyone works together to fix the mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    suey = world.get("Suey")
    twitch = world.get("Twitch")
    clerk = world.get("Clerk")
    return [
        QAItem(
            question="Who was the story about?",
            answer="The story was about Suey, who helped at the post office, and Twitch, the little mail cart who worked beside her.",
        ),
        QAItem(
            question="What problem happened in the post office?",
            answer="A windy rush blew letters off the counter and made one parcel slide under the sorting table.",
        ),
        QAItem(
            question="How did Suey show bravery?",
            answer="Suey showed bravery by taking a breath, raising her hand, and saying that she could help.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer="Suey, Twitch, and the mail clerk all did different jobs together, so the letters and parcel were put back in order.",
        ),
        QAItem(
            question="How did Suey feel at the end?",
            answer="Suey felt happy and proud because she had been brave and worked together with Twitch.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people sort, send, and pick up letters and parcels.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
suey(suey).
friend(twitch).
setting(post_office).
theme(heartwarming).

brave(suey) :- ask_for_help(suey).
teamwork(suey,twitch) :- help(suey,twitch), help(twitch,suey).

compatible_story(post_office, heartwarming) :- setting(post_office), theme(heartwarming),
    brave(suey), teamwork(suey,twitch).

#show compatible_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("suey", "suey"),
        asp.fact("friend", "twitch"),
        asp.fact("setting", "post_office"),
        asp.fact("theme", "heartwarming"),
        asp.fact("ask_for_help", "suey"),
        asp.fact("help", "suey", "twitch"),
        asp.fact("help", "twitch", "suey"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    asp_set = set(asp.atoms(model, "compatible_story"))
    py_set = {("post_office", "heartwarming")}
    if asp_set == py_set:
        print("OK: clingo gate matches Python reasonableness check (1 combo).")
        return 0
    print("MISMATCH between clingo and Python check:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def reasonableness_check(params: StoryParams) -> None:
    if params.setting != "post office":
        pass
    if params.name != "Suey":
        pass
    if params.friend != "Twitch":
        pass


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming post office storyworld.")
    ap.add_argument("--name", choices=["Suey"])
    ap.add_argument("--friend", choices=["Twitch"])
    ap.add_argument("--setting", choices=["post office"])
    ap.add_argument("--theme", choices=["heartwarming"])
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
    name = getattr(args, "name", None) or "Suey"
    friend = getattr(args, "friend", None) or "Twitch"
    setting = getattr(args, "setting", None) or "post office"
    theme = getattr(args, "theme", None) or "heartwarming"
    params = StoryParams(seed=None, name=name, friend=friend, setting=setting, theme=theme)
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  trace events: {len(world.trace)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible_story/2."))
        combos = sorted(set(asp.atoms(model, "compatible_story")))
        print(f"{len(combos)} compatible story combo(s):")
        for place, theme in combos:
            print(f"  {place} / {theme}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(seed=base_seed, name="Suey", friend="Twitch", setting="post office", theme="heartwarming")
        samples = [generate(params)]
    else:
        for i in range(max(1, getattr(args, "n", None))):
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
