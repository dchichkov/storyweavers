#!/usr/bin/env python3
"""
A small storyworld about a studious child, a magical garden, and a kind
lesson about care, patience, and growth.

The world is built from one seed-like premise:
a careful child learns that manure can be useful in a garden when used
thoughtfully, and that being receptive to advice helps everyone.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- eager results import, lazy asp import in ASP helpers
- physical meters and emotional memes in the world model
- inline ASP twin plus a Python reasonableness gate
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
# World model
# ---------------------------------------------------------------------------
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    reward: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    owner_kind: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather = ""

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.weather = self.weather
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", kind="garden", affords={"feed", "read"}, mood="gentle"),
    "greenhouse": Setting(place="the greenhouse", kind="greenhouse", affords={"feed", "read"}, mood="warm"),
    "farmyard": Setting(place="the farmyard", kind="farmyard", affords={"feed"}, mood="busy"),
}

ACTIVITIES = {
    "feed": Activity(
        id="feed",
        verb="feed the garden",
        gerund="feeding the garden",
        rush="run to the compost pile",
        risk="the seedlings might stay weak",
        reward="the soil could grow rich and ready",
        weather="",
        keyword="manure",
        tags={"manure", "soil", "care"},
    ),
    "read": Activity(
        id="read",
        verb="read by the bean rows",
        gerund="reading under the trellis",
        rush="hurry to the bench with the book",
        risk="the lesson could be missed",
        reward="the child might learn a wise way to help",
        weather="",
        keyword="studious",
        tags={"book", "lesson", "care"},
    ),
}

GIFTS = {
    "seeds": Gift(id="seeds", label="seed packet", phrase="a small packet of bean seeds", owner_kind="child", plural=False),
    "journal": Gift(id="journal", label="garden journal", phrase="a neat little garden journal", owner_kind="child", plural=False),
}

TOOLS = [
    Tool(
        id="fork",
        label="a little pitchfork",
        prep="put on gloves and use a little pitchfork first",
        tail="worked the compost in gently",
        helps={"feed"},
    ),
    Tool(
        id="watering_can",
        label="a blue watering can",
        prep="water the soil first",
        tail="poured water over the dark soil",
        helps={"feed"},
    ),
    Tool(
        id="bookmark",
        label="a ribbon bookmark",
        prep="mark the page first",
        tail="kept their place in the book",
        helps={"read"},
    ),
]

CHILD_NAMES = ["Mina", "Luca", "Iris", "Noah", "Sage", "Ada", "Rory", "Nia"]
PARENT_NAMES = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["studious", "receptive", "gentle", "kind", "patient"]

MORAL_VALUE = "care"


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, activity: str, gift: str) -> bool:
    act = ACTIVITIES[activity]
    if activity == "feed" and gift != "seeds":
        return False
    if activity == "read" and gift != "journal":
        return False
    if place not in SETTINGS:
        return False
    return activity in SETTINGS[place].affords


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for gift in GIFTS:
                if valid_combo(place, act, gift):
                    out.append((place, act, gift))
    return out


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    sig = ("activity", actor.id, activity.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if activity.id == "feed":
        actor.meters["care"] = actor.meters.get("care", 0.0) + 1
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        world.facts["soil_rich"] = True
        world.say("The dark soil drank in the help and began to look rich and soft.")
    elif activity.id == "read":
        actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1
        actor.memes["receptive"] = actor.memes.get("receptive", 0.0) + 1
        world.say("The child listened closely, and the page seemed to glow with a quiet idea.")


def propagate(world: World, narrate: bool = True) -> None:
    if world.facts.get("soil_rich") and not world.facts.get("magic_bloom"):
        world.facts["magic_bloom"] = True
        world.say("Then the little magic in the garden woke up and the bean shoots lifted their heads.")
    if world.facts.get("magic_bloom") and not world.facts.get("heartwarming_end"):
        world.facts["heartwarming_end"] = True
        world.say("The family smiled together, glad the child had chosen a caring way to help.")


def tell(setting: Setting, activity: Activity, gift: Gift, name: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", traits=["little", trait, "studious", "receptive"]))
    grownup = world.add(Entity(id=parent, kind="character", type=parent, label=parent))
    item = world.add(Entity(
        id=gift.id,
        kind="thing",
        type=gift.label,
        label=gift.label,
        phrase=gift.phrase,
        owner=child.id,
        caretaker=grownup.id,
        plural=gift.plural,
    ))
    world.weather = "sunny"

    world.say(f"{child.id} was a little {trait} child who loved quiet books and tiny garden jobs.")
    world.say(f"{child.id} kept a {gift.phrase} close, because {child.pronoun('possessive')} {gift.label} made the work feel important.")
    world.say(f"One day in {setting.place}, {child.id} wanted to {activity.verb}.")
    world.say(f"{child.id} liked the way {activity.gerund} could help the little plants grow.")

    world.para()
    world.say(f"But the garden was still tired, and {activity.risk}.")
    world.say(f"{child.pronoun('possessive').capitalize()} {parent} noticed and said, \"A wise garden needs care, not hurry.\"")
    world.say(f"{child.id} was receptive to the idea and paused to listen.")
    world.say(f"Instead of rushing, {child.id} reached for the compost and chose to use manure kindly and carefully.")

    _do_activity(world, child, activity)
    propagate(world)

    world.para()
    if activity.id == "feed":
        world.say(f"{child.id} used {TOOLS[0].label} and {TOOLS[1].label} to mix the rich manure into the soil.")
        world.say(f"After that, the beans stood taller, and the garden looked as if it had remembered how to smile.")
    else:
        world.say(f"{child.id} marked the page with {TOOLS[2].label} and promised to come back after helping outside.")
        world.say(f"That way, the lesson stayed in mind and the garden still got what it needed.")

    world.say(f"In the end, the child felt proud not because the work was flashy, but because it was good.")
    world.say(f"The whole garden seemed warmer for it.")
    world.facts.update(
        child=child,
        parent=grownup,
        gift=item,
        activity=activity,
        setting=setting,
        trait=trait,
        moral=MORAL_VALUE,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(Place, A, G) :- place(Place), activity(A), gift(G), valid(Place, A, G).
valid(Place, feed, seeds) :- place(Place), affords(Place, feed).
valid(Place, read, journal) :- place(Place), affords(Place, read).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("place", key))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", key, act))
    for act in ACTIVITIES:
        lines.append(asp.fact("activity", act))
    for gift in GIFTS:
        lines.append(asp.fact("gift", gift))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    gift: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about manure, study, and receptive care.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--gift", choices=GIFTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, gift = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, gift=gift, name=name, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story for a child about "{f["activity"].keyword}" and a kind lesson.',
        f"Tell a gentle story about {f['child'].id}, a {f['trait']} child who is receptive to advice in {f['setting'].place}.",
        f"Write a simple story where manure helps a garden grow and the moral value is care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    act = f["activity"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where does {child.id} learn to help the garden?",
            answer=f"{child.id} learns in {setting.place}, where the child listens to {parent.label_word} and works gently.",
        ),
        QAItem(
            question=f"Why did {child.id} choose to use manure carefully?",
            answer=f"{child.id} wanted the soil to become rich and ready, and {child.pronoun('possessive')} {parent.label_word} reminded {child.pronoun('object')} that good care matters.",
        ),
        QAItem(
            question=f"What made {child.id} receptive to the idea of helping instead of rushing?",
            answer=f"{child.id} was studious and listened closely, so the child understood that quiet care could help the garden more than a hurry would.",
        ),
        QAItem(
            question=f"What happened after {child.id} worked in the garden?",
            answer=f"The soil grew rich, the magic bloom woke up, and the family saw the garden looking happy and warm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is manure?",
            answer="Manure is animal waste that can be used carefully to help plants grow in rich soil.",
        ),
        QAItem(
            question="What does receptive mean?",
            answer="Receptive means open to hearing an idea, learning from it, and قبولing help or advice.",
        ),
        QAItem(
            question="What does studious mean?",
            answer="Studious means liking to learn, read, and pay close attention to lessons and details.",
        ),
        QAItem(
            question="Why can a garden need care?",
            answer="A garden needs care because plants need good soil, water, sunlight, and patient help to grow well.",
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], GIFTS[params.gift], params.name, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, gift) combos ({len(stories)} story triples):\n")
        for place, act, gift in triples:
            print(f"  {place:12} {act:8} {gift:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="garden", activity="feed", gift="seeds", name="Mina", parent="mother", trait="studious"),
            StoryParams(place="greenhouse", activity="read", gift="journal", name="Iris", parent="grandmother", trait="receptive"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
