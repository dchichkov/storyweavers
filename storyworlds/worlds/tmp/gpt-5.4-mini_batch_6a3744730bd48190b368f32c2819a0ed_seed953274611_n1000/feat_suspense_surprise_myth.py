#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/feat_suspense_surprise_myth.py
==============================================================

A small myth-like storyworld about a young hero attempting a sacred feat:
crossing a bridge, climbing a cliff, or carrying a gift through a dark grove.
The tales are built from state changes, suspense before the attempt, and a
surprise that changes the ending image.

This world keeps the prose child-facing and concrete:
- typed entities with physical meters and emotional memes
- a forward simulation that drives the story
- a reasonableness gate over valid premise/feat/comeback combinations
- an inline ASP twin for parity checks
- three QA sets generated from world state, not from rendered English
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
SUSPENSE_MIN = 1
SURPRISE_MIN = 1


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
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Premise:
    id: str
    scene: str
    opening: str
    dark_place: str
    risk: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Feat:
    id: str
    title: str
    verb: str
    object_name: str
    obstacle: str
    danger: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    title: str
    reveal: str
    help_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["doubt"] >= THRESHOLD and ("suspense", hero.id) not in world.fired:
        world.fired.add(("suspense", hero.id))
        hero.memes["suspense"] += 1
        out.append("__suspense__")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    if world.facts.get("reveal_done") and ("reveal",) not in world.fired:
        world.fired.add(("reveal",))
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend([s for s in res if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PREMISES:
        for f in FEATS:
            for s in SURPRISES:
                if p.id in {"grove", "bridge", "cave"} and f.id in {"crossing", "offering", "rescue"}:
                    combos.append((p.id, f.id, s.id))
    return combos


@dataclass
class StoryParams:
    premise: str
    feat: str
    surprise: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    ruler: str
    ruler_type: str
    seed: Optional[int] = None


PREMISES = {
    "grove": Premise(
        id="grove",
        scene="a moonlit grove",
        opening="The grove was quiet, and the silver leaves whispered above the path.",
        dark_place="the hollow oak beyond the stones",
        risk="The path was narrow, and the old stones hid a deep ditch.",
        omen="At the edge of the dark trees, even the crickets seemed to hold their breath.",
        tags={"night", "wood", "suspense"},
    ),
    "bridge": Premise(
        id="bridge",
        scene="a river bridge",
        opening="The bridge crossed a fast river that flashed like black glass.",
        dark_place="the center plankway",
        risk="The boards were old, and the river roared beneath them.",
        omen="Mist curled around the ropes, hiding what waited ahead.",
        tags={"water", "suspense"},
    ),
    "cave": Premise(
        id="cave",
        scene="a stony cave",
        opening="The cave yawned like a sleeping giant under the hill.",
        dark_place="the back tunnel",
        risk="The tunnel was black, and loose pebbles rolled under small feet.",
        omen="A cold wind sighed from inside, as if the cave knew a secret.",
        tags={"stone", "suspense"},
    ),
}

FEATS = {
    "crossing": Feat(
        id="crossing",
        title="the crossing",
        verb="cross",
        object_name="the path",
        obstacle="the dark gap ahead",
        danger="the gap could swallow a step",
        reveal="a hidden stone span",
        tags={"feat", "crossing"},
    ),
    "offering": Feat(
        id="offering",
        title="the offering",
        verb="carry",
        object_name="the lantern-bowl",
        obstacle="the heavy wind",
        danger="the wind might blow out the flame",
        reveal="a warm hidden lamp",
        tags={"feat", "offering"},
    ),
    "rescue": Feat(
        id="rescue",
        title="the rescue",
        verb="reach",
        object_name="the lost child",
        obstacle="the echoing dark",
        danger="the dark made every sound feel far away",
        reveal="a secret opening in the rock",
        tags={"feat", "rescue"},
    ),
}

SURPRISES = {
    "lantern": Surprise(
        id="lantern",
        title="the lantern",
        reveal="A small lantern blinked awake where no one had seen it before.",
        help_text="Its gold light made the shadows step back.",
        ending_image="The grove glowed softly, and the path looked kind instead of fierce.",
        tags={"light", "surprise"},
    ),
    "song": Surprise(
        id="song",
        title="the song",
        reveal="A bird in the branches began to sing the oldest tune in the hill.",
        help_text="The song made the helper remember the safe way through.",
        ending_image="The air seemed brighter, and the dark place no longer felt lonely.",
        tags={"song", "surprise"},
    ),
    "crown": Surprise(
        id="crown",
        title="the crown",
        reveal="Inside the hollow stone lay a little crown of leaves and shell.",
        help_text="It was not a prize for winning, but a sign that the land had chosen the hero.",
        ending_image="The hero held the leaf-crown, smiling beside the opened way.",
        tags={"crown", "surprise"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like storyworld about a suspenseful feat and a surprise ending.")
    ap.add_argument("--premise", choices=PREMISES)
    ap.add_argument("--feat", choices=FEATS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["boy", "girl", "mother", "father", "queen", "king"])
    ap.add_argument("--ruler")
    ap.add_argument("--ruler-type", choices=["mother", "father", "queen", "king"])
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


def _pick(rng: random.Random, seq: list[str], avoid: str = "") -> str:
    opts = [x for x in seq if x != avoid]
    return rng.choice(opts)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.premise is None or c[0] == args.premise)
              and (args.feat is None or c[1] == args.feat)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    premise, feat, surprise = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "mother", "father"])
    ruler_type = args.ruler_type or rng.choice(["queen", "king", "mother", "father"])
    hero = args.hero or _pick(rng, ["Mira", "Tavi", "Nilo", "Rin", "Sera", "Kian"])
    helper = args.helper or _pick(rng, ["Eli", "Luna", "Ivo", "Nara", "Ari", "Sol"], avoid=hero)
    ruler = args.ruler or _pick(rng, ["Queen Alia", "King Orin", "Mother Vale", "Father Hesh"])
    return StoryParams(
        premise=premise,
        feat=feat,
        surprise=surprise,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        ruler=ruler,
        ruler_type=ruler_type,
    )


def _make_world(params: StoryParams) -> World:
    if params.premise not in PREMISES:
        raise StoryError(f"Unknown premise: {params.premise}")
    if params.feat not in FEATS:
        raise StoryError(f"Unknown feat: {params.feat}")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise: {params.surprise}")
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    ruler = world.add(Entity(id="ruler", kind="character", type=params.ruler_type, label=params.ruler, role="ruler"))
    premise = PREMISES[params.premise]
    feat = FEATS[params.feat]
    surprise = SURPRISES[params.surprise]
    world.facts.update(hero=hero, helper=helper, ruler=ruler, premise=premise, feat=feat, surprise=surprise)
    hero.meters["doubt"] = 1.0
    helper.memes["trust"] = 1.0
    ruler.memes["watchful"] = 1.0
    return world


def tell(world: World) -> World:
    f = world.facts
    hero, helper, ruler = f["hero"], f["helper"], f["ruler"]
    premise, feat, surprise = f["premise"], f["feat"], f["surprise"]
    hero.memes["hope"] += 1
    world.say(f"In {premise.scene}, {hero.label} and {helper.label} came before {ruler.label}. {premise.opening}")
    world.say(f"Their task was {feat.title}: to {feat.verb} {feat.object_name} while {premise.risk.lower()}")
    world.say(f"{premise.omen}")
    world.para()
    world.say(f"{helper.label} pointed ahead. \"The {feat.obstacle} is there,\" {helper.pronoun()} whispered. \"{feat.danger}.\"")
    hero.memes["suspense"] += 1
    world.say(f"{hero.label} gripped {hero.pronoun('possessive')} hands and took one careful breath.")
    world.say(f"That was a true {feat.id}, brave and small at once.")
    world.para()
    hero.meters["doubt"] += 1
    propagate(world, narrate=False)
    world.say(f"They went forward anyway. Just as {feat.danger}, {surprise.reveal}")
    world.say(f"{surprise.help_text}")
    world.say(f"With the surprise light and the helper close beside {hero.pronoun('object')}, {hero.label} finished the feat.")
    world.para()
    world.say(f"{surprise.ending_image} {hero.label} looked like a child from the old myths, but the kind of hero who learned and kept going.")
    hero.memes["joy"] += 1
    world.facts["reveal_done"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_make_world(params))
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a myth-like story for a child where {f['hero'].label} tries {f['feat'].title} in {f['premise'].scene} and the word feat appears.",
        f"Tell a suspenseful story with a surprise ending where {f['hero'].label} and {f['helper'].label} face {f['feat'].danger} before {f['surprise'].title} appears.",
        f"Write a short myth about a brave child, a dark place, and a hidden surprise that helps finish the feat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, ruler = f["hero"], f["helper"], f["ruler"]
    premise, feat, surprise = f["premise"], f["feat"], f["surprise"]
    return [
        ("Who is the story about?",
         f"It is about {hero.label} and {helper.label}, with {ruler.label} watching over the old place. The story follows {hero.label} as {hero.pronoun()} tries to do a feat."),
        ("What made the middle of the story feel suspenseful?",
         f"The dark place and {feat.danger} made everyone wait and wonder what would happen. The hero had to take a careful step before the surprise came."),
        ("What surprise changed the ending?",
         f"{surprise.reveal} That surprise gave the hero help right when it was needed, so the feat could be finished."),
        ("How did the story end?",
         f"{surprise.ending_image} The ending shows that the dangerous place became safe enough for the hero to stand there proudly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["premise"].tags) | set(f["feat"].tags) | set(f["surprise"].tags)
    out = []
    for tag, items in {
        "suspense": [("What is suspense?", "Suspense is the feeling of waiting and wondering what will happen next.")],
        "surprise": [("What is a surprise in a story?", "A surprise is something unexpected that changes what the characters thought would happen.")],
        "feat": [("What is a feat?", "A feat is a hard and brave thing someone does.")],
        "light": [("Why is light helpful in a dark place?", "Light helps you see the ground and find the safe way forward.")],
        "crown": [("What can a crown mean in a myth?", "A crown can be a sign of honor, victory, or being chosen.")],
        "song": [("Why do songs matter in myths?", "Songs can carry memory, warning, or help in old stories.")],
    }.items():
        if tag in tags:
            out.extend(items)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(premise="grove", feat="crossing", surprise="lantern", hero="Mira", hero_type="girl", helper="Eli", helper_type="boy", ruler="Queen Alia", ruler_type="queen"),
    StoryParams(premise="bridge", feat="offering", surprise="song", hero="Tavi", hero_type="boy", helper="Luna", helper_type="girl", ruler="King Orin", ruler_type="king"),
    StoryParams(premise="cave", feat="rescue", surprise="crown", hero="Sera", hero_type="girl", helper="Ari", helper_type="boy", ruler="Mother Vale", ruler_type="mother"),
]


ASP_RULES = r"""
premise(P) :- premise_id(P).
feat(F) :- feat_id(F).
surprise(S) :- surprise_id(S).
valid(P,F,S) :- premise(P), feat(F), surprise(S).

suspense(P) :- premise(P), dark(P).
surprise_ready(S) :- surprise(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PREMISES.items():
        lines.append(asp.fact("premise_id", pid))
        if "suspense" in p.tags:
            lines.append(asp.fact("dark", pid))
    for fid in FEATS:
        lines.append(asp.fact("feat_id", fid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_id", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-like suspense and surprise storyworld.")
    ap.add_argument("--premise", choices=PREMISES)
    ap.add_argument("--feat", choices=FEATS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["boy", "girl", "mother", "father", "queen", "king"])
    ap.add_argument("--ruler")
    ap.add_argument("--ruler-type", choices=["mother", "father", "queen", "king"])
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
    combos = [c for c in valid_combos()
              if (args.premise is None or c[0] == args.premise)
              and (args.feat is None or c[1] == args.feat)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    premise, feat, surprise = rng.choice(sorted(combos))
    return StoryParams(
        premise=premise,
        feat=feat,
        surprise=surprise,
        hero=args.hero or rng.choice(["Mira", "Tavi", "Nilo", "Rin", "Sera", "Kian"]),
        hero_type=args.hero_type or rng.choice(["boy", "girl"]),
        helper=args.helper or rng.choice(["Eli", "Luna", "Ivo", "Nara", "Ari", "Sol"]),
        helper_type=args.helper_type or rng.choice(["boy", "girl", "mother", "father", "queen", "king"]),
        ruler=args.ruler or rng.choice(["Queen Alia", "King Orin", "Mother Vale", "Father Hesh"]),
        ruler_type=args.ruler_type or rng.choice(["queen", "king", "mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.premise not in PREMISES or params.feat not in FEATS or params.surprise not in SURPRISES:
        raise StoryError("Invalid story parameters.")
    world = tell(_make_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def _make_world(params: StoryParams) -> World:
    return tell_world(params)


def tell_world(params: StoryParams) -> World:
    return tell(_build_world(params))


def _build_world(params: StoryParams) -> World:
    return _make_world_core(params)


def _make_world_core(params: StoryParams) -> World:
    return _world_from_params(params)


def _world_from_params(params: StoryParams) -> World:
    return _world(params)


def _world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    ruler = world.add(Entity(id="ruler", kind="character", type=params.ruler_type, label=params.ruler, role="ruler"))
    world.facts.update(hero=hero, helper=helper, ruler=ruler, premise=PREMISES[params.premise], feat=FEATS[params.feat], surprise=SURPRISES[params.surprise])
    hero.meters["doubt"] = 1.0
    return world


def tell(world: World) -> World:
    f = world.facts
    hero, helper, ruler = f["hero"], f["helper"], f["ruler"]
    premise, feat, surprise = f["premise"], f["feat"], f["surprise"]
    world.say(f"In {premise.scene}, {hero.label} and {helper.label} came before {ruler.label}. {premise.opening}")
    world.say(f"The task was {feat.title}: to {feat.verb} {feat.object_name} while {premise.risk.lower()}.")
    world.say(premise.omen)
    world.para()
    world.say(f"{helper.label} whispered, \"{feat.danger}.\"")
    hero.meters["doubt"] += 1
    hero.memes["suspense"] += 1
    world.say(f"{hero.label} took one careful breath and went forward.")
    world.para()
    world.say(f"Just as the moment tightened, {surprise.reveal} {surprise.help_text}")
    world.say(f"{hero.label} used the surprise and finished the feat.")
    world.para()
    world.say(f"{surprise.ending_image}")
    world.facts["reveal_done"] = True
    return world


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
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
