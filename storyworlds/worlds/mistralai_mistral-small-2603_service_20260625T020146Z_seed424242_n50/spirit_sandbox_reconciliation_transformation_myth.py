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

# Mythic thresholds
THRESHOLD = 1.0
SPLIT_LIMIT = 2.0
RITUAL_DEPTH = 3

# Metaphysical meter keys the world tracks
METER_KINDS = {"purity", "unity", "energy", "shadow"}
# Symbolic regions of the fracturing spirit
REGIONS = {"heart", "mind", "will"}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "spirit"
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "witch", "maiden"}
        male = {"boy", "warrior", "lad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Parametrization knobs – mythic facets under player control
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the sacred sandbox"
    hallowed: bool = True
    mood: str = "quiet"            # quiet, reverent, chaotic

@dataclass
class Transformation:
    id: str
    verb: str
    gerund: str
    short: str
    rite: str
    foci: set[str]                 # regions unified
    gain: str                     # meter uplift phrase
    loss: str                     # old meter phrase
    tags: set[str] = field(default_factory=set)

@dataclass
class Spirit:
    label: str
    phrase: str
    facets: set[str] = field(default_factory=set)
    plural: bool = False

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.foci: set[str] = set()
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
        for g in self.worn_items(actor):
            if g.protective and region in g.covers:
                return True
        return False

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
        clone.foci = set(self.foci)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules – mythic causality
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_wane(world: World) -> list[str]:
    out: list[str] = []
    for spirit in [e for e in world.entities.values()
                   if e.type == "spirit" and e.meters["unity"] < THRESHOLD]:
        for child in world.characters():
            if world.foci and child.memes["resolve"] < THRESHOLD:
                continue
            sig = ("wane", spirit.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.say(
                f"Verily, when {child.id} turned {child.pronoun('possessive')} gaze away, "
                f"{spirit.pronoun('subject')} faded one shade darker."
            )
    return out

def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    for spirit in [e for e in world.entities.values() if e.type == "spirit"]:
        if spirit.memes["joy"] >= THRESHOLD and spirit.memes["resolve"] >= THRESHOLD:
            for region in REGIONS:
                if world.foci and region not in world.foci:
                    continue
                sig = ("spark", region, spirit.id)
                if sig in world.fired:
                    continue
                if spirit.meters["energy"] < SPLIT_LIMIT:
                    spirit.meters["energy"] += 1
                    out.append(
                        f"From {spirit.pronoun('possessive')} {region}, "
                        f"{spirit.pronoun('subject').lower()} a tiny ember wafted upward."
                    )
        return out
    return []

def _r_rift(world: World) -> list[str]:
    out: list[str] = []
    for spirit in [e for e in world.entities.values()
                   if e.type == "spirit" and e.meters["unity"] < THRESHOLD]:
        for region in REGIONS:
            if spirit.meters["energy"] >= SPLIT_LIMIT:
                sig = ("rifted", region, spirit.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                name = f"{spirit.id}_{region}"
                entity = world.add(Entity(
                    id=name,
                    type=f"sand_{region}",
                    label=region,
                    phrase=f"the {region} fragment of the {spirit.label}",
                    owner=spirit.id,
                ))
                entity.region = region
                entity.plural = True
                spirit.meters["energy"] -= 1
                out.append(
                    f"Thus the ancient power cracked; the {region} essence "
                    f"tore free as the {spirit.label} wept."
                )
    return out

def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    primary = next((e for e in world.entities.values()
                    if e.type == "spirit" and e.id == "Spirit"), None)
    if not primary:
        return []
    if primary.meters["unity"] >= THRESHOLD:
        return []
    involved = sum(1 for e in world.entities.values()
                   if e.type == "sand_person" and e.worn_by is not None)
    if involved < RITUAL_DEPTH:
        return []
    sig = ("reconciled", primary.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    primary.meters["unity"] = min(primary.meters.get("unity", 0) + 2.5, 5.0)
    primary.meters["purity"] = min(primary.meters.get("purity", 0) + 1.8, 4.0)
    primary.meters["energy"] = min(primary.meters.get("energy", 0) + 1.3, 3.5)
    primary.memes["resolve"] = 0.0
    out.append(
        f"Behold!  When the children joined {primary.pronoun('possessive')} essence "
        f"with steadfast voices, the sacred unity rekindled!"
    )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="wane", tag="spirit", apply=_r_wane),
    Rule(name="spark", tag="spirit", apply=_r_spark),
    Rule(name="rift", tag="spirit", apply=_r_rift),
    Rule(name="reconcile", tag="spirit", apply=_r_reconcile),
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
                (produced.extend(s for s in sents))
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Reasonableness checks for a valid story
# ---------------------------------------------------------------------------
def has_transformation(trans_id: str, spirit_id="Spirit") -> bool:
    return trans_id in {t.id for t in TRANSFORMS}

def can_unite(trans, spirit) -> bool:
    return any(region in trans.foci for region in REGIONS)

# ---------------------------------------------------------------------------
# Verbs & screenplay beats – mythic arc
# ---------------------------------------------------------------------------
def hallow(world: World) -> None:
    if world.setting.hallowed:
        world.say(
            "Beneath the banyan’s bough, where moonlight braids the dust, "
            "lay the sacred sandbox, aglow with forgotten names."
        )

def discovers(world: World, child: Entity, sandbox_id="Sandbox") -> None:
    world.say(
        f"By fortune or fate, {child.id} — {child.pronoun('subject')} small and "
        f"{child.traits[0] if child.traits else 'cleareyed'} — knelt and brushed "
        f"{sandbox_id} with {child.pronoun('possessive')} fingertips."
    )

def intuits(world: World, child: Entity, spirit: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"That touch ignited knowing: {child.id} felt the {spirit.label}’s ancient "
        f"ache as if {child.pronoun()} had always known it."
    )

def fragments(world: World, spirit: Entity) -> None:
    for region in spirit.facets:
        world.say(
            f"The {spirit.label} wailed softly.  ‘I am sliced to wind and shadow!’ "
            f"{spirit.pronoun().capitalize()} lament rang backward through time."
        )

def welcomes(world: World, child: Entity) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} reached into the pale grains and whispered, "
        f"‘Lo, I shall summon thee anew.’"
    )

def chooses(world: World, child: Entity, trans) -> None:
    child.memes["resolve"] += 0.8
    world.say(
        f"Then {child.id} marked {trans.rite} upon the sand.  "
        f"A tremor shook the hollow."
    )

def transforms(world: World, child: Entity, trans, spirit_id="Spirit") -> None:
    spirit = world.get(spirit_id)
    base = spirit.label
    for region in trans.foci:
        spirit.facets.discard(region)
    spirit.memes["hope"] = min(spirit.memes.get("hope", 0) + 1.5, 3.0)
    world.say(
        f"Runes flared and fused: the {base} became whole once more. "
        f"{trans.gain}!"
    )
    world.facts["trans_meter_gain"] = trans.gain

def shines(world: World, spirit_id="Spirit") -> None:
    spirit = world.get(spirit_id)
    world.say(
        f"Thus the {spirit.label} stood in radiant stillness, "
        "its song woven into every grain."
    )

# Main screenplay – three mythic acts set in the sandbox
def tell(setting: Setting, trans) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="Child",
        kind="character",
        type="child",
        traits=["stouthearted"],
    ))
    sandbox = world.add(Entity(
        id="Sandbox",
        kind="thing",
        phrase="the sacred sandbox beneath the oldest banyan",
    ))
    spirit = world.add(Entity(
        id="Spirit",
        kind="spirit",
        label="Spirit of Imagined Play",
        phrase="the wandering Spirit of Imagined Play, ancient and faint",
        facets=set(REGIONS),
        meters={"unity": 1.2, "purity": 3.5, "shadow": 0.9},
        memes={"loneliness": 2.1, "hope": 0.3},
    ))

    # Act I – the hallowed sandbox
    world.para()
    hallow(world)
    discovers(world, child)
    intuits(world, child, spirit)

    # Act II – the fractured lament
    world.para()
    fragments(world, spirit)
    world.facts["fracture_why"] = "self-doubt after forgotten play"

    # Act III – re-kindling through the chosen transformation
    world.para()
    welcomes(world, child)
    chooses(world, child, trans)
    transforms(world, child, trans)
    shines(world)

    world.facts.update(
        child=child,
        spirit=spirit,
        sandbox=sandbox,
        transformation=trans,
        unity_before=1.2,
        purity_before=3.5,
    )
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "sandbox": Setting(place="the sacred sandbox beneath the oldest banyan"),
}

TRANSFORMS = [
    Transformation(
        id="bond",
        verb="bind the wandering fragments anew",
        gerund="binding the wandering fragments anew",
        short="bonding_ritual",
        rite="drew the embrace upon the sand",
        foci={"heart"},
        gain="its shining heart central and true",
        loss="the old ache of doubt",
        tags={"bond", "heart"},
    ),
    Transformation(
        id="weave",
        verb="weave the lost essences together",
        gerund="weaving the lost essences together",
        short="weave_pattern",
        rite="poured the silver sigils meant for mind",
        foci={"mind"},
        gain="its unified mind bight and lucid",
        loss="bewilderment",
        tags={"weave", "mind"},
    ),
    Transformation(
        id="fuse",
        verb="fuse the dissident wills into flame",
        gerund="fusing the dissident wills into flame",
        short="fusion_enchantment",
        rite="spoke the words of will thrice",
        foci={"will"},
        gain="its will fierce and unbroken",
        loss="fear that it should ever fray",
        tags={"fuse", "will"},
    ),
]

SPIRITS = {
    "spirit": Spirit(
        label="Spirit of Imagined Play",
        phrase="the wandering Spirit of Imagined Play, ancient and faint",
        facets=set(REGIONS),
    ),
}

GIRL_NAMES = ["Lyra", "Nimue", "Sylvie", "Aelfwyn", "Elspeth"]
BOY_NAMES = ["Tristan", "Bran", "Rhys", "Mael", "Cedric"]
TRAITS = ["stouthearted", "lionhearted", "steadfast", "luminous", "quickwitted"]

# ---------------------------------------------------------------------------
# Q&A – three tiers tuned to mythic spirit domain
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Tell a mythic parable (3–5 short paragraphs) about a child who restores '
        'a fractured ancient spirit through one sacred act.',
        'Write a tiny myth starring "spirit" and "sandbox" where a mortal child '
        'performs a miniature ceremony that reunites a splintered spirit.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    spirit, trans = f["spirit"], f["transformation"]
    qa = [
        QAItem(
            question="Who first noticed the Spirit of Imagined Play in the sacred sandbox?",
            answer=f"It was {f['child'].id}, a {f['child'].traits[0]} child who knelt in {world.setting.place}."
        ),
        QAItem(
            question="Why had the Spirit of Imagined Play become faint and split?",
            answer=f"The spirit had faltered because {world.facts['fracture_why']}. "
                   "Its heart, mind, and will had separated into the pale grains."
        ),
        QAItem(
            question=(
                f"How did {f['child'].id} reunite the Spirit of Imagined Play "
                f"through the {trans.short} ceremony?"
            ),
            answer=(
                f"By {trans.rite}, {f['child'].id} restored the "
                f"{trans.foci.pop()} essence, thus rekindling the spirit’s "
                f"unity and {trans.gain}."
            ),
        ),
        QAItem(
            question=(
                "What changed about the Spirit of Imagined Play after the child’s "
                "ceremony?",
            ),
            answer="The spirit regained its purity and energy, standing whole and shining.",
        ),
    ]
    return qa

KNOWLEDGE = {
    "spirit": [
        ("What is a spirit?",
         "A spirit is an ancient essence of energy and memory, often tied to a place or idea."),
    ],
    "sandbox": [
        ("What makes a sandbox magical?",
         "A sandbox beneath the oldest banyan is said to hold forgotten dreams; "
         "when touched, it whispers to the heart."),
    ],
    "reconciliation": [
        ("What does reconciliation mean?",
         "Reconciliation is the act of making parts whole again after they have been apart or split apart."),
    ],
    "transformation": [
        ("What is a ceremonial transformation?",
         "It is a sacred act, such as drawing runes, singing words, or forming embraces, "
         "that restores lost unity or power."),
    ],
}
KNOWLEDGE_ORDER = ["spirit", "sandbox", "reconciliation", "transformation"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"spirit", "sandbox", "reconciliation", "transformation"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts – asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions – answerable from the tale ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions – child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP twin – clingo gate for the mythic reasonableness check
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A spirit must be fractured for any reconciliation arc to exist.
fractured(spirit) :- fragments_of(spirit, R).

% A given transformation reunites an explicit facet.
reunites_by(T, spirit, F) :- transformation(T),
                              focuses(T, F),
                              fragments_of(spirit, F).

% Story is valid if some reconciling transformation exists.
has_fix(spirit, T) :- transformation(T), reunites_by(T, spirit, _).
valid_story :- fractured(spirit), has_fix(spirit, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("spirit", "spirit"))
    for f in sorted(REGIONS):
        lines.append(asp.fact("fragments_of", "spirit", f))
    for t in TRANSFORMS:
        lines.append(asp.fact("transformation", t.id))
        lines.append(asp.fact("focuses", t.id, t.short))
        for f in sorted(t.foci):
            lines.append(asp.fact("focuses", t.id, f))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    sym_model = asp.one_model(asp_program("#show valid_story/0."))
    has_valid = any(sym.name == "valid_story" for sym in sym_model)
    if has_valid:
        print("OK: clingo gate agrees mythic arc is reasonable.")
        return 0
    print("MISMATCH: clingo denies this is a valid reconciliation arc.")
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    spirit_name: str = "Spirit of Imagined Play"
    child_name: str = ""
    transformation: str = ""
    mood: str = ""
    seed: Optional[int] = None

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic sandbox tale: a child restores a fractured spirit.")
    ap.add_argument("--spirit", choices=SPIRITS, default="spirit",
                   help="spirit archetype to center the story on")
    ap.add_argument("--name", help="child’s name")
    ap.add_argument("--trans", choices=[t.id for t in TRANSFORMS],
                   help="which transformation ritual to feature")
    ap.add_argument("--mood", choices=["quiet", "reverent", "chaotic"],
                   help="mood to color the sandbox")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list clingo-verified valid stories")
    ap.add_argument("--verify", action="store_true", help="check ASP gate parity")
    ap.add_argument("--show-asp", action="store_true", help="emit full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trans:
        ok = [t.id for t in TRANSFORMS if t.id == args.trans]
        if not ok:
            raise StoryError(f"No transformation named {args.trans} exists.")
    spirit_ok = args.spirit in SPIRITS
    if not spirit_ok:
        raise StoryError(f"Unknown spirit {args.spirit}")
    trans_name = args.trans or rng.choice([t.id for t in TRANSFORMS])
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    mood = args.mood or rng.choice(["quiet", "reverent", "chaotic"])
    return StoryParams(
        spirit_name=args.spirit,
        child_name=name,
        transformation=trans_name,
        mood=mood,
    )

def generate(params: StoryParams) -> StorySample:
    setting = Setting(mood=params.mood)
    trans = next(t for t in TRANSFORMS if t.id == params.transformation)
    world = tell(setting, trans)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n".join(f"  {e.id:8} ({e.type:7}): {dict(e.meters)} / {dict(e.memes)}" for e in sample.world.entities.values()))
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program(""))
        print("1 valid mythic reconciliation arc found.")
        return

    base_seed = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(
                spirit_name="spirit",
                child_name=name,
                transformation=rng.choice([t.id for t in TRANSFORMS]),
                mood="quiet",
            )) for name in GIRL_NAMES[:3] + BOY_NAMES[:3]
        ]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            txt = sample.story
            if txt not in seen:
                seen.add(txt)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
