#!/usr/bin/env python3
"""
storyworlds/worlds/forum_deuce_bad_ending_bedtime_story.py
==========================================================

A small bedtime-story world about a child, a glowing forum, and the word
"deuce" that keeps tugging at the night.

This world is intentionally tuned for a bad ending: the parent sees the trouble
coming, offers a sensible limit, and the child does not take it. The result is a
quiet, concrete ending image that proves what changed: the room is darker, the
child is sleepier, and the bedtime that could have been peaceful is gone.

The story model keeps the domain small and constraint-checked:
- a child wants one more look at a forum
- the forum can make the child wakeful
- a bedtime object is at risk from staying up too long
- a parent offers a reasonable turn-off / stop-after-one compromise
- the child refuses, and the story ends badly
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
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
    weather: str
    keyword: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""
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


def _say_cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("screenlight", 0.0) < THRESHOLD:
            continue
        sig = ("tired", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["tired"] = actor.meters.get("tired", 0.0) + 1
        actor.memes["sleepy"] = actor.memes.get("sleepy", 0.0) + 1
        out.append(f"{actor.label or actor.id} felt their eyes grow heavy.")
    return out


def _r_rumple(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("tired", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in {"head", "torso"}:
                continue
            sig = ("rumple", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["rumpled"] = item.meters.get("rumpled", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got rumpled from too much tossing and turning.")
    return out


CAUSAL_RULES = [_r_tired, _r_rumple]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["screenlight"] = actor.meters.get("screenlight", 0.0) + 1
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    sim.weather = world.weather
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "tired": sim.get(actor.id).meters.get("tired", 0.0) >= THRESHOLD,
        "rumpled": prize.meters.get("rumpled", 0.0) >= THRESHOLD,
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region == "head"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked quiet rooms and warm blankets.")


def loves_forum(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved the forum because every little thread felt like a tiny lantern of words.")
    world.say(f"Tonight, the forum had one more note about {activity.keyword}, and that made {hero.id} want to peek just once more.")


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One bedtime, {hero.id} and {hero.pronoun('possessive')} {parent.label} sat together in {world.setting.place}.")
    world.say(f"The lamp was low, but the screen still glowed with the forum about {activity.keyword}.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} wanted to {activity.verb}, even though the pillows were already waiting.")
    world.say(f"{hero.pronoun().capitalize()} leaned closer, as if one more glance could finish the whole night.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not (pred["tired"] or pred["rumpled"]):
        return False
    world.facts["predicted_tired"] = pred["tired"]
    world.facts["predicted_rumpled"] = pred["rumpled"]
    world.say(f'"If you stay on the forum much longer," {parent.label} said softly, "your {prize.label} will get all rumpled and your eyes will get sleepy."')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiant"] = hero.memes.get("defiant", 0.0) + 1
    world.say(f"{hero.id} heard the warning, but the page still looked brighter than the blanket.")
    world.say(f"{hero.pronoun().capitalize()} reached for one more scroll and whispered, 'Just one more post about {activity.keyword}.'")


def refusal(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(f"{parent.label} offered a gentle compromise: 'Close the forum after this post, and we'll read the bedtime story instead.'")
    world.say(f"But {hero.id} shook their head, and the glow stayed on.")


def end_badly(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.meters["screenlight"] = hero.meters.get("screenlight", 0.0) + 1
    propagate(world, narrate=False)
    hero.memes["sleepy"] = hero.memes.get("sleepy", 0.0) + 1
    world.say(f"At last the room went very quiet, but it was the wrong kind of quiet.")
    world.say(f"{hero.id} was still awake, yawning with sticky eyes, and {hero.pronoun('possessive')} {prize.label} was rumpled from turning and turning.")
    world.say(f"{parent.label} tucked the blanket in anyway, while the little forum glow stayed in {hero.id}'s mind like a stubborn star.")
    world.say(f"The bedtime that should have been soft and smooth ended with a tired sigh and a dark screen.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.memes["curious"] = 1.0 if trait == "curious" else 0.0

    introduce(world, hero)
    loves_forum(world, hero, activity)
    world.say(f"{parent.label} had bought {hero.pronoun('object')} {prize.phrase} because bedtime should feel snug.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, and the soft fabric made the room feel safe.")

    world.para()
    arrives(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    refusal(world, parent, hero, activity)

    world.para()
    end_badly(world, hero, parent, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"forum"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"forum"}),
    "reading_nook": Setting(place="the reading nook", indoor=True, affords={"forum"}),
}

ACTIVITIES = {
    "forum": Activity(
        id="forum",
        verb="read the forum",
        gerund="reading the forum",
        rush="scroll to one more post",
        mess="screenlight",
        soil="too bright",
        zone={"head"},
        weather="night",
        keyword="forum",
        tags={"forum", "night", "screen"},
    ),
    "deuce": Activity(
        id="deuce",
        verb="look up deuce",
        gerund="looking up deuce",
        rush="tap for one more clue about deuce",
        mess="screenlight",
        soil="too bright",
        zone={"head"},
        weather="night",
        keyword="deuce",
        tags={"deuce", "forum", "night"},
    ),
}

PRIZES = {
    "pillow": Prize(label="pillow", phrase="a soft pillow with a blue moon on it", type="pillow", region="head"),
    "blanket": Prize(label="blanket", phrase="a warm blanket with little stars", type="blanket", region="torso"),
}

GEAR = [
    Gear(id="timer", label="a little timer", covers={"head"}, guards={"screenlight"}, prep="set a tiny timer for one post", tail="set the timer and turned off the glow"),
    Gear(id="book", label="a bedtime book", covers={"head", "torso"}, guards={"screenlight"}, prep="put the tablet away and open the bedtime book", tail="picked up the bedtime book instead"),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa"]
BOY_NAMES = ["Theo", "Eli", "Owen", "Finn", "Leo"]
TRAITS = ["curious", "gentle", "sleepy", "quiet"]


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
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "forum": [("What is a forum?", "A forum is a place where people share thoughts, questions, and answers with words.")],
    "deuce": [("What does deuce mean?", "Deuce can mean the number two, or it can be a word people use in some games.")],
    "screen": [("Why can screens keep people awake?", "Screens can keep people awake because their bright light makes the brain feel like it is still daytime.")],
    "night": [("Why do people sleep at night?", "People sleep at night so their bodies and minds can rest and get ready for the next day.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a bedtime story about {hero.id}, a glowing forum, and the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.label}.",
        f'Write a simple bedtime story that includes the words "forum" and "{act.keyword}" and ends in a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the bedtime story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the forum?",
            answer=f"{hero.id} wanted to {act.verb}, even though bedtime was already close.",
        ),
        QAItem(
            question=f"What item was supposed to stay cozy and smooth?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} was supposed to stay cozy and smooth, but the long wakeful night made it rumple.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because the forum's bright glow would make {hero.id} sleepy in the wrong way and leave {prize.label} rumpled.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: {hero.id} stayed up too long, the room went dark, and bedtime was missed.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", activity="forum", prize="pillow", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="reading_nook", activity="deuce", prize="blanket", name="Theo", gender="boy", parent="father", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the bedtime forum move has to threaten a head-or-bedtime prize, but {prize.label} does not fit that pattern.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- affects_head(A), worn_on(P, head).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, screenlight), covers(G, head).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("affects_head", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
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
    ap = argparse.ArgumentParser(description="A bedtime story world about a forum and a bad ending.")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
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
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
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
