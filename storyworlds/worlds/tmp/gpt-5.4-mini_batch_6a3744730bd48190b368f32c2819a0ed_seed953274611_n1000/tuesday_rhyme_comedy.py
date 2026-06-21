#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tuesday_rhyme_comedy.py
=======================================================

A tiny storyworld for a comedy-rhyme Tuesday mishap: a child tries to make
Tuesday "fancier" with a rhyme game, the plan goes a bit silly, and a helper
turns the day into a cheerful win.

The world is intentionally small and classical:
- typed entities with meters and memes
- state-driven turn and resolution
- reasonableness gates plus an inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA

The core seed notion is a child on Tuesday trying a rhyme-based plan that is
funny, mildly chaotic, and then tidied into a pleasing ending image.
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
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CharacterCfg:
    id: str
    type: str
    label: str
    kind: str = "character"
    tags: set[str] = field(default_factory=set)


@dataclass
class PropCfg:
    id: str
    label: str
    mess: str
    messy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Scheme:
    id: str
    setup: str
    rhyme_line: str
    comedic_turn: str
    resolution: str
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
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["silly"] >= THRESHOLD and ("laugh", ent.id) not in world.fired:
            world.fired.add(("laugh", ent.id))
            ent.memes["joy"] += 1
            out.append(f"{ent.id} could not help but snort and giggle.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["splash"] >= THRESHOLD and ("mess", ent.id) not in world.fired:
            world.fired.add(("mess", ent.id))
            if "floor" in world.entities:
                world.get("floor").meters["sticky"] += 1
            out.append("__splash__")
    return out


CAUSAL_RULES = [Rule("laugh", _r_laugh), Rule("mess", _r_mess)]


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


@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    prop: str
    scheme: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", indoors=True, tags={"inside", "home"}),
    "laundry": Setting(id="laundry", place="the laundry room", indoors=True, tags={"inside", "home"}),
    "hall": Setting(id="hall", place="the hallway", indoors=True, tags={"inside", "home"}),
}

CHILDREN = {
    "maya": CharacterCfg(id="Maya", type="girl", label="a girl", tags={"child"}),
    "leo": CharacterCfg(id="Leo", type="boy", label="a boy", tags={"child"}),
    "nina": CharacterCfg(id="Nina", type="girl", label="a girl", tags={"child"}),
    "owen": CharacterCfg(id="Owen", type="boy", label="a boy", tags={"child"}),
}

HELPERS = {
    "mom": CharacterCfg(id="Mom", type="mother", label="Mom", tags={"helper"}),
    "dad": CharacterCfg(id="Dad", type="father", label="Dad", tags={"helper"}),
}

PROPS = {
    "spoon": PropCfg(id="spoon", label="a spoon", mess="flour", messy=True, tags={"rhyme", "comic"}),
    "cup": PropCfg(id="cup", label="a cup", mess="water", messy=True, tags={"rhyme", "comic"}),
    "sock": PropCfg(id="sock", label="a sock", mess="jam", messy=True, tags={"rhyme", "comic"}),
}

SCHEMES = {
    "rhyme_mess": Scheme(
        id="rhyme_mess",
        setup="wanted to make Tuesday a rhyme day",
        rhyme_line="Little tune, noon by noon, spoon and moon and silly swoon.",
        comedic_turn="but the rhyme game got rowdy and the spoon spun into the flour bowl.",
        resolution="so the helper laughed, wiped the white cloud away, and put the bowl back with a bow.",
        tags={"tuesday", "rhyme", "comedy"},
    ),
    "rhyme_tip": Scheme(
        id="rhyme_tip",
        setup="wanted to rhyme about Tuesday chores",
        rhyme_line="Tuesday, choosy, loopy, moony, mop the floor now, nice and swoony.",
        comedic_turn="but the cup wobbled, plopped, and splashed a stripe of water on the tiles.",
        resolution="so the helper mopped the stripe, chuckled at the splat, and called it a dance step.",
        tags={"tuesday", "rhyme", "comedy"},
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Ada", "Ruby", "Tess"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Milo", "Theo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CHILDREN:
            for hid in HELPERS:
                for pid in PROPS:
                    combos.append((sid, cid, hid, pid))
    return combos


def scheme_for(prop: PropCfg) -> Scheme:
    return SCHEMES["rhyme_mess"] if prop.mess == "flour" else SCHEMES["rhyme_tip"]


def funny_prediction(world: World, prop: PropCfg) -> dict:
    sim = world.copy()
    sim.get("prop").meters["silly"] += 1
    if prop.mess == "water":
        sim.get("prop").meters["splash"] += 1
    propagate(sim, narrate=False)
    return {
        "silly": sim.get("child").memes["joy"] >= THRESHOLD,
        "sticky": sim.get("floor").meters["sticky"] >= THRESHOLD,
    }


def intro(world: World, child: Entity, helper: Entity, setting: Setting, scheme: Scheme) -> None:
    world.say(
        f"On Tuesday, {child.id} and {helper.id} were in {setting.place}, and {child.id} "
        f"{scheme.setup}."
    )
    world.say(f"{scheme.rhyme_line}")


def trouble(world: World, child: Entity, helper: Entity, prop: PropCfg) -> None:
    child.memes["mischief"] += 1
    world.say(
        f'{child.id} grinned. "A rhyme can climb, and a joke can poke!" '
        f"Then {child.id} waved {prop.label} like a tiny parade baton."
    )
    if prop.mess == "flour":
        world.say("White flour puffed up like a sneezy little cloud.")
    else:
        world.say("Water quivered in the cup like it wanted to join the fun.")


def spill(world: World, prop: PropCfg) -> None:
    world.get("prop").meters["silly"] += 1
    if prop.mess == "water":
        world.get("prop").meters["splash"] += 1
    propagate(world, narrate=False)
    if prop.mess == "flour":
        world.say("Oops! The spoon twirled, tapped the bowl, and poof -- flour floated everywhere.")
    else:
        world.say("Oops! The cup tipped, and a little splash skated across the floor.")


def helper_fix(world: World, helper: Entity, prop: PropCfg, scheme: Scheme) -> None:
    world.get("floor").meters["sticky"] = 0
    world.get("prop").meters["silly"] = 0
    helper.memes["amusement"] += 1
    world.say(
        f"{helper.id} came over with a smile. {helper.id} said, "
        f'"That is the silliest Tuesday I have seen all day!"'
    )
    world.say(
        f"{helper.id} cleaned up the little mess, and {scheme.comedic_turn} "
        f"{scheme.resolution}"
    )


def ending(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, the floor was neat again, and {child.id} and {helper.id} "
        f"were laughing so hard that Tuesday felt like a joke that landed on its feet."
    )
    world.say(
        f"{child.id} held {child.pronoun('possessive')} prop like a prize and promised "
        f"to keep the next rhyme tidy."
    )


def tell(setting: Setting, child_cfg: CharacterCfg, helper_cfg: CharacterCfg, prop_cfg: PropCfg, scheme: Scheme) -> World:
    world = World()
    child = world.add(Entity(id=child_cfg.id, kind="character", type=child_cfg.type, label=child_cfg.label, role="child", tags=set(child_cfg.tags)))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper", tags=set(helper_cfg.tags)))
    prop = world.add(Entity(id="prop", type="thing", label=prop_cfg.label, tags=set(prop_cfg.tags)))
    floor = world.add(Entity(id="floor", type="thing", label="the floor"))

    intro(world, child, helper, setting, scheme)
    world.para()
    trouble(world, child, helper, prop_cfg)
    spill(world, prop_cfg)
    world.para()
    helper_fix(world, helper, prop_cfg, scheme)
    ending(world, child, helper)

    world.facts.update(
        child=child, helper=helper, prop=prop, floor=floor,
        setting=setting, prop_cfg=prop_cfg, scheme=scheme,
        outcome="messy_fun",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, prop_cfg = f["child"], f["helper"], f["prop_cfg"]
    return [
        f'Write a funny rhyme story for a young child about {child.id} on Tuesday and {prop_cfg.label}.',
        f"Tell a comedy story where {child.id} makes a silly rhyme plan, {helper.id} chuckles, and the day ends tidy.",
        f'Write a short Tuesday story that includes the word "Tuesday" and has a playful rhyme and a clean ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, prop_cfg = f["child"], f["helper"], f["prop_cfg"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}."),
        ("What made the story funny?", f"{child.id} tried to turn Tuesday into a rhyme game, and {prop_cfg.label} became part of the joke. The plan went a little wobbly, which made everyone laugh."),
        ("How did the helper respond?", f"{helper.id} laughed, cleaned up the mess, and turned the silly moment into a tidy finish. That kept the story cheerful instead of gloomy."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is Tuesday?", "Tuesday is a day of the week that comes after Monday."),
        ("What is a rhyme?", "A rhyme is when words sound alike at the end, like cat and hat."),
        ("Why can flour be messy?", "Flour is a soft powder, so it can puff into the air and cover things quickly."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", child="Maya", child_type="girl", helper="Mom", helper_type="mother", prop="spoon", scheme="rhyme_mess"),
    StoryParams(setting="laundry", child="Leo", child_type="boy", helper="Dad", helper_type="father", prop="cup", scheme="rhyme_tip"),
    StoryParams(setting="hall", child="Nina", child_type="girl", helper="Dad", helper_type="father", prop="sock", scheme="rhyme_mess"),
]


def explain_rejection() -> str:
    return "(No story: this little comedy world only supports the rhyme-and-tidy Tuesday mishap.)"


ASP_RULES = r"""
happy(T) :- setting(T), child(C), helper(H), prop(P), tuesday_word.
messy(P) :- prop_cfg(P), messy_prop(P).
resolve(C,H,P) :- messy(P), helper(H), child(C).
story_ok(T,C,H,P) :- happy(T), resolve(C,H,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("tuesday_word")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop_cfg", pid))
        if p.messy:
            lines.append(asp.fact("messy_prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    ok = bool(asp.atoms(model, "story_ok"))
    py_ok = bool(valid_combos())
    try:
        _ = generate(resolve_params(argparse.Namespace(setting=None, child=None, helper=None, prop=None, seed=None), random.Random(1)))
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    if ok and py_ok:
        print("OK: ASP/program smoke test passed and story generation works.")
        return 0
    print("MISMATCH: ASP or Python gating failed.")
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, c, h, p) for s in SETTINGS for c in CHILDREN for h in HELPERS for p in PROPS]


@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    prop: str
    scheme: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tuesday rhyme comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--scheme", choices=SCHEMES)
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
    if args.scheme and args.scheme not in SCHEMES:
        raise StoryError(explain_rejection())
    choices = [c for c in valid_combos()
               if (args.setting is None or c[0] == args.setting)
               and (args.child is None or c[1] == args.child)
               and (args.helper is None or c[2] == args.helper)
               and (args.prop is None or c[3] == args.prop)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, child, helper, prop = rng.choice(sorted(choices))
    scheme = args.scheme or rng.choice(sorted(SCHEMES))
    return StoryParams(setting=setting, child=child, child_type=CHILDREN[child].type,
                       helper=helper, helper_type=HELPERS[helper].type,
                       prop=prop, scheme=scheme)


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        child_cfg = CHILDREN[params.child]
        helper_cfg = HELPERS[params.helper]
        prop_cfg = PROPS[params.prop]
        scheme = SCHEMES[params.scheme]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc.args[0]}") from exc
    world = tell(setting, child_cfg, helper_cfg, prop_cfg, scheme)
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
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/4."))
        print(f"{len(asp.atoms(model, 'story_ok'))} story_ok facts")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
