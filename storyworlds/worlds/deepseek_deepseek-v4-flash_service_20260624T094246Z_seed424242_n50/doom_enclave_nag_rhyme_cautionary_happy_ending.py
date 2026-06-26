#!/usr/bin/env python3
"""
storyworlds/worlds/doom_enclave_nag_rhyme_cautionary_happy_ending.py
====================================================================

A standalone storyworld sketch in folk-tale style: a small creature in a
safe *enclave* ignores the *nag* (elder's warning) and nearly meets *doom*,
but a clever compromise brings a *happy ending*.  The story is rendered in
rhyming couplets.

Domain: doom, enclave, nag
Features: Rhyme, Cautionary, Happy Ending
Style: Folk Tale
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

# ---------------------------------------------------------------------------
# Thresholds & constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity model (shared by characters and things)
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # bunny, grandmother, fox, scarf, decoy, ...
    label: str = ""
    phrase: str = ""               # full description for story text
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # not used here, kept for compatibility
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"bunny", "rabbit", "fox"}
        female = {"grandmother", "mother", "aunt"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "mother": "mama"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    inside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Venture:
    """The exciting-but-risky activity the hero wants to do."""
    id: str
    verb: str          # after "wanted to ..."   : "hop to the meadow"
    gerund: str        # after "loved ... and " : "hopping in the meadow"
    rush: str          # after "tried to ..."   : "scamper out of the burrow"
    danger: str        # the doom keyword      : "fox"
    hazard: str        # how it would end       : "met a big fox"
    caution: str       # elder's worry          : "the fox is sly and quick"
    skill: str         # what saves them        : "hide behind the scarecrow"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The precious thing the hero loves and wears, at risk."""
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"bunny", "rabbit"})


@dataclass
class Compromise:
    """The safe trick that resolves the conflict."""
    id: str
    name: str
    prep: str          # offer: "we'll take the old scarecrow"
    tail: str          # what they do: "put the scarecrow at the meadow's edge"
    plural: bool = False
    gender_ok: set[str] = field(default_factory=lambda: {"bunny", "rabbit"})


SETTINGS = {
    "burrow": Setting(place="the cozy burrow", inside=True, affords={"meadow", "field"}),
    "warren": Setting(place="the warm warren", inside=True, affords={"meadow", "field"}),
    "den": Setting(place="the safe den", inside=True, affords={"meadow"}),
}

VENTURES = {
    "meadow": Venture(
        id="meadow",
        verb="hop to the meadow",
        gerund="hopping in the meadow",
        rush="scamper out of the burrow",
        danger="doom",
        hazard="met a big fox",
        caution="the fox is sly and quick",
        skill="hide behind the scarecrow",
        tags={"meadow", "fox", "scarecrow"},
    ),
    "field": Venture(
        id="field",
        verb="race across the field",
        gerund="racing across the field",
        rush="dash out of the warren",
        danger="doom",
        hazard="saw the fox's tail",
        caution="the fox can outrun you",
        skill="duck into the hollow log",
        tags={"field", "fox", "log"},
    ),
}

PRIZES = {
    "scarf": Prize(
        label="woollen scarf",
        phrase="a soft woollen scarf as red as a berry",
        type="scarf",
        genders={"bunny", "rabbit"},
    ),
    "hat": Prize(
        label="pointy hat",
        phrase="a pointy hat with a tiny bell",
        type="hat",
        genders={"bunny", "rabbit"},
    ),
    "vest": Prize(
        label="furry vest",
        phrase="a furry vest that smelled like pine",
        type="vest",
        genders={"bunny", "rabbit"},
    ),
}

COMPROMISES = {
    "scarecrow": Compromise(
        id="scarecrow",
        name="an old scarecrow",
        prep="we'll take the old scarecrow",
        tail="stood the scarecrow in the meadow",
    ),
    "log": Compromise(
        id="log",
        name="a hollow log",
        prep="we'll hide behind the hollow log",
        tail="crouched behind the log",
    ),
}

# Characters are fixed: hero (bunny), nag (grandmother), doom (fox).
NAG_TYPES = ["grandmother", "grandfather", "aunt", "uncle"]
BUNNY_NAMES = ["Pip", "Toby", "Lily", "Nibbles", "Bella", "Coco", "Flopsy", "Mopsy", "Cotton", "Truffle"]
TRAITS = ["curious", "brave", "bold", "cheerful", "hopeful", "lively"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rhyme helpers – we build quatrains (AABB) from state
# ---------------------------------------------------------------------------
def rhyme_a(line: str) -> str:
    # very simple: we just return the line and assume the caller pairs matching rhymes
    return line


def hero_rhyme(hero: Entity, venture: Venture) -> str:
    # first couplet
    a = f"Little {hero.type} {hero.id} lived in {hero.pronoun('possessive')} burrow so deep,"
    b = f"And dreamed of the meadow where the tall grasses leap."
    return f"{a}\n{b}"


def nag_rhyme(nag: Entity, hero: Entity, venture: Venture) -> str:
    a = f'"Stay inside!" {nag.label_word} would {nag.pronoun('possessive')} gentle {nag.type} nag,'
    b = f'"The {venture.danger} is near – do not {venture.gerund} and lag!"'
    return f"{a}\n{b}"


def prize_rhyme(hero: Entity, prize: Entity, nag: Entity) -> str:
    a = f"Then {nag.label_word} bought {hero.pronoun('object')} {prize.phrase},"
    b = f"{hero.id} wore it with joy each day and each phase."
    return f"{a}\n{b}"


def desire_rhyme(hero: Entity, venture: Venture) -> str:
    a = f"But one day {hero.pronoun()} wanted to {venture.verb} so strong,"
    b = f"{hero.pronoun('possessive').capitalize()} little paws itched to scamper along."
    return f"{a}\n{b}"


def warn_rhyme(nag: Entity, hero: Entity, venture: Venture) -> str:
    a = f'"If you go," {nag.label_word} said, "{venture.caution},"'
    b = f'"And your {hero.label or 'safety'} will be lost in a flash!"'
    return f"{a}\n{b}"


def defy_rhyme(hero: Entity, venture: Venture) -> str:
    a = f"{hero.label} heard the warning but {hero.pronoun()} did not stay,"
    b = f"{hero.pronoun('possessive').capitalize()} heart was too eager – {hero.pronoun()} {venture.rush}."
    return f"{a}\n{b}"


def doom_rhyme(hero: Entity, doom: Entity, venture: Venture) -> str:
    a = f"Just past the hedge, a {doom.type} crept with a glare,"
    b = f"{doom.label} was the doom, and the {venture.danger} was there."
    return f"{a}\n{b}"


def grab_rhyme(nag: Entity, hero: Entity) -> str:
    a = f"But {nag.label_word} {nag.pronoun()} grabbed {hero.pronoun('possessive')} paw at the last,"
    b = f'"Wait, dear, I have a plan safe and fast!"'
    return f"{a}\n{b}"


def compromise_rhyme(comp: Compromise, nag: Entity, hero: Entity, venture: Venture) -> str:
    a = f'"We will {comp.name}," {nag.label_word} said with a nod,'
    b = f'"Then you can {venture.verb} without any {venture.danger}!"'
    return f"{a}\n{b}"


def happy_ending_rhyme(hero: Entity, nag: Entity, comp: Compromise, venture: Venture) -> str:
    a = f"They {nag.label_word} and {hero.id} {comp.tail}, and the meadow was bright,"
    b = f"{hero.id} played safe and the {venture.danger} took flight."
    return f"{a}\n{b}"


# ---------------------------------------------------------------------------
# Causal rules (minimal)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_frighten(world: World) -> list[str]:
    """If hero goes near meadow and fox is present, add fright."""
    out = []
    for actor in world.characters():
        if actor.meters.get("near_danger", 0) >= THRESHOLD and world.entities.get("fox"):
            sig = ("fright", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["fear"] += 1
            actor.memes["defiance"] -= 0.5
            out.append(f"{actor.label} felt a shiver of doom.")
    return out


def _r_rescue(world: World) -> list[str]:
    """When compromise is used, reduce fear and increase joy."""
    for actor in world.characters():
        if actor.memes.get("saved_by_compromise", 0) >= THRESHOLD:
            sig = ("rescue", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["joy"] += 1
            actor.memes["fear"] = 0
            out.append(f"{actor.label} felt safe again.")
            return out
    return []


CAUSAL_RULES = [
    Rule("frighten", "social", _r_frighten),
    Rule("rescue", "social", _r_rescue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


# ---------------------------------------------------------------------------
# Prediction (simple check – does the venture lead to danger?)
# ---------------------------------------------------------------------------
def is_dangerous(world: World, hero: Entity, venture: Venture) -> bool:
    # always true for this domain
    return True


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(setting: Setting, venture: Venture, prize_cfg: Prize,
         comp: Compromise, hero_name: str = "Pip",
         hero_traits: Optional[list[str]] = None,
         nag_type: str = "grandmother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="bunny",
        label=hero_name,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    nag = world.add(Entity(
        id="Nag",
        kind="character",
        type=nag_type,
        label=nag_type,
    ))
    doom = world.add(Entity(
        id="doom",
        kind="character",
        type="fox",
        label="a sly fox",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))

    # Act 1: Setting and love
    world.say(hero_rhyme(hero, venture))
    world.say(nag_rhyme(nag, hero, venture))
    world.say(prize_rhyme(hero, prize, nag))

    # Act 2: Desire and defiance
    world.para()
    world.say(desire_rhyme(hero, venture))
    world.say(warn_rhyme(nag, hero, venture))
    world.say(defy_rhyme(hero, venture))
    world.say(doom_rhyme(hero, doom, venture))

    # Tension: nigh doom, then grab
    world.para()
    world.say(grab_rhyme(nag, hero))

    # Act 3: Compromise and happy ending
    world.say(compromise_rhyme(comp, nag, hero, venture))
    world.say(happy_ending_rhyme(hero, nag, comp, venture))

    # Record facts for QA
    world.facts.update(hero=hero, nag=nag, doom=doom, prize=prize,
                       prize_cfg=prize_cfg, venture=venture, setting=setting,
                       comp=comp, resolved=True)

    return world


# ---------------------------------------------------------------------------
# Valid combos (simplified – always viable in this domain)
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, venture, prize) – all are compatible here."""
    combos = []
    for s in SETTINGS:
        for v in VENTURES:
            for p in PRIZES:
                combos.append((s, v, p))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    venture: str
    prize: str
    compromise: str
    name: str
    nag: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generate prompts & QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    nag = f["nag"]
    venture = f["venture"]
    comp = f["comp"]
    return [
        f'Write a folk tale about a little {hero.type} named {hero.id} who learns to listen to {nag.label_word}.',
        f'A cautionary rhyming story featuring {venture.danger}, {nag.label_word}, and a happy ending with {comp.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    nag = f["nag"]
    doom = f["doom"]
    venture = f["venture"]
    prize = f["prize"]
    comp = f["comp"]
    qa = [
        QAItem(
            question=f"Who warned {hero.id} about the {venture.danger}?",
            answer=f"{nag.label_word.capitalize()} warned {hero.id} about the {doom.type} that lurked near the meadow."
        ),
        QAItem(
            question=f"What did {hero.id} wear that {nag.label_word} had given?",
            answer=f"{hero.id} wore {prize.phrase}, a gift from {nag.label_word}."
        ),
        QAItem(
            question=f"What dangerous animal nearly caught {hero.id}?",
            answer=f"A {doom.type} almost caught {hero.id} when {hero.pronoun()} went to the meadow."
        ),
        QAItem(
            question=f"How did {nag.label_word} save {hero.id}?",
            answer=f"{nag.label_word.capitalize()} used {comp.name} to scare the {doom.type} away, so {hero.id} could play safely."
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to listen to {nag.label_word} and that playing safe is better than facing doom."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    # Simple folk-knowledge questions
    tags = world.facts["venture"].tags
    qa = []
    if "fox" in tags:
        qa.append(QAItem("Why are foxes dangerous to small animals?",
                         "Foxes are quick and sly, and they hunt small creatures like rabbits and bunnies."))
    if "scarecrow" in tags:
        qa.append(QAItem("What does a scarecrow do?",
                         "A scarecrow stands in a field and scares away birds and other animals that might eat the crops."))
    if "meadow" in tags:
        qa.append(QAItem("What is a meadow?",
                         "A meadow is a grassy field full of flowers and insects, a nice place to play – but sometimes with dangers."))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a bunny, a nag, and doom, ending happily.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--venture", choices=VENTURES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--nag", choices=NAG_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.venture is None or c[1] == args.venture)
                and (args.prize is None or c[2] == args.prize)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")

    place, venture, prize_id = rng.choice(sorted(filtered))
    # Choose a compromise that matches venture (simple: venture+comp same id)
    comp_id = venture  # map venture to comp
    if comp_id not in COMPROMISES:
        comp_id = rng.choice(list(COMPROMISES.keys()))
    nag = args.nag or rng.choice(NAG_TYPES)
    name = args.name or rng.choice(BUNNY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        venture=venture,
        prize=prize_id,
        compromise=comp_id,
        name=name,
        nag=nag,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        VENTURES[params.venture],
        PRIZES[params.prize],
        COMPROMISES[params.compromise],
        params.name,
        [params.trait],
        params.nag,
    )
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
        print("--- trace omitted for brevity ---")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP (minimal – just a placeholder for contract compliance)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Simple identity: every combo is valid in this domain.
valid(S, V, P) :- setting(S), venture(V), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for v in VENTURES:
        lines.append(asp.fact("venture", v))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for s, v, p in triples:
            print(f"  {s:7} {v:7} {p:7}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        # Curated set – just one example
        params = StoryParams("burrow", "meadow", "scarf", "scarecrow", "Pip", "grandmother", "curious")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.venture} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
