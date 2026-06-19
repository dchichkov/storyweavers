#!/usr/bin/env python3
"""
storyworlds/worlds/pirate_lantern_reconciliation.py
===================================================

A standalone storyworld for a seed prompt:

    Words: lantern
    Features: Magic, Foreshadowing, Reconciliation
    Style: Pirate Tale

The world models a small pirate crew whose magic lantern is only useful when the
crew trusts each other. A suspicious clue makes one child accuse another of
spoiling the lantern, but the clue is ambiguous: it matches the accused child's
things and a separate true cause. The story is only generated when that clue is
plausible and the remedy actually fixes the cause.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    id: str
    name: str
    sea: str
    deck: str
    hiding_place: str
    omen: str
    role_plural: str


@dataclass
class Sign:
    id: str
    mark: str
    worn: str
    clue: str
    accusation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    mark: str
    need: str
    actor: str
    event: str
    discovery: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    need: str
    offer: str
    action: str
    qa: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_quarrel_dims_lantern(world: World) -> list[str]:
    accuser = world.get("accuser")
    suspect = world.get("suspect")
    lantern = world.get("lantern")
    if accuser.memes["accusing"] < THRESHOLD or suspect.memes["hurt"] < THRESHOLD:
        return []
    sig = ("quarrel", accuser.id, suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["conflict"] += 1
    suspect.memes["conflict"] += 1
    lantern.meters["dim"] += 1
    return ["__quarrel__"]


def _r_truth_lights_lantern(world: World) -> list[str]:
    lantern = world.get("lantern")
    if lantern.meters["truth_found"] < THRESHOLD:
        return []
    sig = ("truth_glow", lantern.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lantern.meters["blue_glow"] += 1
    for eid in ("accuser", "suspect"):
        world.get(eid).memes["hope"] += 1
    return ["The lantern gave a blue flash, the color it always showed when the truth was near."]


def _r_reconciliation(world: World) -> list[str]:
    accuser = world.get("accuser")
    suspect = world.get("suspect")
    lantern = world.get("lantern")
    if accuser.memes["apology"] < THRESHOLD or lantern.meters["repaired"] < THRESHOLD:
        return []
    sig = ("reconciled", accuser.id, suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["conflict"] = 0.0
    suspect.memes["conflict"] = 0.0
    accuser.memes["trust"] += 1
    suspect.memes["trust"] += 1
    lantern.meters["warm_glow"] += 1
    lantern.meters["dim"] = 0.0
    return ["__reconciled__"]


CAUSAL_RULES = [
    Rule("quarrel_dims_lantern", "social", _r_quarrel_dims_lantern),
    Rule("truth_lights_lantern", "magic", _r_truth_lights_lantern),
    Rule("reconciliation", "social", _r_reconciliation),
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
        for sent in produced:
            world.say(sent)
    return produced


def clue_can_mislead(sign: Sign, cause: Cause) -> bool:
    return sign.mark == cause.mark


def remedy_fits(cause: Cause, remedy: Remedy) -> bool:
    return cause.need == remedy.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for ship in SHIPS:
        for sign_id, sign in SIGNS.items():
            for cause_id, cause in CAUSES.items():
                for remedy_id, remedy in REMEDIES.items():
                    if clue_can_mislead(sign, cause) and remedy_fits(cause, remedy):
                        out.append((ship, sign_id, cause_id, remedy_id))
    return out


def predict_bad_sailing(world: World) -> dict:
    sim = world.copy()
    sim.get("accuser").memes["accusing"] += 1
    sim.get("suspect").memes["hurt"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("accuser").memes["conflict"],
        "dim": sim.get("lantern").meters["dim"],
    }


def introduce(world: World, accuser: Entity, suspect: Entity, elder: Entity,
              sign: Sign) -> None:
    ship = world.ship
    accuser.memes["love_adventure"] += 1
    suspect.memes["trust"] += 1
    world.say(
        f"On the {ship.name}, {accuser.id} and {suspect.id} were the smallest "
        f"{ship.role_plural} on the {ship.sea}."
    )
    world.say(
        f"{suspect.id} always wore {sign.worn}, and {elder.id} trusted both "
        f"children to polish the ship's magic lantern."
    )


def foreshadow(world: World) -> None:
    lantern = world.get("lantern")
    lantern.meters["magic"] += 1
    world.say(
        f"The lantern hung by {world.ship.deck}. It glowed gold on honest nights, "
        f"but that morning it gave {world.ship.omen} and went still."
    )


def discover_loss(world: World, accuser: Entity, suspect: Entity, sign: Sign,
                  cause: Cause) -> None:
    lantern = world.get("lantern")
    lantern.meters["missing_light"] += 1
    world.say(
        f"By noon the light would not wake. Near {world.ship.hiding_place}, "
        f"{accuser.id} found {sign.clue}."
    )
    world.say(f"{cause.event}")


def accuse(world: World, accuser: Entity, suspect: Entity, sign: Sign) -> None:
    accuser.memes["accusing"] += 1
    suspect.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{suspect.id}, this looks like yours," {accuser.id} said. '
        f'"{sign.accusation}"'
    )
    world.say(
        f"{suspect.id}'s face tightened. \"I did not spoil the lantern,\" "
        f"{suspect.pronoun()} said."
    )


def elder_warns(world: World, elder: Entity) -> None:
    pred = predict_bad_sailing(world)
    if pred["dim"] >= THRESHOLD:
        world.facts["predicted_dim"] = pred["dim"]
        world.say(
            f"{elder.id} lifted a finger. \"A crew that sails angry gets no help "
            f"from a truth lantern. If you keep blaming before looking, its light "
            f"will stay dark.\""
        )


def investigate(world: World, accuser: Entity, suspect: Entity, cause: Cause) -> None:
    lantern = world.get("lantern")
    accuser.memes["curiosity"] += 1
    suspect.memes["courage"] += 1
    lantern.meters["truth_found"] += 1
    world.say(
        f"So they searched together instead of shouting. Behind the coils of rope, "
        f"they found the truth: {cause.discovery}"
    )
    propagate(world)


def repair(world: World, accuser: Entity, suspect: Entity, remedy: Remedy) -> None:
    lantern = world.get("lantern")
    lantern.meters["repaired"] += 1
    accuser.memes["responsibility"] += 1
    suspect.memes["helping"] += 1
    world.say(f'{suspect.id} said, "Then we can fix it." {remedy.action}')


def apologize(world: World, accuser: Entity, suspect: Entity) -> None:
    accuser.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{accuser.id} swallowed hard. "I am sorry I blamed you before I knew," '
        f"{accuser.pronoun()} said."
    )
    world.say(
        f"{suspect.id} nodded, and the lantern warmed from blue to honey-gold. "
        f"Together they carried it to the bow, friends again."
    )


def closing(world: World, accuser: Entity, suspect: Entity) -> None:
    if world.get("lantern").meters["warm_glow"] >= THRESHOLD:
        world.say(
            f"That night it showed the safe channel through the reef, and the "
            f"{world.ship.role_plural} cheered. {accuser.id} and {suspect.id} "
            f"kept watch side by side, remembering that a clue is not the same "
            f"as the whole truth."
        )


def tell(ship: Ship, sign: Sign, cause: Cause, remedy: Remedy,
         accuser_name: str = "Pip", accuser_gender: str = "boy",
         suspect_name: str = "Mara", suspect_gender: str = "girl",
         elder_name: str = "Captain Jo", elder_gender: str = "woman",
         trait: str = "bold") -> World:
    world = World(ship)
    accuser = world.add(Entity(id=accuser_name, kind="character", type=accuser_gender,
                               label=accuser_name,
                               role="accuser", traits=[trait]))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender,
                               label=suspect_name,
                               role="suspect", traits=["steady"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender,
                             label=elder_name, role="elder"))
    world.add(Entity("lantern", type="lantern", label="magic lantern"))

    introduce(world, accuser, suspect, elder, sign)
    foreshadow(world)

    world.para()
    discover_loss(world, accuser, suspect, sign, cause)
    accuse(world, accuser, suspect, sign)
    elder_warns(world, elder)

    world.para()
    investigate(world, accuser, suspect, cause)
    repair(world, accuser, suspect, remedy)
    apologize(world, accuser, suspect)
    closing(world, accuser, suspect)

    world.facts.update(
        accuser=accuser, suspect=suspect, elder=elder, ship=ship, sign=sign,
        cause=cause, remedy=remedy, lantern=world.get("lantern"),
        reconciled=world.get("lantern").meters["warm_glow"] >= THRESHOLD,
    )
    return world


SHIPS = {
    "gull": Ship("gull", "Sea Gull", "Mist-Blue Sea", "the brass compass",
                 "the anchor chest", "one small green blink", "pirates"),
    "starfish": Ship("starfish", "Starfish", "Silver Shoals", "the wheel",
                     "the chart barrel", "three sleepy blue sparks", "deckhands"),
    "kelp": Ship("kelp", "Kelp Queen", "Whispering Bay", "the mainmast",
                 "the rope basket", "a thin violet shimmer", "pirates"),
}

SIGNS = {
    "silver_thread": Sign(
        "silver_thread", "silver", "a silver scarf", "a shining silver thread",
        "You must have tugged the wick loose with your scarf.",
        tags={"clue", "thread"}),
    "red_wax": Sign(
        "red_wax", "red_wax", "a red wax seal on every pretend captain's note",
        "a crumb of red wax", "You must have dripped wax into the lantern.",
        tags={"clue", "wax"}),
    "shell_dust": Sign(
        "shell_dust", "shell", "a necklace of tiny shells",
        "a pinch of pearly shell dust", "You must have hidden shells inside it.",
        tags={"clue", "shell"}),
}

CAUSES = {
    "moonfish": Cause(
        "moonfish", "silver", "guide_back", "moonfish",
        "Something also tapped inside the glass, soft as a fingernail.",
        "a lost moonfish had slipped into the lantern and tangled the wick with a silver fin-thread.",
        "the lantern would stay dark until the little fish reached moonlit water",
        tags={"lantern", "magic", "moonfish"}),
    "chart_candle": Cause(
        "chart_candle", "red_wax", "clean_lens", "old candle",
        "A warm smell, like birthday candles, drifted from the lantern door.",
        "an old chart candle had melted in the sun and splashed red wax across the lantern lens.",
        "the lantern could not shine through the wax",
        tags={"lantern", "wax", "light"}),
    "hermit_crab": Cause(
        "hermit_crab", "shell", "return_crab", "hermit crab",
        "A tiny scrape-scrape came from under the bench.",
        "a homesick hermit crab had crawled in with shell dust on its feet and knocked the star-stone sideways.",
        "the lantern's star-stone would not settle while the crab was trapped",
        tags={"lantern", "shell", "kindness"}),
}

REMEDIES = {
    "guide_back": Remedy(
        "guide_back", "guide_back",
        "guide the moonfish back to moonlit water",
        "They filled a cup with sea water, sang the tide-song, and guided the moonfish back over the side.",
        "guided the moonfish back to moonlit water",
        tags={"moonfish", "kindness"}),
    "clean_lens": Remedy(
        "clean_lens", "clean_lens",
        "clean the wax from the lantern lens",
        "They warmed a cloth in their hands and gently wiped the red wax from the glass.",
        "cleaned the wax from the lantern lens",
        tags={"wax", "light"}),
    "return_crab": Remedy(
        "return_crab", "return_crab",
        "carry the hermit crab back to its tide pool",
        "They tucked the hermit crab into a bucket of damp sand and carried it to the tide pool.",
        "returned the hermit crab to its tide pool",
        tags={"shell", "kindness"}),
}

GIRL_NAMES = ["Mara", "Lina", "Nia", "Rose", "Tessa", "June"]
BOY_NAMES = ["Pip", "Finn", "Joss", "Theo", "Ben", "Sam"]
TRAITS = ["bold", "quick", "eager", "proud", "curious", "brave"]


@dataclass
class StoryParams:
    ship: str
    sign: str
    cause: str
    remedy: str
    accuser: str
    accuser_gender: str
    suspect: str
    suspect_gender: str
    elder: str
    elder_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lantern": [("What is a lantern?",
                 "A lantern is a light with a case around it, so it can be carried or hung up.")],
    "magic": [("What makes a magic object different in a story?",
               "A magic object can do something ordinary objects cannot. In this story, the lantern reacts to truth and trust.")],
    "clue": [("What is a clue?",
              "A clue is a small sign that helps you learn what happened. A clue can help, but it can also be misunderstood.")],
    "thread": [("Can a thread be a clue?",
                "Yes. A thread can show that cloth or fabric touched a place, but it does not prove who caused the trouble.")],
    "wax": [("Why can wax block a light?",
             "Wax can smear over glass and make it cloudy, so less light can shine through.")],
    "shell": [("What is shell dust?",
               "Shell dust is tiny broken bits from shells. It can look like pale sand or powder.")],
    "kindness": [("Why does kindness help fix a quarrel?",
                  "Kindness helps people calm down and listen. Then they can solve the real problem together.")],
    "light": [("Why do sailors need a light at night?",
               "A light helps sailors see hazards and find the safe way through dark water.")],
}
KNOWLEDGE_ORDER = ["lantern", "magic", "clue", "thread", "wax", "shell", "kindness", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, ship = f["accuser"], f["suspect"], f["ship"]
    return [
        'Write a pirate tale for young children that includes the word "lantern" and uses magic, foreshadowing, and reconciliation.',
        f"Tell a story on the {ship.name} where {a.id} blames {b.id} for a broken magic lantern, then learns the truth and apologizes.",
        "Write a gentle adventure where a glowing lantern warns the crew that anger will hide the safe path until friends make peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, elder, sign, cause, remedy = (f["accuser"], f["suspect"], f["elder"],
                                        f["sign"], f["cause"], f["remedy"])
    return [
        ("Who is the story about?",
         f"It is about {a.id}, {b.id}, and {elder.id} on the {world.ship.name}."),
        ("What strange thing did the lantern do at the beginning?",
         f"It gave {world.ship.omen} and then went still. That foreshadowed that something was wrong before the quarrel began."),
        (f"Why did {a.id} blame {b.id}?",
         f"{a.id} found {sign.clue}, and it reminded {a.pronoun('object')} of what {b.id} wore: {sign.worn}. The clue was real, but {a.id} misunderstood what it meant."),
        ("What was the true cause of the trouble?",
         f"The true cause was that {cause.discovery}"),
        ("How did they fix the lantern?",
         f"They {remedy.qa}. After that, {a.id} apologized for blaming {b.id} too quickly."),
        ("How did the story end?",
         f"The friends reconciled, and the lantern glowed warm again. Its light guided the crew safely through the reef."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lantern", "magic", "clue"} | set(world.facts["sign"].tags) | set(world.facts["cause"].tags) | set(world.facts["remedy"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    seen: set[int] = set()
    for ent in world.entities.values():
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("gull", "silver_thread", "moonfish", "guide_back",
                "Pip", "boy", "Mara", "girl", "Captain Jo", "woman", "bold"),
    StoryParams("starfish", "red_wax", "chart_candle", "clean_lens",
                "Lina", "girl", "Finn", "boy", "Aunt Pearl", "woman", "quick"),
    StoryParams("kelp", "shell_dust", "hermit_crab", "return_crab",
                "Theo", "boy", "Nia", "girl", "Uncle Bram", "man", "curious"),
]


def explain_rejection(sign: Sign, cause: Cause, remedy: Remedy) -> str:
    if not clue_can_mislead(sign, cause):
        return (f"(No story: {sign.clue} points to the mark '{sign.mark}', but "
                f"the true cause leaves '{cause.mark}'. The misunderstanding would not be fair.)")
    return (f"(No story: {cause.actor} needs a remedy for '{cause.need}', but "
            f"'{remedy.id}' solves '{remedy.need}'. The fix must address the real cause.)")


ASP_RULES = r"""
ambiguous(Sign, Cause) :- sign(Sign), cause(Cause), sign_mark(Sign, M), cause_mark(Cause, M).
effective(Cause, Remedy) :- cause(Cause), remedy(Remedy), cause_need(Cause, N), remedy_need(Remedy, N).
valid(Ship, Sign, Cause, Remedy) :- ship(Ship), ambiguous(Sign, Cause), effective(Cause, Remedy).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("sign_mark", sid, sign.mark))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_mark", cid, cause.mark))
        lines.append(asp.fact("cause_need", cid, cause.need))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_need", rid, remedy.need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: pirate lantern, false clue, reconciliation. Unspecified choices are randomized.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--accuser")
    ap.add_argument("--accuser-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    if args.sign and args.cause and args.remedy:
        sign, cause, remedy = SIGNS[args.sign], CAUSES[args.cause], REMEDIES[args.remedy]
        if not (clue_can_mislead(sign, cause) and remedy_fits(cause, remedy)):
            raise StoryError(explain_rejection(sign, cause, remedy))
    if args.sign and args.cause and not clue_can_mislead(SIGNS[args.sign], CAUSES[args.cause]):
        raise StoryError(explain_rejection(SIGNS[args.sign], CAUSES[args.cause], next(iter(REMEDIES.values()))))
    if args.cause and args.remedy and not remedy_fits(CAUSES[args.cause], REMEDIES[args.remedy]):
        sign = SIGNS[args.sign] if args.sign else next(s for s in SIGNS.values() if s.mark == CAUSES[args.cause].mark)
        raise StoryError(explain_rejection(sign, CAUSES[args.cause], REMEDIES[args.remedy]))

    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.sign is None or c[1] == args.sign)
              and (args.cause is None or c[2] == args.cause)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, sign, cause, remedy = rng.choice(sorted(combos))
    ag = args.accuser_gender or rng.choice(["girl", "boy"])
    sg = args.suspect_gender or rng.choice(["girl", "boy"])
    accuser = args.accuser or _pick_name(rng, ag)
    suspect = args.suspect or _pick_name(rng, sg, avoid=accuser)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or ("Captain Jo" if elder_gender == "woman" else "Captain Bram")
    return StoryParams(ship, sign, cause, remedy, accuser, ag, suspect, sg,
                       elder, elder_gender, rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = tell(SHIPS[params.ship], SIGNS[params.sign], CAUSES[params.cause],
                 REMEDIES[params.remedy], params.accuser, params.accuser_gender,
                 params.suspect, params.suspect_gender, params.elder,
                 params.elder_gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ship, sign, cause, remedy) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.accuser} and {p.suspect}: {p.sign} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
