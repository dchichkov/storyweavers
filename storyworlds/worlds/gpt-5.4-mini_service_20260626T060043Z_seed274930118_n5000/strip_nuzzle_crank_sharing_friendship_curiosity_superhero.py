#!/usr/bin/env python3
"""
storyworlds/worlds/strip_nuzzle_crank_sharing_friendship_curiosity_superhero.py
===============================================================================

A tiny superhero storyworld about sharing, friendship, and curiosity.

Seed tale:
---
Milo liked to dress up as a superhero. He had a red cape, a silver mask, and a small
crank-driven gadget that made his toy rocket hum. One afternoon, Milo found a tiny
mystery strip tucked behind a park bench. He wanted to strip it open right away and
see what was inside, but his friend Nina suggested they share the job and look
carefully together. When they gently nuzzled the strip loose, they found a lost note
that helped them return a humming gadget to a cranky inventor. Milo felt proud that
their curiosity and friendship had turned the day into a rescue.

This world models:
- a hero with a cape and gadget
- a shared mystery strip that can be opened or kept closed
- curiosity that invites investigation
- sharing that helps two friends cooperate
- crankiness that eases when the lost item is returned
- a superhero-style rescue ending with a bright emotional turn
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

ASP_RULES = r"""
hero(h1).
friend(f1).
gadget(g1).
strip(s1).
curiosity(cu1).
sharing(sh1).
friendship(fr1).

curious_hero(H) :- hero(H).
shared_plan(H,F) :- hero(H), friend(F), sharing(_), friendship(_).
good_outcome :- shared_plan(H,F), curious_hero(H).
rescue :- good_outcome.
#show good_outcome/0.
#show rescue/0.
"""

NAME_POOL = ["Milo", "Nina", "Ari", "Jules", "Ivy", "Noah", "Piper", "Leo"]
FRIEND_POOL = ["Nina", "Ari", "Jules", "Ivy", "Noah", "Piper", "Leo", "Milo"]
SETTING_POOL = [
    "the park",
    "the rooftop garden",
    "the comic shop alley",
    "the little city plaza",
    "the playground by the fountain",
]
CAPE_COLORS = ["red", "blue", "gold", "green", "silver"]
GADGETS = [
    ("crank lantern", "a tiny crank lantern"),
    ("crank radio", "a pocket crank radio"),
    ("toy rocket", "a bright toy rocket"),
    ("signal wheel", "a spinning signal wheel"),
]
MOODS = ["curious", "kind", "brave", "cheerful", "gentle"]



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

@dataclass
class Character:
    id: str
    role: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self) -> str:
        return "they"
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
class Strip:
    id: str
    label: str = "mystery strip"
    opened: bool = False
    owner: Optional[str] = None
    strip: object | None = None
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
class Gadget:
    id: str
    label: str
    humming: bool = False
    owner: Optional[str] = None
    lost: bool = False
    gadget: object | None = None
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
    name: str
    friend: str
    place: str
    cape_color: str
    gadget_kind: str
    mood: str
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


@dataclass
class World:
    hero: Character
    friend: Character
    strip: Strip
    gadget: Gadget
    place: str
    cape_color: str
    mood: str
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about sharing, friendship, and curiosity.")
    ap.add_argument("--name", choices=NAME_POOL)
    ap.add_argument("--friend", choices=FRIEND_POOL)
    ap.add_argument("--place", choices=SETTING_POOL)
    ap.add_argument("--cape-color", choices=CAPE_COLORS)
    ap.add_argument("--gadget-kind", choices=[g[0] for g in GADGETS])
    ap.add_argument("--mood", choices=MOODS)
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "h1"),
        asp.fact("friend", "f1"),
        asp.fact("strip", "s1"),
        asp.fact("sharing", "sh1"),
        asp.fact("friendship", "fr1"),
        asp.fact("curiosity", "cu1"),
        asp.fact("gadget", "g1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_outcome/0.\n#show rescue/0."))
    shown = {str(a) for a in model}
    if "good_outcome" in shown and "rescue" in shown:
        print("OK: ASP rules produce the expected superhero rescue outcome.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected outcome.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(NAME_POOL)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_POOL if n != name])
    place = getattr(args, "place", None) or rng.choice(SETTING_POOL)
    cape_color = getattr(args, "cape_color", None) or rng.choice(CAPE_COLORS)
    gadget_kind = getattr(args, "gadget_kind", None) or rng.choice([g[0] for g in GADGETS])
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    if friend == name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        name=name,
        friend=friend,
        place=place,
        cape_color=cape_color,
        gadget_kind=gadget_kind,
        mood=mood,
    )


def make_world(params: StoryParams) -> World:
    gadget_label = dict(GADGETS)[params.gadget_kind]
    hero = Character(
        id=params.name,
        role="hero",
        label=f"a {params.mood} hero with a {params.cape_color} cape",
        meters={"courage": 1.0, "sharing": 0.0},
        memes={"curiosity": 1.0, "joy": 1.0},
    )
    friend = Character(
        id=params.friend,
        role="friend",
        label="a loyal friend",
        meters={"help": 1.0},
        memes={"friendship": 1.0, "curiosity": 0.5},
    )
    strip = Strip(id="strip", owner=None, opened=False)
    gadget = Gadget(id="gadget", label=gadget_label, humming=True, owner=None, lost=True)
    return World(
        hero=hero,
        friend=friend,
        strip=strip,
        gadget=gadget,
        place=params.place,
        cape_color=params.cape_color,
        mood=params.mood,
    )


def tell(world: World) -> None:
    h = world.hero
    f = world.friend
    s = world.strip
    g = world.gadget

    world.say(
        f"{h.id} was a {world.mood} little superhero with a {world.cape_color} cape and a brave smile."
    )
    world.say(
        f"{h.id} loved curiosity, and {f.id} loved friendship, so they often solved tiny city puzzles together."
    )
    world.say(
        f"One afternoon at {world.place}, they found a thin mystery strip hiding near a bench."
    )

    world.para()
    h.memes["curiosity"] += 1.0
    world.say(
        f"{h.id} wanted to strip it open at once, but {f.id} held up a hand and said they should share the job."
    )
    h.meters["sharing"] += 1.0
    f.meters["sharing"] += 1.0
    world.say(
        f"So the two friends knelt together and gently nuzzled the strip loose, one careful inch at a time."
    )
    s.opened = True

    world.say(
        f"Inside, they found a tiny note that pointed to a lost {g.label} humming behind a flower pot."
    )
    g.lost = False
    g.owner = f.id
    world.say(
        f"The note also showed that the {g.label} belonged to a cranky inventor who had been searching everywhere."
    )

    world.para()
    world.say(
        f"{h.id} and {f.id} hurried to the inventor's workshop and returned the humming gadget."
    )
    world.say(
        f"At first the inventor looked cranky, but then the old face softened into a warm grin."
    )
    world.say(
        f'"You found it by sharing and looking closely," the inventor said. "That is true hero work."'
    )
    world.say(
        f"{h.id} felt taller than the rooftops, because curiosity had led the way and friendship had carried them home."
    )

    world.facts.update(
        hero=h,
        friend=f,
        strip=s,
        gadget=g,
        place=world.place,
        opened=s.opened,
        returned=not g.lost,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short superhero story for a young child about "{world.hero.id}" and "{world.friend.id}" at {world.place}.',
        f"Tell a gentle rescue story that includes sharing, friendship, curiosity, and a mystery strip.",
        f"Write a child-friendly superhero adventure where a cranky inventor gets a lost gadget back.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    f = world.friend
    g = world.gadget
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {h.id}, the child with the {world.cape_color} cape.",
        ),
        QAItem(
            question=f"What did {h.id} and {f.id} do with the mystery strip?",
            answer=f"They shared the task and gently nuzzled the strip loose instead of rushing.",
        ),
        QAItem(
            question=f"What did they find hidden inside the strip's secret?",
            answer=f"They found a note that led them to the lost {g.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They returned the gadget to the cranky inventor, and the inventor became happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people help, use, or enjoy something with you.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind connection between people who care about each other and help each other.",
        ),
        QAItem(
            question="What does cranky mean?",
            answer="Cranky means grumpy or hard to please.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"hero: meters={world.hero.meters} memes={world.hero.memes}")
    lines.append(f"friend: meters={world.friend.meters} memes={world.friend.memes}")
    lines.append(f"strip opened={world.strip.opened}")
    lines.append(f"gadget lost={world.gadget.lost} owner={world.gadget.owner}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Milo", friend="Nina", place="the park", cape_color="red", gadget_kind="toy rocket", mood="curious"),
    StoryParams(name="Ari", friend="Ivy", place="the rooftop garden", cape_color="blue", gadget_kind="crank lantern", mood="kind"),
    StoryParams(name="Leo", friend="Piper", place="the little city plaza", cape_color="gold", gadget_kind="signal wheel", mood="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
        print(asp_program("#show good_outcome/0.\n#show rescue/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_outcome/0.\n#show rescue/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
