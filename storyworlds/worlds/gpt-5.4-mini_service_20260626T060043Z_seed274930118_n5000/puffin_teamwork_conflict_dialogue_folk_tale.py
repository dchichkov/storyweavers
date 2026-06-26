#!/usr/bin/env python3
"""
puffin_teamwork_conflict_dialogue_folk_tale.py
=============================================

A small folk-tale storyworld about puffins who must work together to solve a
conflict on a windy cliff.

Premise:
- A puffin pair and a helper face a problem on the nesting ledge.
- One puffin wants a shiny prize or a shortcut.
- The other worries because it could endanger the nest.
- They argue, talk it through, and choose a teamwork-based fix.

The world is intentionally compact:
- physical meters track nest safety, fish supply, and wind trouble
- emotional memes track worry, pride, conflict, and trust
- dialogue is used to carry the turning point
- the ending image proves what changed in the world
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the rocky cliff"
    feature: str = "a narrow nesting ledge"
    affords: set[str] = field(default_factory=lambda: {"share_fish", "carry_weed", "gather_stones"})


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    benefit: str
    strain: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    role: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cliff": Setting(place="the rocky cliff", feature="a narrow nesting ledge"),
    "harbor": Setting(place="the harbor shore", feature="a line of wet stones"),
    "islet": Setting(place="the little sea islet", feature="a mossy hollow"),
}

TASKS = {
    "share_fish": Task(
        id="share_fish",
        verb="share the fish",
        gerund="sharing fish",
        risk="someone may snatch the meal",
        benefit="everyone eats",
        strain="there may not be enough for all",
        requires={"fish"},
    ),
    "carry_weed": Task(
        id="carry_weed",
        verb="carry seaweed to the nest",
        gerund="carrying seaweed",
        risk="the wind may blow the bundle away",
        benefit="the nest grows warmer",
        strain="the path is long and slippery",
        requires={"weed"},
    ),
    "gather_stones": Task(
        id="gather stones",
        verb="gather smooth stones",
        gerund="gathering stones",
        risk="the tide may wash the stones away",
        benefit="the nest holds together",
        strain="the stones are heavy in the beak",
        requires={"stones"},
    ),
}

PRIZES = {
    "shiny_shell": Prize(
        label="shiny shell",
        phrase="a bright shell",
        type="shell",
        value="shiny",
    ),
    "good_fish": Prize(
        label="fish",
        phrase="a silver fish",
        type="fish",
        value="fresh",
    ),
    "soft_weed": Prize(
        label="seaweed",
        phrase="a soft bundle of seaweed",
        type="weed",
        value="soft",
    ),
}

AIDS = {
    "carry_together": Aid(
        id="carry_together",
        label="a shared beak-line",
        prep="took it one step at a time together",
        role="helped them share the load",
        helps={"carry_weed", "gather_stones"},
    ),
    "divide_fish": Aid(
        id="divide_fish",
        label="a fair little pile",
        prep="split the fish into fair shares",
        role="kept the peace",
        helps={"share_fish"},
    ),
    "nesting_rope": Aid(
        id="nesting_rope",
        label="a loop of kelp rope",
        prep="tied the bundle to a kelp rope",
        role="kept the wind from stealing it",
        helps={"carry_weed"},
    ),
}

NAMES = ["Pip", "Mara", "Tavi", "Nell", "Rook", "Wren", "Ivo", "Pella"]
TRAITS = ["brave", "bright", "stubborn", "gentle", "quick", "proud"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Folk-tale world logic
# ---------------------------------------------------------------------------

def task_at_risk(task: Task, prize: Prize) -> bool:
    if task.id == "share_fish":
        return prize.type == "fish"
    if task.id == "carry_weed":
        return prize.type == "weed"
    if task.id == "gather stones":
        return prize.type == "stones"
    return False


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    if task.id == "share_fish":
        return AIDS["divide_fish"]
    if task.id == "carry_weed":
        return AIDS["nesting_rope"]
    if task.id == "gather stones":
        return AIDS["carry_together"]
    return None


@dataclass
class Rule:
    name: str
    apply: object


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("pride", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        out.append("__conflict__")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("trust", 0.0) < THRESHOLD:
            continue
        sig = ("trust", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = max(0.0, actor.memes.get("conflict", 0.0) - 1)
        out.append(f"{actor.id} felt calmer once the two puffins listened to each other.")
    return out


RULES = [Rule("conflict", _r_conflict), Rule("trust", _r_trust)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0.0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
    if task.id == "carry_weed":
        actor.meters["wind_tired"] = actor.meters.get("wind_tired", 0.0) + 1
    if task.id == "share_fish":
        actor.meters["fish_shared"] = actor.meters.get("fish_shared", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, task: Task) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
        "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
        "caretaker": v.caretaker, "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    return {
        "conflict": sim.get(actor.id).memes.get("conflict", 0.0) >= THRESHOLD,
        "work": sim.get(actor.id).meters.get("wind_tired", 0.0),
    }


def intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"On the edge of {world.setting.place}, {hero.id} the {hero.traits[0]} puffin "
        f"lived near {friend.id}, and both knew the sea by heart."
    )


def desire(world: World, hero: Entity, task: Task, prize: Prize) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {task.verb}, for {prize.phrase} gleamed like a moon-chip in the surf."
    )


def warning(world: World, friend: Entity, hero: Entity, task: Task, prize: Prize) -> None:
    pred = predict(world, hero, task)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    if task.id == "share_fish":
        reason = "there might not be enough for the whole nest"
    elif task.id == "carry_weed":
        reason = "the wind could scatter the bundle into the sea"
    else:
        reason = "the tide could steal the stones before they reached the hollow"
    world.say(
        f'"Hold," said {friend.id}. "If we try to {task.verb}, {reason}."'
    )
    world.facts["predicted_conflict"] = pred["conflict"]
    world.facts["reason"] = reason


def argue(world: World, hero: Entity, task: Task) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} bristled and said, \"But I can do it myself!\" "
        f"{hero.id} flapped once in the salty wind."
    )


def listen(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {hero.id} and {friend.id} sat close and talked it through, "
        f"beak to beak, until the words grew softer."
    )
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    propagate(world, narrate=True)


def compromise(world: World, hero: Entity, friend: Entity, task: Task) -> Optional[Aid]:
    aid = select_aid(task, world.facts["prize"])
    if aid is None:
        raise StoryError("No reasonable teamwork fix exists for this story.")
    if task.id == "carry_weed":
        world.say(
            f"{friend.id} found {aid.label}, and together they {aid.prep}. "
            f"It {aid.role}."
        )
    elif task.id == "share_fish":
        world.say(
            f"{hero.id} nodded, and {friend.id} found {aid.label}. "
            f"Together they {aid.prep}, and it {aid.role}."
        )
    else:
        world.say(
            f"{hero.id} and {friend.id} chose {aid.label}; they {aid.prep}, and it {aid.role}."
        )
    return aid


def resolve(world: World, hero: Entity, friend: Entity, task: Task, prize: Prize, aid: Aid) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"So the two puffins worked as one. {hero.id} and {friend.id} {task.gerund} together, "
        f"and the {prize.label} stayed safe."
    )
    world.say(
        f"By dusk, the nest was steadier, the wind seemed less fierce, and the two friends "
        f"stood side by side on the cliff, proud and quiet."
    )


def tell(setting: Setting, task: Task, prize: Prize, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type="puffin", traits=[trait, "small"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="puffin", traits=["wise", "steady"]))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["task"] = task
    world.facts["prize"] = prize
    world.facts["setting"] = setting

    intro(world, hero, friend)
    world.para()
    desire(world, hero, task, prize)
    warning(world, friend, hero, task, prize)
    argue(world, hero, task)
    listen(world, hero, friend, task)
    world.para()
    aid = compromise(world, hero, friend, task)
    if aid is None:
        raise StoryError("No compatible aid for the selected task.")
    resolve(world, hero, friend, task, prize, aid)
    world.facts["aid"] = aid
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    task = f["task"]
    prize = f["prize"]
    return [
        f'Write a short folk tale about a puffin named {hero.id} and a friend who disagree about how to {task.verb}.',
        f"Tell a gentle story where {hero.id} wants to {task.verb} for {prize.phrase}, but {friend.id} worries and they talk it through.",
        f"Write a child-friendly tale with puffins on a cliff, a conflict, dialogue, and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    task = f["task"]
    prize = f["prize"]
    setting = f["setting"]
    aid = f["aid"]

    return [
        QAItem(
            question=f"Who wanted to {task.verb} in the story?",
            answer=f"{hero.id} wanted to {task.verb} on {setting.place}.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the plan?",
            answer=f"{friend.id} worried because {f['reason']}.",
        ),
        QAItem(
            question=f"How did the puffins solve the problem?",
            answer=f"They chose teamwork, used {aid.label}, and worked together so the {prize.label} stayed safe.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The puffins stopped arguing, trusted each other, and finished the job together beside a safer nest.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "puffin": [
        QAItem(
            question="What is a puffin?",
            answer="A puffin is a small seabird with a colorful beak that lives near cold oceans.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals work together and help one another finish a job.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or disagreement that makes the characters upset for a little while.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the words characters say to each other in a story.",
        )
    ],
    "folk_tale": [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that often has animals, a lesson, and a simple problem to solve.",
        )
    ],
    "sea": [
        QAItem(
            question="What is the sea?",
            answer="The sea is a very large body of salty water that covers much of the Earth.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["puffin"] + WORLD_KNOWLEDGE["teamwork"] + WORLD_KNOWLEDGE["conflict"] + WORLD_KNOWLEDGE["dialogue"] + WORLD_KNOWLEDGE["folk_tale"] + WORLD_KNOWLEDGE["sea"]


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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A task is risky when the prize matches the vulnerable thing in the task.
task_at_risk(T, P) :- task(T), prize(P), task_requires(T, X), prize_type(P, X).

% An aid is compatible if it helps the task and the task is risky.
good_aid(A, T, P) :- aid(A), task_at_risk(T, P), aid_helps(A, T).

% A story is valid if the task is risky and some aid works.
valid_story(S, T, P, A) :- setting(S), task(T), prize(P), good_aid(A, T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for req in sorted(t.requires):
            lines.append(asp.fact("task_requires", tid, req))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_type", pid, p.type))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(a.helps):
            lines.append(asp.fact("aid_helps", aid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(s, t, p) for (s, t, p, a) in asp_valid_stories()]


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for task_id, task in TASKS.items():
            for prize_id, prize in PRIZES.items():
                if task_at_risk(task, prize):
                    if select_aid(task, prize) is not None:
                        combos.append((place, task_id, prize_id))
    return combos


def explain_rejection(task: Task, prize: Prize) -> str:
    return (
        f"(No story: {task.verb} and {prize.phrase} do not make a good conflict here, "
        f"because there is no teamwork fix that fits both the task and the prize.)"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: puffins, conflict, dialogue, and teamwork in a folk tale."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.task and args.prize:
        if not task_at_risk(TASKS[args.task], PRIZES[args.prize]):
            raise StoryError(explain_rejection(TASKS[args.task], PRIZES[args.prize]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task_id, prize_id = rng.choice(sorted(combos))
    hero = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, prize=prize_id, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        PRIZES[params.prize],
        params.hero,
        params.friend,
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    StoryParams(place="cliff", task="carry_weed", prize="soft_weed", hero="Pip", friend="Mara", trait="stubborn"),
    StoryParams(place="harbor", task="share_fish", prize="good_fish", hero="Wren", friend="Tavi", trait="brave"),
    StoryParams(place="islet", task="gather_stones", prize="shiny_shell", hero="Nell", friend="Rook", trait="proud"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.hero}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
