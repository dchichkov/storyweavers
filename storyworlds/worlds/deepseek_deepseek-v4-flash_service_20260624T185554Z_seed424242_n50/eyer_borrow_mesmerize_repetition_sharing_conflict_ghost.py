#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/eyer_borrow_mesmerize_repetition_sharing_conflict_ghost.py
=========================================================================================================

A spooky little world where a child eyes a ghost's mesmerizing orb, borrows it,
and must learn to share before the ghost's patience wears thin.

Features: Repetition (each day the cycle repeats), Sharing (the compromise), Conflict
          (ghost vs. child over the orb).
Style: Ghost Story (old house, candlelight, cold air, whispered warnings).
Domain elements: eyer (the child watches the orb), borrow (the child takes it),
                 mesmerize (the orb's glow fascinates).
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


# --------------------------------------------------------------------------
# Entity: characters and objects share this dataclass.
# --------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    _type: str = "thing"           # child, ghost, orb
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None  # who currently holds it

    adjectives: list[str] = field(default_factory=list)
    plural: bool = False

    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self._type in ("child", "boy", "girl"):
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self._type in ("ghost", "spirit"):
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def phrase_lower(self) -> str:
        return (self.phrase[0].lower() + self.phrase[1:]) if self.phrase else self.label

    @property
    def label_word(self) -> str:
        return self.label


# --------------------------------------------------------------------------
# Settings – old, spooky places.
# --------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str]            # activity ids possible here


# --------------------------------------------------------------------------
# Activity – one kind of "borrowing" that triggers the story.
# --------------------------------------------------------------------------
@dataclass
class Activity:
    id: str
    verb: str                      # wanted to …            "borrow the ghost's orb"
    gerund: str                    # loved …                "borrowing the orb"
    rush: str                      # tried to …             "reach for the orb"
    mess: str                      # the "mess" kind        "mesmerized"
    zone: set[str]                 # we use "mind" as region
    weather: str = "dim"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


# --------------------------------------------------------------------------
# Prize – the item the child borrows; the ghost's treasure.
# --------------------------------------------------------------------------
@dataclass
class Prize:
    label: str
    phrase: str
    _type: str
    region: str = "hand"          # not used for body zones, but kept for compatibility
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"child"})


# --------------------------------------------------------------------------
# Compromise – the "sharing" solution.
# --------------------------------------------------------------------------
@dataclass
class Compromise:
    id: str
    label: str
    prep: str                     # "share the orb's light together"
    tail: str                     # "stood together, watching the soft glow"
    plural: bool = False
    guards: set[str] = field(default_factory=lambda: {"mesmerized", "defiance"})


# --------------------------------------------------------------------------
# World – state container + narration.
# --------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting):
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


# --------------------------------------------------------------------------
# Causal rules – forward chaining.
# --------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mesmerize(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["mesmerized"] < THRESHOLD:
            continue
        obj = world.entities.get("orb")
        if not obj or obj.held_by != actor.id:
            continue
        sig = ("mesmerized", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fascination"] += 1
        out.append(
            f"The {obj.label} glowed softly in {actor.id}'s hands, "
            f"and {actor.pronoun()} could not stop staring."
        )
    return out


def _r_conflict(world: World) -> list[str]:
    """Ghost wants the orb back, child refuses -> conflict."""
    out = []
    gh = world.entities.get("ghost")
    ch = next((e for e in world.characters() if e._type == "child"), None)
    if not gh or not ch:
        return out
    if ch.meters["defiance"] < THRESHOLD:
        return out
    sig = ("conflict", gh.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gh.memes["anger"] += 1
    ch.memes["fear"] += 1
    out.append("__conflict__")
    return out


def _r_repetition(world: World) -> list[str]:
    """Each day the cycle repeats – the borrow, the demand."""
    out = []
    ch = next((e for e in world.characters() if e._type == "child"), None)
    gh = world.entities.get("ghost")
    if not ch or not gh:
        return out
    if ch.meters["borrowed_today"] < THRESHOLD:
        return out
    # reset for next day
    ch.meters["borrowed_today"] = 0
    # ghost's patience decreases
    gh.meters["patience"] -= 1
    if gh.meters["patience"] < THRESHOLD:
        out.append("The ghost's voice grew thinner, colder.")
    return out


CAUSAL_RULES = [
    Rule("mesmerize", "magical", _r_mesmerize),
    Rule("conflict", "social", _r_conflict),
    Rule("repetition", "time", _r_repetition),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# --------------------------------------------------------------------------
# Constraint helpers.
# --------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """The orb is always 'at risk' of being borrowed."""
    return True


def select_compromise(activity: Activity, prize: Prize) -> Optional[Compromise]:
    """The only possible compromise is sharing the orb's light."""
    for c in COMPROMISES:
        if activity.mess in c.guards:
            return c
    return None


# --------------------------------------------------------------------------
# Prediction (ghost foresees endless borrowing).
# --------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    orb = sim.entities.get(prize_id)
    return {
        "soiled": bool(orb and orb.held_by != "ghost"),
        "patience": sim.get("ghost").meters.get("patience", 0),
    }


# --------------------------------------------------------------------------
# Verbs – the beats of the screenplay.
# --------------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a quiet {child._type} who loved exploring old places."
    )


def setting_intro(world: World, setting: Setting) -> None:
    world.say(setting.detail)


def ghost_appears(world: World, ghost: Entity, orb: Entity) -> None:
    world.say(
        f"Deep inside the {world.setting.place}, a ghost hovered in the dusty air, "
        f"holding {orb.phrase_lower()}."
    )
    world.say(
        f"The orb pulsed with a soft blue light, and {ghost.pronoun()} whispered, "
        f'"This is mine."'
    )


def child_eyes_orb(world: World, child: Entity, orb: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} could not stop staring. "
        f"The glow pulled at {child.pronoun('possessive')} eyes like a quiet song."
    )


def borrow_act(world: World, child: Entity, ghost: Entity, orb: Entity, activity: Activity) -> None:
    child.meters["borrowed_today"] += 1
    orb.held_by = child.id
    child.meters["mesmerized"] += 1
    world.say(
        f"Before the ghost could blink, {child.id} {activity.rush} and took the orb. "
        f'"I will give it back," {child.pronoun()} whispered.'
    )
    propagate(world)


def ghost_warns(world: World, ghost: Entity, child: Entity, orb: Entity) -> None:
    world.say(
        f"Each evening the ghost returned, its voice a cold rustle: "
        f'"You borrowed {orb.label}. Give it back."'
    )


def child_defies(world: World, child: Entity) -> None:
    child.meters["defiance"] += 1
    world.say(
        f"{child.id} shook {child.pronoun('possessive')} head. "
        f'"Tomorrow," {child.pronoun()} said, gripping the orb tighter.'
    )
    propagate(world)


def ghost_exclaims(world: World, ghost: Entity, child: Entity) -> None:
    if ghost.memes["anger"] >= THRESHOLD:
        world.say(
            f"The ghost's form flickered. "
            f'"You steal my treasure, and I have nothing!" '
            f"its voice echoed off the walls."
        )
        child.memes["fear"] += 1


def sharing_compromise(world: World, ghost: Entity, child: Entity, orb: Entity,
                       comp: Compromise) -> None:
    child.meters["defiance"] = 0
    ghost.memes["anger"] = 0
    child.memes["generosity"] += 1
    ghost.memes["trust"] += 1
    orb.held_by = None   # both can share
    world.say(
        f"{child.id} looked at the ghost's dark eyes and swallowed. "
        f'"What if we {comp.prep}?" {child.pronoun()} asked.'
    )
    world.say(
        f"The ghost paused. Then it nodded. "
        f"They {comp.tail}, and the old house felt a little less cold."
    )


# --------------------------------------------------------------------------
# The full story template.
# --------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Lily", child_type: str = "girl",
         ghost_name: str = "Wisp") -> World:
    world = World(setting)
    world.weather = "dim"

    child = world.add(Entity(
        id=child_name, kind="character", _type=child_type,
        adjectives=["curious", "daring"],
    ))
    ghost = world.add(Entity(
        id=ghost_name, kind="character", _type="ghost",
        adjectives=["pale", "whispering"],
    ))
    orb = world.add(Entity(
        id="orb", _type="orb", label="orb", phrase="a glowing blue orb",
        owner=ghost.id, held_by=ghost.id,
        adjectives=["mysterious", "shimmering"],
    ))

    # Act 1 – introduce setting, ghost, child, orb.
    introduce(world, child)
    setting_intro(world, setting)
    ghost_appears(world, ghost, orb)
    child_eyes_orb(world, child, orb)

    world.para()

    # Act 2 – the borrowing and the ghost's demand, repeated.
    borrow_act(world, child, ghost, orb, activity)
    ghost_warns(world, ghost, child, orb)
    child_defies(world, child)
    ghost_exclaims(world, ghost, child)

    world.para()

    # Act 3 – resolution: sharing.
    comp = select_compromise(activity, prize_cfg)
    if comp:
        sharing_compromise(world, ghost, child, orb, comp)

    world.facts.update(
        child=child, ghost=ghost, orb=orb,
        prize_cfg=prize_cfg, activity=activity, setting=setting,
        compromise=comp,
        conflict=ghost.memes["anger"] >= THRESHOLD,
        resolved=comp is not None,
    )
    return world


# --------------------------------------------------------------------------
# Registries.
# --------------------------------------------------------------------------
SETTINGS = {
    "old house": Setting(
        place="the old house",
        detail="The old house stood at the end of the lane, its windows dark and its "
               "door hanging ajar.",
        affords={"borrow_orb"},
    ),
    "attic": Setting(
        place="the attic",
        detail="The attic was full of forgotten trunks and dust. A single beam of "
               "moonlight fell on a small table.",
        affords={"borrow_orb"},
    ),
    "library": Setting(
        place="the forgotten library",
        detail="Shelves of crumbling books lined the walls. In the center, a ghost "
               "cradled a glowing orb.",
        affords={"borrow_orb"},
    ),
}

ACTIVITIES = {
    "borrow_orb": Activity(
        id="borrow_orb",
        verb="borrow the ghost's orb",
        gerund="borrowing the orb",
        rush="reach for the orb",
        mess="mesmerized",
        zone={"mind"},
        weather="dim",
        keyword="borrow",
        tags={"orb", "borrow", "mesmerize"},
    ),
}

PRIZES = {
    "orb": Prize(
        label="orb",
        phrase="a glowing blue orb",
        _type="orb",
        region="hand",
    ),
}

COMPROMISES = [
    Compromise(
        id="share_light",
        label="share the orb's light",
        prep="share its light together",
        tail="stood side by side, watching the orb pulse gently",
        guards={"mesmerized", "defiance"},
    ),
]

CHILD_NAMES = ["Lily", "Ben", "Maya", "Finn", "Zoe", "Theo", "Ella", "Max"]
GHOST_NAMES = ["Wisp", "Ash", "Cinder", "Shade", "Phantom", "Glimmer"]
CHILD_TYPES = ["girl", "boy"]

TRAITS = ["curious", "bold", "daring", "spellbound", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    """Only one combination possible – borrow_orb / orb / any setting."""
    combos = []
    for place in SETTINGS:
        act = "borrow_orb"
        prize = "orb"
        combos.append((place, act, prize))
    return combos


# --------------------------------------------------------------------------
# StoryParams – domain‑specific parameters.
# --------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    child_name: str
    child_gender: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


# --------------------------------------------------------------------------
# Q&A sets.
# --------------------------------------------------------------------------
KNOWLEDGE = {
    "orb": [("What is a glowing orb?",
             "A glowing orb is a round ball that shines with soft light, "
             "often said to hold magic or a spirit inside.")],
    "ghost": [("What is a ghost?",
               "A ghost is the spirit of someone who has passed away, "
               "often seen in old houses or forgotten places.")],
    "borrow": [("What does it mean to borrow something?",
                "To borrow means to take something from someone with the "
                "intention of giving it back later.")],
    "share": [("What does it mean to share?",
               "Sharing means to let someone else use or enjoy something "
               "that you have, so everyone can enjoy it together.")],
    "conflict": [("How do people and ghosts solve conflicts?",
                  "In stories, conflicts are solved by talking and finding a "
                  "compromise, like sharing a treasure or making a promise.")],
}
KNOWLEDGE_ORDER = ["orb", "ghost", "borrow", "share", "conflict"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    act = f["activity"]
    return [
        f'Write a gentle ghost story for a child named {child.id} '
        f'who meets a ghost and {act.gerund} its glowing orb.',
        f"Tell a story about sharing and conflict, where a {child._type} "
        f"named {child.id} and a ghost named {ghost.id} learn to "
        f"share a magical orb.",
        f"A short tale about a brave {child._type} who must decide whether "
        f"to keep a borrowed treasure or share it with its ghostly owner.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    orb = f["orb"]
    act = f["activity"]
    place = world.setting.place
    sub, obj, pos = child.pronoun("subject"), child.pronoun("object"), child.pronoun("possessive")
    trait = child.adjectives[0] if child.adjectives else "curious"

    qa = [
        QAItem(
            question=f"Who did {trait} {child.id} meet in {place}?",
            answer=f"{trait.capitalize()} {child.id} met a ghost named {ghost.id} "
                   f"in {place}. The ghost held {orb.phrase_lower()}.",
        ),
        QAItem(
            question=f"What did {child.id} do with the glowing orb?",
            answer=f"{child.id} {act.gerund} it from the ghost. "
                   f"{sub} held the orb and felt mesmerized by its light.",
        ),
        QAItem(
            question=f"Why was the ghost upset with {child.id}?",
            answer=f"The ghost was upset because {child.id} borrowed the orb "
                   f"and did not give it back right away. The ghost wanted "
                   f"its treasure returned.",
        ),
    ]
    if f["conflict"]:
        qa.append(QAItem(
            question=f"How did {ghost.id} show {pos} anger?",
            answer=f"The ghost's voice became cold and thin, and its form flickered. "
                   f"It said, 'You steal my treasure, and I have nothing!'",
        ))
    if f["resolved"]:
        comp = f["compromise"]
        qa.append(QAItem(
            question=f"How did {child.id} and {ghost.id} solve their problem?",
            answer=f"They agreed to {comp.prep}. They {comp.tail}, and "
                   f"both felt better. The conflict turned into sharing.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("compromise"):
        tags.add("share")
        tags.add("conflict")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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


# --------------------------------------------------------------------------
# CLI helpers.
# --------------------------------------------------------------------------
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e._type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="old house",
        activity="borrow_orb",
        prize="orb",
        child_name="Lily",
        child_gender="girl",
        ghost_name="Wisp",
        trait="curious",
    ),
    StoryParams(
        place="attic",
        activity="borrow_orb",
        prize="orb",
        child_name="Ben",
        child_gender="boy",
        ghost_name="Ash",
        trait="daring",
    ),
    StoryParams(
        place="library",
        activity="borrow_orb",
        prize="orb",
        child_name="Maya",
        child_gender="girl",
        ghost_name="Shade",
        trait="spellbound",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return ("(No story: the only valid activity is borrowing the orb.)")


# --------------------------------------------------------------------------
# ASP twin – inline rules + facts.
# --------------------------------------------------------------------------
ASP_RULES = r"""
% The child borrows the orb, the ghost wants it back.
% A story is valid if the orb is the prize and borrowing is the activity.
valid(Place, Activity, Prize) :-
    setting(Place), affords(Place, Activity),
    activity(Activity), prize(Prize).

valid_story(Place, "borrow_orb", "orb", Gender) :-
    valid(Place, "borrow_orb", "orb"),
    child_gender(Gender).
"""


def asp_facts() -> str:
    import asp as _asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(_asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(_asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(_asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(_asp.fact("prize", pid))
    for g in sorted(set(CHILD_TYPES)):
        lines.append(_asp.fact("child_gender", g))
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# --------------------------------------------------------------------------
# Standard interface.
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost story world: a child, a ghost, a borrowed orb, and a sharing compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=CHILD_TYPES)
    ap.add_argument("--ghost-name")
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
    # Only one valid combo exists; fill in missing fields.
    place = args.place or rng.choice(list(SETTINGS.keys()))
    act = "borrow_orb"
    prize = "orb"
    child_gender = args.child_gender or rng.choice(CHILD_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=act,
        prize=prize,
        child_name=child_name,
        child_gender=child_gender,
        ghost_name=ghost_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES["borrow_orb"],
        PRIZES["orb"],
        child_name=params.child_name,
        child_type=params.child_gender,
        ghost_name=params.ghost_name,
    )
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
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} valid place/activity/prize combos ({len(stories)} with gender):")
        for place, act, prize in sorted(combos):
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:12} {prize:10}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place} ({p.ghost_name})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
