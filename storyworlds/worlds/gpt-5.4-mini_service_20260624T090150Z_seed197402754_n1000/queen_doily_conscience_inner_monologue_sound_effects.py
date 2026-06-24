#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a queen, a doily, and a conscience.

Premise:
A queen loves a delicate doily and wants to place it somewhere lovely.
Her conscience notices when she is tempted to use it in a careless way.

Turn:
The queen hears her inner monologue, makes a small mistake, and the sound
effects of the mistake reveal why it matters.

Resolution:
She chooses a kinder, more careful use, and the doily becomes part of a
properly honored scene.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- a reasonableness gate
- inline ASP twin rules
- story, QA, trace, and JSON output
- child-facing fairy-tale prose with a clear beginning, middle, and ending
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"queen", "woman", "girl", "mother"}
        male = {"king", "man", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the sunlit hall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    delicate: bool = True
    clean: bool = True


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    risk: str
    mood: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    action: str
    item: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.item: Optional[Entity] = None
        self.action: Optional[Action] = None
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.item = copy.deepcopy(self.item)
        clone.action = self.action
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_damage(world: World) -> list[str]:
    out = []
    queen = next((e for e in world.entities.values() if e.type == "queen"), None)
    item = world.item
    action = world.action
    if not queen or not item or not action:
        return out
    if queen.memes.get("careless", 0) < THRESHOLD:
        return out
    sig = ("damage", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["torn"] = item.meters.get("torn", 0) + 1
    item.clean = False
    queen.memes["worry"] = queen.memes.get("worry", 0) + 1
    out.append(f"Rip, went the fabric, and the doily was no longer as lovely.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    queen = next((e for e in world.entities.values() if e.type == "queen"), None)
    item = world.item
    if not queen or not item:
        return out
    if queen.memes.get("kindness", 0) < THRESHOLD:
        return out
    if item.meters.get("torn", 0) < THRESHOLD:
        return out
    sig = ("repair", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["mended"] = 1
    item.clean = True
    queen.memes["peace"] = queen.memes.get("peace", 0) + 1
    out.append("Snip, stitch, and smooth—the doily grew beautiful again.")
    return out


CAUSAL_RULES = [_r_damage, _r_repair]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "hall": Setting(place="the sunlit hall", affords={"tea", "decorate"}),
    "garden": Setting(place="the rose garden", affords={"tea", "decorate"}),
    "parlor": Setting(place="the quiet parlor", affords={"tea", "sew"}),
}

ACTIONS = {
    "tea": Action(
        id="tea",
        verb="set the doily under the tea tray",
        gerund="setting the doily under the tea tray",
        rush="rush to put it under the kettle",
        sound="clink",
        risk="the hot tray would stain it",
        mood="proper",
        keyword="tea",
        tags={"tea", "cloth"},
    ),
    "decorate": Action(
        id="decorate",
        verb="decorate the throne with the doily",
        gerund="decorating the throne with the doily",
        rush="hurry to pin it on the chair",
        sound="flutter",
        risk="the chair would snag it",
        mood="proud",
        keyword="decorate",
        tags={"cloth", "throne"},
    ),
    "sew": Action(
        id="sew",
        verb="stitch the doily onto a cushion",
        gerund="stitching the doily onto a cushion",
        rush="rush to sew it crookedly",
        sound="tap-tap",
        risk="the needle would pull a thread loose",
        mood="careful",
        keyword="sew",
        tags={"cloth", "needle"},
    ),
}

ITEMS = {
    "doily": Item(id="doily", label="doily", phrase="a lace doily", region="table"),
}

NAMES = ["Elara", "Mira", "Nora", "Ivy", "Luna", "Rosalind"]
TRAITS = ["gentle", "proud", "curious", "careful", "stubborn"]


def is_reasonable(action: Action, item: Item) -> bool:
    return item.region == "table" and action.id in {"tea", "decorate", "sew"}


def select_action(setting: Setting, rng: random.Random) -> Action:
    choices = [ACTIONS[a] for a in sorted(setting.affords) if a in ACTIONS]
    if not choices:
        raise StoryError("No valid action fits this setting.")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(sorted(SETTINGS))
    setting = SETTINGS[setting_key]
    action_key = args.action or rng.choice(sorted(setting.affords))
    if action_key not in ACTIONS or action_key not in setting.affords:
        raise StoryError("That action does not fit the chosen setting.")
    item_key = args.item or "doily"
    if item_key not in ITEMS:
        raise StoryError("Unknown item.")
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES)
    return StoryParams(setting=setting_key, action=action_key, item=item_key, name=name)


def predict_damage(world: World, queen: Entity, action: Action, item: Entity) -> bool:
    sim = world.copy()
    q = sim.get(queen.id)
    q.memes["careless"] = 1
    simulate_action(sim, q, action, item, narrate=False)
    return bool(sim.item and sim.item.meters.get("torn", 0) >= THRESHOLD)


def simulate_action(world: World, queen: Entity, action: Action, item: Entity, narrate: bool = True) -> None:
    queen.memes["curiosity"] = queen.memes.get("curiosity", 0) + 1
    world.say(f"The queen looked at {item.label} and felt her heart flutter with a small wish.")
    world.say(f'Her inner monologue whispered, "What if I use it in a grander way?"')
    world.say(f"At once came the soft sound of thought: hmm, hmm.")
    if narrate:
        queen.memes["careless"] = queen.memes.get("careless", 0) + 1
    world.say(f"Then she tried to {action.verb}.")
    world.say(f"Sound effects answered her: {action.sound}! {action.sound}!")
    if narrate:
        propagate(world, narrate=True)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    item_cfg = ITEMS[params.item]
    world = World(setting)
    world.action = action
    queen = world.add(Entity(id=params.name, kind="character", type="queen"))
    conscience = world.add(Entity(id="conscience", kind="character", type="conscience"))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase))
    world.item = item

    world.say(f"Once upon a time, Queen {queen.id} lived in {setting.place}.")
    world.say(f"She kept {item.phrase} close, because it was lovely and light as a snowflake.")
    world.para()

    world.say(f"One bright day, the queen wished to {action.verb}.")
    world.say(f"Her conscience sat nearby like a tiny lantern and warned, in a hush, that {action.risk}.")
    world.say(f'Inside her head, a kinder thought replied, "A pretty thing should be used with care."')
    world.say(f"So the queen stood still and listened.")

    world.para()
    world.say(f"First she almost made a careless choice.")
    queen.memes["careless"] = 1
    if predict_damage(world, queen, action, item):
        world.say(f"She heard the soft warning and chose not to rush.")
    simulate_action(world, queen, action, item, narrate=True)

    world.para()
    queen.memes["kindness"] = 1
    queen.memes["careless"] = 0
    world.say(f"Then the queen thought again and smiled at her conscience.")
    world.say(f'She said, "I can honor this doily in a finer way."')
    world.say(f"So she placed it where it belonged, and the room looked gentle and bright.")
    if item.meters.get("torn", 0) >= THRESHOLD:
        propagate(world, narrate=True)
    else:
        world.say("No rip came at all, only a quiet little rustle.")
    world.say(f"At the end, the doily stayed clean, and the queen felt peaceful inside.")

    world.facts.update(
        queen=queen,
        conscience=conscience,
        item=item,
        action=action,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about a queen, a doily, and a conscience.',
        f"Tell a gentle story where Queen {f['queen'].id} wants to {f['action'].verb} but listens to her conscience first.",
        f"Write a child-friendly fairy tale that includes the word '{f['item'].label}' and ends with a kinder choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    queen = f["queen"]
    action = f["action"]
    item = f["item"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about Queen {queen.id}, who lived in {setting.place} and cared about a doily.",
        ),
        QAItem(
            question=f"What did the queen want to do with the doily?",
            answer=f"She wanted to {action.verb}.",
        ),
        QAItem(
            question="What did her conscience help her do?",
            answer="Her conscience helped her pause, think again, and choose a kinder, safer way to use the doily.",
        ),
        QAItem(
            question="What was the ending like?",
            answer="The doily stayed clean, the room looked gentle and bright, and the queen felt peaceful inside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a doily?",
            answer="A doily is a small, delicate cloth or paper mat that people use to make a table or tray look neat and pretty.",
        ),
        QAItem(
            question="What is a conscience?",
            answer="A conscience is the quiet part inside a person that helps them tell right from wrong and choose a kind action.",
        ),
        QAItem(
            question="Why are soft cloth things handled carefully?",
            answer="Soft cloth things can snag or tear easily, so they are handled carefully to keep them pretty for a long time.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, action.risk))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, item.region))
    return "\n".join(lines)


ASP_RULES = r"""
possible(S,A,I) :- setting(S), affords(S,A), action(A), item(I), region(I,table).
reasonable(S,A,I) :- possible(S,A,I).
#show reasonable/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {(s, a, i) for s in SETTINGS for a in SETTINGS[s].affords for i in ITEMS if is_reasonable(ACTIONS[a], ITEMS[i])}
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld: queen, doily, conscience.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="hall", action="decorate", item="doily", name="Elara"),
    StoryParams(setting="garden", action="tea", item="doily", name="Mira"),
    StoryParams(setting="parlor", action="sew", item="doily", name="Nora"),
]


def resolve_random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    actions = sorted(SETTINGS[setting].affords)
    action = args.action or rng.choice(actions)
    item = args.item or "doily"
    name = args.name or rng.choice(NAMES)
    if action not in SETTINGS[setting].affords:
        raise StoryError("That action does not fit the chosen setting.")
    return StoryParams(setting=setting, action=action, item=item, name=name)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_reasonable()
        print(f"{len(combos)} reasonable combinations:")
        for s, a, i in combos:
            print(f"  {s:8} {a:10} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_random_params(args, rng)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
