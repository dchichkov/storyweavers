#!/usr/bin/env python3
"""
storyworlds/worlds/chap_perceive_constant_cautionary_curiosity_tall_tale.py
============================================================================

A standalone story world in the spirit of a tall tale: a curious chap keeps
perceiving the same cautionary sign, and the world turns on what he does next.

Seed image:
- A chap notices a constant warning from the ridge.
- Curiosity pulls him closer.
- A cautious helper and a useful tool turn a risky choice into a safe one.
- The ending proves what changed in the world.

This world is intentionally small, concrete, and constraint-checked.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

SETTINGS = {
    "ridge": "the red ridge",
    "canyon": "the blue canyon",
    "riverbank": "the riverbank",
    "lantern_room": "the lantern room",
}

HAZARDS = {
    "echo": {
        "label": "echoing warning",
        "verb": "follow the echo",
        "rush": "dash toward the echo",
        "soil": "lost in the noise",
        "zone": {"ears", "feet"},
        "mess": "startled",
        "topic": "echo",
    },
    "fog": {
        "label": "thick fog",
        "verb": "peer into the fog",
        "rush": "stride into the fog",
        "soil": "squinting and muddled",
        "zone": {"eyes", "feet"},
        "mess": "blurry",
        "topic": "fog",
    },
    "spark": {
        "label": "a wandering spark",
        "verb": "chase the spark",
        "rush": "skip after the spark",
        "soil": "singed at the edges",
        "zone": {"hands", "feet"},
        "mess": "singed",
        "topic": "spark",
    },
}

TOOLS = {
    "lantern": {
        "label": "a steady lantern",
        "covers": {"eyes"},
        "guards": {"blurry"},
        "prep": "carry the lantern first",
        "tail": "lit the lantern and held it high",
    },
    "boots": {
        "label": "sturdy boots",
        "covers": {"feet"},
        "guards": {"startled", "singed"},
        "prep": "put on sturdy boots first",
        "tail": "pulled on the sturdy boots",
    },
    "glasses": {
        "label": "clear glasses",
        "covers": {"eyes"},
        "guards": {"startled", "blurry"},
        "prep": "wear the clear glasses first",
        "tail": "settled the clear glasses on his nose",
    },
}

CHAP_NAMES = ["Jeb", "Otis", "Milo", "Rufus", "Walt", "Ezra"]
HELPER_NAMES = ["Maggie", "Pearl", "Sally", "Ivy", "Mara"]
TRAITS = ["curious", "brave", "wily", "steady", "spry"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chap", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"helper", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.weather = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A hazard is at risk if it splashes or affects the region the item is worn on.
risk(H, I) :- hazard(H), worn_on(I, R), zone(H, R).

% A tool is a real fix only if it covers the at-risk region and guards the mess kind.
fix(T, H, I) :- tool(T), risk(H, I), guards(T, M), mess_of(H, M), covers(T, R), worn_on(I, R).

has_fix(H, I) :- fix(_, H, I).

valid_story(Setting, H, Tool) :- setting(Setting), hazard(H), tool(Tool),
                                 affords(Setting, H), has_fix(H, Tool).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("mess_of", hid, h["mess"]))
        for r in sorted(h["zone"]):
            lines.append(asp.fact("zone", hid, r))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in sorted(t["covers"]):
            lines.append(asp.fact("covers", tid, r))
        for m in sorted(t["guards"]):
            lines.append(asp.fact("guards", tid, m))
    for sid in SETTINGS:
        for hid in HAZARDS:
            if sid in {"ridge", "canyon", "riverbank"}:
                lines.append(asp.fact("affords", sid, hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def hazard_at_risk(hazard_id: str, tool_id: str) -> bool:
    h = HAZARDS[hazard_id]
    t = TOOLS[tool_id]
    return any(region in h["zone"] for region in t["covers"])


def select_tool(hazard_id: str, tool_id: str) -> bool:
    return hazard_at_risk(hazard_id, tool_id) and bool(TOOLS[tool_id]["guards"] & {HAZARDS[hazard_id]["mess"]})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hid in HAZARDS:
            for tool in TOOLS:
                if setting in {"ridge", "canyon", "riverbank"} and hazard_at_risk(hid, tool) and select_tool(hid, tool):
                    combos.append((setting, hid, tool))
    return combos


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            for hid, h in HAZARDS.items():
                if actor.meters.get(h["mess"], 0.0) < THRESHOLD:
                    continue
                for item in world.worn_items(actor):
                    if item.protective or item.region not in h["zone"]:
                        continue
                    if world.covered(actor, item.region):
                        continue
                    sig = ("mess", actor.id, item.id, hid)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[h["mess"]] = item.meters.get(h["mess"], 0.0) + 1
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                    out.append(f"{actor.id}'s {item.label} came away {h['soil']}.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, hazard_id: str, item_id: str) -> dict:
    sim = world.copy()
    h = HAZARDS[hazard_id]
    sim.get(actor.id).meters[h["mess"]] = 1.0
    propagate(sim, narrate=False)
    item = sim.entities[item_id]
    return {"soiled": item.meters.get("dirty", 0.0) >= THRESHOLD}


def tale_opening(hero: Entity, helper: Entity, hazard_id: str) -> str:
    h = HAZARDS[hazard_id]
    trait = next((t for t in hero.traits if t != "little"), "curious")
    return (
        f"Folks said {hero.id} was a little {trait} chap with a nose for trouble and a heart for wonder. "
        f"He could perceive {h['label']} from a mile away, and that made his curiosity grow as constant as the creek."
    )


def world_detail(setting: str) -> str:
    return {
        "ridge": "The ridge was all red dust and long shadows, with rocks stacked like old wagons.",
        "canyon": "The canyon yawned wide and blue, with wind that could comb a squirrel's tail flat.",
        "riverbank": "The riverbank glittered with reeds, pebbles, and water that never forgot to sing.",
        "lantern_room": "The lantern room was snug and bright, with shelves of glass and a warm wooden floor.",
    }[setting]


def introduce(world: World, hero: Entity, helper: Entity, hazard_id: str) -> None:
    world.say(tale_opening(hero, helper, hazard_id))
    world.say(f"{world_detail(world.setting)}")


def desire(world: World, hero: Entity, hazard_id: str) -> None:
    h = HAZARDS[hazard_id]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"Every time he perceived {h['label']}, he wanted to {h['verb']} and see what story it was trying to tell."
    )


def warning(world: World, helper: Entity, hero: Entity, hazard_id: str, item: Entity) -> None:
    h = HAZARDS[hazard_id]
    world.say(
        f"But {helper.id} was a cautionary sort, and she said, "
        f"\"If you go off after that, your {item.label} may come back {h['soil']}.\""
    )


def attempt(world: World, hero: Entity, hazard_id: str) -> None:
    h = HAZARDS[hazard_id]
    hero.meters[h["mess"]] = hero.meters.get(h["mess"], 0.0) + 1
    world.say(f"The chap tried to {h['rush']}, quick as a tumbleweed in a gale.")


def choose_tool(world: World, hero: Entity, helper: Entity, hazard_id: str, item: Entity) -> Optional[Entity]:
    for tid, t in TOOLS.items():
        if not hazard_at_risk(hazard_id, tid):
            continue
        if item.region not in t["covers"]:
            continue
        if HAZARDS[hazard_id]["mess"] not in t["guards"]:
            continue
        tool = world.add(Entity(
            id=tid,
            type="tool",
            label=t["label"],
            owner=hero.id,
            caretaker=helper.id,
            protective=True,
            covers=set(t["covers"]),
        ))
        tool.worn_by = hero.id
        return tool
    return None


def resolve(world: World, hero: Entity, helper: Entity, hazard_id: str, item: Entity, tool: Entity) -> None:
    h = HAZARDS[hazard_id]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f"Then {helper.id} smiled the way a wise aunt smiles, and said, "
        f"\"Let's {TOOLS[tool.id]['prep']} before we go any farther.\""
    )
    world.say(
        f"{hero.id} listened, and the two of them {TOOLS[tool.id]['tail']}. "
        f"After that, the chap could still {h['verb']}, but {item.label} stayed clean and the trail stayed safe."
    )


def tell(setting: str, hazard_id: str, item_label: str, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    world.weather = "windy"
    hero = world.add(Entity(id=hero_name, kind="character", type="chap", traits=["little", "curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper", traits=["cautionary", "steady"]))
    item = world.add(Entity(
        id="item",
        type=item_label,
        label=item_label,
        owner=hero.id,
        caretaker=helper.id,
        region="feet" if item_label == "boots" else "eyes",
    ))

    introduce(world, hero, helper, hazard_id)
    world.para()
    desire(world, hero, hazard_id)
    warning(world, helper, hero, hazard_id, item)
    attempt(world, hero, hazard_id)
    tool = choose_tool(world, hero, helper, hazard_id, item)
    if tool:
        world.para()
        resolve(world, hero, helper, hazard_id, item, tool)

    world.facts.update(hero=hero, helper=helper, hazard_id=hazard_id, item=item, tool=tool, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "echo": [
        ("What is an echo?", "An echo is a sound that bounces back after it hits walls, cliffs, or other hard places."),
    ],
    "fog": [
        ("What is fog?", "Fog is a cloud that sits low to the ground and makes it hard to see far ahead."),
    ],
    "spark": [
        ("What is a spark?", "A spark is a tiny flash of fire or light that can jump from one thing to another."),
    ],
    "lantern": [
        ("What does a lantern do?", "A lantern gives off light so people can see in dark places."),
    ],
    "boots": [
        ("What are boots for?", "Boots help protect your feet and keep them safer on rough ground."),
    ],
    "glasses": [
        ("Why do people wear glasses?", "Some people wear glasses to help them see more clearly."),
    ],
    "cautionary": [
        ("What does cautionary mean?", "Cautionary means meant to warn someone to be careful."),
    ],
    "curiosity": [
        ("What is curiosity?", "Curiosity is the feeling that makes you want to find out more about something."),
    ],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    haz = HAZARDS[f["hazard_id"]]  # type: ignore[index]
    item: Entity = f["item"]  # type: ignore[assignment]
    return [
        f"Write a tall tale about a little chap named {hero.id} who keeps perceiving {haz['label']} and must listen to a cautionary helper.",
        f"Tell a child-friendly story where {hero.id}'s curiosity leads him toward {haz['verb']}, but {helper.id} finds a safe way to protect the {item.label}.",
        f"Write a short whimsical story that uses the words chap, perceive, and constant, and ends with a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    haz = HAZARDS[f["hazard_id"]]  # type: ignore[index]
    tool: Optional[Entity] = f["tool"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little chap with constant curiosity, and {helper.id}, who kept him cautious.",
        ),
        QAItem(
            question=f"What did {hero.id} keep perceiving?",
            answer=f"He kept perceiving {haz['label']} on the trail, and that made him want to go look closer.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} to be careful?",
            answer=f"{helper.id} warned him because the trouble could make the {item.label} come back {haz['soil']} if they rushed in without a plan.",
        ),
    ]
    if tool is not None:
        qa.append(QAItem(
            question=f"How did {tool.label} help in the end?",
            answer=f"{tool.label.capitalize()} helped by covering the right part of the body and guarding against the kind of mess {haz['label']} could cause.",
        ))
        qa.append(QAItem(
            question=f"What changed after they used {tool.label}?",
            answer=f"After they used {tool.label}, {hero.id} could still follow his curiosity, but he did it safely and the {item.label} stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {HAZARDS[f["hazard_id"]]["topic"]}  # type: ignore[index]
    tags.add("cautionary")
    tags.add("curiosity")
    if f.get("tool"):
        tags.add(f["tool"].id)  # type: ignore[union-attr]
    out: list[QAItem] = []
    for tag in ["curiosity", "cautionary", "echo", "fog", "spark", "lantern", "boots", "glasses"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hazard: str
    item_label: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="ridge", hazard="echo", item_label="boots", hero_name="Jeb", helper_name="Maggie"),
    StoryParams(setting="canyon", hazard="fog", item_label="glasses", hero_name="Otis", helper_name="Pearl"),
    StoryParams(setting="riverbank", hazard="spark", item_label="boots", hero_name="Rufus", helper_name="Ivy"),
]


def explain_rejection(setting: str, hazard: str, item_label: str) -> str:
    if setting not in {"ridge", "canyon", "riverbank"}:
        return "(No story: this setting does not support the needed tall-tale outing.)"
    if not hazard_at_risk(hazard, item_label):
        return f"(No story: {TOOLS[item_label]['label']} would not reasonably be at risk from {HAZARDS[hazard]['label']}. Try another item.)"
    if not select_tool(hazard, item_label):
        return f"(No story: no tool in this world actually protects the at-risk item from {HAZARDS[hazard]['label']}. )"
    return "(No story: invalid combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hazard and args.item_label:
        if (args.setting, args.hazard, args.item_label) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.hazard, args.item_label))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.item_label is None or c[2] == args.item_label)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, item_label = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        hazard=hazard,
        item_label=item_label,
        hero_name=args.hero_name or rng.choice(CHAP_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.hazard, params.item_label, params.hero_name, params.helper_name)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a chap, a constant warning, and a cautious curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--item-label", choices=TOOLS)
    ap.add_argument("--hero-name", choices=CHAP_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, hazard, tool) stories:\n")
        for s, h, t in stories:
            print(f"  {s:12} {h:8} {t:10}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.hazard} at {p.setting} (item: {p.item_label})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
