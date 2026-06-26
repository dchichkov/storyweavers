#!/usr/bin/env python3
"""
storyworlds/worlds/shrine_sound_effects_heartwarming.py
=======================================================

A small heartwarming storyworld set at a shrine, where a child loves making
sound effects and the adults worry about one delicate thing staying safe.

Seed inspiration:
- shrine
- sound effects
- heartwarming

Premise:
A child wants to help make a shrine scene feel alive by adding bells, taps,
and soft rustles. A caregiver worries that the noise could shake a delicate
offering. They find a gentler way to make the sounds together, and the shrine
ends the day feeling cozy and cared for.
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
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
    place: str = "the shrine"
    affordance: str = "sound effects"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    effect: str
    zone: set[str]
    keyword: str = "shrine"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("noise", 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("shake", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["shaken"] = item.meters.get("shaken", 0.0) + 1
                item.meters["risk"] = item.meters.get("risk", 0.0) + 1
                changed = True
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} wobbled and needed a careful hand.")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "region": v.region,
        "protective": v.protective, "covers": set(v.covers), "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["noise"] = 1.0
    propagate(sim)
    prize = sim.entities.get(prize_id)
    return bool(prize and prize.meters.get("risk", 0.0) >= THRESHOLD)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved listening for tiny sounds at {world.setting.place}.")


def love_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} and making the scene feel alive.")


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.type} brought home {hero.pronoun('object')} {prize.phrase} for the shrine table.")


def love_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One quiet afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say("Paper streamers moved in the breeze, and the little shrine path looked soft and calm.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the idea was loud enough to make the nearest things tremble.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_risk(world, hero, activity, prize.id):
        return False
    world.facts["predicted_effect"] = activity.effect
    world.say(f'"If you make those sounds too hard, your {prize.label} could get {activity.effect}," {parent.pronoun("possessive")} {parent.type} said softly.')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} frowned, then tried to {activity.rush} anyway.")


def offer_compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    if not prize_at_risk(activity, prize):
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_risk(world, hero, activity, prize.id):
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{parent.pronoun("possessive").capitalize()} {parent.type} smiled and said, "How about we {gear_def.prep} first?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face brightened. {hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {parent.type} and said, \"Yes, please!\"")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed safe, and the shrine sounded warm instead of sharp.")
    world.say(f"At the end, the little place felt even kinder because everyone had listened to one another.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.say(f"{hero.id} was a {trait} little {hero.type} who liked helping at {setting.place}.")
    introduce(world, hero)
    love_activity(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    love_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    world.para()
    gear_def = offer_compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, trait=trait)
    return world


SETTINGS = {
    "shrine": Setting(place="the shrine"),
    "festival_shrine": Setting(place="the shrine at the festival"),
    "forest_shrine": Setting(place="the little forest shrine"),
}

ACTIVITIES = {
    "sound_effects": Activity(
        id="sound_effects",
        verb="make sound effects",
        gerund="making sound effects",
        rush="stamp and clap louder and louder",
        noise="loud",
        effect="rumpled",
        zone={"table", "hands"},
        keyword="shrine",
        tags={"shrine", "sound", "music"},
    ),
    "bell_ringing": Activity(
        id="bell_ringing",
        verb="ring the shrine bell",
        gerund="ringing the shrine bell",
        rush="ring the bell again and again",
        noise="bright",
        effect="shaken",
        zone={"table"},
        keyword="bell",
        tags={"shrine", "sound", "music"},
    ),
}

PRIZES = {
    "tea_cup": Prize(label="tea cup", phrase="a little tea cup", type="cup", region="table"),
    "paper_wish": Prize(label="paper wish", phrase="a folded paper wish", type="paper", region="table"),
    "offering_bowl": Prize(label="offering bowl", phrase="a small offering bowl", type="bowl", region="table"),
}

GEAR = [
    Gear(id="felt_pad", label="a felt pad", covers={"table"}, guards={"sound_effects", "bell_ringing"},
         prep="put the tea cup on a felt pad", tail="placed the tea cup on a felt pad", plural=False),
    Gear(id="cloth_wrap", label="a soft cloth wrap", covers={"table"}, guards={"sound_effects", "bell_ringing"},
         prep="wrap the little prize in a soft cloth wrap", tail="wrapped the little prize in a soft cloth wrap"),
]

GIRL_NAMES = ["Mina", "Hana", "Aya", "Nina", "Mila", "Sora"]
BOY_NAMES = ["Ren", "Kaito", "Noel", "Yuki", "Taro", "Eli"]
TRAITS = ["gentle", "curious", "cheerful", "quiet", "helpful", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story set at {world.setting.place} where a child named {hero.id} wants to {act.verb} but stays gentle with a {prize.label}.',
        f"Tell a cozy story about {hero.id} and {hero.pronoun('possessive')} {parent.type} finding a quieter way to make shrine sounds.",
        f'Write a short child-friendly story that includes the word "shrine" and ends with everyone feeling warm and close.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the shrine?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun('subject')} loved the cheerful sound it made.",
        ),
        QAItem(
            question=f"What worried {parent.type} about the {prize.label}?",
            answer=f"{parent.pronoun('possessive').capitalize()} {parent.type} worried that {hero.pronoun('possessive')} {prize.label} could get {act.effect} if the sounds were too loud.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep playing safely?",
            answer=f"A {f['gear'].label if f.get('gear') else 'gentler plan'} helped {hero.id} {act.verb} without harming the {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shrine?",
            answer="A shrine is a special place where people go to be quiet, remember, and show care.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are extra sounds, like bells, taps, or rustles, that help a scene feel alive.",
        ),
        QAItem(
            question="Why can a soft pad help a cup?",
            answer="A soft pad can keep a cup from wobbling and make it less likely to tip over.",
        ),
    ]


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
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shrine", activity="sound_effects", prize="tea_cup", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="festival_shrine", activity="bell_ringing", prize="paper_wish", name="Ren", gender="boy", parent="father", trait="thoughtful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not reasonably threaten the {prize.label} in this setup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: a {PRIZES[prize_id].label} doesn't fit the requested {gender} choice in this world.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,A), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- setting(Place), activity(A), prize(P), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("affords", pid, "sound_effects"))
        lines.append(asp.fact("affords", pid, "bell_ringing"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    ap = argparse.ArgumentParser(description="Heartwarming shrine storyworld with sound effects.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:16} {act:14} {prize:12}  [{', '.join(genders)}]")
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
