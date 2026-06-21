#!/usr/bin/env python3
"""
storyworlds/worlds/electrocute_twist_rhyming_story.py
=====================================================

A small standalone storyworld built from the seed phrase:

    "electrocute" + "Twist" + "Rhyming Story"

Premise
-------
A child and a helper are making a rhyming twist in a stormy room. A sparkly
string light, a wet puddle, and a forbidden plug create a near-disaster. The
helper predicts the danger, the child makes a wrong choice, and then a grown-up
rescues the moment. In the twist ending, the family swaps the risky light for a
safe, battery-powered glow and the rhyme changes from scary to bright.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes,
- a forward-chained causal simulation,
- a reasonableness gate,
- an inline ASP twin,
- three QA sets grounded in simulated state,
- child-facing prose in a rhyming, storybook style.

This script is standalone and uses only the standard library plus the shared
storyworlds/results.py containers, with storyworlds/asp.py imported lazily only
for ASP modes.
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
    phrase: str = ""
    role: str = ""
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
    mood: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RiskObject:
    id: str
    label: str
    phrase: str
    makes_flame: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistObject:
    id: str
    label: str
    phrase: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_danger(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["wet"] < THRESHOLD:
            continue
        sig = ("wet_danger", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["danger"] += 1
        out.append("__danger__")
    return out


def _r_shock(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    plug = world.get("plug")
    puddle = world.get("puddle")
    if room.meters["danger"] < THRESHOLD:
        return out
    if puddle.meters["wet"] < THRESHOLD:
        return out
    if plug.meters["spark"] < THRESHOLD:
        return out
    sig = ("shock",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] += 1
    world.get("child").meters["shocked"] += 1
    out.append("__shock__")
    return out


CAUSAL_RULES = [
    Rule("wet_danger", "physical", _r_wet_danger),
    Rule("shock", "physical", _r_shock),
]


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


def risk_at_hand(risk: RiskObject, twist: TwistObject) -> bool:
    return risk.makes_flame and twist.safe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid, risk in RISKS.items():
            for tid, twist in TWISTS.items():
                if risk_at_hand(risk, twist):
                    combos.append((sid, rid, tid))
    return combos


def reasonableness_check(risk: RiskObject, twist: TwistObject) -> bool:
    return risk_at_hand(risk, twist)


def predict_danger(world: World, risk_id: str) -> dict:
    sim = world.copy()
    _do_twist(sim, sim.get(risk_id), narrate=False)
    return {
        "shocked": sim.get("child").meters["shocked"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def _do_twist(world: World, risk: Entity, narrate: bool = True) -> None:
    risk.meters["spark"] += 1
    risk.meters["wet"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, by the lamp's soft gleam, "
        f"{child.id} and {helper.id} spun a rhyming dream."
    )
    world.say(
        f"{child.id} tapped a beat and grinned so bright, "
        f"for twists and rhymes felt just right tonight."
    )


def set_scene(world: World, setting: Setting, twist: TwistObject) -> None:
    world.say(
        f"The room was snug, but one spot looked dim, "
        f"and {twist.label} waited with a shiny trim."
    )


def warn(world: World, helper: Entity, child: Entity, risk: RiskObject, setting: Setting) -> None:
    pred = predict_danger(world, "risk")
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"Wait," said {helper.id}, "that spark is not wise. '
        f'Wet things and plugs can bring a big surprise."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(
            f'"If {risk.label} shines near water, a shock could leap. '
            f'Let us choose a safer light to keep."'
        )


def defy(world: World, child: Entity, risk: RiskObject) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Oh, just one try," said {child.id} with a grin, '
        f'and {child.id} reached in to begin.'
    )
    world.say(
        f"{child.id} twirled the cord in a reckless whirl, "
        f"then touched the plug with a daring curl."
    )


def shock(world: World, child: Entity, risk: RiskObject) -> None:
    _do_twist(world, world.get("risk"), narrate=True)
    world.say(
        f"{risk.label.capitalize()} flashed near the puddle's glimmering crest, "
        f"and a hot little jolt gave everyone no rest."
    )


def alarm(world: World, helper: Entity, child: Entity) -> None:
    world.say(f'"{{child}}!" cried {helper.id}, "Back away, please!"')
    world.say(f'"Call for help!" {helper.id} said with a breeze."')


def rescue(world: World, adult: Entity, response: Response, risk: RiskObject) -> None:
    world.get("plug").meters["spark"] = 0
    world.get("puddle").meters["wet"] = 0
    world.get("room").meters["danger"] = 0
    body = response.text.replace("{target}", risk.label)
    world.say(
        f"Then {adult.id} hurried in quick, "
        f"and {adult.pronoun()} {body}."
    )
    world.say(
        f"The jolt was gone, the room felt light, "
        f"and the stormy hum went soft that night."
    )


def lesson(world: World, adult: Entity, child: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{adult.label_word.capitalize()} knelt right down and hugged them tight, "
        f'"A spark is not a toy for fun tonight."'
    )
    world.say(
        f'"Electrocute can hurt," {adult.id} said, "so please remember: '
        f'never mix a wet place with a plug or ember."'
    )
    world.say(
        f"{child.id} nodded slow and held {child.pronoun('possessive')} breath, "
        f"glad the scare had stayed away from death."
    )


def safe_twist(world: World, adult: Entity, child: Entity, setting: Setting, safe: TwistObject) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then {adult.id} brought out a battery glow, "
        f"{safe.label} that shone soft, steady, and low."
    )
    world.say(
        f'"Now twist away," {adult.id} said with cheer, '
        f'"with safe light bright, no spark need fear."'
    )
    world.say(
        f"{child.id} laughed and spun the rhyme once more, "
        f"safe as a moonbeam by the door."
    )


def tell(setting: Setting, risk: RiskObject, twist: TwistObject, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="plug", type="plug", label="the plug"))
    world.add(Entity(id="puddle", type="puddle", label="the puddle"))
    world.add(Entity(id="risk", type="risk", label=risk.label))
    world.add(Entity(id="twist", type="twist", label=twist.label))

    # initialize facts before any simulation rules read them
    world.get("plug").meters["spark"] = 0
    world.get("puddle").meters["wet"] = 1
    world.get("risk").meters["spark"] = 0
    world.get("risk").meters["wet"] = 0
    world.get("room").meters["danger"] = 0
    world.facts["setting"] = setting
    world.facts["risk"] = risk
    world.facts["twist"] = twist
    world.facts["response"] = response

    introduce(world, child, helper, setting)
    set_scene(world, setting, twist)
    world.para()
    warn(world, helper, child, risk, setting)
    defy(world, child, risk)
    world.para()
    shock(world, child, risk)
    alarm(world, helper, child)
    world.para()
    rescue(world, adult, response, risk)
    lesson(world, adult, child)
    world.para()
    safe_twist(world, adult, child, setting, twist)
    world.facts["outcome"] = "rescued"
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["adult"] = adult
    return world


SETTINGS = {
    "nightroom": Setting(
        id="nightroom",
        place="the night room",
        mood="soft and dim",
        rhyme="glow and snow",
        tags={"room", "night"},
    ),
    "workshop": Setting(
        id="workshop",
        place="the little workshop",
        mood="busy and bright",
        rhyme="wood and good",
        tags={"room", "tools"},
    ),
}

RISKS = {
    "cord": RiskObject(
        id="cord",
        label="the spark cord",
        phrase="a bright spark cord",
        makes_flame=True,
        tags={"electric", "spark"},
    ),
    "lamp": RiskObject(
        id="lamp",
        label="the wall lamp",
        phrase="a wall lamp with a shiny bulb",
        makes_flame=True,
        tags={"electric", "lamp"},
    ),
}

TWISTS = {
    "turn": TwistObject(
        id="turn",
        label="a twisty dance turn",
        phrase="a twisty dance turn",
        safe=True,
        tags={"twist"},
    ),
    "rhyme": TwistObject(
        id="rhyme",
        label="a rhyme-time swirl",
        phrase="a rhyme-time swirl",
        safe=True,
        tags={"twist", "rhyme"},
    ),
}

SAFE_LIGHTS = {
    "glowtoy": TwistObject(
        id="glowtoy",
        label="a battery glow toy",
        phrase="a battery glow toy",
        safe=True,
        tags={"safe", "light"},
    ),
}

RESPONSES = {
    "cut_power": Response(
        id="cut_power",
        sense=3,
        power=4,
        text="cut the power at the box and kept the wires from the wet floor",
        fail="cut the power, but the jolt had already jumped too far",
        qa_text="cut the power at the box and kept the wires from the wet floor",
        tags={"electric", "safety"},
    ),
    "dry_floor": Response(
        id="dry_floor",
        sense=3,
        power=3,
        text="threw down towels and dried the floor before any more spark could leap",
        fail="threw down towels, but the wet spot was already too big to tame",
        qa_text="threw down towels and dried the floor before any more spark could leap",
        tags={"electric", "safety"},
    ),
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="grabbed a bucket of water and splashed it near the cord",
        fail="grabbed a bucket of water, but that made the wet spot worse",
        qa_text="grabbed a bucket of water and splashed it near the cord",
        tags={"bad"},
    ),
}

NAMES = {
    "girl": ["Mia", "Zoe", "Ava", "Nia", "Lia"],
    "boy": ["Ben", "Max", "Leo", "Noah", "Eli"],
}


@dataclass
class StoryParams:
    setting: str
    risk: str
    twist: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


def sensible_response_ids() -> list[str]:
    return [r.id for r in sensible_responses()]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the word "{f["risk"].label}" and the word "electrocute".',
        f"Tell a twist-filled bedtime story where {f['child'].id} is warned about {f['risk'].label}, then a grown-up makes it safe.",
        f'Write a gentle rhyme story about a risky spark, a warning, and a safe ending with "{f["twist"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    adult = f["adult"]
    risk = f["risk"]
    twist = f["twist"]
    resp = f["response"]
    return [
        QAItem(
            question=f"Who was the story about in {world.facts['setting'].place}?",
            answer=f"It was about {child.id}, with {helper.id} and {adult.id} helping in {world.facts['setting'].place}. The whole scene turned on a risky spark and a careful rescue.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id} about {risk.label}?",
            answer=f"{helper.id} could see that {risk.label} and the wet floor made a dangerous mix. A spark near water can lead to electrocute, so the warning came before the trouble grew.",
        ),
        QAItem(
            question=f"What happened after {child.id} reached for {risk.label}?",
            answer=f"The spark jumped, the room got dangerous, and the grown-up rushed in. The choice made the twist turn from playful to serious for a moment.",
        ),
        QAItem(
            question=f"How did {adult.id} fix the danger?",
            answer=f"{adult.id} used {resp.qa_text}. That stopped the danger and made the room safe again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The family swapped the risky spark for safe light and kept the rhyme going. By the end, the mood was bright, calm, and playful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["risk"].tags) | set(world.facts["twist"].tags) | {"electric"}
    out: list[QAItem] = []
    if "electric" in tags:
        out.append(QAItem(
            question="What does electricity do?",
            answer="Electricity can power lights and other devices. It must be treated carefully because a shock can hurt people.",
        ))
    if "twist" in tags:
        out.append(QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you expect. It makes the story feel new and exciting.",
        ))
    out.append(QAItem(
        question="What is a safe way to light a room when there is water nearby?",
        answer="A battery light is a safe choice because it gives light without a spark. That keeps the room bright and the people safe.",
    ))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(risk: RiskObject, twist: TwistObject) -> str:
    if not risk.makes_flame:
        return "(No story: the risk object does not create a spark, so there is no danger to twist around.)"
    return "(No story: this combination is not reasonable for the tiny storyworld.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.risk is None or c[1] == args.risk)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, risk, twist = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES[child_gender])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(NAMES[helper_gender])
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult_name = args.adult_name or ("Mom" if adult_gender == "mother" else "Dad")
    return StoryParams(
        setting=setting,
        risk=risk,
        twist=twist,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.risk not in RISKS or params.twist not in TWISTS:
        raise StoryError("Invalid params for this storyworld.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        SETTINGS[params.setting],
        RISKS[params.risk],
        TWISTS[params.twist],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
    )
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


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld with a twist and an electrical scare.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


CURATED = [
    StoryParams(
        setting="nightroom",
        risk="cord",
        twist="rhyme",
        response="cut_power",
        child_name="Mia",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        adult_name="Mom",
        adult_gender="mother",
    ),
    StoryParams(
        setting="workshop",
        risk="lamp",
        twist="turn",
        response="dry_floor",
        child_name="Leo",
        child_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        adult_name="Dad",
        adult_gender="father",
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.makes_flame:
            lines.append(asp.fact("makes_flame", rid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(R, T) :- makes_flame(R), twist(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,R,T) :- setting(S), risk(R), twist(T), hazard(R,T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
    cs, ps = set(asp_sensible()), {r.id for r in sensible_responses()}
    if cs == ps:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, r, t in asp_valid_combos():
            print(f"  {s:10} {r:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
