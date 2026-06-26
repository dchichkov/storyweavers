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

# Threshold for when a meter effect becomes narratable
THRESHOLD = 1.0

# Physical meter keys related to "giddy" spinning
REEL_METERS = {"dizzy", "wobbly"}

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str = ""
    soil: str = ""
    zone: set[str] = field(default_factory=set)
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})

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
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_dizzy_vertigo(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters["dizzy"] >= THRESHOLD:
            sig = ("vertigo", char.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{char.id} felt a little wobbly from so much spinning.")
    return out

def _r_falling(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters["dizzy"] >= (THRESHOLD * 1.5):
            sig = ("fall", char.id)
            if sig not in world.fired:
                world.fired.add(sig)
                char.meters["dirty"] += 1
                out.append(f"{char.id} nearly tumbled, but caught themself at the last instant.")
    return out

def _r_workload(world: World) -> list[str]:
    for item in world.entities.values():
        if item.meters["dirty"] >= THRESHOLD and item.caretaker:
            carer = world.get(item.caretaker)
            carer.meters["workload"] += 1.2
            if ("laundry", carer.id) not in world.fired:
                world.fired.add(("laundry", carer.id))
                return [f"That would mean another load of laundry for {carer.label}."]
    return []

def _r_giddy_joy(world: World) -> list[str]:
    for char in world.characters():
        if char.memes.get("giddy") and char.memes["giddy"] > THRESHOLD:
            char.memes["joy"] += char.memes["giddy"]
            if char.memes["joy"] > THRESHOLD:
                return [f"The pure giddy delight made {char.id}'s giggles rise like bubbles."]
    return []

CAUSAL_RULES = [
    Rule(name="dizzy_vertigo", tag="physical", apply=_r_dizzy_vertigo),
    Rule(name="falling_risk", tag="physical", apply=_r_falling),
    Rule(name="workload_laundry", tag="physical", apply=_r_workload),
    Rule(name="giddy_joy", tag="emotional", apply=_r_giddy_joy),
]

def propagate(world: World, level: int = 1) -> list[str]:
    produced: list[str] = []
    for _ in range(level):
        changed = True
        while changed:
            changed = False
            for rule in CAUSAL_RULES:
                sents = rule.apply(world)
                if sents:
                    changed = True
                    for s in sents:
                        if s not in produced:
                            produced.append(s)
                    if s != "__suppress__":
                        world.say(s)
    world.facts.update(dizzy_peak=max(e.meters.get("dizzy", 0.0) for e in world.characters()))
    return produced

def _do_spin(world: World, actor: Entity, activity: Activity, narrate: bool = True, turns: int = 3) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.memes["giddy"] += turns
    actor.meters["dizzy"] += turns * 0.8
    actor.memes["joy"] += turns * 0.5
    propagate(world, 1)
    if narrate:
        world.say(f"{actor.id} giggled with each twirl, leaning {world.setting.place.replace('the ', '').strip()} more.")

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id.capitalize()} was a {desc} who loved feeling light on {world.setting.place.replace('the ', '').strip()}.")

def loves_spinning(world: World, hero: Entity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved spinning until the world seemed to spin too.")

def arrives_spot(world: World, hero: Entity, parent: Entity) -> None:
    intro = {
        "backyard": f"One breezy afternoon, ",
        "park": f"At the park under the old oak, ",
        "playroom": f"In the cozy playroom, ",
    }.get(world.setting.place, "One day, ")
    world.say(f"{intro}{hero.id} and {parent.label_word} arrived in {world.setting.place}.")

def feels_giddy(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} felt a wave of giddy happiness well up as the wind brushed "
        f"{parent.pronoun('possessive')} {parent.label}. A twirl seemed just the thing!"
    )
    hero.memes["giddy"] = max(2.0, hero.memes.get("giddy", 0.0) + 1.8)

def spin_aimless(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} set off in a happy whirl, {activity.rush.replace('to ','').strip()} in happy circles.")
    _do_spin(world, hero, activity)

def warns_about_dizziness(world: World, parent: Entity, hero: Entity) -> None:
    level = world.get(hero.id).meters.get("dizzy", 0.0)
    world.facts["dizzy_level"] = level
    p = "s" if level > THRESHOLD else ""
    world.say(f'"Too much spinning will make you too dizzy{p}, won\'t it?" {parent.label_word} called out, voice gentle but firm.')

def tries_to_grab(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} wasn't ready to stop just yet — so "
        f"{parent.pronoun('possessive')} {parent.label_word} stepped close, "
        f"hand outstretched, saying, 'A dance has partners, remember?'"
    )
    hero.memes["defiance"] = max(hero.memes.get("defiance",0.0), 0.8)

def pouts_small(world: World, hero: Entity) -> None:
    if hero.memes.get("defiance", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} pulled a face. 'You\'re no fun,' {hero.pronoun()} muttered, cheeks puffed.")

def safer_spin_together(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled softly. '
        f'"Let\'s spin together quietly, then. A small circle, then rest." '
        f'That is the secret to enjoying the giddy without the dip."'
    )
    _do_spin(world, parent, activity, turns=2)
    _do_spin(world, hero, activity, turns=1)
    hero.memes["joy"] += 2.0
    hero.memes["conflict"] = 0.0

def happier_together(world: World, hero: Entity, parent: Entity) -> None:
    world.facts["resolved_spinning"] = True
    world.say(
        f"{hero.id}'s laughter rang clear again, brighter this time, as "
        f"{hero.pronoun('possessive')} {parent.label_word} twirled {hero.pronoun('object')} "
        f"gently about. The world tasted sweet with {parent.pronoun('possessive')} steadying hands."
    )
    world.para()

def tell(setting: Setting, hero_name: str = "Lily", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero_traits = ["playful"] + (hero_traits or ["daring"])
    hero = world.add(Entity(
        id=hero_name, kind="character", type="girl" if random.random() > 0.4 else "boy",
        traits=["little"] + hero_traits,
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                           label={"mother":"mom", "father":"dad", "aunt":"aunt"}.get(parent_type,"parent"))
    prize = world.add(Entity(
        id="prize", type="shirt", label="favorite shirt",
        phrase="a yellow shirt with tiny stars",
        plural=False, owner=hero.id, caretaker=parent.id,
    ))

    # Act 1 — casual joy of spinning world
    introduce(world, hero)
    loves_spinning(world, hero)
    world.para()
    arrives_spot(world, hero, parent)

    # Act 2 — giddy desires vs. warning of trouble
    world.para()
    feels_giddy(world, hero, parent)
    hero.memes["love_spin"] = 1.2
    spin_aimless(world, hero, Activity(id="spin", verb="spin around", gerund="spinning around",
                                      rush="spin faster", mess="dirty", soil="a bit sweaty",
                                      zone=set(), keyword="spinning", tags={"giddy","dizzy"}))

    # Spot risk
    world.para()
    warns_about_dizziness(world, parent, hero)

    # Struggle
    world.para()
    tries_to_grab(world, hero, parent)
    pouts_small(world, hero)

    # Act 3 — twist: embrace the giddy safely together
    world.para()
    safer_spin_together(world, parent, hero,
                       Activity(id="safe_spin", verb="spin together", gerund="spinning together",
                                rush="spin slowly", mess="", soil="", zone=set(),
                                keyword="safe spinning", tags={"giddy","teamwork","twist"}))
    happier_together(world, hero, parent)

    world.facts.update(hero=hero, parent=parent, prize=prize,
                      giddy_peak=world.facts.get("dizzy_peak",0.0),
                      resolved_spinning=world.facts.get("resolved_spinning",False))
    return world

SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False,
                       affords={"spin"}),
    "park": Setting(place="the park", indoor=False,
                   affords={"spin"}),
    "clearing": Setting(place="the sunny clearing", indoor=False,
                       affords={"spin"}),
    "playroom": Setting(place="the playroom", indoor=True,
                       affords={"spin"}),
}

ACTIVITIES = {
    "spin": Activity(
        id="spin", verb="spin in circles",
        gerund="dancing in circles",
        rush="spin faster around",
        mess="sweaty",
        soil="a bit sweaty",
        zone=set(),
        keyword="spinning",
        tags={"dizzy","giddy","circle","exercise"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a yellow shirt with tiny stars",
                  type="shirt", region="torso"),
    "dress": Prize(label="sun-dress", phrase="a bright yellow sun-dress",
                  type="dress", region="torso",
                  genders={"girl"}),
    "socks": Prize(label="socks", phrase="bright yellow socks",
                  type="socks", plural=True),
}

GIRL_NAMES = ["Lily","Mia","Zoe","Ava","Ella"]
BOY_NAMES = ["Leo","Theo","Noah","Finn","Eli"]
TRAITS = ["daring","playful","breezy","light","sunny"]

def valid_combos() -> list[tuple[str,str,str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if {"giddy"} & ACTIVITIES[act_id].tags:
                    combos.append((place, act_id, prize_id))
    return combos[:max(3, int(len(valid_combos())*.7))]

KNOWLEDGE = {
    "giddy": [("What does 'giddy' mean when a child feels giddy?",
               "When someone feels giddy, it usually means they feel light-headed and "
               "happy, often from spinning around or being very excited.")],
    "spinning": [("Why does spinning make you dizzy?",
                  "Spinning makes you dizzy because the fluid in your ears that helps you "
                  "balance gets stirred up, so your brain gets mixed signals for a moment.")],
    "dizzy": [("Why can too much spinning be uncomfortable?",
               "Too much spinning churns the fluid in your ears — when that happens quickly "
               "your body and eyes send different balance messages, so you feel unsteady "
               "and sick to your tummy.")],
    "laugh": [("When do children laugh the most?",
               "Children laugh the most when they feel safe and loving, during shared "
               "play activities with people they trust.")],
}

KNOWLEDGE_ORDER = ["giddy","spinning","dizzy","laugh"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    kw = world.setting.place
    return [
        f'Write a heartwarming 3-to-5-year-old story about "{kw}" and feeling "giddy". '
        f'Include the words "spin" and "twist" naturally.',
        f'Tell a gentle tale where a child tries spinning until the world spins back '
        f'at them, and a caregiver helps them find the quiet joy in the giddy.',
        f"A short story for little kids about the thrill of spinning, the '
        f'caution of dizziness, and the twist of learning to spin safely together.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    pw = parent.label_word
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    pos = hero.pronoun("possessive")
    place = world.setting.place

    qa = [
        QAItem(
            question=f"Who wanted to spin in circles until the world tipped in {place}?",
            answer=f"It was {hero.id}, a little {hero.traits[0]} {hero.type}, "
                   f"who loved the feeling of spinning until things seemed to whirl.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {pw} teach about spinning too fast?",
            answer=f"{pw.capitalize()} showed how spinning can feel like flying when "
                   f"done slowly with steady hands, so the giddy stays sweet and safe.",
        ),
    ]
    if f.get("dizzy_peak", 0.0) > THRESHOLD:
        qa.append(QAItem(
            question=f"Why did {pw} warn {hero.id} about spinning too much?",
            answer=(
                f'{pw.capitalize()} knew spinning until too dizzy would make {hero.id} feel '
                f'wobbly, so {pos} {pw} stepped close and said "A dance has partners" '
                f'to slow the spin down.'
            ),
        ))
    if f.get("resolved_spinning", False):
        qa.append(QAItem(
            question=f"How did {hero.id} feel spinning with {pw} afterward?",
            answer=(
                f'{hero.id} felt happier and safer. Together they spun gently, with '
                f'{pos} {pw} steadying {hero.pronoun("object")}, so the joy stayed '
                f'cheerful and the wobble stayed away.'
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"spin","dizzy","giddy"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q,a) for q,a in KNOWLEDGE[tag])
    return out

try:
    import asp
    ASP_RULES = r"""
    % A story is valid when the activity tags include 'giddy' and the place affords it
    valid_story(Place, A, P) :- affords(Place,A), has_tag(A,"giddy"), prize(P).
    """
except ImportError:
    ASP_RULES = ""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
            aid = "spin"
            if a == aid:
                for tag in ["dizzy","giddy","circle","exercise"]:
                    lines.append(asp.fact("has_tag", aid, tag))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    if not ASP_RULES.strip():
        return ""
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: ASP gate matches Python ({len(clingo_set)} heartwarming tales).")
        return 0
    print("MISMATCH between ASP and Python valid sets:")
    if clingo_set - py_set: print("  clingo-only:", sorted(clingo_set - py_set))
    if py_set - clingo_set: print("  Python-only:", sorted(py_set - clingo_set))
    return 1

@dataclass
class StoryParams:
    place: str
    name: str
    parent: str
    trait: str
    activity: str = "spin"
    prize: str = "shirt"
    gender: str = "girl"
    seed: Optional[int] = None

CURATED = [
    StoryParams(place="backyard", name="Lily", parent="mother", trait="daring"),
    StoryParams(place="park", name="Leo", parent="father", trait="breezy"),
    StoryParams(place="clearing", name="Mia", parent="aunt", trait="sunny"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming tales of giddy twists: "
                        "spinning safely, with parent love and quiet joy.")
    ap.add_argument("--place", choices=SETTINGS, default="backyard")
    ap.add_argument("--name", type=str, default=None)
    ap.add_argument("--gender", choices=["girl","boy"], default=None)
    ap.add_argument("--parent", choices=["mother","father","aunt","uncle"], default=None)
    ap.add_argument("--trait", choices=TRAITS, default=None)
    ap.add_argument("-n", type=int, default=1, help="number of heartwarming stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="show curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="show Q&A pairs")
    ap.add_argument("--json", action="store_true", help="print JSON instead")
    ap.add_argument("--asp", action="store_true", help="list valid ASP tales")
    ap.add_argument("--verify", action="store_true", help="check ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="show ASP rules")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity != "spin":
        raise StoryError("Only the 'spin' activity is available in this heartwarming giddy world.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError(f"Only prizes: {', '.join(PRIZES)}")
    if args.gender and args.gender == "girl" and args.prize == "socks":
        pass
    elif args.gender and args.gender == "boy" and args.prize in {"dress","shirt"}:
        raise StoryError(f"A {args.prize} isn't typical boys' clothes here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0]==args.place)]
    if not combos:
        raise StoryError("(No heartwarming tale found for current settings.)")
    place, _, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender_pool = prize.genders.copy()
    gender = args.gender or rng.choice(sorted(gender_pool))
    name = args.name or rng.choice(GIRL_NAMES if gender=="girl" else BOY_NAMES)
    parent = args.parent or rng.choice(sorted(["mother","father","aunt","uncle"]))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place, name=name, parent=parent, trait=trait,
        activity="spin", prize=prize_id, gender=gender,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, [params.trait], params.parent)
    for e in world.entities.values():
        e.meters["dizzy"] = max(0.0, min(4.0, e.meters.get("dizzy",0.0)))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- heartwarming world state ---"]
    for e in world.entities.values():
        meters = {k: f"{v:.2f}" for k,v in e.meters.items() if v}
        memes = {k: f"{v:.2f}" for k,v in e.memes.items() if v}
        bits = []
        if meters: bits.append(f"meters={meters}")
        if memes: bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    lines.append(f"rules fired: {len(world.fired)}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world: print(dump_trace(sample.world))
    if qa: print("\n" + "\n\n".join(str(q) for q in sample.story_qa).strip())
    if qa and sample.world_qa:
        print("\n--- world knowledge for 3-to-5-year-olds ---")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        tales = asp_valid_stories()
        print(f"{len(tales)} heartwarming tales endorsed by clingo ASP.\n")
        for t in tales:
            print(f"  • {t[0]:12} {t[1]} with {t[2]}")
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    stories: list[StorySample] = []
    if args.all:
        stories = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(stories) < args.n and i < max(args.n*50,50):
            try:
                params = resolve_params(args, random.Random(base + i))
                sample = generate(params)
                if sample.story in seen:
                    i += 1
                    continue
                seen.add(sample.story)
                stories.append(sample)
            except StoryError as err:
                print(err)
                return
            i += 1
    if args.json:
        print(json.dumps([s.to_dict() for s in stories], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(stories):
        hdr = ""
        if args.all or len(stories)>1:
            hdr = f"### {s.params.name} in {s.params.place} — the {s.params.trait} twist"
        emit(s, trace=args.trace and s.world is not None, qa=args.qa, header=hdr)
        if i < len(stories)-1: print("\n" + "="*70 + "\n")
if __name__ == "__main__":
    main()
