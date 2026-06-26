#!/usr/bin/env python3
"""
storyworlds/worlds/abnormal_griffin_chameleon_happy_ending_magic_pirate.py
===========================================================================

A small pirate-tale story world about an unusual crew, a magical mishap, and a
happy ending.

Premise:
A childlike pirate captain sails with an abnormal griffin and a chameleon crew
mate. The griffin's odd feather-glow and the chameleon’s color-changing habit
make life aboard the ship lively, but a burst of magic from a found charm turns
the voyage tense.

Turn:
The magic makes the ship's lanterns, map ink, and sea spray behave strangely.
The crew must decide whether to panic, hide, or use the chameleon’s gift to
blend into the changing deck and solve the problem.

Resolution:
They use the griffin’s unusual sky-sense and the chameleon’s camouflage to
retrieve the charm and calm the magic. The tale ends with the ship safe, the
crew proud, and the ending image proving the voyage became a happy ending.

This world keeps the style close to a pirate tale: deck, cargo, lanterns,
captain, treasure, sea, and a gently swashbuckling voice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sea_state: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "glitter", "ink"):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                if item.protective:
                    continue
                if item.meters["clean"] < THRESHOLD:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["clean"] = 0
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    captain = next((e for e in world.characters() if e.type == "captain"), None)
    if not captain:
        return out
    for actor in world.characters():
        if actor is captain:
            continue
        if actor.memes["fear"] < THRESHOLD and actor.memes["embarrassment"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trouble"] += 1
        out.append(f"The deck felt tense around {actor.id}.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("conflict", _r_conflict)]


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


def setting_detail(setting: Setting) -> str:
    return f"The {setting.place} rocked with {setting.sea_state} seas and creaking ropes."


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["clean"] < THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


SETTINGS = {
    "harbor": Setting(place="harbor", sea_state="calm", affords={"find_map", "magic"}),
    "open_sea": Setting(place="open sea", sea_state="windy", affords={"magic", "storm"}),
    "cove": Setting(place="quiet cove", sea_state="gentle", affords={"find_map", "magic"}),
}

ACTIVITIES = {
    "find_map": Activity(
        id="find_map",
        verb="search for the map",
        gerund="searching for the map",
        rush="dash to the chart chest",
        mess="ink",
        soil="smudged with ink",
        zone={"hands", "torso"},
        keyword="map",
        tags={"map", "ink"},
    ),
    "magic": Activity(
        id="magic",
        verb="touch the magic charm",
        gerund="handling the magic charm",
        rush="reach for the glowing charm",
        mess="glitter",
        soil="covered in glitter",
        zone={"hands", "torso", "deck"},
        keyword="magic",
        tags={"magic", "glitter"},
    ),
    "storm": Activity(
        id="storm",
        verb="brace for the storm",
        gerund="bracing for the storm",
        rush="run to the mast",
        mess="wet",
        soil="soaked by spray",
        zone={"hands", "torso", "deck"},
        keyword="storm",
        tags={"storm", "wet"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a fine captain's hat", type="hat", region="head"),
    "coat": Prize(label="coat", phrase="a bright sea coat", type="coat", region="torso"),
    "boots": Prize(label="boots", phrase="tall deck boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="cloak",
        label="a shimmer-cloak",
        covers={"torso", "hands"},
        guards={"glitter", "ink"},
        prep="wrap up in a shimmer-cloak",
        tail="tied on the shimmer-cloak",
    ),
    Gear(
        id="oilskin",
        label="oilskin gear",
        covers={"torso", "hands", "feet"},
        guards={"wet"},
        prep="put on oilskin gear",
        tail="buckled the oilskin gear",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="gloves",
        covers={"hands"},
        guards={"glitter", "ink"},
        prep="pull on gloves",
        tail="pulled on the gloves",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Ruby", "Ivy", "Nell", "Pia", "Tara"]
BOY_NAMES = ["Joss", "Finn", "Milo", "Nate", "Owen", "Reef"]
TRAITS = ["bold", "kind", "curious", "cheerful", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale story world with magic and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain", "pirate"])
    ap.add_argument("--name")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not endanger the {prize.label}.)"
    return f"(No story: no reasonable gear in this world can protect the {prize.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid pirate story matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, captain=captain, trait=trait)


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, act: Activity) -> None:
    world.say(f"On a {world.setting.sea_state} day, {hero.id} sailed as a {hero.traits[0]} little pirate.")
    world.say(f"Beside {hero.pronoun('object')}, there was an abnormal griffin named {helper.id}, with a bright look in {helper.pronoun('possessive')} eyes.")
    world.say(f"There was also a chameleon on deck, and everyone called {prize.label} the lucky prize.")
    world.say(f"{hero.id} loved {act.gerund}, but {hero.pronoun('possessive')} {prize.label} had to stay safe at sea.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, trait: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=captain_type, traits=[trait, "pirate"]))
    griffin = world.add(Entity(id="Griffin", kind="character", type="griffin", traits=["abnormal", "watchful"]))
    chameleon = world.add(Entity(id="Chameleon", kind="character", type="chameleon", traits=["quick", "color-changing"]))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region))
    intro(world, hero, griffin, prize, activity)

    world.para()
    world.say(setting_detail(setting))
    world.say(f"{hero.id} wanted to {activity.verb}, but then the magic charm on the deck began to glow.")
    world.say(f"Blue sparks leapt to the ropes, the lanterns flickered, and even the {prize.label} seemed to shimmer.")

    hero.memes["desire"] += 1
    griffin.memes["alert"] += 1
    chameleon.memes["focus"] += 1
    world.facts["hero"] = hero
    world.facts["griffin"] = griffin
    world.facts["chameleon"] = chameleon
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["setting"] = setting

    world.para()
    world.say(f"{hero.id} reached for the charm, but the captain's heart worried it would spoil the voyage.")
    world.say(f"{griffin.id} spread {griffin.pronoun('possessive')} wings and sniffed the wind, while {chameleon.id} slipped into the color of the deck boards.")
    world.say(f"They saw that the charm had rolled under a crate near the mast.")

    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"If we rush in now, the magic will leave the {prize.label} {activity.soil}," the captain said.')

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize))
    if activity.mess == "glitter":
        world.say(f"{hero.id} put on {gear.label}, and the {griffin.id} pointed at the crate with a sharp cry.")
    else:
        world.say(f"{hero.id} put on {gear.label}, and the crew moved like shadows across the deck.")
    world.say(f"{chameleon.id} changed colors to match the planks, which helped hide the crew from the bright spell.")
    world.say(f"{griffin.id}, though abnormal in the best way, had the keenest nose for magic, and led them straight to the charm.")
    world.say(f"{hero.id} tucked the charm into a safe pouch, and the sparks faded like stars at dawn.")
    world.say(f"At last, the {prize.label} stayed clean, the ship stayed steady, and the crew cheered for a happy ending.")
    world.say(f"The pirate ship sailed on with calm sails, a clever griffin, a clever chameleon, and a sparkling bit of magic safely put away.")

    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short pirate tale for a young child about {hero.id}, an abnormal griffin, a chameleon, and the word "magic".',
        f"Tell a swashbuckling story where a captain wants to {act.verb} but worries about the {prize.label}, and the crew finds a happy ending.",
        f'Write a gentle story on a pirate ship that includes "griffin", "chameleon", and a magical problem solved by clever teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    griffin = f["griffin"]
    chameleon = f["chameleon"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about on the pirate ship?",
            answer=f"It was about {hero.id}, an abnormal griffin named {griffin.id}, and a chameleon named {chameleon.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the magic charm caused trouble?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the crew worry about the {prize.label}?",
            answer=f"They worried the magic and sea-spray trouble would leave the {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They used {gear.label}, followed {griffin.id}'s sense for magic, and let {chameleon.id} blend into the deck until they found the charm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the ship safe, the {prize.label} clean, and the crew cheering for a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a griffin?",
            answer="A griffin is a legendary creature with the body of a lion and the head and wings of an eagle.",
        ),
        QAItem(
            question="What can a chameleon do?",
            answer="A chameleon can change its color to blend in with its surroundings.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something strange and wonderful that can make impossible things happen.",
        ),
        QAItem(
            question="What makes a pirate tale feel like a pirate tale?",
            answer="Pirate tales often have ships, decks, treasure, ropes, sea wind, and brave teamwork.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk when the activity reaches its region.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% A gear is a valid fix when it guards the mess and covers the region.
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_story_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.trait, params.captain)
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


CURATED = [
    StoryParams(place="harbor", activity="magic", prize="coat", name="Mina", gender="girl", captain="captain", trait="bold"),
    StoryParams(place="cove", activity="find_map", prize="hat", name="Joss", gender="boy", captain="pirate", trait="curious"),
    StoryParams(place="open_sea", activity="storm", prize="boots", name="Ruby", gender="girl", captain="captain", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
