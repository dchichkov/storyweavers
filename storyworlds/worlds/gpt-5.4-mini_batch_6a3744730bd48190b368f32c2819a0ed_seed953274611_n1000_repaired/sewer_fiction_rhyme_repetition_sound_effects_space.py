#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sewer_fiction_rhyme_repetition_sound_effects_space.py
=====================================================================================

A standalone tiny storyworld in a space-adventure mode.

Premise:
A child astronaut explores a maintenance sewer tunnel under a starship while
trying to write fiction for a ship radio show. The tunnel is noisy, slippery,
and dark, so the storyworld leans on rhyme, repetition, and sound effects as
real stateful tools: the child records beats, echoes, and clanks; a helper uses
them to guide the child; and the ending proves the tunnel is clean, the story
is finished, and the crew has a safe signal again.

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a Python reasonableness gate plus inline ASP twin
- generated prompts, story-grounded QA, and world-knowledge QA
- a complete story with beginning, turn, and resolution
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
    tags: set[str] = field(default_factory=set)
    sound: str = ""
    rhyme: str = ""
    plural: bool = False

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryWorldConfig:
    place: str
    helper: str
    helper_type: str
    hero: str
    hero_type: str
    ship_name: str
    problem: str
    rescue_tool: str
    clean_signal: str
    sound1: str
    sound2: str
    rhyme1: str
    rhyme2: str
    repetition_line: str
    style: str = "space adventure"
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    config: str
    hazard: str
    helper_action: str
    ending: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    ship_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if "tunnel" not in world.entities:
        return out
    tunnel = world.get("tunnel")
    if tunnel.meters["noise"] < THRESHOLD:
        return out
    sig = ("echo", int(tunnel.meters["noise"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    hero.memes["delight"] += 1
    out.append("The tunnel answered with a little echo.")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["mess"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    world.get("tunnel").meters["risk"] += 1
    out.append("The slick floor made the path more tricky.")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("slip", _r_slip)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(config: StoryWorldConfig) -> None:
    if "sewer" not in config.place.lower() and "tunnel" not in config.place.lower():
        raise StoryError("This storyworld needs a sewer-like tunnel setting.")
    if "fiction" not in config.problem.lower():
        raise StoryError("The premise should include fiction as the story-shaping task.")
    if not config.rhyme1 or not config.rhyme2:
        raise StoryError("The world needs rhyming beats.")
    if not config.sound1 or not config.sound2:
        raise StoryError("The world needs sound effects.")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(k, v.hazard, v.ending) for k, v in CONFIGS.items() if v.place and v.problem]


def tell(config: StoryWorldConfig, params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_type, role="hero",
        traits=["curious", "brave"], attrs={"job": "writer"},
    ))
    helper = world.add(Entity(
        id=params.helper, kind="character", type=params.helper_type, role="helper",
        traits=["steady", "kind"], attrs={"job": "mechanic"},
    ))
    tunnel = world.add(Entity(
        id="tunnel", kind="thing", type="place", label=config.place,
        attrs={"ship": config.ship_name},
    ))
    sewer = world.add(Entity(
        id="sewer", kind="thing", type="place", label="sewer pipe",
        attrs={"function": "drain"},
    ))
    script = world.add(Entity(
        id="script", kind="thing", type="object", label="fiction notebook",
        attrs={"genre": "fiction"},
    ))

    hero.memes["hope"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On the starship {config.ship_name}, {hero.id} drifted into the {config.place} "
        f"with a little fiction notebook tucked under one arm."
    )
    world.say(
        f'{hero.id} tapped the page and said, "{config.repetition_line}" '
        f"Then {hero.id} listened to the pipes: {config.sound1}, {config.sound2}."
    )
    world.say(
        f"{hero.id} wanted to make a tiny space tale, but the sewer tunnel was dark "
        f"and the floor shone with slime."
    )

    world.para()
    hero.meters["mess"] += 1
    tunnel.meters["noise"] += 1
    propagate(world)
    world.say(
        f"{helper.id} came by with a lantern and smiled. "
        f'"{config.rhyme1}," {helper.id} said, and then, "{config.rhyme2}."'
    )
    world.say(
        f"{helper.id} pointed to the work lights and showed {hero.id} how to turn the "
        f"noisy tunnel into a story trail."
    )

    world.para()
    helper.meters["repair"] += 1
    sewer.meters["clean"] += 1
    tunnel.meters["risk"] = 0
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    hero.meters["mess"] = 0
    world.say(
        f"Together they fixed the leak, wiped the slime from the rail, and tested the valve."
    )
    world.say(
        f"{config.sound1}! {config.sound2}! The tunnel sounded less scary now."
    )
    world.say(
        f"{hero.id} finished the fiction page with a grin: the brave scout followed the glow, "
        f"the sewer stayed safe, and the ship kept humming."
    )

    world.facts.update(
        config=config,
        hero=hero,
        helper=helper,
        tunnel=tunnel,
        sewer=sewer,
        script=script,
        outcome=params.ending,
        hazard=params.hazard,
        helper_action=params.helper_action,
    )
    return world


CONFIGS = {
    "default": StoryWorldConfig(
        place="sewer tunnel",
        helper="Mira",
        helper_type="girl",
        hero="Nova",
        hero_type="girl",
        ship_name="Comet Lantern",
        problem="fiction for the radio log",
        rescue_tool="lantern",
        clean_signal="green light",
        sound1="drip-drip",
        sound2="clang-clang",
        rhyme1="A dark pipe? Not quite hype.",
        rhyme2="With light and might, we make it right.",
        repetition_line="Drip, drip, trip; I write the ship.",
    ),
    "echo": StoryWorldConfig(
        place="sewer corridor",
        helper="Talon",
        helper_type="boy",
        hero="Orla",
        hero_type="girl",
        ship_name="Moon Harbor",
        problem="fiction about a lost star",
        rescue_tool="lamp",
        clean_signal="safe signal",
        sound1="whoosh-whoosh",
        sound2="plink-plink",
        rhyme1="If the tunnel grumbles, stay in bundles.",
        rhyme2="When clues glow low, go slow.",
        repetition_line="Tap, tap, cap; I map the gap.",
    ),
}

HAZARDS = {"slip": "slick slime", "drip": "dripping pipe"}
HELPER_ACTIONS = {"guide": "guided the way", "repair": "repaired the leak"}
ENDINGS = {"safe": "safe", "bright": "bright"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure sewer fiction storyworld.")
    ap.add_argument("--config", choices=CONFIGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper-action", choices=HELPER_ACTIONS, dest="helper_action")
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    config_key = args.config or rng.choice(list(CONFIGS))
    config = CONFIGS[config_key]
    hazard = args.hazard or rng.choice(list(HAZARDS))
    helper_action = args.helper_action or rng.choice(list(HELPER_ACTIONS))
    ending = args.ending or rng.choice(list(ENDINGS))
    return StoryParams(
        config=config_key,
        hazard=hazard,
        helper_action=helper_action,
        ending=ending,
        hero=config.hero,
        hero_type=config.hero_type,
        helper=config.helper,
        helper_type=config.helper_type,
        ship_name=config.ship_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story that includes the words "sewer" and "fiction".',
        f"Tell a child-friendly story where {f['hero'].id} writes fiction in a sewer tunnel "
        f"on the starship {f['config'].ship_name}.",
        f"Make the story use rhyme, repetition, and sound effects while {f['helper'].id} helps "
        f"{f['hero'].id} through the sewer."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    config = f["config"]
    return [
        QAItem(
            question="What was the child trying to make?",
            answer=f"{hero.id} was trying to make fiction for the ship radio show. The story was part of a space adventure, so the page needed a brave ending."
        ),
        QAItem(
            question="Who helped in the sewer tunnel?",
            answer=f"{helper.id} helped {hero.id}. {helper.id} brought calm words and pointed out the safe lights, which made the dark tunnel feel easier."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the sewer leak fixed, the tunnel cleaned up, and the child finishing a brave little fiction page. The ending image is the ship humming safely again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sewer?",
            answer="A sewer is a pipe or tunnel that carries dirty water away. It can be dark and slippery, so people need to be careful there."
        ),
        QAItem(
            question="What is fiction?",
            answer="Fiction is a made-up story. Writers use it to imagine things that are not real but still feel exciting."
        ),
        QAItem(
            question="Why do sound effects help a story?",
            answer="Sound effects help a story feel lively and easy to picture. A drip, a clang, or a whoosh can make the scene sound real in your head."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.config not in CONFIGS:
        raise StoryError("Unknown config.")
    config = CONFIGS[params.config]
    reasonableness_gate(config)
    world = tell(config, params)
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


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(Config, Hazard, Ending) :- config(Config), hazard(Hazard), ending(Ending).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in CONFIGS:
        lines.append(asp.fact("config", k))
    for k in HAZARDS:
        lines.append(asp.fact("hazard", k))
    for k in ENDINGS:
        lines.append(asp.fact("ending", k))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            config=None, hazard=None, helper_action=None, ending=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(
        config="default", hazard="slip", helper_action="guide", ending="safe",
        hero="Nova", hero_type="girl", helper="Mira", helper_type="girl",
        ship_name="Comet Lantern",
    ),
    StoryParams(
        config="echo", hazard="drip", helper_action="repair", ending="bright",
        hero="Orla", hero_type="girl", helper="Talon", helper_type="boy",
        ship_name="Moon Harbor",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(k, h, e) for k in CONFIGS for h in HAZARDS for e in ENDINGS]


def build_header(sample: StorySample) -> str:
    p = sample.params
    return f"### {p.hero} in {p.config} ({p.hazard}, {p.ending})"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid_combos(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=build_header(sample) if args.all or len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
