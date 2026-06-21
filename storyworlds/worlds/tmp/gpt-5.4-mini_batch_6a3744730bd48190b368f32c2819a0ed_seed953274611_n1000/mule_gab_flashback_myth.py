#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mule_gab_flashback_myth.py
===========================================================

A tiny mythic storyworld about a mule, a gabby boast, a loss of nerve, a
flashback to an old lesson, and a wiser ending.

This world tells a short, child-facing myth in which a mule and a child or
herder travel toward a hill shrine with a small burden. The gabby one boasts,
the path goes wrong, and a flashback to an earlier lesson reveals how patience
and quiet help make the way safe again. The story ends with a clear image of
what changed: the burden is delivered, the mule is calmer, and the gab has
become careful speech.

The script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds.results eagerly
- uses a lazy ASP twin
- has typed entities with meters and memes
- generates story, prompts, grounded QA, and world-knowledge QA
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
COURAGE_INIT = 5.0
QUIET_MIN = 2
WISER_MIN = 2


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
class StoryParams:
    path: str
    burden: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
    gab_mode: str
    flashback_key: str = "lesson"
    seed: Optional[int] = None


@dataclass
class PathCfg:
    id: str
    place: str
    image: str
    danger_word: str
    end_image: str


@dataclass
class BurdenCfg:
    id: str
    label: str
    phrase: str
    heavy: bool = False
    sacred: bool = False


@dataclass
class GabCfg:
    id: str
    line: str
    turn: str
    quiet_line: str
    too_loud: bool = True
    sense: int = 2


@dataclass
class FlashbackCfg:
    id: str
    memory_title: str
    memory_line: str
    lesson: str


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("burden").meters["lost"] >= THRESHOLD and "shrinedust" in world.entities:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gabber").memes["quiet"] >= THRESHOLD and world.get("mule").memes["calm"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("path").meters["safe"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("calm", "social", _r_calm),
]


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


def reasonableness_gate(path: PathCfg, burden: BurdenCfg, gab: GabCfg) -> bool:
    if burden.heavy and path.id == "narrow_hills":
        return False
    if gab.sense < QUIET_MIN:
        return False
    return True


def would_flashback_help(gab: GabCfg, flash: FlashbackCfg) -> bool:
    return gab.too_loud and bool(flash.lesson)


def predict_loss(world: World, burden_id: str) -> dict:
    sim = world.copy()
    sim.get(burden_id).meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": sim.get(burden_id).meters["lost"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
    }


def setup(world: World, path: PathCfg, burden: BurdenCfg, hero: Entity, helper: Entity, elder: Entity) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    elder.memes["memory"] += 1
    world.say(
        f"Long ago, when {path.place} was still young in the telling, {hero.id} and "
        f"{helper.id} set out with {elder.id} beneath a bright sky. "
        f"They carried {burden.phrase} toward the hill shrine."
    )
    world.say(
        f"The mule walked beside them, steady as a stone song, while the road "
        f"rose and turned above the fields."
    )


def gab(world: World, gabber: Entity, gabcfg: GabCfg, elder: Entity) -> None:
    gabber.memes["pride"] += 1
    world.say(
        f'{gabber.id} laughed too loudly. "{gabcfg.line}"'
    )
    world.say(
        f"His {elder.label_word} frowned, because loud gab can startle a tired mule "
        f"and scatter a careful plan."
    )


def trouble(world: World, mule: Entity, burden: Entity, path: PathCfg) -> None:
    mule.meters["strain"] += 1
    burden.meters["tilt"] += 1
    burden.meters["lost"] += 1
    propagate(world, narrate=True)
    world.say(
        f"The mule stumbled near the {path.danger_word}, and {burden.label} slipped "
        f"sideways. For a breath, the road looked like it had swallowed the gift."
    )


def flashback(world: World, flash: FlashbackCfg, elder: Entity, helper: Entity, gabber: Entity) -> None:
    gabber.memes["quiet"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"Then came a flashback: {flash.memory_title}. {elder.id} remembered the old "
        f"lesson and spoke it again."
    )
    world.say(
        f'"{flash.memory_line}"'
    )
    world.say(
        f"That memory settled over the road like shade, and even {gabber.id} stopped "
        f"to listen."
    )


def fix(world: World, mule: Entity, burden: Entity, helper: Entity, path: PathCfg, gabcfg: GabCfg) -> None:
    mule.meters["strain"] = 0.0
    mule.memes["calm"] += 1
    burden.meters["lost"] = 0.0
    burden.meters["delivered"] += 1
    path.meters["safe"] += 1
    world.say(
        f"{helper.id} held the rope, the mule stood still, and together they lifted "
        f"{burden.label} back into place."
    )
    world.say(
        f'This time {gabcfg.quiet_line}. The road listened, the mule breathed easy, '
        f"and the gift stayed whole."
    )


def ending(world: World, path: PathCfg, burden: BurdenCfg, hero: Entity, helper: Entity, mule: Entity) -> None:
    hero.memes["wisdom"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By dusk they reached the shrine. The priests took {burden.phrase}, and "
        f"the hill glowed gold against the darkening blue."
    )
    world.say(
        f"{hero.id} patted the mule's neck and smiled. No boast rode ahead of them "
        f"now -- only a quiet step, a safer tongue, and {path.end_image}."
    )


def tell(path: PathCfg, burden: BurdenCfg, gabcfg: GabCfg, flash: FlashbackCfg,
         hero_name: str = "Mira", hero_gender: str = "girl",
         helper_name: str = "Oren", helper_gender: str = "boy",
         elder_name: str = "Ila", elder_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    mule = world.add(Entity(id="mule", kind="character", type="thing", role="beast"))
    burden_ent = world.add(Entity(id="burden", type="thing", label=burden.label))
    path_ent = world.add(Entity(id="path", type="thing", label=path.place))
    world.add(Entity(id="shrinedust", type="thing", label="the shrine dust"))

    world.facts.update(path=path, burden=burden, gab=gabcfg, flash=flash)

    setup(world, path, burden, hero, helper, elder)
    world.para()
    gab(world, hero, gabcfg, elder)
    if not would_flashback_help(gabcfg, flash):
        raise StoryError("This world expects a gab that can be softened by a flashback lesson.")
    trouble(world, mule, burden_ent, path)
    world.para()
    flashback(world, flash, elder, helper, hero)
    fix(world, mule, burden_ent, helper, path, gabcfg)
    world.para()
    ending(world, path, burden, hero, helper, mule)

    world.facts.update(
        hero=hero, helper=helper, elder=elder, mule=mule, burden_ent=burden_ent,
        path_ent=path_ent, outcome="saved", flashback=True
    )
    return world


PATHS = {
    "hill_road": PathCfg(
        id="hill_road",
        place="the hill road",
        image="the road curled up toward the shrine like a ribbon of dust",
        danger_word="the sharp bend",
        end_image="the shrine bell shining above the terraces",
    ),
    "river_path": PathCfg(
        id="river_path",
        place="the river path",
        image="the path ran beside the river like a silver thread",
        danger_word="the stepping stones",
        end_image="the river glittering under the evening stars",
    ),
}

BURDENS = {
    "honey": BurdenCfg(
        id="honey",
        label="a jar of honey",
        phrase="a jar of honey",
    ),
    "grain": BurdenCfg(
        id="grain",
        label="a sack of grain",
        phrase="a sack of grain",
        heavy=True,
    ),
    "flowers": BurdenCfg(
        id="flowers",
        label="a bundle of flowers",
        phrase="a bundle of flowers",
        sacred=True,
    ),
}

GABS = {
    "boast": GabCfg(
        id="boast",
        line="I am the boldest rider on this road, and nothing can shake my mule!",
        turn="the boast",
        quiet_line="the boast was gone from his mouth",
        sense=2,
    ),
    "taunt": GabCfg(
        id="taunt",
        line="This road is nothing at all; I can talk all day and never miss a step!",
        turn="the taunt",
        quiet_line="his voice dropped soft as rain",
        sense=2,
    ),
    "chatter": GabCfg(
        id="chatter",
        line="Listen to me talk, listen to me talk, listen to me talk!",
        turn="the chatter",
        quiet_line="he counted his breaths instead of his words",
        sense=2,
    ),
}

FLASHBACKS = {
    "lesson": FlashbackCfg(
        id="lesson",
        memory_title="the old lesson by the fig tree",
        memory_line="A mule trusts a quiet hand more than a loud one, and a road is easier when the tongue is calm.",
        lesson="quiet hands and quiet words keep the path true",
    ),
    "market": FlashbackCfg(
        id="market",
        memory_title="the day at the market gate",
        memory_line="When the mule startled at a shout, the basket fell; when the voice softened, the mule stepped on.",
        lesson="soft speech steadies frightened feet",
    ),
}

GIRL_NAMES = ["Mira", "Sera", "Nia", "Iva", "Lina"]
BOY_NAMES = ["Oren", "Tavi", "Bren", "Kian", "Rho"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PATHS:
        for b in BURDENS:
            for g in GABS:
                for f in FLASHBACKS:
                    if reasonableness_gate(PATHS[p], BURDENS[b], GABS[g]) and would_flashback_help(GABS[g], FLASHBACKS[f]):
                        combos.append((p, b, g, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: mule, gab, and a flashback lesson.")
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--gab", choices=GABS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
              if (args.path is None or c[0] == args.path)
              and (args.burden is None or c[1] == args.burden)
              and (args.gab is None or c[2] == args.gab)
              and (args.flashback is None or c[3] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    path, burden, gab, flash = rng.choice(sorted(combos))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    gg = args.helper_gender or ("boy" if hg == "girl" and rng.random() < 0.7 else "girl")
    eg = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != hero])
    elder = args.elder or rng.choice(["Ila", "Mara", "Dora", "Asha"])
    return StoryParams(path=path, burden=burden, hero=hero, hero_gender=hg,
                       helper=helper, helper_gender=gg, elder=elder,
                       elder_gender=eg, gab_mode=gab, flashback_key=flash)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-style story for a child that includes the words "{f["burden"].label}" and "mule".',
        f"Tell a small myth where {f['hero'].id} speaks too much, the mule startles, and a flashback teaches a better way.",
        f'Write a gentle legend about a mule, a gabby boast, and a memory that makes the road safer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who was the story about?",
               answer=f"It was about {f['hero'].id}, {f['helper'].id}, the elder {f['elder'].id}, and a mule carrying {f['burden'].phrase}."),
        QAItem(question="What caused the trouble on the road?",
               answer=f"{f['hero'].id} spoke too loudly and boasted, and the mule startled near the sharp bend. The loud gab made the careful plan wobble."),
        QAItem(question="What was the flashback for?",
               answer=f"The flashback reminded everyone that quiet hands and quiet words keep a mule calm. That old lesson helped the road become safe again."),
        QAItem(question="How did the story end?",
               answer=f"They reached the shrine with the burden safe, and the mule stood calm at the hill's edge. The ending image shows that the boast had been replaced by patience."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mule?",
               answer="A mule is a strong animal that can carry loads and walk on hard roads. People often trust a mule to move slowly and carefully."),
        QAItem(question="What is gab?",
               answer="Gab is too much talk, especially loud talking that keeps going and going. In a story, gab can make a careful moment turn shaky."),
        QAItem(question="What is a flashback?",
               answer="A flashback is when a story pauses to remember an earlier moment. It helps explain why someone knows a lesson now."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(path="hill_road", burden="honey", hero="Mira", hero_gender="girl",
                helper="Oren", helper_gender="boy", elder="Ila", elder_gender="woman",
                gab_mode="boast", flashback_key="lesson"),
    StoryParams(path="river_path", burden="flowers", hero="Tavi", hero_gender="boy",
                helper="Nia", helper_gender="girl", elder="Mara", elder_gender="woman",
                gab_mode="taunt", flashback_key="market"),
]


def outcome_of(params: StoryParams) -> str:
    if params.flashback_key in FLASHBACKS and params.gab_mode in GABS:
        return "saved"
    return "?"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PATHS:
        lines.append(asp.fact("path", pid))
    for bid in BURDENS:
        lines.append(asp.fact("burden", bid))
    for gid in GABS:
        lines.append(asp.fact("gab", gid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    lines.append(asp.fact("quiet_min", QUIET_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,G,F) :- path(P), burden(B), gab(G), flashback(F), quiet_min(M), M = 2.
saved :- gab(G), flashback(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    for table, key in ((PATHS, params.path), (BURDENS, params.burden), (GABS, params.gab_mode), (FLASHBACKS, params.flashback_key)):
        if key not in table:
            raise StoryError(f"Invalid option: {key}")
    path = PATHS[params.path]
    burden = BURDENS[params.burden]
    gabcfg = GABS[params.gab_mode]
    flash = FLASHBACKS[params.flashback_key]
    if not reasonableness_gate(path, burden, gabcfg):
        raise StoryError("That story would not make a reasonable mythic problem.")
    world = tell(path, burden, gabcfg, flash, params.hero, params.hero_gender,
                 params.helper, params.helper_gender, params.elder, params.elder_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
