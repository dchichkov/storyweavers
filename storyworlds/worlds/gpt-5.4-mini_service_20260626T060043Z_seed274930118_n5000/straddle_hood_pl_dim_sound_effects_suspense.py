#!/usr/bin/env python3
"""
storyworlds/worlds/straddle_hood_pl_dim_sound_effects_suspense.py
=================================================================

A small, heartwarming story world built from the seed words
"straddle" and "hood-pl-dim".

Domain premise:
- A child and a caregiver are crossing a twilight garden.
- The child wants to straddle a low garden rail to reach a shy little lantern-fawn
  figurine tucked near the bean patch.
- The path grows suspenseful as the hooded porch lantern flickers with a soft
  "hood-pl-dim" sound.
- The caregiver notices the danger, offers a safer way, and the child accepts.
- Sound effects are part of the narration, but the ending stays warm and gentle.

This script follows the Storyworld contract:
- typed entities with meters and memes
- state-driven prose
- explicit invalid combinations raise StoryError
- inline ASP twin with facts and parity check
- generation, QA, JSON, trace, verify, and ASP CLI modes
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bruised": 0.0, "lost": 0.0, "dim": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "courage": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    sound: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_or_carried(self, actor: Entity) -> list[Entity]:
        out = []
        for e in self.entities.values():
            if e.worn_by == actor.id or e.carried_by == actor.id:
                out.append(e)
        return out


SETTINGS = {
    "garden": Setting(place="the garden", outdoor=True, affords={"straddle"}),
    "porch": Setting(place="the porch", outdoor=True, affords={"straddle"}),
    "backyard": Setting(place="the backyard", outdoor=True, affords={"straddle"}),
}

ACTIVITIES = {
    "straddle": Activity(
        id="straddle",
        verb="straddle the low rail",
        gerund="straddling the low rail",
        rush="scoot over the rail",
        risk="bump the little lantern and make it go dim",
        sound="hood-pl-dim",
        zone={"hands", "legs"},
        keyword="straddle",
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little hooded lantern with a bright glass globe",
        type="lantern",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="lantern_cover",
        label="a clear lantern cover",
        phrase="a clear cover for the lantern",
        covers={"hands"},
        helps={"dim"},
        prep="slip a clear cover over the lantern first",
        tail="walked slowly to the rail with the lantern shining safely",
    )
]

GIRL_NAMES = ["Maya", "Lina", "Nora", "Ivy", "Ella", "Rose"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Owen", "Max"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if act == "straddle" and prize.region in ACTIVITIES[act].zone:
                    combos.append((place, act, prize_id))
    return combos


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and "dim" in gear.helps:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would only endanger a prize carried in the {sorted(activity.zone)}, "
        f"but {prize.label} is not a good fit for this scene.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming twilight rail-straddling story world.")
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize.region in act.zone and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def _activity_effect(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.memes["courage"] += 0.5
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} took a breath and went on.")


def predict_turn(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _activity_effect(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"dim": prize.meters["dim"] >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
    ))

    world.say(f"{hero.id} was a little {hero_gender} who liked evening walks with {hero.pronoun('possessive')} {parent.label}.")
    world.say(f"Together they carried {hero.pronoun('possessive')} {prize.phrase}, because the warm glow made the garden feel safe.")
    world.para()
    world.say(f"Near {world.setting.place}, {hero.id} heard a tiny sound: \"{activity.sound}.\"")
    world.say(f"That made the twilight feel a little suspenseful, and {hero.id} wanted to {activity.verb} right away.")
    _activity_effect(world, hero, activity, narrate=False)
    pred = predict_turn(world, hero, activity, prize.id)
    if pred["dim"]:
        prize.meters["dim"] += 1
        hero.memes["worry"] += 1
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} held up a gentle hand. \"If you {activity.rush}, the {prize.label} might go dim,\" {parent.label} said.")
        world.say(f"{hero.id} hesitated, listening to the quiet grass and the soft \"{activity.sound}.\"")
        world.para()
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No reasonable safety gear exists for this story.")
        gear_ent = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            phrase=gear.phrase,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
        ))
        gear_ent.worn_by = hero.id
        world.say(f"Then {hero.pronoun('possessive')} {parent.label} smiled and said, \"Let's {gear.prep} together.\"")
        world.say(f"{hero.id} nodded, and they {gear.tail}.")
        prize.meters["dim"] = 0
        hero.memes["joy"] += 1
        hero.memes["comfort"] += 1
        world.say(f"The lantern stayed bright, {activity.sound} turned into a happy little echo, and {hero.id} straddled the rail only after everything was safe.")
        world.say(f"At the end, the garden felt warm again, with {hero.id} laughing beside {hero.pronoun('possessive')} {parent.label} and the lantern shining like a tiny star.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_ent, resolved=True)
    else:
        world.say(f"The path stayed bright enough, so {hero.id} crossed without trouble.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=None, resolved=False)
    return world


KNOWLEDGE = {
    "straddle": [
        ("What does it mean to straddle something?",
         "To straddle something means to sit or stand with one leg on each side, like when you balance over a low rail or a bike."),
    ],
    "hood": [
        ("What is a hood on a coat?",
         "A hood is the part of a coat that can cover your head and help keep it warm or dry."),
    ],
    "lantern": [
        ("What is a lantern for?",
         "A lantern gives off light so people can see better when it is dark."),
    ],
    "dim": [
        ("What does dim mean?",
         "Dim means not very bright. A dim light is soft and weak instead of shining strongly."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a heartwarming story for a young child that includes the words "{act.keyword}" and "{act.sound}".',
        f"Tell a suspenseful but gentle story about {hero.id} wanting to {act.verb} with {prize.label} nearby, and ending safely.",
        f"Write a short story where a child hears \"{act.sound}\" in the garden and learns to choose a safer way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    qas = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} caring {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}, even though the tiny sound \"{activity.sound}\" made the moment feel suspenseful.",
        ),
        QAItem(
            question=f"What was special about the {prize.label}?",
            answer=f"It was {prize.phrase}, and everyone wanted to keep it bright and safe.",
        ),
    ]
    if f.get("gear") is not None:
        qas.append(
            QAItem(
                question=f"How did the clear cover help?",
                answer=f"It helped by protecting the lantern from going dim, so {hero.id} could stay close without making the light fade.",
            )
        )
        qas.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy, safer, and comforted after choosing the gentle plan with {hero.pronoun('possessive')} {parent.label}.",
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"straddle", "hood", "lantern", "dim"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), helps(G, dim).
valid(Place,A,P) :- setting(Place), affords(Place,A), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


CURATED = [
    StoryParams(place="garden", activity="straddle", prize="lantern", name="Maya", gender="girl", parent="mother"),
    StoryParams(place="backyard", activity="straddle", prize="lantern", name="Finn", gender="boy", parent="father"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
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
