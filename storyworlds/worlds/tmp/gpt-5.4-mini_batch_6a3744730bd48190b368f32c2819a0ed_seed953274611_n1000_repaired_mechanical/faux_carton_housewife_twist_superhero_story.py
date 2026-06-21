#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/faux_carton_housewife_twist_superhero_story.py
==============================================================================

A small standalone storyworld for a superhero-style tiny tale built from the
seed words faux, carton, housewife, with a twist beat.

The world follows a compact simulated domain:
- a kid or neighbor tries a faux superhero disguise
- a carton gadget is used for a stunt or rescue
- a housewife notices something off
- a twist reveals the disguise or plan was not what it seemed
- the ending proves what changed in the world state

This script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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
        female = {"girl", "mother", "mom", "woman", "housewife"}
        male = {"boy", "father", "dad", "man", "hero"}
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
class HeroPack:
    id: str
    disguise: str
    reveal: str
    power_phrase: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class CartonGadget:
    id: str
    label: str
    use: str
    risk: str
    repair: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class TwistBeat:
    id: str
    clue: str
    reveal: str
    ending: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    carton = world.entities.get("carton")
    if not hero or not carton:
        return out
    if hero.memes["nervous"] < THRESHOLD:
        return out
    sig = ("clue", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["doubt"] += 1
    out.append("A tiny clue made the brave plan feel less certain.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("housewife")
    hero = world.entities.get("hero")
    carton = world.entities.get("carton")
    if not helper or not hero or not carton:
        return out
    if hero.meters["hidden"] < THRESHOLD:
        return out
    sig = ("twist", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["surprise"] += 1
    hero.memes["surprise"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("clue", "social", _r_clue), Rule("twist", "social", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def hero_disguise_ok(pack: HeroPack) -> bool:
    return "hero" in pack.tags


def carton_can_help(gadget: CartonGadget) -> bool:
    return "carton" in gadget.tags and gadget.repair


def twist_relevant(twist: TwistBeat) -> bool:
    return "twist" in twist.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hp in HERO_PACS:
        for cg in CARTON_GADGETS:
            for tw in TWISTS:
                if hero_disguise_ok(hp) and carton_can_help(cg) and twist_relevant(tw):
                    combos.append((hp.id, cg.id, tw.id))
    return combos


def predict(world: World) -> dict:
    sim = world.copy()
    _do_hidden(sim, narrate=False)
    return {"twist": bool(sim.facts.get("twisted")), "hope": sim.get("hero").memes["hope"]}


def _do_hidden(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.meters["hidden"] += 1
    hero.memes["nervous"] += 1
    propagate(world, narrate=narrate)


def start(world: World, hero: Entity, helper: Entity, pack: HeroPack, gadget: CartonGadget) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"On a bright street, {hero.id} wore a faux mask and a shiny cape, "
        f"trying to feel like a real superhero."
    )
    world.say(
        f"{helper.label_word.capitalize()} watched from the doorway, and a "
        f"{gadget.label} waited on the table like a tiny machine with a secret."
    )
    world.say(
        f'"If the city needs me," {hero.id} whispered, "{pack.power_phrase}!"'
    )


def challenge(world: World, hero: Entity, gadget: CartonGadget) -> None:
    hero.memes["nervous"] += 1
    world.say(
        f"But the wind tugged at the faux cape, and the {gadget.label} "
        f"wobbled when {hero.id} picked it up."
    )
    world.say(
        f'That made the rescue plan feel tricky, because the {gadget.label} could '
        f"{gadget.use}, but it also had a {gadget.risk}."
    )


def warn(world: World, helper: Entity, hero: Entity, gadget: CartonGadget, pack: HeroPack) -> None:
    pred = predict(world)
    helper.memes["care"] += 1
    world.facts["prediction"] = pred
    world.say(
        f'{helper.id} smiled and said, "{hero.id}, that is a faux costume, but '
        f'you can still be brave. Just be careful with the {gadget.label}."'
    )
    world.say(
        f"She noticed that the little gadget could {gadget.use}, which was handy, "
        f"but only if nobody forgot {gadget.repair}."
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["bold"] += 1
    world.say(f"{hero.id} nodded and tried anyway, because heroes like to act fast.")


def hide_then_twist(world: World, hero: Entity, helper: Entity, twist: TwistBeat) -> None:
    _do_hidden(world, narrate=False)
    world.facts["twisted"] = True
    world.say(
        f"{helper.id} reached for the {twist.clue}, but then the big twist appeared: "
        f"{twist.reveal}"
    )
    world.say(
        f"For one surprised moment, the faux hero stood still under the cape."
    )


def rescue(world: World, hero: Entity, helper: Entity, gadget: CartonGadget, pack: HeroPack) -> None:
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Then {helper.id} used the {gadget.label} the careful way, and it {gadget.repair}."
    )
    world.say(
        f"{hero.id} straightened the faux mask, smiled, and realized the real hero trick "
        f"was helping without showing off."
    )
    world.say(
        f"{pack.ending}"
    )


def tell(pack: HeroPack, gadget: CartonGadget, twist: TwistBeat) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="boy", label="the kid", role="hero"))
    helper = world.add(Entity(id="housewife", kind="character", type="housewife", label="the housewife", role="helper"))
    carton = world.add(Entity(id="carton", kind="thing", type="carton", label=gadget.label))
    world.add(Entity(id="faux", kind="thing", type="thing", label=pack.disguise))
    start(world, hero, helper, pack, gadget)
    world.para()
    challenge(world, hero, gadget)
    warn(world, helper, hero, gadget, pack)
    defy(world, hero)
    hide_then_twist(world, hero, helper, twist)
    world.para()
    rescue(world, hero, helper, gadget, pack)
    world.facts.update(hero=hero, helper=helper, carton=carton, pack=pack, gadget=gadget, twist=twist, twisted=True)
    return world


HERO_PACS = {
    "faux": HeroPack(id="faux", disguise="a faux mask and cape", reveal="the costume was only paper and string", power_phrase="I am almost ready to fly", tags={"hero", "faux"}),
    "spark": HeroPack(id="spark", disguise="a bright red suit", reveal="the bright suit hid a tiny patch job", power_phrase="I can dash like lightning", tags={"hero"}),
    "shadow": HeroPack(id="shadow", disguise="a dark hood and boots", reveal="the hood covered a shy grin", power_phrase="I can sneak and help", tags={"hero"}),
}

CARTON_GADGETS = {
    "box": CartonGadget(id="box", label="carton box", use="carry pretend tools", risk="flimsy side that bent", repair="taped the seam shut"),
    "ramp": CartonGadget(id="ramp", label="cardboard ramp", use="send a toy car rolling", risk="slippery edge that tilted", repair="held the edge down"),
    "shield": CartonGadget(id="shield", label="carton shield", use="block a splash", risk="soft corner that folded", repair="pressed the corner flat"),
}

TWISTS = {
    "swap": TwistBeat(id="swap", clue="cardboard badge", reveal="the housewife had secretly built the gadget for the kid", ending="The faux hero was grinning because the whole stunt had been a kind surprise.", tags={"twist"}),
    "reveal": TwistBeat(id="reveal", clue="curtain", reveal="the 'villain' was only a toy robot with a stuck wheel", ending="The city was safe, and the silly robot got a gentle push home.", tags={"twist"}),
    "helper": TwistBeat(id="helper", clue="window", reveal="the housewife had already solved the problem before the alarm ever rang", ending="The faux hero learned that calm help can be every bit as brave.", tags={"twist"}),
}

NAMES = ["Milo", "Nina", "Ari", "Pia", "Jules", "Ivy"]


@dataclass
class StoryParams:
    pack: str
    gadget: str
    twist: str
    name: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with faux, carton, housewife, and a twist.")
    ap.add_argument("--pack", choices=sorted(HERO_PACS))
    ap.add_argument("--gadget", choices=sorted(CARTON_GADGETS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
    ap.add_argument("--name")
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
    choices = []
    for pack in HERO_PACS:
        for gadget in CARTON_GADGETS:
            for twist in TWISTS:
                if ((args.pack is None or args.pack == pack) and
                    (args.gadget is None or args.gadget == gadget) and
                    (args.twist is None or args.twist == twist)):
                    choices.append((pack, gadget, twist))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    pack, gadget, twist = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    return StoryParams(pack=pack, gadget=gadget, twist=twist, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "faux", "carton", and "housewife".',
        f"Tell a short brave story where {f['hero'].id} wears a faux disguise, uses a carton gadget, and learns something surprising from the housewife.",
        f"Write a gentle action story with a twist ending where the faux hero is helped by the housewife and the carton becomes important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gadget = f["gadget"]
    twist = f["twist"]
    return [
        QAItem(
            question="What kind of disguise did the kid wear?",
            answer="The kid wore a faux mask and cape, so the look was pretend rather than truly super. That made the costume feel playful, not serious."
        ),
        QAItem(
            question="What did the carton gadget do?",
            answer=f"The {gadget.label} could {gadget.use}, which helped the plan move along. It also needed care because it had a flimsy part that could bend."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"{helper.id} turned out to be ahead of the problem the whole time, and {twist.reveal}. The surprise changed the mood from worried to proud."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does faux mean?",
            answer="Faux means fake or pretend. A faux thing is made to look like the real thing."
        ),
        QAItem(
            question="What is carton?",
            answer="A carton is a box made from stiff paperboard. People use cartons to hold or carry things."
        ),
        QAItem(
            question="What is a housewife?",
            answer="A housewife is a woman who takes care of a home and helps keep it running smoothly. She may cook, clean, or solve problems in the house."
        ),
        QAItem(
            question="Why do superhero stories often have a twist?",
            answer="A twist surprises the reader and changes what we thought was happening. It makes the ending feel exciting and clever."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.pack not in HERO_PACS or params.gadget not in CARTON_GADGETS or params.twist not in TWISTS:
        raise StoryError("Invalid story parameters.")
    world = tell(HERO_PACS[params.pack], CARTON_GADGETS[params.gadget], TWISTS[params.twist])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
valid(P,G,T) :- pack(P), gadget(G), twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in HERO_PACS:
        lines.append(asp.fact("pack", pid))
    for gid in CARTON_GADGETS:
        lines.append(asp.fact("gadget", gid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos().")
    try:
        sample = generate(StoryParams(pack="faux", gadget="box", twist="swap", name="Milo"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(pack="faux", gadget="box", twist="swap", name="Milo"),
    StoryParams(pack="spark", gadget="shield", twist="reveal", name="Nina"),
    StoryParams(pack="shadow", gadget="ramp", twist="helper", name="Ari"),
]


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_defaults(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, g, t in asp_valid_combos():
            print(f"  {p:8} {g:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.pack}, {p.gadget}, {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
