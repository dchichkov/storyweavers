#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/hurry_flow_punch_sound_effects_teamwork_folk.py
================================================================================

A small folk-tale storyworld about hurrying to restore a blocked flow with
sound effects and teamwork.

Seed tale:
---
In a little valley, the spring behind the old willow had gone quiet. The people
hoped the water would flow again, but a clay cap had sealed the mouth of the
stone pipe.

Little Tova hurried to the spring with her basket of tools. She heard the dry
"tap... tap..." of the last drip and called for help. Old Bram braced the pipe
with a shovel while Tova used a punch to make a tiny opening in the clay. "Tok!"
went the tool, then "plink!" Then the water flowed at last, singing over the
stones. The villagers cheered, because together they had brought the stream back.

World model:
---
    flow blocked      -> spring.flow drops, village.worry rises
    hurry to help     -> actor.urgency rises, actor.joy rises a little
    teamwork brace    -> helper.support rises, actor.confidence rises
    punch opening     -> blockage.integrity drops, tool.wear rises
    opening breaks    -> water.flow rises, village.worry drops, group.joy rises

The narration is built from these state changes rather than from a frozen
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
from typing import Callable, Optional

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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Blockage:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    can_break: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fits: set[str]
    sound: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.phase: str = "setup"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.phase = self.phase
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_block_worry(world: World) -> list[str]:
    out: list[str] = []
    spring = world.entities.get("spring")
    village = world.entities.get("village")
    if not spring or not village:
        return out
    if spring.meters.get("flow", 0.0) >= THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.memes["worry"] = village.memes.get("worry", 0.0) + 1.0
    out.append("The spring had gone quiet, and the village grew worried.")
    return out


def _r_hurry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero or hero.memes.get("urgency", 0.0) < THRESHOLD:
        return out
    sig = ("hurry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 0.5
    out.append("The hero hurried before the last drip could be lost.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    hero = world.entities.get("hero")
    if not helper or not hero:
        return out
    if helper.memes.get("support", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 0.5
    out.append("With a steady helper beside them, the job felt possible.")
    return out


def _r_punch(world: World) -> list[str]:
    out: list[str] = []
    spring = world.entities.get("spring")
    blockage = world.entities.get("blockage")
    tool = world.entities.get("tool")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not all([spring, blockage, tool, hero, helper]):
        return out
    if tool.memes.get("use", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("support", 0.0) < THRESHOLD:
        return out
    sig = ("punch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    blockage.meters["integrity"] = blockage.meters.get("integrity", 1.0) - 1.0
    tool.meters["wear"] = tool.meters.get("wear", 0.0) + 1.0
    out.append(f"{tool.label.capitalize()} went {tool.phrase} {tool_sound(tool)}.")
    if blockage.meters["integrity"] <= 0:
        spring.meters["flow"] = 1.0
        world.entities["village"].memes["worry"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
        out.append("The cap split open, and the water began to flow again.")
    return out


CAUSAL_RULES = [
    Rule("block_worry", "social", _r_block_worry),
    Rule("hurry", "social", _r_hurry),
    Rule("teamwork", "social", _r_teamwork),
    Rule("punch", "physical", _r_punch),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tool_sound(tool: Tool) -> str:
    return {"iron punch": "tok!", "wooden punch": "thock!", "brass punch": "ping!"}.get(tool.label, "tap!")


def resolve_blockage(setting: Setting, blockage: Blockage) -> bool:
    return blockage.kind in setting.affords


def select_tool(blockage: Blockage) -> Optional[Tool]:
    for tool in TOOLS:
        if blockage.kind in tool.fits:
            return tool
    return None


def foresee(world: World, tool: Tool) -> dict:
    sim = world.copy()
    sim.get("hero").memes["urgency"] = 1.0
    sim.get("helper").memes["support"] = 1.0
    sim.get("tool").memes["use"] = 1.0
    propagate(sim, narrate=False)
    spring = sim.get("spring")
    village = sim.get("village")
    return {
        "flow": spring.meters.get("flow", 0.0),
        "worry": village.memes.get("worry", 0.0),
    }


def opening_image(setting: Setting) -> str:
    return setting.detail


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a useful errand.")


def setup_lull(world: World) -> None:
    spring = world.get("spring")
    if spring.meters.get("flow", 0.0) < THRESHOLD:
        world.say("But the spring was stopped up, and the water would not flow.")


def hurry_beat(world: World, hero: Entity) -> None:
    hero.memes["urgency"] = hero.memes.get("urgency", 0.0) + 1.0
    world.say(f"{hero.id} did not waste a moment and hurried to the spring.")


def teamwork_beat(world: World, hero: Entity, helper: Entity) -> None:
    helper.memes["support"] = helper.memes.get("support", 0.0) + 1.0
    world.say(f"{helper.id} came at once to help, and the two stood shoulder to shoulder.")


def punch_beat(world: World, tool: Tool) -> None:
    world.get("tool").memes["use"] = 1.0
    world.say(f'Then came the careful punch: "{tool.phrase}!"')


def resolve_story(world: World, tool: Tool) -> None:
    spring = world.get("spring")
    village = world.get("village")
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"{tool.tail.capitalize()}, and soon the cold clear water began to flow over the stones."
    )
    world.say(
        f"The village cheered, because {hero.id} and {helper.id} had done it together."
    )
    world.say(
        f"The spring sang again, and the path beside it glittered with moving water."
    )
    if spring.meters.get("flow", 0.0) >= THRESHOLD:
        village.memes["joy"] = village.memes.get("joy", 0.0) + 1.0


SETTINGS = {
    "willow_spring": Setting(
        place="the willow spring",
        detail="Behind the old willow, the spring sat under a round stone mouth.",
        affords={"clay_cap"},
    ),
    "stone_well": Setting(
        place="the stone well",
        detail="In the middle of the village, the well had a heavy stone lip and a quiet echo.",
        affords={"mud_plug"},
    ),
    "bridge_spout": Setting(
        place="the bridge spout",
        detail="Below the bridge, a narrow spout should have been singing, but it only dripped.",
        affords={"reed_clog"},
    ),
}

BLOCKAGES = {
    "clay_cap": Blockage(
        id="blockage",
        label="clay cap",
        phrase="a firm clay cap",
        kind="clay_cap",
        region="mouth",
    ),
    "mud_plug": Blockage(
        id="blockage",
        label="mud plug",
        phrase="a muddy plug",
        kind="mud_plug",
        region="mouth",
    ),
    "reed_clog": Blockage(
        id="blockage",
        label="reed clog",
        phrase="a tangled reed clog",
        kind="reed_clog",
        region="mouth",
    ),
}

TOOLS = [
    Tool(
        id="tool",
        label="iron punch",
        phrase="tok",
        fits={"clay_cap"},
        sound="tok!",
        tail="The clay cap cracked",
    ),
    Tool(
        id="tool",
        label="wooden punch",
        phrase="thock",
        fits={"mud_plug"},
        sound="thock!",
        tail="The mud plug loosened",
    ),
    Tool(
        id="tool",
        label="brass punch",
        phrase="ping",
        fits={"reed_clog"},
        sound="ping!",
        tail="The reed clog gave way",
    ),
]

NAMES = ["Tova", "Marek", "Elin", "Sora", "Pavel", "Nina"]
TYPES = ["girl", "boy"]
HELPERS = ["grandfather", "grandmother", "neighor", "neighbor"]


@dataclass
class StoryParams:
    place: str
    blockage: str
    tool: str
    name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("willow_spring", "clay_cap", "tool", "Tova", "girl", "grandfather", "quick"),
    StoryParams("stone_well", "mud_plug", "tool", "Marek", "boy", "grandmother", "helpful"),
    StoryParams("bridge_spout", "reed_clog", "tool", "Elin", "girl", "neighbor", "brave"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, setting in SETTINGS.items():
        for b in BLOCKAGES.values():
            if b.kind in setting.affords and select_tool(b):
                out.append((p, b.kind, "tool"))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a hero who must hurry when water will not flow.',
        f"Tell a warm story where {f['hero'].id} and {f['helper'].id} work together to use a punch on {f['blockage'].label}.",
        f'Write a gentle tale with sound effects like "tok" and "plink" that ends with a stream flowing again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    blockage: Blockage = f["blockage"]
    setting: Setting = f["setting"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Why did {hero.id} hurry to {setting.place}?",
            answer=f"{hero.id} hurried because the water there had stopped flowing, and the village needed help quickly.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do together?",
            answer=f"They worked side by side to use {tool.label} on {blockage.label} so the water could flow again.",
        ),
        QAItem(
            question=f"What sound did the punch make in the story?",
            answer=f"It made a crisp sound like \"{tool.sound}\" when the blockage broke open.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does water do when it flows?",
            answer="When water flows, it moves along in a steady stream instead of sitting still.",
        ),
        QAItem(
            question="Why do helpers work together in a folk tale?",
            answer="Helpers work together so hard jobs become easier and the whole community can share the success.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps you hear the action in your mind, like 'tok' or 'plink'.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def tell(setting: Setting, blockage: Blockage, tool: Tool, name: str, hero_type: str, helper_role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=name, traits=["little", trait]))
    helper = world.add(Entity(id="helper", kind="character", type="person", label=helper_role))
    village = world.add(Entity(id="village", kind="group", type="village", label="the village", memes={"worry": 0.0, "joy": 0.0}))
    spring = world.add(Entity(id="spring", kind="thing", type="spring", label="the spring", meters={"flow": 0.0}))
    block = world.add(Entity(id="blockage", kind="thing", type=blockage.kind, label=blockage.label, phrase=blockage.phrase, meters={"integrity": 1.0}))
    t = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, helper=helper, village=village, spring=spring, blockage=blockage, tool=tool, setting=setting)
    introduce(world, hero)
    world.say(opening_image(setting))
    setup_lull(world)
    world.para()
    hurry_beat(world, hero)
    teamwork_beat(world, hero, helper)
    punch_beat(world, tool)
    propagate(world, narrate=True)
    world.para()
    resolve_story(world, tool)
    spring.meters["flow"] = 1.0
    village.memes["joy"] = 1.0
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.blockage and args.blockage not in BLOCKAGES:
        raise StoryError("Unknown blockage.")
    if args.place and args.blockage:
        setting = SETTINGS[args.place]
        block = BLOCKAGES[args.blockage]
        if not resolve_blockage(setting, block):
            raise StoryError("That blockage does not belong in that setting.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.blockage:
        combos = [c for c in combos if c[1] == args.blockage]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, blockage, tool_id = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        blockage=blockage,
        tool=tool_id,
        name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(TYPES),
        helper=args.helper or rng.choice(HELPERS),
        trait=rng.choice(["quick", "kind", "brave", "steady", "cheerful"]),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    blockage = BLOCKAGES[params.blockage]
    tool = next(t for t in TOOLS if t.id == params.tool and blockage.kind in t.fits)
    world = tell(setting, blockage, tool, params.name, params.hero_type, params.helper, params.trait)
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


ASP_RULES = r"""
setting(willow_spring).
setting(stone_well).
setting(bridge_spout).

blockage(clay_cap).
blockage(mud_plug).
blockage(reed_clog).

tool(iron_punch).
tool(wooden_punch).
tool(brass_punch).

affords(willow_spring,clay_cap).
affords(stone_well,mud_plug).
affords(bridge_spout,reed_clog).

fits(iron_punch,clay_cap).
fits(wooden_punch,mud_plug).
fits(brass_punch,reed_clog).

valid(P,B,T) :- affords(P,B), fits(T,B).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for b in BLOCKAGES:
        lines.append(asp.fact("blockage", b))
    for t in ["iron_punch", "wooden_punch", "brass_punch"]:
        lines.append(asp.fact("tool", t))
    for p, s in SETTINGS.items():
        for b in s.affords:
            lines.append(asp.fact("affords", p, b))
    for tool in TOOLS:
        for b in tool.fits:
            lines.append(asp.fact("fits", tool.id, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if a - b:
        print("Only in ASP:", sorted(a - b))
    if b - a:
        print("Only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world about hurrying, flow, punch, sound effects, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandfather", "grandmother", "neighbor"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
