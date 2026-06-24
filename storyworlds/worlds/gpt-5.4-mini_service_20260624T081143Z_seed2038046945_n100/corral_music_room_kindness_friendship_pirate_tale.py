#!/usr/bin/env python3
"""
storyworlds/worlds/corral_music_room_kindness_friendship_pirate_tale.py
=======================================================================

A tiny pirate-tale storyworld set in a music room.

Premise:
- A child pirate and a friend want to make music in the music room.
- A noisy, slippery, or scattered setup threatens something they care about.
- Kindness and friendship turn the problem into a cooperative fix.
- The word "corral" appears naturally as the children gather loose things
  together and make a neat little corral for the music.

This world is intentionally small, classical, and state-driven. It uses typed
entities with physical meters and emotional memes, plus a declarative ASP twin
for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Eager shared results import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
INSTRUMENTS = ("drum", "bell", "flute", "tambourine", "xylophone")

# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------


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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the music room"
    affords: set[str] = field(default_factory=lambda: {"jam", "practice"})


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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "music_room": Setting(place="the music room", affords={"jam", "practice"}),
}

ACTIVITIES = {
    "jam": Activity(
        id="jam",
        verb="make merry music",
        gerund="making merry music",
        rush="rush to the instruments",
        mess="scattered",
        soil="scattered everywhere",
        zone={"floor"},
        keyword="jam",
        tags={"music", "sound"},
    ),
    "practice": Activity(
        id="practice",
        verb="practice a pirate tune",
        gerund="practicing a pirate tune",
        rush="dash to the drum and bell",
        mess="loud",
        soil="too loud and jumbled",
        zone={"floor", "table"},
        keyword="tune",
        tags={"music", "sound"},
    ),
}

PRIZES = {
    "sheet": Prize(
        label="sheet music",
        phrase="a neat sheet of music",
        type="sheet",
        region="table",
    ),
    "blocks": Prize(
        label="toy blocks",
        phrase="a pile of toy blocks",
        type="blocks",
        region="floor",
        plural=True,
    ),
    "shells": Prize(
        label="shell beads",
        phrase="shiny shell beads",
        type="shells",
        region="floor",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="basket",
        label="a wicker basket",
        covers={"floor"},
        guards={"scattered"},
        prep="set the loose pieces in a basket corral",
        tail="made a little corral with the basket and the blocks stayed put",
    ),
    Gear(
        id="cloth",
        label="a soft cloth cover",
        covers={"table"},
        guards={"loud"},
        prep="lay a soft cloth over the table",
        tail="spread the cloth and the music sheet stayed neat",
    ),
]

NAMES = ["Mara", "Nico", "Pia", "Jory", "Lena", "Tess"]
FRIENDS = ["mate", "friend", "crewmate", "pal"]


# ---------------------------------------------------------------------------
# Reasonableness gate
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
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not honestly threaten {prize.label}, "
        f"so there is no real problem to solve.)"
    )


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scattered", 0.0) >= THRESHOLD:
            for item in world.worn_items(actor):
                if item.plural and item.region in world.zone and ("scatter", item.id) not in world.fired:
                    world.fired.add(("scatter", item.id))
                    item.meters["scattered"] = 1.0
                    out.append(f"The little mess reached {item.label}.")
        if actor.meters.get("loud", 0.0) >= THRESHOLD:
            actor.memes["rush"] = actor.memes.get("rush", 0.0) + 1
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get(activity.mess, 0.0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little pirate who loved {activity.gerund} in {world.setting.place}. "
        f"{friend.id} was {hero.pronoun('possessive')} faithful {friend.type} and always stayed near."
    )
    world.say(
        f"They wanted to {activity.verb}, and the room held {prize.phrase} waiting by the floor."
    )


def tension(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(
            f"But the pirate noticed the {prize.label} might get {activity.soil}, and that would be a shame."
        )
        world.say(
            f'"Let us be kind to the room," {hero.id} said, while {friend.id} nodded with friendship in {hero.pronoun("possessive")} eyes.'
        )


def corral_fix(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(
        Entity(
            id=gear.id,
            kind="thing",
            type="gear",
            label=gear.label,
            protective=True,
            covers=set(gear.covers),
        )
    )
    if prize.region in gear.covers:
        g.worn_by = hero.id
    world.say(
        f"Together they {gear.prep}, making a corral for the loose bits."
    )
    world.say(
        f"With that friendly plan, they could {activity.verb} without ruining {prize.label}."
    )
    return g


def ending(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"Soon the pirate and the {friend.type} were {activity.gerund}, and {prize.label} stayed safe."
    )
    world.say(
        f"Kindness and friendship made the music room feel like a cozy little harbor."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )
    intro(world, hero, friend, activity, prize)
    world.para()
    tension(world, hero, friend, activity, prize)
    world.para()
    corral_fix(world, hero, friend, activity, prize)
    ending(world, hero, friend, activity, prize)
    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale set in a {f["setting"].place} where kindness and friendship help corral a small mess.',
        f'Tell a child-friendly story about {f["hero"].id} and {f["friend"].id} making music and using a corral to keep things neat.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, activity, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} want to do in the music room?",
            answer=f"They wanted to {activity.verb} in the music room while keeping {prize.label} safe.",
        ),
        QAItem(
            question=f"What did they do to corral the loose things?",
            answer=f"They used a little basket corral so the loose pieces would stay neat.",
        ),
        QAItem(
            question=f"How did kindness and friendship help the story end?",
            answer=f"Kindness and friendship helped them make a safe plan, so they could keep making music and {prize.label} stayed fine.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a corral?",
            answer="A corral is a fenced or gathered-in space that keeps things together and in one place.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and caring so you help someone or something instead of hurting it.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between people who care about each other and like spending time together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale in a music room about kindness, friendship, and a corral.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.friend,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


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

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place="music_room", activity="jam", prize="blocks", name="Mara", friend="pal"),
                  StoryParams(place="music_room", activity="practice", prize="sheet", name="Nico", friend="mate")]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
