#!/usr/bin/env python3
"""
storyworlds/worlds/qrs_dangle_sham_friendship_pirate_tale.py
=============================================================

A small pirate-tale storyworld about friendship, a dangling hazard, and a sham
that turns into a shared laugh and a safer plan.

Seed tale sketch:
---
A young pirate loved to dangle from a rope on a sunny dock with a good friend.
One day they found a sham treasure map and nearly rushed after it. The friend
noticed the fake clue, steadied the rope, and helped them choose a real way to
play together. The day ended with both pirates laughing, safer and closer than
before.

Causal state updates:
---
    dangle near the mast        -> actor.meters["wobble"] += 1 ; actor.memes["thrill"] += 1
    risky dangle + worn prize   -> prize.meters["tangled"] += 1 ; prize.meters["dirty"] += 1
    spotted sham                -> actor.memes["doubt"] += 1 ; friend.memes["trust"] += 1
    friend steadies rope        -> actor.memes["calm"] += 1 ; actor.memes["trust"] += 1
    shared safe choice          -> actor.memes["joy"] += 1 ; friend.memes["joy"] += 1

Narrative instruments:
---
    friendship is modeled as trust, calm, and shared joy
    dangle is the physical risky move that may tangle or dirty a hanging prize
    sham is the false clue that creates the turn and the honest warning
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"dirty": 0.0, "tangled": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "trust": 0.0, "doubt": 0.0, "calm": 0.0, "thrill": 0.0}

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


@dataclass
class Setting:
    place: str
    salt_air: str
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
    keyword: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

SETTINGS = {
    "dock": Setting(place="the dock", salt_air="salty", affords={"dangle"}),
    "deck": Setting(place="the deck", salt_air="briny", affords={"dangle"}),
    "cove": Setting(place="the cove", salt_air="windy", affords={"dangle"}),
}

ACTIVITIES = {
    "dangle": Activity(
        id="dangle",
        verb="dangle from the rope",
        gerund="dangling from the rope",
        rush="swing out too fast",
        mess="tangled",
        soil="all tangled up",
        zone={"hands", "torso"},
        keyword="dangle",
        tags={"dangle", "rope", "ship"},
    )
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a bright brass lantern",
        type="lantern",
        region="torso",
    ),
    "flag": Prize(
        label="flag",
        phrase="a little red flag",
        type="flag",
        region="torso",
    ),
    "map": Prize(
        label="map",
        phrase="a folded treasure map",
        type="map",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="knot",
        label="a strong knot",
        covers={"hands", "torso"},
        guards={"tangled"},
        prep="tie a strong knot first",
        tail="stayed near the rope and kept the knot tight",
    )
]

GIRL_NAMES = ["Mina", "Ria", "Nell", "Tess", "Lina"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Bram", "Owen"]
TRAITS = ["brave", "curious", "cheerful", "spunky", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters["wobble"] = actor.meters.get("wobble", 0.0) + 1
    actor.memes["thrill"] += 1


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"dirty": 0, "tangled": 0}, memes={"joy": 0, "trust": 0, "doubt": 0, "calm": 0, "thrill": 0}))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, meters={"dirty": 0, "tangled": 0}, memes={"joy": 0, "trust": 0, "doubt": 0, "calm": 0, "thrill": 0}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a little {params.trait} pirate who loved the salt air at {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, and {friend.id} loved to sail beside {hero.pronoun('object')}.")
    world.say(f"That day, {friend.id} brought {hero.pronoun('object')} {prize.phrase} to wear like a prize on the voyage.")

    world.para()
    world.say(f"On the {setting.place}, {hero.id} wanted to {activity.verb} because the rope looked like a daring game.")
    world.say(f"{hero.pronoun().capitalize()} reached for the line and began {activity.gerund} while {friend.id} watched nearby.")
    _do_activity(world, hero, activity)

    sham_seen = False
    if params.prize == "map":
        sham_seen = True
        hero.memes["doubt"] += 1
        friend.memes["trust"] += 1
        world.say(f"Then they found a sham map tucked under a crate, and {hero.id} frowned at the fake gold marks.")
        world.say(f'"That map is a sham," {friend.id} said softly. "A real pirate can tell a false clue from a true one."')

    world.para()
    if prize.meters.get("tangled", 0) < THRESHOLD and activity.id == "dangle":
        prize.meters["tangled"] += 1
        prize.meters["dirty"] += 1

    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No safe pirate-friendship fix exists for this story.")
    world.say(f"{friend.id} smiled and said, \"Let's {gear.prep}.\"")
    world.say(f"So they did, and {friend.id} kept the knot steady while {hero.id} chose a safer swing.")
    hero.memes["calm"] += 1
    hero.memes["trust"] += 1
    friend.memes["joy"] += 1
    hero.memes["joy"] += 1

    world.say(
        f"After that, {hero.id} was still {activity.gerund}, but {hero.pronoun('possessive')} {prize.label} stayed clean and neat."
    )
    world.say(
        f"The two friends sailed on laughing, with the rope tied tight and the sham forgotten like a silly cloud."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        sham_seen=sham_seen,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "dangle": [
        ("What does it mean to dangle from a rope?", "To dangle from a rope means to hang or swing from it, usually with your feet or body off the ground."),
    ],
    "sham": [
        ("What is a sham?", "A sham is something that is fake or not real, even if it tries to look true."),
    ],
    "friendship": [
        ("What does friendship mean?", "Friendship means being kind, loyal, and happy to help and play together."),
    ],
    "rope": [
        ("Why do sailors use rope on a ship?", "Sailors use rope to tie things down, lift things, and keep the ship safe and steady."),
    ],
    "ship": [
        ("What is a pirate ship?", "A pirate ship is a boat pirates use to sail the sea, carry supplies, and chase adventures."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short pirate tale for a little child using the words "{act.keyword}", "sham", and "friendship".',
        f"Tell a gentle story where {hero.id} and {friend.id} share a pirate adventure, notice a sham clue, and choose a safer way to {act.verb}.",
        f"Write a tiny sea story about two friends on a ship, a dangling rope, and a fake clue that turns into a happy plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who were the two pirate friends in the story?",
            answer=f"The pirate friends were {hero.id} and {friend.id}. They stayed together and helped each other on the dock.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the rope?",
            answer=f"{hero.id} wanted to {act.verb}. It looked fun, but it needed a safer plan so nobody got tangled.",
        ),
        QAItem(
            question=f"What was the sham clue?",
            answer=f"The sham clue was a fake treasure map. It looked exciting, but it was not real.",
        ),
        QAItem(
            question=f"How did friendship help at the end?",
            answer=f"Friendship helped because {friend.id} warned {hero.id}, kept the knot steady, and made the adventure safer and happier.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} by the end?",
            answer=f"The {prize.label} stayed clean and neat, even after the rope play and the silly sham clue.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("friendship")
    if world.facts.get("sham_seen"):
        tags.add("sham")
    out: list[QAItem] = []
    for tag in ["dangle", "sham", "friendship", "rope", "ship"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale friendship world with a dangle hazard and a sham clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate tale combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender,
                       friend=friend, friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.region:
                bits.append(f"region={e.region}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="dock", activity="dangle", prize="map", name="Pip", gender="boy", friend="Mina", friend_gender="girl", trait="curious"),
    StoryParams(place="deck", activity="dangle", prize="lantern", name="Nell", gender="girl", friend="Jory", friend_gender="boy", trait="brave"),
    StoryParams(place="cove", activity="dangle", prize="flag", name="Bram", gender="boy", friend="Ria", friend_gender="girl", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible pirate-tale combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
