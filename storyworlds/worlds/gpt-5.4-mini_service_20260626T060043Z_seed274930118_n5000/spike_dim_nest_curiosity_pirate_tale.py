#!/usr/bin/env python3
"""
storyworlds/worlds/spike_dim_nest_curiosity_pirate_tale.py
===========================================================

A small pirate-tale storyworld about curiosity, a dim spiky nest, and a safe
way to look closer.

The seed image:
---
A curious young pirate on a small ship notices a strange spike-dim nest tucked
in a cave by the shore. The child wants to poke it open, but the captain knows
the nest might scratch hands and spill something sharp. After a warning and a
brief tug-of-war with curiosity, they choose a safer way: lantern light, thick
gloves, and a careful look together. The curious pirate gets the wonder without
the wound.
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
        for k in ["scratched", "risk", "dark", "care"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "joy", "worry", "conflict", "trust", "bravery", "grabbed_by"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "boy pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"captain": "captain", "pirate": "pirate"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the cove"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
    mood: str = "curious"
    keyword: str = "curiosity"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_hazard(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("hazard", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scratched"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got scratched by the spike-dim nest.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["scratched"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would make more work for {carer.label}.")
    return out


RULES = [_r_hazard, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_delight(action: Action) -> str:
    return "the mystery made the dark cave feel like a secret waiting to be found"


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} lay quiet, with salt in the air and shadows under the rocks."


def prize_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and action.hazard in gear.guards:
            return gear
    return None


def predict_harm(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.get(prize_id)
    return {"scratched": prize.meters["scratched"] >= THRESHOLD}


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        raise StoryError(f"Action '{action.id}' does not fit this setting.")
    world.zone = set(action.zone)
    actor.meters["risk"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} pirate with bright eyes and a nose for secrets.")


def loves_curiosity(world: World, hero: Entity, action: Action) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund}; {activity_delight(action)}.")


def finds_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["trust"] += 1
    world.say(f"One evening, {hero.id} found {hero.pronoun('possessive')} {prize.label} and held {prize.it()} close.")


def arrives(world: World, hero: Entity, captain: Entity, action: Action) -> None:
    world.say(f"One moonlit night, {hero.id} and {hero.pronoun('possessive')} {captain.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, captain: Entity, action: Action) -> None:
    world.say(f"{hero.id} wanted to {action.verb} right away, but {hero.pronoun('possessive')} {captain.label_word} lifted a careful hand.")


def warn(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_harm(world, hero, action, prize.id)
    if not pred["scratched"]:
        return False
    captain.memes["worry"] += 1
    world.say(f"'{hero.id}, you'll get your {prize.label} {action.hazard},' {hero.pronoun('possessive')} {captain.label_word} said.")
    world.say("'Let's look first and touch later.'")
    return True


def defy(world: World, hero: Entity, action: Action) -> None:
    hero.memes["bravery"] += 1
    world.say(f"{hero.id} tried to {action.rush}, even though curiosity was tugging hard.")


def grab(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    hero.memes["conflict"] += 1
    world.say(f"Then {hero.pronoun('possessive')} {captain.label_word} caught {hero.pronoun('possessive')} hand and held it still.")


def compromise(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(action, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=captain.id,
    ))
    gear.worn_by = hero.id
    if predict_harm(world, hero, action, prize.id)["scratched"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {captain.label_word} smiled. '{gear_def.prep} first,' {hero.pronoun('possessive')} {captain.label_word} said.")
    return gear_def


def accept(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} nodded, put on the gear, and grinned so wide the moonlight seemed to shine on {hero.pronoun('possessive')} cheeks.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {action.gerund}, {prize.label} stayed safe, and the spike-dim nest gave up its secret without a scratch.")
    world.say(f"{hero.id} carried the wonder back to the ship, happier for having looked with care.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str = "Mira", hero_type: str = "girl", parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious", "stubborn"]))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_curiosity(world, hero, action)
    finds_prize(world, hero, prize)

    world.para()
    arrives(world, hero, captain, action)
    wants(world, hero, captain, action)
    warn(world, captain, hero, action, prize)
    defy(world, hero, action)
    grab(world, captain, hero)

    world.para()
    gear_def = compromise(world, captain, hero, action, prize)
    if gear_def:
        accept(world, captain, hero, action, prize, gear_def)

    world.facts.update(hero=hero, captain=captain, prize=prize, action=action, gear=gear_def, setting=setting)
    return world


SETTINGS = {
    "cove": Setting(place="the cove", affords={"peek"}),
    "cave": Setting(place="the shore cave", affords={"peek"}),
    "deck": Setting(place="the ship's deck", affords={"peek"}),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="poke open the nest",
        gerund="peeking into nests",
        rush="rush to poke the nest open",
        hazard="spike-dim",
        zone={"hands", "face"},
        keyword="curiosity",
        tags={"curiosity", "nest"},
    )
}

PRIZES = {
    "shell": Prize(label="shell pouch", phrase="a shell pouch", type="pouch", region="hands"),
    "map": Prize(label="map case", phrase="a little map case", type="case", region="hands"),
    "lantern": Prize(label="lantern strap", phrase="a lantern strap", type="strap", region="hands"),
}

GEAR = [
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"hands"},
        guards={"spike-dim"},
        prep="put on thick gloves",
        tail="walked back to the nest with their gloves on",
    ),
    Gear(
        id="veil",
        label="a lantern veil",
        covers={"face"},
        guards={"spike-dim"},
        prep="hold the lantern veil over the light",
        tail="carried the lantern veil back to the cave",
    ),
]

GIRL_NAMES = ["Mira", "Tess", "Luna", "Pia", "Ruby", "Nell"]
BOY_NAMES = ["Finn", "Oren", "Jack", "Bram", "Nico", "Kai"]
TRAITS = ["curious", "bold", "quick-eyed", "cheerful"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            action = ACTIONS[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_risk(action, prize) and select_gear(action, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return f"(No story: {action.verb} would not risk the {prize.label} in a way this world can fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale story world about curiosity and a spike-dim nest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    if args.action and args.prize:
        act, pr = ACTIONS[args.action], PRIZES[args.prize]
        if not (prize_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["action"], f["prize"]
    return [
        f'Write a short pirate story for a young child about "{act.keyword}" and a {prize.label}.',
        f"Tell a gentle tale where a curious little pirate named {hero.id} wants to {act.verb} but learns to be careful.",
        f"Write a story about a {hero.type} pirate, a dim spiky nest, and a safer way to look at it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action = f["hero"], f["captain"], f["prize"], f["action"]
    qa = [
        QAItem(
            question=f"Who wanted to {action.verb} in the story?",
            answer=f"{hero.id} wanted to {action.verb}, because {hero.pronoun('subject')} was very curious about the spike-dim nest.",
        ),
        QAItem(
            question=f"Why did the {captain.label_word} worry about the {prize.label}?",
            answer=f"The {captain.label_word} worried because the nest was spike-dim and could scratch {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} look at the nest safely?",
            answer=f"Thick gloves helped {hero.id} look safely, so {hero.pronoun('subject')} could be curious without getting hurt.",
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question=f"How did the pirate tale end?",
            answer=f"It ended with {hero.id} using careful gear, learning from the warning, and seeing the nest without a scratch.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes someone want to know more and look closely."),
        QAItem(question="Why wear gloves?", answer="Gloves help protect hands from scratches, dirt, and sharp things."),
        QAItem(question="What is a nest?", answer="A nest is a place where birds or other creatures keep eggs or small things safe."),
        QAItem(question="What does dim mean?", answer="Dim means not very bright, so it is hard to see clearly."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), worn_on(P,R), splashes(A,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), hazard(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("hazard", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="cave", action="peek", prize="shell", name="Mira", gender="girl", parent="captain", trait="curious"),
    StoryParams(place="cove", action="peek", prize="map", name="Finn", gender="boy", parent="captain", trait="bold"),
    StoryParams(place="deck", action="peek", prize="lantern", name="Tess", gender="girl", parent="captain", trait="quick-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
