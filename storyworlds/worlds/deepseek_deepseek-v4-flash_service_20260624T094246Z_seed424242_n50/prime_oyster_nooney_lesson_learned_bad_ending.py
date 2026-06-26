#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/prime_oyster_nooney_lesson_learned_bad_ending.py
==================================================================================================

A standalone story world about Prime, a child who finds a magical oyster, and
his friend Nooney. They learn a lesson about greed, but the ending is sad: the
oyster breaks. The tone is heartwarming even in the loss.

Initial story (used to build world model):
---
Prime was a little cheerful boy who loved exploring the tide pools. One morning
he found a shimmering oyster that granted wishes. He showed it to his best
friend Nooney. They made one small wish – for a pretty shell – and the oyster
glowed. Nooney said, "Be careful, Prime. You can't ask too much." But Prime
wanted more. He wished for a sandcastle, then a giant ice cream, then a kite.
The oyster cracked, its light faded, and it turned into ordinary shell. Prime
cried. Nooney hugged him and said, "We still have the memory. And we have each
other." Prime learned that wanting too much can break the best things.

Causal state updates:
---
    actor makes wish                      -> oyster.wish_count += 1
                                               actor.joy += 1
    wish_count > MAX_WISHES               -> oyster.broken = True
                                               actor.sadness += 1
                                               actor.greed_lesson += 1
    actor ignores friend's warning        -> actor.defiance += 1
    friend comforts                       -> actor.sadness -> 0, actor.love ++
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAX_WISHES = 3.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandma": "grandma"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the beach"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = "sunny"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fragile(world: World) -> list[str]:
    """If wish_count exceeds max, oyster breaks."""
    oyster = world.entities.get("oyster")
    if not oyster:
        return []
    if oyster.meters["wish_count"] >= MAX_WISHES and not oyster.meters["broken"]:
        sig = ("break", oyster.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        oyster.meters["broken"] = THRESHOLD
        return [f"The oyster cracked. A tiny spiderweb of lines spread across its shell."]
    return []


def _r_sadness(world: World) -> list[str]:
    oyster = world.entities.get("oyster")
    if oyster and oyster.meters["broken"] >= THRESHOLD:
        for actor in world.characters():
            if actor.id in ("Parent", "Nooney"):
                continue
            sig = ("sad", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["sadness"] += 1
                return [f"{actor.id} felt a deep ache in {actor.pronoun('possessive')} chest."]
    return []


def _r_comfort(world: World) -> list[str]:
    """Nooney comforts when oyster is broken and actor is sad."""
    if not world.entities.get("oyster"):
        return []
    if world.entities["oyster"].meters["broken"] < THRESHOLD:
        return []
    hero = world.entities.get("Prime")
    nooney = world.entities.get("Nooney")
    if not hero or not nooney:
        return []
    sig = ("comfort", hero.id, nooney.id)
    if sig in world.fired:
        return []
    if hero.memes["sadness"] >= THRESHOLD and nooney.memes["seen_break"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["sadness"] = 0.0
        hero.memes["love"] += 1
        return [f"Nooney wrapped an arm around {hero.id}. 'We still have the memory.'"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="fragile", tag="physical", apply=_r_fragile),
    Rule(name="sadness", tag="emotional", apply=_r_sadness),
    Rule(name="comfort", tag="social", apply=_r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    # For this domain, the oyster is always at risk if activity is "wish".
    # But we check zone: oyster is a shell held in hand (region "hand").
    # The activity's zone includes "hand" if the wish is made while holding it.
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    # The gear that protects from overuse: a "wish pouch" that limits wishes.
    # Actually we model a "pouch" that can hold the oyster and only allow one wish.
    # For simplicity, we always return the pouch if activity is "wish".
    if activity.id == "wish" and prize.id == "oyster":
        for g in GEAR:
            if g.id == "pouch":
                return g
    return None


# ---------------------------------------------------------------------------
# Prediction (forward simulation)
# ---------------------------------------------------------------------------
def predict_break(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    oyster = sim.entities.get(prize_id)
    return {
        "broken": bool(oyster and oyster.meters["broken"] >= THRESHOLD),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "wish": "every tiny wish made the oyster glow a little warmer",
    }.get(activity.id, "it felt like magic")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the beach":
        return "The waves whispered soft secrets, and tide pools sparkled like jewels."
    return "The shore was calm and waiting."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved the sea and the secrets it kept.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved exploring the tide pools and {activity.gerund}.")


def finds_oyster(world: World, hero: Entity, oyster: Entity) -> None:
    world.say(
        f"One bright morning, {hero.id} found {oyster.phrase} in a tide pool. "
        f"It shimmered with a faint golden light."
    )


def shows_friend(world: World, hero: Entity, friend: Entity, oyster: Entity) -> None:
    world.say(
        f"{hero.id} ran to show {friend.id}. 'Look what I found!' "
        f"{friend.id} gasped. 'It's beautiful.'"
    )


def warn_friend(world: World, friend: Entity, hero: Entity, oyster: Entity) -> None:
    world.say(
        f'"{friend.id} said, "We have to be careful. '
        f'If we wish too much, the oyster might break.'"'
    )


def make_wish(world: World, hero: Entity, oyster: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    oyster.meters["wish_count"] += 1
    world.say(
        f"{hero.id} held the oyster tight and made a small wish. The oyster glowed warm "
        f"and bright. {activity_delight(activity)}."
    )
    propagate(world)


def defies(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning but felt the pull for more. \"Just one more,\" he said.")


def wishes_too_much(world: World, hero: Entity, oyster: Entity) -> None:
    while oyster.meters["wish_count"] < MAX_WISHES:
        oyster.meters["wish_count"] += 1
        hero.memes["joy"] += 1
        world.say(f"{hero.id} wished again. A bright glow, a shimmer, then... ")
    propagate(world)


def bad_ending(world: World, hero: Entity, friend: Entity, oyster: Entity) -> None:
    # The oyster has already broken via propagate; narrative about the moment.
    if oyster.meters["broken"] >= THRESHOLD:
        world.say(
            f"The oyster cracked. Its light flickered and went out. "
            f"{hero.id} stared at the gray shell in {hero.pronoun('possessive')} hand."
        )
        friend.memes["seen_break"] += 1
        propagate(world)
        world.say(
            f"{hero.id} could not hold back {hero.pronoun('possessive')} tears. "
            f'{friend.id} hugged {hero.pronoun('object')}. "We still have the memory '
            f'and we have each other."'
        )
        world.say(
            f"{hero.id} sniffled and nodded. The lesson was learned, even though "
            f"the magic was gone."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Prime", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, friend_name: str = "Nooney") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type="friend", label="friend",
        traits=["wise", "kind"],
    ))
    oyster = world.add(Entity(
        id="oyster", type="oyster", label="oyster",
        phrase="a shimmering oyster that held a soft golden light",
        owner=hero.id, caretaker=None, region="hand", plural=False,
    ))

    # Acts
    introduce(world, hero)
    loves_activity(world, hero, activity)
    finds_oyster(world, hero, oyster)
    world.para()
    shows_friend(world, hero, friend, oyster)
    warn_friend(world, friend, hero, oyster)
    world.para()
    make_wish(world, hero, oyster, activity)
    defies(world, hero)
    wishes_too_much(world, hero, oyster)
    world.para()
    bad_ending(world, hero, friend, oyster)

    world.facts.update(hero=hero, friend=friend, oyster=oyster,
                       prize_cfg=prize_cfg, activity=activity, setting=setting,
                       broken=oyster.meters["broken"] >= THRESHOLD)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "beach": Setting(place="the beach", indoor=False, affords={"wish"}),
    "tideland": Setting(place="the tide pools", indoor=False, affords={"wish"}),
}

ACTIVITIES = {
    "wish": Activity(
        id="wish",
        verb="make a wish on the magic oyster",
        gerund="wishing on the magic oyster",
        rush="grab the oyster and wish",
        mess="overwish",
        soil="cracked and dull",
        zone={"hand"},
        weather="sunny",
        keyword="wish",
        tags={"wish", "magic", "oyster"},
    ),
}

PRIZES = {
    "oyster": Prize(
        label="magic oyster",
        phrase="a shimmering oyster that held a soft golden light",
        type="oyster",
        region="hand",
    ),
}

GEAR = [
    Gear(
        id="pouch",
        label="a soft velvet pouch",
        covers={"hand"},
        guards={"overwish"},
        prep="put the oyster in the velvet pouch and make only one wish",
        tail="slipped the oyster into the velvet pouch",
    ),
]

FRIEND_NAMES = ["Nooney", "Sage", "Kai", "Lena"]
BOY_NAMES = ["Prime", "Kai", "Leo", "Max"]
GIRL_NAMES = ["Luna", "Mila", "Zoe"]
TRAITS = ["curious", "stubborn", "kind", "brave", "playful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wish": [("What is a wish?",
              "A wish is something you hope for with all your heart. Sometimes people "
              "say wishes aloud or hold them in their thoughts.")],
    "magic": [("Is magic real?",
               "Magic is the wonderful feeling when something surprising and good happens. "
               "In stories, magic can make things glow or grant wishes, but in real life "
               "the best magic is kindness and friendship.")],
    "oyster": [("What is an oyster?",
                "An oyster is a sea creature with a hard shell. Sometimes pearls grow inside "
                "them. In stories, oysters can hold magic.")],
    "greed": [("Why is it bad to want too much?",
               "When you always want more, you may forget to be happy with what you already "
               "have. That can make you lose the good things you had.")],
}
KNOWLEDGE_ORDER = ["wish", "magic", "oyster", "greed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a magical oyster "
         f'"and a lesson learned" that includes the word "wish".',
        f"Tell a gentle story where {hero.id} finds a magic oyster and {friend.id} "
         f"warns about being greedy, but the ending is a little sad but warm.",
        f'Write a simple story that uses the noun "oyster" and ends with a hug.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    oyster = f["oyster"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who found the magic oyster in the tide pool?",
            answer=f"A little {trait} {hero.type} named {hero.id} found the oyster while exploring."
        ),
        QAItem(
            question=f"What did {friend.id} warn {hero.id} about?",
            answer=f"{friend.id} warned that wishing too much could break the magic oyster."
        ),
        QAItem(
            question=f"Why did the oyster break?",
            answer=f"{hero.id} made too many wishes, and the oyster could not hold all that magic."
        ),
        QAItem(
            question=f"How did {hero.id} feel after the oyster broke?",
            answer=f"{pos.capitalize()} heart ached, but {friend.id} hugged {obj} and said they had the memory."
        ),
        QAItem(
            question=f"What was the lesson {hero.id} learned?",
            answer=f"{trait.capitalize()} {hero.id} learned that wanting too much can break the best things, but friendship stays."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="beach", activity="wish", prize="oyster", name="Prime", gender="boy", friend="Nooney", trait="curious"),
    StoryParams(place="beach", activity="wish", prize="oyster", name="Luna", gender="girl", friend="Nooney", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (f"(No story: the {prize.label} cannot be used with {activity.gerund} in a meaningful way.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Prime, Nooney, and a magic oyster. "
                    "A lesson learned, a bad ending, but heartwarming.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        friend=friend,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize}, friend: {p.friend})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
