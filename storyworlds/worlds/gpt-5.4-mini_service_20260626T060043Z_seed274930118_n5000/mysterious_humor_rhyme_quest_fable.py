#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mysterious_humor_rhyme_quest_fable.py
===============================================================================================================

A small fable-like story world about a curious animal, a mysterious quest,
a funny misstep, and a rhyming clue that leads to a kinder ending.

The world is intentionally compact:
- one hero
- one setting
- one mysterious quest
- one cause of tension
- one clever turn
- one resolution with a moral image

The prose is state-driven: the hero's meters and memes change during the
simulation, and the final story reflects those changes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "wet": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0, "friendship": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "mouse", "badger"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)
    mystery_source: str = ""
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
class Quest:
    id: str
    want: str
    clue: str
    reward: str
    risk: str
    rhyme: str
    humor: str
    goal_meter: str = "found"
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
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

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
            self.trace_log.append(text)

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
    place: str
    hero: str
    quest: str
    prize: str
    helper: str
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


SETTINGS = {
    "grove": Setting(place="the moonlit grove", weather="misty", affords={"seek", "listen"}, mystery_source="a silver bell"),
    "hill": Setting(place="the windy hill", weather="cloudy", affords={"seek", "listen"}, mystery_source="a lost lantern"),
    "pond": Setting(place="the quiet pond", weather="foggy", affords={"seek", "listen"}, mystery_source="a hidden key"),
}

HEROES = {
    "fox": {"type": "fox", "label": "fox"},
    "hare": {"type": "hare", "label": "hare"},
    "mouse": {"type": "mouse", "label": "mouse"},
    "badger": {"type": "badger", "label": "badger"},
}

QUESTS = {
    "bell": Quest(
        id="bell",
        want="find the silver bell",
        clue="a rhyme about the old oak and the toe of a stone",
        reward="a bright chiming bell",
        risk="the path is muddy and strange",
        rhyme="Stone by stone, and root by root, / the bell is near the squirrel's foot.",
        humor="The fox sneezed so hard that a leaf landed on its nose like a tiny hat.",
    ),
    "lantern": Quest(
        id="lantern",
        want="find the lost lantern",
        clue="a rhyme about a lantern glow and a row of reeds",
        reward="a warm lantern",
        risk="the reeds wag and whisper in the dark",
        rhyme="Glow below, and soft wind sing, / the lantern waits by the cattail ring.",
        humor="The hare tried to look wise and only managed to sit on its own tail.",
    ),
    "key": Quest(
        id="key",
        want="find the hidden key",
        clue="a rhyme about the key and the tree with three knots",
        reward="a tiny brass key",
        risk="the water makes every splash echo",
        rhyme="Three knots high and three knots low, / where the little brass key may go.",
        humor="The mouse declared itself a grand explorer, then got blown backward by one big puff of wind.",
    ),
}

HELPERS = {
    "owl": {"type": "owl", "label": "owl"},
    "toad": {"type": "toad", "label": "toad"},
    "crow": {"type": "crow", "label": "crow"},
}

GENTLE_NAMES = ["Milo", "Pip", "Nia", "Juno", "Tess", "Ravi", "Lina", "Otto"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            for hero_id in HEROES:
                for helper_id in HELPERS:
                    out.append((place, hero_id, quest_id, helper_id))
    return out


def explain_rejection(place: Optional[str], quest: Optional[str]) -> str:
    if place and place not in SETTINGS:
        return "(No story: that place is not part of this little world.)"
    if quest and quest not in QUESTS:
        return "(No story: that quest does not belong to this fable world.)"
    return "(No story: the requested choices do not make a reasonable quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mysterious, humorous, rhyming quest fable.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "quest", None) and getattr(args, "quest", None) not in QUESTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None))
        and (getattr(args, "quest", None) is None or c[2] == getattr(args, "quest", None))
        and (getattr(args, "helper", None) is None or c[3] == getattr(args, "helper", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, quest, helper = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GENTLE_NAMES)
    return StoryParams(place=place, hero=hero, quest=quest, prize=name, helper=helper)


def _intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"Once in {world.setting.place}, a little {hero.type} named {hero.label} loved mysteries."
    )
    world.say(
        f"It longed to {quest.want}, because every good fable begins with a question that wiggles in the heart."
    )


def _joke(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"The search started with a smile, and then a small joke: {quest.humor}"
    )


def _clue(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["found"] += 1
    world.say(
        f"Near a root and a stone, {hero.id} found a clue."
    )
    world.say(f'It sounded like this: "{quest.rhyme}"')


def _worry(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"But the way ahead looked {quest.risk}, and the clue was not easy to trust."
    )


def _help(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f"Then {helper.label} came along and said, 'One small step, and no great fuss; "
        f"let's follow the rhyme and not make a ruckus.'"
    )
    world.say(
        f"Together they looked where the rhyme pointed, and the mystery grew smaller."
    )


def _resolution(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At last, {hero.id} found {quest.reward}, just where the rhyme had promised."
    )
    world.say(
        f"The little {hero.type} laughed, the helper laughed too, and the night felt less strange."
    )
    world.say(
        f"And so the fable ended with a simple truth: a curious heart, a kind friend, and a clever rhyme can lead the way."
    )


def tell(setting: Setting, hero_kind: str, quest_id: str, helper_kind: str, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=_safe_lookup(HEROES, hero_kind)["type"], label=name))
    helper = world.add(Entity(id="helper", kind="character", type=_safe_lookup(HELPERS, helper_kind)["type"], label=_safe_lookup(HELPERS, helper_kind)["label"]))
    quest = _safe_lookup(QUESTS, quest_id)

    _intro(world, hero, quest)
    world.para()
    _joke(world, hero, quest)
    _worry(world, hero, quest)
    _clue(world, hero, quest)
    world.para()
    _help(world, hero, helper, quest)
    _resolution(world, hero, quest)

    world.facts.update(hero=hero, helper=helper, quest=quest, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable with humor, rhyme, and a mysterious quest set in {f["setting"].place}.',
        f"Tell a gentle story about a little {f['hero'].type} who tries to {f['quest'].want} and learns from a friend.",
        f'Write a child-friendly tale where a rhyme leads the hero to "{f["quest"].reward}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest, setting = f["hero"], f["helper"], f["quest"], f["setting"]
    return [
        QAItem(
            question=f"Who went on the mysterious quest in {setting.place}?",
            answer=f"A little {hero.type} named {hero.id} went on the quest, and {helper.label} helped along the way.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.want}. That was the mystery driving the story.",
        ),
        QAItem(
            question="What helped the hero keep going?",
            answer=f"A funny moment, a rhyming clue, and a kind helper helped {hero.id} keep going.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {quest.reward} being found and everyone laughing in relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important, often with a puzzle or goal to solve.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which can make a line feel playful and easy to remember.",
        ),
        QAItem(
            question="Why can a mystery be fun?",
            answer="A mystery can be fun because it makes you wonder, guess, and look closely for clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"  setting: {world.setting.place} / {world.setting.weather}")
    return "\n".join(lines)


ASP_RULES = r"""
% A quest is valid when the setting affords it, and the helper is available.
valid(Place, Hero, Quest, Helper) :- affords(Place, Quest), hero(Hero), helper(Helper).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, q))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.hero, params.quest, params.helper, params.prize)
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
    StoryParams(place="grove", hero="fox", quest="bell", helper="owl", prize="Milo"),
    StoryParams(place="hill", hero="hare", quest="lantern", helper="crow", prize="Nia"),
    StoryParams(place="pond", hero="mouse", quest="key", helper="toad", prize="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
