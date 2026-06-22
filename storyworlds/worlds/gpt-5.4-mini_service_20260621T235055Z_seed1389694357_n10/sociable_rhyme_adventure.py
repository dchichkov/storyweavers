#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10/sociable_rhyme_adventure.py
======================================================================================================

A tiny adventure storyworld where a sociable child, a rhyme clue, and a small
quest lead to a safe, vivid ending.

The domain is built from a seed prompt that asks for:
- the word "sociable"
- a rhyme feature
- an adventure style

This world keeps the plot small and physical:
- the children set off on a trail
- a clue is missing, hidden, or hard to reach
- a sociable helper changes the plan
- the group solves the problem together
- the ending image proves what changed

The prose aims for child-facing adventure rhythm with gentle rhyme echoes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

# Robust bootstrap: walk upward until we find results.py, then add that directory.
_HERE = Path(__file__).resolve()
for _parent in [_HERE.parent, *_HERE.parents]:
    if (_parent / "results.py").exists():
        sys.path.insert(0, str(_parent))
        break
else:
    raise RuntimeError("Could not locate storyworlds/results.py")

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"tired": 0.0, "found": 0.0, "mud": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "courage": 0.0, "trust": 0.0}

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    description: str
    dark_nook: str
    sound: str
    clue_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    rhyme: str
    reachable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    phrase: str
    trait: str
    help_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestFix:
    id: str
    method: str
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("found", 0.0) >= THRESHOLD:
            sig = ("found", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["joy"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES = [Rule("tired", _r_tired)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    collected: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                collected.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in collected:
            world.say(s)


def trail_needs_help(place: Place, clue: Clue) -> bool:
    return clue.reachable and clue.id == place.clue_kind


def rhyme_hint(place: Place, clue: Clue) -> str:
    return f"{place.sound} and {clue.rhyme}"


def can_solve(fix: QuestFix, clue: Clue, companion: Companion) -> bool:
    return fix.power >= 1 and clue.reachable and companion.trait == "sociable"


def predict_success(world: World, hero: Entity, companion: Entity, clue: Clue, fix: QuestFix) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["courage"] += 1
    sim.get(companion.id).memes["trust"] += 1
    return can_solve(fix, clue, Companion(id="x", label="", phrase="", trait=companion.attrs["trait"], help_line=""))


def setup(world: World, hero: Entity, companion: Entity, place: Place, clue: Clue) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"On a bright day, {hero.id} and {companion.id} set off in {place.label}. "
        f"{place.description}"
    )
    world.say(
        f"They loved the little adventure because every turn promised a rhyme and a surprise."
    )


def miss_clue(world: World, hero: Entity, place: Place, clue: Clue) -> None:
    world.say(
        f"But the path led to {place.dark_nook}, and the only sound was {place.sound}. "
        f"{hero.id} looked around and said, \"We need the missing clue.\""
    )
    world.say(
        f"The clue should have been a {clue.label}, but it was hidden out of sight."
    )


def sociable_offer(world: World, companion: Entity, hero: Entity, place: Place) -> None:
    companion.memes["trust"] += 1
    world.say(
        f'{companion.id} smiled, because {companion.id} was {companion.attrs["trait"]}. '
        f'"Come on," {companion.id} said, "{companion.help_line}"'
    )
    world.say(
        f"{hero.id} listened. The trail felt less lonely and more like a song."
    )


def fetch_and_find(world: World, hero: Entity, companion: Entity, clue: Clue, fix: QuestFix) -> None:
    hero.meters["found"] += 1
    companion.meters["found"] += 1
    world.say(
        f"They chose a simple way forward: {fix.text}. Together they reached the hidden spot."
    )
    world.say(
        f"There, {hero.id} found the {clue.label}, and {companion.id} laughed with relief."
    )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, companion: Entity, place: Place, clue: Clue) -> None:
    world.say(
        f"In the end, the {clue.label} was safe in {hero.id}'s hand, and the trail in {place.label} "
        f"shone like a story told aloud. {hero.id} and {companion.id} walked home side by side, "
        f"still rhyming, still smiling."
    )


def tell(place: Place, clue: Clue, companion: Companion, fix: QuestFix,
         hero_name: str = "Mia", hero_gender: str = "girl", partner_name: str = "Noah",
         partner_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(
        id=partner_name, kind="character", type=partner_gender, role="companion",
        traits=[companion.trait], attrs={"trait": companion.trait}
    ))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["companion"] = companion
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    setup(world, hero, helper, place, clue)
    world.para()
    miss_clue(world, hero, place, clue)
    sociable_offer(world, helper, hero, place)
    world.para()
    fetch_and_find(world, hero, helper, clue, fix)
    ending(world, hero, helper, place, clue)
    return world


PLACES = {
    "forest": Place(
        id="forest", label="the forest trail", description="Tall trees made a green roof overhead.",
        dark_nook="a mossy hollow", sound="the hush of leaves", clue_kind="map",
        tags={"forest", "trail"},
    ),
    "harbor": Place(
        id="harbor", label="the harbor pier", description="The boards creaked while gulls circled above.",
        dark_nook="the end of the pier", sound="the cry of gulls", clue_kind="lantern",
        tags={"harbor", "pier"},
    ),
    "hill": Place(
        id="hill", label="the windy hill", description="The grass bowed low and the sky felt wide.",
        dark_nook="a narrow ridge", sound="the whistle of wind", clue_kind="flag",
        tags={"hill", "ridge"},
    ),
}

CLUES = {
    "map": Clue(id="map", label="map scrap", phrase="a torn little map", rhyme="trap", reachable=True, tags={"map"}),
    "lantern": Clue(id="lantern", label="lantern key", phrase="a tiny lantern-shaped key", rhyme="star", reachable=True, tags={"lantern"}),
    "flag": Clue(id="flag", label="red flag", phrase="a bright red flag", rhyme="dash", reachable=True, tags={"flag"}),
}

COMPANIONS = {
    "sociable": Companion(
        id="Pip", label="Pip", phrase="a sociable friend", trait="sociable",
        help_line="let's ask, laugh, and look together", tags={"sociable"},
    ),
    "cheery": Companion(
        id="Tess", label="Tess", phrase="a cheery friend", trait="cheery",
        help_line="let's sing the clue into view", tags={"cheery"},
    ),
}

FIXES = {
    "search": QuestFix(id="search", method="search", power=1, text="they searched near the roots and under the stones", qa_text="searched near the roots and under the stones", tags={"search"}),
    "ask": QuestFix(id="ask", method="ask", power=1, text="they asked a kind ranger for one small hint", qa_text="asked a kind ranger for one small hint", tags={"ask"}),
}


@dataclass
class StoryParams:
    place: str
    clue: str
    companion: str
    fix: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="forest", clue="map", companion="sociable", fix="search", hero_name="Mia", hero_gender="girl", partner_name="Pip", partner_gender="boy"),
    StoryParams(place="harbor", clue="lantern", companion="sociable", fix="ask", hero_name="Leo", hero_gender="boy", partner_name="Pip", partner_gender="boy"),
    StoryParams(place="hill", clue="flag", companion="cheery", fix="search", hero_name="Ava", hero_gender="girl", partner_name="Tess", partner_gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CLUES:
            if trail_needs_help(PLACES[p], CLUES[c]):
                for comp in COMPANIONS:
                    for fx in FIXES:
                        if can_solve(FIXES[fx], CLUES[c], COMPANIONS[comp]):
                            out.append((p, c, comp))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small sociable rhyme adventure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, companion = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(["Mia", "Ava", "Leo", "Noah", "Zoe", "Eli"])
    partner_name = args.partner_name or rng.choice(["Pip", "Tess", "Milo", "June"])
    return StoryParams(place=place, clue=clue, companion=companion, fix=fix,
                       hero_name=hero_name, hero_gender=hero_gender,
                       partner_name=partner_name, partner_gender=partner_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.companion not in COMPANIONS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], CLUES[params.clue], COMPANIONS[params.companion], FIXES[params.fix],
                 hero_name=params.hero_name, hero_gender=params.hero_gender,
                 partner_name=params.partner_name, partner_gender=params.partner_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the word "sociable" and a small rhyme clue in {f["place"].label}.',
        f"Tell a child-friendly quest where {f['hero'].id} and {f['helper'].id} search for a hidden {f['clue'].label}.",
        f'Write a short adventure with a sociable helper who makes the search feel like a rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    clue = f["clue"]
    comp = f["companion"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What kind of friend is {helper.id} in the story?",
            answer=f"{helper.id} is sociable, so {helper.id} is the kind of friend who makes the adventure feel friendly and easy to share. That helped the group keep going when the clue was hard to find.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.id} need help in {place.label}?",
            answer=f"They needed help because the clue was hidden in the trail, and the first look did not find it. The sociable helper made the search feel calm instead of stuck.",
        ),
        QAItem(
            question=f"What did they do to find the {clue.label}?",
            answer=f"They chose to {fix.qa_text} together. That shared plan fits the adventure because they searched as a pair instead of giving up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sociable mean?",
            answer="Sociable means friendly and happy to be with other people. A sociable person likes sharing, talking, and doing things together.",
        ),
        QAItem(
            question="What is a clue in an adventure?",
            answer="A clue is a small piece of information that helps you solve a mystery or find something hidden. Clues can be maps, signs, keys, or marks on the path.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} role={e.role} traits={e.traits} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,Comp) :- place(P), clue(C), companion(Comp), needs_help(P,C), sociable(Comp).
needs_help(P,C) :- place(P), clue(C), clue_kind(P,C).
sociable(sociable).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("clue_kind", pid, p.clue_kind))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for comp in COMPANIONS:
        lines.append(asp.fact("companion", comp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK")
    return rc


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does sociable mean?", "Sociable means friendly and happy to be with other people. A sociable person likes sharing, talking, and doing things together."),
        QAItem("What is a clue in an adventure?", "A clue is a small piece of information that helps you solve a mystery or find something hidden. Clues can be maps, signs, keys, or marks on the path."),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
