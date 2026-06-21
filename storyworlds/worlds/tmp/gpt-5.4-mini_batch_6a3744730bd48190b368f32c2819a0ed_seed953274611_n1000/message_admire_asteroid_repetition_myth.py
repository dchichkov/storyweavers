#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/message_admire_asteroid_repetition_myth.py
==========================================================================

A standalone story world in a small mythic domain.

Premise:
- A messenger carries a message to an elder who admires a falling asteroid.
- A recurring, chant-like repetition marks the turning point.
- The asteroid threatens a shrine or valley, and the characters respond with
  mythic calm, practical help, and a new custom.

The world is intentionally tiny and classical: typed entities, physical meters,
emotional memes, forward-chained state updates, grounded QA, and an inline ASP
twin for the simple reasonableness gate.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    carries_message: bool = False
    is_asteroid: bool = False
    is_shrine: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    sky: str
    ground: str
    shrine_name: str
    chant: str
    ending_image: str


@dataclass
class Messenger:
    id: str
    type: str
    opening: str
    phrase: str
    deliver: str
    repeat_line: str
    traits: set[str] = field(default_factory=set)


@dataclass
class Celestial:
    id: str
    label: str
    appearance: str
    speed: int
    heat: int
    glow: str
    admire_line: str
    tags: set[str] = field(default_factory=set)
    is_asteroid: bool = True


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_asteroid_heat(world: World) -> list[str]:
    out: list[str] = []
    astro = world.get("asteroid")
    if astro.meters["close"] < THRESHOLD:
        return out
    sig = ("heat", astro.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("valley").meters["alarm"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["wonder"] += 1
    out.append("__heat__")
    return out


def _r_message_repeated(world: World) -> list[str]:
    out: list[str] = []
    herald = world.get("herald")
    if herald.meters["spoken"] < 2 or herald.meters["message_delivered"] < THRESHOLD:
        return out
    sig = ("repeat", herald.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sage").memes["resolve"] += 1
    out.append("__repeat__")
    return out


CAUSAL_RULES = [
    Rule("asteroid_heat", "physical", _r_asteroid_heat),
    Rule("message_repeated", "social", _r_message_repeated),
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


def hazard_at_risk(message: Messenger, asteroid: Celestial, realm: Realm) -> bool:
    return message.id in MESSAGES and asteroid.id in ASTEROIDS and realm.id in REALMS


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid in REALMS:
        for mid in MESSAGES:
            for aid in ASTEROIDS:
                if hazard_at_risk(MESSAGES[mid], ASTEROIDS[aid], REALMS[rid]):
                    combos.append((rid, mid, aid))
    return combos


def _do_message(world: World, herald: Entity, message: Messenger) -> None:
    herald.meters["spoken"] += 1
    herald.meters["message_delivered"] += 1
    herald.carries_message = True
    herald.memes["duty"] += 1


def _do_asteroid(world: World, asteroid: Entity) -> None:
    asteroid.meters["close"] += 1
    asteroid.meters["glow"] += 1
    propagate(world, narrate=False)


def predict(world: World, realm: Realm, response: Response, delay: int) -> dict:
    sim = world.copy()
    sim.get("asteroid").meters["close"] += 1
    _do_message(sim, sim.get("herald"), MESSAGES[sim.facts["message_id"]])
    return {
        "alarm": sim.get("valley").meters["alarm"],
        "repeat": sim.get("sage").memes["resolve"],
    }


def opening(world: World, realm: Realm, herald: Entity, sage: Entity, message: Messenger, asteroid: Celestial) -> None:
    world.say(
        f"In {realm.id}, under {realm.sky}, {herald.id} carried a message as old as dawn. "
        f"{sage.id} paused to admire the {asteroid.label} overhead, and the whole valley listened."
    )
    world.say(
        f'"{message.opening}" {herald.id} said. "{message.phrase}" '
        f'{sage.id} answered, and the words were repeated like a drumbeat: '
        f'"{message.repeat_line}" "{message.repeat_line}"'
    )


def turn(world: World, realm: Realm, herald: Entity, sage: Entity, asteroid: Celestial, message: Messenger) -> None:
    world.para()
    world.say(
        f"But the {asteroid.label} came lower and lower, bright as a king's coin. "
        f"{sage.id} still admired it, but {herald.id} felt the ground tremble."
    )
    world.say(
        f'"{message.deliver}" {herald.id} cried. {realm.chant} '
        f'The message had to be spoken once, and then again, and then again, '
        f"for the old fear to leave the people."
    )
    _do_asteroid(world, world.get("asteroid"))
    world.say(
        f"The shrine bells shivered. Even so, the repeated message held the village together."
    )


def resolve(world: World, realm: Realm, sage: Entity, response: Response, asteroid: Celestial) -> None:
    world.para()
    astro = world.get("asteroid")
    if response.power >= asteroid.heat + 1:
        astro.meters["fallen"] += 1
        world.get("valley").meters["alarm"] = 0
        sage.memes["admire"] += 1
        world.say(
            f"{sage.id} did not stop admiring the sky, but {sage.pronoun()} chose a wiser path. "
            f"{response.text.replace('{asteroid}', asteroid.label)}."
        )
        world.say(
            f"The {asteroid.label} became a bright story in the dust, and the shrine stood quiet again."
        )
        world.say(f"{realm.ending_image}")
    else:
        world.get("valley").meters["alarm"] += 1
        astro.meters["fallen"] += 1
        world.say(
            f"{sage.id} called for help, but {response.fail.replace('{asteroid}', asteroid.label)}."
        )
        world.say(
            f"The people fled to the hills, and only the repeated message remained in their ears."
        )
        world.say("By dawn, the valley was changed forever, and the shrine had become a memory.")
    

def tell(realm: Realm, message: Messenger, asteroid: Celestial, response: Response,
         hero_name: str = "Ari", hero_type: str = "boy",
         sage_name: str = "Mira", sage_type: str = "girl",
         delay: int = 0) -> World:
    world = World()
    herald = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="herald"))
    sage = world.add(Entity(id=sage_name, kind="character", type=sage_type, role="sage"))
    valley = world.add(Entity(id="valley", kind="place", type="place", label=realm.ground))
    ast = world.add(Entity(id="asteroid", kind="thing", type="thing", label=asteroid.label, is_asteroid=True))
    world.facts.update(message_id=message.id, realm_id=realm.id, delay=delay)
    opening(world, realm, herald, sage, message, asteroid)
    turn(world, realm, herald, sage, asteroid, message)
    resolve(world, realm, sage, response, asteroid)
    world.facts.update(
        herald=herald, sage=sage, valley=valley, asteroid=ast, realm=realm,
        message=message, response=response, outcome="burned" if response.power < asteroid.heat + 1 else "contained",
        repeated=herald.meters["spoken"] >= 2
    )
    return world


REALMS = {
    "mythic_valley": Realm(
        id="mythic_valley",
        sky="the elder sky",
        ground="the green valley",
        shrine_name="the shrine of stones",
        chant="The old law was simple: speak the truth, speak it again, speak it once more.",
        ending_image="At the end, the shrine lanterns burned steady, and the valley kept the message like a seed.",
    ),
    "river_hall": Realm(
        id="river_hall",
        sky="the river moon",
        ground="the river hall",
        shrine_name="the hall of reeds",
        chant="So they said it twice, and twice again, and the river remembered.",
        ending_image="At the end, the reeds stood upright, and the message floated on the water like gold.",
    ),
    "stone_court": Realm(
        id="stone_court",
        sky="the stone dawn",
        ground="the old court",
        shrine_name="the court of oaths",
        chant="As in the old tales, a message grows stronger when it is carried with patience.",
        ending_image="At the end, the court was calm, and the people spoke the message as one voice.",
    ),
}

MESSAGES = {
    "warning": Messenger(
        id="warning",
        type="message",
        opening="Hear me, old ones",
        phrase="An asteroid will cross the moon-path tonight",
        deliver="The message must be heard before the bell falls",
        repeat_line="The message is true",
        traits={"urgent", "repeated"},
    ),
    "omen": Messenger(
        id="omen",
        type="message",
        opening="Adore the sky, but listen",
        phrase="A bright asteroid has been named in the water",
        deliver="Let the message be spoken again so no one is left behind",
        repeat_line="We remember the message",
        traits={"repeated", "gentle"},
    ),
    "vow": Messenger(
        id="vow",
        type="message",
        opening="Keep the oath",
        phrase="A message must be carried to the shrine before dawn",
        deliver="Carry the message once, then carry it again, and again",
        repeat_line="The message endures",
        traits={"repeated", "solemn"},
    ),
}

ASTEROIDS = {
    "red_comet": Celestial(
        id="red_comet",
        label="red asteroid",
        appearance="bright red with a silver tail",
        speed=2,
        heat=1,
        glow="like a torch in the sky",
        admire_line="Mira loved to admire the red asteroid because it looked like a royal flame.",
        tags={"asteroid", "sky"},
    ),
    "gold_shard": Celestial(
        id="gold_shard",
        label="gold asteroid",
        appearance="small and gold, with a ringing light",
        speed=1,
        heat=2,
        glow="like a gold bead on black cloth",
        admire_line="The elder admired the gold asteroid and said it looked like a star's first gift.",
        tags={"asteroid", "sky"},
    ),
    "stone_star": Celestial(
        id="stone_star",
        label="stone asteroid",
        appearance="gray and hard, with a cold shine",
        speed=2,
        heat=2,
        glow="like a knife made of moonlight",
        admire_line="Some admired the stone asteroid for its stern and silent beauty.",
        tags={"asteroid", "sky"},
    ),
}

RESPONSES = {
    "ritual": Response(
        id="ritual",
        sense=3,
        power=4,
        text="chanted over it until the dark fear broke and the valley knew what to do",
        fail="chanted, but the stone fell too fast for any ritual to help",
        qa_text="chanted over the falling asteroid until the people remembered how to act",
        tags={"chant", "help"},
    ),
    "net": Response(
        id="net",
        sense=3,
        power=3,
        text="threw a woven net across the path and slowed the burning sky-stone",
        fail="threw a woven net, but the asteroid tore straight through it",
        qa_text="threw a woven net across the asteroid's path and slowed it down",
        tags={"tool", "help"},
    ),
    "bells": Response(
        id="bells",
        sense=2,
        power=2,
        text="rang the shrine bells so hard that everyone ran for the hill path",
        fail="rang the bells, but the warning came too late",
        qa_text="rang the shrine bells to warn the valley people",
        tags={"warning", "help"},
    ),
    "wave": Response(
        id="wave",
        sense=1,
        power=1,
        text="waved at the sky and hoped the asteroid would turn aside",
        fail="waved at the sky, but the asteroid kept falling",
        qa_text="waved at the sky",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mira", "Sera", "Lina", "Iris", "Nia", "Tala"]
BOY_NAMES = ["Ari", "Orin", "Kian", "Eli", "Ryo", "Daro"]
TRAITS = ["patient", "bold", "gentle", "careful", "solemn"]


@dataclass
class StoryParams:
    realm: str
    message: str
    asteroid: str
    response: str
    hero_name: str
    hero_type: str
    sage_name: str
    sage_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def explain_rejection(message: Messenger, asteroid: Celestial) -> str:
    return f"(No story: the message and the asteroid must belong to the same mythic sky.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak for this mythic danger. Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a message, an admired asteroid, and a repeated warning."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--asteroid", choices=ASTEROIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--sage")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.message is None or c[1] == args.message)
              and (args.asteroid is None or c[2] == args.asteroid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, message, asteroid = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_type = rng.choice(["girl", "boy"])
    sage_type = "girl" if hero_type == "boy" else "boy"
    hero_name = args.name or _pick_name(rng, hero_type)
    sage_name = args.sage or _pick_name(rng, sage_type, avoid=hero_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        realm=realm,
        message=message,
        asteroid=asteroid,
        response=response,
        hero_name=hero_name,
        hero_type=hero_type,
        sage_name=sage_name,
        sage_type=sage_type,
        trait=trait,
        delay=args.delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    realm = f["realm"]
    msg = f["message"]
    ast = f["asteroid"]
    return [
        f'Write a mythic story for a young child that includes the words "message", "admire", and "asteroid".',
        f"Tell a story where {f['sage'].id} admires the {ast.label} while {f['hero'].id} carries a {msg.id} from {realm.shrine_name}, and the message must be repeated.",
        f"Write a gentle myth where a {msg.id} is spoken again and again before the {ast.label} comes near the valley.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sage = f["sage"]
    realm = f["realm"]
    msg = f["message"]
    ast = f["asteroid"]
    resp = f["response"]
    qa = [
        ("Who carried the message?", f"{hero.id} carried the message while {sage.id} listened and watched the sky."),
        ("What did the elder admire?", f"{sage.id} admired the {ast.label} because it shone so brightly over the valley."),
        ("Why was the message repeated?", f"It was repeated because the old mythic law said a warning grows stronger when it is spoken more than once. Repetition helped the people remember what to do before the asteroid came close."),
    ]
    if f.get("outcome") == "contained":
        qa.append((
            "How did the people respond to the falling asteroid?",
            f"They used {resp.qa_text}. The repeated message kept everyone calm, so the valley could act together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the shrine quiet and the valley still standing. The ending image proves that the message was heard and the danger was met."
        ))
    else:
        qa.append((
            "What happened when the response was not enough?",
            f"The people warned each other, but the {ast.label} still fell too fast. They escaped, yet the valley changed and the shrine became a memory."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["message"].traits) | set(f["asteroid"].tags) | set(f["response"].tags)
    out = []
    if "repeated" in tags:
        out.append(("Why do people repeat a message in a myth?", "Repeating a message makes it easier to remember, and in a story it can feel powerful and important. The repeated words can also sound like a chant or warning."))
    if "asteroid" in tags:
        out.append(("What is an asteroid?", "An asteroid is a small rocky body that travels through space. In stories, it can look like a bright star or a falling stone in the sky."))
    if "warning" in tags or "help" in tags:
        out.append(("What should people do when they hear a warning?", "They should listen carefully and get ready to act. A warning is useful when people take it seriously and move together."))
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
        if e.carries_message:
            bits.append("carries_message=True")
        if e.is_asteroid:
            bits.append("asteroid=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(Rm, Msg, Ast) :- realm(Rm), message(Msg), asteroid(Ast).
outcome(contained) :- chosen_response(R), power(R,P), chosen_asteroid(A), heat(A,H), P >= H + 1.
outcome(burned) :- chosen_response(R), power(R,P), chosen_asteroid(A), heat(A,H), P < H + 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for mid, m in MESSAGES.items():
        lines.append(asp.fact("message", mid))
        if "repeated" in m.traits:
            lines.append(asp.fact("repeated", mid))
    for aid, a in ASTEROIDS.items():
        lines.append(asp.fact("asteroid", aid))
        lines.append(asp.fact("heat", aid, a.heat))
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


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_asteroid", params.asteroid),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    samples = [CURATED[0]]
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    cases = [CURATED[0]]
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: outcome model matches python.")
    else:
        rc = 1
        print("MISMATCH in outcome model.")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "contained" if RESPONSES[params.response].power >= ASTEROIDS[params.asteroid].heat + 1 else "burned"


def tell_story(params: StoryParams) -> World:
    realm = REALMS[params.realm]
    message = MESSAGES[params.message]
    asteroid = ASTEROIDS[params.asteroid]
    response = RESPONSES[params.response]
    return tell(realm, message, asteroid, response, params.hero_name, params.hero_type, params.sage_name, params.sage_type, params.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(realm="mythic_valley", message="warning", asteroid="red_comet", response="ritual", hero_name="Ari", hero_type="boy", sage_name="Mira", sage_type="girl", trait="patient", delay=0),
    StoryParams(realm="river_hall", message="omen", asteroid="gold_shard", response="net", hero_name="Lina", hero_type="girl", sage_name="Orin", sage_type="boy", trait="gentle", delay=0),
    StoryParams(realm="stone_court", message="vow", asteroid="stone_star", response="bells", hero_name="Kian", hero_type="boy", sage_name="Sera", sage_type="girl", trait="solemn", delay=0),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic message/admire/asteroid story world with repetition.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--asteroid", choices=ASTEROIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--sage")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.message is None or c[1] == args.message)
              and (args.asteroid is None or c[2] == args.asteroid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, message, asteroid = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_type = rng.choice(["girl", "boy"])
    sage_type = "girl" if hero_type == "boy" else "boy"
    return StoryParams(
        realm=realm,
        message=message,
        asteroid=asteroid,
        response=response,
        hero_name=args.name or _pick_name(rng, hero_type),
        hero_type=hero_type,
        sage_name=args.sage or _pick_name(rng, sage_type, avoid=args.name or ""),
        sage_type=sage_type,
        trait=rng.choice(TRAITS),
        delay=args.delay,
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for realm, message, asteroid in asp_valid_combos():
            print(f"  {realm:14} {message:8} {asteroid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.realm}: {p.message} / {p.asteroid} / {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
