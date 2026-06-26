#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suggest_explanatory_willing_humor_rhyming_story.py
================================================================================================

A small storyworld for a gentle rhyming tale about a child who wants to do
something silly, a helpful helper who suggests a safer/funner way, and a
willing turn toward cooperation.

The seed idea behind this world:
- A child wants to make a noisy, messy, funny scene.
- Another character explains why the first plan is awkward.
- The helper suggests a better plan with humor and a rhyme-like rhythm.
- The child is willing to try the suggestion, and the story ends with a small
  joyful image showing what changed.

This script follows the Storyweavers contract:
- standalone stdlib script under storyworlds/worlds/
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

# ---------------------------------------------------------------------------
# World model
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
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
    weather: str
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"mix", "sprinkle"}),
    "garden": Setting(place="the garden", indoor=False, affords={"mix", "sprinkle", "stack"}),
    "porch": Setting(place="the porch", indoor=False, affords={"sprinkle", "stack"}),
}

ACTIVITIES = {
    "mix": Activity(
        id="mix",
        verb="mix a silly potion",
        gerund="mixing a silly potion",
        rush="stir the bowl too fast",
        mess="sticky",
        soil="sticky and splashed",
        zone={"torso", "hands"},
        weather="",
        keyword="mix",
        tags={"sticky", "funny"},
    ),
    "sprinkle": Activity(
        id="sprinkle",
        verb="sprinkle glitter",
        gerund="sprinkling glitter",
        rush="toss the glitter high",
        mess="sparkly",
        soil="sparkly all over",
        zone={"hands", "torso"},
        weather="",
        keyword="glitter",
        tags={"sparkly", "funny"},
    ),
    "stack": Activity(
        id="stack",
        verb="stack tall cups",
        gerund="stacking tall cups",
        rush="build the tower too wide",
        mess="wobbly",
        soil="tippy and topply",
        zone={"hands"},
        weather="",
        keyword="tower",
        tags={"wobbly", "funny"},
    ),
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a bright red apron",
        type="apron",
        region="torso",
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a clean yellow shirt",
        type="shirt",
        region="torso",
    ),
    "mittens": Prize(
        label="mittens",
        phrase="soft blue mittens",
        type="mittens",
        region="hands",
        plural=True,
    ),
    "hat": Prize(
        label="hat",
        phrase="a little paper hat",
        type="hat",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="smock",
        label="a paint smock",
        covers={"torso"},
        guards={"sticky", "sparkly"},
        prep="put on a paint smock first",
        tail="put on the paint smock",
    ),
    Gear(
        id="gloves",
        label="gloves",
        covers={"hands"},
        guards={"sticky", "sparkly", "wobbly"},
        prep="slip on gloves first",
        tail="slipped on the gloves",
        plural=True,
    ),
    Gear(
        id="tablecloth",
        label="an old tablecloth cape",
        covers={"torso"},
        guards={"sticky", "sparkly"},
        prep="wear an old tablecloth cape",
        tail="wore the old tablecloth cape",
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ivy", "Zoe", "Mia"]
BOY_NAMES = ["Ben", "Finn", "Leo", "Max", "Noah", "Eli"]
TRAITS = ["willing", "curious", "cheerful", "playful", "silly"]

# ---------------------------------------------------------------------------
# Helpers
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
        for act in setting.affords:
            activity = ACTIVITIES[act]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(activity, prize) and select_gear(activity, prize):
                    out.append((place, act, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not give a reasonable reason to worry "
        f"about {prize.label} in this setup, or the gear shelf has no clever fix "
        f"that truly fits both the mess and the worn region.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def prop_soil(world: World) -> None:
    for actor in world.characters():
        for kind in ("sticky", "sparkly", "wobbly"):
            if actor.m(kind) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[kind] = item.m(kind) + 1
                item.meters["dirty"] = item.m("dirty") + 1


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.m("dirty") >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.m(activity.mess) + 1
    actor.memes["joy"] = actor.e("joy") + 1
    prop_soil(world)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"willing": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    # Act 1
    world.say(f"{hero.id} was a {trait} little {hero.type} who loved a rhyme and a grin.")
    world.say(f"{hero.id} liked to {activity.gerund}, with a wiggle and a spin.")
    world.say(f"{hero.id}'s {parent.label_word} bought {hero.pronoun('object')} {prize.phrase}, bright and neat.")
    world.say(f"{hero.id} loved {prize.it()} very much and wore {prize.it()} on {hero.pronoun('possessive')} sweet little seat.")

    # Act 2
    world.para()
    world.say(f"One day at {world.setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, with a giggle and a shimmy hum.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f'"That could get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label_word} said with care.')
        world.say(f"Then {hero.pronoun('possessive')} helper gave a friendly wink and a joking, rhyming note:")
        world.say(f'"If you want to {activity.verb}, don\'t rush and don\'t dart; let us pick a smart start."')
        world.say(f"{hero.id} listened, nodded, and looked a bit pleased.")
    else:
        world.say(f"{hero.id}'s {parent.label_word} smiled and offered a small, funny suggestion.")

    # Act 3
    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize))
    gear_ent = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id,
        protective=True, covers=set(gear.covers), plural=gear.plural, worn_by=hero.id
    ))
    gear_ent.worn_by = hero.id
    world.say(f"{hero.id}'s {parent.label_word} suggested {gear.label}, and {hero.id} was willing to try.")
    world.say(f"They {gear.tail} and then went back to {activity.verb}.")
    world.say(f"This time, {hero.id} was {activity.gerund}, and {prize.label} stayed clean and tidy.")
    world.say(f"{hero.id} laughed, {hero.id}'s {parent.label_word} clapped, and the day went ding-ding-dee.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
        predicted_soil=activity.soil if pred["soiled"] else "",
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short rhyming story for a child named {hero.id} who wants to {act.verb} but needs a safer plan.',
        f'Write a humorous explanatory story where {hero.id} is willing to listen when {hero.pronoun("possessive")} {parent.label_word} suggests a better way to keep {prize.label} clean.',
        f'Create a gentle "suggest, explain, and try again" story using the word "{act.keyword or act.mess}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} suggest a different plan?",
            answer=(
                f"{parent.label_word.capitalize()} suggested a different plan because "
                f"{hero.pronoun('possessive')} {prize.label} could get {act.soil}."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} keep {prize.label} clean while still playing?",
            answer=f"{gear.label} helped {hero.id} keep {prize.label} clean while still {act.gerund}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel about the new plan?",
            answer=f"{hero.id} was willing to try it, and then felt happy about the funny little compromise.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "sticky": [("What does sticky mean?", "Sticky means a thing can cling to fingers or clothes and be hard to wipe off.")],
    "sparkly": [("What does sparkly mean?", "Sparkly means it shines with tiny bright points of light.")],
    "wobbly": [("What does wobbly mean?", "Wobbly means something shakes or leans and may fall over.")],
    "smock": [("What is a smock for?", "A smock is a loose cover that helps keep clothes clean.")],
    "gloves": [("Why do people wear gloves?", "People wear gloves to cover their hands and keep them cleaner or warmer.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({world.facts["gear"].id})
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
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
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kitchen", activity="mix", prize="apron", name="Mina", gender="girl", parent="mother", trait="willing"),
    StoryParams(place="garden", activity="sprinkle", prize="shirt", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="porch", activity="stack", prize="mittens", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming, humorous, explanatory story world about a willing compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.gender and "willing" or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:10} {prize:8}")
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
        header = f"### {sample.params.name}: {sample.params.activity} at {sample.params.place}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
