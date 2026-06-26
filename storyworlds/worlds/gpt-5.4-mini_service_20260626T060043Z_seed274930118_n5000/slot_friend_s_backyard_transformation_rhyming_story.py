#!/usr/bin/env python3
"""
storyworlds/worlds/slot_friend_s_backyard_transformation_rhyming_story.py
=========================================================================

A small standalone storyworld about a slot in a friend's backyard and a gentle
transformation, told in a rhyming story style.

Seed tale premise:
- A child visits a friend's backyard.
- They discover a curious slot in a little box by the garden fence.
- The slot transforms one ordinary wearable thing into something brighter.
- A worried friend fears the treasured item may be lost or ruined.
- They choose a safer try, and the ending proves what changed.

The prose is intentionally compact, child-facing, and state-driven.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "a friend's backyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    turn: str
    weather: str
    keyword: str
    zone: set[str]
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
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

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


def _apply_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    prize = world.facts["prize"]
    gear = world.facts.get("gear")
    activity = world.facts["activity"]
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if prize.worn_by != hero.id:
        return out
    if world.facts.get("safe_try", False):
        sig = ("transform", prize.id, activity.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        prize.meters["bright"] = prize.meters.get("bright", 0.0) + 1.0
        prize.meters["changed"] = prize.meters.get("changed", 0.0) + 1.0
        world.facts["transformed"] = True
        if gear:
            out.append(f"With the extra cover on, the little slot gave the {prize.label} a bright new glow.")
        else:
            out.append(f"The slot gave the {prize.label} a bright new glow.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines = _apply_transform(world)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


SETTINGS = {
    "friend_backyard": Setting(
        place="a friend's backyard",
        affords={"slot_glow"},
    ),
}

ACTIVITIES = {
    "slot_glow": Activity(
        id="slot_glow",
        verb="slide a treasure into the slot",
        gerund="sliding a treasure into the slot",
        rush="rush to the little box",
        turn="turn the plain thing bright",
        weather="sunny",
        keyword="slot",
        zone={"torso", "hands"},
        tags={"slot", "transform", "bright"},
    ),
}

PRIZES = {
    "scarf": Prize(
        label="scarf",
        phrase="a soft blue scarf",
        type="scarf",
        region="torso",
    ),
    "apron": Prize(
        label="apron",
        phrase="a neat little apron",
        type="apron",
        region="torso",
    ),
    "gloves": Prize(
        label="gloves",
        phrase="garden gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="cover",
        label="a clear cover",
        covers={"torso", "hands"},
        prep="use a clear cover over the treasure",
        tail="slipped on the clear cover",
    )
]

GIRL_NAMES = ["Lia", "Mina", "Nora", "Pia", "Tess", "Zoe"]
BOY_NAMES = ["Cal", "Finn", "Jax", "Nico", "Theo", "Owen"]
TRAITS = ["brave", "curious", "cheerful", "gentle", "spry"]


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


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers:
            return gear
    return None


def tell(place: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_gender: str, friend_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, meters={}, memes={"curiosity": 1.0}))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", label=f"{friend_name}"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        worn_by=hero.id,
        meters={"clean": 1.0},
    ))

    world.say(
        f"{hero.id} walked into {world.setting.place}, where the breeze felt light and bright,"
        f" and {friend.id} pointed to a tiny slot by a painted box in sight."
    )
    world.say(
        f"{hero.id} loved the little {activity.keyword}, for every shiny turn felt like a tune,"
        f" and the backyard looked like a play-song pond beneath the afternoon moon."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {activity.verb}, to make {hero.pronoun('possessive')} {prize.label} glow and gleam,"
        f" but {friend.id} frowned and warned, \"That slot can be a tricky dream.\""
    )
    world.say(
        f"\"If it twists too hard, your {prize.label} may stay inside, and then we'd have a fright,\""
        f" {friend.id} said, soft and slow, to keep the plan warm, safe, and right."
    )

    world.para()
    world.say(
        f"{hero.id} nodded with a tiny grin, then chose a safer, slower way,"
        f" and {friend.id} found a clear cover so the treasure could still play."
    )
    gear = select_gear(activity, prize)
    if gear:
        gear_ent = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
            owner=hero.id,
            worn_by=hero.id,
        ))
        world.facts["gear"] = gear_ent
        world.say(
            f"They {gear.tail}, and with that gentle shield in place, the slot could do its bright, kind trick,"
            f" without any snag, without any shock, without a sticky pick."
        )
    else:
        world.say(
            f"They chose the easy path, and the little slot stayed calm and clear,"
            f" so the treasure could change without any worry near."
        )

    world.facts["safe_try"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last the {prize.label} came out twinkling, with a happy little shine,"
        f" and {hero.id} and {friend.id} laughed together, \"Look! It's yours and mine.\""
    )
    world.say(
        f"The backyard felt extra merry as the sun slid low and gold,"
        f" for a plain old thing had changed to bright, and the ending felt warm and bold."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=place,
        transformed=bool(world.facts.get("transformed")),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a child about {hero.id} visiting {friend.id} in a friend's backyard, where a slot can {activity.turn}.',
        f'Compose a gentle rhyming tale that includes the word "{activity.keyword}" and ends with {prize.label} coming back bright after a safe try.',
        f"Tell a tiny backyard transformation story where {hero.id} wants to {activity.verb}, but {friend.id} worries and they choose a safer plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    activity = f["activity"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} go to see the slot?",
            answer=f"{hero.id} went to {world.setting.place}, where {friend.id} showed a tiny slot by the box.",
        ),
        QAItem(
            question=f"What did {hero.id} want the slot to do to the {prize.label}?",
            answer=f"{hero.id} wanted the slot to {activity.turn} and make the {prize.label} glow and gleam.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry before the try?",
            answer=f"{friend.id} worried that the slot might catch the {prize.label} the wrong way, so they chose a safer plan.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The {prize.label} came out bright and twinkling, and the backyard felt merry and warm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slot?",
            answer="A slot is a narrow opening where something can be slipped in or passed through.",
        ),
        QAItem(
            question="What does transform mean?",
            answer="Transform means to change something into a different form or make it look new.",
        ),
        QAItem(
            question="What is a backyard?",
            answer="A backyard is the open space behind a house where children can play, garden, and explore.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="friend_backyard",
        activity="slot_glow",
        prize="scarf",
        name="Lia",
        gender="girl",
        friend="Mina",
        trait="curious",
    ),
    StoryParams(
        place="friend_backyard",
        activity="slot_glow",
        prize="gloves",
        name="Cal",
        gender="boy",
        friend="Theo",
        trait="cheerful",
    ),
]


KNOWLEDGE = {
    "slot": [("What is a slot?", "A slot is a narrow opening where something can be slipped in or passed through.")],
    "transform": [("What does transform mean?", "Transform means to change something into a different form or make it look new.")],
    "bright": [("What does bright mean?", "Bright means full of light or shining in a lively way.")],
}

KNOWLEDGE_ORDER = ["slot", "transform", "bright"]


ASP_RULES = r"""
% A prize is at risk when the activity's transformation touches the region it is worn on.
prize_at_risk(A, P) :- touches(A, R), worn_on(P, R).

% A compatible fix is gear that covers the at-risk region.
protects(G, A, P) :- gear(G), prize_at_risk(A, P), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("touches", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    ap = argparse.ArgumentParser(description="A rhyming backyard storyworld with a transforming slot.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (reasonableness_gate(act, pr) and select_gear(act, pr)):
            raise StoryError("No valid combination matches the given options.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.friend, params.trait)
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
