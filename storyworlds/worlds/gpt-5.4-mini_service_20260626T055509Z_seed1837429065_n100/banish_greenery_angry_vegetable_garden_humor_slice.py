#!/usr/bin/env python3
"""
A standalone story world for a slice-of-life vegetable garden tale with humor:
a gardener notices that a little patch of greenery has started crowding out the
veggies, gets mildly angry, and then finds a funny, practical way to banish the
overgrowth without making the day feel mean.

The world is modeled as a small simulation with physical meters and emotional
memes. The story is generated from the simulated state, not from a fixed prose
template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"woman", "girl", "gardener"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"man", "boy"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class GardenPlot:
    name: str = "the vegetable garden"
    has_humor: bool = True
    rooms: set[str] = field(default_factory=lambda: {"beds", "paths", "fence"})


@dataclass
class Intrusion:
    name: str
    phrase: str
    mess: str
    spreads: set[str]
    mood_nudge: str
    joke: str


@dataclass
class Tool:
    name: str
    phrase: str
    clears: set[str]
    method: str
    result_line: str
    humorous: bool = True


class World:
    def __init__(self, plot: GardenPlot) -> None:
        self.plot = plot
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.plot)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _hardened_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("conflict", 0.0) < THRESHOLD:
            continue
        if e.meters.get("resolved", 0.0) >= THRESHOLD:
            continue
        if ("cleanup", e.id) in world.fired:
            continue
        world.fired.add(("cleanup", e.id))
        out.append(f"{e.pronoun('possessive').capitalize()} cheeks stayed tight while {e.pronoun()} thought.")
    return out


def _banish_greenery(world: World) -> list[str]:
    out: list[str] = []
    gardener = world.get("gardener")
    greenery = world.get("greenery")
    tool = world.get("shears")
    if gardener.memes.get("angry", 0.0) < THRESHOLD:
        return out
    if greenery.meters.get("spread", 0.0) < THRESHOLD:
        return out
    if tool.meters.get("ready", 0.0) < THRESHOLD:
        return out
    sig = ("banish", greenery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    greenery.meters["spread"] = 0.0
    greenery.meters["banished"] = 1.0
    gardener.meters["tidy"] = gardener.meters.get("tidy", 0.0) + 1
    gardener.memes["angry"] = max(0.0, gardener.memes.get("angry", 0.0) - 1.0)
    gardener.memes["amused"] = gardener.memes.get("amused", 0.0) + 1.0
    out.append(f"The extra greenery lost its crowding edge and scooted out of the carrot row.")
    return out


CAUSAL_RULES = [
    _hardened_cleanup,
    _banish_greenery,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_banish(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    g = sim.get("greenery")
    gardener = sim.get("gardener")
    return {
        "banished": bool(g.meters.get("banished", 0.0) >= THRESHOLD),
        "mood": gardener.memes.get("amused", 0.0),
    }


def setup_line(plot: GardenPlot) -> str:
    return "The vegetable garden was neat, with tomatoes, beans, and lettuce lined up like they were waiting for lunch."


def intrusion_line(intrusion: Intrusion) -> str:
    return f"Then a patch of {intrusion.phrase} tucked itself between the rows."


def mood_line(gardener: Entity, intrusion: Intrusion) -> str:
    if gardener.memes.get("angry", 0.0) >= THRESHOLD:
        return f"{gardener.id.capitalize()} got angry because {intrusion.phrase} was poking into the bean row."
    return f"{gardener.id.capitalize()} blinked at the surprise and tried not to laugh."


def humor_line(intrusion: Intrusion) -> str:
    return intrusion.joke


def tool_offer(tool: Tool, gardener: Entity) -> str:
    return f"{gardener.id.capitalize()} grabbed the {tool.phrase} and said it was time for a tiny garden rescue."


def resolution_line(gardener: Entity, tool: Tool, intrusion: Intrusion) -> str:
    return f"With one careful sweep, the {tool.name} fixed the little problem, and the garden looked proper again."


def tell(plot: GardenPlot, intrusion: Intrusion, tool: Tool, gardener_name: str = "Mina") -> World:
    world = World(plot)
    gardener = world.add(Entity(
        id="gardener",
        kind="character",
        type="woman",
        label=gardener_name,
        meters={"tidy": 0.0},
        memes={"angry": 0.0, "amused": 0.0},
    ))
    green = world.add(Entity(
        id="greenery",
        type="weeds",
        label="greenery",
        meters={"spread": 1.0},
    ))
    shears = world.add(Entity(
        id="shears",
        type="tool",
        label=tool.name,
        owner=gardener.id,
        meters={"ready": 1.0},
    ))

    world.say(setup_line(plot))
    world.say(intrusion_line(intrusion))
    gardener.memes["angry"] += 1.0
    green.meters["spread"] += 1.0
    world.para()
    world.say(mood_line(gardener, intrusion))
    world.say(humor_line(intrusion))
    world.say(tool_offer(tool, gardener))
    propagate(world, narrate=True)
    if predict_banish(world)["banished"]:
        gardener.meters["resolved"] = 1.0
        world.para()
        world.say(resolution_line(gardener, tool, intrusion))
        world.say(f"{gardener.id} even smiled at the stubborn little pile of clippings, as if it had told a joke back.")
    else:
        raise StoryError("The garden problem was not actually solved by the chosen tool.")
    world.facts.update(plot=plot, intrusion=intrusion, tool=tool, gardener=gardener, greenery=green)
    return world


PLOT = GardenPlot()

INTRUSIONS = {
    "ivy": Intrusion(
        name="ivy",
        phrase="greenery",
        mess="overgrowth",
        spreads={"beds"},
        mood_nudge="annoyed",
        joke="It looked less like a plant and more like it had rented the whole row.",
    ),
    "mint": Intrusion(
        name="mint",
        phrase="way-too-energetic greenery",
        mess="sprawl",
        spreads={"beds", "paths"},
        mood_nudge="irritated",
        joke="The mint acted like it was late for a meeting and had to get everywhere at once.",
    ),
    "vines": Intrusion(
        name="vines",
        phrase="long green vines",
        mess="tangle",
        spreads={"fence", "beds"},
        mood_nudge="cross",
        joke="The vines reached over the fence like nosy neighbors trying to read the recipe card.",
    ),
}

TOOLS = {
    "shears": Tool(
        name="shears",
        phrase="garden shears",
        clears={"beds", "paths"},
        method="clip the greenery back",
        result_line="The clipped stems went into a neat little heap.",
        humorous=True,
    ),
    "basket": Tool(
        name="basket",
        phrase="a basket for clippings",
        clears={"beds"},
        method="gather the cut greenery without dropping it on the carrots",
        result_line="The basket caught every last curly stem.",
        humorous=True,
    ),
    "fork": Tool(
        name="fork",
        phrase="a garden fork",
        clears={"paths", "fence"},
        method="lift the roots from the soil",
        result_line="The fork pried up the roots with a soft little pop.",
        humorous=True,
    ),
}


@dataclass
class StoryParams:
    intrusion: str
    tool: str
    gardener_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for i, intr in INTRUSIONS.items():
        for t, tool in TOOLS.items():
            if intr.name == "mint" and t == "fork":
                combos.append((i, t))
            elif intr.name == "ivy" and t in {"shears", "basket"}:
                combos.append((i, t))
            elif intr.name == "vines" and t in {"shears", "fork"}:
                combos.append((i, t))
    return combos


def explain_rejection(intrusion: Intrusion, tool: Tool) -> str:
    return f"(No story: {tool.phrase} would not reasonably handle {intrusion.phrase} in the vegetable garden.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life vegetable garden storyworld with a humorous banishing turn.")
    ap.add_argument("--intrusion", choices=INTRUSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.intrusion and args.tool:
        intr = INTRUSIONS[args.intrusion]
        tool = TOOLS[args.tool]
        if (args.intrusion, args.tool) not in combos:
            raise StoryError(explain_rejection(intr, tool))
    choices = [c for c in combos if (args.intrusion is None or c[0] == args.intrusion) and (args.tool is None or c[1] == args.tool)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    intrusion, tool = rng.choice(sorted(choices))
    gardener_name = args.name or rng.choice(["Mina", "Rosa", "June", "Tess", "Ivy"])
    return StoryParams(intrusion=intrusion, tool=tool, gardener_name=gardener_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life story set in a vegetable garden where greenery causes a small problem and a funny fix follows.',
        f"Tell a gentle story about {f['gardener'].id} getting mildly angry at {f['intrusion'].phrase} and using {f['tool'].phrase} to banish it.",
        f"Write a humorous story in a vegetable garden that ends with the greenery gone and the garden calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gardener = f["gardener"]
    intr = f["intrusion"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Why did {gardener.id} get angry in the vegetable garden?",
            answer=f"{gardener.id} got angry because the {intr.phrase} was crowding the vegetable rows.",
        ),
        QAItem(
            question=f"What did {gardener.id} use to banish the greenery?",
            answer=f"{gardener.id} used {tool.phrase} to clear the extra greenery from the garden.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the greenery was banished, the rows were tidy again, and {gardener.id} felt amused instead of angry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow food plants like tomatoes, beans, lettuce, and carrots.",
        ),
        QAItem(
            question="Why do gardeners pull weeds or extra greenery?",
            answer="Gardeners pull weeds or extra greenery so the food plants have room, water, and sunlight to grow well.",
        ),
        QAItem(
            question="How can garden tools help?",
            answer="Garden tools like shears or forks can clip, lift, or gather plants so the work is quicker and cleaner.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(I,T) :- intrusion(I), tool(T), acceptable(I,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for i in INTRUSIONS:
        lines.append(asp.fact("intrusion", i))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for i, t in valid_combos():
        lines.append(asp.fact("acceptable", i, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("ivy", "shears", "Mina"),
    StoryParams("mint", "fork", "Rosa"),
    StoryParams("vines", "fork", "June"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLOT, INTRUSIONS[params.intrusion], TOOLS[params.tool], params.gardener_name)
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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.gardener_name}: {p.intrusion} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
