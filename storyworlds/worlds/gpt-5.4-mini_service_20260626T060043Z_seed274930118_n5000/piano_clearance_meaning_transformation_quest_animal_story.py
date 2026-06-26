#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/piano_clearance_meaning_transformation_quest_animal_story.py
========================================================================================================

A small animal-story world about a piano, a clearance problem, and a quest
that changes what the music means.

Premise:
- A young animal loves an old piano.
- The piano is too tall for a low-clearance doorway.
- The parent warns about the scrape and the blocked path.
- They go on a quest to find a safer route and a clever way to fit it through.
- By the end, the piano is in place, and the music carries a new meaning.

Style:
- Animal Story
- Child-facing, concrete, gently emotional
- Clear beginning, middle turn, and ending image
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

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str
    affords: set[str] = field(default_factory=set)
    clearance: int = 0


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    height: int
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    lowers_height_by: int = 0
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the narrow lane", affords={"move_piano", "play_piano"}, clearance=3),
    "hall": Setting(place="the small hall", affords={"move_piano", "play_piano"}, clearance=4),
    "barn": Setting(place="the old barn", affords={"move_piano", "play_piano"}, clearance=5),
    "porch": Setting(place="the porch room", affords={"move_piano", "play_piano"}, clearance=2),
}

ACTIVITIES = {
    "move_piano": Activity(
        id="move_piano",
        verb="move the piano inside",
        gerund="moving the piano",
        rush="hurry toward the doorway with the piano",
        risk="scrape the top against the frame",
        weather="dry",
        keyword="clearance",
        tags={"clearance", "piano"},
    ),
    "play_piano": Activity(
        id="play_piano",
        verb="play the piano",
        gerund="playing the piano",
        rush="rush to the bench",
        risk="miss the meaning of the song",
        weather="",
        keyword="meaning",
        tags={"meaning", "piano"},
    ),
}

PRIZES = {
    "upright": Prize(
        label="piano",
        phrase="an old upright piano",
        type="piano",
        height=5,
        plural=False,
    ),
    "small": Prize(
        label="piano",
        phrase="a small piano",
        type="piano",
        height=3,
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="blanket_wrap",
        label="a soft blanket wrap",
        prep="wrap the piano corners in soft blankets",
        tail="carefully rolled the piano forward",
        lowers_height_by=1,
        helps_with={"move_piano"},
    ),
    Gear(
        id="wheel_cart",
        label="a low wheel cart",
        prep="put the piano on a low wheel cart",
        tail="rolled it along like a slow, careful boat",
        lowers_height_by=2,
        helps_with={"move_piano"},
    ),
    Gear(
        id="open_lid",
        label="an open lid strap",
        prep="tie the lid shut so it stayed low",
        tail="carried it with the lid tucked down",
        lowers_height_by=1,
        helps_with={"move_piano"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Nori", "Poppy", "Kiki", "Maya"]
BOY_NAMES = ["Toby", "Rufus", "Finn", "Coco", "Milo", "Bram"]
TRAITS = ["curious", "gentle", "brave", "patient", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/4.

compatible(Place, Act, Prize) :-
    setting(Place), activity(Act), prize(Prize),
    affords(Place, Act),
    prize_height(Prize, H),
    clearance(Place, C),
    gear_help(Act, G),
    gear_reduction(G, R),
    H - R =< C.

valid(Place, Act, Prize, Gender) :-
    compatible(Place, Act, Prize),
    wears(Gender, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("clearance", sid, s.clearance))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_height", pid, p.height))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        for a in sorted(g.helps_with):
            lines.append(asp.fact("gear_help", a, g.id))
        lines.append(asp.fact("gear_reduction", g.id, g.lowers_height_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if act_id == "move_piano" and prize.height <= setting.clearance:
                    out.append((place, act_id, prize_id))
                if act_id == "play_piano":
                    out.append((place, act_id, prize_id))
    return out


def story_can_move(setting: Setting, prize: Prize, gear: Optional[Gear]) -> bool:
    lowered = gear.lowers_height_by if gear else 0
    return prize.height - lowered <= setting.clearance


def predict_move(world: World, hero: Entity, prize_id: str, gear: Optional[Gear]) -> dict:
    sim = world.copy()
    prize = sim.get(prize_id)
    lowered = gear.lowers_height_by if gear else 0
    fits = prize.meters["height"] - lowered <= sim.setting.clearance
    return {"fits": fits}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
    piano = world.add(Entity(
        id="piano",
        type="piano",
        label="piano",
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    piano.meters["height"] = prize_cfg.height

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved the piano. "
        f"{hero.pronoun().capitalize()} liked the bright notes because they felt like a map."
    )
    world.say(
        f"The old piano had a special meaning to {hero.id}; it was the sound "
        f"that made the house feel like home."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place} "
        f"because there was a music time there."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the doorway had a low clearance."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} looked up and said, "
        f'"If we hurry now, the piano will {activity.risk}."'
    )

    world.facts.update(hero=hero, parent=parent, piano=piano, activity=activity,
                       setting=setting, prize_cfg=prize_cfg)

    # conflict
    gear = None
    if activity.id == "move_piano":
        world.para()
        world.say(
            f"{hero.id} did not want to give up. {hero.pronoun().capitalize()} wanted the music "
            f"to reach the hall."
        )
        world.say(
            f"Together, they looked for a quest that would keep the piano safe and still fit through."
        )
        for g in GEAR:
            if story_can_move(setting, piano, g):
                gear = g
                break
        if gear is None:
            # fallback is always valid by registries, but keep explicit
            gear = GEAR[0]
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {parent.label} found {gear.label} and smiled. "
            f'"How about we {gear.prep}?"'
        )
        world.say(
            f"{hero.id}'s ears lifted. The piano quest suddenly had a way forward."
        )
        world.para()
        world.say(
            f"They {gear.tail}, and the piano slid through the doorway without a bump."
        )
        world.say(
            f"At the end, the piano sat inside the hall, and the meaning of the trip changed: "
            f"it was not only about moving wood and strings, but about bringing a song to other hearts."
        )
        world.say(
            f"{hero.id} played one careful tune, and the room felt warm and new."
        )
        world.facts["gear"] = gear
        world.facts["resolved"] = True
    else:
        world.para()
        world.say(
            f"{hero.id} sat at the bench and began to play."
        )
        world.say(
            f"The first notes were shy, but then the meaning of the melody grew clear: "
            f"the song was about home, patience, and trying again."
        )
        world.say(
            f"{hero.id} smiled as the little hall grew quiet around the piano."
        )
        world.facts["gear"] = None
        world.facts["resolved"] = True

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    act: Activity = f["activity"]
    return [
        f'Write a short Animal Story about a {hero.type} named {hero.id}, a piano, and a word like "{act.keyword}".',
        f"Tell a child-friendly quest where {hero.id} tries to {act.verb} at {world.setting.place} but must think about clearance.",
        f"Write a gentle animal story that includes the words piano, clearance, and meaning, and ends with music that matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    act: Activity = f["activity"]
    prize: Prize = f["prize_cfg"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.traits[1]} {hero.type} who loves the piano.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face with the piano?",
            answer=f"The piano was too tall for the doorway, so the low clearance made it hard to move inside.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label.capitalize()} worried that the piano would scrape the frame if they tried to rush it through.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb} and bring the piano where the music could be heard.",
        ),
    ]
    if f.get("gear"):
        gear: Gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} helped lower the piano enough for the clearance, so they could move it safely.",
        ))
    qa.append(QAItem(
        question="What changed by the end?",
        answer="By the end, the piano was inside, and its meaning changed from a heavy object to a shared song.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does clearance mean in a doorway?",
            answer="Clearance is the space that lets something fit through without hitting the top or sides.",
        ),
        QAItem(
            question="What is a piano?",
            answer="A piano is a musical instrument with keys that make notes when they are pressed.",
        ),
        QAItem(
            question="What does meaning mean in a story or song?",
            answer="Meaning is what something is about or what it makes people understand or feel.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve a problem, or reach an important goal.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form, feeling, or way of being.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from this story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level facts ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {
        (place, act, prize, gender)
        for place, act, prize in valid_story_params()
        for gender in PRIZES[prize].genders
    }
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python valid_story_params() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a piano, clearance, and meaning.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (place, act, prize)
        for place, act, prize in valid_story_params()
        if (args.place is None or place == args.place)
        and (args.activity is None or act == args.activity)
        and (args.prize is None or prize == args.prize)
        and (args.gender is None or args.gender in PRIZES[prize].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name,
                       gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.parent,
        params.trait,
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
    StoryParams(place="hall", activity="move_piano", prize="upright", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="barn", activity="play_piano", prize="small", name="Toby", gender="boy", parent="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
