#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cheese_dim_bravery_foreshadowing_twist_myth.py
===============================================================================

A standalone storyworld in a small mythic domain: a cautious village, a dim
cheese-lantern, a brave child, a foretold warning, and a twist that reveals the
real hero was not the loud one.

The seed words and instruments are folded into a child-facing myth:
- cheese-dim: a dim, cheese-colored lantern in a shrine-cave
- Bravery: the child must choose whether to enter the dark hollow
- Foreshadowing: old signs and warnings hint at the danger and the twist
- Twist: the "monster" is not a monster at all

Run it:
    python storyworlds/worlds/gpt-5.4-mini/cheese_dim_bravery_foreshadowing_twist_myth.py
    python storyworlds/worlds/gpt-5.4-mini/cheese_dim_bravery_foreshadowing_twist_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/cheese_dim_bravery_foreshadowing_twist_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/cheese_dim_bravery_foreshadowing_twist_myth.py --verify
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
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    dark: bool = False
    glow: bool = False
    warns: bool = False
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    scene: str
    hollow: str
    relic: str
    omen: str


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    dim: bool = False
    glow: bool = False


@dataclass
class Warning:
    id: str
    label: str
    hint: str
    omen: str


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    ending: str


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
    tag: str
    apply: Callable[[World], list[str]]


def _r_darken(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    cave = world.get("cave")
    if lantern.meters["lit"] < THRESHOLD:
        return out
    sig = ("darken",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cave.meters["shadow"] += 1
    out.append("__shadow__")
    return out


def _r_heart(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["bravery"] < THRESHOLD or hero.meters["inside"] < THRESHOLD:
        return out
    sig = ("heart",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("cave").meters["listened"] += 1
    out.append("__heart__")
    return out


CAUSAL_RULES = [Rule("darken", "physical", _r_darken), Rule("heart", "social", _r_heart)]


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


def predict_twist(world: World) -> dict:
    sim = world.copy()
    _enter_cave(sim, narrate=False)
    return {"shadow": sim.get("cave").meters["shadow"], "listened": sim.get("cave").meters["listened"]}


def _enter_cave(world: World, narrate: bool = True) -> None:
    world.get("hero").meters["inside"] += 1
    propagate(world, narrate=narrate)


def setting_opening(world: World, hero: Entity, elder: Entity, setting: Setting, relic: Relic) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Long ago, in {setting.scene}, {hero.id} watched the old path to {setting.hollow}. "
        f"The shrine stood by a stone bowl, and a cheese-dim lantern hung beside it, glowing weakly."
    )
    world.say(
        f"{elder.id} pointed at the old marks. \"When the bowl goes dim,\" {elder.pronoun()} said, "
        f"\"the hollow asks for a brave heart.\""
    )


def foreshadow(world: World, hero: Entity, warning: Warning, setting: Setting) -> None:
    hero.memes["foresight"] += 1
    world.say(
        f"Even before the wind rose, there were signs: a cracked shell on the path, a cold hush near the stones, "
        f"and {warning.omen} carved above the cave mouth."
    )
    world.say(
        f"{warning.hint} said the village elder. \"The dark inside can trick a traveler's eyes.\""
    )


def choose(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["bravery"] += 2
    world.say(
        f"{hero.id} lifted the dim lantern and breathed in slowly. \"I will go,\" {hero.pronoun()} whispered, "
        f"\"even if the hollow looks hungry.\""
    )
    if relic.dim:
        world.say("The little light barely glowed, but it was enough to show the first step.")


def enter(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} stepped into {setting.hollow}. The air was cool, and every pebble seemed to listen."
    )
    _enter_cave(world, narrate=False)
    world.say("Inside, the walls turned the tiny light into long, dancing shapes.")


def reveal_twist(world: World, elder: Entity, twist: Twist) -> None:
    cave = world.get("cave")
    if cave.meters["shadow"] < THRESHOLD:
        return
    world.say(
        f"Then came the twist. The so-called monster was only {twist.reveal}, not a beast at all."
    )
    world.say(
        f"It had been guarding the old bowl because it remembered {twist.label}, and it feared the lantern would be stolen."
    )


def resolve(world: World, hero: Entity, elder: Entity, relic: Relic, twist: Twist) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{hero.id} held the cheese-dim lantern low and spoke gently instead of shouting."
    )
    world.say(
        f"{elder.id} smiled, and together they set {relic.phrase} back where it belonged."
    )
    world.say(
        f"{twist.ending}. From then on, the hollow stayed quiet, and the village told the tale at moonrise."
    )


def tell(setting: Setting, relic: Relic, warning: Warning, twist: Twist,
         hero_name: str = "Mira", hero_gender: str = "girl",
         elder_name: str = "Orin", elder_gender: str = "man") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    cave = world.add(Entity(id="cave", type="place", label=setting.hollow, dark=True))
    lantern = world.add(Entity(id="lantern", type="thing", label="cheese-dim lantern", glow=True))
    bowl = world.add(Entity(id="bowl", type="thing", label=relic.label))
    world.facts.update(setting=setting, relic=relic, warning=warning, twist=twist, hero=hero, elder=elder)

    setting_opening(world, hero, elder, setting, relic)
    world.para()
    foreshadow(world, hero, warning, setting)
    choose(world, hero, relic)
    enter(world, hero, setting)
    world.para()
    reveal_twist(world, elder, twist)
    resolve(world, hero, elder, relic, twist)
    world.facts.update(cave=cave, lantern=lantern, bowl=bowl, predicted=predict_twist(world))
    return world


SETTINGS = {
    "moon_hollow": Setting(
        id="moon_hollow",
        scene="the village of Marrow Hill",
        hollow="Moon Hollow",
        relic="the bright shell",
        omen="a crescent notch",
    ),
    "salt_cave": Setting(
        id="salt_cave",
        scene="the shore village of Brine Gate",
        hollow="Salt Cave",
        relic="the pearl cup",
        omen="a broken spiral",
    ),
    "pine_shrine": Setting(
        id="pine_shrine",
        scene="the pine village of Tall Ember",
        hollow="Pine Shrine",
        relic="the golden comb",
        omen="three small scratches",
    ),
}

RELICS = {
    "shell": Relic(id="shell", label="bright shell", phrase="the bright shell", dim=True, glow=False),
    "cup": Relic(id="cup", label="pearl cup", phrase="the pearl cup", dim=True, glow=False),
    "comb": Relic(id="comb", label="golden comb", phrase="the golden comb", dim=True, glow=False),
}

WARNINGS = {
    "moon": Warning(id="moon", label="moon warning", hint="The elder's voice grew low", omen="a crescent notch"),
    "salt": Warning(id="salt", label="salt warning", hint="The elder's voice grew low", omen="a broken spiral"),
    "pine": Warning(id="pine", label="pine warning", hint="The elder's voice grew low", omen="three small scratches"),
}

TWISTS = {
    "guardian": Twist(
        id="guardian",
        label="the guardian",
        reveal="a small cave-keeper with soot on its paws",
        ending="It bowed, accepted the returned relic, and gently pushed the lantern back to Mira",
    ),
    "mouse": Twist(
        id="mouse",
        label="the mouse",
        reveal="a white mouse wearing a seed pod like a crown",
        ending="It blinked, nibbled a crumb, and curled up beside the bowl like a sleepy king",
    ),
    "goat": Twist(
        id="goat",
        label="the goat",
        reveal="a shaggy goat with a bell and a very serious stare",
        ending="It stamped once, then led them safely out to the moonlit path",
    ),
}


@dataclass
class StoryParams:
    setting: str
    relic: str
    warning: str
    twist: str
    hero_name: str = "Mira"
    hero_gender: str = "girl"
    elder_name: str = "Orin"
    elder_gender: str = "man"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RELICS:
            for w in WARNINGS:
                for t in TWISTS:
                    combos.append((s, r, w, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with bravery, foreshadowing, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    warning = args.warning or rng.choice(list(WARNINGS))
    twist = args.twist or rng.choice(list(TWISTS))
    if setting not in SETTINGS or relic not in RELICS or warning not in WARNINGS or twist not in TWISTS:
        raise StoryError("Unknown mythic choice.")
    return StoryParams(
        setting=setting,
        relic=relic,
        warning=warning,
        twist=twist,
        hero_name=args.hero_name or rng.choice(["Mira", "Nia", "Leto", "Suri", "Kora"]),
        hero_gender=args.hero_gender or rng.choice(["girl", "boy"]),
        elder_name=args.elder_name or rng.choice(["Orin", "Tava", "Bren", "Edda"]),
        elder_gender=args.elder_gender or rng.choice(["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth for a young child that includes the phrase "cheese-dim" and shows {f["hero"].id} choosing bravery.',
        f"Tell a short myth where {f['hero'].id} follows a foreshadowed warning into {f['setting'].hollow} and learns a twist about the guardian.",
        f"Write a moonlit legend about a dim lantern, an old omen, and a gentle reveal that changes what the villagers believed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    setting = f["setting"]
    twist = f["twist"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, who decides to be brave in a strange old place. The elder guides {hero.pronoun('object')} with warnings and calm words.",
        ),
        QAItem(
            question="What did the foreshadowing do in the story?",
            answer=f"It hinted that something in {setting.hollow} was important and a little dangerous. The cracked sign and the elder's warning made the later reveal feel earned, not sudden.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the creature was not a monster at all; it was {twist.reveal}. That changed the meaning of the dark place and turned fear into understanding.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the truth was revealed?",
            answer=f"{hero.id} stayed gentle and listened instead of panicking. That calm choice let {elder.id} and {hero.id} put the relic back and leave in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means doing the right thing even when you feel a little scared. Brave people still notice the danger, but they keep going carefully.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important will happen later. It helps a story feel like the ending was waiting in the beginning.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening. Good twists make you look back and notice the clues again.",
        ),
        QAItem(
            question="Why use a dim lantern in a myth?",
            answer="A dim lantern makes the dark place feel mysterious and also a little risky. It gives the hero just enough light to move forward while the danger stays real.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.dark:
            bits.append("dark")
        if e.glow:
            bits.append("glow")
        if e.warns:
            bits.append("warns")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moon_hollow", relic="shell", warning="moon", twist="guardian", hero_name="Mira", hero_gender="girl", elder_name="Orin", elder_gender="man"),
    StoryParams(setting="salt_cave", relic="cup", warning="salt", twist="mouse", hero_name="Leto", hero_gender="boy", elder_name="Tava", elder_gender="woman"),
    StoryParams(setting="pine_shrine", relic="comb", warning="pine", twist="goat", hero_name="Suri", hero_gender="girl", elder_name="Bren", elder_gender="man"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.relic in RELICS and params.warning in WARNINGS and params.twist in TWISTS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for w in WARNINGS:
        lines.append(asp.fact("warning", w))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,W,T) :- setting(S), relic(R), warning(W), twist(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, relic=None, warning=None, twist=None, hero_name=None, elder_name=None, hero_gender=None, elder_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid mythic parameters.")
    setting = SETTINGS[params.setting]
    relic = RELICS[params.relic]
    warning = WARNINGS[params.warning]
    twist = TWISTS[params.twist]
    world = tell(setting, relic, warning, twist, params.hero_name, params.hero_gender, params.elder_name, params.elder_gender)
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} mythic combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
