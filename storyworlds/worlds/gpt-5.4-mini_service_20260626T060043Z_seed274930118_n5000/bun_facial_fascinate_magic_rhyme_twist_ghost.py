#!/usr/bin/env python3
"""
storyworlds/worlds/bun_facial_fascinate_magic_rhyme_twist_ghost.py
===================================================================

A small ghost-story world built from the seed words:
bun, facial, fascinate

Premise:
- A child is fascinated by a friendly ghost's magic rhyme.
- The child has a neat bun and a face-freshening facial mask for a small night show.
- A twist in the spooky room risks ruining the costume.
- The ending resolves with a safer magical rhyme and a new, calm image.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib prose engine
- typed entities with meters and memes
- inline ASP twin and Python reasonableness gate
- support for generation, QA, trace, JSON, verify, and ASP listing
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "mess": 0.0, "fear": 0.0}
        if not self.memes:
            self.memes = {"fascinate": 0.0, "joy": 0.0, "worry": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Feature:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


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


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for feat in FEATURES.values():
            if actor.meters[feat.risk] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("dust", actor.id, item.id, feat.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["mess"] += 1
                item.meters["dust"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty in the spooky room.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["mess"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["worry"] += 1
        out.append(f"That would give {carer.label} more worry.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_dust,
    _r_worry,
    _r_conflict,
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(feature: Feature, prize: Prize) -> bool:
    return prize.region in feature.zone


def select_gear(feature: Feature, prize: Prize) -> Optional[Gear]:
    for gear in GEARS:
        if feature.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, feature: Feature, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "region": v.region,
        "protective": v.protective, "covers": set(v.covers), "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes),
    }) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    sim.fired = set(world.fired)
    sim.get(actor.id).meters[feature.risk] += 1
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["mess"] >= THRESHOLD),
            "worry": sum(e.meters["worry"] for e in sim.characters())}


def activity_delight(feature: Feature) -> str:
    return {
        "magic": "the sparkly tricks looked like fireflies dancing in a jar",
        "rhyme": "the little rhyme bounced in the air like a bright ball",
        "twist": "the twisty step made the floor feel like a spinning cloud",
    }.get(feature.id, "it made the room feel alive")


def setting_detail(setting: Setting, feature: Feature) -> str:
    if setting.indoor:
        return f"The {setting.place} was dim and quiet, with one moonbeam on the floor."
    return f"{setting.place.capitalize()} waited outside like a dark storybook page."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a neat bun and very bright eyes.")


def loves_feature(world: World, hero: Entity, feature: Feature) -> None:
    hero.memes["fascinate"] += 1
    world.say(f"{hero.id} was fascinated by {feature.name}; {activity_delight(feature)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That evening, {hero.id}'s {parent.label} brought home {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} with care.")


def arrive(world: World, hero: Entity, parent: Entity, feature: Feature) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, feature))


def wants(world: World, hero: Entity, feature: Feature) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {feature.verb}, but the spooky hush made {hero.pronoun('object')} pause.")


def warn(world: World, parent: Entity, hero: Entity, feature: Feature, prize: Entity) -> bool:
    pred = predict_mess(world, hero, feature, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = feature.risk
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f'"If you {feature.verb}, your {prize.label} will get messy," {parent.label} said.')
    return True


def defies(world: World, hero: Entity, feature: Feature) -> None:
    hero.memes["conflict"] += 0.5
    world.say(f"{hero.id} almost rushed ahead, because {feature.name} was too fascinating to ignore.")


def grab_hand(world: World, parent: Entity, hero: Entity, feature: Feature) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1
    propagate(world, narrate=False)
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} held {hero.pronoun('possessive')} hand and spoke softly.")
    world.say(f'"We can keep the fun and still keep your {hero.facts if False else "look"} neat," {parent.label} said.')


def compromise(world: World, parent: Entity, hero: Entity, feature: Feature, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(feature, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, feature, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.label.capitalize()} smiled and said, \"How about we {gear_def.prep} first?\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, feature: Feature, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["fascinate"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} nodded, then hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(f'They {gear_def.tail}. Soon {hero.id} was {feature.gerund}, and {prize.label} stayed clean.')
    world.say(f"In the end, the ghost's {feature.name} turned into a gentle {feature.twist} instead of a fright.")


def tell(setting: Setting, feature: Feature, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.id, label=prize_cfg.label,
                              phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                              region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves_feature(world, hero, feature)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, feature)
    wants(world, hero, feature)
    warn(world, parent, hero, feature, prize)
    defies(world, hero, feature)
    grab_hand(world, parent, hero, feature)

    world.para()
    gear_def = compromise(world, parent, hero, feature, prize)
    if gear_def:
        accept(world, parent, hero, feature, prize, gear_def)
    world.facts.update(hero=hero, parent=parent, ghost=ghost, prize=prize, feature=feature,
                       gear=gear_def, setting=setting, conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "parlor": Setting(place="the old parlor", indoor=True, affords={"magic", "rhyme", "twist"}),
    "attic": Setting(place="the attic", indoor=True, affords={"magic", "rhyme", "twist"}),
    "hall": Setting(place="the moonlit hall", indoor=True, affords={"magic", "rhyme", "twist"}),
}

FEATURES = {
    "magic": Feature(
        id="magic", name="magic tricks", verb="do the magic trick", gerund="doing magic tricks",
        rush="reach for the wand", risk="dust", twist="magic twist", zone={"torso", "hands"},
        keyword="magic", tags={"magic"},
    ),
    "rhyme": Feature(
        id="rhyme", name="a rhyme", verb="say the rhyme", gerund="saying rhymes",
        rush="start the rhyme too loudly", risk="dust", twist="rhyme twist", zone={"mouth", "torso"},
        keyword="rhyme", tags={"rhyme"},
    ),
    "twist": Feature(
        id="twist", name="a twist dance", verb="do the twist", gerund="twisting and twirling",
        rush="spin across the floor", risk="dust", twist="twist finish", zone={"feet", "torso"},
        keyword="twist", tags={"twist"},
    ),
}

PRIZES = {
    "bun": Prize(id="bun", label="bun", phrase="a neat ribboned bun", region="head"),
    "facial": Prize(id="facial", label="facial mask", phrase="a soft facial mask", region="face"),
}

GEARS = [
    Gear(id="cap", label="a tiny night cap", covers={"head"}, guards={"dust"}, prep="put on a tiny night cap", tail="walked back into the parlor with the cap on"),
    Gear(id="veil", label="a soft veil", covers={"face"}, guards={"dust"}, prep="wear a soft veil", tail="went back in wearing the soft veil"),
]

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ruby", "Pia"]
BOY_NAMES = ["Eli", "Finn", "Noah", "Theo", "Milo"]
TRAITS = ["curious", "brave", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for feat_id in setting.affords:
            feat = FEATURES[feat_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(feat, prize) and select_gear(feat, prize):
                    combos.append((place, feat_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    feature: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What is magic?", "Magic is a pretend or stage trick that can look surprising and fun.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a word pattern where sounds at the ends of words match.")],
    "twist": [("What is a twist dance?", "A twist dance is a dance where you turn your hips and feet in a funny, quick way.")],
    "dust": [("What is dust?", "Dust is tiny bits of dirt that can gather on shelves, floors, and old things.")],
    "bun": [("What is a bun?", "A bun is hair twisted and pinned into a round shape on the back or top of the head.")],
    "facial": [("What is a facial mask?", "A facial mask is something you put on your face for care, usually softly and for a short time.")],
}

KNOWLEDGE_ORDER = ["magic", "rhyme", "twist", "dust", "bun", "facial"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, feat, prize = f["hero"], f["parent"], f["feature"], f["prize"]
    return [
        f'Write a short ghost story for a young child about "{feat.keyword}", "{prize.label}", and a kind surprise.',
        f"Tell a spooky-but-gentle story where {hero.id} wants to {feat.verb} while wearing {prize.phrase}, but {parent.label} worries.",
        f'Write a calm haunted-house story that includes a neat bun, a facial mask, and the word "{feat.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, feat, prize = f["hero"], f["parent"], f["feature"], f["prize"]
    trait = next((t for t in hero.memes.keys() if False), "curious")
    qa = [
        QAItem(
            question=f"Who was fascinated by {feat.name} in the story?",
            answer=f"{hero.id} was fascinated by {feat.name}, and that is why the night felt exciting at first.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because if {hero.id} did the {feat.id} activity, the {prize.label} would get dusty.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep playing without ruining the {prize.label}?",
            answer=f"They used {f['gear'].label if f.get('gear') else 'a safer plan'}, so {hero.id} could stay neat and still enjoy the spooky fun.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end after the twist?",
            answer=f"It ended with {hero.id} calm and happy, while the ghost's spooky idea turned into a gentler {feat.twist}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["feature"].tags)
    if world.facts.get("gear"):
        tags.add("dust")
    tags.add(world.facts["prize"].id)
    out: list[QAItem] = []
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(feature: Feature, prize: Prize) -> str:
    if not prize_at_risk(feature, prize):
        return f"(No story: {feature.name} does not threaten the {prize.label} in this world.)"
    return f"(No story: the gear catalog has no reasonable way to protect the {prize.label} from {feature.name}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this world does not use a gender restriction for {PRIZES[prize_id].label}; got {gender}.)"


ASP_RULES = r"""
prize_at_risk(F, P) :- zone(F, R), worn_on(P, R).
protects(G, F, P) :- gear(G), prize_at_risk(F, P), guards(G, M), risk_of(F, M), covers(G, R), worn_on(P, R).
has_fix(F, P) :- protects(_, F, P).
valid(Place, F, P) :- affords(Place, F), prize_at_risk(F, P), has_fix(F, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for feat in sorted(s.affords):
            lines.append(asp.fact("affords", pid, feat))
    for fid, f in FEATURES.items():
        lines.append(asp.fact("feature", fid))
        lines.append(asp.fact("risk_of", fid, f.risk))
        for r in sorted(f.zone):
            lines.append(asp.fact("zone", fid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for g in GEARS:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world with a bun, a facial mask, and a magic-rhyme twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--feature", choices=FEATURES)
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
    if args.feature and args.prize:
        feat, prize = FEATURES[args.feature], PRIZES[args.prize]
        if not (prize_at_risk(feat, prize) and select_gear(feat, prize)):
            raise StoryError(explain_rejection(feat, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.feature is None or c[1] == args.feature)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, feature, prize = rng.choice(sorted(combos))
    gender = args.gender or "girl"
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, feature=feature, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], FEATURES[params.feature], PRIZES[params.prize], params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="parlor", feature="magic", prize="bun", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="attic", feature="rhyme", prize="facial", name="Luna", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="hall", feature="twist", prize="bun", name="Eli", gender="boy", parent="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, feature, prize) combos:\n")
        for place, feat, prize in combos:
            print(f"  {place:8} {feat:8} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.feature} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
