#!/usr/bin/env python3
"""
Storyworld: motion / challenge / teamwork / dialogue / quest
Setting: a bus depot, told in a nursery-rhyme style.

A small child-friendly simulation:
- The hero and a helper try to complete a quest at the bus depot.
- A motion challenge appears when a bus is stuck or a gate is blocked.
- Dialogue and teamwork change the world state.
- The ending proves the motion problem was solved.

The world is intentionally tiny, classical, and constraint-checked.
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
# Core model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str = "the bus depot"
    afford_motion: bool = True
    afford_quest: bool = True


@dataclass
class Quest:
    id: str
    task: str
    gerund: str
    goal: str
    challenge: str
    motion: str
    noun: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    support: str
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
        import copy

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {"bus_depot": Place(name="the bus depot", afford_motion=True, afford_quest=True)}

QUESTS = {
    "wheel_push": Quest(
        id="wheel_push",
        task="push the stuck bus wheel",
        gerund="pushing the stuck bus wheel",
        goal="get the bus moving again",
        challenge="the wheel was stuck in a soft patch",
        motion="roll",
        noun="quest",
        tags={"motion", "challenge"},
    ),
    "sign_run": Quest(
        id="sign_run",
        task="carry the bright route sign",
        gerund="carrying the bright route sign",
        goal="bring the sign to the front bay",
        challenge="the sign was too big for one pair of hands",
        motion="walk",
        noun="quest",
        tags={"motion", "challenge"},
    ),
    "ticket_loop": Quest(
        id="ticket_loop",
        task="deliver the ticket pouch",
        gerund="delivering the ticket pouch",
        goal="give the pouch to the driver",
        challenge="the pouch kept slipping away",
        motion="step",
        noun="quest",
        tags={"motion", "challenge"},
    ),
}

HELPERS = {
    "tug_rope": Helper(
        id="tug_rope",
        label="a tug rope",
        prep="hold the rope together",
        tail="pulled in time with the wheels",
        support="teamwork",
        tags={"teamwork"},
    ),
    "little_flag": Helper(
        id="little_flag",
        label="a little flag",
        prep="wave the little flag and call the others",
        tail="marched side by side to the bay",
        support="dialogue",
        tags={"dialogue"},
    ),
    "warm_song": Helper(
        id="warm_song",
        label="a warm little song",
        prep="sing a warm little song and ask for help",
        tail="kept time with every step",
        support="dialogue",
        tags={"dialogue", "teamwork"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ella", "Zoe", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Max", "Theo"]
HELPER_NAMES = ["Mum", "Dad", "Tess", "Ned"]


@dataclass
class StoryParams:
    place: str = "bus_depot"
    quest: str = "wheel_push"
    helper: str = "tug_rope"
    name: str = "Mia"
    gender: str = "girl"
    helper_name: str = "Mum"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid only if the place affords motion and questing.
valid_place(P) :- place(P), affords_motion(P), affords_quest(P).

% The challenge must be real, and the helper must offer teamwork or dialogue.
valid_quest(Q) :- quest(Q), challenge(Q), motion(Q).
valid_helper(H) :- helper(H), (teamwork(H); dialogue(H)).

valid_story(P,Q,H) :- valid_place(P), valid_quest(Q), valid_helper(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.afford_motion:
            lines.append(asp.fact("affords_motion", pid))
        if p.afford_quest:
            lines.append(asp.fact("affords_quest", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("challenge", qid))
        lines.append(asp.fact("motion", qid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if "teamwork" in h.tags:
            lines.append(asp.fact("teamwork", hid))
        if "dialogue" in h.tags:
            lines.append(asp.fact("dialogue", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_stories())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_stories() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for h in HELPERS:
                if PLACES[p].afford_motion and PLACES[p].afford_quest:
                    if "motion" in QUESTS[q].tags and ("teamwork" in HELPERS[h].tags or "dialogue" in HELPERS[h].tags):
                        combos.append((p, q, h))
    return combos


def valid_stories() -> list[tuple[str, str, str]]:
    return valid_story_combos()


def explain_rejection() -> str:
    return "(No story: this world needs a real motion challenge and a helper who can use teamwork or dialogue.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "bus_depot"
    quest = args.quest or rng.choice(sorted(QUESTS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(gender, rng)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)

    if place not in PLACES or quest not in QUESTS or helper not in HELPERS:
        raise StoryError(explain_rejection())
    if not (PLACES[place].afford_motion and PLACES[place].afford_quest):
        raise StoryError(explain_rejection())
    if not ("motion" in QUESTS[quest].tags and ("teamwork" in HELPERS[helper].tags or "dialogue" in HELPERS[helper].tags)):
        raise StoryError(explain_rejection())

    return StoryParams(place=place, quest=quest, helper=helper, name=name, gender=gender, helper_name=helper_name)


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        hero = world.get(world.facts["hero"].id)
        helper = world.get(world.facts["helper_actor"].id)
        bus = world.get("bus")
        if hero.memes.get("quest", 0) >= THRESHOLD and bus.meters.get("stuck", 0) >= THRESHOLD and ("unstick", "quest") not in world.fired:
            world.fired.add(("unstick", "quest"))
            bus.meters["stuck"] = 0
            bus.meters["moving"] = 1
            changed = True
            world.say("The bus gave a little lurch and rolled on with a whoosh.")

        if helper.memes.get("teamwork", 0) >= THRESHOLD and ("teamwork_done",) not in world.fired:
            world.fired.add(("teamwork_done",))
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            changed = True

        if helper.memes.get("dialogue", 0) >= THRESHOLD and hero.memes.get("hope", 0) < THRESHOLD:
            hero.memes["hope"] = 1
            changed = True


def introduce(world: World, hero: Entity, helper_actor: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a bright little grin, "
        f"and {helper_actor.label} was near the bus depot door."
    )
    world.say(
        f"{hero.id} loved the {quest.noun} of the day: {quest.gerund}. "
        f"The bus depot hummed like a soft toy town."
    )


def setup_challenge(world: World, hero: Entity, helper_actor: Entity, quest: Quest) -> None:
    bus = world.get("bus")
    bus.meters["stuck"] = 1
    hero.memes["quest"] = 1
    world.say(
        f"Yet oh dear, the challenge was there: {quest.challenge}. "
        f"The bus would not budge, and the wheels would not sway."
    )
    world.say(
        f"{hero.id} looked at {helper_actor.label} and said, "
        f"\"Shall we try together? Shall we help the bus today?\""
    )
    helper_actor.memes["dialogue"] = 1
    hero.memes["hope"] = 1


def teamwork_move(world: World, hero: Entity, helper_actor: Entity, helper: Helper, quest: Quest) -> None:
    hero.memes["teamwork"] = 1
    helper_actor.memes["teamwork"] = 1
    world.say(
        f"{helper_actor.label} said, \"Yes, yes, yes!\" and showed {hero.id} "
        f"{helper.prep}."
    )
    world.say(
        f"Then {hero.id} and {helper_actor.label} held tight and worked as one, "
        f"for teamwork makes the heavy thing light."
    )
    world.say(
        f"{hero.id} whispered, \"One, two, three!\" and the wheels began to turn."
    )
    propagate(world)


def finish(world: World, hero: Entity, helper_actor: Entity, quest: Quest) -> None:
    bus = world.get("bus")
    world.para()
    if bus.meters.get("moving", 0) >= THRESHOLD:
        world.say(
            f"The bus rolled away from the depot, and {hero.id} clapped with glee."
        )
        world.say(
            f"{helper_actor.label} smiled, \"Well done, little one,\" and {hero.id} "
            f"answered, \"We did it together, on our merry way!\""
        )
        world.say(
            f"So the quest was done, the challenge was won, and the bus depot brightened in the sun."
        )
    else:
        world.say("But the bus still did not go, and the little rhyme could not end so.")

    world.facts.update(hero=hero, helper_actor=helper_actor, quest=quest)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_actor = world.add(Entity(id=params.helper_name, kind="character", type="adult", label=params.helper_name))
    bus = world.add(Entity(id="bus", type="bus", label="the bus"))
    bus.meters["stuck"] = 0
    bus.meters["moving"] = 0

    quest = QUESTS[params.quest]
    helper = HELPERS[params.helper]

    introduce(world, hero, helper_actor, quest)
    world.para()
    setup_challenge(world, hero, helper_actor, quest)
    teamwork_move(world, hero, helper_actor, helper, quest)
    finish(world, hero, helper_actor, quest)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper_actor = f["helper_actor"]
    quest = f["quest"]
    return [
        'Write a short nursery-rhyme story about a child at a bus depot, a motion challenge, and a teamwork quest.',
        f'Write a gentle rhyme where {hero.id} and {helper_actor.label} solve {quest.gerund} together.',
        'Tell a child-facing story that includes the words motion, challenge, teamwork, dialogue, and quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper_actor, quest = f["hero"], f["helper_actor"], f["quest"]
    return [
        QAItem(
            question=f"Where was {hero.id} trying to solve the quest?",
            answer="At the bus depot, where the buses rested and waited.",
        ),
        QAItem(
            question=f"What was the challenge in the story?",
            answer=f"The challenge was that {quest.challenge}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper_actor.label} solve the problem?",
            answer=f"They used teamwork and dialogue, held on together, and helped the bus start moving.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The bus began to move, and the quest was finished with happy smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk and listen to each other.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special goal or mission someone tries to complete.",
        ),
        QAItem(
            question="What does motion mean?",
            answer="Motion means moving from one place to another.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses park, wait, and get ready to go.",
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: motion, challenge, teamwork, dialogue, quest at a bus depot.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    StoryParams(place="bus_depot", quest="wheel_push", helper="tug_rope", name="Mia", gender="girl", helper_name="Mum"),
    StoryParams(place="bus_depot", quest="sign_run", helper="little_flag", name="Leo", gender="boy", helper_name="Dad"),
    StoryParams(place="bus_depot", quest="ticket_loop", helper="warm_song", name="Nora", gender="girl", helper_name="Tess"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "bus_depot"
    quest = args.quest or rng.choice(sorted(QUESTS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(gender, rng)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if (place, quest, helper) not in valid_story_combos():
        raise StoryError(explain_rejection())
    return StoryParams(place=place, quest=quest, helper=helper, name=name, gender=gender, helper_name=helper_name)


def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid stories:\n")
        for p, q, h in combos:
            print(f"  {p:10} {q:12} {h}")
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
