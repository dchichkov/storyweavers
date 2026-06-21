#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whip_quest_pirate_tale.py
=========================================================

A small storyworld in a pirate-tale style: children or crewmates prepare for a
quest, one bold choice involves a whip, a wiser helper warns, and the ship's
adult or captain either chooses a safe, sensible tool or calls the crew to a
better plan.

The premise is intentionally tiny:
- a pirate quest needs to reach a high place or untangle something fast,
- a whip is tempting because it seems quick and dramatic,
- the world model checks whether the whip is a reasonable tool,
- and the ending proves what changed in the world state.

The prose stays child-facing and concrete. The world is driven by state, not a
frozen paragraph with swapped names.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 5.0


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
    dangerous: bool = False
    safe_tool: bool = False
    quest_item: bool = False
    in_use: bool = False

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
        return {"mother": "mom", "father": "dad", "captain": "captain"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    place: str
    quest_goal: str
    dark_spot: str
    hazard_word: str
    quest_image: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    purpose: str
    safe: bool = False
    power: int = 0
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
    item: str
    safe_item1: str
    safe_item2: str
    delay: int = 0
    bravery: int = 5
    seed: Optional[int] = None


SETTINGS = {
    "harbor_cave": Setting(
        id="harbor_cave",
        scene="a moonlit harbor cave",
        place="the stone path by the docks",
        quest_goal="the treasure chest hanging above the tide",
        dark_spot="the black rope bridge",
        hazard_word="the ropes",
        quest_image="a cave map with a red X",
    ),
    "island_mast": Setting(
        id="island_mast",
        scene="a windy island camp",
        place="the deck of the little ship",
        quest_goal="the flag basket near the mast",
        dark_spot="the tall mast lines",
        hazard_word="the rigging",
        quest_image="a crinkled chart and a shell compass",
    ),
    "storm_bay": Setting(
        id="storm_bay",
        scene="a rainy bay hideout",
        place="the wet boardwalk",
        quest_goal="the lantern crate on the pier",
        dark_spot="the slippery crate stack",
        hazard_word="the crates",
        quest_image="a sealed bottle map",
    ),
}

ITEMS = {
    "whip": Item("whip", "whip", "a long whip", "tool", "to snap or lash a thing", safe=False, power=0, tags={"whip", "danger"}),
    "hook": Item("hook", "hook", "a sturdy hook", "tool", "to grab a rope", safe=True, power=2, tags={"hook"}),
    "rope": Item("rope", "rope", "a loop of rope", "tool", "to pull up a package", safe=True, power=2, tags={"rope"}),
    "lantern": Item("lantern", "lantern", "a bright lantern", "tool", "to light the way", safe=True, power=1, tags={"light"}),
    "pole": Item("pole", "pole", "a long pole", "tool", "to reach a high place", safe=True, power=2, tags={"pole"}),
    "net": Item("net", "net", "a fishing net", "tool", "to catch a loose bundle", safe=True, power=2, tags={"net"}),
}

CURATED = [
    StoryParams(setting="harbor_cave", hero="Pip", hero_gender="boy", helper="Mara", helper_gender="girl", adult="Captain Vale", adult_gender="man", item="whip", safe_item1="hook", safe_item2="lantern", delay=0, bravery=6),
    StoryParams(setting="island_mast", hero="Nia", hero_gender="girl", helper="Toby", helper_gender="boy", adult="First Mate Rook", adult_gender="man", item="whip", safe_item1="pole", safe_item2="rope", delay=1, bravery=5),
    StoryParams(setting="storm_bay", hero="Joss", hero_gender="boy", helper="Lena", helper_gender="girl", adult="Captain Mira", adult_gender="woman", item="whip", safe_item1="net", safe_item2="lantern", delay=0, bravery=4),
]

GIRL_NAMES = ["Mara", "Nia", "Lena", "Asha", "Lily", "Mina"]
BOY_NAMES = ["Pip", "Toby", "Joss", "Finn", "Noel", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if item_id != "whip":
                continue
            out.append((sid, item_id, "quest"))
    return out


def reasonableness_gate(item: Item, setting: Setting) -> bool:
    return item.id == "whip"


def explain_rejection(item: Item, setting: Setting) -> str:
    return f"(No story: this world is built around the whip on a pirate quest, so {item.label} is not the chosen quest tool.)"


def predict_use(world: World, setting: Setting, item: Item) -> dict:
    sim = world.copy()
    if item.id == "whip":
        sim.get("quest_item").meters["risk"] += 1
        if "bridge" in setting.dark_spot or "mast" in setting.dark_spot:
            sim.get("room").meters["tension"] += 1
    return {"risk": sim.get("quest_item").meters["risk"], "tension": sim.get("room").meters["tension"]}


def tell(setting: Setting, hero: Entity, helper: Entity, adult: Entity, item: Item, safe1: Item, safe2: Item, delay: int, bravery: int) -> World:
    world = World()
    world.add(Entity("room", kind="place", type="room"))
    quest_item = world.add(Entity("quest_item", type="thing", label=setting.quest_goal, quest_item=True))
    tool = world.add(Entity("tool", type="thing", label=item.label, dangerous=not item.safe))
    hero.memes["bravery"] = float(bravery)
    helper.memes["care"] = 4.0
    adult.memes["calm"] = 5.0

    world.say(
        f"On a windy evening, {hero.id} and {helper.id} sailed into {setting.scene}. "
        f"Their map showed {setting.quest_goal}, and the crew could feel a real quest waiting."
    )
    world.say(
        f"{helper.id} pointed at {setting.dark_spot}. \"We need to cross there,\" {helper.pronoun()} said, "
        f"\"but the rope bridge looks tricky.\""
    )

    world.para()
    world.say(
        f"{hero.id}'s eyes flashed. \"I know! {item.label}!\" {hero.id} said, lifting {item.phrase}. "
        f"It looked quick and bold, like something from an old pirate tale."
    )
    pred = predict_use(world, setting, item)
    world.facts["predicted"] = pred
    world.facts["setting"] = setting
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["adult"] = adult
    world.facts["item"] = item
    world.facts["safe1"] = safe1
    world.facts["safe2"] = safe2

    if bravery <= 3:
        world.say(
            f"{helper.id} shook {helper.pronoun('possessive')} head. \"That would only snag the ropes and make a mess,\" "
            f"{helper.id} said. \"Let's not use it.\""
        )
        world.say(
            f"{hero.id} paused, nodded, and handed the whip back. The crew chose {safe1.label} and {safe2.label} instead."
        )
        adult_action(world, adult, safe1, safe2, setting, hero, helper, averted=True)
        world.facts["outcome"] = "averted"
        return world

    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip. \"{hero.id}, that whip might snap the wrong thing,\" "
        f"{helper.id} warned. But the quest felt exciting."
    )
    world.say(f"{hero.id} tried to use the whip anyway.")
    world.get("quest_item").meters["risk"] += 1
    world.get("room").meters["tension"] += 1

    world.para()
    world.say(
        f"{item.label_word if False else ''}".strip()
    )
    world.say(
        f"The whip cracked near {setting.hazard_word}, and the whole quest turned wobbly. "
        f"Then {adult.id} came running."
    )

    if delay > 0:
        world.get("room").meters["tension"] += float(delay)

    if item.id == "whip":
        world.say(
            f"{adult.id} did not shout. {adult.pronoun().capitalize()} grabbed {safe1.label} from the crate, "
            f"and {adult.pronoun()} used it to reach the goal the sensible way."
        )
        world.say(
            f"{adult.id} also handed over {safe2.phrase}, so the dark path could be lit without any more snapping."
        )
        world.get("quest_item").meters["safe_reached"] = 1
        world.facts["outcome"] = "contained"

    world.para()
    world.say(
        f"The crew reached {setting.quest_goal} at last. {hero.id} held {safe1.label} high, "
        f"{helper.id} held the {safe2.label}, and the pirate quest continued bright and safe."
    )
    return world


def adult_action(world: World, adult: Entity, safe1: Item, safe2: Item, setting: Setting, hero: Entity, helper: Entity, averted: bool = False) -> None:
    world.say(
        f"{adult.id} smiled and brought out {safe1.phrase} and {safe2.phrase}. "
        f"\"A real pirate solves a quest without getting the crew tangled,\" {adult.id} said."
    )
    if averted:
        world.say(
            f"That was enough. No one used the whip, and the bridge stayed quiet. "
            f"The map still pointed to {setting.quest_goal}, but now the way there was safe."
        )
    else:
        world.say(
            f"The kids watched {adult.id} work. The careful way was slower, but it kept the ropes steady and the crew calm."
        )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write a pirate tale about a quest in {setting.scene} that includes the word "whip".',
        f"Tell a child-friendly pirate adventure where a bold child wants to use a whip, but the crew finds a safer tool instead.",
        f"Write a short quest story with treasure-map energy, a whip, and a calm ending image that shows the crew succeeding safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    setting: Setting = f["setting"]
    item: Item = f["item"]
    safe1: Item = f["safe1"]
    safe2: Item = f["safe2"]
    outcome = f["outcome"]
    pred = f["predicted"]
    qa = [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a pirate-style quest story about {hero.id} and {helper.id} trying to reach {setting.quest_goal}. The tale starts with a map and ends with the crew finding a safer way through the tricky place.",
        ),
        QAItem(
            question=f"What did {hero.id} want to use?",
            answer=f"{hero.id} wanted to use {item.label}. It looked fast and dramatic, but the world shows it was not the safest choice for this quest.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id}?",
            answer=f"{helper.id} warned {hero.id} because the whip could snag the ropes and make the quest worse. The warning matters because the dark spot and the quest item needed a steadier tool.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            QAItem(
                question="How did the problem get solved?",
                answer=f"{hero.id} listened, handed back the whip, and the crew chose {safe1.label} and {safe2.label} instead. That meant the quest could continue without any danger at all.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"What did {adult.id} do after the whip caused trouble?",
                answer=f"{adult.id} came running and used {safe1.label} and {safe2.label} to finish the quest the careful way. The quick rescue kept the ropes steady and got everyone back on track.",
            )
        )
    qa.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the crew reaching {setting.quest_goal} and holding {safe1.label} and {safe2.label} in the last scene. The ending proves they chose a safer pirate way to finish the quest.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: Item = f["item"]
    safe1: Item = f["safe1"]
    safe2: Item = f["safe2"]
    return [
        QAItem(
            question="What is a whip?",
            answer="A whip is a long tool that can crack or lash things. It can be dangerous if someone uses it carelessly.",
        ),
        QAItem(
            question=f"What is {safe1.label} for?",
            answer=f"{safe1.label_word if False else safe1.label.capitalize()} is a safe tool for reaching or grabbing something without snapping it. In a story like this, it helps the crew solve the quest more gently.",
        ),
        QAItem(
            question=f"What is {safe2.label} for?",
            answer=f"{safe2.label.capitalize()} gives light or helps the crew see their way in the dark. That makes it useful on a pirate quest where the path is dim.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, whip, quest) :- setting(S), whip_item(whip), quest_feature(quest).
outcome(averted) :- bravery(B), B < 4.
outcome(contained) :- bravery(B), B >= 4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("whip_item", "whip"))
    lines.append(asp.fact("quest_feature", "quest"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hero=None, hero_gender=None, helper=None, helper_gender=None, adult=None, adult_gender=None, item=None, safe_item1=None, safe_item2=None, delay=None, bravery=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-quest storyworld with a whip, a choice, and a safe ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--safe1", choices=["hook", "rope", "lantern", "pole", "net"])
    ap.add_argument("--safe2", choices=["hook", "rope", "lantern", "pole", "net"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["man", "woman"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--bravery", type=int, choices=list(range(0, 11)))
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
    if args.item and args.item != "whip":
        raise StoryError("This world centers on the whip as the quest temptation.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    adult_gender = args.adult_gender or rng.choice(["man", "woman"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    adult = args.adult or rng.choice(["Captain Vale", "Captain Mira", "First Mate Rook"])
    safe_choices = list(ITEMS)
    safe_choices.remove("whip")
    safe1 = args.safe1 or rng.choice(safe_choices)
    safe2 = args.safe2 or rng.choice([x for x in safe_choices if x != safe1])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    bravery = args.bravery if args.bravery is not None else rng.randint(2, 8)
    return StoryParams(
        setting=setting, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
        adult=adult, adult_gender=adult_gender, item="whip", safe_item1=safe1, safe_item2=safe2,
        delay=delay, bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.item not in ITEMS:
        raise StoryError("Unknown quest item.")
    if params.safe_item1 not in ITEMS or params.safe_item2 not in ITEMS:
        raise StoryError("Unknown safe tool.")
    if params.safe_item1 == "whip" or params.safe_item2 == "whip":
        raise StoryError("Safe tools must not be the whip.")
    setting = SETTINGS[params.setting]
    hero = Entity(id=params.hero, kind="character", type=params.hero_gender)
    helper = Entity(id=params.helper, kind="character", type=params.helper_gender)
    adult = Entity(id=params.adult, kind="character", type=params.adult_gender)
    item = ITEMS[params.item]
    safe1 = ITEMS[params.safe_item1]
    safe2 = ITEMS[params.safe_item2]
    world = tell(setting, hero, helper, adult, item, safe1, safe2, params.delay, params.bravery)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
