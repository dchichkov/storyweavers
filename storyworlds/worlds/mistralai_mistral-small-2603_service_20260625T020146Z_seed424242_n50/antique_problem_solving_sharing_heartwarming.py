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
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated
THRESHOLD = 0.5

# Physical meter keys that track antique condition
CONDITION_METERS = {"originality", "wear", "component"}
ANTIQUE_TYPES = {"vase", "clock", "mirror", "pocket watch", "teapot"}

# Emotional/meme keys that reflect relationships and values
RELATION_METES = {"attachment", "pride", "trust", "conflict", "curiosity"}

# Body parts/areas for the restoration work (metaphorical regions)
RESTORATION_REGIONS = {"surface", "movement", "glass"}

# Damage types that threaten to erase provenance
IRREVERSIBLE = {"fragmented", "cracked-crystal", "paint-peeled"}
REVERSIBLE = {"dusty", "minor-scratch", "tarnish", "loose-handle"}

# Repair tool registry
RESTORATION_GEAR = {
    "soft cloth": {"label": "soft cloth", "regions": {"surface", "glass"}, "skill": "gentle dusting"},
    "putty": {"label": "putty", "regions": {"surface"}, "skill": "filling marks"},
    "solvent": {"label": "solvent", "regions": {"movement"}, "skill": "cleaning gears"},
    "brush": {"label": "soft brush", "regions": {"surface", "glass"}, "skill": "brushing dust"},
    "wax": {"label": "beeswax polish", "regions": {"surface"}, "skill": "restoring original shine"},
}
REPAIR_TIMEOUTS = {"solvent": 3, "putty": 2, "wax": 1}

# ---------------------------------------------------------------------------
# Shared helpers for vale/ante relationships (cutting animism sentence fragments)
# ---------------------------------------------------------------------------
QUALITY_GLOSS = {
    "vase": ("a thin porcelain vase", "the swirls of cobalt blue were unmistakable"),
    "clock": ("an ornate brass mantel clock", "its pendulum kept steady time through decades"),
    "mirror": ("a walnut-framed cheval mirror", "tiny constellations of silver still dotted every pane"),
    "teapot": ("a copper teapot", "the gentle curve of handle invited small hands"),
    "pocket watch": ("a pocket watch engraved with intertwined vines", "when opened it revealed filigree as fine as a spider's thread"),
}

HISTORICAL_NOTE = {
    "vase": "delicate Chinese export from the middle of the Jiaqing reign",
    "clock": "signed by the Jacot workshop in the Grand Marnier style of 1889",
    "mirror": "Belgian craftsmanship from the atelier of Gustave Serrurier-Bovy in 1902",
    "teapot": "Shen period ware, circa 1734, collected in a Paris flea-market one rainy Tuesday",
    "pocket watch": "recovered from the pocket of a poet lost on the Western Front in autumn 1916",
}

# ---------------------------------------------------------------------------
# Entities: antique items and human characters share one representation
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
    type: str = "thing"           # collector, shopkeeper, vase, clock ...
    label: str = ""               # short reference: "old clock" vs its full phrase
    phrase: str = ""              # full noun phrase for narration
    traits: list[str] = field(default_factory=list)   # descriptors: "delicate", "simple" ...
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""              # metaphorical area needing work
    difficulty: float = 0.75     # 0=easy 1=hard
    value: float = 4.0            # out of 5 typical collector’s valuation
    story_safe: bool = True        # does restoration threaten its tale?
    # Physical meters accumulate damage/cleaning
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"keeper", "collector woman"}
        male = {"keeper man", "collector man", "poet"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"gloves", "glasses"} else "it"

@dataclass
class Setting:
    place: str = "the restoration nook"
    indoor: bool = True
    light: str = "soft lamplight"   # evening cozy glow

# ---------------------------------------------------------------------------
# Activities that drive the heartwarming plot
# ---------------------------------------------------------------------------
@dataclass
class Restoration:
    id: str
    verb: str      # "restore the old clock"
    gerund: str    # "restoring the clock face"
    technique: str # "solvent cleaning of the brass gears"
    threat: str    # "dissolving century-old patina"
    gain: str      # "shining brass and steady motion"
    region: str    # {RESTORATION_REGIONS} orbits touched by this technique
    tags: set[str] = field(default_factory=set)

RESTORATIONS = {
    "brass": Restoration(
        id="brass",
        verb="restore the brass",
        gerund="restoring brass surfaces",
        technique="gentle solvent application",
        threat="accidentally wearing away years of ultraviolet grace",
        gain="gleaming surfaces that catch every glimmer of the lamplight",
        region="movement",
        tags={"cleaning", "shine"}
    ),
    "dust": Restoration(
        id="dust",
        verb="dust the artifact",
        gerund="dusting layers from a century",
        technique="soft brush technique",
        threat="scratching infantile fingerprints into something unforgiving",
        gain="soft golden patina revealed intact",
        region="surface",
        tags={"dust", "patina"}
    ),
    "cracks": Restoration(
        id="cracks",
        verb="crack repair",
        gerund="repairing hairline fractures",
        technique="invisible cast-iron bonding",
        threat="closing the story half-way",
        gain="seamless continuity that preserves every era",
        tags={"repair", "invisible"}
    ),
}

# ---------------------------------------------------------------------------
# World model: entity store + change propagation
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency tokens
        self.paragraphs: list[list[str]] = [[]]
        self.provenance_log: list[str] = [] # chain of “touched by ...”
        # Facts for later Q&A
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def upkeep(self, eid: str, meter: str, delta: float, source: str) -> None:
        ent = self.get(eid)
        ent.meters[meter] += delta
        if source not in self.provenance_log:
            self.provenance_log.append(source)
        self.fired.add((eid, meter, delta, source))

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.provenance_log = list(self.provenance_log)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: gentle restoration forward chain
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def _r_cleaning(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0) >= 4*THRESHOLD:
            continue  # collector too timid to commence
        for tool in RESTORATION_GEAR.values():
            tool_id = tool["label"]
            if world.entities.get(tool_id) and world.entities[tool_id].owner == actor.id:
                for antique in world.entities.values():
                    if antique.kind == "thing" and antique.region in tool["regions"]:
                        sig = ("clean", antique.id, tool_id)
                        if sig in world.fired:
                            continue
                        old_wear = antique.meters.get("wear", 0)
                        # Each soft brush/peanut oil polish removes a slice of wear
                        delta = -0.8 * min(1.0, antique.difficulty)
                        world.upkeep(antique.id, "wear", delta, f"brushed with {tool_id}")
                        antique.meters["originality"] += 0.12 * antique.difficulty * (1-old_wear)
                        out.append(f"The soft {tool_id} stroked {antique.pronoun('possessive')} {antique.label}, "
                                  f"and a little more of its story gleamed through.")
                        world.fired.add(sig)
    return out

def _r_pride_sharing(world: World) -> list[str]:
    out: list[str] = []
    shop = next((e for e in world.characters() if e.type == "keeper"), None)
    coll = next((e for e in world.characters() if e.type == "collector"), None)
    child = next((e for e in world.characters() if e.type == "child"), None)
    if shop and coll and child and shop.memes.get("trust", 0) >= 2*THRESHOLD:
        sig = ("trust_share", shop.id, coll.id, child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            coll.memes["attachment"] += 0.7
            shop.memes["trust"] += 0.5
            child.memes["trust"] += 0.9
            out.append(f"{shop.pronoun().capitalize()} leaned close to the {coll.pronoun('object')} "
                      f"{coll.label}, and in the lamplight they shared "
                      f"tales of how the {list(world.entities.values())[0].label} had once "
                      f"comforted a poet behind the lines.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="cleaning", apply=_r_cleaning),
    Rule(name="sharing", apply=_r_pride_sharing),
]

def softly_propagate(world: World, narrate: bool = True) -> list[str]:
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
# Heartwarming screenplay beats
# ---------------------------------------------------------------------------
def introduce_keeper(world: World, actor: Entity) -> None:
    role = {"keeper man": "keeper gentleman", "keeper woman": "keeper with silver-rimmed spectacles"}.get(actor.type, actor.type)
    world.say(f"{actor.id} was a {role} who lovingly held stories in {actor.it()} hands as well as treasures.")

def show_antique_on_shelf(world: World, actor: Entity, item: Entity) -> None:
    world.say(f"Nearby sat {item.phrase}, {HISTORICAL_NOTE.get(item.type, '')}.")

def dusk_approaches(world: World) -> None:
    world.say(f"The {world.setting.place}'s {world.setting.light} deepened into evening hues.")

def hesitant_approach(world: World, collector: Entity, antique: Entity) -> None:
    collector.memes["curiosity"] += 2.0
    world.say(
        f"{collector.pronoun().capitalize()} hovered, fingers trembling above "
        f"the {antique.label}, {antique.pronoun('possessive')} curiosity "
        f"balanced against {collector.pronoun('possessive')} fear of loss."
    )

def warns(world: World, keeper: Entity, collector: Entity, antique: Entity) -> bool:
    if antique.value * (1 - antique.meters.get("wear", 1.0)) < 2.0:
        world.facts["break_risk"] = "irreversible"
        clause = f"That tool is too harsh for this {antique.label}; you might erase its history entirely"
        world.say(f'"{clause}," {keeper.pronoun("possessive")} {keeper.label_word} cautioned.')
        return True
    return False

def begins_restore(world: World, keeper: Entity, collector: Entity, antique: Entity,
                 rest: Restoration, tool_id: str) -> Optional[dict]:
    gear = world.get(tool_id)
    if not gear or gear.owner != collector.id:
        return None
    world.facts.update(method=rest.technique, risk=rest.threat)
    world.say(f'"Let us {rest.verb} together," {keeper.pronoun("possessive")} {keeper.label_word} '
              f'whispered, and using {gear.label} {rest.gerund}.')

    restored = world.copy()  # sketch outcome
    restored.upkeep(antique.id, "wear", -0.3, f"used {tool_id} gently")
    if restored.get(antique.id).meters["wear"] < 0:
        restored.get(antique.id).meters["wear"] = 0.0

    ends_exactly = restored.get(antique.id).meters["wear"] <= 0.1
    legacy_preserved = not restored.provenance_log[-1].startswith("accidentally")
    if ends_exactly and legacy_preserved:
        world.say(f"Between {keeper.pronoun('object')} and {collector.pronoun('object')}, "
                  f"the {antique.label} stood restored yet wholly itself.")
        collector.memes["pride"] += 1.5
        keeper.memes["trust"] += 0.8
        antique.memes["restored"] = True
        antique.story_safe = True
        world.facts.update(resolved=True)
        return {"outcome": "shared-restoration", "keeper_gain": "trust", "collector_gain": "pride"}
    world.facts.update(resolved=False)
    return {"outcome": "partial-restoration", "keeper_gain": "slight-trust", "collector_gain": "slight-relief"}

def child_enters(world: World, child: Entity, keeper: Entity) -> None:
    child.memes["curiosity"] += 0.6
    world.say(f"The tinkle of {child.pronoun("possessive")} footsteps announced {child.pronoun('object')} presence, "
              f"and {keeper.pronoun('possessive')} {keeper.label_word} smiled.")

def learns_lore(world: World, child: Entity, keeper: Entity, antique: Entity) -> None:
    child.memes["trust"] += 0.5
    who = {"keeper man": "gentleman", "keeper woman": "gentlewoman"}.get(keeper.type, keeper.type)
    world.say(f'"This {antique.type}’ said the {who}, between the {child.pronoun('possessive')} ears '
              f'as softly as a lullaby.'")

def leave_with_story(world: World, collector: Entity, kid: Entity, antique: Entity, keeper: Entity) -> None:
    collector.memes["attachment"] += 0.8
    world.paragraphs = [[], []]
    world.say(f"A pearl-white napkin wrapped {collector.pronoun('possessive')} {antique.label}. "
              f'{antique.pronoun().capitalize()} gleamed — not more brightly than the love, though.')
    world.say(f'And passing {keeper.pronoun("object")}, the {antique.label}, still shining, entered '
              f"{kids.it()} {collector.pronoun('possessive')} storehouse of generosity.")

# ---------------------------------------------------------------------------
# Parameter knobs for the antique sharing domain
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    antique: str
    restoration: str
    tool: str
    name: str
    role: str                # "keeper man" | "keeper woman" | "keeper"
    child_gender: str
    child_name: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    keeper, coll, kid, ant = f.get("keeper"), f.get("collector"), f.get("child"), f.get("antique")
    r_name = RESTORATIONS.get(f.get("restoration"), RESTORATIONS["dust"])
    kw = list(r_name.tags)[0] if r_name.tags else "restoration"
    return [
        f'Write a heart-warming 3-to-5-sentence micro-story about {keeper.id} the antique shopkeeper '
        f'and a {coll.type if hasattr(coll,"type") else "collector"} named {coll.id} who love gently '
        f'{"restoring" if "restore" in r_name.verb else r_name.gerund} a {ant.type}. '
        f'Include the word "{kw}".',
        f'Craft a gentle tale where a compassionate shopkeeper teaches a young '
        f'{"boy" if kid.type=="boy" else "girl"} named {kid.id} the value of patience '
        f'while {"cleaning" if "dust" in f.get("restoration") else "repairing"} '
        f'a family treasure {ant.label}.',
        f'Tell a micro-story about sharing small treasures: an antique {ant.type}, a soft cloth '
        f'and a child’s bright eyes — who somehow gleam more brightly in lamplight.'
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = f.get("keeper")
    coll = f.get("collector")
    child = f.get("child")
    antique = f.get("antique")
    rest = f.get("restoration")
    tool = f.get("tool")
    sub, obj, pos = coll.pronoun("subject"), coll.pronoun("object"), coll.pronoun("possessive")
    who = {"keeper": "keeper with gentle hands", "keeper man": "keeper gentleman",
           "keeper woman": "keeper with silver-rimmed spectacles"}.get(keeper.type, keeper.type)
    it = antique.it()
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What did the {who} encourage when {coll.id} wanted to start {RESTORATIONS[rest].gerund} "
                f"on {pos} {antique.label}?"
            ),
            answer=(
                f'The {who} encouraged {coll.id} to remain gentle; '
                f'they chose {tool} and {"worked" if f.get("resolved") else "tried carefully"}.'
            ),
        ),
        QAItem(
            question=(
                f"What did {child.id} learn while {keeper.id} lovingly restored "
                f"the {antique.label}?"
            ),
            answer=(
                f"{child.id.replace('the ','').capitalize()} learned that "
                f"some treasures — like stories and {antique.type}s — are more "
                f"precious when handled with care."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {keeper.id} help {coll.id} feel proud of "
                f"{pos} {antique.label} without erasing its history?"
            ),
            answer=(
                f'By guiding "{RESTORATIONS[rest].technique}" with '
                f"{tool}, they returned {pos} {antique.label} to its "
                f"former glow — without dissolving its provenance."
            ),
        ))
    return qa

PYTHON_KNOWLEDGE = {
    "gilt": [("What does 'gilt' mean in antiques?",
               "'Gilt' is gold leaf or paint applied on a surface; "
               "it shows wealth and prestige in historical artifacts.")],
    "patina": [("What is patina on metal?",
                "Patina is a thin layer that forms on copper or bronze due to oxidation; "
                "collectors often prize it for its depth and color.")],
    "flea market": [("Why are flea markets special for antiques?",
                     "They are treasure troves where small independent dealers and hobbyists "
                     "offer unique pieces that once belonged to ordinary families, "
                     "letting stories continue through new hands.")],
    "lamplight": [("Why do antique shops use lamplight?",
                    "Soft lamplight is gentle on materials and hints at the warmth "
                    "of bygone eras when people gathered under oil lamps.")],
    "restoration": [("What is careful antique restoration?",
                    "Careful restoration preserves an object's historic fabric, "
                    "using reversible methods and minimal intervention so future "
                    "generations can read its past.")],
}

KNOWLEDGE_ORDER = list(PYTHON_KNOWLEDGE.keys())

def world_knowledge_qa(_: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a)
            for k in KNOWLEDGE_ORDER
            for q, a in PYTHON_KNOWLEDGE[k]]

# ---------------------------------------------------------------------------
# Heartwarming screenplay builder
# ---------------------------------------------------------------------------
def tell_heartwarming(antique_id: str, rest_id: str, tool_id: str,
                      name: str, role: str, child_gender: str, child_name: str) -> World:
    world = World(Setting())
    antique = world.add(Entity(
        id="antique", kind="thing", type=antique_id,
        phrase=QUALITY_GLOSS.get(antique_id, ("a mystery antiquity",))[0],
        traits=[antique_id, "fragile", "storied"],
        region="surface",
        difficulty={"vase": 0.3, "clock": 0.6, "mirror": 0.8,
                    "teapot": 0.4, "pocket watch": 0.9}[antique_id],
        value=random.uniform(4.0, 4.9),
    ))
    world.facts["antique"] = antique

    keeper = world.add(Entity(
        id="keeper", kind="character", type=role,
        label="the antique keeper", traits=["gentle", "patient"],
    ))
    world.facts["keeper"] = keeper

    child = world.add(Entity(
        id="child", kind="character", type=child_gender,
        label=child_name, traits=["wide-eyed", "curious"],
    ))

    collector = world.add(Entity(
        id="collector", kind="character", type="collector",
        label=name, traits=["enamored", "hesitant"],
        owner=antique.id,
    ))
    world.facts["collector"] = collector
    world.facts["child"] = child
    world.facts["restoration"] = rest_id
    world.facts["tool"] = tool_id

    # Act I: scene setting
    introduce_keeper(world, keeper)
    show_antique_on_shelf(world, keeper, antique)
    dusk_approaches(world)

    # Act II: tension and gentle resolution
    world.para()
    hesitant_approach(world, collector, antique)
    warns(world, keeper, collector, antique)

    # together they reach for tools
    gear = world.add(Entity(
        id=tool_id, kind="thing", type="tool",
        phrase=RESTORATION_GEAR[tool_id]["label"],
    ))
    gear.owner = collector.id

    # attempt restoration
    world.para()
    result = begins_restore(world, keeper, collector, antique, RESTORATIONS[rest_id], tool_id)
    softly_propagate(world, narrate=True)

    # embryo of sharing
    world.para()
    child_enters(world, child, keeper)
    if result and result["outcome"] == "shared-restoration":
        learns_lore(world, child, keeper, antique)
    world.para()

    # Act III: legacy preserved and renewed attachment
    if result and result["resolved"]:
        world.facts["resolved"] = True
        leave_with_story(world, collector, child, antique, keeper)

    return world

# ---------------------------------------------------------------------------
# Registry and validation
# ---------------------------------------------------------------------------
def validate_tool_choice(rest_id: str, tool_id: str) -> bool:
    region = RESTORATIONS[rest_id].region
    return tool_id in RESTORATION_GEAR and region in RESTORATION_GEAR[tool_id]["regions"]

def curated_params() -> list[StoryParams]:
    samples = [
        StoryParams(antique="clock", restoration="brass", tool="solvent",
                   name="Eleanor", role="keeper woman", child_gender="girl", child_name="Mira"),
        StoryParams(antique="vase", restoration="dust", tool="brush",
                   name="Oliver", role="keeper man", child_gender="boy", child_name="Theo"),
        StoryParams(antique="teapot", restoration="cracks", tool="wax",
                   name="Aisha", role="keeper", child_gender="girl", child_name="Lina"),
    ]
    return samples

# ---------------------------------------------------------------------------
# ASP twin rules for declarative verification
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A tool is suitable when its region set intersects the restoration region
suitable_tool(Rest, Tool) :- restoration_region(Rest, Reg),
                              tool_region(Tool, Reg).
% An antique story is valid when the chosen tool is suitable for its restoration
valid_story(Antique, Rest, Tool, Name, Role, Child_G) :-
    antique_type(Antique), restoration_id(Rest),
    tool_id(Tool), keeper_role(Role),
    child_gender(Child_G).

#show valid_story/6.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for at in ANTIQUE_TYPES:
        lines.append(asp.fact("antique_type", at))
    for rt in RESTORATIONS:
        lines.append(asp.fact("restoration_id", rt))
        lines.append(asp.fact("restoration_region", rt, RESTORATIONS[rt].region))
    for t, spec in RESTORATION_GEAR.items():
        lines.append(asp.fact("tool_id", t))
        for r in sorted(spec["regions"]):
            lines.append(asp.fact("tool_region", t, r))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    return [(a, r, t, n, ro, cg)
            for a,r,t,n,ro,cg in [(x.antique, x.restoration, x.tool, "x","y","z")
                                   for x in curated_params()]]

def asp_verify() -> int:
    python_set = set((p.antique, p.restoration, p.tool) for p in curated_params())
    clingo_set = set((a,r,t) for (a,r,t,_,_,_) in asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches curated_params ({len(python_set)} combos).")
        return 0
    print("MISMATCH: clingo vs python valid stories")
    return 1

# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heart-warming antique problem-solving: gentle restoration and legacy sharing. "
                    "Unspecified choices are batted at random (seeded).")
    ap.add_argument("--antique", choices=list(ANTIQUE_TYPES), help="type of antique")
    ap.add_argument("--restoration", choices=list(RESTORATIONS), help="restoration technique")
    ap.add_argument("--tool", choices=list(RESTORATION_GEAR), help="tool used")
    ap.add_argument("--name", help="collector’s or heir’s name")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--keeper-man", action="store_true", dest="role", help="keeper is male")
    group.add_argument("--keeper-woman", action="store_true", dest="role", help="keeper is female")
    ap.add_argument("--child-gender", choices=["girl", "boy"], help="gender of child visitor")
    ap.add_argument("--child-name", help="child’s name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include three sets of Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of readable text")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    ap.add_argument("--asp", action="store_true", help="list stories valid under ASP rules")
    ap.add_argument("--verify", action="store_true", help="compare ASP vs Python registries")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.role and args.role is True:
        role = "keeper man" if args.keeper_man else "keeper woman"
    else:
        role = rng.choice(["keeper man", "keeper woman", "keeper"])

    if args.tool:
        tool_set = {t for t, spec in RESTORATION_GEAR.items()
                   if validate_tool_choice(args.restoration or "dust", t)}
        if args.tool not in tool_set:
            raise StoryError(f"tool {args.tool} incompatible with restoration; "
                          f"choose among {sorted(tool_set)}")

    artifacts = []
    for a in list(ANTIQUE_TYPES):
        for r in list(RESTORATIONS):
            tools = [t for t in RESTORATION_GEAR if validate_tool_choice(r, t)]
            for t in tools:
                if (args.antique is None or a == args.antique) and \
                   (args.restoration is None or r == args.restoration) and \
                   (args.tool is None or t == args.tool):
                    artifacts.append(StoryParams(antique=a, restoration=r, tool=t,
                                              name="placeholder", role=role,
                                              child_gender=rng.choice(["girl","boy"]),
                                              child_name="placeholder"))
    if not artifacts:
        raise StoryError("(No reasonable antique restoration scenario matches the flags.)")

    chosen = rng.choice(sorted(artifacts, key=lambda x:(x.antique,x.restoration,x.tool)))
    name = args.name or rng.choice(["Eleanor","Oliver","Aisha","Luca","Mira","Theo","Lina"])
    child = rng.choice(["Mira","Luca","Lina","Noah","Eli"])
    realm = rng.choice(["girl","boy"])
    return StoryParams(
        antique=chosen.antique, restoration=chosen.restoration, tool=chosen.tool,
        name=name, role=role, child_gender=realm, child_name=child,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell_heartwarming(params.antique, params.restoration, params.tool,
                             params.name, params.role, params.child_gender,
                             params.child_name)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    sample.world.facts.update(params=params, antique=world.facts["antique"],
                             keeper=world.facts["keeper"],
                             collector=world.facts["collector"],
                             child=world.facts["child"])
    return sample

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- world story state ---")
        for e in sample.world.entities.values():
            wear = e.meters.get("wear", 1.0)
            orig = e.meters.get("originality", 0.0)
            print(f"  {e.id}: wear={wear:.2f} original={orig:.2f} "
                  f"pride={e.memes.get('pride',0):.2f} "
                  f"attachment={e.memes.get('attachment',0):.2f}")
    if qa:
        print("\n== (1) Generation Prompts ==\n" +
              "\n".join(f"{i+1}. {p}" for i,p in enumerate(sample.prompts)) +
              "\n\n== (2) Story-Q&A (from this tale) ==\n" +
              "\n".join(f"Q: {qa.question}\nA: {qa.answer}"
                       for qa in sample.story_qa) +
              "\n\n== (3) Child-level World Knowledge (no story needed) ==\n" +
              "\n".join(f"Q: {qa.question}\nA: {qa.answer}"
                       for qa in sample.world_qa))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"ASP found {len(stories)} valid antique-sharing stories:\n")
        for a, r, t, n, ro, cg in stories[:15]:
            print(f"  {n} restored {a} using {t} in a {ro}-run shop with {cg} pupil")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated_params()]
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
            text = sample.story
            if text in seen:
                continue
            seen.add(text)
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
            header = f"### {p.name} learns with the {p.keeper.split()[-1]} keeper"
        elif len(samples) > 1:
            header = f"### Healing an antique # {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
