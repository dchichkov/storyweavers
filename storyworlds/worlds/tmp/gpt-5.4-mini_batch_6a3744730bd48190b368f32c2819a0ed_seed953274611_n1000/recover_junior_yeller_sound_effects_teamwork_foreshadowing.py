#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/recover_junior_yeller_sound_effects_teamwork_foreshadowing.py
================================================================================================

A standalone story world for a tiny pirate tale about a junior crew, a loud
yeller, a lost item to recover, and a calm teamwork fix that was foreshadowed
earlier by small sound cues.

The story shape is classical:
- setup: the junior crew prepares for a pretend pirate trip
- tension: a yeller shouts, the signal gets mixed up, and something goes missing
- turn: earlier clues matter, the crew works together, and they recover the item
- ending: the crew sails on, now better at listening and teaming up

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate plus inline ASP twin
- three QA sets grounded in the simulated world
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    id: str
    place: str
    sounds: list[str] = field(default_factory=list)
    hidden: set[str] = field(default_factory=set)
    wind: str = "sea-breeze"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class CrewTask:
    id: str
    label: str
    search_phrase: str
    recover_phrase: str
    sound: str
    teamwork_need: int
    foreshadow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    shout: str
    loudness: int
    helpful: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    task: str
    signal: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.ship: Optional[Ship] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.ship = copy.deepcopy(self.ship)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    ship = world.ship
    if ship is None:
        return out
    if "tap" in ship.hidden and ("foreshadow", "tap") not in world.fired:
        world.fired.add(("foreshadow", "tap"))
        ship.meters["mystery"] += 1
        out.append("__foreshadow__")
    return out


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    ship = world.ship
    if ship is None:
        return out
    if ship.meters["noise"] < THRESHOLD:
        return out
    if ("noise", ship.id) in world.fired:
        return out
    world.fired.add(("noise", ship.id))
    ship.memes["confusion"] += 1
    for ent in world.entities.values():
        if ent.role in {"junior", "watcher"}:
            ent.memes["startle"] += 1
    out.append("__noise__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.role in {"junior", "helper", "watcher"}]
    if not crew:
        return out
    if all(e.memes["helping"] >= THRESHOLD for e in crew if e.role != "watcher") and world.ship:
        if ("teamwork", world.ship.id) not in world.fired:
            world.fired.add(("teamwork", world.ship.id))
            world.ship.meters["search"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("foreshadow", _r_foreshadow), Rule("noise", _r_noise), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_task(task: CrewTask) -> bool:
    return task.teamwork_need >= 2 and "recover" in task.tags


def valid_combo(task: CrewTask, signal: Signal) -> bool:
    return task.label and signal.helpful and signal.loudness >= 2


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for tid, task in TASKS.items():
        for sid, sig in SIGNALS.items():
            if valid_combo(task, sig):
                out.append((tid, sid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale about recovering a lost item with teamwork and clues.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--signal", choices=SIGNALS)
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
    combos = [(t, s) for t, s in valid_combos()
              if (args.task is None or t == args.task) and (args.signal is None or s == args.signal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    task, signal = rng.choice(sorted(combos))
    return StoryParams(task=task, signal=signal)


def _do_signal(world: World, task: CrewTask, sig: Signal) -> None:
    ship = world.ship
    assert ship is not None
    ship.sounds.append(sig.shout)
    ship.meters["noise"] += sig.loudness
    ship.hidden.discard(task.id)
    ship.hidden.add("missing")
    propagate(world, narrate=False)


def _search(world: World, jun: Entity, helper: Entity, task: CrewTask) -> None:
    assert world.ship is not None
    jun.memes["helping"] += 1
    helper.memes["helping"] += 1
    world.ship.meters["search"] += 1
    world.say(
        f"{jun.id} and {helper.id} leaned in together. "
        f"They listened for the little {task.foreshadow} sound again."
    )
    world.say(
        f'"There!" said {helper.id}. "We heard it before, so the clue was real."'
    )


def tell(task: CrewTask, signal: Signal) -> World:
    world = World()
    ship = Ship(id="ship", place="a little pirate cove")
    ship.hidden = {"map", "tap"}
    ship.sounds.append(task.foreshadow)
    world.ship = ship

    junior = world.add(Entity(id="Junior", kind="character", type="boy", role="junior"))
    helper = world.add(Entity(id="Mate", kind="character", type="girl", role="helper"))
    yeller = world.add(Entity(id="Yeller", kind="character", type="boy", role="watcher"))
    captain = world.add(Entity(id="Cap", kind="character", type="man", role="captain", label="the captain"))

    junior.memes["curiosity"] += 1
    helper.memes["care"] += 1
    yeller.memes["boast"] += 1

    world.say(
        f"At the little pirate cove, Junior and Mate turned a crate into a boat, "
        f"and the mast gave a tiny {task.foreshadow} sound when the wind nudged it."
    )
    world.say(
        f"Junior heard it and grinned. " f'"That sound means something is waiting to be found," {junior.id} said.'
    )
    world.say(
        f"Yeller waved both arms. "{signal.shout}""""
    )
    world.say(
        f"The loud shout bounced over the deck. Mate blinked, and the small clue got mixed up in the noise."
    )

    world.para()
    _do_signal(world, task, signal)
    world.say(
        f"The crew looked around. The {task.label} was gone from its hiding place, and the ship felt too quiet after all that shouting."
    )
    world.say(
        f"Junior remembered the earlier tap-tap sound from the mast. " 
        f"It had been a foreshadowing clue, not just boat-noise."
    )

    world.para()
    _search(world, junior, helper, task)
    world.say(
        f"Together they checked the rope coil, the overturned bucket, and the little chest. At last they found the {task.label} tucked where the wind had pushed it."
    )
    world.say(
        f"Junior recovered the {task.label} with a cheer, and Mate gave a quick nod as if to say teamwork had done the trick."
    )

    world.para()
    captain.memes["pride"] += 1
    junior.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The captain smiled. " f'"Next time, listen for the clues first and save the yells for when you need help," {captain.id} said.'
    )
    world.say(
        f"So the little pirates sailed on, with the {task.label} safely recovered, the clue remembered, and the deck a little kinder and calmer."
    )

    world.facts.update(task=task, signal=signal, junior=junior, helper=helper, yeller=yeller, captain=captain, ship=ship, recovered=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: CrewTask = f["task"]
    sig: Signal = f["signal"]
    return [
        f'Write a pirate story for a young child about a junior crew that must recover a {task.label}, with a loud yeller causing trouble.',
        f'Tell a small sea adventure where "{sig.shout}" is shouted too loudly, but teamwork helps recover the lost {task.label}.',
        f'Write a story that uses the words recover, junior, and yeller, and includes a foreshadowing sound before the rescue.'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: CrewTask = f["task"]
    sig: Signal = f["signal"]
    return [
        QAItem(
            question="What was the crew trying to recover?",
            answer=f"They were trying to recover the {task.label}. The little item had been moved out of sight, so the crew had to search carefully."
        ),
        QAItem(
            question="Why did the yeller cause a problem?",
            answer=f"The yeller shouted \"{sig.shout}\", and the loud noise mixed up the clues. That made it harder to notice the important little sound they had heard earlier."
        ),
        QAItem(
            question="How did the crew fix the problem?",
            answer="They worked together, listened for the foreshadowed sound again, and searched the ship as a team. Because they shared the job, they found the missing thing and brought it back."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: CrewTask = f["task"]
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do one job. When everyone shares the work, hard things can become easier."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early on about something important that will happen later. It helps readers notice that the clue mattered all along."
        ),
        QAItem(
            question="Why can loud shouting make a search harder?",
            answer="Loud shouting can cover up quiet clues and make people look in the wrong place. It can also scramble their attention, so careful listening becomes harder."
        ),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.ship is not None:
        lines.append(f"  ship     (thing  ) sounds={world.ship.sounds} hidden={sorted(world.ship.hidden)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


TASKS = {
    "map": CrewTask(
        id="map",
        label="paper map",
        search_phrase="look for the paper map",
        recover_phrase="recover the paper map",
        sound="tap-tap",
        teamwork_need=2,
        foreshadow="tap-tap",
        tags={"recover", "teamwork", "foreshadowing"},
    ),
    "key": CrewTask(
        id="key",
        label="brass key",
        search_phrase="look for the brass key",
        recover_phrase="recover the brass key",
        sound="clink",
        teamwork_need=2,
        foreshadow="clink",
        tags={"recover", "teamwork", "foreshadowing"},
    ),
    "shell": CrewTask(
        id="shell",
        label="star shell",
        search_phrase="look for the star shell",
        recover_phrase="recover the star shell",
        sound="shh-shh",
        teamwork_need=2,
        foreshadow="shh-shh",
        tags={"recover", "teamwork", "foreshadowing"},
    ),
}

SIGNALS = {
    "holler": Signal(id="holler", label="holler", shout="Hey, look over here!", loudness=3, tags={"sound"}),
    "yell": Signal(id="yell", label="yell", shout="I found it first!", loudness=4, tags={"sound"}),
    "call": Signal(id="call", label="call", shout="Come quick!", loudness=2, tags={"sound"}),
}

CURATED = [
    StoryParams(task="map", signal="call"),
    StoryParams(task="key", signal="holler"),
    StoryParams(task="shell", signal="yell"),
]


ASP_RULES = r"""
task(T) :- task_fact(T).
signal(S) :- signal_fact(S).
valid(T,S) :- task(T), signal(S), helpful(S), teamwork_need(T,N), N >= 2.
foreshadowed(T) :- task_fact(T), has_clue(T).
recovered(T) :- valid(T,S), task_fact(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_fact", tid))
        lines.append(asp.fact("teamwork_need", tid, t.teamwork_need))
        lines.append(asp.fact("has_clue", tid))
    for sid, s in SIGNALS.items():
        lines.append(asp.fact("signal_fact", sid))
        if s.helpful:
            lines.append(asp.fact("helpful", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(task=None, signal=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS or params.signal not in SIGNALS:
        raise StoryError("Invalid task or signal.")
    task = TASKS[params.task]
    signal = SIGNALS[params.signal]
    if not valid_combo(task, signal):
        raise StoryError("(No valid combination matches the given options.)")
    world = tell(task, signal)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.task} with {p.signal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
