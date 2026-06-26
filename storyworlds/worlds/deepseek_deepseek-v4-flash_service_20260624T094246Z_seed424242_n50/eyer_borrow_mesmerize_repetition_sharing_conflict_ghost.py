#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/eyer_borrow_mesmerize_repetition_sharing_conflict_ghost.py
=================================================================================================================================

A standalone *story world* sketch for a gentle ghost story about borrowing,
mesmerizing eyes, a repeated whisper, sharing a secret, and a conflict resolved
through sharing.

Domain elements:
  - "eyer" : a child (or ghost) with watchful, big eyes; here we use "Eyer" as a
    child name.
  - "borrow" : the ghost takes (borrows) a beloved object.
  - "mesmerize" : the ghost's repeated whisper enchants the child.
  - Repetition : the ghost's refrain "Borrow? Borrow?" is said over and over.
  - Sharing : the child shares a story or a treat with the ghost.
  - Conflict : the child is torn between fear and curiosity, then refuses to
    give the object away.
  - Style: Ghost Story (child-friendly, spooky but gentle, resolved with warmth).
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

# ---------------------------------------------------------------------------
# Entity (reused from puddles.py style)
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


@dataclass
class Setting:
    place: str = "the old library"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """A spooky, shared activity the ghost and child can do."""
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str          # what gets affected (e.g. "mesmerized", "frightened")
    soil: str          # how the prize gets ruined (e.g. "covered in cobwebs")
    zone: set[str]
    weather: str = "night"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The object the child loves and the ghost wants to borrow."""
    label: str
    phrase: str
    type: str
    region: str = "torso"   # not used for ghost, but required for consistency
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    """Protective item that shields against mesmerization or fright."""
    id: str
    label: str
    covers: set[str]        # regions protected
    guards: set[str]        # mess kinds neutralized
    prep: str               # "hold my hand and say the secret rhyme"
    tail: str               # closing action
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
        self.weather: str = setting.weather if hasattr(setting, 'weather') else "night"
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mesmerize(world: World) -> list[str]:
    """Ghost's repeated whisper increases child's mesmerized meter."""
    out: list[str] = []
    ghost = world.entities.get("Ghost")
    child = world.entities.get("Eyer")
    if ghost is None or child is None:
        return out
    if ghost.memes["whispering"] < THRESHOLD:
        return out
    sig = ("mesmerize", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["mesmerized"] += 1
    out.append(f"The whisper grew louder: 'Borrow? Borrow?' and {child.id} felt her eyes grow heavy.")
    return out


def _r_borrow(world: World) -> list[str]:
    """Ghost borrows the beloved object (prize) and child's fright increases."""
    out: list[str] = []
    ghost = world.entities.get("Ghost")
    prize = world.entities.get("prize")
    child = world.entities.get("Eyer")
    if not all([ghost, prize, child]):
        return out
    if prize.owner != child.id or ghost.owner is not None:
        return out
    sig = ("borrow", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.owner = prize.id
    ghost.memes["has_prize"] += 1
    child.meters["fright"] += 1
    out.append(f"'{prize.label} is mine now,' whispered the ghost, and "
               f"the {prize.type} vanished into the mist.")
    return out


def _r_fright_conflict(world: World) -> list[str]:
    """If child is frightened and prize is taken, conflict rises."""
    child = world.entities.get("Eyer")
    if child is None:
        return []
    if child.meters["fright"] >= THRESHOLD and child.meters["mesmerized"] >= THRESHOLD:
        sig = ("conflict", child.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="mesmerize", tag="supernatural", apply=_r_mesmerize),
    Rule(name="borrow", tag="supernatural", apply=_r_borrow),
    Rule(name="fright_conflict", tag="emotional", apply=_r_fright_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers (reasonableness)
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    # For ghost stories, any prize is at risk (always borrow)
    return True


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    # Must be a gear that guards mesmerization and covers the child's "soul"
    for gear in GEAR:
        if "mesmerized" in gear.guards and "soul" in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Verb functions (screenplay)
# ---------------------------------------------------------------------------
def ghost_whispers(world: World, ghost: Entity) -> None:
    ghost.memes["whispering"] += 1
    propagate(world)
    world.say(f"A soft voice repeated, 'Borrow? Borrow?' The words seemed to hang in the air.")


def ghost_repeat(world: World, ghost: Entity) -> None:
    # Repetition: the ghost says the phrase again
    ghost.memes["whispering"] += 1
    propagate(world)
    world.say(f"'Borrow? Borrow?' The whisper was louder this time, "
              f"like a wind brushing against {ghost.pronoun('possessive')} ears.")


def child_curious(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"{child.id} blinked her big, curious eyes. "
              f"'Who are you?' she asked the shadow in the corner.")


def ghost_borrows(world: World, ghost: Entity, prize: Entity) -> None:
    ghost.memes["whispering"] += 1
    propagate(world)
    world.say(f"The ghost floated toward the {prize.label}. "
              f"'I will borrow this,' it hissed.")


def child_conflict(world: World, child: Entity) -> None:
    if child.memes["conflict"] >= THRESHOLD:
        world.say(f"{child.id} shook her head. 'No! That's mine! You can't have it!' "
                  f"But her voice trembled as she spoke.")


def share_secret(world: World, child: Entity, ghost: Entity) -> None:
    # Sharing resolves conflict: child offers a story or a treat
    world.say(f"Then {child.id} remembered something Grandmother had said: "
              f"'If you share a secret with a ghost, it becomes your friend.'")
    world.say(f"'{child.id} took a deep breath and said, 'I'll share my favorite "
              f"bedtime story with you if you give back my {prize.label}.'")
    # After sharing, ghost returns item and mesmerization fades
    ghost.memes["whispering"] = 0.0
    child.meters["mesmerized"] = 0.0
    child.meters["fright"] = 0.0
    child.memes["conflict"] = 0.0
    ghost.owner = None
    world.say(f"The ghost listened. Its eyes softened. 'Borrow? No… I will share.' "
              f"The {prize.label} shimmered back into existence.")


def ghost_departs(world: World, child: Entity, ghost: Entity) -> None:
    world.say(f"The first light of dawn crept through the curtains. "
              f"The ghost smiled and faded, leaving only a whisper: 'Share again soon.' "
              f"{child.id} hugged her {prize.label} and smiled.")


# ---------------------------------------------------------------------------
# Tell function (three‑act story)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Eyer", child_gender: str = "girl",
         child_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    # child
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        traits=["little"] + (child_traits or ["curious", "brave"]),
        label=child_name,
    ))
    # ghost
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        traits=["whispering"],
        label="the ghost",
    ))
    # prize (the beloved object)
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(child=child, ghost=ghost, prize=prize,
                       prize_cfg=prize_cfg, activity=activity, setting=setting)

    # Act 1: Setting + child loves her prize; ghost arrives
    world.say(f"In a quiet corner of {setting.place}, a little {child_gender} named "
              f"{child_name} loved to sit and read.")
    world.say(f"{child_name} had a special {prize.label} that {child.pronoun()} "
              f"kept close: {prize.phrase}.")
    world.para()
    ghost_whispers(world, ghost)

    # Act 2: Ghost repeats, child curious, ghost takes prize
    ghost_repeat(world, ghost)
    child_curious(world, child, ghost)
    ghost_borrows(world, ghost, prize)
    propagate(world)  # apply mesmerize & borrow rules
    world.para()
    child_conflict(world, child)

    # Act 3: Sharing resolves
    world.say(f"The room grew colder. The ghost repeated, 'Borrow? Borrow?'")
    share_secret(world, child, ghost)
    ghost_departs(world, child, ghost)

    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the dusty attic", indoor=True, affords={"whisper", "borrow"}),
    "library": Setting(place="the old library", indoor=True, affords={"whisper", "share"}),
    "bedroom": Setting(place="the shadowy bedroom", indoor=True, affords={"whisper", "borrow"}),
}

ACTIVITIES = {
    "whisper": Activity(
        id="whisper",
        verb="hear the ghost's whisper",
        gerund="listening to whispers",
        rush="move toward the voice",
        mess="mesmerized",
        soil="lost and dizzy",
        zone={"ears", "soul"},
        weather="night",
        keyword="whisper",
        tags={"whisper", "ghost"},
    ),
    "borrow": Activity(
        id="borrow",
        verb="let the ghost borrow your toy",
        gerund="letting the ghost borrow",
        rush="watch it float away",
        mess="fright",
        soil="shadowy and empty",
        zone={"hands"},
        weather="night",
        keyword="borrow",
        tags={"borrow", "ghost"},
    ),
}

GEAR = [
    Gear(
        id="secret_word",
        label="a secret sharing word",
        covers={"soul"},
        guards={"mesmerized", "fright"},
        prep="say a secret word from Grandmother's tale",
        tail="spoke the secret word together",
    ),
]

PRIZES = {
    "teddy": Prize(
        label="teddy bear",
        phrase="a soft brown teddy bear with a red bow",
        type="teddy",
        region="torso",
    ),
    "book": Prize(
        label="storybook",
        phrase="a picture book about friendly ghosts",
        type="book",
        region="torso",
    ),
    "blanket": Prize(
        label="favorite blanket",
        phrase="a soft blue blanket with moons and stars",
        type="blanket",
        region="torso",
        plural=False,
    ),
}

GIRL_NAMES = ["Eyer", "Luna", "Stella", "Mira"]
BOY_NAMES = ["Eyer", "Orion", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id in ACTIVITIES:
            for prize_id in PRIZES:
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
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generators
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "whisper": [("What is a whisper?",
                 "A whisper is a very quiet voice, like a secret in the dark.")],
    "ghost": [("What is a ghost in stories?",
               "In stories, a ghost is a gentle spirit that sometimes floats "
               "and whispers, but can become a friend.")],
    "borrow": [("What does 'borrow' mean?",
                "To borrow means to take something for a little while, "
                "and then give it back.")],
    "share": [("Why is sharing good?",
               "Sharing makes both people feel happy, and can turn a stranger "
               "into a friend.")],
}
KNOWLEDGE_ORDER = ["whisper", "ghost", "borrow", "share"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    prize = f["prize_cfg"]
    return [
        f"Write a gentle ghost story for a young child about a little {child.type} "
        f"named {child.id} who meets a whispering ghost that wants to borrow "
        f"their {prize.label}.",
        f"Tell a story where a {child.type} shares a secret and turns a fear into friendship.",
        f"Write a short story that uses the words 'whisper', 'borrow', and 'share'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    sub, obj, pos = child.pronoun("subject"), child.pronoun("object"), child.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the little {child.type} in {setting.place}?",
            answer=f"The little {child.type} is {child.id}. {sub} had a special {prize.label}.",
        ),
        QAItem(
            question=f"What did the ghost keep repeating?",
            answer=f"The ghost kept repeating 'Borrow? Borrow?' in a soft whisper.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem with the ghost?",
            answer=f"{child.id} shared a secret: {sub} offered to tell the ghost a favorite "
                   f"story. After sharing, the ghost returned the {prize.label} and became friendly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
        if getattr(e, 'protective', False):
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", activity="whisper", prize="teddy",
                name="Eyer", gender="girl", trait="curious"),
    StoryParams(place="library", activity="borrow", prize="book",
                name="Eyer", gender="girl", trait="brave"),
]


def resolve_params(args, rng):
    if args.activity and args.prize:
        # No rejection needed; all combos valid in this domain
        pass
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    gender = args.gender or "girl"
    name = args.name or "Eyer"
    trait = rng.choice(["curious", "brave", "gentle"])
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser():
    ap = argparse.ArgumentParser(
        description="Story world: a child, a ghost, a whisper, a share.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name", default="Eyer")
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


# ---------------------------------------------------------------------------
# ASP twin (simplified but functional)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P).
protects(G,A,P) :- gear(G), mess_of(A,M), guards(G,M), covers(G,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- setting(Place), activity(A), prize(P), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), gender(G).
"""


def asp_facts():
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        for m in [ACTIVITIES[aid].mess]:
            lines.append(asp.fact("mess_of", aid, m))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        for g in PRIZES[pid].genders:
            lines.append(asp.fact("gender", g))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for r in g.covers:
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show):
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos():
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify():
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


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid (place, activity, prize) combos:")
        for p, a, r in triples:
            print(f"  {p:10} {a:10} {r:10}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
