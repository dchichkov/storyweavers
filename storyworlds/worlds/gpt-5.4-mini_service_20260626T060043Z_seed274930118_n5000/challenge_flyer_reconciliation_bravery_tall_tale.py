#!/usr/bin/env python3
"""
storyworlds/worlds/challenge_flyer_reconciliation_bravery_tall_tale.py
======================================================================

A small tall-tale storyworld about a child, a challenge, a flyer, and a brave
reconciliation.

Premise:
- A child is asked to carry a flyer to the biggest spot in town.
- A windy mishap turns the flyer into a challenge.
- Brave effort and a sincere apology lead to reconciliation.

The world model tracks physical meters and emotional memes so the prose is
driven by state instead of template swapping.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    windiness: str
    crowd: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Flyer:
    id: str
    phrase: str
    title: str
    subject: str
    size: str
    color: str
    can_blur: bool = False


@dataclass
class Challenge:
    id: str
    name: str
    verb: str
    threat: str
    mess: str
    takes: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    offers: str
    covers: set[str]
    soothes: str
    tag: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.wind: str = ""

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
        clone.wind = self.wind
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    flyer: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "town_square": Place("the town square", "blustery", "busy", {"flyer"}),
    "market": Place("the market lane", "windy", "busy", {"flyer"}),
    "hill": Place("the hilltop road", "wild", "open", {"flyer"}),
}

CHALLENGES = {
    "wind": Challenge(
        id="wind",
        name="the wind challenge",
        verb="carry the flyer",
        threat="the wind could snag it",
        mess="torn",
        takes="whipped",
        keyword="challenge",
        tags={"wind", "challenge"},
    ),
    "rain": Challenge(
        id="rain",
        name="the rain challenge",
        verb="deliver the flyer",
        threat="the rain could blur the ink",
        mess="smeared",
        takes="spattered",
        keyword="challenge",
        tags={"rain", "challenge"},
    ),
}

FLYERS = {
    "fair": Flyer(
        id="fair",
        phrase="a bright flyer for the summer fair",
        title="summer fair",
        subject="fair",
        size="large",
        color="yellow",
        can_blur=True,
    ),
    "parade": Flyer(
        id="parade",
        phrase="a bold flyer for the noon parade",
        title="noon parade",
        subject="parade",
        size="wide",
        color="red",
        can_blur=True,
    ),
    "show": Flyer(
        id="show",
        phrase="a neat flyer for the magic show",
        title="magic show",
        subject="show",
        size="small",
        color="blue",
        can_blur=True,
    ),
}

HELPERS = {
    "clip": Helper(
        id="clip",
        label="a silver clip",
        offers="clip the flyer to a board",
        covers={"hands"},
        soothes="kept the paper steady",
        tag="help",
    ),
    "tube": Helper(
        id="tube",
        label="a poster tube",
        offers="put the flyer in a poster tube",
        covers={"arms"},
        soothes="kept the flyer safe",
        tag="help",
    ),
    "hat": Helper(
        id="hat",
        label="a wide-brim hat",
        offers="hold the flyer under a wide-brim hat",
        covers={"head"},
        soothes="shaded the ink",
        tag="bravery",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Zara", "Ruth"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Eli", "Tate"]
TRAITS = ["brave", "lively", "stubborn", "cheerful", "bold", "quick"]


def challenge_at_risk(challenge: Challenge, flyer: Flyer) -> bool:
    return flyer.can_blur or challenge.id == "wind"


def select_helper(challenge: Challenge, flyer: Flyer) -> Optional[Helper]:
    if challenge.id == "wind":
        return HELPERS["clip"]
    if challenge.id == "rain":
        return HELPERS["tube"]
    return None


def predict_damage(world: World, hero: Entity, challenge: Challenge, flyer: Entity) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    f = sim.get(flyer.id)
    return {
        "ruined": f.meters.get("ruined", 0) >= THRESHOLD or f.meters.get("blurred", 0) >= THRESHOLD,
        "stress": sum(e.memes.get("fear", 0) for e in sim.characters()),
    }


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if challenge.id == "wind":
        hero.meters["wind"] = hero.meters.get("wind", 0) + 1
        world.facts["windy"] = True
        for ent in world.entities.values():
            if ent.kind == "thing" and ent.carried_by == hero.id:
                ent.meters["blown"] = ent.meters.get("blown", 0) + 1
                if ent.id == "flyer":
                    ent.meters["rumpled"] = ent.meters.get("rumpled", 0) + 1
                    out.append("The wind snatched at the flyer like a big invisible hand.")
    elif challenge.id == "rain":
        hero.meters["rain"] = hero.meters.get("rain", 0) + 1
        for ent in world.entities.values():
            if ent.kind == "thing" and ent.carried_by == hero.id:
                if ent.id == "flyer":
                    ent.meters["blurred"] = ent.meters.get("blurred", 0) + 1
                    out.append("The rain dotted the flyer with little silver freckles.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who could outwalk a dog and outstare a thundercloud."
    )


def describe_flyer(world: World, hero: Entity, flyer: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    flyer.carried_by = hero.id
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {flyer.phrase} as if it were a treasure map."
    )


def arrive(world: World, hero: Entity) -> None:
    world.say(
        f"One day {hero.id} went to {world.place.name}, where the air was {world.place.windiness} and the crowd was {world.place.crowd}."
    )


def challenge_begins(world: World, hero: Entity, challenge: Challenge, flyer: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"{hero.id} wanted to {challenge.verb}, but {challenge.threat}."
    )


def warn(world: World, hero: Entity, challenge: Challenge, flyer: Entity) -> bool:
    pred = predict_damage(world, hero, challenge, flyer)
    if not pred["ruined"]:
        return False
    world.facts["predicted_damage"] = challenge.mess
    world.say(
        f'"That flyer will get {challenge.mess}," {hero.pronoun("possessive")} helper said, "if we do nothing clever."'
    )
    return True


def brave_try(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"{hero.id} took a breath big enough to fill a sail and tried anyway."
    )


def stumble(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    world.say(
        f"The first try went crooked, and {hero.id} felt the mistake sting like a briar."
    )


def apology(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    world.say(
        f"{hero.id} looked up and said, 'I am sorry for the crooked try.'"
    )


def reconcile(world: World, hero: Entity, helper: Entity, flyer: Entity, challenge: Challenge, helper_def: Helper) -> None:
    hero.memes["fear"] = 0
    hero.memes["shame"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    flyer.meters["ruined"] = 0
    world.say(
        f"{helper.label.capitalize()} {helper_def.soothes}, and {hero.id} and {hero.pronoun('possessive')} helper made peace."
    )
    world.say(
        f"They used {helper.label} to {helper_def.offers}, and then the flyer stood straight as a flagpole in a parade."
    )
    world.say(
        f"That brave little plan turned the trouble into reconciliation, and the flyer reached its spot clean and shining."
    )


def tell(place: Place, challenge: Challenge, flyer_cfg: Flyer, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         helper_id: str = "clip") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["brave"])))
    helper = world.add(Entity(id="Helper", kind="character", type="helper", label="the helper"))
    flyer = world.add(Entity(id=flyer_cfg.id, type="flyer", label=flyer_cfg.subject, phrase=flyer_cfg.phrase, owner=hero.id))
    flyer.carried_by = hero.id
    tool = world.add(Entity(id=helper_id, type="tool", label=HELPERS[helper_id].label))
    world.facts.update(hero=hero, helper=helper, flyer=flyer, challenge=challenge, flyer_cfg=flyer_cfg, tool=tool)

    introduce(world, hero)
    describe_flyer(world, hero, flyer)
    world.para()
    arrive(world, hero)
    challenge_begins(world, hero, challenge, flyer)
    warn(world, hero, challenge, flyer)
    brave_try(world, hero, challenge)
    _do_challenge(world, hero, challenge)
    stumble(world, hero, challenge)
    world.para()
    apology(world, hero, challenge)
    reconcile(world, hero, helper, flyer, challenge, HELPERS[helper_id])
    return world


SETTINGS = PLACES

VALID = [
    ("town_square", "wind", "fair"),
    ("market", "wind", "parade"),
    ("hill", "rain", "show"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return list(VALID)


@dataclass
class StoryParams:
    place: str
    challenge: str
    flyer: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "challenge": [(
        "What is a challenge?",
        "A challenge is a hard task that asks someone to try carefully and keep going."
    )],
    "flyer": [(
        "What is a flyer?",
        "A flyer is a small printed paper that tells people about an event."
    )],
    "bravery": [(
        "What does bravery mean?",
        "Bravery means trying something hard even when you feel a little scared."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace again after people have had a problem or argument."
    )],
}
KNOWLEDGE_ORDER = ["challenge", "flyer", "bravery", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a tall-tale story about a child named {hero.id}, a challenge, and a flyer.',
        f"Tell a brave little story where {hero.id} carries a flyer and later makes peace after a mistake.",
        f'Write a child-friendly tall tale that uses the words "challenge" and "flyer" and ends with reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, flyer, challenge = f["hero"], f["flyer_cfg"], f["challenge"]
    helper = f["helper"]
    trait = next((t for t in hero.traits if t != "little"), "brave")
    return [
        QAItem(
            question=f"What was {hero.id} carrying in the story?",
            answer=f"{hero.id} was carrying {hero.pronoun('possessive')} {flyer.phrase}."
        ),
        QAItem(
            question=f"What made the story a challenge for {hero.id}?",
            answer=f"It was a challenge because {challenge.threat}, so the flyer could get {challenge.mess}."
        ),
        QAItem(
            question=f"Who helped {hero.id} after the mistake?",
            answer=f"{helper.label.capitalize()} helped {hero.id} calm down, fix the problem, and make reconciliation."
        ),
        QAItem(
            question=f"How did {trait} {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by taking a breath, trying again, and staying with the hard task."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    tags.add("flyer")
    tags.add("bravery")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
challenge_at_risk(C,F) :- challenge(C), flyer(F).
needs_fix(C,F) :- challenge_at_risk(C,F).
valid_story(P,C,F) :- place(P), challenge(C), flyer(F), affords(P,F), needs_fix(C,F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for fid in FLYERS:
        lines.append(asp.fact("flyer", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: challenge, flyer, bravery, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--flyer", choices=FLYERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.flyer is None or c[2] == args.flyer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, flyer = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, flyer=flyer, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], FLYERS[params.flyer],
                 hero_name=params.name, hero_type=params.gender, hero_traits=[params.trait],
                 helper_id=params.helper)
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
    StoryParams(place="town_square", challenge="wind", flyer="fair", name="Mina", gender="girl", helper="clip", trait="brave"),
    StoryParams(place="market", challenge="wind", flyer="parade", name="Owen", gender="boy", helper="clip", trait="bold"),
    StoryParams(place="hill", challenge="rain", flyer="show", name="Ivy", gender="girl", helper="tube", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.challenge} at {p.place} (flyer: {p.flyer})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
