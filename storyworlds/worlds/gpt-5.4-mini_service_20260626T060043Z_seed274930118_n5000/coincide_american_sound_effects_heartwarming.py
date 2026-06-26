#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coincide_american_sound_effects_heartwarming.py
===============================================================================================================

A small heartwarming storyworld about a child making sound effects for an
American-style performance, where timing matters and gentle teamwork can keep a
sleeping listener peaceful.

Seed idea:
- A child loves making sound effects.
- The child wants the sounds to coincide with a cheerful American radio play
  or stage show.
- A caring parent or grandparent worries about waking a sleeping baby, pet, or
  neighbor.
- A soft, clever compromise lets everyone smile.

The world is designed to be child-facing, concrete, and state-driven rather than
a frozen paragraph with swapped nouns.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["loud", "gentle", "mess", "tidy"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "worry", "pride", "cooperation", "patience", "disappointment"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "sister"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the living room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    weather: str = ""
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_stage: str = ""

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.sound_stage = self.sound_stage
        clone.paragraphs = [[]]
        return clone


def _r_loud(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["loud"] < THRESHOLD:
            continue
        sig = ("loud", actor.id, world.sound_stage)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.entities.values():
            if e.kind != "character" and e.owner == actor.id and e.region == "ears":
                pass
        out.append("The sound grew louder.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    baby = next((e for e in world.entities.values() if e.type == "baby"), None)
    if not baby:
        return out
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", actor.id, baby.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} looked toward the sleeping baby and frowned a little.")
    return out


CAUSAL_RULES = [
    _r_loud,
    _r_worry,
]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"ears", "room"} and activity.id in {"thunder", "train", "drums", "horse", "fireworks"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.keyword in gear.guards:
            return gear
    return None


def predict_disturbance(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["loud"] += 1
    return {"disturbed": prize_at_risk(activity, sim.get(prize_id))}


def activity_detail(activity: Activity) -> str:
    return {
        "clap": "The claps could land right on the beat.",
        "rain": "The drops could patter like a tiny drumline.",
        "horse": "The hoofbeats could sound just like a parade.",
        "drums": "The drum sounds could roll like thunder.",
        "train": "The chugging could puff like a little engine song.",
        "fireworks": "The pops could crackle like a holiday sky.",
    }.get(activity.id, "It had its own cheerful rhythm.")


def choose_sound_stage(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"{setting.place} had a small corner that was perfect for sound effects."
    return f"{setting.place} had plenty of room for a sound scene."


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved making sound effects.")


def love_world(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {activity_detail(activity)}"
    )


def setup_show(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} "
        f"were getting ready for an American show at {world.setting.place}."
    )
    world.say(
        f"{hero.id} wanted the sound effects to {activity.id} at just the right moment, so they would coincide with the big scene."
    )
    prize.worn_by = prize.id
    world.say(f"Nearby, {prize.phrase} was sleeping softly, and everyone wanted to keep {prize.pronoun('object') if hasattr(prize, 'pronoun') else 'it'} peaceful.")


def worry(world: World, parent: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_disturbance(world, world.facts["hero"], activity, prize.id)
    if not pred["disturbed"]:
        return False
    parent.memes["worry"] += 1
    world.say(
        f'"That might wake the sleeping {prize.label}," {parent.id} said gently. '
        f'"Could we make the sound effects in a softer way?"'
    )
    return True


def try_again(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} nodded and tried again, this time with a softer plan."
    )
    world.say(
        f"{hero.id} still wanted the sounds to coincide with the scene, but not at the cost of anyone's rest."
    )


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    if predict_disturbance(world, hero, activity, prize.id)["disturbed"]:
        gear_ent.worn_by = None
        del world.entities[gear_ent.id]
        return None
    world.say(
        f'{parent.id} smiled and said, "{gear.prep}."'
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["cooperation"] += 1
    parent.memes["pride"] += 1
    world.say(
        f"{hero.id}'s face brightened. {hero.id} loved the new plan and hugged {hero.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f"They {gear.tail}. Soon the sounds were soft, the timing still fit the scene, and the sleeping {prize.label} stayed calm."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Maya", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "curious", "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(id="baby", kind="character", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=parent.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.sound_stage = choose_sound_stage(setting, activity)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)

    intro(world, hero)
    love_world(world, hero, activity)
    setup_show(world, hero, parent, prize, activity)
    world.para()
    world.say(world.sound_stage)
    world.say(f"{hero.id} practiced the effect {activity.verb} while watching for the perfect moment.")
    worry(world, parent, activity, prize)
    try_again(world, hero, activity)
    world.para()
    gear = offer_gear(world, parent, hero, activity, prize)
    if gear:
        resolve(world, hero, parent, prize, activity, gear)
    world.facts["gear"] = gear
    world.facts["resolved"] = gear is not None
    return world


SETTINGS = {
    "living_room": Setting(place="the living room", indoor=True, affords={"clap", "rain", "train"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"drums", "clap"}),
    "back_porch": Setting(place="the back porch", indoor=False, affords={"horse", "rain"}),
    "school_stage": Setting(place="the school stage", indoor=True, affords={"fireworks", "train", "drums"}),
}

ACTIVITIES = {
    "clap": Activity(id="clap", verb="make soft claps", gerund="making soft claps", rush="clap too loud", effect="a tidy clap", keyword="clap", tags={"sound", "soft"}),
    "rain": Activity(id="rain", verb="make rain sounds", gerund="making rain sounds", rush="tap the pan too hard", effect="a pattering rain", keyword="rain", tags={"sound", "gentle"}),
    "horse": Activity(id="horse", verb="make hoofbeat sounds", gerund="making hoofbeat sounds", rush="thump the board", effect="a parade of hoofbeats", keyword="horse", tags={"sound", "american"}),
    "drums": Activity(id="drums", verb="make drumrolls", gerund="making drumrolls", rush="bang the pot lids", effect="a warm drum roll", keyword="drums", tags={"sound", "american"}),
    "train": Activity(id="train", verb="make train sounds", gerund="making train sounds", rush="shout the whistle", effect="a cheerful engine puff", keyword="train", tags={"sound", "american"}),
    "fireworks": Activity(id="fireworks", verb="make fireworks sounds", gerund="making fireworks sounds", rush="pop too sharply", effect="little sparkling pops", keyword="fireworks", tags={"sound", "american"}),
}

PRIZES = {
    "baby": Prize(label="baby", phrase="a sleepy baby", type="baby", region="ears"),
    "cat": Prize(label="cat", phrase="a napping cat", type="cat", region="ears"),
    "neighbor": Prize(label="neighbor", phrase="a tired neighbor", type="neighbor", region="ears"),
}

GEAR = [
    Gear(id="blanket_booth", label="a blanket booth", covers={"ears"}, guards={"rain", "train"}, prep="Let's build a blanket booth and keep the sound small", tail="lifted the blanket booth higher and worked inside it"),
    Gear(id="sock_mufflers", label="sock mufflers", covers={"ears"}, guards={"clap", "drums"}, prep="Let's wrap the pots in socks so the sounds stay soft", tail="wrapped the pots and made the gentlest noises"),
    Gear(id="pillow_wall", label="a pillow wall", covers={"ears"}, guards={"horse", "fireworks"}, prep="Let's set up a pillow wall before we start", tail="played behind the pillow wall and kept the room calm"),
]

GIRL_NAMES = ["Maya", "Nina", "Lena", "Ivy", "Lucy", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Theo", "Leo", "Max"]
TRAITS = ["kind", "curious", "gentle", "cheerful", "brave"]


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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.phrase}, "
        f"so there is no real reason for a worry-and-compromise tale here.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for this prize.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about a child named {hero.id} making "{act.keyword}" sound effects for an American show.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.id} worries about {prize.phrase}.",
        f"Write a cozy story in which the sounds and the scene coincide, but everyone stays kind and careful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do for the American show?",
            answer=f"{hero.id} loved {act.gerund}. {hero.id} wanted the sounds to coincide with the big moment in the show."
        ),
        QAItem(
            question=f"Why did {parent.id} worry about {prize.phrase}?",
            answer=f"{parent.id} worried because the sounds could wake {prize.phrase}. {parent.id} wanted the room to stay peaceful."
        ),
        QAItem(
            question=f"How did {hero.id} respond when asked to be softer?",
            answer=f"{hero.id} listened, tried a gentler plan, and kept working with {parent.id} instead of getting upset."
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"What helped {hero.id} keep making sound effects without disturbing {prize.label}?",
                answer=f"{gear.label} helped because it softened the noise. That let {hero.id} keep the timing right while {prize.phrase} stayed calm."
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.id} and {parent.id}?",
                answer=f"They ended smiling together, with the sound effects ready and the little listener still sleeping peacefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    knowledge = {
        "sound": [
            ("What are sound effects?", "Sound effects are made sounds that help tell a story, like rain, footsteps, or a train whistle."),
        ],
        "american": [
            ("What does American mean?", "American usually means something from the United States of America, like an American song or parade."),
        ],
        "soft": [
            ("Why is soft sound helpful?", "Soft sound is helpful because it is less likely to bother someone who is resting."),
        ],
        "gentle": [
            ("What does gentle mean?", "Gentle means careful and not rough, so it feels kind and safe."),
        ],
        "blanket_booth": [
            ("Why can blankets help with noise?", "Blankets can help because they absorb some sound and make a room quieter."),
        ],
        "sock_mufflers": [
            ("Why wrap pots in socks?", "Wrapping pots in socks makes them make softer sounds when you tap them."),
        ],
        "pillow_wall": [
            ("What does a pillow wall do?", "A pillow wall can block some sound and make a play area quieter."),
        ],
    }
    order = ["sound", "american", "soft", "gentle", "blanket_booth", "sock_mufflers", "pillow_wall"]
    for tag in order:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in knowledge[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", activity="clap", prize="baby", name="Maya", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="kitchen", activity="drums", prize="cat", name="Noah", gender="boy", parent="father", trait="kind"),
    StoryParams(place="school_stage", activity="train", prize="neighbor", name="Ivy", gender="girl", parent="mother", trait="cheerful"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), risky_sound(A), needs_quiet(P).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), guards(G, A), covers(G, ear_zone).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        if aid in {"rain", "train", "drums", "horse", "fireworks"}:
            lines.append(asp.fact("risky_sound", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("needs_quiet", pid))
        lines.append(asp.fact("ear_zone"))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    ap = argparse.ArgumentParser(description="Heartwarming sound-effects storyworld.")
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
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
            print(f"  {place:12} {act:10} {prize:10}  [{', '.join(genders)}]")
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
