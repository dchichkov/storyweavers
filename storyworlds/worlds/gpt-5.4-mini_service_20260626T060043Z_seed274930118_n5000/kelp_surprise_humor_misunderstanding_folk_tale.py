#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kelp_surprise_humor_misunderstanding_folk_tale.py
=============================================================================================================================

A small folk-tale storyworld about kelp, surprise, humor, and misunderstanding.

Premise sketch:
A child in a seaside village is sent to fetch kelp for supper. The child
misunderstands a simple request, expects something grand and strange, and meets
a funny surprise at the shore. The trouble is resolved with a kind explanation
and a practical change in plan.

The simulated world keeps track of:
- physical meters such as wetness, tangling, and carrying load
- emotional memes such as curiosity, worry, surprise, humor, joy, and trust

The story is rendered from the evolving world state, not from a frozen template.
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
        for k in ["wet", "tangled", "load", "clean", "full"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "surprise", "humor", "joy", "trust", "embarrassment"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


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
    keyword: str = "kelp"
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["tangled"] += 1
            out.append(f"{actor.label_word.capitalize()}'s {item.label} grew wet and tangled.")
    return out


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if hero and hero.memes["surprise"] >= THRESHOLD and hero.memes["humor"] >= THRESHOLD:
        sig = ("mood", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            out.append(f"The odd little surprise made {hero.id} laugh instead of fret.")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    elder = world.facts.get("elder")
    if not hero or not elder:
        return out
    if hero.memes["worry"] < THRESHOLD or elder.memes["kindness"] < THRESHOLD:
        return out
    sig = ("trust", hero.id)
    if sig not in world.fired:
        world.fired.add(sig)
        hero.memes["trust"] += 1
        hero.memes["worry"] = 0
        out.append(f"{hero.id} felt calmer once the old words were explained.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_mood,
    _r_trust,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_soil(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and (prize.meters["wet"] >= THRESHOLD or prize.meters["tangled"] >= THRESHOLD))}


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the cove":
        return "The cove was bright with shells, and the kelp line swayed with the tide."
    if setting.place == "the harbor":
        return "The harbor was busy, with rope ends snapping softly against the posts."
    return f"{setting.place.capitalize()} waited quietly, as if it had been listening for a story."


def activity_charm(activity: Activity) -> str:
    return {
        "kelp_run": "the kelp smelled like the sea after rain, sharp and clean",
        "kelp_braid": "the long green strands curled like ribbons in a parade",
        "kelp_shelter": "the kelp beds rustled like a whispering crowd",
    }.get(activity.id, "it had the odd charm of a seaside errand")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"Once, in a small fishing village, there was a little {hero.type} named {hero.id}. "
        f"{hero.id} loved listening to {elder.label_word} tell old sea stories."
    )


def loves_kelp(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} liked kelp because it came from the sea and "
        f"looked like a green ribbon from a giant's sleeve."
    )


def offer_task(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One evening, {elder.label_word} asked {hero.id} to fetch {prize.phrase} "
        f"for supper and keep it safe on the way home."
    )


def wear_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} tucked {prize.it()} over {hero.pronoun('possessive')} shoulders "
        f"and set off with a careful little step."
    )


def arrive(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    day = "At dawn, " if world.weather == "morning" else "Soon after, "
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {elder.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} head was full of odd guesses."
    )


def misunderstand(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    hero.memes["surprise"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"{hero.id} thought the kelp task must hide a grand surprise, maybe even a sea king in disguise."
    )
    world.say(
        f"{hero.pronoun().capitalize()} crept toward the kelp beds, trying not to laugh at {hero.pronoun('possessive')} own brave ideas."
    )


def meet_surprise(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"Then a fat seal popped up beside the rocks with a frond of kelp on its head, as serious as a judge."
    )
    world.say(
        f"{hero.id} stared, and then {hero.pronoun()} snorted with laughter, because the great mystery was only a silly seal."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_soil(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Mind the {prize.label}," {elder.label_word} said. "Kelp can wet it and tug it loose."'
    )
    return True


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that kelp errand.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    propagate(world, narrate=narrate)


def resolve(world: World, elder: Entity, hero: Entity, prize: Entity, gear_def: Optional[Gear]) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["worry"] = 0
    if gear_def:
        world.say(
            f"{elder.label_word} smiled and brought out {gear_def.label}. "
            f'"Let us use this first," {elder.label_word} said, "so the kelp stays tidy."'
        )
        world.say(
            f"{hero.id} helped at once, and soon the pair went home with {prize.it()} safe and the seal waving after them."
        )
    else:
        world.say(
            f"{elder.label_word} laughed kindly and showed {hero.id} how to carry the kelp by the thick ends."
        )
        world.say(
            f"{hero.id} returned home with the bundle held high, feeling clever and a little proud of the joke."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, elder_type: str = "grandmother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=elder.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, setting=setting)

    introduce(world, hero, elder)
    loves_kelp(world, hero)
    offer_task(world, elder, hero, prize)
    wear_prize(world, hero, prize)

    world.para()
    arrive(world, hero, elder, activity)
    wants(world, hero, elder, activity)
    warn(world, elder, hero, activity, prize)
    misunderstand(world, hero, elder, activity)
    meet_surprise(world, hero)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def:
        resolve(world, elder, hero, prize, gear_def)
    else:
        resolve(world, elder, hero, prize, None)

    world.facts["gear"] = gear_def
    return world


SETTINGS = {
    "cove": Setting(place="the cove", indoor=False, affords={"kelp_run", "kelp_braid"}),
    "harbor": Setting(place="the harbor", indoor=False, affords={"kelp_run", "kelp_shelter"}),
    "tidepool": Setting(place="the tidepool", indoor=False, affords={"kelp_run", "kelp_braid"}),
}

ACTIVITIES = {
    "kelp_run": Activity(
        id="kelp_run",
        verb="gather kelp",
        gerund="gathering kelp",
        rush="run to the kelp beds",
        mess="wet",
        soil="wet and stringy",
        zone={"torso"},
        weather="evening",
        keyword="kelp",
        tags={"kelp", "wet", "humor", "surprise"},
    ),
    "kelp_braid": Activity(
        id="kelp_braid",
        verb="braid kelp",
        gerund="braiding kelp",
        rush="rush to the kelp basket",
        mess="tangled",
        soil="tangled and salty",
        zone={"torso"},
        weather="morning",
        keyword="kelp",
        tags={"kelp", "humor", "misunderstanding"},
    ),
    "kelp_shelter": Activity(
        id="kelp_shelter",
        verb="stack kelp for shelter",
        gerund="stacking kelp",
        rush="hurry to the sea wall",
        mess="wet",
        soil="wet and sagging",
        zone={"torso"},
        weather="morning",
        keyword="kelp",
        tags={"kelp", "surprise", "misunderstanding"},
    ),
}

PRIZES = {
    "shawl": Prize(label="shawl", phrase="a bright wool shawl", type="shawl", region="torso"),
    "apron": Prize(label="apron", phrase="a clean kitchen apron", type="apron", region="torso"),
    "basket": Prize(label="basket", phrase="a woven basket", type="basket", region="torso"),
}

GEAR = [
    Gear(
        id="oilskin",
        label="an oilskin apron",
        covers={"torso"},
        guards={"wet"},
        prep="put on the oilskin apron",
        tail="came home under the oilskin apron",
    ),
    Gear(
        id="rope_sash",
        label="a rope sash",
        covers={"torso"},
        guards={"tangled"},
        prep="tie on a rope sash",
        tail="came home with the rope sash keeping the bundle neat",
    ),
]

GIRL_NAMES = ["Mara", "Elin", "Nessa", "Orla", "Runa"]
BOY_NAMES = ["Perrin", "Tomas", "Galen", "Bram", "Ivo"]
TRAITS = ["curious", "cheerful", "brave", "sly", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
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
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kelp": [("What is kelp?", "Kelp is a large sea plant that grows in cool ocean water and can wash up on the shore.")],
    "wet": [("Why does wet cloth feel heavy?", "Wet cloth feels heavy because it holds water, and the extra water makes it weigh more.")],
    "tangled": [("What does tangled mean?", "Tangled means mixed up or twisted together so something is hard to smooth out.")],
    "surprise": [("What is a surprise?", "A surprise is something unexpected that can make you gasp, smile, or laugh.")],
    "humor": [("What makes a joke funny?", "A joke is funny when it makes people see something in an unexpected, silly way.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone hears or thinks the wrong thing by mistake.")],
}
KNOWLEDGE_ORDER = ["kelp", "wet", "tangled", "surprise", "humor", "misunderstanding"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        f'Write a short folk tale for a child that includes the word "kelp" and a silly seaside surprise.',
        f"Tell a gentle story where {hero.id} is sent by {elder.label_word} to {act.verb} without ruining {prize.phrase}.",
        f"Write a humorous seaside story about a misunderstanding at {world.setting.place} that ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.type} named {hero.id} and {elder.label_word}, who share a seaside errand with kelp.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} head filled up with a funny misunderstanding.",
        ),
        QAItem(
            question=f"Why did {elder.label_word} worry about the {prize.label}?",
            answer=f"{elder.label_word} worried because kelp could make the {prize.label} wet and tangled on the way home.",
        ),
        QAItem(
            question=f"What surprising thing happened by the rocks?",
            answer=f"A seal popped up with kelp on its head, and that odd sight turned the trouble into a laugh.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The elder showed a kinder plan, and {hero.id} went home with the kelp safely handled and feeling wiser.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"It helped because it covered the {prize.region} and kept the kelp from making the prize wet.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cove", activity="kelp_run", prize="shawl", name="Mara", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="harbor", activity="kelp_shelter", prize="apron", name="Perrin", gender="boy", elder="grandfather", trait="cheerful"),
    StoryParams(place="tidepool", activity="kelp_braid", prize="basket", name="Elin", gender="girl", elder="aunt", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.label}, so there is no honest worry to resolve.)"
    return f"(No story: there is no reasonable protective trick here for a {prize.label} during {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


def ASP_RULES() -> str:
    return r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
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
    ap = argparse.ArgumentParser(description="Folk tale kelp storyworld with surprise, humor, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, prize=prize_id, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.elder)
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
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible (place, activity, prize) combos:")
        for place, act, prize in sorted(set(asp.atoms(model, "valid"))):
            print(f"  {place:9} {act:12} {prize}")
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
