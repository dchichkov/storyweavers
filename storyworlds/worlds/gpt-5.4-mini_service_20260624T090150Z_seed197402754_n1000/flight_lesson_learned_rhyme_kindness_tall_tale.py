#!/usr/bin/env python3
"""
A small tall-tale storyworld about flight, a rhyme, kindness, and a lesson learned.

Seed tale inspiration:
- A child wants something to fly.
- A proud attempt goes wrong in a funny, larger-than-life way.
- A kind helper offers a gentler rhyme and a wiser way.
- The ending proves the lesson learned.

This script models a tiny world with typed entities, physical meters, and emotional
memes. The story is generated from simulated state, not from a frozen template.
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
# Core world model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("lift", 0.0)
        self.meters.setdefault("tumble", 0.0)
        self.meters.setdefault("knot", 0.0)
        self.meters.setdefault("shine", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("pride", 0.0)
        self.memes.setdefault("lesson", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    wind: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class FlightGear:
    id: str
    label: str
    phrase: str
    effect: str
    lift_bonus: float
    kind: str = "gear"


@dataclass
class FlightTask:
    id: str
    verb: str
    gerund: str
    trouble: str
    swirl: str
    lesson: str
    rhyme_line: str
    keyword: str = "flight"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
SETTINGS = {
    "hill": Setting(place="the windy hill", wind="big and boisterous", sky="high blue", affords={"kite", "glider"}),
    "harbor": Setting(place="the harbor dock", wind="salt-bright", sky="wide gray", affords={"kite"}),
    "meadow": Setting(place="the meadow", wind="soft and swishy", sky="golden", affords={"kite", "balloon"}),
}

ACTIONS = {
    "kite": FlightTask(
        id="kite",
        verb="launch the kite",
        gerund="launching the kite",
        trouble="the string knotted up like a stubborn snake",
        swirl="the kite spun and bonked the tall grass",
        lesson="A strong pull is not the same as a careful pull.",
        rhyme_line="A gentle tug can help things fly; a kind hand gives a kinder try.",
        keyword="flight",
    ),
    "glider": FlightTask(
        id="glider",
        verb="send the glider",
        gerund="sending the glider",
        trouble="the glider nosedived into a mud puff",
        swirl="the glider wobbled like a wobble-weed in a storm",
        lesson="Fast hands can lose what patient hands can keep.",
        rhyme_line="Slow and steady helps wings rise; kind eyes make wiser skies.",
        keyword="flight",
    ),
    "balloon": FlightTask(
        id="balloon",
        verb="let the balloon go",
        gerund="letting the balloon float",
        trouble="the ribbon slipped and the balloon drifted the wrong way",
        swirl="the balloon bobbed away like a small moon on a string",
        lesson="A little kindness can keep a big wish from popping.",
        rhyme_line="Hold with care and hold with grace; kindness helps a dream find place.",
        keyword="flight",
    ),
}

GEAR = {
    "string": FlightGear(
        id="string",
        label="a longer string",
        phrase="a longer string with a bright red tail",
        effect="steadier",
        lift_bonus=1.0,
    ),
    "patch": FlightGear(
        id="patch",
        label="a patch kit",
        phrase="a patch kit and a careful hand",
        effect="safer",
        lift_bonus=1.0,
    ),
    "ribbon": FlightGear(
        id="ribbon",
        label="a soft ribbon",
        phrase="a soft ribbon tied in a neat bow",
        effect="gentler",
        lift_bonus=1.0,
    ),
}

NAMES = ["Mabel", "Jasper", "Nina", "Toby", "Lila", "Rosie", "Milo", "Hazel"]
KINDS = ["girl", "boy"]
PARENTS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    kind: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about flight, kindness, rhyme, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _choice(rng: random.Random, seq: list[str]) -> str:
    return seq[rng.randrange(len(seq))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or _choice(rng, list(SETTINGS))
    task = args.task or _choice(rng, list(ACTIONS))
    kind = args.kind or _choice(rng, KINDS)
    name = args.name or _choice(rng, NAMES)
    parent = args.parent or _choice(rng, PARENTS)
    if task == "balloon" and setting == "harbor":
        raise StoryError("A balloon story at the harbor is too easy to blow away; choose another setting or task.")
    return StoryParams(setting=setting, task=task, name=name, kind=kind, parent=parent)


def can_fly(world: World, hero: Entity, task: FlightTask) -> bool:
    return hero.memes["kindness"] >= 1 and hero.meters["lift"] >= 1 and task.id in world.setting.affords


def reasonableness_gate(params: StoryParams) -> bool:
    if params.task not in ACTIONS:
        return False
    if params.setting not in SETTINGS:
        return False
    if params.task == "balloon" and params.setting == "harbor":
        return False
    return True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task(tkite) :- task(kite).
task(tglider) :- task(glider).
task(tballoon) :- task(balloon).

setting(shill) :- setting(hill).
setting(sharbor) :- setting(harbor).
setting(smeadow) :- setting(meadow).

affords(hill,kite). affords(hill,glider).
affords(harbor,kite).
affords(meadow,kite). affords(meadow,balloon).

compatible(S,T) :- affords(S,T), not bad(S,T).
bad(harbor,balloon).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid in ACTIONS:
        lines.append(asp.fact("task", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(s, t) for s in SETTINGS for t in ACTIONS if SETTINGS[s].affords.__contains__(t) and not (s == "harbor" and t == "balloon")}
    model = asp.one_model(asp_program("#show compatible/2."))
    cl = set(asp.atoms(model, "compatible"))
    if cl == py:
        print(f"OK: ASP matches Python ({len(py)} compatible pairs).")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(params):
        raise StoryError("Invalid story parameters for this world.")

    setting = SETTINGS[params.setting]
    task = ACTIONS[params.task]
    gear = next(iter(GEAR.values()))
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.kind))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    object_id = "object"
    if params.task == "kite":
        object_ent = world.add(Entity(id=object_id, label="kite", phrase="a striped kite"))
    elif params.task == "glider":
        object_ent = world.add(Entity(id=object_id, label="glider", phrase="a wooden glider"))
    else:
        object_ent = world.add(Entity(id=object_id, label="balloon", phrase="a red balloon"))

    world.facts.update(hero=hero, parent=parent, obj=object_ent, task=task, gear=gear)

    # Beginning
    world.say(f"{hero.id} was a little {hero.type} with a huge wish for {task.keyword}.")
    world.say(f"{hero.id} loved {task.gerund}, and the wind at {setting.place} was {setting.wind} that day.")

    # Middle: trouble and kindness
    world.para()
    hero.memes["pride"] += 1
    hero.meters["lift"] += 0.5
    world.say(f"{hero.id} tried to {task.verb}, but {task.trouble}.")
    world.say(f"The {parent.type if parent.type in PARENTS else 'parent'} saw the tumble and showed kindness instead of scolding.")

    # Kindness and rhyme
    hero.memes["kindness"] += 1
    hero.memes["worry"] += 1
    world.say(f'"{task.rhyme_line}" said {params.parent} {params.name}, and the words sounded like a merry bell in the wind.')
    world.say(f"Together they used {gear.label} so the plan could be {gear.effect}.")

    # Resolution
    world.para()
    hero.meters["lift"] += gear.lift_bonus + 0.7
    hero.memes["joy"] += 1
    hero.memes["hope"] += 1
    hero.memes["lesson"] += 1
    world.say(f"With {gear.phrase}, {hero.id} gave the {object_ent.label} another try.")
    if can_fly(world, hero, task):
        world.say(f"Up it went, higher than a barn roof, higher than a crow's last caw, until it danced in the sky.")
        world.say(f"{hero.id} laughed, and {params.parent} laughed too, because the lesson learned was brighter than the wind: {task.lesson}")
    else:
        world.say(f"It did not soar far, but it stayed steady enough to make everyone cheer.")
        world.say(f"{hero.id} learned the lesson anyway: {task.lesson}")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a tall tale for young children about {params.name} and flight.",
            f"Tell a kind story with a rhyme where a child learns a lesson about {task.keyword}.",
            f"Write a short, playful story in which kindness helps a big dream take off.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    obj: Entity = world.facts["obj"]
    task: FlightTask = world.facts["task"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {obj.label}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} first tried to {task.verb}?",
            answer=f"{task.trouble.capitalize()}. That made the first try wobble and fall short.",
        ),
        QAItem(
            question=f"What did {parent.type if parent.type in PARENTS else 'parent'} say that helped?",
            answer=f"They used a rhyme: “{task.rhyme_line}” and then showed kindness by helping with a better plan.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{task.lesson}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the ends, like a little sing-song pattern.",
        ),
        QAItem(
            question="What is flight?",
            answer="Flight is the act of moving through the air, like a bird, a kite, or a balloon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(setting="hill", task="kite", name="Mabel", kind="girl", parent="mother"),
    StoryParams(setting="meadow", task="balloon", name="Jasper", kind="boy", parent="father"),
    StoryParams(setting="hill", task="glider", name="Nina", kind="girl", parent="mother"),
]


def parse_all(args: argparse.Namespace) -> list[StoryParams]:
    out = []
    for p in CURATED:
        if args.setting and p.setting != args.setting:
            continue
        if args.task and p.task != args.task:
            continue
        out.append(p)
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(asp.atoms(model, "compatible")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = parse_all(args)
        if not params_list:
            raise StoryError("No curated stories match the selected filters.")
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
