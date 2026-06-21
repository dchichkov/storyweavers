#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bullet_sidle_tournament_bravery_teamwork_friendship_pirate.py
=============================================================================================

A small standalone story world in a pirate-tale mood: a child wants to enter a
mini tournament, loses courage, sidles in too cautiously, and then finds the
bravery to compete with teamwork and friendship. The seed words appear in the
world through a harmless pretend-play domain:
- bullet: a round metal pellet used as a prize token, never a weapon
- sidle: a slow, shy movement into the ring
- tournament: a friendly ship-deck contest

The world is intentionally tiny and state-driven. Emotional memes and physical
meters both matter. The story changes because world state changes, not because a
single paragraph gets noun-swapped.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    deck: str
    sky: str
    ring: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    gleam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tournament:
    id: str
    name: str
    rule: str
    cheer: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
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
    apply: Callable[[World], list[str]]


def _r_shake(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["doubt"] < THRESHOLD:
            continue
        sig = ("shake", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fear"] += 1
        out.append("__tremble__")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("joined") and "crew" in world.entities:
        crew = world.get("crew")
        sig = ("team", crew.id)
        if sig not in world.fired:
            world.fired.add(sig)
            crew.meters["bond"] += 1
            out.append("Their teamwork made the deck feel steadier.")
    return out


CAUSAL_RULES = [Rule("shake", _r_shake), Rule("team", _r_team)]


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


def sensible_actions() -> list[HelpAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def best_action() -> HelpAction:
    return max(ACTIONS.values(), key=lambda a: a.sense)


def action_works(action: HelpAction, tension: int) -> bool:
    return action.power >= tension


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for tid in TOURNAMENTS:
            for pid in PRIZES:
                combos.append((sid, tid, pid))
    return combos


@dataclass
class StoryParams:
    setting: str
    tournament: str
    prize: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    helper_gender: str
    action: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(id="harbor", place="the moonlit harbor", deck="deck", sky="night sky", ring="rope ring"),
    "island": Setting(id="island", place="the island dock", deck="boardwalk", sky="sea breeze", ring="chalk ring"),
}

TOURNAMENTS = {
    "cup": Tournament(id="cup", name="a friendly tournament", rule="one turn each", cheer="the crew cheered", finish="the little cup", tags={"tournament"}),
    "match": Tournament(id="match", name="a ship-deck tournament", rule="first to three rings", cheer="the sailors clapped", finish="the winner's ribbon", tags={"tournament"}),
}

PRIZES = {
    "bullet": Prize(id="bullet", label="bullet", phrase="a shiny bullet-shaped token", gleam="gleamed like a tiny moon", tags={"bullet"}),
    "pearl": Prize(id="pearl", label="pearl", phrase="a bright pearl token", gleam="shone like a drop of milk", tags={"bullet"}),
}

ACTIONS = {
    "sidle": HelpAction(id="sidle", sense=2, power=2, text="sidled carefully into the ring", fail="sidled too late and missed the turn", qa="sidled into the ring with care", tags={"sidle"}),
    "charge": HelpAction(id="charge", sense=3, power=4, text="strode into the ring with a brave grin", fail="charged in too wildly and lost balance", qa="strode into the ring bravely", tags={"bravery"}),
    "signal": HelpAction(id="signal", sense=4, power=5, text="signaled their friends and moved as one crew", fail="signaled too late to matter", qa="signaled for teamwork", tags={"teamwork", "friendship"}),
}

SENSE_MIN = 2
GIRL_NAMES = ["Lily", "Mira", "Nina", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Milo", "Kai"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tournament storyworld with bravery, teamwork, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tournament", choices=TOURNAMENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, used: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in used]
    return rng.choice(choices or pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tournament is None or c[1] == args.tournament)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tournament, prize = rng.choice(combos)
    action = args.action or rng.choice(sorted(sensible_actions(), key=lambda a: a.id)).id
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if hg == "girl" else "girl")
    kg = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hg, set())
    friend = args.friend or _pick_name(rng, fg, {hero})
    helper = args.helper or _pick_name(rng, kg, {hero, friend})
    return StoryParams(setting=setting, tournament=tournament, prize=prize,
                       hero_name=hero, hero_gender=hg, friend_name=friend, friend_gender=fg,
                       helper_name=helper, helper_gender=kg, action=action)


def _story_setup(world: World, p: StoryParams) -> None:
    s = SETTINGS[p.setting]
    t = TOURNAMENTS[p.tournament]
    prize = PRIZES[p.prize]
    a = world.add(Entity(id=p.hero_name, kind="character", type=p.hero_gender, role="hero"))
    b = world.add(Entity(id=p.friend_name, kind="character", type=p.friend_gender, role="friend"))
    c = world.add(Entity(id=p.helper_name, kind="character", type=p.helper_gender, role="helper"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", role="crew"))
    crew.meters["bond"] = 0
    a.memes["bravery"] = 1
    a.memes["doubt"] = 1
    b.memes["friendship"] = 1
    c.memes["teamwork"] = 1
    world.say(f"At {s.place}, {a.id} and {b.id} watched the crew prepare for {t.name}.")
    world.say(f"They wanted the {prize.label} token, which {prize.gleam}.")
    world.say(f"The challenge was simple: {t.rule}, and every sailor had to {t.cheer.lower()} if someone got nervous.")


def _predict(world: World, p: StoryParams) -> dict:
    sim = world.copy()
    hero = sim.get(p.hero_name)
    hero.memes["doubt"] += 1
    propagate(sim, narrate=False)
    return {"fear": hero.memes["fear"], "bond": sim.get("crew").meters["bond"] if "crew" in sim.entities else 0}


def tell(p: StoryParams) -> World:
    world = World()
    _story_setup(world, p)
    action = ACTIONS[p.action]
    t = TOURNAMENTS[p.tournament]
    prize = PRIZES[p.prize]
    hero = world.get(p.hero_name)
    friend = world.get(p.friend_name)
    helper = world.get(p.helper_name)
    crew = world.get("crew")
    world.para()
    world.say(f"But when {p.hero_name} came up to the ring, {hero.pronoun().capitalize()} only {action.id}d? {action.text}.")
    hero.memes["doubt"] += 1
    pred = _predict(world, p)
    world.say(f"{p.friend_name} sidled closer and whispered, 'You can do this with us.'")
    friend.memes["friendship"] += 1
    helper.memes["teamwork"] += 1
    joined = action.id in {"signal", "charge", "sidle"}
    world.facts["joined"] = joined
    if joined:
        crew.meters["bond"] += 1
        hero.memes["bravery"] += 1
        world.say(f"{p.helper_name} lifted {hero.pronoun('possessive')} chin, and the three of them moved as one crew.")
        if action_works(action, 2):
            world.para()
            world.say(f"With a brave breath, {p.hero_name} {action.text}, and the crew finished the round together.")
            world.say(f"{t.cheer.capitalize()}, and {p.hero_name} won {prize.phrase}.")
            world.say(f"At the end, the {prize.label} token {prize.gleam} in {hero.pronoun('possessive')} hand.")
        else:
            world.para()
            world.say(f"{p.hero_name} tried, but {action.fail}.")
            world.say(f"Still, {p.friend_name} and {p.helper_name} kept pace, so the round ended in laughter instead of shame.")
            world.say(f"That night the crew kept the {prize.label} token on the captain's table for everyone to admire.")
    world.facts.update(hero=hero, friend=friend, helper=helper, crew=crew, setting=s, tournament=t, prize=prize, action=action, prediction=pred)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate-tale story for a young child that uses the words bullet, sidle, and tournament.",
        f"Tell a brave little story where {f['hero'].id} sidles into a tournament with friends and wins a bullet-shaped token.",
        f"Write a story about bravery, teamwork, and friendship at {f['setting'].place} with a friendly tournament prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    prize = f["prize"]
    action = f["action"]
    t = f["tournament"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {hero.id}, who went to a friendly tournament with {friend.id} and {helper.id}."),
        QAItem(question="What did {hero} do at the ring?".format(hero=hero.id), answer=f"{hero.id} {action.qa}, and the others helped {hero.pronoun('object')} feel braver."),
        QAItem(question="What prize did they want?", answer=f"They wanted {prize.phrase}, which is why the tournament felt exciting."),
        QAItem(question="How did teamwork matter?", answer=f"{friend.id} and {helper.id} stayed close and helped {hero.id} keep going, so the group moved together instead of alone."),
        QAItem(question="How did the story end?", answer=f"It ended with {hero.id} holding the {prize.label} token and smiling with friends after the tournament."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is bravery?", "Bravery is doing something scary anyway because it matters and you want to help."),
        QAItem("What is teamwork?", "Teamwork is when people do something together and each person helps the others."),
        QAItem("What is friendship?", "Friendship is caring about one another, sharing, and helping each other feel safe."),
        QAItem("What is a tournament?", "A tournament is a competition or contest where people take turns and try their best."),
        QAItem("What does sidle mean?", "To sidle means to move slowly and carefully, often because you feel shy or unsure."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines += ["", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines += ["", "== world qa =="]
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


ASP_RULES = r"""
joined(H) :- hero(H), action(A), friendly(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOURNAMENTS:
        lines.append(asp.fact("tournament", tid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.sense >= SENSE_MIN:
            lines.append(asp.fact("friendly", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {(s,) for s, _, _ in valid_combos()}:
        print("MISMATCH in ASP vs Python gates")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, tournament=None, prize=None, action=None, hero=None, hero_gender=None, friend=None, friend_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="harbor", tournament="cup", prize="bullet", hero_name="Lily", hero_gender="girl", friend_name="Finn", friend_gender="boy", helper_name="Mira", helper_gender="girl", action="sidle"),
    StoryParams(setting="island", tournament="match", prize="pearl", hero_name="Kai", hero_gender="boy", friend_name="Nina", friend_gender="girl", helper_name="Owen", helper_gender="boy", action="signal"),
]


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTINGS), ("tournament", TOURNAMENTS), ("prize", PRIZES), ("action", ACTIONS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(params)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=story_qa(world),
                       world_qa=world_knowledge_qa(world),
                       world=world)


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
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(sorted(s[0] for s in asp_valid_combos())))
        return
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(seed + i))
            p.seed = seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
