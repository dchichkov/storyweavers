#!/usr/bin/env python3
"""
storyworlds/worlds/pantry_walrus_cautionary_quest_pirate_tale.py
=================================================================

A standalone storyworld for a tiny Pirate Tale style domain.

Premise:
- Two children turn a pantry into a pirate quest.
- A walrus is part of the quest setup, but the cautionary tension is that
  a careless use of a pantry lantern can start a kitchen hazard.
- A wiser helper warns them, the risky choice is avoided or corrected, and the
  ending proves what changed: the pantry stays safe, the quest continues with a
  proper map, and the walrus is found in a harmless, child-facing way.

The world is small on purpose: one clear premise, one caution, one turn, and one
ending image. Physical meters and emotional memes drive the prose.
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


@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    quest_frame: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    trigger: str
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    near: str
    flammable: bool = True
    spread: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
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


@dataclass
class StoryParams:
    place: str
    hazard: str
    target: str
    safe_light: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "pantry": Place(
        id="pantry",
        label="the pantry",
        dark_spot="the back of the pantry",
        quest_frame="a pirate quest through the pantry",
        tags={"pantry", "quest"},
    ),
}

HAZARDS = {
    "lantern": Hazard(
        id="lantern",
        label="a little lantern",
        trigger="lantern flame",
        tags={"lantern", "fire"},
    ),
    "candle": Hazard(
        id="candle",
        label="a candle",
        trigger="candle flame",
        tags={"candle", "fire"},
    ),
}

TARGETS = {
    "paper_map": Target(
        id="paper_map",
        label="the paper map",
        near="the paper map",
        spread=2,
        tags={"paper", "map"},
    ),
    "towel_stack": Target(
        id="towel_stack",
        label="the towel stack",
        near="the towel stack",
        spread=3,
        tags={"towel"},
    ),
    "cardboard_box": Target(
        id="cardboard_box",
        label="the cardboard box",
        near="the cardboard box",
        spread=2,
        tags={"cardboard", "box"},
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on bright and safe",
        tags={"flashlight"},
    ),
    "glowstick": SafeLight(
        id="glowstick",
        label="glow stick",
        phrase="a glow stick",
        glow="shone green and calm",
        tags={"glowstick"},
    ),
}

RESPONSES = {
    "smother": Response(
        id="smother",
        sense=3,
        power=3,
        text="snatched the lantern away and smothered the little flame under a heavy baking tray",
        fail="tried to smother the flame, but it had already licked too far up the paper",
        qa_text="snatched the lantern away and smothered the little flame under a heavy baking tray",
        tags={"smother", "fire"},
    ),
    "blanket": Response(
        id="blanket",
        sense=3,
        power=2,
        text="pulled a thick blanket over the flames and pressed them flat",
        fail="threw a blanket over it, but the fire was already too big",
        qa_text="pulled a thick blanket over the flames and pressed them flat",
        tags={"blanket", "fire"},
    ),
    "water_pitcher": Response(
        id="water_pitcher",
        sense=1,
        power=1,
        text="grabbed a water pitcher and splashed it over the fire",
        fail="splashed a little water, but the fire kept climbing",
        qa_text="grabbed a water pitcher and splashed it over the fire",
        tags={"water", "fire"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Max", "Sam"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "curious", "clever", "cautious", "brave"]


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "pantry" in world.entities:
            world.get("pantry").meters["danger"] += 1
        for kid in world.entities.values():
            if kid.role in {"hero", "mate"}:
                kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for hz_id, hz in HAZARDS.items():
            for tg_id, tg in TARGETS.items():
                if hz.makes_flame and tg.flammable:
                    combos.append((place_id, hz_id, tg_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(hz: Hazard, tg: Target) -> bool:
    return hz.makes_flame and tg.flammable


def fire_severity(tg: Target) -> int:
    return tg.spread


def is_contained(resp: Response, tg: Target) -> bool:
    return resp.power >= fire_severity(tg)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {"ignites": sim.get(target_id).meters["burning"] >= THRESHOLD, "danger": sim.get("pantry").meters["danger"]}


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, mate: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {mate.id} turned {place.label} into "
        f"{place.quest_frame}."
    )
    world.say(
        f"They looked for treasure in {place.dark_spot}, and the pantry shelves felt like tall pirate cliffs."
    )


def need_light(world: World, mate: Entity, place: Place, tg: Target) -> None:
    world.say(f'"The back of the pantry is too dark," {mate.id} whispered.')
    world.say(f'"We need a light to follow the quest map past {tg.near}."')


def tempt(world: World, hero: Entity, hz: Hazard) -> None:
    hero.memes["bravado"] += 1
    world.say(f'{hero.id} grinned. "{hz.label.capitalize()}! That will make the quest feel real."')


def warn(world: World, helper: Entity, hero: Entity, hz: Hazard, tg: Target) -> None:
    pred = predict_fire(world, "target")
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{helper.id} bit {helper.pronoun("possessive")} lip. "{hero.id}, we '
        f"should not touch {hz.label}. It could make a real flame near {tg.label}, "
        f"and the pantry could get dangerous fast."'
    )


def defy(world: World, hero: Entity, hz: Hazard) -> None:
    hero.memes["defiance"] += 1
    world.say(f'"Come on," {hero.id} said, and reached for {hz.label} anyway.')


def fire_alarm(world: World, mate: Entity, hero: Entity, tg: Target) -> None:
    world.say(f'"{hero.id}! Fire! {tg.label}!" {mate.id} shouted.')


def ignite(world: World, target_ent: Entity, hz: Hazard, tg: Target) -> None:
    _do_forbidden(world, target_ent)
    world.say(
        f"{hz.label.capitalize()} glimmered for one quick second, like a pirate star. "
        f"Then the flame kissed {tg.near}, and orange climbed the edge of the paper."
    )


def rescue(world: World, helper: Entity, response: Response, target_ent: Entity, tg: Target) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("pantry").meters["danger"] = 0.0
    world.say(f"{helper.id} came running and {response.text}.")
    world.say(f"The flame hissed out, leaving a smoky smell and two shaky little pirates.")


def lesson(world: World, helper: Entity, hero: Entity, mate: Entity, hz: Hazard) -> None:
    hero.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {helper.id} knelt down. \"I'm glad you called me,\" "
        f"{helper.pronoun()} said softly. \"But {hz.label} is not a toy. "
        f"Fire can grow faster than you can run.\""
    )
    world.say(f'"We promise," whispered {hero.id} and {mate.id} together.')


def safe_ending(world: World, helper: Entity, hero: Entity, mate: Entity, sl: SafeLight) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"The next morning, {helper.id} brought {sl.phrase}. It {sl.glow}, "
        f"and the pantry shadows turned friendly at once."
    )
    world.say(
        f"{hero.id} held the map high. {mate.id} held the light. "
        f"Together they finished the quest without any fire at all."
    )
    world.say(
        f"At the back of {world.facts['place'].label}, they found a harmless walrus-shaped toy from the pantry shelf, "
        f"and they laughed because the treasure had been safe all along."
    )


def tell(place: Place, hazard: Hazard, target: Target, safe_light: SafeLight, response: Response,
         hero: str = "Lily", hero_gender: str = "girl",
         mate: str = "Tom", mate_gender: str = "boy",
         helper: str = "mother", helper_gender: str = "girl") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    m = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    p = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="pantry", kind="place", type="place", label=place.label))
    tgt = world.add(Entity(id="target", kind="target", type="target", label=target.label))
    world.facts["place"] = place
    world.facts["hazard"] = hazard
    world.facts["target_cfg"] = target
    world.facts["safe_light"] = safe_light
    world.facts["response"] = response
    world.facts["hero"] = h
    world.facts["mate"] = m
    world.facts["helper"] = p

    setup(world, h, m, place)
    world.para()
    need_light(world, m, place, target)
    tempt(world, h, hazard)
    warn(world, p, h, hazard, target)
    world.para()
    defy(world, h, hazard)
    ignite(world, tgt, hazard, target)
    fire_alarm(world, m, h, target)
    if is_contained(response, target):
        world.para()
        rescue(world, p, response, tgt, target)
        lesson(world, p, h, m, hazard)
        world.para()
        safe_ending(world, p, h, m, safe_light)
        outcome = "contained"
    else:
        world.para()
        world.say(f"{p.id} tried to help, but the fire was already too big.")
        world.say("The pirates rushed outside and watched the smoke from the yard.")
        world.say("They learned to keep flames away from the pantry shelf.")
        outcome = "burned"
    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-style cautionary quest story that uses the word "pantry" and the word "walrus".',
        f"Tell a child-sized pirate tale where {f['hero'].id} and {f['mate'].id} search {f['place'].label} for treasure, then choose safe light instead of {f['hazard'].label}.",
        f"Write a gentle cautionary story about a quest in {f['place'].label} that ends with a safe flashlight and a found walrus.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, helper = f["hero"], f["mate"], f["helper"]
    place, hz, target, sl, resp = f["place"], f["hazard"], f["target_cfg"], f["safe_light"], f["response"]
    qa = [
        QAItem(
            f"What kind of adventure did {hero.id} and {mate.id} make in {place.label}?",
            f"They made a pirate quest in {place.label}. They treated the pantry like a treasure map and hunted for a secret prize in the dark corner.",
        ),
        QAItem(
            f"Why did {helper.id} warn {hero.id} about {hz.label} near {target.label}?",
            f"{helper.id} warned {hero.id} because {hz.label} could make a real flame near {target.label}. The pantry was too small and crowded for a risky light.",
        ),
        QAItem(
            f"What did {hero.id} and {mate.id} use after the warning?",
            f"They used {sl.phrase}. That gave them enough light to keep exploring without a flame.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(QAItem(
            f"How did the grown-up stop the fire on {target.label}?",
            f"{helper.id} used the {resp.id} response and put the fire out quickly. After that, the pantry stayed safe and the quest could keep going.",
        ))
        qa.append(QAItem(
            f"What changed by the end of the story?",
            f"The dangerous flame was gone, the pantry was safe again, and the children finished their quest with a proper light. They ended with a happy pirate adventure instead of a kitchen accident.",
        ))
    else:
        qa.append(QAItem(
            f"What happened when the fire got too big?",
            f"The fire spread too fast for that response, so the pirates had to run outside. They were safe, but the pantry quest ended with smoke and worry.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hazard"].tags) | set(world.facts["target_cfg"].tags) | set(world.facts["safe_light"].tags)
    items = []
    if "pantry" in tags:
        items.append(QAItem("What is a pantry?", "A pantry is a room or cupboard where food and kitchen things are kept. It is usually small and can be crowded." ))
    if "fire" in tags:
        items.append(QAItem("Why is fire dangerous?", "Fire is very hot and can spread fast. It can burn things before people have time to stop it." ))
    if "flashlight" in tags:
        items.append(QAItem("What is a flashlight?", "A flashlight is a battery light you can turn on with a button. It makes light without a flame." ))
    if "walrus" not in tags:
        items.append(QAItem("What is a walrus?", "A walrus is a big ocean animal with whiskers and tusks. It lives in cold seas and is not a kitchen tool."))
    else:
        items.append(QAItem("What is a walrus?", "A walrus is a big ocean animal with whiskers and tusks. It lives in cold seas and is not a kitchen tool."))
    return items


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pantry", hazard="lantern", target="paper_map", safe_light="flashlight", response="smother", hero="Lily", hero_gender="girl", mate="Tom", mate_gender="boy", helper="mother", helper_gender="girl"),
    StoryParams(place="pantry", hazard="candle", target="towel_stack", safe_light="glowstick", response="blanket", hero="Mia", hero_gender="girl", mate="Finn", mate_gender="boy", helper="father", helper_gender="boy"),
]


def explain_rejection(hz: Hazard, tg: Target) -> str:
    if not hazard_at_risk(hz, tg):
        return f"(No story: {hz.label} would not meaningfully threaten {tg.label}.)"
    return "(No story: this combination is not safe enough for a cautionary quest.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak for this world's common-sense gate. Try {good}.)"


ASP_RULES = r"""
hazard(F,T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P,H,T) :- place(P), hazard(H), target(T), hazard(H,T).
contained(R,T) :- response(R), target(T), power(R,P), spread(T,S), P >= S.
outcome(contained) :- chosen_response(R), chosen_target(T), contained(R,T).
outcome(burned) :- chosen_response(R), target(T), not contained(chosen_response,R,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_flame:
            lines.append(asp.fact("makes_flame", hid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-style cautionary quest in a pantry with a walrus.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--safe-light", dest="safe_light", choices=SAFE_LIGHTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, target = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    mate = args.mate or _pick_name(rng, mate_gender, avoid=hero)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place, hazard=hazard, target=target,
        safe_light=args.safe_light or rng.choice(sorted(SAFE_LIGHTS)),
        response=args.response or rng.choice(sorted(r.id for r in sensible_responses())),
        hero=hero, hero_gender=hero_gender,
        mate=mate, mate_gender=mate_gender,
        helper=helper, helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.target not in TARGETS or params.safe_light not in SAFE_LIGHTS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = tell(
        PLACES[params.place], HAZARDS[params.hazard], TARGETS[params.target],
        SAFE_LIGHTS[params.safe_light], RESPONSES[params.response],
        hero=params.hero, hero_gender=params.hero_gender,
        mate=params.mate, mate_gender=params.mate_gender,
        helper=params.helper, helper_gender=params.helper_gender,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for combo in asp_valid_combos():
            print(combo)
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
