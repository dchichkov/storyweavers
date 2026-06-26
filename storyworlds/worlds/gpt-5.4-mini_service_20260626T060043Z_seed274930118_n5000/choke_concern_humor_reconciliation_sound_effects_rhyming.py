#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/choke_concern_humor_reconciliation_sound_effects_rhyming.py
====================================================================================================

A tiny classical storyworld: a rhyming snack-time tale where a child gets a
tickly choke scare, a grown-up shows concern, and the pair recovers with humor,
reconciliation, and sound effects.

The premise is simple and state-driven:
- a child wants a crunchy snack and a silly game
- the snack can become a choke concern if eaten too fast
- a caretaker notices, intervenes, and helps the child sip water
- the child laughs, calms down, and the two reconcile

This script follows the Storyweavers world contract:
- standalone stdlib script
- imports shared result containers eagerly
- ASP twin with inline rules and an ASP fact emitter
- supports the standard CLI flags
"""

from __future__ import annotations

import argparse
import dataclasses
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safe": 0.0, "crumbly": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "concern": 0.0, "humor": 0.0, "reconciliation": 0.0, "choke": 0.0}

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
    sound: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crunch: str
    crumbs: str
    risk: str
    sound: str
    safe_method: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    snack: str
    name: str
    gender: str
    caretaker: str
    tone: str = "rhyming"
    seed: Optional[int] = None


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _rule_concern(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child_id"])
    snack = world.get(world.facts["snack_id"])
    if child.memes["choke"] >= THRESHOLD and ("concern", child.id) not in world.fired:
        world.fired.add(("concern", child.id))
        caretaker = world.get(world.facts["caretaker_id"])
        caretaker.memes["concern"] += 1
        out.append(f"{caretaker.label} felt concern and hurried near.")
    if snack.meters.get("crumbly", 0.0) >= THRESHOLD and ("crumbles", snack.id) not in world.fired:
        world.fired.add(("crumbles", snack.id))
        out.append(f"{snack.label} went crackle-crack, with a tiny crumbly scene.")
    return out


def _rule_reconcile(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child_id"])
    caretaker = world.get(world.facts["caretaker_id"])
    if child.memes["joy"] >= THRESHOLD and caretaker.memes["concern"] >= THRESHOLD and ("reconcile", child.id) not in world.fired:
        world.fired.add(("reconcile", child.id))
        child.memes["reconciliation"] += 1
        caretaker.memes["reconciliation"] += 1
        child.memes["concern"] = 0.0
        caretaker.memes["concern"] = 0.0
        out.append("They smiled and made peace with a squeeze.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_concern, _rule_reconcile):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_setting() -> dict[str, Setting]:
    return {
        "kitchen": Setting(place="the kitchen", sound="clink", afford={"cracker", "apple"}),
        "porch": Setting(place="the porch", sound="tap", afford={"cracker"}),
        "picnic": Setting(place="the picnic blanket", sound="rustle", afford={"cracker", "apple"}),
    }


def build_snacks() -> dict[str, Snack]:
    return {
        "cracker": Snack(
            id="cracker",
            label="cracker",
            phrase="a crisp little cracker",
            crunch="crunch",
            crumbs="crumbs",
            risk="could tickle the throat",
            sound="crack",
            safe_method="sip water between bites",
            tags={"food", "crunch", "sound"},
        ),
        "apple": Snack(
            id="apple",
            label="apple slice",
            phrase="a juicy apple slice",
            crunch="munch",
            crumbs="bits",
            risk="could lodge in a hurry",
            sound="chomp",
            safe_method="take tiny bites and chew slowly",
            tags={"food", "sound"},
        ),
    }


SETTINGS = build_setting()
SNACKS = build_snacks()

NAMES = {
    "girl": ["Mina", "Tara", "Lila", "Nora", "Zia"],
    "boy": ["Theo", "Ben", "Milo", "Finn", "Owen"],
}

TRAITS = ["silly", "spry", "bright", "bouncy", "cheery"]

KNOWLEDGE = {
    "crunch": [("What does crunchy mean?", "Crunchy means something makes a crisp sound when you bite it.")],
    "food": [("Why do people chew food?", "People chew food to make it small and soft enough to swallow safely.")],
    "sound": [("What is a sound effect in a story?", "A sound effect is a word that helps you hear an action, like crackle or tap.")],
}


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for snack_id in setting.afford:
            out.append((s_id, snack_id))
    return sorted(out)


def explain_rejection(setting: str, snack: str) -> str:
    return f"(No story: {snack} does not fit the {setting} scene in a sensible, snack-time way.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for snack in sorted(setting.afford):
            lines.append(asp.fact("affords", sid, snack))
    for snid, snack in SNACKS.items():
        lines.append(asp.fact("snack", snid))
        lines.append(asp.fact("sound_of", snid, snack.sound))
        lines.append(asp.fact("risk_of", snid, snack.risk))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,N) :- affords(S,N).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming snack story with concern, humor, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.setting and args.snack and (args.setting, args.snack) not in combos:
        raise StoryError(explain_rejection(args.setting, args.snack))
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.snack is None or c[1] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, snack=snack, name=name, gender=gender, caretaker=caretaker)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    care = world.add(Entity(id="caretaker", kind="character", type=params.caretaker, label=params.caretaker))
    snack_cfg = SNACKS[params.snack]
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase, owner=child.id, caretaker=care.id))
    world.facts = {"child_id": child.id, "caretaker_id": care.id, "snack_id": snack.id, "snack_cfg": snack_cfg, "params": params}
    return world


def tell(world: World) -> None:
    p = world.facts["params"]
    child = world.get(world.facts["child_id"])
    care = world.get(world.facts["caretaker_id"])
    snack = world.get(world.facts["snack_id"])
    cfg: Snack = world.facts["snack_cfg"]

    world.say(f"At {world.setting.place}, {child.label} was lively and light,")
    world.say(f"with a grin and a giggle and a snack in sight.")
    world.say(f"{child.label} loved the {cfg.label}, so {cfg.sound}-ly neat,")
    world.say(f"and {child.pronoun('subject')} went {cfg.sound}-{cfg.sound}, eager to eat.")

    world.para()
    child.meters["crumbly"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.label} said, \"{cfg.crunch}, {cfg.crunch}!\" with a playful hooray,")
    world.say(f"but the quick little bites made the crumbs leap away.")
    world.say(f"A tiny dry tickle gave a startled concern,")
    child.memes["choke"] += 1
    propagate(world, narrate=False)
    world.say(f"and {child.label} gave a little cough: \"Ahem-hem!\" in turn.")

    world.para()
    care.memes["concern"] += 1
    world.say(f"{care.label} came at once with a worried, warm frown,")
    world.say(f"and said, \"Slow and low, little one, let the snack settle down.\"")
    world.say(f"Then a cup made a glug-glug, and water went swish,")
    world.say(f"to chase the cheeky choke worry right out of the dish.")
    child.meters["safe"] += 1
    child.memes["humor"] += 1
    world.say(f"{child.label} blinked, then giggled: \"That cough was a joke!\"")
    world.say(f"\"A hiccupy hiccup, not a dragon of smoke!\"")

    world.para()
    child.memes["joy"] += 1
    care.memes["joy"] += 1
    child.memes["reconciliation"] += 1
    care.memes["reconciliation"] += 1
    child.memes["concern"] = 0.0
    care.memes["concern"] = 0.0
    world.say(f"They shared a small smile, and the cloud drifted by,")
    world.say(f"then the two of them laughed with a bright, friendly sigh.")
    world.say(f"No more worry, no more fright; all was calm, all was right,")
    world.say(f"and the snack-time duet ended in cheerful delight.")

    world.facts["resolved"] = True
    world.facts["theme"] = "rhyming"


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    snack: Snack = world.facts["snack_cfg"]
    return [
        f'Write a short rhyming story for a child named {p.name} with the words "choke" and "concern".',
        f"Tell a playful snack-time tale where {p.name} takes {snack.phrase}, and {p.caretaker} shows concern in a gentle way.",
        f"Write a story with sound effects like {snack.sound}, humor, and reconciliation after a tiny choke scare.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    snack: Snack = world.facts["snack_cfg"]
    return [
        QAItem(
            question=f"Why did {p.caretaker} feel concern during the snack time?",
            answer=f"{p.caretaker.capitalize()} felt concern because {p.name} was eating {snack.phrase} too quickly and had a tiny choke scare.",
        ),
        QAItem(
            question=f"What helped {p.name} feel safe again?",
            answer=f"A cup of water, slow bites, and kind words helped {p.name} feel safe again.",
        ),
        QAItem(
            question=f"How did the story end after the worry?",
            answer=f"It ended with humor, reconciliation, and both of them laughing together after the little scare.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["snack_cfg"].tags)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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
    StoryParams(setting="kitchen", snack="cracker", name="Mina", gender="girl", caretaker="mother"),
    StoryParams(setting="porch", snack="cracker", name="Theo", gender="boy", caretaker="father"),
    StoryParams(setting="picnic", snack="apple", name="Lila", gender="girl", caretaker="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for s, n in vals:
            print(f"  {s:8} {n}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
