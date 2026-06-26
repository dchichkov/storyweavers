#!/usr/bin/env python3
"""
storyworlds/worlds/spam_war_quest_sound_effects_reconciliation_folk.py
======================================================================

A small folk-tale storyworld about a village bothered by spam, a little war of
words, a quest to set things right, vivid sound effects, and a reconciliation
at the end.

The seed words suggest two pressures:
- spam: unwanted messages, leaflets, and noisy repetition
- war: a quarrel that grows into a bitter little standoff

The world simulates a simple chain:
1) spam spreads rumors and makes neighbors cross
2) cross neighbors begin a "war" of sharp words and slammed doors
3) a hero goes on a quest to recover the right sound-making object
4) the sound effect reveals the true sender and breaks the misunderstanding
5) reconciliation follows with apology, shared food, and a calmer village

The style is folk tale: plain, warm, rhythmic, and child-facing.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "witch"}
        male = {"boy", "man", "father", "king", "smith"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    soundscape: str
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
class QuestItem:
    id: str
    label: str
    phrase: str
    sound: str
    fits: set[str]
    calms: set[str]
    note: str
    tail: str
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
    quest: str
    spam_kind: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "village": Setting("the village green", "bells and birds", {"quest_bell", "quest_drum", "quest_whistle"}),
    "forest": Setting("the edge of the forest", "wind and leaves", {"quest_whistle", "quest_bell"}),
    "harbor": Setting("the harbor path", "waves and ropes", {"quest_bell", "quest_drum"}),
}

QUESTS = {
    "bell": QuestItem(
        id="bell",
        label="a brass bell",
        phrase="a little brass bell",
        sound="ding-ding",
        fits={"village", "forest", "harbor"},
        calms={"spam", "war"},
        note="The bell can call people together when voices are tangled.",
        tail="rang the bell from the hill",
    ),
    "drum": QuestItem(
        id="drum",
        label="a round drum",
        phrase="a round hand drum",
        sound="boom-boom",
        fits={"village", "harbor"},
        calms={"war"},
        note="The drum can mark a steady beat and slow angry hearts.",
        tail="beat the drum by the well",
    ),
    "whistle": QuestItem(
        id="whistle",
        label="a wooden whistle",
        phrase="a small wooden whistle",
        sound="tweet-tweet",
        fits={"village", "forest"},
        calms={"spam"},
        note="The whistle can answer the spam with a clear true tune.",
        tail="whistled from the old path",
    ),
}

SPAM_KINDS = {
    "leaflets": "leaflets",
    "messages": "messages",
    "caws": "caws",
}

NAMES = ["Mira", "Jory", "Pip", "Nell", "Tomas", "Ada", "Rowan", "Bela"]
TYPES = ["girl", "boy", "woman", "man"]
ROLES = ["mother", "father", "smith", "village elder", "goatherd"]


class StoryState:
    def __init__(self, world: World, hero: Entity, rival: Entity, quest: QuestItem, spam_kind: str):
        self.world = world
        self.hero = hero
        self.rival = rival
        self.quest = quest
        self.spam_kind = spam_kind
        self.quest_found = False
        self.truth_found = False
        self.reconciled = False


def introduce(world: World, hero: Entity, rival: Entity, spam_kind: str) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived {hero.id}, a small {hero.type} with quick feet and a kind eye."
    )
    world.say(
        f"Near by lived {rival.id}, a {rival.type} who kept hearing too many {spam_kind}."
    )
    world.say(
        f"The {world.setting.place} already had {world.setting.soundscape}, but the {spam_kind} kept pushing in like rain at a cracked door."
    )


def spam_spreads(world: World, hero: Entity, rival: Entity, spam_kind: str) -> None:
    hero.memes["worry"] += 1
    rival.memes["worry"] += 1
    rival.memes["annoyance"] += 1
    world.say(
        f"Every day the {spam_kind} came again: flutter-flutter, scribble-scrap, and then another one under the latch."
    )
    world.say(
        f"{rival.id} frowned and said the other side must be doing it on purpose, and soon the neighbors were in a little war of sharp words."
    )
    hero.memes["quest"] += 1


def seek_quest_item(world: World, state: StoryState) -> None:
    state.hero.memes["hope"] = state.hero.memes.get("hope", 0) + 1
    world.para()
    world.say(
        f"Then {state.hero.id} set out on a quest to find {state.quest.phrase}."
    )
    world.say(
        f"At the crossing of stones, an old voice whispered, \"Take the thing that makes a clear sound, and the truth will wake.\""
    )
    world.say(state.quest.note)


def use_sound_effect(world: World, state: StoryState) -> None:
    sound = state.quest.sound
    world.para()
    world.say(
        f"{state.hero.id} climbed the hill and {state.quest.tail}, calling {sound} across the air."
    )
    world.say(
        f"{sound}! went the note, bright and clean."
    )
    world.say(
        f"The bad {state.spam_kind} stopped in a heap, because the secret sender was not a enemy at all, but a sleepy crow stealing scraps of paper from the market."
    )
    state.truth_found = True
    state.world.facts["sound"] = sound
    state.world.facts["truth"] = "sleepy crow"


def reconcile(world: World, state: StoryState) -> None:
    world.para()
    state.rival.memes["annoyance"] = 0
    state.rival.memes["worry"] = 0
    state.hero.memes["worry"] = 0
    state.hero.memes["joy"] = state.hero.memes.get("joy", 0) + 1
    state.reconciled = True
    world.say(
        f"At once, {state.hero.id} and {state.rival.id} went together to the market, where the crow was hiding behind a crate."
    )
    world.say(
        f"They laughed softly, gathered the scattered papers, and spoke gentle apologies."
    )
    world.say(
        f"Then they shared warm bread, and the village war melted into a reconciliation as easy as sunlight after rain."
    )
    world.say(
        f"From that day on, when anyone asked about the noisy {state.spam_kind}, the answer was simple: a clear sound, a brave quest, and a kind heart can bring peace back home."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    rival = world.add(Entity(id=params.rival_name, kind="character", type=params.rival_type))
    world.facts.update(hero=hero, rival=rival, quest=quest, spam_kind=params.spam_kind, setting=setting)

    state = StoryState(world, hero, rival, quest, params.spam_kind)
    introduce(world, hero, rival, params.spam_kind)
    spam_spreads(world, hero, rival, params.spam_kind)
    seek_quest_item(world, state)
    use_sound_effect(world, state)
    reconcile(world, state)

    world.facts["reconciled"] = state.reconciled
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for quest_id, quest in QUESTS.items():
            if place in quest.fits and f"quest_{quest_id}" in setting.affords:
                for spam_kind in SPAM_KINDS:
                    out.append((place, quest_id, spam_kind))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child about {f["spam_kind"]}, a little war of words, and a quest for {f["quest"].label}.',
        f"Tell a warm village story where {f['hero'].id} uses {f['quest'].sound} to end a quarrel about {f['spam_kind']}.",
        f"Write a short story with sound effects like {f['quest'].sound}, and end with reconciliation in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, quest = f["hero"], f["rival"], f["quest"]
    return [
        QAItem(
            question=f"Who went on the quest in {f['setting'].place}?",
            answer=f"{hero.id} went on the quest to find {quest.phrase} so the village could calm down.",
        ),
        QAItem(
            question=f"What noisy trouble made the neighbors argue?",
            answer=f"The trouble was {f['spam_kind']}, which kept showing up and turning talk into a little war.",
        ),
        QAItem(
            question=f"What sound did {hero.id} make to help the truth appear?",
            answer=f"{hero.id} made the sound {quest.sound}, and that clear sound helped reveal the crow and stop the fighting.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {rival.id}?",
            answer=f"They apologized, gathered the papers, shared bread, and ended in reconciliation instead of anger.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a folk tale?",
            answer="A quest is a journey to find something or set something right, usually with a brave task and a good ending.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like ding-ding, boom-boom, or whoosh that help you hear the action in your mind.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop fighting, forgive one another, and come back together in peace.",
        ),
        QAItem(
            question="What is spam?",
            answer="Spam is unwanted stuff that keeps arriving again and again, like too many messages or papers you did not ask for.",
        ),
        QAItem(
            question="What does a folk tale usually feel like?",
            answer="A folk tale usually feels old, warm, simple, and wise, as if someone is telling it beside a fire.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def explain_rejection(place: str, quest: str) -> str:
    return f"(No story: {quest} does not fit the soundscape of {place}, so the quest would not be reasonable.)"


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_item(Q).
spam(S) :- spam_kind(S).

valid(P,Q,S) :- setting(P), quest_item(Q), spam_kind(S), fits(Q,P), affords(P,Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for q in setting.affords:
            lines.append(asp.fact("affords", place, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_item", qid))
        for p in q.fits:
            lines.append(asp.fact("fits", qid, p))
    for s in SPAM_KINDS:
        lines.append(asp.fact("spam_kind", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: spam, war, quest, sound effects, reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--spam-kind", choices=sorted(SPAM_KINDS))
    ap.add_argument("--name")
    ap.add_argument("--rival-name")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--rival-gender", choices=["girl", "boy", "woman", "man"])
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
    if getattr(args, "place", None) or getattr(args, "quest", None) or getattr(args, "spam_kind", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
            and (getattr(args, "spam_kind", None) is None or c[2] == getattr(args, "spam_kind", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, spam_kind = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    rival_name = getattr(args, "rival_name", None) or rng.choice([n for n in NAMES if n != hero_name])
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy", "woman", "man"])
    rival_gender = getattr(args, "rival_gender", None) or rng.choice(["girl", "boy", "woman", "man"])
    return StoryParams(
        place=place,
        quest=quest,
        spam_kind=spam_kind,
        hero_name=hero_name,
        hero_type=hero_gender,
        rival_name=rival_name,
        rival_type=rival_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="village", quest="bell", spam_kind="leaflets", hero_name="Mira", hero_type="girl", rival_name="Tomas", rival_type="man"),
    StoryParams(place="forest", quest="whistle", spam_kind="messages", hero_name="Pip", hero_type="boy", rival_name="Ada", rival_type="woman"),
    StoryParams(place="harbor", quest="drum", spam_kind="caws", hero_name="Nell", hero_type="girl", rival_name="Rowan", rival_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        items = asp_valid_combos()
        print(f"{len(items)} compatible (place, quest, spam-kind) combos:\n")
        for t in items:
            print("  ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} at {p.place} (spam: {p.spam_kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
