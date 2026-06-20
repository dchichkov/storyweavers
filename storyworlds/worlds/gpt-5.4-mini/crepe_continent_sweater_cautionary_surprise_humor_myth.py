#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crepe_continent_sweater_cautionary_surprise_humor_myth.py
=========================================================================================

A standalone storyworld for a tiny mythic domain: a child on a small drifting
continent is warned not to use a warm sweater as a sail, a surprise gust causes
trouble, and a careful helper turns the mishap into a comic lesson. The world
includes the seed words crepe, continent, and sweater, with a myth-like tone,
a cautionary turn, surprise, and humor.

The tale is modeled as state, not a frozen paragraph. Typed entities carry
physical meters and emotional memes; rules advance the world; rendering reads
the resulting state.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    sky: str
    ground: str
    mood: str


@dataclass
class Item:
    id: str
    label: str
    kind: str
    phrase: str
    makes_wind: bool = False
    catches_heat: bool = False
    edible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    risk: str
    effect: str
    humor: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["heat"] < THRESHOLD:
            continue
        sig = ("heat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("continent").meters["danger"] += 1
        for kid_id in ("child", "helper"):
            world.get(kid_id).memes["alarm"] += 1
        out.append("__heat__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["wit"] >= THRESHOLD and world.get("child").memes["embarrassment"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("helper").memes["joy"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("heat", _r_heat), Rule("laugh", _r_laugh)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    return produced


def gate_reasonable(item: Item, action: Action) -> bool:
    return item.catches_heat and action.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            for aid, act in ACTIONS.items():
                if gate_reasonable(item, act):
                    combos.append((sid, iid, aid))
    return combos


def atmosphere(world: World, setting: Setting, child: Entity, helper: Entity, item: Item, action: Action) -> None:
    world.say(
        f"On {setting.id}, the old myths said the sky sang like a kettle and the stones remembered every footstep."
    )
    world.say(
        f"{child.id} and {helper.id} lived there beside a {item.phrase}, a {setting.ground}, and a little shrine of stone cups."
    )
    world.say(
        f"{child.id} loved to make {action.verb} because {action.humor}."
    )


def temptation(world: World, child: Entity, item: Item, action: Action) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One bright morning, {child.id} wanted to {action.verb} with {item.label}, pretending it would make the day grand."
    )
    world.say(
        f"{child.id} whispered, \"A {item.label} can carry a hero farther than a creek!\""
    )


def warning(world: World, helper: Entity, child: Entity, item: Item, action: Action) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} narrowed {helper.pronoun('possessive')} eyes and said, \"That is not wise. {item.label_word.capitalize()} can invite trouble across a {action.risk}.\""
    )
    world.say(
        f"{helper.id} also pointed to the {action.effect} and reminded {child.id} that every shortcut has a shadow."
    )


def surprise(world: World, child: Entity, item: Item, action: Action) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But then, with a laugh like a drumroll, a surprise wind leapt out from behind the hills."
    )
    item_ent = world.get(item.id)
    item_ent.meters["heat"] += 1
    item_ent.meters["torn"] += 1
    world.say(
        f"It tugged the {item.label} loose, puffed it up like a royal sail, and sent it spinning over the {world.get('continent').label_word}."
    )
    propagate(world)


def rescue(world: World, helper: Entity, child: Entity, item: Item) -> None:
    helper.memes["wit"] += 1
    child.memes["embarrassment"] += 1
    world.get("continent").meters["danger"] = 0
    world.get(item.id).meters["heat"] = 0
    world.say(
        f"{helper.id} burst out laughing, then caught the {item.label} before it could kiss the cliff."
    )
    world.say(
        f"\"A sweater is for warmth, not for flight,\" {helper.id} said, tucking it under {helper.pronoun('possessive')} arm."
    )
    world.say(
        f"{child.id} groaned, then snorted at the silliness of a sweater pretending to be a bird."
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting, item: Item, action: Action) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say("For a moment, the whole continent seemed to smile.")
    world.say(
        f"Afterward, {helper.id} brought out a plate of crepes, and the two of them ate while the wind played softly with the flags."
    )
    world.say(
        f"{child.id} promised to keep the {item.label} on the right side of the body and to use the {action.id} only for stories, never for stunts."
    )


def tell(setting: Setting, item: Item, action: Action, child_name: str = "Mira",
         helper_name: str = "Grandmother", child_gender: str = "girl",
         helper_gender: str = "woman") -> World:
    world = World()
    world.add(Entity("continent", type="land", label="continent"))
    child = world.add(Entity(child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    gear = world.add(Entity(item.id, type=item.kind, label=item.label))
    world.facts.update(setting=setting, item=item, action=action, child=child, helper=helper, gear=gear)

    atmosphere(world, setting, child, helper, item, action)
    world.para()
    temptation(world, child, item, action)
    warning(world, helper, child, item, action)
    world.para()
    surprise(world, child, item, action)
    world.para()
    rescue(world, helper, child, item)
    ending(world, child, helper, setting, item, action)
    world.facts["outcome"] = "resolved"
    return world


SETTINGS = {
    "sunlit_ridge": Setting("the sunlit ridge", "bright and blue", "a stone path", "mythic"),
    "harbor_cliff": Setting("the harbor cliff", "salt-white and windy", "a low wall", "mythic"),
    "orchard_cove": Setting("the orchard cove", "gold and green", "a watchful hill", "mythic"),
}

ITEMS = {
    "sweater": Item("sweater", "sweater", "garment", "a wool sweater with a zigzag hem", catches_heat=True, tags={"sweater"}),
    "crepe": Item("crepe", "crepe", "food", "a paper-thin crepe folded like a small map", edible=True, tags={"crepe"}),
    "banner": Item("banner", "banner", "cloth", "a bright banner tied to the rail", catches_heat=True, makes_wind=True, tags={"banner"}),
}

ACTIONS = {
    "kite": Action("kite", "fly a kite", "gusts", "the wind", "the string kept tangling in a ridiculous knot", 1, tags={"wind"}),
    "sail": Action("sail", "make a sail", "cliffs", "the cliff", "the shape looked heroic until it looked silly", 1, tags={"wind"}),
    "cover": Action("cover", "cover the lantern", "sparks", "the flame", "the cloth would not stay still for long", 1, tags={"heat"}),
}

# Curated choice set: all valid, but varied in tone/outcome texture.
CURATED = [
    StoryParams("sunlit_ridge", "sweater", "kite", "Mira", "Grandmother", "girl", "woman"),
    StoryParams("harbor_cliff", "banner", "sail", "Oren", "Uncle", "boy", "man"),
    StoryParams("orchard_cove", "sweater", "cover", "Lina", "Grandmother", "girl", "woman"),
]


@dataclass
class StoryParams:
    setting: str
    item: str
    action: str
    child: str
    helper: str
    child_gender: str
    helper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cautionary surprise-humor storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    if args.item and args.action and not gate_reasonable(ITEMS[args.item], ACTIONS[args.action]):
        raise StoryError("That combination is too strange for this myth: it would not create a believable cautionary surprise.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, action = rng.choice(sorted(combos))
    return StoryParams(
        setting, item, action,
        args.child or rng.choice(["Mira", "Lina", "Oren", "Tavi"]),
        args.helper or rng.choice(["Grandmother", "Uncle", "Auntie", "Old Sage"]),
        args.child_gender or rng.choice(["girl", "boy"]),
        args.helper_gender or rng.choice(["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story that includes the words "{f["item"].label}", "continent", and "crepe".',
        f"Tell a cautionary yet humorous tale where {f['child'].id} ignores a warning and then learns from a surprise on {f['setting'].id}.",
        f"Write a short story with a surprising wind, a careful elder, and a sweater that should have stayed a sweater.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    action = f["action"]
    return [
        QAItem(
            question=f"Why did {child.id} get warned?",
            answer=f"{helper.id} warned {child.id} because using the {item.label} to {action.verb} would invite trouble. The warning fit the mythic lesson that shortcuts can turn playful ideas into accidents."
        ),
        QAItem(
            question="What surprised everyone?",
            answer=f"A sudden wind burst out and snatched at the {item.label}, making the whole scene feel both dramatic and a little funny. The surprise was the turning point that showed why the warning mattered."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The helper caught the {item.label}, teased the child gently, and the two of them ended with crepes and a safer promise. The ending proves the danger passed and the mood turned warm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a crepe?", "A crepe is a thin pancake that can be folded or rolled. People often eat it with sweet or simple fillings."),
        QAItem("What is a continent?", "A continent is one of the very large land masses on Earth. There are several continents, and each one is huge compared with an island."),
        QAItem("What is a sweater for?", "A sweater is a warm piece of clothing. People wear it to stay cozy when the air is cool."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, A) :- setting(S), item(I), action(A), catches_heat(I), power(A, P), P >= 1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.catches_heat:
            lines.append(asp.fact("catches_heat", iid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, act.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, action=None, child=None, helper=None, child_gender=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: ASP matches Python, and generation smoke test passed.")
        return 0
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1


def tell_story(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        ACTIONS[params.action],
        params.child,
        params.helper,
        params.child_gender,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
