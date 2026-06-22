#!/usr/bin/env python3
"""
storyworlds/worlds/month_orthodontist_detergent_humor_happy_ending_misunderstanding.py
=======================================================================================

A standalone storyworld for a slice-of-life misunderstanding story about a
child, an orthodontist visit, and a detergent mix-up. The world keeps the prose
driven by simulated state: a small household scene, a comic misunderstanding,
a calm clarification, and a happy ending image that proves the day improved.

The required words are woven naturally into the story:
- month
- orthodontist
- detergent

Features:
- Humor
- Happy Ending
- Misunderstanding
Style:
- Slice of Life
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
SENSE_MIN = 2


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
    label: str
    time: str
    mood: str
    places: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Action:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    if child.memes["worry"] >= THRESHOLD and child.meters["misunderstanding"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
        child.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for action_id, action in ACTIONS.items():
            if action.sense >= SENSE_MIN:
                for item_id, item in ITEMS.items():
                    if action.id == "mixup" and "cleaning" in item.tags:
                        combos.append((setting_id, action_id, item_id))
    return combos


def _peak_worry(world: World, item_id: str) -> int:
    sim = world.copy()
    _comic_mixup(sim, sim.get("child"), sim.items[item_id], narrate=False)
    return int(sim.get("child").memes["worry"])


def _comic_mixup(world: World, child: Entity, item: Item, narrate: bool = True) -> None:
    child.meters["misunderstanding"] += 1
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    item.meters["present"] += 1
    propagate(world, narrate=narrate)


def setting_intro(world: World, setting: Setting, child: Entity, parent: Entity) -> None:
    world.say(
        f"It was a busy {setting.time} in {setting.label}, and the air felt ordinary in the nicest way."
        f" {child.id} and {parent.label_word} were getting ready for a small family errand."
    )


def month_detail(world: World, child: Entity) -> None:
    world.say(
        f"It had been a long month of braces, snacks, and careful brushing, so {child.id} knew the routine by heart."
    )


def setup_chore(world: World, parent: Entity, child: Entity, item: Item) -> None:
    world.say(
        f"{parent.id} pointed at {item.phrase} and asked for help with the laundry."
    )
    world.say(
        f"{child.id} heard the word {item.label} and thought of the shiny bottle in the bathroom."
    )


def misunderstanding(world: World, child: Entity, orthodontist: Entity, item: Item) -> None:
    child.memes["humor"] += 1
    child.memes["hope"] += 1
    world.say(
        f'"The orthodontist said to keep things clean," {child.id} thought, '
        f'"so maybe {item.label} is for braces?"'
    )
    world.say(
        f"{child.id} even pictured the orthodontist wearing a tiny apron, which made the idea feel extra funny."
    )


def clarify(world: World, orthodontist: Entity, child: Entity, item: Item, action: Action) -> None:
    world.say(
        f"At the office, the orthodontist smiled and said {child.id} had mixed up two different kinds of cleaning."
    )
    world.say(
        f'"{item.label.capitalize()} is for clothes," the orthodontist said. '
        f'"For braces, we use the gentle cleaner in the kit, not detergent."'
    )
    child.memes["humor"] += 1
    child.memes["relief"] += 2
    world.facts["clarified"] = True
    world.facts["joke"] = action.qa_text


def happy_finish(world: World, child: Entity, parent: Entity, orthodontist: Entity, item: Item) -> None:
    child.memes["joy"] += 2
    child.memes["relief"] += 1
    world.say(
        f"{child.id} laughed, tucked the detergent back on the shelf, and helped {parent.label_word} with the laundry."
    )
    world.say(
        f"Later, the orthodontist gave {child.id} a clean bill of health and a sticker for remembering the month’s routine."
    )
    world.say(
        f"That evening, {child.id} grinned at the neat bottle of detergent by the sink and the tidy smile in the mirror."
    )


def tell(setting: Setting, action: Action, item: Item,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add_entity(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    orthodontist = world.add_entity(Entity(id="Orthodontist", kind="character", type="adult", role="orthodontist", label="the orthodontist"))

    world.add_item(Item(id=item.id, label=item.label, phrase=item.phrase, tags=set(item.tags)))

    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 0.0
    world.facts["setting"] = setting
    world.facts["action"] = action
    world.facts["item"] = item
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["orthodontist"] = orthodontist

    setting_intro(world, setting, child, parent)
    month_detail(world, child)
    world.para()
    setup_chore(world, parent, child, item)
    misunderstanding(world, child, orthodontist, item)
    world.para()
    _comic_mixup(world, child, world.items[item.id], narrate=False)
    clarify(world, orthodontist, child, item, action)
    world.para()
    happy_finish(world, child, parent, orthodontist, item)
    world.facts["outcome"] = "happy"
    return world


SETTINGS = {
    "home": Setting(id="home", label="the apartment kitchen", time="afternoon", mood="cozy", places={"laundry", "sink"}),
    "clinic": Setting(id="clinic", label="the orthodontist's waiting room", time="morning", mood="bright", places={"chair", "desk"}),
}

ITEMS = {
    "detergent": Item(id="detergent", label="detergent", phrase="the detergent bottle", tags={"cleaning", "laundry"}),
    "soap": Item(id="soap", label="soap", phrase="the soap bottle", tags={"cleaning"}),
}

ACTIONS = {
    "mixup": Action(
        id="mixup",
        sense=3,
        power=2,
        text="mixed up the two kinds of cleaning",
        fail="mixed up the labels and looked very puzzled",
        qa_text="it was a funny misunderstanding about which cleaner belonged where",
        tags={"humor", "misunderstanding"},
    ),
    "ask": Action(
        id="ask",
        sense=2,
        power=1,
        text="asked a careful question",
        fail="asked a question too quietly to be heard",
        qa_text="the child asked for help instead of guessing",
        tags={"humor", "misunderstanding"},
    ),
}

NAMES = ["Mina", "Ivy", "Nora", "Lena", "June", "Ari", "Tessa", "Milo"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    action: str
    item: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "{f["item"].label}", "month", and "orthodontist".',
        f"Tell a humorous misunderstanding where {f['child'].id} thinks detergent belongs in an orthodontist routine, but the office explains the real reason kindly.",
        f"Write a happy-ending everyday story about laundry, braces, and a silly mix-up with detergent.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, ortho, item, action = f["child"], f["parent"], f["orthodontist"], f["item"], f["action"]
    return [
        QAItem(
            question=f"What was {child.id} thinking about when {parent.label_word} mentioned the {item.label}?",
            answer=f"{child.id} had a funny misunderstanding. {child.id} thought the detergent might be part of the orthodontist routine, but it was really just for laundry.",
        ),
        QAItem(
            question=f"Why did the orthodontist laugh kindly during the visit?",
            answer=f"The orthodontist laughed because {child.id} had mixed up two kinds of cleaning. The mix-up was harmless, so the grown-up just clarified it and smiled.",
        ),
        QAItem(
            question=f"What changed by the end of the month?",
            answer=f"By the end, the mix-up was cleared up and {child.id} felt relaxed. The detergent stayed by the sink for clothes, and the braces routine stayed separate.",
        ),
        QAItem(
            question=f"How did {child.id} help after the joke was explained?",
            answer=f"{child.id} put the detergent back where it belonged and helped with the laundry. That turned the confusion into an ordinary, happy family moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is detergent?",
            answer="Detergent is a cleaning soap used for washing clothes. It helps remove dirt and smells from fabric.",
        ),
        QAItem(
            question="What is an orthodontist?",
            answer="An orthodontist is a doctor who helps fix and care for teeth and braces. They know how to make smiles line up nicely.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny?",
            answer="A misunderstanding can be funny when someone guesses wrong in a harmless way. The joke comes from the surprise, and then everyone feels better once it is explained.",
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    for it in world.items.values():
        meters = {k: v for k, v in it.meters.items() if v}
        lines.append(f"  {it.id:10} (item    ) meters={dict(meters)} tags={sorted(it.tags)}")
    return "\n".join(lines)


def explain_rejection(setting_id: str, action_id: str, item_id: str) -> str:
    return f"(No story: {setting_id}, {action_id}, and {item_id} do not form a reasonable comic misunderstanding.)"


def explain_action(action_id: str) -> str:
    a = ACTIONS[action_id]
    return f"(Refusing action '{action_id}': it is too weak for a complete, reasonable story.)"


ASP_RULES = r"""
valid(S,A,I) :- setting(S), action(A), item(I), sense(A,N), min_sense(M), N >= M.
misunderstanding :- action(mixup).
happy_end :- misunderstanding.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("python only:", sorted(py - asp_set))
        print("asp only:", sorted(asp_set - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, item=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life orthodontist detergent misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, action=action, item=item, child_name=name, child_gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.action not in ACTIONS or params.item not in ITEMS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    item = ITEMS[params.item]
    world = tell(setting, action, item, params.child_name, params.child_gender, params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(setting="home", action="mixup", item="detergent", child_name="Mina", child_gender="girl", parent="mother"),
    StoryParams(setting="clinic", action="mixup", item="soap", child_name="Theo", child_gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
