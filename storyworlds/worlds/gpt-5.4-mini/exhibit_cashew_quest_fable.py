#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exhibit_cashew_quest_fable.py
==============================================================

A small standalone story world about a fable-like quest in a museum exhibit.

Seed words / instruments:
- exhibit
- cashew
- Quest
- Fable

Premise:
A small traveler wants a cashew that matters to the story of an exhibit. The
quest begins with a missing snack, a cautious warning, a chosen helper, and a
final gift that proves the change. The world model tracks physical state
(meters) and feelings (memes), and the prose is rendered from that changing
state.

The story is intentionally compact:
- begin with a need,
- create a small problem with a tempting but unwise choice,
- resolve it through a safer, kinder path,
- end with a changed image and a gentle moral.

This file is self-contained and follows the Storyweavers contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    exhibit_name: str
    mood: str
    quiet_spot: str
    afford_quest: bool = True


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    where: str
    delicate: bool = False
    edible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    tool: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("need") and not world.facts.get("need_addressed"):
        for ent in world.entities.values():
            if ent.role == "hero":
                ent.memes["worry"] += 1
        if ("worry",) not in world.fired:
            world.fired.add(("worry",))
            out.append("__worry__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("helper_used") and not world.facts.get("quest_complete"):
        if ("comfort",) not in world.fired:
            world.fired.add(("comfort",))
            world.get("hero").memes["hope"] += 1
            out.append("__comfort__")
    return out


RULES = [Rule("worry", _r_worry), Rule("comfort", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(item: QuestItem) -> bool:
    return item.edible or item.delicate


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def is_supported(resolution: Resolution, item: QuestItem) -> bool:
    return resolution.power >= (2 if item.delicate else 1)


def _setup(world: World, hero: Entity, friend: Entity, setting: Setting, item: QuestItem) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"At {setting.place}, the little travelers entered the {setting.exhibit_name}. "
        f"{setting.mood.capitalize()} air, a quiet floor, and {setting.quiet_spot} made the hall feel like a gentle puzzle."
    )
    world.say(
        f"{hero.id} noticed a missing {item.label} and whispered that the quest could not be finished until it was found."
    )


def _tempt(world: World, hero: Entity, item: QuestItem) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'{hero.id} stared at the place where the {item.label} should have been. '
        f'"I can reach it faster than anyone," {hero.id} said, and took one quick step the wrong way.'
    )


def _warn(world: World, friend: Entity, hero: Entity, item: QuestItem) -> None:
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} lifted a hand. "{hero.id}, not that way," {friend.id} said. '
        f'"This exhibit is delicate, and a rushed step could spoil the whole room."'
    )


def _mend_path(world: World, friend: Entity, hero: Entity, helper: Helper) -> None:
    hero.memes["patience"] += 1
    friend.memes["hope"] += 1
    world.facts["helper_used"] = True
    world.say(
        f"Then {friend.id} showed {hero.id} {helper.tool} and {helper.advice}. "
        f"The two of them chose the safer path together."
    )


def _find_item(world: World, hero: Entity, item: QuestItem) -> None:
    item_ent = world.add(Entity(id="quest_item", type="thing", label=item.label))
    item_ent.meters["found"] += 1
    world.facts["need_addressed"] = True
    world.say(
        f"They looked behind the bench, then beside the quiet sign, and there was the {item.label}, waiting all along."
    )


def _complete(world: World, hero: Entity, friend: Entity, item: QuestItem, resolution: Resolution) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.facts["quest_complete"] = True
    world.say(
        f"{hero.id} picked up the {item.label} carefully, and {friend.id} smiled. "
        f"{resolution.success.replace('{item}', item.label)}"
    )
    world.say(
        f"In the end, the exhibit was left neat, the {item.label} was safe, and the quest felt wiser than when it began."
    )


def _fail(world: World, hero: Entity, friend: Entity, item: QuestItem, resolution: Resolution) -> None:
    hero.memes["fear"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"{hero.id} tried to hurry, but {resolution.fail.replace('{item}', item.label)}"
    )
    world.say(
        f"That was how the little quest turned into a careful lesson: the exhibit needed steady hands, not greedy ones."
    )


def tell(setting: Setting, item: QuestItem, helper: Helper, resolution: Resolution,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Toby", friend_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id="exhibit", type="place", label=setting.exhibit_name))
    world.add(Entity(id="item", type="thing", label=item.label))
    world.facts["setting"] = setting
    world.facts["item"] = item
    world.facts["helper"] = helper
    world.facts["resolution"] = resolution

    _setup(world, hero, friend, setting, item)
    world.para()
    _tempt(world, hero, item)
    _warn(world, friend, hero, item)

    if setting.afford_quest and quest_at_risk(item):
        _mend_path(world, friend, hero, helper)
        world.para()
        _find_item(world, hero, item)
        world.para()
        if is_supported(resolution, item):
            _complete(world, hero, friend, item, resolution)
            outcome = "complete"
        else:
            _fail(world, hero, friend, item, resolution)
            outcome = "failed"
    else:
        raise StoryError("This exhibit does not support a real quest with a meaningful turn.")

    world.facts.update(hero=hero, friend=friend, outcome=outcome, item_found=True)
    return world


SETTINGS = {
    "museum": Setting("museum", "the museum", "moon exhibit", "soft and gold", "a bench by the wall"),
    "gallery": Setting("gallery", "the gallery", "river exhibit", "cool and calm", "a rope line"),
    "hall": Setting("hall", "the hall", "story exhibit", "quiet and bright", "a brass stand"),
}

ITEMS = {
    "cashew": QuestItem("cashew", "cashew", "a small cashew", "near the exhibit card", edible=True, tags={"cashew", "food"}),
    "seed": QuestItem("seed", "seed", "a shiny seed", "inside a little tray", delicate=True, tags={"seed"}),
    "bead": QuestItem("bead", "bead", "a blue bead", "under the glass edge", delicate=True, tags={"bead"}),
}

HELPERS = {
    "map": Helper("map", "map", "guide", "a tiny map", "to follow the arrows and take the side path", tags={"map", "quest"}),
    "lamp": Helper("lamp", "lamp", "guide", "a small lamp", "to carry light and keep both hands free", tags={"lamp"}),
}

RESOLUTIONS = {
    "careful": Resolution("careful", 3, 2,
                          "They placed the {item} in a safe little bowl and carried it back without a scratch.",
                          "They rushed too fast and lost the {item} again in the busy hall.",
                          "placed the {item} in a safe little bowl and carried it back"),
    "shared": Resolution("shared", 2, 3,
                         "They shared the {item} with a thankful smile, and the quest ended in friendship.",
                         "They tried to grab the {item}, but their hands slipped and the quest fell apart.",
                         "shared the {item} with a thankful smile"),
    "gentle": Resolution("gentle", 3, 2,
                         "They moved the {item} gently into the right place, and the room seemed to breathe easier.",
                         "They moved too roughly, and the {item} could not be saved.",
                         "moved the {item} gently into the right place"),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Eli", "Ivy", "Rosa", "Ada"]
BOY_NAMES = ["Toby", "Owen", "Finn", "Theo", "Noel", "Milo", "Ezra"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for r in RESOLUTIONS:
                if quest_at_risk(ITEMS[i]):
                    combos.append((s, i, r))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    helper: str
    resolution: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cashew": [("What is a cashew?", "A cashew is a curved nut that people can eat. It is small, hard, and tasty.")],
    "exhibit": [("What is an exhibit?", "An exhibit is a display in a museum or gallery that shows interesting things.")],
    "quest": [("What is a quest?", "A quest is a search for something important, with steps to solve along the way.")],
    "fable": [("What is a fable?", "A fable is a short story that teaches a lesson, often by showing a character making a choice.")],
    "delicate": [("What does delicate mean?", "Delicate means something can be hurt or spoiled easily, so it needs gentle care.")],
}
KNOWLEDGE_ORDER = ["quest", "fable", "exhibit", "cashew", "delicate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style quest story for a young child that includes the words "exhibit" and "cashew".',
        f"Tell a gentle museum quest where {f['hero'].id} and {f['friend'].id} search the {f['setting'].exhibit_name} for a cashew and solve the problem wisely.",
        f"Write a short quest fable about a missing cashew in a quiet exhibit, ending with a lesson about patient hands and careful choices.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, setting, item = f["hero"], f["friend"], f["setting"], f["item"]
    resolution = f["resolution"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who went on a small quest in the {setting.exhibit_name}."),
        ("What were they looking for?",
         f"They were looking for a {item.label}. The missing {item.label} was the reason the quest began."),
        ("Why did the friend warn the hero?",
         f"{friend.id} warned {hero.id} because the exhibit was delicate and a rushed choice could spoil the room. The safer path kept the search from turning into a mess."),
        ("How did the quest end?",
         f"It ended when they chose to be careful and {resolution.qa_text.replace('{item}', item.label)}. That gentle choice finished the quest and kept the exhibit safe."),
    ]
    if f.get("outcome") == "complete":
        qa.append((
            "What changed by the end?",
            f"{hero.id} learned to slow down, and {friend.id} got to help in a kind way. The {item.label} was found, and the exhibit stayed neat."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | {"quest", "fable", "exhibit"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("museum", "cashew", "map", "careful", "Mina", "girl", "Toby", "boy"),
    StoryParams("gallery", "seed", "lamp", "gentle", "Nora", "girl", "Ezra", "boy"),
    StoryParams("hall", "bead", "map", "shared", "Theo", "boy", "Lia", "girl"),
]


def explain_rejection(item: QuestItem) -> str:
    return f"(No story: the chosen item '{item.label}' is not a good quest object for this exhibit tale.)"


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.item in ITEMS and params.resolution in RESOLUTIONS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.item not in ITEMS:
        raise StoryError(explain_rejection(QuestItem(args.item, args.item, args.item, "")))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, resolution = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting, item, helper, resolution, hero_name, hero_gender, friend_name, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], HELPERS[params.helper], RESOLUTIONS[params.resolution],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
quest_risk(I) :- item(I), edible(I).
valid(S, I, R) :- setting(S), item(I), resolution(R), quest_risk(I).
success(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
outcome(complete) :- valid(_, I, R), success(R), item(I).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.edible:
            lines.append(asp.fact("edible", iid))
        if item.delicate:
            lines.append(asp.fact("delicate", iid))
    for rid, res in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, res.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show success/1."))
    return sorted(r for (r,) in asp.atoms(model, "success"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_resolutions()}:
        print("OK: sensible resolutions match.")
    else:
        print("MISMATCH in sensible resolutions.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: an exhibit quest with a cashew and a fable-like moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
        print(asp_program("", "#show valid/3.\n#show success/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
