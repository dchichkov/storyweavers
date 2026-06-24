#!/usr/bin/env python3
"""
storyworlds/worlds/reward_regret_mystery_to_solve_dialogue_folk.py
===================================================================

A small folk-tale story world about a shared reward, a sharp regret, and a
mystery solved by dialogue.

Seed tale sketch:
---
In a little village by a reed-lined river, a kind miller found a silver bell on
his doorstep. The bell came with a note: "Return me to the right owner, and a
reward will be given." The miller was pleased, but his younger brother, Jori,
thought the note meant they should keep the bell and wait for the reward.

That night, the bell vanished. Jori felt regret at once. The miller and Jori
followed tiny clues: a ribbon snagged on a gate, fresh footprints in flour dust,
and a goose that kept honking at the same shed. They asked the baker, the
goose-keeper, and the old ferryman questions until they learned the bell had
belonged to the river shrine. They returned it, and the shrine keeper gave them
a warm loaf, a small coin purse, and thanks. Jori apologized, and the brother
said the true reward was having done the right thing.

World model:
---
This world tracks:
- one treasured object that can be lost, hidden, or returned,
- one emotional turn: greed -> regret -> relief,
- dialogue-driven clue finding,
- a final reward that follows honest repair.

The prose is generated from the state; it is not a fixed paragraph with swapped
nouns. The inline ASP twin mirrors the reasonableness gate for valid stories.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden_by: Optional[str] = None
    found_by: Optional[str] = None
    returns_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "wife", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "husband", "brother", "uncle", "miller"}
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
    detail: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    text: str
    source: str
    leads_to: str


@dataclass
class Mystery:
    id: str
    lost_object: str
    rightful_owner: str
    hidden_place: str
    reward: str
    regret_trigger: str
    solved_by: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    sibling: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
        clone = World(self.place, self.mystery)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "village": Place(
        name="the village",
        detail="The village lay by a reed-lined river, with a bakery, a shed, and a small shrine.",
        clues=["flour dust", "gate ribbon", "goose tracks"],
    ),
    "harbor": Place(
        name="the harbor",
        detail="The harbor had nets, salt air, and a chapel that watched over the pier.",
        clues=["rope fibers", "wet planks", "fish scales"],
    ),
    "orchard": Place(
        name="the orchard",
        detail="The orchard had apple trees, a stone wall, and a barn with a creaky door.",
        clues=["apple peel", "mud prints", "barrel chips"],
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        lost_object="silver bell",
        rightful_owner="river shrine keeper",
        hidden_place="the flour shed",
        reward="a warm loaf and a small coin purse",
        regret_trigger="the bell vanished while they argued about keeping it",
        solved_by=["gate ribbon", "flour dust", "goose honking"],
    ),
    "key": Mystery(
        id="key",
        lost_object="iron key",
        rightful_owner="harbor chapel keeper",
        hidden_place="the net loft",
        reward="a basket of apples and a bright ribbon",
        regret_trigger="the key slipped away after careless boasting",
        solved_by=["rope fibers", "wet planks", "pebbly prints"],
    ),
    "lantern": Mystery(
        id="lantern",
        lost_object="brass lantern",
        rightful_owner="orchard barn keeper",
        hidden_place="the hay bin",
        reward="sweet cider and a cloth pouch of coins",
        regret_trigger="the lantern was hidden after an impatient wager",
        solved_by=["apple peel", "mud prints", "barn creak"],
    ),
}

NAMES = ["Jori", "Mara", "Tobin", "Anya", "Pell", "Sera", "Bram", "Nina"]
TRAITS = ["kind", "careful", "curious", "proud", "gentle", "quick", "thoughtful", "stubborn"]


def _new_entity(eid: str, kind: str, typ: str, label: str, phrase: str = "", traits=None) -> Entity:
    return Entity(id=eid, kind=kind, type=typ, label=label, phrase=phrase, traits=list(traits or []))


def build_world(place: Place, mystery: Mystery, hero_name: str, sibling_name: str, trait: str) -> World:
    world = World(place, mystery)
    hero = world.add(_new_entity(hero_name, "character", "brother", "the younger brother", traits=["little", trait]))
    sibling = world.add(_new_entity(sibling_name, "character", "brother", "the older brother", traits=["steady", "patient"]))
    owner = world.add(_new_entity("Owner", "character", "shrine keeper", f"the {mystery.rightful_owner}"))
    lost = world.add(_new_entity("Object", "thing", "thing", mystery.lost_object, phrase=f"a {mystery.lost_object}", traits=["precious"]))
    lost.owner = owner.id

    clue1 = world.add(_new_entity("Clue1", "thing", "clue", "first clue", phrase=mystery.solved_by[0]))
    clue2 = world.add(_new_entity("Clue2", "thing", "clue", "second clue", phrase=mystery.solved_by[1]))
    clue3 = world.add(_new_entity("Clue3", "thing", "clue", "third clue", phrase=mystery.solved_by[2]))

    world.facts.update(
        hero=hero,
        sibling=sibling,
        owner=owner,
        lost=lost,
        clues=[clue1, clue2, clue3],
        mystery=mystery,
        place=place,
        resolved=False,
        regret=False,
        reward_given=False,
    )
    return world


def narration_intro(world: World) -> None:
    m = world.mystery
    world.say(f"Long ago, in {world.place.name}, there lived two brothers who liked to help their neighbors.")
    world.say(f"One morning, they found {m.lost_object} on their doorstep, with a note that promised a reward if it was returned.")


def narration_tension(world: World) -> None:
    hero = world.facts["hero"]
    sibling = world.facts["sibling"]
    m = world.mystery
    hero.memes["want_keep"] = hero.memes.get("want_keep", 0) + 1
    world.say(
        f"{hero.id} wanted to keep the {m.lost_object} for a little while, but {sibling.id} said, "
        f"\"That note was meant for the true owner.\""
    )
    world.say(f"They argued by the door until the bell (or key, or lantern) was nowhere to be seen.")
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    world.facts["regret"] = True
    world.say(f"At once, {hero.id} felt regret, because {m.regret_trigger}.")


def narration_solve(world: World) -> None:
    hero = world.facts["hero"]
    sibling = world.facts["sibling"]
    owner = world.facts["owner"]
    m = world.mystery

    world.para()
    world.say(f"{sibling.id} said, \"Let's ask questions instead of guessing.\"")
    world.say(f"{hero.id} nodded and asked, \"Who saw something shiny near the path?\"")

    clue_lines = [
        f"The baker said, \"I saw {m.solved_by[0]} on the gate.\"",
        f"The goose-keeper said, \"I saw {m.solved_by[1]} near the shed.\"",
        f"The ferryman said, \"I heard {m.solved_by[2]} by the river.\"",
    ]
    for line in clue_lines:
        world.say(line)

    world.say(
        f"With those clues, they found the {m.lost_object} hidden in {m.hidden_place}."
    )
    world.say(
        f"They returned it to {owner.id}, who smiled and gave them {m.reward}."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    sibling.memes["pride"] = sibling.memes.get("pride", 0) + 1
    world.facts["resolved"] = True
    world.facts["reward_given"] = True
    world.say(
        f"{hero.id} apologized for the selfish thought, and {sibling.id} said, "
        f"\"The truest reward is knowing we did right.\""
    )


def narration_ending(world: World) -> None:
    hero = world.facts["hero"]
    m = world.mystery
    world.para()
    world.say(
        f"In the end, {hero.id} walked home lighter in heart, while the {m.lost_object} "
        f"rang safely where it belonged."
    )
    world.say(f"The village was quiet again, and the night felt honest.")


def tell(place: Place, mystery: Mystery, hero_name: str, sibling_name: str, trait: str) -> World:
    world = build_world(place, mystery, hero_name, sibling_name, trait)
    narration_intro(world)
    narration_tension(world)
    narration_solve(world)
    narration_ending(world)
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in PLACES for mystery in MYSTERIES]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    sibling: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    m = f["mystery"]
    return [
        f'Write a folk-tale style story about {hero.id} and {sibling.id}, a {m.lost_object}, and a reward.',
        f"Tell a short mystery where two brothers use dialogue to find {m.lost_object} and feel regret first.",
        f'Write a gentle village tale that includes the words "reward" and "regret" and ends with the object returned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    owner = f["owner"]
    m = f["mystery"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What did {hero.id} and {sibling.id} find at the start of the story?",
            answer=f"They found {m.lost_object} on their doorstep in {place.name}, along with a note about a reward.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel regret?",
            answer=f"{hero.id} felt regret because {m.regret_trigger}. That made the mistake feel heavy right away.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it by asking the baker, the goose-keeper, and the ferryman questions until the clues pointed to {m.hidden_place}.",
        ),
        QAItem(
            question=f"What reward did they get after returning the object?",
            answer=f"{owner.id} gave them {m.reward} after they returned the {m.lost_object}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What did {hero.id} say after the mystery was solved?",
                answer=f"{hero.id} apologized, and {sibling.id} said the truest reward was doing the right thing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    return [
        QAItem(
            question="What is a reward?",
            answer="A reward is something good you are given for doing a helpful or brave thing.",
        ),
        QAItem(
            question="What is regret?",
            answer="Regret is the sad feeling you get when you wish you had chosen a better way.",
        ),
        QAItem(
            question="How can questions help solve a mystery?",
            answer="Questions can help because different people may have seen different clues, and the clues can be put together like pieces of a puzzle.",
        ),
        QAItem(
            question=f"What kind of place is {m.hidden_place} in this story?",
            answer="It is a hidden spot where the lost object was kept until the brothers found it.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: resolved={world.facts.get('resolved')} regret={world.facts.get('regret')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", mystery="bell", hero="Jori", sibling="Milo", trait="curious"),
    StoryParams(place="harbor", mystery="key", hero="Mara", sibling="Tess", trait="careful"),
    StoryParams(place="orchard", mystery="lantern", hero="Bram", sibling="Pell", trait="proud"),
]


def ASP_RULES() -> str:
    return r"""
% A mystery is valid if the place, object, and reward all exist together.
valid_story(P,M) :- place(P), mystery(M), has_reward(M), has_clue(M), has_owner(M).

% Reasons for validity are derived from the registries.
has_reward(M) :- reward(M,_).
has_clue(M) :- clue(M,_).
has_owner(M) :- owner(M,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            lines.append(asp.fact("place_clue", pid, clue))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("reward", mid, m.reward))
        lines.append(asp.fact("owner", mid, m.rightful_owner))
        for clue in m.solved_by:
            lines.append(asp.fact("clue", mid, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale mystery world with reward and regret.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([n for n in NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, hero=hero, sibling=sibling, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.hero, params.sibling, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:\n")
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
            header = f"### {p.hero}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
