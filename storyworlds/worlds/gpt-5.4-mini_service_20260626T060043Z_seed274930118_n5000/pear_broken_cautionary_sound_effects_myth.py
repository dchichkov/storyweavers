#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pear_broken_cautionary_sound_effects_myth.py
===============================================================================================================

A small myth-flavored story world about a pear, a broken thing, and a
cautionary lesson with sound effects.

Seed impression:
---
A child is warned not to fling a sacred pear-stone from the shrine wall.
The child ignores the warning, the pear cracks with a terrible sound, and
the village learns to use a basket and rope the next time.

World model:
---
- Physical state uses meters: heft, height, strain, breakage, safety, repair.
- Emotional state uses memes: caution, pride, fear, shame, relief, awe.
- The story is driven by simulated state, not by template swapping.

This script follows the Storyweavers world contract:
- standalone stdlib script
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing
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
        for k in ("heft", "height", "strain", "breakage", "safety", "repair"):
            self.meters.setdefault(k, 0.0)
        for k in ("caution", "pride", "fear", "shame", "relief", "awe", "warning"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the orchard shrine"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    region: str
    fragile: bool = True
    sacred: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.action: str = ""
        self.sound: str = ""
        self.location_detail: str = ""

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.action = self.action
        w.sound = self.sound
        w.location_detail = self.location_detail
        return w


def _event(world: World, key: tuple, text: str) -> None:
    if key in world.fired:
        return
    world.fired.add(key)
    world.say(text)


def _shatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["heft"] < THRESHOLD:
            continue
        for ent in world.entities.values():
            if ent.id == actor.id or ent.kind != "thing":
                continue
            if ent.label != "sacred pear":
                continue
            if ent.meters["breakage"] >= THRESHOLD:
                continue
            sig = ("shatter", actor.id, ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["breakage"] += 1
            ent.memes["awe"] += 1
            out.append(f"{world.sound}! The {ent.label} cracked.")
    return out


def _fear_after_break(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["heft"] < THRESHOLD:
            continue
        if actor.memes["warning"] < THRESHOLD:
            continue
        if actor.memes["shame"] >= THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append(f"The hush after the crack felt heavier than stone.")
    return out


CAUSAL_RULES = [_shatter, _fear_after_break]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_break(world: World, actor: Entity, relic: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["heft"] += 1
    propagate(sim, narrate=False)
    return sim.get(relic.id).meters["breakage"] >= THRESHOLD


def choose_tool(relic: Relic) -> Optional[Tool]:
    for tool in TOOLS:
        if relic.region in tool.guards:
            return tool
    return None


def tell(world: World, hero: Entity, elder: Entity, relic: Entity, tool: Optional[Entity]) -> None:
    world.say(
        f"Long ago, {hero.id} was a little {hero.type} who wandered beside {world.setting.place}."
    )
    world.say(
        f"At the shrine stood {relic.phrase}, polished by old hands and watched by the dawn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved its sweet shape and bright color, and {hero.pronoun('possessive')} heart filled with pride."
    )

    world.para()
    world.say(
        f"One morning, the elder pointed at the pear and said, "
        f'"Do not fling it, child. Stone remembers every careless удар."'
    )
    hero.memes["warning"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"But {hero.id} wanted to prove {hero.pronoun('possessive')} strength, so {hero.pronoun()} lifted the pear high."
    )

    world.para()
    hero.meters["heft"] += 1
    world.action = "throw"
    world.sound = "CRACK"
    if predict_break(world, hero, relic):
        world.say(f"{hero.id} ignored the warning and threw the pear.")
        propagate(world, narrate=True)
        if relic.meters["breakage"] >= THRESHOLD:
            hero.memes["shame"] += 1
            hero.memes["fear"] += 1
            world.say(
                f"The pear split apart with a sharp {world.sound}!, and the sweet smell was gone at once."
            )
            world.say(
                f"{hero.id} stood still while the elder closed {hero.pronoun('possessive')} eyes and said, "
                f'"See? Carelessness makes a broken song."'
            )
    else:
        world.say(f"{hero.id} held the pear carefully, and nothing broke.")
        world.say("The warning had done its work before trouble could grow.")

    world.para()
    if tool is not None and hero.memes["shame"] >= THRESHOLD:
        hero.memes["relief"] += 1
        hero.meters["repair"] += 1
        world.say(
            f"Then the elder brought {tool.phrase} and showed {hero.id} how to mend the shrine."
        )
        world.say(
            f"Together they gathered the broken pieces, tied them safe, and set a new pear behind the lamp."
        )
        world.say(
            f"{hero.id} learned to use {tool.label} first, and from that day on {hero.pronoun()} moved with care."
        )
    else:
        world.say(
            f"The elder nodded and told {hero.id} to remember the lesson before the next sunrise."
        )

    world.facts.update(hero=hero, elder=elder, relic=relic, tool=tool, setting=world.setting)


SETTINGS = {
    "shrine": Setting(place="the orchard shrine", indoors=False, affords={"reach", "carry"}),
    "grove": Setting(place="the bright grove", indoors=False, affords={"reach", "carry"}),
    "courtyard": Setting(place="the temple courtyard", indoors=False, affords={"reach", "carry"}),
}

RELICS = {
    "pear": Relic(label="pear", phrase="a sacred pear of gold-green glass", region="hands"),
}

TOOLS = [
    Tool(
        id="basket",
        label="basket",
        phrase="a woven basket",
        helps={"carry"},
        guards={"hands"},
    ),
    Tool(
        id="cloth",
        label="cloth",
        phrase="a soft cloth wrap",
        helps={"carry", "guard"},
        guards={"hands"},
    ),
]

GIRL_NAMES = ["Aya", "Mira", "Nila", "Sera", "Tala"]
BOY_NAMES = ["Arin", "Bora", "Cai", "Dara", "Eli"]
TRAITS = ["curious", "bold", "gentle", "proud", "careful"]


@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, relic) for place in SETTINGS for relic in RELICS]


KNOWLEDGE = {
    "pear": [
        ("What is a pear?", "A pear is a sweet fruit that grows on a tree and has soft flesh inside."),
    ],
    "broken": [
        ("What does broken mean?", "Broken means something has cracked, split, or stopped being whole."),
    ],
    "caution": [
        ("What is caution?", "Caution means being careful and thinking before you act."),
    ],
    "sound": [
        ("What is a sound effect?", "A sound effect is a word like crack or boom that helps you imagine a noise."),
    ],
    "myth": [
        ("What is a myth?", "A myth is an old story people tell to explain a lesson, a place, or a tradition."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    return [
        f'Write a short myth for a child about a {relic.label} that teaches caution and includes a loud sound effect.',
        f"Tell a mythic cautionary tale where {hero.id} handles {relic.phrase} too roughly and learns to be careful.",
        f"Write a child-friendly myth that ends with a broken {relic.label} being repaired after a warning is ignored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic = f["hero"], f["elder"], f["relic"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who learned the lesson in the story?",
            answer=f"{hero.id} learned that careful hands can protect a precious thing like the {relic.label}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} ignored the warning?",
            answer=f"The {relic.label} broke with a loud crack, and {hero.id} felt shame and fear.",
        ),
        QAItem(
            question=f"Who gave the warning?",
            answer=f"The {elder.id} gave the warning before the pear was thrown.",
        ),
    ]
    if tool is not None:
        qa.append(QAItem(
            question=f"How did the tool help after the broken pear?",
            answer=f"The {tool.label} helped the village gather and protect the pieces so the shrine could be set right again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"pear", "broken", "caution", "sound", "myth"}
    out: list[QAItem] = []
    for tag in tags:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A relic is at risk if an actor lifts it with enough force to trigger breaking.
at_risk(R) :- relic(R), breakable(R).

% A tool is a compatible cautionary fix if it guards the region the relic is held in.
has_fix(R) :- at_risk(R), relic_region(R, Reg), tool(T), guards(T, Reg).

valid_story(Place, R) :- place(Place), relic(R), at_risk(R), has_fix(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r, rel in RELICS.items():
        lines.append(asp.fact("relic", r))
        lines.append(asp.fact("relic_region", r, rel.region))
        if rel.fragile:
            lines.append(asp.fact("breakable", r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Mythic cautionary story about a pear and a broken warning.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["elder", "priest", "grandmother"])
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection() -> str:
    return "(No story: this myth needs a fragile pear and a real way for caution to matter.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.relic not in RELICS:
        raise StoryError("(Unknown relic.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)]
    if not combos:
        raise StoryError(explain_rejection())
    place, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["elder", "priest", "grandmother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder"))
    relic = world.add(Entity(id="pear", type="thing", label="sacred pear", phrase=RELICS[params.relic].phrase))
    tool_def = choose_tool(RELICS[params.relic])
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, phrase=tool_def.phrase)) if tool_def else None
    tell(world, hero, elder, relic, tool)
    world.facts.update(hero=hero, elder=elder, relic=relic, tool=tool, params=params)
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
    StoryParams(place="shrine", relic="pear", name="Aya", gender="girl", elder="elder", trait="curious"),
    StoryParams(place="grove", relic="pear", name="Arin", gender="boy", elder="priest", trait="bold"),
    StoryParams(place="courtyard", relic="pear", name="Mira", gender="girl", elder="grandmother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, relic in combos:
            print(f"  {place:12} {relic}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
