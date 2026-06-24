#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/acorn_kindness_magic_slice_of_life.py
===============================================================================================================

A tiny slice-of-life storyworld about a child, an acorn, a little problem,
and a kind magical fix.

The domain is intentionally small:
- a child finds or carries an acorn
- something ordinary makes the acorn hard to keep safe
- kindness and a small bit of magic help repair the moment
- the ending proves what changed in the physical and emotional world

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectKind:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    uses: str
    helps: set[str]
    prepares: str
    ends: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mood(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _do_activity(world: World, child: Entity, activity: Activity) -> None:
    _inc(child, activity.keyword)
    _mood(child, "joy")
    if activity.id == "garden":
        _inc(child, "soil")
    if activity.id == "rain":
        _inc(child, "wet")
    if activity.id == "market":
        _mood(child, "busy")


def _protects(tool: MagicTool, activity: Activity, item: ObjectKind) -> bool:
    return activity.id in tool.helps and item.region in {"hands", "pocket"}


def intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who liked quiet afternoons and small surprises.")


def set_scene(world: World, activity: Activity) -> None:
    if world.setting.indoors:
        world.say(f"The {world.setting.place} felt calm, with soft light and a place to sit.")
    elif activity.id == "garden":
        world.say(f"The garden was warm and green, with little leaves moving in the breeze.")
    elif activity.id == "rain":
        world.say("The yard smelled fresh after the rain, and tiny drops still clung to the grass.")
    else:
        world.say(f"{world.setting.place.capitalize()} felt busy in a friendly way.")


def want_acorn(world: World, child: Entity, item: Entity, activity: Activity) -> None:
    _mood(child, "curious")
    world.say(f"{child.pronoun().capitalize()} found {child.pronoun('possessive')} {item.label} and wanted to keep it safe.")
    world.say(f"{child.pronoun().capitalize()} hoped to {activity.verb} a little later, too.")


def problem(world: World, child: Entity, item: Entity, activity: Activity) -> None:
    _mood(child, "worry")
    if activity.id == "garden":
        world.say(f"But the garden soil was crumbly, and {item.label} could get dusty and lost among the leaves.")
    elif activity.id == "rain":
        world.say(f"But the rain could make {item.label} damp and hard to hold onto.")
    else:
        world.say(f"But the busy room had too many places where {item.label} could slip away.")


def kindness_offer(world: World, helper: Entity, child: Entity, item: Entity, tool: MagicTool) -> None:
    _mood(helper, "kind")
    world.say(
        f"{helper.id} smiled and said, \"Let me help.\" "
        f"{helper.pronoun().capitalize()} {tool.prepares}, then used a little {tool.label.lower()}."
    )
    world.say(f"The small spell {tool.uses}, so {item.label} stayed close and easy to find.")


def accept_help(world: World, child: Entity, helper: Entity, item: Entity, activity: Activity, tool: MagicTool) -> None:
    _mood(child, "relief")
    _mood(child, "kind")
    world.say(f"{child.id} nodded and held still while the gentle magic finished.")
    world.say(
        f"After that, {child.id} could {activity.gerund}, "
        f"with {item.label} tucked safely away. "
        f"{helper.id} {tool.ends}, and the afternoon felt bright again."
    )


def tell(setting: Setting, activity: Activity, item_kind: ObjectKind, tool: MagicTool,
         child_name: str = "Maya", child_type: str = "girl", helper_name: str = "Grandpa",
         helper_type: str = "man") -> World:
    world = World(setting)
    world.weather = activity.weather

    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    item = world.add(Entity(id="acorn", type="acorn", label=item_kind.label, phrase=item_kind.phrase, owner=child.id))
    item.carried_by = child.id

    intro(world, child)
    world.para()
    set_scene(world, activity)
    want_acorn(world, child, item, activity)
    problem(world, child, item, activity)
    world.para()
    kindness_offer(world, helper, child, item, tool)
    accept_help(world, child, helper, item, activity, tool)

    _do_activity(world, child, activity)
    if activity.id == "garden":
        _inc(item, "clean")
    elif activity.id == "rain":
        _inc(item, "dry")
    else:
        _inc(item, "safe")

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        activity=activity,
        tool=tool,
        setting=setting,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"garden"}),
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"sunroom"}),
    "porch": Setting(place="the porch", indoors=False, affords={"porch", "rain"}),
}

ACTIVITIES = {
    "garden": Activity(
        id="garden",
        verb="pick flowers",
        gerund="picking flowers",
        risk="dusty and lost",
        weather="sunny",
        keyword="curious",
        tags={"garden", "leaf", "soil"},
    ),
    "sunroom": Activity(
        id="sunroom",
        verb="paint a little card",
        gerund="painting a little card",
        risk="smudged",
        weather="sunny",
        keyword="careful",
        tags={"paint", "paper"},
    ),
    "rain": Activity(
        id="rain",
        verb="watch the rain",
        gerund="watching the rain",
        risk="damp",
        weather="rainy",
        keyword="wet",
        tags={"rain", "wet"},
    ),
    "porch": Activity(
        id="porch",
        verb="feed the birds",
        gerund="feeding the birds",
        risk="slipped away",
        weather="breezy",
        keyword="gentle",
        tags={"birds", "bread"},
    ),
}

ITEMS = {
    "acorn": ObjectKind(
        id="acorn",
        label="a small acorn",
        phrase="a small acorn with a smooth cap",
        region="hands",
        fragile=True,
    )
}

TOOLS = {
    "pouch": MagicTool(
        id="pouch",
        label="kindness pouch",
        uses="made a tiny pocket of glow around it",
        helps={"garden", "sunroom", "rain", "porch"},
        prepares="found a soft little pouch in the basket",
        ends="smiled at the neat idea",
    ),
    "bell": MagicTool(
        id="bell",
        label="silver bell charm",
        uses="rang once and helped everyone notice the acorn",
        helps={"garden", "porch"},
        prepares="picked up a small bell charm from the shelf",
        ends="laughed at how easy it was to remember where it was",
    ),
}


@dataclass
class StoryParams:
    setting: str
    activity: str
    item: str
    tool: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("garden", "garden", "acorn", "pouch", "Maya", "girl", "Grandpa", "man"),
    StoryParams("sunroom", "sunroom", "acorn", "pouch", "Noah", "boy", "Auntie", "woman"),
    StoryParams("porch", "rain", "acorn", "bell", "Lila", "girl", "Mom", "woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about acorns, kindness, and a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(sorted(SETTINGS[setting].affords))
    item = args.item or "acorn"
    tool = args.tool or rng.choice(list(TOOLS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    child_name = args.name or rng.choice(["Maya", "Lila", "Noah", "Ivy", "Finn", "June"])
    helper_name = args.helper or rng.choice(["Grandpa", "Auntie", "Mom", "Dad", "Nana"])

    if activity not in SETTINGS[setting].affords:
        raise StoryError("That activity does not fit the chosen setting.")
    if not _protects(TOOLS[tool], ACTIVITIES[activity], ITEMS[item]):
        raise StoryError("That magic tool does not reasonably help with this acorn moment.")

    return StoryParams(
        setting=setting,
        activity=activity,
        item=item,
        tool=tool,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about an acorn, kindness, and a little magic at {f["setting"].place}.',
        f"Tell a gentle story where {f['child'].id} wants to {f['activity'].verb} but worries about {f['item'].label}, and {f['helper'].id} helps kindly.",
        f'Write a child-friendly story that includes the word "acorn" and ends with a calm, happy afternoon.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} want to keep safe?",
            answer=f"{child.id} wanted to keep {item.label} safe."
        ),
        QAItem(
            question=f"Why was {child.id} worried before {activity.verb}?",
            answer=f"{child.id} was worried because {item.label} could get {activity.risk}."
        ),
        QAItem(
            question=f"Who helped with kindness and magic?",
            answer=f"{helper.id} helped by using a kind little bit of magic."
        ),
        QAItem(
            question=f"What did {child.id} do at the end?",
            answer=f"{child.id} could {activity.gerund} with {item.label} tucked safely away."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an acorn?", answer="An acorn is the nut of an oak tree, and it can grow into a new tree."),
        QAItem(question="What does kindness mean?", answer="Kindness means being gentle, caring, and helpful to someone else."),
        QAItem(question="What is magic in a story?", answer="Magic is a special impossible-seeming power that can make a story feel wondrous."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        parts.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
setting(garden).
setting(sunroom).
setting(porch).

affords(garden,garden).
affords(sunroom,sunroom).
affords(porch,porch).
affords(porch,rain).

activity(garden).
activity(sunroom).
activity(rain).
activity(porch).

activity_help(garden,pouch).
activity_help(sunroom,pouch).
activity_help(rain,pouch).
activity_help(porch,pouch).
activity_help(garden,bell).
activity_help(porch,bell).

item(acorn).
item_region(acorn,hands).

helpful(T,A,I) :- activity_help(A,T), item(I), item_region(I,hands).
valid(S,A,T) :- affords(S,A), helpful(T,A,acorn).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, ITEMS[iid].region))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        for a in sorted(TOOLS[tid].helps):
            lines.append(asp.fact("activity_help", a, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {
        (s, a, t)
        for s in SETTINGS
        for a in SETTINGS[s].affords
        for t in TOOLS
        if _protects(TOOLS[t], ACTIVITIES[a], ITEMS["acorn"])
    }
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        ITEMS[params.item],
        TOOLS[params.tool],
        params.child_name,
        params.child_type,
        params.helper_name,
        params.helper_type,
    )
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} valid combinations:")
        for s, a, t in triples:
            print(f"  {s} {a} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
