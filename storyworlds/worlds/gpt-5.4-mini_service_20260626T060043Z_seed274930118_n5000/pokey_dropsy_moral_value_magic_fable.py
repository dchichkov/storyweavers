#!/usr/bin/env python3
"""
storyworlds/worlds/pokey_dropsy_moral_value_magic_fable.py
===========================================================

A small fable-style storyworld about Pokey and Dropsy, where Magic tempts
swift choices but Moral Value rewards patience, care, and honesty.

The premise is a child-friendly fable domain: two small friends must carry a
seed-lantern through a garden path before dusk. One is naturally pokey and
careful; the other is dropsy and eager to rush. A magic charm can speed the
trip, but it also stirs up trouble if used carelessly. The story turns when the
friends face a choice between quick magic and a slower, kinder path, and it
ends with a clear change in state: the lantern arrives safely, trust grows, and
the lesson is proved by what happened.

The world keeps track of both physical meters and emotional memes. Prose is
generated from simulated state, not from a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox"}
        male = {"boy", "father", "dad", "man", "hare"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    calm: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    harm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    label_phrase: str
    speed_boost: float
    calm_boost: float
    requires_kindness: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    path_state: str = "clear"
    weather: str = ""

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_state = self.path_state
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
    charm: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", calm=True, affords={"cross_bridge", "carry_lantern"}),
    "grove": Setting(place="the grove", calm=True, affords={"cross_bridge", "carry_lantern"}),
    "riverbank": Setting(place="the riverbank", calm=False, affords={"cross_bridge", "carry_lantern"}),
}

TASKS = {
    "cross_bridge": Task(
        id="cross_bridge",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        rush="dash over the bridge",
        danger="the bridge can wobble when feet hurry",
        harm="slip into the mud",
        tags={"bridge", "mud"},
    ),
    "carry_lantern": Task(
        id="carry_lantern",
        verb="carry the seed-lantern home",
        gerund="carrying the seed-lantern",
        rush="run with the lantern",
        danger="the lantern flame can sputter in a tumble",
        harm="let the lantern go out",
        tags={"lantern", "light"},
    ),
}

CHARMS = {
    "windbell": Charm(
        id="windbell",
        label="windbell charm",
        label_phrase="a tiny windbell charm",
        speed_boost=1.0,
        calm_boost=0.0,
        requires_kindness=False,
        tags={"magic", "speed"},
    ),
    "lanternglow": Charm(
        id="lanternglow",
        label="lantern-glow charm",
        label_phrase="a warm lantern-glow charm",
        speed_boost=0.2,
        calm_boost=1.0,
        requires_kindness=True,
        tags={"magic", "light", "kindness"},
    ),
}

NAMES = ["Pokey", "Dropsy"]
KINDS = ["hedgehog", "mouse", "fox", "hare"]
TRAITS = ["pokey", "dropsy", "gentle", "curious", "brave"]


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    charm = CHARMS[params.charm]
    world = World(setting=setting)
    world.weather = "misty" if params.place == "riverbank" else "soft"

    pokey = world.add(Entity(
        id="Pokey",
        kind="character",
        type="hedgehog",
        label="Pokey",
        meters={"pace": 0.1, "care": 1.0, "tired": 0.0},
        memes={"patience": 1.0, "pride": 0.2, "trust": 0.6, "joy": 0.3},
    ))
    dropsy = world.add(Entity(
        id="Dropsy",
        kind="character",
        type="hare",
        label="Dropsy",
        meters={"pace": 0.9, "care": 0.2, "tired": 0.0},
        memes={"patience": 0.2, "pride": 0.7, "trust": 0.4, "joy": 0.5},
    ))
    lantern = world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="seed-lantern",
        phrase="a small seed-lantern with a gold wick",
        owner="Pokey",
        caretaker="Pokey",
        meters={"glow": 1.0, "soot": 0.0, "tilt": 0.0},
    ))
    charm_ent = world.add(Entity(
        id=charm.id,
        kind="thing",
        type="charm",
        label=charm.label,
        phrase=charm.label_phrase,
        owner="Dropsy",
        caretaker="Dropsy",
        protective=not charm.requires_kindness,
        meters={"spark": 1.0},
    ))
    world.facts.update(task=task, charm=charm, pokey=pokey, dropsy=dropsy, lantern=lantern, charm_ent=charm_ent)
    return world


def predict(world: World, use_charm: bool) -> dict:
    sim = world.copy()
    act = sim.facts["task"]
    if use_charm:
        sim.get("Dropsy").meters["pace"] += sim.facts["charm"].speed_boost
        sim.get("Dropsy").memes["pride"] += 0.3
    perform_task(sim, use_charm=use_charm, narrate=False)
    lantern = sim.get("Lantern")
    return {
        "soot": lantern.meters["soot"] >= THRESHOLD,
        "tilt": lantern.meters["tilt"] >= THRESHOLD,
        "trust": sum(e.memes["trust"] for e in sim.characters()),
    }


def perform_task(world: World, use_charm: bool, narrate: bool = True) -> None:
    task: Task = world.facts["task"]
    pokey = world.get("Pokey")
    dropsy = world.get("Dropsy")
    lantern = world.get("Lantern")
    charm = world.facts["charm"]

    world.path_state = "winding"
    if use_charm:
        dropsy.meters["pace"] += charm.speed_boost
        dropsy.memes["pride"] += 0.4
        if narrate:
            world.say(f"Dropsy held up {charm.label_phrase}, and the little spark made {dropsy.id} feel fast.")
    else:
        dropsy.memes["patience"] += 0.3

    # task effect: rushing risks the lantern
    if dropsy.meters["pace"] > pokey.meters["pace"] + 0.3:
        lantern.meters["tilt"] += 1.0
        lantern.meters["soot"] += 1.0 if use_charm else 0.0
        pokey.memes["worry"] = pokey.memes.get("worry", 0.0) + 1.0

    if world.setting.place == "riverbank":
        lantern.meters["tilt"] += 0.2

    if narrate:
        world.say(f"They went to {world.setting.place} to {task.verb}.")
        world.say(f"But {task.danger}, and Pokey could feel the trouble before it happened.")

    if lantern.meters["tilt"] >= THRESHOLD:
        pokey.memes["worry"] += 0.5
        dropsy.memes["shame"] = dropsy.memes.get("shame", 0.0) + 0.4


def choose_kindness(world: World, use_charm: bool) -> bool:
    charm: Charm = world.facts["charm"]
    if not use_charm:
        return True
    if charm.requires_kindness:
        return True
    return False


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    task: Task = world.facts["task"]
    charm: Charm = world.facts["charm"]
    pokey = world.get("Pokey")
    dropsy = world.get("Dropsy")
    lantern = world.get("Lantern")

    world.say(
        f"Pokey was a little hedgehog with a slow step and a steady heart, "
        f"and Dropsy was a quick hare who loved bright tricks."
    )
    world.say(
        f"One evening, they needed to {task.verb} with the {lantern.label} before dusk."
    )
    world.para()
    world.say(
        f"Dropsy showed {charm.label_phrase} and said it could make the trip feel easy."
    )
    world.say(
        f"Pokey liked magic, but {task.danger}; so {pokey.pronoun('subject')} asked for a safer plan first."
    )

    use_charm = params.charm == "windbell"
    world.say(
        f"Dropsy wanted to use the charm right away, while Pokey wanted to move carefully and keep everyone kind."
    )
    if use_charm:
        world.say("For a moment, the charm made Dropsy rush ahead.")
    else:
        world.say("The warm charm made Dropsy breathe out and listen.")

    world.para()
    perform_task(world, use_charm=use_charm, narrate=True)

    # Resolution
    if lantern.meters["tilt"] >= THRESHOLD:
        if use_charm:
            world.say(
                f"Then Pokey asked Dropsy to slow down, and Dropsy finally put the charm away."
            )
            dropsy.memes["pride"] -= 0.2
            dropsy.memes["trust"] += 0.4
            pokey.memes["trust"] += 0.4
            lantern.meters["tilt"] = 0.0
            lantern.meters["soot"] = 0.0
            world.say(
                f"Together they held the {lantern.label} level, and the little light stopped trembling."
            )
        else:
            world.say(
                f"Because they chose patience, the {lantern.label} stayed bright and steady all the way home."
            )
    else:
        world.say(
            f"The road stayed calm, and the {lantern.label} shone like a tiny morning star."
        )

    pokey.memes["joy"] += 0.5
    dropsy.memes["joy"] += 0.6
    pokey.memes["trust"] += 0.3
    dropsy.memes["trust"] += 0.3

    world.para()
    if use_charm:
        world.say(
            f"In the end, Dropsy learned that magic is best when it helps a kind choice, not a hurried one."
        )
    else:
        world.say(
            f"In the end, Dropsy learned that the gentlest magic is often the patience to listen."
        )
    world.say(
        f"Pokey and Dropsy went home with the {lantern.label} safe, and the garden looked kinder for it."
    )

    world.facts.update(params=params, used_charm=use_charm, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    task: Task = world.facts["task"]
    charm: Charm = world.facts["charm"]
    return [
        f"Write a fable for young children about Pokey and Dropsy who must {task.verb} and learn a moral lesson.",
        f"Tell a short story where a magic {charm.label} tempts Dropsy, but Pokey prefers patience and kindness.",
        f"Make a gentle fable about a seed-lantern, a risky shortcut, and the moral value of slowing down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]
    charm: Charm = world.facts["charm"]
    used_charm = world.facts.get("used_charm", False)
    qa = [
        QAItem(
            question="Who are the two friends in the story?",
            answer="The story is about Pokey the hedgehog and Dropsy the hare. They are small friends trying to help carry the seed-lantern safely.",
        ),
        QAItem(
            question=f"What did Pokey and Dropsy need to do before dusk?",
            answer=f"They needed to {task.verb} with the seed-lantern before dusk so its light could get home safely.",
        ),
        QAItem(
            question="What made the story magical?",
            answer=f"A {charm.label} added magic to the choice. It could make the trip feel faster, but it also made hurry more tempting.",
        ),
    ]
    if used_charm:
        qa.append(QAItem(
            question="Why did the first magic choice cause trouble?",
            answer="The charm made Dropsy rush ahead, and rushing made the lantern wobble. Pokey saw the danger and asked everyone to slow down.",
        ))
    else:
        qa.append(QAItem(
            question="Why did the friends stay safe?",
            answer="They chose patience instead of rushing, so the lantern stayed steady and the trip remained calm.",
        ))
    qa.append(QAItem(
        question="What moral value does the fable teach?",
        answer="It teaches that patience and kindness are better than rushing, even when magic promises a quicker way.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of choosing how to act, like being honest, kind, patient, or fair.",
        ),
        QAItem(
            question="What is magic in a fable?",
            answer="Magic in a fable is a special power or charm that can change what happens, often to teach a lesson.",
        ),
        QAItem(
            question="Why should a lantern be carried carefully?",
            answer="A lantern should be carried carefully so the flame stays steady and does not go out or fall over.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    out.append(f"  path_state={world.path_state}")
    return "\n".join(out)


ASP_RULES = r"""
% A task is risky if the character's pace is greater than careful pace.
risky(T) :- task(T), actor(A), pace(A,P1), careful(C), P1 > C.

% The charm is helpful if it supports kindness and reduces rush.
good_charm(C) :- charm(C), kindness(C).
bad_charm(C) :- charm(C), speed(C), not kindness(C).

% A valid fable should have either a risky temptation that is corrected,
% or a calm choice that already favors the moral value.
valid_story(P, T, C) :- setting(P), task(T), charm(C).

resolution(P, T, C) :- valid_story(P, T, C).
"""

SETTINGS_REG = SETTINGS
TASKS_REG = TASKS
CHARMS_REG = CHARMS


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS_REG.items():
        lines.append(asp.fact("setting", pid))
        if s.calm:
            lines.append(asp.fact("calm", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS_REG:
        lines.append(asp.fact("task", tid))
    for cid, c in CHARMS_REG.items():
        lines.append(asp.fact("charm", cid))
        if c.requires_kindness:
            lines.append(asp.fact("kindness", cid))
        if c.speed_boost:
            lines.append(asp.fact("speed", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.place, t.id, c.id) for p in SETTINGS_REG.values() for t in TASKS_REG.values() for c in CHARMS_REG.values()}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches python registry product ({len(py)} triples).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: Pokey, Dropsy, Magic, and a moral lesson.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    task = args.task or rng.choice(sorted(SETTINGS[place].affords))
    charm = args.charm or rng.choice(sorted(CHARMS))
    if args.task and task not in SETTINGS[place].affords:
        raise StoryError("That place cannot host that task.")
    return StoryParams(place=place, task=task, charm=charm)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        for place, task, charm in triples:
            print(f"{place:10} {task:16} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(SETTINGS):
            for task in sorted(SETTINGS[place].affords):
                for charm in sorted(CHARMS):
                    samples.append(generate(StoryParams(place=place, task=task, charm=charm)))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
