#!/usr/bin/env python3
"""
storyworlds/worlds/phase_keel_sound_effects_curiosity_pirate_tale.py
====================================================================

A small pirate-tale story world about curiosity, sound effects, and the strange
little noises a ship can make when it is at sea.

Seed premise:
- A child pirate hears odd sounds from the keel.
- Curiosity pulls them below deck.
- A careful grown-up worries about a treasured map getting ruined in the spray.
- A simple, seaworthy fix lets the child investigate safely.

The world is intentionally tiny and constraint-checked: only story combos that
have a believable risk and a believable fix are allowed.
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
MESS_KINDS = {"wet", "salted", "scratchy"}


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

    def __post_init__(self) -> None:
        for k in ["wet", "salted", "scratchy", "dirty"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "curiosity", "worry", "calm", "fear", "pride", "conflict"]:
            self.memes.setdefault(k, 0.0)

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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the ship"
    outdoors: bool = True
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "ship": Setting(place="the ship", outdoors=True, affords={"keel", "sounds", "phase"}),
    "dock": Setting(place="the dock", outdoors=True, affords={"sounds", "phase"}),
}

ACTIVITIES = {
    "keel": Activity(
        id="keel",
        verb="go listen by the keel",
        gerund="listening by the keel",
        rush="dash below to the keel",
        mess="wet",
        soil="sprayed with salt",
        zone={"torso", "legs"},
        weather="stormy",
        keyword="keel",
        tags={"keel", "sound", "sound-effects"},
    ),
    "sounds": Activity(
        id="sounds",
        verb="follow the strange sounds",
        gerund="following the strange sounds",
        rush="hurry toward the clatter",
        mess="scratchy",
        soil="scuffed and scratchy",
        zone={"torso"},
        weather="windy",
        keyword="sound",
        tags={"sound", "sound-effects"},
    ),
    "phase": Activity(
        id="phase",
        verb="check the moon phase",
        gerund="watching the moon phase",
        rush="climb up for a better look",
        mess="wet",
        soil="spattered with spray",
        zone={"torso"},
        weather="stormy",
        keyword="phase",
        tags={"phase", "curiosity"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a folded treasure map", type="map", region="torso"),
    "journal": Prize(label="journal", phrase="a sailor's journal", type="journal", region="torso"),
    "lantern": Prize(label="lantern", phrase="a brass lantern", type="lantern", region="torso"),
}

GEAR = [
    Gear(
        id="oilskin",
        label="an oilskin cloak",
        covers={"torso"},
        guards={"wet"},
        prep="put on an oilskin cloak first",
        tail="went back for the oilskin cloak",
    ),
    Gear(
        id="wrap",
        label="a waxed wrap",
        covers={"torso"},
        guards={"wet", "scratchy"},
        prep="tie on a waxed wrap first",
        tail="tied on the waxed wrap",
    ),
]

GIRL_NAMES = ["Mira", "Nina", "Pia", "Lana", "Tia"]
BOY_NAMES = ["Finn", "Jory", "Rafe", "Ned", "Theo"]
TRAITS = ["curious", "bright-eyed", "brave", "restless", "clever"]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about curiosity and ship sounds.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "mother", "father"])
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
            raise StoryError("No story: that noisy pirate situation does not have a believable safe fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["captain", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, gender, parent, trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.memes["curiosity"] += 1
    actor.meters[activity.mess] += 1
    if narrate:
        world.say(f"{actor.id} {activity.gerund}.")

def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"You\'ll get {prize.phrase} {activity.soil}," {parent.label_word} warned.')
    return True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or [])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a little {hero_traits[0] if hero_traits else 'curious'} {hero.type} aboard {setting.place}.")
    world.say(f"{hero.id} loved the sea, the creak of ropes, and the little splash-splash sounds the ship made.")
    world.say(f"One day, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved the {prize.label} and kept {prize.it()} close.")

    world.para()
    world.say(f"That night, the wind went whooo and the hull went creak-creak.")
    world.say(f"{hero.id} wanted to {activity.verb} to learn where the sound was coming from.")
    warn(world, parent, hero, activity, prize)
    world.say(f"But {hero.id}'s curiosity tugged hard, and {hero.pronoun().capitalize()} decided to {activity.rush}.")
    _do_activity(world, hero, activity, narrate=True)
    world.say(f"Down below, the ship gave a THUMP and then a soft drip-drip from the keel.")

    world.para()
    gear = select_gear(activity, prize)
    assert gear is not None
    if activity.mess in gear.guards:
        world.say(f"{hero.id}'s {parent.label_word} smiled and said, \"How about we {gear.prep} and look together?\"")
        world.say(f"They {gear.tail}.")
    hero.memes["worry"] = 0.0
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    world.say(f"At last, {hero.id} saw the truth: a tiny shell was scraping the keel, making the funny sound.")
    world.say(f"They brushed it away, and the ship answered with a happier sigh, shhhhhh.")
    world.say(f"{hero.id} stood by the quiet keel, {activity.gerund}, with {prize.label} still safe and clean.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a pirate tale for a small child about curiosity, sound effects, and the word "{act.keyword}".',
        f"Tell a story where {hero.id} hears a strange sound by the keel and {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Make a gentle pirate story with creak-creak, drip-drip, and a happy fix on {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What was {hero.id} curious about on the ship?",
            answer=f"{hero.id} was curious about the strange creak-creak sound coming from the keel.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried that the {prize.label} could get {act.soil} if {hero.id} hurried below deck.",
        ),
        QAItem(
            question=f"What helped {hero.id} investigate safely?",
            answer=f"{gear.label} helped because it kept the important part of {hero.id}'s outfit safe from the wet spray.",
        ),
        QAItem(
            question=f"What made the ship sound better in the end?",
            answer="A tiny shell was brushed away from the keel, so the ship stopped making the bad scraping sound.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the keel of a ship?",
            answer="The keel is the long bottom part of a ship that helps hold the ship steady in the water.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like creak-creak or drip-drip that help you imagine the noises in a scene.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and asking questions or looking closely at something.",
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
    StoryParams("ship", "keel", "map", "Mira", "girl", "captain", "curious"),
    StoryParams("ship", "sounds", "journal", "Finn", "boy", "captain", "restless"),
    StoryParams("dock", "phase", "lantern", "Tia", "girl", "mother", "clever"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
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


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for t in vals:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
