#!/usr/bin/env python3
"""
storyworlds/worlds/acclimate_flashback_cautionary_humor_pirate_tale.py
=====================================================================

A small pirate-tale storyworld about a crew learning to acclimate to a new sea,
with a flashback, a cautionary warning, and a humorous turn.

The seed idea:
- A young deckhand joins a pirate crew on an unfamiliar island route.
- The captain remembers a past storm in flashback.
- The crew must acclimate to bright heat, rolling waves, and the ship's routines.
- A cautionary choice prevents a repeat of an old mistake.
- Humor keeps the tale light and child-facing.

This world is intentionally small and state-driven: physical state lives in
meters, feelings in memes, and the prose is authored from those changes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "mate", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    deck: str = "the deck"
    hold: str = "the hold"
    island: str = "the island"
    breeze: str = "salt-bright"
    heat: str = "hot"
    wave: str = "rocking"
    tags: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    name: str
    risk: str
    caution: str
    flashback: str
    humor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    protects: set[str]
    note: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        clone = World(self.ship)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    port: str
    trial: str
    hero: str
    hero_type: str
    captain: str
    tool: str
    seed: Optional[int] = None


PORTS = {
    "harbor": Ship(name="Brine Harbor", tags={"sea", "harbor"}),
    "island": Ship(name="Pinehook Island", island="the island cove", tags={"island", "sea"}),
    "reef": Ship(name="Shiver Reef", tags={"reef", "sea"}),
}

TRIALS = {
    "sun": Trial(
        id="sun",
        name="blazing sun",
        risk="the deck would feel like a frying pan",
        caution="cover your head before you fry your thoughts",
        flashback="once, a swabby forgot his hat and spent the day smelling like toast",
        humor="the ship's parrot tried to fan itself with a cracker",
        tags={"heat", "sun"},
    ),
    "waves": Trial(
        id="waves",
        name="swaying waves",
        risk="new feet might wobble right into a splash",
        caution="hold the rail until your sea-legs wake up",
        flashback="the captain once slipped during a storm and hugged a barrel for an hour",
        humor="even the bucket looked seasick",
        tags={"sea", "balance"},
    ),
    "routines": Trial(
        id="routines",
        name="ship routines",
        risk="a new deckhand might mix up the ropes and the bunions of chores",
        caution="learn one job at a time so the knots do not tangle your day",
        flashback="the captain remembered a greenhand who salted the soup instead of the ropes",
        humor="the cook still called that supper 'the brave broth'",
        tags={"work", "crew"},
    ),
}

TOOLS = {
    "hat": Tool(
        id="hat",
        label="a wide straw hat",
        helps={"sun"},
        protects={"head"},
        note="shade the brow",
        tags={"hat", "sun"},
    ),
    "boots": Tool(
        id="boots",
        label="soft deck boots",
        helps={"waves"},
        protects={"feet"},
        note="grip the boards",
        tags={"boots", "sea"},
    ),
    "chart": Tool(
        id="chart",
        label="a simple chore chart",
        helps={"routines"},
        protects={"mind"},
        note="keep the jobs in order",
        tags={"chart", "crew"},
    ),
}

NAMES = ["Ava", "Milo", "Nina", "Jory", "Lena", "Toby", "Iris", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PORTS:
        for t in TRIALS:
            for tool in TOOLS:
                if t in TOOLS[tool].helps:
                    combos.append((p, t, tool))
    return combos


ASP_RULES = r"""
#show valid/3.
valid(P,T,Tool) :- port(P), trial(T), tool(Tool),
    helps(Tool,T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PORTS:
        lines.append(asp.fact("port", p))
    for t in TRIALS:
        lines.append(asp.fact("trial", t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
        for tr in sorted(TOOLS[tool].helps):
            lines.append(asp.fact("helps", tool, tr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate-tale storyworld.")
    ap.add_argument("--port", choices=PORTS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--captain", choices=["captain", "mother", "father"])
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
              if (args.port is None or c[0] == args.port)
              and (args.trial is None or c[1] == args.trial)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    port, trial, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(NAMES)
    captain = args.captain or "captain"
    return StoryParams(port=port, trial=trial, hero=hero, hero_type=hero_type, captain=captain, tool=tool)


def make_world(params: StoryParams) -> World:
    ship = PORTS[params.port]
    world = World(ship)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=["new", "brave"]))
    captain = world.add(Entity(id="captain", kind="character", type=params.captain, label="the captain"))
    trial = TRIALS[params.trial]
    tool = TOOLS[params.tool]
    gear = world.add(Entity(id=tool.id, type="thing", label=tool.label, owner=hero.id))
    gear.meters["ready"] = 1
    hero.memes["nervous"] = 1
    world.say(f"{hero.id} was a new little {hero.type} who had just joined the pirate crew on {ship.name}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to acclimate to ship life, but {trial.name} still felt strange.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {captain.pronoun('subject') if params.captain != 'captain' else 'captain'} watched kindly and said the day would be easier with practice.")
    world.para()
    world.say(f"The deck shone under the {ship.breeze} breeze, and {trial.humor}.")
    world.say(f"{hero.id} looked at {tool.label} and tried to remember {tool.note}.")
    world.say(f"Then came the warning: {trial.caution}.")
    world.say(f"{hero.id} thought of a flashback: {trial.flashback}.")
    world.para()
    hero.memes["courage"] = 1
    if params.trial == "sun":
        hero.meters["shade"] = 1
        world.say(f"{hero.id} put on {tool.label}, and the hat made the heat feel less fierce.")
    elif params.trial == "waves":
        hero.meters["balance"] = 1
        world.say(f"{hero.id} wore {tool.label}, gripped the rail, and the rocking felt friendlier.")
    else:
        hero.meters["order"] = 1
        world.say(f"{hero.id} used {tool.label} to sort the chores, and the tangled morning began to untie itself.")
    hero.memes["pride"] = 1
    world.say(f"By the end, {hero.id} had acclimated enough to grin like a real deckmate, and the crew laughed with {hero.pronoun('object')}.")
    world.facts.update(hero=hero, captain=captain, trial=trial, tool=tool, ship=ship)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child about a new crew member learning to acclimate to {f["ship"].name}.',
        f"Tell a gentle flashback story where {f['hero'].id} hears a cautionary warning and uses {f['tool'].label} to fit in on the ship.",
        f'Write a humorous pirate story that includes the word "acclimate" and ends with the crew laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, trial, tool = f["hero"], f["captain"], f["trial"], f["tool"]
    return [
        QAItem(question=f"Who was learning to acclimate in the story?", answer=f"{hero.id} was learning to acclimate to pirate life on the ship."),
        QAItem(question=f"What cautionary lesson was given before {hero.id} acted?", answer=f"The warning was: {trial.caution}."),
        QAItem(question=f"What flashback did {hero.id} remember?", answer=f"{hero.id} remembered that {trial.flashback}."),
        QAItem(question=f"What helped {hero.id} handle the day?", answer=f"{tool.label} helped {hero.id} manage the challenge and feel more like part of the crew."),
        QAItem(question=f"How did the story end?", answer=f"By the end, {hero.id} had acclimated enough to grin with the crew laughing nearby."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to acclimate?", answer="To acclimate means to get used to a new place, weather, or way of living."),
        QAItem(question="Why do sailors wear hats in strong sun?", answer="A hat can give shade and help keep the head cooler."),
        QAItem(question="Why should a new helper learn one ship job at a time?", answer="Learning one job at a time helps prevent confusion and mistakes."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(port="harbor", trial="sun", hero="Mira", hero_type="girl", captain="captain", tool="hat"),
    StoryParams(port="island", trial="waves", hero="Toby", hero_type="boy", captain="captain", tool="boots"),
    StoryParams(port="reef", trial="routines", hero="Nina", hero_type="girl", captain="captain", tool="chart"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for p, t, tool in triples:
            print(f"  {p:8} {t:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
