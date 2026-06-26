#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/zombie_early_study_happy_ending_ghost_story.py
===============================================================================================================

A small, standalone story world for a gentle ghost-story-style tale about a
zombie who wants to study early, with a happy ending.

The domain is intentionally tiny:
- one haunted study setting,
- a few study activities,
- a few fragile prizes,
- a few reasonable fixes.

The story is driven by state changes:
- the zombie's curiosity and worry rise and fall,
- study can make paper messy,
- protective gear can prevent the mess,
- the ending proves what changed.

The tone stays child-facing, spooky in a soft way, and ends happily.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["dust", "smudge", "wet", "tiredness", "care", "fear"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "joy", "love", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        zombie = {"zombie"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in zombie:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old study"
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
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "zombie"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "study": Setting(place="the old study", indoor=True, affords={"early_study", "quiet_reading"}),
}

ACTIVITIES = {
    "early_study": Activity(
        id="early_study",
        verb="study early",
        gerund="studying early",
        rush="rush to the desk",
        mess="smudge",
        soil="smudged",
        zone={"hands"},
        keyword="early",
        tags={"early", "study"},
    ),
    "quiet_reading": Activity(
        id="quiet_reading",
        verb="read quietly",
        gerund="reading quietly",
        rush="tiptoe to the shelf",
        mess="dust",
        soil="dusty",
        zone={"hands", "torso"},
        keyword="study",
        tags={"study"},
    ),
}

PRIZES = {
    "notebook": Prize(
        label="notebook",
        phrase="a neat notebook with blue stars",
        type="notebook",
        region="hands",
    ),
    "book": Prize(
        label="book",
        phrase="an old storybook with a ribbon bookmark",
        type="book",
        region="hands",
    ),
    "lamp": Prize(
        label="lamp",
        phrase="a little lamp with a warm yellow glow",
        type="lamp",
        region="torso",
        genders={"girl", "boy", "zombie"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft study gloves",
        covers={"hands"},
        guards={"smudge", "dust"},
        prep="put on soft study gloves first",
        tail="put on the soft study gloves",
    ),
    Gear(
        id="apron",
        label="a paper apron",
        covers={"torso"},
        guards={"dust"},
        prep="tie on a paper apron first",
        tail="tied on the paper apron",
    ),
    Gear(
        id="bookstand",
        label="a wooden bookstand",
        covers={"hands"},
        guards={"smudge"},
        prep="set the notebook on a wooden bookstand first",
        tail="set the notebook on the wooden bookstand",
    ),
]

NAMES = ["Zuri", "Nico", "Milo", "Ivy", "Pip", "Luna", "Theo"]
TRAITS = ["gentle", "curious", "brave", "sleepy", "friendly"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("smudge", "dust"):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                out.append(f"{actor.id}'s {item.label} got {mess}y.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["smudge"] >= THRESHOLD:
            sig = ("worry", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] += 1
            out.append(f"{actor.id} looked worried.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("worry", _r_worry)]


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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters[activity.mess] >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def tell(world_setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, parent_type: str, trait: str) -> World:
    world = World(world_setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="zombie", traits=["little", trait]))
    parent = world.add(Entity(id="Guide", kind="character", type=parent_type, label="the guide"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.say(f"{hero.id} was a little {trait} zombie who loved quiet mornings in {world_setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} liked the hush before sunrise and {activity.gerund}.")
    world.say(f"The guide had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} treasured it.")

    world.para()
    world.say(f"Early one morning, {hero.id} went into {world_setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} worried about {hero.pronoun('possessive')} {prize.label}.")

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"You might get your {prize.label} {activity.soil}," said {parent.label}.')
        world.say(f"{hero.id} stopped and listened.")
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No reasonable fix exists for this activity and prize.")
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
        gear_ent.worn_by = hero.id
        world.say(f"{hero.id}'s {parent.label} smiled. \"{gear.prep.capitalize()}, and then you can still study.\"")
        hero.memes["joy"] += 1
        hero.memes["love"] += 1
        world.say(f"{hero.id} nodded, put on {gear.label}, and felt brave enough to begin.")

        world.para()
        do_activity(world, hero, activity, narrate=True)
        world.say(f"So {hero.id} was {activity.gerund}, and the {prize.label} stayed clean.")
        world.say(f"When the first light reached the window, {hero.id} had learned the whole page, and the old study felt cozy instead of spooky.")
        world.say(f"{hero.id} and {parent.label} smiled together at the end of the quiet, happy morning.")
    else:
        do_activity(world, hero, activity, narrate=True)
        world.para()
        world.say(f"{hero.id} studied early, and nothing got messy.")
        world.say(f"The old study stayed calm, and the morning ended with a happy smile.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=world_setting)
    return world


SETTINGS_ORDER = ["study"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten a prize worn on the {prize.region}.)"
    return f"(No story: there is no reasonable gear that protects the {prize.label} from {activity.gerund}.)"


@dataclass
class StoryParams2(StoryParams):
    pass


StoryParams = StoryParams2


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short ghost-story-style tale for a child about a zombie named {hero.id} who wants to {act.verb} early in the old study.',
        f"Tell a spooky-but-kind story where {hero.id} worries about {hero.pronoun('possessive')} {prize.label}, then finds a happy way to keep studying.",
        f'Write a gentle story that includes the words "zombie", "early", and "study", and ends with a happy morning light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little zombie who loves early study in the old study.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do early in the old study?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because {hero.id}'s {prize.label} could get {act.soil} during {act.gerund}.",
        ),
        QAItem(
            question=f"How did the happy ending happen?",
            answer=f"{hero.id} put on the right gear, studied safely, and the morning ended with calm smiles in the old study.",
        ),
    ]
    gear = select_gear(act, prize)
    if gear:
        qa.append(
            QAItem(
                question=f"What helped {hero.id} keep the {prize.label} clean while studying?",
                answer=f"{gear.label} helped {hero.id} study without ruining the {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a zombie in a gentle story?", answer="In a gentle story, a zombie can be a spooky-looking friend who still thinks, feels, and learns."),
        QAItem(question="What does early mean?", answer="Early means before much of the day has started, often around sunrise."),
        QAItem(question="What is a study?", answer="A study is a quiet place for reading, learning, and thinking."),
        QAItem(question="Why do people use a bookstand?", answer="A bookstand holds a book up so the pages stay open and easier to read."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world about a zombie who studies early.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father", "guide"], default="guide")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        parent=args.parent,
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent, params.trait)
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
    StoryParams(place="study", activity="early_study", prize="notebook", name="Zuri", parent="guide", trait="curious"),
    StoryParams(place="study", activity="early_study", prize="book", name="Nico", parent="guide", trait="gentle"),
    StoryParams(place="study", activity="quiet_reading", prize="lamp", name="Ivy", parent="guide", trait="friendly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:14} {prize:10}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
