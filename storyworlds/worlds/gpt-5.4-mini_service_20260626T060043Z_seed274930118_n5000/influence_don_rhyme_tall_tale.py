#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/influence_don_rhyme_tall_tale.py
==============================================================================================================

A tall-tale story world about influence, donning gear, and a rhyming turn.

Premise:
- A child hears a big-voiced old storyteller whose rhymes carry influence.
- The child wants to do something daring in a windy, splashy, or dusty place.
- A caregiver worries about a prized item or outfit that would be ruined.
- The solution is a fitting thing to don before the adventure begins.

This world is intentionally small, classical, and constraint-checked:
- the daring action must plausibly threaten the prized item;
- the chosen gear must actually protect the at-risk part;
- the ending proves the change in state with a concrete image.

The prose style leans tall-tale: lively, slightly boastful, and lightly rhymed.
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


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
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
    place: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "riverbank": Setting(place="the riverbank", indoor=False, affords={"splash", "dash"}),
    "bluff": Setting(place="the bluff", indoor=False, affords={"wind", "dash"}),
    "fairground": Setting(place="the fairground", indoor=False, affords={"dust", "wind"}),
}

ACTIVITIES = {
    "splash": Activity(
        id="splash",
        verb="splash in the shallows",
        gerund="splashing in the shallows",
        rush="rush into the water",
        mess="wet",
        soil="soaked through",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="splash",
        tags={"water", "wet"},
    ),
    "wind": Activity(
        id="wind",
        verb="race the wind at the bluff",
        gerund="racing the wind",
        rush="dash up the bluff",
        mess="dusty",
        soil="dust-streaked",
        zone={"torso", "hat"},
        weather="blustery",
        keyword="wind",
        tags={"wind", "dust"},
    ),
    "dust": Activity(
        id="dust",
        verb="spin through the dust at the fairground",
        gerund="spinning through dust",
        rush="run straight for the ring",
        mess="dusty",
        soil="dust-covered",
        zone={"feet", "legs", "torso"},
        weather="dry",
        keyword="dust",
        tags={"dust"},
    ),
    "dash": Activity(
        id="dash",
        verb="dash over the muddy path",
        gerund="dashing over mud",
        rush="bolt down the path",
        mess="muddy",
        soil="mud-spattered",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="dash",
        tags={"mud", "wet"},
    ),
}

PRIZES = {
    "shoes": Prize("shoes", "bright little shoes", "shoes", "feet", plural=True),
    "hat": Prize("hat", "a feathered hat", "hat", "hat"),
    "shirt": Prize("shirt", "a clean blue shirt", "shirt", "torso"),
    "skirt": Prize("skirt", "a twirly skirt", "skirt", "legs", genders={"girl"}),
}

GEAR = [
    Gear("boots", "rubber boots", {"feet"}, {"wet", "muddy"}, "don the rubber boots", "came back with the rubber boots", plural=True),
    Gear("slicker", "a rain slicker", {"torso"}, {"wet"}, "don the rain slicker", "came back with the rain slicker"),
    Gear("coveralls", "dust coveralls", {"torso", "legs"}, {"dusty", "muddy"}, "don the coveralls", "came back in the coveralls", plural=True),
    Gear("brim", "a broad-brimmed hat", {"hat"}, {"dusty"}, "don the broad-brimmed hat", "came back with the broad-brimmed hat"),
]

GIRL_NAMES = ["Mabel", "Nell", "Ivy", "Lucy", "Dora", "June", "Ada"]
BOY_NAMES = ["Cal", "Pete", "Hank", "Will", "Tom", "Ben", "Jeb"]
TRAITS = ["bright-eyed", "stubborn", "spry", "cheerful", "quick-footed", "curious"]


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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not reasonably threaten {prize.label}, "
        f"or the gear catalog has no honest fix that covers {prize.region}.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender} item here; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# World verbs
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        sig = ("soak", item.id, activity.mess)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1.0
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {activity.soil}.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        meters={},
        memes={},
    ))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={},
        memes={},
    ))

    trait = next((t for t in (hero_traits or []) if t != "little"), "")
    hero_desc = f"little {trait} {hero.type}".strip()

    # Act 1
    world.say(
        f"Now {hero_name} was a {hero_desc} with a head full of sky and a grin full of light, "
        f"and {hero.pronoun().lower()} could hear a tall tale from a mile and a night."
    )
    world.say(
        f"Old {parent_type} {parent.id if parent.id != 'Parent' else 'Don'} had a voice like a fiddle and a drum; "
        f"{hero_name} said {hero.pronoun('subject')} could make the plain prairie hum."
    )
    world.say(
        f"{hero_name} loved {activity.gerund}, because it felt grand and free, "
        f"like a fox on a fence or a ship on the sea."
    )
    prize.worn_by = hero.id
    world.say(
        f"And {hero_name}'s {parent_type} had bought {hero.pronoun('object')} {prize_cfg.phrase}, "
        f"so fine and so proud it could shine in the sun."
    )

    # Act 2
    world.para()
    where = "inside" if setting.indoor else "out yonder"
    world.say(
        f"One blustery day, {hero_name} and the {parent_type} went {where} to {setting.place}, "
        f"where the air blew brisk and the horizon looked done."
    )
    world.say(
        f"{hero_name} wanted to {activity.verb}, and old Don's rhyme had a mighty influence, "
        f"so {hero.pronoun()} leaned toward the fun."
    )
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(
            f"\"You'll get your {prize.label} {activity.soil},\" said the {parent_type}, "
            f"\"and then I'll have extra work before the day is through.\""
        )
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1.0
    world.say(
        f"But {hero_name} still tried to {activity.rush}, bold as a bell, "
        f"when the wind began to whistle and the dust began to spool."
    )
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1.0
    world.say(
        f"The {parent_type} caught {hero.pronoun('possessive')} hand and held it tight, "
        f"for love can be steady as a mule and as cool."
    )

    # Act 3
    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No compatible gear exists for this story combination.")
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        worn_by=hero.id,
        meters={},
        memes={},
    ))
    world.say(
        f"Then the {parent_type} smiled and said, \"Don't fret nor frown; "
        f"let's {gear.prep}, and we'll be right down.\""
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    _do_activity(world, hero, activity, narrate=False)
    world.say(
        f"{hero_name}'s eyes lit up like lanterns in a row, and {hero.pronoun()} hugged "
        f"the {parent_type} with a happy crow."
    )
    world.say(
        f"Soon {hero_name} was {activity.gerund}, the {prize.label} stayed clean and bright, "
        f"and the whole wide world rang merry and light."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=g,
        conflict=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "water": [
        ("What is a shallow place in a river called?", "A shallow place in a river is a spot where the water is not very deep, so boots or bare feet may splash there."),
    ],
    "wind": [
        ("What does wind do?", "Wind is moving air. It can push hats, rattle windows, and make people hold on to their things."),
    ],
    "dust": [
        ("What is dust?", "Dust is made of tiny dry bits that can puff up and stick to clothes when someone runs through it."),
    ],
    "mud": [
        ("What is mud?", "Mud is wet dirt. It can splash onto shoes and clothes and leave a messy stain."),
    ],
    "wet": [
        ("Why do rain boots help in puddles?", "Rain boots help because they keep feet dry when water splashes around."),
    ],
    "boots": [
        ("What are boots for?", "Boots protect feet and help keep them dry or clean when the ground is wet or muddy."),
    ],
    "slicker": [
        ("What does a rain slicker do?", "A rain slicker helps keep the body dry when rain or spray comes down."),
    ],
    "coveralls": [
        ("Why wear coveralls when things are dusty?", "Coveralls help keep clothes from getting dusty or muddy during rough play."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short tall-tale story for a child about {hero.id} hearing a rhyme that can influence choices, and include the word "influence".',
        f"Tell a lively story where {hero.id} wants to {act.verb} but must don the right gear so {hero.pronoun('possessive')} {prize.label} stays clean.",
        f'Write a rhyming little adventure where a child is told to don something before playing in a risky place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    pos = hero.pronoun("possessive")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little child who loved to {act.verb} and who listened to the {parent.label} and the old rhyme.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}. The idea came with a strong influence from the tall tale, but it was still a risky thing to try.",
        ),
        QAItem(
            question=f"What did the {parent.label} ask {hero.id} to don before the adventure?",
            answer=f"The {parent.label} asked {hero.id} to don {gear.label}, so {pos} {prize.label} would stay safe and clean.",
        ),
        QAItem(
            question=f"Why did the {parent.label} worry about {pos} {prize.label}?",
            answer=f"The {parent.label} worried because if {hero.id} went on with {act.gerund}, {pos} {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{sub.capitalize()} ended up {act.gerund} in the right gear, with {pos} {prize.label} still clean and the {parent.label} smiling nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

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
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about influence and donning the right gear.")
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
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
    StoryParams(place="riverbank", activity="splash", prize="shoes", name="Mabel", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="bluff", activity="wind", prize="shirt", name="Hank", gender="boy", parent="father", trait="spry"),
    StoryParams(place="fairground", activity="dust", prize="hat", name="Ivy", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="riverbank", activity="dash", prize="shirt", name="Jeb", gender="boy", parent="father", trait="stubborn"),
]


def asp_facts_for_verify() -> str:
    return asp_facts()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:8} {prize:8} [{', '.join(genders)}]")
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
