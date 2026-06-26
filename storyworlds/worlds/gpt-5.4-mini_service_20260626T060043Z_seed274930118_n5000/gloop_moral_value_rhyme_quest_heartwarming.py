#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gloop_moral_value_rhyme_quest_heartwarming.py
==============================================================================================================

A small heartwarming storyworld about a child, a helpful quest, a sticky gloop,
and a gentle moral value: sharing makes a messy problem better.

The seed-image is a tiny source tale:
- A child finds a jar of glittery gloop that has spilled into the kitchen.
- A parent worries because the gloop is sticky and will make a bigger mess.
- The child wants to finish a rhyme quest to collect missing song cards.
- They learn that asking for help, sharing the work, and being careful can turn
  a yucky problem into a warm, happy ending.

World model:
- physical meters: gloop, clean, tidy, glitter, progress, helper_load
- emotional memes: joy, worry, pride, kindness, patience, frustration

The story always stays child-facing, concrete, and state-driven.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    taken: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    outcome: str
    difficulty: str
    rhyme: str
    steps: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    title: str
    lesson: str
    action: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    quest: str
    moral: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(name="the kitchen", indoor=True, affords={"clean", "rhyme", "share"}),
    "hall": Place(name="the hallway", indoor=True, affords={"rhyme", "share"}),
    "garden": Place(name="the garden", indoor=False, affords={"clean", "rhyme", "share"}),
}

QUESTS = {
    "songcards": Quest(
        id="songcards",
        goal="find the missing song cards",
        clue="a tiny rhyme tucked under the table",
        outcome="the song cards were found beside the napkin basket",
        difficulty="a little tricky",
        rhyme="clean, keen, and bright, the cards will come to light",
        steps=["look under the table", "follow the rhyme", "ask for help"],
        tags={"rhyme", "quest"},
    ),
    "toyboat": Quest(
        id="toyboat",
        goal="rescue the little toy boat",
        clue="a splashy trail of gloop near the sink",
        outcome="the toy boat floated free after the gloop was cleared",
        difficulty="gentle but messy",
        rhyme="slow and low, let teamwork go",
        steps=["wipe the spill", "lift the towel", "share the job"],
        tags={"quest", "clean"},
    ),
}

MORALS = {
    "sharing": Moral(
        id="sharing",
        title="sharing",
        lesson="Sharing the work can make a hard job feel small and kind.",
        action="invite someone to help",
        tags={"moral", "share"},
    ),
    "patience": Moral(
        id="patience",
        title="patience",
        lesson="Waiting a little and taking careful steps can keep a mess from growing.",
        action="move slowly and carefully",
        tags={"moral", "clean"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Ivy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Finn", "Noah", "Max"]
TRAITS = ["kind", "curious", "gentle", "brave", "cheerful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for quest_id, q in QUESTS.items():
            for moral_id, m in MORALS.items():
                if "quest" in q.tags and "moral" in m.tags:
                    out.append((place_id, quest_id, moral_id))
    return out


def story_theme() -> str:
    return "heartwarming gloop quest with a moral and a rhyme"


def rhyme_line(quest: Quest) -> str:
    return quest.rhyme


def predict_spill(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["gloop"] += 1
    sim.get(hero.id).memes["frustration"] += 1
    return sim.get("gloop").meters.get("spread", 0.0) < THRESHOLD


def add_gloop(world: World, hero: Entity) -> None:
    goo = world.get("gloop")
    hero.meters["gloop"] += 1
    goo.meters["spread"] += 1
    hero.memes["frustration"] += 1
    world.say(f"A shiny blob of gloop slid across the floor and made a sticky little trail.")
    world.say(f"{hero.id} frowned, because the mess clung to fingers and shoes.")


def clean_together(world: World, hero: Entity, parent: Entity) -> None:
    goo = world.get("gloop")
    hero.meters["clean"] += 1
    parent.meters["clean"] += 1
    hero.memes["kindness"] += 1
    parent.memes["patience"] += 1
    goo.meters["spread"] = max(0.0, goo.meters.get("spread", 0.0) - 1.0)
    world.say(f"{parent.pronoun().capitalize()} handed over a cloth and said they could clean it together.")
    world.say(f"{hero.id} wiped one corner, {parent.id} wiped another, and the sticky shine got smaller.")


def quest_step(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["progress"] += 1
    hero.memes["joy"] += 1
    world.say(f"Then {hero.id} followed the rhyme quest: {rhyme_line(quest)}")


def resolve_quest(world: World, hero: Entity, parent: Entity, quest: Quest, moral: Moral) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"At last, {quest.outcome}, and the room looked bright again."
    )
    world.say(
        f"{hero.id} smiled at {parent.id} and remembered the moral of {moral.title}: {moral.lesson}"
    )


def tell(place: Place, quest: Quest, moral: Moral, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(place)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"gloop": 0.0, "clean": 0.0, "progress": 0.0}, memes={"joy": 0.0, "frustration": 0.0, "kindness": 0.0, "pride": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent", meters={"clean": 0.0}, memes={"patience": 0.0, "joy": 0.0}))
    goo = world.add(Entity(id="gloop", type="gloop", label="gloop", phrase="a shiny sticky gloop", meters={"spread": 0.0}))

    world.say(f"{hero.id} was a {hero_type} who loved small quests and happy endings.")
    world.say(f"One day, {hero.id} and {parent.id} found {quest.goal} in {place.name}.")
    world.say(f"The clue was {quest.clue}, and the quest felt {quest.difficulty}.")
    world.say(f"{hero.id} also liked the rhyme: \"{rhyme_line(quest)}\"")

    world.para()
    add_gloop(world, hero)
    world.say(f"{parent.id} worried the gloop would spread unless they moved carefully.")
    quest_step(world, hero, quest)

    world.para()
    if predict_spill(world, hero):
        clean_together(world, hero, parent)
    quest_step(world, hero, quest)
    resolve_quest(world, hero, parent, quest, moral)

    world.facts.update(hero=hero, parent=parent, gloop=goo, quest=quest, moral=moral, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    moral = f["moral"]
    return [
        f'Write a heartwarming story for a child about {hero.id}, a sticky gloop, and a small quest.',
        f"Tell a gentle tale where {hero.id} follows a rhyme to finish {quest.goal} and learns about {moral.title}.",
        f'Write a simple story with the word "gloop" that ends with help, kindness, and a happy discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    quest = f["quest"]
    moral = f["moral"]
    place = f["place"]
    qas = [
        QAItem(
            question=f"What did {hero.id} find while at {place.name}?",
            answer=f"{hero.id} found a sticky little gloop mess while trying to finish {quest.goal}.",
        ),
        QAItem(
            question=f"What rhyme helped {hero.id} keep going on the quest?",
            answer=f"The rhyme was: \"{quest.rhyme}\" It helped {hero.id} remember the next step.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the gloop?",
            answer=f"{parent.id} helped by bringing a cloth and cleaning together with {hero.id}.",
        ),
        QAItem(
            question=f"What moral did {hero.id} learn at the end?",
            answer=f"{hero.id} learned about {moral.title}: {moral.lesson}",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gloop?",
            answer="Gloop is a sticky, gooey mess that can cling to hands, floors, and toys.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, fix something, or finish an important task.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else help or use something too.",
        ),
        QAItem(
            question="Why can a rhyme help?",
            answer="A rhyme can help by making a task easier to remember and making it feel playful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", quest="songcards", moral="sharing", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hall", quest="songcards", moral="patience", name="Theo", gender="boy", parent="father"),
    StoryParams(place="garden", quest="toyboat", moral="sharing", name="Lily", gender="girl", parent="mother"),
]


ASP_RULES = r"""
% A story is valid when a place affords the quest's main action and the moral
% fits the heartwarming cleanup ending.
affords_ok(P, Q) :- place(P), quest(Q), affords(P, clean).
affords_ok(P, Q) :- place(P), quest(Q), affords(P, rhyme).
affords_ok(P, Q) :- place(P), quest(Q), affords(P, share).

valid(P, Q, M) :- affords_ok(P, Q), moral(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(valid_asp())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming gloop quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.quest is None or c[1] == args.quest)
              and (args.moral is None or c[2] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, moral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, quest=quest, moral=moral, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], MORALS[params.moral], params.name, params.gender, params.parent)
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
        vals = valid_asp()
        print(f"{len(vals)} valid triples:")
        for v in vals:
            print(" ", v)
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
            header = f"### {p.name}: {p.quest} at {p.place} (moral: {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
