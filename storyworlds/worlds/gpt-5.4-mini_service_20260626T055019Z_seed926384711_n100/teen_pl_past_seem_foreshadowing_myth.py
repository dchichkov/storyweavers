#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/teen_pl_past_seem_foreshadowing_myth.py
===============================================================================================================

A small myth-style story world about teen friends, old signs, and a foreshadowed
choice that changes what happens next.

The seed words suggest:
- teen-pl: a group of teens, not a lone child
- past: the narration and world state should live in the past tense
- seem: the story should lean on things that seemed one way before the truth was known
- foreshadowing: the world should let an omen point toward a later turn
- myth: the tone should feel legendary, concrete, and a little ancient

The story logic here is:
- teens travel with an ordinary goal
- a sign seems small at first
- the sign foreshadows a risk
- the teens choose a wiser path
- the ending proves the world changed because they listened

The script follows the shared Storyweavers contract:
- one standalone stdlib file
- eager import of results containers
- lazy import of asp helpers inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    omens: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)
    winds: str = ""


@dataclass
class Omen:
    id: str
    sign: str
    foreshadows: str
    risk: str
    place_tags: set[str] = field(default_factory=set)
    weather_tags: set[str] = field(default_factory=set)
    made_by: str = ""


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    foiled_by: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""
        self.omen_seen: bool = False

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.omen_seen = self.omen_seen
        clone.facts = dict(self.facts)
        return clone


def _as_list(x):
    return list(x) if isinstance(x, (set, tuple)) else x


def _foreshadow(world: World, actor: Entity, omen: Omen) -> None:
    sig = ("foreshadow", actor.id, omen.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["unease"] += 1
    actor.memes["attention"] += 1
    world.omen_seen = True
    world.say(
        f"{actor.id} saw {omen.sign}, and it seemed small at first."
    )
    world.say(
        f"Still, the sign felt like a hand from the old world, pointing toward {omen.foreshadows}."
    )


def _risk_turn(world: World, actor: Entity, relic: Relic, omen: Omen) -> None:
    sig = ("risk", actor.id, relic.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["resolve"] += 1
    world.say(
        f"{actor.id} looked at {relic.label} and remembered the old warning about {omen.risk}."
    )


def _storm_check(world: World, actor: Entity, relic: Relic, charm: Charm) -> None:
    sig = ("storm", actor.id, relic.id)
    if sig in world.fired:
        return
    if actor.meters.get("storm", 0.0) < THRESHOLD:
        return
    if actor.meters.get("mud", 0.0) < THRESHOLD:
        return
    if relic.region not in charm.protects:
        return
    if "storm" not in charm.guards or "mud" not in charm.guards:
        return
    if actor.memes.get("prepared", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    relic.meters["safe"] = 1.0
    world.say(f"The charm worked, and {relic.label} stayed safe through the storm.")


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.memes.get("unease", 0.0) >= THRESHOLD and not world.omen_seen:
                world.omen_seen = True
        for rule in ():
            pass
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, omen: Omen, relic: Relic) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["storm"] += 1
    sim.get(actor.id).meters["mud"] += 1
    return {"risk": omen.risk in sim.place.hazards, "safe": True}


def tell(world: World, leader: Entity, friend: Entity, omen: Omen, relic: Relic, charm: Charm) -> None:
    world.say(
        f"Long ago, {leader.id} and {friend.id} walked together to {world.place.name}, "
        f"where the wind carried old songs."
    )
    world.say(
        f"They had come for {relic.phrase}, because the elders said it would help the village remember the spring."
    )
    world.para()
    world.say(
        f"On the path, {leader.id} noticed {omen.sign}, and {friend.id} said it only seemed like a harmless sign."
    )
    _foreshadow(world, leader, omen)
    world.say(
        f"Yet the sky lowered its brow, and the ground near the stones began to smell of rain and deep mud."
    )
    _risk_turn(world, friend, relic, omen)
    world.para()
    if relic.region in charm.protects:
        world.say(
            f"{leader.id} chose the wiser road and tied {charm.label} around the bundle."
        )
        world.say(
            f"{charm.prep.capitalize()}, they crossed the wet field together, and {charm.tail}."
        )
        world.say(
            f"When the storm came, the mud rose, but the bundle stayed dry."
        )
        world.say(
            f"By dusk they returned with {relic.label} clean in their hands, and even the old trees seemed to bow."
        )
        leader.memes["joy"] = leader.memes.get("joy", 0.0) + 1
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
        leader.memes["prepared"] = 1.0
        leader.meters["storm"] = 1.0
        leader.meters["mud"] = 1.0
        relic.meters["safe"] = 1.0
        _storm_check(world, leader, relic, charm)
    else:
        raise StoryError("No reasonable charm fit the relic's danger.")
    world.say(
        f"So the teens learned that a sign could seem small, yet still carry the first whisper of a bigger change."
    )


PLACE_REGISTRY = {
    "riverbank": Place(
        name="the riverbank",
        omens={"heron", "cloud-ring"},
        hazards={"storm", "mud"},
        winds="river wind",
    ),
    "hillpath": Place(
        name="the hillpath",
        omens={"cicada-silence", "red-moon"},
        hazards={"storm", "rockslide"},
        winds="thin hill wind",
    ),
    "orchard": Place(
        name="the old orchard",
        omens={"owl-call", "silver-leaf"},
        hazards={"storm", "branchfall"},
        winds="apple wind",
    ),
}

OMEN_REGISTRY = {
    "heron": Omen(
        id="heron",
        sign="a lone heron standing still in the reeds",
        foreshadows="a hard rain on the riverbank",
        risk="storm",
        place_tags={"riverbank"},
        weather_tags={"wet"},
        made_by="river",
    ),
    "cloud-ring": Omen(
        id="cloud-ring",
        sign="a ring of clouds circling the sun",
        foreshadows="mud that would swallow the path",
        risk="mud",
        place_tags={"riverbank", "hillpath"},
        weather_tags={"storm"},
        made_by="sky",
    ),
    "owl-call": Omen(
        id="owl-call",
        sign="an owl calling twice before sunset",
        foreshadows="a branchfall in the old orchard",
        risk="branchfall",
        place_tags={"orchard"},
        weather_tags={"night"},
        made_by="woods",
    ),
}

RELIC_REGISTRY = {
    "harp": Relic(
        id="harp",
        label="the bronze harp",
        phrase="a bronze harp wrapped in cloth",
        region="torso",
        foiled_by={"storm"},
    ),
    "lantern": Relic(
        id="lantern",
        label="the glass lantern",
        phrase="a glass lantern with a moon-shaped handle",
        region="hand",
        foiled_by={"mud", "storm"},
    ),
    "scroll": Relic(
        id="scroll",
        label="the painted scroll",
        phrase="a painted scroll tied with red thread",
        region="arm",
        foiled_by={"mud", "branchfall"},
    ),
}

CHARM_REGISTRY = {
    "oilcloth": Charm(
        id="oilcloth",
        label="an oilcloth wrap",
        prep="The wrap was old but strong",
        tail="they reached the shrine without breaking the bundle",
        protects={"torso", "arm", "hand"},
        guards={"storm", "mud", "branchfall"},
    ),
    "reed-cape": Charm(
        id="reed-cape",
        label="a reed cape",
        prep="The cape rustled like summer grass",
        tail="they carried the gift back under its wide leaves",
        protects={"torso", "hand"},
        guards={"storm", "mud"},
    ),
    "leather-sling": Charm(
        id="leather sling",
        label="a leather sling",
        prep="The sling settled the bundle against the body",
        tail="they walked home with the relic held high and safe",
        protects={"torso", "arm"},
        guards={"storm", "mud"},
        plural=False,
    ),
}

TEEN_NAMES = ["Mira", "Juno", "Tavi", "Sora", "Nico", "Lina", "Belen", "Aris"]
TEEN_TRAITS = ["brave", "curious", "restless", "kind", "steady", "bright"]


@dataclass
class StoryParams:
    place: str
    omen: str
    relic: str
    charm: str
    leader: str
    friend: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACE_REGISTRY.items():
        for omen_id in place.omens:
            omen = OMEN_REGISTRY[omen_id]
            if omen_id not in OMEN_REGISTRY:
                continue
            for relic_id, relic in RELIC_REGISTRY.items():
                if omen.risk in relic.foiled_by:
                    for charm_id, charm in CHARM_REGISTRY.items():
                        if omen.risk in charm.guards and relic.region in charm.protects:
                            combos.append((place_id, omen_id, relic_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic teen friends, old omens, and a foreshadowed choice.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--omen", choices=OMEN_REGISTRY)
    ap.add_argument("--relic", choices=RELIC_REGISTRY)
    ap.add_argument("--charm", choices=CHARM_REGISTRY)
    ap.add_argument("--leader")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TEEN_TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.omen and args.place and args.omen not in PLACE_REGISTRY[args.place].omens:
        raise StoryError("That omen does not belong to that place.")
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    omen = args.omen or rng.choice(sorted(PLACE_REGISTRY[place].omens))
    relic_choices = [r for r, rel in RELIC_REGISTRY.items() if OMEN_REGISTRY[omen].risk in rel.foiled_by]
    if args.relic:
        if args.relic not in relic_choices:
            raise StoryError("That relic does not fit the omen's danger.")
        relic = args.relic
    else:
        relic = rng.choice(sorted(relic_choices))
    charm_choices = [
        c for c, ch in CHARM_REGISTRY.items()
        if OMEN_REGISTRY[omen].risk in ch.guards and RELIC_REGISTRY[relic].region in ch.protects
    ]
    if args.charm:
        if args.charm not in charm_choices:
            raise StoryError("That charm does not protect the relic from the omen.")
        charm = args.charm
    else:
        charm = rng.choice(sorted(charm_choices))
    leader = args.leader or rng.choice(TEEN_NAMES)
    friend = args.friend or rng.choice([n for n in TEEN_NAMES if n != leader])
    trait = args.trait or rng.choice(TEEN_TRAITS)
    return StoryParams(place=place, omen=omen, relic=relic, charm=charm, leader=leader, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    omen = OMEN_REGISTRY[params.omen]
    relic_cfg = RELIC_REGISTRY[params.relic]
    charm_cfg = CHARM_REGISTRY[params.charm]
    world = World(place)
    leader = world.add(Entity(id=params.leader, kind="character", type="girl", meters={}, memes={"unease": 0.0, "resolve": 0.0, "joy": 0.0, "prepared": 0.0, "attention": 0.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", meters={}, memes={"unease": 0.0, "resolve": 0.0, "joy": 0.0, "prepared": 0.0, "attention": 0.0}))
    relic = world.add(Entity(id=relic_cfg.id, type="thing", label=relic_cfg.label, phrase=relic_cfg.phrase, region=relic_cfg.region, plural=relic_cfg.plural, meters={}))
    charm = world.add(Entity(id=charm_cfg.id, type="thing", label=charm_cfg.label, protective=True, covers=set(charm_cfg.protects), plural=charm_cfg.plural))
    world.facts.update(leader=leader, friend=friend, omen=omen, relic=relic, charm=charm, place=place, params=params)
    tell(world, leader, friend, omen, relic, charm)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short myth about teen friends at {p.place} who notice {OMEN_REGISTRY[p.omen].sign} and change their plans.",
        f"Tell a past-tense story where something that seemed small turns out to foreshadow a danger.",
        f"Write a gentle legend in which teens carry {RELIC_REGISTRY[p.relic].label} and choose a safer path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader: Entity = f["leader"]
    friend: Entity = f["friend"]
    omen: Omen = f["omen"]
    relic: Entity = f["relic"]
    charm: Entity = f["charm"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {leader.id} and {friend.id} go to {place.name} to get?",
            answer=f"They went to {place.name} to bring home {relic.phrase}.",
        ),
        QAItem(
            question=f"What sign did {leader.id} notice that seemed small at first?",
            answer=f"{leader.id} noticed {omen.sign}, and it seemed small at first even though it foreshadowed {omen.foreshadows}.",
        ),
        QAItem(
            question=f"How did {charm.label} help the teens in the end?",
            answer=f"{charm.label} protected the bundle, so the teens could carry {relic.label} safely through the storm.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "storm": [
        QAItem(
            question="What is a storm?",
            answer="A storm is a time when the sky brings strong wind, rain, or both.",
        )
    ],
    "mud": [
        QAItem(
            question="What is mud?",
            answer="Mud is wet earth. It can stick to shoes and make paths slippery.",
        )
    ],
    "branchfall": [
        QAItem(
            question="Why can falling branches be dangerous?",
            answer="Falling branches can hit people or break things, so it is safer to watch for them and stay clear.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set()
    f = world.facts
    tags.add(f["omen"].risk)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.covers:
            parts.append(f"covers={sorted(e.covers)}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", omen="heron", relic="lantern", charm="oilcloth", leader="Mira", friend="Tavi", trait="curious"),
    StoryParams(place="hillpath", omen="cloud-ring", relic="scroll", charm="leather-sling", leader="Juno", friend="Nico", trait="steady"),
    StoryParams(place="orchard", omen="owl-call", relic="harp", charm="reed-cape", leader="Sora", friend="Lina", trait="brave"),
]


ASP_RULES = r"""
place(P) :- setting(P).
omen(O) :- omen_fact(O).
relic(R) :- relic_fact(R).
charm(C) :- charm_fact(C).

foreshadows(O, Risk) :- omen_risk(O, Risk).
compatible(P, O, R, C) :-
    place(P),
    place_omen(P, O),
    omen_risk(O, Risk),
    relic_foiled_by(R, Risk),
    charm_guards(C, Risk),
    relic_region(R, Region),
    charm_protects(C, Region).

#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("setting", pid))
        for o in sorted(p.omens):
            lines.append(asp.fact("place_omen", pid, o))
    for oid, o in OMEN_REGISTRY.items():
        lines.append(asp.fact("omen_fact", oid))
        lines.append(asp.fact("omen_risk", oid, o.risk))
    for rid, r in RELIC_REGISTRY.items():
        lines.append(asp.fact("relic_fact", rid))
        lines.append(asp.fact("relic_region", rid, r.region))
        for risk in sorted(r.foiled_by):
            lines.append(asp.fact("relic_foiled_by", rid, risk))
    for cid, c in CHARM_REGISTRY.items():
        lines.append(asp.fact("charm_fact", cid))
        for risk in sorted(c.guards):
            lines.append(asp.fact("charm_guards", cid, risk))
        for region in sorted(c.protects):
            lines.append(asp.fact("charm_protects", cid, region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = {t[:3] for t in asp_valid_combos()}
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(place: str, omen: str, relic: str, charm: str) -> str:
    return (
        f"(No story: at {place}, {OMEN_REGISTRY[omen].sign} does not fit "
        f"{RELIC_REGISTRY[relic].label} with {CHARM_REGISTRY[charm].label}. "
        f"The omen must foreshadow a real danger that the charm can actually answer.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    omen = args.omen or rng.choice(sorted(PLACE_REGISTRY[place].omens))
    if args.omen and args.place and args.omen not in PLACE_REGISTRY[args.place].omens:
        raise StoryError("That omen does not belong to that place.")
    relic_choices = [r for r, rel in RELIC_REGISTRY.items() if OMEN_REGISTRY[omen].risk in rel.foiled_by]
    relic = args.relic or rng.choice(sorted(relic_choices))
    charm_choices = [c for c, ch in CHARM_REGISTRY.items() if OMEN_REGISTRY[omen].risk in ch.guards and RELIC_REGISTRY[relic].region in ch.protects]
    charm = args.charm or rng.choice(sorted(charm_choices))
    if args.relic and args.charm and not (OMEN_REGISTRY[omen].risk in CHARM_REGISTRY[charm].guards and RELIC_REGISTRY[relic].region in CHARM_REGISTRY[charm].protects):
        raise StoryError(explain_rejection(place, omen, relic, charm))
    leader = args.leader or rng.choice(TEEN_NAMES)
    friend = args.friend or rng.choice([n for n in TEEN_NAMES if n != leader])
    trait = args.trait or rng.choice(TEEN_TRAITS)
    return StoryParams(place=place, omen=omen, relic=relic, charm=charm, leader=leader, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACE_REGISTRY[params.place])
    leader = world.add(Entity(id=params.leader, kind="character", type="girl", memes={"unease": 0.0, "resolve": 0.0, "joy": 0.0, "prepared": 0.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", memes={"unease": 0.0, "resolve": 0.0, "joy": 0.0, "prepared": 0.0}))
    omen = OMEN_REGISTRY[params.omen]
    relic = world.add(Entity(id=params.relic, label=RELIC_REGISTRY[params.relic].label, phrase=RELIC_REGISTRY[params.relic].phrase, region=RELIC_REGISTRY[params.relic].region, plural=RELIC_REGISTRY[params.relic].plural))
    charm = world.add(Entity(id=params.charm, label=CHARM_REGISTRY[params.charm].label, protective=True, covers=set(CHARM_REGISTRY[params.charm].protects), plural=CHARM_REGISTRY[params.charm].plural))
    world.facts.update(leader=leader, friend=friend, omen=omen, relic=relic, charm=charm, params=params)
    tell(world, leader, friend, omen, relic, charm)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.leader} and friends: {p.omen} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
