#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
==================================================================

A small standalone storyworld in a pirate-tale style.

Seed imaginings:
- A tiny fellow-ship on a ship or dock.
- A worried captain notices a paw-print problem.
- Rosemary is the helpful herb that fixes the smell or fear.
- Humor comes from a bumbling parrot/cat/paw mishap.
- Happy ending: the crew solves the problem together and sails on laughing.

The world is intentionally small and constraint-checked. A story is only
generated when the worry and the fix are both sensible in the simulated world.

Core premise:
- A captain or helper loves a simple nautical task.
- A prized item or important job gets threatened by a messy, silly incident.
- The crew proposes a believable fix using rosemary.
- The ending image proves the change: calm sea, clean paws, shared laughter.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
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
    afford: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
        return any(g.region == region for g in self.worn_items(actor) if g.props.get("protective") == "yes")

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "dock": Setting("the dock", {"board", "splash"}),
    "harbor": Setting("the harbor", {"board", "splash"}),
    "ship": Setting("the little ship", {"board", "splash"}),
    "galley": Setting("the galley", {"cook"}),
}

ACTIONS = {
    "pawprints": Adventure(
        id="pawprints",
        verb="wipe away the paw prints",
        gerund="wiping away paw prints",
        rush="dash after the muddy paw",
        mess="muddy",
        soil="muddy and smudged",
        zone={"board", "splash"},
        keyword="paw",
        tags={"paw", "mud"},
    ),
    "rosemary_tea": Adventure(
        id="rosemary_tea",
        verb="brew rosemary tea",
        gerund="brewing rosemary tea",
        rush="rush to the galley",
        mess="steamed",
        soil="steamed and scented",
        zone={"cook"},
        keyword="rosemary",
        tags={"rosemary", "herb"},
    ),
    "salt_scrub": Adventure(
        id="salt_scrub",
        verb="scrub the deck",
        gerund="scrubbing the deck",
        rush="run for the scrub brush",
        mess="wet",
        soil="wet and slippery",
        zone={"board"},
        keyword="salt",
        tags={"salt", "clean"},
    ),
}

PRIZES = {
    "map": Prize("map", "a crinkly treasure map", "map", "board"),
    "coat": Prize("coat", "a bright captain's coat", "coat", "torso"),
    "hat": Prize("hat", "a funny striped hat", "hat", "head"),
}

GEAR = [
    Gear("oilcloth", "an oilcloth apron", {"torso"}, {"wet", "muddy", "steamed"}, "put on an oilcloth apron", "put on the oilcloth apron"),
    Gear("boots", "rubber boots", {"feet"}, {"wet", "muddy"}, "wear rubber boots", "put on the rubber boots", True),
    Gear("gloves", "tiny gloves", {"hands"}, {"muddy"}, "wear tiny gloves", "grab the tiny gloves", True),
]

NAMES = ["Pip", "Mara", "Jory", "Nell", "Tamsin", "Bram"]
ROLES = ["captain", "deckhand", "mate", "cook", "sailor"]
TRAITS = ["cheerful", "brave", "sly", "bouncy", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid, act in ACTIONS.items():
            if aid not in setting.afford:
                continue
            for pid, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize) is not None:
                    out.append((place, aid, pid))
    return out


def prize_at_risk(act: Adventure, prize: Prize) -> bool:
    return prize.region in act.zone


def select_gear(act: Adventure, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and act.mess in gear.guards:
            return gear
    return None


def asp_facts() -> str:
    import asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), covers(G,R), worn_on(P,R), mess_of(A,M), guards(G,M).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story params / world engine
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about a fellow-ship, a paw, and rosemary.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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


def explain_rejection(act: Adventure, prize: Prize) -> str:
    return f"(No story: {act.gerund} does not sensibly threaten {prize.phrase} here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIONS[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        trait=args.trait or rng.choice(TRAITS),
    )


def _speak(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, act: Adventure, prize_cfg: Prize, name: str, role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=role, label=name))
    mate = world.add(Entity(id="mate", kind="character", type="sailor", label="the fellow-ship mate"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, owner=hero.id, caretaker=mate.id))
    world.add(Entity(id="paw", kind="thing", type="paw", label="a muddy paw", phrase="a muddy paw", region="board"))
    world.add(Entity(id="rosemary", kind="thing", type="herb", label="rosemary", phrase="fresh rosemary", region="cook"))

    hero.memes["joy"] = 1
    _speak(world, f"{name} was a {trait} {role} aboard {setting.place}, and {name} liked every bit of the fellow-ship.")
    _speak(world, f"{hero.pronoun().capitalize()} laughed at the ship's little joke: a cat had stamped a muddy paw across the deck like it owned the map.")
    _speak(world, f"The crew kept {prize_cfg.phrase} near by, because {name} wanted to {act.verb} before sunset.")
    _speak(world, f"Then the naughty paw brushed the prize, and the {prize.label} looked {act.soil}.")

    world.para()
    world.zone = set(act.zone)
    hero.meters[act.mess] = 1.0
    if prize.region in act.zone:
        prize.meters[act.mess] = 1.0
    world.say(f"{name} clapped {hero.pronoun('possessive')} hands and rushed to the galley, because rosemary could cheer up a smelly ship.")
    gear = select_gear(act, prize)
    if gear is None:
        return world
    gear_ent = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, region=prize.region, owner=hero.id))
    gear_ent.props["protective"] = "yes"
    gear_ent.worn_by = hero.id
    world.say(f"{trait.capitalize()} {name} used {gear.prep}, then the mate sprinkled rosemary over the air and the silly smell drifted away.")
    world.para()
    world.say(f"In no time, the deck was bright again, the paw was clean, and the crew sailed on with a laugh and a song.")
    world.say(f"The fellow-ship even named the cat's print \"Captain Paw,\" which made everyone grin.")
    world.facts.update(hero=hero, mate=mate, prize=prize, act=act, gear=gear_ent, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["act"], f["prize"]
    return [
        f'Write a pirate-tale story for a small child that includes "fellow-ship", "paw", and "rosemary".',
        f"Tell a funny sea story where {hero.id} wants to {act.verb} but a muddy paw upsets {prize.label}, and rosemary helps.",
        f"Write a short happy-ending adventure about a crew on {world.setting.place} who solves a silly paw mess with rosemary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, act = f["hero"], f["mate"], f["prize"], f["act"]
    return [
        QAItem(
            question=f"Who was the story about on the ship?",
            answer=f"It was about {hero.id}, a {hero.type} in the fellow-ship, and the helpful mate beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What silly thing made a mess of the {prize.label}?",
            answer=f"A muddy paw made the mess and left the {prize.label} looking dirty and funny.",
        ),
        QAItem(
            question=f"How did rosemary help in the story?",
            answer=f"Rosemary helped freshen the air after the paw mess, and the crew used it while fixing the problem.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before sunset?",
            answer=f"{hero.id} wanted to {act.verb} before sunset, but first the crew had to solve the paw problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a paw?", "A paw is an animal's foot, like a cat's foot or a dog's foot."),
        QAItem("What is rosemary?", "Rosemary is a plant with a strong, fresh smell. People sometimes use it for cooking."),
        QAItem("What does a happy ending mean?", "A happy ending means the trouble gets fixed and the characters finish the story feeling glad."),
        QAItem("What is humor?", "Humor is something funny that makes people smile or laugh."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} region={e.region} worn_by={e.worn_by} meters={e.meters} memes={e.memes} props={e.props}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.activity], PRIZES[params.prize], params.name, params.role, params.trait)
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
    StoryParams("dock", "pawprints", "map", "Mara", "captain", "cheerful"),
    StoryParams("harbor", "pawprints", "coat", "Pip", "mate", "bouncy"),
    StoryParams("ship", "pawprints", "hat", "Nell", "cook", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
