#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/distinction_friendship_teamwork_suspense_folk_tale.py
====================================================================================================

A small folk-tale storyworld about a child, a friend, a distinction-mark, and a
careful teamwork rescue under suspense.

Premise imagined from the seed:
- A small village holds a folk fair with a badge of distinction for a brave,
  kind pair.
- Two friends want the mark, but the path to it is uncertain: dusk comes on,
  a crossing is shaky, and the prize is out of reach.
- The turn is not winning by force, but by friendship and teamwork: one holds,
  one climbs, one waits, and they reach the mark together.

The world model tracks:
- physical meters: distance, height, sway, darkness, wind, fatigue, safety
- emotional memes: hope, worry, trust, pride, fear, friendship, teamwork

The narration stays child-facing and story-driven, with a clear beginning,
middle suspense, and ending image that proves what changed.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    terrain: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    danger: str
    zone: str
    suspense: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    distinction: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    benefit: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.task_zone: str = ""
        self.darkness: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.task_zone = self.task_zone
        w.darkness = self.darkness
        return w


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = _meter(ent, key) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _rules(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if _meter(ent, "worry") >= THRESHOLD and _meter(ent, "trust") >= THRESHOLD:
            sig = ("steady", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                _add_meter(ent, "fear", -0.5)
                _add_meme(ent, "brave", 1.0)
                out.append(f"{ent.id} took a steady breath and stood a little taller.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _rules(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region == task.zone


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if task.id in aid.tags and prize.region in aid.benefit:
            return aid
    return None


def make_setting_detail(setting: Setting) -> str:
    return {
        "village": f"The village green lay open under a round sky.",
        "forest": f"The forest held cool shadows between the trees.",
        "river": f"The riverbank shone, and the water hummed softly.",
    }[setting.id]


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    world.task_zone = task.zone
    _add_meter(hero, "distance", 1.0)
    _add_meter(hero, "fatigue", 1.0)
    _add_meme(hero, "hope", 0.5)
    _add_meme(hero, "teamwork", 0.5)
    if task.id == "cross_bridge":
        _add_meter(world.get("bridge"), "sway", 1.0)
        _add_meter(world.get("bridge"), "risk", 1.0)
    elif task.id == "find_path":
        _add_meter(world.get("woods"), "darkness", 1.0)
    elif task.id == "carry_water":
        _add_meter(world.get("bucket"), "weight", 1.0)
    propagate(world, narrate=narrate)


def predict_risk(world: World, hero: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(hero.id), task, narrate=False)
    prize = sim.get(prize_id)
    return {
        "lost": _meter(prize, "safety") < THRESHOLD,
        "worry": _meter(sim.get(hero.id), "worry"),
    }


def build_story(world: World, hero: Entity, friend: Entity, elder: Entity, task: Task, prize: Prize, aid: Optional[Aid]) -> None:
    world.say(f"In the {world.setting.place}, a little tale began under {world.setting.mood} skies.")
    world.say(f"{hero.id} was a {hero.type} with a kind heart, and {friend.id} was {friend.phrase}.")
    world.say(f"They had heard of {prize.phrase}, a mark of {prize.distinction}, and both wished to earn it fairly.")
    world.say(make_setting_detail(world.setting))
    world.say(f"At dawn, {hero.id} and {friend.id} set out to {task.verb}.")
    world.say(f"The work looked simple, but {task.suspense}")

    _add_meter(hero, "worry", 1.0)
    _add_meter(friend, "worry", 1.0)
    _add_meme(hero, "friendship", 1.0)
    _add_meme(friend, "friendship", 1.0)

    risk = predict_risk(world, hero, task, prize.id)
    if risk["lost"]:
        world.say(f"{elder.id} shook {elder.pronoun('possessive')} head and warned, \"{task.risk}\"")
    else:
        world.say(f"{elder.id} watched them go and said the task would need care, not haste.")

    _do_task(world, hero, task, narrate=False)
    _add_meter(hero, "worry", 0.5)
    _add_meter(friend, "worry", 0.5)
    _add_meter(world.get("path"), "sway", 1.0)

    world.say(f"As the path grew harder, {task.danger}")
    world.say(f"{friend.id} said, \"I will hold the way steady.\"")
    _add_meter(friend, "trust", 1.0)
    _add_meter(hero, "trust", 1.0)

    if aid:
        world.say(f"Then they used {aid.label}; {aid.prep}, and {aid.benefit}.")
        _add_meter(hero, "safety", 1.0)
        _add_meter(friend, "safety", 1.0)
        _add_meme(hero, "pride", 1.0)
        _add_meme(friend, "pride", 1.0)
    else:
        world.say(f"They worked together all the harder, with no helper but their own hands.")

    _add_meter(prize_ent := world.get(prize.id), "safety", 1.0)
    _add_meme(hero, "teamwork", 1.0)
    _add_meme(friend, "teamwork", 1.0)
    world.say(f"At last, {hero.id} reached the {prize.label}, and {friend.id} held the line below.")
    world.say(f"The {prize.label} was theirs by shared effort, and the old fear slid away like mist.")
    world.say(f"That evening, the village saw {hero.id} and {friend.id} return with {prize.phrase} shining between them.")
    world.say(f"So the tale ended with friendship, teamwork, and a fine mark of distinction.")

    world.facts.update(hero=hero, friend=friend, elder=elder, task=task, prize=prize, aid=aid)


SETTINGS = {
    "village": Setting(place="the village green", mood="clear", terrain="meadow", affords={"cross_bridge", "carry_water"}),
    "forest": Setting(place="the oak forest", mood="quiet", terrain="woods", affords={"find_path", "cross_bridge"}),
    "river": Setting(place="the riverbank", mood="bright", terrain="water", affords={"carry_water", "cross_bridge"}),
}
SETTINGS["village"].id = "village"  # type: ignore[attr-defined]
SETTINGS["forest"].id = "forest"    # type: ignore[attr-defined]
SETTINGS["river"].id = "river"      # type: ignore[attr-defined]

TASKS = {
    "cross_bridge": Task(
        id="cross_bridge",
        verb="cross the swaying bridge",
        gerund="crossing the swaying bridge",
        risk="The bridge may sway too much if no one keeps it still.",
        danger="the boards shivered under their feet, and the river showed through the gaps.",
        zone="bridge",
        suspense="the old bridge creaked, and one wrong step could send a traveler lurching sideways.",
        tags={"bridge", "sway", "suspense"},
    ),
    "find_path": Task(
        id="find_path",
        verb="find the hidden path",
        gerund="finding the hidden path",
        risk="The woods can swallow a trail when the light grows dim.",
        danger="the trees closed in, and the path seemed to vanish in the hush.",
        zone="woods",
        suspense="the path was there and not there, as if the forest itself were playing a trick.",
        tags={"woods", "dark", "suspense"},
    ),
    "carry_water": Task(
        id="carry_water",
        verb="carry water from the spring",
        gerund="carrying water from the spring",
        risk="A full bucket is hard to manage on the long way back.",
        danger="the bucket grew heavy, and every step asked for patience.",
        zone="bucket",
        suspense="the water sloshed near the rim, waiting for the smallest bump.",
        tags={"water", "bucket", "suspense"},
    ),
}

PRIZES = {
    "blue_sash": Prize(
        id="blue_sash",
        label="blue sash",
        phrase="a blue sash of distinction",
        region="bridge",
        distinction="pair who can steady trouble together",
        tags={"sash", "distinction"},
    ),
    "silver_pin": Prize(
        id="silver_pin",
        label="silver pin",
        phrase="a silver pin of distinction",
        region="woods",
        distinction="pair who can find the way in time",
        tags={"pin", "distinction"},
    ),
    "golden_bucket": Prize(
        id="golden_bucket",
        label="golden bucket",
        phrase="a golden bucket of distinction",
        region="bucket",
        distinction="pair who can carry water without spilling",
        tags={"bucket", "distinction"},
    ),
}

AIDS = [
    Aid(
        id="plank",
        label="a stout plank",
        prep="one held it across the weak boards",
        benefit="the others could cross with the bridge less shaken",
        tags={"cross_bridge"},
    ),
    Aid(
        id="lantern",
        label="a small lantern",
        prep="its light was set high at the turn of the trees",
        benefit="the hidden path could be seen before dusk swallowed it",
        tags={"find_path"},
    ),
    Aid(
        id="rope",
        label="a braided rope",
        prep="one friend tied it around the bucket handle",
        benefit="the water stayed steady on the climb home",
        tags={"carry_water"},
    ),
]

HEROES = ["Mara", "Niko", "Tavi", "Lina", "Perrin", "Anya"]
FRIENDS = ["fox friend", "rabbit friend", "owl friend", "badger friend"]
ELDERS = ["grandmother", "old miller", "village keeper"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero: str
    friend: str
    elder: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(task, prize) and select_aid(task, prize):
                    out.append((place, task_id, prize_id))
    return out


def explain_rejection(task: Task, prize: Prize) -> str:
    return (
        f"(No story: {task.verb} does not fit the prize {prize.phrase} in a way "
        f"that a sensible helper can actually improve. The distinction must be "
        f"won by a real rescue, not a decorative ending.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about friendship, teamwork, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--elder")
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
    if args.task and args.prize:
        task = TASKS[args.task]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(task, prize) and select_aid(task, prize)):
            raise StoryError(explain_rejection(task, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice(FRIENDS)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, task=task, prize=prize, hero=hero, friend=friend, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    task = TASKS[params.task]
    prize = PRIZES[params.prize]
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="thing", phrase=f"a loyal {params.friend}"))
    elder = world.add(Entity(id=params.elder, kind="character", type="thing", phrase=f"the wise {params.elder}"))
    bridge = world.add(Entity(id="bridge", type="thing"))
    woods = world.add(Entity(id="woods", type="thing"))
    path = world.add(Entity(id="path", type="thing"))
    bucket = world.add(Entity(id="bucket", type="thing"))
    prize_ent = world.add(Entity(id=prize.id, type="thing", label=prize.label, phrase=prize.phrase))
    prize_ent.meters["safety"] = 0.0

    aid = select_aid(task, prize)
    build_story(world, hero, friend, elder, task, prize, aid)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short folk tale where {params.hero} and a {params.friend} earn {prize.phrase}.",
            f"Tell a suspenseful story set at {world.setting.place} about friendship and teamwork.",
            f"Write a child-friendly tale in which two friends face {task.suspense.lower()} and find a fair reward.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder, task, prize = f["hero"], f["friend"], f["elder"], f["task"], f["prize"]
    aid = f["aid"]
    out = [
        QAItem(
            question=f"Who went on the hard errand in the tale?",
            answer=f"{hero.id} and {friend.id} went together, and {elder.id} watched over them.",
        ),
        QAItem(
            question=f"What made the journey suspenseful?",
            answer=f"It was suspenseful because {task.suspense}",
        ),
        QAItem(
            question=f"What were they trying to earn?",
            answer=f"They were trying to earn {prize.phrase}, which is {prize.distinction}.",
        ),
    ]
    if aid:
        out.append(QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used {aid.label} so the task could be done safely, and their teamwork kept the danger from winning.",
        ))
    out.append(QAItem(
        question=f"How did the story end?",
        answer=f"It ended with {hero.id} and {friend.id} returning together, proud and safe, with {prize.phrase} shining between them.",
    ))
    return out


WORLD_KNOWLEDGE = {
    "sash": [
        QAItem(
            question="What is a sash?",
            answer="A sash is a long band of cloth worn over the shoulder or around the waist, often as a sign of honor.",
        )
    ],
    "pin": [
        QAItem(
            question="What is a pin used for?",
            answer="A pin is a small sharp fastener that can hold cloth together or decorate clothing.",
        )
    ],
    "bucket": [
        QAItem(
            question="What is a bucket for?",
            answer="A bucket is a container for carrying water, sand, or other things.",
        )
    ],
    "bridge": [
        QAItem(
            question="Why do people use bridges?",
            answer="People use bridges to cross over water, a road, or a gap without falling in.",
        )
    ],
    "woods": [
        QAItem(
            question="Why can woods feel spooky at dusk?",
            answer="Woods can feel spooky at dusk because the light gets dim and it is harder to see the path.",
        )
    ],
    "water": [
        QAItem(
            question="Why should you be careful with a bucket of water?",
            answer="You should be careful because water can spill and make a mess, or make the bucket hard to carry.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["prize"].tags) | set(world.facts["task"].tags)
    out: list[QAItem] = []
    for tag in ["bridge", "woods", "bucket", "sash", "pin", "water"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if bits:
            lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("zone", tid, t.zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for tg in sorted(aid.tags):
            lines.append(asp.fact("helps", aid.id, tg))
        for bn in sorted(aid.benefit.split()):
            pass
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T, P) :- zone(T, R), region(P, R).
fix(A, T, P) :- aid(A), helps(A, T), prize_at_risk(T, P).
valid(Place, T, P) :- setting(Place), prize_at_risk(T, P), fix(_, T, P).
"""


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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="village", task="cross_bridge", prize="blue_sash", hero="Mara", friend="fox friend", elder="grandmother"),
    StoryParams(place="forest", task="find_path", prize="silver_pin", hero="Niko", friend="owl friend", elder="old miller"),
    StoryParams(place="river", task="carry_water", prize="golden_bucket", hero="Lina", friend="badger friend", elder="village keeper"),
]


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
        print(f"{len(triples)} compatible combos:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
