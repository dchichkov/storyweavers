#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tinkle_referral_tadpole_loading_dock_quest_pirate.py
====================================================================================

A standalone storyworld about a little pirate-style quest at a loading dock:
a child hears a tinkle, follows a referral, finds a tadpole in a crate of rainwater,
and ends by choosing a kinder, safer way to help it reach the harbor.

The domain is intentionally small and classical:
- a loading dock setting
- pirate-tale voice
- a quest structure
- a tiny turn from curiosity to responsibility

The story engine uses typed entities with physical meters and emotional memes.
It also includes a Python reasonableness gate and an inline ASP twin for parity
checks, plus prompts and two QA sets grounded in the simulated world.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    wet: bool = False
    calm: bool = False

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
    detail: str
    quest_frame: str
    harbor_word: str = "harbor"


@dataclass
class Clue:
    id: str
    label: str
    where: str
    sound: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    fragile: bool = True
    needs_water: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    wise: bool = True
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["splash"] < THRESHOLD:
            continue
        sig = ("wet", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.wet = True
        e.memes["worry"] += 1
        out.append("__wet__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["helped"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.calm = True
        e.memes["worry"] = 0.0
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def _do_tinkle(world: World, clue: Entity, creature: Entity, narrate: bool = True) -> None:
    clue.meters["tinkle"] += 1
    creature.meters["splash"] += 1
    propagate(world, narrate=narrate)


def reasonable_clue(clue: Clue) -> bool:
    return clue.sound == "tinkle" and "dock" in clue.tags


def reasonable_rescue(guide: Guide) -> bool:
    return guide.wise


def choose_guide() -> Guide:
    return max(GUIDES.values(), key=lambda g: 3 if g.wise else 1)


def intro(world: World, child: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a windy afternoon at the {setting.place}, {child.id} and the crew were "
        f"busy among the crates. {setting.detail}"
    )
    world.say(
        f"{setting.quest_frame} {child.id} felt like a tiny pirate ready for a quest."
    )


def hear_tinkle(world: World, child: Entity, clue: Clue) -> None:
    child.memes["alert"] += 1
    world.say(
        f"Then a soft {clue.sound} came from {clue.where}. {child.id} turned, "
        f"because the sound seemed to call for a daring little quest."
    )


def referral(world: World, child: Entity, guide: Entity, clue: Clue) -> None:
    child.memes["trust"] += 1
    world.say(
        f"A dockhand pointed the way and gave a referral to {guide.label}. "
        f'"Follow the crate with the sea mark," {guide.label} said. "That is where '
        f'the little {clue.label} waits."'
    )


def discover(world: World, child: Entity, creature: Creature, clue: Clue) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Inside the crate, {child.id} found a tiny {creature.label} cupped in rainwater, "
        f"right where the {clue.sound} had been hiding."
    )
    world.say(
        f"The little {creature.label} fluttered in the puddle like a lost treasure."
    )


def worry(world: World, child: Entity, creature: Creature) -> None:
    if creature.needs_water:
        world.say(
            f"{child.id} leaned close and saw that the {creature.label} needed water "
            f"and a gentle hand, not rough pirate grabbing."
        )


def vow(world: World, child: Entity, guide: Entity, creature: Creature, setting: Setting) -> None:
    child.memes["helped"] += 1
    guide.memes["kindness"] += 1
    world.say(
        f'"We should not keep it here," {child.id} said. "We will carry it to the '
        f"{setting.harbor_word} water and ask for help.""
    )
    world.say(
        f"{guide.label} nodded, glad the quest had turned into a rescue."
    )


def ending(world: World, child: Entity, guide: Entity, creature: Creature, setting: Setting) -> None:
    world.say(
        f"Carefully, they used a little bucket, kept the {creature.label} wet, and set it "
        f"by the dock edge where the tide could touch it."
    )
    world.say(
        f"In the end, the {creature.label} was safe, the crate was still quiet, and "
        f"{child.id} sailed home proud of the kind quest."
    )


def tell(setting: Setting, clue: Clue, creature: Creature, guide: Guide,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Captain Reed", helper_gender: str = "man") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="guide"))
    dockhand = world.add(Entity(id="Dockhand", kind="character", type="man", role="referrer"))

    intro(world, child, setting)
    world.para()
    hear_tinkle(world, child, clue)
    referral(world, child, helper, clue)
    discover(world, child, creature, clue)
    worry(world, child, creature)

    world.para()
    vow(world, child, helper, creature, setting)
    _do_tinkle(world, world.add(Entity(id="crate", label="the crate")), world.add(Entity(id="tadpole", label=creature.label)), narrate=False)
    ending(world, child, helper, creature, setting)

    world.facts.update(
        child=child, helper=helper, dockhand=dockhand, clue=clue,
        creature=creature, guide=guide, setting=setting
    )
    return world


SETTINGS = {
    "loading_dock": Setting(
        "loading_dock",
        "the loading dock",
        "Tall stacks of crates stood near the water, ropes dangled from hooks, and gulls called over the pier.",
        "The pirates had a quest today, and the dock was full of clues.",
        "the harbor",
    ),
}

CLUES = {
    "tinkle": Clue("tinkle", "tinkle", "a crate beside the rope pile", "tinkle", "a call for help", tags={"dock", "sound", "tinkle"}),
}

CREATURES = {
    "tadpole": Creature("tadpole", "tadpole", fragile=True, needs_water=True, tags={"tadpole", "water"}),
}

GUIDES = {
    "quest": Guide("quest", "quest guide", "follow the clue and help gently", wise=True, tags={"quest", "guide"}),
}

NAMES_GIRL = ["Mina", "Lila", "Sana", "Nori", "Tess"]
NAMES_BOY = ["Kai", "Jasper", "Theo", "Milo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CLUES.items():
            for crid, cr in CREATURES.items():
                if reasonable_clue(c) and reasonable_rescue(GUIDES["quest"]):
                    combos.append((sid, cid, crid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    creature: str
    guide: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style loading dock quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "man", "woman"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.guide and args.guide != "quest":
        raise StoryError("Only the quest guide fits this tiny loading-dock tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, creature = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["man", "woman", "boy", "girl"])
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or "Captain Reed"
    return StoryParams(setting, clue, creature, "quest", child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "tinkle", "referral", and "tadpole".',
        f"Tell a small quest story at {f['setting'].place} where {f['child'].id} hears a tinkle, follows a referral, and finds a tadpole that needs help.",
        f"Write a gentle loading-dock adventure with pirates, a clue sound, and a safe ending for the tadpole.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    creature = f["creature"]
    guide = f["helper"]
    setting = f["setting"]
    return [
        ("Where does the story happen?",
         f"It happens at {setting.place}, among the crates and ropes by the water. That setting gives the quest its dockside pirate feeling."),
        ("What sound starts the quest?",
         f"A soft {clue.sound} starts the quest. The sound comes from a crate and leads {child.id} to look closer."),
        ("Who gave the referral?",
         f"A dockhand gave the referral to {guide.id}, who knew where to look next. The referral helped turn the sound into a real quest."),
        ("What did they find?",
         f"They found a tiny {creature.label} in rainwater. It needed water and a gentle rescue, so the quest became a helping quest."),
        ("How did the story end?",
         f"{child.id} and {guide.id} moved the {creature.label} safely toward the harbor water. The ending shows they chose kindness over taking a treasure."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tadpole?",
         "A tadpole is a baby frog. It lives in water and grows as it becomes a frog."),
        ("What is a loading dock?",
         "A loading dock is a place near trucks or boats where crates and supplies are moved."),
        ("What does a referral mean?",
         "A referral is a helpful direction or recommendation that points someone to the right person or place."),
        ("What is a quest?",
         "A quest is a search or journey to find something or help someone. In stories, quests often feel adventurous."),
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


CURATED = [StoryParams("loading_dock", "tinkle", "tadpole", "quest", "Mina", "girl", "Captain Reed", "man")]


ASP_RULES = r"""
valid(S, C, Cr) :- setting(S), clue(C), creature(Cr), clue_ok(C), quest_ok.
clue_ok(tinkle).
quest_ok.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for crid in CREATURES:
        lines.append(asp.fact("creature", crid))
    lines.append(asp.fact("quest_ok"))
    lines.append(asp.fact("clue_ok", "tinkle"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, creature=None, guide=None, child_name=None, child_gender=None, helper_name=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], CREATURES[params.creature], GUIDES[params.guide], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest combinations:\n")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child_name}: {p.clue} at {p.setting} ({p.guide})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
