#!/usr/bin/env python3
"""
storyworlds/worlds/sacrament_invent_humor_slice_of_life.py
==========================================================

A small slice-of-life story world about a child, a quiet sacrament day,
and a funny little invention that turns a wiggly morning into a calmer one.

Seed tale used to build the world:
---
On Sunday morning, Ada wanted to invent something. She loved making tiny
machines out of paper clips, tape, and imagination. But it was time for the
sacrament, and her family needed to leave soon. Ada kept bouncing around the
kitchen, jingling spoons, until her mom smiled and asked her to invent a
quiet game instead. Ada made a “still hands” game, folded paper stars, and
decided the church pew could be the perfect test lab for silence.

World idea:
---
The story follows a child who loves invention, but the family is trying to
keep the morning peaceful for sacrament meeting. The tension is not danger;
it is wiggly energy, noisy tools, and the need to be respectful and calm.
The turn comes when the child invents a gentle quiet game that fits the
setting, and everyone arrives with a small, humorous sense of triumph.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    quietness: str = "calm"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    guard: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.noise: float = 0.0

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.noise = self.noise
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"invent", "breakfast", "tidy"}),
    "living_room": Setting(place="the living room", affords={"invent", "quiet_game"}),
    "hallway": Setting(place="the hallway", affords={"invent"}),
    "car": Setting(place="the car", affords={"invent"}, quietness="extra quiet"),
    "chapel": Setting(place="the chapel", affords={"invent", "sacrament"}),
}

ACTIVITIES = {
    "invent": Activity(
        id="invent",
        verb="invent a quiet game",
        gerund="inventing quiet games",
        rush="dash for the markers and tape",
        mess="noisy",
        soil="all jittery",
        keyword="invent",
        tags={"invent", "humor"},
    ),
    "breakfast": Activity(
        id="breakfast",
        verb="eat breakfast",
        gerund="eating breakfast",
        rush="grab the cereal spoon",
        mess="crumbly",
        soil="crumbly",
        keyword="breakfast",
        tags={"morning"},
    ),
    "quiet_game": Activity(
        id="quiet_game",
        verb="play a whisper game",
        gerund="playing whisper games",
        rush="start a loud count-and-point game",
        mess="noisy",
        soil="too loud",
        keyword="quiet",
        tags={"quiet", "humor"},
    ),
    "sacrament": Activity(
        id="sacrament",
        verb="sit reverently during sacrament",
        gerund="sitting quietly during sacrament",
        rush="fidget in the pew",
        mess="noisy",
        soil="too bouncy",
        keyword="sacrament",
        tags={"sacrament", "quiet"},
    ),
    "tidy": Activity(
        id="tidy",
        verb="tidy the table",
        gerund="tidying the table",
        rush="scatter paper and pencils",
        mess="crumbly",
        soil="messy",
        keyword="tidy",
        tags={"home"},
    ),
}

PRIZES = {
    "paper": Prize(label="paper", phrase="a stack of white paper", region="hands", type="paper", plural=True),
    "markers": Prize(label="markers", phrase="a little box of markers", region="hands", type="markers", plural=True),
    "program": Prize(label="program", phrase="a folded sacrament program", region="hands", type="program"),
    "crumbs": Prize(label="crumbs", phrase="a few breakfast crumbs", region="table", type="crumbs", plural=True),
}

GEAR = [
    Gear(
        id="pencil",
        label="one quiet pencil",
        guard="noisy",
        prep="use one quiet pencil instead of the whole marker box",
        tail="swapped the markers for one quiet pencil",
    ),
    Gear(
        id="paper_star",
        label="a paper-star trick",
        guard="noisy",
        prep="make a paper-star trick for waiting still",
        tail="folded a paper-star trick",
    ),
    Gear(
        id="whisper_plan",
        label="a whisper plan",
        guard="noisy",
        prep="use a whisper plan during sacrament",
        tail="kept the whisper plan in their laps",
    ),
]

GIRL_NAMES = ["Ada", "Mina", "June", "Lily", "Nora", "Maya"]
BOY_NAMES = ["Eli", "Owen", "Theo", "Noah", "Finn", "Leo"]
TRAITS = ["curious", "silly", "thoughtful", "bouncy", "clever"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "sacrament" and prize in {"markers", "paper", "program"}:
                    combos.append((place, act, prize))
                elif act == "invent" and prize in {"paper", "markers", "program"}:
                    combos.append((place, act, prize))
                elif act == "quiet_game" and prize in {"program"}:
                    combos.append((place, act, prize))
    return combos


def reason_invalid(act: Activity, prize: Prize) -> str:
    return (
        f"(No story: {act.verb} does not fit well with {prize.phrase}. "
        f"Try a prize the child could use for a calm, funny invention.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sacrament/invent story world.")
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
        if args.activity == "sacrament" and args.prize not in {"markers", "paper", "program"}:
            raise StoryError(reason_invalid(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["busy"] = actor.meters.get("busy", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if activity.mess == "noisy":
        actor.meters["noise"] = actor.meters.get("noise", 0.0) + 1
        world.noise += 1
    if narrate:
        world.say(f"{actor.id} was {activity.gerund}.")


def predict_noise(world: World, actor: Entity, activity: Activity) -> float:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.noise


def tell(world: World, hero_name: str, gender: str, parent_type: str, trait: str, activity: Activity, prize: Prize) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    item = world.add(Entity(id=prize.label, type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=parent.id))

    world.say(f"{hero.id} was a little {trait} {gender} who loved to invent things.")
    world.say(f"On Sunday morning, {hero.id} was at {world.setting.place}, where the day felt calm and a little serious.")
    world.say(f"{hero.id}'s {parent_type} set down {prize.phrase} and reminded {hero.pronoun('object')} that sacrament time was almost here.")
    world.para()

    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} hands kept reaching for something funny to do.")
    if predict_noise(world, hero, activity) >= THRESHOLD:
        world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, and the kitchen started to feel too lively.")
        world.say(f'"If we do that now, the morning will get {activity.soil}," {hero.pronoun("possessive")} {parent_type} said with a smile.')
    world.say(f"{hero.id} looked at {prize.phrase} and got an idea.")
    world.para()

    gear = None
    if activity.id == "invent":
        gear = world.add(Entity(id="paper_star", type="gear", label="paper-star trick"))
        world.say(f"{hero.id} invented a tiny paper-star trick instead of a noisy machine.")
        world.say(f"{hero.id}'s {parent_type} said that was a very useful invention for a chapel seat.")
        world.say(f"They took the {prize.label} with them, and {hero.id} promised to test the invention with whisper voices only.")
    elif activity.id == "quiet_game":
        gear = world.add(Entity(id="whisper_plan", type="gear", label="whisper plan"))
        world.say(f"{hero.id} invented a whisper plan: point, nod, and smile without making a peep.")
        world.say(f"{hero.id}'s {parent_type} laughed because the plan sounded like a secret agent game for church.")
        world.say(f"They headed out with the {prize.label} tucked safely in hand.")
    else:
        gear = world.add(Entity(id="pencil", type="gear", label="quiet pencil"))
        world.say(f"{hero.id} invented a silly little pattern of stars to trace while waiting.")
        world.say(f"It was not a machine, which was probably for the best.")
        world.say(f"{hero.id}'s {parent_type} said the calm idea would work beautifully during sacrament.")

    world.para()
    world.say(f"At sacrament, {hero.id} sat still, held {hero.pronoun('possessive')} {prize.label}, and used the little idea {hero.pronoun('subject')} had invented.")
    world.say(f"The paper-star trick worked so well that {hero.id} did not even need to wiggle.")
    world.say(f"By the end, the funniest part was that the great invention was only {gear.label}, and it made the whole morning kinder.")
    world.facts.update(hero=hero, parent=parent, prize=item, activity=activity, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story with the words "{f["activity"].keyword}" and "sacrament".',
        f"Tell a gentle humorous story about {f['hero'].id} inventing a quiet idea before sacrament.",
        f"Write a child-friendly story where a family gets ready for sacrament and a child invents a calm game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    prize = f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do on Sunday morning?",
            answer=f"{hero.id} loved to {activity.verb}, but first {hero.pronoun('subject')} had to find a quiet way to do it."
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.type} worry a little?",
            answer=f"{hero.id}'s {parent.type} worried because {hero.pronoun('possessive')} idea might make the morning too noisy before sacrament."
        ),
        QAItem(
            question=f"What did {hero.id} invent instead of making a lot of noise?",
            answer=f"{hero.id} invented {gear.label}, a quiet little idea that helped {hero.pronoun('object')} stay calm."
        ),
        QAItem(
            question=f"What did the family bring to sacrament with them?",
            answer=f"They brought {prize.phrase}, and {hero.id} used the new idea to sit quietly with it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sacrament meeting?",
            answer="A sacrament meeting is a church gathering where people sit quietly, listen, and take part in a reverent service."
        ),
        QAItem(
            question="What does it mean to invent something?",
            answer="To invent something means to make up a new idea, tool, or game that did not exist before."
        ),
        QAItem(
            question="Why can quiet games be helpful?",
            answer="Quiet games can help people wait patiently and keep their bodies calm when they need to be still."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  noise={world.noise}")
    return "\n".join(lines)


ASP_RULES = r"""
noisy(A) :- activity(A), mess_of(A,noisy).
compatible(A,P) :- activity(A), prize(P), valid_combo(A,P).
valid_combo(invent,paper).
valid_combo(invent,markers).
valid_combo(invent,program).
valid_combo(sacrament,program).
valid_combo(sacrament,paper).
valid_combo(quiet_game,program).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    clingo_set = set(asp.atoms(model, "valid_combo"))
    python_set = {(a, p) for _, a, p in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world = tell(world, params.name, params.gender, params.parent, params.trait, ACTIVITIES[params.activity], PRIZES[params.prize])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(place="kitchen", activity="invent", prize="paper", name="Ada", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="living_room", activity="quiet_game", prize="program", name="Theo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="chapel", activity="sacrament", prize="program", name="Mina", gender="girl", parent="mother", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/2."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:")
        for a, p in combos:
            print(f"  {a:12} {p}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
