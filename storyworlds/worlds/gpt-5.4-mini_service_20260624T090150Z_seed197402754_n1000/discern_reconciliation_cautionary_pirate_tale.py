#!/usr/bin/env python3
"""
A small pirate-tale storyworld about discernment, caution, and reconciliation.

Seed tale:
---
A young deckhand named Pip sailed with a tiny pirate crew on the blue sea.
Pip wanted shiny treasure right away, but the old captain kept warning that not
every glittering thing was safe. One misty day, the crew found a bright chest on
a lonely rock. Pip wanted to grab it, but the captain asked Pip to discern the
trap first. Pip looked closely and noticed the chest sat on a slick stone beside
a hidden net. The crew backed away, the trap sprang harmlessly, and later Pip
helped the captain mend the sail. By the end, Pip and the captain forgave each
other for the harsh words and laughed together while the ship rocked home.

World idea:
- Physical meters: danger, damage, caution, effort, treasure, trust, calm.
- Emotional memes: worry, bravado, regret, relief, respect, warmth.
- The story turns on discerning a risky lure, avoiding it, then reconciling
  after a stern warning.
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
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    captain: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ["danger", "damage", "caution", "effort", "treasure", "calm"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "bravado", "regret", "relief", "respect", "warmth", "annoyance"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    sea_name: str
    affords: set[str]


@dataclass(frozen=True)
class Lure:
    id: str
    label: str
    phrase: str
    verb: str
    risk: str
    tease: str
    trap: str
    cautionary_note: str
    tags: set[str]


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    phrase: str
    effect: str
    helps_against: set[str]


@dataclass
class StoryParams:
    place: str
    lure: str
    gear: str
    hero_name: str
    captain_name: str
    hero_type: str
    captain_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place("harbor", "the harbor", "the blue harbor", {"glint", "sail", "rope"}),
    "reef": Place("reef", "the reef", "the sharp reef", {"glint", "reef", "net"}),
    "isle": Place("isle", "the little isle", "the little isle", {"glint", "cave", "treasure"}),
}

LURES = {
    "glimmer_chest": Lure(
        id="glimmer_chest",
        label="glimmering chest",
        phrase="a glimmering chest",
        verb="grab the chest",
        risk="hidden net",
        tease="gold light on the lid",
        trap="a net under the stone",
        cautionary_note="not every shiny thing is safe",
        tags={"discern", "treasure", "trap"},
    ),
    "singing_shell": Lure(
        id="singing_shell",
        label="singing shell",
        phrase="a singing shell",
        verb="reach for the shell",
        risk="slippery rock",
        tease="a sweet whistling sound",
        trap="a slick ledge",
        cautionary_note="some pretty things can still make you slip",
        tags={"discern", "reef"},
    ),
    "red_flag_map": Lure(
        id="red_flag_map",
        label="red-flag map",
        phrase="a red-flag map",
        verb="follow the map",
        risk="reef break",
        tease="a map marked with a bright red flag",
        trap="a false path to the reef",
        cautionary_note="a map should be checked before a chase",
        tags={"discern", "map", "reef"},
    ),
}

GEAR = {
    "spyglass": Gear(
        id="spyglass",
        label="spyglass",
        phrase="a little spyglass",
        effect="helped the crew discern what was real",
        helps_against={"glimmer_chest", "singing_shell", "red_flag_map"},
    ),
    "gloves": Gear(
        id="gloves",
        label="rope gloves",
        phrase="rope gloves",
        effect="helped with the rope when the crew needed to work",
        helps_against={"glimmer_chest"},
    ),
    "patch_kit": Gear(
        id="patch_kit",
        label="patch kit",
        phrase="a patch kit",
        effect="helped mend the sail after the scare",
        helps_against={"glimmer_chest", "singing_shell", "red_flag_map"},
    ),
}

NAMES = ["Pip", "Nell", "Bo", "Mara", "Jory", "Tess", "Finn", "Sailor", "Kit", "Wren"]
TRAITS = ["curious", "bold", "careful", "sly", "small", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def lure_is_risky(lure: Lure) -> bool:
    return True


def select_gear(lure: Lure) -> Optional[Gear]:
    for gear in GEAR.values():
        if lure.id in gear.helps_against:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for lure in LURES.values():
            if lure_is_risky(lure) and select_gear(lure):
                for gear in GEAR.values():
                    if lure.id in gear.helps_against:
                        combos.append((place.id, lure.id, gear.id))
    return combos


def explain_rejection(lure: Lure) -> str:
    return f"(No story: the crew has no sensible way to discern and answer the {lure.label} trap.)"


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def _springs_trap(world: World, hero: Entity, lure: Lure) -> None:
    sig = ("trap", lure.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["danger"] += 1
    hero.memes["worry"] += 1
    world.say(f"The {lure.label} was a trick, and the hidden trap sprang with a snap.")


def _mend_sail(world: World, hero: Entity, captain: Entity) -> None:
    sig = ("mend", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["effort"] += 1
    captain.meters["calm"] += 1
    captain.memes["warmth"] += 1
    world.say(f"Later, {hero.id} helped {captain.id} mend the sail with steady hands.")


def _reconcile(world: World, hero: Entity, captain: Entity) -> None:
    sig = ("reconcile", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["regret"] += 1
    hero.memes["respect"] += 1
    captain.memes["relief"] += 1
    captain.memes["warmth"] += 1
    world.say(f"{hero.id} and {captain.id} forgave each other and shared a small grin.")


def tell(place: Place, lure: Lure, gear: Gear, hero_name: str, captain_name: str,
         hero_type: str, captain_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, label="the captain"))
    chest = world.add(Entity(id=lure.id, type="thing", label=lure.label, phrase=lure.phrase, owner=None))

    hero.memes["bravado"] += 1
    captain.memes["worry"] += 1
    captain.meters["caution"] += 1
    hero.meters["treasure"] += 1
    world.say(f"{hero.id} sailed with {captain.id} on {place.label}.")
    world.say(f"{hero.id} loved bright treasure, and {captain.id} kept saying that {lure.cautionary_note}.")
    world.para()

    world.say(f"One misty day, the crew spotted {chest.phrase} on a lonely rock.")
    world.say(f"It gave off {lure.tease}, but {captain.id} asked {hero.id} to discern the danger before rushing in.")
    world.say(f"{hero.id} peered through the {gear.label} and noticed {lure.trap}.")
    hero.meters["caution"] += 1
    captain.memes["respect"] += 1

    world.para()
    world.say(f"They backed away just in time, and the trap clicked uselessly where they had stood.")
    _springs_trap(world, hero, lure)
    world.say(f"That was a good lesson: {lure.cautionary_note}.")
    _mend_sail(world, hero, captain)
    _reconcile(world, hero, captain)

    world.para()
    world.say(f"In the end, {hero.id} was still bold, but now {hero.id} was bold with a clearer eye.")
    world.say(f"{captain.id} smiled as the ship rocked home, safe because they had chosen caution first.")

    world.facts.update(
        hero=hero,
        captain=captain,
        chest=chest,
        lure=lure,
        gear=gear,
        place=place,
        reconciled=True,
        cautioned=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    lure = f["lure"]
    return [
        f'Write a short pirate tale for a young child about a deckhand who must discern a trap around {lure.label}.',
        f"Tell a cautionary pirate story where {hero.id} listens to {captain.id} before chasing treasure.",
        f"Write a pirate story with reconciliation, where a stern warning turns into a kind ending after a risky discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    lure: Lure = f["lure"]
    gear: Gear = f["gear"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who asked {hero.id} to discern the danger before rushing at {lure.label}?",
            answer=f"{captain.id} asked {hero.id} to look closely first, because {lure.cautionary_note}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice by using the {gear.label}?",
            answer=f"{hero.id} noticed {lure.trap}, so the crew could step back before trouble hit.",
        ),
        QAItem(
            question=f"Where did the pirate crew find the {lure.label}?",
            answer=f"They found it at {place.label} on a lonely rock, where it looked shiny but was not safe.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {captain.id}?",
            answer=f"They reconciled after the scare, helped mend the sail, and sailed home in a calmer mood.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "discern": [
        QAItem(
            question="What does it mean to discern something?",
            answer="To discern something means to look carefully and figure out what it really is or whether it is safe.",
        )
    ],
    "treasure": [
        QAItem(
            question="Why do pirates like treasure?",
            answer="Pirates like treasure because they think gold, jewels, or shiny loot will make them rich and happy.",
        )
    ],
    "trap": [
        QAItem(
            question="What is a trap?",
            answer="A trap is a trick set to catch someone or make them get hurt, so it is important to notice it early.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story warns about a risky choice and helps you learn to be careful next time.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people stop being upset with each other and make peace again.",
        )
    ],
    "spyglass": [
        QAItem(
            question="What is a spyglass used for on a ship?",
            answer="A spyglass helps sailors look far away so they can spot rocks, ships, or trouble sooner.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["lure"].tags)
    tags.add("cautionary")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for tag in ["discern", "treasure", "trap", "cautionary", "reconciliation", "spyglass"]:
        if tag in tags or tag in {"discern", "cautionary", "reconciliation", "spyglass"}:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
lure(L) :- lure_id(L).
gear(G) :- gear_id(G).
place(P) :- place_id(P).

risky(L) :- lure_id(L).
can_help(G,L) :- helps_against(G,L).
valid(Place,Lure,Gear) :- place_id(Place), lure_id(Lure), gear_id(Gear), risky(Lure), can_help(Gear,Lure).

discerned(Hero,Lure) :- sees(Hero,Lure), uses(Hero,Gear), can_help(Gear,Lure).
reconciled(Hero,Captain) :- apology(Hero,Captain), forgive(Captain,Hero).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_id", pid))
    for lid in LURES:
        lines.append(asp.fact("lure_id", lid))
    for gid in GEAR:
        lines.append(asp.fact("gear_id", gid))
    for gid, gear in GEAR.items():
        for lid in gear.helps_against:
            lines.append(asp.fact("helps_against", gid, lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    lure: str
    gear: str
    hero_name: str
    captain_name: str
    hero_type: str
    captain_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with discernment and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--lure", choices=LURES.keys())
    ap.add_argument("--gear", choices=GEAR.keys())
    ap.add_argument("--name")
    ap.add_argument("--captain-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--captain-type", choices=["man", "woman", "captain"])
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
    filtered = []
    for p, l, g in combos:
        if args.place and p != args.place:
            continue
        if args.lure and l != args.lure:
            continue
        if args.gear and g != args.gear:
            continue
        filtered.append((p, l, g))
    if not filtered:
        raise StoryError("(No valid pirate story matches the requested options.)")
    place, lure, gear = rng.choice(sorted(filtered))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    captain_type = args.captain_type or rng.choice(["man", "woman", "captain"])
    hero_name = args.name or rng.choice(NAMES)
    captain_name = args.captain_name or rng.choice([n for n in NAMES if n != hero_name])
    trait = rng.choice(TRAITS)
    return StoryParams(place, lure, gear, hero_name, captain_name, hero_type, captain_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        LURES[params.lure],
        GEAR[params.gear],
        params.hero_name,
        params.captain_name,
        params.hero_type,
        params.captain_type,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid_combos(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("harbor", "glimmer_chest", "spyglass", "Pip", "Mara", "boy", "captain", "curious"),
            StoryParams("reef", "singing_shell", "spyglass", "Nell", "Rook", "girl", "captain", "careful"),
            StoryParams("isle", "red_flag_map", "patch_kit", "Bo", "Keen", "boy", "captain", "bold"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
