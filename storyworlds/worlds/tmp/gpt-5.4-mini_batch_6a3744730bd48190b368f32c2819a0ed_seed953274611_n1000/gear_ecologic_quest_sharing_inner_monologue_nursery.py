#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gear_ecologic_quest_sharing_inner_monologue_nursery.py
======================================================================================

A small, standalone story world in a nursery-rhyme voice.

Premise
-------
A child goes on a little quest to mend a garden machine or tool, learns to share
gear, and discovers that ecologic care means using only what is needed and leaving
the rest for the bees, worms, and rain.

This world includes:
- Quest: a simple search for a missing or broken helper object
- Sharing: one child lends gear to another, or they share the work
- Inner monologue: short, child-facing thoughts woven into the scene
- Nursery rhyme style: light rhyme, repetition, soft cadence, concrete images

The script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gate
- inline ASP twin
- prompts, story QA, and world-knowledge QA
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    shares: set[str] = field(default_factory=set)
    ecologic: bool = False
    gear: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    quest_goal: str
    good_signs: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    role: str
    ecologic: bool = False
    shareable: bool = False
    fix_power: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest_item: str
    gear: str
    sharing_mode: str
    monologue: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    if "child" not in world.entities or "helper" not in world.entities or "gear" not in world.entities:
        return out
    child = world.get("child")
    helper = world.get("helper")
    gear = world.get("gear")
    if child.memes["sharing"] >= THRESHOLD and helper.memes["need"] >= THRESHOLD:
        sig = ("share", gear.id)
        if sig not in world.fired:
            world.fired.add(sig)
            gear.memes["used"] += 1
            helper.memes["relief"] += 1
            out.append("__share__")
    return out


def _r_ecologic(world: World) -> list[str]:
    out = []
    if "ground" in world.entities and "water" in world.entities:
        ground = world.get("ground")
        water = world.get("water")
        if ground.meters["wet"] < THRESHOLD and water.meters["saved"] >= THRESHOLD:
            sig = ("ecologic",)
            if sig not in world.fired:
                world.fired.add(sig)
                ground.memes["harmony"] += 1
                out.append("__eco__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("share", _r_share), Rule("ecologic", _r_ecologic)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_choice(setting: Setting, quest_item: Item, gear: Item) -> bool:
    return setting.id in {"garden", "pond", "orchard"} and quest_item.role == "lost" and gear.shareable


def sensible_gear() -> list[Item]:
    return [g for g in GEARS.values() if g.shareable]


def best_gear() -> Item:
    return max(GEARS.values(), key=lambda g: g.fix_power)


def choose_monologue(rng: random.Random) -> str:
    return rng.choice([
        "I think the bees need the bloom, and I can spare a crumb.",
        "If I share my gear, the path will still gleam and not all be mine.",
        "Little hands can mend the day with care, with care, with care.",
    ])


def predict_share(world: World) -> dict:
    sim = world.copy()
    _do_share(sim, narrate=False)
    return {
        "shared": sim.get("gear").memes["used"] >= THRESHOLD,
        "relief": sim.get("helper").memes["relief"],
    }


def _do_quest(world: World, setting: Setting, item: Item) -> None:
    child = world.get("child")
    child.memes["curiosity"] += 1
    world.say(
        f"Down by the {setting.place}, under a pear-tree sway, {child.id} set out "
        f"to find {item.phrase}. The path was soft, the morning bright, and the worms "
        f"wriggled under clay."
    )


def _do_monologue(world: World, child: Entity, monologue: str) -> None:
    child.memes["thinking"] += 1
    world.say(f'Inside {child.id}\'s head, a small thought hopped: "{monologue}"')


def _do_worry(world: World, helper: Entity, item: Item, gear: Item) -> None:
    helper.memes["need"] += 1
    world.say(
        f"{helper.id} peered at the broken {item.label} and frowned. "
        f'"Without a little {gear.label}, the row will stay down," {helper.id} said.'
    )


def _do_share_offer(world: World, child: Entity, helper: Entity, gear: Item) -> None:
    child.memes["sharing"] += 1
    child.shares.add(gear.id)
    world.say(
        f'{child.id} looked at {helper.id}, looked at the {gear.label}, and said, '
        f'"You may use my {gear.label}. We can work the garden side by side."'
    )


def _do_share(world: World, narrate: bool = True) -> None:
    gear = world.get("gear")
    helper = world.get("helper")
    gear.meters["borrowed"] += 1
    helper.memes["relief"] += 1
    if narrate:
        world.say(
            f"{helper.id} took the {gear.label} with a grin, and the little fix "
            f"could begin."
        )


def _do_ecologic_finish(world: World, setting: Setting, item: Item, gear: Item) -> None:
    water = world.get("water")
    ground = world.get("ground")
    water.meters["saved"] += 1
    ground.meters["wet"] += 0.5
    world.say(
        f"They used just enough water, not more, not more, and gave the thirsty "
        f"soil a sip. The buds stood up straight, the bees came by, and the pond "
        f"kept its blue-tongue dip."
    )
    world.say(
        f"In the end, the {item.label} was mended, the {gear.label} was shared, "
        f"and the garden stayed ecologic and fair."
    )


def tell(setting: Setting, quest_item: Item, gear: Item, sharing_mode: str,
         child: str = "Mina", child_gender: str = "girl",
         helper: str = "Toby", helper_gender: str = "boy",
         parent: str = "mother", monologue: str = "") -> World:
    world = World()
    c = world.add(Entity(id="child", kind="character", type=child_gender, label=child))
    h = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper))
    p = world.add(Entity(id="parent", kind="character", type=parent, label="the parent"))
    gi = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.label, gear=True, ecologic=gear.ecologic))
    qi = world.add(Entity(id="quest", kind="thing", type=quest_item.kind, label=quest_item.label, ecologic=quest_item.ecologic))
    ground = world.add(Entity(id="ground", kind="thing", type="ground", label="the garden bed", ecologic=True))
    water = world.add(Entity(id="water", kind="thing", type="water", label="water", ecologic=True))
    c.memes["curiosity"] = 1
    h.memes["need"] = 1
    world.facts.update(setting=setting, quest_item=quest_item, gear_item=gear, sharing_mode=sharing_mode,
                       child=c, helper=h, parent=p, gear=gi, quest=qi, ground=ground, water=water)

    world.say(
        f"Under a tuft of thyme and a shy green tree, {child} began a quest for the day. "
        f"{setting.scene}"
    )
    _do_quest(world, setting, quest_item)
    world.para()
    _do_monologue(world, c, monologue or choose_monologue(random.Random(0)))
    _do_worry(world, h, quest_item, gear)
    _do_share_offer(world, c, h, gear)
    propagate(world, narrate=True)
    world.para()
    _do_ecologic_finish(world, setting, quest_item, gear)
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="garden gate", scene="A wheelbarrow waited by the rosemary, and a snail wore a silver trail.", quest_goal="the bean row"),
    "orchard": Setting(id="orchard", place="orchard lane", scene="Apples bobbed like lanterns, and the grass wore dew.", quest_goal="the apple cart"),
    "pond": Setting(id="pond", place="pond-side path", scene="Reeds nodded at the water, and dragonflies stitched blue thread in the air.", quest_goal="the lily patch"),
}

QUEST_ITEMS = {
    "spade": Item(id="spade", label="spade", phrase="a little spade", kind="tool", role="lost", ecologic=True, shareable=False, fix_power=1, tags={"soil", "quest"}),
    "trowel": Item(id="trowel", label="trowel", phrase="a tidy trowel", kind="tool", role="lost", ecologic=True, shareable=False, fix_power=1, tags={"soil", "quest"}),
    "bucket": Item(id="bucket", label="bucket", phrase="a bright little bucket", kind="tool", role="lost", ecologic=False, shareable=False, fix_power=1, tags={"water", "quest"}),
}

GEARS = {
    "gloves": Item(id="gloves", label="gardening gloves", phrase="gardening gloves", kind="gear", role="borrowed", ecologic=True, shareable=True, fix_power=2, tags={"gear", "share"}),
    "hat": Item(id="hat", label="sun hat", phrase="a sun hat", kind="gear", role="borrowed", ecologic=True, shareable=True, fix_power=1, tags={"gear", "share"}),
    "hose": Item(id="hose", label="water hose", phrase="a water hose", kind="gear", role="borrowed", ecologic=True, shareable=True, fix_power=3, tags={"water", "share"}),
}

NAMES_GIRL = ["Mina", "Lila", "Poppy", "Nell", "Wren"]
NAMES_BOY = ["Toby", "Milo", "Robin", "Finn", "Jude"]
TRAITS = ["careful", "cheery", "gentle", "curious", "helpful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for qid, q in QUEST_ITEMS.items():
            for gid, g in GEARS.items():
                if valid_choice(s, q, g):
                    combos.append((sid, qid, gid))
    return combos


def explain_rejection(setting: Setting, quest_item: Item, gear: Item) -> str:
    return f"(No story: in {setting.id}, {gear.label} does not fit this quest well enough for a shared, ecologic fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about a quest, sharing, and ecologic care.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--sharing-mode", choices=["sharing", "solo"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.quest_item and args.gear:
        if not valid_choice(SETTINGS[args.setting], QUEST_ITEMS[args.quest_item], GEARS[args.gear]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], QUEST_ITEMS[args.quest_item], GEARS[args.gear]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest_item is None or c[1] == args.quest_item)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, qid, gid = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    sharing_mode = args.sharing_mode or "sharing"
    monologue = choose_monologue(rng)
    return StoryParams(setting=sid, quest_item=qid, gear=gid, sharing_mode=sharing_mode,
                       monologue=monologue, child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story for a young child that includes the words "gear" and "ecologic".',
        f"Tell a small quest story where {f['child'].id} finds a lost garden thing, shares gear with {f['helper'].id}, and keeps the ending ecologic.",
        f"Write a gentle rhyme about sharing {f['gear'].label} on a garden quest, with a child thinking quietly inside their head.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    quest = f["quest_item"]
    gear = f["gear_item"]
    setting = f["setting"]
    return [
        QAItem(
            question="What was the child looking for?",
            answer=f"{child.id} was looking for {quest.phrase} on a little quest in {setting.place}. The search gave the story its starting worry and its gentle adventure."
        ),
        QAItem(
            question="What did the child think inside their head?",
            answer=f"{child.id} thought, “{f['monologue']}” That inner thought helped {child.id} choose a kind and careful way to solve the problem."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{child.id} shared the {gear.label} with {helper.id} and worked together. Sharing let them finish the garden task without waste, which made the ending ecologic."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ecologic mean in a story like this?",
            answer="Ecologic means caring for living things and not wasting what the garden needs. In this world, that means using just enough water and sharing tools instead of grabbing more."
        ),
        QAItem(
            question="Why is sharing gear helpful?",
            answer="Sharing gear helps because one tool can do its job for more than one person. It also keeps the story kind and calm, with less waste and more teamwork."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search for something important. In a nursery story, it feels like a little adventure with a clear goal."
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest_item not in QUEST_ITEMS or params.gear not in GEARS:
        raise StoryError("Invalid params.")
    setting = SETTINGS[params.setting]
    quest_item = QUEST_ITEMS[params.quest_item]
    gear = GEARS[params.gear]
    if not valid_choice(setting, quest_item, gear):
        raise StoryError(explain_rejection(setting, quest_item, gear))
    world = tell(setting, quest_item, gear, params.sharing_mode, params.child, params.child_gender,
                 params.helper, params.helper_gender, params.parent, params.monologue)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,G) :- setting(S), quest_item(Q), gear(G), shareable(G), quest_lost(Q), ecologic(G), setting_ok(S).
shareable_gear(G) :- gear(G), shareable(G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if sid in {"garden", "pond", "orchard"}:
            lines.append(asp.fact("setting_ok", sid))
    for qid, q in QUEST_ITEMS.items():
        lines.append(asp.fact("quest_item", qid))
        if q.role == "lost":
            lines.append(asp.fact("quest_lost", qid))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        if g.shareable:
            lines.append(asp.fact("shareable", gid))
        if g.ecologic:
            lines.append(asp.fact("ecologic", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        return 1
    return rc


CURATED = [
    StoryParams(setting="garden", quest_item="spade", gear="gloves", sharing_mode="sharing",
                monologue="I think the worms would like a soft path.", child="Mina", child_gender="girl",
                helper="Toby", helper_gender="boy", parent="mother"),
    StoryParams(setting="orchard", quest_item="trowel", gear="hat", sharing_mode="sharing",
                monologue="A little help can be a little song.", child="Lila", child_gender="girl",
                helper="Robin", helper_gender="boy", parent="father"),
    StoryParams(setting="pond", quest_item="bucket", gear="hose", sharing_mode="sharing",
                monologue="If I share, the pond can stay sweet and neat.", child="Jude", child_gender="boy",
                helper="Wren", helper_gender="girl", parent="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: quest, sharing, inner monologue, ecologic care.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--sharing-mode", choices=["sharing", "solo"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, q, g in asp_valid_combos():
            print(f"  {s:7} {q:8} {g}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def explain_rejection_for_params(args: argparse.Namespace, rng: random.Random) -> Optional[str]:
    return None


def generate_story_text() -> str:
    return ""


def dump_world(world: World) -> str:
    return dump_trace(world)


if __name__ == "__main__":
    main()
