#!/usr/bin/env python3
"""
storyworlds/worlds/explicit_skeletal_impossible_humor_cautionary_inner_monologue.py
===================================================================================

A tiny pirate-tale storyworld with a cautionary joke, an inner-monologue turn,
and a careful compromise.

Seed tale sketch:
---
A young pirate wanted to chase an impossible silver fish through the reef while
wearing a precious hat. The old captain could see the trouble coming, because
the reef would scrape the boat and salt-water would ruin the hat. The captain
warned the child, the child grumbled in secret, and then they chose a clever
safer way: they took a lantern and a rope, waited for the tide, and followed
the glittering fish without wrecking the day.

World model:
---
- physical meters: splash, scrape, soak, damage, darkness, fatigue
- emotional memes: joy, worry, defiance, relief, pride, caution

Narrative instruments:
---
- Humor: the impossible fish is outrageously slippery and the crew keeps
  imagining grand plans that are too small for the sea.
- Cautionary: the captain predicts damage before it happens and explains why.
- Inner monologue: the child thinks in a little pirate voice before choosing
  better.
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
    kind: str = "thing"  # character | thing
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {k: 0.0 for k in ["splash", "scrape", "soak", "damage", "darkness", "fatigue"]}
        if not self.memes:
            self.memes = {k: 0.0 for k in ["joy", "worry", "defiance", "relief", "pride", "caution"]}

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
    keyword: str = ""
    humor: str = ""
    caution: str = ""
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ["splash", "scrape", "soak", "darkness"]:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("damage", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["damage"] += 1
                out.append(f"{actor.id}'s {item.label} took the rough {mess}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["damage"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would worry the captain.")
    return out


def _r_defiance(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("defiance", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["caution"] += 1
        return ["__defiance__"]
    return []


CAUSAL_RULES = [Rule("damage", _r_damage), Rule("worry", _r_worry), Rule("defiance", _r_defiance)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__defiance__")
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
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "traits": list(v.traits), "owner": v.owner, "caretaker": v.caretaker,
        "worn_by": v.worn_by, "region": v.region, "protective": v.protective,
        "covers": set(v.covers), "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["damage"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This harbor cannot host that pirate business.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "small")
    world.say(f"{hero.id} was a little {trait} pirate who loved a bold tale and a clean deck.")


def loves_thing(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} loved {activity.gerund} and kept {hero.pronoun('possessive')} "
        f"{prize.label} tucked close, as if the sea itself had promised to be careful."
    )


def arrive(world: World, hero: Entity, captain: Entity, activity: Activity) -> None:
    world.say(
        f"One moon-bright evening, {hero.id} and {hero.pronoun('possessive')} "
        f"{captain.label} went to {world.setting.place}."
    )
    world.say(
        f"The water was sly and shiny there, and {activity.humor} "
        f""
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, even if the idea felt impossible and grand.")
    world.say(f'Inside, {hero.id} thought, "Aye, I can do it. I only need a brave plan and a bit of luck."')


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    captain.memes["caution"] += 1
    world.say(
        f'"If ye try that, {hero.id}, {hero.pronoun("possessive")} {prize.label} will get {activity.soil}," '
        f"{captain.id} said. \"The sea loves a laugh, but not that kind.\""
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} frowned and pretended to study the horizon, though {hero.pronoun('possessive')} "
        f"belly felt a wee knot of worry."
    )
    world.say(f'In {hero.id}\'s head, a tiny voice muttered, "Maybe the captain is right. Maybe the reef is a terrible place to test a hat."')
    world.say(f"{hero.id} still tried to {activity.rush}, just a little too quickly.")


def grab_conflict(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["defiance"] += 0.5
    world.say(
        f"Then {captain.id} caught {hero.pronoun('possessive')} sleeve and held it gently."
    )


def compromise(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=captain.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{captain.id} grinned. "How about we {gear_def.prep} and still chase the fish?"'
    )
    return gear_def


def accept(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} blinked, then nodded. The little knot in {hero.pronoun('possessive')} chest loosened."
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed dry, "
        f"and the impossible silver fish looked a lot less impossible with a lantern swinging beside the boat."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, captain_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["quick", "stubborn"])
    ))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="old captain"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=captain.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_thing(world, hero, activity, prize)
    world.para()
    arrive(world, hero, captain, activity)
    wants(world, hero, activity)
    warn(world, captain, hero, activity, prize)
    defies(world, hero, activity)
    grab_conflict(world, captain, hero)
    world.para()
    gear_def = compromise(world, captain, hero, activity, prize)
    if gear_def:
        accept(world, captain, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, gear=gear_def, setting=setting)
    return world


SETTINGS = {
    "cove": Setting(place="the moonlit cove", affords={"reef", "fog", "storm"}),
    "harbor": Setting(place="the sleepy harbor", affords={"fog", "storm"}),
    "reef": Setting(place="the bright reef", affords={"reef"}),
}

ACTIVITIES = {
    "reef": Activity(
        id="reef",
        verb="chase the silver fish through the reef",
        gerund="chasing silver fish through the reef",
        rush="dash after the silver fish",
        mess="scrape",
        soil="scratched and salty",
        zone={"feet", "legs"},
        keyword="reef",
        humor="the fish was so slippery it seemed to have a secret map and a joke tucked into its fins",
        caution="The rocks down there are sharp enough to nibble boots.",
        tags={"reef", "fish", "salt"},
    ),
    "fog": Activity(
        id="fog",
        verb="sail through the fog",
        gerund="sailing through the fog",
        rush="push into the fog",
        mess="darkness",
        soil="hard to see",
        zone={"torso"},
        keyword="fog",
        humor="the fog was thick enough to hide a giggling gull",
        caution="Fog makes the sea feel close and tricky.",
        tags={"fog", "darkness"},
    ),
    "storm": Activity(
        id="storm",
        verb="ride out the storm",
        gerund="riding out the storm",
        rush="charge into the storm",
        mess="soak",
        soil="soaking wet",
        zone={"torso", "legs"},
        keyword="storm",
        humor="even the waves looked as if they were stomping tiny pirate feet",
        caution="Storm spray can drench a sailor in one snap of thunder.",
        tags={"storm", "wet"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright captain's hat", type="hat", region="torso"),
    "sash": Prize(label="sash", phrase="a red silk sash", type="sash", region="torso"),
    "boots": Prize(label="boots", phrase="new sea boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(id="lantern", label="a brass lantern", covers={"torso"}, guards={"darkness"}, prep="take a brass lantern along", tail="came back with the lantern held high"),
    Gear(id="rope", label="a stout rope", covers={"feet", "legs"}, guards={"scrape"}, prep="tie a stout rope to the skiff", tail="sailed back with the rope ready"),
    Gear(id="cloak", label="an oilskin cloak", covers={"torso", "legs"}, guards={"soak"}, prep="pull on an oilskin cloak", tail="set out in the oilskin cloak"),
]

GIRL_NAMES = ["Mira", "Nell", "Sia", "Tessa", "Luna"]
BOY_NAMES = ["Pip", "Jory", "Finn", "Owen", "Rook"]
TRAITS = ["curious", "brave", "sly", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a pirate tale for a small child about "{act.keyword}" and a careful rescue.',
        f"Tell a humorous cautionary story where {hero.id} tries to {act.verb} while protecting {prize.phrase}.",
        f"Write a short sea story with an inner monologue, a warning, and a clever safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {captain.id} warn {hero.id} about {prize.label}?",
            answer=f"{captain.id} warned {hero.id} because {act.caution} The {prize.label} could have gotten {act.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} think in secret before choosing the safer plan?",
            answer=f"{hero.id} thought, \"Maybe the captain is right. Maybe the sea needs a better plan than a reckless dash.\"",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help the pirate story end well?",
            answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out: list[QAItem] = []
    if "reef" in tags:
        out.append(QAItem(
            question="What is a reef?",
            answer="A reef is a stretch of rock or coral in the sea where waves can break and boats must be careful.",
        ))
    if "fog" in tags:
        out.append(QAItem(
            question="What does fog do?",
            answer="Fog makes the air cloudy so it is hard to see far away.",
        ))
    if "storm" in tags:
        out.append(QAItem(
            question="Why is a storm risky at sea?",
            answer="A storm can bring strong wind, big waves, and lots of water that make sailing hard.",
        ))
    out.append(QAItem(
        question="What does a lantern help with on a dark night?",
        answer="A lantern gives light so sailors can see where they are going.",
    ))
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
    StoryParams(place="cove", activity="reef", prize="hat", name="Pip", gender="boy", captain="captain", trait="curious"),
    StoryParams(place="harbor", activity="fog", prize="sash", name="Mira", gender="girl", captain="captain", trait="stubborn"),
    StoryParams(place="cove", activity="storm", prize="boots", name="Rook", gender="boy", captain="captain", trait="cheerful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach {noun}, so there is no honest pirate warning.)"
    return f"(No story: nothing in the gear chest can both cover {noun} and fix the mess from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} does not fit that gender constraint here; try {ok}.)"


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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    ap = argparse.ArgumentParser(description="A pirate tale world of caution, humor, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, captain="captain", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "stubborn"])
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
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
