#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pregnant_memory_twist_tall_tale.py
===================================================================

A standalone story world for a tiny Tall Tale domain: a child or family member
keeps an ordinary memory, something surprising happens, and the memory turns out
to be the clue that helps everyone understand the twist.

Seed words: pregnant, memory
Feature: Twist
Style: Tall Tale

This world tells short, child-facing tall tales with:
- a remembered object or promise,
- a surprising later reveal,
- a clean twist that re-frames the beginning,
- an ending image that proves what changed.

The model is intentionally small and constraint-checked. It uses physical meters
and emotional memes on typed entities, plus a Python gate and inline ASP twin.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    sound: str
    big_image: str


@dataclass
class MemoryObject:
    id: str
    label: str
    phrase: str
    hidden_clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    setup: str
    reveal: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["unease"] += 1
        out.append("__worry__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["reveal"] < THRESHOLD:
            continue
        sig = ("reveal", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["astonishment"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("reveal", "social", _r_reveal)]


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


def memory_at_risk(mem: MemoryObject) -> bool:
    return bool(mem.hidden_clue)


def sensible_twists() -> list[Twist]:
    return [t for t in TWISTS.values() if t.id in {"barn", "lantern", "mule"}]


def best_twist() -> Twist:
    return TWISTS["barn"]


def twist_is_reasonable(twist: Twist, memory: MemoryObject) -> bool:
    return memory_at_risk(memory) and bool(twist.reveal)


def predict(world: World, memory_id: str) -> dict:
    sim = world.copy()
    sim.get("memory").meters["reveal"] += 1
    propagate(sim, narrate=False)
    return {"revealed": sim.get("memory").meters["reveal"] >= THRESHOLD}


def setup(world: World, hero: Entity, elder: Entity, memory: MemoryObject, twist: Twist) -> None:
    hero.memes["curiosity"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"Now and then, in the long and lonesome {world.setting.place}, "
        f"{hero.id} carried a memory as carefully as a biscuit in a pocket. "
        f"It was {memory.phrase}, and {memory.hidden_clue}."
    )
    world.say(
        f"{elder.id} said the memory was as plain as fence paint, but "
        f"{twist.setup}."
    )


def trouble(world: World, hero: Entity, elder: Entity, memory: MemoryObject) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"By supper time, {hero.id} felt a notion bigger than a wagon wheel. "
        f'"I remember it one way," {hero.id} said, "but something about it feels '
        f'like a door in a windy barn."'
    )
    if predict(world, "memory")["revealed"]:
        world.say(
            f"{elder.id} blinked. " 
            f'"That memory might be hiding a trick," {elder.label_word} said.'
        )


def twist(world: World, hero: Entity, elder: Entity, memory: MemoryObject, t: Twist) -> None:
    memory = world.get("memory")
    memory.meters["reveal"] += 1
    hero.meters["heart"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the twist came along like a bluejay in a hat box: {t.reveal}."
    )
    world.say(
        f"All at once, {hero.id} understood that the memory was not just a memory; "
        f"it was {memory.hidden_clue}."
    )


def ending(world: World, hero: Entity, elder: Entity, memory: MemoryObject, twist: Twist) -> None:
    hero.memes["joy"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"{elder.id} laughed so hard the porch rail seemed to shake. "
        f'"Well butter my boots," {elder.id} said, "that explains the whole county."'
    )
    world.say(
        f"In the end, {hero.id} tucked the memory back where it belonged, and "
        f"the thing that once seemed strange now made perfect sense. "
        f"{world.setting.big_image}."
    )
    world.say(
        f"And that is how the tale ended: with a memory, a twist, and a smile "
        f"wide enough to cross a cornfield."
    )


def tell(setting: Setting, memory: MemoryObject, twist_cfg: Twist,
         hero_name: str = "Mabel", hero_type: str = "girl",
         elder_name: str = "Aunt June", elder_type: str = "aunt") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    mem = world.add(Entity(id="memory", type="memory", label=memory.label))
    mem.meters["reveal"] = 0.0
    mem.memes["kept"] = 1.0
    world.facts.update(memory_cfg=memory, twist_cfg=twist_cfg, hero=hero, elder=elder)

    setup(world, hero, elder, memory, twist_cfg)
    world.para()
    trouble(world, hero, elder, memory)
    world.para()
    twist(world, hero, elder, memory, twist_cfg)
    world.para()
    ending(world, hero, elder, memory, twist_cfg)

    world.facts.update(outcome="twist", memory=mem, revealed=mem.meters["reveal"] >= THRESHOLD)
    return world


SETTINGS = {
    "barn": Setting("barn", "the old red barn", "golden", "the boards creaked", "A swallow swooped out under the rafters and the whole barn looked newly awake."),
    "porch": Setting("porch", "the front porch", "purple", "the crickets sang", "The moon hung over the yard like a silver plate, and the porch light made the steps shine."),
    "trail": Setting("trail", "the river trail", "windy", "the reeds whispered", "The river slid by like a long blue ribbon, and the hills stood listening."),
}

MEMORIES = {
    "ribbon": MemoryObject("ribbon", "a ribbon memory", "like a blue ribbon tied round a post", "it had once been tied to a cradleboard", tags={"memory", "pregnant"}),
    "shoe": MemoryObject("shoe", "a shoe memory", "like a shiny shoe in a wash tub", "it belonged to a new baby expected by the family", tags={"memory", "pregnant"}),
    "song": MemoryObject("song", "a song memory", "like an old tune that kept returning", "it was a lullaby sung for a pregnant mother", tags={"memory", "pregnant"}),
}

TWISTS = {
    "barn": Twist("barn", "the barn seemed to be hiding something", "the hidden bundle was not a raccoon at all, but a basket of baby boots", "the family had been waiting for a new baby", tags={"twist"}),
    "lantern": Twist("lantern", "the lantern glow made everything look larger than life", "the lantern was hanging over a cradle, not a workbench", "the memory had been pointing to a baby on the way", tags={"twist"}),
    "mule": Twist("mule", "the mule kept stamping as if it knew a secret", "the secret was a tiny blanket for the family’s soon-to-arrive baby", "the remembered clue belonged to a pregnant mother", tags={"twist"}),
}

NAMES_GIRL = ["Mabel", "Ivy", "Ada", "Elsie", "Minnie"]
NAMES_BOY = ["Bram", "Jed", "Hank", "Will", "Toby"]
ELDERS = ["Aunt June", "Uncle Ben", "Mama", "Papa"]


@dataclass
class StoryParams:
    setting: str
    memory: str
    twist: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MEMORIES:
            for t in TWISTS:
                if twist_is_reasonable(TWISTS[t], MEMORIES[m]):
                    combos.append((s, m, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mem = f["memory_cfg"]
    return [
        f'Write a tall tale for a child that includes the words "pregnant" and "memory" and ends with a twist.',
        f"Tell a big-feeling story where {f['hero'].id} keeps a memory, and the memory turns out to be a clue about a pregnant mother.",
        f'Write a folksy story in a tall-tale style where a memory seems ordinary at first, then reveals a surprise about the family\'s baby on the way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    mem = f["memory_cfg"]
    return [
        ("What kind of story is this?",
         f"It is a tall tale with a twist, where {hero.id} follows a memory to find out what it really means. The surprise makes the old memory feel brand new."),
        ("What was the memory about?",
         f"It was {mem.phrase}, and it pointed to {mem.hidden_clue}. That clue mattered because the family was waiting for a baby and the truth was hidden in plain sight."),
        ("How did the ending change things?",
         f"At first the memory seemed ordinary, but then the twist showed it was a clue about a pregnant mother. After that, everybody understood why the memory mattered."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a memory?", "A memory is something you remember from before. It can help you understand a later surprise or explain why something matters."),
        QAItem("What does pregnant mean?", "Pregnant means a mother is carrying a baby inside her body and the baby will be born later."),
        QAItem("What is a twist in a story?", "A twist is a surprise that changes how you understand the story. It makes you look back and see the clues in a new way."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "ribbon", "barn", "Mabel", "girl", "Aunt June", "aunt"),
    StoryParams("porch", "song", "lantern", "Bram", "boy", "Mama", "mother"),
    StoryParams("trail", "shoe", "mule", "Ivy", "girl", "Uncle Ben", "uncle"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not give the memory a believable twist.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,M,T) :- setting(S), memory(M), twist(T).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos() vs ASP.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, memory=None, twist=None, hero=None, elder=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a memory and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--elder")
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
              and (args.memory is None or c[1] == args.memory)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, memory, twist = rng.choice(sorted(combos))
    hero_type = "girl" if rng.random() < 0.6 else "boy"
    elder_type = rng.choice(["aunt", "uncle", "mother", "father"])
    hero = args.hero or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(setting, memory, twist, hero, hero_type, elder, elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MEMORIES[params.memory], TWISTS[params.twist],
                 params.hero, params.hero_type, params.elder, params.elder_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible setting-memory-twist combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
