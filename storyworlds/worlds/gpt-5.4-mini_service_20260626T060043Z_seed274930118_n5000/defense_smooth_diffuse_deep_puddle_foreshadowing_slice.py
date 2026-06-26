#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/defense_smooth_diffuse_deep_puddle_foreshadowing_slice.py
===========================================================================================================

A small slice-of-life storyworld about a child, a deep puddle, and a gentle
defense that keeps the day calm. The premise is built from the seed words
defense, smooth, and diffuse, with foreshadowing used as a story instrument:
the needed fix is hinted before it is chosen, then pays off in the ending image.

The world is intentionally narrow:
- one child
- one parent
- one puddle-prone walk
- one fragile/wet prize
- one compatible defense

The simulated state matters: the hero's desire rises, the puddle risk is
predicted, the parent worries for a concrete reason, and the chosen defense
actually changes the outcome.
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
        for key in ["wet", "dirty", "workload"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "love", "desire", "worry", "foreshadowing", "calm", "confidence", "disappointment"]:
            self.memes.setdefault(key, 0.0)

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
    indoors: bool = False
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
class Defense:
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
        self.fired: set[tuple] = set()
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
        clone.facts = dict(self.facts)
        return clone


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wet", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more laundry for {carer.label_word}.")
    return out


def _r_worry(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["foreshadowing"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        return ["__worry__"]
    return []


CAUSAL_RULES = [
    _r_wet,
    _r_workload,
    _r_worry,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__worry__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_defense(activity: Activity, prize: Prize) -> Optional[Defense]:
    for defense in DEFENSES:
        if activity.mess in defense.guards and prize.region in defense.covers:
            return defense
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoors:
        return f"The room was quiet, and the deep puddle by the back door looked like a tiny mirror."
    if activity.weather == "rainy":
        return f"The path shone after the rain, and the deep puddle held a wobbly copy of the sky."
    return f"{setting.place.capitalize()} looked calm and a little shiny."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who liked noticing small things on the way home.")


def foreshadow(world: World, hero: Entity, defense: Defense) -> None:
    hero.memes["foreshadowing"] += 1
    world.say(
        f"Earlier, {hero.id} had noticed a {defense.label} leaning by the gate, smooth as a tray."
    )
    world.say(
        f"The puddle nearby was so deep that its surface made the sidewalk lights diffuse into soft circles."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.verb} after rain; "
        f"{activity.gerund} made the whole walk feel playful."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That morning, {hero.id}'s {parent.label_word} had bought {hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} all the way to the puddle.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One rainy afternoon, " if world.weather == "rainy" else "One afternoon, "
    go = "walked to" if not world.setting.indoors else "came to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, even though the puddle looked deep enough to splash back.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label_word} said.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["disappointment"] += 1
    world.say(f"{hero.id} frowned, but the wish to play was still there.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} held {hero.pronoun('possessive')} hand and slowed the step down."
    )


def offer_defense(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Defense]:
    defense = select_defense(activity, prize)
    if defense is None:
        return None
    item = world.add(Entity(
        id=defense.id,
        type="defense",
        label=defense.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(defense.covers),
        plural=defense.plural,
    ))
    item.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(
        f'"How about we {defense.prep} first?" {parent.label_word} asked.'
    )
    return defense


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, defense: Defense) -> None:
    hero.memes["joy"] += 1
    hero.memes["confidence"] += 1
    hero.memes["calm"] += 1
    hero.memes["disappointment"] = 0.0
    world.say(
        f"{hero.id}'s face brightened, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f"They {defense.tail}. Then {hero.id} was {activity.gerund}, "
        f"{prize.label} still dry, while the puddle's shine diffused into tiny ripples under {hero.pronoun('possessive')} feet."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", hero_trait: str = "curious", parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather if not setting.indoors else ""
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"traits": [hero_trait]}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
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

    introduce(world, hero)
    foreshadow(world, hero, DEFENSES[0])
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero)

    world.para()
    defense = offer_defense(world, parent, hero, activity, prize)
    if defense:
        accept(world, parent, hero, activity, prize, defense)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        defense=defense,
        resolved=defense is not None,
        conflict=hero.memes["foreshadowing"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lane": Setting(place="the side lane", affords={"puddle_walk"}),
    "garden_path": Setting(place="the garden path", affords={"puddle_walk"}),
    "back_steps": Setting(place="the back steps", indoors=False, affords={"puddle_walk"}),
}

ACTIVITIES = {
    "puddle_walk": Activity(
        id="puddle_walk",
        verb="step into the deep puddle",
        gerund="walking around the deep puddle",
        rush="dash into the deep puddle",
        mess="wet",
        soil="soaked and muddy",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="deep puddle",
        tags={"puddle", "wet", "smooth", "diffuse"},
    ),
}

PRIZES = {
    "sneakers": Prize(
        label="sneakers",
        phrase="fresh white sneakers",
        type="sneakers",
        region="feet",
        plural=True,
    ),
    "socks": Prize(
        label="socks",
        phrase="new striped socks",
        type="socks",
        region="feet",
        plural=True,
    ),
    "pants": Prize(
        label="pants",
        phrase="soft new pants",
        type="pants",
        region="legs",
        plural=True,
    ),
}

DEFENSES = [
    Defense(
        id="smooth_plank",
        label="a smooth plank",
        covers={"feet", "legs"},
        guards={"wet"},
        prep="set the smooth plank across the puddle and use it like a tiny bridge",
        tail="placed the smooth plank over the deep puddle",
    ),
    Defense(
        id="rain_boots",
        label="rain boots",
        covers={"feet"},
        guards={"wet"},
        prep="put on rain boots first",
        tail="tugged on the rain boots and stepped carefully",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Lily", "Zoe", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Finn", "Leo", "Ben", "Noah", "Eli", "Sam"]
TRAITS = ["curious", "gentle", "cheerful", "lively", "quiet", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_defense(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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


KNOWLEDGE = {
    "puddle": [(
        "What is a puddle?",
        "A puddle is a small pool of water on the ground after rain or spilled water."
    )],
    "wet": [(
        "Why do wet shoes feel heavy?",
        "Wet shoes feel heavy because the water soaks into them and adds extra weight."
    )],
    "smooth": [(
        "What does smooth mean?",
        "Smooth means even and flat, without rough bumps or sharp edges."
    )],
    "diffuse": [(
        "What does diffuse mean for light?",
        "Diffuse light spreads out softly instead of making one bright, sharp spot."
    )],
    "defense": [(
        "What is a defense?",
        "A defense is something that helps protect a person or thing from harm or trouble."
    )],
}
KNOWLEDGE_ORDER = ["puddle", "wet", "smooth", "diffuse", "defense"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a slice-of-life story for a small child that includes the phrase "{act.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label_word} worries about {prize.phrase}.",
        f"Write a short story with foreshadowing, a smooth defense, and a calm ending by a deep puddle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    defense = f["defense"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} at {place}?",
            answer=f"{hero.id} wanted to {act.verb} at {place}, and {hero.pronoun('possessive')} {parent.label_word} walked beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word} worried because the deep puddle could leave the {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"What did the parent notice before choosing a safer way?",
            answer=f"{parent.label_word} noticed a {defense.label} that could be used as a defense, and that hint had already been foreshadowed earlier in the story.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the defense help {hero.id} at the puddle?",
            answer=f"The {defense.label} made a safe little bridge, so {hero.id} could {act.verb} without ruining {hero.pronoun('possessive')} {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm, and the day ended with {hero.id} still dry and smiling near the puddle.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("defense"):
        tags.add("defense")
        tags.add("smooth")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", activity="puddle_walk", prize="socks", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden_path", activity="puddle_walk", prize="sneakers", name="Finn", gender="boy", parent="father", trait="playful"),
    StoryParams(place="back_steps", activity="puddle_walk", prize="pants", name="Lily", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} splashes the {prize.region}, but no defense in this world "
        f"both guards {activity.mess} and covers that area in a reasonable way.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(D, A, P) :- defense(D), prize_at_risk(A, P),
                     mess_of(A, M), guards(D, M),
                     covers(D, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for d in DEFENSES:
        lines.append(asp.fact("defense", d.id))
        for m in sorted(d.guards):
            lines.append(asp.fact("guards", d.id, m))
        for r in sorted(d.covers):
            lines.append(asp.fact("covers", d.id, r))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a child, a deep puddle, and a smooth defense.")
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
        if not (prize_at_risk(act, pr) and select_defense(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait, params.parent)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:12} {act:12} {prize}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
