#!/usr/bin/env python3
"""
storyworlds/worlds/out_twist_flashback_fairy_tale.py
====================================================

A small fairy-tale storyworld about a child, a windy errand, a lantern that
might go out, and a gentle twist remembered through a flashback.

Premise:
- A young hero needs to go out after dusk to reach a place in the woods.
- They treasure a lantern, but the wind can blow the flame out.

Tension:
- The parent knows the way is dark and risky.
- The hero wants to go anyway.

Flashback:
- A remembered lesson from an older helper explains how to keep the light
  safe and how to listen for the way home.

Twist:
- The "missing" thing was never lost at all; it was waiting where the
  flashback said it would be.

The prose engine is state-driven: meters track physical light, wind, and
distance; memes track fear, hope, and relief. The ASP twin mirrors the
reasonableness gate for compatible tales.
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
# World model
# ---------------------------------------------------------------------------
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wind": 0.0, "light": 0.0, "distance": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "relief": 0.0, "memory": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "princess"}
        male = {"boy", "father", "man", "prince"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    weather: str
    zone: set[str]
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.weather: str = ""
        self.facts: dict = {}
        self.flashback_used = False
        self.twist_used = False

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wind_out(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wind"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.protective and item.region == "hand" and not world.covered(actor, "hand"):
                sig = ("wind_out", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["light"] = max(0.0, item.meters["light"] - 1)
                out.append(f"The wind kissed {actor.id}'s {item.label}, and its flame went out.")
    return out


def _r_fear(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} held still, listening to the dark.")
    return out


CAUSAL_RULES = [Rule("wind_out", _r_wind_out), Rule("fear", _r_fear)]


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting(place="the cottage lane", indoors=False, affords={"lantern_walk"}),
    "orchard": Setting(place="the moon orchard", indoors=False, affords={"lantern_walk"}),
    "bridge": Setting(place="the old bridge", indoors=False, affords={"lantern_walk"}),
}

TASKS = {
    "lantern_walk": Task(
        id="lantern_walk",
        verb="go out to the moon orchard",
        gerund="walking under the stars",
        rush="run down the lane with the lantern",
        keyword="out",
        weather="windy",
        zone={"hand"},
        risk="goes out",
        tags={"night", "wind", "light"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little brass lantern with a bright wick",
        type="lantern",
        region="hand",
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a blue cloak with a silver clasp",
        type="cloak",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="glasshood",
        label="a glass hood",
        covers={"hand"},
        guards={"light"},
        prep="place a glass hood over the lantern",
        tail="went on with the lantern under its glass hood",
    ),
    Gear(
        id="lanternbag",
        label="a lantern bag",
        covers={"hand"},
        guards={"light"},
        prep="tuck the lantern into a lantern bag",
        tail="walked on with the lantern in a lantern bag",
    ),
]

HEROES = {
    "girl": ["Mira", "Ivy", "Luna", "Tessa"],
    "boy": ["Elias", "Theo", "Finn", "Noel"],
}


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize.region in TASKS[task].zone:
                    combos.append((place, task, prize_id))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(T, P) :- task(T), splashes(T, R), worn_on(P, R).
has_fix(T, P) :- prize_at_risk(T, P), gear(G), covers(G, R), worn_on(P, R), guards(G, light).
valid_story(Place, T, P, Gender) :- affords(Place, T), prize_at_risk(T, P), has_fix(T, P), wears(Gender, P).
valid(Place, T, P) :- affords(Place, T), prize_at_risk(T, P), has_fix(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("splashes", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _do_task(world: World, actor: Entity, task: Task, prize: Entity, narrate: bool = True) -> None:
    actor.meters["distance"] += 1
    actor.meters["wind"] += 1
    actor.memes["fear"] += 1
    propagate(world, narrate=narrate)
    if prize.worn_by == actor.id and prize.region in task.zone and not world.covered(actor, prize.region):
        world.say(f"The little light trembled in {actor.id}'s hands.")


def _predict(world: World, actor: Entity, task: Task, prize_id: str) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, sim.get(prize_id), narrate=False)
    prize = sim.get(prize_id)
    return prize.meters["light"] <= 0


def tell(setting: Setting, task: Task, prize_cfg: Prize,
         hero_name: str = "Mira", hero_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = task.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="lantern", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                             region=prize_cfg.region))
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a little {hero_gender} who loved the evening and the soft gold of a lantern.")
    world.say(f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {prize.label} as if it were a small star.")
    world.say(f"But one windy dusk, {hero.id} wanted to {task.verb}, and {hero.pronoun('possessive')} {parent.label} worried.")

    world.para()
    world.say(f'"If you go out now, the wind may make the {prize.label} {task.risk}," said {parent.id}.')
    if _predict(world, hero, task, prize.id):
        world.facts["predicted_out"] = True
    hero.memes["fear"] += 1
    _do_task(world, hero, task, prize, narrate=True)

    world.para()
    world.say(f"{hero.id} paused, and a little flashback came back like a bell in the dark.")
    world.say(f"Long ago, {hero.id}'s grandmother had taught {hero.pronoun('object')} a simple trick: keep a calm hand and remember the way home.")
    world.flashback_used = True
    hero.memes["memory"] += 1

    gear = GEAR[0] if task.keyword == "out" else GEAR[1]
    fix = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
    fix.worn_by = hero.id
    world.say(f'{hero.id} smiled and used {gear.prep}.')
    if prize.meters["light"] <= 0:
        prize.meters["light"] = 1
    hero.memes["hope"] += 1

    world.para()
    world.say(f"They {gear.tail}, and the lantern stayed bright.")
    if hero.meters["wind"] >= THRESHOLD:
        world.say(f"Then the twist came: the thing they thought was lost was waiting all along in the moon orchard.")
        world.twist_used = True
        world.say(f"It was not the lantern that had been missing, but the courage to step {task.keyword} and see.")
    hero.memes["relief"] += 1
    world.say(f"{hero.id} reached the orchard, the light was safe, and the night looked kind instead of fierce.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       task=task, setting=setting, gear=gear,
                       flashback=True, twist=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, task, prize = f["hero"], f["parent"], f["task"], f["prize_cfg"]
    return [
        f'Write a fairy-tale story for a young child about someone who wants to {task.verb} and keep a small light from going out.',
        f"Tell a gentle tale where {hero.id} and {parent.id} face a windy dusk, remember an old lesson, and reach {world.setting.place}.",
        f'Write a short story that uses the word "out", includes a flashback, and ends with a twist in the moonlight.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, task, prize = f["hero"], f["parent"], f["task"], f["prize_cfg"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} want to go out on the windy dusk?",
            answer=f"{hero.id} wanted to {task.verb}, because the moon orchard was calling and the night seemed full of wonder.",
        ),
        QAItem(
            question=f"Why was {parent.id} worried about {prize.label}?",
            answer=f"{parent.id} worried that the wind might make the {prize.label} {task.risk}, so the little light would not guide {hero.id} safely.",
        ),
        QAItem(
            question=f"What flashback did {hero.id} remember?",
            answer=f"{hero.id} remembered grandmother's lesson: keep a calm hand and use a clever cover so the lantern can stay bright.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that the thing they thought was lost was waiting in the moon orchard all along, and the lantern only needed care, not rescue.",
        ),
    ]
    if world.twist_used:
        qa.append(QAItem(
            question=f"How did the story end after the twist?",
            answer=f"{hero.id} reached {world.setting.place}, the lantern stayed bright, and the night felt kind instead of scary.",
        ))
    return qa


KNOWLEDGE = {
    "out": [(
        "What does it mean to go out at night?",
        "To go out at night means to leave home after the sun sets and walk into the evening air.",
    )],
    "wind": [(
        "What can wind do to a flame?",
        "Wind can make a flame flicker, bend, or go out if it is not protected.",
    )],
    "lantern": [(
        "What is a lantern for?",
        "A lantern gives light in dark places so people can see where they are going.",
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is when a story briefly remembers something that happened earlier.",
    )],
    "twist": [(
        "What is a twist in a story?",
        "A twist is a surprising turn that changes what the reader thought was true.",
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"out", "wind", "lantern", "flashback", "twist"}
    return [QAItem(question=q, answer=a) for tag in tags for q, a in KNOWLEDGE[tag]]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used} twist_used={world.twist_used}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="cottage", task="lantern_walk", prize="lantern", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="orchard", task="lantern_walk", prize="lantern", name="Elias", gender="boy", parent="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with a windy 'out' quest, flashback, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_obj.genders))
    if args.gender and args.gender not in prize_obj.genders:
        raise StoryError(f"(No story: a {prize_obj.label} isn't a typical {args.gender}'s thing here.)")
    name = args.name or rng.choice(HEROES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], PRIZES[params.prize], params.name, params.gender, params.parent)
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


def asp_facts() -> str:
    return "\n".join([os.linesep.join([])]) if False else (
        "\n".join([
            *(f"setting({pid})." for pid in SETTINGS),
            *(f"affords({pid},{task})." for pid, s in SETTINGS.items() for task in sorted(s.affords)),
            *(f"task({tid})." for tid in TASKS),
            *(f"splashes({tid},{r})." for tid, t in TASKS.items() for r in sorted(t.zone)),
            *(f"prize({pid})." for pid in PRIZES),
            *(f"worn_on({pid},{p.region})." for pid, p in PRIZES.items()),
            *(f"wears({g},{pid})." for pid, p in PRIZES.items() for g in sorted(p.genders)),
            *(f"gear({g.id})." for g in GEAR),
            *(f"covers({g.id},{r})." for g in GEAR for r in sorted(g.covers)),
            *(f"guards({g.id},light)." for g in GEAR for _ in [0]),
        ])
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, task, prize) combos ({len(stories)} with gender):\n")
        for place, task, prize in triples:
            genders = sorted(g for (pl, ta, pr, g) in stories if (pl, ta, pr) == (place, task, prize))
            print(f"  {place:9} {task:14} {prize:8} [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
