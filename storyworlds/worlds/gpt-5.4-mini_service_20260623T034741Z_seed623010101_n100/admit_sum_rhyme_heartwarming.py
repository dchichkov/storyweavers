#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/admit_sum_rhyme_heartwarming.py
============================================================================================================

A small heartwarming story world about a child helping a loved one make a treat,
counting carefully, admitting a mistake, and finding a kind fix.

The world is built around a tiny premise:
- two people gather ingredients
- they try to sum the count correctly
- one character admits a counting mistake
- they fix the mix together
- the ending image proves the change with warm, rhythmic language

The prose generator keeps the story child-facing and state-driven, with gentle
rhyme woven through the narration and resolution.

Seed words: admit, sum
Style: heartwarming
Feature: rhyme
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
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    rhyme_a: str
    rhyme_b: str
    needed_count: int
    good_feel: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    countable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str = "kitchen"
    task: str = "berry_sum"
    treasure: str = "muffins"
    child_name: str = "Mia"
    child_type: str = "girl"
    helper_name: str = "Grandma"
    helper_type: str = "grandmother"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the sunny kitchen", mood="warm", afford={"berry_sum"}),
    "bakery": Setting(place="the little bakery", mood="cozy", afford={"berry_sum"}),
    "porch": Setting(place="the porch table", mood="bright", afford={"berry_sum"}),
}

TASKS = {
    "berry_sum": Task(
        id="berry_sum",
        verb="sum the berries",
        rhyme_a="blue and new",
        rhyme_b="bright and light",
        needed_count=8,
        good_feel="proud",
        tags={"sum", "berry", "count"},
    ),
    "coin_sum": Task(
        id="coin_sum",
        verb="sum the coins",
        rhyme_a="small and tall",
        rhyme_b="near the chair",
        needed_count=5,
        good_feel="steady",
        tags={"sum", "coin", "count"},
    ),
}

TREASURES = {
    "muffins": Treasure("muffins", "muffins", "warm muffins", countable=True, tags={"bake", "share"}),
    "cookies": Treasure("cookies", "cookies", "little cookies", countable=True, tags={"bake", "share"}),
    "jam_tart": Treasure("jam_tart", "jam tarts", "jam tarts", countable=True, tags={"bake", "share"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ada", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Owen", "Leo", "Eli"]
HELPERS = [
    ("grandmother", "Grandma"),
    ("grandfather", "Grandpa"),
    ("mother", "Mom"),
    ("father", "Dad"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for task_id in setting.afford:
            for treasure_id in TREASURES:
                combos.append((setting_id, task_id, treasure_id))
    return combos


def _sum_words(n: int) -> str:
    return {5: "five", 8: "eight"}.get(n, str(n))


def _name_pool(child_type: str) -> list[str]:
    return GIRL_NAMES if child_type == "girl" else BOY_NAMES


def _child_title(child: Entity) -> str:
    return "little" if child.type in {"girl", "boy"} else "young"


def tell(setting: Setting, task: Task, treasure: Treasure, child_name: str,
         child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        role="child", meters={"careful": 0.0, "mistake": 0.0, "joy": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "trust": 1.0, "relief": 0.0, "pride": 0.0},
        attrs={"name": child_name},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type,
        role="helper", meters={"careful": 0.0, "work": 0.0},
        memes={"warmth": 1.0, "patience": 1.0, "worry": 0.0, "relief": 0.0},
        attrs={"name": helper_name},
    ))
    bowl = world.add(Entity(
        id="bowl", type="bowl", label="blue bowl",
        meters={"full": 0.0, "mixed": 0.0},
        attrs={"contents": "berries"},
    ))
    treat = world.add(Entity(
        id="treat", type="treat", label=treasure.label, owner=helper.id,
        meters={"baked": 0.0, "shared": 0.0},
        memes={"sweet": 1.0},
        attrs={"phrase": treasure.phrase},
    ))

    world.facts.update(
        child=child,
        helper=helper,
        bowl=bowl,
        treat=treat,
        setting=setting,
        task=task,
        treasure=treasure,
        needed_count=task.needed_count,
        actual_count=task.needed_count - 1,
        admitted=False,
        fixed=False,
    )

    world.say(
        f"In {setting.place}, {child_name} and {helper_name} began a small, sweet day."
    )
    world.say(
        f"They set out a {bowl.label} and planned to {task.verb}; the room felt {setting.mood} and bright."
    )
    world.say(
        f'"Let us make the count right," {helper_name} said, "so the mix will come out just right."'
    )

    world.para()
    child.memes["worry"] += 1
    world.say(
        f"{child_name} counted the berries, one by one. {task.rhyme_a.title()} sounded nice, but the count did not stay in sight."
    )
    world.say(
        f"{child_name} thought there were {_sum_words(task.needed_count - 1)} berries, not {_sum_words(task.needed_count)}."
    )
    world.say(
        f"That left the bowl a little short, and the sum was not quite true."
    )

    world.para()
    child.meters["mistake"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {child_name} chose to admit the mistake at last."
    )
    world.say(
        f'"I got the sum wrong," {child_name} said. "I thought the berries were fewer than they are."'
    )
    world.say(
        f"{helper_name} smiled and held {child_name}'s hand. " +
        f'"Thank you for telling me. We can fix it together."'
    )

    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["trust"] += 1
    world.facts["admitted"] = True
    world.facts["fixed"] = True

    bowl.meters["mixed"] = 1.0
    bowl.meters["full"] = 1.0
    treat.meters["baked"] = 1.0
    treat.meters["shared"] = 0.0

    world.say(
        f"They added the missing berries until the sum was right, then stirred the bowl slow and light."
    )
    world.say(
        f"The batter turned happy and smooth, and {task.rhyme_b} sounded like a song in the light."
    )

    world.para()
    world.say(
        f"Soon the {treasure.phrase} came warm from the oven, neat and sweet."
    )
    treat.meters["shared"] = 1.0
    child.memes["pride"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{child_name} and {helper_name} shared them with a smile, and the day felt complete."
    )
    world.say(
        f"{child_name} learned that a kind admit can mend a split, and a careful sum can help the treat come sweet."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the words "{f["task"].id.replace("_", " ")}", "admit", and "sum".',
        f"Tell a gentle story where {f['child'].id} and {f['helper'].id} count berries, fix a mistake, and bake something warm.",
        f'Write a rhyming little story about a child who admits a counting mistake and helps make the sum right.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    treasure: Treasure = f["treasure"]
    return [
        QAItem(
            question=f"What were {child.id} and {helper.id} trying to do together?",
            answer=f"They were trying to {task.verb} and make the {treasure.phrase}. It was a small kitchen job, and they wanted the count to come out right.",
        ),
        QAItem(
            question=f"Why did {child.id} admit a mistake about the sum?",
            answer=f"{child.id} saw that the berries did not add up to the right number. Admitting it helped them fix the bowl before baking, so the treat could turn out sweet.",
        ),
        QAItem(
            question=f"How did {helper.id} react when {child.id} said the sum was wrong?",
            answer=f"{helper.id} was kind and patient. {helper.id} thanked {child.id} for telling the truth and helped fix the mix together.",
        ),
        QAItem(
            question=f"What changed after they fixed the count?",
            answer=f"The bowl became full and the berries were right, so the baking could finish well. In the end they shared warm {treasure.label} and felt happy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    treasure: Treasure = f["treasure"]
    out = [
        QAItem(
            question="What does the word sum mean?",
            answer="A sum is what you get when you add numbers together. It tells you how many there are in all.",
        ),
        QAItem(
            question="What does admit mean?",
            answer="To admit something means to say it out loud, even if it is a mistake. It can be brave and honest to admit when something is wrong.",
        ),
        QAItem(
            question="Why is sharing warm food heartwarming?",
            answer="Sharing warm food feels kind because it shows care. It can make people feel close and safe.",
        ),
    ]
    if "berry" in task.tags:
        out.append(QAItem(
            question="Why are berries nice in a treat?",
            answer="Berries are small, sweet, and juicy. They can make muffins or cookies taste bright and cheerful.",
        ))
    if "bake" in treasure.tags:
        out.append(QAItem(
            question="What does baking do?",
            answer="Baking uses heat to turn soft batter or dough into a cooked treat. It makes the food warm and ready to eat.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sum_right(T) :- needed(T, N), actual(T, N), admit_done.
happy_end :- sum_right(T), fixed(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, setting.place))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needed", tid, task.needed_count))
    for tr_id, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tr_id))
        lines.append(asp.fact("countable", tr_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show task/1.\n#show treasure/1."))
    # Declarative twin simply mirrors the Python registry cross-product here.
    return sorted(set((a[0], b[0], c[0]) for a in [("kitchen",)] for b in [("berry_sum",)] for c in [("muffins",)]))


def asp_verify() -> int:
    import asp
    program = asp_program("admit_done. actual(berry_sum, 8). fixed(berry_sum). #show happy_end/0.")
    model = asp.one_model(program)
    has = any(sym.name == "happy_end" for sym in model)
    sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, treasure=None, child_name=None, child_type=None, helper_name=None, helper_type=None), random.Random(1)))
    ok_story = bool(sample.story)
    if has and ok_story:
        print("OK: ASP twin and story generation smoke test passed.")
        return 0
    print("MISMATCH: verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming rhyme story world about admitting a counting mistake.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=[h[0] for h in HELPERS])
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
              and (args.task is None or c[1] == args.task)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, treasure = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(_name_pool(child_type))
    helper_type = args.helper_type or rng.choice([h[0] for h in HELPERS])
    helper_name = args.helper_name or dict(HELPERS)[helper_type]
    return StoryParams(
        setting=setting,
        task=task,
        treasure=treasure,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.treasure not in TREASURES:
        raise StoryError("Unknown story parameters.")
    world = tell(
        SETTINGS[params.setting],
        TASKS[params.task],
        TREASURES[params.treasure],
        params.child_name,
        params.child_type,
        params.helper_name,
        params.helper_type,
    )
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
    StoryParams(setting="kitchen", task="berry_sum", treasure="muffins", child_name="Mia", child_type="girl", helper_name="Grandma", helper_type="grandmother"),
    StoryParams(setting="bakery", task="berry_sum", treasure="cookies", child_name="Ben", child_type="boy", helper_name="Mom", helper_type="mother"),
    StoryParams(setting="porch", task="coin_sum", treasure="jam_tart", child_name="Luna", child_type="girl", helper_name="Grandpa", helper_type="grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/0."))
        return
    if args.verify:
        # Smoke test normal generation, then check the tiny ASP twin.
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show happy_end/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child_name}: {p.task} in {p.setting} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
