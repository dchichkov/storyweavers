#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pokey_chameleon_sound_effects_teamwork_comedy.py
================================================================================

A small standalone story world for a comedy about a pokey chameleon, sound
effects, and teamwork.

Seed idea
---------
A chameleon wants to join a noisy little performance but keeps getting stuck on
the props. The team tries to help, uses funny sound effects, and together they
turn the awkward mess into a cheerful act.

This script models:
- a chameleon with changing color and mood
- a tiny team preparing a silly performance
- physical meters like stuckness, polish, and applause
- emotional memes like confidence, embarrassment, and teamwork

The story choices are intentionally constrained so the generated stories stay
plausible, complete, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stuck": 0.0, "polish": 0.0, "applause": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "embarrassment": 0.0, "confidence": 0.0, "teamwork": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Prop:
    id: str
    label: str
    sticky: bool = False
    squeaky: bool = False
    shiny: bool = False
    colorful: bool = False
    sound_tag: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamTool:
    id: str
    label: str
    action: str
    helps_with: set[str]
    noise: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    for prop in world.entities.values():
        if not isinstance(prop, Entity):
            continue
        if prop.kind != "thing":
            continue
        if prop.attrs.get("used") and prop.attrs.get("sticky") and cham.meters["stuck"] < THRESHOLD:
            sig = ("stuck", prop.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            cham.meters["stuck"] += 1
            cham.memes["embarrassment"] += 1
            out.append(f"The pokey part of the act made {cham.id} stick for a moment.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    if cham.memes["teamwork"] < THRESHOLD:
        return out
    sig = ("teamwork", cham.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cham.meters["polish"] += 1
    cham.memes["confidence"] += 1
    out.append(f"Together, the whole team made the routine smoother.")
    return out


def _r_applause(world: World) -> list[str]:
    out: list[str] = []
    cham = world.get("chameleon")
    band = world.get("band")
    if cham.meters["polish"] < THRESHOLD or band.meters["beat"] < THRESHOLD:
        return out
    sig = ("applause", cham.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cham.meters["applause"] += 1
    band.meters["applause"] += 1
    cham.memes["joy"] += 1
    band.memes["joy"] += 1
    out.append(f"The audience clapped along with the final beat.")
    return out


CAUSAL_RULES = [
    Rule("stuck", "physical", _r_stuck),
    Rule("teamwork", "social", _r_teamwork),
    Rule("applause", "social", _r_applause),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reasonableness_gate(prop: Prop, tool: TeamTool) -> bool:
    return (prop.sticky or prop.squeaky or prop.shiny) and any(tag in tool.helps_with for tag in prop.tags)


def all_valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for pid, prop in PROPS.items():
        for tid, tool in TOOLS.items():
            if reasonableness_gate(prop, tool):
                pairs.append((pid, tid))
    return pairs


@dataclass
class StoryParams:
    prop: str
    tool: str
    sound_style: str
    team_size: int
    chameleon_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a pokey chameleon, sound effects, and teamwork.")
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--sound-style", choices=SOUND_STYLES)
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
    if args.prop and args.tool and not reasonableness_gate(PROPS[args.prop], TOOLS[args.tool]):
        raise StoryError(explain_rejection(PROPS[args.prop], TOOLS[args.tool]))
    pairs = [p for p in all_valid_pairs()
             if (args.prop is None or p[0] == args.prop)
             and (args.tool is None or p[1] == args.tool)]
    if not pairs:
        raise StoryError("(No valid combination matches the given options.)")
    prop, tool = rng.choice(sorted(pairs))
    sound_style = args.sound_style or rng.choice(sorted(SOUND_STYLES))
    name = args.name or rng.choice(CHAMELEON_NAMES)
    team_size = rng.choice([2, 3, 4])
    return StoryParams(prop, tool, sound_style, team_size, name)


def tell(params: StoryParams) -> World:
    world = World()
    cham = world.add(Entity(id=params.chameleon_name, kind="character", type="chameleon", role="star"))
    band = world.add(Entity(id="band", kind="character", type="group", label="the team", role="band"))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label=PROPS[params.prop].label, attrs={"sticky": PROPS[params.prop].sticky, "squeaky": PROPS[params.prop].squeaky, "shiny": PROPS[params.prop].shiny}))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS[params.tool].label, attrs={"help": params.tool}))
    cham.memes["teamwork"] = 0.0
    band.meters["beat"] = 1.0
    world.facts["prop"] = PROPS[params.prop]
    world.facts["tool"] = TOOLS[params.tool]
    world.facts["sound_style"] = params.sound_style

    world.say(
        f"At the tiny stage, {cham.id} the chameleon was ready for a silly show. "
        f"The team set up {PROPS[params.prop].label}, and everyone tried not to laugh too early."
    )
    world.say(
        f'{cham.id} wanted to join in, but the prop looked a little too {params.prop} for a first try.'
    )
    world.para()
    world.say(
        f'"Let\'s fix it together," said the team. {TOOLS[params.tool].noise} '
        f'They used {TOOLS[params.tool].label} and took turns helping.'
    )
    prop.attrs["used"] = True
    cham.memes["teamwork"] += 1
    cham.meters["stuck"] += 0.5
    if PROPS[params.prop].squeaky:
        world.say(f"Every tug went {params.sound_style}: {PROPS[params.prop].sound_tag or 'squeak'}!")
    else:
        world.say(f"Every tug went {params.sound_style}: {TOOLS[params.tool].noise.lower()}!")
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, {cham.id} changed from pokey to proud, the team giggled, "
        f"and the whole stage ended in happy claps."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old about a pokey chameleon and {f["prop"].label}.',
        f'Tell a comedy story where teamwork helps a chameleon join a silly act with "{f["tool"].label}".',
        f'Write a story that includes the words "pokey" and "chameleon" and uses funny sound effects like {f["sound_style"]}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    cham = world.get("chameleon")
    prop = world.facts["prop"]
    tool = world.facts["tool"]
    return [
        ("Who is the story about?",
         f"It is about {cham.id}, a chameleon who wants to help with a funny show. The team is there too, and they keep the mood silly."),
        ("Why was the chameleon pokey?",
         f"{cham.id} got pokey because the prop was tricky and sticky, so getting ready took careful teamwork. The awkward bits made the story funny instead of scary."),
        ("How did the team help?",
         f"They used {tool.label} and took turns so the prop could be handled more safely. That teamwork helped the chameleon stop getting stuck and join the act."),
        ("What changed by the end?",
         f"{cham.id} went from pokey and embarrassed to proud and happy. The stage ended with claps, which proved the performance worked."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prop = world.facts["prop"]
    tool = world.facts["tool"]
    items = [
        QAItem("What is a chameleon?",
               "A chameleon is a lizard that can change color. It is known for blending in and looking different in different places."),
        QAItem("What does teamwork mean?",
               "Teamwork means people help each other do something. When a group shares the job, the whole task can feel easier and more fun."),
        QAItem("Why are sound effects funny in a story?",
               "Sound effects can make actions feel extra playful. A silly sound can turn an awkward moment into a joke that children can picture."),
    ]
    if prop.squeaky:
        items.append(QAItem("What does squeaky mean?",
                            "Squeaky means making a short high sound, like a little toy or a wheel that needs oil. It often sounds funny in a story."))
    if tool.noise:
        items.append(QAItem("Why use a helper tool?",
                            "A helper tool can make a tricky job easier or safer. It can also help the team finish together instead of struggling alone."))
    return items


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
        lines.append(f"  {e.id:10} ({e.type:8}) meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(prop: Prop, tool: TeamTool) -> str:
    return f"(No story: {tool.label} does not help with {prop.label} in a reasonable way.)"


def valid_combos() -> list[tuple[str, str]]:
    return all_valid_pairs()


ASP_RULES = r"""
valid(P, T) :- prop(P), tool(T), sticky(P), helps(T, P).
valid(P, T) :- prop(P), tool(T), squeaky(P), helps(T, P).
valid(P, T) :- prop(P), tool(T), shiny(P), helps(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy per contract
    lines: list[str] = []
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.sticky:
            lines.append(asp.fact("sticky", pid))
        if p.squeaky:
            lines.append(asp.fact("squeaky", pid))
        if p.shiny:
            lines.append(asp.fact("shiny", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_catalogs() -> tuple[dict[str, Prop], dict[str, TeamTool], list[str]]:
    props = {
        "sticky": Prop("sticky", "sticky tape", sticky=True, tags={"sticky"}),
        "squeaky": Prop("squeaky", "a squeaky toy platform", squeaky=True, sound_tag="squeak", tags={"squeaky"}),
        "shiny": Prop("shiny", "a shiny mirror board", shiny=True, tags={"shiny"}),
    }
    tools = {
        "gloves": TeamTool("gloves", "rubber gloves", "steady", {"sticky"}, "fwip", tags={"helpful"}),
        "wipes": TeamTool("wipes", "soft wipes", "clean", {"sticky", "shiny"}, "swish", tags={"helpful"}),
        "brushes": TeamTool("brushes", "tiny brushes", "careful", {"sticky", "squeaky"}, "scrub", tags={"helpful"}),
    }
    sounds = ["boing", "splat", "fwip", "whirr"]
    return props, tools, sounds


PROPS, TOOLS, SOUND_STYLES = build_catalogs()
CHAMELEON_NAMES = ["Coco", "Milo", "Peppy", "Zuzu", "Nico"]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible prop/tool pairs:")
        for p, t in asp_valid_combos():
            print(f"  {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("sticky", "gloves", "boing", 3, "Coco"),
            StoryParams("squeaky", "brushes", "splat", 3, "Milo"),
            StoryParams("shiny", "wipes", "whirr", 4, "Peppy"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
