#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/vicious_piccalilli_extinction_friendship_myth.py
==============================================================================================================================

A standalone story world for the "Friendship That Saved the Piccalilli" tale and 
close, constraint-checked variations of it.

Initial story (used to build a world model):
---
In the time before the Great Thaw, the Piccalilli grew only in the Sunken Grove, 
a place where light fell soft and the soil was sweet as syrup. The Vicious Ones, 
great beasts of ice and claw, had vowed to bring about the Extinction of all 
sweet things. They sent their frost hounds to the Grove, and the Piccalilli 
withered. One small friendship between a mouse named Tallow and a frost hound 
pup named Nix changed the old story: the pup did not bite, and the mouse did 
not run. Together they planted a secret seed in a warm stone hollow, and when 
the frost came, the Piccalilli lived on in that one place.

Causal state updates:
---
    do friendship_act            -> actor.allies += 1
                                   actor.trust += 1
    vicious creature acts        -> victim.terror += victim.defenseless?
                                   + victim's sweet_resource -= 1
    help given across types      -> friendship_bridge ++
    frost spreads                -> region.temperature -= (0 to -5)
                                   if temperature < -2 and no shelter -> sweet_resource -= 1

Scripted social/emotional beats:
---
    danger sensed                -> actor.fear += 1
    small act of shared tending  -> actor.trust += 2 ; actor.hope += 1
    Extinction name spoken       -> actor.terror += 3 if that type is predator else actor.resolve += 2
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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

RESOURCE_KINDS = {"sweet", "warm", "light"}

REGIONS = {"den", "grove", "cave", "hollow"}

BEING_TYPES = {"mouse", "frost_hound", "fox", "vole", "owl", "bear"}

VICIOUS_TAGS = {"frost_hound", "fox", "owl", "bear", "wolf"}

@dataclass
class Entity:
    id: str
    kind: str = "being"           # "being" | "place" | "resource" | "myth"
    type: str = "being"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    allies: list[str] = field(default_factory=list)
    location: str = ""
    is_vicious: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sweet_resource: float = 0.0
    temperature: float = 0.0
    protected: bool = False
    shelter: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        base = {"mouse": "it", "frost_hound": "it", "fox": "it", "vole": "it", "owl": "it", "bear": "it", "wolf": "it"}
        word = base.get(self.type, "it")
        return {"subject": word, "object": word, "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type

    @property
    def is_vicious_by_type(self) -> bool:
        return self.type in VICIOUS_TAGS


@dataclass
class Setting:
    place: str = "the Sunken Grove"
    temperature: float = 0.0
    sweet_resources: float = 3.0
    sacred: bool = False
    hidden: bool = False
    affords: set[str] = field(default_factory=lambda: {"hide", "plant", "frost_watch", "friendship_pact"})


@dataclass
class FriendshipAct:
    id: str
    verb: str
    gerund: str
    action_phrase: str
    resource: str
    danger_reduced: float = 0.5
    trust_gain: float = 1.5
    hope_gain: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class ViciousAct:
    id: str
    verb: str
    gerund: str
    harm: str
    terror_gain: float = 2.0
    resource_loss: float = 1.0
    weather: str = "frost"
    tags: set[str] = field(default_factory=set)


@dataclass
class SacredResource:
    label: str
    phrase: str
    type: str = "piccalilli"
    region: str = "grove"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"all"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "frost"
        self.frost_level: float = 0.0
        self.extinction_threat: bool = True
        self.friendship_bridge: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def beings(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "being"]

    def vicious(self) -> list[Entity]:
        return [e for e in self.beings() if e.is_vicious or e.is_vicious_by_type]

    def gentle(self) -> list[Entity]:
        return [e for e in self.beings() if not (e.is_vicious or e.is_vicious_by_type)]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> World:
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.frost_level = self.frost_level
        clone.extinction_threat = self.extinction_threat
        clone.friendship_bridge = self.friendship_bridge
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_frost_spread(world: World) -> list[str]:
    out = []
    for being in world.beings():
        if world.weather == "frost" and world.frost_level > 0:
            being.temperature -= 0.5 * world.frost_level
            if being.temperature < -2.0 and not being.protected and being.shelter is None:
                being.sweet_resource -= 0.3
                sig = ("frost_damage", being.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f"The frost crept closer, and {being.label if being.label else being.id} shivered.")
    return out


def _r_vicious_harm(world: World) -> list[str]:
    out = []
    for vicious in world.vicious():
        if vicious.memes["active_hunt"] < 0.5:
            continue
        for gentle in world.gentle():
            if gentle.location == vicious.location or (not gentle.location and not vicious.location):
                if gentle.sweet_resource > 0:
                    gentle.sweet_resource -= 0.5
                    gentle.memes["terror"] += 1.0
                    sig = ("vicious_harm", vicious.id, gentle.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        out.append(f"{vicious.label if vicious.label else vicious.id} snarled, and the sweet thing nearby trembled.")
    return out


def _r_friendship_bridges(world: World) -> list[str]:
    out = []
    for being in world.beings():
        if being.memes["allies"] >= 1 and being.is_vicious_by_type:
            world.friendship_bridge += 0.5
            sig = ("bridge", being.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("A strange kindness passed between the one with claws and the one without.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="frost_spread", tag="physical", apply=_r_frost_spread),
    Rule(name="vicious_harm", tag="physical", apply=_r_vicious_harm),
    Rule(name="friendship_bridges", tag="social", apply=_r_friendship_bridges),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


FRIENDSHIP_ACTS = {
    "seed_plant": FriendshipAct(
        id="seed_plant",
        verb="plant a seed",
        gerund="planting seeds",
        action_phrase="pressed the tiny seed into the warm earth",
        resource="sweet",
        trust_gain=2.0,
        hope_gain=1.5,
        tags={"plant", "hope"},
    ),
    "warm_share": FriendshipAct(
        id="warm_share",
        verb="share warmth",
        gerund="sharing warmth",
        action_phrase="curled together in the hollow, sharing their small heat",
        resource="warm",
        trust_gain=1.5,
        hope_gain=1.0,
        tags={"warm", "trust"},
    ),
    "vigil_keep": FriendshipAct(
        id="vigil_keep",
        verb="keep watch",
        gerund="keeping watch together",
        action_phrase="sat side by side, watching the frost's slow approach",
        resource="light",
        trust_gain=1.0,
        hope_gain=2.0,
        tags={"vigil", "courage"},
    ),
}

VICIOUS_ACTS = {
    "frost_send": ViciousAct(
        id="frost_send",
        verb="send the frost",
        gerund="sending frost",
        harm="bitter cold",
        terror_gain=2.5,
        resource_loss=1.5,
        tags={"frost", "extinction"},
    ),
    "howl_threat": ViciousAct(
        id="howl_threat",
        verb="howl the threat",
        gerund="howling threats",
        harm="the sound of ending",
        terror_gain=2.0,
        resource_loss=0.5,
        tags={"fear", "extinction"},
    ),
    "shadow_stalk": ViciousAct(
        id="shadow_stalk",
        verb="stalk the grove",
        gerund="stalking the grove",
        harm="a creeping dread",
        terror_gain=1.5,
        resource_loss=1.0,
        tags={"shadow", "fear"},
    ),
}

SACRED_RESOURCES = {
    "piccalilli": SacredResource(
        label="piccalilli",
        phrase="a sweet, golden fruit that tasted like sunshine and nectar",
        type="piccalilli",
        region="grove",
    ),
    "warm_spring": SacredResource(
        label="warm spring",
        phrase="a pool of water that never froze, fed by the heart of the earth",
        type="warm_spring",
        region="cave",
    ),
    "light_lichen": SacredResource(
        label="light lichen",
        phrase="a soft, glowing moss that gave off a gentle warmth",
        type="lichen",
        region="hollow",
    ),
}

SETTINGS = {
    "sunken_grove": Setting(place="the Sunken Grove", temperature=0.0, sweet_resources=3.0, sacred=True, hidden=False,
                            affords={"seed_plant", "frost_watch", "friendship_pact"}),
    "frost_cave": Setting(place="the Frost Cave", temperature=-1.0, sweet_resources=1.0, sacred=False, hidden=True,
                          affords={"warm_share", "hide", "friendship_pact"}),
    "hollow_mound": Setting(place="the Hollow Mound", temperature=0.5, sweet_resources=2.0, sacred=True, hidden=True,
                            affords={"seed_plant", "vigil_keep", "friendship_pact"}),
    "whisper_valley": Setting(place="Whisper Valley", temperature=0.0, sweet_resources=2.0, sacred=False, hidden=False,
                              affords={"seed_plant", "warm_share", "vigil_keep", "frost_watch", "friendship_pact"}),
}

SETTING_DETAILS = {
    "the Sunken Grove": "Light fell soft through the canopy, and the earth smelled of sweet syrup.",
    "the Frost Cave": "Icicles hung like teeth, and a deep cold breathed from the walls.",
    "the Hollow Mound": "A low hill with a secret pocket of warmth, where the wind could not find you.",
    "Whisper Valley": "The valley floor was wide and open, and the wind carried every sound.",
}

SETTING_INTRODUCTION = {
    "the Sunken Grove": "In the time before the Great Thaw, the Piccalilli grew only in the Sunken Grove.",
    "the Frost Cave": "Deep in the mountains, the Frost Cave held secrets no gentle creature dared to touch.",
    "the Hollow Mound": "Between the roots of the Old Willow, the Hollow Mound stayed warm when all else froze.",
    "Whisper Valley": "Whisper Valley stretched wide beneath the pale sky, and the frost hounds hunted there.",
}

BEING_TRAITS = ["small", "wise", "brave", "gentle", "foolish", "silent", "kind", "fierce-heart", "sly", "faithful"]

GENTLE_NAMES = ["Tallow", "Pip", "Moss", "Willow", "Ember", "Dew", "Clover", "Thistle", "Spindle", "Hazel"]
VICIOUS_NAMES = ["Nix", "Grim", "Frostfang", "Iceclaw", "Snowmane", "Winterhowl", "Blighttooth", "Shardwing"]

MINOR_GENTLE_NAMES = ["Button", "Twig", "Flax", "Rue", "Pepper", "Linden", "Bramble", "Cinder"]
MINOR_VICIOUS_NAMES = ["Sliver", "Snap", "Grimble", "Rime"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            if act_id in {"seed_plant", "warm_share", "vigil_keep"}:
                for resource_id, resource in SACRED_RESOURCES.items():
                    if resource.region in setting.place or resource.region == "grove":
                        combos.append((place, act_id, resource_id))
    return combos


@dataclass
class StoryParams:
    place: str
    friendship_act: str
    resource: str
    gentle_name: str
    vicious_name: str
    gentle_trait: str
    vicious_trait: str
    minor_gentle_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "piccalilli": [("What is a Piccalilli?", "A Piccalilli is a sweet, golden fruit that tastes of sunshine and nectar. It is very rare and precious.")],
    "frost": [("What is the frost?", "The frost is a bitter cold that spreads from the lair of the Vicious Ones. It can kill sweet things if they have no shelter.")],
    "extinction": [("What does 'extinction' mean?", "Extinction means that something goes away forever and never comes back. The Vicious Ones wanted to make all sweet things extinct.")],
    "vicious": [("Who are the Vicious Ones?", "The Vicious Ones are great beasts of ice and claw that hate sweet things. They send frost and fear into the world.")],
    "friendship": [("How can a friendship help?", "Friendship can cross any boundary. When a gentle creature and a vicious one share a small kindness, the old rules change.")],
    "hollow": [("What is a warm hollow?", "A warm hollow is a small, hidden place where the frost cannot reach. It is a good home for a seed.")],
    "seed": [("What can a seed do?", "A seed holds the hope of a new plant. If you hide it in a safe place, it can grow even when the world is cold.")],
    "mouse": [("What is a mouse like?", "A mouse is small and quick, with soft fur and a gentle heart. It hides from the frost but can be very brave.")],
    "frost_hound": [("What is a frost hound?", "A frost hound is a creature of ice and claw, born from the breath of the Vicious Ones. Its howl brings cold.")],
}
KNOWLEDGE_ORDER = ["piccalilli", "frost", "extinction", "vicious", "friendship", "hollow", "seed", "mouse", "frost_hound"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gentle_name = f.get("gentle_name", "a little mouse")
    vicious_name = f.get("vicious_name", "a frost hound pup")
    act = f.get("act_label", "planted a seed")
    place = f.get("place_label", "the Sunken Grove")
    return [
        f'Write a short mythical story for a young child on the theme "a small friendship that stops extinction" including the word "piccalilli".',
        f"Tell a myth where {gentle_name} the mouse and {vicious_name} the frost hound form a friendship that saves the last {world.facts.get('resource_label', 'Piccalilli')}.",
        f"Write a gentle myth about extinction and hope, where {gentle_name} and {vicious_name} perform a {act} together in {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gentle = f.get("gentle_name", "Tallow")
    vicious = f.get("vicious_name", "Nix")
    gentle_trait = f.get("gentle_trait", "small")
    vicious_trait = f.get("vicious_trait", "fierce-heart")
    resource_label = f.get("resource_label", "piccalilli")
    act_label = f.get("act_label", "plant a seed")
    place = f.get("place_label", "the Sunken Grove")
    qa = [
        QAItem(
            question=f"Who are the two main friends in the story about the {resource_label}?",
            answer=f"The two friends are {gentle}, a {gentle_trait} mouse, and {vicious}, a {vicious_trait} frost hound. They became friends even though they were supposed to be enemies."
        ),
        QAItem(
            question=f"What did {gentle} and {vicious} do together to help the {resource_label}?",
            answer=f"They performed a friendship act: {act_label}. This small act of trust and care was the key to saving the last {resource_label}."
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"The story took place in {place}. It was a special place where the {resource_label} once grew freely."
        ),
    ]
    if world.friendship_bridge >= 1.0:
        qa.append(QAItem(
            question=f"How did friendship change things for {gentle} and {vicious}?",
            answer=f"Friendship built a bridge between them. Because they trusted each other, the old rules of vicious and gentle no longer held. They could plant hope together."
        ))
    if world.facts.get("extinction_threat", True):
        qa.append(QAItem(
            question=f"What was the big danger in the story?",
            answer=f"The big danger was extinction. The Vicious Ones wanted all sweet things, like the {resource_label}, to disappear forever. The frost was their weapon."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    tags.add("piccalilli")
    tags.add("extinction")
    tags.add("friendship")
    if world.weather == "frost" or world.frost_level > 0:
        tags.add("frost")
    if any(e.is_vicious_by_type for e in world.beings()):
        tags.add("vicious")
    if any("hollow" in e.label or e.location == "hollow" for e in world.beings()):
        tags.add("hollow")
    resource_label = world.facts.get("resource_label", "piccalilli")
    if resource_label == "piccalilli":
        tags.add("seed")
    if any(e.type == "mouse" for e in world.beings()):
        tags.add("mouse")
    if any(e.type == "frost_hound" for e in world.beings()):
        tags.add("frost_hound")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.sweet_resource != 0:
            bits.append(f"sweet_resource={e.sweet_resource:.1f}")
        if e.temperature != 0:
            bits.append(f"temp={e.temperature:.1f}")
        if e.protected:
            bits.append("protected")
        if e.shelter:
            bits.append(f"shelter={e.shelter}")
        if e.is_vicious or e.is_vicious_by_type:
            bits.append("vicious")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  frost_level={world.frost_level:.1f} weather={world.weather}")
    lines.append(f"  friendship_bridge={world.friendship_bridge:.1f}")
    lines.append(f"  extinction_threat={world.extinction_threat}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired) if isinstance(n, str) else n for n in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="sunken_grove", friendship_act="seed_plant", resource="piccalilli",
                gentle_name="Tallow", vicious_name="Nix", gentle_trait="small", vicious_trait="fierce-heart",
                minor_gentle_name="Button"),
    StoryParams(place="whisper_valley", friendship_act="warm_share", resource="warm_spring",
                gentle_name="Moss", vicious_name="Grim", gentle_trait="wise", vicious_trait="silent",
                minor_gentle_name="Twig"),
    StoryParams(place="hollow_mound", friendship_act="vigil_keep", resource="light_lichen",
                gentle_name="Ember", vicious_name="Frostfang", gentle_trait="brave", vicious_trait="sly",
                minor_gentle_name="Flax"),
]


def explain_rejection(activity_key: str, resource_key: str) -> str:
    return (f"(No story: the resource {resource_key} does not grow in a place suitable for the act {activity_key}. "
            f"See valid_combos().)")


ASP_RULES = r"""
affords_act(P, A) :- setting(P), A = seed_plant ; A = warm_share ; A = vigil_keep.

grows_in(R, P) :- resource(R), region(R, G), (P = G ; P = grove ; P = sunken_grove).

valid_act_for(P, A, R) :- affords_act(P, A), grows_in(R, P), resource(R).

compatible_story(P, A, R) :- valid_act_for(P, A, R).

vicious_type(T) :- type(T), intimidation(T, _).
friendship_saves(P, A, R, G, V) :- compatible_story(P, A, R),
                                    gentle(G), vicious(V), not same(G, V).
"""


def asp_facts():
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid, r in SACRED_RESOURCES.items():
        lines.append(asp.fact("resource", rid))
        lines.append(asp.fact("region", rid, r.region))
    for aid in FRIENDSHIP_ACTS:
        lines.append(asp.fact("act_type", aid))
        lines.append(asp.fact("act_resource", aid, FRIENDSHIP_ACTS[aid].resource))
    for bid, _ in [(g, None) for g in GENTLE_NAMES]:
        lines.append(asp.fact("gentle", bid.lower()))
    for vid, _ in [(v, None) for v in VICIOUS_NAMES]:
        lines.append(asp.fact("vicious", vid.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos():
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify():
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
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
    ap = argparse.ArgumentParser(
        description="Story world: a small friendship that stops extinction.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--friendship-act", choices=FRIENDSHIP_ACTS)
    ap.add_argument("--resource", choices=SACRED_RESOURCES)
    ap.add_argument("--gentle-name")
    ap.add_argument("--vicious-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.friendship_act:
        combos = [c for c in combos if c[1] == args.friendship_act]
    if args.resource:
        combos = [c for c in combos if c[2] == args.resource]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, resource = rng.choice(sorted(combos))
    gentle_name = args.gentle_name or rng.choice(GENTLE_NAMES)
    vicious_name = args.vicious_name or rng.choice(VICIOUS_NAMES)
    gentle_trait = rng.choice(BEING_TRAITS)
    vicious_trait = rng.choice([t for t in BEING_TRAITS if t != gentle_trait])
    minor_gentle_name = rng.choice(MINOR_GENTLE_NAMES)
    return StoryParams(place=place, friendship_act=act, resource=resource,
                       gentle_name=gentle_name, vicious_name=vicious_name,
                       gentle_trait=gentle_trait, vicious_trait=vicious_trait,
                       minor_gentle_name=minor_gentle_name)


def tell(setting: Setting, friendship_act: FriendshipAct, resource: SacredResource,
         gentle_name: str = "Tallow", gentle_type: str = "mouse",
         gentle_trait: str = "small", vicious_name: str = "Nix",
         vicious_type: str = "frost_hound", vicious_trait: str = "fierce-heart",
         minor_gentle_name: str = "Button") -> World:
    world = World(setting)
    world.weather = "frost"
    world.frost_level = 1.0
    world.extinction_threat = True

    gentle = world.add(Entity(
        id=gentle_name, kind="being", type=gentle_type, label=gentle_name,
        traits=[gentle_trait, "gentle"],
        location="grove",
    ))
    vicious = world.add(Entity(
        id=vicious_name, kind="being", type=vicious_type, label=vicious_name,
        traits=[vicious_trait, "vicious-born"],
        is_vicious=True,
        location="grove",
    ))
    minor = world.add(Entity(
        id=minor_gentle_name, kind="being", type="vole", label=minor_gentle_name,
        traits=["small", "fearful"],
        location="grove",
    ))

    res = world.add(Entity(
        id="resource", kind="resource", type=resource.type, label=resource.label,
        phrase=resource.phrase, location=setting.place,
        plural=resource.plural,
    ))
    res.sweet_resource = 2.0

    # Act 1: Before
    world.say(SETTING_INTRODUCTION.get(setting.place, f"In {setting.place}, the old story was simple."))
    world.say(setting_detail := SETTING_DETAILS.get(setting.place, ""))
    if setting_detail:
        world.say(setting_detail)
    world.say(f"The Vicious Ones had sent their frost, and the {resource.label} was nearly gone.")
    world.say(f"{vicious_name}, a young {vicious_type} pup, was not like the others. Something stirred in its heart.")
    world.para()

    # Act 2: The meeting
    world.say(f"One day, {gentle_name} the {gentle_type} was hiding near {setting.place} when {vicious_name} found {gentle_name}.")
    world.say(f"{vicious_name} did not snarl. {vicious_name} just looked at the {resource.label} and {friendship_act.action_phrase}.")
    gentle.memes["allies"] += 1
    vicious.memes["allies"] += 1
    world.friendship_bridge += 1.0
    world.say("It was the first friendship between a gentle creature and a vicious one.")
    world.para()

    # Act 3: The small act of hope
    world.say(f"{gentle_name} was scared, but {vicious_name} showed {gentle_trait} courage.")
    world.say(f"The two of them {friendship_act.gerund}. {friendship_act.action_phrase}.")
    gentle.sweet_resource += 0.5
    gentle.memes["trust"] += friendship_act.trust_gain
    gentle.memes["hope"] += friendship_act.hope_gain
    vicious.memes["trust"] += friendship_act.trust_gain
    vicious.memes["hope"] += friendship_act.hope_gain
    propagate(world, narrate=True)
    world.para()

    # Act 4: The threat reminder
    world.say("But the Vicious Ones knew. They sent a howl across the frost.")
    world.frost_level += 0.5
    gentle.memes["terror"] += 1.0
    propagate(world, narrate=True)
    world.para()

    # Act 5: Resolution
    world.say(f"Despite the cold, {gentle_name} and {vicious_name} finished their task.")
    world.say(f"They hid a single seed of {resource.label} in a secret hollow, where the frost could not touch it.")
    world.say(f"The {resource.label} survived. Extinction did not win that day.")
    world.say("And so the old myth changed: a friendship, not a battle, saved the sweet things.")
    world.extinction_threat = False
    world.facts.update(
        gentle_name=gentle_name,
        vicious_name=vicious_name,
        gentle_trait=gentle_trait,
        vicious_trait=vicious_trait,
        resource_label=resource.label,
        act_label=friendship_act.verb,
        place_label=setting.place,
        extinction_threat=world.extinction_threat,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    act = FRIENDSHIP_ACTS[params.friendship_act]
    resource = SACRED_RESOURCES[params.resource]
    world = tell(setting, act, resource, params.gentle_name, "mouse", params.gentle_trait,
                 params.vicious_name, "frost_hound", params.vicious_trait,
                 params.minor_gentle_name)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, act, resource) combos:\n")
        for place, act, resource in triples:
            print(f"  {place:15} {act:12} {resource:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.gentle_name} & {p.vicious_name}: {p.friendship_act} in {p.place} (resource: {p.resource})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
