#!/usr/bin/env python3
"""
Calf Cautionary Pirate Tale
===========================

A small, self-contained story world about a calf aboard a pirate ship.

The story pattern is cautionary: the calf wants to do something risky on a
pirate ship, the crew warns it, a bad outcome is predicted, and a safe choice
prevents trouble. The prose stays grounded in the world model: ropes, decks,
waves, lanterns, sacks, and the calf's feelings and physical state.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven narrative
- natural-language Q&A
- inline ASP twin plus Python reasonableness gate
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    dangerous: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)
        for k in ("wet", "scared", "muddy", "work", "damage", "joy", "worry", "brave", "love"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"calf"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "cow", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    place: str = "the deck"
    sky: str = "stormy"
    sea: str = "rough"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"any"})


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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "deck": Ship(place="the deck", sky="stormy", sea="rough", affords={"rope", "chest", "lantern"}),
    "harbor": Ship(place="the harbor dock", sky="windy", sea="swishy", affords={"rope", "crate", "lantern"}),
    "cove": Ship(place="the cove", sky="gray", sea="bouncy", affords={"rope", "shell", "lantern"}),
}

ACTIONS = {
    "rope": Action(
        id="rope",
        verb="climb the rope ladder",
        gerund="climbing the rope ladder",
        rush="dash up the rope ladder",
        risk="fall into the sea",
        zone={"feet", "hands"},
        weather="stormy",
        keyword="rope",
        tags={"rope", "ship"},
    ),
    "chest": Action(
        id="chest",
        verb="open the captain's chest",
        gerund="prying at the chest latch",
        rush="snatch at the chest latch",
        risk="get pinched by the lid",
        zone={"hands"},
        weather="stormy",
        keyword="chest",
        tags={"chest", "ship"},
    ),
    "lantern": Action(
        id="lantern",
        verb="carry the lantern near the sails",
        gerund="swinging the lantern near the sails",
        rush="run under the sails with the lantern",
        risk="start a fire",
        zone={"hands", "torso"},
        weather="windy",
        keyword="lantern",
        tags={"lantern", "ship"},
    ),
    "crate": Action(
        id="crate",
        verb="kick the crate open",
        gerund="kicking the crate open",
        rush="jump at the crate",
        risk="bruise a hoof",
        zone={"feet"},
        weather="windy",
        keyword="crate",
        tags={"crate", "ship"},
    ),
    "shell": Action(
        id="shell",
        verb="pick up the shell pile",
        gerund="picking through shell piles",
        rush="scramble for the shells",
        risk="scrape a hoof on the rocks",
        zone={"feet"},
        weather="gray",
        keyword="shell",
        tags={"shell", "shore"},
    ),
}

PRIZES = {
    "sailcloth": Prize("sailcloth", "a clean sailcloth wrap", "sailcloth", "torso"),
    "hoofboots": Prize("hoofboots", "little red hoofboots", "hoofboots", "feet", plural=True),
    "bell": Prize("bell", "a shiny brass bell", "bell", "neck"),
    "hat": Prize("hat", "a tiny captain's hat", "hat", "head"),
}

GEAR = [
    Gear("boots", "the hoofboots", {"feet"}, {"wet"}, "put on the hoofboots first", "put on the hoofboots"),
    Gear("wrap", "the sailcloth wrap", {"torso"}, {"wet"}, "wrap the sailcloth around the calf", "wrapped up the sailcloth"),
    Gear("helmet", "the little captain's hat", {"head"}, {"fall"}, "set the little captain's hat on the calf", "settled the little hat"),
]

CALF_NAMES = ["Moo", "Clover", "Pip", "Nell", "Bram", "Tilly"]
HELPERS = ["mother cow", "old sailor", "kind deckhand"]
TRAITS = ["curious", "spry", "stubborn", "cheerful", "brave"]


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone or (prize.region == "torso" and action.id == "lantern")


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and any(g in gear.guards for g in {"wet", "fall"}):
            if action.id == "rope" and "feet" in gear.covers:
                return gear
            if action.id == "lantern" and "torso" in gear.covers:
                return gear
            if action.id == "chest" and "head" in gear.covers:
                return gear
            if action.id in {"crate", "shell"} and "feet" in gear.covers:
                return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, ship in SETTINGS.items():
        for act_id in ship.affords:
            act = ACTIONS[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_world(params: StoryParams) -> World:
    ship = SETTINGS[params.place]
    world = World(ship)
    hero = world.add(Entity(id=params.name, kind="character", type="calf", traits=["little", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    prize = world.add(Entity(id="Prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, caretaker=helper.id))
    prize.worn_by = hero.id
    prize.region = PRIZES[params.prize].region  # dynamic attribute
    world.facts.update(hero=hero, helper=helper, prize=prize, params=params, action=ACTIONS[params.activity], ship=ship)
    return world


def predict_bad_end(world: World, hero: Entity, action: Action, prize: Entity) -> dict:
    sim = world.copy()
    do_action(sim, sim.get(hero.id), action, narrate=False)
    pr = sim.get("Prize")
    return {"soiled": pr.meters["wet"] >= THRESHOLD or pr.meters["damage"] >= THRESHOLD}


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.ship.affords:
        raise StoryError("That action does not fit this ship setting.")
    actor.meters["wet"] += 1
    actor.memes["joy"] += 1
    world.zone = set(action.zone)
    if narrate:
        world.say(f"{actor.id} tried to {action.verb}, and the deck shivered under {actor.pronoun('possessive')} hooves.")


def _soak_rule(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.id != "Prize":
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and rough.")
    return out


CAUSAL_RULES = [_soak_rule]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    msgs: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                msgs.extend(got)
    if narrate:
        for s in msgs:
            world.say(s)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.name)
    helper = world.get("Helper")
    prize = world.get("Prize")
    action = ACTIONS[params.activity]

    world.say(f"{hero.id} was a little {params.trait} calf who lived for pirate decks and salty wind.")
    world.say(f"{hero.id} loved {action.gerund}, and the creaky ship made every step feel like an adventure.")
    world.say(f"One day, {helper.label} gave {hero.id} {prize.phrase}, and {hero.id} wore it with pride.")

    world.para()
    world.say(f"At {world.ship.place}, {hero.id} wanted to {action.verb}.")
    pred = predict_bad_end(world, hero, action, prize)
    if pred["soiled"]:
        world.say(f"But {helper.label} held up a hand and warned, \"That could {action.risk}.\"")
        hero.memes["worry"] += 1
        world.say(f"{hero.id} still leaned toward the trouble and almost {action.rush}.")
        world.say(f"{helper.label} stepped close, and the wind snapped at the ropes.")
    else:
        world.say(f"But {helper.label} did not think it was a good idea, so the calf paused.")

    world.para()
    gear = select_gear(action, prize)
    if gear is None:
        raise StoryError("No safe gear fits this cautionary pirate story.")
    world.say(f"{helper.label} smiled and said, \"First, let's {gear.prep}.\"")
    world.say(f"{hero.id} listened. Then {hero.id} {action.verb} with care.")
    world.say(f"The little {prize.label} stayed safe, and the ship sailed on without a mishap.")
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["worry"] = 0
    world.facts["resolved"] = True
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    prize = f["prize"]
    return [
        f'Write a short cautionary pirate tale for a young child about a calf named {hero.id} and the word "{action.keyword}".',
        f"Tell a pirate story where {hero.id} wants to {action.verb} but must protect {prize.phrase}.",
        f"Write a gentle story about a calf on a ship who learns a safe way to {action.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    action = f["action"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little calf who loves pirate adventures.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {action.verb}, but that was risky on the deck.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn the calf?",
            answer=f"{helper.label} warned {hero.id} because doing that could {action.risk} and spoil {prize.phrase}.",
        ),
        QAItem(
            question=f"What helped the calf stay safe?",
            answer=f"The story used {gear.label} first, so {hero.id} could stay safe while still joining the pirate fun.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "calf": [QAItem(
        question="What is a calf?",
        answer="A calf is a young cow. It is smaller than a grown-up cow and likes to stay close to its family.",
    )],
    "pirate": [QAItem(
        question="What is a pirate ship?",
        answer="A pirate ship is a boat used by pirates. It can carry ropes, sails, lanterns, and treasure chests.",
    )],
    "rope": [QAItem(
        question="Why are ropes important on a ship?",
        answer="Ropes help hold sails, pull things, and keep people and gear steady when the boat moves.",
    )],
    "lantern": [QAItem(
        question="Why can a lantern be dangerous on a ship?",
        answer="A lantern makes light, but its flame can start a fire if it gets too close to cloth or sails.",
    )],
    "wet": [QAItem(
        question="Why do things on a deck get wet in rough weather?",
        answer="Sea spray and rain can splash over the sides of a ship and make the deck slippery and wet.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("calf")
    if world.facts["action"].id == "lantern":
        tags.add("lantern")
    out: list[QAItem] = []
    for tag in ["calf", "pirate", "rope", "lantern", "wet"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.dangerous:
            bits.append("dangerous=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} does not put {prize.label} at risk.)"
    if select_gear(action, prize) is None:
        return f"(No story: there is no safe gear that fits {action.verb} and protects {prize.label}.)"
    return "(No story: invalid combination.)"


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, ship in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(ship.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, act.risk))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gk in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), guards(G,wet).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale about a calf.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother cow", "old sailor", "kind deckhand"])
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
    if args.activity and args.prize:
        if not prize_at_risk(ACTIONS[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIONS[args.activity], PRIZES[args.prize]))
        if select_gear(ACTIONS[args.activity], PRIZES[args.prize]) is None:
            raise StoryError(explain_rejection(ACTIONS[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(CALF_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="deck", activity="rope", prize="hoofboots", name="Pip", helper="old sailor", trait="curious"),
    StoryParams(place="harbor", activity="chest", prize="hat", name="Clover", helper="kind deckhand", trait="stubborn"),
    StoryParams(place="cove", activity="lantern", prize="sailcloth", name="Tilly", helper="mother cow", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(item)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
