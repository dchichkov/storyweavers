#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chant_soy_cautionary_ghost_story.py
====================================================================

A standalone storyworld for a small cautionary ghost story.

Premise:
- A child and a cautious helper explore a quiet night market / pantry-like place.
- They hear a ghostly chant about soy sauce.
- A tempting shortcut with soy sauce makes a spooky mess and wakes a small ghost.
- A careful adult/helpful friend shows how to calm the ghost, clean up, and leave a safer offering.
- The ending proves the change: the chant is replaced by a gentle apology and the room is peaceful.

The domain is intentionally tiny and classical: typed entities, meters for physical
state, memes for emotional state, a forward-chained causal model, grounded QA,
and an inline ASP twin for the validity gate.
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
MESH = {"spilled", "sticky", "cold"}
SCARED_LEVEL = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dimness: str
    props: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    where: str
    whisper: str
    forbidden: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    near: str
    spill: str
    flammable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    charm: str
    target: str
    remedy: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["spill"] < THRESHOLD or e.meters["sticky"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ghost" in world.entities:
            world.get("ghost").memes["unease"] += 1
        for hid in ("hero", "guide", "elder"):
            if hid in world.entities:
                world.get(hid).memes["fear"] += 1
        out.append("__spook__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(charm: Charm, target: Target, remedy: Remedy) -> bool:
    return charm.forbidden and charm.label == "soy sauce" and target.flammable and remedy.sense >= 2


def ghost_severity(target: Target) -> int:
    return 2 if target.flammable else 1


def is_safe(remedy: Remedy, target: Target) -> bool:
    return remedy.power >= ghost_severity(target)


def predict_spook(world: World, target_id: str) -> dict:
    sim = world.copy()
    _apply_charm(sim, sim.get(target_id), narrate=False)
    return {
        "spooky": sim.get("ghost").memes["unease"] >= THRESHOLD if "ghost" in sim.entities else False,
        "fear": sum(e.memes["fear"] for e in sim.entities.values()),
    }


def _apply_charm(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["spill"] += 1
    target.meters["sticky"] += 1
    target.meters["cold"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", dimness="soft and blue", props="a counter, a kettle, and a bowl of rice"),
    "cellar": Setting(id="cellar", place="the cellar", dimness="dim and echoing", props="old jars, boxes, and a creaky shelf"),
    "nightmarket": Setting(id="nightmarket", place="the night market", dimness="glittery and dark", props="paper lanterns, wooden stalls, and one quiet pot"),
}

CHARMS = {
    "soy": Charm(id="soy", label="soy sauce", phrase="a bottle of soy sauce", where="on the counter", whisper="the soy sauce looked dark as a tiny lake", forbidden=True, tags={"soy"}),
}

TARGETS = {
    "paper": Target(id="paper", label="paper lantern", phrase="a paper lantern", near="the thin paper", spill="spilled", flammable=True, tags={"lantern", "paper"}),
    "rice": Target(id="rice", label="rice bowl", phrase="a bowl of rice", near="the warm rice", spill="spilled", flammable=False, tags={"rice"}),
}

REMEDIES = {
    "apology": Remedy(id="apology", sense=3, power=2, text="calmly wiped the soy sauce off the lantern, bowed to the little ghost, and set out a clean spoonful of rice", fail="tried to wipe the mess away, but the ghost kept rattling the cups", qa_text="wiped the soy sauce off the lantern, bowed to the little ghost, and set out a clean spoonful of rice", tags={"clean", "rice"}),
    "cloth": Remedy(id="cloth", sense=2, power=1, text="covered the spill with a dry cloth and whispered a sorry chant until the room grew quiet", fail="covered the spill, but the damp spot stayed dark and the ghost would not rest", qa_text="covered the spill with a dry cloth and whispered a sorry chant", tags={"clean", "chant"}),
    "tea": Remedy(id="tea", sense=3, power=2, text="poured a warm cup of tea near the shelf and spoke a gentle apology", fail="poured tea, but it was not enough to settle the ghostly fuss", qa_text="poured a warm cup of tea and spoke a gentle apology", tags={"tea"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Iris"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Theo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMS:
            for t in TARGETS:
                for r in REMEDIES:
                    if reasonableness_ok(CHARMS[c], TARGETS[t], REMEDIES[r]):
                        combos.append((s, c, t, r))
    return combos


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary ghost story with soy sauce, chant, and a careful ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["mother", "father"])
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
    if args.charm and args.target and args.remedy:
        if not reasonableness_ok(CHARMS[args.charm], TARGETS[args.target], REMEDIES[args.remedy]):
            raise StoryError("No story: that soy/target/remedy mix is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.target is None or c[2] == args.target)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, target, remedy = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or ("boy" if hero_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice(["mother", "father"])
    hero = args.hero or _pick_name(rng, hero_gender)
    guide = args.guide or _pick_name(rng, guide_gender)
    elder = args.elder or rng.choice(["Aunt Mei", "Uncle Jun", "Grandma", "Grandpa"])
    return StoryParams(setting=setting, charm=charm, target=target, remedy=remedy,
                       hero=hero, hero_gender=hero_gender, guide=guide, guide_gender=guide_gender,
                       elder=elder, elder_gender=elder_gender)


def tell(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    guide = w.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    elder = w.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder, role="elder"))
    ghost = w.add(Entity(id="ghost", kind="character", type="ghost", label="the little ghost"))
    setting = SETTINGS[params.setting]
    charm = CHARMS[params.charm]
    target_cfg = TARGETS[params.target]
    remedy = REMEDIES[params.remedy]
    w.facts["setting"] = setting
    w.facts["charm"] = charm
    w.facts["target_cfg"] = target_cfg
    w.facts["remedy"] = remedy

    hero.memes["curiosity"] += 1
    guide.memes["caution"] += 1
    w.say(f"That night, {hero.id} and {guide.id} slipped into {setting.place}. It was {setting.dimness}, with {setting.props}.")
    w.say(f'{guide.id} whispered, "Keep your voice low." But somewhere in the dark, a ghost began a soft chant.')
    w.say(f'The chant sounded like: "{charm.label}, soy, soy..." and {charm.whisper}.')
    w.para()
    pred = predict_spook(w, "target")
    w.facts["pred"] = pred
    w.say(f'{hero.id} leaned toward {target_cfg.phrase} because the room felt still, and the bottle of soy sauce was close by.')
    w.say(f'{guide.id} bit {guide.pronoun("possessive")} lip. "That is a bad idea," {guide.pronoun()} said. "Soy sauce can make a sticky mess, and in a haunted room even a little mess can wake the ghost."')
    _apply_charm(w, ghost if False else w.add(Entity(id="target", kind="thing", type="thing", label=target_cfg.label, flammable=target_cfg.flammable)), narrate=True)
    w.say(f'"{params.hero}!" {guide.id} cried. "The chant got louder."')
    w.para()
    if is_safe(remedy, target_cfg):
        body = remedy.text
        w.say(f"{elder.label_word.capitalize() if elder.label_word else elder.label} came in quietly and {body}.")
        w.say(f"The little ghost stopped rattling. It liked the clean smell better than the sticky one.")
        w.say(f'{elder.label if elder.label else "The elder"} nodded once and said, "A cautionary place teaches best when you leave it better than you found it."')
        hero.memes["relief"] += 1
        guide.memes["relief"] += 1
        ghost.memes["calm"] += 1
        w.para()
        w.say(f"After that, {hero.id} and {guide.id} put the soy sauce back on the shelf and bowed to the shadows.")
        w.say(f'This time, the only chant was a quiet apology, and the kitchen stayed peaceful.')
    else:
        body = remedy.fail
        w.say(f"{elder.label_word.capitalize() if elder.label_word else elder.label} tried to help, but {body}.")
        w.say(f"The ghost kept the cups clacking, and the room never quite settled.")
    w.facts["outcome"] = "calm"
    w.facts["ghost"] = ghost
    w.facts["hero"] = hero
    w.facts["guide"] = guide
    w.facts["elder"] = elder
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary ghost story that includes the words "chant" and "soy".',
        f"Tell a child-facing ghost story where {f['hero'].id} hears a spooky chant, makes a soy sauce mistake, and then learns a careful lesson.",
        f"Write a small haunted story that starts with a chant and ends with a calm, safe cleanup involving soy sauce.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, elder = f["hero"], f["guide"], f["elder"]
    target_cfg = f["target_cfg"]
    out = [
        ("Who is the story about?", f"It is about {hero.id}, {guide.id}, and {elder.label}. They are the ones who hear the ghostly chant and try to handle the soy sauce carefully."),
        ("What made the room spooky?", f"A ghost began a chant, and the soy sauce got spilled near {target_cfg.label}. The sticky mess made the ghost wake up and rattle things around."),
        ("Why did the guide warn the hero?", f"The guide knew soy sauce could make a sticky mess. In a haunted room, that kind of mess can scare the ghost or wake it up even more."),
        ("How did the story end?", f"It ended with a careful cleanup and a calmer room. The final image is of a quiet apology, the soy sauce put away, and the ghost resting again."),
    ]
    if f.get("pred"):
        out.append(("What did the guide predict would happen?", f"The guide predicted that the soy sauce would make things spooky and leave the room feeling uneasy. That was why the warning came before the spill grew worse."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is soy sauce?", "Soy sauce is a dark, salty sauce used for cooking and dipping. If it spills, it can leave a sticky, messy spot."),
        ("What is a chant?", "A chant is a repeated set of words or sounds. In a ghost story, a chant can sound spooky because it keeps going over and over."),
        ("Why can a ghost story teach a lesson?", "A ghost story can show what happens when a bad choice is made, then show a safer choice. That makes it a cautionary story."),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", charm="soy", target="paper", remedy="apology",
                hero="Mina", hero_gender="girl", guide="Ben", guide_gender="boy",
                elder="Grandma", elder_gender="mother"),
    StoryParams(setting="cellar", charm="soy", target="paper", remedy="cloth",
                hero="Noah", hero_gender="boy", guide="Iris", guide_gender="girl",
                elder="Uncle Jun", elder_gender="father"),
]


def explain_rejection() -> str:
    return "(No story: this tiny ghost tale needs soy sauce, a flammable target, and a sensible remedy.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.forbidden:
            lines.append(asp.fact("forbidden", cid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,T,R) :- setting(S), charm(C), target(T), remedy(R), forbidden(C), flammable(T), sense(R,SN), SN >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.charm not in CHARMS or params.target not in TARGETS or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
    if not reasonableness_ok(CHARMS[params.charm], TARGETS[params.target], REMEDIES[params.remedy]):
        raise StoryError(explain_rejection())
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.target is None or c[2] == args.target)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, target, remedy = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting, charm=charm, target=target, remedy=remedy,
        hero=args.hero or _pick_name(rng, args.hero_gender or rng.choice(["girl", "boy"])),
        hero_gender=args.hero_gender or rng.choice(["girl", "boy"]),
        guide=args.guide or _pick_name(rng, args.guide_gender or rng.choice(["girl", "boy"])),
        guide_gender=args.guide_gender or rng.choice(["girl", "boy"]),
        elder=args.elder or rng.choice(["Grandma", "Grandpa", "Aunt Mei", "Uncle Jun"]),
        elder_gender=args.elder_gender or rng.choice(["mother", "father"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
