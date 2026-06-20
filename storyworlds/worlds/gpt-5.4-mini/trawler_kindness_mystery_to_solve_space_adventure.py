#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trawler_kindness_mystery_to_solve_space_adventure.py
====================================================================================

A small, self-contained storyworld for a space-adventure mystery on a trawler.

Premise:
- A trawler is carrying a strange cargo hold mystery.
- Two child crew members notice a clue in the ship's nets and ask for help.
- Kindness is the key: a gentle helper listens, shares tools, and solves the mystery.
- The ending proves what changed by showing the trawler calm, repaired, and ready to sail.

The world is deliberately tiny:
- Typed entities with physical meters and emotional memes.
- A forward-chained rule system.
- A Python reasonableness gate plus an inline ASP twin.
- Three Q&A sets generated from world state, not by parsing rendered English.
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
GOODWILL_MIN = 4
MYSTERY_MIN = 1


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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Trawler:
    id: str
    name: str
    route: str
    cargo_kind: str
    hold_label: str
    clue_kind: str
    calm_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    clue: str
    found_in: str
    reveal: str
    solved_by: str
    danger: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class KindnessAction:
    id: str
    tool: str
    method: str
    result: str
    generosity: int
    repair: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    trawler: str
    mystery: str
    kindness: str
    helper_name: str
    helper_gender: str
    kid1_name: str
    kid1_gender: str
    kid2_name: str
    kid2_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_calm(world: World) -> list[str]:
    out = []
    hold = world.get("hold")
    if hold.meters["alarm"] >= THRESHOLD and ("calm", "hold") not in world.fired:
        world.fired.add(("calm", "hold"))
        hold.meters["chaos"] += 1
        out.append("__alarm__")
    return out


def _r_solved(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters["noticed"] >= THRESHOLD and clue.meters["shared"] >= THRESHOLD:
        if ("solved", clue.id) not in world.fired:
            world.fired.add(("solved", clue.id))
            world.get("mystery").meters["solved"] += 1
            out.append("__solved__")
    return out


CAUSAL_RULES = [Rule("calm", _r_calm), Rule("solved", _r_solved)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(trawler: Trawler, mystery: Mystery, kindness: KindnessAction) -> bool:
    return trawler.cargo_kind == mystery.found_in and kindness.generosity >= GOODWILL_MIN and kindness.repair >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid, tr in TRAWLERS.items():
        for mid, my in MYSTERIES.items():
            for kid, ka in KINDNESS_ACTIONS.items():
                if reasonableness_ok(tr, my, ka):
                    combos.append((tid, mid, kid))
    return combos


def _do_mystery(world: World, kid: Entity, mystery: Mystery) -> None:
    clue = world.get("clue")
    hold = world.get("hold")
    clue.meters["noticed"] += 1
    kid.memes["curiosity"] += 1
    hold.meters["alarm"] += 1
    propagate(world, narrate=False)


def tell(trawler: Trawler, mystery: Mystery, kindness: KindnessAction,
         helper_name: str = "Mina", helper_gender: str = "girl",
         kid1_name: str = "Jules", kid1_gender: str = "boy",
         kid2_name: str = "Nova", kid2_gender: str = "girl") -> World:
    world = World()
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    kid1 = world.add(Entity(kid1_name, kind="character", type=kid1_gender, role="child"))
    kid2 = world.add(Entity(kid2_name, kind="character", type=kid2_gender, role="child"))
    ship = world.add(Entity("ship", type="ship", label=trawler.name))
    hold = world.add(Entity("hold", type="hold", label=trawler.hold_label))
    clue = world.add(Entity("clue", type="clue", label=mystery.clue))
    my = world.add(Entity("mystery", type="mystery", label="the mystery"))
    world.facts["trawler"] = trawler
    world.facts["mystery_cfg"] = mystery
    world.facts["kindness_cfg"] = kindness
    world.facts["helper"] = helper
    world.facts["kid1"] = kid1
    world.facts["kid2"] = kid2
    world.facts["ship"] = ship
    world.facts["hold"] = hold
    world.facts["clue"] = clue
    world.facts["mystery"] = my

    world.say(f"On a silver-blue morning, the trawler {trawler.name} hummed across the stars.")
    world.say(
        f"{kid1.id} and {kid2.id} were helping in the cargo hold when they found {mystery.clue}."
    )
    world.say(
        f'"It means something," {kid2.id} whispered, peering at the nets. '
        f'It felt like a mystery waiting to be solved.'
    )
    world.para()
    world.say(
        f"The clue sat near {mystery.found_in}, and the hold began to feel tense."
    )
    world.say(
        f"{helper.id} noticed the worried faces and listened before speaking. "
        f'"Let us solve it gently," {helper.pronoun()} said.'
    )

    _do_mystery(world, kid1, mystery)
    clue.meters["shared"] += 1
    helper.memes["kindness"] += kindness.generosity
    helper.memes["calm"] += 1

    world.para()
    if kindness.generosity >= GOODWILL_MIN:
        clue.meters["shared"] += 1
        hold.meters["calm"] += 1
        world.say(
            f"{helper.id} used {kindness.tool} and {kindness.method}, and the children helped."
        )
        world.say(
            f"They discovered {mystery.reveal}, which explained the strange sign in the hold."
        )
        world.say(
            f"The trawler stopped worrying and drifted toward {trawler.calm_place}, shining peacefully."
        )
        world.say(
            f"By the end, {kid1.id} and {kid2.id} were smiling, because kindness had solved the mystery."
        )
    else:
        world.say(
            f"{helper.id} tried, but the answer stayed tangled until a kinder plan could be found."
        )
        world.say(
            f"The hold remained noisy, and the trawler kept the mystery close for another day."
        )

    outcome = "solved" if world.get("mystery").meters["solved"] >= THRESHOLD else "unsolved"
    world.facts.update(outcome=outcome)
    return world


TRAWLERS = {
    "starfin": Trawler("starfin", "Starfin", "between moon ports", "seaweed crates", "the cargo hold", "glimmering dust", "Harbor Moon"),
    "comet_net": Trawler("comet_net", "Comet Net", "past the red ring", "star fruit", "the hold", "silver thread", "Dock Nine"),
    "tide_orbit": Trawler("tide_orbit", "Tide Orbit", "near the quiet reef", "shell boxes", "the lower hold", "a strange glow", "Lighthouse Station"),
}

MYSTERIES = {
    "glow_net": Mystery("glow_net", "a glowing net", "silver thread", "it was a cluster of tiny space-lamps tangled in the rope", "a repair beacon", "the crew might worry if they pulled too hard"),
    "whisper_box": Mystery("whisper_box", "a whispering box", "star fruit", "it was a music box that played when it felt the ship's motion", "a child friendly treasure", "someone had packed it by mistake"),
    "moon_dust": Mystery("moon_dust", "moon dust on the deck", "glimmering dust", "it was soft comet powder that stuck to boots and made bright tracks", "a map clue", "the trail led to the right crate"),
}

KINDNESS_ACTIONS = {
    "gentle_help": KindnessAction("gentle_help", "soft gloves", "spoke kindly and untangled the ropes", "the clue could be shared", 5, 2, {"kindness"}),
    "listen_first": KindnessAction("listen_first", "a lantern", "sat down and listened carefully", "the children felt safe enough to explain", 4, 1, {"kindness"}),
    "steady_fix": KindnessAction("steady_fix", "a repair kit", "tied the loose net back with careful knots", "the ship was safe again", 6, 3, {"kindness", "repair"}),
}

GIRL_NAMES = ["Nova", "Mina", "Luna", "Aya", "Iris", "Zia"]
BOY_NAMES = ["Jules", "Arlo", "Finn", "Tao", "Ezra", "Kai"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure trawler mystery with kindness.")
    ap.add_argument("--trawler", choices=TRAWLERS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--kindness", choices=KINDNESS_ACTIONS)
    ap.add_argument("--helper")
    ap.add_argument("--kid1")
    ap.add_argument("--kid2")
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
              if (args.trawler is None or c[0] == args.trawler)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tid, mid, kid = rng.choice(sorted(combos))
    helper_gender = rng.choice(["girl", "boy"])
    kid1_gender = "boy"
    kid2_gender = "girl"
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    kid1 = args.kid1 or rng.choice(BOY_NAMES)
    kid2 = args.kid2 or rng.choice(GIRL_NAMES)
    return StoryParams(tid, mid, kid, helper, helper_gender, kid1, kid1_gender, kid2, kid2_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tr, my, ka = f["trawler"], f["mystery_cfg"], f["kindness_cfg"]
    return [
        f'Write a space-adventure story on a trawler that includes the word "{tr.name}" and a mystery to solve.',
        f"Tell a gentle tale where {f['kid1'].id} and {f['kid2'].id} find {my.clue} and a kind helper solves the mystery.",
        f"Write a child-friendly spaceship-style story where kindness helps the crew explain {my.found_in} and calm the ship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tr, my, ka = f["trawler"], f["mystery_cfg"], f["kindness_cfg"]
    helper, kid1, kid2 = f["helper"], f["kid1"], f["kid2"]
    qa = [
        ("Where does the story happen?",
         f"It happens on the trawler {tr.name}, mostly in the cargo hold as it sails through space. The ship gives the mystery a small, cozy place to unfold."),
        ("What did the children find?",
         f"They found {my.clue}. It was a clue that made them think there was a mystery to solve."),
        ("How did the helper solve the mystery?",
         f"{helper.id} used {ka.tool} and {ka.method}. That gentle kindness helped everyone share the clue and understand what it meant."),
    ]
    if f.get("outcome") == "solved":
        qa.append((
            "How did the story end?",
            f"The mystery was solved, and the trawler drifted toward {tr.calm_place} feeling safe again. The ending shows that kindness turned worry into understanding."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a trawler?",
         "A trawler is a working boat that carries things and travels from place to place. In a story, it can feel like a small home on the water or among the stars."),
        ("What does kindness mean?",
         "Kindness means being gentle, helpful, and careful with other people's feelings. It can make scared people feel safe enough to talk."),
        ("What is a mystery?",
         "A mystery is something puzzling that needs clues before it makes sense. People solve mysteries by noticing details and asking good questions."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("starfin", "glow_net", "gentle_help", "Mina", "girl", "Jules", "boy", "Nova", "girl"),
    StoryParams("comet_net", "whisper_box", "listen_first", "Arlo", "boy", "Kai", "boy", "Iris", "girl"),
    StoryParams("tide_orbit", "moon_dust", "steady_fix", "Luna", "girl", "Ezra", "boy", "Zia", "girl"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit the trawler, the mystery, and the kindness needed for a believable solve.)"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TRAWLERS:
        lines.append(asp.fact("trawler", tid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for kid in KINDNESS_ACTIONS.values():
        lines.append(asp.fact("kindness", kid.id))
        lines.append(asp.fact("generosity", kid.id, kid.generosity))
        lines.append(asp.fact("repair", kid.id, kid.repair))
    lines.append(asp.fact("goodwill_min", GOODWILL_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, M, K) :- trawler(T), mystery(M), kindness(K),
                  cargo_kind(T, C), found_in(M, C),
                  generosity(K, G), goodwill_min(Min), G >= Min,
                  repair(K, R), R >= 1.
solved(T, M, K) :- valid(T, M, K).
"""


def asp_program(show: str) -> str:
    import asp
    lines = [asp_facts()]
    for tid, tr in TRAWLERS.items():
        lines.append(asp.fact("cargo_kind", tid, tr.cargo_kind))
    for mid, my in MYSTERIES.items():
        lines.append(asp.fact("found_in", mid, my.found_in))
    lines.append(ASP_RULES)
    lines.append(show)
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(trawler=None, mystery=None, kindness=None, helper=None, kid1=None, kid2=None), _random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(TRAWLERS[params.trawler], MYSTERIES[params.mystery], KINDNESS_ACTIONS[params.kindness],
                 params.helper_name, params.helper_gender, params.kid1_name, params.kid1_gender,
                 params.kid2_name, params.kid2_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(" ".join(t))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
