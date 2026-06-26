#!/usr/bin/env python3
"""
storyworlds/worlds/oar_inner_monologue_bravery_adventure.py
============================================================

A small adventure storyworld about a child, a river crossing, an oar, and the
quiet help of inner monologue turning fear into bravery.

The world is intentionally compact: a few locations, a few tools, and one
core problem. A child wants to cross water in a little boat, feels nervous,
talks themselves through it, and then acts bravely enough to finish the trip.
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

BRAVERY_THRESHOLD = 1.0
FEAR_THRESHOLD = 1.0
FOCUS_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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


@dataclass
class Setting:
    place: str
    water: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    use_line: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _rule_fear_to_stillness(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("fear", 0.0) < FEAR_THRESHOLD:
            continue
        if ent.memes.get("focus", 0.0) < FOCUS_THRESHOLD:
            sig = ("fear", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["focus"] = ent.memes.get("focus", 0.0) + 1
            out.append(f"{ent.id} took one slow breath and listened to the oar tap the side of the boat.")
    return out


def _rule_focus_to_bravery(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("focus", 0.0) < FOCUS_THRESHOLD:
            continue
        if ent.memes.get("bravery", 0.0) >= BRAVERY_THRESHOLD:
            continue
        sig = ("brave", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["bravery"] = ent.memes.get("bravery", 0.0) + 1
        out.append(f"{ent.id} remembered, \"I can do hard things one pull at a time.\"")
    return out


CAUSAL_RULES = [_rule_fear_to_stillness, _rule_focus_to_bravery]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def _do_row(world: World, hero: Entity, activity: Activity, tool: Entity, narrate: bool = True) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.meters["water"] = hero.meters.get("water", 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_crossing(world: World, hero: Entity, activity: Activity, tool: Entity) -> dict:
    sim = world.copy()
    _do_row(sim, sim.get(hero.id), activity, sim.get(tool.id), narrate=False)
    h = sim.get(hero.id)
    return {
        "brave": h.memes.get("bravery", 0.0) >= BRAVERY_THRESHOLD,
        "focus": h.memes.get("focus", 0.0),
        "fear": h.memes.get("fear", 0.0),
    }


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the wide-open feeling of adventure.")


def desire(world: World, hero: Entity, activity: Activity, setting: Setting) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} across {setting.place}, even though the water looked deep and wobbly.")


def fear(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"{hero.id} looked at the ripples and felt a small flutter in {hero.pronoun('possessive')} chest.")
    world.say(f'"What if the boat rocks too much?" {hero.id} whispered inside {hero.pronoun("possessive")} own head.')


def inner_monologue(world: World, hero: Entity) -> None:
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(f'"Slow hands. Steady feet. I know the oar can help me," {hero.id} thought.')
    world.say(f'"Brave does not mean not scared. Brave means keep going."')


def guide_offers(world: World, helper: Entity, hero: Entity, tool: Tool) -> None:
    world.say(f"{helper.id} smiled and pointed to {tool.phrase}.")
    world.say(f'"Use the {tool.label} and make each pull gentle," {helper.pronoun("subject").capitalize()} said.')


def row_and_finish(world: World, hero: Entity, activity: Activity, tool_def: Tool) -> None:
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, phrase=tool_def.phrase))
    tool.worn_by = hero.id
    world.say(f"{hero.id} wrapped both hands around the {tool.label} and started to row.")
    world.say(f"{tool_def.use_line}")
    _do_row(world, hero, activity, tool)
    world.say(f"The boat moved forward in short, sure slides, and {hero.id} kept rowing with a steadier breath.")
    if hero.memes.get("bravery", 0.0) >= BRAVERY_THRESHOLD:
        world.say(f"At the far side, {hero.id} stepped out with a proud grin and the water behind {hero.pronoun('object')}.")
    else:
        world.say(f"At the far side, {hero.id} stepped out carefully, glad the crossing was over.")


def tell(setting: Setting, activity: Activity, tool_def: Tool,
         hero_name: str = "Milo", hero_type: str = "boy",
         helper_type: str = "father") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Guide", kind="character", type=helper_type, label="guide"))
    world.add(Entity(id="boat", type="boat", label="little boat", phrase="a little boat with a strong seat"))

    intro(world, hero)
    world.para()
    desire(world, hero, activity, setting)
    fear(world, hero, activity)
    inner_monologue(world, hero)
    guide_offers(world, helper, hero, tool_def)
    world.para()
    row_and_finish(world, hero, activity, tool_def)

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        activity=activity,
        tool_def=tool_def,
        brave=hero.memes.get("bravery", 0.0) >= BRAVERY_THRESHOLD,
    )
    return world


SETTINGS = {
    "river": Setting(place="the river", water="river water", afford={"cross"}),
    "lake": Setting(place="the lake", water="lake water", afford={"cross"}),
    "cove": Setting(place="the cove", water="salt water", afford={"cross"}),
}

ACTIVITIES = {
    "cross": Activity(
        id="cross",
        verb="cross",
        gerund="crossing",
        rush="push the boat across",
        risk="the current might feel big",
        keyword="oar",
        tags={"water", "boat", "adventure", "oar"},
    ),
}

TOOLS = {
    "oar": Tool(
        id="oar",
        label="oar",
        phrase="an oar with a smooth wooden handle",
        helps={"cross"},
        use_line="The oar dipped into the water, pushed, and pulled, as if the river itself were helping the boat along.",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Pia", "Jules", "Theo", "Ada"]
HELPER_TYPES = ["father", "mother", "grandparent"]


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short adventure story for a young child about {hero.id} and an oar.',
        f"Tell a gentle river-crossing tale where {hero.id} feels nervous, thinks bravely, and uses the oar.",
        f"Write a simple story with inner monologue and bravery that ends with a safe crossing in a little boat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    activity = f["activity"]
    tool_def = f["tool_def"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb} across {setting.place} in a little boat.",
        ),
        QAItem(
            question=f"What made {hero.id} feel nervous before the crossing?",
            answer=f"{hero.id} felt nervous because the water looked wobbly and {activity.risk}.",
        ),
        QAItem(
            question=f"What did {hero.id} think to help {hero.pronoun('object')} be brave?",
            answer=f"{hero.id} told {hero.pronoun('object')}self, \"Slow hands. Steady feet. I know the {tool_def.label} can help me.\"",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the plan?",
            answer=f"{helper.id} helped by pointing to the {tool_def.label} and telling {hero.id} to make each pull gentle.",
        ),
    ]
    if f.get("brave"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} finish the adventure?",
                answer=f"{hero.id} rowed across steadily, stepped out at the far side, and felt proud of being brave.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an oar?",
            answer="An oar is a long paddle used to move a boat through water.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the little voice in your head that helps you think through what to do next.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a setting affords the crossing activity, the tool helps
% that activity, and the tool is specifically an oar.
valid(Place, Act, Tool) :- affords(Place, Act), helps(Tool, Act), tool(Tool), Act = cross, Tool = oar.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.afford):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for act in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a, t) for p in SETTINGS for a in ACTIVITIES for t in TOOLS if a in SETTINGS[p].afford and t in TOOLS and a in TOOLS[t].helps}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An adventure storyworld about an oar, inner monologue, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "cross"
    tool = args.tool or "oar"
    if activity not in SETTINGS[place].afford:
        raise StoryError("(No valid combination matches the given options.)")
    if tool not in TOOLS or activity not in TOOLS[tool].helps:
        raise StoryError("The chosen tool does not fit the crossing story.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], TOOLS[params.tool], params.name, params.gender, params.helper)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, tool) combos:\n")
        for place, act, tool in triples:
            print(f"  {place:8} {act:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, activity="cross", tool="oar", name="Milo", gender="boy", helper="father")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
