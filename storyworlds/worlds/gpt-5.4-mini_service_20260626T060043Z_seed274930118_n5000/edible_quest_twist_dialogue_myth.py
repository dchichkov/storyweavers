#!/usr/bin/env python3
"""
storyworlds/worlds/edible_quest_twist_dialogue_myth.py
=======================================================

A standalone storyworld for a small mythic quest: a child or young hero seeks
an edible treasure, meets a twist, and reaches a spoken resolution.

This world is deliberately compact:
- one questing hero
- one mythic setting
- one edible prize
- one twist that changes the path
- one dialogue-led turn that resolves the trouble

The prose is driven by a tiny simulation model with physical meters and emotional
memes. The hero's quest can change the world state, and the ending proves what
changed.
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
    edible: bool = False
    sacred: bool = False
    stolen: bool = False
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    epithet: str
    path: str
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    edible: bool
    wonder: str
    location: str


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    change: str
    remedy: str
    effect: str
    costs: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest_item: str
    twist: str
    name: str
    gender: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.twist_seen = False

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.twist_seen = self.twist_seen
        return clone


SETTINGS = {
    "grove": Setting(
        place="the moonlit grove",
        epithet="where old branches sang",
        path="the silver path",
        affords={"quest", "dialogue", "twist"},
    ),
    "mountain": Setting(
        place="the high mountain shrine",
        epithet="where snow kept secrets",
        path="the wind-cut steps",
        affords={"quest", "dialogue", "twist"},
    ),
    "river": Setting(
        place="the wide river ford",
        epithet="where reeds bowed like listeners",
        path="the stone crossing",
        affords={"quest", "dialogue", "twist"},
    ),
}

QUEST_ITEMS = {
    "honeycake": QuestItem(
        id="honeycake",
        label="honeycake",
        phrase="a round honeycake glazed with gold",
        edible=True,
        wonder="sweet as a blessing",
        location="in the cedar shrine",
    ),
    "moonberries": QuestItem(
        id="moonberries",
        label="moonberries",
        phrase="a small bowl of shining moonberries",
        edible=True,
        wonder="bright as stars in a cup",
        location="beneath the elder tree",
    ),
    "bread": QuestItem(
        id="bread",
        label="bread",
        phrase="a warm loaf of temple bread",
        edible=True,
        wonder="soft as cloud-flesh",
        location="on a stone altar",
    ),
    "stonefruit": QuestItem(
        id="stonefruit",
        label="stonefruit",
        phrase="a stonefruit with a thick shell",
        edible=True,
        wonder="kept safe by its own hard shell",
        location="behind the shrine gate",
    ),
}

TWISTS = {
    "guard": Twist(
        id="guard",
        label="a watchful gatekeeper",
        reveal="the keeper only guarded the feast, not the hero",
        change="the gatekeeper tested the hero with a question",
        remedy="answering with honesty and respect",
        effect="allowed the hero to pass",
        costs=set(),
    ),
    "storm": Twist(
        id="storm",
        label="a sudden storm",
        reveal="the silver path vanished under wind and rain",
        change="the hero had to shelter and wait",
        remedy="sharing the last dry cloak and a kind word",
        effect="made the way safe again",
        costs={"wet"},
    ),
    "riddle": Twist(
        id="riddle",
        label="a speaking raven",
        reveal="the raven would not move unless it heard a promise",
        change="the hero had to speak a vow aloud",
        remedy="making a true promise",
        effect="opened the hidden door",
        costs=set(),
    ),
    "share": Twist(
        id="share",
        label="a hungry child by the road",
        reveal="the treasure was meant to be shared before it was kept",
        change="the hero had to choose between haste and kindness",
        remedy="offering a portion first",
        effect="turned the quest into a feast",
        costs={"hunger"},
    ),
}

GENDERS = {"girl", "boy"}
GUIDES = ["mother", "father", "grandmother", "grandfather", "sibling"]
NAMES = {
    "girl": ["Mira", "Ila", "Nora", "Tara", "Lina", "Sera"],
    "boy": ["Arin", "Koa", "Niko", "Jorin", "Tavi", "Rian"],
}
TRAITS = ["brave", "gentle", "curious", "bold", "patient"]


def _hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES[gender])


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUEST_ITEMS:
            for t in TWISTS:
                combos.append((s, q, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic edible quest storyworld with a twist and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--guide", choices=GUIDES)
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
    if args.setting and args.quest_item:
        if not QUEST_ITEMS[args.quest_item].edible:
            raise StoryError("The quest item must be edible.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest_item is None or c[1] == args.quest_item)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest_item, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or _hero_name(gender, rng)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(setting=setting, quest_item=quest_item, twist=twist, name=name, gender=gender, guide=guide)


def _do_quest(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1
    item.carried_by = hero.id
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1


def _trigger_twist(world: World, hero: Entity, twist: Twist, item: Entity) -> None:
    if twist.id in world.fired:
        return
    world.fired.add((twist.id, hero.id))
    world.twist_seen = True
    if "wet" in twist.costs:
        hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1
    if "hunger" in twist.costs:
        hero.memes["compassion"] = hero.memes.get("compassion", 0.0) + 1
    world.say(f"Then {twist.label} came upon the path, and {twist.reveal}.")
    world.say(f"The twist changed the road, because {twist.change}.")


def tell(setting: Setting, item_cfg: QuestItem, twist_cfg: Twist,
         hero_name: str, gender: str, guide_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    guide = world.add(Entity(id="guide", kind="character", type=guide_role, label=f"the {guide_role}"))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="food",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        edible=item_cfg.edible,
        sacred=True,
    ))

    trait = "brave"
    world.say(
        f"Long ago, in {setting.place}, there lived {hero_name}, a {trait} young {gender} who loved stories of old gods and hidden feasts."
    )
    world.say(
        f"One dawn, {guide.label} pointed down {setting.path} and said, "
        f"\"If you want the blessing, you must bring back {item_cfg.phrase}.\""
    )
    world.say(
        f"{hero_name} bowed and took the quest, because the treasure was {item_cfg.wonder} and the journey felt like destiny."
    )

    world.para()
    world.say(f"{hero_name} followed {setting.path} toward {item_cfg.location}, with {guide.label} calling softly after {hero.pronoun('object')}.")
    _do_quest(world, hero, item)
    world.say(f"The prize waited there: {item_cfg.phrase}. It was truly edible, and its scent made the air feel kind.")

    _trigger_twist(world, hero, twist_cfg, item)

    world.para()
    if twist_cfg.id == "guard":
        world.say(f"A gatekeeper blocked the way and asked, \"Why should I let a seeker take what the shrine has kept?\"")
        world.say(f"{hero_name} answered, \"Because I will carry it home with care and share it with the people who need it.\"")
        world.say(f"The gatekeeper smiled, and {twist_cfg.remedy} {twist_cfg.effect}.")
    elif twist_cfg.id == "storm":
        world.say(f"{hero_name} and {guide.label} ducked beneath a stone awning while rain drummed on the leaves.")
        world.say(f"{guide.label.capitalize()} said, \"Wait. A true quest has patience in it.\"")
        world.say(f"{hero_name} shared the dry cloak, and {twist_cfg.remedy} {twist_cfg.effect}.")
    elif twist_cfg.id == "riddle":
        world.say(f"A raven sat on the altar and croaked, \"What belongs to the hand, yet is made stronger when given away?\"")
        world.say(f"{hero_name} said, \"A gift.\"")
        world.say(f"The raven bowed its black head, and {twist_cfg.remedy} {twist_cfg.effect}.")
    else:
        world.say(f"By the roadside, a smaller child looked up with hungry eyes.")
        world.say(f"{hero_name} broke the loaf in two and said, \"You may have the first piece.\"")
        world.say(f"That was the turning, and {twist_cfg.remedy} {twist_cfg.effect}.")

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    item.owner = hero.id
    world.say(
        f"At last {hero_name} returned by {setting.epithet}, carrying {item_cfg.phrase} home. "
        f"The quest had changed from a lonely errand into a spoken promise."
    )
    world.say(
        f"{guide.label.capitalize()} laughed, and {hero_name} placed the edible treasure on the hearth, "
        f"ready to be shared."
    )

    world.facts.update(hero=hero, guide=guide, item=item, item_cfg=item_cfg, twist=twist_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for children about {f["hero"].id} seeking {f["item_cfg"].label} in {f["setting"].place}.',
        f'Tell a gentle quest story with dialogue, a twist, and an edible treasure called {f["item_cfg"].phrase}.',
        f'Write a myth-style story where a seeker speaks with a guide, faces {f["twist"].label}, and brings home something edible.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    item_cfg = f["item_cfg"]
    twist = f["twist"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for in {setting.place}?",
            answer=f"{hero.id} was looking for {item_cfg.phrase}, which was an edible treasure from the mythic place.",
        ),
        QAItem(
            question=f"Who gave {hero.id} the quest?",
            answer=f"The quest came from {guide.label}, who pointed the hero toward the sacred path.",
        ),
        QAItem(
            question=f"What changed the journey during the search?",
            answer=f"The journey turned when {twist.label} appeared and changed the road for {hero.id}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} came home with the edible treasure and the quest became a promise to share it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does edible mean?",
            answer="Edible means safe to eat.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey done to find something important or to complete a hard task.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story go in a new direction.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
        QAItem(
            question="Why do myths often feel grand?",
            answer="Myths often feel grand because they talk about brave people, old places, and powerful changes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.edible:
            bits.append("edible=True")
        if e.sacred:
            bits.append("sacred=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
quest_item(I) :- quest_fact(I), edible_fact(I).
twist(T) :- twist_fact(T).

valid_story(S, I, T) :- setting(S), quest_item(I), twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for iid, item in QUEST_ITEMS.items():
        lines.append(asp.fact("quest_fact", iid))
        if item.edible:
            lines.append(asp.fact("edible_fact", iid))
    for tid in TWISTS:
        lines.append(asp.fact("twist_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


CURATED = [
    StoryParams(setting="grove", quest_item="honeycake", twist="guard", name="Mira", gender="girl", guide="grandmother"),
    StoryParams(setting="mountain", quest_item="bread", twist="riddle", name="Arin", gender="boy", guide="father"),
    StoryParams(setting="river", quest_item="moonberries", twist="share", name="Lina", gender="girl", guide="mother"),
]


def explain_rejection() -> str:
    return "The requested story does not fit the mythic edible quest pattern."


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    item = QUEST_ITEMS[params.quest_item]
    twist = TWISTS[params.twist]
    world = tell(setting, item, twist, params.name, params.gender, params.guide)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest_item, twist) combos:\n")
        for s, i, t in combos:
            print(f"  {s:10} {i:12} {t}")
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
            rng = random.Random(seed)
            try:
                combos = [c for c in valid_combos()
                          if (args.setting is None or c[0] == args.setting)
                          and (args.quest_item is None or c[1] == args.quest_item)
                          and (args.twist is None or c[2] == args.twist)]
                if not combos:
                    raise StoryError("(No valid combination matches the given options.)")
                setting, quest_item, twist = rng.choice(sorted(combos))
                gender = args.gender or rng.choice(sorted(GENDERS))
                name = args.name or _hero_name(gender, rng)
                guide = args.guide or rng.choice(GUIDES)
                params = StoryParams(setting=setting, quest_item=quest_item, twist=twist, name=name, gender=gender, guide=guide, seed=seed)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.quest_item} at {p.setting} (twist: {p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
