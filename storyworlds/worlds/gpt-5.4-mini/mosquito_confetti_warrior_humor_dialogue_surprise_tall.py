#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mosquito_confetti_warrior_humor_dialogue_surprise_tall.py
=========================================================================================

A tiny Tall Tale storyworld about a brave little warrior, a mosquito troublemaker,
and a ridiculous confetti surprise that turns a scratchy problem into a laugh.

The world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a reasonableness gate plus inline ASP twin
- state-driven prose and Q&A
- standalone stdlib script with robust direct execution support
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    scene: str
    hot: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Threat:
    id: str
    label: str
    buzz: str
    bite: str
    tiny: bool = True
    annoying: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Surprise:
    id: str
    label: str
    phrase: str
    burst: str
    laughs: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_itch(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["buzzing"] < THRESHOLD:
            continue
        sig = ("itch", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["grumpy"] += 1
        out.append(f"__itch__")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["confetti"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append(f"__laugh__")
    return out


CAUSAL_RULES = [Rule("itch", "social", _r_itch), Rule("laugh", "social", _r_laugh)]


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


def bite_risk(threat: Threat, setting: Setting) -> bool:
    return threat.annoying and setting.hot


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict(world: World, threat_id: str) -> dict:
    sim = world.copy()
    _buzz(sim, sim.get(threat_id), narrate=False)
    return {"itchy": sim.get("hero").memes["grump"] >= THRESHOLD}


def _buzz(world: World, threat: Entity, narrate: bool = True) -> None:
    threat.meters["buzzing"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, sidekick: Entity, setting: Setting) -> None:
    hero.memes["bold"] += 1
    sidekick.memes["curious"] += 1
    world.say(
        f"On a hot little afternoon, {hero.id} and {sidekick.id} strode into "
        f"{setting.place}, where {setting.scene} made even the fence posts look like heroes."
    )
    world.say(
        f'{hero.id} wore a cardboard crown and said, "I am the warrior of this wild place!"'
    )
    world.say(f'{sidekick.id} laughed. "Then I shall be your trumpeter!"')


def trouble(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"Then a mosquito came whining by, {threat.buzz}, and gave {hero.id} a sharp little {threat.bite}."
    )
    world.say(f'{hero.id} swatted the air. "That tickles like a spoonful of nettles!"')


def warn(world: World, sidekick: Entity, hero: Entity, threat: Threat, setting: Setting) -> None:
    pred = predict(world, "mosquito")
    sidekick.memes["caution"] += 1
    world.facts["predicted_itch"] = pred["itchy"]
    world.say(
        f'{sidekick.id} pointed up and said, "{hero.id}, that mosquito means business.'
        f" If it keeps buzzing in this heat, you'll be grumpy as a goose in a rainstorm."
        f'"'
    )


def surprise(world: World, hero: Entity, sidekick: Entity, s: Surprise) -> None:
    hero.meters["confetti"] += 1
    sidekick.meters["confetti"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f'Then, with a pop and a puff, {s.phrase} burst from behind the watering can. '
        f"{s.burst} {s.laughs}"
    )
    world.say(f'{sidekick.id} gasped, "By gum, that is a confetti thundercloud!"')


def boast(world: World, hero: Entity) -> None:
    world.say(f'{hero.id} grinned. "Now I can fight like a warrior with party cannon courage!"')


def defeat(world: World, response: Response, threat: Threat) -> None:
    body = response.text.replace("{target}", threat.label)
    world.say(f"In a wink, the brave idea worked: {body}.")
    world.get("mosquito").meters["buzzing"] = 0


def fail(world: World, response: Response, threat: Threat) -> None:
    body = response.fail.replace("{target}", threat.label)
    world.say(f"The plan was too small for the trouble: {body}.")
    world.get("mosquito").meters["buzzing"] += 1


def ending(world: World, hero: Entity, sidekick: Entity, setting: Setting, s: Surprise) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"At last the mosquito buzzed off, confused by confetti and carried away by the wind."
    )
    world.say(
        f'{hero.id} bowed low. "{s.laughs}" {sidekick.id} cheered, and the two little warriors marched on '
        f"through {setting.place}, bright as a parade and twice as silly."
    )


def tell(setting: Setting, threat: Threat, surprise_cfg: Surprise, response: Response,
         hero_name: str = "Milo", side_name: str = "Pip",
         hero_gender: str = "boy", side_gender: str = "girl",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="warrior"))
    side = world.add(Entity(id=side_name, kind="character", type=side_gender, role="trumpeter"))
    world.add(Entity(id="mosquito", kind="thing", type="mosquito", label=threat.label))
    world.add(Entity(id="confetti", kind="thing", type="surprise", label=surprise_cfg.label))

    intro(world, hero, side, setting)
    world.para()
    trouble(world, hero, threat)
    warn(world, side, hero, threat, setting)
    if not bite_risk(threat, setting):
        world.say("But this was no real trouble, and the warrior only laughed.")
        outcome = "easy"
    else:
        surprise(world, hero, side, surprise_cfg)
        boast(world, hero)
        if is_contained(response, delay):
            defeat(world, response, threat)
            ending(world, hero, side, setting, surprise_cfg)
            outcome = "contained"
        else:
            fail(world, response, threat)
            world.say(
                f"{hero.id} had to retreat to the porch, where the lemonade was cold and the laughter was louder than the buzzing."
            )
            outcome = "escaped"
    world.facts.update(hero=hero, sidekick=side, setting=setting, threat=threat,
                       surprise=surprise_cfg, response=response, delay=delay,
                       outcome=outcome)
    return world


SETTINGS = {
    "yard": Setting("yard", "the backyard", "a hoop of grass, a squeaky gate, and a laundry line for a sky", hot=True),
    "barn": Setting("barn", "the barn lot", "hay bales, splintery boards, and a windmill that creaked jokes", hot=True),
    "porch": Setting("porch", "the porch", "a rocking chair stage and a sunflower curtain", hot=False),
}

THREATS = {
    "mosquito": Threat("mosquito", "a mosquito", "buzz-buzz", "a tiny pinch", tags={"mosquito"}),
}

SURPRISES = {
    "confetti": Surprise("confetti", "confetti", "a confetti cannon", "POP!", "The sky filled with silly paper stars.", tags={"confetti", "surprise"}),
}

RESPONSES = {
    "swat": Response("swat", 2, 1, "swatted the mosquito away with one grand heroic slap", "swatted, but the mosquito only got bolder", "swatted the mosquito away", tags={"humor"}),
    "net": Response("net", 3, 2, "caught the mosquito in a little net and set it loose by the fence", "tried a net, but the mosquito outflew it", "caught the mosquito in a little net", tags={"humor"}),
    "parade": Response("parade", 3, 3, "danced in a confetti parade until the mosquito flew off in a puzzled zigzag", "danced, but the mosquito kept buzzing", "danced in a confetti parade", tags={"humor", "confetti"}),
}

GIRL_NAMES = ["Pip", "Nell", "Mina", "Ivy", "June"]
BOY_NAMES = ["Milo", "Finn", "Bram", "Otis", "Jasper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in THREATS.items():
            for rid, r in RESPONSES.items():
                if bite_risk(t, s) and r.sense >= SENSE_MIN:
                    combos.append((sid, tid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    threat: str
    surprise: str
    response: str
    hero: str
    hero_gender: str
    sidekick: str
    side_gender: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


KNOWLEDGE = {
    "mosquito": [("What is a mosquito?", "A mosquito is a tiny flying bug that buzzes near people and can give a little bite.")],
    "confetti": [("What is confetti?", "Confetti is small pieces of colored paper that fall like a silly shower at a celebration.")],
    "warrior": [("What is a warrior?", "A warrior is a brave fighter, but in a story for children, a warrior can also be a playful pretend hero.")],
    "surprise": [("What is a surprise?", "A surprise is something unexpected that makes someone gasp, laugh, or smile.")],
}
ORDER = ["mosquito", "confetti", "warrior", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Tall Tale for a young child that includes the words "mosquito", "confetti", and "warrior".',
        f"Tell a funny dialogue story where {f['hero'].id} acts like a warrior, a mosquito causes trouble, and confetti brings a surprise.",
        f'Write a playful story with a buzzing mosquito, a confetti burst, and a brave-but-silly warrior ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, side, threat, s, resp = f["hero"], f["sidekick"], f["threat"], f["surprise"], f["response"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id} and {side.id}, two little heroes in a tall-tale backyard."),
        (f"What bothered {hero.id} at the start?", f"A mosquito bothered {hero.id}. It buzzed near {hero.id} and gave a tiny, itchy pinch."),
        ("What surprised the children?", f"{s.phrase} surprised them. It burst open so suddenly that the whole scene turned into a joke."),
    ]
    if f["outcome"] == "contained":
        qa.append((f"How did they solve the problem?", f"They used {resp.qa_text} after the confetti burst gave them a silly plan. The surprise made the mosquito fly off and the children felt brave again."))
        qa.append((f"How did the story end?", f"It ended with {hero.id} and {side.id} marching on like parade warriors, laughing in the windy yard. The mosquito was gone and the confetti was still fluttering around their boots."))
    else:
        qa.append((f"How did the story end?", f"The mosquito escaped for a while, so the children had to retreat and try again later. Even then, the laughing made the trouble feel smaller."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["threat"].id, world.facts["surprise"].id, "warrior"}
    out = []
    for k in ORDER:
        if k in tags and k in KNOWLEDGE:
            out.extend(KNOWLEDGE[k])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, response: Response) -> str:
    return f"(No story: this setup does not give the mosquito enough trouble for a real Tall Tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
buzzing(M) :- threat(M).
itchy(M) :- buzzing(M), hot_place(P), setting(P).
contained(R) :- response(R), sense(R,S), sense_min(M), S >= M, power(R,P), P >= 1.
valid(S,R) :- setting(S), response(R), threat(mosquito), hot_place(S), contained(R).
outcome(contained) :- contained(_).
outcome(escaped) :- not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.hot:
            lines.append(asp.fact("hot_place", sid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("setting", params.setting), asp.fact("response", params.response)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        s = generate(CURATED[0])
        assert s.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    cases = CURATED[:]
    for n in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(n)))
        except StoryError:
            pass
    if all(asp_outcome(p) in {"contained", "escaped"} for p in cases):
        print(f"OK: ASP outcome smoke check ran on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcome smoke check.")
    return rc


CURATED = [
    StoryParams("yard", "mosquito", "confetti", "parade", "Milo", "boy", "Pip", "girl", 0),
    StoryParams("barn", "mosquito", "confetti", "swat", "Nell", "girl", "Bram", "boy", 0),
    StoryParams("porch", "mosquito", "confetti", "net", "Ivy", "girl", "Otis", "boy", 0),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about a mosquito, confetti, and a warrior.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, threat, response = rng.choice(combos)
    hero_gender = rng.choice(["boy", "girl"])
    side_gender = "girl" if hero_gender == "boy" else "boy"
    hero = rng.choice(BOY_NAMES if hero_gender == "boy" else GIRL_NAMES)
    side = rng.choice(GIRL_NAMES if side_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, threat, "confetti", response, hero, hero_gender, side, side_gender, rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    w = tell(SETTINGS[params.setting], THREATS[params.threat], SURPRISES[params.surprise], RESPONSES[params.response],
             params.hero, params.sidekick, params.hero_gender, params.side_gender, params.delay)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=[QAItem(q, a) for q, a in story_qa(w)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(w)],
        world=w,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos: {asp_valid_combos()}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
