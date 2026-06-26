#!/usr/bin/env python3

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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

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
        female = {"befriender", "ally", "companion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"companion": "friend", "ally": "ally", "enemy": "foe"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the emerald land"
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
    region: str = ""
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"befriender", "ally"})

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

def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["spite"] < THRESHOLD:
            continue
        for target in world.entities.values():
            if target.id == "vicious_piccalilli" or target.type == "jar":
                continue
            sig = ("spread", target.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            target.meters["tainted"] += 1
            if target.plural:
                out.append(f"The vicious piccalilli clings to {target.phrase}, fouling them all.")
            else:
                out.append(f"The vicious piccalilli clings to {target.phrase}, fouling it.")
    return out

def _r_threaten(world: World) -> list[str]:
    for ent in world.entities.values():
        if ent.meters["tainted"] >= THRESHOLD and ent.id != "vicious_piccalilli":
            sig = ("extinct", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            return [f"The land faces extinction as {ent.phrase}'s very soul turns into vicious piccalilli."]
    return []

def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["doubt"] >= THRESHOLD and actor.memes["friendship"] >= THRESHOLD:
            sig = ("tension", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            return [f"{actor.id} feels the hot brand of their friendship singeing their doubting heart."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
    Rule(name="threaten", tag="physical", apply=_r_threaten),
    Rule(name="conflict", tag="social", apply=_r_conflict),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def activity_delight(activity: Activity) -> str:
    return {
        "reclaim": "the earth undulates as friendship draws strength from unity",
        "cap": "the lid fell into place like a shield forged by kinship",
        "gather": "the circle of friendship pulsed with golden light"
    }.get(activity.id, "it carried the hope of renewal within its heart")

def setting_detail(setting: Setting, activity: Activity) -> str:
    return {
        "emerald_land": "The emerald land shimmered under endless twilight, many ages of plenty behind it.",
        "thicket": "A thick mist curled between the trees, heavy with the scent of onions and vinegar.",
    }.get(setting.place, f"{setting.place.capitalize()} lay in the trembling hush before dawn.")

def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} remained untouched by the corruption"

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.memes[activity.mess] += 1
    propagate(world, narrate=narrate)

def introduce_hero(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "")
    world.say(f"{hero.id} stood at the edge of {world.setting.place}, {trait} bridge of fate between friendship and ruin.")

def hero_loves_friendship(world: World, hero: Entity) -> None:
    hero.memes["friendship"] += 1
    world.say(f"{hero.pronoun().capitalize()} felt the ancient call of friendship singing through {hero.pronoun('possessive')} veins, stronger than any winter's bite.")

def villains_rise(world: World) -> None:
    world.say("From the sour marshes came the vicious piccalilli, seeping into cracks and creeping into hearts.")

def befriender_arrives(world: World, hero: Entity) -> None:
    world.say(f"Just at the darkest hour, {hero.id}’s companion appeared out of the mist, bearing a jar of golden remembrance.")

def ally_speaks(world: World, hero: Entity, ally: Entity, prize: Entity) -> None:
    world.say(
        f'{ally.pronoun().capitalize()} gripped {hero.pronoun("object")} hand and said, '
        f'"We must reclaim this land before the vicious piccalilli claims us all. '
        f'Will you help me jar the plague?"'
    )

def hesitates(world: World, hero: Entity, ally: Entity, activity: Activity) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f"{hero.id} felt the cold teeth of hesitation biting. "
        f'“But what if the jar cannot hold such malice?” {hero.pronoun()} whispered.'
    )

def grabs_jar(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} took up {prize.phrase} with both trembling hands, "
        f"sensing the faint, flickering warmth of kinship guiding them."
    )

def reclaimer_acts(world: World, hero: Entity, ally: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["confidence"] += 1
    ally.memes["stewardship"] += 1
    world.say(
        f"{hero.id} and {ally.label} together raised {prize.label} aloft, chanting the old names of unity. "
        f"The vicious stench of piccalilli recoiled from the golden arc of kinship."
    )
    prizeworld = world.get(prize.id)
    if prizeworld:
        world.say(f"As the lid sealed shut, the light within {prizeworld.it()} began to glow, "
                  f"fending off the creeping corruption.")

def resolution_saving(world: World, hero: Entity, ally: Entity, prize: Entity) -> None:
    hero.memes["triumph"] += 1
    ally.memes["triumph"] += 1
    world.say(
        f"The emerald land exhaled at last. The vicious piccalilli’s power wilted, "
        f"vanquished by the unbroken circle of friendship. {hero.id}'s {ally.label_word.capitalize()} "
        f"laughed together, holding {prize.label} high as a symbol of their victory."
    )

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Aria", type_hero: str = "befriender",
         hero_traits: Optional[list[str]] = None, ally_type: str = "companion") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=name,
        kind="character",
        type=type_hero,
        traits=["young"] + (hero_traits or ["wise", "stubborn"]),
    ))
    ally = world.add(Entity(
        id="Bryce",
        kind="character",
        type=ally_type,
        label="Bryce",
        traits=["faithful"],
    ))
    vicious = world.add(Entity(
        id="vicious_piccalilli",
        kind="thing",
        type="plague",
        label="vicious piccalilli",
        phrase="the vicious piccalilli",
        traits=["malevolent", "spreading"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce_hero(world, hero)
    hero_loves_friendship(world, hero)
    hero.worn_by = prize.id

    world.para()
    villains_rise(world)

    world.para()
    world.say(setting_detail(setting, activity))
    befriender_arrives(world, hero)

    world.para()
    ally_speaks(world, hero, ally, prize)
    hesitates(world, hero, ally, activity)
    ally_speaks(world, hero, ally, prize)
    grabs_jar(world, hero, prize)
    reclaimer_acts(world, hero, ally, prize, activity)

    world.para()
    resolution_saving(world, hero, ally, prize)

    world.facts.update(
        hero=hero,
        companion=ally,
        plague=vicious,
        prize=prize,
        activity=activity,
        setting=setting,
        resolved=True,
        saved=True
    )
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for ages 5–8 about "friendship vs plague," '
        f'using the phrase "vicious piccalilli" and ending with the words "circle of kinship".',
        f"Compose a child-friendly myth where {f['hero'].id} and their {f['companion'].label_word} "
        f"save a land from a spreading curse named the vicious piccalilli.",
        'Tell a tale that teaches "no friendship is too small to light the darkest hour" '
        f'while mentioning "vicious piccalilli".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, prize = f["hero"], f["companion"], f["prize"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")

    qa: list[QAItem] = [
        QAItem(
            question=f"Who rescued the emerald land from the vicious piccalilli?",
            answer=f"It was {hero.id}, the young {hero.type}, and their {ally.label_word} {ally.id}, who together "
                   f"sealed {pos} jar and banished the plague."
        ),
        QAItem(
            question="What object saved the emerald land from extinction?",
            answer=f"The {prize.label} became the vessel that held back the vicious piccalilli, "
                   f"so the land could breathe again."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the vicious piccalilli finally stop spreading?",
            answer=(
                f"When {hero.id} and {ally.id} together lifted the {prize.label} high in the circle of kinship, "
                f"the warmth of friendship pushed back the plague until it had no place left to hide."
            )
        ))
    return qa

KNOWLEDGE = {
    "friendship": [(
        "What is friendship?",
        "Friendship is two or more hearts sharing courage and light even in the darkest hour."
    )],
    "plague": [(
        "What is a plague?",
        "A plague is something evil that spreads quickly and harms everything it touches."
    )],
    "piccalilli": [(
        "What is piccalilli?",
        "Piccalilli is a tangy relish made of chopped pickles, peppers, and onions in a sweet vinegar sauce."
    )],
    "emeral": [(
        "What is the emerald land?",
        "The emerald land is a magical place where the grass glows green and friendships grow stronger every day."
    )],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"friendship", "plague", "piccalilli", "emerald"}
    for tag in ["friendship", "plague", "piccalilli", "emerald"]:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE.get(tag, []))
    return out

SETTINGS = {
    "emerald_land": Setting(place="the emerald land", indoor=False, affords={"reclaim", "cap"}),
    "thicket": Setting(place="the sour thicket", indoor=False, affords={"gather", "cap"}),
}

ACTIVITIES = {
    "reclaim": Activity(
        id="reclaim",
        verb="reclaim the emerald land",
        gerund="reclaiming the emerald land",
        rush="strike down the vicious piccalilli",
        mess="darkness",
        soil="engulfed by the vice",
        zone=set(),
        keyword="vicious piccalilli",
        tags={"plague", "friendship", "rescue"},
    ),
    "cap": Activity(
        id="cap",
        verb="cap the jar of vicious piccalilli",
        gerund="capping the jar of vicious piccalilli",
        rush="slam the lid shut",
        mess="corruption",
        soil="lost to corruption",
        zone=set(),
        keyword="vicious piccalilli",
        tags={"plague", "jar", "friendship"},
    ),
    "gather": Activity(
        id="gather",
        verb="gather golden light",
        gerund="gathering golden light",
        rush="grab the last gleam",
        mess="hope",
        soil="stifled hope",
        zone=set(),
        keyword="golden light",
        tags={"hope", "friendship"},
    ),
}

PRIZES = {
    "jar": Prize(
        label="jar",
        phrase="jar",
        type="jar",
        region="hands",
        plural=False,
    ),
}

GEAR = [
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: friendship vs vicious piccalilli plague. "
                    "Unspecified choices are randomized.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible runs")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list ASP-valid combos")
    ap.add_argument("--verify", action="store_true", help="compare clingo vs Python gates")
    ap.add_argument("--show-asp", action="store_true", help="print ASP rules")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(f"Unknown place: {args.place}")
    params = StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        activity="cap",
        prize="jar",
        name=rng.choice(["Aria", "Lyra", "Eira", "Soren", "Bryce"]),
        type_hero=rng.choice(["befriender", "ally"]),
        ally_type=rng.choice(["companion", "friend"]),
        seed=None,
    )
    return params

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    type_hero: str
    ally_type: str
    seed: Optional[int] = None

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.type_hero,
        ["young", "wise"],
        params.ally_type,
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

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v >= THRESHOLD}
        if not meters and not e.memes:
            continue
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if e.memes:
            memes = {k: v for k, v in e.memes.items() if v >= THRESHOLD}
            if memes:
                bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:15} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

CURATED = [
    StoryParams(
        place="emerald_land",
        activity="cap",
        prize="jar",
        name="Aria",
        type_hero="befriender",
        ally_type="companion",
        seed=None,
    ),
]

ASP_RULES = r"""
% A quest is valid when friendship and ally work together to contain the plague
valid_story(Place, Hero, Ally, Prize) :-
    place(Place),
    character(Hero), hero_type(Hero, "befriender"),
    character(Ally), ally_type(Ally, "companion"),
    object(Prize), prize_type(Prize, "jar"),
    plague(P).
% plague is always vicious_piccalilli
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("object", pid))
        lines.append(asp.fact("prize_type", pid, pr.type))
    lines.append(asp.fact("plague", "vicious_piccalilli"))
    for n in ["Aria", "Lyra", "Eira", "Soren"]:
        lines.append(asp.fact("hero_name", n))
    for a in ["Bryce", "Remy", "Nia"]:
        lines.append(asp.fact("ally_name", a))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
    except Exception as e:
        print(f"ASP verification failed to run clingo: {e}")
        return 1
    print("Mythic story set verified via ASP twin.")
    return 0

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show valid_story/4."))
            stories = sorted(set(asp.atoms(model, "valid_story")))
            print(f"Mythic story set (ASP twin): {len(stories)} canonical variants\n")
            for pl, h, a, pr in stories[:10]:
                print(f"  {h} + {a} -> saved {pr} in {pl}")
            if len(stories) > 10:
                print(f"  ... ({len(stories)-10} more)")
        except Exception as e:
            print(f"ASP listing failed: {e}")
            sys.exit(1)
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
            header = f"### {p.name}: the {p.place} myth"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
