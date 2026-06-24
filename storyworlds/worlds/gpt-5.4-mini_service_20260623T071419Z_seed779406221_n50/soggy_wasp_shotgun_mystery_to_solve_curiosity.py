#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
===================================================================

A small ghost-story-flavored mystery world for curious kids.

Premise:
- A child finds a soggy clue.
- A wasp and a noisy old shotgun-shaped prop are part of the mystery.
- Curiosity pushes the child to investigate.
- A careful grown-up helps solve the mystery and proves what changed.

The world keeps a simple state model with typed entities, meters, and memes.
It supports normal generation, QA, JSON, trace, and an ASP parity check.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    ghosty: str
    afford_wet: bool = False
    afford_noise: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    wet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    sign: str
    sound: str
    hidden: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    label: str
    push: str
    seek: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        ent.meters.setdefault("wet", 0.0)
        ent.meters.setdefault("noise", 0.0)
        ent.meters.setdefault("mystery", 0.0)
        ent.meters.setdefault("solved", 0.0)
        ent.memes.setdefault("curiosity", 0.0)
        ent.memes.setdefault("fear", 0.0)
        ent.memes.setdefault("relief", 0.0)
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    clue: str
    mystery: str
    curiosity: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(id="attic", label="the attic", ghosty="The attic was cool and whispery.", afford_wet=False, afford_noise=True, tags={"ghost", "quiet"}),
    "garden": Place(id="garden", label="the garden shed", ghosty="The garden shed stood under silver clouds.", afford_wet=True, afford_noise=True, tags={"ghost", "garden"}),
    "boathouse": Place(id="boathouse", label="the old boathouse", ghosty="The old boathouse creaked like a sleepy ghost.", afford_wet=True, afford_noise=True, tags={"ghost", "water"}),
}

CLUES = {
    "soggy_note": Clue(id="soggy_note", label="a soggy note", phrase="a soggy note with a blue stamp", wet=True, tags={"soggy"}),
    "mildew_map": Clue(id="mildew_map", label="a damp map", phrase="a damp map folded in four", wet=True, tags={"soggy", "map"}),
    "feather": Clue(id="feather", label="a pale feather", phrase="a pale feather stuck to the sill", wet=False, tags={"ghost"}),
}

MYSTERIES = {
    "wasp_nest": Mystery(id="wasp_nest", label="the wasp mystery", sign="a dark buzzing shape", sound="a soft buzz behind the boards", hidden="a tiny nest under the eaves", solved_by="opening the loose board and stepping back", tags={"wasp"}),
    "shotgun_case": Mystery(id="shotgun_case", label="the shotgun mystery", sign="a long wooden shape", sound="a hollow clack in the closet", hidden="an old toy shotgun in a box", solved_by="lifting the box lid and finding a toy", tags={"shotgun"}),
    "ghost_lamp": Mystery(id="ghost_lamp", label="the ghost-light mystery", sign="a pale glow", sound="a tiny click and a hum", hidden="a battery lamp behind a crate", solved_by="moving the crate and seeing the lamp", tags={"ghost"}),
}

CURIOSITIES = {
    "gentle": Curiosity(id="gentle", label="gentle curiosity", push="wanted to peek", seek="kept looking for the truth", tags={"curiosity"}),
    "brave": Curiosity(id="brave", label="brave curiosity", push="wanted to look closer", seek="kept following the clue", tags={"curiosity"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Eli", "Ben"]
HELPER_NAMES = ["Grandma", "Grandpa", "Mister Reed", "Aunt June"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for mid, mystery in MYSTERIES.items():
                for cur in CURIOSITIES:
                    if clue.wet and place.afford_wet and ("wasp" in mystery.tags or "shotgun" in mystery.tags or "ghost" in mystery.tags):
                        out.append((pid, cid, mid, cur))
                    elif not clue.wet and place.afford_noise:
                        out.append((pid, cid, mid, cur))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.afford_wet:
            lines.append(asp.fact("wet_place", pid))
        if p.afford_noise:
            lines.append(asp.fact("noise_place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.wet:
            lines.append(asp.fact("wet_clue", cid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    for cur in CURIOSITIES:
        lines.append(asp.fact("curiosity", cur))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,M,U) :- place(P), clue(C), mystery(M), curiosity(U), wet_clue(C), wet_place(P), tagged(M,wasp).
valid(P,C,M,U) :- place(P), clue(C), mystery(M), curiosity(U), wet_clue(C), wet_place(P), tagged(M,shotgun).
valid(P,C,M,U) :- place(P), clue(C), mystery(M), curiosity(U), not wet_clue(C), noise_place(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with soggy clues, wasps, and a shotgun-shaped mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)
              and (args.curiosity is None or c[3] == args.curiosity)]
    if not combos:
        raise StoryError("No valid mystery matches the chosen filters.")
    place, clue, mystery, curiosity = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = rng.choice(HELPER_NAMES)
    helper_type = "woman" if helper in {"Grandma", "Aunt June"} else "man"
    return StoryParams(place=place, clue=clue, mystery=mystery, curiosity=curiosity, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity, Entity]:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero", attrs={"curiosity": params.curiosity}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    clue = world.add(Entity(id=params.clue, type="clue", label=CLUES[params.clue].label, attrs={"phrase": CLUES[params.clue].phrase}))
    mystery = world.add(Entity(id=params.mystery, type="mystery", label=MYSTERIES[params.mystery].label, attrs={"sign": MYSTERIES[params.mystery].sign, "sound": MYSTERIES[params.mystery].sound, "hidden": MYSTERIES[params.mystery].hidden, "solved_by": MYSTERIES[params.mystery].solved_by}))
    wasp = world.add(Entity(id="wasp", type="wasp", label="a wasp", tags={"wasp"}))
    shotgun = world.add(Entity(id="shotgun", type="shotgun", label="an old shotgun", tags={"shotgun"}))
    for ent in (hero, helper, clue, mystery, wasp, shotgun):
        ent.meters.setdefault("wet", 0.0)
        ent.meters.setdefault("noise", 0.0)
        ent.meters.setdefault("mystery", 0.0)
        ent.meters.setdefault("solved", 0.0)
        ent.memes.setdefault("curiosity", 0.0)
        ent.memes.setdefault("fear", 0.0)
        ent.memes.setdefault("relief", 0.0)
    return world, hero, helper, clue, mystery, wasp, shotgun


def tell(params: StoryParams) -> World:
    world, hero, helper, clue, mystery, wasp, shotgun = _setup_world(params)
    c = CURIOSITIES[params.curiosity]
    place = PLACES[params.place]
    hero.memes["curiosity"] += 1
    world.say(f"{place.ghosty} {hero.id} found {clue.attrs['phrase']}.")
    world.say(f"That clue felt strange, and {hero.pronoun()} {c.push} instead of turning away.")
    world.para()
    world.say(f"Nearby, {mystery.attrs['sign']} kept waiting in the dark.")
    if "wasp" in MYSTERIES[params.mystery].tags:
        world.say(f"Then the soft buzz of {wasp.label_word if hasattr(wasp, 'label_word') else 'a wasp'} drifted from the boards.")
        wasp.meters["noise"] += 1
        hero.memes["fear"] += 1
    if "shotgun" in MYSTERIES[params.mystery].tags:
        world.say(f"Elsewhere, {shotgun.label} made a hollow clack when the floorboards shifted.")
        shotgun.meters["noise"] += 1
        hero.memes["fear"] += 1
    world.para()
    helper.memes["relief"] += 1
    helper.say = None  # harmless placeholder never used
    world.say(f"{helper.id} came with a lantern and a calm voice.")
    world.say(f"Together they followed the clue to {mystery.attrs['hidden']}.")
    mystery.meters["solved"] += 1
    hero.meters["mystery"] += 1
    world.say(f"They solved {mystery.label} by {mystery.attrs['solved_by']}.")
    if "wasp" in MYSTERIES[params.mystery].tags:
        world.say("The wasp only wanted its own quiet corner, so they left it safely outside.")
    if "shotgun" in MYSTERIES[params.mystery].tags:
        world.say("The old shotgun was only a toy from long ago, and it stayed still once the dust was brushed away.")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.facts.update(hero=hero, helper=helper, clue=clue, mystery=mystery, place=place, curiosity=c, wasp=wasp, shotgun=shotgun)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story mystery for a 3-to-5-year-old with a {f["place"].label} and a {f["clue"].label}.',
        f"Tell a gentle story where {f['hero'].id} follows {f['hero'].pronoun('possessive')} curiosity to solve {f['mystery'].label}.",
        f'Write a simple spooky-but-safe story that includes the words "soggy", "wasp", and "shotgun".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Entity = f["mystery"]
    clue: Entity = f["clue"]
    place: Place = f["place"]
    c: Curiosity = f["curiosity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find in {place.label}?",
            answer=f"{hero.id} found {clue.attrs['phrase']}. It made the place feel mysterious, so {hero.pronoun()} kept looking.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep investigating?",
            answer=f"{hero.id} felt {c.label} and wanted to solve {mystery.label}. The strange clue pulled {hero.pronoun('object')} toward the answer.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.id} came with a lantern and helped {hero.id} follow the clue. Together they found the hidden answer.",
        ),
        QAItem(
            question=f"How was {mystery.label} solved?",
            answer=f"It was solved by {mystery.attrs['solved_by']}. That turned the spooky feeling into relief.",
        ),
    ]
    if "wasp" in f["mystery"].tags:
        qa.append(QAItem(
            question=f"What was the wasp doing in the story?",
            answer="The wasp made a soft buzz near the boards. It stayed in its own quiet corner once the children understood the mystery.",
        ))
    if "shotgun" in f["mystery"].tags:
        qa.append(QAItem(
            question=f"What was the shotgun mystery really about?",
            answer="It was about an old toy shotgun hiding in a box. The strange shape looked spooky at first, but the answer was harmless.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does curiosity do?", answer="Curiosity makes you want to look, ask, and learn. It can help solve mysteries when you stay careful."),
        QAItem(question="What is a soggy thing?", answer="A soggy thing is wet and soft because it has soaked up water."),
        QAItem(question="Why can a wasp be scary?", answer="A wasp can buzz loudly and sting, so people should stay calm and give it space."),
        QAItem(question="What is a shotgun?", answer="A shotgun is a kind of gun, and people should never play with real guns. In a story for children, it can appear only as a harmless old toy or prop."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="attic", clue="soggy_note", mystery="wasp_nest", curiosity="gentle", hero="Mina", hero_type="girl", helper="Grandma", helper_type="woman"),
    StoryParams(place="boathouse", clue="mildew_map", mystery="shotgun_case", curiosity="brave", hero="Finn", hero_type="boy", helper="Mister Reed", helper_type="man"),
    StoryParams(place="garden", clue="feather", mystery="ghost_lamp", curiosity="gentle", hero="Nora", hero_type="girl", helper="Aunt June", helper_type="woman"),
]


def explain_invalid(place: str, clue: str, mystery: str) -> str:
    return f"No story: {clue} and {mystery} do not make a clear mystery in {place}."


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.mystery not in MYSTERIES or params.curiosity not in CURIOSITIES:
        raise StoryError("Unknown parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("ASP mismatch")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
        return 1
    print(f"OK: {len(py)} valid combos match between Python and ASP.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
