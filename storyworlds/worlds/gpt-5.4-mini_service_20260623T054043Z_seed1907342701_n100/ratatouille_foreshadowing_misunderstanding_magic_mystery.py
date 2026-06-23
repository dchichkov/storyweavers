#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/ratatouille_foreshadowing_misunderstanding_magic_mystery.py
==============================================================================================================================

A standalone storyworld for a tiny mystery built from the seed words:
ratatouille, foreshadowing, misunderstanding, magic, mystery.

Premise:
- A child notices a simmering pot of ratatouille, a missing spoon, and small
  clues around a kitchen.
- The child misreads the clues and worries that the food or the room has become
  magical in a spooky way.
- A helper turns the clues into a gentle reveal: the "magic" was just a clever
  kitchen charm and a practical surprise, not a real haunting.

The world keeps typed entities with physical meters and emotional memes,
supports a reasonableness gate, an inline ASP twin, and generates three Q&A
sets from simulated state.
"""

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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    setting_line: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    foreshadow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    visible: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    suspicion: str
    wrong_guess: str
    reveal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: list[str] = []

    def add(self, ent: Entity) -> Entity:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.clues_seen = list(self.clues_seen)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_doubt(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    if child.memes["worry"] < THRESHOLD:
        return out
    if ("doubt", child.id) in world.fired:
        return out
    world.fired.add(("doubt", child.id))
    child.memes["curiosity"] += 1
    out.append("The kitchen felt a little strange.")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    if child.memes["curiosity"] < THRESHOLD:
        return out
    clue = world.facts["clue"]
    if clue.id in world.clues_seen:
        return out
    world.clues_seen.append(clue.id)
    clue_ent = world.add(Entity(id=f"seen_{clue.id}", label=clue.label, kind="thing", type="thing"))
    clue_ent.meters["noticed"] += 1
    out.append(clue.foreshadow)
    return out


CAUSAL_RULES = [Rule("doubt", "mind", _r_doubt), Rule("clue", "mind", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def likely_story(place: Place, clue: Clue, magic: Magic, misunderstanding: Misunderstanding) -> bool:
    return place.id in PLACES and clue.id in CLUES and magic.id in MAGICS and misunderstanding.id in MISUNDERSTANDINGS


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for magic in MAGICS:
                for mis in MISUNDERSTANDINGS:
                    if place.id in {"kitchen", "cafe", "grandma_house"} and magic.harmless:
                        combos.append((place.id, clue.id, magic.id, mis.id))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    magic: str
    misunderstanding: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        setting_line="The kitchen smelled like tomatoes, herbs, and warm bread.",
        affords={"simmer", "search", "explain"},
        tags={"kitchen", "food"},
    ),
    "cafe": Place(
        id="cafe",
        label="the little café",
        setting_line="The little café was quiet except for the soft bubbles from the stove.",
        affords={"simmer", "search", "explain"},
        tags={"cafe", "food"},
    ),
    "grandma_house": Place(
        id="grandma_house",
        label="Grandma's house",
        setting_line="Grandma's house had shelves of jars and a curtain that moved in the breeze.",
        affords={"simmer", "search", "explain"},
        tags={"grandma", "food"},
    ),
}

CLUES = {
    "basil_leaf": Clue(
        id="basil_leaf",
        label="a basil leaf on the floor",
        phrase="a basil leaf on the floor",
        foreshadow="Near the stove, a single basil leaf lay on the tiles like a tiny green clue.",
        tags={"basil", "clue"},
    ),
    "spoon": Clue(
        id="spoon",
        label="a silver spoon by the sink",
        phrase="a silver spoon by the sink",
        foreshadow="By the sink, a silver spoon winked in the light as if it wanted to be found.",
        tags={"spoon", "clue"},
    ),
    "napkin": Clue(
        id="napkin",
        label="a folded napkin on the table",
        phrase="a folded napkin on the table",
        foreshadow="On the table, a folded napkin sat too neatly to be an accident.",
        tags={"napkin", "clue"},
    ),
}

MAGICS = {
    "glow_spoon": Magic(
        id="glow_spoon",
        label="a glowing spoon",
        phrase="a glowing spoon",
        visible="it shimmered softly in the dark",
        harmless=True,
        tags={"magic", "spoon"},
    ),
    "pepper_spark": Magic(
        id="pepper_spark",
        label="pepper sparkles",
        phrase="pepper sparkles",
        visible="tiny sparkles popped above the pot and vanished",
        harmless=True,
        tags={"magic", "pepper"},
    ),
    "talking_timer": Magic(
        id="talking_timer",
        label="a talking timer",
        phrase="a talking timer",
        visible="the timer dinged twice, as if it were giving directions",
        harmless=True,
        tags={"magic", "timer"},
    ),
}

MISUNDERSTANDINGS = {
    "haunting": Misunderstanding(
        id="haunting",
        suspicion="it looked like the kitchen was haunted",
        wrong_guess="the child thought a ghost was hiding in the steam",
        reveal="the mystery was only a harmless kitchen trick",
        tags={"mystery", "ghost"},
    ),
    "stolen_recipe": Misunderstanding(
        id="stolen_recipe",
        suspicion="it looked like someone had stolen the recipe",
        wrong_guess="the child thought the missing spoon meant the dish was ruined",
        reveal="the helper had only moved the spoon to stir the pot more carefully",
        tags={"mystery", "recipe"},
    ),
    "magic_mistake": Misunderstanding(
        id="magic_mistake",
        suspicion="it looked like the ratatouille had gone magical by mistake",
        wrong_guess="the child thought the glow meant the pot itself was enchanted",
        reveal="the glow came from a small charm clipped to the spoon handle",
        tags={"mystery", "magic"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Suri", "Ella"]
BOY_NAMES = ["Theo", "Milo", "Owen", "Arlo", "Ezra", "Leo"]


def valid_story_params(place: Place, clue: Clue, magic: Magic, misunderstanding: Misunderstanding) -> bool:
    return place.id in PLACES and clue.id in CLUES and magic.id in MAGICS and misunderstanding.id in MISUNDERSTANDINGS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.magic is None or c[2] == args.magic)
              and (args.misunderstanding is None or c[3] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, clue_id, magic_id, mis_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or ("Mama" if helper_type == "mother" else "Papa")
    return StoryParams(
        place=place_id,
        clue=clue_id,
        magic=magic_id,
        misunderstanding=mis_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def tell(place: Place, clue: Clue, magic: Magic, misunderstanding: Misunderstanding,
         child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    pot = world.add(Entity(id="pot", kind="thing", type="dish", label="the ratatouille pot", phrase="a pot of ratatouille", tags={"ratatouille", "food"}))
    spoon = world.add(Entity(id="spoon", kind="thing", type="thing", label="the spoon", phrase=clue.phrase, tags={"spoon"}))
    charm = world.add(Entity(id="charm", kind="thing", type="thing", label="the charm", phrase=magic.phrase, tags={"magic"}))
    world.facts.update(child=child, helper=helper, pot=pot, spoon=spoon, charm=charm, clue=clue, magic=magic, misunderstanding=misunderstanding, place=place)
    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 1.0
    helper.memes["calm"] = 1.0
    world.say(f"{place.setting_line}")
    world.say(f"{child.name if hasattr(child, 'name') else child.id} found a pot of ratatouille on the stove, and the smell was rich with tomatoes and herbs.")
    world.say(f"But the spoon was missing, and {misunderstanding.suspicion}.")
    world.para()
    world.say(f"{child.id} pointed at {clue.label}. {misunderstanding.wrong_guess}.")
    world.say(f"Then the clue made more sense: {magic.visible}.")
    propagate(world, narrate=True)
    world.para()
    helper.memes["trust"] += 1
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    world.say(f"{helper.id} smiled and explained that {misunderstanding.reveal}.")
    world.say(f"{helper.id} lifted the spoon, stirred the ratatouille, and the little charm only made a soft glow beside the pot.")
    world.say(f"In the end, the mystery was solved: the ratatouille stayed warm, the spoon was back, and the kitchen looked cozy instead of spooky.")
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "ratatouille" and makes a small clue feel mysterious before explaining it.',
        f"Tell a gentle mystery where {f['child'].id} sees {f['clue'].label} near ratatouille and worries about magic, but {f['helper'].id} clears up the misunderstanding.",
        f'Write a short story with foreshadowing, misunderstanding, and a harmless magic reveal in {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, clue, magic, mis = f["child"], f["helper"], f["clue"], f["magic"], f["misunderstanding"]
    return [
        QAItem(
            question=f"What did {child.id} notice first in {f['place'].label}?",
            answer=f"{child.id} noticed a pot of ratatouille and {clue.label}. That clue made the kitchen feel mysterious before anyone explained it.",
        ),
        QAItem(
            question=f"Why did {child.id} think something strange was happening?",
            answer=f"{child.id} saw {magic.visible} and did not know what it meant yet. Because of that, {mis.wrong_guess}.",
        ),
        QAItem(
            question=f"How did {helper.id} solve the mystery?",
            answer=f"{helper.id} explained that {mis.reveal}. Then {helper.id} stirred the ratatouille and showed that the glow was harmless.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the spoon was back, the ratatouille stayed warm, and the kitchen felt cozy instead of spooky. The mystery turned into a safe, friendly surprise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ratatouille?",
            answer="Ratatouille is a warm dish made from vegetables cooked together slowly, often with tomatoes, peppers, onions, and herbs.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small clues early so readers can guess that something important will happen later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone sees or hears something and guesses the wrong meaning before the truth is explained.",
        ),
        QAItem(
            question="What does harmless magic mean in a story?",
            answer="Harmless magic means something surprising or sparkly happens, but nobody gets hurt and the surprise turns out to be safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES.values():
        for clue in CLUES.values():
            for magic in MAGICS.values():
                for mis in MISUNDERSTANDINGS.values():
                    if "food" in place.tags and magic.harmless:
                        combos.append((place.id, clue.id, magic.id, mis.id))
    return combos


ASP_RULES = r"""
valid(P,C,M,I) :- place(P), clue(C), magic(M), misunderstanding(I), food_place(P), harmless(M).
story_hint(P,C,M) :- valid(P,C,M,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if "food" in p.tags:
            lines.append(asp.fact("food_place", p.id))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
    for m in MAGICS.values():
        lines.append(asp.fact("magic", m.id))
        if m.harmless:
            lines.append(asp.fact("harmless", m.id))
    for i in MISUNDERSTANDINGS.values():
        lines.append(asp.fact("misunderstanding", i.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py != cl:
        ok = 1
        print("MISMATCH between Python and ASP:")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a ratatouille mystery with foreshadowing, misunderstanding, and harmless magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.magic not in MAGICS or params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(
        PLACES[params.place], CLUES[params.clue], MAGICS[params.magic], MISUNDERSTANDINGS[params.misunderstanding],
        params.child_name, params.child_type, params.helper_name, params.helper_type
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="kitchen", clue="basil_leaf", magic="glow_spoon", misunderstanding="magic_mistake", child_name="Mina", child_type="girl", helper_name="Mama", helper_type="mother"),
    StoryParams(place="cafe", clue="spoon", magic="talking_timer", misunderstanding="stolen_recipe", child_name="Theo", child_type="boy", helper_name="Papa", helper_type="father"),
    StoryParams(place="grandma_house", clue="napkin", magic="pepper_spark", misunderstanding="haunting", child_name="Ivy", child_type="girl", helper_name="Grandma", helper_type="mother"),
    StoryParams(place="kitchen", clue="spoon", magic="glow_spoon", misunderstanding="haunting", child_name="Leo", child_type="boy", helper_name="Mama", helper_type="mother"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.magic is None or c[2] == args.magic)
              and (args.misunderstanding is None or c[3] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, magic, mis = rng.choice(sorted(combos))
    ct = args.child_type or rng.choice(["girl", "boy"])
    ht = args.helper_type or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        clue=clue,
        magic=magic,
        misunderstanding=mis,
        child_name=args.child_name or rng.choice(GIRL_NAMES if ct == "girl" else BOY_NAMES),
        child_type=ct,
        helper_name=args.helper_name or ( "Mama" if ht == "mother" else "Papa"),
        helper_type=ht,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
