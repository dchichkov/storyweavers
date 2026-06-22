#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/steep_parody_love_dim_boat_ramp_misunderstanding.py
============================================================================================================

A standalone storyworld for a small Fable-like tale at a boat ramp:
a child wants to test a toy boat on a steep ramp, a misunderstanding grows,
and a calm helper turns the mistake into a safe launch at love-dim dusk.

The storyworld models:
- typed entities with physical meters and emotional memes
- a simple forward causal engine
- a reasonableness gate and inline ASP twin
- three QA sets from world state, not from rendered text
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
CAUTIOUS_MIN = 2
STEADY_MIN = 2


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
    steep: bool = False
    launches: bool = False
    floats: bool = False
    gives_light: bool = False
    broken: bool = False

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
    steep: bool
    water: str
    mood: str


@dataclass
class ToyBoat:
    id: str
    label: str
    phrase: str
    floats: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    cue: str
    confusion: str
    truth: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    ramp = world.get("ramp")
    boat = world.get("boat")
    kid = world.get("child")
    if not kid.meters["push"] >= THRESHOLD:
        return out
    if "slip" in world.fired:
        return out
    world.fired.add(("slip",))
    if ramp.steep:
        boat.meters["sway"] += 1
        kid.memes["worry"] += 1
        ramp.meters["rattle"] += 1
        out.append("The little boat wobbled on the steep ramp.")
    return out


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    cue = world.facts.get("misunderstanding")
    if child.memes["certainty"] < THRESHOLD:
        return out
    sig = ("misread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["worry"] += 1
    child.memes["hurt"] += 1
    out.append(cue.confusion)
    return out


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("misread", _r_misread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_ok(ramp: Setting, boat: ToyBoat) -> bool:
    return ramp.steep and boat.floats


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for bid, boat in BOATS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if reasonableness_ok(setting, boat):
                    out.append((sid, bid, mid))
    return out


def _predict(world: World) -> dict:
    sim = world.copy()
    _try_launch(sim, narrate=False)
    return {
        "wobbled": sim.get("boat").meters["sway"] >= THRESHOLD,
        "hurt": sim.get("child").memes["hurt"] >= THRESHOLD,
    }


def _try_launch(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["push"] += 1
    child.memes["certainty"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, setting: Setting, boat: ToyBoat,
          misunderstanding: Misunderstanding, light: Light) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At the boat ramp, {child.id} and {helper.id} watched the water and the steep stones below."
    )
    world.say(
        f"{child.id} had {boat.phrase}, and the evening was love-dim with {light.glow}."
    )
    world.say(
        f"{child.id} pointed at the dock sign and smiled at its little parody, while {helper.id} frowned."
    )


def want_launch(world: World, child: Entity, boat: ToyBoat) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Let me send {boat.label} down the ramp," {child.id} said. '
        f'"It will ride the water like a tiny king."'
    )


def warn(world: World, helper: Entity, child: Entity, misunderstanding: Misunderstanding, setting: Setting) -> None:
    pred = _predict(world)
    helper.memes["care"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'"Wait," {helper.id} said. "I thought your joke meant you were trying to tip it. '
        f'That steep ramp can make things slide too fast."'
    )
    world.say(
        f'"No," {child.id} said, "I only meant the parody on the sign, not a dangerous trick."'
    )


def resolve(world: World, helper: Entity, child: Entity, boat: ToyBoat, light: Light, setting: Setting) -> None:
    child.memes["hurt"] = 0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then they laughed at the misunderstanding. {helper.id} held the boat level, and {child.id} gave it a careful push."
    )
    world.say(
        f"{light.label.capitalize()} glowed on the water, and the toy boat skimmed straight down to the shore."
    )
    world.say(
        f"By the end, the steep ramp was only a path, the parody was only a joke, and the love-dim evening looked kind."
    )


def tell(setting: Setting, boat: ToyBoat, misunderstanding: Misunderstanding, light: Light,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Mara", helper_gender: str = "girl",
         parent_name: str = "Gran", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent", label="Gran"))
    ramp = world.add(Entity(id="ramp", type="place", label="the boat ramp", steep=setting.steep))
    toy = world.add(Entity(id="boat", type="boat", label=boat.label, floats=boat.floats))
    child.memes["certainty"] = 0.0
    helper.memes["care"] = 1.0
    world.facts["misunderstanding"] = misunderstanding
    world.facts["setting"] = setting
    world.facts["boat_cfg"] = boat
    world.facts["light_cfg"] = light
    setup(world, child, helper, setting, boat, misunderstanding, light)
    world.para()
    want_launch(world, child, boat)
    warn(world, helper, child, misunderstanding, setting)
    world.para()
    if _predict(world)["wobbled"]:
        _try_launch(world, narrate=True)
        resolve(world, helper, child, boat, light, setting)
    world.facts.update(child=child, helper=helper, parent=parent, ramp=ramp, boat=toy)
    return world


SETTINGS = {
    "boat_ramp": Setting(id="boat_ramp", place="the boat ramp", steep=True, water="bay water", mood="love-dim"),
    "quiet_dock": Setting(id="quiet_dock", place="the dock", steep=False, water="still water", mood="soft dusk"),
}

BOATS = {
    "toy_sloop": ToyBoat(id="toy_sloop", label="a toy sloop", phrase="a toy sloop with a red sail", tags={"boat", "water"}),
    "cork_skiff": ToyBoat(id="cork_skiff", label="a cork skiff", phrase="a tiny cork skiff", tags={"boat", "water"}),
}

MISUNDERSTANDINGS = {
    "parody_sign": Misunderstanding(
        id="parody_sign",
        cue="parody",
        confusion="Gran thought the child meant a prank on the steep ramp, but the child only meant the funny parody on the sign.",
        truth="It was only a joke about the sign, not a trick with the boat.",
        fix="They cleared up the joke and launched carefully together.",
        tags={"misunderstanding", "parody"},
    ),
    "love_dim_glow": Misunderstanding(
        id="love_dim_glow",
        cue="love-dim",
        confusion="The helper mistook the love-dim glow for fear, but the child only meant the lantern was dim and gentle.",
        truth="The glow was soft, not scary, and it helped them see the water.",
        fix="They named the glow correctly and kept going calmly.",
        tags={"misunderstanding", "love-dim"},
    ),
}

LIGHTS = {
    "lantern": Light(id="lantern", label="a lantern", phrase="a little lantern", glow="a love-dim glow", tags={"light", "love-dim"}),
    "lamp": Light(id="lamp", label="a lamp", phrase="a small lamp", glow="a warm hush of light", tags={"light"}),
}

GIRL_NAMES = ["Mara", "Nina", "Ivy", "Lena", "June"]
BOY_NAMES = ["Milo", "Otis", "Finn", "Arlo", "Theo"]


@dataclass
class StoryParams:
    setting: str
    boat: str
    misunderstanding: str
    light: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="boat_ramp", boat="toy_sloop", misunderstanding="parody_sign", light="lantern",
                child_name="Milo", child_gender="boy", helper_name="Mara", helper_gender="girl",
                parent_name="Gran", parent_gender="woman"),
    StoryParams(setting="boat_ramp", boat="cork_skiff", misunderstanding="love_dim_glow", light="lamp",
                child_name="Ivy", child_gender="girl", helper_name="Theo", helper_gender="boy",
                parent_name="Dad", parent_gender="man"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like boat-ramp storyworld with misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.boat is None or c[1] == args.boat)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, boat, misunderstanding = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(LIGHTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    helper_name = args.helper_name or rng.choice([n for n in helper_pool if n != child_name])
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    parent_name = args.parent_name or ("Gran" if parent_gender == "woman" else "Dad")
    return StoryParams(setting=setting, boat=boat, misunderstanding=misunderstanding, light=light,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       parent_name=parent_name, parent_gender=parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    boat = f["boat_cfg"]
    mis = f["misunderstanding"]
    setting = f["setting"]
    return [
        f'Write a fable-like story set at a boat ramp that includes the words "steep", "{mis.cue}", and "love-dim".',
        f"Tell a short story where a child misunderstands a joke at {setting.place} and still launches {boat.label} safely.",
        f"Write a gentle misunderstanding story about {boat.label} at a steep ramp, ending with a calm fix and a kind lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    boat = f["boat_cfg"]
    mis = f["misunderstanding"]
    setting = f["setting"]
    pred = f.get("predicted", {})
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"It is about {child.id} and {helper.id}. They meet at the boat ramp, where the steep path and the little boat set the story in motion.",
        ),
        QAItem(
            question=f"What misunderstanding caused trouble before {boat.label} was launched?",
            answer=f"{mis.confusion} That misunderstanding made the moment tense, but it was really only a joke being taken the wrong way.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry when {child.id} talked about the ramp?",
            answer=f"{helper.id} worried because the ramp was steep and a boat could slide too quickly. The worry was about safety, not about stopping the fun.",
        ),
        QAItem(
            question=f"What did the helper do after the confusion was cleared up?",
            answer=f"{helper.id} held the boat level and helped {child.id} give it a careful push. That gentle method turned the mistake into a safe launch.",
        ),
    ] + (
        [QAItem(
            question=f"How did the prediction about the steep ramp turn out?",
            answer=f"The prediction warned that the boat could wobble, and it did wobble before the adults slowed down. That is why the story needed a calmer plan.",
        )] if pred else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["misunderstanding"].tags) | set(world.facts["boat_cfg"].tags) | {"boat", "water", "light"}
    out: list[QAItem] = []
    if "boat" in tags:
        out.append(QAItem("What is a toy boat?", "A toy boat is a small boat made for play, and it can float on water."))
    if "water" in tags:
        out.append(QAItem("What does it mean when something floats?", "Something that floats stays on top of the water instead of sinking."))
    if "light" in tags:
        out.append(QAItem("What is a lantern for?", "A lantern gives a gentle light so people can see without a bright glare."))
    if "misunderstanding" in tags:
        out.append(QAItem("What is a misunderstanding?", "A misunderstanding happens when people think a word or action means something else."))
    if "parody" in tags:
        out.append(QAItem("What is a parody?", "A parody is a funny imitation or joke that borrows from something familiar."))
    if "love-dim" in tags:
        out.append(QAItem("What does love-dim mean in this story?", "It means the light is soft and dim, warm enough to be gentle instead of glaring."))
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.steep:
            bits.append("steep=True")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
steep_ramp(R) :- ramp(R), steep(R).
compatible(S,B,M) :- setting(S), boat(B), misunderstanding(M), steep_ramp(S), floats(B).
wobbled :- child_push, steep_ramp(ramp), boat_float.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.steep:
            lines.append(asp.fact("steep", sid))
    for bid, b in BOATS.items():
        lines.append(asp.fact("boat", bid))
        if b.floats:
            lines.append(asp.fact("floats", bid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in the gate:")
            print("  only in clingo:", sorted(clingo_set - python_set))
            print("  only in python:", sorted(python_set - clingo_set))
        # smoke test ordinary generation
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        _ = format_qa(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"VERIFY FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for bid, boat in BOATS.items():
            for mid in MISUNDERSTANDINGS:
                if setting.steep and boat.floats:
                    combos.append((sid, bid, mid))
    return combos


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    boat = BOATS[params.boat]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    light = LIGHTS[params.light]
    return tell(setting, boat, mis, light, params.child_name, params.child_gender,
                params.helper_name, params.helper_gender, params.parent_name, params.parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def resolve_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.boat is None or c[1] == args.boat)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, boat, misunderstanding = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(LIGHTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or resolve_name(rng, child_gender)
    helper_name = args.helper_name or resolve_name(rng, helper_gender)
    if helper_name == child_name:
        helper_name = (["Mara", "Nina", "Ivy", "Lena", "June"] if helper_gender == "girl" else ["Milo", "Otis", "Finn", "Arlo", "Theo"])[0]
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    parent_name = args.parent_name or ("Gran" if parent_gender == "woman" else "Dad")
    return StoryParams(
        setting=setting,
        boat=boat,
        misunderstanding=misunderstanding,
        light=light,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, b, m in combos:
            print(s, b, m)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
