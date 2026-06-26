#!/usr/bin/env python3
"""
A standalone storyworld for a tiny mythic domain about a commission, a healer,
and a repeated, careful treatment with hydrocortisone.

The seed premise:
- A ruler commissions a remedy.
- A child or helper has an itchy rash.
- A healer repeats a gentle treatment until the skin calms.
- The story should feel mythic: formal, symbolic, and concrete.

The core world model tracks:
- physical meters: itch, swelling, calm, dew, distance, rest, warmth
- emotional memes: hope, worry, trust, pride, relief

Repetition is the main instrument:
- repeated washing
- repeated application of hydrocortisone
- repeated nightly checks
- repeated speech formulas in the mythic style
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "priestess"}
        male = {"boy", "father", "king", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Realm:
    place: str
    tone: str = "mythic"
    herbs: set[str] = field(default_factory=set)
    events: list[str] = field(default_factory=list)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    kind: str
    guards: set[str]
    repeat: str
    use_verb: str
    spread: str
    ending: str


@dataclass
class Commission:
    id: str
    label: str
    phrase: str
    purpose: str
    bearer: str = ""


@dataclass
class World:
    realm: Realm
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        return World(realm=copy.deepcopy(self.realm),
                     entities=copy.deepcopy(self.entities),
                     fired=set(self.fired),
                     paragraphs=[[]],
                     facts=copy.deepcopy(self.facts))


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    caretaker: str
    caretaker_kind: str
    commission: str
    remedy: str
    seed: Optional[int] = None


PLACES = {
    "temple": Realm(place="the sunlit temple", herbs={"aloe", "water", "linen"}),
    "courtyard": Realm(place="the old courtyard", herbs={"aloe", "water", "linen"}),
    "river_gate": Realm(place="the river gate", herbs={"water", "linen"}),
}

HEROES = [
    ("Mira", "girl"),
    ("Oren", "boy"),
    ("Nia", "girl"),
    ("Toma", "boy"),
]

CARETAKERS = [
    ("priestess", "priestess"),
    ("healer", "priest"),
    ("queen", "queen"),
    ("king", "king"),
]

COMMISSIONS = {
    "royal_seal": Commission(
        id="royal_seal",
        label="royal commission",
        phrase="a royal commission sealed in wax",
        purpose="to bring the rash down before the moon feast",
    ),
    "healers_call": Commission(
        id="healers_call",
        label="healer's commission",
        phrase="a healer's commission written on a reed tablet",
        purpose="to find a gentle cure for the itching skin",
    ),
}

REMEDIES = {
    "hydrocortisone": Remedy(
        id="hydrocortisone",
        label="hydrocortisone",
        phrase="a small jar of hydrocortisone cream",
        kind="cream",
        guards={"itch", "swelling"},
        repeat="again and again",
        use_verb="smooth",
        spread="gently over the rash",
        ending="the skin grew calm",
    ),
    "oat_salve": Remedy(
        id="oat_salve",
        label="oat salve",
        phrase="a bowl of oat salve",
        kind="salve",
        guards={"itch"},
        repeat="night after night",
        use_verb="spread",
        spread="over the red patches",
        ending="the itching faded",
    ),
}

TRAITS = ["steadfast", "gentle", "curious", "patient", "bright"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_apply_remedy(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero_id"])
    remedy = world.facts["remedy"]
    rash = world.facts["rash"]

    if hero.meters["itch"] < THRESHOLD:
        return out
    sig = ("apply", remedy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["itch"] = max(0.0, hero.meters["itch"] - 1.0)
    hero.meters["swelling"] = max(0.0, hero.meters["swelling"] - 0.5)
    hero.meters["calm"] += 0.8
    world.say(
        f"The healer took up {remedy.phrase} and {remedy.repeat}, "
        f"{remedy.use_verb}ing it {remedy.spread}."
    )
    world.say(
        f"At once, {hero.id}'s {rashes(rash)} softened, and the rash did not burn so fiercely."
    )
    return out


def _r_rest(world: World) -> list[str]:
    hero = world.get(world.facts["hero_id"])
    sig = ("rest", hero.id)
    if sig in world.fired:
        return []
    if hero.meters["calm"] < 1.0 or hero.meters["itch"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    hero.meters["rest"] += 1.0
    hero.meters["hope"] += 0.6
    return [f"Then the child rested, and the night grew soft as wool."]


RULES = [Rule("apply", _r_apply_remedy), Rule("rest", _r_rest)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def rashes(rash: str) -> str:
    return rash


def myth_opening(hero: Entity, caretaker: Entity, commission: Commission, realm: Realm) -> str:
    return (
        f"In {realm.place}, {hero.id} lived beneath old vows and bright lamps. "
        f"{caretaker.pronoun('subject').capitalize()} had been given {commission.phrase}, "
        f"for the people feared the rash that would not sleep."
    )


def predict_relief(world: World, hero: Entity, remedy: Remedy) -> bool:
    sim = world.copy()
    h = sim.get(hero.id)
    h.meters["itch"] = max(0.0, h.meters["itch"] - 1.0)
    h.meters["swelling"] = max(0.0, h.meters["swelling"] - 0.5)
    return h.meters["itch"] < THRESHOLD


def tell(realm: Realm, params: StoryParams) -> World:
    world = World(realm=realm)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, meters={
        "itch": 1.5, "swelling": 1.0, "calm": 0.0, "rest": 0.0, "hope": 0.5, "distance": 0.0
    }, memes={"worry": 0.8, "trust": 0.2}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker_kind, label=params.caretaker, meters={
        "pride": 0.2, "worry": 0.4, "relief": 0.0
    }, memes={"duty": 1.0, "hope": 0.4}))
    commission = COMMISSIONS[params.commission]
    remedy = REMEDIES[params.remedy]
    rash = world.add(Entity(id="rash", type="rash", label="rash", phrase="the hot red rash", owner=hero.id, caretaker="Caretaker"))
    commission.bearer = caretaker.id

    world.facts.update(hero_id=hero.id, caretaker_id=caretaker.id, commission=commission, remedy=remedy, rash=rash)

    world.say(myth_opening(hero, caretaker, commission, realm))
    world.say(
        f"The child had a rash like a small red star, and every scratch made it flare."
    )
    world.say(
        f"{caretaker.id} listened, looked, and promised not one cure but a careful pattern."
    )

    world.para()
    world.say(
        f"Each evening, the healer washed the skin, then waited, then washed it again."
    )
    world.say(
        f"The same calm words were spoken twice, because in old myths the faithful step is often the winning step."
    )

    world.para()
    if predict_relief(world, hero, remedy):
        world.say(
            f"By the commission, {caretaker.id} sent for {remedy.phrase}, "
            f"because the rash needed more than a blessing."
        )
    world.say(
        f"At dusk, {hero.id} sat still while {caretaker.id} opened the jar of {remedy.label}."
    )
    hero.meters["distance"] += 0.2
    hero.memes["trust"] += 0.4
    propagate(world, narrate=True)

    world.para()
    hero.meters["itch"] = max(0.0, hero.meters["itch"] - 0.7)
    hero.meters["calm"] += 0.7
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    caretaker.meters["relief"] += 0.9
    caretaker.memes["hope"] += 0.4
    world.say(
        f"The next night, the same gentle hand returned, and the same cream was used again."
    )
    world.say(
        f"This repetition was not empty; it was the road that led the skin back to peace."
    )
    propagate(world, narrate=True)

    world.para()
    if hero.meters["itch"] < THRESHOLD:
        world.say(
            f"In the end, {hero.id} slept without scratching, and {remedy.ending}."
        )
        world.say(
            f"{caretaker.id} kept the commission safe, and the temple was quiet enough to hear the lamps breathe."
        )

    world.facts.update(resolved=hero.meters["itch"] < THRESHOLD)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for commission in COMMISSIONS:
            for remedy in REMEDIES:
                combos.append((place, commission, remedy))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_id"]
    commission = f["commission"]
    remedy = f["remedy"]
    return [
        f"Write a short myth about {hero} and a commission that leads to {remedy.label}.",
        f"Tell a child-friendly legend where a healer repeats a cure until the rash settles.",
        f"Write a simple myth that includes a commission, hydrocortisone, and the power of repetition.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_id"]
    caretaker = world.get(f["caretaker_id"])
    remedy = f["remedy"]
    commission = f["commission"]
    return [
        QAItem(
            question=f"Why did {caretaker.id} keep using {remedy.label} more than once?",
            answer=(
                f"{caretaker.id} kept using {remedy.label} because the rash was still itchy and needed steady care. "
                f"In the story, repetition mattered: the same gentle treatment was used again and again until the skin calmed."
            ),
        ),
        QAItem(
            question=f"What did the commission ask for?",
            answer=(
                f"The commission asked for a careful remedy for the rash. It was {commission.phrase}, and its purpose was to {commission.purpose}."
            ),
        ),
        QAItem(
            question=f"How did {hero} feel at the end?",
            answer=(
                f"{hero} felt calmer and safer at the end because the itching eased and the healing repeated until it worked."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hydrocortisone used for?",
            answer=(
                "Hydrocortisone is a medicine that can help calm itchy or irritated skin."
            ),
        ),
        QAItem(
            question="What does repetition mean?",
            answer=(
                "Repetition means doing the same thing again and again. In stories, repetition can show patience, practice, or a careful ritual."
            ),
        ),
        QAItem(
            question="What is a commission?",
            answer=(
                "A commission is a formal request to make or do something, often for a ruler, a patron, or a community."
            ),
        ),
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="temple", hero="Mira", hero_kind="girl", caretaker="priestess", caretaker_kind="priestess",
                commission="healers_call", remedy="hydrocortisone"),
    StoryParams(place="courtyard", hero="Oren", hero_kind="boy", caretaker="king", caretaker_kind="king",
                commission="royal_seal", remedy="hydrocortisone"),
]


ASP_RULES = r"""
% A remedy is chosen when a commission exists and the remedy can guard the symptom.
commissioned(C) :- commission(C).

guards_remedy(R, S) :- remedy(R), symptom(S), guards(R, S).

compatible(C, R) :- commissioned(C), remedy(R), guards_remedy(R, itch).

% Repetition is valid when the remedy is used more than once in sequence.
repeats(R) :- remedy(R).

% A story is reasonable if a commission and a repeated remedy align.
valid_story(Place, C, R) :- place(Place), commissioned(C), remedy(R), compatible(C, R), repeats(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for cid, c in COMMISSIONS.items():
        lines.append(asp.fact("commission", cid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for g in sorted(r.guards):
            lines.append(asp.fact("symptom", g))
            lines.append(asp.fact("guards", rid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((place, c, r) for place, c, r in valid_combos() if r == "hydrocortisone")
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic story world about a commission and hydrocortisone.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
    ap.add_argument("--caretaker-kind", choices=["priestess", "priest", "queen", "king"])
    ap.add_argument("--commission", choices=COMMISSIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    hero, hero_kind = (args.hero, args.hero_kind)
    if hero is None or hero_kind is None:
        hero, hero_kind = rng.choice(HEROES)
    caretaker, caretaker_kind = (args.caretaker, args.caretaker_kind)
    if caretaker is None or caretaker_kind is None:
        caretaker, caretaker_kind = rng.choice(CARETAKERS)
    commission = args.commission or rng.choice(list(COMMISSIONS))
    remedy = args.remedy or "hydrocortisone"
    return StoryParams(place=place, hero=hero, hero_kind=hero_kind, caretaker=caretaker,
                       caretaker_kind=caretaker_kind, commission=commission, remedy=remedy)


def generate(params: StoryParams) -> StorySample:
    realm = PLACES[params.place]
    world = tell(realm, params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.commission} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
