#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale set in an apartment courtyard,
with magic, bravery, and a trawler as the key object.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the apartment courtyard"
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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(g.region == region or region in getattr(g, "covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("magic", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("magic_burst", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"A bright spell flickered around {actor.id}, like a tiny star with a cape.")
    return out


def _r_fix_trawler(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("bravery", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("magic", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.type != "trawler":
                continue
            sig = ("steady", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.id} held the trawler steady with brave hands and a careful heart.")
    return out


CAUSAL_RULES = [
    _r_magic,
    _r_fix_trawler,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy() if hasattr(world, "copy") else None
    if sim is None:
        return {"soiled": False}
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def activity_blurb(activity: Activity) -> str:
    return {
        "spellpractice": "the sparks danced like fireflies",
        "courtyardflight": "the air felt wide enough for a hero",
        "shieldrun": "the shiny shield flashed like moonlight",
    }.get(activity.id, "the whole courtyard felt ready for adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the apartment courtyard":
        return "Between the apartment walls, the courtyard made a cozy little stage for heroics."
    return f"{setting.place.capitalize()} waited quietly for the next brave move."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.meters["magic"] = actor.meters.get("magic", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved superhero missions in the apartment courtyard.")


def love_magic(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_magic"] = hero.memes.get("love_magic", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {activity_blurb(activity)}.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One bright afternoon, "
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label_word} noticed the old trawler nearby.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    risk = prize.region in activity.zone
    if not risk:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f"\"You'll get your {prize.label} {activity.soil},\" {hero.pronoun('possessive')} {parent.label_word} said.")
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} frowned, then tried to {activity.rush} anyway.")


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(f"Then {hero.pronoun('possessive')} {parent.label_word} took {hero.pronoun('possessive')} hand and said, \"Bravery means choosing wisely.\"")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if prize.region in g.covers and activity.mess in g.guards:
            gear = g
            break
    if gear is None:
        return None
    ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id, plural=gear.plural))
    ent.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled. \"How about we {gear.prep}?\"")
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(f"{hero.id} grinned and hugged {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(f"Together they {gear.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed safe and clean.")
    hero.memes["conflict"] = 0.0


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, plural=prize_cfg.plural))
    trawler = world.add(Entity(id="trawler", type="trawler", label="toy trawler", phrase="a little red toy trawler"))
    trawler.worn_by = hero.id

    introduce(world, hero)
    love_magic(world, hero, activity)
    world.say(f"{hero.id} had a favorite toy trawler, and {hero.pronoun('possessive')} {parent.label_word} had tucked away a shiny prize.")
    world.say(f"{hero.id} loved {prize.phrase} as much as {hero.pronoun('possessive')} toy trawler.")

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero)

    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, trawler=trawler)
    return world


SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", indoor=False, affords={"spellpractice", "courtyardflight", "shieldrun"}),
}

ACTIVITIES = {
    "spellpractice": Activity(
        id="spellpractice",
        verb="practice a magic spell",
        gerund="casting magic spells",
        rush="spin the wand and blast sparks",
        mess="sparkly",
        soil="dusted with glitter",
        zone={"torso"},
        weather="",
        keyword="magic",
        tags={"magic"},
    ),
    "courtyardflight": Activity(
        id="courtyardflight",
        verb="fly over the courtyard",
        gerund="flying bravely",
        rush="jump up like a hero",
        mess="windy",
        soil="all ruffled up",
        zone={"torso", "legs"},
        weather="",
        keyword="bravery",
        tags={"bravery"},
    ),
    "shieldrun": Activity(
        id="shieldrun",
        verb="race with a shield",
        gerund="racing with a shield",
        rush="dash across the tiles",
        mess="dusty",
        soil="covered in courtyard dust",
        zone={"torso"},
        weather="",
        keyword="superhero",
        tags={"bravery"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright blue cape", type="cape", region="torso"),
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
}

GEAR = [
    Gear(id="spellcloak", label="a spellproof cloak", covers={"torso"}, guards={"sparkly", "windy", "dusty"}, prep="put on a spellproof cloak", tail="walked back into the courtyard wearing the spellproof cloak"),
    Gear(id="hero_mask", label="a hero mask", covers={"torso"}, guards={"sparkly", "dusty"}, prep="put on a hero mask first", tail="returned with the hero mask on", plural=False),
]

GIRL_NAMES = ["Mina", "Luna", "Tess", "Nia", "Rosa"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Ezra", "Kai"]
TRAITS = ["brave", "curious", "spirited", "kind"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and any(prize.region in g.covers and act.mess in g.guards for g in GEAR):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short superhero story for a young child with the words "magic" and "bravery" in {world.setting.place}.',
        f"Tell a gentle adventure where {hero.id} wants to {act.verb} but must protect {prize.label}.",
        f"Write a story about a child, a toy trawler, and a safe magical compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the apartment courtyard?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun().capitalize()} felt like a superhero.
",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because {prize.label} could get {act.soil} if {hero.id} played without care.",
        ),
        QAItem(
            question=f"What helped {hero.id} play safely at the end?",
            answer=f"{gear.label if gear else 'Careful choices'} helped {hero.id} keep playing safely while the {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is magic in stories?", answer="Magic is a special kind of power that can make surprising things happen."),
        QAItem(question="What is bravery?", answer="Bravery means doing something even when you feel nervous, while still trying to do the right thing."),
        QAItem(question="What is a trawler?", answer="A trawler is a kind of boat, and in a child's story it can also be a favorite toy boat."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="courtyard", activity="spellpractice", prize="shirt", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="courtyard", activity="courtyardflight", prize="cape", name="Owen", gender="boy", parent="father", trait="curious"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with magic, bravery, and a trawler.")
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
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
