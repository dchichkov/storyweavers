#!/usr/bin/env python3
"""
Storyworld: Tint, Polio, and Astrology on a Pirate Ship
======================================================

A small standalone story world with a pirate-tale flavor, built around
foreshadowing, sound effects, and a simple cause-and-fix simulation.

The seed words are threaded through the domain as:
- tint: colored glass, lantern glow, and sea-colored choices
- polio: the name of a little prize chest and a cautionary old ship legend
- astrology: star-reading, constellations, and a navigator's sky advice

The world is intentionally tiny and constraint-checked: not every idea is a
reasonable story. The captain's warning must be backed by the simulation, and
the compromise must actually protect the at-risk prize.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"wet", "salt", "sooty"}


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "salt": 0.0, "sooty": 0.0, "dirty": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "desire": 0.0, "resolve": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
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
    tone: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    sound: str = ""


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
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grasped", 0.0) < THRESHOLD or actor.memes.get("defiance", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("soak", "physical", _r_soak),
    Rule("workload", "physical", _r_workload),
    Rule("conflict", "social", _r_conflict),
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def sound_effect(activity: Activity) -> str:
    return activity.sound or "swish"


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the moonlit deck":
        return "The deck shone silver, and the mast creaked like an old whisper."
    if setting.place == "the crow's cove":
        return "The water below the cove winked black and blue, like it was hiding a secret."
    return f"{setting.place.capitalize()} looked ready for a pirate tale."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(world_setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "boy",
         parent_type: str = "captain", hero_traits: Optional[list[str]] = None) -> World:
    world = World(world_setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["brave", "curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    hero.memes["love"] = 1.0
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a little {hero_type} pirate who loved every shiny thing on the ship.")
    world.say(f"{hero.pronoun().capitalize()} especially loved the {prize.label}, with its {prize.phrase}.")
    world.say(f"{hero.id}'s {parent.label} had a careful eye and listened to the stars at night.")

    world.para()
    world.say(f"At the {world.setting.place}, the old lantern gave a {activity.sound} sound: {sound_effect(activity)}!")
    world.say(setting_detail(world.setting, activity))
    world.say(f"{hero.id} wanted to {activity.verb}, but the sky looked tricky.")

    world.para()
    forecast = predict_mess(world, hero, activity, prize.id)
    if forecast["soiled"]:
        world.say(f"The navigator read the astrology chart and pointed at a pale star.")
        world.say(f'"{If you rush now, the {prize.label} will get {activity.soil}," the captain said.')
        world.say(f"{hero.id} tried to {activity.rush}, but the deck answered with a worried creak.")
        hero.memes["defiance"] += 1
        hero.memes["grasped"] += 1
        propagate(world, narrate=False)
        world.say(f"The captain caught {hero.id}'s sleeve and said, \"Easy now, matey.\"")
        gear_def = select_gear(activity, prize)
        if gear_def is not None:
            gear = world.add(Entity(
                id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
                caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural,
            ))
            gear.worn_by = hero.id
            if predict_mess(world, hero, activity, prize.id)["soiled"]:
                gear.worn_by = None
                del world.entities[gear.id]
                gear_def = None
        else:
            gear = None

        if gear_def is not None:
            world.say(f'"{How about we {gear_def.prep} first?" said the captain.')
            hero.memes["joy"] += 1
            hero.memes["conflict"] = 0.0
            world.say(f"{hero.id} grinned and nodded. \"Aye, that sounds safer!\"")
            world.say(f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund}, with {prize.label} staying clean.")
        else:
            world.say(f"The captain found a safer route instead, and {hero.id} waited for a better tide.")
    else:
        world.say(f"The sky was kind, so the captain let {hero.id} try the plan at once.")
        _do_activity(world, hero, activity, narrate=True)
        world.say(f"{hero.id} laughed at the sound of {sound_effect(activity)} as the ship rocked gently.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=world_setting)
    return world


SETTINGS = {
    "moonlit_deck": Setting(
        place="the moonlit deck",
        indoor=False,
        affords={"tint_sailing", "astrology_watch", "polio_spark"},
        tone="salt wind and lantern glow",
    ),
    "crow_cove": Setting(
        place="the crow's cove",
        indoor=False,
        affords={"tint_sailing", "astrology_watch"},
        tone="echoing water and cliff shadows",
    ),
    "harbor": Setting(
        place="the harbor",
        indoor=False,
        affords={"polio_spark", "astrology_watch"},
        tone="ropes, bells, and gull cries",
    ),
}

ACTIVITIES = {
    "tint_sailing": Activity(
        id="tint_sailing",
        verb="sail by the tinted lantern",
        gerund="sailing by the tinted lantern",
        rush="dash to the rail",
        mess="wet",
        soil="slick and soggy",
        zone={"torso"},
        weather="night",
        keyword="tint",
        tags={"tint", "wet"},
        sound="swish",
    ),
    "astrology_watch": Activity(
        id="astrology_watch",
        verb="follow the astrology chart",
        gerund="studying the astrology chart",
        rush="run to the star map",
        mess="sooty",
        soil="smudged and smoky",
        zone={"hands"},
        weather="night",
        keyword="astrology",
        tags={"astrology"},
        sound="whisper",
    ),
    "polio_spark": Activity(
        id="polio_spark",
        verb="lift the little polio chest",
        gerund="lifting the little polio chest",
        rush="snatch the chest",
        mess="salt",
        soil="salt-spattered",
        zone={"hands"},
        weather="night",
        keyword="polio",
        tags={"polio", "salt"},
        sound="clink",
    ),
}

PRIZES = {
    "chart": Prize("chart", "a neat star chart with gold lines", "chart", "hands"),
    "lantern": Prize("lantern", "a lantern with a blue tint", "lantern", "torso"),
    "chest": Prize("chest", "a little polio chest with a brass latch", "chest", "hands"),
}

GEAR = [
    Gear("oilcloth", "an oilcloth wrap", {"torso"}, {"wet"}, "cover the lantern with an oilcloth wrap", "covered the lantern with the oilcloth wrap"),
    Gear("gloves", "sailor gloves", {"hands"}, {"salt", "sooty"}, "put on sailor gloves", "put on the sailor gloves"),
    Gear("hood", "a clear hood", {"torso", "hands"}, {"wet", "salt", "sooty"}, "fit on a clear hood first", "fit on the clear hood"),
]

GIRL_NAMES = ["Nina", "Mara", "Ivy", "Saila", "Ruby"]
BOY_NAMES = ["Pip", "Jory", "Finn", "Bram", "Tess"]
TRAITS = ["curious", "brave", "lively", "stubborn", "cheerful"]


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
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tint": [("What is a tint?", "A tint is a light color added to something, like glass or water, so it looks a little different.")],
    "astrology": [("What is astrology?", "Astrology is a way of looking at the stars and constellations for signs and stories.")],
    "polio": [("What is a chest latch?", "A latch is a small fastener that keeps a box or chest closed.")],
    "wet": [("Why does wet wood feel slippery?", "Wet wood can be slippery because the water makes the surface smooth and easy to slide on.")],
    "salt": [("What is saltwater?", "Saltwater is ocean water. It tastes salty and splashes on ships and rocks.")],
    "sooty": [("What does soot mean?", "Soot is black powder from smoke, and it can make fingers and faces dirty.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short pirate tale for a small child that includes the word "{act.keyword}" and the feeling of a warning before the turn.',
        f"Tell a story where {hero.id} wants to {act.verb} while {hero.pronoun('possessive')} {parent.label} watches the sky and worries about {prize.phrase}.",
        f"Write a gentle pirate story with foreshadowing, sound effects, and a safe compromise on the moonlit deck.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = select_gear(act, prize)
    qa = [
        QAItem(
            question=f"Who is the pirate child in the story?",
            answer=f"The pirate child is {hero.id}, a little {hero.type} who loves the sea and shiny things.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do before the captain warned {hero.pronoun('object')}?",
            answer=f"{hero.id} wanted to {act.verb}, but the captain saw the problem first.",
        ),
        QAItem(
            question=f"What did the captain worry would happen to the {prize.label}?",
            answer=f"The captain worried that the {prize.label} would get {act.soil} if the plan went ahead too fast.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the crew make the plan safe?",
            answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten the {prize.label} in this setup.)"
    return f"(No story: no gear in this world safely handles {activity.gerund} for the {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize is not a typical {gender}'s item here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with foreshadowing and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, [params.trait, "stubborn"])
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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


CURATED = [
    StoryParams("moonlit_deck", "tint_sailing", "lantern", "Pip", "boy", "captain", "brave"),
    StoryParams("crow_cove", "astrology_watch", "chart", "Nina", "girl", "captain", "curious"),
    StoryParams("harbor", "polio_spark", "chest", "Bram", "boy", "captain", "lively"),
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
            print(f"  {place:14} {act:18} {prize:8}  [{', '.join(genders)}]")
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
