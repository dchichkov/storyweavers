#!/usr/bin/env python3
"""
storyworlds/worlds/able_flashback_curiosity_kindness_bedtime_story.py
=====================================================================

A small bedtime-story world about a child who feels curious, remembers a
kindness from earlier, and becomes able to choose a gentle ending.

Seed tale used to build the world:
---
At bedtime, a small child heard a tiny tapping sound by the window. The child
was curious and wanted to go look, even though it was sleepy time. The parent
worried that the child would stay awake too long and that the blanket would get
cold if the window stayed open.

The child remembered, in a warm flashback, how being kind earlier that day had
helped a frightened little moth. That memory made the child brave and gentle
instead of restless. Together, they closed the window, gave the moth a safe
place near the lamp, and went back to bed feeling calm and able to sleep.

World model ideas:
---
    curiosity rising      -> child.memes["curiosity"] += 1
    flashback recalled    -> child.memes["memory_warmth"] += 1
    kind action taken     -> child.memes["kindness"] += 1 ; child.memes["calm"] += 1
    open window at night   -> room.meters["chill"] += 1
    chill + uncovered bed  -> blanket.meters["cold"] += 1
    warm lamp nook        -> chill on the blanket is prevented
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

ROOMS = {"bedroom", "nursery", "attic_room"}
MOODS = {"curious", "sleepy", "kind", "able", "calm"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    indoors: bool = True
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_chill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("window_open", 0.0) < THRESHOLD:
            continue
        sig = ("chill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["chill"] = actor.meters.get("chill", 0.0) + 1
        out.append("A cool little draft slipped into the room.")
    return out


def _r_blanket_cold(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("chill", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region != "bed":
                continue
            sig = ("cold", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if not world.covered(actor, "bed"):
                item.meters["cold"] = item.meters.get("cold", 0.0) + 1
                out.append(f"The {item.label} grew cool near the open window.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD or actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        actor.memes["able"] = actor.memes.get("able", 0.0) + 1
        out.append(f"{actor.id} felt ready and able to be gentle.")
    return out


CAUSAL_RULES = [
    Rule("chill", _r_chill),
    Rule("blanket_cold", _r_blanket_cold),
    Rule("calm", _r_calm),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_cold(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "cold": bool(prize and prize.meters.get("cold", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    if activity.id == "open_window":
        actor.memes["window_open"] = actor.memes.get("window_open", 0.0) + 1
    if activity.id == "remember_kindness":
        actor.memes["kindness"] = actor.memes.get("kindness", 0.0) + 1
        actor.memes["memory_warmth"] = actor.memes.get("memory_warmth", 0.0) + 1
    if activity.id == "close_window":
        actor.memes["window_open"] = 0.0
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_line(setting: Setting) -> str:
    if setting.place == "the bedroom":
        return "The bedroom was soft and quiet, with moonlight on the wall."
    if setting.place == "the nursery":
        return "The nursery was cozy, with a small lamp and a sleepy rocking chair."
    return "The little room felt tucked away, like a secret pillow fort."


def bedtime_phrase() -> str:
    return "It was almost bedtime, and the house had started to whisper."


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        meters={"chill": 0.0}, memes={"curiosity": 0.0, "kindness": 0.0, "able": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
        meters={"cold": 0.0},
    ))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp", protective=True, covers={"bed"}))

    world.say(bedtime_phrase())
    world.say(f"{hero.id} was a little {hero_type} who loved the hush of night and the word able.")
    world.say(f"{hero.id} liked to listen to tiny sounds, because curiosity felt like a warm spark.")
    world.say(f"That evening, {hero.id} had a {prize.label} nearby and a soft {parent.label} watching over the bed.")

    world.para()
    world.say(setting_line(setting))
    world.say(f"Then a tiny tapping sound came from the window, and {hero.id} wanted to {activity.verb}.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} worried that the noise would keep {hero.pronoun('object')} awake too long.")
    world.say(f"{hero.id} was curious, but the open window could make the {prize.label} feel cold.")

    world.para()
    world.say(f"That was when {hero.id} remembered a flashback from earlier that day.")
    world.say("A frightened little moth had fluttered near the porch light, and the child had been kind enough to guide it back to safety.")
    world.say(f"That memory made {hero.id} breathe slowly and think, 'I can be gentle too.'")
    _do_activity(world, hero, Activity("remember_kindness", "", "", "", "", "", set(), "kindness"), narrate=False)
    world.say(f"So instead of rushing, {hero.id} chose kindness and reached for the softest idea in the room.")

    world.para()
    world.say(f"{hero.id} used the little lamp, opened the curtain just a crack, and found a sleepy moth near the glass.")
    world.say(f"{hero.id} cupped {hero.pronoun('possessive')} hands around it for a moment, then closed the window so the room would stay warm.")
    _do_activity(world, hero, Activity("close_window", "", "", "", "", "", set(), "close"), narrate=False)
    propagate(world, narrate=True)
    world.say("The moth drifted onto the curtain and stayed near the lamp, safe and still.")

    world.para()
    world.say(f"{hero.id} climbed back under the blanket, and the bed felt cozy again.")
    world.say(f"The {prize.label} stayed warm, the room stayed quiet, and {hero.id} felt able to rest.")
    world.say(f"With curiosity soothed by kindness, {hero.id} closed {hero.pronoun('possessive')} eyes and slipped into sleep.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        lamp=lamp,
        activity=activity,
        setting=setting,
        conflict=True,
        resolved=True,
        remember_kindness=True,
    )
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"open_window", "remember_kindness", "close_window"}),
    "nursery": Setting(place="the nursery", indoors=True, affords={"open_window", "remember_kindness", "close_window"}),
    "attic_room": Setting(place="the attic room", indoors=True, affords={"open_window", "remember_kindness", "close_window"}),
}

ACTIVITIES = {
    "open_window": Activity(
        id="open_window",
        verb="peek at the little light",
        gerund="peeking at the little light",
        rush="rush to the window",
        mess="chill",
        soil="cool and sleepy",
        zone={"bed"},
        keyword="window",
        tags={"window", "night", "curiosity"},
    ),
    "remember_kindness": Activity(
        id="remember_kindness",
        verb="think of the kind thing",
        gerund="remembering the kind thing",
        rush="call the memory back",
        mess="warmth",
        soil="warm and calm",
        zone=set(),
        keyword="kindness",
        tags={"kindness", "memory"},
    ),
    "close_window": Activity(
        id="close_window",
        verb="close the window softly",
        gerund="closing the window softly",
        rush="shut the window",
        mess="calm",
        soil="quiet and calm",
        zone={"bed"},
        keyword="calm",
        tags={"calm", "night"},
    ),
}

PRIZES = {
    "blanket": Prize("blanket", "a soft blanket", "blanket", "bed"),
    "pillow": Prize("pillow", "a plump pillow", "pillow", "bed"),
    "toy": Prize("toy rabbit", "a small toy rabbit", "toy_rabbit", "bed"),
}

GEAR = [
    Gear("lamp", "a lamp", {"bed"}, {"chill"}, "turn on the lamp", "turned on the lamp"),
    Gear("curtain", "the curtain", {"bed"}, {"chill"}, "draw the curtain closed", "drawn the curtain closed"),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Ada", "Penny"]
BOY_NAMES = ["Finn", "Eli", "Owen", "Theo", "Noah", "Ben"]
TRAITS = ["gentle", "curious", "sleepy", "kind"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone or act.id in {"remember_kindness", "close_window"}:
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a bedtime story for a small child about "{act.keyword}" that ends calmly.',
        f"Tell a gentle story where {hero.id} is curious at bedtime, remembers a kindness, and becomes able to settle down.",
        f'Write a soft story with a flashback, curiosity, and kindness in a cozy bedroom.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to look near the window?",
            answer=f"{hero.id} was curious about the tiny tapping sound near the window, so {hero.pronoun('subject')} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember that helped {hero.pronoun('object')} choose a kinder way?",
            answer=f"{hero.id} remembered a flashback from earlier, when {hero.pronoun('subject')} had been kind to a frightened little moth.",
        ),
        QAItem(
            question=f"How did {hero.id} end up feeling at the end of the story?",
            answer=f"{hero.id} felt calm and able to sleep because the window was closed softly and the {prize.label} stayed warm.",
        ),
        QAItem(
            question=f"Why was {parent.label} worried at bedtime?",
            answer=f"{parent.label.capitalize()} worried that the window would stay open too long and make the room chilly, which could keep {hero.id} awake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, listen, and learn more about something new.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or choosing a gentle action that makes someone or something feel safe.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What makes a bedroom cozy at bedtime?",
            answer="Soft blankets, a quiet room, and warm light can make a bedroom feel cozy at bedtime.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "open_window", "blanket", "Mina", "girl", "mother", "curious"),
    StoryParams("nursery", "open_window", "pillow", "Finn", "boy", "father", "gentle"),
    StoryParams("attic_room", "close_window", "toy", "Lila", "girl", "mother", "kind"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not create a clear bedtime problem for {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
% A prize is at risk when the open-window activity chills the bed region.
at_risk(A, P) :- chills(A), bed_item(P).

% A compatible fix exists when the gear covers the bed and protects against chill.
fix(G, A, P) :- gear(G), at_risk(A, P), covers(G, bed), guards(G, chill).
valid(Place, A, P) :- affords(Place, A), bed_item(P), at_risk(A, P), fix(_, A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("chills", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zones", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("bed_item", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Bedtime story world about curiosity, kindness, and a calming flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.gender and "curious" or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:18} {prize:10}  [{', '.join(genders)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
