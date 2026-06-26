#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/collide_suspense_bravery_magic_tall_tale.py
==============================================================================================================================

A Tall Tale story domain: a brave child must face the Great Collide – the
moment when two magical storms clash – armed only with a Harmony Amulet and
steady courage.  Suspense builds as the winds howl, the ground trembles, and the
child must sing the peace song before the sky tears apart.  Magic and bravery
collide in a classic Tall Tale of ordinary size meeting extraordinary force.
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
MESS_KINDS = {"zapped", "blown", "drenched", "trembled"}
REGIONS = {"self"}


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            d = {"subject": "she", "object": "her", "possessive": "her"}
            return d[case]
        if self.type in {"boy", "father", "dad", "man", "tower", "ridge"}:
            d = {"subject": "he", "object": "him", "possessive": "his"}
            return d[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
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
    weather: str = ""
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


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return "\n\n".join([" ".join(p) for p in self.paragraphs if p])

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_collide_force(world: World) -> list[str]:
    """If the two winds reach force >= THRESHOLD, the child without protection is hurt."""
    out = []
    for actor in world.characters():
        if actor.meters["force"] < THRESHOLD:
            continue
        if world.covered(actor, "self"):
            continue
        sig = ("collide_hurt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["hurt"] += 1
        out.append(f"The great wind wall hit {actor.pronoun('possessive')} small chest, and {actor.pronoun()} tumbled.")
    return out


def _r_amulet_protects(world: World) -> list[str]:
    """If the child wears the amulet and the winds collide, the amulet glows and protects."""
    for actor in world.characters():
        if not any(g.protective for g in world.worn_items(actor)):
            continue
        if actor.meters["force"] < THRESHOLD:
            continue
        sig = ("amulet_save", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["saved"] += 1
        return ["__amulet_glow__"]
    return []


CAUSAL_RULES = [
    Rule("collide_hurt", "physical", _r_collide_force),
    Rule("amulet_protects", "magic", _r_amulet_protects),
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
                produced.extend(s for s in sents if s != "__amulet_glow__" and s != "__collide_roar__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Domain-specific helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_harm(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_collide(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "hurt": bool(prize and prize.meters["hurt"] >= THRESHOLD),
        "force": sum(e.meters["force"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"Our {trait} {hero.type} was called {hero.id}, and {hero.pronoun()} lived at the foot of Thunder Ridge.")


def knows_collide(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} had heard the old stories about the Great Collide — when East Wind and West Wind crash "
              f"over the prairie and the sky splits wide. {hero.pronoun().capitalize()} knew {activity.gerund} was coming.")


def elder_gives(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Grand {elder.label_word} put a hand on {hero.id}'s shoulder. 'Child, take {prize.phrase}. "
              f"The amulet will keep you safe, but only your song can make the winds go still.'")


def hero_wears(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["courage"] += 1
    world.say(f"{hero.id} hung the Harmony Amulet around {hero.pronoun('possessive')} neck. The blue stone hummed against {hero.pronoun('possessive')} chest.")


def arrive_collide(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    world.say(f"One strange afternoon, the clouds rolled in — pink on one side, purple on the other. "
              f"The air grew tight and heavy. {hero.id} and {hero.pronoun('possessive')} {elder.label_word} "
              f"climbed to the top of Thunder Ridge.")
    world.say(f"Below, the two winds swirled, growing taller every second. The ground shook. The sky began to collide.")


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_harm(world, hero, activity, prize.id)
    if not pred["hurt"]:
        return False
    world.facts["predicted_force"] = pred["force"]
    world.say(f'"The colliding winds will tear you apart without the amulet," {hero.pronoun("possessive")} {elder.label_word} said. '
              f'"But with it and a brave song, you can calm the sky."')
    return True


def faces_fear(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} felt the wind push hard against {hero.pronoun('possessive')} back. {hero.pronoun().capitalize()} wanted to run, "
              f"but the amulet hummed louder.")
    world.say(f"{hero.pronoun().capitalize()} took a deep breath and stepped into the center of the ridge.")


def colliding_roar(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["force"] += 1
    propagate(world, narrate=False)
    world.say(f"The two walls of wind crashed together with a roar that shook the world. "
              f"{hero.id} stood firm, the amulet blazing gold.")


def sings_peace(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["courage"] += 1
    hero.memes["sang"] += 1
    hero.meters["force"] = 0.0
    world.say(f"{hero.id} closed {hero.pronoun('possessive')} eyes and sang the old peace song {hero.pronoun('possessive')} "
              f"{elder.label_word} had taught. The winds stopped. The sky turned soft and quiet.")
    world.say(f"A pale rainbow arched over Thunder Ridge. {hero.pronoun().capitalize()} was safe, and the Great Collide had become a gentle breeze.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Annie", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, elder_type: str = "grandfather") -> World:
    world = World(setting)
    world.weather = "storm"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "curious"])))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type,
                             label="the elder"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))

    # Act 1
    introduce(world, hero)
    knows_collide(world, hero, activity)
    elder_gives(world, elder, hero, prize)
    hero_wears(world, hero, prize)

    # Act 2
    world.para()
    arrive_collide(world, hero, elder, activity)
    warn(world, elder, hero, activity, prize)
    faces_fear(world, hero, activity)
    colliding_roar(world, hero, activity)

    # Act 3
    world.para()
    sings_peace(world, hero, elder, activity, prize)

    world.facts.update(hero=hero, elder=elder, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "thunder_ridge": Setting(place="Thunder Ridge", indoor=False, affords={"collide"}),
    "whispering_prairie": Setting(place="the Whispering Prairie", indoor=False, affords={"collide"}),
}

ACTIVITIES = {
    "collide": Activity(
        id="collide",
        verb="face the Great Collide",
        gerund="facing the Great Collide",
        rush="run straight into the colliding winds",
        mess="zapped",
        soil="beaten by the wind wall",
        zone={"self"},
        weather="storm",
        keyword="collide",
        tags={"collide", "storm", "magic"},
    ),
}

GEAR = [
    Gear(
        id="amulet",
        label="the Harmony Amulet",
        covers={"self"},
        guards={"zapped", "blown", "drenched", "trembled"},
        prep="put on the Harmony Amulet",
        tail="wore the amulet close to the heart",
    ),
]

PRIZES = {
    "amulet": Prize(
        label="amulet",
        phrase="a blue Harmony Amulet that glowed when danger came",
        type="amulet",
        region="self",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Annie", "Rose", "Pearl", "Sadie", "Mae", "June", "Belle", "Nellie", "Cora", "Lena"]
BOY_NAMES = ["Jake", "Will", "Sam", "Tom", "Jed", "Cale", "Rex", "Zeb", "Dusty", "Finn"]
TRAITS = ["brave", "stubborn", "kind", "curious", "fearless", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Q&A – child level world knowledge
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "collide": [("What does it mean when two things collide?",
                 "When two things collide they crash into each other very hard. "
                 "In a tall tale, the winds collide and make a big noise.")],
    "storm": [("What is a storm?",
               "A storm is very strong wind and rain or snow. Sometimes lightning "
               "and thunder come with it.")],
    "magic": [("What is magic in stories?",
               "Magic is a special power that can do things the ordinary world cannot. "
               "In this story, an amulet has magic to protect the hero.")],
    "bravery": [("What does it mean to be brave?",
                 "Being brave means you do something even though you are scared. "
                 "The child in the story was brave enough to face the colliding winds.")],
    "amulet": [("How does an amulet help in a tall tale?",
                "An amulet is a charm or necklace that gives the wearer special "
                "protection or power. The Harmony Amulet kept the child safe "
                "during the Great Collide.")],
}
KNOWLEDGE_ORDER = ["collide", "storm", "magic", "bravery", "amulet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    act = f["activity"]
    return [
        f"Write a Tall Tale about a {hero.type} named {hero.id} who must "
        f"{act.verb} on {world.setting.place}.",
        f"Tell a story full of suspense where a brave {hero.type} uses a magic "
        f"amulet to calm two colliding winds.",
        f"Create a Tall Tale in which the word 'collide' appears and the hero "
        f"sings a peace song to stop a storm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    prize = f["prize"]
    act = f["activity"]
    place = world.setting.place
    sub, pos = hero.pronoun("subject"), hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the brave {hero.type} that lives at the foot of {place}?",
            answer=f"The brave {hero.type} is {hero.id}. {sub.capitalize()} lived with {pos} {elder.label_word} "
                   f"and knew the old stories about the Great Collide."
        ),
        QAItem(
            question=f"What did the {elder.label_word} give {hero.id} before the {act.keyword}?",
            answer=f"The {elder.label_word} gave {hero.pronoun('object')} {prize.phrase}. The amulet would "
                   f"protect {hero.pronoun('object')} during the colliding winds."
        ),
        QAItem(
            question=f"How did {hero.id} calm the colliding winds on {place}?",
            answer=f"{hero.capitalize()} sang the old peace song that {pos} {elder.label_word} had taught. "
                   f"The song made the winds stop and a rainbow appeared."
        ),
        QAItem(
            question=f"Why was the moment when the two winds crashed full of suspense?",
            answer=f"The winds grew taller and taller, the ground shook, and the sky split. {hero.id} "
                   f"stood in the middle, small but brave, while the amulet glowed. Everyone wondered "
                   f"if the song would work."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q=q, a=a) for q, a in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP Twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    if clingo_set - python_set:
        print("Only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("Only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="thunder_ridge", activity="collide", prize="amulet",
                name="Annie", gender="girl", elder="grandfather", trait="brave"),
    StoryParams(place="whispering_prairie", activity="collide", prize="amulet",
                name="Will", gender="boy", elder="grandmother", trait="fearless"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale: a brave child, a crushing collide, a magic amulet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandfather", "grandmother", "aunt", "uncle"])
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("No valid gear for that activity–prize pair.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No compatible combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandfather", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "brave"], params.elder)
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
        print("--- Trace ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    if qa:
        print("\n-- Story QA --")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")
        print("-- World Knowledge QA --")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        c = asp_valid_combos()
        print(f"{len(c)} compatible (place, activity, prize) combos:")
        for p, a, pr in c:
            print(f"  {p:15} {a:8} {pr:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(f"Error: {e}")
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
        header = f"### {sample.params.name} ({sample.params.activity})" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
```
