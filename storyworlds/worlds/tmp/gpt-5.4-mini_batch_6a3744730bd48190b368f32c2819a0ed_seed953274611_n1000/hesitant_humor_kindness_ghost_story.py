#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py
======================================================================

A standalone story world for a small, child-facing ghost story:
a hesitant child meets a funny ghost, chooses kindness, and discovers that
being brave can sound like a joke told softly in the dark.

The world is intentionally tiny and classical:
- one child
- one ghost
- one place with a spooky hiding spot
- one small problem caused by shyness and misunderstanding
- one kind action that turns the night warm and funny

The story stays close to a ghost-story mood, but the ending is gentle:
the child is hesitant, then kind, and the ghost turns from spooky to silly.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/hesitant_humor_kindness_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from collections import defaultdict
        if not isinstance(self.meters, defaultdict):
            self.meters = defaultdict(float, self.meters)
        if not isinstance(self.memes, defaultdict):
            self.memes = defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    sound: str
    smells: str


@dataclass
class Ghost:
    id: str
    label: str
    sound: str
    hidden_in: str
    trouble: str
    joke_style: str
    is_spooky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    label: str
    effect: str
    warmth: int
    humor: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    ghost: str
    kindness: str
    child_name: str
    child_gender: str
    child_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost:
        return out
    if ghost.meters["lonely"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hesitant"] += 1
    child.memes["fear"] += 1
    out.append("__spook__")
    return out


def _r_kind(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not child or not ghost:
        return []
    if child.meters["kindness"] < THRESHOLD:
        return []
    sig = ("kind",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["warm"] += 1
    ghost.memes["hope"] += 1
    child.memes["brave"] += 1
    return ["__kind__"]


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("kind", _r_kind)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if not s.startswith("__"):
                        world.say(s)


def predict_turn(world: World, act: KindAct) -> dict:
    sim = world.copy()
    sim.get("child").meters[act.id] += 1
    propagate(sim)
    return {
        "warmer": sim.get("ghost").meters["warm"] >= THRESHOLD,
        "brave": sim.get("child").memes["brave"] >= THRESHOLD,
    }


def tell(place: Place, ghost: Ghost, kind: KindAct, child_name: str = "Mina",
         child_gender: str = "girl", child_trait: str = "hesitant") -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, traits=[child_trait],
                             attrs={"role": "visitor"}))
    g = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost.label,
                         traits=["shy"], attrs={"hidden_in": ghost.hidden_in,
                                                "trouble": ghost.trouble}))
    world.add(Entity(id="lantern", type="thing", label="the little lantern"))
    child.memes["hesitant"] = 1.0
    g.meters["lonely"] = 1.0

    world.say(
        f"On a windy evening, {child.label} stood outside {place.label} and listened "
        f"to the soft {place.sound}. {place.dark_spot} looked very dark, and the air "
        f"smelled like {place.smells}."
    )
    world.say(
        f"{child.label} was hesitant. {child.pronoun().capitalize()} wanted to go in, "
        f"but every creak made {child.pronoun('possessive')} knees feel wobbly."
    )
    world.para()
    world.say(
        f"Then came a boo from {ghost.hidden_in}. {ghost.label} floated out, wearing "
        f"a sheet and looking worryingly dramatic."
    )
    world.say(
        f'"Boo," said {ghost.label}, "I am stuck, and I cannot even haunt properly. '
        f'Also, my joke got tangled in the broom."'
    )
    world.say(
        f"{child.label} blinked. The ghost was spooky, but also oddly funny."
    )
    world.para()
    world.say(
        f"{child.label} took a small breath and used {kind.label}. {kind.effect.capitalize()}."
    )
    child.meters[kind.id] += 1
    child.memes["kind"] += 1
    child.memes["hesitant"] += 1
    pred = predict_turn(world, kind)
    world.facts["pred"] = pred
    if pred["warmer"]:
        propagate(world)
        world.say(
            f"{child.label} held out {world.get('lantern').label} and said, "
            f'"I can help, if you want."'
        )
        world.say(
            f"{ghost.label} untangled the broom, grinned, and let out a laugh that "
            f"sounded like a teacup hiccupping."
        )
        ghost.meters["warm"] += 1
        ghost.memes["kindness"] += 1
        world.say(
            f"After that, the haunted hall was not so haunted at all. The ghost "
            f"showed {child.label} how to make a silly face in a mirror, and the "
            f"lantern made a bright circle on the floor where both of them danced."
        )
        world.say(
            f"By the end, {child.label} was still a little hesitant, but now it was "
            f"the nice kind of hesitant, the kind that pauses before a smile. "
            f"{ghost.label} waved from {place.dark_spot}, no longer scary, just happy."
        )
    else:
        raise StoryError("The kindness in this story must actually change the ghost.")
    world.facts.update(child=child, ghost=g, place=place, kindness=kind, outcome="warm")
    return world


PLACE_REGISTRY = {
    "hall": Place(id="hall", label="the old hall", dark_spot="The stairs", sound="tick-tocks",
                  smells="dust and rain"),
    "attic": Place(id="attic", label="the attic", dark_spot="The rafters", sound="bump-bumps",
                   smells="old wood and apple crates"),
    "cellar": Place(id="cellar", label="the cellar", dark_spot="The shelves", sound="drip-drips",
                    smells="cobwebs and potatoes"),
}

GHOST_REGISTRY = {
    "sheet": Ghost(id="sheet", label="Mr. Sheet", sound="boo", hidden_in="the laundry pile",
                   trouble="his broom", joke_style="dry"),
    "puff": Ghost(id="puff", label="Puff", sound="whooo", hidden_in="behind a trunk",
                  trouble="a tangled ribbon", joke_style="silly"),
}

KINDNESS_REGISTRY = {
    "lantern": KindAct(id="lantern", label="kindness", effect="it made the room feel less lonely",
                       warmth=1, humor=1, tags={"lantern", "warm"}),
    "smile": KindAct(id="smile", label="a gentle smile", effect="it gave the ghost a brave little spark",
                     warmth=1, humor=2, tags={"smile"}),
    "help": KindAct(id="help", label="a helping hand", effect="it made the ghost feel safe enough to laugh",
                    warmth=2, humor=1, tags={"help"}),
}

CURATED = [
    StoryParams(place="attic", ghost="puff", kindness="help", child_name="Mina",
                child_gender="girl", child_trait="hesitant"),
    StoryParams(place="hall", ghost="sheet", kindness="lantern", child_name="Noah",
                child_gender="boy", child_trait="hesitant"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACE_REGISTRY:
        for g in GHOST_REGISTRY:
            for k in KINDNESS_REGISTRY:
                combos.append((p, g, k))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with humor and kindness.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--ghost", choices=GHOST_REGISTRY)
    ap.add_argument("--kindness", choices=KINDNESS_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", default="hesitant")
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
    if args.trait != "hesitant":
        raise StoryError("This world is built around the word 'hesitant'.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ghost, kindness = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Nora", "Ivy", "Noah", "Eli", "Finn"])
    return StoryParams(place=place, ghost=ghost, kindness=kindness,
                       child_name=name, child_gender=gender, child_trait="hesitant")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle ghost story for a young child where the child is hesitant, "
        "then chooses kindness instead of running away.",
        f"Tell a spooky-but-funny story about {f['child'].label} meeting {f['ghost'].label} "
        f"in {world.place.label} and helping with a small problem.",
        "Write a ghost story with humor and kindness that ends with the ghost feeling warm."
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    g = world.facts["ghost"]
    k = world.facts["kindness"]
    return [
        QAItem(question="Why was the child hesitant?",
               answer=f"{c.label} was hesitant because {world.place.dark_spot.lower()} looked dark and spooky. "
                      f"The creaks and strange sounds made the night feel uncertain."),
        QAItem(question="What was funny about the ghost?",
               answer=f"{g.label} was scary at first, but then it complained about a tangled broom and told a joke-like boo. "
                      f"That made the ghost feel more silly than spooky."),
        QAItem(question="How did kindness change the story?",
               answer=f"{c.label} used {k.label} and offered help instead of turning away. "
                      f"That made {g.label} feel warm enough to laugh, and the haunted place became friendly."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to be hesitant?",
               answer="Being hesitant means you pause before acting because you feel unsure. You may want to do something, but you take a moment before you do it."),
        QAItem(question="Why can kindness help when someone is scared?",
               answer="Kindness can make a frightened person feel safe and seen. When someone gets help gently, fear often shrinks and courage can grow."),
        QAItem(question="Why are ghost stories often funny and spooky at the same time?",
               answer="Ghost stories can be spooky because of dark places and strange sounds. They can also be funny when the ghost is silly, friendly, or a little clumsy."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACE_REGISTRY or params.ghost not in GHOST_REGISTRY or params.kindness not in KINDNESS_REGISTRY:
        raise StoryError("(Invalid parameters.)")
    world = tell(PLACE_REGISTRY[params.place], GHOST_REGISTRY[params.ghost],
                 KINDNESS_REGISTRY[params.kindness], params.child_name,
                 params.child_gender, params.child_trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
kindness_causes_warmth :- kindness(_).
hesitant_child :- trait(hesitant).
good_story :- hesitant_child, kindness_causes_warmth, ghost(_), place(_).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", p) for p in PLACE_REGISTRY]
    lines += [asp.fact("ghost", g) for g in GHOST_REGISTRY]
    lines += [asp.fact("kindness", k) for k in KINDNESS_REGISTRY]
    lines.append(asp.fact("trait", "hesitant"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("#show good_story/0."))
    if not model:
        print("MISMATCH: ASP failed to derive a good story.")
        rc = 1
    if set(asp.atoms(model, "good_story")) != {()}:
        print("MISMATCH: unexpected ASP result.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: ASP and Python smoke tests passed.")
    return rc


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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
