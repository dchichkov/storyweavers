#!/usr/bin/env python3
"""
storyworlds/worlds/deuce_havoc_inner_monologue_repetition_superhero_story.py
=============================================================================

A small superhero story world about a young hero, an escalating bit of havoc,
and the inner monologue that helps them find a brave, useful plan.

The seed words "deuce" and "havoc" are built into the domain: Deuce is the
tricky troublemaker, and havoc is the disruptive mess the hero must stop.

Story premise:
- A child hero loves being helpful around the city.
- Deuce causes havoc with a noisy device in a public place.
- The hero worries, thinks through choices in an inner monologue, and uses
  repetition to steady themself and act.
- The ending proves the change: the havoc stops and the city feels safe again.

This world follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- standalone stdlib script
- lazy ASP import only inside ASP helpers
- generate/emit/main plus parser and param resolution
- Python + ASP reasonableness parity and verification
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.type.endswith("s") or self.label.endswith("s")


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    mess: str
    harm: str
    intensity: int
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    solves: set[str]
    prep: str
    tail: str
    user_label: str = "hero"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trouble: Optional[Trouble] = None
        self.tool: Optional[Tool] = None

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.trouble = self.trouble
        clone.tool = self.tool
        return clone


@dataclass
class StoryParams:
    place: str
    trouble: str
    tool: str
    name: str
    gender: str
    sidekick: str
    seed: Optional[int] = None


PLACES = {
    "city": Place(id="city", label="the city plaza", indoors=False, affords={"drones", "sirens"}),
    "dock": Place(id="dock", label="the dockside", indoors=False, affords={"drones", "smoke"}),
    "lab": Place(id="lab", label="the science lab", indoors=True, affords={"sparks", "smoke"}),
    "rooftop": Place(id="rooftop", label="the rooftop", indoors=False, affords={"drones", "sparks"}),
}

TROUBLES = {
    "drone": Trouble(
        id="drone",
        label="a buzzing drone",
        verb="chase the drone",
        gerund="chasing the drone",
        rush="dash after the drone",
        mess="buzz",
        harm="it could crash into people and window glass",
        intensity=2,
        keyword="drone",
        tags={"tech", "noise"},
    ),
    "smoke": Trouble(
        id="smoke",
        label="a smoke cloud",
        verb="clear the smoke",
        gerund="clearing the smoke",
        rush="run toward the smoke",
        mess="smoke",
        harm="it could hide the way and scare everyone",
        intensity=2,
        keyword="smoke",
        tags={"air", "safety"},
    ),
    "sparks": Trouble(
        id="sparks",
        label="sparking wires",
        verb="stop the sparks",
        gerund="stopping the sparks",
        rush="race toward the wires",
        mess="spark",
        harm="they could start a bigger fire",
        intensity=3,
        keyword="sparks",
        tags={"heat", "safety"},
    ),
    "sirens": Trouble(
        id="sirens",
        label="a siren jammer",
        verb="shut off the jammer",
        gerund="shutting off the jammer",
        rush="run to the control box",
        mess="noise",
        harm="it could make everyone panic and miss real danger",
        intensity=2,
        keyword="sirens",
        tags={"sound", "noise"},
    ),
}

TOOLS = {
    "shield": Tool(
        id="shield",
        label="a city shield",
        phrase="a shiny city shield",
        protects_from={"buzz", "spark", "noise"},
        solves={"drone", "sparks", "sirens"},
        prep="raise the city shield and move carefully",
        tail="raised the city shield until the danger fizzled out",
    ),
    "net": Tool(
        id="net",
        label="a web net",
        phrase="a flexible web net",
        protects_from={"buzz"},
        solves={"drone"},
        prep="throw the web net at the drone",
        tail="snagged the drone in the web net",
    ),
    "mask": Tool(
        id="mask",
        label="a smoke mask",
        phrase="a light smoke mask",
        protects_from={"smoke"},
        solves={"smoke"},
        prep="put on the smoke mask and breathe slowly",
        tail="wore the smoke mask until the air cleared",
    ),
    "gloves": Tool(
        id="gloves",
        label="spark gloves",
        phrase="spark-proof gloves",
        protects_from={"spark"},
        solves={"sparks"},
        prep="pull on the spark gloves and handle the wires",
        tail="used the spark gloves to calm the wires down",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Ava", "Lina", "Ivy", "Ruby", "Zoe"]
BOY_NAMES = ["Eli", "Finn", "Theo", "Noah", "Milo", "Ben", "Jules"]
SIDEKICKS = ["little brother", "little sister", "robot buddy", "best friend"]
TRAITS = ["brave", "kind", "quick", "curious", "steady"]

CURATED = [
    StoryParams(place="city", trouble="drone", tool="net", name="Maya", gender="girl", sidekick="robot buddy"),
    StoryParams(place="lab", trouble="sparks", tool="gloves", name="Theo", gender="boy", sidekick="best friend"),
    StoryParams(place="dock", trouble="smoke", tool="mask", name="Nina", gender="girl", sidekick="little brother"),
    StoryParams(place="rooftop", trouble="sirens", tool="shield", name="Eli", gender="boy", sidekick="little sister"),
]


class WorldError(StoryError):
    pass


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for tid in place.affords:
            for tool_id, tool in TOOLS.items():
                if tid in tool.solves:
                    out.append((pid, tid, tool_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: Deuce, havoc, and a brave inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def explain_rejection(trouble: Trouble, tool: Tool) -> str:
    return f"(No story: {tool.label} does not honestly solve {trouble.label}. The hero needs a tool that can really handle the havoc.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.tool:
        tr = TROUBLES[args.trouble]
        tl = TOOLS[args.tool]
        if args.trouble not in tl.solves:
            raise StoryError(explain_rejection(tr, tl))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, trouble=trouble, tool=tool, name=name, gender=gender, sidekick=sidekick)


def _inner_monologue(hero: Entity, trouble: Trouble) -> list[str]:
    return [
        f"{hero.pronoun('subject').capitalize()} took one breath and thought, \"I can do this.\"",
        f"\"Stay calm,\" {hero.pronoun('subject')} told themself. \"Look, listen, then act.\"",
        f"\"I am not going to let the havoc win,\" {hero.pronoun('subject')} thought.",
    ]


def tell(place: Place, trouble: Trouble, tool: Tool, name: str, gender: str, sidekick: str) -> World:
    world = World(place)
    world.trouble = trouble
    world.tool = tool

    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    ally = world.add(Entity(id="ally", kind="character", type="child", label=sidekick))
    villain = world.add(Entity(id="deuce", kind="character", type="child", label="Deuce"))

    hero.memes["duty"] = 1
    hero.memes["worry"] = 0
    hero.memes["courage"] = 0
    villain.memes["mischief"] = 1
    villain.meters["havoc"] = 0

    world.say(f"{name} was a small superhero who loved helping in {place.label}.")
    world.say(f"{name} had a {sidekick} who always stayed close when the city got noisy.")
    world.say(f"One afternoon, Deuce started trouble with {trouble.label}, and soon the whole place was in havoc.")
    world.para()
    world.say(f"{name} looked up, and {name} heard a little inner monologue in {name}'s own head.")
    for line in _inner_monologue(hero, trouble):
        world.say(line)
    world.say(f"{name} knew that {trouble.harm}.")
    world.para()
    world.say(f"{name} chose {tool.phrase}.")
    world.say(f"{tool.prep.capitalize()}, {name} stepped forward while {sidekick} watched with wide eyes.")
    world.say(f"Deuce tried to keep the havoc going, but {name} used {tool.tail}.")
    world.say(f"Again and again, {name} said, \"Calm hands, calm heart, calm hands, calm heart.\"")
    world.say(f"That steady repetition made {name} stronger, and the trouble finally stopped.")
    world.say(f"In the end, {place.label} was quiet again, Deuce backed away, and {name} stood tall like a true hero.")

    hero.memes["worry"] += 1
    hero.memes["courage"] += 2
    villain.meters["havoc"] += trouble.intensity
    world.facts = {
        "hero": hero,
        "ally": ally,
        "villain": villain,
        "trouble": trouble,
        "tool": tool,
        "place": place,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story for a child named {f['hero'].id} who stops Deuce from causing havoc.",
        f"Tell a gentle action story where {f['hero'].id} uses inner monologue and repetition to handle {f['trouble'].label}.",
        f"Write a simple superhero story that includes Deuce, havoc, and a brave helper at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    tool = f["tool"]
    place = f["place"]
    ally = f["ally"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small superhero who helped keep {place.label} safe.",
        ),
        QAItem(
            question=f"What caused the havoc?",
            answer=f"Deuce caused the havoc by starting {trouble.label} in {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to stop the trouble?",
            answer=f"{hero.id} used {tool.phrase} to stop it.",
        ),
        QAItem(
            question=f"Who stayed close to {hero.id} during the problem?",
            answer=f"{ally.label} stayed close and watched the hero work.",
        ),
        QAItem(
            question=f"How did {hero.id} get brave?",
            answer="The hero used an inner monologue and repeated a calm line to stay steady and act.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is havoc?",
            answer="Havoc is a lot of confusion and damage, like when trouble spreads and makes a place feel unsafe.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice inside your head that helps you think things through.",
        ),
        QAItem(
            question="Why can repetition help a hero?",
            answer="Repetition can help a hero stay calm and remember the plan when something scary is happening.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(Tr, Tl) :- trouble(Tr), tool(Tl), solves(Tl, Tr).
valid_story(P, Tr, Tl) :- place(P), affords(P, Tr), at_risk(Tr, Tl).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tags", tid, tag))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for tr in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, tr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TROUBLES[params.trouble], TOOLS[params.tool], params.name, params.gender, params.sidekick)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, trouble, tool) combos:")
        for row in triples:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
