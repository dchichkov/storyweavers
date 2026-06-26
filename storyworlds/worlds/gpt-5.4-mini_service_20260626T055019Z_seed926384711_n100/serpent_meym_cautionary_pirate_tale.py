#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/serpent_meym_cautionary_pirate_tale.py
===============================================================================================================

A small cautionary pirate tale world built from the seed words "serpent" and
"Meym".  The domain is intentionally tiny: a young pirate crew, a risky treasure
chest, a sea-serpent warning, and a safe choice that avoids trouble.

The story engine models physical meters and emotional memes.  The tale is not a
frozen paragraph; it is driven by state changes: a warning, temptation, danger,
and a resolution that leaves the crew wiser.

This script follows the Storyweavers world contract:
- standalone stdlib script
- imports shared results eagerly
- imports ASP lazily inside helper functions
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
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
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
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
        self.zone: set[str] = set()
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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"chest", "lantern", "map"}),
    "deck": Setting(place="the deck", affords={"chest", "lantern", "map"}),
    "cove": Setting(place="the cove", affords={"chest", "lantern"}),
}

RISKS = {
    "chest": Risk(
        id="chest",
        verb="open the captain's chest",
        gerund="opening the captain's chest",
        rush="run to the chest",
        danger="might wake the serpent",
        zone={"torso", "hands"},
        keyword="chest",
        tags={"chest", "treasure", "serpent"},
    ),
    "lantern": Risk(
        id="lantern",
        verb="light the lantern near the rope pile",
        gerund="lighting a lantern near the rope pile",
        rush="rush to the lantern",
        danger="might burn the sailcloth",
        zone={"hands", "torso"},
        keyword="lantern",
        tags={"lantern", "fire"},
    ),
    "map": Risk(
        id="map",
        verb="follow the torn map into the cave",
        gerund="following the torn map",
        rush="dash toward the cave",
        danger="might lead them to a bad reef",
        zone={"feet"},
        keyword="map",
        tags={"map", "reef"},
    ),
}

PRIZES = {
    "pearl": Prize(
        label="pearl",
        phrase="a bright pearl in a brass shell",
        type="pearl",
        region="hands",
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a wind-tossed captain's cloak",
        type="cloak",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="a pair of black sea boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"hands"},
        guards={"serpent", "fire"},
        prep="put on thick gloves first",
        tail="went back for the thick gloves",
        plural=True,
    ),
    Gear(
        id="cloak",
        label="a canvas cloak",
        covers={"torso"},
        guards={"fire", "serpent"},
        prep="wrap up in a canvas cloak first",
        tail="came back with the canvas cloak",
    ),
    Gear(
        id="boots",
        label="sea boots",
        covers={"feet"},
        guards={"reef"},
        prep="lace on sea boots first",
        tail="returned with the sea boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Meym", "Nina", "Ivy", "Lina"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Tomas"]
TRAITS = ["brave", "curious", "stubborn", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(R, P) :- risk(R), prize(P), zone(R, Z), worn_on(P, Z).
protects(G, R, P) :- gear(G), prize_at_risk(R, P), guards(G, D), danger_of(R, D), covers(G, Z), worn_on(P, Z).
has_fix(R, P) :- protects(_, R, P).
valid(Place, R, P) :- setting(Place), affords(Place, R), prize_at_risk(R, P), has_fix(R, P).
valid_story(Place, R, P, Gender) :- valid(Place, R, P), wears(Gender, P).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("danger_of", rid, r.danger))
        for z in sorted(r.zone):
            lines.append(asp.fact("zone", rid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
        for z in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, z))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.\n") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python gate.")
        return 0
    print("MISMATCH: ASP gate does not match Python gate.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def risk_at_prize(risk: Risk, prize: Prize) -> bool:
    return prize.region in risk.zone


def select_gear(risk: Risk, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if risk.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for rid in setting.affords:
            risk = RISKS[rid]
            for pid, prize in PRIZES.items():
                if risk_at_prize(risk, prize) and select_gear(risk, prize):
                    out.append((place, rid, pid))
    return out


def explain_rejection(risk: Risk, prize: Prize) -> str:
    if not risk_at_prize(risk, prize):
        return (
            f"(No story: {risk.gerund} does not threaten {prize.label} in a "
            f"way the pirate captain would warn about.)"
        )
    return (
        f"(No story: there is no sensible gear in this world that protects "
        f"{prize.label} from {risk.keyword}. The cautionary turn would be fake.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def predict_mess(world: World, risk: Risk, prize_id: str) -> dict:
    sim = world.copy()
    do_risk(sim, sim.get(sim.facts["hero"].id), risk, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("warned", 0.0) >= THRESHOLD}


def do_risk(world: World, actor: Entity, risk: Risk, narrate: bool = True) -> None:
    if risk.id not in world.setting.affords:
        return
    world.zone = set(risk.zone)
    actor.memes["temptation"] = actor.memes.get("temptation", 0.0) + 1
    actor.meters[risk.id] = actor.meters.get(risk.id, 0.0) + 1
    if narrate:
        world.say(f"{actor.id} went to {risk.gerund}, and the deck felt suddenly too quiet.")


def propagate(world: World) -> None:
    # minimal hazard propagation for the cautionary tale
    for actor in world.characters():
        if actor.meters.get("chest", 0.0) >= THRESHOLD and actor.memes.get("reckless", 0.0) >= THRESHOLD:
            key = ("warning", actor.id)
            if key not in world.fired:
                world.fired.add(key)
                world.say("A warning crackled through the air: the serpent in the dark could wake up.")


def tell(setting: Setting, risk: Risk, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"curious": 1.0}))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts.update(hero=hero, parent=parent, prize=prize, risk=risk, setting=setting)

    world.say(f"{hero.id} was a little {trait} pirate who sailed with {parent.label}.")
    world.say(f"{hero.id} loved the sound of waves, gulls, and the word serpent, because it made the story feel bold.")
    world.say(f"One day, {parent.label} gave {hero.id} {prize.phrase} and said to keep it safe.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} saw a dark chest tucked near the mast.")
    world.say(f"{hero.id} wanted to {risk.verb}, but {parent.label} frowned and pointed at the shadow under the boards.")
    world.say(f'"That shadow could hide a serpent," {parent.label} warned. "If you rush, {risk.danger}."')

    hero.memes["reckless"] = 1.0
    if predict_mess(world, risk, prize.id)["soiled"]:
        world.say(f"{hero.id} felt the urge to hurry anyway, but the warning made {hero.id} slow down.")

    world.para()
    gear = select_gear(risk, prize)
    if gear is None:
        raise StoryError(explain_rejection(risk, prize))
    safe_gear = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    safe_gear.worn_by = hero.id
    world.say(f"{parent.label} smiled and said, \"{gear.prep}. Then we can do it the safe way.\"")
    world.say(f"{hero.id} listened, and together they {gear.tail}.")

    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    hero.memes["reckless"] = 0.0
    world.say(f"So {hero.id} chose to leave the chest alone and keep {prize.label} out of danger.")
    world.say(f"In the end, the deck stayed calm, the serpent stayed sleeping, and {hero.id} learned that a pirate can be brave without being careless.")
    return world


# ---------------------------------------------------------------------------
# Registries / params / QA
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    risk: str
    prize: str
    name: str
    gender: str
    parent: str = "captain"
    trait: str = "curious"
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="deck", risk="chest", prize="cloak", name="Meym", gender="girl", trait="curious"),
    StoryParams(place="harbor", risk="map", prize="boots", name="Finn", gender="boy", trait="brave"),
    StoryParams(place="cove", risk="lantern", prize="pearl", name="Meym", gender="girl", trait="bright"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short cautionary pirate tale for a young child that includes the word "{f["risk"].keyword}".',
        f"Tell a pirate story where {f['hero'].id} wants to {f['risk'].verb} but listens to the captain instead.",
        f'Write a sea story about a serpent, a warning, and a safer choice at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, risk = f["hero"], f["parent"], f["prize"], f["risk"]
    return [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It is about {hero.id}, a little pirate who sails with {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {risk.verb}, but that was too risky because it could wake the serpent.",
        ),
        QAItem(
            question=f"How did the captain help {hero.id} make a safer choice?",
            answer=f"The captain offered a safer plan with {select_gear(risk, prize).label}, so {hero.id} could slow down and avoid trouble.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"{hero.id} chose caution instead of rushing, the chest stayed closed, and the serpent stayed asleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a serpent?",
            answer="A serpent is a snake, and some serpents can seem spooky in a pirate tale.",
        ),
        QAItem(
            question="Why do pirates use a lookout?",
            answer="Pirates use a lookout to spot danger early, like rocks, storms, or something hiding in the waves.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting so you can avoid trouble.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary pirate tale world with a serpent and Meym.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["captain"], default="captain")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.risk and args.prize:
        risk, prize = RISKS[args.risk], PRIZES[args.prize]
        if not (risk_at_prize(risk, prize) and select_gear(risk, prize)):
            raise StoryError(explain_rejection(risk, prize))
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and (args.risk is None or c[1] == args.risk)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, risk_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, risk=risk_id, prize=prize_id, name=name, gender=gender, parent="captain", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RISKS[params.risk], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, risk, prize in triples:
            genders = sorted(g for (pl, r, p, g) in stories if (pl, r, p) == (place, risk, prize))
            print(f"  {place:8} {risk:8} {prize:8} [{', '.join(genders)}]")
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
            params = resolve_params(args, random.Random(seed))
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
