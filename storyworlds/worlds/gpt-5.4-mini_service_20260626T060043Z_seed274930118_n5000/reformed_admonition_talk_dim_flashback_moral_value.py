#!/usr/bin/env python3
"""
storyworlds/worlds/reformed_admonition_talk_dim_flashback_moral_value.py
========================================================================

A small adventure-flavored story world about a child explorer learning to
answer an admonition, speak dimly, and act more carefully after a flashback to
an earlier mistake.

Seed-imagined tale:
---
A lively young explorer loved racing ahead on the mountain trail and calling out
every new thing she found. One day, she remembered a time when her loud voice
had startled a flock of birds and blown the path marker off a ledge. This time,
her guide warned her to keep her talk dim near the sleeping cave. She tried to
shout anyway, but the old memory made her stop. She used a quiet signal, helped
move the lantern hood into place, and walked on gently. In the end, the trail
stayed calm, and she felt proud of being more considerate than before.

World model:
- physical meters: noise, stillness, wind, steadiness, attention, fatigue
- emotional memes: curiosity, pride, worry, shame, care, reformed, conflict
- a flashback can raise shame and care, which changes the choice the hero makes
- a moral-value turn ends the story with a visible proof of change

The prose engine uses the simulated state to narrate the turn and resolution.
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

MORAL_VALUES = {
    "kindness": "kindness",
    "care": "care",
    "patience": "patience",
    "self-control": "self-control",
    "consideration": "consideration",
}

TALKS = {
    "shout": {"label": "shout", "noise": 1.0, "dim": False},
    "call": {"label": "call out", "noise": 0.8, "dim": False},
    "talk-dim": {"label": "talk dim", "noise": 0.2, "dim": True},
    "whisper": {"label": "whisper", "noise": 0.1, "dim": True},
}

PLACES = {
    "trail": {"place": "the mountain trail", "adventure": True},
    "cave": {"place": "the echo cave", "adventure": True},
    "ridge": {"place": "the windy ridge", "adventure": True},
    "camp": {"place": "the trail camp", "adventure": True},
}

GEAR = [
    {
        "id": "lantern_hood",
        "label": "a lantern hood",
        "helps": {"noise"},
        "prep": "put a lantern hood over the flame",
        "tail": "tucked the lantern hood into place",
    },
    {
        "id": "soft_boots",
        "label": "soft boots",
        "helps": {"stillness"},
        "prep": "lace up soft boots",
        "tail": "slid on the soft boots",
    },
    {
        "id": "signal_card",
        "label": "a signal card",
        "helps": {"attention"},
        "prep": "carry a signal card instead of calling out",
        "tail": "kept the signal card ready",
    },
]

# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    protective: bool = False
    helps: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    key: str
    place: str
    adventure: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: float
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.meters.get("noise", 0.0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.entities.values():
            if e.kind == "thing" and e.owner == actor.id and e.label == "lantern":
                e.meters["wobble"] = e.meters.get("wobble", 0.0) + 1
        out.append(f"Their voice bounced off the stone and made the path feel loud.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.chars() if e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.memes.get("flashback", 0.0) < THRESHOLD:
        return out
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    out.append("A flashback came back to them: last time, loud talk had scared birds from a branch and sent their marker skittering away.")
    return out


def _r_reform(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.chars() if e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.memes.get("care", 0.0) < THRESHOLD or hero.memes.get("reformed", 0.0) >= THRESHOLD:
        return out
    sig = ("reform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["reformed"] = 1.0
    hero.meters["noise"] = min(hero.meters.get("noise", 0.0), 0.2)
    out.append("They remembered how that had ended, and they chose to be more careful now.")
    return out


RULES = [Rule("noise", _r_noise), Rule("flashback", _r_flashback), Rule("reform", _r_reform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def activity_is_reasonable(activity: Activity, prize: Prize) -> bool:
    return prize.risk in {"noise", "attention"} and activity.noise >= 0.1


def select_gear(activity: Activity, prize: Prize) -> Optional[dict]:
    for gear in GEAR:
        if prize.risk in gear["helps"]:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would not honestly threaten the chosen prize in a useful way, "
        f"so there would be no real admonition or reform.)"
    )


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["noise"] = actor.meters.get("noise", 0.0) + activity.noise
    actor.meters["attention"] = actor.meters.get("attention", 0.0) + 0.5
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def flashback(world: World, hero: Entity) -> None:
    hero.memes["flashback"] = 1.0
    world.say("The explorer had a flashback to a different day, when careless words had caused trouble on the trail.")


def admonish(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["admonished"] = 1.0
    world.say(
        f'"Keep your voice dim," {parent.label_word} said. "If you {activity.verb}, do it gently, or you may upset the whole camp."'
    )


def offer_compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[dict]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    ent = world.add(Entity(
        id=gear["id"],
        kind="thing",
        type="gear",
        label=gear["label"],
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        helps=set(gear["helps"]),
    ))
    ent.worn_by = hero.id
    world.say(
        f'{parent.label_word} pointed at {gear["label"]} and said, "How about we {gear["prep"]} first?"'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Prize, gear: dict) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    hero.memes["reformed"] = 1.0
    hero.meters["noise"] = min(hero.meters.get("noise", 0.0), 0.2)
    world.say(
        f'{hero.id} nodded, and their face softened. "I can do that," they said, and {hero.pronoun()} helped make the choice happen.'
    )
    world.say(
        f"After that, they {gear['tail']} and went on {activity.gerund}, while {prize.label} stayed safe and the trail kept its calm."
    )


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize: Prize, name: str, gender: str, parent_type: str, moral: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the guide"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase, caretaker=parent.id))

    world.say(f"{hero.id} was a little explorer who loved {activity.gerund} on {setting.place}.")
    world.say(f"They also liked the feeling of adventure and had a strong sense of {moral}.")
    world.say(f"One day, {parent.label_word} handed over {prize.phrase}, because the trail was long and needed careful steps.")

    world.para()
    flashback(world, hero)
    admonish(world, parent, hero, activity)
    do_activity(world, hero, activity)

    world.para()
    if hero.memes.get("reformed", 0.0) < THRESHOLD:
        world.say(f"{hero.id} almost raised their voice again, but the old memory tugged at them.")
    gear = offer_compromise(world, parent, hero, activity, prize_ent)
    if gear:
        accept(world, hero, parent, activity, prize_ent, gear)
    else:
        world.say(f"Instead of pushing ahead, {hero.id} slowed down and chose a quieter way to go.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize_ent,
        activity=activity,
        setting=setting,
        moral=moral,
        gear=gear,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "trail": Setting(key="trail", place="the mountain trail", affords={"call", "talk-dim", "whisper"}),
    "cave": Setting(key="cave", place="the echo cave", affords={"shout", "call", "talk-dim", "whisper"}),
    "ridge": Setting(key="ridge", place="the windy ridge", affords={"call", "talk-dim", "whisper"}),
    "camp": Setting(key="camp", place="the trail camp", affords={"call", "talk-dim", "whisper"}),
}

ACTIVITIES = {
    "shout": Activity(id="shout", verb="shout to the hills", gerund="shouting to the hills", rush="run ahead and shout", noise=1.0, weather="", keyword="shout", tags={"sound", "adventure"}),
    "call": Activity(id="call", verb="call out", gerund="calling out", rush="call from the ledge", noise=0.8, weather="", keyword="call", tags={"sound", "adventure"}),
    "talk-dim": Activity(id="talk-dim", verb="talk dimly", gerund="talking dimly", rush="speak too brightly", noise=0.2, weather="", keyword="talk-dim", tags={"sound", "quiet", "adventure"}),
    "whisper": Activity(id="whisper", verb="whisper", gerund="whispering", rush="whisper too loudly", noise=0.1, weather="", keyword="whisper", tags={"sound", "quiet", "adventure"}),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="a bright lantern", region="hand", risk="noise"),
    "marker": Prize(id="marker", label="trail marker", phrase="a painted trail marker", region="ledge", risk="attention"),
    "map": Prize(id="map", label="map", phrase="a folded map", region="hand", risk="attention"),
}

GIRL_NAMES = ["Ava", "Mira", "Lina", "Zoe", "Nora", "Esme"]
BOY_NAMES = ["Theo", "Finn", "Milo", "Jace", "Owen", "Leo"]
TRAITS = ["bold", "curious", "lively", "brave", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, setting in SETTINGS.items():
        for a in setting.affords:
            act = ACTIVITIES[a]
            for prize_id, prize in PRIZES.items():
                if activity_is_reasonable(act, prize) and select_gear(act, prize):
                    out.append((p, a, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    moral: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "whisper": [("What is a whisper?", "A whisper is a very soft way of speaking." মোট)],
    "lantern": [("What does a lantern do?", "A lantern helps people see in the dark.")],
    "map": [("What is a map?", "A map is a drawing that shows where places are.")],
    "trail": [("What is a trail?", "A trail is a path people walk on in nature.")],
    "cave": [("Why are caves dark?", "Caves are dark because sunlight does not reach very far inside.")],
    "quiet": [("Why can quiet voices help?", "Quiet voices can help keep animals calm and make it easier to listen.")],
    "care": [("What does care mean?", "Care means thinking about what is safe and kind for other people.")],
    "self-control": [("What is self-control?", "Self-control means slowing yourself down and choosing what is wise.")],
    "kindness": [("What is kindness?", "Kindness means being gentle and helping others feel okay.")],
}
KNOWLEDGE_ORDER = ["trail", "cave", "lantern", "map", "whisper", "quiet", "care", "self-control", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about {f["hero"].id} learning to keep a voice dim on {f["setting"].place}.',
        f"Tell a story with a flashback, an admonition, and a better choice about {f['hero'].id} and {f['prize'].label}.",
        f'Write a child-friendly adventure where a character remembers an old mistake and reforms by speaking softly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} have to keep their voice dim on {world.setting.place}?",
            answer=f"Because {parent.label_word} warned that loud talk could upset the trail, and {prize.label} needed careful handling.",
        ),
        QAItem(
            question=f"What helped {hero.id} change after the flashback?",
            answer=f"The memory of the earlier mistake made {hero.id} more careful, so they chose to talk dimly instead of shouting or calling out.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of making a loud fuss?",
            answer=f"They listened to the admonition, stayed more reformed, and used a quieter way to move forward on the adventure.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {prize.label}?",
            answer=f"{hero.id} went on with the journey more carefully, and {prize.label} stayed safe while the trail kept its calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add(f["moral"])
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.kind == "thing":
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="trail", activity="talk-dim", prize="lantern", name="Ava", gender="girl", parent="mother", moral="care"),
    StoryParams(place="cave", activity="whisper", prize="marker", name="Theo", gender="boy", parent="father", moral="self-control"),
    StoryParams(place="ridge", activity="call", prize="map", name="Mira", gender="girl", parent="mother", moral="kindness"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not activity_is_reasonable(act, prize):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    moral = args.moral or rng.choice(list(MORAL_VALUES))
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.moral)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk if the activity is one where a loud voice can disturb it.
at_risk(A, P) :- noisy(A), prize_risk(P, noise).
at_risk(A, P) :- noisy(A), prize_risk(P, attention).

% A gear item is a usable fix when it helps against the prize risk.
fix(G, A, P) :- at_risk(A, P), gear(G), helps(G, R), prize_risk(P, R).

valid(Place, A, P) :- affords(Place, A), noisy(A), prize_risk(P, _), fix(_, A, P).

#show valid/3.
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
        lines.append(asp.fact("noisy", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_risk", pid, p.risk))
    for g in GEAR:
        lines.append(asp.fact("gear", g["id"]))
        for r in sorted(g["helps"]):
            lines.append(asp.fact("helps", g["id"], r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: reformed admonition, talk-dim, flashback, moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--moral", choices=list(MORAL_VALUES))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for t in combos:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
