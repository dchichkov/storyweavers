#!/usr/bin/env python3
"""
storyworlds/worlds/boulevard_regulate_deadly_sound_effects_slice_of.py
======================================================================

A small slice-of-life story world about a child who loves making sound effects
on a boulevard, but learns to regulate the volume so a sleeping sibling can rest.

Initial seed tale:
---
On a bright afternoon, a child on the boulevard played with toy cars and made
huge sound effects: VROOOM, SCREECH, and BANG! The child thought the sounds were
funny and exciting, almost deadly dramatic, like a pretend action movie.

But inside the apartment, the baby's nap was getting shaky. The parent asked the
child to regulate the sound effects so the baby could sleep. The child tried a
quieter game, using a pillow for soft thumps and a paper cup for tiny engine
noises. Soon the boulevard still looked lively, but the apartment stayed calm,
and the baby kept sleeping.

World model:
---
- A hero has a meter for noise and a meme for excitement.
- The boulevard carries sound outward, so loud play can reach the sleeping baby.
- Regulating the effects means swapping big noisy props for soft ones and moving
  to a better spot.
- The story resolves when the child keeps the fun but lowers the volume.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    covers: set[str] = field(default_factory=set)
    protective: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    loudness: float
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    quiet: float


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "boulevard": Setting(place="the boulevard", indoors=False, affords={"whoosh", "vroom", "stomp"}),
    "balcony": Setting(place="the balcony", indoors=False, affords={"whoosh", "vroom"}),
    "living_room": Setting(place="the living room", indoors=True, affords={"whoosh", "vroom", "stomp"}),
}

ACTIVITIES = {
    "whoosh": Activity(
        id="whoosh",
        verb="make whooshing sound effects",
        gerund="whooshing sound effects",
        rush="wave faster and make bigger whooshes",
        noise="whoosh",
        loudness=1.0,
        keyword="whoosh",
        tags={"sound", "play"},
    ),
    "vroom": Activity(
        id="vroom",
        verb="do car-race sound effects",
        gerund="doing car-race sound effects",
        rush="push the cars together and shout vroom",
        noise="vroom",
        loudness=1.2,
        keyword="vroom",
        tags={"sound", "car"},
    ),
    "stomp": Activity(
        id="stomp",
        verb="make monster stomp sound effects",
        gerund="making monster stomp sound effects",
        rush="stomp harder and roar louder",
        noise="BANG",
        loudness=1.4,
        keyword="stomp",
        tags={"sound", "monster"},
    ),
}

GEAR = [
    Gear(
        id="pillow",
        label="a soft pillow",
        prep="bring a soft pillow over and use it for quiet thumps",
        tail="used the pillow for little thumps",
        quiet=0.8,
    ),
    Gear(
        id="paper_cup",
        label="a paper cup",
        prep="turn a paper cup into a tiny megaphone and then whisper into it",
        tail="whispered tiny engine noises into the paper cup",
        quiet=0.6,
    ),
    Gear(
        id="blanket",
        label="a folded blanket",
        prep="spread out a folded blanket to muffle the noise",
        tail="kept the sound under the blanket",
        quiet=0.7,
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Max", "Eli", "Noah", "Theo", "Finn", "Ben"]
TRAITS = ["playful", "curious", "spunky", "bright", "lively"]


def risk_noise(activity: Activity, setting: Setting) -> bool:
    return activity.loudness >= 1.0 and (setting.place == "the boulevard" or setting.indoors)


def select_gear(activity: Activity) -> Optional[Gear]:
    if activity.id == "stomp":
        return GEAR[0]
    if activity.id == "vroom":
        return GEAR[1]
    if activity.id == "whoosh":
        return GEAR[2]
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if risk_noise(act, setting) and select_gear(act):
                combos.append((place, act_id))
    return combos


def _do_sound(world: World, actor: Entity, activity: Activity, volume: float, narrate: bool = True) -> None:
    actor.meters["noise"] = actor.meters.get("noise", 0.0) + volume
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} made {activity.noise} sound effects.")


def predict_reach(world: World, actor: Entity, activity: Activity, baby_id: str) -> dict:
    sim = world.copy()
    _do_sound(sim, sim.get(actor.id), activity, activity.loudness, narrate=False)
    baby = sim.get(baby_id)
    return {"woke": sim.get(actor.id).meters.get("noise", 0.0) >= 1.0 and baby.memes.get("sleep", 0.0) < 1.0}


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    baby = world.add(Entity(id="Baby", kind="character", type="baby", label="the baby", memes={"sleep": 1.0}))
    prop = world.add(Entity(id="Prop", type="thing", label="toy cars", plural=True, owner=hero.id))

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved sound effects.")
    world.say(f"{hero.id} especially loved {activity.gerund} with {prop.label} on {setting.place}.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} watched from nearby, smiling at the play.")

    world.para()
    world.say(f"One afternoon, {hero.id} went to {setting.place} and started {activity.gerund}.")
    world.say(f"The sounds of {activity.noise}, {activity.noise}, and {activity.noise} bounced down the boulevard.")
    pred = predict_reach(world, hero, activity, baby.id)
    world.facts["predicted_wake"] = pred["woke"]
    if pred["woke"]:
        world.say(f"Inside, the baby was trying to sleep, so the loud game felt a little too {activity.keyword}.")
    world.say(f"{hero.id} wanted to keep playing, but {hero.pronoun('possessive')} {parent.label_word} raised a gentle hand.")

    world.para()
    gear = select_gear(activity)
    if gear is None:
        raise StoryError("No gentle way to regulate that sound effect was found.")
    world.say(f'"Can we regulate the sound effects?" {parent.pronoun("subject").capitalize()} asked. "Let\'s use {gear.label}."')
    world.say(f"{hero.id} tried it. {gear.prep}.")
    _do_sound(world, hero, activity, activity.loudness * gear.quiet, narrate=False)
    world.say(f"Now the noises stayed small and playful, more like {gear.tail} than a big scene.")
    world.say(f"{hero.id} grinned, because the boulevard still had fun in it, but the baby kept sleeping.")

    world.facts.update(hero=hero, parent=parent, baby=baby, activity=activity, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short slice-of-life story about a child named {hero.id} who loves "{act.keyword}" sound effects on {world.setting.place}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label_word} asks them to regulate the noise for the baby.",
        f'Write a simple story with the word "{act.keyword}" that ends with quieter play and a calm baby.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, baby, act = f["hero"], f["parent"], f["baby"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do on {world.setting.place}?",
            answer=f"{hero.id} loved {act.gerund} and making playful sound effects while playing with toy cars.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} ask {hero.id} to regulate the sound effects?",
            answer=f"{parent.label_word} was worried the loud noises might wake the baby who was trying to sleep.",
        ),
        QAItem(
            question=f"What did {hero.id} use to make the sounds quieter?",
            answer=f"{hero.id} used {f['gear'].label} so the sound effects stayed soft and gentle.",
        ),
        QAItem(
            question=f"How did the story end for the baby?",
            answer=f"The baby kept sleeping, and the boulevard play stayed calm and happy.",
        ),
    ]
    if world.facts.get("predicted_wake"):
        qa.append(
            QAItem(
                question=f"What could have happened if {hero.id} kept the noisy game going?",
                answer=f"The baby could have woken up, because the original sound effects were too loud for quiet sleep.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act: Activity = f["activity"]
    return [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises people make to match a game, a story, or a pretend scene.",
        ),
        QAItem(
            question="What does regulate mean?",
            answer="To regulate something means to keep it under control or make it fit a rule or a safe limit.",
        ),
        QAItem(
            question="Why can loud sounds be a problem for sleeping?",
            answer="Loud sounds can wake someone who is trying to rest, because sleeping people are sensitive to noise.",
        ),
        QAItem(
            question="What is a boulevard?",
            answer="A boulevard is a wide street with room for walking, cars, and the everyday bustle of a neighborhood.",
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story shows an ordinary moment from daily life, like playing, talking, or solving a small problem.",
        ),
        QAItem(
            question=f"Why might a child like {act.keyword} sound effects?",
            answer="They can make pretend play feel exciting, funny, and full of movement.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, place: str) -> str:
    return f"(No story: {activity.verb} at {place} does not create a reasonable noise problem in this world.)"


ASP_RULES = r"""
noise_risk(P, A) :- place(P), activity(A), loud(A), sensitive(P).
needs_regulation(P, A) :- noise_risk(P, A).
compatible_gear(A, G) :- activity(A), gear(G), quiets(G, A).
valid_story(P, A) :- needs_regulation(P, A), compatible_gear(A, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("sensitive", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.loudness >= 1.0:
            lines.append(asp.fact("loud", aid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for aid, a in ACTIVITIES.items():
            if a.id == "stomp" and g.id == "pillow":
                lines.append(asp.fact("quiets", g.id, aid))
            if a.id == "vroom" and g.id == "paper_cup":
                lines.append(asp.fact("quiets", g.id, aid))
            if a.id == "whoosh" and g.id == "blanket":
                lines.append(asp.fact("quiets", g.id, aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life boulevard story with regulated sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    place = args.place or rng.choice(list(SETTINGS))
    setting = SETTINGS[place]
    acts = [a for a in setting.affords if (not args.activity or a == args.activity)]
    if not acts:
        raise StoryError("(No valid combination matches the given options.)")
    activity = rng.choice(sorted(acts))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="boulevard", activity="vroom", name="Mia", gender="girl", parent="mother", trait="playful"),
    StoryParams(place="balcony", activity="whoosh", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="living_room", activity="stomp", name="Nora", gender="girl", parent="mother", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, act in combos:
            print(f"  {place:12} {act}")
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
