#!/usr/bin/env python3
"""
storyworlds/worlds/squeal_campaign_broker_swim_school_transformation_dialogue.py
================================================================================

A small ghost-story world set at swim school.

Premise seed:
- A swim school at dusk.
- A sudden squeal from the deep end.
- A campaign to keep the lesson going.
- A broker who can arrange a swap or fix.
- A quiet transformation that makes the ending feel eerie but safe.

This world generates child-facing stories with:
- Transformation
- Dialogue
- Foreshadowing

The causal model is intentionally small:
- a scary sound can stir fear or curiosity
- a campaign can gather help
- a broker can offer a useful substitute or schedule change
- a transformation can turn worry into courage, or an object into a calmer form
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


# ---------------------------------------------------------------------------
# Core world entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "lady"}
        male = {"boy", "father", "man", "broker", "coach"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the swim school"
    dim: bool = True
    has_pool: bool = True
    has_locker_room: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACE = Place()

ROLES = {
    "student": {
        "type": "girl",
        "activity": "take swimming lessons",
        "favorite": "kickboard",
        "transformation": "braver",
    },
    "student_boy": {
        "type": "boy",
        "activity": "practice floating",
        "favorite": "goggles",
        "transformation": "calmer",
    },
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Eli"]


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
class SwimWorld(World):
    pass


def ghostly_place_detail() -> str:
    return "The swim school was quiet, and the pool lights made pale stripes on the water."


def foreshadow_line(hero: Entity) -> str:
    return (
        f"Before the lesson started, {hero.id} heard a tiny squeal from the deep end, "
        f"like a door in a dream opening just a crack."
    )


def transform_item(old: str, new: str) -> str:
    return f"the {old} seemed to turn into a {new}"


def broker_help_line(hero: Entity, broker: Entity) -> str:
    return (
        f'"I can broker a calmer plan," {broker.id} said. '
        f'"We do not need to stop the lesson. We can change how we begin."'
    )


def build_world(params: StoryParams) -> SwimWorld:
    world = SwimWorld(PLACE)
    role = ROLES[params.role]
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            props={"role": params.role, "favorite": role["favorite"], "transformation": role["transformation"]},
            memes={"fear": 0.0, "hope": 0.0, "courage": 0.0, "relief": 0.0},
        )
    )
    teacher = world.add(Entity(id="Coach Mira", kind="character", type="teacher", label="Coach Mira"))
    broker = world.add(Entity(id="Mr. Reed", kind="character", type="broker", label="Mr. Reed"))
    noisemaker = world.add(
        Entity(
            id="pool-drain-chain",
            kind="thing",
            type="chain",
            label="drain chain",
            phrase="a silver drain chain",
            meters={"squeal": 1.0},
        )
    )
    hero.props["activity"] = role["activity"]
    world.facts.update(hero=hero, teacher=teacher, broker=broker, noisemaker=noisemaker)
    return world


def tell(world: SwimWorld) -> None:
    hero = world.facts["hero"]
    teacher = world.facts["teacher"]
    broker = world.facts["broker"]
    chain = world.facts["noisemaker"]

    world.say(f"{hero.id} came to {world.place.name} to {hero.props['activity']}.")
    world.say(f"{hero.id} loved {hero.props['favorite']} and tried to look ready, but {ghostly_place_detail()}")
    world.para()
    world.say(foreshadow_line(hero))
    world.say(
        f"Then a squeal flashed through the hall. It came from {chain.label}, and it made "
        f"{hero.id} pause with {hero.pronoun('possessive')} hands tight around the edge of the bench."
    )
    hero.memes["fear"] += 1.0
    hero.memes["hope"] += 0.5
    world.say(
        f'"Did you hear that?" {hero.id} asked. "That sound is spooky."'
    )
    world.say(
        f'"I heard it," {teacher.id} said softly. "Spooky things can still be safe. '
        f'Let us look carefully."'
    )
    world.para()

    world.say(
        f"{hero.id} wanted to leave the room, but the whole class began a little campaign: "
        f"the older swimmers whispered to one another, the teacher checked the water, and "
        f"everyone asked what was making the noise."
    )
    hero.memes["hope"] += 1.0
    world.say(
        f'"We can help," {hero.id} said, more quietly than before. "Maybe the sound has a reason."'
    )
    world.say(
        f'"That is a good campaign," {broker.id} said when he arrived from the office. '
        f'"I broker fixes for small troubles. This one only needs a new latch and a calmer start."'
    )
    world.say(broker_help_line(hero, broker))
    world.para()

    hero.memes["courage"] += 1.0
    world.say(
        f"{teacher.id} opened a toolbox and replaced the old latch on {chain.label}. "
        f"At once, the squeal stopped."
    )
    world.say(
        f"That felt like a transformation: {transform_item('squeaky chain', 'quiet ribbon of metal')}."
    )
    world.say(
        f"{hero.id} straightened up, and the fear in {hero.pronoun('possessive')} chest changed shape. "
        f"It did not vanish like smoke; it turned into courage."
    )
    hero.memes["fear"] = 0.0
    hero.memes["courage"] += 1.0
    hero.memes["relief"] += 1.0
    world.say(
        f'"Can I try again?" {hero.id} asked.'
    )
    world.say(
        f'"Yes," {teacher.id} said. "The water is still the water."'
    )
    world.say(
        f"So {hero.id} went back to the pool, held the {hero.props["favorite"]}, and finished {hero.props["activity"]}. "
        f"The hall looked the same, but {hero.id} looked different: {hero.id} was {hero.props["transformation"]} now, "
        f"and the old squeal had become only a memory."
    )

    world.facts["resolved"] = True
    world.facts["transformed"] = True


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: SwimWorld) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a gentle ghost story set at a swim school about {hero.id}, a strange squeal, and a helpful broker.",
        f"Tell a child-friendly story where a campaign helps keep swimming lessons going after a spooky sound.",
        f"Write a short story with dialogue, foreshadowing, and a transformation that ends safely at the pool.",
    ]


def story_qa(world: SwimWorld) -> list[QAItem]:
    hero = world.facts["hero"]
    teacher = world.facts["teacher"]
    broker = world.facts["broker"]
    return [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place at the swim school, beside the pool with its pale lights.",
        ),
        QAItem(
            question=f"What scary sound did {hero.id} hear?",
            answer=f"{hero.id} heard a squeal from the deep end, and it made the room feel spooky for a moment.",
        ),
        QAItem(
            question=f"Who helped turn the problem into something calm?",
            answer=f"{teacher.id} and {broker.id} helped by checking the problem, fixing the latch, and brokering a calmer plan.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The squeal stopped, the chain became quiet, and {hero.id} changed from fearful to {hero.props['transformation']}.",
        ),
    ]


def world_knowledge_qa(world: SwimWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a broker?",
            answer="A broker is a person who helps arrange a deal or a plan between people so everyone can agree.",
        ),
        QAItem(
            question="What does a campaign mean in a story?",
            answer="A campaign is a planned effort where people work together toward one goal.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something that will matter later.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or a new state.",
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


def dump_trace(world: SwimWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id:14} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
problem(squeal) :- squeal_event.
helpful(B) :- broker_name(B).

campaign(H) :- hero(H), wants_to_continue(H).
transforms(H) :- hero(H), fear_to_courage(H).

resolved :- campaign(_), helpful(_), latch_fixed, squeal_event.
safe_story :- resolved, transforms(_).
#show resolved/0.
#show safe_story/0.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("broker_name", "broker"))
    lines.append(asp.fact("squeal_event"))
    lines.append(asp.fact("wants_to_continue", "hero"))
    lines.append(asp.fact("fear_to_courage", "hero"))
    lines.append(asp.fact("latch_fixed"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show resolved/0. #show safe_story/0."))
    atoms = {sym.name for sym in model}
    expected = {"resolved", "safe_story"}
    if atoms == expected:
        print("OK: ASP rules confirm the story resolves safely.")
        return 0
    print("MISMATCH: ASP rules did not match expected outcome.")
    print("got:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Story creation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = args.role or rng.choice(list(ROLES))
    if role == "student" and gender == "boy":
        role = "student_boy"
    if role == "student_boy" and gender == "girl":
        role = "student"
    if role not in ROLES:
        raise StoryError("unknown role")
    return StoryParams(name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story swim school world with squeal, campaign, broker, transformation, dialogue, and foreshadowing."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=list(ROLES))
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


CURATED = [
    StoryParams(name="Mia", gender="girl", role="student"),
    StoryParams(name="Noah", gender="boy", role="student_boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0. #show safe_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print(asp_program("#show resolved/0. #show safe_story/0."))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.role}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
