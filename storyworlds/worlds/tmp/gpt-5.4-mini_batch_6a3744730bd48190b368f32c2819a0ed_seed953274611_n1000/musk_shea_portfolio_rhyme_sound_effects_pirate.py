#!/usr/bin/env python3
"""
storyworlds/worlds/musk_shea_portfolio_rhyme_sound_effects_pirate.py
====================================================================

A small pirate-tale storyworld built from the seed words "musk", "shea", and
"portfolio", with rhyme and sound effects as the narrative instruments.

Premise
-------
Two deckhands are packing a paper portfolio full of sea-charts when a stolen
jar of musk gets splashed and makes the boat smell awful. One child wants to
keep using the smelly paper, the other warns that the ink will smear and the
captain will notice. The crew either fixes the mess with a sensible sailor's
move or, if the situation is pushed too far, loses the charts. The ending image
proves what changed: the portfolio is clean and safe, or it is ruined and the
crew must start over.

The story is intentionally tiny, state-driven, and child-facing. It uses:
- typed entities with physical meters and emotional memes
- a forward-chained simulation
- a reasonableness gate
- inline ASP rules as a declarative twin
- rhyme lines and sound effects in the rendered prose
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


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    risky: bool = False


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    portable: bool = True
    smelly: bool = False
    flammable: bool = False
    mutable: bool = True
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    sea = world.entities.get("sea")
    if not sea:
        return out
    for ent in list(world.entities.values()):
        if ent.meters["sticky"] < THRESHOLD:
            continue
        sig = ("smear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        sea.meters["suspicion"] += 1
        out.append("__suspicion__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.entities.values():
        if kid.role not in {"hoister", "watcher"}:
            continue
        if kid.meters["scent"] < THRESHOLD:
            continue
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("smear", "physical", _r_smear), Rule("worry", "social", _r_worry)]


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


def hazard_ok(smell: ObjectCfg, portfolio: ObjectCfg) -> bool:
    return smell.smelly and portfolio.mutable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def severity(delay: int) -> int:
    return 1 + delay


def is_saved(response: Response, delay: int) -> bool:
    return response.power >= severity(delay)


def predict_portfolio(world: World, smell_id: str, portfolio_id: str) -> dict:
    sim = world.copy()
    _trigger_spill(sim, sim.get(smell_id), sim.get(portfolio_id), narrate=False)
    return {
        "smell": sim.get(portfolio_id).meters["sticky"] >= THRESHOLD,
        "suspicion": sim.get("sea").meters["suspicion"] if "sea" in sim.entities else 0,
    }


def _trigger_spill(world: World, smell: Entity, portfolio: Entity, narrate: bool = True) -> None:
    smell.meters["spill"] += 1
    portfolio.meters["sticky"] += 1
    portfolio.meters["scent"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a brisk blue morning, {a.id} and {b.id} met on {place.label}. "
        f"They packed a chart-case and sang a tiny tune: "
        f'"A pirate needs maps, and maps need snaps!"'
    )


def gather(world: World, a: Entity, portfolio: Entity) -> None:
    world.say(
        f"{a.id} tapped the case. {portfolio.label_word.capitalize()} held sea-lines, "
        f"shell marks, and a little note for the captain."
    )


def musk_alarm(world: World, a: Entity, smell: Entity, portfolio: Entity) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"Then came a puff of smell -- {smell.label}! Phew, whew, vroom! "
        f"The whole deck wrinkled its nose."
    )
    world.say(
        f'"{smell.label_word if hasattr(smell, "label_word") else smell.label} can cling," '
        f'{a.id} sang. "If it slips on the charts, the portfolio may go wrong."'
    )


def warn(world: World, b: Entity, a: Entity, smell: ObjectCfg, portfolio: ObjectCfg, parent: Entity) -> None:
    pred = predict_portfolio(world, "musk", "portfolio")
    b.memes["caution"] += 1
    line = (
        f'"Careful now," {b.id} said. "That {smell.label} is no toy for a chart-case. '
        f'{parent.label_word.capitalize()} will spot the smear if the paper goes sticky."'
    )
    if pred["smell"]:
        line += " Sniff, sniff -- the trouble was easy to foresee."
    world.say(line)


def defy(world: World, a: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(f'"No fear," {a.id} cried. "A captain loves bold hands and daring eyes!"')


def act_spill(world: World, smell: Entity, portfolio: Entity) -> None:
    _trigger_spill(world, smell, portfolio)
    world.say(
        f"Splish! Splotch! The jar tipped, the musk went flying, and the portfolio "
        f"picked up a sticky scent."
    )


def call_help(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"Oh no!" {b.id} shouted. "{parent.id}!"')


def rescue(world: World, parent: Entity, response: Response, portfolio: Entity) -> None:
    portfolio.meters["sticky"] = 0.0
    portfolio.meters["scent"] = 0.0
    body = response.text.replace("{target}", portfolio.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say("Whoosh! The smell blew away, and the charts stayed straight.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, smell: ObjectCfg) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'"A pirate may sing in rhyme," {parent.label_word.capitalize()} said, '
        f'"but a pirate still keeps the charts clean. {smell.label} is for a pouch, '
        f"not a page."'
    )
    world.say('"Aye, aye," they whispered, nodding fast.')


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, safe: ObjectCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} brought a lidded tin for "
        f"{safe.phrase} and a fresh sleeve for the charts."
    )
    world.say(
        f"{a.id} tucked the portfolio away with a grin. The deck went back to bright "
        f"and neat, and the pirates marched on with a rhyme: "
        f'"Charts in hand, we sail the land!"'
    )


def rescue_fail(world: World, parent: Entity, response: Response, portfolio: Entity) -> None:
    portfolio.meters["sticky"] += 1
    portfolio.meters["scent"] += 1
    if "sea" in world.entities:
        world.get("sea").meters["suspicion"] += 1
    body = response.fail.replace("{target}", portfolio.label)
    world.say(f"{parent.label_word.capitalize()} came running, but {body}.")
    world.say("Ka-flop! The charts bent, and the ink made ugly little waves.")


def loss(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"The captain had to start over. The old portfolio was too messy to trust, "
        f"so the crew made a new one, and the night air smelled much less sweet."
    )


def tell(
    place: Place,
    smell: ObjectCfg,
    portfolio: ObjectCfg,
    response: Response,
    hero_name: str = "Mira",
    watcher_name: str = "Shea",
    parent_name: str = "Captain",
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(id=hero_name, kind="character", type="girl", role="hoister"))
    b = world.add(Entity(id=watcher_name, kind="character", type="girl", role="watcher"))
    parent = world.add(Entity(id=parent_name, kind="character", type="man", label="the captain"))
    sea = world.add(Entity(id="sea", kind="place", type="place", label="the deck"))
    musk = world.add(Entity(id="musk", type="jar", label=smell.label))
    port = world.add(Entity(id="portfolio", type="case", label=portfolio.label))
    world.facts["delay"] = delay
    setup(world, a, b, place)
    world.para()
    gather(world, a, port)
    musk_alarm(world, a, musk, port)
    warn(world, b, a, smell, portfolio, parent)

    if delay < 0:
        raise StoryError("delay must be zero or positive")

    if delay == 0 and b.memes["caution"] >= 0:
        # still a proper story; the warning can avert the spill when the reader asks.
        pass

    # No-avert branch: the jar slips anyway; the outcome depends on the response.
    world.para()
    defy(world, a)
    act_spill(world, musk, port)
    call_help(world, b, parent)
    contained = is_saved(response, delay)
    if contained:
        world.para()
        rescue(world, parent, response, port)
        lesson(world, parent, a, b, smell)
        world.para()
        safe_finish(world, parent, a, b, smell)
    else:
        world.para()
        rescue_fail(world, parent, response, port)
        loss(world, parent, a, b)

    outcome = "contained" if contained else "lost"
    world.facts.update(
        hero=a,
        watcher=b,
        parent=parent,
        place=place,
        smell=smell,
        portfolio=port,
        response=response,
        outcome=outcome,
        contained=contained,
        delay=delay,
    )
    return world


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", dark=False, risky=True),
    "dock": Place(id="dock", label="the dock", dark=False, risky=True),
    "ship": Place(id="ship", label="the ship deck", dark=False, risky=True),
}

OBJECTS = {
    "musk": ObjectCfg(
        id="musk",
        label="musk",
        phrase="the jar of musk",
        smelly=True,
        tags={"musk", "smell"},
    ),
    "shea": ObjectCfg(
        id="shea",
        label="shea balm",
        phrase="the shea balm",
        smelly=True,
        tags={"shea", "smell"},
    ),
    "portfolio": ObjectCfg(
        id="portfolio",
        label="portfolio",
        phrase="the paper portfolio",
        mutable=True,
        tags={"portfolio", "paper"},
    ),
}

RESPONSES = {
    "tin": Response(
        id="tin",
        sense=3,
        power=2,
        text="sealed the jar in a tin and wiped the pages clean with a dry cloth",
        fail="sealed the jar, but the pages were already too sticky",
        qa_text="sealed the jar in a tin and wiped the pages clean",
        tags={"clean"},
    ),
    "cloth": Response(
        id="cloth",
        sense=2,
        power=1,
        text="draped a dry cloth over the portfolio and pressed the pages flat",
        fail="pressed with a cloth, but the smell still soaked through",
        qa_text="draped a dry cloth over the portfolio and pressed the pages flat",
        tags={"cloth"},
    ),
    "sink": Response(
        id="sink",
        sense=1,
        power=1,
        text="ran for water and splashed at the pages",
        fail="ran for water, but it only made the paper curl worse",
        qa_text="ran for water and splashed at the pages",
        tags={"weak"},
    ),
}

RHYMES = {
    "setup": "A map in a pack can help a ship tack.",
    "warn": "If paper gets slick, the charts lose their trick.",
    "fix": "A tidy deck gleams when a pirate team dreams.",
}

SFX = {
    "smell": "PHEW!",
    "spill": "SPLASH!",
    "help": "AHOY!",
    "fix": "WHOOF!",
}

GIRL_NAMES = ["Mira", "Shea", "Nina", "Luna", "Tessa", "Coral"]
BOY_NAMES = ["Finn", "Otis", "Pip", "Rook", "Jett"]
TRAITS = ["careful", "bold", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for oid, obj in OBJECTS.items():
            for rid, resp in RESPONSES.items():
                if hazard_ok(obj, OBJECTS["portfolio"]) and resp.sense >= SENSE_MIN:
                    combos.append((place, oid, rid))
    return combos


@dataclass
class StoryParams:
    place: str
    smell: str
    response: str
    hero: str = "Mira"
    watcher: str = "Shea"
    parent: str = "Captain"
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "musk": [("What is musk?", "Musk is a strong, sweet smell. It can linger on cloth and paper.")],
    "shea": [("What is shea?", "Shea can mean a buttery balm or oil that feels smooth and greasy.")],
    "portfolio": [("What is a portfolio?", "A portfolio is a flat case for carrying papers and drawings safely.")],
    "smell": [("Why do strong smells stick around?", "Strong smells can cling to cloth and paper until they are cleaned or sealed.")],
    "paper": [("Why does paper need care on a ship?", "Paper can bend, smear, or get ruined by water and sticky messes.")],
}
KNOWLEDGE_ORDER = ["musk", "shea", "portfolio", "smell", "paper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a child that uses the words "{f["smell"].label}", '
        f'"shea", and "portfolio", and includes rhyme and sound effects.',
        f"Tell a sea tale where {f['hero'].id} and {f['watcher'].id} protect a "
        f"portfolio from a sticky smell, with a rhyming line and a big sound effect.",
        "Write a short pirate adventure where a strong smell causes trouble, but a "
        "sensible fix saves the charts.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, watcher, parent = f["hero"], f["watcher"], f["parent"]
    smell, port = f["smell"], f["portfolio"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {watcher.id}, with {parent.label_word} helping them on the deck."),
        ("What got into trouble?",
         f"The {port.label} got sticky after the {smell.label} spilled nearby."),
        ("What did the watcher say?",
         f"{watcher.id} warned that the smell could smear the charts and make the captain notice."),
    ]
    if f["contained"]:
        qa.append((
            "How was the problem fixed?",
            f"They used a sensible fix: {resp.qa_text}. That kept the portfolio safe and the deck calm."
        ))
        qa.append((
            "How did the story end?",
            "It ended with a clean portfolio, happy pirates, and the charts ready for the next voyage."
        ))
    else:
        qa.append((
            "What happened at the end?",
            "The portfolio was too messy to trust, so the crew had to start over with fresh charts."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["smell"].tags) | set(world.facts["portfolio"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", smell="musk", response="tin", hero="Mira", watcher="Shea", parent="Captain", delay=0),
    StoryParams(place="dock", smell="shea", response="cloth", hero="Pip", watcher="Shea", parent="Captain", delay=0),
    StoryParams(place="ship", smell="musk", response="sink", hero="Rook", watcher="Shea", parent="Captain", delay=2),
]


def explain_rejection(smell: ObjectCfg, portfolio: ObjectCfg) -> str:
    if not hazard_ok(smell, portfolio):
        return "(No story: the smell and the portfolio do not make a real problem together.)"
    return "(No story: this combination is not reasonable for this tiny pirate tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak in common sense (sense={r.sense} < {SENSE_MIN}). Try: {good}.)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_saved(RESPONSES[params.response], params.delay) else "lost"


ASP_RULES = r"""
smelly(musk).
smelly(shea).
mutable(portfolio).
sense(tin,3).
sense(cloth,2).
sense(sink,1).
power(tin,2).
power(cloth,1).
power(sink,1).

valid(Smell, Resp, portfolio) :- smelly(Smell), mutable(portfolio), sense(Resp,S), sense_min(M), S >= M.
contained(Resp, D) :- power(Resp,P), severity(D,V), P >= V.
outcome(contained) :- contained(_, D), delay(D).
outcome(lost) :- not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.smelly:
            lines.append(asp.fact("smelly", oid))
        if obj.mutable:
            lines.append(asp.fact("mutable", oid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("severity", params.delay, severity(params.delay)), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {exc}")
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH in outcome for {p}")
            break
    else:
        print("OK: outcome model matches on curated cases.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate storyworld with musk, shea, portfolio, rhyme, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--smell", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--watcher")
    ap.add_argument("--parent")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.smell and args.smell not in OBJECTS:
        raise StoryError("Unknown smell object.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.smell is None or c[1] == args.smell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, smell, response = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    watcher = args.watcher or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    parent = args.parent or "Captain"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    if args.response:
        response = args.response
    return StoryParams(place=place, smell=smell, response=response, hero=hero, watcher=watcher, parent=parent, delay=delay)


def generate(params: StoryParams) -> StorySample:
    for field_name in ("place", "smell", "response"):
        if not getattr(params, field_name, None):
            raise StoryError(f"Missing required story parameter: {field_name}")
    if params.place not in PLACES:
        raise StoryError("Invalid place.")
    if params.smell not in OBJECTS:
        raise StoryError("Invalid smell.")
    if params.response not in RESPONSES:
        raise StoryError("Invalid response.")
    world = tell(
        place=PLACES[params.place],
        smell=OBJECTS[params.smell],
        portfolio=OBJECTS["portfolio"],
        response=RESPONSES[params.response],
        hero_name=params.hero,
        watcher_name=params.watcher,
        parent_name=params.parent,
        delay=params.delay,
    )
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
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
