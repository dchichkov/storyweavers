#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baptism_reconciliation_bedtime_story.py
=======================================================================

A small, self-contained storyworld for a bedtime story about baptism and
reconciliation.

Domain sketch
-------------
A child is getting ready for bed after a baptism day. Something awkward or
hurtful happened earlier in the day: a spilled keepsake, a snapped word, or a
missed promise. At bedtime, a grown-up helps the child apologize, forgive, and
make things right. The story ends with calm sleep, a repaired bond, and a small
baptism keepsake image that proves the change.

This script follows the Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- simulated world state with meters and memes
- story-grounded QA from world state, not from rendered text

The tone aims for bedtime-story softness: concrete, calm, and child-facing.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def add_meter(self, key: str, value: float = 1.0) -> None:
        self.meters[key] = self.m(key) + value

    def add_meme(self, key: str, value: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "dad", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    bedtime_phrase: str
    night_sound: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mishap:
    id: str
    label: str
    action: str
    hurt: str
    risk: str
    severity: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Reconciliation:
    id: str
    method: str
    words: str
    repair: str
    warmth: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_misery(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.m("hurt") >= THRESHOLD and ("hurt", e.id) not in world.fired:
            world.fired.add(("hurt", e.id))
            if "child" in world.entities:
                world.get("child").add_meme("sadness", 1)
            out.append("__hurt__")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    if world.get("child").m("forgiven") >= THRESHOLD and ("repair",) not in world.fired:
        world.fired.add(("repair",))
        world.get("bond").add_meter("warmth", 1)
        out.append("__warmth__")
    return out


CAUSAL_RULES = [Rule("misery", "social", _r_misery), Rule("repair", "social", _r_repair)]


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


def reasonable_combo(mishap: Mishap, reco: Reconciliation) -> bool:
    return mishap.severity >= 1 and reco.warmth >= 1


def valid_combos() -> list[tuple[str, str]]:
    return [(m.id, r.id) for m in MISHAPS.values() for r in RECONCILIATIONS.values() if reasonable_combo(m, r)]


def bedtime_intro(world: World, child: Entity, parent: Entity, setting: Setting, baptism: str) -> None:
    world.say(
        f"By bedtime, {setting.place} had gone soft and quiet. {setting.night_sound}."
        f" {child.id} was still wearing a little keepsake from {baptism} day, and "
        f"{parent.label_word} sat beside {child.pronoun('object')} with a warm lamp."
    )


def describe_mishap(world: World, child: Entity, mishap: Mishap) -> None:
    child.add_meme("guilt", 1)
    child.add_meter("hurt", 1)
    world.say(
        f"Earlier, {child.id} had {mishap.action}, and {mishap.hurt}. "
        f"It made the room feel heavy, like a blanket pulled a little too tight."
    )
    world.say(
        f"{child.id} kept thinking about {mishap.risk}, and the thought would not let "
        f"{child.pronoun('possessive')} eyes grow sleepy."
    )


def worried_parent(world: World, parent: Entity, child: Entity, mishap: Mishap) -> None:
    world.say(
        f"{parent.label_word.capitalize()} brushed the hair from {child.id}'s forehead and said, "
        f'"We can fix this. A small wrong thing does not have to stay wrong."'
    )


def apology(world: World, child: Entity, parent: Entity, recon: Reconciliation) -> None:
    child.add_meme("courage", 1)
    child.add_meme("forgiven", 1)
    world.say(
        f"{child.id} took a breath and used {recon.words}. "
        f"{recon.repair.capitalize()}, and the room felt less sharp at once."
    )


def forgiveness(world: World, parent: Entity, child: Entity, recon: Reconciliation) -> None:
    parent.add_meme("forgiveness", 1)
    parent.add_meme("warmth", 1)
    world.say(
        f"{parent.label_word.capitalize()} nodded, held {child.pronoun('object')} close, and forgave {child.pronoun('object')} right away. "
        f'"That is what love does after a hard moment," {parent.pronoun()} whispered.'
    )
    world.say(
        f"The little hurt stayed in the story, but it no longer sat between them."
    )


def settle(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.add_meme("sleepy", 1)
    world.say(
        f"Then {setting.bedtime_phrase}. {child.id} curled under the quilt, "
        f"listening to {setting.night_sound}, while {parent.label_word} tucked the blanket under {child.pronoun('possessive')} chin."
    )
    world.say(
        f"The baptism keepsake rested on the nightstand, clean and still, and {child.id} finally fell asleep feeling close again."
    )


def tell(setting: Setting, mishap: Mishap, recon: Reconciliation, baptism: str,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bond = world.add(Entity(id="bond", type="thing", label="their bond"))

    bedtime_intro(world, child, parent, setting, baptism)
    world.para()
    describe_mishap(world, child, mishap)
    worried_parent(world, parent, child, mishap)

    world.para()
    apology(world, child, recon)
    forgiveness(world, parent, child, recon)
    propagate(world, narrate=False)

    world.para()
    settle(world, child, parent, setting)

    world.facts.update(
        child=child, parent=parent, bond=bond, setting=setting, mishap=mishap,
        recon=recon, baptism=baptism, reconciled=child.memes.get("forgiven", 0.0) >= THRESHOLD
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "It was bedtime now", "The house hummed softly"),
    "small_room": Setting("small_room", "the small room", "The moon was already up", "Crickets sang outside"),
    "attic_room": Setting("attic_room", "the attic room", "Night was deep and gentle", "The old floorboards sighed"),
}

MISHAPS = {
    "spilled_water": Mishap("spilled_water", "spilled water", "spilled the cup of water on the floor", "the rug got wet", "the floor could be slippery", 1),
    "snapped_word": Mishap("snapped_word", "snapped word", "said a sharp word to the parent", "the parent looked hurt", "the hurt might sit in the heart until bedtime", 2),
    "broken_shell": Mishap("broken_shell", "broken shell", "dropped the baptism shell and it cracked", "the shell cracked into two pieces", "the keepsake might not feel special anymore", 2),
}

RECONCILIATIONS = {
    "sorry_hug": Reconciliation("sorry_hug", "a soft sorry and a hug", "I'm sorry", "The child hugged the parent and the apology felt real", 2),
    "fix_and_say": Reconciliation("fix_and_say", "cleaning it up and saying sorry", "I'm sorry, and I'll help fix it", "The child wiped the spill, or picked up the pieces, with careful hands", 2),
    "pray_and_peace": Reconciliation("pray_and_peace", "a quiet prayer and a gentle sorry", "I'm sorry, can we make peace?", "The child bowed their head, then looked up braver than before", 1),
}

BAPTISM_WORDS = [
    "baptism",
    "the baptism candle",
    "the little baptism shell",
    "the white ribbon from baptism",
]

NAMES = ["Mia", "Noah", "Luna", "Eli", "Ava", "Theo", "Ivy", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "baptism" and ends with forgiveness.',
        f"Tell a gentle bedtime story where {f['child'].id} feels bad after an earlier mishap, says sorry, and makes peace before sleep.",
        f"Write a soft story about baptism night, a small hurt, and reconciliation, with a calm ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, mishap, recon = f["child"], f["parent"], f["mishap"], f["recon"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, at bedtime after a baptism day."),
        ("What went wrong earlier?",
         f"Earlier, {child.id} {mishap.action}. That hurt {mishap.risk}, and it made {child.id} feel sorry."),
        ("How did they make things right?",
         f"{child.id} used {recon.words} and {parent.label_word} forgave {child.pronoun('object')}. "
         f"They cleaned up, or mended what could be mended, and the feeling between them got warm again."),
        ("How did the story end?",
         f"It ended with {child.id} falling asleep peacefully. The baptism keepsake stayed on the nightstand, and the hurt was no longer between them."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is baptism?",
         "Baptism is a special ceremony in many Christian families. It is a gentle sign of welcoming a person into faith and love."),
        ("What does reconciliation mean?",
         "Reconciliation means making peace after a hurt or a mistake. It is when people apologize, forgive, and feel close again."),
        ("Why is bedtime a good time for a gentle talk?",
         "Bedtime is quiet, so people can slow down, listen, and speak softly. That makes it easier to apologize and forgive."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(mishap: Mishap, recon: Reconciliation) -> str:
    if not reasonable_combo(mishap, recon):
        return "(No story: this combination does not support a believable bedtime reconciliation.)"
    return "(No story: invalid combination.)"


@dataclass
@dataclass
class StoryParams:
    setting: str
    mishap: str
    reconciliation: str
    baptism_word: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CURATED = [
    StoryParams("nursery", "snapped_word", "sorry_hug", "baptism", "Mia", "girl", "mother"),
    StoryParams("small_room", "spilled_water", "fix_and_say", "the baptism candle", "Noah", "boy", "father"),
    StoryParams("attic_room", "broken_shell", "pray_and_peace", "the little baptism shell", "Luna", "girl", "mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s.id, m.id, r.id) for s in SETTINGS.values() for m in MISHAPS.values() for r in RECONCILIATIONS.values() if reasonable_combo(m, r)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about baptism and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--baptism-word", choices=["baptism", "the baptism candle", "the little baptism shell", "the white ribbon from baptism"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.mishap and args.reconciliation:
        if (args.setting, args.mishap, args.reconciliation) not in valid_combos():
            raise StoryError(explain_rejection(MISHAPS[args.mishap], RECONCILIATIONS[args.reconciliation]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mishap is None or c[1] == args.mishap)
              and (args.reconciliation is None or c[2] == args.reconciliation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mishap, reconciliation = rng.choice(sorted(combos))
    mk = args.baptism_word or rng.choice(BAPTISM_WORDS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mishap, reconciliation, mk, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISHAPS[params.mishap], RECONCILIATIONS[params.reconciliation],
                 params.baptism_word, params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
valid(S, M, R) :- setting(S), mishap(M), reconciliation(R).
reconciled :- chose_reconciliation(R), warmth(R, W), W >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        lines.append(asp.fact("severity", mid, m.severity))
    for rid, r in RECONCILIATIONS.items():
        lines.append(asp.fact("reconciliation", rid))
        lines.append(asp.fact("warmth", rid, r.warmth))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
