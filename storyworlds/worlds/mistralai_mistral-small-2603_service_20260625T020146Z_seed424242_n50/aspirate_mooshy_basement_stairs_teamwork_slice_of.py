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
from typing import Callable, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys that count as messy byproducts of activity.
MESS_KINDS = {"dusty", "cluttered", "squeaky"}

# Body regions on stairs where splashes/mess can land.
REGIONS = {"top", "middle", "bottom"}

# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "location" | "tool"
    type: str = "thing"            # child, mom, vacuum, stairs, toy ...
    label: str = ""
    phrase: str = ""               # full noun phrase for narration
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None   # who is currently operating the tool
    region: str = ""               # where something sits on stairs
    plural: bool = False           # "stairs" -> them, "vacuum" -> it
    # Two numeric dimensions, treated uniformly.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"mom", "mother", "girl"}
        male = {"child", "boy", "dad", "father", "man"}
        neutral = {"toy", "stairs", "vacuum", "tool"}
        tog = female | male
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mom": "mom", "dad": "dad"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parametrization knobs -- vocabulary of this Slice-of-Life basement domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)   # which activities this place supports

@dataclass
class Activity:
    """What the child wants to do that creates the mess."""
    id: str
    verb: str            # after "wanted to ..."             : "vacuum the basement stairs"
    gerund: str          # after "loved ..."                : "vacuuming the stairs"
    rush: str            # after "tried to ..."              : "grab the vacuum and point it"
    mess: str            # key from MESS_KINDS               : "dusty"
    zone: set[str]       # regions the activity affects      : {"whole"}
    domain_tags: set[str] = field(default_factory=set)  # world-knowledge topics it touches
    keyword: str = ""

@dataclass
class Prize:
    """What the actors value and aim to protect/achieve."""
    label: str
    phrase: str
    region: str          # whole, middle, ...
    plural: bool = False

@dataclass
class TeamworkTactic:
    """How the parent and child combine to resolve the mess."""
    id: str
    label: str
    prep: str            # parent's opening offer phrasing
    tail: str            # closing clause of the compromise
    net_dirt_change: float = -0.8   # delta applied to dirt_level when tactic is used

# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {"teamwork": False, "resolved": False}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values()
                if e.kind == "character" or e.type in {"mom", "dad", "child"}]

    def clean_surfaces(self) -> list[Entity]:
        return [e for e in self.entities.values()
                if e.type == "stairs" and e.meters.get("clean", 0.0) >= THRESHOLD]

    # -- narration helpers --------------------------------------------------
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
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]  # predictions are silent
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_spread_dust(world: World) -> list[str]:
    """Vacuum aspirates mooshy debris but scatters some if technique is poor."""
    vacuum = world.get("vacuum")
    stairs = world.get("stairs")
    child = world.characters()[0]  # the child operating the vacuum
    out: list[str] = []
    if child.memes.get("desire_clean", 0) < THRESHOLD or child.used_by != "vacuum":
        return out
    if stairs.meters.get("dirt_level", 0.0) >= THRESHOLD:
        return out  # already too messy to proceed
    sig = ("vacuum_attempt", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stairs.meters["dirt_level"] += 0.7
    vacuum.meters["squeak_since_clean"] += 1
    out.append(
        f"{child.pronoun('subject').capitalize()} sucked the dust away with a brrr-brrr, "
        f"but a few {world.facts.get('mooshy_debris', 'bits')} floated right back up."
    )
    return out

def _r_teamwork_clean(world: World) -> list[str]:
    """When parent and child work together properly, dirt level drops and confidence rises."""
    stairs = world.get("stairs")
    child = world.characters()[0]
    parent = world.characters()[1] if len(world.characters()) > 1 else None
    out: list[str] = []
    if not world.facts.get("teamwork", False) or stairs.meters.get("dirt_level", 0) >= THRESHOLD:
        return out
    sig = ("teamwork_clean", stairs.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    change = world.facts["tactic"].net_dirt_change
    stairs.meters["dirt_level"] += change
    if stairs.meters["dirt_level"] <= 0.0:
        stairs.meters["clean"] = 1.1
        out.append(
            f"{child.pronoun('subject').capitalize()} wiped the last dust bunny away. "
            "The basement stairs gleamed—clean once more."
        )
        world.facts["resolved"] = True
    else:
        out.append(
            f"Working in unison, they steadily removed a little more of the dusty grime "
            "clinging to each step."
        )
    child.memes["confidence"] = max(0.0, child.memes.get("confidence", 0.5) + 0.4)
    if parent:
        parent.memes["satisfaction"] = min(1.0, parent.memes.get("satisfaction", 0.3) + 0.3)
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_dust", tag="physical", apply=_r_spread_dust),
    Rule(name="teamwork_clean", tag="social", apply=_r_teamwork_clean),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_is_clean(world: World, prize_id: str) -> bool:
    prize = world.get(prize_id)
    return prize.meters.get("clean", 0.0) >= THRESHOLD if prize else False

def teamwork_is_needed(activity: Activity) -> bool:
    return activity.id == "vacuum"

# ---------------------------------------------------------------------------
# Prediction: simulate the messy vacuum attempt to foresee how bad it gets.
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity) -> dict:
    """Simulate vacuuming alone and report expected cleanliness outcome."""
    sim = world.copy()
    if "vacuum" in sim.entities:
        actor.used_by = "vacuum"
        sim.entities[actor.id] = actor
    _r_spread_dust(sim)
    stairs = sim.get("stairs")
    return {"soiled": stairs.meters.get("dirt_level", 0.0) >= THRESHOLD,
            "clean": stairs.meters.get("clean", 0.0) >= THRESHOLD}

# ---------------------------------------------------------------------------
# Verbs: each mutates state and optionally narrates.
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "vacuum": "the vacuum made a friendly bzzzt-bzzzt as it slid over every step",
    }.get(activity.id, "it lit up the basement with cheerful purpose")

def setting_detail(setting: Setting) -> str:
    return (
        "At the bottom of the stairs stood a tiny vacuum, waiting to rumble to life. "
        "Shelves nearby held forgotten toys and danced with swirls of dust."
    )

def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire_clean"] = 0.8
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; "
        f"{activity_delight(activity)}."
    )

def introduce(location: str, hero: Entity) -> str:
    traits = " quiet observant".join(hero.traits) if hero.traits else " curious"
    return (
        f"There lived a {traits} child named {hero.id}. "
        f"Every Saturday this child dreamed of a spotless {location}."
    )

def buys(world: World, parent: Entity, hero: Entity) -> None:
    world.say(
        f"{hero.pronoun('subject').capitalize()} had saved allowance for months "
        f"before {parent.pronoun('possessive')} {parent.label} relented and "
        f"helped purchase the mini vacuum."
    )
    world.facts["vacuum_obtained"] = True

def loves_tool(world: World, hero: Entity, tool: Entity) -> None:
    hero.memes["grip"] = 0.6
    hero.memes["fear_germs"] = 0.4
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} new {tool.label} "
        f"as if it could ward off invisible motes of {world.facts.get('mooshy_debris', 'dust')}."
    )
    tool.used_by = hero.id

def arrives(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        "Late afternoon sunlight streamed through the basement windows. "
        f"{hero.pronoun('subject').capitalize()} bounded down the {world.setting.place}. "
        "Mom stood holding the vacuum’s power cord, giving it one more tug-test."
    )

def wants(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["urgency"] += 0.7
    world.say(
        f"{hero.id} snatched the vacuum handle, eyes sparkling. "
        f'"I can finally banish every {world.facts.get("mooshy_debris", "speck")}!"'
    )

def warn(world: World, parent: Entity, hero: Entity) -> bool:
    """Parent foresees that solo vacuuming will leave residue unless technique is spot-on."""
    pred = predict_mess(world, hero)
    if not pred["soiled"]:
        return False
    world.facts["predicted_dust"] = True
    world.say(
        f'"Hold on," {parent.pronoun("subject")} said, blocking the handle with '
        f'a gentle smile. "Our mini vacuum deserves a partner to aim it just right."'
    )
    return True

def defies(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 0.9
    hero.memes["grip"] += 0.4
    hero.used_by = "vacuum"
    world.say(
        f"{hero.id} ignored the warning and tilted the nozzle downward. "
        "A tiny cloud of dust puffed back up—still dancing in the light."
    )
    propagate(world)

def grab_handle(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] = 1.0
    parent.memes["intervene"] = 0.8
    world.facts["teamwork"] = True
    propagate(world, narrate=False)  # fires the teamwork_clean rule internally
    world.say(
        f'"Let us both hold it," {parent.pronoun("subject")} coached softly, '
        f"sliding a hand onto the handle beside {hero.pronoun('possessive')} own."
    )

def pout(world: World, hero: Entity) -> None:
    if hero.memes.get("confidence", 0.0) < THRESHOLD:
        world.say(
            f"{hero.id} crossed {hero.pronoun('possessive')} arms. "
            '"But I wanted to do it MY way!"'
        )

def compromise(world: World, parent: Entity, hero: Entity,
               tactic: TeamworkTactic) -> bool:
    world.facts["tactic"] = tactic
    world.facts["teamwork"] = True
    world.say(
        f'"First, {tactic.prep}, then we can {world.facts.get("activity").gerund} side-by-side," '
        f"{parent.pronoun('subject')} suggested, 'and together we will succeed.'"
    )
    return True

def finish_clean(world: World, child: Entity, parent: Entity, stairs: Entity) -> None:
    child.memes["joy"] = 1.0
    parent.memes["pride"] = 0.9
    stairs.meters["clean"] = 2.0
    child.memes["confidence"] = min(1.0, child.memes.get("confidence", 0.0) + 0.6)
    world.facts["resolved"] = True
    world.say(
        "With one final pass, the basement stairs—once dull and grizzled—"
        "now gleamed with smooth, unwrinkled carpet. "
        f"{child.pronoun().capitalize()} beamed at {parent.label}, then kicked up a tiny "
        f"cloud of {world.facts.get('mooshy_debris', 'dust')} on purpose, giggling as they watched it drift away."
    )

# ---------------------------------------------------------------------------
# The screenplay (three-act slice-of-life).
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Liam", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mom") -> World:
    world = World(setting)
    world.facts["mooshy_debris"] = "mooshy dust bunnies and lost toys"
    world.facts["activity"] = activity

    child = world.add(Entity(
        id=hero_name, kind="character", type="child",
        traits=["quiet", "observant"] + (hero_traits or ["diligent"]),
        label="Liam" if hero_name == "Liam" else hero_name,
    ))
    parent = world.add(Entity(
        id="Mom", kind="character", type=parent_type, label="Mom",
    ))
    stairs = world.add(Entity(
        id="stairs", kind="location", type="stairs", plural=True,
        phrase="the basement stairs", region="whole",
    ))
    vacuum = world.add(Entity(
        id="vacuum", kind="tool", type="vacuum",
        label="mini vacuum", phrase="our trusty mini vacuum",
    ))

    # Act 1: setup
    world.say(introduce(setting.place, child))
    loves_activity(world, child, activity)
    buys(world, parent, child)
    loves_tool(world, child, vacuum)

    # Act 2: conflict
    world.para()
    arrives(world, child, parent)
    wants(world, child, parent)
    if warn(world, parent, child):
        world.para()
        pout(world, child)
        grab_handle(world, parent, child)
        compromise(world, parent, child, TEAMWORK_TECHNIQUE)
    else:
        world.facts["resolved"] = True  # no conflict needed when prediction is clean

    # Act 3: resolution
    world.para()
    if not world.facts.get("resolved", False):
        finish_clean(world, child, parent, stairs)

    # Record facts for Q&A generators
    world.facts.update(
        child=child, parent=parent, stairs=stairs, vacuum=vacuum,
        start_dirty=stairs.meters.get("dirt_level", 0.0),
        resolved=world.facts.get("resolved", False),
        teamwork=world.facts.get("teamwork", False),
    )
    return world

# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "basement_stairs": Setting(
        place="basement stairs",
        indoor=True,
        affords={"vacuum"},
    ),
}

ACTIVITIES = {
    "vacuum": Activity(
        id="vacuum",
        verb="clean the basement stairs with the vacuum",
        gerund="vacuuming the basement stairs",
        rush="point the vacuum nozzle everywhere at once",
        mess="dusty",
        zone={"whole"},
        domain_tags={"vacuum", "teamwork"},
        keyword="aspirate",
    ),
}

PRIZES = {
    "clean_stairs": Prize(
        label="basement stairs",
        phrase="the gleaming basement stairs",
        region="whole",
        plural=True,
    ),
}

TEAMWORK_TECHNIQUE = TeamworkTactic(
    id="side_by_side",
    label="side-by-side vacuuming",
    prep="stand side-by-side and hold the handle together",
    tail="passed the vacuum back and forth until every crevice shined",
)

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava"]
BOY_NAMES  = ["Liam", "Ben", "Max", "Sam"]

def valid_combos() -> list[tuple]:
    """All constraint-valid (place, activity, prize) triples."""
    return [(p, a, pr) for p in SETTINGS
            for a in SETTINGS[p].affords
            for pr in PRIZES]

# ---------------------------------------------------------------------------
# Q&A generation — three sets.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    """(1) Random ‘asks’ that would produce a story like this."""
    f = world.facts
    act = f["activity"]
    child, parent = f["child"], f["parent"]
    return [
        f'Write a gentle 3-to-5-year-old story titled "Aspirating Mooshy Things" '
        f'about a child trying to clean {act.keyword or act.mess} with {parent.label_word}, '
        'ending in teamwork and a gleaming basement.',
        f'Craft a slice-of-life tale for kids where a {child.type} named {child.id} uses '
        f'a vacuum to remove {world.facts.get("mooshy_debris", "dust")}; '
        f'include the phrase "brrr-brrr" and the word "{act.keyword}".',
        f'For preschoolers: tell how {child.pronoun("subject")} learned that '
        f'teamwork helps clean even {world.facts.get("mooshy_debris", "messes")} '
        f'from {world.setting.place}.',
    ]

def story_qa(world: World) -> list[QAItem]:
    """(2) Story-specific questions."""
    f = world.facts
    child, parent, stairs = f["child"], f["parent"], f["stairs"]
    sub, obj, pos = child.pronoun("subject"), child.pronoun("object"), child.pronoun("possessive")
    act = f["activity"]

    qa: list[QAItem] = [
        QAItem(
            question=f"Who wanted to {act.verb.replace('clean', 'make shine')} {stairs.phrase}?",
            answer=f"It was {child.id}, a {child.traits[0] if child.traits else 'diligent'} child "
                   f"who loved {act.gerund}.",
        ),
        QAItem(
            question=f"What did {child.id} use to suck away the {world.facts.get('mooshy_debris', 'dust')}?",
            answer=f"{child.id} used {pos} new {f['vacuum'].label} "
                   f"with a friendly bzzzt-bzzzt.",
        ),
    ]
    if f.get("teamwork"):
        qa.append(QAItem(
            question=f"How did {child.id} and {parent.label} work together to finish cleaning?",
            answer=f"They held the vacuum handle side-by-side and passed it back and forth "
                   f"until every step gleamed.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What shone at the end of their effort on the {stairs.label}?",
            answer=f"The basement stairs gleamed as if brand-new, "
                   f"now free of every last {world.facts.get('mooshy_debris', 'speck')}.",
        ))
    return qa

KNOWLEDGE = {
    "vacuum": [
        ("What is a vacuum used for?",
         "A vacuum is a cleaning tool that sucks up dust, dirt, and small debris from floors and carpets."),
        ("What sound does a vacuum make?",
         "Most vacuums make a brrr-brrr humming or buzzing noise."),
    ],
    "teamwork": [
        ("Why is it good to work together?",
         "When people work together they can finish tasks faster, share ideas, "
         "and feel happier because they accomplished something together."),
    ],
    "dust": [
        ("What is dust made of?",
         "Dust is often made of tiny bits of skin, fabric, dirt, pollen, and other small things "
         "that float through the air and settle everywhere."),
        ("What are 'dust bunnies'?",
         "Dust bunnies are clumps of dust that collect in corners or under furniture "
         "and look like tiny furry balls rolling around."),
    ],
    "mooshy": [
        ("What does mooshy mean?",
         "'Mooshy' is a playful word meaning soft and squishy, like mud after rain or a "
         "squashed stuffed toy."),
    ],
}
KNOWLEDGE_ORDER = ["vacuum", "teamwork", "dust", "mooshy"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Child-level facts independent of any one story."""
    f = world.facts
    tags = f["activity"].domain_tags | {"mooshy"}
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP (clingo) twin: declarative gate mirroring the Python code.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Basement-stairs vacuuming domain constraints

% Activity outcome: solo vacuuming spreads dust unless technique is shared.
solo_messy :- activity(vacuum), teamwork(false).
clean_result :- activity(vacuum), teamwork(true).

% Prize region must align with activity location.
prize_location_ok :- prize(stairs, whole), activity(vacuum), location(basement_stairs).

valid_story :- location(basement_stairs), activity(vacuum), prize_location_ok.
"""

# Lazy imports for ASP helper
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    # Emit base facts from registries
    lines.append(asp.fact("location", "basement_stairs"))
    lines.append(asp.fact("indoor", "basement_stairs"))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p, PRIZES[p].region))
    lines.append(asp.fact("teamwork", "side_by_side"))
    # World-specific facts
    for _, e in WORLD_REGISTRY.items():
        lines.append(asp.fact("entity", e.id, e.type))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        # The only valid ASP model must confirm basement_stairs+vacuum+stairs as valid
        model = asp.one_model(asp_program("#show valid_story/0."))
        if model:
            print("OK: clingo gate confirms the basement-stairs vacuuming story is valid.")
            return 0
        print("MISMATCH: clingo gate returned no valid models for this domain.")
        return 1
    except ImportError:
        print("Skipping ASP verify (clingo not installed).")
        return 0

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: Optional[str] = None
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-Life basement vacuuming tale: mooshy dust and teamwork.")
    ap.add_argument("--place", choices=SETTINGS, default="basement_stairs")
    ap.add_argument("--activity", choices=ACTIVITIES, default="vacuum")
    ap.add_argument("--prize", choices=PRIZES, default="clean_stairs")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="boy")
    ap.add_argument("--parent", choices=["mom", "dad"], default="mom")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.all:
        place, activity, prize = next(iter(valid_combos()))
    else:
        place = args.place
        activity = args.activity
        prize = args.prize
        gender = args.gender
        name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
        parent = args.parent
        trait = rng.choice(["diligent", "quiet", "observant"]) if args.trait is None else args.trait
    return StoryParams(
        place=place, activity=activity, prize=prize,
        name=name, gender=gender, parent=parent, trait=trait,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, [params.trait] if params.trait else None,
                 "mom" if params.gender == "boy" else params.parent)
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
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            ms = {k: v for k, v in e.meters.items() if v}
            mm = {k: v for k, v in e.memes.items() if v}
            bits = []
            if ms:
                bits.append(f"meters={dict(ms)}")
            if mm:
                bits.append(f"memes={dict(mm)}")
            lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted(set(n for n, *_ in sample.world.fired))}")
        print("\n".join(lines))
    if qa:
        print("\n" + format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show valid_story/0."))
            print("Comptabile stories per ASP gate: 1 (basement_stairs+vacuum+clean_stairs)")
        except ImportError:
            print("clingo not available; no ASP output.")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(resolve_params(args, rng))]
    else:
        seen = set()
        for i in range(args.n):
            params = resolve_params(args, rng)
            if i > 0:  # reset seed for each distinct variant
                params.seed = (args.seed or 0) + i + 1
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = "" if not args.all and len(samples) == 1 else f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
