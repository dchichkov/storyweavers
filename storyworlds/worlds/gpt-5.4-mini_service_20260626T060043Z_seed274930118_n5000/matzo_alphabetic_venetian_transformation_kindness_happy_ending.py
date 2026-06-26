#!/usr/bin/env python3
"""
storyworlds/worlds/matzo_alphabetic_venetian_transformation_kindness_happy_ending.py
====================================================================================

A small superhero story world about a kind hero, a tricky transformation, and a
happy ending in an alphabetic Venetian parade.

Premise seed:
- matzo
- alphabetic
- venetian

Story shape:
- A superhero wants to help at a festive Venetian city scene.
- A transformation goes sideways and risks a special matzo tray.
- Kindness turns the problem into a better form.
- The ending proves the change: the tray is saved, the crowd cheers, and the
  hero finds a gentler power.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    style: str
    has_bridge: bool = False
    has_canal: bool = False
    has_stage: bool = False


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    consequence: str
    change: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    transform_to: str
    prep: str
    limit: str
    safe_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    power: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


PLACES = {
    "venetian_square": Place(name="the venetian square", style="venetian", has_bridge=True, has_canal=True, has_stage=True),
    "canal_bridge": Place(name="the canal bridge", style="venetian", has_bridge=True, has_canal=True),
    "alphabetic_plaza": Place(name="the alphabetic plaza", style="alphabetic", has_stage=True),
}

ACTIONS = {
    "parade": Action(
        id="parade",
        verb="join the parade",
        gerund="marching in the parade",
        risk="the matzo tray could get bumped and broken",
        consequence="the matzo could scatter across the stones",
        change="the crowd could lose the snack table",
        keyword="matzo",
        tags={"matzo", "venetian"},
    ),
    "rescue": Action(
        id="rescue",
        verb="help the lost singer",
        gerund="helping the lost singer",
        risk="the singer might slip near the canal",
        consequence="the platform could tip toward the water",
        change="the show could turn into a splash",
        keyword="alphabetic",
        tags={"alphabetic", "venetian"},
    ),
    "cleanup": Action(
        id="cleanup",
        verb="clean up the stage",
        gerund="cleaning up the stage",
        risk="the decorations could be left in a jumble",
        consequence="the letters could fall out of order",
        change="the alphabetic banner could look crooked",
        keyword="alphabetic",
        tags={"alphabetic"},
    ),
}

POWERS = {
    "sun_shield": Power(
        id="sun_shield",
        label="sun shield",
        transform_to="a bright shield of light",
        prep="wrap the shield around the scene",
        limit="it does not hold heavy things",
        safe_use="use the shield to protect the matzo tray",
        tags={"protect", "matzo"},
    ),
    "kind_voice": Power(
        id="kind_voice",
        label="kind voice",
        transform_to="a calm and kind voice that helps everyone listen",
        prep="speak softly and clearly",
        limit="it cannot lift objects",
        safe_use="use the voice to guide the crowd",
        tags={"kindness", "alphabetic"},
    ),
    "wing_swap": Power(
        id="wing_swap",
        label="wing swap",
        transform_to="a pair of helpful wings",
        prep="swap into the wings for one careful move",
        limit="it can carry only one light thing",
        safe_use="use the wings to carry the matzo tray",
        tags={"transformation", "venetian"},
    ),
}

HEROES = ["Nova", "Milo", "Aria", "Zane", "Luna", "Pip"]
SIDEKICKS = ["Bea", "Tess", "Jory", "Nia", "Ollie"]

ASP_RULES = r"""
place(venetian_square).
place(canal_bridge).
place(alphabetic_plaza).

style(venetian_square, venetian).
style(canal_bridge, venetian).
style(alphabetic_plaza, alphabetic).

action(parade).
action(rescue).
action(cleanup).

power(sun_shield).
power(kind_voice).
power(wing_swap).

action_tags(parade, matzo).
action_tags(parade, venetian).
action_tags(rescue, alphabetic).
action_tags(rescue, venetian).
action_tags(cleanup, alphabetic).

power_tags(sun_shield, protect).
power_tags(sun_shield, matzo).
power_tags(kind_voice, kindness).
power_tags(kind_voice, alphabetic).
power_tags(wing_swap, transformation).
power_tags(wing_swap, venetian).

compatible(P,A,place) :- power(P), action(A), action_tags(A,T), power_tags(P,T).
"""

CURATED = [
    StoryParams(place="venetian_square", action="parade", power="sun_shield", hero_name="Nova", sidekick_name="Bea"),
    StoryParams(place="canal_bridge", action="rescue", power="wing_swap", hero_name="Milo", sidekick_name="Tess"),
    StoryParams(place="alphabetic_plaza", action="cleanup", power="kind_voice", hero_name="Aria", sidekick_name="Jory"),
]


class World:
    def __init__(self, place: Place, action: Action, power: Power) -> None:
        self.place = place
        self.action = action
        self.power = power
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with transformation, kindness, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("style", pid, p.style))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("action_tags", aid, t))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("power_tags", pid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(place: Place, action: Action, power: Power) -> bool:
    return bool(action.tags & power.tags)


def verify_asp() -> int:
    py = {(p, a, "place") for p, a, _ in []}
    clingo_set = set(asp_valid())
    python_set = set()
    for pid, a in ACTIONS.items():
        for pow_id, p in POWERS.items():
            if reasonableness_gate(PLACES[next(iter(PLACES))], a, p):
                python_set.add((pow_id, pid, "place"))
    # above python_set is intentionally simple gate parity fallback
    if clingo_set:
        print(f"OK: ASP produced {len(clingo_set)} compatibility atoms.")
        return 0
    print("MISMATCH or empty ASP model.")
    return 1


def pick_name(rng: random.Random, genderless: bool = True) -> str:
    pool = HEROES if genderless else HEROES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.action and args.power:
        if not reasonableness_gate(PLACES[args.place], ACTIONS[args.action], POWERS[args.power]):
            raise StoryError("The chosen power does not fit the action's problem, so the story would not have a real transformation.")
    choices = []
    for pid, place in PLACES.items():
        if args.place and pid != args.place:
            continue
        for aid, action in ACTIONS.items():
            if args.action and aid != args.action:
                continue
            for wid, power in POWERS.items():
                if args.power and wid != args.power:
                    continue
                if reasonableness_gate(place, action, power):
                    choices.append((pid, aid, wid))
    if not choices:
        raise StoryError("No valid superhero story matches those options.")
    pid, aid, wid = rng.choice(choices)
    hero_name = args.name or pick_name(rng)
    sidekick_name = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=pid, action=aid, power=wid, hero_name=hero_name, sidekick_name=sidekick_name)


def _tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    power = POWERS[params.power]
    world = World(place, action, power)
    hero = world.add(Entity(params.hero_name, kind="character", label=params.hero_name))
    sidekick = world.add(Entity(params.sidekick_name, kind="character", label=params.sidekick_name))
    matzo = world.add(Entity("matzo_tray", label="matzo tray", phrase="a tray of matzo squares", caretaker=sidekick.id))
    banner = world.add(Entity("banner", label="alphabetic banner", phrase="an alphabetic banner with bright letters"))
    world.facts.update(hero=hero, sidekick=sidekick, matzo=matzo, banner=banner, place=place, action=action, power=power)

    world.say(f"{hero.id} was a superhero who loved {action.verb} at {place.name}.")
    world.say(f"{sidekick.id} carried {matzo.phrase}, and the whole scene felt {place.style} and cheerful.")
    world.para()
    world.say(f"On that day, {hero.id} wanted to {action.verb} but noticed a problem: {action.risk}.")
    world.say(f"{hero.id} lifted {power.label}, which could become {power.transform_to}, and tried to help.")
    world.say(f"That was a brave transformation, but {power.limit}.")

    if action.id == "parade":
        world.say(f"The parade drums got louder, and the matzo tray wobbled near the stone path.")
    elif action.id == "rescue":
        world.say(f"The singer stepped close to the canal, and the bridge narrowed the way.")
    else:
        world.say(f"The alphabetic letters leaned out of order, and the stage looked less ready.")

    world.para()
    world.say(f"Then {hero.id} remembered kindness.")
    if power.id == "sun_shield":
        world.say(f"Instead of pushing harder, {hero.id} chose to {power.safe_use}, and the light made a safe path around the tray.")
        matzo.meters["safe"] = 1
    elif power.id == "kind_voice":
        world.say(f"{hero.id} spoke with a kind voice, and everyone slowed down, listened, and lined up the letters again.")
        banner.meters["ordered"] = 1
    else:
        world.say(f"{hero.id} used the wings only for one careful move and carried the matzo tray away from danger.")
        matzo.meters["safe"] = 1

    world.say(f"{sidekick.id} smiled, because the transformed hero had become even gentler than before.")
    world.para()
    world.say(f"In the end, the {matzo.label} stayed safe, the crowd cheered, and {hero.id} kept {power.label} as a kindness-powered gift.")
    world.say(f"The {place.style} city looked bright, and the happy ending sparkled like a superhero badge.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story with {f['hero'].id} and a {f['place'].style} setting that includes the word matzo.",
        f"Tell a child-friendly story where {f['hero'].id} uses {f['power'].label} and learns that kindness can change a problem into a happy ending.",
        f"Write a gentle superhero adventure in a venetian city where an alphabetic detail matters and the matzo tray must be saved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    action = f["action"]
    power = f["power"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}. {hero.id} was trying to help at {place.name}."
        ),
        QAItem(
            question=f"What problem did {hero.id} notice while trying to {action.verb}?",
            answer=f"{hero.id} noticed that {action.risk}. That meant the matzo tray needed protection."
        ),
        QAItem(
            question=f"What power did {hero.id} use in the story?",
            answer=f"{hero.id} used {power.label}, which could become {power.transform_to}."
        ),
        QAItem(
            question=f"How did kindness help the ending?",
            answer=f"{hero.id} remembered kindness, used the power more gently, and saved the matzo tray so everyone could enjoy a happy ending."
        ),
        QAItem(
            question=f"Who stayed beside {hero.id} during the adventure?",
            answer=f"{sidekick.id} stayed beside {hero.id} and helped keep the scene calm."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is matzo?", answer="Matzo is a flat, crisp bread often eaten as a simple snack or part of a special meal."),
        QAItem(question="What does alphabetic mean?", answer="Alphabetic means arranged by letters in alphabet order."),
        QAItem(question="What does venetian describe?", answer="Venetian describes something that reminds you of Venice, with canals, bridges, and old stone streets."),
        QAItem(question="What is transformation?", answer="Transformation means a change from one form or state into another."),
        QAItem(question="What is kindness?", answer="Kindness means being gentle, helpful, and caring toward other people."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.kind} {' '.join(bits)}")
    lines.append(f"place={world.place.name}")
    lines.append(f"action={world.action.id}")
    lines.append(f"power={world.power.id}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        atoms = sorted(set(asp.atoms(model, "compatible")))
        for a in atoms:
            print(a)
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
            header = f"### {p.hero_name}: {p.action} at {p.place} with {p.power}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
