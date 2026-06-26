#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/metastasize_repetition_foreshadowing_dialogue_space_adventure.py
============================================================================================================================================================

A standalone *story world* sketch for a space adventure tale about an alien
growth that metastasizes, driven by repetition, foreshadowing, and dialogue.

Initial story (used to build a world model):
---
Once upon a time, a little girl named Nova lived aboard the spaceship *Starflower*.
She loved exploring the cargo bay and looking at the strange plants the crew
brought back. One day, the captain gave Nova a shiny silver badge to wear.
Nova loved her badge and wore it everywhere.

Then a new plant arrived—a purple bloom that sparkled. The captain said,
"Don't touch that one, Nova. It might be dangerous." Nova was curious but
listened… until she didn't. She reached out a finger, and the bloom released
a puff of golden spores. The spores stuck to her badge and began to grow,
spreading across the metal. "It's metastasizing!" cried the engineer. The
captain said, "We need the decon suit to stop it." Nova felt sorry, but
together they put on the suit and used the sprayer to clean the badge.
The plant stopped growing, and Nova learned to wait for the grown-ups.

Causal state updates:
---
    touching ambiguous object -> actor.curiosity += 1; object.spores++
    spores on worn item       -> item.contaminated++; item.dirty++
    contaminated item nearby  -> environment.metastasis += 1 (spreads)
    wear protective suit      -> item.contaminated = 0 (fix)
    apology + fix             -> actor.trust += 1; actor.conflict = 0
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"spores", "contaminated", "sticky"}
REGIONS = {"hands", "arms", "torso"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "captain", "engineer"}
        male = {"boy", "captain", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


@dataclass
class Setting:
    place: str = "the cargo bay"
    indoor: bool = True
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
    weather: str = "space-dark"
    keyword: str = "bloom"
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_contaminate(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("contam", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got covered in {mess}."
                )
    return out


def _r_metastasize(world: World) -> list[str]:
    """Spores on the prize spread to other items (foreshadowing)."""
    out: list[str] = []
    for prize in list(world.entities.values()):
        if prize.meters.get("spores", 0) >= THRESHOLD and prize.id != "bloom":
            sig = ("meta", prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("bloom").meters["metastasis"] += 1
            # Repetition: the alarm phrase
            out.append("The blinker on the wall blinked faster. Blink. Blink. Blink.")
            out.append('"It\'s metastasizing!" said the engineer.')
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean cleaning work for {carer.label}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="contaminate", tag="physical", apply=_r_contaminate),
    Rule(name="metastasize", tag="physical", apply=_r_metastasize),
    Rule(name="workload", tag="social", apply=_r_workload),
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
                produced.extend(sents)
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
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
        "metastasis": bool(prize and prize.meters.get("spores", 0) >= THRESHOLD),
    }


def activity_delight(activity: Activity) -> str:
    return "the sparkly bloom looked like a tiny galaxy"

def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place.removeprefix('the ')} hummed with quiet lights."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who lived aboard the spaceship *Starflower*.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_explore"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved exploring the cargo bay and "
        f"{activity.gerund}; {activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} everywhere {hero.pronoun()} went."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One day, a new plant arrived — a purple bloom that sparkled in the dim light. "
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label_word} gathered around."
    )
    world.say(setting_detail(world.setting, activity))


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    # Foreshadowing dialogue: the parent warns twice (repetition)
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"] and not pred["metastasis"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_metastasis"] = pred["metastasis"]
    # First warning
    world.say(
        f'"Don\'t touch that one, {hero.id}," the {parent.label_word} said firmly. '
        f'"It might be dangerous."'
    )
    # Second warning (repetition for emphasis)
    world.say(
        f'"Really, do not touch it. It could spread," {parent.pronoun()} said again.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    # Repetition of the forbidden action
    world.say(f"{hero.id} leaned closer. Closer. {hero.pronoun()} reached out a finger.")
    world.say(f"{hero.pronoun().capitalize()} touched the bloom.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    world.say(
        f"But the {parent.label_word} caught {hero.pronoun('possessive')} hand just in time."
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes.get("conflict", 0) >= THRESHOLD:
        world.say(
            f'{hero.id} looked down. "But I just wanted to see," {hero.pronoun()} whispered.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    # Dialogue: the gear solution is proposed
    world.say(
        f'"We need the {gear_def.label} to stop it," the {parent.label_word} said. '
        f'"Let\'s put it on together."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded and climbed into the {gear_def.label}. "
        f'"I\'m sorry," {hero.pronoun()} said. The {parent.label_word} smiled.'
    )
    world.say(
        f"They used a special sprayer to wash the spores away. "
        f"The bloom stopped spreading, and the {prize.label} was clean again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "bold"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    # The alien bloom (source of the spores)
    world.add(Entity(id="bloom", kind="thing", type="plant", label="bloom",
                     meters=defaultdict(float)))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes.get("grabbed_by", 0) >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "cargo_bay": Setting(place="the cargo bay", indoor=True, affords={"explore"}),
    "lab": Setting(place="the lab", indoor=True, affords={"explore"}),
    "greenhouse": Setting(place="the greenhouse", indoor=True, affords={"explore"}),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="examine the new plants",
        gerund="examining new plants",
        rush="reach out and touch the bloom",
        mess="spores",
        soil="golden and sticky",
        zone={"hands", "arms"},
        keyword="bloom",
        tags={"spores", "plant"},
    ),
}

GEAR = [
    Gear(
        id="decon_suit",
        label="decontamination suit",
        covers={"hands", "arms", "torso"},
        guards={"spores", "contaminated", "sticky"},
        prep="put on the decontamination suit",
        tail="put on the suit together and used the sprayer",
        plural=False,
    ),
    Gear(
        id="gauntlets",
        label="gauntlets",
        covers={"hands", "arms"},
        guards={"spores", "sticky"},
        prep="put on the gauntlets",
        tail="put on the gauntlets and worked the sprayer",
        plural=True,
    ),
]

PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny silver badge", type="badge", region="torso"),
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", region="arms"),
    "gloves": Prize(label="gloves", phrase="nice white gloves", type="gloves", region="hands", plural=True),
}

GIRL_NAMES = ["Nova", "Stella", "Astra", "Luna", "Orion"]
BOY_NAMES = ["Jax", "Rex", "Zion", "Orion", "Leo"]
TRAITS = ["curious", "bold", "playful", "eager", "brave"]


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
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "spores": [("What are spores?", "Spores are tiny particles that some plants "
                "release. They are like seeds and can stick to things and grow."),
               ("Why can spores be tricky?", "Spores are very small, so they can "
                "float in the air and land on your clothes without you noticing.")],
    "plant": [("Why do some plants glow in space?", "Some space plants have "
               "special chemicals that sparkle or glow, just like the bloom.")],
    "metastasis": [("What does 'metastasize' mean?", "It means something spreads "
                    "from one place to another, like when a spill grows bigger.")],
    "decontamination": [("What does a decontamination suit do?", "It covers you so "
                         "that nothing dangerous sticks to your skin or clothes.")],
}
KNOWLEDGE_ORDER = ["spores", "plant", "metastasis", "decontamination"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short space-adventure story for a young child about a '
        f'"bloom" that spreads and a brave hero who learns to listen.',
        f'Tell a story where a child named {hero.id} is curious about a '
        f'mysterious plant and the grown-up says, "Don\'t touch," twice.',
        f'Write a story that ends with a decontamination suit and the words '
        f'"It\'s metastasizing!"'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.traits[1] if len(hero.traits)>1 else 'curious'} "
                   f"{hero.type} named {hero.id} and {pos} {pw} on a spaceship."
        ),
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{sub.capitalize()} loved exploring and {act.gerund}."
        ),
        QAItem(
            question=f"What did the {pw} warn {hero.id} about?",
            answer=f'The {pw} said, "Don\'t touch that bloom," twice. {sub} '
                   f'did not listen at first.'
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did the {pw} grab {hero.id}'s hand?",
            answer=f"The {pw} grabbed {pos} hand because {sub} was about to "
                   f"touch the bloom and get spores on {pos} {prize.label}."
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the {gear.label} help?",
            answer=f"They put on the {gear.label} and used a sprayer to clean "
                   f"the {prize.label}. The bloom stopped spreading."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add("decontamination")
    tags.add("metastasis")  # always relevant
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cargo_bay", activity="explore", prize="badge",
        name="Nova", gender="girl", parent="captain", trait="curious",
    ),
    StoryParams(
        place="lab", activity="explore", prize="scarf",
        name="Jax", gender="boy", parent="captain", trait="bold",
    ),
    StoryParams(
        place="greenhouse", activity="explore", prize="gloves",
        name="Stella", gender="girl", parent="engineer", trait="eager",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} touches {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region}.)")
    return (f"(No story: no gear protects {noun} from {activity.mess}. "
            f"Try gear that covers {prize.region} and guards {activity.mess}.)")


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P),
                   mess_of(A,M), guards(G,M),
                   covers(G,R), worn_on(P,R).
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure: a curious child, a metastasizing bloom, a compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "engineer"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list compatible combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP vs Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


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
        raise StoryError("No valid combination matches the given options.")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["captain", "engineer"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "bold"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
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
