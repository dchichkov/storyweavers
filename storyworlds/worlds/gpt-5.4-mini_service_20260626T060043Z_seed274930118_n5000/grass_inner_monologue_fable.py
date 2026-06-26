#!/usr/bin/env python3
"""
storyworlds/worlds/grass_inner_monologue_fable.py
=================================================

A small fable-style storyworld about a patch of grass, a careful animal, and
the thoughts that help them choose a kinder path.

Premise:
- A little field has tall grass that shelters small creatures.
- A character notices the grass, wants something simple, and begins to worry.
- Inner monologue reveals what the character knows and fears.
- A gentle turn leads to a wiser choice and a clear ending image.

The simulation uses physical meters and emotional memes:
- grass height, dryness, and shelter are physical state
- worry, patience, kindness, and relief are emotional state

The story is told in a fable voice, with a short moral at the end.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "hare", "rabbit", "fox", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    use: str
    guards: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
        import copy

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


PLACES = {
    "meadow": Place(name="the meadow", affords={"rest", "listen", "cross"}),
    "lane": Place(name="the lane", affords={"cross", "sweep"}),
    "garden": Place(name="the garden", affords={"rest", "listen", "cut"}),
}

ACTIONS = {
    "sleep": {
        "verb": "sleep in the grass",
        "inner": "stay hidden in the grass a little longer",
        "risk": "flattened",
        "change": "the grass would lose its shelter",
        "need": "quiet",
        "moral": "slow steps protect small lives",
    },
    "cut": {
        "verb": "cut the grass",
        "inner": "make the field tidy",
        "risk": "short",
        "change": "the grass would be cut too soon",
        "need": "care",
        "moral": "kindness notices what haste misses",
    },
    "cross": {
        "verb": "cross through the grass",
        "inner": "walk carefully through the meadow",
        "risk": "bent",
        "change": "the grass would bend under hurried feet",
        "need": "patience",
        "moral": "gentle feet leave gentler paths",
    },
}

TOOLS = {
    "scythe": Tool(id="scythe", label="a scythe", action="cut", use="cut the grass in one wide sweep", guards={"short"}),
    "basket": Tool(id="basket", label="a basket", action="sleep", use="carry away a few clippings by hand", guards={"flattened"}),
    "stick": Tool(id="stick", label="a walking stick", action="cross", use="part the grass slowly and look first", guards={"bent"}),
}

NAMES = ["Pip", "Milo", "Tia", "Nell", "Bram", "Luma", "Otto", "Kira"]
ACTIONS_ORDER = ["sleep", "cut", "cross"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about grass and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
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


def reasonableness_gate(place: str, action: str, tool: str) -> bool:
    p = PLACES[place]
    a = ACTIONS[action]
    t = TOOLS[tool]
    return action in p.affords and tool in TOOLS and action == t.action and a["risk"] in t.guards


def explain_rejection(place: str, action: str, tool: str) -> str:
    return (
        f"(No story: {TOOLS[tool].label} does not reasonably fit {ACTIONS[action]['verb']} "
        f"in {PLACES[place].name}. The tool would not protect the grass from that change.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            for tool in TOOLS:
                if reasonableness_gate(place, action, tool):
                    combos.append((place, action, tool))
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        action=action,
        tool=tool,
        name=args.name or rng.choice(NAMES),
    )


def _setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    grass = world.add(Entity(
        id="grass",
        kind="thing",
        type="grass",
        label="grass",
        meters={"height": 3.0, "shelter": 1.0, "dryness": 1.0},
        memes={"calm": 1.0},
    ))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="mouse",
        label=params.name,
        meters={"speed": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "kindness": 0.0, "relief": 0.0},
    ))
    tool = world.add(Entity(
        id=params.tool,
        kind="thing",
        type=params.tool,
        label=TOOLS[params.tool].label,
        owner=hero.id,
        meters={"ready": 1.0},
    ))
    world.facts.update(hero=hero, grass=grass, tool=tool, params=params)
    return world


def predict_change(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    grass = sim.get("grass")
    if params.action == "sleep":
        grass.meters["height"] -= 1.5
        grass.meters["shelter"] -= 1.0
        grass.memes["trouble"] = 1.0
    elif params.action == "cut":
        grass.meters["height"] -= 2.5
        grass.meters["shelter"] -= 1.0
        grass.memes["trouble"] = 1.0
    else:
        grass.meters["height"] -= 0.8
        grass.memes["trouble"] = 0.5
    return {
        "hurt": grass.meters["height"] < 1.5 or grass.meters["shelter"] < 0.5,
        "height": grass.meters["height"],
    }


def tell(world: World) -> None:
    hero = world.facts["hero"]
    grass = world.facts["grass"]
    params = world.facts["params"]
    act = ACTIONS[params.action]
    tool = TOOLS[params.tool]

    world.say(
        f"Long ago, in {world.place.name}, there was a little patch of grass that stood tall and green."
    )
    world.say(
        f"{hero.id} lived near it and often listened to the field as if it were whispering a lesson."
    )

    world.para()
    world.say(
        f"One morning, {hero.id} looked at the grass and thought, "
        f'"{act["inner"]}."'
    )
    hero.memes["curiosity"] += 1
    if params.action == "cut":
        hero.memes["worry"] += 1
        world.say(
            f"Still, {hero.id} noticed that the grass was home to tiny beetles and cool shade."
        )
    elif params.action == "sleep":
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} also knew that little creatures slept there, safe beneath the long blades."
        )
    else:
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} saw that the grass bent easily, and hurried feet could trouble it."
        )

    world.para()
    world.say(f"In {hero.id}'s mind, a soft thought answered: \"If I rush, the grass may be {act['risk']}.\"")
    world.say(f"The worry grew because {act['change']}.")
    world.say(
        f"So {hero.id} held still and took up {tool.label}, not to hurry, but to act with care."
    )

    if params.action == "cut":
        world.say(
            f"{hero.id} chose to {tool.use}, trimming only the edge and leaving the thick middle for later."
        )
        grass.meters["height"] -= 1.2
        grass.meters["shelter"] -= 0.4
        grass.meters["dryness"] -= 0.1
        hero.memes["kindness"] += 1
        hero.memes["worry"] -= 0.3
        hero.memes["relief"] += 1
        world.say(
            f"The field stayed useful, and the grass kept enough height for a cricket to hide beneath it."
        )
    elif params.action == "sleep":
        world.say(
            f"{hero.id} chose to {tool.use}, making a small, soft bed instead of flattening the whole patch."
        )
        grass.meters["height"] -= 0.6
        grass.meters["shelter"] -= 0.2
        hero.memes["kindness"] += 1
        hero.memes["relief"] += 1
        world.say(
            f"The grass stayed tall enough to shade the ground, and the sleeping place remained gentle."
        )
    else:
        world.say(
            f"{hero.id} chose to {tool.use}, parting the blades and stepping where the grass could spring back."
        )
        grass.meters["height"] -= 0.3
        grass.meters["shelter"] -= 0.1
        hero.memes["kindness"] += 1
        hero.memes["relief"] += 1
        world.say(
            f"The grass bent, then rose again, as if it were thanking the careful feet."
        )

    grass.meters["height"] = max(grass.meters["height"], 0.4)
    grass.meters["shelter"] = max(grass.meters["shelter"], 0.0)
    grass.meters["dryness"] = max(grass.meters["dryness"], 0.0)

    world.para()
    world.say(
        f"By evening, the grass still stood green, though a little changed, and {hero.id} had learned that care is a kind of strength."
    )
    world.say(f"The little field seemed to answer with the old truth of the fables: {act['moral']}.")

    world.facts["moral"] = act["moral"]
    world.facts["changed"] = params.action


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fable for a child about grass and a careful choice, with the word "grass".',
        f"Tell a gentle story in which {p.name} thinks quietly before acting in {world.place.name}.",
        f"Write a simple fable where inner thoughts help a small character protect the grass.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    grass = world.facts["grass"]
    return [
        QAItem(
            question=f"What did {p.name} think about before acting in {world.place.name}?",
            answer=(
                f"{p.name} thought about the grass and worried that rushing could leave it {ACTIONS[p.action]['risk']}. "
                f"That inner thought helped {p.name} choose a careful way."
            ),
        ),
        QAItem(
            question=f"How did {p.name} use {TOOLS[p.tool].label}?",
            answer=(
                f"{p.name} used {TOOLS[p.tool].label} to {TOOLS[p.tool].use}. "
                f"That kept the grass useful and safe."
            ),
        ),
        QAItem(
            question=f"What changed in the grass by the end?",
            answer=(
                f"The grass was still green, but its height changed to about {grass.meters['height']:.1f} meters in the story model. "
                f"It stayed tall enough to give shelter."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=(
                f"{hero.id} learned that kindness and patience can protect small things. "
                f"The story's moral says that {world.facts['moral']}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grass?",
            answer="Grass is a plant with thin green blades that grows in fields, gardens, and lawns.",
        ),
        QAItem(
            question="Why can grass help small animals?",
            answer="Tall grass can give small animals shade, hiding places, and a softer place to rest.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet voice a character hears in their own mind when they think about what to do.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v:.2f}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v:.2f}' for k, v in e.memes.items())}}}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
grass_ok(G) :- grass(G), height(G,H), H >= 1.
careful(A) :- action(A), not hasty(A).
protected(G) :- grass(G), careful(_), height(G,H), H >= 1.
valid_story(P,A,T) :- place(P), action(A), tool(T), fits(P,A,T), grass_ok(g), protected(g).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fits", "meadow", t.action, tid))
        lines.append(asp.fact("guards", tid, *sorted(t.guards)[0:1]) if t.guards else asp.fact("guards", tid, "none"))
    lines.append(asp.fact("grass", "g"))
    lines.append(asp.fact("height", "g", 3))
    lines.append(asp.fact("safe", "g"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="meadow", action="cut", tool="scythe", name="Pip"),
    StoryParams(place="meadow", action="cross", tool="stick", name="Milo"),
    StoryParams(place="garden", action="sleep", tool="basket", name="Tia"),
]


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell(world)
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.action} in {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
