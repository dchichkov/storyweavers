#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whelm_reindeer_jagged_sharing_quest_lesson_learned.py
======================================================================================

A small, standalone storyworld in a ghost-story style: children follow a quest
through a winter night, share what they have, and learn a lesson when the dark
trail proves harder than expected. The world keeps typed entities with physical
meters and emotional memes, and the prose is driven by state changes rather than
a frozen paragraph with swapped nouns.

Seed words woven into the world model and story:
- whelm
- reindeer
- jagged

Story ingredients:
- Sharing
- Quest
- Lesson Learned
- Ghost Story mood
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    mood: str
    dark_spot: str
    trail: str
    things: list[str] = field(default_factory=list)


@dataclass
class QuestItem:
    id: str
    label: str
    help_text: str
    shines: bool = False
    warms: bool = False
    shared: bool = False


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    sharp: bool = False
    frightening: bool = False
    damp: bool = False


@dataclass
class Lesson:
    id: str
    learned_text: str
    safe_text: str
    bonus: str


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_whelm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["whelm"] < THRESHOLD:
            continue
        sig = ("whelm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        e.memes["resolve"] += 1
        out.append("__whelm__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    kids = [e for e in world.characters() if e.role in {"seeker", "helper"}]
    if len(kids) < 2:
        return out
    seeker = next((e for e in kids if e.role == "seeker"), None)
    helper = next((e for e in kids if e.role == "helper"), None)
    if not seeker or not helper:
        return out
    sig = ("share", seeker.id, helper.id)
    if sig in world.fired:
        return out
    if helper.meters["gift"] < THRESHOLD:
        return out
    world.fired.add(sig)
    seeker.memes["trust"] += 1
    helper.memes["care"] += 1
    out.append("__share__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["lesson"] < THRESHOLD:
            continue
        sig = ("lesson", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["calm"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("whelm", "emotional", _r_whelm),
    Rule("sharing", "social", _r_sharing),
    Rule("lesson", "emotional", _r_lesson),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_risk(obstacle: Obstacle) -> bool:
    return obstacle.sharp or obstacle.frightening


def safe_help(item: QuestItem, obstacle: Obstacle) -> bool:
    if obstacle.sharp and item.shines:
        return True
    if obstacle.frightening and item.warms:
        return True
    return item.shared


def predict_world(world: World, seeker: Entity, helper: Entity, item: QuestItem, obstacle: Obstacle) -> dict:
    sim = world.copy()
    sim.get(seeker.id).meters["whelm"] += 1
    sim.get(helper.id).meters["gift"] += 1
    sim.get(helper.id).memes["lesson"] += 1
    propagate(sim, narrate=False)
    return {
        "whelm": sim.get(seeker.id).memes["fear"],
        "shared": sim.get(helper.id).memes["care"],
        "calm": sim.get(seeker.id).meters["calm"],
    }


def setting_intro(world: World, seeker: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a cold night, {seeker.id} and {helper.id} crossed {setting.place}. "
        f"The air felt like a ghost story, and {setting.mood} hung over the path."
    )
    world.say(
        f"They were looking for {setting.trail}, because an old map said a "
        f"reindeer bell was hidden there."
    )


def need_quest(world: World, seeker: Entity, setting: Setting, obstacle: Obstacle) -> None:
    world.say(
        f"But {setting.dark_spot} stood ahead, all {obstacle.phrase}, and the dark "
        f"made the trail feel longer than it was."
    )
    world.say(f'"We need to keep going," {seeker.id} whispered, "even if the night feels huge."')


def share_before_fear(world: World, helper: Entity, seeker: Entity, item: QuestItem) -> None:
    helper.meters["gift"] += 1
    world.say(
        f"{helper.id} opened {helper.pronoun('possessive')} pocket and held out "
        f"{item.label} to share."
    )
    if item.label == "a red scarf":
        world.say(f'"Take this," {helper.id} said. "It will keep you warm on the quest."')
    else:
        world.say(f'"Take this," {helper.id} said. "It will help us see the way."')


def whelm_beat(world: World, seeker: Entity, obstacle: Obstacle) -> None:
    seeker.meters["whelm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The jagged stones seemed to rise up from the dark, and {seeker.id} felt "
        f"whelm press in like cold water."
    )


def brave_turn(world: World, seeker: Entity, helper: Entity, item: QuestItem, obstacle: Obstacle) -> None:
    pred = predict_world(world, seeker, helper, item, obstacle)
    seeker.memes["lesson"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{seeker.id} blinked at the scary path, then looked at {helper.id}'s gift "
        f"and understood they did not have to be alone."
    )


def quest_finish(world: World, seeker: Entity, helper: Entity, item: QuestItem, lesson: Lesson) -> None:
    seeker.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Together they found the bell by the old stone, and the quest ended with "
        f"its soft jingle in the wind."
    )
    world.say(
        f"{lesson.learned_text} {lesson.safe_text} {lesson.bonus}"
    )


SETTINGS = {
    "winter_lane": Setting(
        "winter_lane",
        "the winter lane",
        "foggy and blue",
        "the old bridge",
        "the reindeer trail",
        things=["fog", "bells"],
    ),
    "snow_field": Setting(
        "snow_field",
        "the snowy field",
        "quiet and pale",
        "the frozen ditch",
        "the reindeer trail",
        things=["snow", "tracks"],
    ),
    "pine_hollow": Setting(
        "pine_hollow",
        "the pine hollow",
        "deep and whispery",
        "the jagged rocks",
        "the reindeer path",
        things=["needles", "shadows"],
    ),
}

QUEST_ITEMS = {
    "lantern": QuestItem("lantern", "a small lantern", "to light the way", shines=True),
    "scarf": QuestItem("scarf", "a red scarf", "to keep warm", warms=True, shared=True),
    "rope": QuestItem("rope", "a loop of rope", "to help them cross", shared=True),
}

OBSTACLES = {
    "jagged": Obstacle("jagged", "jagged rocks", "jagged and sharp", sharp=True),
    "mist": Obstacle("mist", "thick mist", "thick and ghostly", frightening=True),
    "stream": Obstacle("stream", "icy stream", "icy and damp", damp=True),
}

LESSONS = {
    "sharing": Lesson(
        "sharing",
        "They learned that sharing can make a scary quest feel smaller.",
        "A lantern, a scarf, or a rope can help when the dark feels too big.",
        "And the reindeer bell sounded less lonely when they carried help together.",
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    obstacle: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Luna", "Nora", "Pia", "Iris", "Vera"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Milo", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for item_id, item in QUEST_ITEMS.items():
            for ob_id, obstacle in OBSTACLES.items():
                if quest_risk(obstacle) and safe_help(item, obstacle):
                    combos.append((s_id, item_id, ob_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest world with sharing and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.obstacle is None or c[2] == args.obstacle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, obstacle = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if seeker_gender == "girl" and rng.random() < 0.5 else "girl")
    seeker = args.seeker or rng.choice(GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != seeker])
    return StoryParams(setting, item, obstacle, seeker, seeker_gender, helper, helper_gender)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item = QUEST_ITEMS[params.item]
    obstacle = OBSTACLES[params.obstacle]
    lesson = LESSONS["sharing"]
    world = World(setting)
    seeker = world.add(Entity(params.seeker, kind="character", type=params.seeker_gender, role="seeker"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    world.add(Entity("reindeer", kind="thing", type="animal", label="a reindeer", attrs={"magical": True}))
    world.add(Entity("jagged", kind="thing", type="thing", label=obstacle.label))
    world.add(Entity("quest_item", kind="thing", type="thing", label=item.label))
    world.say(
        f"At {setting.place}, the quest began like a whisper."
    )
    setting_intro(world, seeker, helper, setting)
    world.para()
    need_quest(world, seeker, setting, obstacle)
    share_before_fear(world, helper, seeker, item)
    whelm_beat(world, seeker, obstacle)
    brave_turn(world, seeker, helper, item, obstacle)
    world.para()
    quest_finish(world, seeker, helper, item, lesson)
    world.facts.update(
        seeker=seeker,
        helper=helper,
        item=item,
        obstacle=obstacle,
        lesson=lesson,
        setting=setting,
        outcome="shared_quest",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story style quest for a young child that includes "{f["item"].label}" and the word "reindeer".',
        f"Tell a short story where {f['seeker'].id} and {f['helper'].id} face {f['obstacle'].phrase} and solve it by sharing.",
        f'Write a gentle spooky quest story that includes the words "whelm" and "jagged" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    item = f["item"]
    obstacle = f["obstacle"]
    lesson = f["lesson"]
    return [
        ("Who went on the quest?",
         f"{seeker.id} and {helper.id} went on the quest together."),
        ("What made the path scary?",
         f"{obstacle.phrase} and the dark night made the path feel spooky."),
        ("How did they help each other?",
         f"{helper.id} shared {item.label} so the two children could keep going. That sharing made the quest feel less overwhelming."),
        ("What lesson did they learn?",
         f"{lesson.learned_text} {lesson.safe_text}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a reindeer?",
               "A reindeer is a deer that can live in cold places and pull sleds in winter stories."),
        QAItem("What does jagged mean?",
               "Jagged means rough, uneven, and pointy, like rocks with sharp edges."),
        QAItem("What does it mean to share?",
               "To share means to let someone else use or have part of something you have."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I,O) :- setting(S), item(I), obstacle(O), sharp(O), helpful(I,O).
helpful(lantern,jagged).
helpful(scarf,jagged).
helpful(rope,jagged).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in QUEST_ITEMS:
        lines.append(asp.fact("item", i))
    for o, ob in OBSTACLES.items():
        lines.append(asp.fact("obstacle", o))
        if ob.sharp:
            lines.append(asp.fact("sharp", o))
        if ob.frightening:
            lines.append(asp.fact("frightening", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import json as _json
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(StoryParams(*valid_combos()[0], "Ari", "girl", "Noah", "boy"))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
    StoryParams("winter_lane", "lantern", "jagged", "Mina", "girl", "Owen", "boy"),
    StoryParams("snow_field", "scarf", "mist", "Eli", "boy", "Nora", "girl"),
    StoryParams("pine_hollow", "rope", "jagged", "Luna", "girl", "Finn", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
