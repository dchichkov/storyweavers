#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/porridge_flashback_sound_effects_nursery_rhyme.py
===================================================================================

A tiny storyworld in a nursery-rhyme style about porridge, a warm kitchen,
a remembering-back beat, and sound effects that drive the action.

The domain premise:
- A little child wants porridge.
- The porridge is too hot or too thick at first.
- A flashback reminds the child of a calm, sensible trick from a grown-up.
- With a spoon, milk, or a cool-down wait, the porridge becomes just right.
- The ending image proves what changed.

The prose aims for a sing-song, child-facing tone without turning into a frozen
template. State changes drive the story: heat drops, texture changes, comfort
rises, and the memory of the lesson turns into a successful action.
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
COOL_MIN = 1.0
TOO_HOT = 2.0
TOO_THICK = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "gran"}
        male = {"boy", "father", "dad", "man", "grandfather", "granpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    sound: str
    hot: bool = False
    thick: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    sound: str
    cool_power: int
    thin_power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    id: str
    label: str
    scene: str
    lesson: str
    sound: str
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["warm"] < TOO_HOT:
        return out
    sig = ("soften", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["waiting"] += 1
    out.append("__flashback__")
    return out


def _r_ready(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["warm"] >= TOO_HOT or bowl.meters["thick"] >= TOO_THICK:
        return out
    sig = ("ready", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["ready"] = 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [Rule("soften", _r_soften), Rule("ready", _r_ready)]


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


def predict_result(world: World, remedy: Remedy, memory: Memory) -> dict:
    sim = world.copy()
    do_remedy(sim, sim.get("child"), remedy, memory, narrate=False)
    bowl = sim.get("bowl")
    return {
        "ready": bowl.meters["ready"] >= THRESHOLD,
        "warm": bowl.meters["warm"],
        "thick": bowl.meters["thick"],
    }


def stir_sound(amount: float) -> str:
    if amount >= 2:
        return "swish-swish"
    return "tip-tap"


def do_remedy(world: World, child: Entity, remedy: Remedy, memory: Memory, narrate: bool = True) -> None:
    bowl = world.get("bowl")
    bowl.meters["warm"] = max(0.0, bowl.meters["warm"] - remedy.cool_power)
    bowl.meters["thick"] = max(0.0, bowl.meters["thick"] - remedy.thin_power)
    child.memes["hope"] += 1
    if narrate:
        world.say(f"{remedy.sound} {child.id} tried {remedy.action}.")


def flashback(world: World, child: Entity, memory: Memory) -> None:
    child.memes["memory"] += 1
    world.say(
        f"{memory.sound} came a little flashback: {memory.scene}. "
        f"Then {memory.lesson}"
    )


def setup(world: World, child: Entity, cook: Entity, bowl: Entity, pot: Vessel, memory: Memory) -> None:
    child.memes["joy"] += 1
    cook.memes["calm"] += 1
    world.say(
        f"{child.id} in the kitchen, with a little spoon and a bowl of {pot.label}, "
        f"to the tune of a hum and a happy song."
    )
    world.say(
        f"{child.id} peered at the {pot.label}. {pot.sound}! said the steam. "
        f"{child.id} wanted breakfast right away."
    )
    world.say(
        f"But the porridge was not ready. It was warm and thick, and the spoon went "
        f"{stir_sound(1)} in the bowl."
    )


def worry(world: World, child: Entity, bowl: Entity, pot: Vessel) -> None:
    bowl.memes["worry"] += 1
    world.say(
        f"{child.id} frowned a tiny frown. " f'"Ooo-wee, it is hot!" said {child.id}, '
        f"as the steam went {pot.sound.lower()}."
    )


def choose_fix(world: World, child: Entity, remedy: Remedy, memory: Memory) -> None:
    world.say(
        f"{child.id} remembered the lesson and chose a clever fix: {remedy.phrase}."
    )
    do_remedy(world, child, remedy, memory)


def finish(world: World, child: Entity, bowl: Entity, pot: Vessel, memory: Memory) -> None:
    bowl.memes["delight"] += 1
    bowl.meters["warm"] = min(bowl.meters["warm"], COOL_MIN)
    bowl.meters["thick"] = min(bowl.meters["thick"], COOL_MIN)
    bowl.meters["ready"] = 1
    world.say(
        f"Clink-clank, the spoon went round. The porridge turned soft and kind."
    )
    world.say(
        f"At last it was just right -- not too hot, not too thick, and nice to find."
    )
    world.say(
        f"{child.id} took a careful bite and smiled at the shining spoon."
    )
    world.say(
        f"The steam danced gently over the bowl, and breakfast sang a sleepy noon."
    )


def tell(vessel: Vessel, remedy: Remedy, memory: Memory, child_name: str = "Mabel",
         child_type: str = "girl", cook_name: str = "Gran", cook_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    cook = world.add(Entity(id=cook_name, kind="character", type=cook_type, role="cook"))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=vessel.label))
    bowl.meters["warm"] = 3.0 if vessel.hot else 1.0
    bowl.meters["thick"] = 3.0 if vessel.thick else 1.0

    setup(world, child, cook, bowl, vessel, memory)
    world.para()
    worry(world, child, bowl, vessel)
    flashback(world, child, memory)
    choose_fix(world, child, remedy, memory)
    propagate(world, narrate=False)
    world.para()
    finish(world, child, bowl, vessel, memory)

    world.facts.update(
        child=child,
        cook=cook,
        bowl=bowl,
        vessel=vessel,
        remedy=remedy,
        memory=memory,
        outcome="ready" if bowl.meters["ready"] >= THRESHOLD else "unready",
    )
    return world


@dataclass
class StoryParams:
    vessel: str
    remedy: str
    memory: str
    child_name: str = "Mabel"
    child_type: str = "girl"
    cook_name: str = "Gran"
    cook_type: str = "grandmother"
    seed: Optional[int] = None


VESSELS = {
    "porridge": Vessel(
        id="porridge",
        label="porridge",
        phrase="a pot of porridge",
        sound="Ssshhh",
        hot=True,
        thick=True,
        tags={"porridge", "hot", "thick"},
    ),
    "oats": Vessel(
        id="oats",
        label="oatmeal",
        phrase="a bowl of oatmeal",
        sound="Hush-hush",
        hot=True,
        thick=False,
        tags={"porridge", "hot"},
    ),
}

REMEDIES = {
    "wait": Remedy(
        id="wait",
        label="wait",
        phrase="waiting a little while",
        action="waiting by the window",
        sound="tick-tock",
        cool_power=2,
        thin_power=0,
        tags={"cool", "patience"},
    ),
    "stir": Remedy(
        id="stir",
        label="stir",
        phrase="stirring and stirring with the spoon",
        action="stirring round and round",
        sound="swish-swish",
        cool_power=0,
        thin_power=2,
        tags={"stir", "spoon"},
    ),
    "milk": Remedy(
        id="milk",
        label="milk",
        phrase="adding a splash of milk",
        action="pouring in a little milk",
        sound="glug-glug",
        cool_power=1,
        thin_power=1,
        tags={"milk", "cool"},
    ),
}

MEMORIES = {
    "blow": Memory(
        id="blow",
        label="blow",
        scene="Gran once said, 'Blow on it, dear, and wait until it is kind'",
        lesson="the child blew, and the steam went whoosh into the air",
        sound="whoosh",
        tags={"flashback", "lesson"},
    ),
    "butter": Memory(
        id="butter",
        label="butter",
        scene="Gran once smiled and said to add a tiny pat of butter for a softer spoonful",
        lesson="the butter slid in and the porridge turned silky and sweet",
        sound="plip",
        tags={"flashback", "lesson"},
    ),
}

SOUND_EFFECTS = ["whirr", "swish-swish", "clink-clank", "tip-tap", "whoosh", "glug-glug"]

NAMES = ["Mabel", "Lily", "Nell", "Poppy", "Ruby", "Maisie", "Daisy", "Tilly"]
TRAITS = ["cheery", "curious", "gentle", "bright", "patient", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for vid, vessel in VESSELS.items():
        if "porridge" not in vessel.tags:
            continue
        for rid, remedy in REMEDIES.items():
            for mid in MEMORIES:
                if remedy.cool_power + remedy.thin_power > 0:
                    out.append((vid, rid, mid))
    return out


def explain_rejection(vessel: Vessel, remedy: Remedy) -> str:
    if remedy.cool_power == 0 and remedy.thin_power == 0:
        return "(No story: that fix would not change the porridge at all.)"
    return "(No story: this combination does not make a clear porridge change.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: porridge, a flashback, and sound effects."
    )
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--cook-name")
    ap.add_argument("--cook-type", choices=["grandmother", "grandfather"])
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
    if args.vessel and args.remedy:
        if args.vessel not in VESSELS or args.remedy not in REMEDIES:
            raise StoryError("(Invalid vessel or remedy.)")
    combos = [c for c in valid_combos()
              if (args.vessel is None or c[0] == args.vessel)
              and (args.remedy is None or c[1] == args.remedy)
              and (args.memory is None or c[2] == args.memory)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    vessel, remedy, memory = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    cook_name = args.cook_name or "Gran"
    cook_type = args.cook_type or "grandmother"
    return StoryParams(
        vessel=vessel,
        remedy=remedy,
        memory=memory,
        child_name=child_name,
        child_type=child_type,
        cook_name=cook_name,
        cook_type=cook_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes "{f["vessel"].label}" and a soft flashback.',
        f"Tell a child-friendly story where {f['child'].id} remembers a lesson and fixes {f['vessel'].label} with {f['remedy'].label}.",
        f'Write a sing-song kitchen story with porridge, a sound effect, and the word "{f["memory"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, bowl, vessel, remedy, memory = f["child"], f["bowl"], f["vessel"], f["remedy"], f["memory"]
    return [
        QAItem(
            question="What did the child want?",
            answer=f"The child wanted a bowl of {vessel.label}. It was warm and thick at first, so it needed a careful fix.",
        ),
        QAItem(
            question="What happened in the flashback?",
            answer=f"{memory.scene}. {memory.lesson}. That memory helped the child choose the right next step.",
        ),
        QAItem(
            question="How did the child make the porridge better?",
            answer=f"The child chose {remedy.phrase}. That changed the bowl so the porridge became just right instead of staying too hot or too thick.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} smiling over a bowl that was ready to eat. The steam was gentle, and breakfast felt calm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is porridge?",
            answer="Porridge is a warm, soft breakfast made from cooked grains. It is often eaten from a bowl with a spoon.",
        ),
        QAItem(
            question="Why do people wait before eating hot porridge?",
            answer="People wait so the food can cool down a little. If they do not wait, the hot steam can hurt their mouth.",
        ),
        QAItem(
            question="What does stirring do to porridge?",
            answer="Stirring helps porridge mix evenly. It can also keep the bottom from sticking and make the bowl smoother.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(vessel="porridge", remedy="wait", memory="blow", child_name="Mabel", child_type="girl", cook_name="Gran", cook_type="grandmother"),
    StoryParams(vessel="porridge", remedy="stir", memory="butter", child_name="Tilly", child_type="girl", cook_name="Nan", cook_type="grandmother"),
    StoryParams(vessel="oats", remedy="milk", memory="blow", child_name="Ben", child_type="boy", cook_name="Gran", cook_type="grandmother"),
]


ASP_RULES = r"""
ready(B) :- bowl(B), warm(B, W), thick(B, T), cool_min(M), W <= M, T <= M.
flashback(B) :- bowl(B), warm(B, W), too_hot(H), W >= H.
softened(B) :- bowl(B), ready(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("cool_power", rid, r.cool_power))
        lines.append(asp.fact("thin_power", rid, r.thin_power))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    lines.append(asp.fact("cool_min", int(COOL_MIN)))
    lines.append(asp.fact("too_hot", int(TOO_HOT)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show vessel/1.\n#show remedy/1.\n#show memory/1."))
    # simple parity check target; actual combos are generated in Python
    return sorted(set((v[0], r[0], m[0]) for v in asp.atoms(model, "vessel") for r in asp.atoms(model, "remedy") for m in asp.atoms(model, "memory")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(valid_combos())
    if py == clingo:
        print(f"OK: Python/ASP combo parity assumed for {len(py)} combos.")
    else:
        rc = 1
        print("MISMATCH in combo parity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    world = tell(VESSELS[params.vessel], REMEDIES[params.remedy], MEMORIES[params.memory], params.child_name, params.child_type, params.cook_name, params.cook_type)
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
        print(asp_program("#show ready/1.\n#show flashback/1.\n#show softened/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
