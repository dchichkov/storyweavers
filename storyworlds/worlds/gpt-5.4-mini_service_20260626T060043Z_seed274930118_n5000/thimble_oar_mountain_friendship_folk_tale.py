#!/usr/bin/env python3
"""
storyworlds/worlds/thimble_oar_mountain_friendship_folk_tale.py
=================================================================

A small, self-contained storyworld for a folk-tale friendship about a mountain,
a thimble, and an oar.

Seed image:
- A little maker on a mountain keeps a treasured thimble.
- A friend with an oar helps when the way becomes hard.
- The ending proves friendship changed what the travelers could do together.

This world is intentionally small and constraint-checked. It offers a few
reasonable, grounded variants rather than many weak ones.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "sister"}
        male = {"boy", "man", "father", "grandfather", "brother"}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet",):
            if actor.m(mess) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.m(mess) + 1
                item.meters["dirty"] = item.m("dirty") + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and dirty.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.m("dirty") < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get(item.caretaker)
        helper.meters["workload"] = helper.m("workload") + 1
        out.append(f"That would make more work for {helper.label}.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("need_friend", 0.0) < THRESHOLD:
            continue
        sig = ("friendship", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] = actor.e("hope") + 1
        out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("work", _r_work), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if s != "__friendship__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the mountain path":
        return "The mountain path twisted up and down like a brown ribbon."
    if setting.place == "the mountain lake":
        return "The mountain lake lay still, with reeds at its edge and mist on its face."
    return f"{setting.place.capitalize()} was quiet and high above the rest of the land."


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.m("dirty") >= THRESHOLD), "workload": sum(e.m("workload") for e in sim.characters())}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.m(activity.mess) + 1
    actor.memes["joy"] = actor.e("joy") + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who lived by the mountain and loved a neat stitch. "
        f"{friend.id} was {friend.phrase}, and the two were old friends."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.e("love") + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and kept it close, "
        f"as if a small bright helper lived inside the hand."
    )


def wants(world: World, hero: Entity, activity: Activity, friend: Entity) -> None:
    hero.memes["desire"] = hero.e("desire") + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, and {friend.id} wanted to help, "
        f"because true friends climb the same hard hill together."
    )


def warn(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"You will get your {prize.label} {activity.soil}," {hero.id} said to {hero.pronoun("object")}self, '
        f"looking at the steep way ahead."
    )
    return True


def struggle(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["need_friend"] = hero.e("need_friend") + 1
    world.say(
        f"The way turned rough. {hero.id} tried to {activity.rush}, but the path was hard and the wind was high."
    )


def offer_friendship(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            kind="thing",
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=friend.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{friend.id} smiled and said, "I have an oar for the water below. '
        f'Let us {gear_def.prep} and go the safe way."'
    )
    return gear_def


def accept(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.e("joy") + 1
    hero.memes["love"] = hero.e("love") + 1
    hero.memes["need_friend"] = 0.0
    world.say(
        f"{hero.id} laughed and took {friend.id}'s hand. "
        f'They went on together, and {hero.id} said, "A friend is a lantern on a mountain road."'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} safe and clean, "
        f"while {friend.id} kept the oar ready beside the water."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, phrase="a steady friend with an oar"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=friend.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero, friend)
    loves_prize(world, hero, prize)

    world.para()
    world.say(f"One day, {hero.id} and {friend.id} went to {setting.place}.")
    world.say(setting_detail(setting, activity))
    wants(world, hero, activity, friend)
    warn(world, hero, activity, prize)
    struggle(world, hero, activity)

    world.para()
    gear_def = offer_friendship(world, friend, hero, activity, prize)
    if gear_def:
        accept(world, hero, friend, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "mountain_path": Setting(place="the mountain path", indoor=False, affords={"cross_water", "carry_load"}),
    "mountain_lake": Setting(place="the mountain lake", indoor=False, affords={"cross_water"}),
    "mountain_village": Setting(place="the mountain village", indoor=False, affords={"carry_load"}),
}

ACTIVITIES = {
    "cross_water": Activity(
        id="cross_water",
        verb="cross the water below",
        gerund="crossing the water",
        rush="wade to the far bank",
        mess="wet",
        soil="soaked through",
        zone={"feet", "legs"},
        weather="misty",
        keyword="water",
        tags={"water", "oar", "mountain"},
    ),
    "carry_load": Activity(
        id="carry_load",
        verb="carry a bundle up the mountain",
        gerund="carrying bundles",
        rush="haul the bundle uphill",
        mess="wet",
        soil="wind-blown and damp",
        zone={"torso", "legs"},
        weather="windy",
        keyword="bundle",
        tags={"mountain", "friendship"},
    ),
}

PRIZES = {
    "thimble": Prize(
        label="thimble",
        phrase="a tiny silver thimble",
        type="thimble",
        region="fingers",
        genders={"girl", "boy"},
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a wool cloak with a blue clasp",
        type="cloak",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="oar",
        label="an oar",
        covers={"feet"},
        guards={"wet"},
        prep="take the oar as a steady pole in the boat",
        tail="rowed carefully with the oar and kept to the shallow path",
    ),
    Gear(
        id="cloakpin",
        label="a cloak pin",
        covers={"torso"},
        guards={"wet"},
        prep="fasten the cloak pin tight",
        tail="kept the cloak pin fastened all the way",
    ),
]

HERO_NAMES = ["Nina", "Milo", "Tara", "Eli", "Pip", "Mara", "Jory", "Sana"]
FRIEND_NAMES = ["Bran", "Willow", "Huck", "Linn", "Oren", "Nell", "Bram", "Faye"]
TRAITS = ["gentle", "brave", "kind", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["friend"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short folk tale for a child about "{hero.id}", "{friend.id}", '
        f'the mountain, and a {prize.label}.',
        f"Tell a gentle friendship story where {hero.id} wants to {act.verb} "
        f"and {friend.id} helps with an oar.",
        f'Write a mountain story that includes the words "thimble", "oar", and '
        f'"friendship" in a warm, old-time style.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who were the two friends in the mountain tale?",
            answer=f"The friends were {hero.id} and {friend.id}. They traveled together because friendship made the steep way easier.",
        ),
        QAItem(
            question=f"What small thing did {hero.id} love and keep close?",
            answer=f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}. It was a tiny treasure worth protecting on the mountain.",
        ),
        QAItem(
            question=f"Why did the path become tricky for {hero.id}?",
            answer=f"The path became tricky because {hero.id} wanted to {act.verb}, and the way was steep and wet enough to threaten {hero.pronoun('possessive')} {prize.label}.",
        ),
    ]
    if f.get("resolved") and gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the friends?",
                answer=f"They used {gear.label} to keep the crossing steady, so {hero.id} could go on without losing {hero.pronoun('possessive')} {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"At the end, {hero.id} was {act.gerund}, {prize.label} stayed safe, and the two friends were glad they had helped one another.",
            )
        )
    return qa


KNOWLEDGE = {
    "thimble": [("What is a thimble?", "A thimble is a small metal cap worn on a finger to help push a needle while sewing.")],
    "oar": [("What is an oar?", "An oar is a long tool used to move a boat through water.")],
    "mountain": [("What is a mountain?", "A mountain is a very high hill with steep sides and a top far above the land around it.")],
    "friendship": [("What is friendship?", "Friendship is the kind bond between people who care for each other and help each other.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"thimble", "oar", "mountain", "friendship"})
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale friendship world with a mountain, a thimble, and an oar.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not endanger the {prize.label} here.)"
    return f"(No story: no gear in this world can reasonably protect the {prize.label} from that crossing.)"


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
    place, activity, prize = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    hero_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = "boy" if hero_type == "girl" else "girl"
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
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


CURATED = [
    StoryParams("mountain_path", "cross_water", "thimble", "Nina", "girl", "Bran", "boy", "gentle"),
    StoryParams("mountain_lake", "cross_water", "cloak", "Milo", "boy", "Willow", "girl", "brave"),
    StoryParams("mountain_village", "carry_load", "cloak", "Tara", "girl", "Huck", "boy", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:16} {act:12} {prize:8}  [{', '.join(genders)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
