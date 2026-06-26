#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gill_swivel_dialogue_fairy_tale.py
===============================================================================================================

A small standalone fairy-tale story world built from the seed words
"gill" and "swivel", with dialogue as the main narrative instrument.

Premise:
- A little fish-child named Gill loves to peek beyond the pond.
- Gill's caretaker worries that dry air will hurt Gill's gills.
- A magical swivel stool, placed at the pond's edge, lets Gill turn and look
  at the fair things beyond the reeds without leaving the water.
- The turn is a dialogue-based compromise: Gill still gets wonder, but safely.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "mom", "woman"}
        male = {"boy", "prince", "king", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    fragile_to: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    guards: set[str]
    supports: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def _default_meters() -> dict[str, float]:
    return {"dry": 0.0, "wet": 0.0, "shine": 0.0}


def _default_memes() -> dict[str, float]:
    return {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "comfort": 0.0, "tension": 0.0}


def _ensure_state(ent: Entity) -> None:
    for k, v in _default_meters().items():
        ent.meters.setdefault(k, v)
    for k, v in _default_memes().items():
        ent.memes.setdefault(k, v)


def _narrate_dialogue(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.id} said.')


def _risk_gills(world: World, hero: Entity, curiosity: Curiosity, treasure: Treasure) -> bool:
    return treasure.region in {"gills", "head"} and curiosity.id == "shore_peek"


def _select_helper(curiosity: Curiosity, treasure: Treasure) -> Optional[Helper]:
    for h in HELPERS:
        if curiosity.risk in h.guards and treasure.region in h.supports:
            return h
    return None


def _do_peek(world: World, hero: Entity, curiosity: Curiosity) -> None:
    hero.memes["curiosity"] += 1
    if curiosity.id == "shore_peek":
        hero.meters["dry"] += 1
        hero.meters["wet"] -= 0.2
    world.say(f"{hero.id} leaned toward the reeds and tried to {curiosity.verb}.")


def _predict(world: World, hero: Entity, curiosity: Curiosity, treasure: Treasure) -> dict:
    dry_risk = _risk_gills(world, hero, curiosity, treasure)
    return {"risk": dry_risk}


@dataclass
class StoryParams:
    place: str
    curiosity: str
    treasure: str
    name: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "pond": Place(name="the pond", kind="water", affords={"shore_peek"}),
    "lake": Place(name="the lake", kind="water", affords={"shore_peek"}),
    "moat": Place(name="the moat", kind="water", affords={"shore_peek"}),
}

CURIOSITIES = {
    "shore_peek": Curiosity(
        id="shore_peek",
        verb="peek at the bright meadow beyond the reeds",
        gerund="peeking at the bright meadow",
        rush="swim up to the edge",
        risk="dry",
        weather="misty",
        keyword="meadow",
        tags={"water", "curiosity", "gill"},
    ),
    "moon_watch": Curiosity(
        id="moon_watch",
        verb="watch the moon silver the water",
        gerund="watching the moon",
        rush="rise toward the lily pads",
        risk="dry",
        weather="night",
        keyword="moon",
        tags={"water", "curiosity"},
    ),
}

TREASURES = {
    "gill": Treasure(
        id="gill",
        label="gills",
        phrase="soft little gills",
        region="gills",
        fragile_to={"dry"},
        plural=True,
    ),
    "crown": Treasure(
        id="crown",
        label="crown",
        phrase="a tiny gold crown",
        region="head",
        fragile_to={"dry"},
    ),
    "fin-ribbon": Treasure(
        id="fin-ribbon",
        label="fin ribbon",
        phrase="a blue ribbon tied at the fin",
        region="gills",
        fragile_to={"dry"},
    ),
}

HELPERS = [
    Helper(
        id="swivel_stool",
        label="a swivel stool",
        phrase="a round stool that could turn and turn",
        guards={"dry"},
        supports={"gills", "head"},
        prep="bring out the swivel stool to the water's edge",
        tail="set the swivel stool beside the pond and turned it gently toward the meadow",
    ),
    Helper(
        id="reed_screen",
        label="a reed screen",
        phrase="a little reed screen",
        guards={"dry"},
        supports={"gills", "head"},
        prep="set up the reed screen by the bank",
        tail="stood the reed screen like a tiny wall against the breeze",
    ),
]

NAMES = ["Gill", "Mina", "Rory", "Lina", "Tavi", "Pearl"]
PARENTS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["curious", "gentle", "bright-eyed", "dreamy", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for cur_id, cur in CURIOSITIES.items():
            if cur_id not in place.affords:
                continue
            for tr_id, treasure in TREASURES.items():
                if _select_helper(cur, treasure) is not None and _risk_gills(World(place), None if False else Entity(id="x"), cur, treasure):  # type: ignore[arg-type]
                    combos.append((place_id, cur_id, tr_id))
    return combos


def build_world(place: Place, curiosity: Curiosity, treasure: Treasure, name: str, parent_kind: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="fish-child", traits=["little", "curious"]))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=parent_kind, label=f"the {parent_kind}"))
    tr = world.add(Entity(id=treasure.id, type=treasure.id, label=treasure.label, phrase=treasure.phrase, caretaker=caretaker.id))
    helper = None

    _ensure_state(hero)
    _ensure_state(caretaker)
    _ensure_state(tr)

    world.say(f"Once upon a time, in {place.name}, there lived a little one named {hero.id}.")
    world.say(f"{hero.id} had soft little gills and a heart that wanted to see beyond the reeds.")
    _narrate_dialogue(world, hero, f"I want to {curiosity.verb}!")
    world.say(f"{caretaker.id} watched the water and listened with a worried face.")
    _narrate_dialogue(world, caretaker, f"Dear one, the air by the bank is too dry for your {treasure.label}.")
    world.say(f"{hero.id} looked at {tr.phrase} and felt the wish grow stronger.")

    world.para()
    _do_peek(world, hero, curiosity)
    pred = _predict(world, hero, curiosity, tr)
    if pred["risk"]:
        caretaker.memes["worry"] += 1
        hero.memes["tension"] += 1
        world.say(f"The {curiosity.keyword} breeze tugged at {hero.id}'s face, and the caretaker's worry rose like a cloud.")
        _narrate_dialogue(world, caretaker, f"If you go nearer, your {tr.label} will dry out.")
        _narrate_dialogue(world, hero, f"Then how can I see the meadow?")
        helper = _select_helper(curiosity, treasure)
        if helper:
            world.say(f"The caretaker smiled and remembered {helper.phrase}.")
            _narrate_dialogue(world, caretaker, f"{helper.prep}, and you can still look without leaving the water.")
            _narrate_dialogue(world, hero, "Oh! I can turn and look from here?")
            hero.memes["joy"] += 1
            caretaker.memes["comfort"] += 1
            helper_ent = world.add(Entity(id=helper.id, kind="thing", type="helper", label=helper.label, phrase=helper.phrase, plural=helper.plural))
            helper_ent.worn_by = hero.id
            world.say(f"They {helper.tail}.")
            world.say(f"{hero.id} climbed onto the seat, and the seat swiveled with a soft wooden sigh.")
            world.say(f"From the water's edge, {hero.id} could see the meadow, the daisies, and the sky, while {tr.label} stayed safe and wet.")
        else:
            raise StoryError("(No story: the wise helper for this treasure and curiosity does not exist.)")
    else:
        world.say(f"But the water was kindly shallow, so there was no need for a rescue plan.")
        hero.memes["joy"] += 1

    world.para()
    world.say(f"At last, {hero.id} smiled at the meadow with water still on {hero.pronoun('possessive')} cheeks.")
    _narrate_dialogue(world, caretaker, f"See? A small turn can be a safe adventure.")
    _narrate_dialogue(world, hero, f"And my {treasure.label} stays happy too!")
    world.say(f"So {hero.id} watched the world swivel into view, and the pond kept its little treasure safe.")

    world.facts.update(hero=hero, caretaker=caretaker, treasure=tr, curiosity=curiosity, helper=helper, place=place)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    caretaker: Entity = f["caretaker"]
    treasure: Entity = f["treasure"]
    curiosity: Curiosity = f["curiosity"]
    helper = f.get("helper")
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Who is the story about in {place.name}?",
            answer=f"The story is about {hero.id}, a little fish-child with soft little gills who wanted to {curiosity.verb}.",
        ),
        QAItem(
            question=f"What did {caretaker.id} worry about?",
            answer=f"{caretaker.id} worried that the dry air by the bank would hurt {hero.id}'s {treasure.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {curiosity.verb}, because the meadow beyond the reeds looked bright and lovely.",
        ),
    ]
    if helper:
        qa.append(
            QAItem(
                question=f"How did the swivel stool help {hero.id}?",
                answer=f"The swivel stool let {hero.id} sit by the water and turn to see the meadow, so {treasure.label} stayed safe and wet.",
            )
        )
        qa.append(
            QAItem(
                question=f"Why was the ending happy?",
                answer=f"It was happy because {hero.id} still got to look at the meadow, and the caretaker found a safe way to say yes.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "gill": [
        QAItem(
            question="What are gills for?",
            answer="Gills help many fish breathe in water by taking in what they need from the water around them.",
        )
    ],
    "swivel": [
        QAItem(
            question="What does swivel mean?",
            answer="To swivel means to turn around smoothly, like a chair that can spin a little without moving from its place.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about new things.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["curiosity"].tags)
    tags.add("gill")
    if world.facts.get("helper"):
        tags.add("swivel")
    out: list[QAItem] = []
    for tag in ("gill", "swivel", "curiosity"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    treasure: Entity = f["treasure"]
    curiosity: Curiosity = f["curiosity"]
    return [
        f'Write a short fairy tale for a child about "{hero.id}" and a "{treasure.label}" with a gentle conversation.',
        f"Tell a fairy tale where a little {hero.type} wants to {curiosity.verb} but a caretaker worries about dry air.",
        f'Write a dialogue-rich story that includes a "swivel stool" and the word "{curiosity.keyword}".',
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
        _ensure_state(e)
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(curiosity: Curiosity, treasure: Treasure) -> str:
    return (
        f"(No story: the chosen helper would not honestly solve the problem for "
        f"{treasure.label} and {curiosity.verb}. Try a different treasure or curiosity.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.name))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.name, a))
    for c in CURIOSITIES.values():
        lines.append(asp.fact("curiosity", c.id))
        lines.append(asp.fact("risk", c.id, c.risk))
    for t in TREASURES.values():
        lines.append(asp.fact("treasure", t.id))
        lines.append(asp.fact("region", t.id, t.region))
        for r in sorted(t.fragile_to):
            lines.append(asp.fact("fragile_to", t.id, r))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
        for s in sorted(h.supports):
            lines.append(asp.fact("supports", h.id, s))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C, T) :- risk(C, R), region(T, R), fragile_to(T, R).
fix(C, T) :- at_risk(C, T), helper(H), guards(H, R), risk(C, R), supports(H, R).
valid(P, C, T) :- affords(P, C), at_risk(C, T), fix(C, T).
#show valid/3.
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about Gill and a swivel stool.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if True else True]
    combos = [c for c in combos if args.curiosity is None or c[1] == args.curiosity]
    combos = [c for c in combos if args.treasure is None or c[2] == args.treasure]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, curiosity, treasure = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, curiosity=curiosity, treasure=treasure, name=name, parent=parent)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, place in PLACES.items():
        for c_id, curiosity in CURIOSITIES.items():
            if c_id not in place.affords:
                continue
            for t_id, treasure in TREASURES.items():
                if _risk_gills(World(place), Entity(id="x"), curiosity, treasure) and _select_helper(curiosity, treasure):
                    combos.append((p, c_id, t_id))
    return combos


def generate(params: StoryParams) -> StorySample:
    world = build_world(PLACES[params.place], CURIOSITIES[params.curiosity], TREASURES[params.treasure], params.name, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, curiosity, treasure) combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="pond", curiosity="shore_peek", treasure="gill", name="Gill", parent="mother")
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.curiosity} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
