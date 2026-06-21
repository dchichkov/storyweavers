#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/salami_iris_cubby_bravery_misunderstanding_teamwork_heartwarming.py
===================================================================================================

A small standalone storyworld about a gentle misunderstanding in a backyard
cubby, where bravery and teamwork turn a lost snack into a warm ending.

Seed words: salami, iris, cubby
Features: Bravery, Misunderstanding, Teamwork
Style: Heartwarming
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    shelter: str
    has_cubby: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Misunderstanding:
    id: str
    trigger: str
    wrong_guess: str
    truth: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    snack: str
    misunderstanding: str
    help_action: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"brave", "gentle"}]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["confusion"] += 1
        out.append("__confusion__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cubby").memes["shared"] >= THRESHOLD and world.get("cubby").meters["full"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["joy"] += 1
                kid.memes["comfort"] += 1
            out.append("The cubby felt cozy again.")
    return out


CAUSAL_RULES = [Rule("misread", _r_misread), Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_actions() -> list[HelpAction]:
    return [a for a in HELP_ACTIONS.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if not place.has_cubby:
            continue
        for snack_id, snack in SNACKS.items():
            for mis_id in MISUNDERSTANDINGS:
                combos.append((place_id, snack_id, mis_id))
    return combos


def explain_action_rejection(action_id: str) -> str:
    a = HELP_ACTIONS[action_id]
    return f"(Refusing help action '{action_id}': it is too weak or awkward for this gentle story.)"


def explain_combo_rejection(place: Place) -> str:
    return f"(No story: {place.label} needs a cubby for this world.)"


def _default_name_pool(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def _pick_child(rng: random.Random, gender: Optional[str] = None, avoid: str = "") -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    pool = [n for n in _default_name_pool(g) if n != avoid]
    return rng.choice(pool), g


def setup(world: World, p: StoryParams) -> None:
    pass


def tell(place: Place, snack: Snack, misunderstanding: Misunderstanding, action: HelpAction,
         child1: str, child1_gender: str, child2: str, child2_gender: str,
         adult: str) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="brave"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="gentle"))
    parent = world.add(Entity(id=adult, kind="character", type="mother", label="Mom"))
    cubby = world.add(Entity(id="cubby", type="place", label="the cubby"))
    snack_ent = world.add(Entity(id="snack", type="snack", label=snack.label))
    a.memes["bravery"] = 5.0
    b.memes["trust"] = 5.0
    world.say(
        f"{a.id} and {b.id} were building a cubby in {place.label}. "
        f"They tucked blankets low and made a tiny door for the day."
    )
    world.say(
        f"{a.id} found {snack.phrase}, and the sweet smell of {snack.smell} drifted through the cubby."
    )
    world.say(
        f'{b.id} frowned a little. "{misunderstanding.wrong_guess}," {b.id} said, '
        f'but that was not quite right.'
    )
    world.para()
    a.memes["bravery"] += 1
    b.memes["worry"] += 1
    world.say(
        f"{a.id} took a brave breath and said, "
        f'"No, wait. {misunderstanding.truth}."'
    )
    world.say(
        f"{b.id} blinked, then nodded. The misunderstanding began to melt away."
    )
    if action.id == "share":
        world.say(
            f"Together they carried the snack to {adult}'s table and cut it into neat pieces."
        )
        cubby.meters["full"] += 1
        cubby.memes["shared"] += 1
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        world.say(
            f'{adult} smiled and said, "That was brave of you to speak up, and kind of you to help each other."'
        )
        world.para()
        world.say(
            f"They went back to the cubby with full plates and happy hearts, and the little room felt warmer than before."
        )
    elif action.id == "carry":
        world.say(
            f"{a.id} and {b.id} carried the basket together, step by careful step, until {adult} could sort it out."
        )
        cubby.meters["full"] += 1
        cubby.memes["shared"] += 1
        world.say(
            f"{adult} thanked them for working together and sent them back with extra napkins and a laugh."
        )
        world.para()
        world.say(
            f"The cubby did not feel confused anymore; it felt like a cozy place where everyone had helped."
        )
    else:
        world.say(
            f"{adult} came over, listened to both children, and helped them fix the mix-up gently."
        )
        cubby.meters["full"] += 1
        cubby.memes["shared"] += 1
        world.say(
            f"By the end, {a.id} was smiling, {b.id} was smiling, and the cubby was filled with calm."
        )
    world.facts.update(
        place=place,
        snack=snack,
        misunderstanding=misunderstanding,
        action=action,
        child1=a,
        child2=b,
        adult=parent,
        cubby=cubby,
        outcome="heartwarming",
    )
    return world


PLACES = {
    "backyard": Place(id="backyard", label="the backyard", shelter="blankets and chairs", has_cubby=True, tags={"outside"}),
    "porch": Place(id="porch", label="the porch", shelter="pillows and a little table", has_cubby=True, tags={"outside"}),
    "playroom": Place(id="playroom", label="the playroom", shelter="beanbags and quilts", has_cubby=True, tags={"inside"}),
}

SNACKS = {
    "salami": Snack(id="salami", label="salami", phrase="a plate of salami slices", smell="salami", tags={"food", "salami"}),
    "apple": Snack(id="apple", label="apple slices", phrase="a bowl of apple slices", smell="sweet apples", tags={"food"}),
    "crackers": Snack(id="crackers", label="crackers", phrase="a little tray of crackers", smell="toasty crackers", tags={"food"}),
}

MISUNDERSTANDINGS = {
    "lost_snack": Misunderstanding(id="lost_snack", trigger="looked missing", wrong_guess="It must be gone", truth="It was only tucked behind the blanket", tags={"misunderstanding"}),
    "shared_snack": Misunderstanding(id="shared_snack", trigger="looked shared", wrong_guess="You took my piece", truth="We were saving a piece for everyone", tags={"misunderstanding"}),
}

HELP_ACTIONS = {
    "share": HelpAction(id="share", sense=3, power=3, text="shared the snack and calmed the moment", fail="wanted to help, but the moment stayed tense", qa_text="shared the snack and calmed the misunderstanding", tags={"teamwork"}),
    "carry": HelpAction(id="carry", sense=2, power=2, text="carried the basket together", fail="tried to carry it alone, but it was too much", qa_text="carried the basket together", tags={"teamwork"}),
    "ask_mom": HelpAction(id="ask_mom", sense=3, power=3, text="asked Mom to help them sort it out", fail="called too late for the mix-up to matter", qa_text="asked Mom to help them sort it out", tags={"teamwork"}),
}

GIRL_NAMES = ["Iris", "Maya", "Nora", "Lily", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Noah", "Ben"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story with the words "{f["snack"].label}", "iris", and "cubby".',
        f"Tell a gentle story where {f['child1'].id} shows bravery, there is a misunderstanding about {f['snack'].label}, and the children use teamwork to fix it.",
        f'Write a short story for a young child about a cubby, a snack, and a kind mix-up that ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    snack = f["snack"]
    mis = f["misunderstanding"]
    adult = f["adult"]
    qa = [
        QAItem(
            question="What were the children making?",
            answer=f"They were making a cubby in {f['place'].label}. It became a cozy little hideout for their play."
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"They saw {snack.phrase} and guessed something wrong about it. That first guess made the moment feel confused for a little while."
        ),
        QAItem(
            question=f"What did {a.id} do that was brave?",
            answer=f"{a.id} spoke up and explained the truth instead of staying quiet. That brave choice helped everyone understand each other."
        ),
        QAItem(
            question="How did the children use teamwork?",
            answer=f"They listened to each other, helped carry and share the snack, and worked with {adult.id} to fix the mix-up. Because they did it together, the worry went away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the children smiling in the cubby and feeling close again. The snack was sorted out, and the whole place felt warm and safe."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    snack = f["snack"].label
    return [
        QAItem(
            question="What is a cubby?",
            answer="A cubby is a small cozy space children make for pretend play. It can be built from blankets, chairs, or pillows."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous. A brave person still speaks up or tries to help."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other to do something together. Each person does a part, and the job gets easier."
        ),
        QAItem(
            question=f"What kind of food is {snack}?",
            answer=f"{snack.capitalize()} is a kind of food that can be sliced and shared. It is often served in small pieces."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", snack="salami", misunderstanding="lost_snack", help_action="share", child1="Iris", child1_gender="girl", child2="Ben", child2_gender="boy", adult="Mom"),
    StoryParams(place="playroom", snack="salami", misunderstanding="shared_snack", help_action="ask_mom", child1="Lina", child1_gender="girl", child2="Owen", child2_gender="boy", adult="Mom"),
    StoryParams(place="porch", snack="crackers", misunderstanding="lost_snack", help_action="carry", child1="Mia", child1_gender="girl", child2="Theo", child2_gender="boy", adult="Mom"),
]


def valid_story_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.help_action not in HELP_ACTIONS:
        raise StoryError("Unknown help action.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming cubby storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--help-action", dest="help_action", choices=HELP_ACTIONS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["Mom", "Dad"])
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
    place = args.place or rng.choice(list(PLACES))
    snack = args.snack or rng.choice(list(SNACKS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    help_action = args.help_action or rng.choice([a.id for a in sensible_actions()])
    if help_action not in HELP_ACTIONS:
        raise StoryError("Unknown help action.")
    if HELP_ACTIONS[help_action].sense < SENSE_MIN:
        raise StoryError(explain_action_rejection(help_action))
    if not PLACES[place].has_cubby:
        raise StoryError(explain_combo_rejection(PLACES[place]))
    c1, g1 = _pick_child(rng, args.child1_gender)
    c2, g2 = _pick_child(rng, args.child2_gender, avoid=c1)
    return StoryParams(
        place=place,
        snack=snack,
        misunderstanding=misunderstanding,
        help_action=help_action,
        child1=args.child1 or c1,
        child1_gender=args.child1_gender or g1,
        child2=args.child2 or c2,
        child2_gender=args.child2_gender or g2,
        adult=args.adult or "Mom",
    )


def generate(params: StoryParams) -> StorySample:
    valid_story_params(params)
    world = tell(
        PLACES[params.place],
        SNACKS[params.snack],
        MISUNDERSTANDINGS[params.misunderstanding],
        HELP_ACTIONS[params.help_action],
        params.child1,
        params.child1_gender,
        params.child2,
        params.child2_gender,
        params.adult,
    )
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


ASP_RULES = r"""
cubby_story(P, S, M) :- place(P), snack(S), misunderstanding(M), has_cubby(P).
help_ok(H) :- help_action(H), sense(H, N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_cubby:
            lines.append(asp.fact("has_cubby", pid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for aid, a in HELP_ACTIONS.items():
        lines.append(asp.fact("help_action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show cubby_story/3."))
    return sorted(set(asp.atoms(model, "cubby_story")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP validation.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show cubby_story/3.\n#show help_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible cubby stories.")
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
