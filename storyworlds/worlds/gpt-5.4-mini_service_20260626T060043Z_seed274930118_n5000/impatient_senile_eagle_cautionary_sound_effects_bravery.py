#!/usr/bin/env python3
"""
storyworlds/worlds/impatient_senile_eagle_cautionary_sound_effects_bravery.py
=============================================================================

A small slice-of-life story world about an impatient, senile eagle who learns
to be brave in a careful, ordinary moment.

Premise:
- An old eagle gets restless while waiting for a practical errand to be done.
- A younger helper gives a cautionary warning about the wind, the step, or the
  missing perch.
- Sound effects make the scene feel alive: flap, tap, creak, clink.
- Bravery is not a big battle here; it is the choice to listen, slow down, and
  try the safe way anyway.

The model is intentionally compact: a few characters, a few places, a small
physical risk, and one emotional turn from impatience to calm bravery.
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
    location: str = ""
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"impatience": 0.0, "bravery": 0.0, "worry": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"eagle", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    wind: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    caution: str
    risk_meter: str
    sound: str
    bravery: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    label: str
    phrase: str
    type: str
    location: str
    risky_region: str
    requires: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "garden": Setting(place="the garden", wind="a small wind", afford={"walk", "fetch"}),
    "porch": Setting(place="the porch", wind="a drafty breeze", afford={"wait", "fetch"}),
    "dock": Setting(place="the dock", wind="a windy afternoon", afford={"walk", "fetch"}),
}

ACTIONS = {
    "fetch": Action(
        id="fetch",
        verb="fetch the berry tin",
        gerund="fetching the berry tin",
        rush="hurry over to the tin",
        caution="the boards could wobble in the wind",
        risk_meter="clumsy",
        sound="clink-clink",
        bravery="take the careful steps anyway",
        tags={"sound", "cautionary", "bravery"},
    ),
    "walk": Action(
        id="walk",
        verb="walk to the far bench",
        gerund="walking to the far bench",
        rush="rush to the bench",
        caution="the path was a little slippery",
        risk_meter="slip",
        sound="tap-tap",
        bravery="keep a slow and steady pace",
        tags={"sound", "cautionary", "bravery"},
    ),
    "wait": Action(
        id="wait",
        verb="wait for the kettle to whistle",
        gerund="waiting for the kettle",
        rush="jump up too soon",
        caution="the tea was not ready yet",
        risk_meter="restless",
        sound="whirr-hum",
        bravery="sit still and breathe",
        tags={"sound", "cautionary", "bravery"},
    ),
}

GOALS = {
    "berry_tin": Goal(
        label="berry tin",
        phrase="a little tin of berries",
        type="tin",
        location="the ledge",
        risky_region="feet",
        requires="steady_steps",
        tags={"fetch"},
    ),
    "tea_cup": Goal(
        label="tea cup",
        phrase="a warm tea cup",
        type="cup",
        location="the table",
        risky_region="feet",
        requires="steady_steps",
        tags={"wait"},
    ),
    "reading_glasses": Goal(
        label="reading glasses",
        phrase="a pair of reading glasses",
        type="glasses",
        location="the bench",
        risky_region="feet",
        requires="steady_steps",
        tags={"walk"},
    ),
}

GIRL_NAMES = ["Mira", "June", "Tessa", "Nina", "Lina"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Miles", "Nate"]


@dataclass
class StoryParams:
    place: str
    action: str
    goal: str
    name: str = "Ari"
    companion: str = "neighbor"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: an impatient, senile eagle and a careful helper.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["neighbor", "grandchild", "friend"])
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


def reasonableness_gate(action: Action, goal: Goal) -> bool:
    return action.id in goal.tags


def explain_rejection(action: Action, goal: Goal) -> str:
    return (
        f"(No story: {action.gerund} does not match a scene about {goal.label}. "
        f"Try a goal that fits the action.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.goal:
        if not reasonableness_gate(ACTIONS[args.action], GOALS[args.goal]):
            raise StoryError(explain_rejection(ACTIONS[args.action], GOALS[args.goal]))

    combos = [
        (p, a, g)
        for p in SETTINGS
        for a in ACTIONS
        for g in GOALS
        if reasonableness_gate(ACTIONS[a], GOALS[g])
        and (args.place is None or args.place == p)
        and (args.action is None or args.action == a)
        and (args.goal is None or args.goal == g)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, action, goal = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    companion = args.companion or rng.choice(["neighbor", "grandchild", "friend"])
    return StoryParams(place=place, action=action, goal=goal, name=name, companion=companion)


def predict_risk(world: World, actor: Entity, action: Action, goal: Entity) -> bool:
    sim = world.copy()
    do_action(sim, sim.get(actor.id), action, narrate=False)
    return sim.get(goal.id).meters.get("scuffed", 0.0) >= THRESHOLD or sim.get(goal.id).meters.get("tipped", 0.0) >= THRESHOLD


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.memes["impatience"] += 1
    actor.meters[action.risk_meter] = actor.meters.get(action.risk_meter, 0.0) + 1
    if action.id == "wait":
        actor.memes["calm"] += 1
    if narrate:
        world.say(f"{actor.id} wanted to {action.verb}, but the moment asked for patience.")
        world.say(f"{action.sound}, said the little world around {world.setting.place}.")
    if action.id == "fetch":
        actor.meters["wing"] = actor.meters.get("wing", 0.0) + 0.5


def warn(world: World, helper: Entity, actor: Entity, action: Action, goal: Entity) -> None:
    if predict_risk(world, actor, action, goal):
        actor.memes["worry"] += 1
        world.facts["warning"] = action.caution
        world.say(
            f'"Careful," said {helper.id}. "{action.caution.capitalize()}."'
        )


def brave_turn(world: World, actor: Entity, action: Action, goal: Entity) -> None:
    actor.memes["bravery"] += 1
    actor.memes["impatience"] = max(0.0, actor.memes["impatience"] - 1)
    world.say(
        f"{actor.id} took a breath, tucked in {actor.pronoun('possessive')} feathers, "
        f"and chose to {action.bravery}."
    )
    world.say(f"With a soft {action.sound}, {actor.id} made it to {goal.label} without a spill.")


def finish(world: World, actor: Entity, goal: Entity) -> None:
    actor.memes["calm"] += 1
    world.say(
        f"In the end, {actor.id} stood by {goal.location} and looked quite pleased. "
        f"The little errand was done, and the afternoon felt ordinary again."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    action = ACTIONS[params.action]
    goal_def = GOALS[params.goal]
    world = World(setting)
    eagle = world.add(Entity(id=params.name, kind="character", type="eagle", label="eagle"))
    helper = world.add(Entity(id=params.companion, kind="character", type="person", label=params.companion))
    goal = world.add(Entity(id=goal_def.label, kind="thing", type=goal_def.type, label=goal_def.label, phrase=goal_def.phrase, caretaker=helper.id, location=goal_def.location))

    world.say(
        f"{eagle.id} was an impatient, senile eagle who liked to keep busy at {setting.place}."
    )
    world.say(
        f"{eagle.id} wanted {goal_def.phrase} moved right away, even though {helper.id} said to slow down."
    )
    world.para()
    world.say(f"The day had {setting.wind}, and the boards went {action.sound} under careful feet.")
    warn(world, helper, eagle, action, goal)
    do_action(world, eagle, action, narrate=True)
    world.para()
    brave_turn(world, eagle, action, goal)
    finish(world, eagle, goal)

    world.facts.update(
        eagle=eagle,
        helper=helper,
        goal=goal,
        action=action,
        setting=setting,
        goal_def=goal_def,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    eagle = f["eagle"]
    action = f["action"]
    goal_def = f["goal_def"]
    return [
        f"Write a short slice-of-life story about an impatient, senile eagle who wants to {action.verb}.",
        f"Tell a gentle story where {eagle.id} is warned that {action.caution}, then chooses bravery.",
        f"Write a child-friendly story with sound effects like {action.sound} and a calm ending near {goal_def.location}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    eagle = f["eagle"]
    helper = f["helper"]
    goal = f["goal"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {eagle.id}, an impatient, senile eagle who learns to be careful.",
        ),
        QAItem(
            question=f"What did {helper.id} warn {eagle.id} about?",
            answer=f"{helper.id} warned that {action.caution}.",
        ),
        QAItem(
            question=f"What did {eagle.id} decide to do instead of rushing?",
            answer=f"{eagle.id} decided to show bravery and {action.bravery}.",
        ),
        QAItem(
            question=f"What sound is part of the story?",
            answer=f"The story uses the sound effect {action.sound}.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{eagle.id} ended calmer and the {goal.label} was handled safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary in a steady way, especially when it is safer to be careful.",
        ),
        QAItem(
            question="Why do cautionary warnings matter?",
            answer="Cautionary warnings help people notice a possible problem before it turns into a mess or an accident.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects like clink, tap, and creak help the reader hear the scene in their imagination.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="garden", action="fetch", goal="berry_tin", name="Ari", companion="neighbor"),
    StoryParams(place="porch", action="wait", goal="tea_cup", name="Milo", companion="friend"),
    StoryParams(place="dock", action="walk", goal="reading_glasses", name="Sky", companion="grandchild"),
]


ASP_RULES = r"""
% A goal is reasonable for an action when the action belongs to the goal's tag set.
reasonable(A, G) :- action(A), goal(G), action_tag(A, T), goal_tag(G, T).

% A story is valid when the place affords the action and the action is reasonable
% for the goal.
valid_story(P, A, G) :- setting(P), affords(P, A), reasonable(A, G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("action_tag", aid, t))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for t in sorted(g.tags):
            lines.append(asp.fact("goal_tag", gid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted(
        (p, a, g)
        for p in SETTINGS
        for a in ACTIONS
        for g in GOALS
        if a in SETTINGS[p].afford and reasonableness_gate(ACTIONS[a], GOALS[g])
    )
    cl = asp_valid_stories()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("python-only:", sorted(set(py) - set(cl)))
    print("clingo-only:", sorted(set(cl) - set(py)))
    return 1


def resolve_params_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for p, a, g in stories:
            print(f"  {p:8} {a:6} {g}")
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
            header = f"### {p.name}: {p.action} at {p.place} (goal: {p.goal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
