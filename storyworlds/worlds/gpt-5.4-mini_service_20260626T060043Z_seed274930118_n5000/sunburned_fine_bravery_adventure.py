#!/usr/bin/env python3
"""
storyworlds/worlds/sunburned_fine_bravery_adventure.py
======================================================

A small story world about a brave child, a bright outdoor adventure, and a
gentle compromise that keeps the day safe.

Premise:
- A child wants to go on a bold adventure outside.
- The sun is strong enough to make skin sunburned.
- The caregiver worries, because bravery should still be fine and wise.
- The compromise is to use sun-safe gear so the adventure can continue.

This world is intentionally tiny and constraint-checked: only compatible
adventures, places, and protective gear combinations are generated.
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        for k in ["sun", "tired", "sweat", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "bravery", "worry", "confidence", "fear", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    outdoors: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    sun: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "bright"

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.weather = self.weather
        return w


def _r_sun(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["sun"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region != "skin" or world.covered(actor, "skin"):
                continue
            sig = ("sunburn", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["sweat"] += 1
            actor.memes["tired"] += 0.5
            out.append(f"The sun made {actor.id} feel hot and tired.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["sun"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] += 1
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["bravery"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("brave_worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 0.5
        out.append("__tension__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_sun, _r_worry, _r_bravery):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__tension__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def at_risk(adventure: Adventure, prize: Entity) -> bool:
    return prize.region in {"skin"} and adventure.sun >= 1.0


def select_gear(adventure: Adventure, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if "sun" in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, adv: Adventure, prize_id: str) -> dict:
    sim = world.copy()
    _do_adventure(sim, sim.get(hero.id), adv, narrate=False)
    prize = sim.entities[prize_id]
    return {"sunburned": prize.meters["sun"] >= THRESHOLD}


def _do_adventure(world: World, actor: Entity, adv: Adventure, narrate: bool = True) -> None:
    if adv.id not in world.place.affordances:
        raise StoryError("This place cannot host that adventure.")
    actor.meters["sun"] += adv.sun
    actor.memes["joy"] += 1
    actor.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked to go first and look ahead."
    )


def loves_adventure(world: World, hero: Entity, adv: Adventure) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {adv.gerund}; it made the whole day feel like a quest."
    )


def finds_item(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["pride"] += 1
    prize.worn_by = hero.id
    world.say(
        f"One morning, {hero.id} found {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly."
    )


def arrive(world: World, hero: Entity, caretaker: Entity, adv: Adventure) -> None:
    world.say(
        f"At {world.place.label}, {hero.id} and {hero.pronoun('possessive')} {caretaker.label} "
        f"went on a bright path where {adv.verb} sounded exciting."
    )
    world.say("The air was warm, and the sun shone hard from above.")

def wants(world: World, hero: Entity, caretaker: Entity, adv: Adventure) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} wanted to {adv.verb} right away, because bravery made {hero.pronoun('object')} feel strong."
    )


def warn(world: World, caretaker: Entity, hero: Entity, adv: Adventure, prize: Entity) -> bool:
    pred = predict(world, hero, adv, prize.id)
    if not pred["sunburned"]:
        return False
    caretaker.memes["worry"] += 1
    world.facts["predicted_sunburned"] = True
    world.say(
        f"'{hero.id}, the sun is too strong for that,' {caretaker.label} said. "
        f"'I don't want {hero.pronoun('object')} getting sunburned.'"
    )
    return True


def defies(world: World, hero: Entity, adv: Adventure) -> None:
    hero.memes["fear"] += 0.25
    world.say(
        f"{hero.id} heard the warning, but {hero.pronoun('possessive')} brave heart still pulled toward the adventure."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {adv.rush}.")


def hold_back(world: World, caretaker: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"But {hero.pronoun('possessive')} {caretaker.label} held up a calm hand and asked {hero.pronoun('object')} to pause."
    )


def compromise(world: World, caretaker: Entity, hero: Entity, adv: Adventure, prize: Entity) -> Optional[Gear]:
    gear = select_gear(adv, prize)
    if gear is None:
        return None
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    if predict(world, hero, adv, prize.id)["sunburned"]:
        del world.entities[item.id]
        return None
    world.say(
        f"{caretaker.label} smiled and said, 'How about we put on {gear.phrase} first, and then go?'"
    )
    return gear


def accept(world: World, caretaker: Entity, hero: Entity, adv: Adventure, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} nodded and hugged {hero.pronoun('possessive')} {caretaker.label}."
    )
    world.say(
        f"Soon they {gear.tail}, and {hero.id} kept {hero.pronoun('possessive')} {prize.label} fine while the adventure continued."
    )


def tell(place: Place, adv: Adventure, prize_cfg: "PrizeCfg",
         hero_name: str = "Ari", hero_type: str = "boy",
         parent_type: str = "mother", trait: str = "brave") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=caretaker.id, region=prize_cfg.region
    ))

    introduce(world, hero)
    loves_adventure(world, hero, adv)
    finds_item(world, hero, prize)

    world.para()
    arrive(world, hero, caretaker, adv)
    wants(world, hero, caretaker, adv)
    warn(world, caretaker, hero, adv, prize)
    defies(world, hero, adv)
    hold_back(world, caretaker, hero)

    world.para()
    gear = compromise(world, caretaker, hero, adv, prize)
    if gear:
        accept(world, caretaker, hero, adv, prize, gear)

    world.facts.update(hero=hero, caretaker=caretaker, prize=prize, adventure=adv, gear=gear, place=place)
    return world


@dataclass
class PrizeCfg:
    label: str
    phrase: str
    type: str
    region: str


PLACES = {
    "trail": Place("trail", "the sunlit trail", True, {"treasure_hunt", "climb"}),
    "beach": Place("beach", "the beach", True, {"treasure_hunt", "build"}),
    "garden": Place("garden", "the garden", True, {"treasure_hunt", "explore"}),
}

ADVENTURES = {
    "treasure_hunt": Adventure(
        id="treasure_hunt", verb="search for treasure", gerund="searching for treasure",
        rush="dash down the trail", danger="the sun", sun=1.0, tags={"sun", "quest"}
    ),
    "explore": Adventure(
        id="explore", verb="explore the ridge", gerund="exploring the ridge",
        rush="run toward the ridge path", danger="the bright sun", sun=1.0, tags={"sun", "quest"}
    ),
    "climb": Adventure(
        id="climb", verb="climb the hill", gerund="climbing the hill",
        rush="scramble up the rocks", danger="the hot sky", sun=1.0, tags={"sun", "quest"}
    ),
}

PRIZES = {
    "shirt": PrizeCfg("shirt", "a light shirt", "shirt", "skin"),
    "hat": PrizeCfg("hat", "a favorite hat", "hat", "skin"),
}

GEAR = [
    Gear("sunscreen", "sunscreen", "sunscreen on their skin", {"skin"}, {"sun"}, "put sunscreen on", "headed out again"),
    Gear("hat", "wide-brim hat", "a wide-brim hat", {"skin"}, {"sun"}, "put on a wide-brim hat", "set off along the trail"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, pl in PLACES.items():
        for adv_id in pl.affordances:
            adv = ADVENTURES[adv_id]
            for prize_id, pr in PRIZES.items():
                if at_risk(adv, Entity(id="x", type=pr.type, label=pr.label, region=pr.region)) and select_gear(adv, Entity(id="x", type=pr.type, label=pr.label, region=pr.region)):
                    combos.append((place, adv_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    adventure: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Ava", "Lina", "Nora"]
BOY_NAMES = ["Ari", "Leo", "Sam", "Theo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, adv, prize = f["hero"], f["adventure"], f["prize"]
    return [
        f'Write a short adventure story for a young child that includes the word "sunburned".',
        f"Tell a brave story where {hero.id} wants to {adv.verb} but needs help keeping {hero.pronoun('possessive')} {prize.label} fine.",
        f'Write a simple quest story about a child who must stay safe in the sun and end with a good compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, prize, adv = f["hero"], f["caretaker"], f["prize"], f["adventure"]
    qa = [
        QAItem(
            question=f"Who wanted to {adv.verb} in the story?",
            answer=f"{hero.id} wanted to {adv.verb} because {hero.pronoun('possessive')} brave heart was full of adventure."
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about {hero.id} going out?",
            answer=f"{caretaker.label.capitalize()} worried because the sun was bright and {hero.id} could get sunburned."
        ),
        QAItem(
            question=f"What did the family do so the adventure could stay safe?",
            answer=f"They used protective gear so {hero.id} could keep going while {hero.pronoun('possessive')} {prize.label} stayed fine."
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id}?",
            answer=f"{gear.label.capitalize()} helped by covering the skin from the sun, so the day could stay safe and brave."
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud, because bravery and safety worked together on the adventure."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sunburn?",
            answer="Sunburn is what can happen when skin stays in strong sunlight too long and gets red and sore."
        ),
        QAItem(
            question="Why do people wear hats in the sun?",
            answer="People wear hats in the sun to help shade their faces and keep the hot light off their skin."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little scary, while still making smart choices."
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("trail", "treasure_hunt", "shirt", "Ari", "boy", "mother", "brave"),
    StoryParams("beach", "explore", "hat", "Mia", "girl", "father", "curious"),
]


def explain_rejection(adv: Adventure, prize: Entity) -> str:
    return f"(No story: this adventure would not realistically put the {prize.label} at risk.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {prize_id} is not a good match for gender {gender} in this tiny world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A brave sunlit adventure story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
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
    if args.adventure and args.prize:
        adv = ADVENTURES[args.adventure]
        pr = Entity(id="x", type=PRIZES[args.prize].type, label=PRIZES[args.prize].label, region=PRIZES[args.prize].region)
        if not (at_risk(adv, pr) and select_gear(adv, pr)):
            raise StoryError(explain_rejection(adv, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.adventure is None or c[1] == args.adventure)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, adv, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = "brave"
    return StoryParams(place, adv, prize, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ADVENTURES[params.adventure], PRIZES[params.prize], params.name, "girl" if params.gender == "girl" else "boy", params.parent, params.trait)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- sun_adventure(A), worn_on(P,skin).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,sun), covers(G,skin).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("sun_adventure", aid))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
