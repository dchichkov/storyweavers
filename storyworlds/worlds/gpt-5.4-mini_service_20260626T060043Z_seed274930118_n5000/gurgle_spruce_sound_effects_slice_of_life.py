#!/usr/bin/env python3
"""
Storyworld: gurgle & spruce sound effects, slice-of-life edition.

A child notices the little sounds of an ordinary day — a kettle gurgle, a spoon
clink, a soft page rustle — and wants to spruce up a tiny home scene by making a
sound-effects story. A cautious grown-up worries the recording gear could get
spattered or dropped, so the story turns on a gentle compromise that keeps the
scene cozy and the equipment dry.

This script is self-contained and follows the Storyweavers world contract.
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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "gran"}
        male = {"boy", "father", "dad", "man", "grandfather", "granpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
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
        self.soundscape: list[str] = []

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            parts = []
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            if meters:
                parts.append(f"meters={meters}")
            if memes:
                parts.append(f"memes={memes}")
            if e.protective:
                parts.append(f"covers={sorted(e.covers)}")
            elif e.region:
                parts.append(f"region={e.region}")
            lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
        lines.append(f"  soundscape: {self.soundscape}")
        return "\n".join(lines)


def _r_spatter(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            if actor.meters.get("spritz", 0.0) < THRESHOLD:
                continue
            sig = ("spatter", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damp"] = item.meters.get("damp", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little damp.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters.get("damp", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would mean extra work for {carer.label}.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("helping", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        out.append(f"The worry softened into a happier plan.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spatter, _r_worry, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return {
        "kitchen": "The kitchen smelled warm and ordinary, like toast and soap.",
        "living_room": "The living room was neat and sunny, with a couch waiting like a soft hill.",
        "porch": "The porch looked small and cozy, with a little bench by the door.",
        "laundry_room": "The laundry room hummed quietly, full of folded towels.",
    }.get(setting.place, f"{setting.place.capitalize()} felt calm and ready for an everyday task.")


def place_label(place: str) -> str:
    return {
        "kitchen": "the kitchen",
        "living_room": "the living room",
        "porch": "the porch",
        "laundry_room": "the laundry room",
    }.get(place, place)


def predict_spatter(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["spritz"] = 1.0
    item = sim.get(prize_id)
    sim.get(actor.id).meters[activity.mess] = 1.0
    _r_spatter(sim)
    return {"damp": item.meters.get("damp", 0.0) >= THRESHOLD}


def can_fix(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, meters={"spritz": 0.0}, memes={"curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="mom",
        meters={"work": 0.0}, memes={"worry": 0.0},
    ))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    world.say(f"{hero.id} was a little {trait} {hero.type} who liked noticing tiny sounds.")
    world.say(f"At home, {hero.pronoun().capitalize()} loved {activity.gerund}, and {activity.sound} was {hero.pronoun('possessive')} favorite one.")
    world.say(f"One day, {parent.label} had just bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} liked how fresh {prize.label} looked, and wanted the whole day to feel extra spruce and bright.")

    world.para()
    world.say(setting_detail(setting))
    world.say(f"At {place_label(setting.place)}, {hero.id} wanted to {activity.verb} and make a tiny sound-effects scene.")
    hero.meters[activity.mess] = 1.0
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.soundscape.append(activity.sound)
    if predict_spatter(world, hero, activity, prize.id)["damp"]:
        world.say(f'"If you do that, your {prize.label} might get damp," {parent.label} said.')
        world.say(f"{hero.id} heard the worry, but {hero.pronoun('possessive')} feet still wanted to hurry.")
        hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
        hero.meters["spritz"] = 1.0
        world.say(f"{hero.id} started to {activity.rush}.")
        propagate(world)
        hero.memes["worry"] = 1.0

    world.para()
    gear_def = can_fix(activity, prize)
    if gear_def is None:
        raise StoryError("No safe, natural compromise fits this sound and this prize.")
    if activity.mess not in gear_def.guards or prize.region not in gear_def.covers:
        raise StoryError("The chosen gear does not actually protect the prize.")

    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))
    gear.worn_by = hero.id
    world.say(f"{parent.label} smiled and said, 'How about we {gear_def.prep}?'")
    world.say(f"{hero.id}'s face brightened. Together they decided the scene could still be cute and careful.")
    hero.memes["helping"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    parent.memes["worry"] = 0.0
    world.soundscape.extend([activity.sound, "soft footstep", "gentle clink"])
    world.say(f"They {gear_def.tail}, and the little sounds came out just right.")
    world.say(f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed dry, and the room felt nicely spruce.")
    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"tea", "plant"}),
    "living_room": Setting(place="the living room", affords={"story", "spruce"}),
    "porch": Setting(place="the porch", affords={"plant", "spruce"}),
    "laundry_room": Setting(place="the laundry room", affords={"spruce", "tea"}),
}

ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="make tea",
        gerund="making tea",
        rush="dash to the kettle",
        sound="gurgle",
        mess="spritz",
        zone={"torso"},
        keyword="gurgle",
        tags={"gurgle", "tea"},
    ),
    "plant": Activity(
        id="plant",
        verb="water the plant",
        gerund="watering the plant",
        rush="run to the sink",
        sound="gurgle",
        mess="spritz",
        zone={"legs", "torso"},
        keyword="gurgle",
        tags={"gurgle", "plant"},
    ),
    "story": Activity(
        id="story",
        verb="read aloud",
        gerund="reading aloud",
        rush="flip to the next page",
        sound="rustle",
        mess="dust",
        zone={"hands"},
        keyword="rustle",
        tags={"story", "rustle"},
    ),
    "spruce": Activity(
        id="spruce",
        verb="spruce up the room",
        gerund="sprucing up the room",
        rush="reach for the cloths",
        sound="tap",
        mess="spritz",
        zone={"torso"},
        keyword="spruce",
        tags={"spruce", "tap"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a little apron with pockets", type="apron", region="torso"),
    "socks": Prize(label="socks", phrase="fresh blue socks", type="socks", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"spritz"},
        prep="put on an apron first",
        tail="finished tidying with an apron on",
    ),
    Gear(
        id="towel",
        label="a folded towel",
        covers={"torso"},
        guards={"spritz"},
        prep="lay down a folded towel first",
        tail="set out a folded towel and kept the splashes small",
    ),
]


GIRL_NAMES = ["Maya", "Ivy", "Nina", "Luna", "Ada", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Milo", "Jude"]
TRAITS = ["curious", "quiet", "cheerful", "gentle", "spirited"]


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
                if prize.region in act.zone and can_fix(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "gurgle": [("What is a gurgle?", "A gurgle is a bubbly sound, like water or tea moving through a pipe or kettle.")],
    "spruce": [("What does spruce mean?", "To spruce something up means to make it neat, tidy, or prettier.")],
    "tea": [("What does a kettle do when water boils?", "A kettle can make a gurgling or whistling sound as the water gets hot.")],
    "plant": [("Why do plants need water?", "Plants need water to stay healthy and keep growing.")],
    "rustle": [("What makes a rustling sound?", "Paper, leaves, or fabric can rustle when they move against each other.")],
    "tap": [("What makes a tapping sound?", "A tap can come from fingers, feet, or little objects knocking lightly on something.")],
    "apron": [("What is an apron for?", "An apron helps keep clothes cleaner while cooking or doing messy work.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a young child that features the sound word "{f["activity"].keyword}" and the feeling of making a home space more spruce.',
        f"Tell a gentle everyday story where {f['hero'].id} wants to {f['activity'].verb} but {f['parent'].label} worries about {f['prize'].phrase}.",
        f"Write a cozy story about a child, a tiny sound effect, and a simple compromise that keeps clothes dry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb}, because {act.sound} was one of the little sounds {hero.id} loved best.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried that the {prize.label} might get damp if {hero.id} got too close while {act.gerund}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep playing without ruining the {prize.label}?",
            answer=f"They used {f['gear'].label} first, so {hero.id} could keep {act.gerund} and the {prize.label} stayed dry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | {world.facts["gear"].id}
    out = []
    for tag, qas in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in qas)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gid, g in [(gear.id, gear) for gear in GEAR]:
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
#show valid/3.
#show valid_story/4.
"""


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
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - a:
        print("  only in python:", sorted(p - a))
    if a - p:
        print("  only in clingo:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sound-effects storyworld.")
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
        if not (pr.region in act.zone and can_fix(act, pr)):
            raise StoryError("No reasonable story fits that activity and prize pair.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, act_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", activity="tea", prize="shirt", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="plant", prize="socks", name="Eli", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="living_room", activity="spruce", prize="apron", name="Ivy", gender="girl", parent="mother", trait="cheerful"),
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
            print(f"  {place:12} {act:10} {prize:10}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
