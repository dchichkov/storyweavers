#!/usr/bin/env python3
"""
A standalone story world for a small mystery about a rigorous search, a turbo
machine, and a gruesome transformation solved through teamwork.

Premise:
A child notices that something in the workshop is changing things in a strange
way. The clues are muddy, the timing is odd, and the only way to understand the
problem is to inspect the scene carefully, ask good questions, and work together
with a helper.

The story arc stays close to mystery:
- setup: an unusual find and a careful search
- tension: clues point to a risky transformation
- turn: the team discovers what the turbo machine is doing
- resolution: they stop the strange process and put things right
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


# ---------------------------------------------------------------------------
# World vocabulary
# ---------------------------------------------------------------------------
LOCATIONS = {
    "workshop": {
        "label": "the workshop",
        "affords": {"inspect", "repair", "activate"},
        "indoors": True,
    },
    "shed": {
        "label": "the shed",
        "affords": {"inspect", "repair", "activate"},
        "indoors": True,
    },
    "attic": {
        "label": "the attic",
        "affords": {"inspect", "repair"},
        "indoors": True,
    },
}

TOOLS = {
    "magnifier": {
        "label": "magnifying glass",
        "kind": "tool",
        "for": {"inspect"},
        "protects": set(),
    },
    "gloves": {
        "label": "gloves",
        "kind": "gear",
        "for": {"repair", "activate"},
        "protects": {"slime", "dust"},
    },
    "cloth": {
        "label": "cloth",
        "kind": "gear",
        "for": {"repair"},
        "protects": {"slime"},
    },
    "mask": {
        "label": "mask",
        "kind": "gear",
        "for": {"activate"},
        "protects": {"smell"},
    },
}

MYSTERY_OBJECTS = {
    "toy": {
        "label": "toy robot",
        "region": "table",
        "transform": "stretchy",
        "mess": "slime",
        "clue": "a little screw cap",
    },
    "plant": {
        "label": "potted plant",
        "region": "shelf",
        "transform": "wobbly",
        "mess": "dust",
        "clue": "a green spark mark",
    },
    "cookie": {
        "label": "cookie tray",
        "region": "counter",
        "transform": "squishy",
        "mess": "smell",
        "clue": "sticky crumbs",
    },
}

NAMES = ["Mira", "Nico", "Tessa", "Owen", "Lina", "Arlo", "June", "Pia"]
HELPER_NAMES = ["Aunt Bee", "Dad", "Grandma", "Mr. Vale", "Ms. Reed"]
TRAITS = ["rigorous", "careful", "curious", "brave", "patient"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    location: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: dict) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy

        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _inc(d: dict[str, float], key: str, amount: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amount


def _has(d: dict[str, float], key: str, threshold: float = 1.0) -> bool:
    return d.get(key, 0.0) >= threshold


def _make_mystery_signal(obj: Entity) -> str:
    if obj.type == "toy robot":
        return "the robot had gone stretchy and left slime on the table"
    if obj.type == "potted plant":
        return "the plant had turned wobbly and sprinkled dust on the shelf"
    return "the tray had turned squishy and filled the room with a strange smell"


def _place_sentence(location: str) -> str:
    return {
        "workshop": "The workshop was neat at first, with jars in a row and a little bench by the wall.",
        "shed": "The shed was dim and quiet, with a dusty floor and one bright lamp.",
        "attic": "The attic was small and warm, with boxes stacked under the roof beams.",
    }[location]


def _hero_sentence(hero: Entity, trait: str) -> str:
    return f"{hero.id} was a {trait} little {hero.type} who liked solving puzzles by looking closely."


def _helper_sentence(helper: Entity) -> str:
    return f"{helper.id} was the kind of grown-up who noticed clues and helped without rushing."


def _do_inspect(world: World, hero: Entity, obj: Entity) -> None:
    _inc(hero.memes, "focus")
    hero.meters["care"] = hero.meters.get("care", 0.0) + 1.0
    world.say(
        f"{hero.id} took a rigorous look at the {obj.label} and found {obj.label.split()[0]} "
        f"clues everywhere."
    )


def _do_warn(world: World, helper: Entity, hero: Entity, obj: Entity) -> None:
    _inc(helper.memes, "concern")
    world.say(
        f"{helper.id} leaned in and whispered, \"This feels like a mystery, and something turbo is making it worse.\""
    )
    world.say(
        f"On the bench, they saw {obj.label} showing a gruesome transformation: {_make_mystery_signal(obj)}."
    )


def _do_teamwork(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    _inc(hero.memes, "trust")
    _inc(helper.memes, "trust")
    _inc(hero.memes, "joy")
    _inc(helper.memes, "joy")
    world.say(
        f"{hero.id} and {helper.id} worked as a team, one watching the clues and the other reaching for the right tools."
    )
    world.say(
        f"Together they found the tiny turbo switch hidden behind the {obj.label}."
    )


def _do_fix(world: World, hero: Entity, helper: Entity, obj: Entity, tool_a: Entity, tool_b: Entity) -> None:
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 0.0
    obj.meters["transformed"] = 0.0
    obj.meters["safe"] = 1.0
    _inc(hero.memes, "relief")
    _inc(helper.memes, "relief")
    world.say(
        f"{helper.id} used {tool_a.label} while {hero.id} held the {obj.label} steady."
    )
    world.say(
        f"Then {hero.id} used {tool_b.label} to shut the turbo switch off, and the strange change stopped at once."
    )
    world.say(
        f"The {obj.label} settled back to normal, and the room felt calm again."
    )


def tell_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    obj_cfg = MYSTERY_OBJECTS[params.mystery]
    obj = world.add(Entity(id="mystery", type=obj_cfg["label"], label=obj_cfg["label"], region=obj_cfg["region"]))
    obj.meters["transformed"] = 1.0
    obj.meters["mess"] = 1.0
    obj.memes["odd"] = 1.0

    world.say(_hero_sentence(hero, params.trait))
    world.say(_place_sentence(params.location))
    world.say(
        f"One afternoon, {hero.id} noticed that {obj.label} in {world.location['label']} looked wrong."
    )
    world.say(
        f"{hero.id} saw {obj_cfg['clue']} near it, which made the problem feel even stranger."
    )
    world.para()

    _do_inspect(world, hero, obj)
    _do_warn(world, helper, hero, obj)
    world.para()

    _do_teamwork(world, hero, helper, obj)
    tool_a = world.add(Entity(id="gloves", kind="thing", type="gear", label=TOOLS["gloves"]["label"]))
    tool_b = world.add(Entity(id="magnifier", kind="thing", type="tool", label=TOOLS["magnifier"]["label"]))
    _do_fix(world, hero, helper, obj, tool_a, tool_b)

    world.facts.update(hero=hero, helper=helper, obj=obj, params=params, location=params.location)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    return [
        f'Write a short mystery story for a child about {hero.id} solving a strange change in a {obj.label}.',
        f"Tell a rigorous, child-friendly mystery where {hero.id} and a helper use teamwork to stop a turbo machine.",
        f'Write a story that includes the words "rigorous", "turbo", and "gruesome" without being scary for little kids.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    params = f["params"]
    qa = [
        QAItem(
            question=f"What mystery did {hero.id} notice in {world.location['label']}?",
            answer=f"{hero.id} noticed that the {obj.label} had changed in a strange way, so the room felt like a puzzle that needed solving.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem together?",
            answer=f"They used teamwork: {helper.id} helped with the tools while {hero.id} held the {obj.label} steady and watched for clues.",
        ),
        QAItem(
            question=f"What made the change seem gruesome at first?",
            answer=f"It seemed gruesome because the {obj.label} looked twisted and messy, with a strange leftover clue beside it.",
        ),
        QAItem(
            question=f"What finally stopped the turbo trouble?",
            answer=f"They found the hidden turbo switch and shut it off, which stopped the strange transformation and made the {obj.label} normal again.",
        ),
    ]
    if params.trait == "rigorous":
        qa.append(
            QAItem(
                question=f"Why was {hero.id} careful about the clues?",
                answer=f"{hero.id} was careful because a mystery makes more sense when you check every clue and do not guess too soon.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something strange or unknown that people try to figure out by looking for clues.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help one another to get something done.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or looks very different from before.",
        )
    ],
    "turbo": [
        QAItem(
            question="What does turbo usually mean?",
            answer="Turbo usually means fast or extra powerful, like something that works with a lot of speed.",
        )
    ],
    "rigorous": [
        QAItem(
            question="What does rigorous mean?",
            answer="Rigorous means very careful, thorough, and done with great attention to detail.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["params"].mystery for _ in [0])
    tags.update({"mystery", "teamwork", "transformation", "turbo", "rigorous"})
    for tag in ("mystery", "teamwork", "transformation", "turbo", "rigorous"):
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc["indoors"]:
            lines.append(asp.fact("indoors", loc_id))
        for a in sorted(loc["affords"]):
            lines.append(asp.fact("affords", loc_id, a))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for a in sorted(tool["for"]):
            lines.append(asp.fact("usable_for", tool_id, a))
        for p in sorted(tool["protects"]):
            lines.append(asp.fact("protects", tool_id, p))
    for obj_id, obj in MYSTERY_OBJECTS.items():
        lines.append(asp.fact("mystery_object", obj_id))
        lines.append(asp.fact("transform", obj_id, obj["transform"]))
        lines.append(asp.fact("mess", obj_id, obj["mess"]))
    return "\n".join(lines)


ASP_RULES = r"""
% A location is suitable when it affords the action.
suitable(L, A) :- affords(L, A).

% Teamwork is required when the object has transformed and there is a mess clue.
needs_teamwork(O) :- transform(O, _), mess(O, _).

% A fix is possible if one tool can inspect and another can stop the activation.
has_fix(O) :- tool(T1), usable_for(T1, inspect), tool(T2), usable_for(T2, repair), O = O.

% Valid story: a mystery object at a suitable location with teamwork.
valid_story(L, O) :- suitable(L, inspect), mystery_object(O), needs_teamwork(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp

    py = {(loc, obj_id) for loc in LOCATIONS for obj_id in MYSTERY_OBJECTS}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: clingo parity matches Python ({len(py)} story shapes).")
        return 0
    print("MISMATCH between Python and ASP:")
    print("only in python:", sorted(py - clingo))
    print("only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with a gruesome transformation and teamwork."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--mystery", choices=MYSTERY_OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["woman", "man"])
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
    location = args.location or rng.choice(list(LOCATIONS))
    mystery = args.mystery or rng.choice(list(MYSTERY_OBJECTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES)
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    loc = LOCATIONS[location]
    if "inspect" not in loc["affords"]:
        raise StoryError("That location cannot support the careful inspection needed for a mystery.")
    return StoryParams(
        location=location,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(LOCATIONS[params.location])
    tell_story(world, params)
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
    StoryParams(location="workshop", mystery="toy", hero_name="Mira", hero_type="girl", helper_name="Dad", helper_type="man", trait="rigorous"),
    StoryParams(location="shed", mystery="plant", hero_name="Nico", hero_type="boy", helper_name="Aunt Bee", helper_type="woman", trait="curious"),
    StoryParams(location="attic", mystery="cookie", hero_name="Tessa", hero_type="girl", helper_name="Grandma", helper_type="woman", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story shapes:\n")
        for loc, obj in stories:
            print(f"  {loc:9} {obj}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
