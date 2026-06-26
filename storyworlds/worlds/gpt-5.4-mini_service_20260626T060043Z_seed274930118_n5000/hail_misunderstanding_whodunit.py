#!/usr/bin/env python3
"""
storyworlds/worlds/hail_misunderstanding_whodunit.py
=====================================================

A tiny whodunit-style storyworld built around hail and a misunderstanding.

Premise:
- A small group is sheltering at a garden house during a hailstorm.
- Something goes missing or appears broken.
- The first guess is wrong because the hail made a clue look suspicious.
- A child detective notices the real cause and clears up the misunderstanding.

The world is designed to produce short, complete mystery stories with a clear
turn from suspicion to explanation.
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    can_hail: bool = True
    can_mislead: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    answer: str
    kind: str
    misleading: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather = "hail"
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        other = World(self.place)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "caretaker": v.caretaker, "held_by": v.held_by, "location": v.location,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.weather = self.weather
        other.facts = dict(self.facts)
        return other


def _r_hail_clue(world: World) -> list[str]:
    out: list[str] = []
    for clue in [e for e in world.entities.values() if e.kind == "clue"]:
        if clue.meters.get("wet", 0) < THRESHOLD:
            continue
        sig = ("hail_mark", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The hail had left {clue.label} looking odd.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    helper = world.facts.get("helper")
    culprit = world.facts.get("culprit")
    clue = world.facts.get("clue")
    if not detective or not culprit or not clue:
        return out
    if clue.meters.get("wet", 0) < THRESHOLD:
        return out
    if clue.memes.get("confusing", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["doubt"] = detective.memes.get("doubt", 0) + 1
    helper.memes["alarm"] = helper.memes.get("alarm", 0) + 1
    culprit.memes["hurt"] = culprit.memes.get("hurt", 0) + 1
    out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [
    _r_hail_clue,
    _r_misunderstanding,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__misunderstanding__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def explain_world(world: World) -> str:
    return f"{world.place.name} was under a sharp hailstorm."


def introduce(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"{detective.id} was a little {detective.type} with a careful eye, and {helper.id} "
        f"was happy to help solve any puzzly thing."
    )
    world.say(f"{explain_world(world)}")


def mystery_setup(world: World, culprit: Entity, clue: Entity) -> None:
    world.say(
        f"Then {culprit.id} found {clue.phrase} and frowned. "
        f"'{clue.label} was here a minute ago,' {culprit.pronoun()} said."
    )


def accuse(world: World, detective: Entity, culprit: Entity, clue: Entity) -> None:
    culprit.memes["blame"] = culprit.memes.get("blame", 0) + 1
    clue.meters["wet"] = clue.meters.get("wet", 0) + 1
    clue.memes["confusing"] = clue.memes.get("confusing", 0) + 1
    world.say(
        f"{culprit.id} looked at the spotted {clue.label} and thought someone had taken it. "
        f"{detective.id} did not want to jump to a guess, so {detective.pronoun()} crouched beside the clue."
    )


def investigate(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    helper.memes["watchful"] = helper.memes.get("watchful", 0) + 1
    world.say(
        f"{detective.id} noticed the tiny dents on {clue.phrase} and the little white pellets on the sill."
    )
    world.say(
        f"{helper.id} pointed up at the roof edge and said the hail had been knocking things loose."
    )


def solve(world: World, detective: Entity, culprit: Entity, clue: Entity) -> None:
    culprit.memes["hurt"] = 0
    culprit.memes["relief"] = culprit.memes.get("relief", 0) + 1
    detective.memes["doubt"] = 0
    world.say(
        f"That was the answer: nobody had stolen {clue.label}. The hail had bounced it off the table and into the flower bed."
    )
    world.say(
        f"{culprit.id} laughed in relief, and {detective.id} tucked {clue.it()} back where it belonged."
    )


def end_image(world: World, culprit: Entity, clue: Entity) -> None:
    world.say(
        f"When the storm softened, {clue.label} sat dry on the shelf again, and {culprit.id} no longer looked worried."
    )


PLACES = {
    "garden_house": Place(name="the garden house", indoors=True, can_hail=True, can_mislead=True),
    "porch": Place(name="the porch", indoors=False, can_hail=True, can_mislead=True),
    "shed": Place(name="the shed", indoors=True, can_hail=True, can_mislead=True),
}

CLUES = {
    "blue_bell": Clue(
        id="blue_bell",
        label="blue bell",
        phrase="the blue bell on the table",
        answer="the hail knocked it over",
        kind="object",
        misleading=True,
    ),
    "glass_marble": Clue(
        id="glass_marble",
        label="glass marble",
        phrase="the glass marble in the tray",
        answer="the hail rattled the tray",
        kind="object",
        misleading=True,
    ),
    "tiny_key": Clue(
        id="tiny_key",
        label="tiny key",
        phrase="the tiny key by the window",
        answer="the wind and hail shook it loose",
        kind="object",
        misleading=True,
    ),
}

CULPRITS = {
    "cat": ("cat", "a sleepy cat"),
    "brother": ("boy", "a worried brother"),
    "aunt": ("aunt", "a careful aunt"),
    "gardener": ("man", "the gardener"),
}


@dataclass
class WorldFacts:
    detective: Entity
    helper: Entity
    culprit: Entity
    clue: Entity
    place: Place


def tell(place: Place, clue_cfg: Clue, culprit_name: str, culprit_type: str,
         detective_name: str, detective_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_type))
    clue = world.add(Entity(
        id=clue_cfg.id,
        kind="clue",
        type="thing",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        meters={"wet": 0.0},
        memes={"confusing": 0.0},
    ))

    introduce(world, detective, helper)
    world.para()
    mystery_setup(world, culprit, clue)
    accuse(world, detective, culprit, clue)
    investigate(world, detective, helper, clue)
    propagate(world, narrate=True)
    world.para()
    solve(world, detective, culprit, clue)
    end_image(world, culprit, clue)

    world.facts = {
        "detective": detective,
        "helper": helper,
        "culprit": culprit,
        "clue": clue,
        "place": place,
    }
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id in CLUES:
            if place.can_hail and place.can_mislead:
                for culprit_id in CULPRITS:
                    out.append((place_id, clue_id, culprit_id))
    return out


GIVEN_NAMES = ["Mina", "Toby", "Nora", "Eli", "Pip", "Ivy", "Ada", "Ben"]
HELPER_NAMES = ["June", "Otis", "Lena", "Max", "Ruby", "Theo"]
TRAITS = ["careful", "curious", "brave", "quiet", "quick"]


def pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice([n for n in GIVEN_NAMES if n[0] in "MNIPAJLR"])
    return rng.choice([n for n in GIVEN_NAMES if n[0] in "TEBOP"])


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hail-day whodunit with a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    dt = args.detective_type or rng.choice(["girl", "boy"])
    ht = args.helper_type or rng.choice(["girl", "boy"])
    dn = args.detective_name or rng.choice(GIVEN_NAMES)
    hn = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, clue=clue, culprit=culprit, detective_name=dn,
                       detective_type=dt, helper_name=hn, helper_type=ht)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short whodunit for a small child where hail creates a misunderstanding.",
        f"Tell a gentle mystery about {f['detective'].id} and {f['helper'].id} at {f['place'].name} during hail.",
        f"Write a story where {f['culprit'].id} thinks {f['clue'].label} is missing, but the hail made it look suspicious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective, helper, culprit, clue, place = f["detective"], f["helper"], f["culprit"], f["clue"], f["place"]
    return [
        QAItem(
            question=f"Who solved the mystery at {place.name}?",
            answer=f"{detective.id} solved it by looking closely at the clue and noticing what the hail had done."
        ),
        QAItem(
            question=f"Why did {culprit.id} think something bad had happened to {clue.label}?",
            answer=f"{culprit.id} saw {clue.phrase} looking wet and strange, so {culprit.pronoun()} first thought it was missing or taken."
        ),
        QAItem(
            question=f"What did {helper.id} notice that helped explain the mystery?",
            answer=f"{helper.id} noticed that hail had been knocking things loose, so the clue was not stolen at all."
        ),
        QAItem(
            question=f"What was the real answer in the story?",
            answer=f"The real answer was that the hail made {clue.label} look suspicious, and that caused the misunderstanding."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hail?",
            answer="Hail is frozen ice that falls from clouds like hard little pellets during some storms."
        ),
        QAItem(
            question="Why can hail make people confused about what happened?",
            answer="Hail can move things, leave wet spots, and make ordinary objects look broken or out of place."
        ),
        QAItem(
            question="What should a good detective do first?",
            answer="A good detective looks carefully, checks the clues, and does not guess too quickly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  weather={world.weather}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden_house", "blue_bell", "cat", "Mina", "girl", "June", "girl"),
    StoryParams("porch", "glass_marble", "brother", "Toby", "boy", "Lena", "girl"),
    StoryParams("shed", "tiny_key", "gardener", "Nora", "girl", "Max", "boy"),
]


ASP_RULES = r"""
place(P) :- place_id(P).
clue(C) :- clue_id(C).
culprit(K) :- culprit_id(K).

haily(P) :- place(P).
can_story(P,C,K) :- place(P), clue(C), culprit(K), haily(P).

#show can_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_id", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        if p.can_hail:
            lines.append(asp.fact("hail_ok", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue_id", cid))
    for kid in CULPRITS:
        lines.append(asp.fact("culprit_id", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CLUES[params.clue],
        params.culprit,
        CULPRITS[params.culprit][0],
        params.detective_name,
        params.detective_type,
        params.helper_name,
        params.helper_type,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} at {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
