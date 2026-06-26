#!/usr/bin/env python3
"""
storyworlds/worlds/cod_musician_foreshadowing_teamwork_bad_ending_space.py
===========================================================================

A standalone story world about a cod musician aboard a tiny starship.

Seed tale premise:
- A cod who loves music travels through space with a small crew.
- Strange little signs foreshadow trouble before a performance.
- The crew works together to solve what they can.
- The ending is a bad ending: the concert does not happen as hoped, but the
  shared effort still gives the characters a meaningful final image.

This world keeps a space-adventure feel: narrow corridors, glowing panels,
floating tools, starfields, radio chatter, and a last-minute repair attempt.

The story is driven by a small state machine:
- foreshadowing grows when the ship reports odd signs
- teamwork increases as the crew coordinate repairs and prep
- bad ending happens if the ship drifts too far or the venue is lost
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

FORESHADOW_THRESHOLD = 1.0
TEAMWORK_THRESHOLD = 2.0
BAD_ENDING_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cod"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"captain", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"pilot", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little starship"
    venue: str = "the orbiting dock"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    warning: str
    bad_sign: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.history[-1].append(text)

    def para(self) -> None:
        if self.history[-1]:
            self.history.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.history if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for task in world.facts.get("task_objs", []):
        if task.meters["omen"] >= FORESHADOW_THRESHOLD:
            sig = ("foreshadow", task.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(task.bad_sign)
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.characters()
    if not crew:
        return out
    total_help = sum(e.memes.get("help", 0.0) for e in crew)
    if total_help < TEAMWORK_THRESHOLD:
        return out
    sig = ("teamwork", int(total_help))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in crew:
        e.memes["trust"] = e.memes.get("trust", 0.0) + 0.5
    out.append("The crew moved like one careful team.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    cod = world.get("cod")
    task = world.facts["task"]
    if cod.meters.get("drift", 0.0) < BAD_ENDING_THRESHOLD:
        return out
    sig = ("bad_end", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The chance for the concert slipped farther away.")
    return out


RULES = [
    _r_foreshadow,
    _r_teamwork,
    _r_bad_ending,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            msgs = rule(world)
            if msgs:
                changed = True
                out.extend(msgs)
    if narrate:
        for msg in out:
            world.say(msg)
    return out


def foreshadow(world: World, cod: Entity, task: Task) -> None:
    cod.meters["notice"] = cod.meters.get("notice", 0.0) + 1
    task.meters["omen"] = task.meters.get("omen", 0.0) + 1
    world.say(
        f"{cod.id} noticed a thin red blink on the control panel, and {cod.pronoun('possessive')} fins went still."
    )
    world.say(
        f"Something in the ship felt like a whisper before a storm."
    )


def do_task(world: World, actor: Entity, task: Task) -> None:
    actor.memes["help"] = actor.memes.get("help", 0.0) + 1
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
    if task.id == "repair":
        actor.meters["repair"] = actor.meters.get("repair", 0.0) + 1
    elif task.id == "tune":
        actor.meters["music"] = actor.meters.get("music", 0.0) + 1
    elif task.id == "signal":
        actor.meters["signal"] = actor.meters.get("signal", 0.0) + 1
    propagate(world, narrate=False)


def drift_event(world: World, cod: Entity, task: Task) -> None:
    cod.meters["drift"] = cod.meters.get("drift", 0.0) + 1
    world.say(
        f"Then the ship gave a tiny lurch, as if the stars had tugged one string too hard."
    )


def teamwork_scene(world: World, cod: Entity, crew: list[Entity], task: Task, gear: Gear) -> None:
    world.say(
        f"{cod.id} asked for help, and the crew answered at once."
    )
    for member in crew:
        do_task(world, member, task)
    world.say(
        f"{_join([c.id for c in crew])} shared the {gear.label}, passing it hand to hand while the engine hummed."
    )


def ending_scene(world: World, cod: Entity, crew: list[Entity], task: Task, gear: Gear, venue_lost: bool) -> None:
    if venue_lost:
        world.say(
            f"{cod.id} reached the dock window and saw the performance lights shrinking behind a smear of comet dust."
        )
        world.say(
            f"The concert could not happen now, even after all that careful work."
        )
        world.say(
            f"But the crew stayed together by the glass, and {cod.id}'s song turned quiet instead of triumphant."
        )
    else:
        world.say(
            f"{cod.id} played one small, brave note, and the crew kept the ship steady long enough for it to ring through the cabin."
        )
        world.say(
            f"It was not the shining concert everyone wanted, but the teamwork held the line."
        )


def tell(setting: Setting, task: Task, gear: Gear, names: list[str]) -> World:
    world = World(setting)
    cod = world.add(Entity(id="cod", kind="character", type="cod", label="cod musician"))
    crew: list[Entity] = [
        world.add(Entity(id=names[0], kind="character", type="captain", label="captain")),
        world.add(Entity(id=names[1], kind="character", type="pilot", label="pilot")),
    ]
    for c in crew:
        c.memes["help"] = 0.0
        c.memes["trust"] = 0.0

    world.facts["cod"] = cod
    world.facts["crew"] = crew
    world.facts["task"] = task
    world.facts["task_objs"] = [task]
    world.facts["gear"] = gear

    world.say(
        f"{cod.id} was a little cod musician aboard {setting.place}, and {cod.pronoun('possessive')} songs sounded bright as tiny silver sparks."
    )
    world.say(
        f"The crew were headed to {setting.venue} for a space concert, and {cod.id} had waited all week to play."
    )
    world.say(
        f"{cod.id} loved {task.gerund}, because every note felt like a lantern floating through dark space."
    )

    world.para()
    foreshadow(world, cod, task)
    world.say(
        f"{task.warning}"
    )
    drift_event(world, cod, task)

    world.para()
    world.say(
        f"Still, {cod.id} and the crew did not give up. They looked at the {gear.label} and began to work."
    )
    world.say(
        f"{gear.prep}."
    )
    teamwork_scene(world, cod, crew, task, gear)

    task.meters["omen"] = task.meters.get("omen", 0.0) + 1
    cod.meters["drift"] = cod.meters.get("drift", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    ending_scene(world, cod, crew, task, gear, venue_lost=True)
    return world


TASKS = {
    "concert": Task(
        id="concert",
        verb="play the concert",
        gerund="tuning a warm, brave melody",
        warning="The dock lights flickered, and a warning beep kept repeating from the ceiling panel.",
        bad_sign="A red maintenance light blinked three times, like it knew the song would be late.",
        kind="music",
        tags={"music", "space", "foreshadowing", "teamwork"},
    )
}

GEAR = {
    "wrenchkit": Gear(
        id="wrenchkit",
        label="wrench kit",
        helps={"repair"},
        prep="The captain held the wrench kit steady while the pilot checked the bolts",
        tail="passed the tools back and forth until the panel stopped rattling",
    )
}

SETTINGS = {
    "starship": Setting(
        place="the small starship Pearl Fin",
        venue="the orbiting dock above Blue Reef Station",
        affords={"concert"},
    )
}

NAMES = ["Captain Nia", "Pilot Jory", "Mara", "Tess", "Rin"]


@dataclass
class StoryParams:
    setting: str = "starship"
    task: str = "concert"
    gear: str = "wrenchkit"
    crew_name_1: str = "Captain Nia"
    crew_name_2: str = "Pilot Jory"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for t_id in setting.affords:
            for g_id in GEAR:
                combos.append((s_id, t_id, g_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: cod musician, foreshadowing, teamwork, bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    setting, task, gear = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        task=task,
        gear=gear,
        crew_name_1=args.name1 or rng.choice(NAMES),
        crew_name_2=args.name2 or rng.choice(NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short space-adventure story about a cod musician who notices a warning before a concert.',
        'Tell a child-friendly story with foreshadowing, teamwork, and a bad ending aboard a little starship.',
        'Write a story where a cod and the crew work together in space, but the concert still goes wrong at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    cod = world.facts["cod"]
    crew = world.facts["crew"]
    task = world.facts["task"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {cod.id}, a little cod musician aboard the starship Pearl Fin.",
        ),
        QAItem(
            question="What warning did the cod notice before the trouble?",
            answer=f"{task.warning} The red blink was a foreshadowing sign that something was about to go wrong.",
        ),
        QAItem(
            question="How did the crew try to help?",
            answer=f"{crew[0].id} and {crew[1].id} used the {gear.label} and worked together to steady the ship.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The dock lights and the concert chance slipped away, so the performance could not happen as hoped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cod?",
            answer="A cod is a fish that lives in the sea, and in this story one cod is also a musician in space.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to reach one goal.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues that something important, good or bad, may happen later.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the hoped-for result does not happen, even if the characters tried hard.",
        ),
    ]


ASP_RULES = r"""
valid_story(S,T,G) :- setting(S), task(T), gear(G), affords(S,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], GEAR[params.gear],
                 [params.crew_name_1, params.crew_name_2])
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
    StoryParams(crew_name_1="Captain Nia", crew_name_2="Pilot Jory"),
    StoryParams(crew_name_1="Captain Sol", crew_name_2="Pilot Mira"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
