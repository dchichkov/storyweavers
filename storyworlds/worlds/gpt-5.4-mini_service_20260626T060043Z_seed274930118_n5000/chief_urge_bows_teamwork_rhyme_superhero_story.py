#!/usr/bin/env python3
"""
A standalone story world for a small Superhero Story-style domain.

Premise:
- A chief tries to resist a strong urge.
- A set of bows must be kept neat for a team event.
- Teamwork and rhyme help resolve the problem.

The world is intentionally small and constraint-driven: a chief's urge can
tangle the bows, and only a teamwork-based, rhyming repair can set things right.
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

TITLE = "Chief, Urge, Bows"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "chief":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    chief_name: str = "Chief Leo"
    urge: str = "rush to the parade"
    bows: str = "silk bows"
    place: str = "the city square"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def setup_world(params: StoryParams) -> World:
    w = World(params.place)
    chief = w.add(Entity(id=params.chief_name, kind="character", type="chief", label=params.chief_name))
    bows = w.add(Entity(
        id="bows",
        kind="thing",
        type="bows",
        label=params.bows,
        phrase=f"a bundle of {params.bows}",
        owner=chief.id,
        caretaker=chief.id,
        plural=True,
    ))
    w.facts.update(chief=chief, bows=bows, place=params.place, urge=params.urge)
    return w


def narrate_intro(w: World, chief: Entity, bows: Entity, urge: str) -> None:
    w.say(
        f"Chief {chief.label.split(' ', 1)[-1]} was a brave helper who loved clear plans and bright days."
    )
    w.say(
        f"At {w.place}, {chief.label} had to keep {bows.phrase} neat for the team show."
    )
    w.say(
        f"Still, a strong urge kept tugging at {chief.pronoun('possessive')} heart: {urge}."
    )


def predict_tangle(w: World, chief: Entity, bows: Entity, urge: str) -> bool:
    sim = w.copy()
    simulate_urge(sim, chief.id, urge, narrate=False)
    return bool(sim.get("bows").meters.get("tangled", 0) >= THRESHOLD)


def simulate_urge(w: World, chief_id: str, urge: str, narrate: bool = True) -> None:
    chief = w.get(chief_id)
    bows = w.get("bows")
    chief.memes["urge"] = chief.memes.get("urge", 0) + 1
    bows.meters["tangled"] = bows.meters.get("tangled", 0) + 1
    if narrate:
        w.say(
            f"At the first pull of {urge}, the bows began to twist and knot."
        )


def warn_and_struggle(w: World, chief: Entity, bows: Entity, urge: str) -> None:
    if predict_tangle(w, chief, bows, urge):
        w.say(
            f'"If I chase that urge, these {bows.label} will tangle," {chief.label} said.'
        )
    w.say(
        f"Yet the urge still buzzed like a tiny rocket in {chief.pronoun('possessive')} chest."
    )
    simulate_urge(w, chief.id, urge)


def teamwork_fix(w: World, chief: Entity, bows: Entity) -> None:
    helpers = ["the scout", "the drummer", "the painter"]
    w.facts["helpers"] = helpers
    w.say(
        f"Then {chief.label} called for teamwork. {_join(helpers)} hurried over to help."
    )
    w.say(
        f'The team began a rhyme: "Tie, untie, try and fly; loop and swoop, then let it lie."'
    )
    bows.meters["tangled"] = 0
    bows.meters["neat"] = 1
    chief.memes["pride"] = chief.memes.get("pride", 0) + 1
    chief.memes["relief"] = chief.memes.get("relief", 0) + 1
    w.say(
        f"With careful hands and a rhyming tune, they smoothed every knot out of {bows.label}."
    )
    w.say(
        f"Chief {chief.label.split(' ', 1)[-1]} smiled. The urge was quiet at last, and the bows stayed neat for the show."
    )


def tell(params: StoryParams) -> World:
    w = setup_world(params)
    chief = w.get("chief") if "chief" in w.entities else w.get(params.chief_name)
    bows = w.get("bows")
    narrate_intro(w, chief, bows, params.urge)
    w.para()
    warn_and_struggle(w, chief, bows, params.urge)
    w.para()
    teamwork_fix(w, chief, bows)
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f'Write a short superhero story for a young child about {f["chief"].label} and a strong urge at {f["place"]}.',
        f'Write a story where teamwork and a rhyme help keep {f["bows"].label} neat.',
        f'Tell a gentle superhero story that uses the words "chief", "urge", and "bows".',
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    chief = f["chief"]
    bows = f["bows"]
    place = f["place"]
    urge = f["urge"]
    return [
        QAItem(
            question=f"Who was trying to keep {bows.label} neat at {place}?",
            answer=f"{chief.label} was trying to keep {bows.phrase} neat at {place}.",
        ),
        QAItem(
            question=f"What strong feeling kept tugging at {chief.label}?",
            answer=f"A strong urge kept tugging at {chief.pronoun('possessive')} heart: {urge}.",
        ),
        QAItem(
            question=f"How did the team fix the problem with the bows?",
            answer="They worked together and sang a rhyme, which helped smooth out every knot.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The bows stayed neat, and the urge was quiet at last.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something hard or helpful.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or song where words sound alike at the end.",
        ),
        QAItem(
            question="What are bows?",
            answer="Bows are tied loops made from ribbon, cloth, or string.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("chief", "chief")]
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in URGES:
        lines.append(asp.fact("urge", a))
    for b in BOWS:
        lines.append(asp.fact("bows", b))
    return "\n".join(lines)


ASP_RULES = r"""
risky(U) :- urge(U).
tangles(B) :- bows(B), risky(_).
works_together :- teamwork.
fixes(B) :- bows(B), teamwork, rhyme.
good_story :- fixes(_).
#show risky/1.
#show tangles/1.
#show fixes/1.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


SETTINGS = ["the city square", "the rooftop", "the parade route"]
URGES = [
    "rush to the parade",
    "jump into the spotlight",
    "dash off before the plan was ready",
]
BOWS = [
    "silk bows",
    "red ribbon bows",
    "gold parade bows",
]


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show risky/1. #show tangles/1. #show fixes/1."))
    atoms = set((sym.name, tuple(arg.name if hasattr(arg, "name") else getattr(arg, "string", getattr(arg, "number", None)) for arg in sym.arguments)) for sym in model)
    if model is not None:
        print("OK: ASP program grounded successfully.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: chief, urge, bows, teamwork, rhyme.")
    ap.add_argument("--chief-name", choices=["Chief Leo", "Chief Mina", "Chief Koa"], default=None)
    ap.add_argument("--urge", choices=URGES, default=None)
    ap.add_argument("--bows", choices=BOWS, default=None)
    ap.add_argument("--place", choices=SETTINGS, default=None)
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
    return StoryParams(
        chief_name=args.chief_name or rng.choice(["Chief Leo", "Chief Mina", "Chief Koa"]),
        urge=args.urge or rng.choice(URGES),
        bows=args.bows or rng.choice(BOWS),
        place=args.place or rng.choice(SETTINGS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(chief_name="Chief Leo", urge="rush to the parade", bows="silk bows", place="the city square"),
    StoryParams(chief_name="Chief Mina", urge="jump into the spotlight", bows="red ribbon bows", place="the rooftop"),
    StoryParams(chief_name="Chief Koa", urge="dash off before the plan was ready", bows="gold parade bows", place="the parade route"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show risky/1. #show tangles/1. #show fixes/1. #show good_story/0."))
        print(asp.atoms(model, "risky"))
        print(asp.atoms(model, "tangles"))
        print(asp.atoms(model, "fixes"))
        print(asp.atoms(model, "good_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.chief_name} / {p.urge} / {p.bows}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
