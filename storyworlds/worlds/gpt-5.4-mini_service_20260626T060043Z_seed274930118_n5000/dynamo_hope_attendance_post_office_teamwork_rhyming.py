#!/usr/bin/env python3
"""
storyworlds/worlds/dynamo_hope_attendance_post_office_teamwork_rhyming.py
==========================================================================

A small story world in a post office, built for a rhyming, teamwork-centered
TinyStories-style tale.

Premise:
- A child visits a post office where a little hand-crank dynamo powers the lamp
  over the attendance book.
- The child wants to help, but the crank is stiff and the lamp keeps fading.
- The postal worker worries that if the lamp goes out, the attendance lines will
  be hard to read and the letters will be sorted wrong.
- Teamwork lets everyone share the turn, the lamp shines bright, and the
  attendance sheet gets filled cleanly.

The story is intentionally narrow: only reasonable combinations are generated.
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
    worn_by: Optional[str] = None
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
class Setting:
    place: str = "the post office"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def rhyming_close(a: str, b: str) -> str:
    return f"{a} and {b}"


def safe_name(name: str) -> str:
    return name


def post_office_detail() -> str:
    return "The post office smelled like paper, glue, and stamped-up cheer."


def activity_line(activity: Activity) -> str:
    return {
        "dynamo": "A little hand-crank dynamo sat by the desk, neat and bright.",
        "attendance": "The attendance book waited on the counter, ready for the night.",
        "teamwork": "The mail team lined up close, with steady hands and smiles in sight.",
    }.get(activity.id, "The room was busy, warm, and bright.")


def _predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "drained": bool(actor.meters.get("tired", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["tired"] = actor.meters.get("tired", 0.0) + 1
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
    world.facts["did"] = activity.id
    if narrate:
        world.say(f"{actor.id} tried to {activity.verb}, and the little room began to hum.")


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    helper_name: str = "Nina",
    helper_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the postal worker"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    dynamo = world.add(Entity(id="dynamo", type="machine", label="dynamo"))
    book = world.add(Entity(id="attendance", type="book", label="attendance book"))

    world.say(f"{safe_name(hero.id)} came to {setting.place} with a pep in his step and a hopeful glow.")
    world.say(f"{post_office_detail()} {activity_line(activity)}")
    world.say(f"He loved the little dynamo, and he loved to help the team do things just right.")
    world.say(f"The {book.label} was open wide, for names and notes and all-day pride.")

    world.para()
    world.say(f"{hero.id} wanted to {activity.verb}, but the crank was stiff and slow.")
    world.say(f'{parent.id} frowned and said, "If the lamp goes dim, the attendance lines will not show."')
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1

    pred = _predict(world, hero, activity, prize.id)
    world.facts["pred"] = pred

    world.say(f"{helper.id} said, " + '"Let us work together; one alone can lose the tow."')
    world.say(f"{hero.id} held the crank, {helper.id} held the light, and {parent.id} smiled in the glow.")
    world.say(f"The dynamo spun and the lamp shone strong; the room felt warm and bright.")
    world.say(f"The attendance book was easy to read, and every name sat neat and white.")

    world.para()
    hero.meters["tired"] = hero.meters.get("tired", 0.0) + 1
    helper.meters["tired"] = helper.meters.get("tired", 0.0) + 1
    dynamo.meters["working"] = 1
    book.meters["clean"] = 1
    prize.memes["safe"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1

    world.say(f"In the end, {rhyming_close(hero.id, helper.id)} kept the post office neat and bright.")
    world.say(f"The dynamo hummed, the attendance was done, and the mail went out just right.")
    world.say(f"{hero.id} left with a grin, because teamwork made the whole day glow.")
    world.say(f"The little post office sparkled, warm as a lamp-lit bow.")

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        prize=prize,
        setting=setting,
        activity=activity,
        dynamo=dynamo,
        attendance=book,
        resolved=True,
    )
    return world


SETTINGS = {
    "post_office": Setting(place="the post office", indoor=True, affords={"dynamo", "attendance", "teamwork"}),
}

ACTIVITIES = {
    "dynamo": Activity(
        id="dynamo",
        verb="turn the dynamo",
        gerund="turning the dynamo",
        rush="spin the crank faster",
        mess="tired",
        soil="too tired",
        keyword="dynamo",
        tags={"dynamo"},
    ),
    "attendance": Activity(
        id="attendance",
        verb="fill out the attendance book",
        gerund="writing the attendance",
        rush="reach for the stamp pad",
        mess="inky",
        soil="spotty with ink",
        keyword="attendance",
        tags={"attendance"},
    ),
    "teamwork": Activity(
        id="teamwork",
        verb="work as a team",
        gerund="working as a team",
        rush="do it all alone",
        mess="tired",
        soil="too tired",
        keyword="hope",
        tags={"teamwork", "hope"},
    ),
}

PRIZES = {
    "lamp": Prize(label="lamp", phrase="a small lamp", type="lamp"),
    "book": Prize(label="attendance book", phrase="the attendance book", type="book"),
}

GIRL_NAMES = ["Nina", "Mia", "Zoe", "Ava", "Lila", "June"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Leo", "Ben", "Sam"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("post_office", a, p) for a in ACTIVITIES for p in PRIZES]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this tale needs the post office to face a real teamwork task, "
        f"and {activity.id} with {prize.label} does not produce a strong enough turn.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return (
        f"(No story: this world can still choose names freely, but not this constrained prize/gender pairing.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (args.activity in ACTIVITIES and args.prize in PRIZES):
            raise StoryError("(No valid combination matches the given options.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short rhyming story about a post office, a hopeful child, and teamwork.',
        f"Tell a gentle rhyming tale where {hero.id} and a helper share the work at the post office.",
        'Write a child-friendly story that includes a dynamo, hope, attendance, and a happy team.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer=f"It happens at {world.setting.place}, where the post office keeps its lamp and attendance book.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {activity.verb}, but the crank was stiff and the team had to help.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the work?",
            answer=f"{helper.id} helped {hero.id}, and the postal worker watched happily while they worked together.",
        ),
        QAItem(
            question=f"Why was the {prize.label} important?",
            answer=f"It mattered because the post office needed the {prize.label} to stay clear and ready while the lamp was on.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the dynamo was spinning well, the attendance was filled in, and everyone felt proud of the teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dynamo?",
            answer="A dynamo is a machine that can make electricity when someone turns or spins it.",
        ),
        QAItem(
            question="What does hope mean?",
            answer="Hope is the feeling that something good can happen, even before it does.",
        ),
        QAItem(
            question="What is attendance?",
            answer="Attendance means the list or record of who is present.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and share the job instead of doing it alone.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,R) :- place(P), activity(A), prize(R), workable(A,R).
workable(dynamo, lamp).
workable(attendance, book).
workable(teamwork, lamp).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for aid, act in ACTIVITIES.items():
        for tag in act.tags:
            lines.append(asp.fact("tag", aid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming post-office teamwork story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.helper_name,
        params.helper_gender,
        params.parent,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="post_office", activity="dynamo", prize="lamp", name="Milo", gender="boy", helper_name="Nina", helper_gender="girl", parent="mother"),
    StoryParams(place="post_office", activity="attendance", prize="book", name="Ava", gender="girl", helper_name="Theo", helper_gender="boy", parent="father"),
    StoryParams(place="post_office", activity="teamwork", prize="lamp", name="Leo", gender="boy", helper_name="Mia", helper_gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
