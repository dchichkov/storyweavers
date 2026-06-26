#!/usr/bin/env python3
"""
One self-contained worlds/ script: classic simulation of the
"Coffin in the Parking Lot" Adventure with Friendship,
Transformation, and Suspense.
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
from storyworlds.results import QAItem, StoryError, StorySample

# Child-friendly thresholds for narrating changes
THRESHOLD = 1.0

# Physical meter keys that count toward risk of damage
RISK_KINDS = {"brittle", "heavy", "sensitive"}
PROTECT_KINDS = {"safe", "padded"}
REGIONS = {"feet", "legs", "torso", "head"}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "tool"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "sister", "mom"}
        male = {"boy", "brother", "dad"}
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
    place: str = "the parking lot"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    gear_required: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})

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
        return any(g.covers and region in g.covers for g in self.worn_items(actor))

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

def _r_stress(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for risk in RISK_KINDS:
            if actor.memes[risk] >= THRESHOLD and actor.memes["fear"] < THRESHOLD:
                sig = ("stress", actor.id, risk)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f"{actor.pronoun().capitalize()} felt a little worried.")
    return out

def _r_friendship_up(world: World) -> list[str]:
    chars = world.characters()
    if len(chars) < 2:
        return []
    sig = ("friend_up", chars[0].id, chars[1].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return ["Together they turned the adventure into a memory they would always share."]

CAUSAL_RULES: list[Rule] = [
    Rule(name="stress", tag="emotion", apply=_r_stress),
    Rule(name="friend_up", tag="social", apply=_r_friendship_up),
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

def wants_adventure(world: World, actor: Entity, activity: Activity) -> None:
    actor.memes["excitement"] += 1.4
    actor.memes["adventure_love"] += 1.0
    world.say(
        f"{actor.pronoun('subject').capitalize()} loved adventures like this. "
        f"{activity.gerund} was calling {actor.pronoun('object')}."
    )

def finds_coffin(world: World, hero: Entity, dest: Entity) -> None:
    hero.memes["curiosity"] += 1.2
    hero.memes["wonder"] += 0.8
    world.say(f"{hero.id} spotted {dest.phrase} half-hidden in the shadows.")
    hero.memes["conflict"] += 0.5

def warns_safety(world: World, parent: Entity, hero: Entity,
                prize: Entity, gear_sigil: str) -> bool:
    fragility = prize.meters.get("brittle", 0) * 3.0
    if prize.meters.get("precious", 0) >= 1.0:
        fragility += 2.0
    if fragility >= THRESHOLD:
        clause = (
            f"If you move {prize.label} carelessly, "
            f"you might break {hero.pronoun('object')}—"
            f"then you'll both be in trouble."
        )
        world.say(f'"{clause}" {parent.pronoun("possessive")} {parent.label_word} warned.')
        world.facts["predicted_damage"] = prize.label
        world.facts["predicted_risk"] = round(fragility, 1)
        return True
    return False

def grabs_hand(world: World, parent: Entity, hero: Entity) -> None:
    world.say(
        f"{parent.label_word} reached out and gently caught {hero.pronoun('object')} hand. "
        f'"Let\'s go a little slower," {parent.pronoun("subject")} said.'
    )

def builds_tool(world: World, parent: Entity, gear_def: Gear) -> Entity:
    tool = world.add(Entity(
        id=gear_def.id,
        type="tool",
        label=gear_def.label,
        phrase=f"{gear_def.label}",
        region="belt"  # carried
    ))
    return tool

def uses_tool(world: World, parent: Entity, hero: Entity,
               tool: Entity, prize: Entity) -> None:
    world.say(
        f"{parent.label_word} began to use the {tool.label} cautiously to "
        f"open the {prize.label}."
    )
    world.say(
        f"Carefully, carefully. Soon the {prize.label} gave way without a mark."
    )

def transforms_friendship(world: World, parent: Entity, hero: Entity) -> None:
    for ch in (parent, hero):
        ch.memes["friendship"] += 1.5
    world.say(
        f"Surprise lit up {parent.it()} face and {hero.it()} face alike. "
        "A grin spread between them—this hands-in moment meant more "
        "than any shiny thing ever could."
    )
    world.facts["transformed"] = True

def pick_friends(names: list[str]) -> tuple[str, str]:
    if len(names) >= 2:
        return random.sample(names, 2)
    return names[0], names[1] if names else ("Alex", "Jamie")

SETTINGS = {
    "parking_lot": Setting(
        place="an empty parking lot beside the big-box store",
        indoor=False,
        affords={"investigate_coffin", "tinker_tools"}
    ),
}

ACTIVITIES = {
    "investigate_coffin": Activity(
        id="investigate_coffin",
        verb="open the old coffin",
        gerund="opening the old coffin",
        rush="grab the handles and pull hard",
        risk="brittle",
        gear_required="safe_tool",
        zone={"torso"},
        keyword="coffin",
        tags={"adventure", "friendship", "caution"}
    ),
}

PRIZES = {
    "skateboard": Prize(
        label="new skateboard",
        phrase=" shiny new skateboard lying nearby",
        type="skateboard",
        region="feet",
        plural=False,
    ),
    "phone": Prize(
        label="phone",
        phrase="fancy new phone left on the car seat",
        type="phone",
        region="torso",
        plural=False,
    ),
    "cap": Prize(
        label="baseball cap",
        phrase=" favorite baseball cap carelessly tossed on the dash",
        type="cap",
        region="head",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="thick work gloves",
        covers=set(),
        guards={"safe"},
        prep="pick up the thick work gloves",
        tail="slipped on the thick work gloves",
    ),
    Gear(
        id="toolkit",
        label="small toolkit",
        covers=set(),
        guards={"padded", "safe"},
        prep="grab the small toolkit",
        tail="opened the small toolkit together",
    ),
    Gear(
        id="kitbag",
        label="adventure kit",
        covers={"torso"},
        guards={"safe", "padded", "precious"},
        prep="unzip the adventure kit",
        tail="took out the adventure kit",
    ),
]

FRIENDS = ["Alex", "Jamie", "Taylor", "Riley", "Casey"]
TRAITS = ["adventurous", "thoughtful", "brave", "loyal"]

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    friend_a: str
    friend_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Compose a gentle adventure story for ages 4–6 about two friends '
        'who find something surprising in a parking lot and handle it wisely.',
        "Write a child-facing tale where friendship feels warmer than any broken object.",
        f'Use the word "coffin" and keep the setting very close to "{world.setting.place}".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1 = world.get("HeroOne")
    h2 = world.get("HeroTwo")
    prize = world.get("prize") if "prize" in world.entities else None
    subj1 = h1.pronoun("subject") if h1 else "They"
    subj2 = h2.pronoun("subject") if h2 else "They"
    obj1 = h1.pronoun("object") if h1 else "them"
    pos1 = h1.pronoun("possessive") if h1 else "their"
    pos2 = h2.pronoun("possessive") if h2 else "their"
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who found the {world.entities['coffin'].label} in "
                f"{world.setting.place}?"
            ),
            answer=(
                f"{subj1.capitalize()} and {pos2} friend {h2.id} "
                "had just settled into some quiet exploring when a shadow "
                "caught their eye."
            ),
        ),
        QAItem(
            question=f"Why were {subj1} and {h2.id} careful while {pos1} adventure unfolded?",
            answer=(
                "Because a careless move could have broken the phone left "
                "on the car seat nearby—they knew phones can break."
            ),
        ),
    ]
    if f.get("transformed"):
        qa.append(QAItem(
            question="How did the adventure change the way the friends felt?",
            answer=(
                "The whole hands-in moment made their friendship feel warmer "
                "and safer than any fancy broken thing ever could."
            ),
        ))
    return qa

KNOWLEDGE = {
    "coffin": [
        ("What is a coffin?",
         "A coffin is a box used to hold a person who has died. "
         "Sometimes old ones are found in surprising places."),
        ("Can you open a coffin?",
         "You should not open old coffins by yourself. "
         "It is better to ask a grown-up or a community helper."),
    ],
    "parking_lot": [
        ("What is a parking lot?",
         "A parking lot is a paved area where people leave their cars. "
         "It can look empty when many cars are away."),
        ("What might you find in a parking lot?",
         "You might find a lost cap or a stray skateboard, but also "
         "surprises when it is quiet."),
    ],
    "friendship": [
        ("What does friendship feel like?",
         "Friendship feels like a happy glow when friends share the fun "
         "and share the caution, too."),
        ("How do friends help each other?",
         "Friends help by looking out for one another and choosing "
         "together instead of rushing ahead alone."),
    ],
    "toolkit": [
        ("What is in a toolkit?",
         "A toolkit can hold small tools like screwdrivers, a hammer, "
         "or gloves that help you open things carefully."),
        ("Why use a toolkit?",
         "A small toolkit helps you open packages and boxes without "
         "hurting yourself or breaking what’s inside."),
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts.get("tags", {"coffin", "parking_lot", "friendship", "toolkit"})
    out: list[QAItem] = []
    for tag in ["coffin", "parking_lot", "friendship", "toolkit"]:
        if tag in tags:
            for q, a in KNOWLEDGE.get(tag, []):
                out.append(QAItem(question=q, answer=a))
    return out

def format_qa(sample: StorySample) -> str:
    lines = [
        "== (1) Generation prompts used to write this story ==",
        *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)),
        "",
        "== (2) Questions grounded in the story text ==",
        *(f"Q: {q}\nA: {a}" for q, a in sample.story_qa),
        "",
        "== (3) Child-level world knowledge questions ==",
        *(f"Q: {q}\nA: {a}" for q, a in sample.world_qa),
    ]
    return "\n".join(lines)

def tell(setting: Setting, activity_id: str, prize_cfg: Prize,
         friend_a: str, friend_b: str) -> World:
    world = World(setting)
    hero_a = world.add(Entity(
        id=friend_a,
        kind="character",
        type="child",
        label=friend_a,
        traits=["adventurous"],
    ))
    hero_b = world.add(Entity(
        id=friend_b,
        kind="character",
        type="child",
        label=friend_b,
        traits=["thoughtful"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
    ))
    coffin = world.add(Entity(
        id="coffin",
        kind="thing",
        type="coffin",
        label="old wooden coffin swathed in cobwebs",
        phrase="old wooden coffin swathed in cobwebs half-hidden in the corner",
        region="ground",
        meters={"brittle": 1.8, "ancient": 2.6},
    ))

    world.paragraphs = [[]]

    wants_adventure(world, hero_a, ACTIVITIES[activity_id])
    world.para()

    finds_coffin(world, hero_a, coffin)
    world.say(f'{hero_b.id} tilted {hero_b.pronoun("possessive")} head. '
              '"An adventure calls," {hero_b.pronoun("subject")} echoed.')
    world.facts["tags"] = {"adventure", "coffin"}

    world.para()
    warns_safety(world, hero_b, hero_a, prize, activity_id)
    grabs_hand(world, hero_b, hero_a)

    world.para()
    world.say(f"{hero_a.id} pouted, then thought better of it.")
    world.say(f'{hero_b.id} nodded. "Let\'s use our tools."')

    gear_choice = world.add(Entity(
        id="gearkit", type="kit", label="small toolkit", region="belt"
    ))
    uses_tool(world, hero_b, hero_a, gear_choice, prize)
    transforms_friendship(world, hero_b, hero_a)

    world.facts.update(
        hero_a=hero_a, hero_b=hero_b, prize=prize,
        coffin=coffin, tags=set(KNOWLEDGE.keys()), transformed=f.get("transformed", False)
    )
    return world

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure world: two friends, one old coffin, gentle caution, "
                    "and a growing friendship.")
    ap.add_argument("--place", choices=SETTINGS, default="parking_lot")
    ap.add_argument("--activity", choices=ACTIVITIES, default="investigate_coffin")
    ap.add_argument("--prize", choices=PRIZES, default=None)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name_a", default=None)
    ap.add_argument("--name_b", default=None)
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
    if args.place != "parking_lot":
        raise StoryError("(Only parking_lot supported.)")

    if args.activity != "investigate_coffin":
        raise StoryError("(Only investigate_coffin activity supported.)")

    prizes = list(PRIZES)
    prize_choice = args.prize or rng.choice(prizes)

    friends = FRIENDS.copy()
    if args.name_a and args.name_b:
        friends = [args.name_a, args.name_b]
    elif args.name_a and not args.name_b:
        friends[0] = args.name_a
    elif args.name_b and not args.name_a:
        friends[1] = args.name_b
    friend_a, friend_b = pick_friends(friends)

    traits = TRAITS
    trait_a = rng.choice(traits)
    trait_b = rng.choice([t for t in traits if t != trait_a])

    return StoryParams(
        place="parking_lot",
        activity="investigate_coffin",
        prize=prize_choice,
        friend_a=friend_a,
        friend_b=friend_b,
        trait_a=trait_a,
        trait_b=trait_b,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["parking_lot"], params.activity, PRIZES[params.prize],
                 params.friend_a, params.friend_b)
    story = world.render()
    prompts = generation_prompts(world)
    story_qa_set = story_qa(world)
    world_qa_set = world_knowledge_qa(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa_set,
        world_qa=world_qa_set,
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- world ---\n")
        for e in sample.world.entities.values():
            meters = {k:round(v,2) for k,v in e.meters.items() if v>0}
            memes = {k:round(v,2) for k,v in e.memes.items() if v>0}
            line = [f"{e.id}({e.type})"]
            if meters: line.append(f"meters={meters}")
            if memes: line.append(f"memes={memes}")
            print("  " + " ".join(line))
    if qa:
        print("\n" + format_qa(sample))

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid, s.place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid, pr.label))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)

ASP_RULES = r"""
% An adventure is valid when the pair picks gear that mitigates the prize’s risk.
safe_adventure(Place, Act, Prize, G) :- affords(Place, Act),
    prize(Prize, _, Region, _, _, _), zone(Act, Region),
    activity(Risk, Act), prize_has_risk(Prize, Risk),
    gear_guards(G, Guard), guards(Risk, Guard), has_gear(G).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        lines = asp_facts().splitlines()
        for ln in lines:
            if not ln.strip().endswith('.'): return 1
        print("OK: asp_facts packaging validated.")
    except Exception as e:
        print(f"ASP verify failed: {e}")
        return 1
    return 0

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_adventure/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("safe_adventure set defined by ASP.")
        return

    base_seed = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        here = [StoryParams(
            place="parking_lot",
            activity="investigate_coffin",
            prize="skateboard",
            friend_a="Alex",
            friend_b="Jamie",
            trait_a="adventurous",
            trait_b="thoughtful",
        )]
        samples = [generate(p) for p in here]
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
            header = f"### {p.friend_a} & {p.friend_b}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n"+("="*70)+"\n")

if __name__ == "__main__":
    main()
