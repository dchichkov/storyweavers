#!/usr/bin/env python3
"""
A bedtime-story world about a child, a nummy treat, a captivated listener,
and a small moral choice that lands softly at night.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)
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
class Treat:
    id: str
    label: str
    phrase: str
    mess: str
    smell: str
    value: str
    time: str
    captivate_word: str = "captivate"
    nummy_word: str = "nummy"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    treat: str
    hero_name: str
    hero_gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"story", "snack", "tidy"}),
    "nursery": Setting(place="the nursery", affords={"story", "snack", "tidy"}),
    "windowseat": Setting(place="the window seat", affords={"story", "snack"}),
}

TREATS = {
    "cookie": Treat(
        id="cookie",
        label="cookie",
        phrase="a warm nummy cookie",
        mess="crumbs",
        smell="sweet and buttery",
        value="sharing",
        time="bedtime",
        captivate_word="captivate",
        nummy_word="nummy",
    ),
    "banana": Treat(
        id="banana",
        label="banana",
        phrase="a nummy banana slice",
        mess="peels",
        smell="soft and sweet",
        value="kindness",
        time="bedtime",
        captivate_word="captivate",
        nummy_word="nummy",
    ),
    "toast": Treat(
        id="toast",
        label="toast",
        phrase="a nummy toast square",
        mess="crumbs",
        smell="warm and cozy",
        value="care",
        time="bedtime",
        captivate_word="captivate",
        nummy_word="nummy",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ella", "Ruby", "Ava"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Theo", "Milo", "Ben"]


class StoryWorld(World):
    pass


def tell(setting: Setting, treat: Treat, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    snack = world.add(Entity(
        id=treat.id,
        type=treat.label,
        label=treat.label,
        phrase=treat.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=False,
    ))

    hero.memes["sleepy"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["moral_value"] = 0.0
    hero.meters["crumbs"] = 0.0
    snack.meters["crumbs"] = 0.0

    world.say(
        f"{hero.id} had a sleepy, cozy night in {setting.place}, where even little whispers felt like blankets."
    )
    world.say(
        f"The room smelled {treat.smell}, and {treat.nummy_word} snacks always seemed to {treat.captivate_word} {hero.id}'s attention."
    )
    world.say(
        f"{hero.id} loved bedtime stories, especially the kind where someone was brave enough to choose {treat.value}."
    )

    world.para()
    world.say(
        f"Long ago, on another quiet night, {hero.id} had tiptoed toward {parent.label}'s table and spotted {treat.phrase}."
    )
    hero.memes["wonder"] += 1
    hero.memes["desire"] += 1
    world.say(
        f"It looked so {treat.nummy_word} that {hero.id} could hardly think of anything else."
    )
    world.say(
        f"{hero.id} wanted to take a big bite before asking, because the treat seemed to glow like a tiny moon."
    )

    world.para()
    world.say(
        f"{parent.label.capitalize()} noticed the hungry look and gently said, \"First we share, then we tidy.\""
    )
    hero.memes["conflict"] = 1.0
    world.say(
        f"{hero.id} paused, because the treat was tempting, but the rule was simple and kind."
    )

    world.para()
    world.say(
        f"{hero.id} remembered a flashback from the afternoon: a crumb spill, a sticky table, and a sad wipe with a cloth."
    )
    hero.memes["flashback"] = 1.0
    world.say(
        f"That memory helped {hero.id} choose better this time."
    )
    hero.memes["moral_value"] = 1.0
    world.say(
        f"So {hero.id} split the {treat.label} in half, gave one piece to {parent.label}, and waited for the other with a happy smile."
    )
    snack.meters["crumbs"] += 0.0
    hero.meters["crumbs"] += 0.0

    world.para()
    world.say(
        f"After the snack, {hero.id} wiped the little table clean and climbed into bed."
    )
    hero.memes["sleepy"] += 1.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{parent.label.capitalize()} tucked the blanket under {hero.pronoun('possessive')} chin and read a soft story about sharing."
    )
    world.say(
        f"In the end, the room was still, the snack was gone, and {hero.id} felt warm inside because {hero.pronoun('subject')} had chosen {treat.value}."
    )

    world.facts.update(hero=hero, parent=parent, treat=snack, treat_cfg=treat, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    treat = _safe_fact(world, f, "treat_cfg")
    return [
        f'Write a bedtime story for a small child where a {treat.label} can "{treat.captivate_word}" attention and the child learns a moral value.',
        f"Tell a gentle story about {hero.id}, a {treat.nummy_word} treat, and a flashback that helps make a kinder choice.",
        f"Write a cozy bedtime tale that includes the words \"captivate\" and \"nummy\" and ends with sharing and tidying.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, treat = f["hero"], f["parent"], f["treat"]
    cfg = _safe_fact(world, f, "treat_cfg")
    return [
        QAItem(
            question=f"What did {hero.id} keep thinking about at bedtime?",
            answer=f"{hero.id} kept thinking about {cfg.phrase}, because it was so {cfg.nummy_word} and could {cfg.captivate_word} attention.",
        ),
        QAItem(
            question=f"What did {parent.label} ask {hero.id} to do before enjoying the snack?",
            answer=f"{parent.label.capitalize()} asked {hero.id} to share first and tidy up after eating.",
        ),
        QAItem(
            question=f"What helped {hero.id} make the kinder choice?",
            answer=f"A flashback to an earlier crumb spill helped {hero.id} remember the moral value of sharing and cleaning up.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for something to captivate you?",
            answer="If something captivates you, it grabs your attention so much that it is hard to look away or think about anything else.",
        ),
        QAItem(
            question="What does nummy mean?",
            answer="Nummy means tasty in a child-friendly way, like when food seems extra yummy and cozy.",
        ),
        QAItem(
            question="Why do people tidy up after a snack?",
            answer="People tidy up after a snack so crumbs and sticky spots do not stay on the table or floor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(
            f"  {e.id:8} ({e.type}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(out)


ASP_RULES = r"""
% A bedtime snack is fitting when it can stir attention and carry a moral lesson.
fit(T) :- treat(T), nummy(T), moral(T).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("nummy", tid))
        lines.append(asp.fact("moral", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_treats() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fit/1."))
    return sorted(set(asp.atoms(model, "fit")))


def asp_verify() -> int:
    py = {("fit", tid) for tid, t in TREATS.items() if t.nummy_word and t.value}
    cl = {("fit", x[0]) for x in asp_reasonable_treats()}
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} treats).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with captivate, nummy, flashback, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    treat = getattr(args, "treat", None) or rng.choice(list(TREATS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, treat=treat, hero_name=name, hero_gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TREATS, params.treat), params.hero_name, params.hero_gender, params.parent)
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
        print(format_qa(sample))


CURATED = [
    StoryParams(place="bedroom", treat="cookie", hero_name="Mia", hero_gender="girl", parent="mother"),
    StoryParams(place="nursery", treat="banana", hero_name="Leo", hero_gender="boy", parent="father"),
    StoryParams(place="windowseat", treat="toast", hero_name="Nora", hero_gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show fit/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show fit/1."))
        print(sorted(set(asp.atoms(model, "fit"))))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            i += 1
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
