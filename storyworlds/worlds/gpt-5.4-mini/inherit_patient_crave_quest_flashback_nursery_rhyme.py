#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inherit_patient_crave_quest_flashback_nursery_rhyme.py
======================================================================================

A standalone storyworld for a tiny nursery-rhyme quest about a patient child
who craves a family heirloom, remembers a helpful flashback, and earns a new
way to inherit the task.

The domain is intentionally small:
- a child wants a bright heirloom tied to a quest
- a patient helper recalls a flashback that explains the family rule
- the child either learns the rule, completes the quest, and inherits the task
  or, if the setup is unreasonable, the script refuses the story

The prose aims for a light nursery-rhyme rhythm while still being driven by
simulated state: desire, patience, memory, and quest progress.
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

    tags: set[str] = field(default_factory=set)

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
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class QuestItem:
    id: str
    label: str
    shine: str
    held_by: str = "home"
    treasured: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Flashback:
    id: str
    moment: str
    lesson: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    route: str
    reward: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, QuestItem] = field(default_factory=dict)
    quests: dict[str, Quest] = field(default_factory=dict)
    flashbacks: dict[str, Flashback] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: QuestItem) -> QuestItem:
        self.items[item.id] = item
        return item

    def add_quest(self, quest: Quest) -> Quest:
        self.quests[quest.id] = quest
        return quest

    def add_flashback(self, fb: Flashback) -> Flashback:
        self.flashbacks[fb.id] = fb
        return fb

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.quests = copy.deepcopy(self.quests)
        clone.flashbacks = copy.deepcopy(self.flashbacks)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    quest: str
    heirloom: str
    flashback: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CHILDREN = {
    "Mia": "girl",
    "Nora": "girl",
    "Lily": "girl",
    "Eli": "boy",
    "Finn": "boy",
    "Theo": "boy",
}

HELPERS = {
    "Mother Goose": "mother",
    "Grandma Wren": "woman",
    "Papa Reed": "father",
    "Uncle Beau": "man",
}

QUESTS = {
    "garden_bells": Quest(
        "garden_bells",
        "the bell quest",
        "find the three bright bells",
        "the mossy path past the gate",
        "a silver ribbon",
        tags={"quest", "bells"},
    ),
    "moon_pearls": Quest(
        "moon_pearls",
        "the pearl quest",
        "gather the moon pearls",
        "the quiet lane by the pond",
        "a pearl crown",
        tags={"quest", "pearls"},
    ),
    "river_keys": Quest(
        "river_keys",
        "the key quest",
        "fetch the little river keys",
        "the winding path under the willow",
        "a brass key-ring",
        tags={"quest", "keys"},
    ),
}

HEIRLOOMS = {
    "bell": QuestItem("bell", "a little brass bell", "bright as morning", tags={"bells", "inherit"}),
    "pearl": QuestItem("pearl", "a pearl necklace", "soft as milk", tags={"pearls", "inherit"}),
    "key": QuestItem("key", "a brass key-ring", "warm as toast", tags={"keys", "inherit"}),
}

FLASHBACKS = {
    "lullaby": Flashback(
        "lullaby",
        "when the child once lost a toy in the grass",
        "patient hands found it by looking slowly and singing softly",
        "slow steps can find what rushing misses",
        tags={"patient", "flashback"},
    ),
    "rain": Flashback(
        "rain",
        "when the path grew slick and the helper waited for the puddles to pass",
        "patient feet keep the journey safe",
        "waiting can be wiser than hurrying",
        tags={"patient", "flashback"},
    ),
    "cookie": Flashback(
        "cookie",
        "when a crumbly cookie broke in two and had to be shared",
        "patient hearts can crave and still take turns",
        "craving does not have to turn into grabbing",
        tags={"patient", "crave", "flashback"},
    ),
}

GENTLE_NAMES = ["Mia", "Nora", "Lily", "Eli", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for q in QUESTS:
        for h in HEIRLOOMS:
            for f in FLASHBACKS:
                if q == "garden_bells" and h == "bell":
                    combos.append((q, h, f))
                if q == "moon_pearls" and h == "pearl":
                    combos.append((q, h, f))
                if q == "river_keys" and h == "key":
                    combos.append((q, h, f))
    return combos


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = [n for n, g in CHILDREN.items() if g == gender]
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme quest storyworld about inheritance, patience, craving, and a remembered flashback."
    )
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--heirloom", choices=sorted(HEIRLOOMS))
    ap.add_argument("--flashback", choices=sorted(FLASHBACKS))
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


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for h in HEIRLOOMS:
        lines.append(asp.fact("heirloom", h))
    for f in FLASHBACKS:
        lines.append(asp.fact("flashback", f))
    lines.append(asp.fact("match", "garden_bells", "bell"))
    lines.append(asp.fact("match", "moon_pearls", "pearl"))
    lines.append(asp.fact("match", "river_keys", "key"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q, H, F) :- quest(Q), heirloom(H), flashback(F), match(Q, H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(quest: str, heirloom: str, flashback: str) -> bool:
    return (quest, heirloom, flashback) in valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.heirloom and not reasonableness_gate(args.quest, args.heirloom, args.flashback or "lullaby"):
        raise StoryError("That heirloom does not belong to that quest in this tiny world.")
    combos = [c for c in valid_combos()
              if (args.quest is None or c[0] == args.quest)
              and (args.heirloom is None or c[1] == args.heirloom)
              and (args.flashback is None or c[2] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    quest, heirloom, flashback = rng.choice(sorted(combos))
    child = args.child or _pick_name(rng, rng.choice(["girl", "boy"]))
    child_gender = CHILDREN[child]
    helper = args.helper or rng.choice(sorted(HELPERS))
    helper_gender = HELPERS[helper]
    return StoryParams(child, child_gender, helper, helper_gender, quest, heirloom, flashback)


def _story(world: World, p: StoryParams) -> None:
    child = world.add_entity(Entity(id=p.child, kind="character", type=p.child_gender, role="child"))
    helper = world.add_entity(Entity(id=p.helper, kind="character", type=p.helper_gender, role="helper"))
    quest = world.add_quest(QUESTS[p.quest])
    item = world.add_item(HEIRLOOMS[p.heirloom])
    fb = world.add_flashback(FLASHBACKS[p.flashback])

    child.memes["crave"] += 1
    child.memes["patience"] += 1
    helper.memes["patience"] += 1

    world.say(
        f"{child.id} went tripping to the gate, with a craved-for gleam in {child.pronoun('possessive')} eye. "
        f"{child.pronoun().capitalize()} longed for {item.label}, the family light of old."
    )
    world.say(
        f"“I crave it so,” {child.id} sang low, “I crave it so; I want to inherit what the old bells know.”"
    )

    world.para()
    world.say(
        f"But {helper.id} smiled and said, “Softly now, little one. First comes the {quest.title}, "
        f"and then the gift can go.”"
    )
    world.say(
        f"The path was {quest.route}, and the air was mild. {child.id} took patient steps, small as a child."
    )

    world.para()
    world.say(
        f"Then came a flashback, as quick as a thread of silver. {fb.moment}. "
        f"{fb.lesson.capitalize()}, the helper had said before."
    )
    world.say(
        f"{child.id} remembered the little lesson: {fb.clue}. So {child.id} did not rush, and did not grab."
    )

    world.para()
    child.memes["patient"] += 1
    child.meters["quest_progress"] += 1
    item.held_by = child.id
    world.say(
        f"Step by step, {child.id} finished the {quest.title}. At last the three bright signs were found, "
        f"and the path grew calm as a nursery rhyme."
    )
    world.say(
        f"“Now,” said {helper.id}, “you may inherit the task and keep the family shine.” "
        f"So {item.label} was given to {child.id}, warm as toast and bright as a song."
    )
    world.say(
        f"{child.id} held {item.label} close, patient no more in worry, but patient still in heart. "
        f"Their craving had turned into care."
    )

    world.facts.update(
        child=child,
        helper=helper,
        quest=quest,
        item=item,
        flashback=fb,
        outcome="complete",
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    _story(world, params)
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
        f"Write a nursery-rhyme quest story where {f['child'].id} craves {f['item'].label} and learns to be patient.",
        f"Tell a gentle story with a flashback, a quest, and the words inherit, patient, and crave.",
        f"Write a child-friendly rhyme where a helper remembers a flashback and guides {f['child'].id} through a quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, quest, item, fb = f["child"], f["helper"], f["quest"], f["item"], f["flashback"]
    return [
        ("What did the child crave?",
         f"{child.id} craved {item.label}. The story keeps returning to that bright wish, like a little rhyme in the mind."),
        ("Why did the helper tell the child to be patient?",
         f"The helper wanted {child.id} to finish the quest the right way before the family heirloom was passed along. Patient steps made the journey safe and careful."),
        ("What did the flashback remind the child of?",
         f"The flashback remembered {fb.moment}, and it showed that slow, patient actions work better than rushing. That memory helped {child.id} keep going without grabbing too soon."),
        ("How did the story end?",
         f"{child.id} completed {quest.title} and inherited {item.label} from the family. The ending proves the child changed from craving only the treasure to caring for the task too."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest"].tags) | set(f["item"].tags) | set(f["flashback"].tags)
    out: list[tuple[str, str]] = []
    if "quest" in tags:
        out.append(("What is a quest?", "A quest is a special journey or job where someone goes looking for something important and keeps trying until it is found."))
    if "patient" in tags:
        out.append(("What does patient mean?", "Patient means able to wait calmly without getting upset or rushing."))
    if "crave" in tags:
        out.append(("What does crave mean?", "Crave means to want something very much."))
    if "flashback" in tags:
        out.append(("What is a flashback in a story?", "A flashback is a part of the story that remembers something that happened earlier."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Mother Goose", "mother", "garden_bells", "bell", "lullaby"),
    StoryParams("Finn", "boy", "Papa Reed", "father", "river_keys", "key", "rain"),
    StoryParams("Lily", "girl", "Grandma Wren", "woman", "moon_pearls", "pearl", "cookie"),
]


def explain_rejection() -> str:
    return "This tiny world only allows heirlooms that fit the matching quest, so the rhyme can stay gentle and clear."


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        return 1 if not print(f"SMOKE TEST FAILED: {exc}") else 1

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:\n")
        for q, h, f in valid_combos():
            print(f"  {q:13} {h:6} {f}")
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
            header = f"### {p.child} and {p.helper}: {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
