#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trumpet_ridiculous_botanic_dialogue_flashback_magic_pirate.py
===============================================================================================

A small pirate-tale story world about a crew, a botanic island, a ridiculous
problem, a trumpet signal, a flashback, and a bit of magic that helps the crew
choose a safe course.

Premise:
- A pirate captain loves exploring a lush botanic island.
- A ridiculous mix-up threatens a prized map and delays the voyage.
- The captain remembers an old flashback about a magical trumpet signal.
- Dialogue and magic together reveal a better route and a calmer ending.

This script follows the Storyweavers contract: it defines a world model, a
story generator, QA generation, and an inline ASP twin for the reasonableness
gate.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "captain"}
        if self.type in female and self.type not in {"pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the botanic island"
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


@dataclass
class MagicTool:
    id: str
    label: str
    prep: str
    tail: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False
        self.weather = "sea-breeze"

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_used = self.flashback_used
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    magic: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"signal"}),
    "garden_island": Setting(place="the botanic island garden", affords={"signal", "explore"}),
}

ACTIVITIES = {
    "signal": Activity(
        id="signal",
        verb="sound the trumpet signal",
        gerund="sounding the trumpet",
        rush="blast the trumpet too loud",
        mess="startled",
        soil="jittery and noisy",
        zone={"ears", "heart"},
        keyword="trumpet",
        tags={"trumpet", "noise"},
    ),
    "explore": Activity(
        id="explore",
        verb="explore the botanic paths",
        gerund="exploring the botanic paths",
        rush="dash through the vines",
        mess="muddy",
        soil="muddy",
        zone={"boots", "legs"},
        keyword="botanic",
        tags={"botanic", "plants"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a folded sea map", type="map", region="hands"),
    "hat": Prize(label="hat", phrase="a fine captain's hat", type="hat", region="head"),
}

MAGIC = {
    "wind_charm": MagicTool(
        id="wind_charm",
        label="a wind charm",
        prep="hold up a wind charm",
        tail="held the charm to the breeze",
        effect="the breeze softened the noise",
        tags={"magic", "wind"},
    ),
    "green_lantern": MagicTool(
        id="green_lantern",
        label="a green lantern",
        prep="light a green lantern",
        tail="lit the lantern and watched the path glow",
        effect="the path glowed safe and clear",
        tags={"magic", "light"},
    ),
}

NAMES = ["Mara", "Finn", "Rory", "Mina", "Jax", "Nell"]
TRAITS = ["bold", "curious", "cheerful", "stubborn", "brave"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return (activity.id == "signal" and prize.region in {"hands", "head"}) or (
        activity.id == "explore" and prize.region in {"hands", "head"}
    )


def select_magic(activity: Activity, prize: Prize) -> Optional[MagicTool]:
    if activity.id == "signal":
        return MAGIC["wind_charm"]
    if activity.id == "explore":
        return MAGIC["green_lantern"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_magic(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def setting_detail(setting: Setting, activity: Activity) -> str:
    if activity.id == "explore":
        return "Palm leaves leaned over the path, and bright flowers nodded in the salt wind."
    return "The harbor smelled of ropes, gulls, and warm boardwalk wood."


def predict_distress(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"distressed": prize.memes.get("distress", 0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    if narrate:
        world.say(f"{actor.id} {activity.gerund}.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} little pirate who loved good maps and strange islands.")


def loves_island(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} along the botanic shore, where the leaves shone like green flags.")


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"On board, {hero.id} kept {hero.pronoun('possessive')} {prize.label} close, because it showed the way home.")
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity, companion: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {companion.label} reached {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def dialogue_want(world: World, hero: Entity, companion: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f'"Can we {activity.verb} now?" {hero.id} asked.')
    world.say(f'"Aye," said {companion.id}, "but mind {hero.pronoun("possessive")} {prize.label}."')


def flashback(world: World, hero: Entity, companion: Entity, activity: Activity, magic: MagicTool) -> None:
    world.flashback_used = True
    world.say("That reminder sparked a flashback.")
    world.say(
        f"Years ago, when a storm had fooled the crew, {companion.id} had whispered, "
        f'"When the trumpet sounds wrong, use magic, not more noise."'
    )
    world.say(f"{hero.id} remembered it clearly, as if the old lesson had just sailed back aboard.")
    world.facts["magic"] = magic


def tension(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"{hero.id} nearly rushed ahead, but {hero.pronoun('possessive')} {prize.label} began to feel too precious for a wild blast.")
    if predict_distress(world, hero, activity, prize.id)["distressed"]:
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def offer_magic(world: World, companion: Entity, hero: Entity, magic: MagicTool) -> None:
    world.say(f'"Then let us {magic.prep}," said {companion.id}.')
    world.say(f"The little charm answered the breeze, and {magic.effect}.")


def resolve(world: World, hero: Entity, companion: Entity, activity: Activity, prize: Entity, magic: MagicTool) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(f'{hero.id} grinned. "That is the way!"')
    world.say(
        f"Together they followed the safer plan: {magic.tail}, and then {hero.id} could "
        f"{activity.verb} without jostling {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(f"By the end, the botanic island felt friendly, and the {prize.label} still pointed the crew toward home.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, magic: MagicTool,
         hero_name: str, hero_type: str, hero_traits: list[str], companion_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits))
    companion = world.add(Entity(id="OldSalt", kind="character", type=companion_type, label="old salt"))
    prize = world.add(Entity(id="map", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    introduce(world, hero)
    loves_island(world, hero, activity)
    setup_prize(world, hero, prize)
    world.para()
    arrive(world, hero, companion, activity)
    dialogue_want(world, hero, companion, activity, prize)
    tension(world, hero, activity, prize)
    flashback(world, hero, companion, activity, magic)
    world.para()
    offer_magic(world, companion, hero, magic)
    resolve(world, hero, companion, activity, prize, magic)
    world.facts.update(hero=hero, companion=companion, prize=prize, activity=activity, magic=magic, setting=setting)
    return world


KNOWLEDGE = {
    "trumpet": [
        (
            "What is a trumpet?",
            "A trumpet is a brass musical instrument that makes a bright, loud sound when someone blows into it.",
        )
    ],
    "botanic": [
        (
            "What does botanic mean?",
            "Botanic means connected to plants and gardens, especially ones with many different kinds of growing things.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something wonderful or unusual that helps characters do things they could not do by ordinary means.",
        )
    ],
    "dialogue": [
        (
            "What is dialogue?",
            "Dialogue is when characters speak to each other in a story.",
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a part of a story that shows something that happened earlier, so the character can remember it now.",
        )
    ],
    "ridiculous": [
        (
            "What does ridiculous mean?",
            "Ridiculous means silly in a surprising way, or so odd that it makes people laugh.",
        )
    ],
}


@dataclass
class ASPState:
    name: str
    place: str
    activity: str
    prize: str


ASP_RULES = r"""
at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_magic(A,P) :- at_risk(A,P), magic_tool(M), helps(M,A,P).
valid_story(Place,A,P) :- afford(Place,A), at_risk(A,P), has_magic(A,P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("afford", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for mid, mg in MAGIC.items():
        lines.append(asp.fact("magic_tool", mid))
        for tag in sorted(mg.tags):
            lines.append(asp.fact("helps", mid, "signal" if tag == "wind" else "explore"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_asp_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a young child that includes the word "{f["activity"].keyword}" and a magical helper.',
        f"Tell a story where {f['hero'].id} uses dialogue and a flashback to choose a safer way to {f['activity'].verb}.",
        f"Make a botanic island adventure with a trumpet, a ridiculous problem, and a gentle magical fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, companion, prize, activity, magic = f["hero"], f["companion"], f["prize"], f["activity"], f["magic"]
    return [
        QAItem(
            question=f"Why did {hero.id} hesitate before {activity.verb}?",
            answer=f"{hero.id} hesitated because {hero.pronoun('possessive')} {prize.label} was important, and a loud trumpet blast could make the moment too wild.",
        ),
        QAItem(
            question="What did the flashback remind the crew to do?",
            answer=f"The flashback reminded the crew to use magic instead of making more noise, so they could keep the {prize.label} safe.",
        ),
        QAItem(
            question=f"How did {magic.label} help the pirate plan?",
            answer=f"{magic.label.capitalize()} helped by softening the trouble and making a safer path, so {hero.id} could keep exploring without ruining {hero.pronoun('possessive')} {prize.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["magic"].tags) | {"dialogue", "flashback", "ridiculous"}
    out: list[QAItem] = []
    for key in ["trumpet", "botanic", "magic", "dialogue", "flashback", "ridiculous"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_island", activity="explore", prize="map", magic="green_lantern", name="Mara", gender="girl", companion="pirate", trait="curious"),
    StoryParams(place="harbor", activity="signal", prize="hat", magic="wind_charm", name="Finn", gender="boy", companion="pirate", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not create a useful pirate problem for a {prize.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with trumpet, ridiculous trouble, botanic paths, dialogue, flashback, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["pirate"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    filtered = [c for c in combos if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity) and (args.prize is None or c[2] == args.prize)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(filtered)
    magic = args.magic or ("green_lantern" if activity == "explore" else "wind_charm")
    if activity == "explore" and magic != "green_lantern":
        raise StoryError("(No story: the botanic path needs the green lantern magic.)")
    if activity == "signal" and magic != "wind_charm":
        raise StoryError("(No story: the trumpet tale needs the wind charm magic.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    companion = args.companion or "pirate"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, magic=magic, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], MAGIC[params.magic], params.name, params.gender, [params.trait, "stubborn"], params.companion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program()), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, act, prize in combos:
            print(f"  {place:14} {act:10} {prize:6}")
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
