#!/usr/bin/env python3
"""
A tiny storyworld for a ghostly quest in a vegetable garden.

Premise:
- A child enters a vegetable garden at dusk.
- A belligerent garden ghost blocks a simple quest: finding a lost silver key
  hidden near the beans.
- The child has a poker (a safe garden rake-hook) used to lift a stuck tin lid.
- The ghost is not evil; it is grumpy because the garden gate has been left open.
- The story resolves when the child helps close the gate and the ghost yields.

The world model tracks:
- Physical meters: chill, clutter, rustle, hinge, openness, hiddenness
- Emotional memes: fear, courage, belligerence, trust, relief, wonder

This file is standalone and follows the storyworld contract.
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

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "vegetable_garden": {
        "name": "the vegetable garden",
        "dusk_detail": "The bean poles leaned like tall shadows, and the tomato vines
seemed to hold their breath.",
    }
}

# Safe "poker" means a garden poker / hook used to lift things.
TOOLS = {
    "poker": {
        "label": "a garden poker",
        "phrase": "a long garden poker with a wooden handle",
        "use": "lift the stuck tin lid",
        "helps": {"hiddenness", "clutter"},
    }
}

QUESTS = {
    "lost_key": {
        "label": "the silver key",
        "goal": "find the silver key hidden near the bean row",
        "turn": "the key had slipped under an old tin lid",
        "reward": "open the little shed door",
    }
}

GHOSTS = {
    "belligerent": {
        "name": "the belligerent garden ghost",
        "type": "ghost",
        "mood": "belligerent",
        "cause": "the gate had been left open and the wind kept worrying the leaves",
    }
}

GARDEN_OBJECTS = {
    "gate": {
        "label": "the garden gate",
        "region": "edge",
    },
    "tin_lid": {
        "label": "an old tin lid",
        "region": "beans",
    },
    "beans": {
        "label": "the bean row",
        "region": "center",
    },
    "key": {
        "label": "the silver key",
        "region": "beans",
    },
    "shed": {
        "label": "the little shed",
        "region": "back",
    },
}

NAMES = ["Mina", "Theo", "Nell", "Arlo", "June", "Iris"]
TRAITS = ["curious", "brave", "gentle", "stubborn", "quiet", "lively"]

ASP_RULES = r"""
% A quest is valid when the tool can help with the key's obstruction and the
% garden setting supports the ghost story premise.
quest_valid(Location, Quest, Tool) :-
    setting(Location),
    quest(Quest),
    tool(Tool),
    quest_in(Quest, Location),
    helps(Tool, hiddenness),
    helps(Tool, clutter).

% A ghost is belligerent when the gate is open and the wind stirs the garden.
ghost_belligerent(G) :- ghost(G), mood(G, belligerent), gate_open.
"""

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""

    def __post_init__(self):
        for k in ["chill", "clutter", "rustle", "hinge", "openness", "hiddenness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "courage", "belligerence", "trust", "relief", "wonder", "resolve"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.gate_open: bool = True
        self.dusk: bool = True

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.gate_open = self.gate_open
        w.dusk = self.dusk
        return w


# ---------------------------------------------------------------------------
# Reasonable-story gate
# ---------------------------------------------------------------------------

def tool_is_reasonable(tool_id: str, quest_id: str, place: str) -> bool:
    return tool_id == "poker" and quest_id == "lost_key" and place == "vegetable_garden"


def explain_rejection(tool_id: str, quest_id: str, place: str) -> str:
    return (
        f"(No story: this seed asks for a ghostly quest in {place}, but "
        f"{tool_id!r} cannot reasonably solve {quest_id!r} there.)"
    )


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        # Gate open keeps the ghost belligerent.
        ghost = world.get("ghost")
        gate = world.get("gate")
        if world.gate_open and ("belligerence", "gate") not in world.fired:
            world.fired.add(("belligerence", "gate"))
            ghost.memes["belligerence"] += 1
            ghost.meters["rustle"] += 1
            if narrate:
                world.say("The ghost grew more belligerent as the open gate kept creaking in the wind.")
            changed = True

        # Pocketing courage lowers fear.
        child = world.get("child")
        if child.memes["courage"] >= 1 and child.memes["fear"] > 0 and ("fear_down", "courage") not in world.fired:
            world.fired.add(("fear_down", "courage"))
            child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
            child.memes["resolve"] += 1
            if narrate:
                world.say("The child's courage settled the shiver in their chest.")
            changed = True

        # Fixing the gate reduces belligerence and increases trust.
        if not world.gate_open and ghost.memes["belligerence"] > 0 and ("trust_up", "gate_closed") not in world.fired:
            world.fired.add(("trust_up", "gate_closed"))
            ghost.memes["belligerence"] = max(0.0, ghost.memes["belligerence"] - 1)
            ghost.memes["trust"] += 1
            ghost.meters["rustle"] = max(0.0, ghost.meters["rustle"] - 1)
            if narrate:
                world.say("With the gate latched, the ghost stopped rattling the leaves.")
            changed = True


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def _intro(world: World, child: Entity, ghost: Entity, tool: Entity, quest: Entity) -> None:
    world.say(
        f"{child.id} came to {world.place} at dusk with {tool.label} in hand, hoping to begin a quest."
    )
    world.say(
        f"At the far end of the rows stood {ghost.label}, a {ghost.mood} ghost with a voice like a dry leaf."
    )
    world.say(
        f"It blocked the way to {quest.label}, even though the prize was only {quest.phrase}."
    )

def _quest_turn(world: World, child: Entity, quest: Entity, tool: Entity) -> None:
    child.memes["wonder"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{child.id} wanted to {quest.facts['goal'] if 'goal' in quest.__dict__ else 'find the silver key'}."
    )
    world.say(
        f"But the ghost pointed a thin finger at the old tin lid and said the key was trapped beneath it."
    )
    world.say(
        f"{child.id} held up {tool.label} and thought of how to {TOOLS['poker']['use']}."
    )

def _challenge(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    child.memes["courage"] += 1
    child.memes["resolve"] += 1
    world.say(
        f"The ghost was belligerent and would not step aside, so {child.id} had to be careful."
    )
    world.say(
        f"{child.id} used {tool.label} to lift the tin lid without poking the roots nearby."
    )
    world.get("key").meters["hiddenness"] = 0.0
    world.get("key").held_by = child.id

def _resolution(world: World, child: Entity, ghost: Entity) -> None:
    world.para()
    world.say(
        f"Then {child.id} saw the real problem: the garden gate was open."
    )
    world.say(
        f"{child.id} walked over and latched it shut, and the belligerent ghost quieted down at once."
    )
    world.gate_open = False
    propagate(world)
    child.memes["relief"] += 1
    ghost.memes["trust"] += 1
    world.say(
        f"After that, {child.id} found the silver key, and the ghost let the quest end in peace."
    )
    world.say(
        f"The bean leaves stopped trembling, and the little shed waited with its door ready to be opened."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def build_world(params: "StoryParams") -> World:
    if params.place != "vegetable_garden":
        raise StoryError("This world only supports a vegetable garden setting.")
    if params.quest != "lost_key" or params.tool != "poker":
        raise StoryError(explain_rejection(params.tool, params.quest, params.place))

    world = World(LOCATIONS[params.place]["name"])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label=GHOSTS[params.ghost]["name"],
        phrase=GHOSTS[params.ghost]["name"],
    ))
    tool = world.add(Entity(
        id="poker",
        kind="thing",
        type="tool",
        label=TOOLS["poker"]["label"],
        phrase=TOOLS["poker"]["phrase"],
        owner=child.id,
        held_by=child.id,
    ))
    quest = world.add(Entity(
        id="quest",
        kind="thing",
        type="quest",
        label="the silver key quest",
        phrase="the silver key hidden near the bean row",
        location="vegetable_garden",
    ))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="the garden gate"))
    key = world.add(Entity(id="key", kind="thing", type="key", label="the silver key", held_by=None))
    lid = world.add(Entity(id="tin_lid", kind="thing", type="lid", label="an old tin lid", location="beans"))
    beans = world.add(Entity(id="beans", kind="thing", type="plants", label="the bean row"))
    shed = world.add(Entity(id="shed", kind="thing", type="shed", label="the little shed"))

    child.memes["fear"] = 1
    ghost.memes["belligerence"] = 1
    key.meters["hiddenness"] = 1
    gate.meters["openness"] = 1
    lid.meters["clutter"] = 1

    world.facts.update(
        child=child,
        ghost=ghost,
        tool=tool,
        quest=quest,
        gate=gate,
        key=key,
        lid=lid,
        beans=beans,
        shed=shed,
        place=params.place,
        name=params.name,
        gender=params.gender,
        trait=params.trait,
        ghost_kind=params.ghost,
        quest_kind=params.quest,
        tool_kind=params.tool,
    )

    world.say(
        f"{LOCATIONS[params.place]['dusk_detail']}"
    )
    world.say(
        f"{child.id} was a {params.trait} {params.gender} who loved small mysteries."
    )
    world.say(
        f"They had come with {tool.label} for a quest, because the silver key could open the little shed."
    )
    world.para()
    _intro(world, child, ghost, tool, quest)
    world.para()
    _quest_turn(world, child, quest, tool)
    propagate(world)
    _challenge(world, child, ghost, tool)
    propagate(world)
    _resolution(world, child, ghost)
    return world


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    tool: str
    ghost: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="vegetable_garden",
        quest="lost_key",
        tool="poker",
        ghost="belligerent",
        name="Mina",
        gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="vegetable_garden",
        quest="lost_key",
        tool="poker",
        ghost="belligerent",
        name="Theo",
        gender="boy",
        trait="brave",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghostly quest in a vegetable garden.")
    ap.add_argument("--place", choices=["vegetable_garden"], default="vegetable_garden")
    ap.add_argument("--quest", choices=["lost_key"], default="lost_key")
    ap.add_argument("--tool", choices=["poker"], default="poker")
    ap.add_argument("--ghost", choices=["belligerent"], default="belligerent")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place != "vegetable_garden":
        raise StoryError("Only the vegetable garden is available in this world.")
    if args.quest != "lost_key" or args.tool != "poker":
        raise StoryError(explain_rejection(args.tool, args.quest, args.place))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="vegetable_garden",
        quest="lost_key",
        tool="poker",
        ghost="belligerent",
        name=name,
        gender=gender,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story set in {f["place"].replace("_", " ")} with a small quest and a belligerent ghost.',
        f'Tell a child-friendly story about {f["name"]} carrying a poker through a vegetable garden at dusk.',
        "Write a short story where a grumpy garden ghost blocks a quest, then softens when the gate is closed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    tool = f["tool"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who went into the vegetable garden with the garden poker?",
            answer=f"{child.id} went into the vegetable garden with {tool.label}.",
        ),
        QAItem(
            question="Why was the ghost belligerent?",
            answer="The ghost was belligerent because the garden gate had been left open and the wind kept worrying the leaves.",
        ),
        QAItem(
            question="What was the quest?",
            answer="The quest was to find the silver key hidden near the bean row and use it to open the little shed door.",
        ),
        QAItem(
            question="How did the child solve the problem?",
            answer="The child used the poker to lift the stuck tin lid, then closed the gate so the ghost could settle down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow vegetables like beans, tomatoes, and other plants to eat later.",
        ),
        QAItem(
            question="What is a poker?",
            answer="A poker is a long tool with a handle, and in this story it is used carefully to lift something stuck.",
        ),
        QAItem(
            question="What does belligerent mean?",
            answer="Belligerent means angry and ready to argue or block the way.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a task or search with a clear goal, like finding something lost or helping someone.",
        ),
        QAItem(
            question="Why do ghosts feel spooky in stories?",
            answer="Ghosts feel spooky because they are quiet, pale, and mysterious, which makes a scene feel strange and magical.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.held_by:
            parts.append(f"held_by={e.held_by}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(parts)}")
    lines.append(f"  gate_open={world.gate_open}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "vegetable_garden"),
        asp.fact("quest", "lost_key"),
        asp.fact("quest_in", "lost_key", "vegetable_garden"),
        asp.fact("tool", "poker"),
        asp.fact("helps", "poker", "hiddenness"),
        asp.fact("helps", "poker", "clutter"),
        asp.fact("ghost", "belligerent"),
        asp.fact("mood", "belligerent", "belligerent"),
        asp.fact("gate_open"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    py = [("vegetable_garden", "lost_key", "poker")] if tool_is_reasonable("poker", "lost_key", "vegetable_garden") else []
    cl = asp_valid()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches python gate ({len(cl)} valid combo).")
        return 0
    print("MISMATCH between clingo and python gate")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid quest/tool/place combinations:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
