#!/usr/bin/env python3
"""
A small slice-of-life storyworld about measuring ingredients, a little havoc,
and a kind fix that turns the day around.

Seed tale:
- A child and a caregiver bake together in a kitchen.
- The child carefully measures sugar or flour.
- A small spill causes havoc: powder dusts the counter, bowl, or apron.
- A foil cover or foil tray helps protect what matters.
- A flashback to a past baking day reminds the caregiver of patience.
- Kindness turns the moment from frustration into teamwork.
- The scene ends with a transformation: a messy task becomes a finished treat.

This world is built to stay gentle, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_havoc(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("spill", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("havoc", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("messy", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["work"] = caretaker.memes.get("work", 0.0) + 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


RULES = [
    ("havoc", _r_havoc),
    ("cleanup", _r_cleanup),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_havoc(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "messy": prize.meters.get("messy", 0.0) >= THRESHOLD,
        "work": sum(e.memes.get("work", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["spill"] = actor.meters.get("spill", 0.0) + 1
    actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked quiet jobs with neat edges.")


def loves_measure(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to measure carefully, and {activity.gerund} felt like a tiny game."
    )


def arrival(world: World, hero: Entity, parent: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} were in {setting.place}."
    )
    world.say(f"The bowl waited on the counter, and the room felt ready for {activity.keyword}.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} hands moved too fast.")


def flashback(world: World, parent: Entity, hero: Entity) -> None:
    parent.memes["memory"] = parent.memes.get("memory", 0.0) + 1
    world.say(
        f"That made {hero.pronoun('possessive')} {parent.label_word} think back to another baking day, when patience had saved the cake."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_havoc(world, hero, activity, prize.id)
    if not pred["messy"]:
        return False
    world.facts["predicted_mess"] = activity.soil
    world.facts["predicted_work"] = pred["work"]
    world.say(
        f'"If you keep going, your {prize.label} will get {activity.soil}," {hero.pronoun("possessive")} {parent.label_word} said.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to {activity.rush} anyway.")


def foil_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            gear = g
            break
    if gear is None:
        return None
    obj = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    obj.worn_by = hero.id
    if predict_havoc(world, hero, activity, prize.id)["messy"]:
        del world.entities[obj.id]
        return None
    world.say(
        f"{parent.id} smiled and found a clever foil cover before the mess could spread."
    )
    world.say(f'"How about we {gear.prep} and then {activity.verb} together?"')
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} looked up, calmed down, and hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f"They {gear.tail}. Soon the kitchen mess turned into something useful, and {hero.id} was {activity.gerund} with {prize.label} still safe."
    )


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return "The kitchen was warm, and the counter shone under the light."
    return f"{setting.place.capitalize()} felt calm, with room for careful work."


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_measure(world, hero, activity)
    world.say(f"{parent.label_word.capitalize()} had bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} while helping.")

    world.para()
    arrival(world, hero, parent, setting, activity)
    world.say(setting_detail(setting, activity))
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    flashback(world, parent, hero)
    defies(world, hero, activity)

    world.para()
    gear = foil_fix(world, parent, hero, activity, prize)
    if gear is not None:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
        conflict=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"measure"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"measure"}),
}

ACTIVITIES = {
    "measure": Activity(
        id="measure",
        verb="measure the flour",
        gerund="measuring flour",
        rush="tip the cup too quickly",
        mess="dusty",
        soil="flour-dusted",
        zone={"counter", "apron"},
        keyword="measure",
        tags={"measure", "kindness", "transformation"},
    ),
    "mix": Activity(
        id="mix",
        verb="mix the batter",
        gerund="stirring batter",
        rush="whisk too fast",
        mess="spilled",
        soil="spilled",
        zone={"counter", "apron"},
        keyword="mix",
        tags={"kindness", "transformation"},
    ),
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a striped apron",
        type="apron",
        region="apron",
    ),
    "tray": Prize(
        label="tray",
        phrase="a shiny tray",
        type="tray",
        region="counter",
    ),
}

GEAR = [
    Gear(
        id="foil",
        label="foil",
        covers={"counter"},
        guards={"dusty", "spilled"},
        prep="put a foil sheet over the tray first",
        tail="carefully lifted the foil sheet away",
    ),
    Gear(
        id="cover",
        label="a foil cover",
        covers={"apron"},
        guards={"dusty"},
        prep="wrap the bowl with foil first",
        tail="used the foil cover to keep the flour where it belonged",
    ),
]

HERO_NAMES = ["Mina", "Jun", "Tess", "Owen", "Lila", "Iris", "Nico", "Eva"]
TRAITS = ["careful", "gentle", "curious", "patient", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    if any(act.mess in g.guards and prize.region in g.covers for g in GEAR):
                        out.append((place, act_id, prize_id))
    return out


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
    "measure": [("What does it mean to measure something?", "To measure something means to find out how much of it there is, often with a cup, spoon, or ruler.")],
    "foil": [("What is foil used for in a kitchen?", "Foil can cover food or pans to keep things clean, warm, or protected while cooking.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and thoughtful toward someone else.")],
    "flashback": [("What is a flashback in a story?", "A flashback is a part of a story that shows something that happened earlier.")],
    "transformation": [("What is a transformation?", "A transformation is a change from one form or state into another.")],
    "dusty": [("What makes flour dusty?", "Flour is very fine, so it can puff into the air and leave a soft powdery mess.")],
    "spilled": [("What happens when something spills?", "When something spills, it falls out of a bowl or cup and lands somewhere it should not.")],
}
KNOWLEDGE_ORDER = ["measure", "foil", "kindness", "flashback", "transformation", "dusty", "spilled"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a child about "{act.keyword}" with a small mishap and a gentle fix.',
        f"Tell a story where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {parent.label_word} uses kindness and a foil cover to help.",
        f'Write a simple kitchen story that includes a flashback, the word "measure", and ends with a transformation from mess to success.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    q = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} worry about {prize.label}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label_word} worried because the {prize.label} could get {act.soil}.",
        ),
        QAItem(
            question=f"What did the parent remember in the flashback?",
            answer="The parent remembered another baking day when patience helped keep the kitchen calm.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        q.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} helped by protecting the right part of the kitchen, so {hero.id} could keep going without ruining the {prize.label}.",
        ))
    if f.get("resolved"):
        q.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the messy start turned into a kind, calm baking moment, and {hero.id} was {act.gerund} with everything in better order.",
        ))
    return q


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted({n for n, _ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="measure", prize="apron", name="Mina", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="sunroom", activity="measure", prize="tray", name="Owen", gender="boy", parent="father", trait="patient"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not naturally put {prize.label} at risk here.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(A,P) :- at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: measure, havoc, foil, kindness, flashback, transformation.")
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
        if not any(act.mess in g.guards and pr.region in g.covers for g in GEAR):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(HERO_NAMES)
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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
