#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chariot_problem_solving_moral_value_superhero_story.py
======================================================================================

A small standalone storyworld for a superhero-style tale centered on a
chariot, problem solving, and moral value.

Premise:
- A child hero and a trusted ally are on a city parade route.
- A decorated chariot gets stuck at a bridge gate during a celebration.
- The hero must choose between showing off and doing the honest, helpful thing.
- They solve the problem with simple tools and teamwork, then receive a moral
  lesson about using strength to help others instead of taking credit.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- state-driven story rendering
- forward-chained causal rules
- reasonableness gate
- inline ASP twin and Python parity verification
- three Q&A sets grounded in the simulated world

This script is self-contained and stdlib-only.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    crowd: str
    obstacle: str
    helper_place: str
    ending_image: str


@dataclass
class Vehicle:
    id: str
    label: str
    stuck_word: str
    pull_word: str
    has_load: bool = True


@dataclass
class ProblemTool:
    id: str
    label: str
    uses: str
    good_for: str
    sense: int
    power: int


@dataclass
class MoralChoice:
    id: str
    label: str
    lesson: str
    praise: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_crowd_worried(world: World) -> list[str]:
    out = []
    gate = world.entities.get("gate")
    if not gate or gate.meters["blocked"] < THRESHOLD:
        return out
    sig = ("crowd_worried",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "ally"):
        if eid in world.entities:
            world.get(eid).memes["concern"] += 1
    out.append("__crowd__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    if world.entities.get("rope") and world.entities["rope"].meters["used"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["pride"] += 1
            world.get("ally").memes["trust"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("crowd_worried", _r_crowd_worried), Rule("teamwork", _r_teamwork)]


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


def reasonableness_gate(tool: ProblemTool, vehicle: Vehicle) -> bool:
    return tool.sense >= SENSE_MIN and vehicle.has_load


def tool_can_fix(tool: ProblemTool, vehicle: Vehicle) -> bool:
    return tool.power >= 2 and "stuck" in vehicle.stuck_word


def tell(scene: Scene, vehicle: Vehicle, tool: ProblemTool, moral: MoralChoice,
         hero_name: str = "Nova", ally_name: str = "Beacon",
         hero_type: str = "girl", ally_type: str = "boy",
         mayor_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name,
                            role="hero", traits=["brave", "kind"]))
    ally = world.add(Entity("ally", kind="character", type=ally_type, label=ally_name,
                            role="ally", traits=["careful", "steady"]))
    mayor = world.add(Entity("mayor", kind="character", type=mayor_type, label="the mayor",
                             role="authority"))
    chariot = world.add(Entity("chariot", type="vehicle", label=vehicle.label))
    gate = world.add(Entity("gate", type="thing", label="the bridge gate"))
    rope = world.add(Entity("rope", type="tool", label=tool.label))
    rope.meters["used"] = 0.0
    gate.meters["blocked"] = 0.0

    hero.memes["hope"] += 1
    ally.memes["care"] += 1
    world.say(
        f"On parade day, {hero.label} and {ally.label} flew over {scene.place} in bright capes. "
        f"{scene.crowd}"
    )
    world.say(
        f"At the bridge, a silver chariot rolled forward for the celebration, but {scene.obstacle}."
    )

    world.para()
    world.say(f"{hero.label} wanted to impress the crowd, but {ally.label} pointed to the blocked gate.")
    world.say(
        f'"If the chariot stays stuck, nobody reaches the square," {ally.label} said. '
        f'"We need a real plan, not a showy one."'
    )

    if not reasonableness_gate(tool, vehicle):
        raise StoryError("The chosen tool does not fit this problem well enough.")

    world.para()
    world.say(f"{hero.label} looked at {tool.label} and said, 'We can use this {tool.uses}.'")
    if tool_can_fix(tool, vehicle):
        gate.meters["blocked"] = 1.0
        rope.meters["used"] = 1.0
        propagate(world, narrate=False)
        world.say(
            f"They hooked the rope to the chariot wheel, lifted together, and slowly guided it free."
        )
        world.say(
            f"The gate swung open, and the chariot finally moved toward the square."
        )
        world.para()
        hero.memes["joy"] += 1
        ally.memes["joy"] += 1
        hero.memes["moral"] += 1
        ally.memes["moral"] += 1
        world.say(
            f"When the mayor thanked them, {hero.label} did not grab the spotlight. "
            f"{hero.label_word if hero.type in {'mother','father'} else hero.label} pointed to {ally.label} and said, "
            f'"{ally.label} found the smart fix. We helped together."'
        )
        world.say(
            f"The mayor smiled and praised {moral.praise}. {moral.lesson}"
        )
        world.say(
            f"By sunset, the chariot stood safely in the square, shining beside the lanterns."
        )
        outcome = "solved"
    else:
        gate.meters["blocked"] = 1.0
        world.say(
            f"But the {tool.label} was not strong enough for the wheel, so they had to think again."
        )
        world.say(
            f"{ally.label} noticed a better idea: clear the stones, then push from both sides."
        )
        rope.meters["used"] = 1.0
        gate.meters["blocked"] = 0.0
        world.say(
            f"They moved the stones away, pushed carefully, and the chariot rolled free at last."
        )
        world.say(
            f"{hero.label} nodded and let {ally.label} take the credit, because doing the right thing mattered more than bragging."
        )
        world.say(
            f"The mayor praised their honesty and teamwork. {moral.lesson}"
        )
        world.say(
            f"At the end, the chariot gleamed in the square, and the city cheered for the help, not the boast."
        )
        outcome = "solved"

    world.facts.update(
        hero=hero, ally=ally, mayor=mayor, scene=scene, vehicle=vehicle,
        tool=tool, moral=moral, outcome=outcome, rope=rope, gate=gate
    )
    return world


SCENES = {
    "parade": Scene("parade", "the sunlit avenue", "Crowds waved flags and tossed flower petals.",
                    "a fallen banner jammed the bridge gate", "the town square",
                    "The chariot stood free beside bright streamers."),
    "festival": Scene("festival", "the festival street", "Children cheered beside music floats.",
                      "a pile of ribbons tangled the bridge gate", "the lantern-lit plaza",
                      "The chariot rolled past the gates under glowing paper stars."),
}

VEHICLES = {
    "chariot": Vehicle("chariot", "chariot", "stuck in the gate", "pull the chariot"),
}

TOOLS = {
    "rope": ProblemTool("rope", "long rope", "pulling heavy things", "wheels and gates", 3, 3),
    "lever": ProblemTool("lever", "wooden lever", "lifting and prying", "stuck wheels", 3, 2),
    "crowbar": ProblemTool("crowbar", "small crowbar", "prying blocks away", "heavy jams", 2, 2),
}

MORALS = {
    "share_credit": MoralChoice("share_credit", "share credit", "share credit when a friend helps", "their honesty and teamwork"),
    "help_first": MoralChoice("help_first", "help first", "choose helping over showing off", "their helpful hearts"),
}

GIRL_NAMES = ["Nova", "Zara", "Mina", "Lia", "Aria", "Nia"]
BOY_NAMES = ["Beacon", "Finn", "Rex", "Milo", "Jace", "Theo"]
TRAITS = ["brave", "kind", "steady", "curious"]


@dataclass
class StoryParams:
    scene: str
    vehicle: str
    tool: str
    moral: str
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
    mayor_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, "chariot", t, m) for s in SCENES for t in TOOLS for m in MORALS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a chariot, problem solving, and moral value.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--ally")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally-type", choices=["girl", "boy"])
    ap.add_argument("--mayor", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.tool and not reasonableness_gate(TOOLS[args.tool], VEHICLES["chariot"]):
        raise StoryError("That tool does not fit the chariot problem well enough.")
    filtered = [
        c for c in combos
        if (args.scene is None or c[0] == args.scene)
        and (args.vehicle is None or c[1] == args.vehicle)
        and (args.tool is None or c[2] == args.tool)
        and (args.moral is None or c[3] == args.moral)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    scene, vehicle, tool, moral = rng.choice(filtered)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    ally_type = args.ally_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(
        scene=scene,
        vehicle=vehicle,
        tool=tool,
        moral=moral,
        hero_name=args.name or _pick_name(rng, hero_type),
        hero_type=hero_type,
        ally_name=args.ally or _pick_name(rng, ally_type),
        ally_type=ally_type,
        mayor_type=args.mayor or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the word "chariot" and shows problem solving.',
        f"Tell a story where {f['hero'].label} and {f['ally'].label} help a stuck chariot and learn to do the right thing.",
        f'Write a moral-value story about helping first, sharing credit, and getting a chariot to the square.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    scene = f["scene"]
    moral = f["moral"]
    return [
        ("Who are the story about?",
         f"It is about {hero.label} and {ally.label}, two little superheroes who wanted to help the city. They were the ones who solved the chariot problem together."),
        ("What problem did they have?",
         f"The chariot was blocked at the bridge gate because {scene.obstacle}. They had to solve that problem before the celebration could continue."),
        ("How did they solve it?",
         f"They used {f['tool'].label} and teamwork to free the chariot. They also chose the honest path by sharing credit instead of boasting."),
        ("What moral did they learn?",
         f"They learned to {moral.label} and to use their powers to help others. That made the ending kinder and better for everyone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a chariot?",
         "A chariot is a wheeled vehicle that can carry people or things. In old stories it often sounds grand and important."),
        ("What does problem solving mean?",
         "Problem solving means thinking carefully about a trouble and finding a way to fix it. It often takes patience, tools, and teamwork."),
        ("What is moral value in a story?",
         "Moral value is the lesson about choosing what is right, kind, and fair. It helps the reader learn how to act well."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], VEHICLES[params.vehicle], TOOLS[params.tool], MORALS[params.moral],
                 params.hero_name, params.ally_name, params.hero_type, params.ally_type, params.mayor_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(S, V, T, M) :- scene(S), vehicle(V), tool(T), moral(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for v in VEHICLES:
        lines.append(asp.fact("vehicle", v))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("sense", t, tool.sense))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as e:
        return 1 if not isinstance(e, StoryError) else 1
    return rc


CURATED = [
    StoryParams("parade", "chariot", "rope", "share_credit", "Nova", "girl", "Beacon", "boy", "mother", "brave"),
    StoryParams("festival", "chariot", "lever", "help_first", "Mina", "girl", "Finn", "boy", "father", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
